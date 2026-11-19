#!/usr/bin/env python3
"""Atlas v5.5.4 Translit Check — B-3 transliterasyon tutarliligi denetimi

NEDEN VAR:
  *sekîne / sakīna / šəkhīnāh / Shekhinah / Şekina* ayni metinde karisirsa
  hakem filolojik ciddiyeti sorgular (B-3). SCOPE-CONTRACT'ta bir sistem
  ilan edilmeli (DMG / IJMES / ALA-LC / EJTA / DIN 31635 / ISO 233).

KONTROLLER:
  TR-01  SCOPE'ta transliterasyon sistemi ilan edilmis mi? (yoksa P1)
  TR-02  MASTER'da ayni kavram icin birden fazla farkli yazim var mi?
         sekîne ailesi orneginde: sekine / sekîne / sakīna / sakina /
         šəkhīnāh / shekhinah / sekina / şekina vb. 2+ farkli yazim → P1

  TR-02 yalniz sekîne ailesi uzerinde calisir (B-3 ornegi). Baska kavramlar
  icin de ayni mantik genisletilebilir; simdi kapsam bu.

  Sistem→yazim eslesmesi (DMG su yazimi ister gibi) bu asamada denetlenmez;
  yalniz tutarlilik denetlenir. Kaynak metne sadakat ayrica philology
  lensi tarafindan degerlendirilir.

Kullanim:
  python3 scripts/translit_check.py
  python3 scripts/translit_check.py --dosya makale.md --scope scope.md
"""
import re, sys, pathlib

SCOPE_CANDS = ["00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md", "SCOPE.md"]
MASTER_CANDS = [
    "03-FAZ-3-MASTER-v5.5.md",
    "03-FAZ-3-MASTER-v5.4.md",
    "03-FAZ-3-MASTER-v5.2.md",
    "MASTER.md",
]

# --dosya / --scope bayraklari
hedef = scope_hedef = None
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--dosya" and i + 1 < len(args):
        hedef = pathlib.Path(args[i+1]); i+=2; continue
    if args[i] == "--scope" and i + 1 < len(args):
        scope_hedef = pathlib.Path(args[i+1]); i+=2; continue
    i+=1

if hedef is None:
    hedef = next((pathlib.Path(c) for c in MASTER_CANDS if pathlib.Path(c).exists()), None)
if hedef is None or not hedef.exists():
    print("FAIL TR-00: denetlenecek metin bulunamadi (MASTER yok, --dosya verilmedi)")
    sys.exit(1)

scope = scope_hedef
if scope is None:
    scope = next((pathlib.Path(c) for c in SCOPE_CANDS if pathlib.Path(c).exists()), None)

# --- TR-01: SCOPE'ta sistem ilan edilmis mi? ---
if scope is None or not scope.exists():
    print("FAIL TR-01: SCOPE-CONTRACT bulunamadi — transliterasyon sistemi ilan edilemedi")
    sys.exit(1)

st = scope.read_text(errors="ignore")
# SCOPE icinde "transliter" gecen satirlari topla
st_low = st.lower()
has_transliter_line = "transliter" in st_low

# bilinen sistem token'lari
SISTEMLER = ["DMG", "IJMES", "ALA-LC", "EJTA", "DIN 31635", "ISO 233", "LOC", "EI2"]
ilan = None
ilan_satir = None
for ln in st.splitlines():
    if "transliter" in ln.lower():
        for s in SISTEMLER:
            if re.search(rf"(?<!\w){re.escape(s)}(?!\w)", ln, re.I):
                ilan = s; ilan_satir = ln.strip(); break
        if ilan:
            break

