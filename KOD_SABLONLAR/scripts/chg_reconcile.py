#!/usr/bin/env python3
"""chg_reconcile — kod hattinin EN KRITIK kapisi (RECK-01..07)

NEDEN VAR:
Akademik hatta `fix_reconcile.py` "duzeltildi denen sey gercekten metinde mi"
sorusunu sorar. Kod hattinda ayni soru daha tehlikelidir, cunku ajan diff
uretir: "CHG-003 uygulandi" cumlesi hicbir dosyaya dokunmadan yazilabilir, ve
tersine, planda olmayan bir dosya sessizce degistirilebilir. Bu betik iddia ile
diff'i CARPRAZ eslestirir. Ajan beyani girdi degil, DENETLENEN seydir.

MAKINE BLOGU ZORUNLULUGU:
KFAZ0/1/2 artefaktlari .md'dir ama her biri govdesinde bir ```json bloku
tasimak zorundadir. Markdown tablosu ayristirmak kirilgandir ve sessizce yanlis
okur; sessiz yanlis okuma bu labda P0'dir. Blok yoksa kontrol CALISTIRILMADI
sayilir ve P0 verilir — "ayristiramadim" ile "temiz" ayni sey degildir.

KURALLAR
  RECK-01  KFAZ0'daki her REQ, KFAZ1 planinda karsiligini bulur              [P0]
  RECK-02  "UYGULANMIS" her CHG'nin dosyasi `git diff`te                     [P0]
  RECK-03  Diff'teki her URUN dosyasi planda var  [SCOPE_VIOLATION P0]
  RECK-03  Kurulum dosyalari muaf ama LOGLANIR  [BILGI/KURULUM — O4-04]
  RECK-03  `__pycache__/` icindeki .pyc muaf ama LOGLANIR [BILGI/ONBELLEK — O5-02/05]
  RECK-04  2B kapisinin iddia ettigi her CHG diff'te                         [P0]
  RECK-05  Hayalet CHG yok (olmayan REQ'e / plansiz dosyaya baglanmis)       [P0]
  RECK-06  Dondurulmus bolge diff'te GORUNMEZ                                [P0]
  RECK-07  Davranissal her REQ, TABANDA OLMAYAN bir test adina eslenir       [P0]
  RECK-08  Makine bloklarinin ALAN BICIMI semaya uyar     [SCHEMA_INVALID P0]
  RECK-09  KFAZ0'da (plan oncesi) URUN kodu diff'te GORUNMEZ
                                               [KFAZ0_PRE_PLAN_CHANGE P0]

RECK-08 NICIN EKLENDI (OLCUM-02, 24.08.2026):
Ilk canli kosuda KFAZ0 ajani `req` alanini NESNE listesi yerine DIZE listesi
yazdi. Asagidaki satir dize girdileri `isinstance(x, dict)` ile sessizce
atiyordu; `req_listesi` bos kaliyor, RECK-01 ve RECK-07 HIC KOSMUYOR ve kapi
PASS veriyordu. Kural mantigi dogruydu, olen sey GIRDI DOGRULAMASIYDI.
Artik sema disi her alan P0'dir ve sessizce dusen girdi YOKTUR.

RECK-07 NICIN BOYLE:
"Test ekledim" demek yetmez; tabanda zaten var olan bir teste isaret etmek
bedava yesildir. Yeni davranis, YENI bir test adi gerektirir. Bu, testin
DOLU oldugunu kanitlamaz (bkz. test_attest kalan risk) — yoklugunu engeller.

Kullanim:
  python3 scripts/chg_reconcile.py [--kosu _KOSU] [--taban _KOSU/gate/BASELINE.json]
                                   [--gate2b _KOSU/gate/KOD-gate-2b.json] [--json]
"""
import json, pathlib, re, subprocess, sys

JSON_CIK = "--json" in sys.argv


def arg(b, v):
    if b in sys.argv:
        i = sys.argv.index(b)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return v


