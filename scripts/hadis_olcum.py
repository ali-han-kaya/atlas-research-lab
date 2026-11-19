#!/usr/bin/env python3
"""hadis_olcum.py — SKILL.md icindeki Arapca hadis alintilarinin kelime sayimini olcer.

NEDEN (7 Kasim 2026, dis denetim D2): `SKILL.md` "34 kelime" ve "18 kelime"
diyordu ama satirda komut/ham cikti/exit yoktu; 5/18 dis model bunu
KAPATMADI saydi. §12 "komut + ham cikti + kod" ister. Bu betik o komuttur.

Kullanim:
    python3 scripts/hadis_olcum.py SKILL.md [--bekle 34 18]

Cikti (ham):
    L457: ham_kelime=34 harakatsiz_kelime=34
    L463: ham_kelime=18 harakatsiz_kelime=18

Exit: 0 = olcum yapildi ve `--bekle` verildiyse sayilar tutuyor
      1 = sayi tutmuyor (iddia bayat) veya alinti bulunamadi
      2 = kullanim hatasi / dosya yok
"""
import re
import sys
import unicodedata

ARAPCA = re.compile(r"`([\u0600-\u06FF][^`]*)`")


def olc(yol):
    """(satir_no, ham_kelime, harakatsiz_kelime) listesi dondurur."""
    try:
        with open(yol, encoding="utf-8") as f:
            satirlar = f.read().split("\n")
    except OSError as e:
        print(f"HATA: {yol} okunamadi: {e}", file=sys.stderr)
        raise SystemExit(2)

    sonuc = []
    for i, satir in enumerate(satirlar, 1):
        if "Arapca" not in satir and "\u0600" not in satir:
            continue
        m = ARAPCA.search(satir)
        if not m:
            continue
        alinti = m.group(1)
        harakatsiz = "".join(c for c in alinti if not unicodedata.combining(c))
        sonuc.append((i, len(alinti.split()), len(harakatsiz.split())))
    return sonuc


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    yol = argv[1]
    bekle = None
    if "--bekle" in argv:
        k = argv.index("--bekle")
        bekle = [int(x) for x in argv[k + 1:]]

    satirlar = olc(yol)
    if not satirlar:
        print("HATA: Arapca alinti bulunamadi", file=sys.stderr)
        return 1

    for n, ham, harakatsiz in satirlar:
        print(f"L{n}: ham_kelime={ham} harakatsiz_kelime={harakatsiz}")

    if bekle is not None:
        olculen = [h for _, h, _ in satirlar]
        if olculen != bekle:
            print(f"UYUSMAZLIK: olculen={olculen} beklenen={bekle}", file=sys.stderr)
            return 1
        print(f"UYUM: {len(olculen)} alinti, sayilar tutuyor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
