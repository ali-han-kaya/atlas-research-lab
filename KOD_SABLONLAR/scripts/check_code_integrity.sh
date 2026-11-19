#!/usr/bin/env bash
# check_code_integrity — KFAZ0..5 artefakt zinciri + kapi verdict + FINAL tazeligi
#
# NEDEN VAR:
# Akademik hattaki check_integrity.sh'in kod karsiligi. Bir kosunun "bitti"
# demesi, artefaktlarin var oldugu anlamina gelmez; artefaktlarin var olmasi da
# tutarli olduklari anlamina gelmez. En sinsi hata FINAL kapinin BAYAT olmasidir:
# 2A/2B yeniden kosmus ama FINAL eski dosyadan kalmistir.
#
# BOSLUKLU YOL DERSI (v1.5, kanitlanmis kusur): bu betik mutlak yolu bosluk
# iceren bir dizinden calistirilabilir. Her degisken tirnak icindedir; $0'in
# dizini de tirnaklanir. Regresyonu ITG-90 testi korur.
#
# Kullanim: bash scripts/check_code_integrity.sh [--full] [--kosu _KOSU]
set -uo pipefail

KOSU="_KOSU"
FULL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --full) FULL=1; shift ;;
    --kosu) KOSU="${2:-_KOSU}"; shift 2 ;;
    -h|--help)
      echo "Kullanim: bash scripts/check_code_integrity.sh [--full] [--kosu _KOSU]"
      echo "  KFAZ0..5 artefakt zinciri + kapi verdict + FINAL tazeligi denetler."
      exit 0 ;;
    *) shift ;;
  esac
done

HATA=0
UYARI=0

fail() { printf 'FAIL %s\n' "$1"; HATA=$((HATA + 1)); }
warn() { printf 'UYARI %s\n' "$1"; UYARI=$((UYARI + 1)); }
ok()   { [ "$FULL" -eq 1 ] && printf 'OK   %s\n' "$1"; return 0; }

if [ ! -d "$KOSU" ]; then
  fail "ITG-00 kosu dizini yok: $KOSU (bu betik PROJE klasorunden calistirilir)"
  printf 'CODE-INTEGRITY FAIL — %d hata\n' "$HATA"
  exit 1
fi

# --- ITG-01..06 faz artefaktlari ------------------------------------------------
zorunlu_var() {
  local desen="$1" etiket="$2"
  local bulunan
  bulunan="$(find "$KOSU" -maxdepth 1 -name "$desen" -type f 2>/dev/null | head -1)"
  if [ -z "$bulunan" ]; then
    fail "$etiket artefakti yok: $KOSU/$desen"
    return 1
  fi
  ok "$etiket: $bulunan"
  printf '%s' "$bulunan"
}

F0="$(zorunlu_var '00-KFAZ-0-*.md' 'ITG-01 KFAZ0')" || true
F1="$(zorunlu_var '01-KFAZ-1-*.md' 'ITG-02 KFAZ1')" || true
F2="$(zorunlu_var '02-KFAZ-2-*.md' 'ITG-03 KFAZ2')" || true
F3="$(zorunlu_var '03-KFAZ-3-*.json' 'ITG-04 KFAZ3')" || true

# --- ITG-07 makine blogu zorunlulugu -------------------------------------------
for par in "$F0:KFAZ0" "$F1:KFAZ1" "$F2:KFAZ2"; do
  dosya="${par%:*}"; etiket="${par##*:}"
  if [ -n "$dosya" ] && [ -f "$dosya" ]; then
    if ! grep -q '```json' "$dosya"; then
      fail "ITG-07 $etiket ($dosya) icinde \`\`\`json makine blogu YOK — chg_reconcile ayristiramaz"
    else
      ok "ITG-07 $etiket makine blogu var"
    fi
  fi
done

# --- ITG-08 KFAZ3 kaniti gecerli ve cikis kodu tasiyor mu -----------------------
if [ -n "$F3" ] && [ -f "$F3" ]; then
  if ! python3 -c "import json,sys;d=json.load(open(sys.argv[1]));sys.exit(0 if 'cikis_kodu' in d else 3)" "$F3" 2>/dev/null; then
    fail "ITG-08 KFAZ3 kaniti ($F3) bozuk JSON ya da \`cikis_kodu\` alani yok"
  else
    ok "ITG-08 KFAZ3 kaniti gecerli ve cikis kodu tasiyor"
  fi
fi

# --- ITG-10..12 kapi dosyalari --------------------------------------------------
GATE_DIR="$KOSU/gate"
if [ ! -d "$GATE_DIR" ]; then
  fail "ITG-10 kapi dizini yok: $GATE_DIR"
