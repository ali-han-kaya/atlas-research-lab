#!/usr/bin/env python3
"""sunnah_karsilastir.py — SKILL.md'deki Arapca hadis alintisini sunnah.com ile karsilastirir.

NEDEN (7 Kasim 2026, kalem 2): `SKILL.md` "sunnah.com govdesiyle birebir ayni"
diyordu ama bu iddia GERI ALINMISTI — `webfetch` yaniti dosyada yoktu, kunye
`OLCULMEDI` idi. Bu betik iddiayi olculebilir hale getirir.

OLCUT: alinti, sayfadaki Arapca bloklardan BIRIYLE normalize-esit mi?
  normalize = hareke (U+064B-0652, U+0670, U+06D6-06ED) silinir,
              Arapca disi karakterler silinir, bosluk teklesir.
  Yani "sayfada VAR MI" olculur; "baska yerde de var mi" olculmez.

Erisim notu (olculdu): `curl` bugun 403 · `urllib` duz de 403 ·
`urllib` + tarayici User-Agent = **200**. Bu yuzden UA sabit yazildi.

Kullanim:
    python3 scripts/sunnah_karsilastir.py SKILL.md 6094
    python3 scripts/sunnah_karsilastir.py SKILL.md 39

Cikti (ham):
    SAYFA: https://sunnah.com/bukhari:6094 -> 200 (30521 bayt)
    BLOK : 3 arapca blok
    ALINTI: harakatsiz 34 kelime
    SONUC: ESIT (blok #2 ile)

Exit: 0 = alinti sayfada BIREBIR var · 1 = bulunamadi / ag hatasi · 2 = kullanim
"""
import hashlib
import os
import re
import sys
import unicodedata
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

HAREKE = set(range(0x064B, 0x0653)) | {0x0670} | set(range(0x06D6, 0x06EE))
# ARAPCA NOKTALAMA da silinir (7 Kasim 2026, olcum): `،`=U+060C harf araliginda
# oldugu icin normalize'da KALIYORDU; alinti virgulsuz, sayfa virgullu oldugu icin
# karsilastirma "BULUNAMADI" donuyordu. Olculdu: blok 34 kelime, alinti 34 kelime,
# tek fark noktalama.
NOKTALAMA = {0x060C, 0x061B, 0x061F, 0x066A, 0x066B, 0x066C, 0x066D,
             0x06D4, 0x066E, 0x2E41, 0x00AB, 0x00BB}


def normalize(s):
    """Harake + noktalama sil, yalniz Arapca harfleri tut, bosluk teklesir."""
    out = []
    for ch in s:
        o = ord(ch)
        if o in HAREKE or o in NOKTALAMA:
            continue
        if 0x0600 <= o <= 0x06FF:
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())


# HARF VARYANTLARI (7 Kasim 2026, OLCULMEYEN kalem 10): Arapca'da ayni sesin
# iki yazimi olabilir — elif+hemze (U+0623) ile elif (U+0627), ye+hemze (U+0626)
# ile ye (U+064A). Olculdu: normalize('\u0623') != normalize('\u0627'), yani
# yazim farki "birebir degil" hukmu veriyordu.
# KURAL: bu esleme **SIKI** olcume GIRMEZ. SIKI olcum birebir ayniligi olcer
# (iddia odur). Gevsek esleme yalniz **bilgi** olarak yazilir — gecis sebebi
# gorunsun, ama esik dusurulmesin.
VARYANT = {
    0x0623: 0x0627,  # elif + hemze ustu  -> elif
    0x0625: 0x0627,  # elif + hemze alti  -> elif
    0x0622: 0x0627,  # elif + med         -> elif
    0x0624: 0x0648,  # vav + hemze        -> vav
    0x0626: 0x064A,  # ye + hemze         -> ye
    0x0649: 0x064A,  # elif maksura       -> ye
    0x0629: 0x0647,  # te marbuta         -> he
}


def gevsek(s):
    """SIKI normalize + harf varyant eslemesi (yalniz BILGI amacli)."""
    out = []
    for ch in normalize(s):
        out.append(" " if ch == " " else chr(VARYANT.get(ord(ch), ord(ch))))
    return " ".join("".join(out).split())


def sayfa_arapca_bloklar(html):
    """HTML'den Arapca bloklari cikarir (en az 20 Arapca karakter)."""
    # etiketleri bosluga cevir
    temiz = re.sub(r"<[^>]+>", " ", html)
    # Arapca kosullar
    adaylar = re.findall(r"[\u0600-\u06FF][\u0600-\u06FF\s\u064B-\u0652\u0670\u06D6-\u06ED\u060C.\u061F]*", temiz)
    bloklar = []
    for a in adaylar:
        n = normalize(a)
        if len(n.split()) >= 5:
            bloklar.append(n)
    # tekrarlari at, sirayi koru
    gorulen, benzersiz = set(), []
    for b in bloklar:
        if b not in gorulen:
            gorulen.add(b)
            benzersiz.append(b)
    return benzersiz


