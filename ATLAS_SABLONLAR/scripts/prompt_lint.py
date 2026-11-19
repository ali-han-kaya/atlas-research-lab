#!/usr/bin/env python3
"""Atlas v5.5.4 Prompt Lint — ajan promptlarinin makine denetimi

NEDEN VAR:
Betik katmaninin 44 testi var, prompt katmaninin HIC yoktu. Oysa DENEME'deki
yanlis PASS betikte degil PROMPTTA olustu: gate-2b'nin kanit alani serbest
metindi, writer-master "DOGRULANMADI etiketi birakma" diyordu, lens-structure
"ayri bir kanit alani GEREKMEZ" yaziyordu. Uc kusur da promptta yaziliydi.

Bu betik model cagirmaz, ag gerektirmez, saniyeler surer. Prompt REGRESYONUNU
yakalar: birisi bu kusurlari geri getirirse kirmizi yanar.

KONTROLLER
  PL-01  Frontmatter var ve description tasiyor
  PL-02  mode kapali listede (primary|subagent|all)
  PL-04  Symlink hedefi repo koku icinde
  PL-09  FAZ1 lensleri KARAR VERMEZ (verdict/gate_decision alani yasak)
  PL-10  "kanit GEREKMEZ" tarzi vacuous-PASS muafiyeti yok
  PL-11  "her zaman PASS" tarzi kalici muafiyet yok
  PL-12  Belirsizlik cikisi var (DOGRULANAMADI|CALISTIRILMADI|NOT_EXECUTED|UNKNOWN)
  PL-13  Belirsizlik etiketi yasaklanmiyor ("etiketlerini birakma" kalibi)
  PL-14  Betik cagiran ajan exit kodundan soz ediyor (fail-closed)
  PL-16  Cagirilan scripts/*.py gercekten var
  PL-18  Symlink kirik degil
  PL-19  Eslenmis promptun JSON alanlari hedef semanin required/properties alanlariyla uyumlu

Kullanim: python3 scripts/prompt_lint.py [--dizin <yol>] [--sessiz]
"""
import glob, json, os, pathlib, re, sys

SESSIZ = "--sessiz" in sys.argv
dizin = "."
if "--dizin" in sys.argv:
    i = sys.argv.index("--dizin")
    if i + 1 < len(sys.argv):
        dizin = sys.argv[i + 1]

KOK = pathlib.Path(dizin).resolve()
hatalar = []
uyarilar = []

LENS = re.compile(r"lens", re.I)
KARAR_ALANI = re.compile(r'"(?:verdict|gate_decision)"\s*:', re.I)
VACUOUS = re.compile(r"kan[ıi]t.{0,80}GEREKMEZ|GEREKMEZ.{0,80}kan[ıi]t|evidence.{0,60}not required", re.I | re.S)
KALICI_MUAF = re.compile(r"her zaman\s+PASS|always\s+pass|daima\s+PASS|dai̇ma\s+PASS", re.I)
BELIRSIZ = re.compile(r"DOGRULANAMADI|DOĞRULANAMADI|CALISTIRILMADI|ÇALIŞTIRILMADI|NOT_EXECUTED|UNKNOWN", re.I)
ETIKET_YASAK = re.compile(r"etiketleri(?:ni)?\s+b[ıi]rakma", re.I)
BETIK_CAGRI = re.compile(r"(?:python3|bash)\s+scripts/([\w.]+)")
EXIT_SOZ = re.compile(r"exit\s*kod|exit\s*code|çıkış\s*kod|cikis\s*kod", re.I)
MODLAR = {"primary", "subagent", "all"}
JSON_KOD_BLOK = re.compile(r"```json\s*(.*?)```", re.I | re.S)

# Prompt-sema eslemesi kapali listedir. Ayni sablon hem lab agacinda
# `ATLAS_SABLONLAR/templates`, hem kurulu pakette `templates` altinda bulunabilir.
# `$defs/main` secimi, REVIEWER/CRITIC dallarinin alanlarini MAIN'e zorlamaz.
SEMA_ESLEMELERI = {
    "atlas-review-main.md": (
        (
            "ATLAS_SABLONLAR/templates/REVIEW-PANEL-SCHEMA.json",
            "templates/REVIEW-PANEL-SCHEMA.json",
        ),
        "#/$defs/main",
    ),
}