KOSU = pathlib.Path(arg("--kosu", "_KOSU"))
# K10 (OLCUM-02): /kod-faz1 adim 5 bu betigi CAGIRIR ve fazin kapanis kurali
# "exit 0 degilse DUR" der. Ama betik KFAZ2 artefaktini KOSULSUZ istiyordu ve
# KFAZ2 tanim geregi henuz yazilmamistir -> KFAZ1 asla tamamlanamazdi.
# Cozum: faz BILDIRILIR (--faz) ya da artefaktlardan CIKARILIR. Henuz sirasi
# gelmemis artefakt P1 CALISTIRILMADI'dir; GECMIS bir artefaktin eksikligi P0.
FAZ = (arg("--faz", "") or "").upper()
TABAN = pathlib.Path(arg("--taban", str(KOSU / "gate" / "BASELINE.json")))
GATE2B = pathlib.Path(arg("--gate2b", str(KOSU / "gate" / "KOD-gate-2b.json")))
bulgular = []


def ekle(kural, siddet, aciklama, kod=None):
    b = {"kural": kural, "siddet": siddet, "aciklama": aciklama}
    if kod:
        b["kod"] = kod
    bulgular.append(b)


JSON_BLOK = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def makine_blogu(desen, sema, gerekli=True):
    """Artefaktin govdesindeki ```json blogunu al.

    `gerekli=False` ise (o faz henuz gelmedi) eksiklik P1 CALISTIRILMADI'dir.
    Bu bir muafiyet DEGILDIR: kayit yine dusuyor, yalniz hattı kilitlemiyor.
    """
    adaylar = sorted(KOSU.glob(desen))
    if not adaylar:
        ekle("RECK-00", "P0" if gerekli else "P1",
             f"artefakt yok: {KOSU}/{desen}" + ("" if gerekli else " — bu faz henuz gelmedi"),
             "CALISTIRILMADI")
        return None
    metin = adaylar[0].read_text(errors="ignore")
    m = JSON_BLOK.search(metin)
    if not m:
        ekle("RECK-00", "P0", f"{adaylar[0].name} icinde ```json makine blogu YOK — "
                              f"markdown tablosu ayristirmak kirilgandir, sessiz yanlis "
                              f"okuma P0'dir", "CALISTIRILMADI")
        return None
    try:
        d = json.loads(m.group(1))
    except Exception as e:
        ekle("RECK-00", "P0", f"{adaylar[0].name} makine blogu JSON gecersiz: {e}", "CALISTIRILMADI")
        return None
    if d.get("sema") != sema:
        ekle("RECK-00", "P1", f"{adaylar[0].name} sema='{d.get('sema')}' beklenen='{sema}'")
    return d


# Faz cikarimi: --faz verilmediyse en ileri artefakttan cikar.
if not FAZ:
    if sorted(KOSU.glob("02-KFAZ-2-*.md")):
        FAZ = "KFAZ2"
    elif sorted(KOSU.glob("01-KFAZ-1-*.md")):
        FAZ = "KFAZ1"
    else:
        FAZ = "KFAZ0"
_SIRA = {"KFAZ0": 0, "KFAZ1": 1, "KFAZ2": 2, "KFAZ3": 3, "KFAZ4": 4, "KFAZ5": 5}
if FAZ not in _SIRA:
    # Bilinmeyen faz SESSIZCE kabul edilmez: yazim hatasi kapinin siddetini
    # farkinda olmadan degistirebilir. `budget_guard` da ayni sekilde davranir.
    print(f"FAIL: bilinmeyen faz '{FAZ}' (beklenen: {list(_SIRA)}) — "
          f"kapi CALISTIRILMADI (fail-closed)")
    sys.exit(1)
_n = _SIRA[FAZ]

faz0 = makine_blogu("00-KFAZ-0-*.md", "KFAZ0/v1", gerekli=_n >= 0)
faz1 = makine_blogu("01-KFAZ-1-*.md", "KFAZ1/v1", gerekli=_n >= 1)
faz2 = makine_blogu("02-KFAZ-2-*.md", "KFAZ2/v1", gerekli=_n >= 2)


# ===================================================== RECK-08  SEMA DOGRULAMA
# Sessiz dusme YOKTUR: bicimi tutmayan her alan P0 SCHEMA_INVALID uretir.
REQ_TURLERI = {"davranissal", "behavioral", "davranis", "yapisal", "structural", "yapi"}


