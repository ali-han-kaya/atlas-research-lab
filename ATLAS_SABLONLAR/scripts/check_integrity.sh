#!/bin/bash
# Atlas v5.5.4 Integrity Check (sikilastirilmis)
# v5.5.3: --faz3'e fix_reconcile, --gate'e verdict + tazelik kontrolu eklendi.
# 25.08.2026 (lab v1.7.14): alt betikler CWD'den degil betik konumundan cozulur (OP-01).
set -e

# OP-01 (lab v1.7.13): alt betikler CWD'den DEGIL bu betigin yanindan cozulur.
# Belgelenen kullanimda (betik projenin kendi scripts/'inde) sonuc birebir ayni;
# capraz-agac cagrisinda artik banner'in soyledigi surum kosar, karisik surum degil.
BETIKLER="$(cd "$(dirname "$0")" && pwd)"

FAZ="${1:---full}"
echo "=== ATLAS v5.5.4 Integrity $FAZ ==="

check_exists(){
  [ -f "$1" ] && return 0
  echo "FAIL $1 yok"
  echo "  ipucu: bu betik PROJE klasorunden calistirilir (su an: $(pwd))"
  echo "  ornek: cd <proje>; bash scripts/check_integrity.sh --full"
  exit 1
}
check_master_script(){
  local betik="$BETIKLER/$1"
  local rc
  check_exists "$betik"
  echo "-- $1 --"
  if python3 "$betik" --dosya "$MASTER"; then
    return 0
  else
    rc=$?
    echo "FAIL $1 exit=$rc"
    exit "$rc"
  fi
}
check_dersler_warning(){
  local cikti
  echo "-- DERSLER (OLGU-06, uyari) --"
  if [ ! -f "$BETIKLER/olgu_lint.py" ]; then
    echo "WARN OLGU-06 olgu_lint.py yok; DERSLER denetlenemedi"
  elif cikti=$(python3 "$BETIKLER/olgu_lint.py" --dersler 2>&1); then
    printf '%s\n' "$cikti"
  else
    printf '%s\n' "$cikti" | sed 's/^FAIL /WARN /'
    echo "WARN OLGU-06 DERSLER denetimi gecmedi; diger kapilar devam ediyor"
  fi
}
check_size(){
  S=$(wc -c < "$1")
  [ "$S" -ge "$2" ] || { echo "FAIL $1 kucuk $S < $2"; exit 1; }
  echo "OK $1 ${S}B"
}
check_words(){
  # B-9 (lab v1.7.27): uzunluk esigi bayt degil KELIME — dil bagimsiz.
  # Gerekce: UTF-8'de Turkce karakter cok baytli; 15000B esigi Ingilizce
  # metinde baska, Turkce metinde baska sayfa sayisina denk geliyordu.
  W=$(wc -w < "$1")
  [ "$W" -ge "$2" ] || { echo "FAIL $1 az kelime $W < $2"; exit 1; }
  echo "OK $1 ${W} kelime"
}
check_contains(){
  grep -q "$2" "$1" || { echo "FAIL $1 icinde '$2' yok"; exit 1; }
  echo "OK $1 icinde '$2' var"
}
check_json(){
  # dosya adi argv ile gecirilir: bosluk/tirnak iceren yollar guvenli
  if python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$1" 2>/dev/null; then
    echo "OK JSON $1"
  else
    echo "FAIL JSON $1 gecersiz"; exit 1
  fi
}
check_json_verdict_pass(){
  V=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("verdict","?"))' "$1" 2>/dev/null) || { echo "FAIL $1 okunamadi"; exit 1; }
  case "$V" in
    PASS) echo "OK $1 verdict=PASS" ;;
    PASS-PENDING-ETHICS)
      echo "OK $1 verdict=PASS-PENDING-ETHICS (etik onay disinda engel yok; DEC-035 acik)" ;;
    *) echo "FAIL $1 verdict=$V (PASS bekleniyor)"; exit 1 ;;
  esac
}

