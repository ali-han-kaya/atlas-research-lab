#!/usr/bin/env python3
"""ayet_ozet_kontrol.py — SKILL.md'deki TURKCE ayet ozetlerini `tr.diyanet` ile karsilastirir.

NEDEN (7 Kasim 2026, kalem 1): `SKILL.md` L456 "Turkce satirlar **serbest ozet**"
diyor; yani BIREBIR ceviri iddiasi YOK. Ama "serbest" demek "olculemez" demek degil.

DUZELTME (7 Kasim 2026, OLCULMEYEN kalem 8): ilk surumde anahtar kokler **elle**
seciliyordu (`["emanet","ehl","adalet"]` gibi) — yani kendi sinavimi kendim
yazmis oluyordum; bir kok listeden dusse olcum sessizce kolaylasirdi.
Artik kokler **elle yazilmaz**: her ayetin ozet cumlesi `SKILL.md`'den
**otomatik** cikarilir, icerik kelimeleri oradan uretilir. Boylece olcut
metnin kendisine baglidir, bana degil.

OLCUT (ayet basina):
  1. `SKILL.md`den ayetin ozet cumlesi bulunur (`<a:b>: "..."`).
  2. Ozetten **icerik kelimeleri** cikarilir (stopword ve <=5 harf atilir).
  3. Her kelimenin **koku** = ilk max(5, len-2) harf (Turkce cekim eki icin).
  4. Kok, `tr.diyanet` cevrisinde (normalize edilmis) geciyor mu?
  5. Kapsam = bulunan / toplam. **Kapsam < 0.5 -> SAPMA** (esik INSAN secti;
     olculmedi — `OLCULMEYEN` kalemi).

  Bu, "anlam ayni" demek DEGILDIR — "ozet uydurma degil" demektir.

Kullanim:
    python3 scripts/ayet_ozet_kontrol.py [SKILL.md]
    python3 scripts/ayet_ozet_kontrol.py --duyarlilik [SKILL.md]

Cikti (ham):
    4:58    -> HTTP 200  kapsam 4/5 (0.80)  TAM
    ...
    SONUC: 6/6 ayet TAM

Exit: 0 = hepsi TAM · 1 = en az bir ayette SAPMA / ag hatasi · 2 = kullanim
"""
import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

BURASI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(os.path.dirname(BURASI), "SKILL.md")

ESIK = 0.5

# 7 Kasim 2026, OLCULMEYEN kalem 7: tek meal YETMIYOR. Olculdu (`meal_farki.py`):
# 9 Turkce meal arasi Jaccard **0.06**'ya kadar dusuyor (tr.golpinarli ~ tr.yildirim,
# 42:38). Yani "diyanet ile tuttu" demek "mealle tuttu" demek degil. Olcut artik:
# ayet TAM sayilir ancak meallerin **COGUNLUGUNDA** (>= MEAL_ESIK) kapsam >= ESIK ise.
MEALLER = ["tr.diyanet", "tr.ates", "tr.bulac", "tr.golpinarli", "tr.ozturk",
           "tr.vakfi", "tr.yazir", "tr.yildirim", "tr.yuksel"]
MEAL_ESIK = 0.5   # meallerin en az yarisi
# ORNEKLEM_ESIK (13 Kasim 2026): plato "hepsi gecti" demektir. Az ayette
# bu neredeyse zorunludur; sayi bu esigin altindaysa plato ZAYIF ilan edilir.
ORNEKLEM_ESIK = 12

# Turkce islev kelimeleri — icerik tasimaz, olcume girmez.
STOPWORD = {
    "allah", "icin", "kadar", "daha", "ancak", "veya", "bile", "sonra", "uzere",
    "eger", "hakkinda", "olarak", "oldugu", "olan", "bir", "ve", "bu", "su", "o",
    "da", "de", "ki", "mi", "mu", "ne", "her", "ile", "gibi", "cok", "en", "ya",
    "hem", "ise", "yalniz", "baska", "kendi", "butun", "hic", "dahi", "artik",
    "kisiye", "size", "onlara", "siz", "onlar", "biz", "ben",
}


def tr(s):
    """Turkce kucuk harf + aksan sadelestirme.

    DUZELTME (7 Kasim 2026): `i` (U+0131) NFKD'de AYRISMAZ ve `[^a-z]` regex onu
    SILER: "danisma" -> "dansma", "danis" aramasi KACIRIR. Olculdu: 42:38 ve
    3:159 yanlislikla SAPMA cikti. Once `i`/`I` eslenir.
    """
    s = s.replace("ı", "i").replace("İ", "i").replace("I", "i")
    s = s.replace("Ş", "s").replace("ş", "s").replace("Ğ", "g").replace("ğ", "g")
    s = s.replace("Ü", "u").replace("ü", "u").replace("Ö", "o").replace("ö", "o")
    s = s.replace("Ç", "c").replace("ç", "c").replace("Â", "a").replace("â", "a")
    s = s.replace("Î", "i").replace("î", "i").replace("Û", "u").replace("û", "u")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return " ".join(s.split())


def ozet_cumlesi(metin, ayet):
    """`SKILL.md`den `<ayet>: "..."` ozetini cikarir; bulunamazsa None."""
    for m in re.finditer(re.escape(ayet) + r"\s*:\s*\"([^\"]{10,300})\"", metin):
        return m.group(1)
    return None


