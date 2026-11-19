#!/usr/bin/env python3
"""Atlas v5.5.4 Cite Match — atif <-> kaynakca %100 eslesme denetimi

NEDEN VAR:
Lab'in hicbir betigi metin-ici atif ile kaynakca arasindaki eslesmeyi
denetlemiyordu. DENEME kosusunda govde tek kaynak aniyor, kaynakcada dort
girdi var; hicbir kapi bunu gormedi. isimlendir/OPTIMIZE_KOMUT_V5.9.md ise
"atif-kaynakca %100 eslessin" sartini kosuyor.

KONTROLLER:
  CITE-01  Metinde anilan her kaynak kaynakcada var          (eksik kaynak)
  CITE-02  Kaynakcadaki her girdi metinde en az bir kez anilir (oksuz kaynak)
  CITE-03  Ayni soyad icin celisen yil kullanimi              (UYARI)

Desteklenen bicimler: (Yazar, 2020) · (Smith & Doe, 2021) · (Kara, 2022, s. 5)
(A, 2020; B, 2021) · Yazar (2020) · Scholem (1941, s. 45) · (Yazar vd., 2020)
(Smith et al., 2021) · Tabari (1987) — TRANSLITERASYONLU adlar dahil
(Ṭabarī, Ḥallāj, Šekhinah, Ġazālī gibi noktali/uzatmali harfler)

v5.5.4 GUVENLIK DUZELTMESI (bagimsiz denetimde kanitlandi, bkz. CM-7/CM-8):
  ONCE: anlatimsal atif regex'i `[A-ZÇĞİÖŞÜ]` ile basliyordu ve yildan hemen
  sonra kapanis parantezi bekliyordu. Sonuc:
    - `Ṭabarī (1987)`  -> KACIYORDU (Ṭ karakter sinifinda yok)
    - `Scholem (1941, s. 45)` -> KACIYORDU (yil sonrasi sayfa eki)
  Ikisi de kaynakcada olmadigi halde CITE-MATCH PASS veriyordu. Islam/Yahudi
  calismalarinda yazar adlari transliterasyonludur ve 40+ kelimelik alintilarda
  sayfa numarasi ZORUNLUDUR — yani labin kendi kurali atifi denetciye gorunmez
  kiliyordu. Artik unicode harf sinifi + opsiyonel sayfa eki destekleniyor.

Kullanim:
  python3 scripts/cite_match.py
  python3 scripts/cite_match.py --dosya makale.md
  python3 scripts/cite_match.py --gevsek     # oksuz kaynak FAIL degil UYARI
"""
import re, sys, pathlib, unicodedata

# v1.7.275 (CM-10) — YANLIS POZITIF DUZELTMESI (olculdu: silat-makale, 10 Kasim 2026)
#   ONCE: parantez icinde yil varsa, yilin SOLUNDAKI HER SEY yazar adi sayiliyordu
#   (`ad = parca[:m.start()]`). Olculen sonuc — dort "atif"in dordu de atif degildi:
#     '(cilt 8, 2009)'                 -> dergi CILT NO   -> yazar "cilt 8"
#     '(kaynaklar/alusi-1924-...jpg)'  -> DOSYA YOLU      -> yazar "kaynaklar alusi-"
#     '(o. 1205/1791)'                 -> VEFAT TARIHI    -> yazar "o "
#   SIMDI: aday, yildan geriye dogru taranir ve yalniz MAKUL soyad kabul edilir
#   (_soyad_adayi). Kucuk harf baslangic, sayi, tek harf kisaltma, olcu/alan
#   sozcukleri (cilt/vol/s./p./baski/ed.) reddedilir. Makul aday yoksa parantez
#   atif SAYILMAZ — yanlis pozitif uretmektense hic uretmemek dogrudur (fail-closed
#   yonu: sahte FAIL yerine sahte PASS degil; bkz. DERSLER 2026-11-10).
#   CITE-02 de duzeltildi: kaynakca girdisi "atif kalibi taninmadi" diye oksuz
#   ilan ediliyordu. Artik soyad govdede geciyorsa INFO, hic gecmiyorsa FAIL.
#   (Olculdu: Al-Rawi 6 · El-Zein 5 · Yaltirik 4 · Alusi 11 kez metinde idi.)

MASTER_CANDS = ["03-FAZ-3-MASTER-v5.5.md", "03-FAZ-3-MASTER-v5.4.md",
                "03-FAZ-3-MASTER-v5.2.md", "MASTER.md"]
