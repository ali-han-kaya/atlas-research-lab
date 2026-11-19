#!/usr/bin/env python3
"""perm_lint — opencode `permission` bloklarinin makine denetimi

NEDEN VAR:
OLCUM-01 (docs/OLCUM-01-IZIN-GLOB.md) su uc seyi olctu:
  1. opencode globlari POSIX glob DEGIL. `*` ile `**` ayni sey; ikisi de `/` asar.
  2. `**/X/**` kok dizini KORUMAZ. Canli kosuda gizli dosya sizdi.
  3. Karar `findLast` ile verilir: en son eslesen kural kazanir, en ozgul degil.
Bu ucu bilmeden yazilan izin bloklari SESSIZCE etkisiz kalir. Labin 10 ajan
dosyasinin 10'unda `"*"` haritanin sonundaydi; onundeki her deny olu kuraldi.
Hicbir test bunu yakalamiyordu. Bu betik onu yakalar.

Betik kalip METNINE bakmaz. Ikiliden birebir cikarilmis eslestiriciyi ve
findLast karar fonksiyonunu tasir, her kural icin ORNEK YOL uretir ve kuralin
kendi ornek yolunda gercekten kazanip kazanmadigini OLCER.

KONTROLLER
  PERM-01  Olu kural yok: her kural kendi ornek yolunda kendi kararini kazanir  [P0]
           (pratikte: `"*"` haritanin ILK satiri olmali)
  PERM-02  Cift kalip: her deny hem kok hem ic ice yolu kapsar (IK-1)           [P0]
  PERM-03  `**/*.uzanti` kalibi kok seviyeyi kacirir (IK-4)                     [P1]
  PERM-04  ACILMAZ cizgesi read'te deny ise edit'te de deny (tek yonlu; politika)  [P0]
  PERM-05  Yalniz `{"*": "deny"}` iceren harita dize bicimiyle yazilmali (IK-5) [P2]
  PERM-06  Kritik sinir `ask`e birakilmamis (IK-6: --auto ask'i allow yapar)    [P1]
  PERM-07  Yol kalibi mutlak degil, worktree'ye goreli (IK-7)                   [P1]
  PERM-08  `bash` deny'i tek basina sinir degildir — asilabilir (IK-8)          [P1]

IK-8 gerekcesi (OLCUM-01 §8, canli kanit): `rm *` deny'i `/bin/rm` ile,
`git commit*` deny'i `sh -c "git commit ..."` ile asildi. Bash deny'i
danismandir, kapi degildir.

Kullanim:
  python3 perm_lint.py [--dizin <yol>] [--sessiz] [--json]
Cikis: 0 = temiz, 1 = en az bir P0
"""
import glob, json, os, pathlib, re, sys
from collections import OrderedDict

# ---------------------------------------------------------------- eslestirici
# opencode 1.18.21 ikilisinden BIREBIR cikarilmis Wildcard.match portu:
#   o.replace(/[.+^${}()|[\]\\]/g,"\\$&").replace(/\*/g,".*").replace(/\?/g,".")
#   if (l.endsWith(" .*")) l = l.slice(0,-3)+"( .*)?"
#   new RegExp("^"+l+"$","s").test(e)
_KACIS = re.compile(r"([.+^${}()|\[\]\\])")

def esles(deger: str, kalip: str) -> bool:
    deger = (deger or "").replace("\\", "/")
    kalip = (kalip or "").replace("\\", "/")
    r = _KACIS.sub(r"\\\1", kalip).replace("*", ".*").replace("?", ".")
    if r.endswith(" .*"):
        r = r[:-3] + "( .*)?"
    return re.match("^" + r + "$", deger, re.DOTALL) is not None

def degerlendir(izin, deger, kurallar):
    """opencode Permission.evaluate portu: findLast, eslesme yoksa 'ask'."""
    kazanan = None
    for k in kurallar:
        if esles(izin, k["permission"]) and esles(deger, k["pattern"]):
            kazanan = k
    return kazanan or {"permission": izin, "pattern": "*", "action": "ask"}

# ------------------------------------------------------------ frontmatter ayr
def frontmatter_izin(metin):
    """permission: blogunu SIRAYI KORUYARAK cikarir. PyYAML gerektirmez."""
    if not metin.lstrip().startswith("---"):
        return None
    parcalar = metin.split("---", 2)
    if len(parcalar) < 3:
        return None
    fm = parcalar[1].split("\n")
    try:
        bas = next(i for i, l in enumerate(fm) if re.match(r"^permission:\s*$", l))
    except StopIteration:
        return None
    blok = OrderedDict()
    aktif = None
    for satir in fm[bas + 1:]:
        if satir.strip() == "" or satir.lstrip().startswith("#"):
            continue
        if not satir.startswith(" "):          # frontmatter'da yeni ust anahtar
            break
        m2 = re.match(r"^  (\S[^:]*):\s*(\S.*)?$", satir)
        m4 = re.match(r"^    (\S.*?):\s*(\S.*)$", satir)
        if m2:
            anahtar, deger = m2.group(1).strip('"\''), (m2.group(2) or "").strip()
            if deger:                           # dize bicimi:  bash: deny
                blok[anahtar] = deger
                aktif = None
            else:                               # harita bicimi: bash:
                blok[anahtar] = OrderedDict()
                aktif = anahtar
        elif m4 and aktif is not None:
            k, v = m4.group(1).strip().strip('"\''), m4.group(2).strip()
            blok[aktif][k] = v
    return blok or None