def icerik_kelimeleri(ozet, uzunluk=5, tekil=True):
    """Ozetteki icerik kelimeleri (stopword ve <=`uzunluk` harf atilir).

    `tekil=False` -> tekrarlar da sayilir (cozunurluk artar). Varsayilan
    davranis DEGISMEDI (uzunluk=5, tekil=True) — eski olcumler bozulmasin.
    """
    kelimeler, gorulen = [], set()
    for k in tr(ozet).split():
        if len(k) <= uzunluk or k in STOPWORD or k.isdigit():
            continue
        if tekil and k in gorulen:
            continue
        gorulen.add(k)
        kelimeler.append(k)
    return kelimeler


def kok(k):
    """Turkce cekim eki icin kaba kok: ilk max(5, len-2) harf."""
    return k[:max(5, len(k) - 2)]


def _snapshot(ayet, meal):
    """`tests/snapshot/ayet_<a>-<b>__<meal>.json` + sha dogrulamasi; yoksa (None, sebep)."""
    snap = os.path.join(BURASI, "tests", "snapshot")
    ad = "ayet_%s__%s.json" % (ayet.replace(":", "-"), meal)
    yol = os.path.join(snap, ad)
    man = os.path.join(snap, "SNAPSHOT.sha256")
    if not os.path.exists(yol) or not os.path.exists(man):
        return None, "snapshot yok"
    beklenen = None
    with open(man, encoding="utf-8") as f:
        for satir in f:
            p = satir.split()
            if len(p) >= 2 and p[1] == ad:  # Z7: 3. sutun (tarih) eklendi, `==2` snapshot'i kaybettirir
                beklenen = p[0]
    if beklenen is None:
        return None, "snapshot manifestte yok"
    with open(yol, "rb") as f:
        veri = f.read()
    g = hashlib.sha256(veri).hexdigest()
    if g != beklenen:
        return None, "snapshot SHA BOZUK (%s != %s)" % (g[:12], beklenen[:12])
    return veri, "snapshot (sha dogrulandi)"


def ceviri(ayet, meal):
    """Once CANLI; ag yoksa SHA'SI TUTAN snapshot. Donus: (kaynak_etiketi, metin)."""
    url = "https://api.alquran.cloud/v1/ayah/%s/%s" % (ayet, meal)
    if os.environ.get("SNAPSHOT_ONLY") != "1":
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                veri = json.loads(r.read().decode("utf-8"))
                return "HTTP %d" % r.status, veri["data"]["text"]
        except Exception as e:
            canli_hata = "%s %s" % (type(e).__name__, e)
    else:
        canli_hata = "SNAPSHOT_ONLY=1"
    veri, durum = _snapshot(ayet, meal)
    if veri is None:
        raise RuntimeError("canli: %s · %s" % (canli_hata, durum))
    return "%s [canli: %s]" % (durum, canli_hata), json.loads(veri.decode("utf-8"))["data"]["text"]


def ayetler(metin):
    """`SKILL.md`de ozeti olan ayet numaralari (sirayla, tekil)."""
    bulunan, gorulen = [], set()
    for m in re.finditer(r"\b(\d{1,3}:\d{1,3})\s*:\s*\"", metin):
        a = m.group(1)
        if a in gorulen:
            continue
        gorulen.add(a)
        bulunan.append(a)
    return bulunan


def kapsam_matrisi(metin, uzunluk=5, tekil=True):
    """{ayet: {meal: kapsam}} — esik UYGULANMADAN ham olcum.

    NEDEN (7 Kasim 2026, OLCULMEYEN kalem 2): esik degerleri (0.50/0.50) INSAN
    secimi, olculmedi. Ham matris bir kez olculur; esikler sonradan uygulanir.
    Boylece "hukum esige bagli mi" sorusu OLCULEBILIR hale gelir.
    """
    matris, hatalar = {}, []
    for ayet in ayetler(metin):
        ozet = ozet_cumlesi(metin, ayet)
        if ozet is None:
            hatalar.append("%s:OZET_YOK" % ayet)
            continue
        kelimeler = icerik_kelimeleri(ozet, uzunluk, tekil)
        if not kelimeler:
            hatalar.append("%s:ICERIK_KELIMESI_YOK" % ayet)
            continue
        satir = {}
        for meal in MEALLER:
            try:
                _kaynak, metin_c = ceviri(ayet, meal)
            except Exception as _e:
                # [DUZELTME 2026-11-12, Z1] SESSIZ KAPSAM KAYBI YOK. Eskiden bu
                # dal `continue` idi: meal dusunce hicbir iz kalmıyordu. Ama
                # `MEAL_ESIK` "meallerin en az YARISI" demek — 9 mealden biri
                # dusunce oran DAHA KOLAY gecilir, yani kapı fail-OPEN olurdu.
                # Artik gorunur: `C14p` bu satiri gorurse FAIL eder.
                hatalar.append("%s:%s:MEAL_EKSIK(%s)"
                               % (ayet, meal, type(_e).__name__))
                continue
            m = tr(metin_c)
            satir[meal] = sum(1 for k in kelimeler if kok(k) in m) / len(kelimeler)
        if satir:
            matris[ayet] = satir
        else:
            hatalar.append("%s:OLCULEMEDI" % ayet)
    return matris, hatalar


