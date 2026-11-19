#!/usr/bin/env bash
# sync_worktree.sh — bir worktree HEAD'ini ana depoya yalniz fast-forward ile tasir.
#
# Kullanim:
#   sync_worktree.sh [--dry-run] <worktree_yolu>
#
# Betik ANA DEPODA calistirilir. Kaynak worktree'de gecici bir dal olusturur,
# bu dali ana depoya FETCH_HEAD olarak ceker, --ff-only ile birlestirir ve
# gecici dali kaynak worktree'den siler. Hata halinde de gecici dali temizler.

set -uo pipefail

KURU=0
WORKTREE=""

kullanim() {
  echo "Kullanim: sync_worktree.sh [--dry-run] <worktree_yolu>" >&2
}

hata() {
  echo "FAIL: $*" >&2
  exit 1
}

komut_goster() {
  printf '  +'
  printf ' %q' "$@"
  printf '\n'
}

calistir() {
  komut_goster "$@"
  if [ "$KURU" -eq 1 ]; then
    return 0
  fi
  if ! "$@"; then
    hata "komut basarisiz: $1"
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) KURU=1 ;;
    -h|--help) kullanim; exit 0 ;;
    -*) kullanim; echo "FAIL: bilinmeyen bayrak: $1" >&2; exit 64 ;;
    *)
      [ -z "$WORKTREE" ] || { kullanim; exit 64; }
      WORKTREE="$1"
      ;;
  esac
  shift
done

[ -n "$WORKTREE" ] || { kullanim; exit 64; }
[ -d "$WORKTREE" ] || hata "worktree dizini yok: $WORKTREE"

ANA_REPO=$(git rev-parse --show-toplevel 2>/dev/null) || hata "ana dizin bir Git deposu degil"
WORKTREE=$(cd "$WORKTREE" 2>/dev/null && pwd) || hata "worktree yolu cozumlenemedi"
git -C "$WORKTREE" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || hata "kaynak yol bir Git worktree degil: $WORKTREE"

[ -z "$(git -C "$ANA_REPO" status --porcelain)" ] \
  || hata "ana repo temiz degil; senkronizasyon durduruldu"
[ -z "$(git -C "$WORKTREE" status --porcelain)" ] \
  || hata "kaynak worktree temiz degil; yalniz commitlenmis HEAD tasinabilir"
git -C "$ANA_REPO" symbolic-ref -q HEAD >/dev/null 2>&1 \
  || hata "ana repo detached HEAD durumunda"

KAYNAK_COMMIT=$(git -C "$WORKTREE" rev-parse --verify HEAD 2>/dev/null) \
  || hata "worktree HEAD okunamadi"
GECICI_DIZIN=$(mktemp -d "${TMPDIR:-/tmp}/sync-worktree.XXXXX") \
  || hata "gecici ad uretilemedi"
GECICI_DAL="temp-sync-${GECICI_DIZIN##*.}"
DAL_OLUSTU=0

temizle() {
  DURUM=$?
  trap - EXIT INT TERM
  if [ "$DAL_OLUSTU" -eq 1 ]; then
    if ! git -C "$WORKTREE" branch -D "$GECICI_DAL" >/dev/null 2>&1; then
      echo "FAIL: gecici dal temizlenemedi: $GECICI_DAL" >&2
      [ "$DURUM" -ne 0 ] || DURUM=1
    fi
  fi
  rmdir "$GECICI_DIZIN" >/dev/null 2>&1 || true
  exit "$DURUM"
}
trap temizle EXIT INT TERM

git -C "$WORKTREE" show-ref --verify --quiet "refs/heads/$GECICI_DAL" \
  && hata "gecici dal zaten var: $GECICI_DAL"

echo "ana repo       : $ANA_REPO"
echo "kaynak worktree: $WORKTREE"
echo "kaynak commit  : $KAYNAK_COMMIT"
echo "gecici dal     : $GECICI_DAL"
[ "$KURU" -eq 1 ] && echo "DRY-RUN: Git referanslari degistirilmeyecek"

calistir git -C "$WORKTREE" branch "$GECICI_DAL" HEAD
[ "$KURU" -eq 1 ] || DAL_OLUSTU=1
calistir git -C "$ANA_REPO" fetch "$WORKTREE" "$GECICI_DAL"
calistir git -C "$ANA_REPO" merge --ff-only FETCH_HEAD
calistir git -C "$WORKTREE" branch -D "$GECICI_DAL"
DAL_OLUSTU=0

if [ "$KURU" -eq 1 ]; then
  echo "DRY-RUN PASS"
  exit 0
fi

ANA_COMMIT=$(git -C "$ANA_REPO" rev-parse --verify HEAD 2>/dev/null) \
  || hata "ana repo HEAD senkronizasyon sonrasinda okunamadi"
[ "$ANA_COMMIT" = "$KAYNAK_COMMIT" ] \
  || hata "ana repo beklenen worktree commit'ine ulasmadi"

echo "SYNC-WORKTREE PASS commit=$ANA_COMMIT"