def json_izin(yol):
    """opencode.json icindeki agent.<ad>.permission bloklarini sirayi koruyarak alir."""
    try:
        d = json.load(open(yol, encoding="utf-8"), object_pairs_hook=OrderedDict)
    except Exception:
        return {}
    cikti = {}
    for ad, cfg in (d.get("agent") or {}).items():
        if isinstance(cfg, dict) and cfg.get("permission"):
            cikti[ad] = cfg["permission"]
    return cikti

# --------------------------------------------------------------- yardimcilar
def duzlestir(blok):
    """fromConfig portu: sirali {izin: kural} -> [{permission,pattern,action}]"""
    out = []
    for anahtar, deger in blok.items():
        if isinstance(deger, str):
            out.append({"permission": anahtar, "pattern": "*", "action": deger})
        else:
            for kalip, eylem in deger.items():
                out.append({"permission": anahtar, "pattern": kalip, "action": eylem})
    return out

def ornek_yol(kalip):
    """Kalibin kendi harflerinden bir ornek yol uretir: yahuditurk/** -> yahuditurk/xx"""
    cekirdek = kalip[3:] if kalip.startswith("**/") else kalip
    return cekirdek.replace("*", "x").replace("?", "x") or "x"

YOL_KALIBI = re.compile(r"[/.]")

# --------------------------------------------------------------------- girdi
SESSIZ = "--sessiz" in sys.argv
JSON_CIK = "--json" in sys.argv
dizin = "."
if "--dizin" in sys.argv:
    i = sys.argv.index("--dizin")
    if i + 1 < len(sys.argv):
        dizin = sys.argv[i + 1]
KOK = pathlib.Path(dizin).resolve()

# Kirmizi cizgiler IKI SINIF (AI_CALISMA_SISTEMI / devir §5):
#   ACILMAZ      : okunamaz -> okunamayan sey YAZILAMAZ da. read-deny => edit-deny ZORUNLU.
#   DEGISTIRILMEZ: yazilamaz ama OKUNMASI GEREKIR (ATLAS sablonlari, DENEME regresyon dersi).
#                  edit-deny => read-deny ZORUNLU DEGIL; tersini dayatmak labi kirar.
ACILMAZ = ["yahuditurk", "portfolyo", "TRUTH_MAKALE"]
DEGISTIRILMEZ = ["ATLAS", "toolkit", "isimlendir", "DENEME"]
KIRMIZI_CIZGILER = ACILMAZ + DEGISTIRILMEZ
YOL_IZINLERI = {"read", "edit", "write", "external_directory"}

hatalar, uyarilar = [], []
kaynaklar = []

for f in sorted(glob.glob(str(KOK / "**/.opencode/agent/*.md"), recursive=True)):
    p = pathlib.Path(f)
    if p.is_symlink() and not p.exists():
        hatalar.append(f"PERM-00 {os.path.relpath(f, KOK)}: KIRIK SYMLINK")
        continue
    blok = frontmatter_izin(p.read_text(errors="ignore"))
    if blok:
        kaynaklar.append((os.path.relpath(f, KOK), blok))

for f in sorted(glob.glob(str(KOK / "**/opencode.json"), recursive=True)):
    for ad, blok in json_izin(f).items():
        kaynaklar.append((f"{os.path.relpath(f, KOK)}#agent.{ad}", blok))

if not kaynaklar:
    print(f"FAIL PERM-00: {dizin} altinda permission blogu tasiyan ajan bulunamadi")
    sys.exit(1)