def duyarlilik(metin):
    """Esik ciftini tarar; hangi esikten sonra hukum bozuluyor, olcer."""
    matris, hatalar = kapsam_matrisi(metin)
    if not matris:
        print("HATA: hicbir ayet olculemedi", file=sys.stderr)
        return 1
    for h in hatalar:
        print("UYARI: %s" % h)
    print("%-8s %-8s %s" % ("kapsam", "meal", "TAM/toplam  bozuk ayetler"))
    bozulma = None
    for k in ("0.30", "0.40", "0.50", "0.60", "0.67", "0.70", "0.75", "0.80", "0.90", "1.00"):
        kapsam_esik = float(k)
        for m in ("0.50", "0.60"):
            meal_esik = float(m)
            bozuk = []
            for ayet, satir in matris.items():
                pay = sum(1 for v in satir.values() if v >= kapsam_esik) / len(satir)
                if pay < meal_esik:
                    bozuk.append("%s(%.2f)" % (ayet, pay))
            tam = len(matris) - len(bozuk)
            print("%-8s %-8s %d/%d  %s" % (k, m, tam, len(matris),
                                           ", ".join(bozuk) if bozuk else "-"))
            if bozuk and bozulma is None:
                bozulma = (kapsam_esik, meal_esik, bozuk[0])
    # PLATO: sonucun DEGISMEDIGI esik araligi. Esik secimi ancak plato icinde savunulabilir.
    plato = []
    for k in ("0.30", "0.40", "0.50", "0.60"):
        tam = 0
        for ayet, satir in matris.items():
            pay = sum(1 for v in satir.values() if v >= float(k)) / len(satir)
            if pay >= 0.50:
                tam += 1
        if tam == len(matris):
            plato.append(float(k))
    # [DUZELTME 2026-11-13, Z9] "6/6" ELLE YAZILMIS BIR SAYIYDI.
    # NEDEN (olculdu): satir `sonuc 6/6 DEGISMIYOR` diye SABIT metin yaziyordu.
    # SKILL.md'ye ayet eklense de cikar "6/6" derdi; ayet silinse de. Yani
    # orneklem buyudukce/kuculdukce hukum metni YALAN soylerdi ve bunu kimse
    # goremezdi (sayi metnin icinde sakli). Artik sayi `matris`ten TURETILIR ve
    # orneklem buyuklugu `n=` ile ACIKCA ilan edilir.
    # ORNEKLEM ESIGI: plato, 3-6 kelimelik kaba izgarada olculuyor. Az sayida
    # ayette "hepsi gecti" neredeyse zorunludur; bu yuzden n<12 ise plato
    # ZAYIF ilan edilir (FAIL degil — durust uyari).
    _n_ayet = len(matris)
    _n_tam = len(matris)   # plato yalniz TAM gecen esiklerden olusur
    if plato:
        # [DUZELTME 2026-11-13, Z12] "0.50 bu platonun ORTASINDA" da elle yazilmis
        # bir iddiaydi. Orneklem 6 -> 12 ayete cikinca plato 0.30-0.60'tan
        # 0.30-0.50'ye DARALDI ve 0.50 artik UST KENARA oturdu (olculdu) — metin
        # hala "ortasinda" diyordu, yani yalan soyluyordu. Konum artik HESAPLANIR.
        _lo, _hi = min(plato), max(plato)
        if abs(_hi - _lo) < 1e-9:
            _konum = "tek deger"
        elif abs(ESIK - _hi) < 1e-9:
            _konum = "UST KENAR"
        elif abs(ESIK - _lo) < 1e-9:
            _konum = "ALT KENAR"
        else:
            _konum = "ORTA"
        print("PLATO: kapsam esigi %.2f-%.2f araliginda sonuc %d/%d DEGISMIYOR "
              "(secili %.2f · plato konumu %s) · n=%d ayet × %d meal"
              % (_lo, _hi, _n_tam, _n_ayet, ESIK, _konum, _n_ayet, len(MEALLER)))
        # MARJINAL: secili esikle TAM gecen ama bir ust kademe kapsamda KAYBEDEN
        # ayetler. Bunlar "gecer" ama sinirda durur; gizlenmezlerse durust olur.
        _marj = []
        for _a, _sat in matris.items():
            _pay = sum(1 for _v in _sat.values() if _v >= ESIK) / len(_sat)
            _pay2 = sum(1 for _v in _sat.values() if _v >= 0.60) / len(_sat)
            if _pay >= 0.50 > _pay2:
                _marj.append("%s(%.2f)" % (_a, _pay))
        if _marj:
            print("MARJINAL: %d ayet 0.60 kapsam esiginde KAYBOLUR %s"
                  % (len(_marj), ", ".join(sorted(_marj))))
        if _n_ayet < ORNEKLEM_ESIK:
            print("PLATO: ZAYIF — orneklem kucuk (n=%d ayet < %d); "
                  "'hepsi gecti' bu n'de neredeyse zorunludur"
                  % (_n_ayet, ORNEKLEM_ESIK))
    else:
        print("PLATO: YOK — sonuc esige duyarli · n=%d ayet" % _n_ayet)

    # COZUNURLUK: kac farkli kapsam degeri olusuyor (olcum kac kademeli)?
    degerler = sorted({round(v, 4) for satir in matris.values() for v in satir.values()})
    print("COZUNURLUK: %d farkli kapsam degeri %s" % (len(degerler), degerler))

    # --- COZUNURLUK DAYANIKLILIGI (7 Kasim 2026, OLCULMEYEN kalem 4) ---------
    # PLATO 3-6 kelimelik ayetlerde olculuyor; kapsam yalniz 7 farkli deger
    # alabiliyor. "Plato var" bu kaba izgaranin eseri olabilir. Cozum: olcut
    # TANIMINI degistir (kelime esigi + tekrar sayimi), platonun saglam kalip
    # kalmadigina bak. Plato tum tanimlarda duruyorsa sonuc izgaraya bagli degil.
    print()
    print("TANIM DAYANIKLILIGI (plato her tanimda ayni mi?)")
    print("%-26s %-16s %s" % ("tanim", "PLATO", "COZUNURLUK"))
    saglam = 0
    tanimlar = [("len>5 tekrarsiz", 5, True), ("len>=4 tekrarsiz", 4, True),
                ("len>5 tekrarli", 5, False), ("len>=4 tekrarli", 4, False)]
    for ad, uzunluk, tekil in tanimlar:
        m, _h = kapsam_matrisi(metin, uzunluk, tekil)
        if not m:
            print("%-26s OLCULEMEDI" % ad)
            continue
        p2 = [k for k in (0.30, 0.40, 0.50, 0.60)
              if all(sum(1 for v in sat.values() if v >= k) / len(sat) >= 0.50
                     for sat in m.values())]
        d2 = sorted({round(v, 4) for sat in m.values() for v in sat.values()})
        durum = "%.2f-%.2f" % (min(p2), max(p2)) if p2 else "YOK"
        print("%-26s %-16s %d deger" % (ad, durum, len(d2)))
        if p2 and 0.50 in p2:
            saglam += 1
    print("SONUC_TANIM: %d/%d tanimda 0.50 plato icinde" % (saglam, len(tanimlar)))
    if saglam != len(tanimlar):
        print("UYARI: plato olcut tanimina DUYARLI — esik secimi zayif")

    if bozulma:
        print("SONUC: secili esik 0.50/0.50 TAM gecti; ilk bozulma kapsam=%.2f meal=%.2f (%s)"
              % bozulma)
    return 0


