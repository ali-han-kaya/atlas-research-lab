#!/usr/bin/env python3
"""injection_sayac.py — `INJECTION_ATTEMPT=<n>` ile `durum.json.injection` sayisini karsilastirir.

NEDEN (7 Kasim 2026, kalem 8): `SKILL.md` §8.2/6 sarti `n == len(durum.json.injection)`
diyor ama bunu **elle** denetliyordu; `C13t` yalnizca metnin VARLIGINI olcuyordu.
Bu betik sarti CALISTIRIR.

Kullanim:
    python3 scripts/injection_sayac.py <teslim_manifesti.md> <durum.json>

Cikti (ham):
    MANIFEST: INJECTION_ATTEMPT=2
    DURUM   : injection=2 kayit
    UYUM    : evet

Exit:
    0 = uyum (sayilar esit)
    1 = UYUMSUZLUK veya alan eksik (fail-closed)
    2 = kullanim hatasi / dosya okunamadi

Not: `INJECTION_ATTEMPT=<n>` **0 da yazilir** — alanin YOKLUGU uyumsuzluktur,
"0 sayilir" degildir (SKILL.md §8.1: alan her zaman tasinir).
"""
import json
import re
import sys

DESEN = re.compile(r"INJECTION_ATTEMPT\s*=\s*(\d+)")


def manifest_sayi(yol):
    try:
        with open(yol, encoding="utf-8") as f:
            metin = f.read()
    except OSError as e:
        print("HATA: manifest okunamadi: %s" % e, file=sys.stderr)
        raise SystemExit(2)
    bulunan = DESEN.findall(metin)
    if not bulunan:
        return None
    if len(set(bulunan)) > 1:
        return ("CELISKI", bulunan)
    return int(bulunan[0])


def durum_sayi(yol):
    try:
        with open(yol, encoding="utf-8") as f:
            d = json.load(f)
    except OSError as e:
        print("HATA: durum.json okunamadi: %s" % e, file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print("HATA: durum.json bozuk: %s" % e, file=sys.stderr)
        raise SystemExit(2)
    if "injection" not in d:
        # SKILL.md: eksik anahtar BOS KUME sayilir — sessiz gecme, ama olcum de dogru olsun
        return ("EKSIK_ANAHTAR", 0)
    if not isinstance(d["injection"], list):
        return ("TIP_HATASI", None)
    return ("VAR", len(d["injection"]))


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    m, d = argv[1], argv[2]

    n = manifest_sayi(m)
    if n is None:
        print("MANIFEST: INJECTION_ATTEMPT alani YOK")
        print("UYUM    : HAYIR (alan her zaman tasinir; 0 da yazilir)", file=sys.stderr)
        return 1
    if isinstance(n, tuple):
        print("MANIFEST: CELISKI %s" % (n[1],))
        print("UYUM    : HAYIR (ayni manifestte iki farkli sayi)", file=sys.stderr)
        return 1
    print("MANIFEST: INJECTION_ATTEMPT=%d" % n)

    durum, uzunluk = durum_sayi(d)
    if durum == "TIP_HATASI":
        print("DURUM   : injection TIP_HATASI (liste bekleniyordu)")
        print("UYUM    : HAYIR (fail-closed)", file=sys.stderr)
        return 1
    if durum == "EKSIK_ANAHTAR":
        print("DURUM   : injection anahtari YOK -> bos kume sayilir (0)")
    else:
        print("DURUM   : injection=%d kayit" % uzunluk)

    if n == uzunluk:
        print("UYUM    : evet")
        return 0
    print("UYUM    : HAYIR (manifest=%d, durum=%d)" % (n, uzunluk), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
