#!/usr/bin/env python3
"""Atlas v5.5.4 Declaration Check — B-5 dergi beyan paketi denetimi

KONTROL EDILENLER (TASARIM-AKADEMIK-BOSLUKLAR.md B-5):
  DEC-01  Etik Kurul / Ethics Committee  — numara veya "gerekmedi" gerekcesi
  DEC-02  Cikar Catismasi / Conflict of Interest
  DEC-03  Finansman / Funding
  DEC-04  Yazar Katkisi / CRediT / Author Contributions
  DEC-05  Veri/Materyal Erisilebilirligi / Data Availability
  DEC-06  YZ Kullanimi Beyani / AI Use Disclosure  (emanet geregi)
  DEC-07  DPIA — kosullu: kisisel veri isleniyorsa ZORUNLU, yoksa gerekceli N/A

Her baslik MASTER'da bir markdown basligi (# / ## / ###) olarak aranir.
Baslik var ama ardindaki icerik bos ise (sonraki basliga kadar metin yok) FAIL'dir.
Eksik baslik veya bos icerik P0 sayilir (dergi masasindan donus riski).

DPIA kurali B-1 ile uyumlu: teoloji metni icin kisisel veri yoksa bos DPIA
yazdirmak uydurmaya zorlamaktir. Bu script kisisel veri isareti arar; isaret
yoksa ve DPIA yoksa CALISTIRILMADI sayar (yesil isik degil).

Kullanim:
  python3 scripts/declaration_check.py
  python3 scripts/declaration_check.py --dosya makale.md
"""
import re, sys, pathlib

MASTER_CANDS = [
    "03-FAZ-3-MASTER-v5.5.md",
    "03-FAZ-3-MASTER-v5.4.md",
    "03-FAZ-3-MASTER-v5.2.md",
    "MASTER.md",
]

# --dosya ile hedef sec
hedef = None
if "--dosya" in sys.argv:
    i = sys.argv.index("--dosya")
    if i + 1 < len(sys.argv):
        hedef = pathlib.Path(sys.argv[i + 1])
if hedef is None:
    hedef = next((pathlib.Path(c) for c in MASTER_CANDS if pathlib.Path(c).exists()), None)
if hedef is None or not hedef.exists():
    print("FAIL DEC-00: denetlenecek metin bulunamadi (MASTER yok, --dosya verilmedi)")
    sys.exit(1)

text = hedef.read_text(errors="ignore")
lines = text.splitlines()

# basliklari topla: seviye, metin, baslangic satir indeksi
headings = []
fence_char = None
fence_len = 0
for idx, ln in enumerate(lines):
    fence_match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", ln)
    if fence_match:
        marker = fence_match.group(1)
        suffix = fence_match.group(2)
        if fence_char is None:
            fence_char = marker[0]
            fence_len = len(marker)
        elif (
            marker[0] == fence_char
            and len(marker) >= fence_len
            and not suffix.strip()
        ):
            fence_char = None
            fence_len = 0
        continue
    if fence_char is not None:
        continue
    m = re.match(r"^(#{1,6})\s+(.+)$", ln)
    if m:
        headings.append((len(m.group(1)), m.group(2).strip(), idx))

# --- v1.7.278 (DEC-12): TURKCE HARF KATLAMA --------------------------------------
# ONCE: karsilastirma `title.strip().lower()` ile yapiliyordu; desenler ASCII
#   ("cikar catismasi", "yazar katkisi", "veri erisilebilirligi", "yapay zeka").
#   Turkce yazimda baslik "Çıkar Çatışması" -> lower() -> "çıkar çatışması"
#   != "cikar catismasi" -> beyan VAR ama arac GORMUYOR.
#   Olculdu (10 Kasim 2026, /tmp fiksturu): 6 Turkce basligin 4'u taninmadi —
#   DEC-02 · DEC-04 · DEC-05 · DEC-06. Yani arac makaleyi ASCII Turkce yazmaya
#   ZORLUYORDU; "Kaynakca" gibi harfsiz baslik yazmak zorunda kaliyordu.
#   Ayrica `'İ'.lower()` = 'i' + U+0307 (bilesik nokta) — Python Turkce
#   yerel ayarini bilmez; bu yuzden katlama lower()'DAN ONCE yapilir.
# SIMDI: iki taraf da ASCII'ye katlanir (ç→c · ğ→g · ı→i · İ→i · ö→o · ş→s ·
#   ü→u · â→a · î→i · û→u). Katlama EKLEME degil EŞİTLEME icin kullanilir;
#   "Destek" gibi gevsek desenler yine eslesmez (DEC-10'daki KATI eslesme korunur).
_TR_KATLA = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "İ": "i", "ö": "o",
    "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u", "â": "a", "Â": "a",
    "î": "i", "Î": "i", "û": "u", "Û": "u",
})

def _katla(s):
    """Turkce harfleri ASCII'ye katla, sonra kucult (lower'dan ONCE)."""
    return s.strip().translate(_TR_KATLA).lower()