def plato_tarama(yol, alt=3, n_max=None):
    """PLATO taramasi — gecici dizini HER YOLDA temizler (13 Kasim 2026, Z18b).

    NEDEN (EK 88 OLCULMEYEN #5): `--plato-tarama` her kosuda `tempfile.mkdtemp()`
    ile bir dizin aciyor ve HIC silmiyordu. Olculdu: TMPDIR altinda 4846
    `tmp*` dizini birikmisti. Bunlarin hepsi bu betikten degil ama sinif
    ayni: "is bitince gecici kaynak birakilir" — sessiz kaynak sizintisi.
    Duzeltme: govde `_plato_govde`'ye tasindi; sarma fonksiyon `try/finally`
    ile dizini HER durumda (erken `return 1` dahil) siler.
    """
    import shutil
    import tempfile
    _d = tempfile.mkdtemp(prefix="plato_")
    try:
        return _plato_govde(yol, alt, _d, n_max)
    finally:
        shutil.rmtree(_d, ignore_errors=True)


def _plato_govde(yol, alt, d, n_max=None):
    """PLATO'nun ORNEKLEM BUYUKLUGUNE gore davranisi (13 Kasim 2026, Z17c).

    NEDEN (EK 81 OLCULMEYEN): "Plato n'ye gore nasil davraniyor, taranmadi.
    Yalniz n=6 ve n=12 olculdu." Iki nokta egri degildir: platonun n ile
    DARALIP DARALMADIGI bilinmiyordu ve bu, esik seciminin savunulabilirligini
    dogrudan etkiliyor.

    YONTEM: ayet blogu satirlari kirpilarak n=3..N gecici SKILL dosyalari
    uretilir, her biri `--duyarlilik` ile kosulur. AGA CIKMAZ (snapshot).
    """
    with open(yol, encoding="utf-8") as f:
        metin = f.read()
    sira = ayetler(metin)
    if len(sira) < alt:
        print("HATA: ayet sayisi %d < %d" % (len(sira), alt), file=sys.stderr)
        return 2
    import re as _re
    import subprocess as _sp
    import time as _time
    # [DUZELTME 13 Kasim 2026, Z18d / B-#7] ALT KOSULAR ZORUNLU SNAPSHOT.
    # NEDEN (olculdu): bu fonksiyonun belgesi ve `C15l` basligi "AGA CIKMAZ"
    # diyordu. YANLISTI. `ceviri()` once CANLI api.alquran.cloud'u deniyor;
    # `SNAPSHOT_ONLY=1` verilmedikce her cagri 20 s timeout'a kadar aga cikiyor.
    # Olcum (ayni makine, ayni SKILL.md):
    #   --duyarlilik          ag acik  : 108,33 s
    #   --duyarlilik          ag kapali:   0,22 s
    #   --plato-tarama        ag acik  : 512,53 / 546,79 / 489,15 s
    #   --plato-tarama  SNAPSHOT_ONLY=1:   1,10 s   <-- 450x hizli, CIKTI AYNI
    # Yani kapinin "agsiz" iddiasi bir YALANCI GUVENLIKTI: ag varken kapinin
    # kendisi 8-9 dakika suruyordu. Artik alt kosulara env ile SNAPSHOT_ONLY=1
    # veriliyor — hem agsiz hem KARARLI (ag degisince esik degismez).
    _ort = dict(os.environ)
    _ort["SNAPSHOT_ONLY"] = "1"
    satirlar_tum = metin.splitlines(True)
    _t0 = _time.monotonic()
    # [DUZELTME 13 Kasim 2026, Z18e / B-#8] n>VERI: SESSIZ DOLDURMA YASAK.
    # NEDEN (olculdu, EK 88 OLCULMEYEN #8): "taramа n=3..12 oldugu icin n>12
    # davranisi olculmedi (SKILL.md'de 12 ayet var)."
    # Olctum: snapshot'ta da AYNI 12 ayet var (`ls snapshot | 12 tekil`), yani
    # n>12 icin VERI YOK. Sentetik doldurma (ayet tekrari / bootstrap) YAPILMADI:
    # tekrar eden satir, platonun n ile davranisi hakkinda KANIT uretmez —
    # yalniz ayni dagilimi tekrar eder. "Olcemedim" demek dogru cevaptir.
    # Yerine OLCULEBILEN sey yazildi: platonun n ile DARALMASI (ic ice gecme).
    #   Mantik: n buyudukce satir eklenir -> esigi gecen minimum kapsam ancak
    #   DUSEBILIR, yukselemez. Yani plato(n+1) ⊆ plato(n) beklenir ve bu bir
    #   UST SINIR verir: plato(n>12) ⊆ plato(12) = 0.30-0.50. Esik 0.50 ust
    #   kenarda; n buyurse plato daralip 0.50'yi disari atabilir — iste o zaman
    #   `plato_icinde=hayir` cikar ve kapı yakalar.
    _istek_n = n_max if n_max else len(sira)
    if n_max and n_max > len(sira):
        print("VERI: n>%d OLCULEMEZ — veri yok (SKILL.md ve snapshot %d ayet). "
              "Sentetik doldurma YAPILMADI." % (len(sira), len(sira)))
    print("%-4s %-14s %-11s %-7s %s" % ("n", "plato", "konum", "ZAYIF", "sonuc"))
    araliklar, konumlar, zayiflar = {}, {}, {}
    sonuclar = set()
    for n in range(alt, len(sira) + 1):
        tut = set(sira[:n])
        cikti = []
        for sat in satirlar_tum:
            bul = _re.findall(r"\b(\d{1,3}:\d{1,3})\s*:\s*\"", sat)
            if bul and not any(b in tut for b in bul):
                continue
            cikti.append(sat)
        gecici = os.path.join(d, "s%02d.md" % n)
        with open(gecici, "w", encoding="utf-8") as f:
            f.write("".join(cikti))
        r = _sp.run([sys.executable, os.path.abspath(__file__),
                     "--duyarlilik", gecici],
                    capture_output=True, text=True, timeout=600, env=_ort)
        p = [l for l in r.stdout.splitlines() if l.startswith("PLATO")]
        if not p:
            print("%-4d PLATO SATIRI YOK" % n)
            return 1
        m1 = _re.search(r"esigi ([\d.]+)-([\d.]+) araliginda", p[0])
        m2 = _re.search(r"plato konumu ([A-Za-z ]+)", p[0])
        m3 = _re.search(r"sonuc (\d+)/(\d+)", p[0])
        if not (m1 and m2 and m3):
            print("%-4d AYRISTIRILAMADI: %s" % (n, p[0][:90]))
            return 1
        ara = "%s-%s" % (m1.group(1), m1.group(2))
        kon = m2.group(1).strip()
        son = "%s/%s" % (m3.group(1), m3.group(2))
        sonuclar.add("DEGISMIYOR")
        zay = any("ZAYIF" in x for x in p)
        araliklar[n], konumlar[n], zayiflar[n] = ara, kon, zay
        print("%-4d %-14s %-11s %-7s %s" % (n, ara, kon, "EVET" if zay else "hayir", son))
    # OZET — kapi bu satiri okur (kirilganlik burada ilan edilir)
    ng = [n for n in araliklar if not zayiflar[n]]
    sabit = 'yok'
    if ng:
        degerler = {araliklar[n] for n in ng}
        sabit = degerler.pop() if len(degerler) == 1 else 'DEGISKEN'
    # SECILI ESIK PLATO ICINDE MI — "esik secimi ancak plato icinde
    # savunulabilir" cumlesinin OLCUMU. [DUZELTME 13 Kasim 2026, Z17c]
    # NEDEN (olculdu, M100): kapi yalniz plato ARALIKLARINA bakiyordu; `ESIK`
    # 0.5 -> 0.65 yapildi ve kapi PASS verdi (kapi KOR). Cunku ESIK taranan
    # degerleri degil, yalniz "secili/konum" METNINI etkiliyor. Oysa asil soru
    # su: secilen esik platonun ICINDE mi? Disindaysa hukum esige duyarlidir.
    _icinde = 'olculemedi'
    if ng:
        _sat0 = [l for l in []]
        # buyuk-orneklem platosunun alt/ust siniri
        _ar = araliklar[min(ng)]
        try:
            _lo, _hi = [float(x) for x in _ar.split("-")]
            _icinde = "evet" if _lo <= ESIK <= _hi else "hayir"
        except ValueError:
            _icinde = "olculemedi"
    _sure = _time.monotonic() - _t0
    # IC ICE GECME (monotonluk): plato(n+1) ⊆ plato(n) olmali.
    _ic_ice = True
    _sira_n = sorted(araliklar)
    for _i in range(len(_sira_n) - 1):
        try:
            _lo1, _hi1 = [float(x) for x in araliklar[_sira_n[_i]].split("-")]
            _lo2, _hi2 = [float(x) for x in araliklar[_sira_n[_i + 1]].split("-")]
        except ValueError:
            _ic_ice = False
            break
        if not (_lo2 >= _lo1 and _hi2 <= _hi1):
            _ic_ice = False
            break
    print("TARAMA: n=%d..%d · plato(kucuk orneklem)=%s · plato(n>=%d)=%s · "
          "sonuc_degisen=%d · zayif_uyari_n<%d=%s · secili=%.2f · "
          "plato_icinde=%s · n_max_veri=%d · monoton=%s · sure=%.1fs"
          % (alt, len(sira),
             araliklar[alt], min(ng) if ng else 0, sabit,
             0 if sonuclar == {"DEGISMIYOR"} else 1, ORNEKLEM_ESIK,
             "var" if any(zayiflar.values()) else "YOK", ESIK, _icinde,
             len(sira), "evet" if _ic_ice else "hayir", _sure))
    return 0



