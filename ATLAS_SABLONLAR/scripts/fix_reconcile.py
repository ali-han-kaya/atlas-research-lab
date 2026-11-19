#!/usr/bin/env python3
"""Atlas v5.5.4 FIX Reconcile — FAZ1 <-> FAZ2 <-> MASTER sayi ve ID mutabakati

NEDEN VAR:
DENEME/ kosusunda manifesto 8 FIX'i "UYGULANMIS" ilan etti, MASTER'a yalniz 2'si
yansidi, gate 2B "8/8 KANITLI" dedi ve --full FULL PASS verdi. gate_merge.py
ajanin SAYI beyanina guvenmez ama KANIT beyanini dogrulayamaz. Bu betik o kor
noktayi kapatir: kanit iddiasini makineyle sinar.

KONTROLLER (hepsi fail-closed):
  REC-01  FAZ1 bulgu sayisi == FAZ2 FIX sayisi
  REC-02  P0/P1 dagilimi FAZ1 ile FAZ2 arasinda ayni
  REC-03  Her FAZ1 bulgu ID'si FAZ2 metninde geciyor (izlenebilirlik)
          SINIR: bu bir VARLIK kontroludur — ID'nin duz metinde gecmesi yeter.
          Tablo satirinda esleneme garantisi vermez; anlamsal esleme insan isi.
  REC-04  "UYGULANMIS" ilan edilen her FIX-ID MASTER metninde gorunur
  REC-05  gate 2B'de "KANITLI" denen her fix_id MASTER metninde gorunur
  REC-06  MASTER'da gecen her FIX-ID manifestoda tanimli (hayalet kanit yok)

Kullanim:
  python3 scripts/fix_reconcile.py
  ATLAS_FAZ1_FILE=... ATLAS_FAZ2_FILE=... python3 scripts/fix_reconcile.py
  python3 scripts/fix_reconcile.py --sessiz    # sadece PASS/FAIL satirlari
"""
import json, os, re, pathlib, sys

FAZ1 = pathlib.Path(os.environ.get("ATLAS_FAZ1_FILE", "01-FAZ-1-LENS-ANALYSIS.json"))
FAZ2 = pathlib.Path(os.environ.get("ATLAS_FAZ2_FILE", "02-FAZ-2-FIX-MANIFEST.md"))
GATE2B = pathlib.Path(os.environ.get("ATLAS_GATE2B_FILE", "gate/STRONG-gate-2b-v5.5.json"))
MASTER_CANDS = ["03-FAZ-3-MASTER-v5.5.md", "03-FAZ-3-MASTER-v5.4.md",
                "03-FAZ-3-MASTER-v5.2.md", "MASTER.md"]

UYGULANDI_RE = re.compile(r"UYGULANMI[SŞ]", re.I)
KANITLI_RE = re.compile(r"KANITLI", re.I)
FIX_RE = re.compile(r"FIX-(\d{3})")
BULGU_RE = re.compile(r"\bF-(\d{3})\b")

fails = []
notes = []


def say(msg):
    if "--sessiz" not in sys.argv:
        print(msg)


def fail(code, msg):
    fails.append(f"FAIL {code}: {msg}")


# --- FAZ1 bulgulari ---------------------------------------------------------
if not FAZ1.exists():
    print(f"FAIL REC-00: FAZ1 dosyasi yok ({FAZ1})")
    sys.exit(1)

faz1_ids, faz1_pri = [], []
raw1 = FAZ1.read_text(errors="ignore")
if FAZ1.suffix.lower() == ".json":
    try:
        d1 = json.loads(raw1)
    except Exception as e:
        print(f"FAIL REC-00: FAZ1 JSON gecersiz: {e}")
        sys.exit(1)
    items = d1.get("findings") or d1.get("bulgular") or []
    for f in items:
        if not isinstance(f, dict):
            continue
        fid = str(f.get("id") or f.get("finding_id") or "")
        m = BULGU_RE.search(fid)
        faz1_ids.append(m.group(0) if m else fid)
        faz1_pri.append(str(f.get("priority") or f.get("severity") or "?").upper())
else:
    # markdown FAZ1: tablo satirlarindan F-xxx + P0/P1 topla
    for line in raw1.splitlines():
        m = BULGU_RE.search(line)
        if not m:
            continue
        faz1_ids.append(m.group(0))
        pm = re.search(r"\bP([012])\b", line)
        faz1_pri.append(f"P{pm.group(1)}" if pm else "?")

if not faz1_ids:
    print(f"FAIL REC-00: FAZ1'de ({FAZ1}) hic bulgu ID'si ayristirilamadi")
    sys.exit(1)

# --- FAZ2 FIX tablosu -------------------------------------------------------
if not FAZ2.exists():
    print(f"FAIL REC-00: FAZ2 dosyasi yok ({FAZ2})")
    sys.exit(1)

raw2 = FAZ2.read_text(errors="ignore")
fix_rows = {}   # FIX-xxx -> {"pri":..., "durum":..., "satir":...}
for line in raw2.splitlines():
    if not line.strip().startswith("|"):
        continue
    cols = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cols) < 3:
        continue
    m = FIX_RE.search(cols[0])
    if not m:
        continue
    fid = m.group(0)
    pm = re.search(r"\bP([012])\b", " ".join(cols))
    fix_rows[fid] = {
        "pri": f"P{pm.group(1)}" if pm else "?",
        "durum": cols[-2] if len(cols) >= 2 else "",
        "satir": line,
    }

