#!/usr/bin/env python3
"""Atlas v5.5.4 Provenance Check — CHK-01, CHK-02, CHK-05 (sikilastirilmis)

ZORUNLU SCOPE-ID'lerin MASTER'da GERCEK BOLUM (baslik) olarak olup olmadigini,
PROVENANCE tablosunda "kapsiyor" durumuyla yer alip almadigini ve baslik
benzersizligini kontrol eder.

Onceki surumden farklar:
- CHK-01: ID'nin metnin herhangi bir yerinde gecmesi YETMEZ; bir markdown
  basligina (# / ## / ###) dahil olmasi gerekir.
- ZORUNLU satirlari SADECE tablo-sutunu formatinda (| ... | ZORUNLU | ...)
  eslesir; "degil ZORUNLU" gibi serbest metin yanlis pozitif URETMEZ.
- CHK-02: PROVENANCE tablosu satir satir ayristirilir; her ZORUNLU ID icin
  tabloda bir satir VE durumun "kapsiyor" (veya DEC-027 kapsaminda
  [UNVERIFIED]) olmasi gerekir. Sadece "PROVENANCE" kelimesinin varligi
  YETMEZ.
- B-9 (lab v1.7.27): Ingilizce koşuda durum token'lari da kabul edilir —
  makine sozlugu: kapsiyor|COVERED → OK · unverified|UNVERIFIED → OK
  (DEC-027) · MISSING/kapsamiyor → FAIL. Durum alani buyuk/kucuk harf
  duyarsizdir.
"""
import re, pathlib, sys

MASTER_CANDS = [
    "03-FAZ-3-MASTER-v5.5.md",
    "03-FAZ-3-MASTER-v5.4.md",
    "03-FAZ-3-MASTER-v5.2.md",
    "MASTER.md",
]
SCOPE = pathlib.Path("00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md")

if not SCOPE.exists():
    print("FAIL: SCOPE-CONTRACT yok")
    sys.exit(1)

master = None
for c in MASTER_CANDS:
    if pathlib.Path(c).exists():
        master = pathlib.Path(c)
        break

if not master:
    print("FAIL: MASTER yok")
    sys.exit(1)

st = SCOPE.read_text(errors="ignore")
mt = master.read_text(errors="ignore")

overall_fail = False

# --- ZORUNLU SC-ID'leri SADECE tablo-sutunu formatinda cikar ---
# Beklenen format: | SC-XXX | Baslik | ZORUNLU | Kaynak | Gerekce |
zor = []
for line in st.splitlines():
    if not line.strip().startswith("|"):
        continue
    cols = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cols) < 3:
        continue
    id_match = re.search(r"SC-\d{3}", cols[0])
    if not id_match:
        continue
    # ZORUNLU herhangi bir sutunda TAM esdeger olarak geciyor mu?
    if any(c.upper() == "ZORUNLU" for c in cols):
        zor.append(id_match.group(0))

if not zor:
    # VACUOUS PASS KAPALI (v5.5.3): zorunlu liste bos ise CHK-01/02 anlamsizca
    # PASS verirdi. Bos liste artik FAIL nedenidir; sessiz yesil kosu yoktur.
    print("FAIL CHK-00: SCOPE-CONTRACT'ta tablo-sutunu formatinda ZORUNLU SC-ID bulunamadi")
    print("  Beklenen format: | SC-XXX | Baslik | ZORUNLU | Kaynak | Gerekce |")
    print("  Bos zorunlu liste ile CHK-01/CHK-02 anlamsiz PASS verirdi; kosu durduruldu.")
    sys.exit(1)

# --- CHK-01: her ZORUNLU ID bir MARKDOWN BASLIGINDA var mi? ---
heading_ids = set()
for line in mt.splitlines():
    m = re.match(r"^#{1,6}\s+(?:\*\*(SC-\d{3})\*\*|(SC-\d{3}))(?=\s|$)", line)
    if m:
        heading_ids.add(m.group(1) or m.group(2))