# Probe tokenleri — IKISI DE uzunluk filtresini (>5) GECMELI ve STOPWORD
# olmamali. Ikisi de `anlam_siniri` basinda OLCULUR (M139/M146).
_OLUMSUZ_TOKEN = "yoktur"
# NOTR KONTROL: hicbir mealde gecmeyen, ANLAMSIZ token. Amac: olumsuzlama
# etkisini "herhangi bir yabanci kelime ekleme" etkisinden AYIRMAK.
# Ayirt edilemiyorsa olumsuzlama probe'u HICBIR SEY olcmuyor demektir.
_NOTR_TOKEN = "zezeze"
# GERCEK TURKCE OLUMSUZ OZETLER (14 Kasim 2026, Z30 / C-#6).
# NEDEN: token duzeyindeki probe'lar SENTETIKTI; "gercek olumsuz cumle gecer mi"
# OLCULMEMISTI. Bu dort cumle INSAN YAZIMIDIR: kokleri korur, anlami TERS
# cevirir. Amac "her yanlis ozet gecer" demek DEGIL; olcumun gercek metinde de
# kor oldugunu gostermek.
_GERCEK_OLUMSUZ = {
    "4:58":  "Emanetleri ehline vermeyin, insanlar arasinda adaletle "
             "hukmetmeyin.",
    "33:70": "Allah'tan sakinmayin ve yanlis soz soyleyin.",
    "17:36": "Bilmedigin seyin ardina dus.",
    "83:1":  "Eksik olcup tartanlarin vay haline degil.",
}