check_gate_freshness(){
  # FINAL-GATE, 2A/2B'den SONRA uretilmis olmali. Bayat FINAL yakalanir.
  python3 - "$1" "$2" "$3" <<'PYFRESH'
import json, sys, os
fin, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
def gd(p):
    try:
        return json.load(open(p)).get("metadata", {}).get("gate_date")
    except Exception:
        return None
gf, ga, gb = gd(fin), gd(a), gd(b)
if not gf or not ga or not gb:
    print("FAIL gate_date alani eksik (FINAL/2A/2B)"); sys.exit(1)
if gf < max(ga, gb):
    print(f"FAIL FINAL-GATE bayat: gate_date={gf} < 2A/2B={max(ga,gb)}"); sys.exit(1)
mf, ma, mb = os.path.getmtime(fin), os.path.getmtime(a), os.path.getmtime(b)
if mf + 1 < max(ma, mb):
    print("FAIL FINAL-GATE dosyasi 2A/2B'den eski (mtime)"); sys.exit(1)
print(f"OK FINAL-GATE taze (gate_date={gf})")
PYFRESH
}

check_devir_evidence(){
  python3 - "$1" <<'PYDEVIR'
import pathlib
import re
import sys
import unicodedata

yol = pathlib.Path(sys.argv[1])
if not yol.is_file():
    print(f"FAIL DEVIR-01: {yol} yok")
    sys.exit(1)

def norm(metin):
    metin = unicodedata.normalize("NFKD", metin)
    metin = "".join(c for c in metin if not unicodedata.combining(c))
    metin = metin.replace("ı", "i")
    return re.sub(r"\s+", " ", metin.casefold()).strip()

def hucreler(satir):
    return [h.replace(r"\|", "|").strip()
            for h in re.split(r"(?<!\\)\|", satir.strip().strip("|"))]

satirlar = yol.read_text(encoding="utf-8").splitlines()
baslangic = next((i for i, s in enumerate(satirlar)
                  if re.match(r"^##\s+(?:\d+\.\s+)?iddia vs dogrulama(?:\s|$)", norm(s))), None)
if baslangic is None:
    print("FAIL DEVIR-01: IDDIA vs DOGRULAMA alani yok")
    sys.exit(1)

tablo = []
for satir in satirlar[baslangic + 1:]:
    temiz = satir.strip()
    if temiz.startswith("#"):
        break
    if temiz.startswith("|") and temiz.endswith("|"):
        tablo.append(temiz)
    elif tablo and temiz:
        break

if len(tablo) < 2:
    print("FAIL DEVIR-01: IDDIA vs DOGRULAMA tablosu bos")
    sys.exit(1)

baslik = [norm(h).strip(" `") for h in hucreler(tablo[0])]
zorunlu = {"iddia": None, "komut": None, "cikti": None, "exit": None}
es_anlamlilar = {
    "iddia": "iddia",
    "komut": "komut",
    "cikti": "cikti",
    "ham cikti": "cikti",
    "exit": "exit",
    "kod": "exit",
    "exit kodu": "exit",
}
for i, ad in enumerate(baslik):
    kanonik = es_anlamlilar.get(ad)
    if kanonik:
        zorunlu[kanonik] = i

eksik = [ad for ad, i in zorunlu.items() if i is None]
if eksik:
    print("FAIL DEVIR-01: zorunlu kolon yok: " + ", ".join(eksik))
    sys.exit(1)

gecerli = 0
for satir in tablo[2:]:
    hucre = hucreler(satir)
    if len(hucre) <= max(zorunlu.values()):
        continue
    degerler = [hucre[zorunlu[ad]].strip(" `") for ad in zorunlu]
    if all(d and d not in {"-", "—", "...", "…"} for d in degerler):
        gecerli += 1

if gecerli == 0:
    print("FAIL DEVIR-01: IDDIA vs DOGRULAMA tablosu bos")
    sys.exit(1)

print(f"OK DEVIR-01: IDDIA vs DOGRULAMA tablosu dolu ({gecerli} satir)")
PYDEVIR
}

