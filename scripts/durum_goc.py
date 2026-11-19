#!/usr/bin/env python3
"""durum_goc.py — eski `durum.json` semasini guncel semaya tasir (geriye uyum).

NEDEN (7 Kasim 2026, kalem 7): `SKILL.md` icinde `sir` gocu **kurali** yaziliydi
ama diskte `durum.json` **0 adet** oldugu icin goc **hic calistirilmamisti**.
"Kural var, mekanizma yok" — labin tekrar eden hastaligi (D19 dersi).

KURAL (SKILL.md §1.1):
  - okuyucu: eksik `sir` anahtarini `[]` sayar (OLCULMEDI degil, BOS KUME)
  - yazici : her guncellemede anahtari ekler
  - goc    : **veri degismez** — yalnizca eksik anahtar eklenir

Kullanim:
    python3 scripts/durum_goc.py <durum.json>          # goc eder (yerinde yazar)
    python3 scripts/durum_goc.py <durum.json> --kuru   # yalnizca rapor, yazmaz

Exit:
    0 = goc yapildi / gerek yoktu (kuru kosuda: rapor verildi)
    1 = dosya okunamadi, JSON bozuk veya anahtar TIP HATASI (fail-closed)
    2 = kullanim hatasi

Cikti (ham, ornek):
    ONCE: sir=<yok> injection=[] anahtar=11
    EKLENEN: sir
    SONRA: sir=[] injection=[] anahtar=12
    VERI_DEGISMEDI: evet (sir disindaki tum anahtarlar bayt-ayni)
"""
import json
import sys

ZORUNLU = ("sir", "injection")


def oku(yol):
    try:
        with open(yol, encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        print("HATA: okunamadi: %s" % e, file=sys.stderr)
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        print("HATA: JSON bozuk: %s" % e, file=sys.stderr)
        raise SystemExit(1)


def tarif(d, anahtar):
    """Anahtarin durumunu tek kelimeyle soyler: yok / tip-hatasi / <deger ozeti>."""
    if anahtar not in d:
        return "yok"
    v = d[anahtar]
    if not isinstance(v, list):
        return "TIP_HATASI(%s)" % type(v).__name__
    return "%d kayit" % len(v)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    yol = argv[1]
    kuru = "--kuru" in argv

    onceki = oku(yol)
    print("ONCE: " + " ".join("%s=%s" % (a, tarif(onceki, a)) for a in ZORUNLU)
          + " anahtar=%d" % len(onceki))

    # FAIL-CLOSED (7 Kasim 2026, olcum M3): anahtar VAR ama tipi list degilse
    # goc sessizce gecmemeli. Eksik anahtar `[]` sayilir; BOZUK anahtar sayilmaz.
    # Aksi halde `sir:"x"` tasiyan dosya "goc edildi" damgasi alip bozuk kalirdi.
    bozuk = [a for a in ZORUNLU if a in onceki and not isinstance(onceki[a], list)]
    if bozuk:
        print("HATA: tip hatasi (liste bekleniyordu): " + " · ".join(bozuk),
              file=sys.stderr)
        print("GOC_YAPILMADI: veri bozuk, elle duzeltilmeli", file=sys.stderr)
        return 1

    eklenen = []
    for a in ZORUNLU:
        if a not in onceki:
            onceki[a] = []          # eksik anahtar BOS KUME sayilir (OLCULMEDI degil)
            eklenen.append(a)

    if not eklenen:
        print("EKLENEN: (yok)")
        print("SONRA: " + " ".join("%s=%s" % (a, tarif(onceki, a)) for a in ZORUNLU)
              + " anahtar=%d" % len(onceki))
        print("GOC_GEREKMEDI: evet")
        return 0

    print("EKLENEN: " + " · ".join(eklenen))

    # veri degismedi mi: eklenen anahtarlar cikarilinca onceki sozluk bayt-ayni mi
    kopya = {k: v for k, v in onceki.items() if k not in eklenen}
    if kuru:
        print("KURU_KOSU: yazilmadi")
        return 0

    with open(yol, "w", encoding="utf-8") as f:
        json.dump(onceki, f, ensure_ascii=False)
        f.write("\n")

    geri = oku(yol)
    temiz = {k: v for k, v in geri.items() if k not in eklenen}
    print("SONRA: " + " ".join("%s=%s" % (a, tarif(geri, a)) for a in ZORUNLU)
          + " anahtar=%d" % len(geri))
    print("VERI_DEGISMEDI: %s" % ("evet" if temiz == kopya else "HAYIR — GERI AL"))
    return 0 if temiz == kopya else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
