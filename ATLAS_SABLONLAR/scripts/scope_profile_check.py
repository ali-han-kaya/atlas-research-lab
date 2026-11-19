#!/usr/bin/env python3
"""Atlas v5.5.4 Scope Profile Check — ALAN_PROFILI zorunlu-ID kapisi (B-1)

NEDEN VAR:
`atlas-scoper.md` daha once 22 ZORUNLU basligi SABIT kodluyordu; icinde
`Null Model` (SC-007) ve `Istatistik` (SC-009) vardi. Filolojik-teolojik bir
makalede bu iki bolum YOKTUR. `provenance_check.py` CHK-01 her ZORUNLU ID'yi
MASTER'da BASLIK olarak aradigindan, hat yazari OLMAYAN bir istatistik bolumu
uydurmaya aktif olarak zorluyordu. Dogru cevap "bu bolum bu alanda yok"tur;
bos bir bolum uydurmak sidk ihlalidir.

Bu betik zorlamayi tersine cevirir: profil disi bir ZORUNLU ID **FAIL**'dir.

KONTROLLER
  SP-01  `ALAN_PROFILI:` beyani var ve kapali listede                          [P0]
  SP-02  Profil disi ZORUNLU SC-ID yok (or. filolojik profilde Null Model)     [P0]
  SP-03  Profilin ORTAK zorunlulari eksiksiz                                   [P0]
  SP-04  Profile ozgu 4 yuva (SC-002/007/009/010) ZORUNLU olarak var           [P0]
  SP-05  SC-017 DPIA ZORUNLU ise kisisel veri beyani var                       [P1]
  SP-06  ZORUNLU SC-ID hic bulunamadi (vacuous PASS kapali)                    [P0]
  SP-07  Gerekli tablo basliklari eksiksiz ve benzersiz                         [P0]

Kullanim: python3 scripts/scope_profile_check.py [--scope <yol>] [--json]
"""
import json, pathlib, re, sys

JSON_CIK = "--json" in sys.argv
SCOPE = pathlib.Path("00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md")
if "--scope" in sys.argv:
    i = sys.argv.index("--scope")
    if i + 1 < len(sys.argv):
        SCOPE = pathlib.Path(sys.argv[i + 1])

PROFILLER = {"ampirik", "filolojik-teolojik", "kavramsal", "solo"}

ORTAK = {"SC-001", "SC-003", "SC-004", "SC-005", "SC-006", "SC-008", "SC-011",
         "SC-012", "SC-013", "SC-014", "SC-015", "SC-016", "SC-018", "SC-019",
         "SC-020", "SC-021", "SC-022", "SC-030"}
PROFIL_YUVA = {"SC-002", "SC-007", "SC-009", "SC-010"}

# Profil disi sayilan BASLIK kaliplari: yuva numarasi ayni kalir, BASLIK degisir.
# Bir yuvanin basligi baska bir profile aitse, yazar olmayan bir bolume itiliyordur.
YASAK_BASLIK = {
    "filolojik-teolojik": [r"null\s*model", r"istatistik", r"statistic",
                           r"sinirbilim", r"neuroscience", r"bulgular\b"],
    "kavramsal":          [r"null\s*model", r"istatistik", r"statistic",
                           r"sinirbilim", r"neuroscience"],
    "ampirik":            [r"transliterasyon", r"tertium\s*comparationis",
                           r"birincil\s*metin\s*k[uü]lliyat"],
}

bulgular = []


def ekle(kural, siddet, aciklama):
    bulgular.append({"kural": kural, "siddet": siddet, "aciklama": aciklama})


if not SCOPE.exists():
    print(f"FAIL SP-00: SCOPE-CONTRACT yok: {SCOPE}")
    sys.exit(1)

st = SCOPE.read_text(errors="ignore")

# --- SP-01 profil beyani
m = re.search(r"ALAN_PROFILI\s*:\s*([A-Za-zçğıöşüÇĞİÖŞÜ\-]+)", st)
profil = (m.group(1).strip().lower() if m else None)
if not profil:
    ekle("SP-01", "P0", "SCOPE-CONTRACT'ta `ALAN_PROFILI:` beyani YOK — profil beyan "
                        "edilmeden kosu baslamaz (bkz. atlas-scoper Bolum 0)")
elif profil not in PROFILLER:
    ekle("SP-01", "P0", f"ALAN_PROFILI='{profil}' kapali listede yok: {sorted(PROFILLER)}")
    profil = None

