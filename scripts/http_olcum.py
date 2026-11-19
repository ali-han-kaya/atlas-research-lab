#!/usr/bin/env python3
"""http_olcum.py — verilen URL'ler icin HTTP durum kodunu ham olarak yazar.

NEDEN (7 Kasim 2026, dis denetim D4/D21): `SKILL.md` "curl/urllib ayni gun 403"
diyordu ama o gunun ciktisi dosyada yoktu; ayrica `urllib -> 200 200` iddiasinin
komutu hic kaydedilmemisti. §12 "komut + ham cikti + kod" ister; bu betik
tekrarlanabilir komutun kendisidir.

Kullanim:
    python3 scripts/http_olcum.py <url> [<url> ...]

Cikti (ham, her URL icin bir satir):
    <url> -> 403
    <url> -> HTTPError 403
    <url> -> ERR URLError ...

Exit: 0 = her URL olculdu (durum ne olursa olsun; 403 de bir OLCUMDUR)
      2 = kullanim hatasi
"""
import sys
import urllib.error
import urllib.request


def olc(url, zaman_asimi=20):
    try:
        with urllib.request.urlopen(url, timeout=zaman_asimi) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:
        return "HTTPError %d" % e.code
    except Exception as e:                      # ag yok / DNS / timeout
        return "ERR %s %s" % (type(e).__name__, e)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    for url in argv[1:]:
        print("%s -> %s" % (url, olc(url)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