def _liste_of_str(d, alan, etiket):
    v = d.get(alan)
    if v is None:
        return
    if not isinstance(v, list):
        ekle("RECK-08", "P0", f"{etiket}.{alan} liste degil ({type(v).__name__})", "SCHEMA_INVALID")
        return
    for i, x in enumerate(v):
        if not isinstance(x, str):
            ekle("RECK-08", "P0", f"{etiket}.{alan}[{i}] dize degil ({type(x).__name__}): {x!r}",
                 "SCHEMA_INVALID")


def sema_dogrula_faz0(d):
    if d is None:
        return
    if "req" not in d:
        ekle("RECK-08", "P0", "KFAZ0 makine blogunda `req` alani YOK", "SCHEMA_INVALID"); return
    v = d.get("req")
    if not isinstance(v, list):
        ekle("RECK-08", "P0", f"KFAZ0.req liste degil ({type(v).__name__})", "SCHEMA_INVALID"); return
    if not v:
        ekle("RECK-08", "P0", "KFAZ0.req BOS — kapsamsiz sozlesme denetlenemez", "SCHEMA_INVALID")
    for i, x in enumerate(v):
        if not isinstance(x, dict):
            ekle("RECK-08", "P0",
                 f"KFAZ0.req[{i}] nesne degil ({type(x).__name__}): {x!r} — beklenen "
                 f'{{"id":..,"tur":"davranissal|yapisal","kabul":..}}. Dize listesi yazmak '
                 f"RECK-01 ve RECK-07'yi SESSIZCE devre disi birakir", "SCHEMA_INVALID")
            continue
        if not x.get("id"):
            ekle("RECK-08", "P0", f"KFAZ0.req[{i}] `id` alani yok/bos", "SCHEMA_INVALID")
        tur = str(x.get("tur", "")).lower()
        if not tur:
            ekle("RECK-08", "P0", f"KFAZ0.req[{i}] ({x.get('id')}) `tur` alani YOK — "
                                  f"tursuz REQ RECK-07 kapsamina GIRMEZ", "SCHEMA_INVALID")
        elif tur not in REQ_TURLERI:
            ekle("RECK-08", "P0", f"KFAZ0.req[{i}] ({x.get('id')}) tur='{x.get('tur')}' "
                                  f"kapali listede yok {sorted(REQ_TURLERI)}", "SCHEMA_INVALID")
        if not str(x.get("kabul", "")).strip():
            ekle("RECK-08", "P1", f"KFAZ0.req[{i}] ({x.get('id')}) `kabul` bos — "
                                  f"olculebilir kabul olcutu yok")


def sema_dogrula_faz1(d):
    if d is None:
        return
    for alan in ("degisecek", "dondurulan"):
        if alan not in d:
            ekle("RECK-08", "P0", f"KFAZ1 makine blogunda `{alan}` alani YOK", "SCHEMA_INVALID")
        else:
            _liste_of_str(d, alan, "KFAZ1")
    rt = d.get("req_test")
    if rt is None:
        ekle("RECK-08", "P0", "KFAZ1 makine blogunda `req_test` alani YOK", "SCHEMA_INVALID")
    elif not isinstance(rt, dict):
        ekle("RECK-08", "P0", f"KFAZ1.req_test sozluk degil ({type(rt).__name__})", "SCHEMA_INVALID")
    else:
        for k, v in rt.items():
            if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
                ekle("RECK-08", "P0", f"KFAZ1.req_test['{k}'] dize listesi degil: {v!r}",
                     "SCHEMA_INVALID")
    cakisan = set(d.get("degisecek") or []) & set(d.get("dondurulan") or [])
    for x in sorted(cakisan):
        ekle("RECK-08", "P0", f"'{x}' hem `degisecek` hem `dondurulan` listesinde", "SCHEMA_INVALID")