# DUZELTME (15 Kasim 2026, Z53 — OLCULDU): desen Fransizca basligi tanimiyordu.
# `re.I` aksan ESITLEMEZ: 'references' deseni 'références' ile eslesmez.
# OLCULDU (midéo MASTER, 10 aday baslik, betigin kendi deseniyle):
#   '## Bibliographie provisoire ...' GECMEZ · '## Bibliographie' GECMEZ
#   '## Références' GECMEZ · '## Références bibliographiques' GECMEZ
#   '## References' GECER · '## Kaynakça' GECER · '## Bibliyografya' GECER
# Yani Fransizca yazilmis bir MASTER kaynakca basligini gecebilmek icin
# Ingilizce veya Turkce baslik yazmak ZORUNDAYDI — kapinin kendi kusuru.
# Bu degisiklik kontrolu GEVSETMEZ: yalniz bolum BASLIGI tanima genisler;
# CITE-01/CITE-02 aynen kosar. OLCULDU: midéo ayni dosyada hala rc=1 —
#   ESKI desen: 'FAIL CITE-00: kaynakca bolumu bulunamadi'
#   YENI desen: 'FAIL CITE-00: kaynakcada Soyad, A. (Yil). bicimli girdi ayristirilamadi'
# yani kapi SUSMADI, gercek kusuru (kaynakca girdisi yok) gosterdi.
KAYNAKCA_BASLIK = re.compile(r"^#{1,6}\s.*(kaynak[cç]a|references|bibliyografya|bibliographie|r[ée]f[ée]rences)", re.I)
YIL = r"(1[6-9]\d{2}|20\d{2})"
# v1.7.403 (OLCULDU 17 Kasim 2026): HICRI/MILADI CIFT YIL.
# ONCE: kaynakcada `(505/1111)` bicimli girdi HIC sayilmiyordu; desen `505` gorup
#   atliyor, girdi sessizce DUSUYORDU. Fikstur olcumu: 3 girdi -> 1 sayilan.
# SIMDI: `(xxx/1yyy)` bicimi taninir ve anahtar MILADI taraf olur (`1111`), boylece
#   govdedeki `(Yazar, 1111)` atfiyla eslesir.
# DAR tutuldu (fail-closed): SOL taraf 1-3 haneli. `(2025/2076)` gibi YIL ARALIKLARI
#   eslesmez. TEK hicri yil `(1420)` KAYNAKCADA kabul EDILMEZ: `(1250)` gibi sayfa
#   numarasi olabilir (olculdu: labda 0 ornek, ama risk gercek).
# GUVENLIK KAPISI (OLCULDU 17 Kasim 2026, silat + DEVIR): ciplak `1[0-5]\d{2}`
# gercek metinde YANLIS POZITIF uretiyor:
#   `JK010344` -> 1034 · `DEVIR:10546` -> 1054 · `L1205` -> 1205
# 492 dosyalik taramada 4 dosya bozuldu (3'u silat, 1'i DEVIR; 15 -> 18 sahte eksik atif).
# ONCE yil ONUNDE `,` / bosluk / `/` olmali (govdede `(Yazar, 1111)` ve `(Yazar, 505/1111)`
# bicimleri kalir), SONRA 4 hane bitmeli (`10344` yakalanmaz).
HICRI = r"(?:(?<=[,\s/])1[0-5]\d{2}(?!\d))"
CIFT_YIL = r"\(\s*\d{1,3}\s*/\s*(\d{4})\s*\)"   # sag taraf 4 hane; aralik asagida denetlenir
# DIS GRUP YAKALAYICI olmali: tek basina `re.search(ATIF_YIL, ...)` cagrildiginda
# group(1) = eslesen YIL METNI olsun. Yakalayici olmayinca ic `YIL` grubu 1 oluyor
# ve HICRI dalinda group(1) None donuyordu (olculdu: traceback, satir 364).
ATIF_YIL = r"(" + HICRI + r"|" + YIL + r")"
GEVSEK = "--gevsek" in sys.argv

# --- ad katlama: aksan/diakritik ve Turkce ozel harfler tek bicime -----------------
# Kaynakca anahtari ile metin-ici anahtar AYNI katlamadan gecmeli; yoksa
# 'Âlûsî' kaynakcada 'Âlûsî', metinde 'Alusi' gecince eslesmez.
# sozluk bicimi kullanildi: iki esit uzunlukta dizge sayma hatasina acikti
# (olculdu: 'str.maketrans' ValueError — 18 harfe 19 karsilik yazilmisti).
_TR_ESLE = str.maketrans({
    "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
    "ç": "c", "Ç": "c", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u",
    "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u", "Û": "u",
})