if not fix_rows:
    print(f"FAIL REC-00: FAZ2'de ({FAZ2}) tablo formatinda FIX satiri bulunamadi")
    sys.exit(1)

# --- MASTER -----------------------------------------------------------------
master = next((pathlib.Path(c) for c in MASTER_CANDS if pathlib.Path(c).exists()), None)
if master is None:
    print("FAIL REC-00: MASTER yok")
    sys.exit(1)
mt = master.read_text(errors="ignore")
master_fix_ids = set(FIX_RE.findall(mt))
master_fix_ids = {f"FIX-{n}" for n in master_fix_ids}

# --- REC-01 sayi mutabakati -------------------------------------------------
if len(faz1_ids) != len(fix_rows):
    fail("REC-01", f"FAZ1 bulgu={len(faz1_ids)} ama FAZ2 FIX={len(fix_rows)}")
else:
    say(f"PASS REC-01: FAZ1 {len(faz1_ids)} bulgu == FAZ2 {len(fix_rows)} FIX")

# --- REC-02 oncelik dagilimi ------------------------------------------------
def dagilim(lst):
    return {p: lst.count(p) for p in ("P0", "P1", "P2") if lst.count(p)}

d_faz1 = dagilim(faz1_pri)
d_faz2 = dagilim([v["pri"] for v in fix_rows.values()])
if d_faz1 != d_faz2:
    fail("REC-02", f"oncelik dagilimi FAZ1={d_faz1} != FAZ2={d_faz2}")
else:
    say(f"PASS REC-02: oncelik dagilimi ayni {d_faz1}")

# --- REC-03 izlenebilirlik --------------------------------------------------
izlenen = set(BULGU_RE.findall(raw2))
izlenen = {f"F-{n}" for n in izlenen}
eksik_iz = [b for b in faz1_ids if b not in izlenen]
if eksik_iz:
    fail("REC-03", f"{len(eksik_iz)} FAZ1 bulgusu FAZ2'de atifsiz: {eksik_iz}")
else:
    say(f"PASS REC-03: {len(faz1_ids)} bulgunun tamami FAZ2'de atifli")

# --- REC-04 uygulandi denen FIX MASTER'da gorunur mu ------------------------
iddia = [f for f, v in fix_rows.items() if UYGULANDI_RE.search(v["durum"] or v["satir"])]
gorunmez = sorted(f for f in iddia if f not in master_fix_ids)
if gorunmez:
    fail("REC-04", f"{len(gorunmez)}/{len(iddia)} 'UYGULANMIS' FIX MASTER'da yok: {gorunmez}")
else:
    say(f"PASS REC-04: {len(iddia)} 'UYGULANMIS' FIX'in tamami MASTER'da gorunur")

# --- REC-05 gate 2B kanit iddiasi -------------------------------------------
if GATE2B.exists():
    try:
        g2b = json.loads(GATE2B.read_text(errors="ignore"))
    except Exception as e:
        fail("REC-05", f"gate 2B JSON gecersiz: {e}")
    else:
        if not isinstance(g2b, dict):
            fail("REC-05", f"gate 2B kok nesnesi sozluk degil ({type(g2b).__name__}) — "
                 "kanit iddiasi OLCULEMEDI")
        else:
            rec = g2b.get("manifest_reconciliation", [])
            if not isinstance(rec, list):
                fail("REC-05", "gate 2B manifest_reconciliation liste degil "
                     f"({type(rec).__name__}) — kanit iddiasi OLCULEMEDI")
                rec = []
            kanitli = [str(r.get("fix_id", "")) for r in rec
                       if isinstance(r, dict) and KANITLI_RE.search(str(r.get("status", "")))]
            sahte = sorted(f for f in kanitli if f not in master_fix_ids)
            if sahte:
                fail("REC-05", f"gate 2B '{len(sahte)}' FIX'i KANITLI ilan etti ama MASTER'da yok: {sahte}")
            else:
                say(f"PASS REC-05: gate 2B'nin {len(kanitli)} KANITLI iddiasi MASTER'da dogrulandi")
else:
    notes.append(f"NOT REC-05: gate 2B dosyasi yok ({GATE2B}) — FAZ4 oncesi normaldir")

# --- REC-06 hayalet kanit ---------------------------------------------------
hayalet = sorted(f for f in master_fix_ids if f not in fix_rows)
if hayalet:
    fail("REC-06", f"MASTER'da manifestoda olmayan FIX-ID: {hayalet}")
else:
    say(f"PASS REC-06: MASTER'daki {len(master_fix_ids)} FIX-ID manifestoda tanimli")

for n in notes:
    say(n)

if fails:
    for f in fails:
        print(f)
    print(f"FIX-RECONCILE FAIL — {len(fails)} mutabakat ihlali")
    sys.exit(1)

print(f"FIX-RECONCILE PASS — {len(faz1_ids)} bulgu / {len(fix_rows)} FIX / {len(master_fix_ids)} MASTER kaniti mutabik")
sys.exit(0)