else
  for g in "KOD-gate-2a.json" "KOD-gate-2b.json"; do
    if [ ! -f "$GATE_DIR/$g" ]; then
      fail "ITG-11 zorunlu kapi dosyasi yok: $GATE_DIR/$g"
    else
      # ITG-11 artik yalniz "gecerli JSON" demiyor. OLCUM-02 K13/K15:
      #  - K13: zaman asimiyla oldurulen bir kapi kosusu YARIM YAZILMIS bir
      #    verdict birakti; dosyanin VARLIGI kapinin kostugu anlamina gelmiyor.
      #  - K15: 2A durum alanini `durum` diye yazdi; `ortak_gate` `status` okur.
      #    Bozuk sema birlestirmede yakalandi ama ITG-11 "gecerli JSON" diyip
      #    operatoru yanlis yonlendiriyordu.
      SEMA_HATA=$(python3 - "$GATE_DIR/$g" <<'PYITG'
import json, sys
yol = sys.argv[1]
try:
    d = json.load(open(yol))
except Exception as e:
    print(f"bozuk JSON: {e}"); raise SystemExit(0)
if not isinstance(d, dict):
    print("kok nesne degil"); raise SystemExit(0)
diziler = [k for k in ("checks", "manifest_reconciliation") if isinstance(d.get(k), list)]
if not diziler:
    print("`checks` ya da `manifest_reconciliation` dizisi YOK — denetim izi tasimiyor")
    raise SystemExit(0)
eksik = []
for k in diziler:
    for i, c in enumerate(d[k]):
        if not isinstance(c, dict):
            eksik.append(f"{k}[{i}] nesne degil")
        elif not str(c.get("status", "")).strip():
            eksik.append(f"{k}[{i}] `status` alani yok"
                         + (" (`durum` yazilmis)" if c.get("durum") else ""))
if eksik:
    print("; ".join(eksik[:4]))
PYITG
)
      if [ -n "$SEMA_HATA" ]; then
        fail "ITG-11 kapi dosyasi SEMA DISI: $GATE_DIR/$g -> $SEMA_HATA"
      else
        ok "ITG-11 $g gecerli JSON + sema uygun"
      fi
    fi
  done
  if [ -f "$GATE_DIR/KOD-gate-2c.json" ]; then
    ok "ITG-12 kosullu 2C kapisi var"
  fi
fi

# --- ITG-20 FINAL tazeligi ------------------------------------------------------
FINAL="$GATE_DIR/FINAL-KOD-GATE.json"
if [ ! -f "$FINAL" ]; then
  fail "ITG-20 FINAL-KOD-GATE.json yok — kapi birlestirilmemis"
else
  # Tazelik SHA256 ile olculur; mtime ayni saniye icindeki yeniden yazimi kacirir.
  BAYAT_CIKTI="$(python3 - "$FINAL" "$GATE_DIR" <<'PYIN'
import hashlib, json, pathlib, sys
final = pathlib.Path(sys.argv[1]); gate = pathlib.Path(sys.argv[2])
try:
    d = json.loads(final.read_text())
except Exception as e:
    print(f"COZULEMEDI FINAL JSON gecersiz: {e}"); sys.exit(0)
kayit = d.get("girdi_sha256") or {}
if not kayit:
    print("COZULEMEDI FINAL icinde girdi_sha256 yok — tazelik mtime'a dusuyor"); sys.exit(0)
for yol, beklenen in kayit.items():
    p = pathlib.Path(yol)
    if not p.is_absolute() and not p.exists():
        p = gate / pathlib.Path(yol).name
    if not p.exists():
        print(f"BAYAT girdi kapisi kayip: {yol}"); continue
    simdi = hashlib.sha256(p.read_bytes()).hexdigest()
    if simdi != beklenen:
        print(f"BAYAT {pathlib.Path(yol).name} FINAL yazildigindan beri DEGISMIS")
PYIN
)"
  BAYAT=0
  if printf '%s' "$BAYAT_CIKTI" | grep -q '^BAYAT'; then
    while IFS= read -r satir; do
      [ -z "$satir" ] && continue
      case "$satir" in
        BAYAT*) fail "ITG-20 FINAL BAYAT: ${satir#BAYAT }"; BAYAT=1 ;;
      esac
    done <<< "$BAYAT_CIKTI"
  elif printf '%s' "$BAYAT_CIKTI" | grep -q '^COZULEMEDI'; then
    warn "ITG-20 ${BAYAT_CIKTI#COZULEMEDI }"
    for g in "$GATE_DIR"/KOD-gate-2*.json; do
      [ -f "$g" ] || continue
      if [ "$g" -nt "$FINAL" ]; then
        fail "ITG-20 FINAL BAYAT: $(basename "$g") FINAL'den YENI"
        BAYAT=1
      fi
    done
  fi
  [ "$BAYAT" -eq 0 ] && ok "ITG-20 FINAL taze"
  V="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('verdict',''))" "$FINAL" 2>/dev/null || printf '')"
  if [ -z "$V" ]; then
    fail "ITG-21 FINAL icinde verdict alani yok"
  else
    ok "ITG-21 FINAL verdict=$V"
    if [ "$V" != "PASS" ] && [ -f "$KOSU/05-KFAZ-5-TESLIM.md" ]; then
      fail "ITG-22 FINAL verdict=$V oldugu halde TESLIM artefakti yazilmis"
    fi
  fi
fi

# --- ITG-30 dongu sayaci --------------------------------------------------------
if [ -f "$GATE_DIR/DONGU.json" ]; then
  ok "ITG-30 dongu sayaci var"
else
  warn "ITG-30 DONGU.json yok — tur sayisi izlenmiyor"
fi

# --- ITG-40 taban ---------------------------------------------------------------
if [ ! -f "$GATE_DIR/BASELINE.json" ]; then
  fail "ITG-40 BASELINE.json yok — taban olmadan test_attest ve freeze_check karar veremez"
else
  ok "ITG-40 taban var"
fi

if [ "$HATA" -gt 0 ]; then
  printf 'CODE-INTEGRITY FAIL — %d hata, %d uyari\n' "$HATA" "$UYARI"
  exit 1
fi
printf 'CODE-INTEGRITY PASS — %d uyari\n' "$UYARI"
exit 0