def yerel_ref_coz(sema, ref):
    if not isinstance(ref, str) or not ref.startswith("#/"):
        raise ValueError(f"yalniz yerel JSON Pointer desteklenir: {ref!r}")
    dugum = sema
    for parca in ref[2:].split("/"):
        parca = parca.replace("~1", "/").replace("~0", "~")
        if not isinstance(dugum, dict) or parca not in dugum:
            raise ValueError(f"cozulemeyen $ref: {ref}")
        dugum = dugum[parca]
    return dugum


def sema_alanlarini_topla(sema, baslangic_ref):
    """Hedef dal ve ulasilabilir alt nesnelerde required/properties birlesimi."""
    zorunlu = set()
    izinli = set()
    gorulen = set()

    def gez(dugum):
        if not isinstance(dugum, dict):
            return
        isaret = id(dugum)
        if isaret in gorulen:
            return
        gorulen.add(isaret)

        if "$ref" in dugum:
            gez(yerel_ref_coz(sema, dugum["$ref"]))
        if "required" in dugum:
            alanlar = dugum["required"]
            if not isinstance(alanlar, list) or not all(isinstance(x, str) for x in alanlar):
                raise ValueError("required string[] degil")
            zorunlu.update(alanlar)
        ozellikler = dugum.get("properties", {})
        if not isinstance(ozellikler, dict):
            raise ValueError("properties nesne degil")
        izinli.update(ozellikler)
        for alt in ozellikler.values():
            gez(alt)
        if "items" in dugum:
            gez(dugum["items"])
        for anahtar in ("allOf", "anyOf", "oneOf"):
            dallar = dugum.get(anahtar, [])
            if not isinstance(dallar, list):
                raise ValueError(f"{anahtar} liste degil")
            for alt in dallar:
                gez(alt)

    gez(yerel_ref_coz(sema, baslangic_ref))
    return zorunlu, izinli


def json_anahtarlarini_topla(deger):
    alanlar = set()
    if isinstance(deger, dict):
        alanlar.update(deger)
        for alt in deger.values():
            alanlar.update(json_anahtarlarini_topla(alt))
    elif isinstance(deger, list):
        for alt in deger:
            alanlar.update(json_anahtarlarini_topla(alt))
    return alanlar


def prompt_sema_kontrol(p, ad, metin):
    esleme = SEMA_ESLEMELERI.get(p.name)
    if esleme is None:
        return
    aday_yollar, baslangic_ref = esleme
    sema_yollari = [KOK / yol for yol in aday_yollar if (KOK / yol).is_file()]
    if len(sema_yollari) != 1:
        hatalar.append(
            f"PL-19 {ad}: hedef sema tekil/okunabilir degil: "
            + ", ".join(aday_yollar)
        )
        return
    try:
        sema = json.loads(sema_yollari[0].read_text(encoding="utf-8"))
        if not isinstance(sema, dict):
            raise ValueError("sema JSON nesnesi degil")
        zorunlu, izinli = sema_alanlarini_topla(sema, baslangic_ref)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        hatalar.append(f"PL-19 {ad}: hedef sema gecersiz: {type(exc).__name__}: {exc}")
        return

    bloklar = JSON_KOD_BLOK.findall(metin)
    prompt_alanlari = set()
    if not bloklar:
        hatalar.append(f"PL-19 {ad}: acik JSON ornegi yok; required alanlar dogrulanamadi")
        return
    for sira, blok in enumerate(bloklar, 1):
        try:
            prompt_json = json.loads(blok)
        except json.JSONDecodeError as exc:
            hatalar.append(f"PL-19 {ad}: JSON ornegi {sira} gecersiz: {exc.msg}")
            continue
        prompt_alanlari.update(json_anahtarlarini_topla(prompt_json))

    eksik = sorted(zorunlu - prompt_alanlari)
    fazla = sorted(prompt_alanlari - izinli)
    if eksik:
        hatalar.append(f"PL-19 {ad}: semanin zorunlu alanlari promptta eksik: {', '.join(eksik)}")
    if fazla:
        uyarilar.append(f"PL-19 {ad}: semada olmayan JSON alanlari: {', '.join(fazla)}")

dosyalar = sorted(glob.glob(str(KOK / "**/.opencode/agent/*.md"), recursive=True)
                  + glob.glob(str(KOK / "**/.opencode/command/*.md"), recursive=True))