def find_heading(patterns):
    for _, title, idx in headings:
        normalized_title = _katla(title)
        for pat in patterns:
            if _katla(pat) == normalized_title:
                return title, idx
    return None, None

# --- v1.7.277 (DEC-10): RUN-IN (satir ici kalin) BEYAN ETIKETI -------------------
# ONCE: beyan yalniz markdown BASLIGI olarak aranıyordu (`## Etik Kurul`).
#   Oysa akademik yazimda beyan sikca satir ici kalin etiketle verilir:
#     **DPIA (Veri Koruma Etki Degerlendirmesi):** N/A (gerekceli) — ...
#   Olculdu (silat-makale): belgede DPIA beyani VAR (satir 361) ama
#   declaration_check "baslik yok" dedi -> yanlis pozitif.
# SIMDI: `**Etiket:**` bicimi de beyan etiketi sayilir. Eslesme KATI:
#   desen, etiketin TAMAMI ya da parantez ONCESI cekirdegi ile BIREBIR esismeli
#   (startswith DEGIL — "destek" gibi gevsek desenler yanlis pozitif uretirdi).
#   Boylece "**Not:**" / "**Onerme (C01):**" gibi etiketler beyan sanilmaz.
RUN_IN = re.compile(r"^\s{0,3}\*\*([^*\n]{2,80}?)[:：]\*\*\s*(.*)$")
runin = []          # (etiket, satir indeksi, ayni satirdaki icerik)
fence_char = None
fence_len = 0
for idx, ln in enumerate(lines):
    fence_match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", ln)
    if fence_match:
        marker = fence_match.group(1)
        suffix = fence_match.group(2)
        if fence_char is None:
            fence_char = marker[0]
            fence_len = len(marker)
        elif marker[0] == fence_char and len(marker) >= fence_len and not suffix.strip():
            fence_char = None
            fence_len = 0
        continue
    if fence_char is not None:
        continue
    rid = RUN_IN.match(ln)
    if rid:
        runin.append((rid.group(1).strip(), idx, rid.group(2).strip()))

def find_runin(patterns):
    for label, idx, rest in runin:
        core = re.split(r"\s*\(", label)[0].strip()
        adaylar = {_katla(label), _katla(core)}
        for pat in patterns:
            if _katla(pat) in adaylar:
                return label, idx
    return None, None

def runin_has_content(idx, rest):
    if rest.strip():
        return True
    sonraki = [i for _, _, i in headings if i > idx] + [i for _, i, _ in runin if i > idx]
    son = min(sonraki) if sonraki else len(lines)
    chunk = "\n".join(lines[idx + 1:son]).strip()
    meaningful = [l for l in chunk.splitlines()
                  if l.strip() and l.strip() not in ("---", "***", "___")]
    return len(meaningful) > 0

def section_has_content(heading_idx):
    # heading_idx -> headings listesindeki sira, degil satir numarasi
    h_pos = None
    for i, (_, _, sidx) in enumerate(headings):
        if sidx == heading_idx:
            h_pos = i
            break
    if h_pos is None:
        return False
    start_line = headings[h_pos][2] + 1
    end_line = headings[h_pos + 1][2] if h_pos + 1 < len(headings) else len(lines)
    chunk = "\n".join(lines[start_line:end_line]).strip()
    # en az bir anlamli satir var mi? (bosluk / cizgi degil)
    meaningful = [l for l in chunk.splitlines() if l.strip() and l.strip() not in ("---", "***", "___")]
    return len(meaningful) > 0

# alti beyan + YZ
beyanlar = [
    ("DEC-01 Etik Kurul", ["etik kurul", "ethics committee", "etik onay", "etik kurul onayi", "ethics approval"]),
    ("DEC-02 Cikar Catismasi", ["cikar catismasi", "conflict of interest", "competing interest", "cikar catismasi beyani"]),
    ("DEC-03 Finansman", ["finansman", "funding", "destek", "tesekkur", "acknowledg", "grant"]),
    ("DEC-04 Yazar Katkisi", ["yazar katkisi", "author contribution", "credit", "yazarlik katkisi", "contribution"]),
    ("DEC-05 Veri Erisilebilirligi", ["veri erisilebilirligi", "data availability", "veri paylasimi", "materyal erisilebilirligi", "data access", "open data"]),
    ("DEC-06 YZ Kullanimi", ["yapay zeka", "yapay zekâ", "yz kullanimi", "ai use", "ai disclosure", "yapay zeka destegi", "ai assistance",
                             # DEC-12: Turkce tam baslik varyanti — "Yapay Zekâ Kullanımı"
                             # katlamadan sonra "yapay zeka kullanim" olur; desen TAM eslesmeli
                             # oldugu icin ek olarak yazilir. ("-i" eki desende YOK: basliga gore.)
                             "yapay zeka kullanimi"]),
]

has_fail = False