for ad, blok in kaynaklar:
    kurallar = duzlestir(blok)
    deny_kaliplari = {}   # izin -> [kalip]

    for anahtar, deger in blok.items():
        haritami = not isinstance(deger, str)
        girdiler = list(deger.items()) if haritami else [("*", deger)]

        # PERM-05: yalniz {"*": "deny"} iceren harita
        if haritami and len(girdiler) == 1 and girdiler[0][0] == "*" and girdiler[0][1] == "deny":
            uyarilar.append(f"PERM-05 {ad} [{anahtar}]: yalniz \"*\": deny iceriyor — "
                            f"dize bicimi (`{anahtar}: deny`) yazilmali, arac tool listesinden duser")

        for kalip, eylem in girdiler:
            # PERM-01 olu kural: kendi ornek yolunda kendi karari kazanmali
            ornek = ornek_yol(kalip)
            sonuc = degerlendir(anahtar, ornek, kurallar)
            if sonuc["action"] != eylem:
                hatalar.append(
                    f"PERM-01 {ad} [{anahtar}] \"{kalip}\": {eylem} OLU KURAL — "
                    f"ornek yol '{ornek}' uzerinde kazanan \"{sonuc['pattern']}\": {sonuc['action']}. "
                    f"Cozum: \"*\" satirini haritanin BASINA al (karar findLast ile verilir)")

            # PERM-06 kritik sinir ask'e birakilmis mi
            if eylem == "ask" and any(c.lower() in kalip.lower() for c in KIRMIZI_CIZGILER):
                uyarilar.append(f"PERM-06 {ad} [{anahtar}] \"{kalip}\": kirmizi cizge 'ask' yazilmis — "
                                f"--auto bayragi ask'i allow yapar; deny yazilmali")

            # PERM-07 mutlak yol
            if anahtar in YOL_IZINLERI and kalip.startswith("/") and anahtar != "external_directory":
                uyarilar.append(f"PERM-07 {ad} [{anahtar}] \"{kalip}\": mutlak yol — "
                                f"kaliplar worktree'ye gorelidir; worktree disi icin external_directory kullan")

            if eylem == "deny":
                deny_kaliplari.setdefault(anahtar, []).append(kalip)

                # PERM-03 **/*.uzanti kok seviyeyi kacirir
                if re.match(r"^\*\*/\*?\.[A-Za-z0-9]+$", kalip):
                    uyarilar.append(f"PERM-03 {ad} [{anahtar}] \"{kalip}\": kok seviyeyi kacirir — "
                                    f"uzanti kuralinda `**/` kullanma, \"{kalip[3:]}\" yeter")

    # PERM-02 cift kalip: her deny hem kok hem ic ice yolu kapsamali
    for anahtar, kaliplar in deny_kaliplari.items():
        if anahtar not in YOL_IZINLERI:
            continue
        anahtar_denyleri = [k for k in kurallar if k["permission"] == anahtar and k["action"] == "deny"]
        for kalip in kaliplar:
            if not YOL_KALIBI.search(kalip):
                continue
            kok = ornek_yol(kalip)
            ic = "alt/" + kok
            for sonda, etiket in ((kok, "kok seviye"), (ic, "ic ice")):
                if not any(esles(sonda, k["pattern"]) for k in anahtar_denyleri):
                    esdes = kalip[3:] if kalip.startswith("**/") else "**/" + kalip
                    hatalar.append(
                        f"PERM-02 {ad} [{anahtar}] \"{kalip}\": {etiket} yol '{sonda}' KORUNMUYOR — "
                        f"esdes kalip eksik: \"{esdes}\" (IK-1: her koruma cift kalipla yazilir)")
                    break

    # PERM-04 ACILMAZ cizgesi read'te deny ise edit'te de deny olmali (tek yonlu)
    read_d = " ".join(deny_kaliplari.get("read", []))
    edit_d = " ".join(deny_kaliplari.get("edit", []))
    for cizgi in ACILMAZ:
        if cizgi.lower() in read_d.lower() and cizgi.lower() not in edit_d.lower():
            hatalar.append(f"PERM-04 {ad}: '{cizgi}' ACILMAZ cizgesi read altinda deny ama "
                           f"edit altinda DEGIL — okunamayan sey yazilamaz da olmali")

    # PERM-08 bash deny'i tek basina sinir degil
    if deny_kaliplari.get("bash"):
        uyarilar.append(f"PERM-08 {ad} [bash]: {len(deny_kaliplari['bash'])} deny kalibi var — "
                        f"bash deny'i ASILABILIR (`/bin/rm`, `sh -c \"...\"`; OLCUM-01 §8 canli kanit). "
                        f"Tek sinir olarak guvenilmemeli")

if JSON_CIK:
    print(json.dumps({"kaynak_sayisi": len(kaynaklar), "hatalar": hatalar, "uyarilar": uyarilar},
                     ensure_ascii=False, indent=2))
else:
    if not SESSIZ:
        for u in uyarilar:
            print(f"UYARI {u}")
    for h in hatalar:
        print(f"FAIL {h}")

if hatalar:
    if not JSON_CIK:
        print(f"PERM-LINT FAIL — {len(kaynaklar)} izin blogu, {len(hatalar)} hata, {len(uyarilar)} uyari")
    sys.exit(1)
if not JSON_CIK:
    print(f"PERM-LINT PASS — {len(kaynaklar)} izin blogu temiz ({len(uyarilar)} uyari)")
sys.exit(0)
