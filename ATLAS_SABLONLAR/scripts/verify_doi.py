#!/usr/bin/env python3
"""Atlas v5.5.4 DOI + UNVERIFIED Checker (bolum-farkindali)

[DOGRULANMADI] / [DOĞRULANMADI] / [DOGRULANAMADI] / [UNVERIFIED] etiketlerini tespit eder.
DEC-027 ISTISNASI: '§8' baslikli ve icinde 'M1' gecen bolum icindeki etiketler
KASITLIDIR; bu bolum disindaki her etiket P0 FAIL nedenidir.
DOI'leri CrossRef API ile dogrular; DOGRULANAN gecersiz DOI (HTTP != 200,
gercek yanit alinmis) FAIL nedenidir. Sadece agtaki gecici hata (exception)
FAIL saymaz, WARN olarak raporlanir.

Kullanim:
  python3 scripts/verify_doi.py                  # MASTER yoksa sessizce gec (erken fazlar icin)
  python3 scripts/verify_doi.py --require-master # MASTER yoksa FAIL (post-FAZ3 dogrulama icin)
"""
import re, pathlib, sys, time
import unicodedata

CANDS = [
    "03-FAZ-3-MASTER-v5.5.md",
    "03-FAZ-3-MASTER-v5.4.md",
    "03-FAZ-3-MASTER-v5.2.md",
    "MASTER.md",
]

require_master = "--require-master" in sys.argv

mp = None
for c in CANDS:
    if pathlib.Path(c).exists():
        mp = pathlib.Path(c)
        break

if not mp:
    if require_master:
        print("FAIL: MASTER yok (--require-master ile cagrildi)")
        sys.exit(1)
    print("MASTER yok (erken faz olabilir, atlandi)")
    sys.exit(0)

text = unicodedata.normalize("NFC", mp.read_text(errors="ignore"))

# --- DEC-027 bolum-farkindaligi ---
# v5.5.4 GUVENLIK DUZELTMESI:
#   ONCE: is_target = ("§8" in title or "8" in title) and ("M1" in title.upper())
#   "8" alt dizge araniyordu; "## 18. Sinirliliklar ve M1 notu" basligi da
#   muafiyeti tetikliyor ve o bolumdeki TUM [DOGRULANMADI] etiketleri P0
#   denetiminden muaf oluyordu. Icinde 8 rakami gecen herhangi bir baslik
#   (18, 28, 2008, §1.8) + "M1" dizgesi CHK-03'u tesadufen kapatabiliyordu.
#   Bagimsiz denetimde kanitlandi (atlas_selftest VD-4).
#
#   SIMDI iki yol var, ikisi de ACIK NIYET gerektirir:
#     1. Baslik satirinda veya bolum icinde `<!-- DEC-027-EXEMPT -->` isareti
#        (tercih edilen — dosya adindan/numarasindan bagimsiz, aciktir)
#     2. Eski usul: baslikta `§8` (bolum isaretiyle, tam) VE "M1"
#   Ciplak "8" artik yetmez.
EXEMPT_MARK = "DEC-027-EXEMPT"
exempt_titles = []
lines = text.splitlines()
heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
exempt_ranges = []  # (start_line_idx, end_line_idx) dahil aralik, 0-index
cur_start = None
cur_level = None
for i, line in enumerate(lines):
    m = heading_re.match(line)
    if m:
        level = len(m.group(1))
        title = m.group(2)
        # H1 muafiyeti belge sonuna kadar kapanamayacagi icin gecersizdir;
        # mevcut ayni/ust seviye kapanis mantigi yalniz H2+ icin korunur.
        is_target = level >= 2 and (
            (EXEMPT_MARK in line)
            or (bool(re.search(r"§\s*8(?![0-9])", title)) and ("M1" in title.upper()))
        )
        if is_target:
            exempt_titles.append(title.strip())
        if cur_start is not None and (is_target or level <= cur_level):
            exempt_ranges.append((cur_start, i - 1))
            cur_start = None
            cur_level = None
        if is_target:
            cur_start = i
            cur_level = level
