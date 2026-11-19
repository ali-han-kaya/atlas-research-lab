#!/usr/bin/env python3
"""snapshot_yenile.py — dis kaynaklarin (sunnah.com, api.alquran.cloud) yerel snapshot'ini alir.

NEDEN (7 Kasim 2026, OLCULMEYEN kalem 2): `C14l`/`C14m` **ag bagimliydi**;
ag yoksa lint FAIL donuyordu, yani cevrimdisi ortamda lab hic yesil olamiyordu.
Cozum: sayfa/ayet bir kez indirilir, **sha256** ile sabitlenir, `tests/snapshot/`
altina yazilir. Olcum betigi once CANLI dener; ag yoksa **sha'si tutan** snapshot'i
kullanir ve bunu ciktida ACIKCA soyler (`KAYNAK: snapshot (sha dogrulandi)`).

Bu, "reproducible build" mantigidir: dis dunya degisebilir, ama **olcumun dayanagi**
degismez — degisirse sha tutmaz ve olcum FAIL verir.

Kullanim:
    python3 scripts/snapshot_yenile.py            # indir + yaz + sha uret
    python3 scripts/snapshot_yenile.py --dogrula  # yalniz sha dogrula (ag yok)

Exit:
    0 = tamam / sha tutuyor
    1 = indirme hatasi veya sha UYUSMUYOR (fail-closed)
    2 = kullanim

Cikti (ham):
    YAZILDI: sunnah_6094.html 29820 bayt sha=8f3a...
    YAZILDI: ayet_4-58.json 412 bayt sha=...
    MANIFEST: 8 dosya -> scripts/tests/snapshot/SNAPSHOT.sha256
"""
import hashlib
import json
import os
import sys
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# ESKI_GUN: snapshot bu kadar gunden eskiyse UYARI yazilir. UYARI, FAIL DEGIL:
# sha hala tutuyor, olcum gecerli — ama "dunya degismis olabilir" gorunur olsun.
# Esik INSAN secimi (OLCULMEDI).
ESKI_GUN = 90

BURASI = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(BURASI, "tests", "snapshot")
MANIFEST = os.path.join(SNAP, "SNAPSHOT.sha256")

SUNNAH = ["6094", "39"]
# ORNEKLEM TEK KAYNAKTAN (14 Kasim 2026, Z21c / C-#2): liste artik
# `scripts/ayetler.py`de. Iki kopya vardi ve ayrisma SESSIZDI (olculdu:
# orneklem 12->16 yapilinca `meal_farki.py` 12'de kaldi, 4 yeni ayet
# olcume hic girmedi). Burada ATAMA YOK; `C15m` bunu denetler.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ayetler import AYETLER  # noqa: E402

# 7 Kasim 2026, OLCULMEYEN kalem 7: tek meal yetmiyor — mealler arasi Jaccard
# 0.06'ya kadar dusuyor (olculdu: scripts/meal_farki.py). Olcum 9 mealli yapilir.
MEALLER = ["tr.diyanet", "tr.ates", "tr.bulac", "tr.golpinarli", "tr.ozturk",
           "tr.vakfi", "tr.yazir", "tr.yildirim", "tr.yuksel"]