if not dosyalar:
    print(f"FAIL PL-00: {dizin} altinda .opencode/agent|command/*.md yok")
    sys.exit(1)

sayim = 0
for f in dosyalar:
    p = pathlib.Path(f)
    ad = os.path.relpath(f, KOK)
    okuma_yolu = p
    if p.is_symlink():
        hedef = pathlib.Path(os.path.realpath(p))
        if not p.exists():
            hatalar.append(f"PL-18 {ad}: KIRIK SYMLINK")
            continue
        try:
            kok_ici = os.path.commonpath([str(KOK), str(hedef)]) == str(KOK)
        except ValueError:
            kok_ici = False
        if not kok_ici:
            hatalar.append(f"PL-04 {ad}: KOK-DISI SYMLINK hedefi: {hedef}")
            continue
        okuma_yolu = hedef
    sayim += 1
    t = okuma_yolu.read_text(errors="ignore")
    komut = "/command/" in f.replace("\\", "/")
    on_madde_eslesmesi = re.search(r"^---\s*\n(.*?)\n---", t, re.S)
    on_madde = on_madde_eslesmesi.group(1) if on_madde_eslesmesi else ""
    devre_disi = re.search(r"^disable:\s*true\s*$", on_madde, re.M) is not None

    # PL-01 / PL-02
    if not t.lstrip().startswith("---"):
        hatalar.append(f"PL-01 {ad}: frontmatter yok")
    elif not re.search(r"^description:\s*\S", t, re.M):
        hatalar.append(f"PL-01 {ad}: 'description' yok")
    m = re.search(r"^mode:\s*(\S+)\s*$", t, re.M)
    if m and m.group(1).strip() not in MODLAR:
        hatalar.append(f"PL-02 {ad}: mode kapali listede degil: {m.group(1)}")

    if devre_disi:
        continue

    # PL-19 prompt-sema alan uyumu
    prompt_sema_kontrol(p, ad, t)

    # PL-09 lens karar vermez
    if LENS.search(p.stem) and KARAR_ALANI.search(t):
        hatalar.append(f"PL-09 {ad}: FAZ1 lensi karar alani tasiyor (verdict/gate_decision) — hakem degil danisman")

    # PL-10 vacuous PASS
    if VACUOUS.search(t):
        hatalar.append(f"PL-10 {ad}: 'kanit GEREKMEZ' muafiyeti — vacuous PASS deligi")

    # PL-11 kalici muafiyet
    for mm in KALICI_MUAF.finditer(t):
        sat = t[:mm.start()].count("\n") + 1
        hatalar.append(f"PL-11 {ad}:{sat}: kalici muafiyet ('her zaman PASS') — kimlik listesi kullanilmali")

    # PL-13 belirsizligi yasaklama
    if ETIKET_YASAK.search(t):
        hatalar.append(f"PL-13 {ad}: belirsizlik etiketini YASAKLIYOR — sidk ilkesinin tersine cevrilmesi")

    # PL-12 belirsizlik cikisi (yalniz denetleyici/uretici ajanlarda beklenir)
    if not komut and not BELIRSIZ.search(t):
        uyarilar.append(f"PL-12 {ad}: belirsizlik cikisi yok (DOGRULANAMADI/CALISTIRILMADI)")

    # PL-14 + PL-16 betik cagrilari
    cagrilar = set(BETIK_CAGRI.findall(t))
    if cagrilar:
        if not EXIT_SOZ.search(t):
            uyarilar.append(f"PL-14 {ad}: betik cagiriyor ama exit kodundan soz etmiyor (fail-open riski)")
        for c in cagrilar:
            aday = list(KOK.glob(f"**/scripts/{c}"))
            if not aday:
                hatalar.append(f"PL-16 {ad}: olmayan betigi cagiriyor: scripts/{c}")

if not SESSIZ:
    for u in uyarilar:
        print(f"UYARI {u}")
for h in hatalar:
    print(f"FAIL {h}")

if hatalar:
    print(f"PROMPT-LINT FAIL — {sayim} dosya, {len(hatalar)} hata, {len(uyarilar)} uyari")
    sys.exit(1)
print(f"PROMPT-LINT PASS — {sayim} prompt dosyasi temiz ({len(uyarilar)} uyari)")
sys.exit(0)