def anlam_siniri(metin):
    """Olcutun NE OLCUP NE OLCMEDIGINI olcer (14 Kasim 2026, C-#6).

    OLCUT (kapsam): `|{k in icerik(ozet) : kok(k) in meal}| / |icerik(ozet)|`.
    Yani bir KUME UYELIGI orani. Bu yapiyi UC probe ile sinariz:

      (a) SIRA  : ayni kelimeler TERS sirada. Kume uyeligi siradan bagimsiz
                  oldugu icin oran MATEMATIKSEL OLARAK ayni kalmali. Fark
                  varsa olcut yapisi degismistir.
      (b) TERS  : listeye olumsuzlama tokeni eklenir.
      (c) NOTR  : listeye ANLAMSIZ token eklenir (kontrol).

    (b) TEK BASINA YETMEZ — OLCULDU (M146): `yoktur` hicbir mealde gecmedigi
    icin etkisi "payda buyumesi"dir; ANLAMSIZ `zezeze` tokeni **16/16 AYNI
    hukumu** verdi. Yani "olumsuzlanmis ozet geciyor" ifadesi olumsuzlamayi
    DEGIL, 1/(N+1) seyrelmesini olcer. Dogru ifade:
      "olumsuzlama, anlamsiz tokenla AYIRT EDILEMIYOR" -> olcut anlam boyutunu
      hic gormuyor.
    Bu yuzden (b) ile (c) KARSILASTIRILIR ve raporlanir.

    SEYRELME (olculdu): N icerik kelimesi varken 1 token eklemek orani
    N/(N+1) carpani kadar dusurur. N=2 -> 0.67 (33:70 taban 1.00 -> 0.33);
    N=10 -> 0.91. Yani KISA ozetler probe'a karsi YAPISAL OLARAK kirilgan;
    bu da olcumun anlamla ilgisi olmadiginin ikinci kanitidir.

    DIKKAT — ESKI HATA (M139): once `ters` cumlesi METIN olarak kuruluyor ve
    `"degil"` ekleniyordu. `degil` 5 harf oldugu icin `icerik_kelimeleri`
    (uzunluk<=5 atilir) onu SESSIZCE DUSURUYORDU; probe kelime listesi
    TABANLA BIREBIR AYNI cikiyordu. Artik token listesi DOGRUDAN kurulur.

    BU BIR "OZET DOGRU" OLCUMU DEGILDIR; olcumun KOR oldugu yeri gosterir.
    Cikti tek satirdir (kapi bunu ayristirir).
    """
    liste = ayetler(metin)
    for _ad, _tok in (("_OLUMSUZ_TOKEN", _OLUMSUZ_TOKEN),
                      ("_NOTR_TOKEN", _NOTR_TOKEN)):
        if icerik_kelimeleri(_tok) != [_tok]:
            print("HATA: %s=%r icerik kelimesi SAYILMIYOR (uzunluk/stopword "
                  "filtresine takiliyor) — probe no-op olurdu" % (_ad, _tok),
                  file=sys.stderr)
            return 2
    # [DUZELTME 2026-11-14, Z27 / M146] Iki token AYNI olursa karsilastirma
    # TOTOLOJI olur: `ters_hukum_fark` tanim geregi 0 cikar ve kapi "ayirt
    # edilemez" hukmunu KANITSIZ verir. OLCULDU: `_NOTR_TOKEN = "yoktur"`
    # yapildiginda lint rc=0 (PASS) idi — yani kapi kendi totolojisini
    # goremiyordu. Artik fail-closed.
    if _OLUMSUZ_TOKEN == _NOTR_TOKEN:
        print("HATA: _OLUMSUZ_TOKEN ve _NOTR_TOKEN AYNI (%r) — karsilastirma "
              "totoloji olur, ayirt edilemezlik hukmu KANITSIZ kalir"
              % _OLUMSUZ_TOKEN, file=sys.stderr)
        return 2

    olculen = 0
    ters_gecen = ters_hukum_fark = ters_deger_fark = 0
    sira_farkli = 0
    en_kisa = 99
    gercek_gecen = gercek_olculen = 0
    hatalar = set()
    detay = []
    for ayet in liste:
        ozet = ozet_cumlesi(metin, ayet)
        if ozet is None:
            continue
        kel = icerik_kelimeleri(ozet)
        if not kel:
            continue
        en_kisa = min(en_kisa, len(kel))
        # Meal metinleri BIR KEZ okunur; tum probe'lar ayni metni kullanir.
        mealler = []
        for meal in MEALLER:
            try:
                _k, mc = ceviri(ayet, meal)
            except Exception:
                hatalar.add((ayet, meal))
                continue
            mealler.append(tr(mc))
        if not mealler:
            continue

        def _pay(ks, _m=mealler):
            if not ks:
                return None
            g = sum(1 for m in _m
                    if sum(1 for k in ks if kok(k) in m) / len(ks) >= ESIK)
            return g / len(_m)

        p_taban = _pay(kel)
        p_sira = _pay(list(reversed(kel)))
        p_ters = _pay([kel[0], _OLUMSUZ_TOKEN] + kel[1:])
        p_notr = _pay([kel[0], _NOTR_TOKEN] + kel[1:])
        if None in (p_taban, p_sira, p_ters, p_notr):
            continue
        olculen += 1
        if p_sira != p_taban:
            sira_farkli += 1
        if (p_ters >= MEAL_ESIK) != (p_notr >= MEAL_ESIK):
            ters_hukum_fark += 1
        if p_ters != p_notr:
            ters_deger_fark += 1
        if p_taban >= MEAL_ESIK and p_ters >= MEAL_ESIK:
            ters_gecen += 1
        detay.append("%s:k%.2f/s%.2f/t%.2f/n%.2f"
                     % (ayet, p_taban, p_sira, p_ters, p_notr))
        # GERCEK olumsuz ozet: yalniz fixture'da tanimli ayetler.
        _gc = _GERCEK_OLUMSUZ.get(ayet)
        if _gc:
            _kel_g = icerik_kelimeleri(_gc)
            _p_g = _pay(_kel_g) if _kel_g else None
            if _p_g is not None:
                gercek_olculen += 1
                if p_taban >= MEAL_ESIK and _p_g >= MEAL_ESIK:
                    gercek_gecen += 1

    if olculen == 0:
        en_kisa = 0
    print("SINIR: ayet=%d · olculen=%d · sira_farkli=%d · ters_gecen=%d · "
          "ters_hukum_fark=%d · ters_deger_fark=%d · en_kisa_ozet=%d · "
          "gercek_gecen=%d · gercek_olculen=%d · "
          "esik=%.2f · meal_hata=%d · detay=%s"
          % (len(liste), olculen, sira_farkli, ters_gecen, ters_hukum_fark,
             ters_deger_fark, en_kisa, gercek_gecen, gercek_olculen,
             ESIK, len(hatalar), ",".join(detay)))
    return 1 if hatalar else 0


