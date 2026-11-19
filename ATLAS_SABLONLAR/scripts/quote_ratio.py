#!/usr/bin/env python3
"""Atlas v5.5.4 Quote Ratio — B-4 alinti orani ve uzun alinti uclusu denetimi

NEDEN VAR:
  Birincil metin agirlikli makalede dogrudan alinti orani yuksektir; olculmezse
  hakem "asiri alinti" der, olculup gerekcelendirilirse itiraz kalkar. Ayrica
  40+ kelimelik her dogrudan alintida tirnak + sayfa no + kaynakca eslesmesi
  uclusu zorunludur (eksikse atifsiz blok suphesi → P0).

KONTROLLER:
  QR-01  Alinti orani = alinti_karakteri / govde_karakteri  (bilgi/harici karsilastirma yok)
  QR-02  40+ kelimelik her alintida bitisik atif + ayni atifta sayfa no  (eksikse P0)

  Alinti tanimi:
    - cift tirnakli: " ... "  " ... "  « ... »  „ ... "
    - blok alinti: satir basi  "> " ile baslayan markdown blockquote
  Govde = kaynakca basligindan ONCEKI kisim (cite_match ile ayni ayrim).

  Esik: SCOPE-CONTRACT'ta "alinti.*%" / "quote.*%" deseni aranir; bulunursa
  orana karsi karsilastirilir ve asim acikca yazilir. Esik yoksa yalniz
  oran raporlanir (CALISTIRILMADI degil, bilgi).

Kullanim:
  python3 scripts/quote_ratio.py
  python3 scripts/quote_ratio.py --dosya makale.md
  python3 scripts/quote_ratio.py --esik 25   (SCOPE aramasi yerine dogrudan esik ver)
"""
import re, sys, pathlib

MASTER_CANDS = [
    "03-FAZ-3-MASTER-v5.5.md",
    "03-FAZ-3-MASTER-v5.4.md",
    "03-FAZ-3-MASTER-v5.2.md",
    "MASTER.md",
]
KAYNAKCA_BASLIK = re.compile(r"^#{1,6}\s.*(kaynak[cç]a|references|bibliyografya)", re.I)
YIL = r"(1[6-9]\d{2}|20\d{2})"
# QR-02: alinti ardinda yalniz bosluk/noktalama atlanir; arada anlatim olamaz.
# Sayfa ayni atifta olmalidir: (Yazar, 2020, s. 5) / Yazar (2020, p. 5).
# Alinti icindeki veya sonraki ilgisiz cumledeki sayfa isareti kanit degildir.
ATIF_YAKIN = re.compile(r"(\([^)]*" + YIL + r"[^)]{0,30}\)|[^\W\d_][\w'’ʼ-]*\s*\(" + YIL + r"[^)]*\))")

# --dosya ve --esik bayraklari
hedef = None
esik_cli = None
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--dosya" and i + 1 < len(args):
        hedef = pathlib.Path(args[i + 1]); i += 2; continue
    if args[i] == "--esik" and i + 1 < len(args):
        try: esik_cli = float(args[i + 1].replace("%", "").replace(",", "."))
        except: pass
        i += 2; continue
    i += 1

if hedef is None:
    hedef = next((pathlib.Path(c) for c in MASTER_CANDS if pathlib.Path(c).exists()), None)
if hedef is None or not hedef.exists():
    print("FAIL QR-00: denetlenecek metin bulunamadi (MASTER yok, --dosya verilmedi)")
    sys.exit(1)

lines = hedef.read_text(errors="ignore").splitlines()

# --- kaynakca bolumunu ayir ---
kaynakca_satirlari, govde_satirlari = [], []
icindeyiz = False
kaynakca_seviye = 0
for ln in lines:
    bas = re.match(r"^(#{1,6})\s", ln)
    if bas:
        seviye = len(bas.group(1))
        if KAYNAKCA_BASLIK.match(ln):
            icindeyiz, kaynakca_seviye = True, seviye
            continue
        if icindeyiz and seviye <= kaynakca_seviye:
            icindeyiz = False
    (kaynakca_satirlari if icindeyiz else govde_satirlari).append(ln)