missing_headings = [s for s in zor if s not in heading_ids]
if missing_headings:
    print(f"FAIL CHK-01: {len(zor)} zorunlu, {len(missing_headings)} basliksiz {missing_headings}")
    overall_fail = True
else:
    print(f"PASS CHK-01: {len(zor)} zorunlu SCOPE-ID MASTER'da baslik olarak var")

# --- Yalniz PROVENANCE bolumundeki taninmis tabloyu ayristir ---
mt_lines = mt.splitlines()
prov_heading_idx = None
prov_heading_level = None
for idx, line in enumerate(mt_lines):
    m = re.match(r"^(##)\s+PROVENANCE(?:\s+Tablosu)?\s*$", line.strip(), re.I)
    if m:
        prov_heading_idx = idx
        prov_heading_level = len(m.group(1))
        break

prov_rows = {}
prov_table_found = False
if prov_heading_idx is not None:
    prov_end_idx = len(mt_lines)
    for idx in range(prov_heading_idx + 1, len(mt_lines)):
        m = re.match(r"^(#{1,6})\s+", mt_lines[idx])
        if m and len(m.group(1)) <= prov_heading_level:
            prov_end_idx = idx
            break

    prov_section = mt_lines[prov_heading_idx + 1:prov_end_idx]
    prov_header_idx = None
    sid_col = None
    durum_col = None
    for idx, line in enumerate(prov_section):
        if not line.strip().startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        sid_aday = next((i for i, col in enumerate(cols)
                         if re.fullmatch(r"SC(?:OPE)?-ID", col, re.I)), None)
        durum_aday = next((i for i, col in enumerate(cols)
                           if col.casefold() == "durum"), None)
        if sid_aday is not None and durum_aday is not None:
            prov_header_idx = idx
            sid_col = sid_aday
            durum_col = durum_aday
            prov_table_found = True
            break

    if prov_table_found:
        for line in prov_section[prov_header_idx + 1:]:
            if not line.strip().startswith("|"):
                break
            if re.match(r"^\|\s*-+", line):
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) <= max(sid_col, durum_col):
                continue
            m = re.search(r"SC-\d{3}", cols[sid_col])
            if not m:
                continue
            prov_rows[m.group(0)] = cols[durum_col]

# --- CHK-02: her ZORUNLU ID provenance tablosunda "kapsiyor" (veya DEC-027
#     kapsaminda [UNVERIFIED]) durumunda mi? ---
missing_prov = []
bad_status = []
if prov_heading_idx is None:
    print("FAIL CHK-02: PROVENANCE bolumu bulunamadi")
    overall_fail = True
elif not prov_table_found:
    print("FAIL CHK-02: PROVENANCE bolumunde taninmis SC-ID/SCOPE-ID ve Durum tablosu bulunamadi")
    overall_fail = True
else:
    for sid in zor:
        if sid not in prov_rows:
            missing_prov.append(sid)
            continue
        durum = prov_rows[sid].strip().casefold()
        # B-9: makine token'lari — TR kapsiyor | EN covered/unverified | MISSING FAIL
        if durum in {"kapsiyor", "kaps\u0131yor", "covered", "unverified", "[unverified]"}:
            continue
        bad_status.append((sid, prov_rows[sid]))

    if missing_prov or bad_status:
        print(f"FAIL CHK-02: PROVENANCE eksik {missing_prov} / gecersiz-durum {bad_status}")
        overall_fail = True
    else:
        print(f"PASS CHK-02: {len(zor)} zorunlu ID PROVENANCE tablosunda 'kapsiyor' durumunda")

# --- CHK-05: Baslik benzersizligi ---
titles = re.findall(r"^#+\s+(.+)$", mt, re.M)
seen = set()
dup = []
for t in titles:
    tn = t.strip().lower()
    if tn in seen:
        dup.append(t)
    seen.add(tn)
if dup:
    print(f"WARN CHK-05: {len(dup)} tekrar baslik {dup}")
else:
    print(f"PASS CHK-05: {len(titles)} benzersiz baslik")

sys.exit(1 if overall_fail else 0)