def sema_dogrula_faz2(d):
    if d is None:
        return
    v = d.get("chg")
    if v is None:
        ekle("RECK-08", "P0", "KFAZ2 makine blogunda `chg` alani YOK", "SCHEMA_INVALID"); return
    if not isinstance(v, list):
        ekle("RECK-08", "P0", f"KFAZ2.chg liste degil ({type(v).__name__})", "SCHEMA_INVALID"); return
    for i, x in enumerate(v):
        if not isinstance(x, dict):
            ekle("RECK-08", "P0", f"KFAZ2.chg[{i}] nesne degil ({type(x).__name__}): {x!r}",
                 "SCHEMA_INVALID")
            continue
        for alan in ("id", "dosya", "durum"):
            if not str(x.get(alan, "")).strip():
                ekle("RECK-08", "P0", f"KFAZ2.chg[{i}] `{alan}` alani yok/bos", "SCHEMA_INVALID")
        # B2 (OLCUM-06, 26.08.2026): `req` alani liste ise set uyesi aramasi
        # `TypeError: unhashable type: 'list'` ile coker; semada yakalanmali ve
        # crash yerine SCHEMA_INVALID P0 uretilmelidir. Liste DIZE degildir.
        if "req" in x and x["req"] is not None and not isinstance(x["req"], str):
            ekle("RECK-08", "P0",
                 f"KFAZ2.chg[{i}] `req` dize degil ({type(x['req']).__name__}): {x['req']!r} — "
                 f"tek REQ kimligi beklenir (örn. \"REQ-001\"); liste ise tekillestir",
                 "SCHEMA_INVALID")


sema_dogrula_faz0(faz0)
sema_dogrula_faz1(faz1)
sema_dogrula_faz2(faz2)

# DIFF KUMESI = degistirilen (tracked) + EKLENEN (untracked) dosyalar.
# `git diff` izlenmeyen dosyayi GOSTERMEZ; yalniz ona bakan bir kapsam kapisi,
# plansiz olarak EKLENEN yeni bir dosyayi hic gormez. Bu kusur kod_selftest
# RECK-2 negatif fiksturuyle yakalandi (24.08.2026) ve burada kapatildi.
diff_dosyalar = set()
_git_ok = True
for _komut in (["git", "diff", "--name-only", "HEAD"],
               ["git", "ls-files", "--others", "--exclude-standard"]):
    _r = subprocess.run(_komut, capture_output=True, text=True, timeout=120)
    if _r.returncode != 0:
        _git_ok = False
        ekle("RECK-00", "P0", f"`{' '.join(_komut)}` exit={_r.returncode}: "
                              f"{_r.stderr.strip()[:200]} — carpraz esleme CALISTIRILMADI",
             "CALISTIRILMADI")
        continue
    _onek = str(KOSU).rstrip("/") + "/"
    diff_dosyalar |= {x.strip() for x in _r.stdout.split("\n")
                      if x.strip() and not x.strip().startswith(_onek)}
if not _git_ok:
    diff_dosyalar = set()

# ------------------------------------------------- O4-04  KURULUM GURULTUSU
# OLCUM-04 (24.08.2026): `kur.sh` hedef depoya 64 dosya kurar (.opencode/,
# scripts/, ORTAK/, templates/, opencode.json, 00_KOD_OKU_BENI.md ...). Bunlar
# ilk koşuda `git ls-files --others` ile IZLENMEYEN gorunur ve RECK-03 hepsini
# "planda yok" diye P0 sayar: olculen 63x P0, tamami SAHTE. Hat kendi kurulumunu
# kapsam ihlali saniyordu ve FINAL bu gurultuyle FAIL veriyordu.
#
# Cozum: SABIT ve BELGELI bir kurulum oneki listesi. SESSIZ MUAFIYET YOKTUR —
# haric tutulan her dosya `BILGI RECK-03 kurulum dosyasi: <ad>` satiriyla loga
# duser ve JSON raporda `kurulum_dosyalari` altinda sayilir.
#
# SINIR (bilerek yazildi): hedef proje kendi `scripts/` dizinini kullaniyorsa o
# dizindeki GERCEK bir kapsam ihlali de muaf olur. Bu yuzden muafiyet gorunur
# tutulur; sessiz olsaydi kapiyi kor ederdi.
KURULUM_KALIPLARI = (
    ".opencode/", "scripts/", "templates/", "ORTAK/",
    "opencode.json", "routing.profiles.json",
    "00_KOD_OKU_BENI.md", "OPERATOR_SURME.md", "AI_CALISMA_SISTEMI_v1.md",
    "kod_profil.json",
    # O5-02 (24.08.2026): kurulum artik hedefin `.gitignore`'una derleme
    # onbellegi satirlarini ekliyor (kur.sh adim 5). Taze depoda bu dosya
    # IZLENMEYEN dogar; listeye alinmasaydi kurulumun KENDISI RECK-03 P0
    # uretirdi — kapatilan gurultunun aynisi, baska kapida (olculdu).
    ".gitignore",
)