def _tablo_temizle(satir):
    """Markdown tablo satirindaki tirnak isaretlerini etkisizlestir.

    v1.7.288 (QR-11): tablo hucresi ALINTI DEGILDIR. ATLAS once bunlari alintiyordu.
    Olculdu (10.11.2026, ayni metin iki betikle):
        ege MASTER  ATLAS %3.5 · 32 span   vs  yamali %1.1 · 12 span
        silat MASTER ATLAS %3.2 · 36 span  vs  yamali %3.0 · 31 span
    Yama `ege-makale/scripts/quote_ratio.py`'de 2026-09-18'den beri vardi
    (DEVIR.md:35) ama ATLAS'a tasinmamisti; proje kopyasi duzeltmeyi biliyordu,
    sablon bilmiyordu. Degisim 1 karakter -> 1 karakter (`ʺ`), bu yuzden
    govde karakter sayisi ve span KONUMLARI DEGISMEZ (QR-02 hala dogru eslesir).
    """
    if satir.lstrip().startswith("|"):
        for ch in ('"', "“", "”", "‘", "’", "«", "»"):
            satir = satir.replace(ch, "ʺ")
    return satir


govde_satirlari = [_tablo_temizle(_s) for _s in govde_satirlari]
govde = "\n".join(govde_satirlari)
kaynakca = "\n".join(kaynakca_satirlari)

if not govde.strip():
    print("FAIL QR-00: govde bos (kaynakca basligi butun metni yutuyor olabilir)")
    sys.exit(1)

# --- govde karakter sayisi ---
govde_karakter = len(govde)
if govde_karakter == 0:
    print("FAIL QR-00: govde karakter sayisi 0")
    sys.exit(1)

# --- alinti span'larini topla ---
alinti_spanlar = []  # (metin, bas, son)
# QR-01 icin kaynak metindeki icerik araliklari; QR-02 span'lari korunur.
alinti_icerik_araliklari = []

# 1) cift tirnakli alintilar (duz + curly + guillemet)
#    deduplication: ayni span uc farkli desende eslesirse bir kez sayilir
_goruldu = set()

# 1a) DUZ TIRNAK: once KONUMA GORE SIRALI eslestir (1<->2, 3<->4), SONRA uzunluk filtrele.
# v1.7.276 (QR-10) — YANLIS POZITIF DUZELTMESI (olculdu: silat-makale, 10 Kasim 2026)
#   ONCE: re.finditer(r'"([^"]{10,}?)"') — 10 karakterden KISA vurgu cifti
#   ("benzerlik", "31", "c. 11") atlaninca eslestirme KAYIYOR: bir terimin
#   KAPANIS tirnagi, sonraki ifadenin ACILIS tirnagi olarak okunuyor.
#   Olculdu: 51 duz-tirnak spani, 14'u 40+ kelime ve HEPSI duzyazi / tablo satiri /
#   sozluk maddesi — hicbiri alinti degil; 10 sahte FAIL uretildi.
#   Turkce metinde duz tirnak VURGU icindir; ayrica tipografik tirnak ("" '') ve
#   blok alinti (>) da desteklenir.
#   Dengesizlik (tek sayida tirnak) SESSIZ gecmez: UYARI basilir, cunku eslestirme
#   yanlis olabilir ve bu durumda "temiz" demek yanlis olur.
_duz_konumlar = [m.start() for m in re.finditer(r'"', govde)]
if len(_duz_konumlar) % 2:
    _tekil = _duz_konumlar[-1]
    _ctx = govde[max(0, _tekil - 40):_tekil + 40].replace("\n", " ")
    print(f"UYARI QR-02-denge: duz tirnak sayisi TEK ({len(_duz_konumlar)}) — son tirnak "
          f"eslenmedi; ciftler kaymissa alinti sinirlari guvenilmez. Kuyruk: ...{_ctx}...")
