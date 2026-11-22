#!/usr/bin/env bash
# kur.sh — KOD hattini bir HEDEF DEPOYA kurar ve kurulumu DOGRULAR
#
# NEDEN VAR (OLCUM-02 K1 + K2, 24.08.2026):
#   Hattin teslim paketi kendi kendine YETMIYORDU ve kurulum yordami hicbir
#   yerde yazili degildi. Canli kosuda iki sey birden kirildi:
#     K1  `scripts/budget_guard.py` bir SYMLINK'ti (`../../ATLAS_SABLONLAR/...`);
#         hedef depoya kopyalaninca hedef yoktu -> `/kod-faz0` adim 2 exit=2.
#     K2  `kod_gate_merge.py` `ORTAK/scripts/ortak_gate.py`'yi arar, ama `ORTAK/`
#         `KOD_SABLONLAR/`'in ICINDE DEGILDIR -> exit=1, "Hat eksik kurulmus".
#   Ikisi de dogru fail-closed davraniyordu; eksik olan KURULUMDU.
#
# Kullanim:
#   bash KOD_SABLONLAR/scripts/kur.sh <hedef-depo-yolu> [--kuru|--dogrula]
#     --kuru     hicbir sey yazma, ne yapilacagini goster
#     --dogrula  KOPYALAMA, yalniz MEVCUT kurulumu denetle
#
# NEDEN --dogrula AYRI BIR MOD (bu turda olculdu):
# Kurulum modu dogrulamadan ONCE yeniden kopyalar; bu yuzden "ORTAK ayrismis mi"
# kontrolu kurulum modunda ASLA ATESLEYEMEZ — bozulan dosya uzerine taze kopya
# yazilir. Boyle bir kontrol BOSTUR (her zaman gecer). Sapma ancak kopyalama
# YAPILMAYAN bir modda anlamlidir.
#
# Cikis kodlari: 0 kurulum tam ve dogrulandi · 1 dogrulama basarisiz · 64 kullanim
set -uo pipefail

HEDEF=""; KURU=0; SADECE_DOGRULA=0
while [ $# -gt 0 ]; do
  case "$1" in
    --kuru) KURU=1; shift ;;
    --dogrula) SADECE_DOGRULA=1; shift ;;
    -h|--help)
      echo "Kullanim: bash KOD_SABLONLAR/scripts/kur.sh <hedef-depo-yolu> [--kuru|--dogrula]"
      echo "  (bayraksiz)  kurulum + dogrulama"
      echo "  --kuru       hicbir sey yazma, ne yapilacagini goster"
      echo "  --dogrula    kopyalama YOK, yalniz mevcut kurulumu denetle"
      exit 0 ;;
    -*)     echo "FAIL: bilinmeyen bayrak '$1'" >&2; exit 64 ;;
    *)      HEDEF="$1"; shift ;;
  esac
done
[ -n "$HEDEF" ] || { echo "Kullanim: kur.sh <hedef-depo-yolu> [--kuru]" >&2; exit 64; }

BETIK_DIZIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SABLON="$(cd "$BETIK_DIZIN/.." && pwd)"          # KOD_SABLONLAR/
LAB="$(cd "$SABLON/.." && pwd)"                  # lab koku

[ -d "$HEDEF" ] || { echo "FAIL: hedef dizin yok: $HEDEF" >&2; exit 1; }
HEDEF="$(cd "$HEDEF" && pwd)"

# LAB'in GERCEKTEN lab olup olmadigi ISARETLE anlasilir, konumdan DEGIL.
# Uctan uca kosuda olculdu: betik KURULU BIR KOPYADAN (`<hedef>/scripts/kur.sh`)
# calistirildiginda `$SABLON/..` hedefin UST DIZINI cikiyor ve `--dogrula`
# "hedef labin icinde" diye yanlis reddediyordu.
LAB_GERCEK=0
if [ -d "$LAB/ATLAS_SABLONLAR" ] && [ -d "$LAB/ORTAK/scripts" ]; then LAB_GERCEK=1; fi