# --- ZORUNLU SC-ID'leri normalize tablo basliklarina gore cikar
zor = {}
satirlar = st.splitlines()
tablo_baslangici = next((i for i, line in enumerate(satirlar)
                         if line.strip().startswith("|")), None)
gerekli_basliklar = ("id", "başlık", "zorunluluk")
sutun_indeksleri = {}
tablo_semasi_gecerli = tablo_baslangici is not None

if tablo_baslangici is None:
    ekle("SP-07", "P0", "pipe ile ayrilmis tablo baslik satiri YOK")
else:
    basliklar = [c.strip().lower() for c in
                 satirlar[tablo_baslangici].strip().strip("|").split("|")]
    for ad in gerekli_basliklar:
        indeksler = [i for i, baslik in enumerate(basliklar) if baslik == ad]
        if not indeksler:
            ekle("SP-07", "P0", f"gerekli tablo basligi EKSIK: '{ad}'")
            tablo_semasi_gecerli = False
        elif len(indeksler) > 1:
            ekle("SP-07", "P0", f"gerekli tablo basligi CIFT: '{ad}' "
                                 f"({len(indeksler)} kez)")
            tablo_semasi_gecerli = False
        else:
            sutun_indeksleri[ad] = indeksler[0]

if tablo_semasi_gecerli:
    son_gerekli_indeks = max(sutun_indeksleri.values())
    for line in satirlar[tablo_baslangici + 1:]:
        if not line.strip().startswith("|"):
            break
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) <= son_gerekli_indeks:
            ekle("SP-07", "P0", "tablo veri satiri gerekli sutunlari tasimiyor: "
                                 f"{line.strip()}")
            continue
        im = re.search(r"SC-\d{3}", cols[sutun_indeksleri["id"]])
        if not im:
            continue
        if cols[sutun_indeksleri["zorunluluk"]].upper() == "ZORUNLU":
            zor[im.group(0)] = cols[sutun_indeksleri["başlık"]]

if tablo_semasi_gecerli and not zor:
    ekle("SP-06", "P0", "tablo-sutunu formatinda ZORUNLU SC-ID bulunamadi — "
                        "bos zorunlu liste ile bu kontrol anlamsizca PASS verirdi "
                        "(vacuous PASS kapali). Beklenen: | SC-XXX | Başlık | ZORUNLU | ... |")

if profil and zor:
    # --- SP-03 ortak zorunlular
    for sc in sorted(ORTAK - set(zor)):
        ekle("SP-03", "P0", f"{sc} her profilde ZORUNLU ama sozlesmede yok")

    # SOLO: routing seviyesinde final-release-only; sözleşme tarafı zorunlu alan/aksiyon genişletilmez.
    if profil != "solo":
        # --- SP-04 profile ozgu yuvalar
        for sc in sorted(PROFIL_YUVA - set(zor)):
            ekle("SP-04", "P0", f"{sc} profile ozgu yuva, ZORUNLU olarak bulunmali "
                                f"(baslik profile gore degisir, yuva numarasi degismez)")

        # --- SP-02 profil disi baslik
        for kalip in YASAK_BASLIK.get(profil, []):
            for sc, baslik in sorted(zor.items()):
                if re.search(kalip, baslik, re.I):
                    ekle("SP-02", "P0", f"{sc} basligi '{baslik}' — '{profil}' profiline AIT DEGIL. "
                                        f"Yazari olmayan bir bolumu ZORUNLU kilmak, hattin yazari "
                                        f"uydurmaya itmesidir (B-1)")

    # --- SP-05 DPIA kosullu
    if "SC-017" in zor:
        if not re.search(r"kisisel\s*veri|ki[şs]isel\s*veri|personal\s*data", st, re.I):
            ekle("SP-05", "P1", "SC-017 DPIA ZORUNLU yazilmis ama SCOPE'ta kisisel veri beyani yok — "
                                "DPIA kosulludur; kisisel veri yoksa `N/A (gerekceli)` yazilir")

p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
rapor = {"sema": "SCOPE-PROFILE/v1", "profil": profil, "zorunlu_sayisi": len(zor),
         "p0": p0, "p1": p1, "bulgular": bulgular}

if JSON_CIK:
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
else:
    for b in bulgular:
        print(f"{b['siddet']} {b['kural']} {b['aciklama']}")
    print(f"SCOPE-PROFILE {'FAIL' if p0 else 'PASS'} — profil={profil} · "
          f"{len(zor)} zorunlu ID · P0={p0} P1={p1}")
sys.exit(1 if p0 else 0)