def _katla(s):
    s = s.translate(_TR_ESLE)
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()

# "atif degil, olcu/gonderme" sozcukleri — bunlar soyad olamaz.
# DAR tutuldu: liste genisledikce GERCEK soyadlari yeme riski artar. Olculdu —
# ilk yazimda "yazar" da listedeydi ve fiksturdeki gercek soyad "Yazar"i yedi,
# CITE-01 "0 atif" verdi (CM-10 yanlis nedenle kirmizi yandi).
_AD_STOP = {
    "cilt", "vol", "volume", "s", "p", "pp", "sf", "sayfa", "bolum",
    "baski", "basim", "no",
    "bkz", "bakiniz", "see", "cf",
    "fig", "figure", "tablo", "table", "section", "eq", "denklem", "madde",
}
_AD_BAGLAC = re.compile(r"(?i)^(ayrıca\s+|ayrica\s+)?(bkz|bakiniz|see|cf|karşılaştır|karsilastir)\.?\s*")

def _soyad_adayi(parca, yil_bas):
    """Yildan onceki dilimden MAKUL tek soyad cikar; yoksa None.

    Yildan geriye dogru taranir: '... icin bkz. Al-Rawi, 2009' -> 'Al-Rawi'.
    '(cilt 8, 2009)' -> None (cilt olcu sozcugu, 8 sayi).
    """
    # TARIH/KUNYE parantezi ATIF DEGILDIR (10.11.2026). Iki bicim olculdu
    # (ege-makale): '(2026-09-18)' ISO tarih · '(TBMM 8 Haziran 1995)' TR tarih.
    # Once bunlar soyad sanilip CITE-01'e "kaynakcada yok" olarak dusuyordu.
    # DIKKAT: '(2020, s. 45)' BOYLE SAYILMAZ — o sayfa numarasidir, atif kalir.
    if re.search(r"\d{4}\s*[-/]\s*\d{1,2}", parca):
        return None
    if re.search(r"\d{1,2}\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+" + YIL, parca):
        return None
    on = parca[:yil_bas]
    on = re.sub(r"(?i)\bvd\.|\bet\s+al\.", " ", on)
    # ilk yazar: & / ve / and ayiricisindan once
    on = re.split(r"\s*&\s*|\s+ve\s+|\s+and\s+", on)[0]
    on = _AD_BAGLAC.sub("", on.lstrip(" \t,;:.-"))
    toklar = re.findall(r"[^\W\d_][\w'’'ʻ\-.]*", on, re.UNICODE)
    for t in reversed(toklar):
        h = t.strip(".-")
        if len(h) < 2:            continue   # 'o.' / 'd.' gibi kisaltmalar soyad degil
        if not h[0].isupper():    continue   # kucuk harf = duz yazi
        if _katla(h) in _AD_STOP: continue   # cilt/vol/s./p./baski...
        if re.search(r"(?i)\.(jpg|jpeg|png|pdf|md|html?)$", t): continue
        return t
    return None

# --dosya ile hedef sec
hedef = None
if "--dosya" in sys.argv:
    i = sys.argv.index("--dosya")
    if i + 1 < len(sys.argv):
        hedef = pathlib.Path(sys.argv[i + 1])
if hedef is None:
    hedef = next((pathlib.Path(c) for c in MASTER_CANDS if pathlib.Path(c).exists()), None)
if hedef is None or not hedef.exists():
    print("FAIL CITE-00: denetlenecek metin bulunamadi (MASTER yok, --dosya verilmedi)")
    sys.exit(1)

satirlar = hedef.read_text(errors="ignore").splitlines()

# --- kaynakca bolumunu ayir --------------------------------------------------
kaynakca_satirlari, govde_satirlari = [], []
icindeyiz = False
kaynakca_seviye = 0
for ln in satirlar:
    bas = re.match(r"^(#{1,6})\s", ln)
    if bas:
        seviye = len(bas.group(1))
        if KAYNAKCA_BASLIK.match(ln):
            icindeyiz, kaynakca_seviye = True, seviye
            continue
        if icindeyiz and seviye <= kaynakca_seviye:
            icindeyiz = False
    (kaynakca_satirlari if icindeyiz else govde_satirlari).append(ln)

