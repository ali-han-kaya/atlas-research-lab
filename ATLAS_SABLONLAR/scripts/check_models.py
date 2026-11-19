#!/usr/bin/env python3
"""Atlas v5.5.4 Model Denetimi — ajan `model:` satirlarini kataloga karsi dogrular

NEDEN VAR:
Ajan dosyasindaki bir model kimligi katalogdan kalkarsa veya `deprecated`
isaretlenirse opencode o ajani SESSIZCE devre disi birakir; kullanici sebebini
anlamadan "ajan calismiyor" der. `model:` satiri hic yoksa ajan sessizce global
varsayilana duser — baska bir saglayiciya ve baska bir fiyata.

KONTROLLER (fail-closed):
  MOD-01  `model:` satiri var (yoksa UYARI: global varsayilana duser)
  MOD-02  Saglayici yetkili (auth.json ile ayni kume)
  MOD-03  Model katalogda VAR
  MOD-04  `deprecated` degil (opencode bunu otomatik disable eder)
  MOD-05  reasoning=true ve tool_call=true
  MOD-06  '~' takma adi kullanilmiyor (hareketli hedef, yeniden uretilemez)
  MOD-07  Prompt govdesindeki model adi frontmatter ile celismiyor
  MOD-08  Symlink hedefi kirik veya denetim koku disindaysa reddedilir

Ag gerektirmez; yalniz yerel katalog onbellegini okur. Hicbir dosya yazmaz.

Kullanim: python3 scripts/check_models.py [--dizin <yol>] [--sessiz]
"""
import glob, json, os, re, sys, pathlib

KAT = pathlib.Path(os.environ.get("ATLAS_MODEL_KATALOG")
                   or os.path.expanduser("~/.cache/opencode/models.json"))
AUTH = pathlib.Path(os.path.expanduser("~/.local/share/opencode/auth.json"))
SESSIZ = "--sessiz" in sys.argv

dizin = "."
if "--dizin" in sys.argv:
    i = sys.argv.index("--dizin")
    if i + 1 < len(sys.argv):
        dizin = sys.argv[i + 1]

if not KAT.exists():
    print(f"FAIL MOD-00: model katalogu yok ({KAT})")
    print("  ipucu: opencode bir kez calistirilinca onbellek olusur")
    sys.exit(1)
kat = json.loads(KAT.read_text())

# yetkili saglayicilar: auth.json varsa oradan, yoksa guvenli varsayilan
if AUTH.exists():
    try:
        yetkili = set(json.loads(AUTH.read_text()).keys())
    except Exception:
        yetkili = {"openrouter", "opencode-go", "meta"}
else:
    yetkili = {"openrouter", "opencode-go", "meta"}

AILE = ("claude", "opus", "sonnet", "haiku", "deepseek", "glm", "kimi",
        "gemini", "llama", "gpt-oss", "qwen", "grok", "minimax")

hata = []
uyari = []
sayim = 0
kok = pathlib.Path(dizin).resolve()
gorulen_hedefler = set()
dosyalar = sorted(glob.glob(os.path.join(dizin, "**/.opencode/agent/*.md"), recursive=True))
if not dosyalar:
    print(f"FAIL MOD-00: {dizin} altinda .opencode/agent/*.md bulunamadi")
    sys.exit(1)

for f in dosyalar:
    ad = os.path.relpath(f, dizin)
    gercek_yol = pathlib.Path(os.path.realpath(f))
    if os.path.islink(f):
        if not os.path.exists(f):
            hata.append(f"MOD-08 {ad}: KIRIK_SYMLINK -> {gercek_yol}")
            continue
        try:
            kok_ici = os.path.commonpath((str(kok), str(gercek_yol))) == str(kok)
        except ValueError:
            kok_ici = False
        if not kok_ici:
            hata.append(f"MOD-08 {ad}: KOK_DISI_SYMLINK -> {gercek_yol}")
            continue
        if not gercek_yol.is_file():
            hata.append(f"MOD-08 {ad}: SYMLINK_HEDEFI_DOSYA_DEGIL -> {gercek_yol}")
            continue
    if gercek_yol in gorulen_hedefler:
        continue
    gorulen_hedefler.add(gercek_yol)
    txt = gercek_yol.read_text(errors="ignore")
    sayim += 1
    devre_disi = re.search(r"^disable:\s*true\s*$", txt, re.M) is not None
    m = re.search(r"^model:\s*(\S+)\s*$", txt, re.M)
    if not m:
        if not devre_disi:
            uyari.append(f"MOD-01 {ad}: 'model:' satiri yok -> global varsayilana duser")
        continue
    tam = m.group(1)
    if tam.startswith("~") or "/~" in tam:
        hata.append(f"MOD-06 {ad}: '~' takma adi hareketli hedeftir: {tam}")
        continue
    prov, _, mid = tam.partition("/")
    if prov not in yetkili:
        hata.append(f"MOD-02 {ad}: saglayici yetkisiz: {prov} (yetkili: {sorted(yetkili)})")
        continue
    bilgi = kat.get(prov, {}).get("models", {}).get(mid)
    if bilgi is None:
        hata.append(f"MOD-03 {ad}: katalogda YOK: {tam}")
        continue
    if str(bilgi.get("status", "")).lower() == "deprecated":
        hata.append(f"MOD-04 {ad}: DEPRECATED — opencode otomatik disable eder: {tam}")
    if not (bilgi.get("reasoning") and bilgi.get("tool_call")):
        hata.append(f"MOD-05 {ad}: reasoning/tool_call desteklemiyor: {tam}")
    # MOD-07 govde-frontmatter celiskisi
    govde = txt.split("---", 2)[-1].lower()
    fm_aile = {a for a in AILE if a in mid.lower()}
    gv_aile = {a for a in AILE if a in govde}
    celisen = gv_aile - fm_aile - {"gpt-oss"}
    if fm_aile and celisen:
        uyari.append(f"MOD-07 {ad}: govdede baska model ailesi aniliyor: {sorted(celisen)} (frontmatter: {mid})")

if not SESSIZ:
    for u in uyari:
        print(f"UYARI {u}")
for h in hata:
    print(f"FAIL {h}")

if hata:
    print(f"MODEL-DENETIM FAIL — {sayim} ajan, {len(hata)} hata, {len(uyari)} uyari")
    sys.exit(1)
print(f"MODEL-DENETIM PASS — {sayim} ajan dosyasinin tamami katalogda gecerli ({len(uyari)} uyari)")
sys.exit(0)
