#!/usr/bin/env python3
"""hadis_id_dogrula.py — `hadeethenc` id eslesmesini ARAPCA ile KANITLAR.

NEDEN (7 Kasim 2026, `OLCULMEYEN` kalem 2): `hadis_tr_karsilastir.py` iki
hadisi hadeethenc id'leriyle eslestiriyor (6094 -> 5504, 39 -> 5795) ama bu
eslesme **elle**, Turkce basliga bakilarak yapildi. Eslesme yanlissa
"2/2 hadis TAM" olcumu YANLIS hadisi olcer — yani olcumun temeli curuk olur.

COZUM: iki BAGIMSIZ kaynagin **Arapca** metni karsilastirilir.
    kaynak A: sunnah.com  (SKILL.md'deki alinti + `sunnah_<no>.bloklar.txt`)
    kaynak B: hadeethenc.com (`language=ar&id=<kid>`)
Arapca iki kaynakta da ayni ise id eslesmesi KANITLANMIS olur; Turkce ceviri
de dogru hadise aittir.

OLCUT (7 Kasim 2026 duzeltmesi — ILK OLCUT YANLISTI): once "birebir alt dizgi"
araniyordu. Olculdu ki Buhari 6094 icin **tutmuyor** — ama sebep yanlis id
DEGIL, **farkli rivayet**: iki kaynak ayni hadisi iki degisik lafizla veriyor
(sunnah: "...وإن الرجل ليصدق حتى يكون صديقا...", hadeethenc: "...وما يزال
الرجل يصدق ويتحري الصدق..."). Ikisi de ayni hadis (muttefekun aleyh).

Bu yuzden olcut **degismeZ obek ortusmesi**dir: harakatsiz metinlerde 3
kelimelik kayan pencere kesisimi / kucuk metnin obek sayisi.
    >= 0.50 -> AYNI_HADIS (id eslesmesi dogrulandi)
    <  0.50 -> FARKLI (id eslesmesi curuk)
Farkli rivayet lafizlari **gizlenmez**: ortusmeyen parcalar yazdirilir.
Bu "metinler ayni" demek degildir — "ayni hadis" demektir.

Kullanim:
    python3 scripts/hadis_id_dogrula.py [SKILL.md]
    SNAPSHOT_ONLY=1 python3 scripts/hadis_id_dogrula.py     # cevrimdisi

Exit: 0 = iki hadis de Arapca ile dogrulandi · 1 = eslesme tutmuyor · 2 = kullanim
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

from ayet_ozet_kontrol import tr
from hadis_tr_karsilastir import HADISLER

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

BURASI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(os.path.dirname(BURASI), "SKILL.md")

# ESIK: obek ortusmesi icin "ayni hadis" siniri. INSAN secimi.
# DUYARLILIK OLCULDU (7 Kasim 2026): dogru eslesme 0.53-1.00, yanlis 0.00;
# gecerli aralik 0.01-0.53, yani 0.50 UST KENARDA. Simdilik korunuyor —
# degistirmek insan karari — ama negatif kontrol her kosuda kosar (fail-closed).
ESIK = 0.5


def arapca_normal(s):
    """Harakatsiz + elif/hemze sadelesmis Arapca (karsilastirma icin).

    NEDEN: `tr()` Turkce icin yazildi ve `[^a-z0-9 ]` Arapcayi SILER.
    Burada ayri bir normalizasyon gerekir — ama gevsek degil: yalniz haraket
    ve elif/hemze/yeterme varyanti sadelesir, HARFLER korunur.
    """
    s = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", s)     # haraket + teveel
    s = re.sub(r"[\u0622\u0623\u0625\u0627]", "\u0627", s)  # elif varyantlari
    s = s.replace("\u0649", "\u064A")                      # elif maksura -> ye
    s = s.replace("\u0629", "\u0647")                      # te marbuta -> he
    s = re.sub(r"[\u060C\u061B\u061F.,:;\"'«»\(\)\[\]]", " ", s)
    return " ".join(s.split())


def obek_orani(a, b, n=3):
    """`a`nin n-gram obeklerinden kaci `b`de var (0..1)."""
    ka, kb = obekler(a, n), obekler(b, n)
    return len(ka & kb) / len(ka) if ka else 0.0


def obekler(kelimeler, n=3):
    """n kelimelik kayan pencere kumesi (rivayet farkina dayanikli)."""
    return {" ".join(kelimeler[i:i + n]) for i in range(len(kelimeler) - n + 1)}


def _snapshot(no):
    """`no` = SKILL hadis numarasi (6094 / 39). Kid DEGIL.

    KUSUR (7 Kasim 2026, mutasyon testinde yakalandi): once `kid` gecirilip
    ters esleme (`kids_icin`) ile dosya adi tahmin ediliyordu. Ayni kid iki
    hadise eslendiginde (mutasyon: 6094 -> 5795) 6094 icin **39'un dosyasi**
    okundu (62 kelime, 17/32) — yani yanlis id MASKELENIYORDU. Artik `no`
    dogrudan gecirilir; maskeleme imkansiz.
    """
    snap = os.path.join(BURASI, "tests", "snapshot")
    ad = "hadeeth_%s__ar.json" % no
    yol = os.path.join(snap, ad)
    man = os.path.join(snap, "SNAPSHOT.sha256")
    if not os.path.exists(yol) or not os.path.exists(man):
        return None, "snapshot yok"
    beklenen = None
    with open(man, encoding="utf-8") as f:
        for satir in f:
            if satir.lstrip().startswith("#"):
                continue
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


def arapca_kaynak(no, kid):
    url = "https://hadeethenc.com/api/v1/hadeeths/one/?language=ar&id=%s" % kid
    canli_hata = None
    if os.environ.get("SNAPSHOT_ONLY") != "1":
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return "HTTP %d" % r.status, json.loads(r.read().decode("utf-8"))
        except Exception as e:
            canli_hata = "%s %s" % (type(e).__name__, e)
    else:
        canli_hata = "SNAPSHOT_ONLY=1"
    veri, durum = _snapshot(no)
    if veri is None:
        raise RuntimeError("canli: %s · %s" % (canli_hata, durum))
    sozluk = json.loads(veri.decode("utf-8"))
    # KAYNAK KIMLIGI KILIDI (7 Kasim 2026, mutasyon testinde yakalandi): snapshot
    # `no` ile adlandigi icin yanlis `kid` eslesmesini MASKELIYORDU — mutasyon
    # (6094 -> 5795) yanmadi, hala 2/2 cikti. Artik snapshot kendi `id`sini
    # tasir ve beklenen `kid` ile karsilastirilir; tutmazsa fail-closed.
    if str(sozluk.get("id")) != str(kid):
        raise RuntimeError(
            "snapshot BASKA hadise ait: dosya id=%s, beklenen id=%s — id eslesmesi "
            "degismis, snapshot tazelenmeden olcum YAPILAMAZ"
            % (sozluk.get("id"), kid))
    return "%s [canli: %s]" % (durum, canli_hata), sozluk


def skill_alintisi(metin, hadis):
    """`SKILL.md`den hadisin ARAPCA alintisini cikarir (`` `...` `` icinde)."""
    for satir in metin.splitlines():
        if ("Buhari %s" % hadis) not in satir:
            continue
        m = re.search(r"\(sunnah\.com[^)]*\):\s*`([^`]{40,900})`", satir)
        if m:
            return m.group(1)
    return None


def main(argv):
    if len(argv) > 1 and argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2
    # [DUZELTME 2026-11-13, Z10] YOL HER SIRADA OKUNUR.
    # NEDEN (olculdu): `--kunye`/baska bayrak ONCE gelince `argv[1]` bayrak
    # oluyor ve yol SESSIZCE `SKILL.md`ye dusuyordu. Ayrım edici test — OLMAYAN
    # yol verilince:
    #   `--kunye /yok/boyle.md`   -> rc=0 "SONUC: 2/2 hadis TAM"  (yol YOK SAYILDI)
    #   `/yok/boyle.md --kunye`   -> rc=2 "HATA: okunamadi ..."    (dogru)
    # Ayni sinif `ayet_ozet_kontrol.py`de olculmustu (Z9/EK 79). Sinif tek
    # yerde kapatilmaz: bayrak olmayan ILK arguman yoldur.
    yol = next((a for a in argv[1:] if not a.startswith("-")), SKILL)
    try:
        with open(yol, encoding="utf-8") as f:
            metin = f.read()
    except OSError as e:
        print("HATA: %s okunamadi: %s" % (yol, e), file=sys.stderr)
        return 2

    # --- NEGATIF KONTROL (7 Kasim 2026, OLCULMEYEN kalem 5) -----------------
    # KUSUR: esik 0.50 secildi ama DUYARLILIGI olculmedi. Olculdu: Buhari 6094
    # obek orani 0.53 — esigin yalniz 0.03 ustunde, yani KENARDA. Ustelik
    # n-gram boyuna gore dusuyor (n=2: 0.59, n=3: 0.53, n=4: 0.45, n=5: 0.37).
    # Yani "0.50 gecti" tek basina zayif bir cumle.
    # Gercek ayirici ESIK degil AYRIM: dogru eslesme 0.53-1.00, YANLIS eslesme
    # 0.00. Olcum gercekten ayirt ediyor mu? Bunu her kosuda olc.
    onceki = {}
    tam = 0
    for hadis, kid in HADISLER.items():
        try:
            etiket, veri = arapca_kaynak(hadis, kid)
        except RuntimeError as e:
            print("Buhari %-5s <-> hadeethenc id=%s  HATA: %s" % (hadis, kid, e))
            continue
        print("Buhari %-5s <-> hadeethenc id=%s  %s" % (hadis, kid, etiket))
        alinti = skill_alintisi(metin, hadis)
        if alinti is None:
            print("  -> ARAPCA_ALINTI_YOK")
            continue
        a = arapca_normal(alinti).split()
        b = arapca_normal(veri.get("hadeeth", "")).split()
        ka, kb = obekler(a), obekler(b)
        ortak = ka & kb
        oran = len(ortak) / len(ka) if ka else 0.0
        ayni = oran >= 0.50
        print("  ALINTI: %d kelime · hadeethenc: %d kelime · ortak 3'lu obek %d/%d"
              % (len(a), len(b), len(ortak), len(ka)))
        print("  OBEK ORAN: %.2f -> %s" % (oran, "AYNI_HADIS" if ayni else "FARKLI"))
        onceki[hadis] = a
        if ayni:
            tam += 1
        # FARKLI RIVAYET LAFIZLARI GIZLENMEZ
        fark = [o for o in ka if o not in kb]
        if fark:
            print("  ALINTIDA OLUP KAYNAKTA OLMAYAN OBek: %s" % " | ".join(fark[:6]))
    # CAPRAZ: dogru eslesme vs YANLIS eslesme. Ayrım yoksa olcum ayirt etmiyor.
    dogru, yanlis, kaynaklar = [], [], {}
    for hadis, kid in HADISLER.items():
        try:
            _e, v = arapca_kaynak(hadis, kid)
        except RuntimeError:
            continue
        kaynaklar[hadis] = arapca_normal(v.get("hadeeth", "")).split()
        if hadis in onceki:
            oran_ = obek_orani(onceki[hadis], kaynaklar[hadis])
            dogru.append(oran_)
    for h in onceki:
        for k in kaynaklar:
            if h == k:
                continue
            yanlis.append(obek_orani(onceki[h], kaynaklar[k]))

    if dogru and yanlis:
        d_min, y_max = min(dogru), max(yanlis)
        ayrim = d_min - y_max
        gecerli = [i / 100 for i in range(1, 100)
                   if all(d >= i / 100 for d in dogru)
                   and all(y < i / 100 for y in yanlis)]
        print("NEGATIF KONTROL: dogru min=%.3f · yanlis max=%.3f · AYRIM=%.3f"
              % (d_min, y_max, ayrim))
        if gecerli:
            alt, ust = min(gecerli), max(gecerli)
            # KONUM: secili esik gecerli araligin neresinde (0=alt, 1=ust ucu).
            # "ICINDE" demek yetmez — ust kenarda durmak marji daraltir.
            konum = (ESIK - alt) / (ust - alt) if ust > alt else 0.0
            yer = ("ICINDE-UST-KENAR" if konum >= 0.85
                   else "ICINDE-ALT-KENAR" if konum <= 0.15
                   else "ICINDE-ORTA" if ESIK in gecerli else "DISINDA")
            print("ESIK: %.2f · gecerli aralik %.2f-%.2f · konum %.2f -> %s "
                  "(ust marj %.2f)" % (ESIK, alt, ust, konum, yer, ust - ESIK))
        else:
            print("ESIK: %.2f · AYIRAN ARALIK YOK" % ESIK)
        ayrim_ok = ayrim > 0.20
    else:
        print("NEGATIF KONTROL: OLCULEMEDI (capraz cift uretilemedi)")
        ayrim_ok = False

    print("SONUC: %d/%d hadis id eslesmesi ARAPCA obek ortusmesiyle dogrulandi"
          % (tam, len(HADISLER)))
    print("SONUC_AYRIM: %s" % ("AYIRT_EDIYOR" if ayrim_ok else "AYIRT_ETMIYOR"))
    return 0 if (tam == len(HADISLER) and ayrim_ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