for _a, _b in zip(_duz_konumlar[0::2], _duz_konumlar[1::2]):
    _icerik = govde[_a + 1:_b]
    if len(_icerik) < 10:
        continue                       # kisa vurgu tirnagi: atif degil, oran disi
    _key = (_a, _b + 1)
    if _key not in _goruldu:
        _goruldu.add(_key); alinti_spanlar.append((_icerik, _a, _b + 1))
        alinti_icerik_araliklari.append((_a + 1, _b))

for m in re.finditer(r'\u201c([^\u201d]{10,}?)\u201d', govde):
    key = (m.start(), m.end())
    if key not in _goruldu:
        _goruldu.add(key); alinti_spanlar.append((m.group(1), m.start(), m.end()))
        alinti_icerik_araliklari.append((m.start(1), m.end(1)))
for m in re.finditer(r'\u2018([^\u2019]{10,}?)\u2019', govde):
    key = (m.start(), m.end())
    if key not in _goruldu:
        _goruldu.add(key); alinti_spanlar.append((m.group(1), m.start(), m.end()))
        alinti_icerik_araliklari.append((m.start(1), m.end(1)))
for m in re.finditer(r'«([^»]{10,}?)»', govde):
    key = (m.start(), m.end())
    if key not in _goruldu:
        _goruldu.add(key); alinti_spanlar.append((m.group(1), m.start(), m.end()))
        alinti_icerik_araliklari.append((m.start(1), m.end(1)))

# 2) blok alintilar: satir basi "> " ile baslayan ard arda satirlar
blok_aktif = False
blok_bas = 0
blok_metin_parcalari = []
blok_araliklari = []
satir_bas = 0
for idx, ln in enumerate(govde_satirlari):
    if ln.lstrip().startswith(">"):
        if not blok_aktif:
            blok_aktif = True
            # govde icindeki karakter konumu (yaklasik: satirlarin join uzunlugu)
            blok_bas = len("\n".join(govde_satirlari[:idx])) + (1 if idx > 0 else 0)
            blok_metin_parcalari = []
            blok_araliklari = []
        # "> " sonrasi
        ic = re.sub(r"^\s*>\s?", "", ln)
        if blok_metin_parcalari:
            # birlesik metindeki satir sonu sayilir, "> " oneki sayilmaz.
            blok_araliklari.append((satir_bas - 1, satir_bas))
        blok_araliklari.append((satir_bas + len(ln) - len(ic), satir_bas + len(ln)))
        blok_metin_parcalari.append(ic)
    else:
        if blok_aktif:
            birlesik = "\n".join(blok_metin_parcalari)
            if len(birlesik.strip()) >= 20:
                # Kaynak metindeki kesin bitis: > isaretleri de konuma dahildir.
                blok_son = len("\n".join(govde_satirlari[:idx]))
                alinti_spanlar.append((birlesik, blok_bas, blok_son))
                alinti_icerik_araliklari.extend(blok_araliklari)
            blok_aktif = False
            blok_metin_parcalari = []
    satir_bas += len(ln) + 1
if blok_aktif and blok_metin_parcalari:
    birlesik = "\n".join(blok_metin_parcalari)
    if len(birlesik.strip()) >= 20:
        alinti_spanlar.append((birlesik, blok_bas, len(govde)))
        alinti_icerik_araliklari.extend(blok_araliklari)

# TT-C-8: ayni kaynak karakteri bir kez say; ayri alintilarin arasini doldurma.
# Oran kirpilmaz: govde icindeki araliklarin birlesimi yapisal olarak <= govdedir.
birlesik_araliklar = []
for bas, son in sorted(alinti_icerik_araliklari):
    if birlesik_araliklar and bas <= birlesik_araliklar[-1][1]:
        birlesik_araliklar[-1][1] = max(birlesik_araliklar[-1][1], son)
    else:
        birlesik_araliklar.append([bas, son])
alinti_karakter = sum(son - bas for bas, son in birlesik_araliklar)
oran = (alinti_karakter / govde_karakter * 100) if govde_karakter else 0.0