if [ "$LAB_GERCEK" -eq 1 ]; then
  case "$HEDEF" in
    "$LAB"|"$LAB"/*) echo "FAIL: hedef labin ICINDE ($HEDEF). Hat, denetledigi depoya kurulur." >&2; exit 1 ;;
  esac
elif [ "$SADECE_DOGRULA" -eq 0 ]; then
  echo "FAIL: kaynak bir lab agaci degil ($LAB) — kurulum yapilamaz." >&2
  echo "      Kurulum LABDAN calistirilir: bash <lab>/KOD_SABLONLAR/scripts/kur.sh <hedef>" >&2
  exit 1
fi

kopyala() {  # kaynak hedef
  if [ "$KURU" -eq 1 ]; then echo "  [kuru] $1 -> $2"; return 0; fi
  if [ -d "$1" ]; then
    mkdir -p "$2"
    cp -R "$1/." "$2/"
  else
    mkdir -p "$(dirname "$2")"
    cp -R "$1" "$2"
  fi
}

if [ "$SADECE_DOGRULA" -eq 1 ]; then
  echo "=== KOD hatti kurulum DOGRULAMASI (kopyalama YOK) ==="
  echo "hedef  : $HEDEF"
else

echo "=== KOD hatti kurulumu ==="
echo "kaynak : $SABLON"
echo "hedef  : $HEDEF"
[ "$KURU" -eq 1 ] && echo "(KURU KOSU — hicbir dosya yazilmayacak)"

# 1) sablon agaci
for parca in .opencode scripts templates opencode.json routing.profiles.json 00_KOD_OKU_BENI.md OPERATOR_SURME.md; do
  [ -e "$SABLON/$parca" ] || { echo "FAIL: sablonda eksik: $parca" >&2; exit 1; }
  kopyala "$SABLON/$parca" "$HEDEF/$parca"
done

# 2) ORTAK cekirdegi — KOPYALANMAZ DENIR AMA GEREKLIDIR.
#    Kapi ILKELERI tek kaynaktan gelir; burada yapilan sey ilkeyi CATALLAMAK
#    degil, hedef depoya AYNI dosyayi tasimaktir. `dogrula` adimi iki kopyanin
#    SHA256'sinin ayni oldugunu sinar; ayrisirsa kurulum FAIL verir.
[ -f "$LAB/ORTAK/scripts/ortak_gate.py" ] || { echo "FAIL: $LAB/ORTAK/scripts/ortak_gate.py yok" >&2; exit 1; }
kopyala "$LAB/ORTAK/scripts/ortak_gate.py" "$HEDEF/ORTAK/scripts/ortak_gate.py"

# 3) sozlesme dosyasi (opencode.json `instructions` bunu bekler)
[ -f "$LAB/AI_CALISMA_SISTEMI_v1.md" ] && kopyala "$LAB/AI_CALISMA_SISTEMI_v1.md" "$HEDEF/AI_CALISMA_SISTEMI_v1.md"

# 4) kod_profil.json ornegi (VARSA DOKUNMA — hedefin kendi sozlesmesidir)
if [ ! -f "$HEDEF/kod_profil.json" ]; then
  kopyala "$SABLON/templates/kod_profil.ORNEK.json" "$HEDEF/kod_profil.json"
  echo "  NOT: kod_profil.json ORNEKTEN olusturuldu — ELLE DOLDURUN (test_komutu, kilit dosyasi...)"
else
  echo "  kod_profil.json zaten var — DOKUNULMADI"
fi

# 5) .gitignore — DERLEME ONBELLEGI  (O5-02, 24.08.2026)
#    KFAZ3 hedef deponun test komutunu kosar; pytest/python `birim/__pycache__/`
#    ve `tests/__pycache__/` altina .pyc yazar. Kapilar diff kumesini
#    `git diff --name-only HEAD` + `git ls-files --others --exclude-standard`
#    ile kurar: IZLENMEYEN .pyc dosyalari RECK-03 SCOPE_VIOLATION P0 olur
#    (canli senaryoda olculdu: 2x P0 — birim/ ve tests/ __pycache__; tamami SAHTE).
#    KOK NEDEN: hedef deponun .gitignore'unda bu iki satirin OLMAMASI. Kapiya
#    muafiyet eklemek semptomu orter; kurulum bunu KAYNAGINDA kapatir.
#    IDEMPOTENT: dosya yoksa olusturulur, varsa YALNIZ EKSIK satir eklenir;
#    hedefin kendi kurallarina DOKUNULMAZ.
GI="$HEDEF/.gitignore"
GI_BASLIK="# KOD hatti kurulumu (O5-02): derleme onbellegi kapi gurultusu yapar"
GI_EKSIK=""
for satir in '__pycache__/' '*.pyc'; do
  if [ -f "$GI" ] && grep -qxF -- "$satir" "$GI"; then continue; fi
  GI_EKSIK="${GI_EKSIK}${satir}"$'\n'
done
if [ -z "$GI_EKSIK" ]; then
  echo "  .gitignore derleme onbellegini zaten yok sayiyor — DOKUNULMADI"
elif [ "$KURU" -eq 1 ]; then
  echo "  [kuru] .gitignore'a eklenecek: $(printf '%s' "$GI_EKSIK" | tr '\n' ' ')"
else
  if [ -s "$GI" ] && [ -n "$(tail -c 1 "$GI")" ]; then printf '\n' >> "$GI"; fi
  if ! grep -qF -- "$GI_BASLIK" "$GI" 2>/dev/null; then printf '%s\n' "$GI_BASLIK" >> "$GI"; fi
  printf '%s' "$GI_EKSIK" >> "$GI"
  echo "  .gitignore guncellendi: $(printf '%s' "$GI_EKSIK" | tr '\n' ' ')"
fi

if [ "$KURU" -eq 1 ]; then echo "KURU KOSU bitti."; exit 0; fi
fi

# ------------------------------------------------------------------ DOGRULAMA
echo
echo "=== kurulum dogrulamasi ==="
HATA=0
d() { # ad komut...
  local ad="$1"; shift
  if "$@" > /dev/null 2>&1; then echo "  OK   $ad"; else echo "  FAIL $ad"; HATA=$((HATA + 1)); fi
}

# symlink kalmadi mi (K1)
if find "$HEDEF/scripts" -type l | grep -q .; then
  echo "  FAIL kirik/asili symlink var:"; find "$HEDEF/scripts" -type l -exec echo "       {}" \;
  HATA=$((HATA + 1))
else
  echo "  OK   scripts/ altinda symlink yok (K1)"
fi

# ORTAK ayrismamis mi (yalniz LAB elde varken karsilastirilabilir)
if [ ! -f "$HEDEF/ORTAK/scripts/ortak_gate.py" ]; then
  echo "  FAIL ORTAK/scripts/ortak_gate.py hedefte YOK — kod_gate_merge kosamaz"
  HATA=$((HATA + 1))
elif [ "$LAB_GERCEK" -eq 1 ]; then
  A=$(shasum -a 256 "$LAB/ORTAK/scripts/ortak_gate.py" | cut -d' ' -f1)
  B=$(shasum -a 256 "$HEDEF/ORTAK/scripts/ortak_gate.py" | cut -d' ' -f1)
  if [ "$A" = "$B" ]; then echo "  OK   ORTAK/ortak_gate.py labla BIREBIR ($(echo "$A" | cut -c1-12)…)"
  else echo "  FAIL ORTAK/ortak_gate.py AYRISMIS"; HATA=$((HATA + 1)); fi
else
  echo "  CALISTIRILMADI  ORTAK sapma karsilastirmasi — lab agaci elde yok."
  echo "                  Sapmayi gormek icin labdan kostur: <lab>/KOD_SABLONLAR/scripts/kur.sh $HEDEF --dogrula"
fi

# .gitignore derleme onbellegini yok sayiyor mu (O5-02)
# NOT: bu kontrol --dogrula modunda ESKI bir kurulumda FAIL verir; dogrudur —
# kurulum eksiktir ve KFAZ3 sonrasi kapilar sahte P0 uretir.
GI_OK=1
for satir in '__pycache__/' '*.pyc'; do
  grep -qxF -- "$satir" "$HEDEF/.gitignore" 2>/dev/null || GI_OK=0
done
if [ "$GI_OK" -eq 1 ]; then
  echo "  OK   .gitignore derleme onbellegini yok sayiyor (__pycache__/, *.pyc) (O5-02)"
else
  echo "  FAIL .gitignore '__pycache__/' + '*.pyc' icermiyor — KFAZ3 sonrasi kapilar sahte P0 uretir (O5-02)"
  HATA=$((HATA + 1))
fi

# betikler gercekten kosuyor mu (K2/K3)
# NOT: alt kabuk `( ... )` KULLANILMAZ. Kullanilsaydi $HATA alt kabukta artar ve
# disarida KAYBOLURDU; betik basarisiz dogrulamalara ragmen "KURULUM TAM" derdi.
# Bu, tam da bu turda kapatilan fail-OPEN sinifidir (shellcheck SC2030/SC2031).
ONCEKI_DIZIN="$PWD"
cd "$HEDEF" || { echo "  FAIL hedefe girilemedi"; exit 1; }
d "budget_guard --preflight KFAZ0" python3 scripts/budget_guard.py --preflight KFAZ0
python3 scripts/kod_gate_merge.py > /dev/null 2>&1
if [ $? -eq 1 ]; then
  echo "  OK   kod_gate_merge ORTAK'i buldu (kullanim mesaji)"
else
  echo "  FAIL kod_gate_merge — ORTAK bulunamadi ya da beklenmeyen cikis"
  HATA=$((HATA + 1))
fi
d "kod_selftest" python3 scripts/kod_selftest.py
d "perm_lint" python3 scripts/perm_lint.py
cd "$ONCEKI_DIZIN" || exit 1

echo
if [ "$HATA" -eq 0 ]; then
  echo "KURULUM TAM — $HEDEF"
  echo "Sonraki adim: kod_profil.json'u doldurun, sonra /kod-faz0."
  exit 0
fi
echo "KURULUM EKSIK — $HATA dogrulama basarisiz. Hat BASLATILMAMALIDIR (fail-closed)."
exit 1