def indir(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


# Dosya bazli tarihler (Z7): manifest_oku doldurur. Global `SNAPSHOT_TARIH`
# TEK tarih tasir ve dosya bazli gercegi gizliyordu — 12 Kasim 2026'da 3 dosya
# geri yuklendi, ICERIK ayni ama mtime bugune kaydi; global tarih bunu gostermedi.
TARIHLER = {}


def manifest_oku():
    """{dosya_adi: sha} sozlugu; yoksa None. TARIHLER'i da doldurur."""
    if not os.path.exists(MANIFEST):
        return None
    d = {}
    TARIHLER.clear()
    with open(MANIFEST, encoding="utf-8") as f:
        for satir in f:
            if satir.lstrip().startswith("#"):
                continue
            parca = satir.split()
            # [DUZELTME 2026-11-12, Z7] UCUNCU SUTUN: dosya bazli tarih.
            # NEDEN (olculdu): manifestte TEK global `SNAPSHOT_TARIH` vardi ve
            # dosya bazli gercegi gizliyordu. 12 Kasim'da 3 snapshot dosyasi
            # geri yuklendi (M77/M79/M80 mutasyonlari): ICERIK ayni (sha tutuyor)
            # ama mtime bugune kaydi. Global tarih bunu gostermiyordu.
            # Geriye uyumlu: 2 sutunlu eski satirlar da okunur (tarih=None).
            if len(parca) >= 2:
                d[parca[1]] = parca[0]
                if len(parca) >= 3:
                    TARIHLER[parca[1]] = parca[2]
    return d


def snapshot_tarihi():
    """Manifestteki `# SNAPSHOT_TARIH=YYYY-MM-DD` satirini okur; yoksa None."""
    if not os.path.exists(MANIFEST):
        return None
    with open(MANIFEST, encoding="utf-8") as f:
        for satir in f:
            if satir.startswith("# SNAPSHOT_TARIH="):
                return satir.strip().split("=", 1)[1]
    return None


def yas_gun():
    """Snapshot kac gunluk; tarih yoksa None."""
    t = snapshot_tarihi()
    if t is None:
        return None
    import datetime
    try:
        d = datetime.date.fromisoformat(t)
    except ValueError:
        return None
    return (datetime.date.today() - d).days


def yas_dosya(ad):
    """Tek dosyanin yasi (gun). Kaynak sirasi: manifest 3. sutun -> dosya mtime.

    Donus: (gun, kaynak) ya da (None, 'tarih yok').
    """
    import datetime
    t = TARIHLER.get(ad)
    kaynak = 'manifest'
    if t is None:
        yol = os.path.join(SNAP, ad)
        if not os.path.exists(yol):
            return None, 'dosya yok'
        t = datetime.date.fromtimestamp(os.stat(yol).st_mtime).isoformat()
        kaynak = 'mtime'
    try:
        d = datetime.date.fromisoformat(t)
    except ValueError:
        return None, 'tarih bozuk: %s' % t
    return (datetime.date.today() - d).days, kaynak


def mtime_kaymasi(ad):
    """(manifest_tarih, mtime_tarihi) — ikisi farkliysa geri yukleme izi.

    NEDEN: mutasyon testleri (M77/M79/M80) snapshot'i silip `write_bytes` ile
    geri yazdi. ICERIK ayni (sha tutuyor) ama mtime BUGUNE kaydi. Bu bir kayip
    degil, ama "ne zaman indirildi" sorusuna artik mtime cevap veremez.
    Gorunur olmali — sessiz kalmamali.
    """
    import datetime
    yol = os.path.join(SNAP, ad)
    if not os.path.exists(yol):
        return None, None
    mtime = datetime.date.fromtimestamp(os.stat(yol).st_mtime).isoformat()
    return TARIHLER.get(ad), mtime


def icerik_hatasi(ad, veri):
    """Ayet/hadis snapshot'i SEMANTIK olarak gecerli mi? (None = gecerli)

    NEDEN (14 Kasim 2026, Z21 / C-#4): `--dogrula` yalniz sha karsilastiriyordu.
    `indir()` HTTP 200 aldiginda govdenin ICERIGINE bakmiyor; API hata govdesi
    dondurse bile yazilir ve sha'si tutar. Olculdu: `{"code":200,"data":{}}`
    yazildi -> sha TUTTU -> rc=0. Yani "150 dosya dogrulandi" cumlesi
    "150 dosya BOZUK DEGIL" demek degildi.
    """
    if not ad.endswith(".json"):
        return None
    try:
        d = json.loads(veri.decode("utf-8"))
    except Exception as e:
        return "ICERIK_BOZUK(%s)" % type(e).__name__
    if ad.startswith("ayet_"):
        _d = d.get("data")
        if not isinstance(_d, dict):
            return "ICERIK_BOZUK(data yok)"
        if not isinstance(_d.get("text"), str) or not _d["text"].strip():
            return "ICERIK_BOZUK(data.text yok/bos)"
    if ad.startswith("hadeeth_"):
        if not isinstance(d.get("hadeeth"), str) or not d["hadeeth"].strip():
            return "ICERIK_BOZUK(hadeeth yok/bos)"
    return None


def dogrula(ayrintili=True):
    m = manifest_oku()
    if m is None:
        print("HATA: manifest yok: %s" % MANIFEST, file=sys.stderr)
        return 1
    kotu = []
    for ad, beklenen in sorted(m.items()):
        yol = os.path.join(SNAP, ad)
        if not os.path.exists(yol):
            kotu.append("%s YOK" % ad)
            continue
        with open(yol, "rb") as f:
            veri = f.read()
        g = sha(veri)
        if g != beklenen:
            kotu.append("%s SHA_FARKLI" % ad)
        else:
            # ICERIK GECERLILIGI (14 Kasim 2026, Z21 / C-#4) -----------------
            # NEDEN (olculdu): sha YALNIZ baytlari dogrular. 200 donen ama
            # `data.text` TASIMAYAN bir govde yazildi -> sha TUTTU ->
            # `--dogrula` rc=0 "150 dosya sha dogrulandi" dedi. Yani bozuk
            # snapshot YESIL gecti. Olcum: `ayet_ozet_kontrol` o meali
            # "HATA" diye isaretledi ama yine de TAM/PASS verdi.
            # Fail-closed: ayet dosyasi ise sema denetlenir.
            _ic_hata = icerik_hatasi(ad, veri)
            if _ic_hata:
                kotu.append("%s %s" % (ad, _ic_hata))
            elif ayrintili:
                print("DOGRU: %s %s" % (ad, g[:12]))
    if kotu:
        print("SONUC: SNAPSHOT BOZUK — " + " · ".join(kotu), file=sys.stderr)
        return 1
    y = yas_gun()
    if y is None:
        print("YAS: BILINMIYOR (manifestte SNAPSHOT_TARIH yok)")
    else:
        print("YAS: %s gun (tarih %s)" % (y, snapshot_tarihi()))

    # --- DOSYA BAZLI YAS (Z7, 12 Kasim 2026) --------------------------------
    # Global tarih TEK sayidir; en eski dosyayi gizler. Olculuyor: en eski/en yeni.
    yaslar = []
    for ad in sorted(m):
        g, kaynak = yas_dosya(ad)
        if g is not None:
            yaslar.append((g, ad, kaynak))
    if yaslar:
        yaslar.sort()
        en_eski, en_yeni = yaslar[0], yaslar[-1]
        print("YAS_DOSYA: en eski %d gun (%s) · en yeni %d gun (%s) · %d dosya"
              % (en_eski[0], en_eski[1], en_yeni[0], en_yeni[1], len(yaslar)))
        if en_eski[0] > ESKI_GUN:
            print("UYARI: en eski snapshot %d gunden eski (esik %d) — tazele: "
                  "python3 scripts/snapshot_yenile.py" % (en_eski[0], ESKI_GUN))

    # --- MTIME KAYMASI: icerik ayni, tarih yalan (Z7) -----------------------
    # Mutasyon testleri snapshot'i geri yazinca mtime bugune kayar. Bu SESSIZ
    # kalmamali: "ne zaman indirildi" sorusuna mtime cevap veremez hale gelir.
    kayan = []
    for ad in sorted(m):
        man, mtime = mtime_kaymasi(ad)
        if man and mtime and man != mtime:
            kayan.append("%s (manifest %s, mtime %s)" % (ad, man, mtime))
    if kayan:
        # Sozcuk NOTR: mtime ileri de olabilir geri de (M82'de geri kaydirildi).
        print("MTIME_KAYMASI: %d dosya — icerik AYNI (sha tuttu), mtime FARKLI"
              % len(kayan))
        for x in kayan:
            print("  %s" % x)
    else:
        print("MTIME_KAYMASI: -")

    print("SONUC: %d dosya sha dogrulandi" % len(m))
    return 0


def yenile():
    os.makedirs(SNAP, exist_ok=True)
    satirlar = []
    # SUNNAH: HAM HTML SABITLENMEZ (7 Kasim 2026, olculdu). sunnah.com her istekte
    # bayt duzeyinde FARKLI HTML donuyor (dinamik token): iki ardisik indirme
    # sha=27b02cc90e22 / 2889b62ec9db, ama ARAPCA BLOKLAR AYNI.
    # Yani ham sha'yi sabitlemek her tazelemede kirilir ve olcumu degersiz kilar.
    # Sabitlenen sey **normalize edilmis Arapca bloklar**dir (olcumun dayanagi).
    from sunnah_karsilastir import sayfa_arapca_bloklar
    for no in SUNNAH:
        url = "https://sunnah.com/bukhari:%s" % no
        b = indir(url)
        ad_ham = "sunnah_%s.html" % no
        with open(os.path.join(SNAP, ad_ham), "wb") as f:
            f.write(b)          # referans olarak durur, SHA'ya GIRMEZ
        bloklar = sayfa_arapca_bloklar(b.decode("utf-8", "replace"))
        icerik = ("\n".join(bloklar) + "\n").encode("utf-8")
        ad = "sunnah_%s.bloklar.txt" % no
        with open(os.path.join(SNAP, ad), "wb") as f:
            f.write(icerik)
        satirlar.append((ad, sha(icerik)))
        print("YAZILDI: %s %d blok (ham %d bayt, SHA'ya girmez) sha=%s"
              % (ad, len(bloklar), len(b), sha(icerik)[:12]))
    for ayet in AYETLER:
        for meal in MEALLER:
            url = "https://api.alquran.cloud/v1/ayah/%s/%s" % (ayet, meal)
            b = indir(url)
            ad = "ayet_%s__%s.json" % (ayet.replace(":", "-"), meal)
            with open(os.path.join(SNAP, ad), "wb") as f:
                f.write(b)
            satirlar.append((ad, sha(b)))
            print("YAZILDI: %s %d bayt sha=%s" % (ad, len(b), sha(b)[:12]))

    # HADEETHENK TR (7 Kasim 2026, OLCULMEYEN hadis Turkce cevirisi): Arapca
    # sabitlenmisti, Turkce ceviri "bagimsiz dogrulanmadi" idi. Artik bagimsiz
    # Turkce kaynak da sabitlenir; ceviri iddiasi cevrimdisi de olculebilir.
    # `attribution` + `grade` alanlari da saklanir — kunye denetlenebilsin.
    from hadis_tr_karsilastir import HADISLER
    for no, kid in HADISLER.items():
        url = "https://hadeethenc.com/api/v1/hadeeths/one/?language=tr&id=%s" % kid
        b = indir(url)
        veri = json.loads(b.decode("utf-8"))
        icerik = json.dumps({"id": kid,
                             "attribution": veri.get("attribution"),
                             "grade": veri.get("grade"),
                             "hadeeth": veri.get("hadeeth")},
                            ensure_ascii=False, sort_keys=True).encode("utf-8")
        ad = "hadeeth_%s__tr.json" % no
        with open(os.path.join(SNAP, ad), "wb") as f:
            f.write(icerik)
        satirlar.append((ad, sha(icerik)))
        print("YAZILDI: %s (%s · %s) sha=%s" % (ad, veri.get("attribution"),
                                                veri.get("grade"), sha(icerik)[:12]))

        # ARAPCA (7 Kasim 2026, OLCULMEYEN kalem 2): id eslesmesi Turkce baslikla
        # degil ARAPCA metinle kanitlanir; kanit cevrimdisi de gerekli.
        url_ar = "https://hadeethenc.com/api/v1/hadeeths/one/?language=ar&id=%s" % kid
        veri_ar = json.loads(indir(url_ar).decode("utf-8"))
        icerik_ar = json.dumps({"id": kid,
                                "attribution": veri_ar.get("attribution"),
                                "grade": veri_ar.get("grade"),
                                "hadeeth": veri_ar.get("hadeeth")},
                               ensure_ascii=False, sort_keys=True).encode("utf-8")
        ad_ar = "hadeeth_%s__ar.json" % no
        with open(os.path.join(SNAP, ad_ar), "wb") as f:
            f.write(icerik_ar)
        satirlar.append((ad_ar, sha(icerik_ar)))
        print("YAZILDI: %s sha=%s" % (ad_ar, sha(icerik_ar)[:12]))

    import datetime
    tarih = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(MANIFEST, "w", encoding="utf-8") as f:
        # YAS DAMGASI (7 Kasim 2026, OLCULMEYEN kalem 3): snapshot ESKIR. Tarih
        # yazilmazsa "7 Kasim hali"ni olcmeye devam ederiz ve kimse fark etmez.
        # NOT (12 Kasim 2026, Z7): TAZELEME dosya bazli tarihi YENIDEN yazar.
        # Once yalniz 2 sutun yaziyordu; bir tazeleme kosusu 3. sutunu
        # SESSIZCE DUSURUR ve `yas_dosya()` mtime'a duserdi (yani kayma
        # gorunmez olurdu). Artik her satir kendi tazeleme tarihini tasir.
        f.write("# SNAPSHOT_TARIH=%s\n" % tarih)
        for ad, g in satirlar:
            f.write("%s  %s  %s\n" % (g, ad, tarih))
    print("MANIFEST: %d dosya -> %s (tarih %s)" % (len(satirlar), MANIFEST, tarih))
    return 0


def eksik_indir():
    """YALNIZ manifestte OLMAYAN ayet dosyalarini indir ve manifeste EKLE.

    NEDEN (13 Kasim 2026, Z11): `yenile()` TUM snapshot'lari yeniden indirir.
    Orneklemi 6 -> 12 ayete cikarinca bu 60 dosyanin hepsini yeniden yazardı:
    mtime'lar bugune kayar, `MTIME_KAYMASI` 60 dosyaya cikar ve "ne zaman
    indirildi" bilgisi tumden kaybolurdu. Ustelik mevcut 54 ayet dosyasi
    ZATEN dogru — yeniden indirmek gereksiz ag trafigi.
    Bu mod yalniz EKSIK olani indirir; mevcut satirlara DOKUNMAZ.
    """
    os.makedirs(SNAP, exist_ok=True)
    mevcut = manifest_oku()
    if mevcut is None:
        print("HATA: manifest yok: %s" % MANIFEST, file=sys.stderr)
        return 1
    import datetime
    bugun = datetime.date.today().isoformat()
    yeni_satirlar = []
    atlanan = 0
    for ayet in AYETLER:
        for meal in MEALLER:
            ad = "ayet_%s__%s.json" % (ayet.replace(":", "-"), meal)
            if ad in mevcut:
                atlanan += 1
                continue
            url = "https://api.alquran.cloud/v1/ayah/%s/%s" % (ayet, meal)
            try:
                b = indir(url)
            except Exception as e:
                print("HATA: %s indirilemedi: %s" % (ad, e), file=sys.stderr)
                return 1
            with open(os.path.join(SNAP, ad), "wb") as f:
                f.write(b)
            yeni_satirlar.append((ad, sha(b)))
            print("YAZILDI: %s %d bayt sha=%s" % (ad, len(b), sha(b)[:12]))

    if not yeni_satirlar:
        print("EKSIK: yok — %d dosya zaten manifestte" % atlanan)
        return 0

    # Manifeste EKLE (mevcut satirlara dokunma; I6: silme yok).
    metin = open(MANIFEST, encoding="utf-8").read().rstrip("\n").splitlines()
    for ad, g in yeni_satirlar:
        metin.append("%s  %s  %s" % (g, ad, bugun))
    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write("\n".join(metin) + "\n")
    print("MANIFEST: +%d satir (atlanan %d) -> %s"
          % (len(yeni_satirlar), atlanan, MANIFEST))
    # DOGRULAMA ZORUNLU (14 Kasim 2026, Z21 / C-#4) -------------------------
    # NEDEN (olculdu): `--eksik` manifeste YAZIP cikiyordu; `dogrula()`
    # cagrilmiyordu (olculdu: govdede 0 cagri). Indirme yarida kalirsa ya da
    # icerik bozuk gelirse `--eksik` rc=0 doner ve kimse fark etmez.
    # Artik yazdiktan sonra DOGRULAR; basarisizsa rc=1.
    return dogrula(ayrintili=False)


def oz_test():
    """UC DALIN da COKMEDIGINI olcer (14 Kasim 2026, Z21b / C-#5).

    NEDEN: `main()` duzeltmesi "her dal korumali" diyor; bu iddia OLCULMEDEN
    yazilamaz. Oz-test manifest'i okunamaz hale getirir (chmod 000) ve her
    dal icin iki sey arar: (1) traceback YOK, (2) stderr'de `HATA:` var,
    (3) rc=2. Manifest `try/finally` ile geri yuklenir ve sha'si dogrulanir.
    AG KULLANILMAZ: yalnizca `--dogrula` ve `--eksik` kosar; `yenile()` (tum
    snapshot'i yeniden indiren dal) BILEREK kosmaz — yan etkisi var (olculdu:
    kosunca `sunnah_39.html` / `sunnah_6094.html` yeniden yazildi, agac
    kirlendi). Onun icin yalniz KOD yolunu okuyoruz.
    """
    import subprocess as _sp
    if not os.path.exists(MANIFEST):
        print("HATA: manifest yok", file=sys.stderr)
        return 1
    with open(MANIFEST, "rb") as f:
        yedek = f.read()
    mod = os.stat(MANIFEST).st_mode
    kotu = []
    try:
        os.chmod(MANIFEST, 0o000)
        for dal in (["--dogrula"], ["--eksik"]):
            r = _sp.run([sys.executable, os.path.abspath(__file__)] + dal,
                        capture_output=True, text=True, timeout=300)
            tb = "Traceback" in r.stderr
            hata = "HATA:" in r.stderr
            if tb:
                kotu.append("%s TRACEBACK" % " ".join(dal))
            if not hata:
                kotu.append("%s HATA satiri yok" % " ".join(dal))
            if r.returncode != 2:
                kotu.append("%s rc=%d (beklenen 2)" % (" ".join(dal),
                                                       r.returncode))
    finally:
        os.chmod(MANIFEST, mod)
        with open(MANIFEST, "wb") as f:
            f.write(yedek)
    with open(MANIFEST, "rb") as f:
        if sha(f.read()) != sha(yedek):
            kotu.append("manifest GERI YUKLENEMEDI")
    if kotu:
        print("OZ-TEST: COKTU — " + " · ".join(kotu), file=sys.stderr)
        return 1
    print("OZ-TEST: 2 dal korumali (traceback yok · HATA satiri var · rc=2)")
    return 0


def main(argv):
    # HER DAL KORUMALI (14 Kasim 2026, Z21b / C-#5) --------------------------
    # NEDEN (olculdu): `yenile()` try icindeydi ama `dogrula()` ve
    # `eksik_indir()` DEGILDI. Manifest okunamaz hale getirildi
    # (`chmod 000`) ve olculdu:
    #   rc=1 · stdout BOS · stderr "Traceback (most recent call last): ...
    #   PermissionError: [Errno 13] Permission denied: ...SNAPSHOT.sha256"
    # Yani kapi cokuyor ama kullanici "HATA:" bicimli TEK satir gormuyor;
    # ciktiyi ayristiran arac (lint) tanidik desen bulamaz. Ayrica `rc`
    # anlamli ayrilmamisti: "olcum basarisiz" (1) ile "betik cokdu" (2) ayni.
    # Simdi: her dal korumali, cokme rc=2 + tek satir HATA.
    try:
        if "--oz-test" in argv:
            return oz_test()
        if "--dogrula" in argv:
            return dogrula()
        if "--eksik" in argv:
            return eksik_indir()
        return yenile()
    except Exception as e:
        print("HATA: %s: %s: %s" % (' '.join(argv[1:]) or 'yenile',
                                    type(e).__name__, e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