print(f"INFO QR-01: govde {govde_karakter} kar — alinti {alinti_karakter} kar — oran %{oran:.1f}  ({len(alinti_spanlar)} alinti spani)")
# kaynakca yoksa QR-01 anlamsiz degil; sadece govde olculur (kaynakca zaten ayrilmis)

# --- esik (SCOPE'ta ilan) ---
esik = esik_cli
esik_kaynagi = None
if esik is None:
    scope = pathlib.Path("00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md")
    if scope.exists():
        st = scope.read_text(errors="ignore")
        # "%15" ve "15%" yonleri; bosluk ve nokta/virgul ondaliklari desteklenir.
        for line in st.splitlines():
            ml = re.search(r"%\s*(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)\s*%", line)
            if ml and any(k in line.lower() for k in ["alinti", "alıntı", "quote", "orani", "oranı", "esik", "eşik", "threshold"]):
                try:
                    val = float((ml.group(1) or ml.group(2)).replace(",", "."))
                    if 0 < val <= 100:
                        esik = val; esik_kaynagi = f"SCOPE: {line.strip()[:80]}"; break
                except: pass

if esik is not None:
    durum = "ASIM" if oran > esik else "UYGUN"
    print(f"INFO QR-01-esik: ilan edilen esik %{esik:.0f} ({esik_kaynagi or '--esik bayragi'}) — oran %{oran:.1f} → {durum}")
    if oran > esik:
        print(f"UYARI QR-01: oran %{oran:.1f} esigi %{esik:.0f} asiyor — gerekcelendirme beklenir (birincil metin agirlikli ise not dusulebilir)")
else:
    print("INFO QR-01-esik: SCOPE'ta alinti esigi ilan edilmemis — oran yalniz bilgi olarak raporlandi")

# --- QR-02: 40+ kelimelik alintida uclu ---
fail_qr02 = []
for metin, bas, son in alinti_spanlar:
    kelime = len(metin.split())
    if kelime < 40:
        continue
    # TT-C-3: 400 karakterlik pencereden bagimsiz atif/sayfa devsirme.
    # Alintiya bitisik tek atfi esle; sayfayi yalniz bu atfin icinde ara.
    pencere = re.sub(r"^\s*[.,;:!?]?\s*", "", govde[son:son + 400])
    atif = ATIF_YAKIN.match(pencere)
    has_atif = atif is not None
    has_sayfa = bool(atif and re.search(r"\b(s\.|p\.|pp\.|§|sayfa)\s*\d", atif.group(0), re.I))
    has_tirnak = True  # span zaten tirnakli/blok oldugu icin
    # kaynakca eslesmesi ayri bir asama (cite_match bunu denetler); burada yalniz
    # atif + sayfa varligini kontrol ediyoruz; eksikse P0
    if not (has_atif and has_sayfa):
        # kanit icin kisalt
        ozet = metin.strip().replace("\n", " ")[:90].replace("  ", " ")
        fail_qr02.append((kelime, ozet, has_atif, has_sayfa, bas))
        print(f'FAIL QR-02: {kelime} kelimelik alintida uclu eksik (atif={has_atif}, sayfa={has_sayfa}) — "{ozet}..." [pos {bas}]')
    # else sessiz gec

if fail_qr02:
    print(f"QUOTE-RATIO FAIL — QR-02: {len(fail_qr02)} uzun alintida uclu eksik (tirnak+sayfa+atif)")
    sys.exit(1)

if alinti_spanlar:
    print(f"PASS QR-02: {len([1 for t,_,_ in alinti_spanlar if len(t.split())>=40])} uzun (40+) alintinin tamami ucluyu tasiyor (0 eksik)")
else:
    print("INFO QR-02: tirnakli/blok alinti span'i bulunamadi — oran 0 (CALISTIRILMADI degil, bilgi)")

print(f"QUOTE-RATIO PASS — oran %{oran:.1f} · {len(alinti_spanlar)} span · uzun-alinti QR-02 temiz")
sys.exit(0)