check_mutabakat_disclosure(){
  python3 - "$1" <<'PYMUTABAKAT'
import pathlib
import re
import sys
import unicodedata

yol = pathlib.Path(sys.argv[1])
if not yol.is_file():
    print(f"FAIL MUTABAKAT-01: {yol} yok")
    sys.exit(1)

def norm(metin):
    metin = unicodedata.normalize("NFKD", metin)
    metin = "".join(c for c in metin if not unicodedata.combining(c))
    metin = metin.replace("ı", "i")
    return re.sub(r"\s+", " ", metin.casefold()).strip()

satirlar = yol.read_text(encoding="utf-8").splitlines()
baslangic = None
for i, satir in enumerate(satirlar):
    m = re.match(r"^(#{1,6})\s+(.+)$", satir.strip())
    if m and "kural 30" in norm(m.group(2)) and "bagimsizlik beyani" in norm(m.group(2)):
        baslangic = i
        break

if baslangic is None:
    print("FAIL MUTABAKAT-01: KURAL 30 BAGIMSIZLIK BEYANI alani yok")
    sys.exit(1)

icerik = []
for satir in satirlar[baslangic + 1:]:
    if re.match(r"^#{1,6}\s+", satir.strip()):
        break
    if satir.strip() and satir.strip() not in {"-", "—", "...", "…"}:
        icerik.append(satir.strip())

if not icerik:
    print("FAIL MUTABAKAT-01: Kural 30 bagimsizlik beyani bos")
    sys.exit(1)

ham = " ".join(icerik)
metin = norm(ham)
zorunlu = {
    "ayni model": "ayni model" in metin,
    "kopya": "kopya" in metin,
    "bagimsiz uzman sayilmaz": "bagimsiz uzman sayilmaz" in metin,
    "gercek bagimsizlik": "gercek bagimsizlik" in metin,
    "dis model": "dis model" in metin,
}
eksik = [ad for ad, var in zorunlu.items() if not var]
if eksik or ("<" in ham and ">" in ham):
    neden = ", ".join(eksik) if eksik else "yer tutucu doldurulmamis"
    print("FAIL MUTABAKAT-01: Kural 30 beyan icerik eksik: " + neden)
    sys.exit(1)

print("OK MUTABAKAT-01: Kural 30 bagimsizlik beyani dolu")
PYMUTABAKAT
}

MASTER="03-FAZ-3-MASTER-v5.5.md"

# FAZ1/FAZ2 ara dosya adlari proje-durumuna gore degisebilir.
# Varsayilanlar Atlas v5.5.3 gercek dosyalarina gore ayarlanmistir.
FAZ1_FILE=${ATLAS_FAZ1_FILE:-01-FAZ-1-LENS-ANALYSIS.json}
FAZ2_FILE=${ATLAS_FAZ2_FILE:-02-FAZ-2-FIX-MANIFEST.md}
DEVIR_FILE=${ATLAS_DEVIR_FILE:-DEVIR.md}
MUTABAKAT_FILE=${ATLAS_MUTABAKAT_FILE:-rapor/MUTABAKAT.md}

