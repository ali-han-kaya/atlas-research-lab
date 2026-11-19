#!/usr/bin/env bash
# kos_faz.sh — bir KFAZ komutunu GUVENLI surer ve sonucu DOGRULAR
#
# NEDEN VAR (OLCUM-02 canli kosusu, 24.08.2026 — uc ayri kirik):
#
#   K5  `opencode run --agent <alt-ajan>` SESSIZCE varsayilan ajana duser:
#       stderr'e "is a subagent, not a primary agent. Falling back to default
#       agent" yazar, exit=0 doner ve ajanin istem metni de izin blogu da HIC
#       uygulanmaz. On ajandan DOKUZU alt ajandir. Yalniz exit koduna bakan bir
#       surucu bunu fark etmez. -> Bu betik ajan banner'ini DOGRULAR.
#
#   K16 Ajan yapilandirmasi degistikten sonraki kosular sik asiliyor (exit=124,
#       stdout/stderr 0 satir, oturum hic kurulmuyor). Kapi 2B canli kosuda
#       3x240 s + 1x600 s denedi, HIC cikti uretmedi. -> Yeniden deneme sarmali
#       ZORUNLUDUR ve sinir yapilandirilabilir olmalidir.
#
#   K17 Insan onayi isteyen fazlar (KFAZ0/1/5) bassiz kosuda soruyu sorup
#       SIFIR ARTEFAKTLA exit=0 doner. Fail-OPEN. -> Bu betik beklenen
#       artefaktin GERCEKTEN olustugunu dogrular; yoksa exit=4 verir.
#
# Kullanim:
#   scripts/kos_faz.sh --komut kod-faz0 --ajan kod-scoper \
#                      --artefakt '_KOSU/00-KFAZ-0-*.md' \
#                      [--artefakt '_KOSU/gate/BASELINE.json'] \
#                      [--model <saglayici/model>] [--sure 240] [--deneme 3] \
#                      -- "istem metni"
#
# Cikis kodlari:
#   0  ajan dogru, artefaktlarin hepsi uretildi
#   2  ajan DUSTU (K5) — istenen alt ajan yerine baska ajan kostu
#   3  butun denemeler asildi (K16)
#   4  ajan kostu ama beklenen artefakt YOK (K17 — onay cikmazi dahil)
#   *  --artefakt verilmezse UYARI + 'artefakt_denetimi=YOK' (O4-01), exit degismez
#  66  YENIDEN GIRIS — betik kendi icinden cagrildi (O3-02 ozyineleme kilidi)
#   *  opencode'un kendi cikis kodu
#   O3-02 (OLCUM-03, 24.08.2026) OZYINELEME: bu betigin kullanimi
#       `00_KOD_OKU_BENI.md`'de yaziliydi ve o dosya `opencode.json`
#       `instructions` listesindedir — yani HER AJANIN sistem istemine yukleniyordu.
#       Ajanlar operatore yazilmis talimati kendi gorevleri sandi: tek kosuda
#       `kod-architect` 44 kez bu betigi, 6 kez `opencode run --agent`i cagirdi;
#       acilan oturum sayisi build=78 / kod-architect=74 oldu, ic ice cagrilar
#       dis kosunun log dosyasini kirpti ve ucretsiz modelin GUNLUK KOTASI
#       tukendi (KFAZ2-KFAZ5 hic kosamadi). -> Iki katmanli duzeltme:
#       (a) surme bolumu `OPERATOR_SURME.md`'ye tasindi (instructions DISI),
#       (b) asagidaki YENIDEN GIRIS KILIDI — makine olarak reddeder, exit=66.

set -uo pipefail

# ---------------------------------------------------------------- O3-02 KILIDI
# Ortam degiskeni cocuk sureclere MIRAS GECER. Bir ajan bu betigi kendi
# icinden cagirirsa degisken zaten set olur ve cagri reddedilir.
if [ -n "${KOD_KOS_FAZ_AKTIF:-}" ]; then
  echo "DURDU — kos_faz.sh YENIDEN GIRIS: zaten '$KOD_KOS_FAZ_AKTIF' fazi suruluyor." >&2
  echo "        Hatti bir AJAN degil, disaridan bir OPERATOR surer. Bir faz ajani" >&2
  echo "        kos_faz.sh'i ya da 'opencode run'u CAGIRMAZ (00_KOD_OKU_BENI.md)." >&2
  echo "        Kanit/gerekce: OLCUM-03 O3-02." >&2
  exit 66
fi