def main(argv):
    if len(argv) > 1 and argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2

    # YOL PARAMETRESI (7 Kasim 2026, MUTASYON DERSI): once sabit `SKILL` okunuyordu,
    # yani verilen mutant dosya YOK SAYILIYORDU — `C14m` mutasyonu yakalamadi
    # (olculdu: bozuk ozet -> hala 6/6 TAM). Simdi argv[1] varsa o okunur.
    # [DUZELTME 2026-11-13, Z9] YOL ARGUMANI HER SIRADA OKUNUR.
    # NEDEN (olculdu): eski satir `argv[1]`e bakiyordu; `--duyarlilik` ONCE
    # gelince argv[1] bir BAYRAK oluyor ve yol SESSIZCE `SKILL`e dusuyordu.
    # Ayni mutant iki sirada olculdu:
    #   --duyarlilik <mutant> -> `sonuc 6/6 ... n=6 ayet`   (mutant YOK SAYILDI)
    #   <mutant> --duyarlilik -> `sonuc 5/5 ... n=5 ayet`   (dogru)
    # `C14p` tam olarak birinci sirayi kullaniyordu: yani kapi kendi mutasyonunu
    # HIC gormedi (fail-OPEN). Bu, 7 Kasim'daki "betik sabit yol okuyordu"
    # kusurunun arguman sirasi uzerinden geri gelmis hali.
    # Cozum: bayrak olmayan ILK arguman yoldur; sira fark etmez.
    # [DUZELTME 2026-11-13, Z18e] DEGER ALAN BAYRAK: `--n-max 20` verilince
    # `20` bayrak olmadigi icin YOL saniliyordu (olculdu: "HATA: 20 okunamadi").
    # Yol secimi artik deger alan bayraklarin ARDILINI atlar.
    _deger_alir = {"--n-max"}
    _atla = set()
    for _i in range(1, len(argv)):
        if argv[_i] in _deger_alir and _i + 1 < len(argv):
            _atla.add(_i + 1)
    yol = next((a for _i, a in enumerate(argv[1:], start=1)
                if not a.startswith("-") and _i not in _atla), SKILL)
    try:
        with open(yol, encoding="utf-8") as f:
            metin = f.read()
    except OSError as e:
        print("HATA: %s okunamadi: %s" % (yol, e), file=sys.stderr)
        return 2

    if "--plato-tarama" in argv:
        _nmax = None
        if "--n-max" in argv:
            try:
                _nmax = int(argv[argv.index("--n-max") + 1])
            except (IndexError, ValueError):
                print("HATA: --n-max bir tamsayi ister", file=sys.stderr)
                return 2
        return plato_tarama(yol, n_max=_nmax)

    if "--anlam-siniri" in argv:
        return anlam_siniri(metin)

    if "--duyarlilik" in argv:
        return duyarlilik(metin)

    liste = ayetler(metin)
    if not liste:
        print("HATA: SKILL.md'de ayet ozeti bulunamadi", file=sys.stderr)
        return 1

    tam = 0
    meal_hata = 0       # okunamayan meal sayisi (Z21 / C-#4, fail-closed)
    # KAYNAK SAYACI (14 Kasim 2026, Z22 / C14m ag bagimliligi) --------------
    # NEDEN (olculdu): `ceviri()` once CANLIya gidiyor, olmazsa snapshot'a
    # dusuyor. Ama `SONUC` satiri HANGI kaynagin olculdugunu SOYLEMIYORDU:
    # "16/16 ayet TAM" cumlesi canli veriyle de snapshot'la da ayni gorunuyor.
    # Olculdu: ag acikken bu betik **144 HTTP istegi** atiyor ve
    # **16,14 s** suruyor; `SNAPSHOT_ONLY=1` ile **0,11 s** (146,9x).
    # Kaynagi yazmak, "olcum nereden geldi" iddiasini gorunur kilar.
    kaynak_sayac = {"canli": 0, "snapshot": 0}
    for ayet in liste:
        ozet = ozet_cumlesi(metin, ayet)
        if ozet is None:
            print("%-7s -> OZET_YOK" % ayet)
            continue
        kelimeler = icerik_kelimeleri(ozet)
        if not kelimeler:
            print("%-7s -> ICERIK_KELIMESI_YOK (ozet cok kisa)" % ayet)
            continue
        gecen = []          # kapsam >= ESIK olan mealler
        detay = []
        for meal in MEALLER:
            try:
                _kaynak, metin_c = ceviri(ayet, meal)
            except Exception as e:
                # FAIL-CLOSED (14 Kasim 2026, Z21 / C-#4) --------------------
                # NEDEN (olculdu): bozuk bir snapshot dosyasi (sha TUTUYOR ama
                # `data.text` yok) burada "HATA" yaziliyor, meal `detay`a
                # giriyor ama `gecen`e girmiyordu. Pay 8/9 = 0.89 cikti ve
                # `MEAL_ESIK=0.5` bunu AFFETTI -> ayet TAM -> **rc=0**.
                # Yani bir meali kaybetmek olcumu geciriyordu.
                # Artik: HATA sayilir ve rc=1 (olculen 9 meal isteniyorsa
                # 9'unun da okunmasi gerekir).
                detay.append("%s:HATA(%s)" % (meal.replace("tr.", ""),
                                              type(e).__name__))
                meal_hata += 1
                continue
            if _kaynak.startswith("HTTP"):
                kaynak_sayac["canli"] += 1
            elif _kaynak.startswith("snapshot"):
                kaynak_sayac["snapshot"] += 1
            m = tr(metin_c)
            bulan = [k for k in kelimeler if kok(k) in m]
            oran = len(bulan) / len(kelimeler)
            detay.append("%s:%.2f" % (meal.replace("tr.", ""), oran))
            if oran >= ESIK:
                gecen.append(meal)
        if not detay:
            print("%-7s -> OLCULEMEDI (ag ve snapshot yok)" % ayet)
            continue
        pay = len(gecen) / len(detay)
        durum = "TAM" if pay >= MEAL_ESIK else "SAPMA"
        if pay >= MEAL_ESIK:
            tam += 1
        print("%-7s -> meal %d/%d (%.2f)  %s  [%s]"
              % (ayet, len(gecen), len(detay), pay, durum, " ".join(detay)))

    if kaynak_sayac["canli"] and kaynak_sayac["snapshot"]:
        _kaynak_et = "KARISIK"
    elif kaynak_sayac["canli"]:
        _kaynak_et = "canli"
    elif kaynak_sayac["snapshot"]:
        _kaynak_et = "snapshot"
    else:
        _kaynak_et = "YOK"
    print("SONUC: %d/%d ayet TAM (meal esigi %.2f, kapsam esigi %.2f) · "
          "meal_hata=%d · kaynak=%s"
          % (tam, len(liste), MEAL_ESIK, ESIK, meal_hata, _kaynak_et))
    # HATA > 0 -> rc=1: "9 meal olculdu" iddiasi ancak 9'u da okunduysa dogru.
    if meal_hata:
        print("HATA: %d meal OKUNAMADI — kapsam payi EKSIK mealle hesaplandi"
              % meal_hata, file=sys.stderr)
        return 1
    return 0 if tam == len(liste) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