def _kurulum_dosyasi(yol):
    return any(yol == k or yol.startswith(k) for k in KURULUM_KALIPLARI)


# --------------------------------------------- O5-02  DERLEME ONBELLEGI (.pyc)
# 24.08.2026 (canli senaryo, olculdu): KFAZ3 hedef deponun test komutunu kosar;
# python `birim/__pycache__/*.pyc` ve `tests/__pycache__/*.pyc` uretir. Bunlar
# `git ls-files --others` ile IZLENMEYEN gorunur ve RECK-03 hepsini "planda yok"
# diye P0 sayardi (olculen: 2x P0, tamami SAHTE — hicbiri kaynak degisikligi
# degil, kapinin KENDI kosusunun yan urunu).
#
# ASIL COZUM `kur.sh`tedir: kurulum hedef deponun .gitignore'una `__pycache__/`
# ve `*.pyc` ekler, boylece dosyalar diff kumesine HIC GIRMEZ. Burasi EK
# SAVUNMADIR: hedef deponun .gitignore'u elle bozulursa kapi yine sahte P0
# uretmez. SESSIZ MUAFIYET YOKTUR — her biri `BILGI RECK-03 derleme onbellegi:`
# satiriyla loga duser ve JSON raporda `onbellek_dosya_sayisi` altinda sayilir.
#
# SINIR (bilerek dar, IKI KOSUL birden): dosya hem `.pyc` uzantili OLACAK hem de
# adi TAM OLARAK `__pycache__` olan bir DIZIN BILESENININ altinda DURACAK.
#
# NEDEN ALT-DIZE DEGIL (O5-05, bagimsiz denetim 24.08.2026 — P0):
# Ilk daraltma yalniz uzantiya bakiyordu; ikincisi `"__pycache__/" in yol` diye
# ALT-DIZE ariyordu. Ikisi de delindi. Alt-dize surumunde depo kokundeki
# `evil__pycache__/anahtar.pyc` — icinde GERCEK bir PEM ozel anahtar — her iki
# kapida da muaf sayildi: `chg_reconcile` BILGI ONBELLEK + exit=0, `secret_scan`
# BILGI SEC-05 + exit=0. Yani tek bir dizin adiyla KAPSAM ve SIZINTI kapilari
# BIRLIKTE atlatilabiliyordu (olculdu; bu turda yeniden uretildi).
# Artik yol bilesenlerine ayrilir ve `__pycache__` TAM ESLESME ile aranir;
# `parts[:-1]` dosya adinin kendisini disarida birakir. `evil__pycache__`,
# `__pycache__x`, `x__pycache__` gibi adlar ARTIK ESLESMEZ.
ONBELLEK_UZANTILARI = (".pyc",)
ONBELLEK_DIZIN_ADI = "__pycache__"


def _onbellek_dosyasi(yol):
    if not yol.endswith(ONBELLEK_UZANTILARI):
        return False
    # git yollari her zaman `/` ayracli gelir -> PurePosixPath dogru ayirici
    return ONBELLEK_DIZIN_ADI in pathlib.PurePosixPath(yol).parts[:-1]


onbellek_dosyalari = {d for d in diff_dosyalar if _onbellek_dosyasi(d)}
kurulum_dosyalari = {d for d in diff_dosyalar
                     if _kurulum_dosyasi(d) and d not in onbellek_dosyalari}
urun_dosyalari = diff_dosyalar - kurulum_dosyalari - onbellek_dosyalari

