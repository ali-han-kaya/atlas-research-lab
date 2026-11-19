#!/usr/bin/env python3
"""Atlas v5.5.4 Source Class Check — B-2 kaynak sinifi denetimi

NEDEN VAR:
  Karsilastirmali din hakeminin ilk itirazi: "Sekina iddiasi Zohar'a mi,
  Scholem'in Zohar okumasina mi dayaniyor?" Aktarma atif bu alanda agir
  kusurdur; kaynağın birincil/ikincil sinifi belirtilmezse iddia havada
  kalir (B-2).

KONTROLLER:
  SRC-01  PROVENANCE tablosunda Kaynak Sinifi sutunu var mi? (yoksa CALISTIRILMADI)
          Ayrica varsa KAYNAK SINIFLANDIRMA tablosundaki sinyal->sinif atamasiyla
          celisen PROVENANCE satirini FAIL eder (yanlis sinif atamasi).
  SRC-02  Her satirda sinif degeri gecerli mi? BIRINCIL|IKINCIL|UCUNCUL|AKTARMA (bos/yanlis P1)
  SRC-03  AKTARMA satirlarinda "asil kaynak gorulmedi" beyanı var mi? (yoksa P1)

  Kaynak Sinifi sutunu PROVENANCE_Template'de 5. sutun (0-bazli 4) olarak
  beklenir; baslik satirinda "Kaynak Sinifi" / "Source Class" gecmelidir.
  Eski 5-sutunlu tablo (sinif sutunu yok) kademeli gecis icin CALISTIRILMADI
  sayilir, FAIL degil — mevcut fikstirleri kirmamak icin.

Kullanim:
  python3 scripts/source_class_check.py
  python3 scripts/source_class_check.py --dosya makale.md
"""
import re, sys, pathlib

MASTER_CANDS = [
    "03-FAZ-3-MASTER-v5.5.md",
    "03-FAZ-3-MASTER-v5.4.md",
    "03-FAZ-3-MASTER-v5.2.md",
    "MASTER.md",
]

hedef = None
if "--dosya" in sys.argv:
    i = sys.argv.index("--dosya")
    if i + 1 < len(sys.argv):
        hedef = pathlib.Path(sys.argv[i + 1])
if hedef is None:
    hedef = next((pathlib.Path(c) for c in MASTER_CANDS if pathlib.Path(c).exists()), None)
if hedef is None or not hedef.exists():
    print("FAIL SRC-00: denetlenecek metin bulunamadi (MASTER yok, --dosya verilmedi)")
    sys.exit(1)

text = hedef.read_text(errors="ignore")
lines = text.splitlines()

# PROVENANCE bolumunu bul ve sonraki ayni/ust seviye baslikta sinirla
prov_heading_idx = None
prov_heading_level = None
for idx, ln in enumerate(lines):
    m = re.match(r"^(##)\s+PROVENANCE(?:\s+Tablosu)?\s*$", ln.strip(), re.I)
    if m:
        prov_heading_idx = idx
        prov_heading_level = len(m.group(1))
        break

if prov_heading_idx is None:
    print("INFO SRC-01: CALISTIRILMADI — PROVENANCE bolumu bulunamadi")
    sys.exit(0)

prov_end_idx = len(lines)
for idx in range(prov_heading_idx + 1, len(lines)):
    m = re.match(r"^(#{1,6})\s+", lines[idx])
    if m and len(m.group(1)) <= prov_heading_level:
        prov_end_idx = idx
        break

# PROVENANCE tablosunu bul: baslik satirinda SCOPE-ID ve Durum gecmeli
# Header tespiti: "SCOPE-ID" ve "Kaynak Sinifi" ayni satirda
header_idx = None
has_class_col = False
for idx in range(prov_heading_idx + 1, prov_end_idx):
    ln = lines[idx]
    if re.search(r"SC(?:OPE)?-ID", ln, re.I) and "Kaynak" in ln and "Durum" in ln:
        if re.search(r"Kaynak\s*S[ıi]n[ıi]f[ıi]|Source\s*Class", ln, re.I):
            has_class_col = True
            header_idx = idx
            break
        # ilk SCOPE-ID/Durum satiri sinif sutunu olmadan da baslik olabilir
        if header_idx is None:
            header_idx = idx

if header_idx is None:
    print("INFO SRC-01: CALISTIRILMADI — PROVENANCE tablosu bulunamadi (baslik satiri yok)")
    sys.exit(0)

if not has_class_col:
    print("INFO SRC-01: CALISTIRILMADI — PROVENANCE tablosunda 'Kaynak Sinifi' sutunu yok (eski 5-sutunlu tablo; kademeli gecis)")
    print("  Beklenen baslik: | SCOPE-ID | Bolum | Kaynak | Satir Referansi | Kaynak Sinifi | Durum |")
    sys.exit(0)

# Sutun indeksini basliktan cikar
header = lines[header_idx]
cols_h = [c.strip() for c in header.strip().strip("|").split("|")]
sinif_col = None
for i, h in enumerate(cols_h):
    if re.search(r"Kaynak\s*S[ıi]n[ıi]f[ıi]|Source\s*Class", h, re.I):
        sinif_col = i
        break