if cur_start is not None:
    exempt_ranges.append((cur_start, len(lines) - 1))


def in_exempt_zone(line_idx):
    return any(s <= line_idx <= e for s, e in exempt_ranges)


# Seffaflik: hangi bolumler muaf sayildi, insan gorsun.
if exempt_titles:
    print(f"[DEC-027] muaf bolum sayisi: {len(exempt_titles)}")
    for t in exempt_titles:
        print(f"  muaf: {t}")
else:
    print("[DEC-027] muaf bolum yok")


patterns = [
    r"\[DOGRULANMADI\]",
    r"\[DOĞRULANMADI\]",
    r"\[DOGRULANAMADI\]",
    r"\[DOĞRULANAMADI\]",
    r"\[UNVERIFIED\]",
]
combined = re.compile("|".join(patterns), re.IGNORECASE)

violations = []  # disaridaki (yasak) etiketler
exempt_hits = 0  # DEC-027 kapsaminda beklenen etiketler
for i, line in enumerate(lines):
    for mm in combined.finditer(line):
        if in_exempt_zone(i):
            exempt_hits += 1
        else:
            violations.append((i + 1, line.strip()[:200]))

print(f"[{mp.name}] DEC-027 istisna bolgesinde {exempt_hits} etiketli ifade (kasitli, izinli)")
print(f"[{mp.name}] istisna DISINDA {len(violations)} etiketli ifade")
for ln, snippet in violations[:10]:
    print(f"  satir {ln}: {snippet}")

# --- DOI tespiti (deterministik siralama) ---
dois = re.findall(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, re.I)
unique_dois = sorted(set(d.rstrip(".,);'\"") for d in dois))
print(f"DOI {len(dois)} toplam {len(unique_dois)} unique")

doi_confirmed_invalid = []
doi_network_errors = []
checked = 0
MAX_CHECK = 10
try:
    import requests

    for doi in unique_dois[:MAX_CHECK]:
        checked += 1
        try:
            r = requests.get(
                f"https://api.crossref.org/works/{doi}",
                timeout=10,
                headers={"User-Agent": "Atlas-v5.5.4 (mailto:atlas@local)"},
            )
            if r.status_code == 200:
                print(f"OK {doi} [200]")
            else:
                print(f"FAIL {doi} [{r.status_code}]")
                doi_confirmed_invalid.append((doi, r.status_code))
            time.sleep(1.1)  # rate limit
        except Exception as e:
            print(f"ERR (ag hatasi, sayilmaz) {doi} {e}")
            doi_network_errors.append((doi, str(e)))
    if len(unique_dois) > MAX_CHECK:
        print(f"NOT: {len(unique_dois) - MAX_CHECK} DOI daha var, ilk {MAX_CHECK} (alfabetik) kontrol edildi.")
except ImportError:
    print("requests modulu yok — DOI dogrulama atlandi (bu bir FAIL nedeni degildir, ancak DOI'ler dogrulanmamis kabul edilir)")

# --- Sonuc ---
fail = False
if violations:
    print(f"FAIL: istisna disinda {len(violations)} etiketli ifade bulundu")
    fail = True
if doi_confirmed_invalid:
    print(f"FAIL: {len(doi_confirmed_invalid)} DOI CrossRef'te dogrulanamadi (gecerli HTTP yaniti, 200 degil): {doi_confirmed_invalid}")
    fail = True
if doi_network_errors:
    print(f"WARN: {len(doi_network_errors)} DOI icin ag hatasi (FAIL sayilmadi, manuel kontrol onerilir)")

if fail:
    sys.exit(1)
else:
    print("PASS: etiketli ifade (istisna disinda) yok, dogrulanabilen DOI'ler gecerli")
    sys.exit(0)