if not kaynakca_satirlari:
    print("FAIL CITE-00: kaynakca bolumu bulunamadi (baslik 'Kaynakca' / 'References' olmali)")
    sys.exit(1)

def _ad_norm(s):
    s = _katla(s).replace(".", "")      # 'U.S.' ile 'US' ayni olsun (kaynakca noktayi siler)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())

# --- APA yil eki ('2026a'/'2026b') ayrimi (11.11.2026) -------------------------
# Olculdu: ayni soyad + ayni yil iki kaynak TEK anahtara cokuyordu. Sonuc:
#   - kaynakca girdisi sozlukte USTUNE YAZILIYOR (biri kayboluyor),
#   - CITE-02 "hic anilmayan" o girdiyi hic gormuyor -> YANLIS PASS.
# Olcum: /tmp/opencode/cmy2 -> beklenen CITE-02 FAIL, alinan PASS (rc=0).
# Cozum: yil anahtari APA ekini TASIR ('2026a'). 2-tuple bicimi korunur.
def _yil_ek(yil, kuyruk):
    """kuyruk: yildan SONRAKI metin. Ilk karakter kucuk latin harfi ise APA eki."""
    if kuyruk and kuyruk[0].isascii() and kuyruk[0].islower():
        return yil + kuyruk[0]
    return yil

# --- kaynakca girdilerini ayristir -------------------------------------------
def ilk_soyad(ham):
    ham = ham.strip().lstrip("-*• ").strip()
    on = re.split(r"\s*\(", ham, maxsplit=1)[0]
    on = re.split(r",", on, maxsplit=1)[0]
    on = re.sub(r"[^\wÇĞİÖŞÜçğıöşü' -]", "", on).strip()
    return on

kaynaklar = {}   # (soyad_kucuk, yil) -> ham satir
for ln in kaynakca_satirlari:
    # Yil parantezi icinde TARIH EKI olabilir: '(2020, 1 Ekim)' · '(1995, 8 Haziran)'.
    # Once yalniz '\(YIL\)' araniyordu; bu bicimdeki kaynakca girdisi HIC sayilmiyordu
    # (olculdu: ege-makale -> CITE-00 "girdi ayristirilamadi", oysa 6 girdi vardi).
    # Ek DAR tutuldu: '[,;]' + 60 karakter. Sayfa araligi degil, yayin tarihi ekidir.
    # 11.11.2026: APA yil eki ('2026a') ANAHTARA girer — yoksa iki girdi cakisir.
    YIL_P = r"(?:\(" + YIL + r"([a-z]?)(?:[,;]\s*[^)]{0,60})?\)|" + CIFT_YIL + r")"
    # 11.11.2026: '(t.y.)' = tarih yok. Once bu girdiler HIC sayilmiyordu
    # (olculdu: ege 12 girdi -> 7 sayilan; 4'u t.y. idi ve hepsi BIRINCIL).
    if not ln.strip():
        continue
    if not re.search(YIL_P, ln):
        if not re.search(r"\(\s*t\.\s*y\.\s*\)", ln):
            continue
        _ty_soyad = ilk_soyad(ln)
        if not _ty_soyad:
            continue
        kaynaklar[(_ad_norm(_ty_soyad), "t.y.")] = ln.strip()
        continue
    m = re.search(YIL_P, ln)
    soyad = ilk_soyad(ln)
    if not soyad:
        continue
    _y = m.group(1) or m.group(3)      # cift yilda miladi taraf (v1.7.403)
    if m.group(3) is not None:          # cift yil: sag taraf MAKUL miladi olmali
        if not (1000 <= int(m.group(3)) <= 2099):
            continue                    # fail-closed: aralik disi girdi sayilmaz
    kaynaklar[(_katla(soyad), _y + (m.group(2) or ""))] = ln.strip()

if not kaynaklar:
    if re.search(r"\(\s*1[0-5]\d{2}\s*\)", "\n".join(kaynakca_satirlari)):
        print("NOT: tek hicri yil '(1420)' kaynakcada DESTEKLENMEZ (sayfa numarasi ile")
        print("     karisabilir). Cift yil yazin: '(1420/1999)'.")
    print("FAIL CITE-00: kaynakcada 'Soyad, A. (Yil).' bicimli girdi ayristirilamadi")
    sys.exit(1)

# --- metin-ici atiflari topla ------------------------------------------------
govde = "\n".join(govde_satirlari)
atiflar = {}   # (soyad_kucuk, yil) -> ham atif