KOMUT=""; AJAN=""; MODEL=""; SURE=240; DENEME=3; ARTEFAKTLAR=(); ISTEM=""
LOGDIZIN="${KOS_FAZ_LOG:-_KOSU/loglar}"

while [ $# -gt 0 ]; do
  case "$1" in
    --komut)    KOMUT="$2"; shift 2 ;;
    --ajan)     AJAN="$2"; shift 2 ;;
    --model)    MODEL="$2"; shift 2 ;;
    --sure)     SURE="$2"; shift 2 ;;
    --deneme)   DENEME="$2"; shift 2 ;;
    --artefakt) ARTEFAKTLAR+=("$2"); shift 2 ;;
    -h|--help)
      echo "Kullanim: bash scripts/kos_faz.sh --komut <cmd> --ajan <ajan> -- <istem>"
      echo "  Secimli: --model <m> · --sure <saniye> · --deneme <n> · --artefakt <dosya> (tekrarlanabilir)"
      exit 0 ;;
    --)         shift; ISTEM="$*"; break ;;
    *)          echo "FAIL: bilinmeyen bayrak '$1'" >&2; exit 64 ;;
  esac
done

if [ -z "$KOMUT" ] || [ -z "$AJAN" ] || [ -z "$ISTEM" ]; then
  echo "FAIL: --komut, --ajan ve -- <istem> zorunludur" >&2
  exit 64
fi

# ------------------------------------------------ O3-04  TEMIZ-AGAC KAPISI
# Taban (BASELINE) KIRLI agacta olculurse yeni testler `test_adlari`na sizar
# ve RECK-07 + `kosan>=taban` ayirt edicileri zehirlenir (OLCUM-03 O3-04,
# canli olculdu: kosan=9 >= taban=9). Bu yuzden kod-faz0 YALNIZ temiz agacta
# baslar. Kurulumun kendi kalintilari (.gitignore, kod_profil.json, scripts/)
# once commit'lenmelidir. Sinirlar (bilerek):
#   - `_KOSU/` hattin kendi artefakt dizinidir, kirilik SAYILMAZ.
#   - git depo olmayan yerde kapi sessiz gecer (taban zaten HEAD'e baglanamaz).
if [ "$KOMUT" = "kod-faz0" ]; then
  _PORSELEN=$(git status --porcelain 2>/dev/null | grep -v "^?? _KOSU/" || true)
  if [ -n "$_PORSELEN" ]; then
    echo "DURDU — kod-faz0 TEMIZ OLMAYAN agacta baslatilamaz (O3-04 kapisi)." >&2
    echo "        Kirli agacta olculen taban RECK-07'yi zehirler." >&2
    echo "        Once kurulum artefaktlarini commit'leyin:" >&2
    git status --short >&2
    echo "        Ardindan kod-faz0'i yeniden surun." >&2
    exit 1
  fi
fi

if ! command -v opencode >/dev/null 2>&1; then
  echo "FAIL: opencode bulunamadi — faz CALISTIRILMADI (fail-closed)" >&2
  exit 65
fi
command -v timeout >/dev/null 2>&1 || { echo "FAIL: 'timeout' yok (coreutils gerekli)" >&2; exit 65; }

mkdir -p "$LOGDIZIN"
CIK="$LOGDIZIN/$KOMUT.out"; HATA="$LOGDIZIN/$KOMUT.err"

ARGS=(run --command "$KOMUT" --auto)
[ -n "$MODEL" ] && ARGS+=(-m "$MODEL")

SON_EXIT=124
for ((d = 1; d <= DENEME; d++)); do
  echo "### $KOMUT deneme $d/$DENEME (zaman asimi ${SURE}s)" >&2
  KOD_KOS_FAZ_AKTIF="$KOMUT" timeout "$SURE" opencode "${ARGS[@]}" "$ISTEM" > "$CIK" 2> "$HATA"
  SON_EXIT=$?
  echo "### deneme $d exit=$SON_EXIT · stdout=$(wc -l < "$CIK") satir · stderr=$(wc -l < "$HATA") satir" >&2
  [ "$SON_EXIT" -ne 124 ] && break
done

if [ "$SON_EXIT" -eq 124 ]; then
  echo "DURDU — $KOMUT: $DENEME denemenin hepsi ${SURE}s'de asildi (exit=124). Oturum kurulmadi."
  echo "OLCULMEYEN: $KOMUT hic kosmadi · hangi_karari_etkiler: bu fazin ciktisi yok · siddet: P0"
  exit 3
fi

