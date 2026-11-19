#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""token_olcum.py — denetim paketlerinin GERÇEK token sayısı.

NEDEN VAR (9 Kasım 2026): Bir tur boyunca «bayt ÷ 4» tahmini yazdım ve
**%33 yanlıştı** (Türkçe daha çok token harcıyor). Tahmin, ölçüm gibi
görünüyordu. Bu betik tahmini KALDIRIR: `tiktoken` varsa gerçek sayıyı verir,
yoksa **OLCULMEDI** yazar — uydurmaz.

NEDEN AYRI BETİK: `tiktoken` lab ortamının bağımlılığı değil (venv'de).
Betik iki yolda da doğru davranır:
  * tiktoken var  -> gerçek sayı + kodlama adı
  * tiktoken yok  -> exit 2 + `OLCULMEDI` + kurulum komutu

KULLANIM
    python3 scripts/token_olcum.py                    # 3 paket + eser
    python3 scripts/token_olcum.py docs/...md ...     # seçili dosyalar
    python3 scripts/token_olcum.py --json             # makine okunur

KURULUM (venv, sistem python'unu bozmadan)
    python3 -m venv .venv-token
    .venv-token/bin/pip install tiktoken
    .venv-token/bin/python scripts/token_olcum.py
"""

import json
import os
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BURASI)

VARSAYILAN = [
    "docs/DIS_DENETIM_TUR4_P1.md",
    "docs/DIS_DENETIM_TUR4_P2.md",
    "SKILL.md",
]
KODLAMALAR = ("o200k_base", "cl100k_base")


def _tarih():
    import datetime
    return datetime.date.today().isoformat()


def _paket_no(ad):
    """`..._P1.md` ve `...P1_...` adlarinin IKISINI de yakalar.

    NEDEN (12 Kasim 2026, olculdu): eski kod `"P1_" in ad` ariyordu; gercek
    dosya adi `DIS_DENETIM_TUR4_P1.md` -> `_P1.` var, `P1_` YOK. Bu yuzden
    "P1+P2 birlikte" ozet satiri HIC basilmadi ve bu sessizce fark edilmedi.
    Adlandirma degisse de calissin diye iki bicim de kabul edilir.
    """
    for no in ("P1", "P2"):
        if no + "_" in ad or "_" + no + "." in ad:
            return no
    return None


def _aday_yollar():
    """Bugünün paketleri yoksa en yeni tarihliyi bul (dün üretilmiş olabilir)."""
    import glob
    yol = []
    for kalip in VARSAYILAN:
        if "{tarih}" not in kalip:
            yol.append(kalip)
            continue
        # ONCE bugunun dosyasi; yoksa en yeni tarihli — ama `P1_`/`P2_` HARIC
        # (joker `DIS_DENETIM_TUR4_*.md` parcalari da yakalar; 9 Kasim 2026'da
        #  yasanan hata: "tek dosya" sanilan sey P2 cikti ve P2 iki kez basildi).
        on, son = kalip.split("{tarih}")
        bugun = os.path.join(KOK, on + _tarih() + son)
        if os.path.exists(bugun):
            yol.append(os.path.relpath(bugun, KOK))
            continue
        duz = [p for p in glob.glob(os.path.join(KOK, on + "*" + son))
               if "_P1_" not in p and "_P2_" not in p]
        if duz:
            yol.append(os.path.relpath(sorted(duz)[-1], KOK))
    return yol


def main(argv):
    if "--json" in argv:
        argv = [a for a in argv if a != "--json"]
        makine = True
    else:
        makine = False
    secili = [a for a in argv[1:] if not a.startswith("-")]
    yollar = secili or _aday_yollar()

    try:
        import tiktoken
    except ImportError:
        print("OLCULMEDI: tiktoken kurulu degil — token sayisi UYDURULMAZ.")
        print("  Kurulum: python3 -m venv .venv-token && "
              ".venv-token/bin/pip install tiktoken")
        print("  Sonra : .venv-token/bin/python scripts/token_olcum.py")
        print("  NOT   : bayt/4 TAHMINI %33 yanlisti (9 Kasim 2026'da olculdu).")
        return 2

    enc = {ad: tiktoken.get_encoding(ad) for ad in KODLAMALAR}
    satirlar = []
    for rel in yollar:
        tam = rel if os.path.isabs(rel) else os.path.join(KOK, rel)
        if not os.path.exists(tam):
            satirlar.append({"dosya": rel, "durum": "YOK"})
            continue
        with open(tam, encoding="utf-8") as f:
            metin = f.read()
        satirlar.append({
            "dosya": rel,
            "bayt": os.path.getsize(tam),
            "token": {ad: len(enc[ad].encode(metin)) for ad in KODLAMALAR},
            "durum": "OK",
        })

    if makine:
        print(json.dumps({"tiktoken": tiktoken.__version__,
                          "olculen": satirlar}, ensure_ascii=False, indent=2))
        return 0

    print("tiktoken %s · kodlamalar: %s" % (tiktoken.__version__,
                                            ", ".join(KODLAMALAR)))
    print("%-46s %8s %9s %9s" % ("dosya", "bayt", KODLAMALAR[0], KODLAMALAR[1]))
    for s in satirlar:
        if s["durum"] != "OK":
            print("%-46s %8s %9s %9s" % (s["dosya"], "-", "-", "-"))
            continue
        print("%-46s %8d %9d %9d" % (s["dosya"], s["bayt"],
                                     s["token"][KODLAMALAR[0]],
                                     s["token"][KODLAMALAR[1]]))
    # P1 + P2 birlikte okunursa
    p1 = next((s for s in satirlar if _paket_no(s["dosya"]) == "P1"), None)
    p2 = next((s for s in satirlar if _paket_no(s["dosya"]) == "P2"), None)
    if p1 and p2 and p1["durum"] == p2["durum"] == "OK":
        print("\nP1+P2 birlikte: %d token (%s) · %d token (%s)"
              % (p1["token"][KODLAMALAR[0]] + p2["token"][KODLAMALAR[0]],
                 KODLAMALAR[0],
                 p1["token"][KODLAMALAR[1]] + p2["token"][KODLAMALAR[1]],
                 KODLAMALAR[1]))
        print("NOT: bolmek TOPLAMI kucultmez; faydasi KISMI OKUMA'dir "
              "(denetci yalniz P1'i okur).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
