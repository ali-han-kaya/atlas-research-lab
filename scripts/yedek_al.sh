#!/usr/bin/env bash
# ATLAS yerel yedek — tam git bundle + geri yuklenebilirlik dogrulamasi.
#
# Ne yapar:
#   1. Depodaki TUM refleri (dallar, etiketler, isaretciler) tek dosyada toplar.
#   2. `git bundle verify` ile dosyanin eksiksiz oldugunu dogrular.
#   3. Gecici bir klasore klonlayip HEAD'in birebir ayni oldugunu ve `git fsck`
#      temiz gectigini olcer. Kopya yalniz /tmp altinda olusur ve betik cikista
#      onu siler; depoya ve gecmise hicbir sey yazmaz.
#
# Kullanim:
#   scripts/yedek_al.sh [depo-koku] [hedef-dizin]
#
#   depo-koku    : varsayilan, bu betigin bulundugu depo
#   hedef-dizin  : varsayilan $ATLAS_YEDEK_DIZIN veya $HOME/atlas-yedek
#
# Ornek:
#   scripts/yedek_al.sh . "$HOME/atlas-yedek"
set -euo pipefail

LAB="${1:-$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)}"
HEDEF="${2:-${ATLAS_YEDEK_DIZIN:-$HOME/atlas-yedek}}"
TS="$(date +%Y%m%d-%H%M%S)"
BUNDLE="$HEDEF/atlas-$TS.bundle"

mkdir -p "$HEDEF"

echo "YEDEK — kaynak: $LAB"
git -C "$LAB" bundle create "$BUNDLE" --all
git -C "$LAB" bundle verify "$BUNDLE"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/atlas-yedek-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

git clone --quiet "$BUNDLE" "$TMP/kopya"
YEREL="$(git -C "$LAB" rev-parse HEAD)"
KOPYA="$(git -C "$TMP/kopya" rev-parse HEAD)"
if [ "$YEREL" != "$KOPYA" ]; then
    echo "YEDEK FAIL — HEAD uyusmuyor: kaynak=$YEREL kopya=$KOPYA" >&2
    exit 1
fi
git -C "$TMP/kopya" fsck --full --no-progress >/dev/null

BOYUT="$(wc -c < "$BUNDLE" | tr -d ' ')"
echo "YEDEK PASS — $BUNDLE"
echo "  HEAD=$YEREL · commit=$(git -C "$LAB" rev-list --count HEAD) · bayt=$BOYUT"