case "$FAZ" in
  --faz0)
    check_exists "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
    check_size "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md" 1000
    check_contains "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md" "SC-"
    check_contains "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md" "DEC-"
    ;;
  --faz1)
    check_exists "$FAZ1_FILE"
    check_size "$FAZ1_FILE" 5000
    check_contains "$FAZ1_FILE" "CHK-"
    check_contains "$FAZ1_FILE" "P0"
    ;;
  --faz2)
    check_exists "$FAZ2_FILE"
    check_size "$FAZ2_FILE" 1000
    check_contains "$FAZ2_FILE" "FIX-"
    ;;
  --faz3)
    check_exists "$MASTER"
    check_words "$MASTER" 1500
    check_size "$MASTER" 1000
    check_contains "$MASTER" "PROVENANCE"
    echo "-- verify_doi.py (DEC-027 bolum-farkindali, sert kontrol) --"
    python3 "$BETIKLER/verify_doi.py" --require-master
    echo "-- provenance_check.py (CHK-01/02/05) --"
    python3 "$BETIKLER/provenance_check.py"
    echo "-- source_class_check.py (B-2 kaynak sinifi) --"
    python3 "$BETIKLER/source_class_check.py"
    echo "-- translit_check.py (B-3 transliterasyon tutarliligi) --"
    python3 "$BETIKLER/translit_check.py"
    echo "-- fix_reconcile.py (REC-01..06 sayi/ID mutabakati) --"
    python3 "$BETIKLER/fix_reconcile.py"
    ;;
  --gate)
    check_exists "gate/STRONG-gate-2a-v5.5.json"
    check_json "gate/STRONG-gate-2a-v5.5.json"
    check_json_verdict_pass "gate/STRONG-gate-2a-v5.5.json"
    check_exists "gate/STRONG-gate-2b-v5.5.json"
    check_json "gate/STRONG-gate-2b-v5.5.json"
    check_json_verdict_pass "gate/STRONG-gate-2b-v5.5.json"
    check_exists "gate/FINAL-GATE-v5.5.json"
    check_json "gate/FINAL-GATE-v5.5.json"
    check_gate_freshness "gate/FINAL-GATE-v5.5.json" "gate/STRONG-gate-2a-v5.5.json" "gate/STRONG-gate-2b-v5.5.json"
    check_exists "04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md"
    ;;
  --gate2c)
    # P1-8: FAZ5 panelinden SONRA kosan kosullu birincil-kaynak istisnasi.
    # P1-9: SOLO yalnızca routing seviyesinde "final-release-only" bir profil
    # olur; sözleşme/kapı davranışı bu davranış değişikliğiyle değişmez,
    # sadece dokümantasyon bu gerçekliği sürdürür.
    # Gate-2A/2B'nin 2-of-2 FINAL kararina oy eklemez ve --full'a bagli degildir.
    check_exists "rapor/PANEL/FINAL-PANEL.json"
    check_json "rapor/PANEL/FINAL-PANEL.json"
    check_exists "rapor/PANEL/GATE-2C-REQUEST.json"
    check_json "rapor/PANEL/GATE-2C-REQUEST.json"
    check_exists "gate/STRONG-gate-2c-v5.5.json"
    check_json "gate/STRONG-gate-2c-v5.5.json"
    python3 "$BETIKLER/gate_2c.py" \
      --panel "rapor/PANEL/FINAL-PANEL.json" \
      --request "rapor/PANEL/GATE-2C-REQUEST.json" \
      --schema "$BETIKLER/../templates/GATE-2C-SCHEMA.json" \
      --check-output "gate/STRONG-gate-2c-v5.5.json"
    ;;
  --devir)
    check_devir_evidence "$DEVIR_FILE"
    ;;
  --teslim)
    # P1-4: teslim manifesti butunluk + imza kapisi. Ali'nin 31.08 karari geregi
    # --full zincirine BAGLI DEGIL: teslim asamasina gelmemis proje kirilmasin.
    python3 "$BETIKLER/teslim_imza.py" --dogrula
    ;;
  --mutabakat)
    check_mutabakat_disclosure "$MUTABAKAT_FILE"
    ;;
  --full)
    # Ders borcu burada uyari; olgu_lint OLGU-06 dogrudan cagrida FAIL'dir.
    check_dersler_warning
    echo "-- FAZ0 --"; "$0" --faz0
    echo "-- FAZ1 --"; "$0" --faz1
    echo "-- FAZ2 --"; "$0" --faz2
    echo "-- FAZ3 (verify_doi + provenance_check dahil) --"; "$0" --faz3
    # MASTER denetimleri FINAL kapisindan once zorunludur; ilk hatada durulur.
    check_master_script cite_match.py
    check_master_script quote_ratio.py
    check_master_script declaration_check.py
    echo "-- GATE --"; "$0" --gate
    echo "-- DEVIR --"; "$0" --devir
    echo "-- FINAL VERDICT --"
    check_json_verdict_pass "gate/FINAL-GATE-v5.5.json"
    echo "FULL PASS v5.5.4 — tum fazlar + sayi/ID mutabakati + gate + devir dogrulandi"
    ;;
  *)
    echo "Kullanim: bash $0 --faz0|--faz1|--faz2|--faz3|--gate|--gate2c|--devir|--mutabakat|--teslim|--full"
    exit 1
    ;;
esac