for label, patterns in beyanlar:
    title, sidx = find_heading(patterns)
    if title is not None:
        if not section_has_content(sidx):
            print(f'FAIL {label}: baslik var ("{title}") ama icerik bos — en az bir cumle gerekli')
            has_fail = True
        else:
            print(f'PASS {label}: "{title}" basligi ve icerigi var')
        continue
    # DEC-10: baslik yoksa RUN-IN kalin etiket ara
    r_title, r_idx = find_runin(patterns)
    if r_title is not None:
        r_rest = next(rest for lbl, i, rest in runin if i == r_idx and lbl == r_title)
        if not runin_has_content(r_idx, r_rest):
            print(f'FAIL {label}: satir ici etiket var ("{r_title}") ama icerik bos')
            has_fail = True
        else:
            print(f'PASS {label}: satir ici beyan etiketi "{r_title}:" ve icerigi var')
        continue
    print(f"FAIL {label}: baslik bulunamadi — aranan: {patterns[0]}")
    has_fail = True

# --- DPIA (kosullu) ---
dpia_title, dpia_idx = find_heading(["dpia", "veri koruma etki", "data protection impact"])
dpia_runin = None
if dpia_title is None:
    dpia_runin = find_runin(["dpia", "veri koruma etki", "data protection impact"])

# v1.7.277 (DEC-11): N/A BEYANI KENDI TETIKLEYICISINI ICERIR.
#   ONCE: govdede "kisisel veri" aranir, BULUNURSA DPIA zorunlu sayilirdi.
#   Belge "kisisel veri ISLENMEMEKTEDIR" diyorsa bu cumle kendi aramasini
#   doyuruyordu -> "kisisel veri var ama DPIA yok" -> yanlis pozitif.
#   Olculdu (silat-makale satir 361): DPIA satiri TAM O CUMLEYI baslatiyordu.
#   SIMDI: her gecis icin ±120 karakter penceresine bakilir; olumsuzluk isareti
#   (N/A · yok · bulunmamaktad · -mA · gerekmez · no personal data) varsa o gecis
#   SAYILMAZ. En az bir OLUMSUZ OLMAYAN gecis varsa kisisel veri gercekten var.
kisisel_isaretler = ["kisisel veri", "kişisel veri", "personal data", "katilimci", "katılımcı",
                     "gorusme", "görüşme", "anket", "mulakat", "mülakat", "röportaj"]
OLUMSUZLUK = re.compile(
    r"(?i)(\bN\s*/\s*A\b|\byoktur\b|\byok\b|\bbulunmamaktad|\bgerekmez\b|\bgerekmiyor\b"
    r"|\bnot applicable\b|\bno personal data\b|\bdoes not (?:process|collect)\b"
    r"|\w+ma(?:makta|maktadır|dı|di)\b|\w+me(?:mekte|mektedir|di|dı)\b)")
_govde_alt = text.lower()
kisisel_gecisler = []
for k in kisisel_isaretler:
    for m in re.finditer(re.escape(k.lower()), _govde_alt):
        pencere = _govde_alt[max(0, m.start() - 120):m.end() + 120]
        kisisel_gecisler.append((m.start(), bool(OLUMSUZLUK.search(pencere))))
kisisel_var = any(not olumsuz for _, olumsuz in kisisel_gecisler)
kisisel_olumsuz = [g for g in kisisel_gecisler if g[1]]

if dpia_title is not None:
    if not section_has_content(dpia_idx):
        print(f'FAIL DEC-07 DPIA: baslik var ("{dpia_title}") ama icerik bos')
        has_fail = True
    else:
        print(f'PASS DEC-07 DPIA: "{dpia_title}" basligi ve icerigi var')
elif dpia_runin[0] is not None:
    r_title, r_idx = dpia_runin
    r_rest = next(rest for lbl, i, rest in runin if i == r_idx and lbl == r_title)
    if not runin_has_content(r_idx, r_rest):
        print(f'FAIL DEC-07 DPIA: satir ici etiket var ("{r_title}") ama icerik bos')
        has_fail = True
    else:
        print(f'PASS DEC-07 DPIA: satir ici beyan etiketi "{r_title}:" ve icerigi var')
elif kisisel_var:
    print("FAIL DEC-07 DPIA: kisisel veri isareti var ama DPIA basligi yok — DPIA veya gerekceli N/A gerekli")
    has_fail = True
elif kisisel_olumsuz:
    print(f"INFO DEC-07 DPIA: CALISTIRILMADI — {len(kisisel_olumsuz)} gecis yalniz OLUMSUZ baglamda "
          f"(N/A / islenmemektedir); kisisel veri islendigine dair kanit yok, DPIA gerekmez")
else:
    print("INFO DEC-07 DPIA: CALISTIRILMADI — kisisel veri isareti yok, DPIA gerekmez (N/A gerekceli sayilir)")

if has_fail:
    print("DECLARATION-CHECK FAIL — eksik/bos beyan var (dergi masasindan donus riski)")
    sys.exit(1)

print(f"DECLARATION-CHECK PASS — {len(beyanlar)} beyan basligi + kosullu DPIA denetlendi")
sys.exit(0)