if sinif_col is None:
    print("FAIL SRC-01: baslikta 'Kaynak Sinifi' bulundu ama sutun indeksi cikarilamadi")
    sys.exit(1)

GECERLI = {"BIRINCIL", "BIRINÇIL", "IKINCIL", "İKİNCİL", "UCUNCUL", "ÜÇÜNCÜL", "AKTARMA"}
# TR normalizasyon
TR = str.maketrans("İIŞĞÜÖÇı", "IISGUOCI")
def norm(s):
    return str(s or "").strip().upper().translate(TR).replace("-", "_").replace(" ", "_")

# SRC-01 tablo capraz kontrolu: belgede KAYNAK SINIFLANDIRMA tablosu varsa
# (Sinyal -> Sinif), PROVENANCE satirindaki sinif bu tabloyla celisemez.
# Tablo yoksa eski davranis aynen korunur; bu bir geriye donuk uyum yoludur.
sinif_tablosu = {}
for _i, _ln in enumerate(lines):
    if not re.match(r"^#{1,6}\s+KAYNAK\s+SINIFLANDIRMA(?:\s+TABLOSU)?\s*$", _ln.strip(), re.I):
        continue
    _baslik = None
    for _j in range(_i + 1, len(lines)):
        if re.match(r"^#{1,6}\s+", lines[_j]):
            break
        if not lines[_j].strip().startswith("|"):
            continue
        _kol = [c.strip() for c in lines[_j].strip().strip("|").split("|")]
        _low = [c.lower() for c in _kol]
        if _baslik is None and "sinyal" in _low and ("sınıf" in _low or "sinif" in _low):
            _baslik = _low.index("sinyal")
            _sinif_i = _low.index("sınıf") if "sınıf" in _low else _low.index("sinif")
            continue
        if _baslik is None:
            continue
        if len(_kol) <= max(_baslik, _sinif_i):
            continue
        if re.match(r"^\s*-+", _kol[0]):
            continue
        _sinyal = _kol[_baslik].strip().lower()
        _sinif = norm(_kol[_sinif_i])
        if _sinyal and _sinif in GECERLI:
            sinif_tablosu[_sinyal] = _sinif
    break

kaynak_col = next((i for i, h in enumerate(cols_h) if re.fullmatch(r"Kaynak", h, re.I)), None)

fail = False
satir_say = 0
for idx in range(header_idx + 2, prov_end_idx):
    ln = lines[idx]
    if not ln.strip().startswith("|"):
        continue
    if re.match(r"^\|\s*-+", ln):
        continue
    cols = [c.strip() for c in ln.strip().strip("|").split("|")]
    if len(cols) <= sinif_col:
        continue
    m = re.search(r"SC-\d{3}", cols[0])
    if not m:
        continue
    sid = m.group(0)
    satir_say += 1
    ham = cols[sinif_col]
    pr = norm(ham)
    if pr not in GECERLI:
        print(f"FAIL SRC-02: {sid} Kaynak Sinifi bos/yanlis: '{ham}' — beklenen BIRINCIL|IKINCIL|UCUNCUL|AKTARMA")
        fail = True
        continue
    # SRC-01: sinyal tablosu varsa yanlis sinif atamasini yakala
    tablo_ihlali = False
    if sinif_tablosu and kaynak_col is not None and len(cols) > kaynak_col:
        kaynak = cols[kaynak_col].strip().lower()
        for sinyal, beklenen in sinif_tablosu.items():
            if sinyal in kaynak:
                if pr != beklenen:
                    print(f"FAIL SRC-01: {sid} Kaynak '{cols[kaynak_col]}' siniflandirma "
                          f"tablosunda {beklenen}, PROVENANCE'ta {pr} — yanlis sinif atamasi")
                    fail = True
                    tablo_ihlali = True
                break
    if tablo_ihlali:
        continue
    # normalize AKTARMA icin beyan kontrolu
    if pr == "AKTARMA":
        # ayni satirda veya tablonun hemen sonrasindaki 2 satir icinde beyan ara
        baglam = " ".join(cols) + " " + " ".join(lines[idx+1:idx+3])
        if "asil kaynak gorulmedi" not in baglam.lower() and "asıl kaynak görülmedi" not in baglam.lower():
            print(f"FAIL SRC-03: {sid} AKTARMA ama 'asil kaynak gorulmedi' beyani yok")
            fail = True
            continue
    print(f"PASS {sid}: Kaynak Sinifi={ham}")

if satir_say == 0:
    print("INFO SRC-01: CALISTIRILMADI — PROVENANCE tablosunda SC satiri yok")
    sys.exit(0)

if fail:
    print(f"SOURCE-CLASS-CHECK FAIL — {satir_say} satirdan en az biri P1")
    sys.exit(1)

print(f"SOURCE-CLASS-CHECK PASS — {satir_say} satir Kaynak Sinifi gecerli")
sys.exit(0)
