#!/usr/bin/env python3
"""hadis_tr_karsilastir.py — SKILL.md'deki TURKCE hadis cevirilerini
BAGIMSIZ bir Turkce hadis kaynagiyla (hadeethenc.com) karsilastirir.

NEDEN (7 Kasim 2026, `OLCULMEYEN` hadis Turkce cevirisi): `SKILL.md` iki hadisin
Turkce cevirisini tasiyor ama bunlar **bu dosyanin kendi metni**ydi —
"bagimsiz dogrulanmadi, `OLCULMEDI`". Yani Arapca sabitlenmis, Turkce serbestti.
Bu betik o boslugu olcer: ceviri BAGIMSIZ kaynakla ortusuyor mu?

KAYNAK: `hadeethenc.com` (Türkiye Diyanet Vakfı / Rabwah merkezli, cok dilli
hadis ansiklopedisi). Her hadis icin `attribution` (kimin rivayet ettigi) ve
`grade` (siyha derecesi) alanlarini da tasir — yani kunye de denetlenebilir.

KUNYE ESLESMESI (elle yazildi, olculdu):
    SKILL Buhari 6094 -> hadeethenc id=5504  (attribution: Muttefekun aleyh)
    SKILL Buhari 39   -> hadeethenc id=5795  (attribution: Buhari rivayet etmistir)
Eslestirme Arapca metin + konu basligiyla dogrulandi; id'ler tahmin degil,
kategori listesi `per_page=100` ile tarandi ve baslikla bulundu.

OLCUT (hadis basina):
  1. `SKILL.md`den hadisin Turkce ceviri cumlesi cikarilir.
  2. Icerik kelimeleri + kaba kok (ayni `ayet_ozet_kontrol.py` fonksiyonlari —
     tek mekanizma, iki kopya degil).
  3. Kok, bagimsiz Turkce hadis metninde geciyor mu?
  4. Kapsam = bulunan / toplam. **Kapsam < ESIK -> SAPMA.**

  Bu "birebir ceviri" olcumu DEGILDIR — "ceviri uydurma degil, bagimsiz kaynakta
  karsiligi var" olcumudur. Birebir iddia icin ayri kanit gerekir.

Kullanim:
    python3 scripts/hadis_tr_karsilastir.py [SKILL.md]
    python3 scripts/hadis_tr_karsilastir.py --kunye     # yalniz kunye/derece
    SNAPSHOT_ONLY=1 python3 scripts/hadis_tr_karsilastir.py   # cevrimdisi

Exit: 0 = hepsi TAM · 1 = SAPMA / ag hatasi · 2 = kullanim
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

from ayet_ozet_kontrol import icerik_kelimeleri, kok, tr

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

BURASI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(os.path.dirname(BURASI), "SKILL.md")

ESIK = 0.5

HADISLER = {"6094": "5504", "39": "5795"}


def _snapshot(hadis):
    """`tests/snapshot/hadeeth_<no>__tr.json` + sha dogrulamasi; yoksa (None, sebep)."""
    snap = os.path.join(BURASI, "tests", "snapshot")
    ad = "hadeeth_%s__tr.json" % hadis
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


def kaynak(hadis):
    """Once CANLI; ag yoksa SHA'SI TUTAN snapshot. Donus: (etiket, sozluk)."""
    kid = HADISLER[hadis]
    url = "https://hadeethenc.com/api/v1/hadeeths/one/?language=tr&id=%s" % kid
    canli_hata = None
    if os.environ.get("SNAPSHOT_ONLY") != "1":
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                veri = json.loads(r.read().decode("utf-8"))
                return "HTTP %d" % r.status, veri
        except Exception as e:
            canli_hata = "%s %s" % (type(e).__name__, e)
    else:
        canli_hata = "SNAPSHOT_ONLY=1"
    veri, durum = _snapshot(hadis)
    if veri is None:
        raise RuntimeError("canli: %s · %s" % (canli_hata, durum))
    sozluk = json.loads(veri.decode("utf-8"))
    # KAYNAK KIMLIGI KILIDI (7 Kasim 2026): snapshot `no` ile adlandigi icin
    # yanlis `kid` eslesmesi MASKELENIYORDU. Snapshot kendi `id`sini tasir;
    # beklenen `kid` ile tutmazsa fail-closed.
    if str(sozluk.get("id")) != str(kid):
        raise RuntimeError(
            "snapshot BASKA hadise ait: dosya id=%s, beklenen id=%s"
            % (sozluk.get("id"), kid))
    return "%s [canli: %s]" % (durum, canli_hata), sozluk


def ceviri_cumlesi(metin, hadis):
    """`SKILL.md`den hadisin Turkce ceviri cumlesini cikarir.

    Desen: ayni satirda `Buhari <no>` ve `**Turkce tam ceviri** ...: "..."`.
    Hadis numarasi ile ceviri AYNI satirda olmak zorunda — boylece yanlis
    hadisin cevirisi eslesmez.
    """
    for satir in metin.splitlines():
        if ("Buhari %s" % hadis) not in satir:
            continue
        # ONCE «...» : resmi kaynaktan ALINTI (7 Kasim 2026 sonrasi bicim).
        m = re.search(r"\u00ab([^\u00bb]{20,900})\u00bb", satir)
        if m:
            return m.group(1)
        # GERIYE UYUM: eski serbest ceviri bicimi ("...").
        m = re.search(r"Turkce tam ceviri\*\*[^:]*:\s*\"([^\"]{20,600})\"", satir)
        if m:
            return m.group(1)
    return None


def kapsam(ceviri, kaynak_metni):
    """Icerik kelimelerinin kaci bagimsiz kaynakta geciyor."""
    kelimeler = icerik_kelimeleri(ceviri)
    if not kelimeler:
        return None, [], []
    m = tr(kaynak_metni)
    gecen = [k for k in kelimeler if kok(k) in m]
    return len(gecen) / len(kelimeler), gecen, kelimeler


def main(argv):
    if len(argv) > 1 and argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2

    sadece_kunye = "--kunye" in argv
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

    tam, toplam = 0, 0
    for hadis in HADISLER:
        toplam += 1
        try:
            etiket, veri = kaynak(hadis)
        except RuntimeError as e:
            print("Buhari %-5s (hadeethenc id=%s)  HATA: %s" % (hadis, HADISLER[hadis], e))
            continue
        print("Buhari %-5s (hadeethenc id=%s)  %s" % (hadis, HADISLER[hadis], etiket))
        print("  KUNYE : %s · DERECE: %s" % (veri.get("attribution", "?"),
                                             veri.get("grade", "?")))
        if sadece_kunye:
            tam += 1
            continue
        cumle = ceviri_cumlesi(metin, hadis)
        if cumle is None:
            print("  -> CEVIRI_YOK (SKILL.md'de `Turkce tam ceviri` cumlesi bulunamadi)")
            continue
        oran, gecen, kelimeler = kapsam(cumle, veri.get("hadeeth", ""))
        if oran is None:
            print("  -> ICERIK_KELIMESI_YOK")
            continue
        durum = "TAM" if oran >= ESIK else "SAPMA"
        if durum == "TAM":
            tam += 1
        print("  KAPSAM: %d/%d (%.2f)  %s" % (len(gecen), len(kelimeler), oran, durum))
        if durum == "SAPMA":
            eksik = [k for k in kelimeler if k not in gecen]
            print("  KAYNAKTA GECMEYEN: %s" % ", ".join(eksik))

    print("SONUC: %d/%d hadis TAM (esik %.2f, kaynak hadeethenc.com)" % (tam, toplam, ESIK))
    return 0 if tam == toplam else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
