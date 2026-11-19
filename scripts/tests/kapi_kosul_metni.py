#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kapi_kosul_metni.py — iki `skill_lint.py` sürümü arasında KAPI KAPSAMI.

NEDEN VAR (15 Kasım 2026, Z45c): EK 115 §2/10 satırındaki ölçüm ("26 kapının
koşul metni aynı, parmak izleri döndü") **depoda olmayan** geçici bir betikle
alınmıştı; başka makinede tek komutla tekrarlanamıyordu. Ölçümü iddia eden,
ölçümü de tekrarlanabilir bırakmalıdır.

NE ÖLÇER
  1. Her kapı için **koşul metni** aynı mı (`ast.unparse(args[2])`)?
     Koşul metni değişmediyse, `kapi_farki`'nin "KOSUL_DEGISTI" demesi
     ölçütün değil **tanım grafiğinin** değiştiğini gösterir.
  2. Her kapının parmak izini oluşturan **parça sayısı** (koşul + erişilebilir
     tanımlar) ve fark: kaç parça kayboldu / eklendi.
  3. **KAYIP PARÇA CANLI MI:** kaybolan parçanın metni B dosyasında **tam satır**
     olarak duruyor mu? Duruyorsa o kod hâlâ yaşıyor ama artık kapıya bağlı
     değil — yani gerçek kör nokta. Durmuyorsa parça, silinen kodun artığıdır
     (bu turda olduğu gibi).

NORMALİZASYON — NEDEN GEREKTİ (15 Kasım 2026, ÖLÇÜLDÜ): ilk sürüm "kayıp"
parçayı B'de **tam satır** olarak arıyordu. İlk koşu `kayip 1522 · CANLI 625`
verdi ve bu sayı YANLIŞ yönlendiriciydi: Z44 kodu `_arsiv_dogrula()` içine
taşınmıştı, yani aynı ifade B'de **8 boşluk girintiyle** duruyordu. Ham metin
karşılaştırması girintiyi kimlik sanıyor.

Artık parça kimliği `ast.unparse(ast.parse(parca).body[0])` — yani **girintisiz
AST metni**. B tarafında dosyadaki TÜM `ast.stmt` düğümleri bu biçime çevrilip
küme yapılır; kayıp parça bu kümede varsa "CANLI"dır (kod yaşıyor, yalnız
kapının kapanışından çıkmış).

KALAN SINIR (gizlenmez): yeniden ADLANDIRMA hâlâ "kayıp" görünür
(`_raw` -> `_arsdo_raw`); AST metni adı taşır. Bu yüzden çıktı bir HÜKÜM değil,
insanın okuyacağı bir listedir; `SONUC` satırı yalnız sayı verir.

CIKIS KODU: 0 = kosul metni hic degismedi ve kapanis daralmadi · 1 = biri oldu
(INSAN BAKSIN; hukum degil) · 2 = kullanim hatasi.

KULLANIM
    python3 scripts/tests/kapi_kosul_metni.py --a ESKI.py --b YENI.py
    python3 scripts/tests/kapi_kosul_metni.py --a ESKI.py --b YENI.py --detay C12a
    python3 scripts/tests/kapi_kosul_metni.py --a <(git show HEAD~3:scripts/skill_lint.py) --b scripts/skill_lint.py
"""

import argparse
import ast
import os
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
sys.path.insert(0, os.path.join(KOK, "scripts"))

import kapi_farki as kf  # noqa: E402  (yol enjeksiyonundan sonra)


def _kosullar(agac):
    """kapi adi -> kosul dugumu (`k(ad, etiket, KOSUL, ayrinti)`)."""
    bulunan = {}
    for d in ast.walk(agac):
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) \
                and d.func.id == "k" and len(d.args) >= 3 \
                and isinstance(d.args[0], ast.Constant):
            ad = d.args[0].value
            if isinstance(ad, str):
                bulunan[ad] = d.args[2]
    return bulunan


def _parcalar(kosul, tanimlar):
    """Parmak izini kuran parçalar — `kapi_farki._kosul_parmak` ile ayni gezinme.

    Ayni gezinmeyi KOPYALAMAK yerine burada acikca yaziyoruz: arac `derinlik`
    parametresi aldiginda parmak izi degisiyor; bu betik o parametreyi
    KULLANMAZ (kapanis), yani `kapi_farki`'nin varsayilani degisirse buradaki
    sayilar kayar. Ayrisma olursa `SONUC` satirindaki parca sayilari ile
    `kapi_farki` ciktisi tutmaz — o zaman once araci oku.
    """
    parcalar = [ast.unparse(kosul)]
    gorulen, kuyruk = set(), [kosul]
    while kuyruk:
        yeni = []
        for dugum in kuyruk:
            for d in ast.walk(dugum):
                if isinstance(d, ast.Name) and d.id in tanimlar \
                        and d.id not in gorulen:
                    gorulen.add(d.id)
                    for kaynak in tanimlar[d.id]:
                        parcalar.append(kaynak)
                        try:
                            yeni.append(ast.parse(kaynak).body[0])
                        except SyntaxError:
                            pass
        kuyruk = yeni
    return parcalar


def _norm(kaynak):
    """Parça kimliği: girintisiz AST metni. Çözülemezse ham metne düşer."""
    try:
        return ast.unparse(ast.parse(kaynak).body[0])
    except (SyntaxError, IndexError, ValueError):
        return kaynak.strip()


def _norm_liste(parcalar):
    """Parcalari normalize edip TEKILLESTIR — iki taraf AYNI olcutle karsilastirilsin.

    NEDEN (15 Kasim 2026, OLCULDU — aracin kendi kusuru): ilk surumde "kayip"
    HAM metinle, "CANLI" ise normalize metinle karsilastiriliyordu. Iki farkli
    olcut bir arada kullanilinca ayni parca hem "kayip" hem "CANLI" gorunuyordu:
    Z44 kodu fonksiyona tasiyinca girinti degisti, ham metin farkli, normalize
    metin ayni. Cikti `kayip 1522 · CANLI 625` idi; bu sayi bir olcum degil,
    iki olcutun karisimiydi. Artik iki taraf da normalize.
    """
    return list(dict.fromkeys(_norm(x) for x in parcalar))


def _stmt_kumesi(agac):
    """B dosyasındaki TÜM deyimlerin normalize metni — 'kod hâlâ var mı' ölçütü."""
    return {ast.unparse(d) for d in ast.walk(agac) if isinstance(d, ast.stmt)}


def detay(a_yolu, b_yolu, kapi):
    """Tek kapi icin kaybolan/eklenen parcalari TEK TEK yazar.

    NEDEN: "60 parca kayboldu" bir SAYIdir; karari degistirmez. Kaybolan parca
    canli mi, silinen kodun artigi mi — ancak metni okuyunca anlasilir.
    """
    with open(a_yolu, encoding="utf-8") as f:
        a_agac = ast.parse(f.read())
    with open(b_yolu, encoding="utf-8") as f:
        b_agac = ast.parse(f.read())
    a_tan, b_tan = kf._tanimlar(a_agac), kf._tanimlar(b_agac)
    a_kos, b_kos = _kosullar(a_agac), _kosullar(b_agac)
    if kapi not in a_kos or kapi not in b_kos:
        print("HATA: kapi iki surumde de yok: %s" % kapi)
        return 2
    b_stmt = _stmt_kumesi(b_agac)
    a_p = _norm_liste(_parcalar(a_kos[kapi], a_tan))
    b_p = _norm_liste(_parcalar(b_kos[kapi], b_tan))
    kayip = [x for x in a_p if x not in set(b_p)]
    print("KAPI %s · parca(A)=%d parca(B)=%d kayip=%d"
          % (kapi, len(a_p), len(b_p), len(kayip)))
    for i, parca in enumerate(kayip, 1):
        n = _norm(parca)
        print("%2d %s %s" % (i, "CANLI " if n in b_stmt else "silinmis",
                             n.replace("\n", " ")[:150]))
    return 0


def olc(a_yolu, b_yolu):
    with open(a_yolu, encoding="utf-8") as f:
        a_agac = ast.parse(f.read())
    with open(b_yolu, encoding="utf-8") as f:
        b_agac = ast.parse(f.read())
    a_tan, b_tan = kf._tanimlar(a_agac), kf._tanimlar(b_agac)
    a_kos, b_kos = _kosullar(a_agac), _kosullar(b_agac)
    b_stmt = _stmt_kumesi(b_agac)

    ortak = sorted(set(a_kos) & set(b_kos))
    print("%-9s %-9s %8s %8s %6s %5s %s"
          % ("kapi", "kosul", "parca(A)", "parca(B)", "kayip", "yeni", "kayiptan canli"))
    ayni = degisti = 0
    toplam_kayip = canli = 0
    canli_ornek = []
    for ad in ortak:
        a_p = _norm_liste(_parcalar(a_kos[ad], a_tan))
        b_p = _norm_liste(_parcalar(b_kos[ad], b_tan))
        ayni_mi = ast.unparse(a_kos[ad]) == ast.unparse(b_kos[ad])
        ayni += ayni_mi
        degisti += (not ayni_mi)
        kayip = [x for x in a_p if x not in set(b_p)]
        yeni = [x for x in b_p if x not in set(a_p)]
        bu_canli = [x for x in kayip if _norm(x) in b_stmt]
        toplam_kayip += len(kayip)
        canli += len(bu_canli)
        if bu_canli and len(canli_ornek) < 3:
            canli_ornek.append((ad, _norm(bu_canli[0])[:60]))
        print("%-9s %-9s %8d %8d %6d %5d %d/%d%s"
              % (ad, "AYNI" if ayni_mi else "DEGISTI", len(a_p), len(b_p),
                 len(kayip), len(yeni), len(bu_canli), len(kayip),
                 ("  <- " + _norm(bu_canli[0])[:40]) if bu_canli else ""))
    print()
    print("SONUC: %d kapi · kosul-metni AYNI %d · DEGISTI %d · kayip parca %d · "
          "kayiptan CANLI %d" % (len(ortak), ayni, degisti, toplam_kayip, canli))
    for ad, metin in canli_ornek:
        print("  CANLI ORNEK %s: %s" % (ad, metin))
    # DEGERLENDIRME satiri ZORUNLU: yukaridaki sayilar bir HUKUM degil.
    # OLCULDU (15 Kasim 2026): C12a'nin kosul metni `_eksik` adini HIC anmiyor,
    # ama C12a'nin kapanisinda `_eksik` tanimlari var — cunku `kapi_farki._tanimlar`
    # (b)/(c) kurallari SARMA BLOK kosullarini da "tanim" sayiyor. Yani kapanis
    # ~900 parcadir ve bir kod tasima yuzlerce parcayi "kayip" gosterebilir.
    # Bu sayi tek basina "kapı kor kaldi" DEMEK DEGILDIR; ayirt edici arac
    # MUTASYON'dur (bir olcut bozulunca kapı yaniyor mu).
    print("DEGERLENDIRME: kayip parca sayisi 'kor nokta' kaniti DEGIL — kapanis")
    print("  tanim grafiginden gelir (sarma blok kosullari dahil). Kor nokta")
    print("  olcumu MUTASYONLA yapilir: skill_lint --kapi / mutasyon_kos.")
    # rc sozlesmesi: 0 = kosul METNI hic degismedi (beklenen), 1 = degisti ya da
    # kapanis daraldi -> INSAN BAKSIN. Hukum degil, dikkat cagrisi.
    return 0 if (degisti == 0 and toplam_kayip == 0) else 1


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--a", required=True, help="eski surum")
    ap.add_argument("--b", required=True, help="yeni surum")
    ap.add_argument("--detay", metavar="KAPI", default=None,
                    help="tek kapi icin kaybolan parcalari tek tek yaz")
    ns = ap.parse_args(argv)
    if ns.detay:
        return detay(ns.a, ns.b, ns.detay)
    return olc(ns.a, ns.b)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