# --------------------------------- O3-05  KFAZ0 PLAN-ONCESI URUN KODU YASAGI
# OLCUM-03 O3-05 (24.08.2026): RECK-03 yalniz `faz0 and faz1` iken kosar.
# Yalniz KFAZ0 artefakti varken (plan henuz yok) diff'teki URUN kodu hicbir
# kurala takilmiyordu: olculen kosuda birim/olcek.py + tests/test_olcek.py
# diff'teydi ve kapi PASS exit=0 verdi — "plan YOKKEN kod degisti" durumunu
# hat tam en tehlikeli oldugu anda goremiyordu. RECK-09 bu kor noktayi kapatir.
# Kurulum/derleme-onbellegi siniflari BILGI ile loglanmaya devam eder
# (O4-04/O5-02 desenleri aynen korunur; sessiz muafiyet yoktur).
if faz0 and not faz1:
    for d in sorted(kurulum_dosyalari):
        ekle("RECK-09", "BILGI", f"kurulum dosyasi (plan oncesi): {d}", "KURULUM")
    for d in sorted(onbellek_dosyalari):
        ekle("RECK-09", "BILGI", f"derleme onbellegi (plan oncesi): {d}", "ONBELLEK")
    for d in sorted(urun_dosyalari):
        ekle("RECK-09", "P0",
             f"'{d}' plan YOKKEN diff'te — taban TEMIZ agacta olculur, urun kodu "
             f"ancak KFAZ2'de planla degisir", "KFAZ0_PRE_PLAN_CHANGE")

if faz0 and faz1:
    req_listesi = {x["id"]: x for x in (faz0.get("req") or []) if isinstance(x, dict) and x.get("id")}
    plan_req = set((faz1.get("req_test") or {}).keys())
    plan_dosya = set(faz1.get("degisecek") or [])
    dondurulan = set(faz1.get("dondurulan") or [])

    # RECK-01
    for rid in sorted(req_listesi):
        if rid not in plan_req and not any(rid in str(v) for v in (faz1.get("req_dosya") or {}).values()):
            ekle("RECK-01", "P0", f"{rid} KFAZ0'da var ama KFAZ1 planinda karsiligi yok")

    # RECK-03 SCOPE_VIOLATION — yalniz URUN dosyalari (O4-04)
    for d in sorted(kurulum_dosyalari - plan_dosya):
        ekle("RECK-03", "BILGI", f"kurulum dosyasi: {d} — kapsam disi sayildi "
                                 f"(O4-04); ihlal olarak islenmedi", "KURULUM")
    for d in sorted(onbellek_dosyalari - plan_dosya):
        ekle("RECK-03", "BILGI", f"derleme onbellegi: {d} — kapsam disi sayildi "
                                 f"(O5-02, pyc); ihlal olarak islenmedi", "ONBELLEK")
    for d in sorted(urun_dosyalari - plan_dosya):
        ekle("RECK-03", "P0", f"diff'te olan '{d}' KFAZ1 planinda YOK", "SCOPE_VIOLATION")

    # RECK-06 dondurulmus bolge
    for d in sorted(dondurulan & diff_dosyalar):
        ekle("RECK-06", "P0", f"DONDURULMUS bolge degismis: {d}")

    # RECK-07 davranissal REQ -> tabanda olmayan test
    taban = json.loads(TABAN.read_text()) if TABAN.exists() else {}
    taban_testler = set(taban.get("test_adlari") or [])
    if not TABAN.exists():
        ekle("RECK-07", "P1", f"{TABAN} yok — taban test adlari bilinmiyor, "
                              f"RECK-07 CALISTIRILMADI", "CALISTIRILMADI")
    elif "test_adlari" not in taban:
        # OLCUM-02 K12: taban DOSYASI var ama `test_adlari` anahtari yoksa
        # taban_testler bos kume olur ve "tabanda yok" kosulu HER AD icin
        # dogru cikar -> RECK-07 sessizce her seyi gecer. Bu bir PASS degil,
        # CALISTIRILAMAMIS bir kuraldir; fail-closed sayilir.
        ekle("RECK-07", "P0", f"{TABAN} icinde `test_adlari` anahtari YOK — taban test "
                              f"adlari bilinmeden 'tabanda olmayan test' kurali "
                              f"DEGERLENDIRILEMEZ", "CALISTIRILMADI")
    else:
        for rid, meta in sorted(req_listesi.items()):
            if str(meta.get("tur", "")).lower() not in ("davranissal", "behavioral", "davranis"):
                continue
            testler = (faz1.get("req_test") or {}).get(rid) or []
            yeni = [t for t in testler if t not in taban_testler]
            if not testler:
                ekle("RECK-07", "P0", f"{rid} davranissal ama hicbir test adina eslenmemis")
            elif not yeni:
                ekle("RECK-07", "P0", f"{rid} yalniz TABANDA ZATEN VAR OLAN teste eslenmis "
                                      f"({', '.join(testler)}) — yeni davranis yeni test adi ister")