if not has_transliter_line:
    # Hizli varyant kontrolu: transliterasyonlu terim yoksa sistem ilani sart degil
    hizli = hedef.read_text(errors="ignore")
    if not re.search(r"\b(?:sek[îi]?ne|sak[îiī]na|šekh|shekhinah|šekina)\b", hizli, re.I):
        print("INFO TR-01: CALISTIRILMADI — SCOPE'ta transliterasyon satiri yok ve MASTER'da sekîne ailesine ait terim de yok (kontrol anlamsiz)")
        # TR-02 de CALISTIRILMADI olacak; butun betik PASS sayilir (kademeli gecis)
        print("INFO TR-02: CALISTIRILMADI — sekîne ailesine ait terim yok")
        print("TRANSLIT-CHECK PASS — TR-01/TR-02 CALISTIRILMADI (kademeli gecis, eski proje)")
        sys.exit(0)
    print("FAIL TR-01: SCOPE'ta 'transliterasyon' satiri yok — sistem ilan edilmeli (DMG / IJMES / ALA-LC / EJTA vb.)")
    sys.exit(1)
if not ilan:
    hizli = hedef.read_text(errors="ignore")
    if not re.search(r"\b(?:sek[îi]?ne|sak[îiī]na|šekh|shekhinah|šekina)\b", hizli, re.I):
        print("INFO TR-01: CALISTIRILMADI — SCOPE'ta transliterasyon sistemi adi yok ama MASTER'da sekîne terimi de yok")
        print("INFO TR-02: CALISTIRILMADI — sekîne ailesine ait terim yok")
        print("TRANSLIT-CHECK PASS — TR-01/TR-02 CALISTIRILMADI (kademeli gecis)")
        sys.exit(0)
    print("FAIL TR-01: SCOPE'ta transliterasyon satiri var ama sistem adi yok — DMG / IJMES / ALA-LC / EJTA / DIN 31635 / ISO 233 gibi bir sistem yazilmali")
    print(f"  Satir: {ilan_satir or '(bulunamadi)'}")
    sys.exit(1)

print(f"PASS TR-01: SCOPE'ta transliterasyon sistemi ilan edilmis — {ilan} ({ilan_satir[:80]})")

# --- TR-02: MASTER'da sekîne ailesi karisik yazilmis mi? ---
text = hedef.read_text(errors="ignore")

# sekîne ailesi icin genis yakalama: latin temelli varyantlar
# sekine / sekîne / sakīna / sakina / šəkhīnāh / shekhinah / şekina / škhina vb.
# Pratik: bu koklerden herhangi birini iceren kelimeleri topla, normalize etmeden
# ayri yazimlari ayir.
# Desen: s/ş + e/a + k + i/ī + na/nah/nh vb. iceren kelimeler — kisa tutuluyor
desen = re.compile(
    r"\b(?:sek[îi]?ne|sak[îiī]na|šekh[iî]nah?|shekhinah|şekina|šəkh[īi]n[āa]h|sakina|sekina)\b",
    re.I
)

eslesenler = desen.findall(text)
# distinct yazimlar (orijinal buyuk/kucuk ve diakritik korunarak, lower ile grupla)
# ayni kelimenin farkli diakritikli hallerini ayri saymak icin lower + diakritik korunur
ayri = {}
for w in eslesenler:
    # normalize sadece lower; diakritik farki korunur (sekine vs sekîne ayridir)
    key = w.lower()
    ayri.setdefault(key, w)

if len(ayri) <= 1:
    if eslesenler:
        print(f"PASS TR-02: sekîne ailesi tek yazimla tutarli — '{next(iter(ayri.values()))}' ({len(eslesenler)} gecis)")
        print("TRANSLIT-CHECK PASS — TR-01 ilan var, TR-02 tutarli")
    else:
        print("INFO TR-02: CALISTIRILMADI — MASTER'da sekîne ailesine ait transliterasyonlu terim bulunamadi (ornegin sekîne/sakīna)")
        print("TRANSLIT-CHECK PASS — TR-01 ilan var, TR-02 CALISTIRILMADI")
    sys.exit(0)
else:
    print(f"FAIL TR-02: sekîne ailesi {len(ayri)} farkli yazimla karisik — tek sisteme sadik kalinmali")
    for k, orij in sorted(ayri.items()):
        print(f"  - '{orij}'")
    print(f"TRANSLIT-CHECK FAIL — ilan {ilan} iken {len(ayri)} farkli yazim")
    sys.exit(1)