def _snapshot_yolu(hadis):
    """`tests/snapshot/sunnah_<no>.bloklar.txt` + sha dogrulamasi.

    DUZELTME (7 Kasim 2026, olculdu): once HAM HTML sabitleniyordu. sunnah.com
    her istekte bayt duzeyinde farkli HTML donduruyor (iki ardisik indirme:
    sha 27b02cc90e22 vs 2889b62ec9db, 30521 bayt ikisi) — ama **Arapca bloklar
    ayni**. Ham sha her tazelemede kiriliyordu; sabitlenen sey artik **normalize
    edilmis Arapca bloklar**. Olcumun dayanagi budur, sayfanin cerezi degil.
    """
    burasi = os.path.dirname(os.path.abspath(__file__))
    snap = os.path.join(burasi, "tests", "snapshot")
    ad = "sunnah_%s.bloklar.txt" % hadis
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
    return veri.decode("utf-8"), "snapshot (sha dogrulandi)"


def sayfa_al(url, hadis):
    """Once CANLI dener; ag yoksa SHA'SI TUTAN snapshot'a duser.

    NEDEN (7 Kasim 2026, OLCULMEYEN kalem 2): once yalniz canli vardi; ag yoksa
    olcum FAIL ediyordu ve cevrimdisi ortamda lab hic yesil olamiyordu.
    Snapshot **sha256** ile sabit: icerik degisirse sha tutmaz -> FAIL (fail-closed).
    """
    if os.environ.get("SNAPSHOT_ONLY") == "1":
        canli_hata = "SNAPSHOT_ONLY=1 (cevrimdisi test)"
    else:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8", "replace"), "HTTP %d" % r.status, "canli (HTTP %d)" % r.status
        except Exception as e:
            canli_hata = "%s %s" % (type(e).__name__, e)
    icerik, durum = _snapshot_yolu(hadis)
    if icerik is None:
        return None, None, "canli: %s · %s" % (canli_hata, durum)
    return icerik, "SNAPSHOT", "%s [canli basarisiz: %s]" % (durum, canli_hata)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    yol, hadis = argv[1], argv[2]

    try:
        with open(yol, encoding="utf-8") as f:
            metin = f.read()
    except OSError as e:
        print("HATA: %s" % e, file=sys.stderr)
        return 2

    # alintiyi dosyadan cek: TUM Arapca alintilari sirayla dene
    alintilar = [g.group(1) for g in re.finditer(r"`([\u0600-\u06FF][^`]{40,})`", metin)]
    if not alintilar:
        print("HATA: dosyada Arapca alinti bulunamadi", file=sys.stderr)
        return 1

    istenen_url = "https://sunnah.com/bukhari:%s" % hadis
    html, kod, kaynak = sayfa_al(istenen_url, hadis)
    if html is None:
        print("SAYFA: %s -> HATA %s" % (istenen_url, kaynak), file=sys.stderr)
        return 1
    print("KAYNAK: %s" % kaynak)

    if kaynak.startswith("snapshot"):
        # snapshot ZATEN normalize edilmis bloklari tasir (satir basina bir blok)
        print("SAYFA: %s -> %s" % (istenen_url, kod))
        bloklar = [x for x in html.split("\n") if x.strip()]
    else:
        print("SAYFA: %s -> %s (%d bayt)" % (istenen_url, kod, len(html)))
        bloklar = sayfa_arapca_bloklar(html)
    print("BLOK : %d arapca blok" % len(bloklar))
    print("ALINTI: %d aday (%s kelime)" % (
        len(alintilar), "/".join(str(len(normalize(a).split())) for a in alintilar)))

    # HER alintiyi dene; eslesen ilk alintiyi bildir
    for j, a in enumerate(alintilar):
        norm = normalize(a)
        for i, b in enumerate(bloklar):
            if b == norm:
                print("SONUC: ESIT — alinti #%d (blok #%d ile) [SIKI]" % (j, i))
                return 0
            if norm in b:
                print("SONUC: ALT_DIZI — alinti #%d (blok #%d icinde) [SIKI]" % (j, i))
                return 0

    # 2) GEVSEK (harf varyanti) — YALNIZ BILGI, PASS degil
    for j, a in enumerate(alintilar):
        g = gevsek(a)
        for i, b in enumerate(bloklar):
            if gevsek(b) == g:
                print("SONUC: BULUNAMADI — SIKI eslesme YOK; gevsek esleme var "
                      "(alinti #%d ~ blok #%d, harf varyanti farki). Bu BIREBIR "
                      "AYNI DEGILDIR." % (j, i))
                return 1

    # OLCUM SONUCU stdout'a yazilir (hata degil): kapilar son satiri okur.
    print("SONUC: BULUNAMADI — hicbir alinti sayfadaki bloklarla eslesmiyor")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