# --- K5: ajan gercekten istenen ajan miydi ---
if grep -qa "Falling back to default agent" "$HATA"; then
  echo "DURDU — $KOMUT: istenen ajan '$AJAN' ALT AJAN oldugu icin duruldu ve"
  echo "        varsayilan ajan kostu. Ajanin istem metni ve IZIN BLOGU uygulanmadi."
  echo "        Kanit: $(grep -a -m1 'Falling back' "$HATA" | tr -d '\033')"
  exit 2
fi
BANNER=$(grep -a -m1 '^> ' "$HATA" | sed 's/\x1b\[[0-9;]*m//g' | sed 's/^> //')
KOSAN_AJAN=$(printf '%s' "$BANNER" | awk -F' · ' '{print $1}' | tr -d ' ')
if [ -n "$KOSAN_AJAN" ] && [ "$KOSAN_AJAN" != "$AJAN" ]; then
  echo "DURDU — $KOMUT: beklenen ajan '$AJAN', kosan ajan '$KOSAN_AJAN'."
  echo "        Kanit banner: $BANNER"
  exit 2
fi

# --- O4-01: --artefakt HIC verilmediyse K17 kapanisi KOSMUYOR ---
# OLCUM-04 (24.08.2026): bayrak verilmeden kosunca ajan onay sorup dursa bile
# betik `OK — kod-faz0 · artefakt=0` yazip exit=0 veriyordu. K17'nin kapanisi
# operatorun bayragi HATIRLAMASINA bagliydi; hatirlamazsa fail-OPEN.
if [ "${#ARTEFAKTLAR[@]}" -eq 0 ]; then
  echo "UYARI — $KOMUT: --artefakt HIC verilmedi. ARTEFAKT DENETIMI YAPILMADI (O4-01)."
  echo "        'Ajan kostu ama uretmedi' durumu bu kosuda YAKALANAMAZ (K17 kapanisi kapali)."
  echo "        Dogrusu: --artefakt '_KOSU/00-KFAZ-0-*.md' gibi en az bir kalip verin."
  echo "OLCULMEYEN: $KOMUT artefakt denetimi CALISTIRILMADI · siddet: P1"
  ARTEFAKT_DENETIMI="YOK"
else
  ARTEFAKT_DENETIMI="VAR"
fi

# --- K17: artefakt gercekten olustu mu (onay cikmazi fail-OPEN'i kapatir) ---
EKSIK=0
for kalip in ${ARTEFAKTLAR+"${ARTEFAKTLAR[@]}"}; do
  # shellcheck disable=SC2086
  if ! compgen -G "$kalip" > /dev/null; then
    echo "EKSIK ARTEFAKT: $kalip"
    EKSIK=$((EKSIK + 1))
  else
    for f in $kalip; do echo "OK ARTEFAKT: $f ($(wc -c < "$f" | tr -d ' ') bayt)"; done
  fi
done
if [ "$EKSIK" -gt 0 ]; then
  echo "DURDU — $KOMUT: ajan exit=$SON_EXIT ile bitti ama $EKSIK artefakt URETILMEDI."
  echo "        En sik sebep: ajan insan onayi sordu ve bassiz kosuda cevap gelmedi."
  echo "        Devam icin: opencode run -c --auto \"EVET, yaz. Soru sorma.\""
  echo "        Ajanin son satiri: $(tail -1 "$CIK" | cut -c1-160)"
  exit 4
fi

# --- O3-08: ajan sifir-disi exit verdiyse "OK" YAZILMAZ.
# Olculen kirik: KFAZ1'de ajan exit=1 (kota hatasi) ile bitti, artefakt vardi ve
# betik "OK — kod-faz1 · exit=1" yazdi. Cikis kodu durusttu ama INSANIN ve
# `grep 'OK —'` yapan bir sarmalayicinin okudugu satir yaniltiyordu.
if [ "$SON_EXIT" -ne 0 ]; then
  echo "DURDU — $KOMUT: artefakt(lar) var ama ajan exit=$SON_EXIT ile bitti."
  echo "        Artefakt bu kosudan mi, onceki denemeden mi KALMA — dogrulanmadi."
  echo "        stderr son satiri: $(tail -1 "$HATA" | sed 's/\x1b\[[0-9;]*m//g' | cut -c1-160)"
  exit "$SON_EXIT"
fi
echo "OK — $KOMUT · ajan=$AJAN · exit=$SON_EXIT · artefakt=${#ARTEFAKTLAR[@]} · artefakt_denetimi=$ARTEFAKT_DENETIMI"
exit "$SON_EXIT"
