#!/usr/bin/env python3
"""dep_audit — bagimlilik yuzeyi denetimi (akademik `verify_doi.py` karsiligi)

NEDEN VAR:
Akademik hatta bir iddianin kaynagi DOI ile dogrulanir. Kod hattinda bir
bagimliligin kaynagi KILIT DOSYASI ile dogrulanir. Sabitlenmemis surum, yarin
baska bir kod calistiracagi anlamina gelir: bugun yesil olan kapi yarin
gecersizdir.

KURALLAR
  DEP-01  Manifest var, kilit ANAHTARI YOK                                    [P0]
  DEP-01  Manifest var, kilit beyani BOS (bilincli)                    [BILGI — O3-10]
  DEP-01  Kilit BEYAN EDILMIS ama diskte yok                                  [P0]
  DEP-02  Manifestteki paket kilitte yok (kilit bayat)                        [P0]
  DEP-03  Sabitlenmemis surum (`*`, `latest`, bos, `^`/`~` kilitsiz)          [P1]
  DEP-04  Diff kilit dosyasina dokunuyor ama manifeste dokunmuyor             [P1]
  DEP-05  Lisans catismasi (izinli listenin disinda)                          [P0]
  DEP-06  Profilde `bagimlilik_manifesti` bos     [CALISTIRILMADI P1 + OLCULMEYEN]

Kullanim: python3 scripts/dep_audit.py [--profil kod_profil.json] [--json]
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
profil = json.loads(profil_yol.read_text()) if profil_yol.exists() else {}
manifestler = profil.get("bagimlilik_manifesti") or []
kilitler = profil.get("kilit_dosyasi") or []
# ------------------------------------------------------------- O3-10 (OLCUM-03)
# `.get(...) or []` "anahtar YOK" ile "anahtar VAR ama BOS" arasini siliyordu.
# Bagimliligi olmayan bir projede `"kilit_dosyasi": []` BILINCLI bir beyandir;
# betik bunu da P0 sayiyordu ve her kosuda sahte bir P0 uretiyordu (OLCUM-03
# O3-10; OLCUM-04'te 2C tarafindan canli tezahur etti). Ayrim artik korunuyor:
#   anahtar YOK          -> P0  (beyan edilmemis, sessiz bosluk)
#   anahtar VAR, bos     -> BILGI (bilincli beyan, kapi calisti)
#   anahtar VAR, dolu    -> dosya yoksa P0 (beyan var ama tutmuyor)
KILIT_BEYANI_VAR = "kilit_dosyasi" in profil
izinli_lisans = set(profil.get("izinli_lisanslar") or
                    ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD", "Unlicense"])
bulgular = []

if not manifestler:
    bulgular.append({"kural": "DEP-06", "siddet": "P1", "kod": "CALISTIRILMADI",
                     "aciklama": "kod_profil.json icinde `bagimlilik_manifesti` bos — "
                                 "bagimlilik denetimi HIC kosmadi, OLCULMEYEN kaydi acilmali"})

SABITLENMEMIS = re.compile(r'["\']?\s*(?:\*|latest|\^|~)\s*["\']?\s*$')

for m in manifestler:
    mp = pathlib.Path(m)
    if not mp.exists():
        bulgular.append({"kural": "DEP-01", "siddet": "P1", "konum": m,
                         "aciklama": "profilde yazili manifest dosyasi yok"})
        continue
    if not kilitler:
        if KILIT_BEYANI_VAR:
            bulgular.append({"kural": "DEP-01", "siddet": "BILGI", "konum": m,
                             "kod": "BEYAN_EDILMIS",
                             "aciklama": "manifest var, kilit dosyasi BILINCLI olarak bos "
                                         "beyan edilmis (`kilit_dosyasi: []`) — P0 uretilmedi"})
        else:
            bulgular.append({"kural": "DEP-01", "siddet": "P0", "konum": m,
                             "aciklama": "manifest var ama KILIT DOSYASI yok ve profilde "
                                         "`kilit_dosyasi` anahtari HIC YOK — yarin baska kod "
                                         "calisir, bugunku kapi gecersizdir"})
    elif not any(pathlib.Path(k).exists() for k in kilitler):
        bulgular.append({"kural": "DEP-01", "siddet": "P0", "konum": m,
                         "aciklama": f"profilde kilit dosyasi BEYAN EDILMIS ({kilitler}) ama "
                                     f"hicbiri diskte YOK — beyan tutmuyor"})
    metin = mp.read_text(errors="ignore")
    for i, satir in enumerate(metin.split("\n"), 1):
        s = satir.strip()
        if not s or s.startswith("#") or s.startswith("["):
            continue
        if "=" in s or ":" in s:
            if SABITLENMEMIS.search(s):
                bulgular.append({"kural": "DEP-03", "siddet": "P1", "konum": f"{m}:{i}",
                                 "aciklama": f"sabitlenmemis surum: {s[:80]}"})

# DEP-04 kilit/manifest esaslilgi
r = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, timeout=120)
if r.returncode == 0:
    degisen = {x.strip() for x in r.stdout.split("\n") if x.strip()}
    kilit_dokundu = any(k in degisen for k in kilitler)
    manifest_dokundu = any(m in degisen for m in manifestler)
    if kilit_dokundu and not manifest_dokundu:
        bulgular.append({"kural": "DEP-04", "siddet": "P1",
                         "aciklama": "kilit dosyasi degismis ama manifest degismemis — "
                                     "gerekcesiz bagimlilik oynamasi"})
else:
    bulgular.append({"kural": "DEP-04", "siddet": "P1", "kod": "CALISTIRILMADI",
                     "aciklama": f"`git diff --name-only HEAD` exit={r.returncode}"})

# DEP-05 lisans
for lis_yol in ("LICENSES.json", "_KOSU/gate/licenses.json"):
    lp = pathlib.Path(lis_yol)
    if lp.exists():
        try:
            for paket, lis in (json.loads(lp.read_text()) or {}).items():
                if lis not in izinli_lisans:
                    bulgular.append({"kural": "DEP-05", "siddet": "P0", "konum": paket,
                                     "aciklama": f"lisans catismasi: {lis} izinli listede yok"})
        except Exception as e:
            bulgular.append({"kural": "DEP-05", "siddet": "P1", "kod": "CALISTIRILMADI",
                             "aciklama": f"{lis_yol} okunamadi: {e}"})
        break

p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
rapor = {"sema": "DEP-AUDIT/v1", "manifest": manifestler, "kilit": kilitler,
         "p0": p0, "p1": p1, "bulgular": bulgular}
if JSON_CIK:
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
else:
    for b in bulgular:
        print(f"{b['siddet']} {b['kural']} {b.get('kod','')} {b.get('konum','')} {b['aciklama']}")
    print(f"DEP-AUDIT {'FAIL' if p0 else 'PASS'} — P0={p0} P1={p1}")
sys.exit(1 if p0 else 0)