# parantezli: (Yazar, 2020) / (A, 2020; B, 2021) / (Smith & Doe, 2021, s. 5)
for blok in re.findall(r"\(([^()]{0,200}?" + ATIF_YIL + r"[^()]{0,40}?)\)", govde):
    ham = blok[0] if isinstance(blok, tuple) else blok
    for parca in ham.split(";"):
        m = re.search(ATIF_YIL, parca)
        if not m:
            continue
        ad = _soyad_adayi(parca, m.start())
        if ad is None:
            continue                       # makul soyad yok -> parantez atif degil
        atiflar[(_katla(ad), _yil_ek(m.group(1), parca[m.end():]))] = parca.strip()

# anlatimsal: Yazar (2020) · Ṭabarī (1987) · Scholem (1941, s. 45) · Smith vd. (2020)
# [^\W\d_] = unicode HARF (Python 3 str desenlerinde unicode varsayilan).
# Yil sonrasi opsiyonel sayfa/bolum eki: (1941, s. 45) · (1988, pp. 12-14)
ANLATIMSAL = re.compile(
    r"([^\W\d_][\w'’ʼʻ-]*)"                    # soyad (transliterasyon dahil)
    r"(?:\s+(?:ve|&|and|vd\.|et\s+al\.)\s*[\w'’-]*)?"  # ikinci yazar / vd. / et al.
    r"\s*\(" + ATIF_YIL + r"(?:\s*[,;][^)]{0,40})?\)"              # (yil) veya (yil, s. 45)
)
for m in ANLATIMSAL.finditer(govde):
    ad = m.group(1)
    anahtar = (_katla(ad), _yil_ek(m.group(2), govde[m.end(2):]))
    if anahtar not in kaynaklar and not any(ch.isupper() for ch in ad):
        continue                      # kaynakcasiz kucuk harfli duz yazi adaylarini alma
    if _katla(ad) in ("bkz", "bakiniz", "sekil", "tablo", "sayfa", "bolum", "madde",
                      "figure", "table", "section", "see", "eq", "denklem"):
        continue                      # atif degil, gonderme
    atiflar[anahtar] = m.group(0)

# --- '(Ad, t.y.)' ve 'Ad (t.y.)' atiflari (11.11.2026) -------------------------
# t.y. girdileri kaynakcaya alindi; atiflari da taninmali. Yil olmadigi icin
# _soyad_adayi/_yil_ek yolu calismaz; yildan ONCEKI TAM AD kullanilir.
_TY = r"t\.\s*y\."
for _m in re.finditer(r"\(([^()]{0,200}?" + _TY + r")\)", govde):
    for _p in _m.group(1).split(";"):
        if not re.search(_TY, _p):
            continue
        _ad = re.split(_TY, _p, maxsplit=1)[0].rstrip(" ,;:.")
        _ad = _AD_BAGLAC.sub("", _ad.lstrip(" \t,;:.-"))
        if _ad.strip():
            atiflar.setdefault((_ad_norm(_ad.strip()), "t.y."), _p.strip())
for _m in re.finditer(r"([^\W\d_][\w'’ʼʻ.-]*(?:\s+[^\W\d_][\w'’ʼʻ.-]*){0,6})\s*\("
                      + _TY + r"\)", govde):
    _ad = _m.group(1).strip()
    if _ad:
        atiflar.setdefault((_ad_norm(_ad), "t.y."), _m.group(0))

# --- cok kelimeli ad / KURUM adi eslestirme (10.11.2026) ----------------------
# Olculdu (ege-makale): kaynakca girdisi 'Turkiye Buyuk Millet Meclisi. (1995, ...)'
#   -> anahtar 'turkiye buyuk millet meclisi'
#   metin-ici atif '(Turkiye Buyuk Millet Meclisi, 1995)'
#   -> _soyad_adayi yildan GERIYE yurudugu icin son kelimeyi aldi: 'meclisi'
# Ayni eser iki farkli anahtar tasidi; CITE-01 "kaynakcada yok" dedi.
# Cozum: YALNIZ eslesmeyen atiflar icin yildan onceki TAM ad normalestirilip kaynak
# adiyla AYNEN karsilastirilir. Alt-dize/kismi eslesme KABUL EDILMEZ: kisa adlar
# ('State', 'Republic') metnin her yerinde gecer ve yanlis pozitif uretir.
_kaynak_ad_norm = {}
for _k in kaynaklar:
    _kaynak_ad_norm.setdefault((_ad_norm(_k[0]), _k[1]), _k)

