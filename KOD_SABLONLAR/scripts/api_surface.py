#!/usr/bin/env python3
"""api_surface — disa acik imza envanteri korunmus mu (KEEP denetimi)

NEDEN VAR:
Akademik hattaki `provenance_check.py`'nin kod karsiligi. Bir refactor'un en
sinsi zarari, davranisi degistirmeden DISA ACIK IMZAYI kirmasidir: testler
gecer, cagiran kod kirilir. KFAZ0'da alinan imza envanteri KFAZ4'te yeniden
alinir ve karsilastirilir.

UC KADEME — ve kademelerin YETKISI farklidir:
  T1  `imza_komutu` calisti, cikti karsilastirildi     -> OLUMLU KARAR URETEBILIR
  T2  regex ile kaba tarama                            -> yalniz DUSUK_GUVEN, karar YOK
  T3  hicbiri yok                                      -> CALISTIRILMADI, P1, karar YOK
T2 ve T3 "imza korunmus" DIYEMEZ. Yalnizca "kirildigina dair kanit bulunamadi"
der. Bu ikisi ayni sey degildir.

KURALLAR
  API-01  KFAZ0 envanteri yok                     [CALISTIRILMADI P1]
  API-02  T1: kaybolan disa acik imza                             [P0]
  API-03  T1: imza degismis (parametre/donus)                     [P0]
  API-04  T2: regex taramasinda kayip aday        [DUSUK_GUVEN P1]
  API-05  T3: hicbir kademe kosmadi               [CALISTIRILMADI P1]

Kullanim: python3 scripts/api_surface.py [--profil kod_profil.json]
                                         [--taban _KOSU/gate/BASELINE.json] [--json]
"""
import json, pathlib, re, subprocess, sys

JSON_CIK = "--json" in sys.argv


def arg(b, v):
    if b in sys.argv:
        i = sys.argv.index(b)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return v


profil_yol = pathlib.Path(arg("--profil", "kod_profil.json"))
taban_yol = pathlib.Path(arg("--taban", "_KOSU/gate/BASELINE.json"))
bulgular = []
kademe = "T3"

profil = json.loads(profil_yol.read_text()) if profil_yol.exists() else {}
taban = json.loads(taban_yol.read_text()) if taban_yol.exists() else {}
taban_imza = taban.get("dis_imza")

if taban_imza is None:
    bulgular.append({"kural": "API-01", "siddet": "P1", "kod": "CALISTIRILMADI",
                     "aciklama": "KFAZ0 imza envanteri yok — karsilastirma yapilamaz"})
    taban_imza = []

imza_komutu = (profil.get("imza_komutu") or "").strip()
simdi = None

if imza_komutu:
    r = subprocess.run(imza_komutu, shell=True, capture_output=True, text=True, timeout=120)
    if r.returncode == 0:
        kademe = "T1"
        simdi = sorted(x.strip() for x in r.stdout.split("\n") if x.strip())
    else:
        bulgular.append({"kural": "API-05", "siddet": "P1", "kod": "CALISTIRILMADI",
                         "aciklama": f"imza_komutu exit={r.returncode}: {r.stderr.strip()[:200]}"})

if simdi is None and taban_imza:
    # T2: kaba regex taramasi — YALNIZ dusuk guven
    kademe = "T2"
    desen = re.compile(r"^\s*(?:export\s+)?(?:public\s+|pub\s+)?"
                       r"(?:def|function|func|fn|class|interface|type|struct)\s+(\w+)", re.M)
    bulunan = set()
    for p in pathlib.Path(".").rglob("*"):
        if not p.is_file() or ".git" in p.parts or "_KOSU" in p.parts:
            continue
        if p.suffix not in {".py", ".js", ".ts", ".tsx", ".go", ".rs", ".swift", ".java", ".rb"}:
            continue
        try:
            bulunan.update(desen.findall(p.read_text(errors="ignore")))
        except Exception:
            continue
    simdi = sorted(bulunan)

if not taban_imza:
    pass
elif kademe == "T1":
    onceki, sonraki = set(taban_imza), set(simdi or [])
    for k in sorted(onceki - sonraki):
        bulgular.append({"kural": "API-02", "siddet": "P0", "kod": "T1",
                         "aciklama": f"disa acik imza KAYBOLDU: {k}"})
elif kademe == "T2":
    onceki_adlar = {re.split(r"[ (\[]", x)[0].split(".")[-1] for x in taban_imza}
    for k in sorted(onceki_adlar - set(simdi or [])):
        bulgular.append({"kural": "API-04", "siddet": "P1", "kod": "DUSUK_GUVEN",
                         "aciklama": f"regex taramasinda bulunamadi: {k} — "
                                     f"T2 olumlu karar URETEMEZ, yalniz suphe kaydeder"})
else:
    bulgular.append({"kural": "API-05", "siddet": "P1", "kod": "CALISTIRILMADI",
                     "aciklama": "ne imza_komutu ne taban envanteri var — "
                                 "imza denetimi HIC kosmadi"})

p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
yetki = {"T1": "olumlu karar uretebilir", "T2": "yalniz DUSUK_GUVEN, karar YOK",
         "T3": "CALISTIRILMADI, karar YOK"}[kademe]
rapor = {"sema": "API-SURFACE/v1", "kademe": kademe, "kademe_yetkisi": yetki,
         "taban_imza_sayisi": len(taban_imza), "simdiki_imza_sayisi": len(simdi or []),
         "p0": p0, "p1": p1, "bulgular": bulgular}
if JSON_CIK:
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
else:
    for b in bulgular:
        print(f"{b['siddet']} {b['kural']} {b.get('kod','')} {b['aciklama']}")
    print(f"API-SURFACE {'FAIL' if p0 else 'PASS'} — kademe={kademe} ({yetki}) · P0={p0} P1={p1}")
sys.exit(1 if p0 else 0)