if faz2:
    chg_listesi = [c for c in (faz2.get("chg") or []) if isinstance(c, dict)]
    plan_dosya = set((faz1 or {}).get("degisecek") or [])
    req_idler = {x.get("id") for x in ((faz0 or {}).get("req") or []) if isinstance(x, dict)}

    for c in chg_listesi:
        cid = c.get("id", "?")
        durum = str(c.get("durum", "")).upper()
        dosya = c.get("dosya")
        # RECK-02
        if durum in ("UYGULANMIS", "UYGULANMIŞ", "APPLIED", "DONE"):
            if not dosya:
                ekle("RECK-02", "P0", f"{cid} UYGULANMIS ama `dosya` alani yok")
            elif dosya not in diff_dosyalar:
                ekle("RECK-02", "P0", f"{cid} 'UYGULANMIS' diyor ama '{dosya}' git diff'te YOK")
        # RECK-05 hayalet — B2 guard: liste ise TypeError vermeden gecer
        _req = c.get("req")
        if isinstance(_req, str) and _req and req_idler and _req not in req_idler:
            ekle("RECK-05", "P0", f"{cid} olmayan bir REQ'e bagli: {_req}", "HAYALET_CHG")
        if dosya and plan_dosya and dosya not in plan_dosya:
            ekle("RECK-05", "P0", f"{cid} plansiz dosyaya bagli: {dosya}", "HAYALET_CHG")

    # RECK-04 2B iddialari
    if GATE2B.exists():
        try:
            g2b = json.loads(GATE2B.read_text())
        except Exception as e:
            ekle("RECK-04", "P0", f"{GATE2B} JSON gecersiz: {e}", "CALISTIRILMADI")
            g2b = {}
        chg_dosya = {c.get("id"): c.get("dosya") for c in chg_listesi}
        for m in (g2b.get("manifest_reconciliation") or []):
            if not isinstance(m, dict):
                continue
            cid = m.get("chg_id") or m.get("id")
            st = str(m.get("status", "")).upper()
            if cid and st in ("UYGULANMIS_KANITLI", "KANITLI", "VERIFIED", "APPLIED_VERIFIED"):
                d = chg_dosya.get(cid)
                if not d:
                    ekle("RECK-04", "P0", f"2B '{cid}' icin KANITLI diyor ama bu CHG manifestte yok")
                elif d not in diff_dosyalar:
                    ekle("RECK-04", "P0", f"2B '{cid}' KANITLI diyor ama '{d}' diff'te YOK — "
                                          f"kapi iddiasi dogrulanmadi")
    else:
        ekle("RECK-04", "P1", f"{GATE2B} yok — 2B iddialari CALISTIRILMADI", "CALISTIRILMADI")

p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
rapor = {"sema": "CHG-RECONCILE/v1", "diff_dosya_sayisi": len(diff_dosyalar),
         "kurulum_dosya_sayisi": len(kurulum_dosyalari),
         "onbellek_dosya_sayisi": len(onbellek_dosyalari),
         "urun_dosya_sayisi": len(urun_dosyalari),
         "p0": p0, "p1": p1, "bulgular": bulgular}
if JSON_CIK:
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
else:
    for b in bulgular:
        print(f"{b['siddet']} {b['kural']} {b.get('kod','')} {b['aciklama']}")
    _ek = (f" (urun {len(urun_dosyalari)} + kurulum {len(kurulum_dosyalari)}"
           f" + onbellek {len(onbellek_dosyalari)})"
           if (kurulum_dosyalari or onbellek_dosyalari) else "")
    print(f"CHG-RECONCILE {'FAIL' if p0 else 'PASS'} — diff'te {len(diff_dosyalar)} dosya{_ek} · P0={p0} P1={p1}")
sys.exit(1 if p0 else 0)