for _k in list(atiflar):
    if _k in kaynaklar:
        continue
    _ham = atiflar[_k]
    _ad_ham = re.split(ATIF_YIL, _ham, maxsplit=1)[0]
    _hedef = _kaynak_ad_norm.get((_ad_norm(_ad_ham), _k[1]))
    if _hedef is None:          # tam ad tutmadi -> atif eslesmemis kalir
        continue
    if _hedef in atiflar:       # ayni kaynaga baska atif zaten bagli
        continue
    del atiflar[_k]
    atiflar[_hedef] = _ham

# --- CITE-01 eksik kaynak -----------------------------------------------------
hatalar = []
eksik = sorted(k for k in atiflar if k not in kaynaklar)
if eksik:
    hatalar.append("CITE-01")
    print(f"FAIL CITE-01: {len(eksik)} atif kaynakcada yok:")
    for k in eksik:
        print(f"    - '{atiflar[k]}'  ->  aranan: {k[0].title()} ({k[1]})")
else:
    print(f"PASS CITE-01: {len(atiflar)} metin-ici atifin tamami kaynakcada var")

# --- CITE-02 oksuz kaynak -----------------------------------------------------
# Kaynakca girdisi "atif kalibi taninmadi" diye oksuz ilan edilmemeli: kural
# "metinde en az bir kez anilir". Soyad govdede geciyorsa anilmis sayilir (INFO),
# hic gecmiyorsa oksuzdur (FAIL). Olculdu (silat-makale): Al-Rawi 6 · El-Zein 5 ·
# Yaltirik 4 · Alusi 11 kez govdede idi ama atif kalibi taninmadigi icin 4'u de
# "oksuz" gorunuyordu.
GOVDE_KATLA = _katla(govde)

def metinde_aniliyor(soyad_katla):
    if len(soyad_katla) < 3:
        return False        # cok kisa soyadda alt-dize eslesmesi yanlis pozitif uretir
    return soyad_katla in GOVDE_KATLA

oksuz, kalipsiz = [], []
for k in sorted(kaynaklar):
    if k in atiflar:
        continue
    # 11.11.2026: APA yil-eki ('2026b') OLAN anahtarda soyad tek basina yeterli
    # degil — ayni soyadin diger eseri govdede geciyor olabilir. O durumda yil-eki
    # govdede hic gecmiyorsa eser gercekten anilmamistir (FAIL).
    _ek_var = len(k[1]) > 4 and k[1][4].isalpha()
    if _ek_var and k[1] not in govde:
        oksuz.append(k)
    else:
        (kalipsiz if metinde_aniliyor(k[0]) else oksuz).append(k)

if kalipsiz:
    print(f"INFO CITE-02: {len(kalipsiz)} kaynakca girdisi metinde aniliyor ama atif kalibi taninmadi:")
    for k in kalipsiz:
        print(f"    - {kaynaklar[k]}")

if oksuz:
    etiket = "UYARI" if GEVSEK else "FAIL"
    if not GEVSEK:
        hatalar.append("CITE-02")
    print(f"{etiket} CITE-02: {len(oksuz)} kaynakca girdisi metinde hic anilmiyor:")
    for k in oksuz:
        print(f"    - {kaynaklar[k]}")
else:
    print(f"PASS CITE-02: {len(kaynaklar)} kaynakca girdisinin tamami metinde anili")

# --- CITE-03 yil celiskisi (uyari) -------------------------------------------
soyad_yil = {}
for (s, y) in list(kaynaklar) + list(atiflar):
    soyad_yil.setdefault(s, set()).add(y[:4])   # APA eki yil degildir
celisen = {s: sorted(y) for s, y in soyad_yil.items() if len(y) > 1}
if celisen:
    print(f"UYARI CITE-03: ayni soyad birden fazla yilla geciyor: {celisen}")
    print("    (ayni yazarin farkli eserleri ise normaldir; a/b son eki gerekebilir)")
else:
    print("PASS CITE-03: yil celiskisi yok")

if hatalar:
    print(f"CITE-MATCH FAIL — {', '.join(hatalar)} · atif={len(atiflar)} kaynak={len(kaynaklar)}")
    sys.exit(1)

print(f"CITE-MATCH PASS — atif {len(atiflar)} <-> kaynak {len(kaynaklar)} %100 eslesiyor")
sys.exit(0)
