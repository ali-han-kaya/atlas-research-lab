#!/usr/bin/env python3
"""meal_farki.py — ayni ayetin farkli Turkce meallerinde ne kadar farkli oldugunu olcer.

NEDEN (7 Kasim 2026, OLCULMEYEN kalem 7): ayet ozetleri yalniz `tr.diyanet`
edition'i ile karsilastirildi. "Baska mealde tutmuyor olabilir" itirazi
olculmemisti. Bu betik **olcer**: 11 Turkce meal arasinda kelime kumesi
ortakligini hesaplar.

OLCUT:
  - Her meal icin ceviri normalize edilip **icerik kelimeleri** cikarilir.
  - Cift bazinda Jaccard: |kesisim| / |birlesim|.
  - `EN_AZ` = en dusuk Jaccard cifti (en farkli iki meal).
  - Yorum: Jaccard dusukse "tek meale dayanma" riski yuksektir.

Kullanim:
    python3 scripts/meal_farki.py                 # canli (ag), snapshot'a duser
    python3 scripts/meal_farki.py 4:58            # tek ayet
    python3 scripts/meal_farki.py --snapshot      # AG YOK: yalniz snapshot

[DUZELTME 13 Kasim 2026, Z16c] NEDEN `--snapshot`: bu betik olcum uretiyordu
ama KAPI DEGILDI — yani "meal farki olculdu" iddiasi her kosuda dogrulanmiyordu
(EK 81 OLCULMEYEN). KapIya baglamak icin once AGA BAGIMLI OLMAKTAN cikmasi
gerekiyordu: ag kapaliyken `OLCULEMEDI` verip rc=1 donuyordu (olculdu), yani
kapI her agsiz kosuda KIRMIZI olurdu.

`scripts/tests/snapshot/` altinda 12 ayet x 9 meal ZATEN var (snapshot_yenile.py
uretiyor, SNAPSHOT.sha256 ile sabitlenmis). Betik artik once CANLI dener, ag
yoksa/`--snapshot` verilmisse **snapshot'tan** okur ve hangi kaynagi kullandigini
ciktida SOYLER (`KAYNAK:`). Sessiz dusme yok: dusme varsa gorunur.

Cikti (ham):
    4:58    meal=11  en_az=0.31 (tr.golpinarli ~ tr.diyanet)  ort=0.55
    ...
    SONUC: 6/6 ayet olculdu · en dusuk Jaccard 0.31

Exit: 0 = olcum tamam · 1 = ag hatasi (hicbir ayet olculemedi) · 2 = kullanim
"""
import json
import os
import re
import sys
import unicodedata
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

EDITIONLAR = ["tr.diyanet", "tr.ates", "tr.bulac", "tr.golpinarli", "tr.ozturk",
              "tr.vakfi", "tr.yazir", "tr.yildirim", "tr.yuksel"]

# ORNEKLEM TEK KAYNAKTAN (14 Kasim 2026, Z21c / C-#2): bkz.
# scripts/ayetler.py. Burada ATAMA YOK; `C15m` bunu denetler.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ayetler import AYETLER  # noqa: E402


STOPWORD = {
    "allah", "icin", "kadar", "daha", "ancak", "veya", "bile", "sonra", "uzere",
    "eger", "hakkinda", "olarak", "oldugu", "olan", "bir", "ve", "bu", "su", "o",
    "da", "de", "ki", "mi", "mu", "ne", "her", "ile", "gibi", "cok", "en", "ya",
    "hem", "ise", "yalniz", "baska", "kendi", "butun", "hic", "dahi", "artik",
    "size", "onlara", "siz", "onlar", "biz", "ben", "sizi", "sizin",
}


def tr(s):
    s = s.replace("ı", "i").replace("İ", "i").replace("I", "i")
    s = s.replace("Ş", "s").replace("ş", "s").replace("Ğ", "g").replace("ğ", "g")
    s = s.replace("Ü", "u").replace("ü", "u").replace("Ö", "o").replace("ö", "o")
    s = s.replace("Ç", "c").replace("ç", "c").replace("Â", "a").replace("â", "a")
    s = s.replace("Î", "i").replace("î", "i").replace("Û", "u").replace("û", "u")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return " ".join(s.split())


def kelimeler(metin):
    k = set()
    for w in tr(metin).split():
        if len(w) > 3 and w not in STOPWORD and not w.isdigit():
            k.add(w[:max(4, len(w) - 2)])
    return k


SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "tests", "snapshot")


def snapshot_yolu(ayet, edition):
    """`snapshot_yenile.py`nin urettigi dosya adi: ayet_4-58__tr.diyanet.json"""
    return os.path.join(SNAP, "ayet_%s__%s.json"
                        % (ayet.replace(":", "-"), edition))


def _snapshot_oku(ayet, edition):
    with open(snapshot_yolu(ayet, edition), encoding="utf-8") as f:
        return json.load(f)["data"]["text"]


def ceviri(ayet, edition, yalniz_snapshot=False):
    """Once CANLI; olmazsa (veya `--snapshot`) yerel snapshot.

    Donus: (metin, kaynak) — kaynak 'canli' | 'snapshot'. Kaynagi cagirana
    soylemek zorundayiz: aksi halde "olctum" cumlesi hangi veriyle olctugunu
    saklar.
    """
    if yalniz_snapshot:
        return _snapshot_oku(ayet, edition), "snapshot"
    url = ("https://api.alquran.cloud/v1/ayah/%s/%s" % (ayet, edition))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))["data"]["text"], "canli"
    except Exception:
        return _snapshot_oku(ayet, edition), "snapshot"


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def main(argv):
    yalniz_snapshot = "--snapshot" in argv
    duz = [a for a in argv[1:] if not a.startswith("-")]
    ayetler = [duz[0]] if duz and ":" in duz[0] else AYETLER
    olculen, en_dusuk = 0, (1.0, "", "")
    kaynaklar = set()

    for ayet in ayetler:
        kumeler = {}
        for ed in EDITIONLAR:
            try:
                metin, kaynak = ceviri(ayet, ed, yalniz_snapshot)
                kumeler[ed] = kelimeler(metin)
                kaynaklar.add(kaynak)
            except Exception:
                pass
        if len(kumeler) < 2:
            print("%-7s -> OLCULEMEDI (meal sayisi %d)" % (ayet, len(kumeler)))
            continue
        ciftler = []
        anahtarlar = sorted(kumeler)
        for i in range(len(anahtarlar)):
            for j in range(i + 1, len(anahtarlar)):
                a, b = anahtarlar[i], anahtarlar[j]
                ciftler.append((jaccard(kumeler[a], kumeler[b]), a, b))
        ciftler.sort()
        en_az = ciftler[0]
        ort = sum(c[0] for c in ciftler) / len(ciftler)
        olculen += 1
        if en_az[0] < en_dusuk[0]:
            en_dusuk = (en_az[0], en_az[1] + " ~ " + en_az[2], ayet)
        print("%-7s meal=%d  en_az=%.2f (%s ~ %s)  ort=%.2f"
              % (ayet, len(kumeler), en_az[0], en_az[1], en_az[2], ort))

    if not olculen:
        print("SONUC: OLCULEMEDI — hicbir ayet olculemedi (ag ve snapshot?)",
              file=sys.stderr)
        return 1
    print("KAYNAK: %s" % ("+".join(sorted(kaynaklar)) or "?"))
    print("SONUC: %d/%d ayet olculdu · en dusuk Jaccard %.2f (%s, ayet %s)"
          % (olculen, len(ayetler), en_dusuk[0], en_dusuk[1], en_dusuk[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
