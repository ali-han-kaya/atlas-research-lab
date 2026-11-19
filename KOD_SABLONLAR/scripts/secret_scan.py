#!/usr/bin/env python3
"""secret_scan — sizinti taramasi (KFAZ4 kapi girdisi)

NEDEN VAR:
Kod hattinda uretilen diff, akademik hatta olmayan bir risk tasir: kimlik
bilgisi. Bu betik kalip TABANINI YENIDEN YAZMAZ. `KOMUT_TOOLKIT_v4`'teki
`v4_verify.py` zaten dogru davraniyor ve OLCULDU (24.08.2026):
  - 9 SECRET_PATTERNS, 20 PLACEHOLDER_HINTS, yan etkisiz import edilebiliyor
  - D2: dosya basina ILK ESLESMEDE DURMUYOR
  - yer tutucu ipucu yalniz NOT dusuruyor, otomatik indirgeme YAPMIYOR
  - imzali muafiyet ve .env.example ayrimi zaten var
Ikinci bir kalip listesi tutmak, birinde duzeltilen kusurun otekinde yasamasi
demektir. Bu yuzden IMPORT edilir; toolkit yoksa betik FAIL-CLOSED durur.

KURALLAR
  SEC-01  Gercek `.env` dosyasi diff'te                                   [P0]
  SEC-02  Eslesen sir kalibi (yer tutucu ipucu tasisa bile DUSURULMEZ)    [P0]
  SEC-03  Yer tutucu ipucu tasiyan eslesme                    [P1 + insan karari]
  SEC-04  Ikili/kilit dosyasi atlandi                                  [bilgi]
  SEC-05  TAM `__pycache__` dizinindeki .pyc kapsam disi           [bilgi]

Kullanim: python3 scripts/secret_scan.py [--diff] [--dizin .] [--json]
  --diff : yalniz `git diff --name-only HEAD` dosyalarini tarar (varsayilan)
  --tum  : calisma agacindaki tum metin dosyalarini tarar
"""
import importlib.util, json, os, pathlib, re, subprocess, sys

JSON_CIK = "--json" in sys.argv
TUM = "--tum" in sys.argv
dizin = "."
if "--dizin" in sys.argv:
    i = sys.argv.index("--dizin")
    if i + 1 < len(sys.argv):
        dizin = sys.argv[i + 1]
KOK = pathlib.Path(dizin).resolve()


def v4_aday_yollar():
    """Arama sirasi: --v4 > env V4_VERIFY_YOLU > kod_profil.json > KOK ici > kardes.

    GUVEN SINIRI (O5-06): taranan deponun DISINDA OZYINELEMELI arama YAPILMAZ.
    Disaridan tek aday, hedefin hemen yanindaki sabit yoldur; o da yoksa KISMI.

    OLCUM-02 K4: toolkit `KOD_SABLONLAR/`'in parcasi DEGILDIR, hash kilitlidir ve
    kirmizi cizgi geregi KOPYALANAMAZ. Hedef depoda betik hicbir zaman kosamiyordu
    ve `/kod-faz2` adim 6 orada duruyordu (canli olculdu). Cozum kalip listesini
    kopyalamak DEGIL, kaynagi ISARET ETMEKTIR.
    """
    adaylar = []
    if "--v4" in sys.argv:
        i = sys.argv.index("--v4")
        if i + 1 < len(sys.argv):
            adaylar.append(pathlib.Path(sys.argv[i + 1]))
    if os.environ.get("V4_VERIFY_YOLU"):
        adaylar.append(pathlib.Path(os.environ["V4_VERIFY_YOLU"]))
    _pr = KOK / "kod_profil.json"
    if _pr.exists():
        try:
            _v = json.loads(_pr.read_text()).get("v4_verify_yolu")
            if _v:
                adaylar.append(pathlib.Path(_v).expanduser())
        except Exception:
            pass
    # --------------------------------------------------- O4-03  DIZIN COZUMLEME
    # OLCUM-04 (24.08.2026): `kod_profil.json` sablonu ve DEVIR §2 "toolkit
    # yolunu ver" diyor; kullanici cogu zaman TOOLKIT DIZININI yaziyor. Betik
    # ise DOSYA bekliyordu: dizin verilince `spec_from_file_location` None
    # dondu, `None.loader` -> AttributeError ve ciplak `secret_scan` CRASH etti
    # (exit=1). Artik dizin verilirse betik v4_verify.py'yi KENDISI cozer.
    _cozulmus = []
    for a in adaylar:
        if a.is_dir():
            for _alt in ("ARACLAR/betikler/v4_verify.py",          # toolkit koku
                         "betikler/v4_verify.py",                   # ARACLAR/ verilmis
                         "v4_verify.py"):                           # betikler/ verilmis
                _c = a / _alt
                if _c.is_file():
                    _cozulmus.append(_c)
                    break
            else:
                _cozulmus += sorted(a.glob("**/v4_verify.py"))[:1]
        else:
            _cozulmus.append(a)
    adaylar = [a for a in _cozulmus if a.is_file()]
    # Taranan deponun KENDI icinde toolkit varsa (lab klonu boyle duruyor) kullan.
    adaylar += sorted(KOK.glob("**/KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_verify.py"))
    # ------------------------------------------------- O5-06  GUVEN SINIRI [P0]
    # Bagimsiz denetim (24.08.2026): burada EBEVEYNDE OZYINELEMELI arama vardi
    # (`KOK.parent.glob("**/KOMUT_TOOLKIT_v4/.../v4_verify.py")`). Bu, taranan
    # deponun DISINDAKI rastgele derinlikteki bir kardes agactan Python dosyasi
    # bulup IMPORT ETMEK demekti — `exec_module` calistirir. Olculdu (bu turda
    # yeniden uretildi): kardes agaca konan sahte bir `v4_verify.py` import
    # edildi, DISKE YAZDI, ve kendi bos SECRET_PATTERNS'ini dayatarak depodaki
    # GERCEK PEM anahtarini gizleyip "SECRET-SCAN PASS exit=0" verdirdi.
    # Denetim ayrica gostermistir ki bu, kotu niyet olmadan da bozuyor: audit
    # klonu sistem temp kokunde dururken ilgisiz bir temp projesi bulundu ve
    # oz-test 142/142 yerine 137/142'ye dustu.
    #
    # Ozyinelemeli arama KALDIRILDI. Yerine YALNIZ TEK, SABIT, OZYINELEMESIZ yol:
    # hedefin hemen yanindaki toolkit. Bulunamazsa KISMI mod (exit=3) — mevcut
    # fail-closed davranis. Toolkit baska yerdeyse operator ACIKCA bildirir:
    # `--v4 <yol>` · `V4_VERIFY_YOLU` · `kod_profil.json`.
    _kardes = KOK.parent / "KOMUT_TOOLKIT_v4" / "ARACLAR" / "betikler" / "v4_verify.py"
    if _kardes.is_file():
        adaylar.append(_kardes)
    return adaylar


def v4_yukle():
    """v4_verify.py'yi bul ve import et. Bulunamazsa KISMI MODA duser (exit=3).

    NOT (24.08.2026): import, KOMUT_TOOLKIT_v4 agacina __pycache__ YAZIYORDU.
    Toolkit DEGISTIRILMEZ bir agactir; kilit manifesti .pyc icermese de oraya
    dosya yazmak kirmizi cizgiye dokunmaktir. Bu yuzden import suresince
    bytecode yazimi KAPATILIR ve sonra eski haline dondurulur.
    """
    for a in v4_aday_yollar():
        spec = importlib.util.spec_from_file_location("v4v", a)
        m = importlib.util.module_from_spec(spec)
        _onceki = sys.dont_write_bytecode
        sys.dont_write_bytecode = True          # toolkit agacina .pyc YAZMA
        try:
            spec.loader.exec_module(m)
        except Exception as e:
            print(f"FAIL SEC-00: v4_verify.py import edilemedi ({a}): {e}")
            sys.exit(1)
        finally:
            sys.dont_write_bytecode = _onceki
        if hasattr(m, "SECRET_PATTERNS"):
            return m, str(a)
    return None, None


v4, v4_yol = v4_yukle()
KISMI = v4 is None
if KISMI:
    # Kalip TABANI yok. Yine de YAPISAL (kalip listesine bagli OLMAYAN)
    # kontroller kosar; bunlar tek basina "temiz" beyani URETEMEZ.
    # NOT: uyari STDERR'e gider. `--json` modunda stdout YALNIZ JSON tasimalidir;
    # aksi halde cikti ayristirilamaz (bu regresyon denetimde yakalandi).
    _uyari = ("UYARI SEC-00 CALISTIRILMADI: v4_verify.py bulunamadi — TAM kalip taramasi "
              "KOSMADI. Kalip listesi KOPYALANMAZ (tek kaynak ilkesi). Yolu su uc yoldan "
              "biriyle bildirin: `--v4 <yol>` · `V4_VERIFY_YOLU` ortam degiskeni · "
              "`kod_profil.json` icinde `v4_verify_yolu`.\n"
              "       KISMI MOD: yalniz yapisal gostergeler taranir (gercek .env, ozel "
              "anahtar basligi). Sonuc 'temiz' SAYILMAZ; exit=3 doner.")
    print(_uyari, file=sys.stderr)
    if not JSON_CIK:
        print(_uyari)


def hedef_dosyalar():
    if TUM:
        return [p for p in KOK.rglob("*") if p.is_file() and ".git" not in p.parts]
    # K19 (bu turda olculdu): yalniz `git diff` okumak, EKLENEN (izlenmeyen) bir
    # sir dosyasini HIC gormemek demektir — `src/gizli.pem` fikstürü kanit.
    # `chg_reconcile` ayni bosluğu 24.08'de kapatmisti; burada acik kalmisti.
    yollar, hepsi_ok = [], True
    for komut in (["git", "diff", "--name-only", "HEAD"],
                  ["git", "ls-files", "--others", "--exclude-standard"]):
        r = subprocess.run(komut, cwd=KOK, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            hepsi_ok = False
            print(f"FAIL SEC-00: `{' '.join(komut)}` exit={r.returncode} — "
                  f"tarama CALISTIRILMADI (fail-closed). stderr: {r.stderr.strip()[:200]}")
            continue
        yollar += [x.strip() for x in r.stdout.split("\n") if x.strip()]
    if not hepsi_ok:
        sys.exit(1)
    return [KOK / x for x in dict.fromkeys(yollar)]


# KISMI mod sabitleri — bir "kalip listesi" DEGILDIR, dosya bicimi imzalaridir.
# Kasten DAR tutulmustur: amaci tam taramanin yerini almak degil, tam tarama
# kosmadiginda en tartismasiz iki gostergenin yine de yakalanmasidir.
# Uctan uca kosuda olculdu: ciplak `-----BEGIN ... PRIVATE KEY-----` kalibi
# BU BETIGIN KENDI KAYNAGINI ve oz-test fiksturlerini esliyordu (yanlis pozitif,
# her KFAZ2'yi bloklardi). Cozum: imza SATIR BASINA capalanir ve ardindan
# GERCEK bir govde satiri (base64) gelmesi sarti aranir. Kaynak kodda kalip tek
# satirlik bir dize literali oldugu icin artik eslesmez; gercek anahtar dosyasi
# eslesir.
KISMI_IMZALAR = [
    (r"(?m)^-----BEGIN [A-Z ]*PRIVATE KEY-----[ \t]*\r?\n[A-Za-z0-9+/=]{8,}",
     "ozel anahtar dosyasi (baslik + govde)"),
]
KISMI_IKILI = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".whl",
               ".so", ".dylib", ".class", ".jar", ".ico", ".woff", ".woff2"}

# ---------------------------------------------- O5-02  DERLEME ONBELLEGI (.pyc)
# 24.08.2026 (olculdu): KFAZ3 sonrasi hedef depoda `__pycache__/*.pyc` dosyalari
# IZLENMEYEN durur ve taranir. .pyc bir KAYNAK degil, taranan bir .py'nin
# DERLENMIS KOPYASIDIR: icindeki her dize sabiti zaten .py taramasinda gorulur.
# Ayni sirri IKI KEZ raporlamak gurultudur ve kapiyi bloklar.
#
# SESSIZ MUAFIYET YOKTUR: her .pyc `BILGI SEC-05 ... pyc` satiriyla loga duser
# (O4-04 kalibi).
#
# SINIR (bilerek dar, IKI KOSUL birden): dosya hem `.pyc` uzantili OLACAK hem de
# adi TAM OLARAK `__pycache__` olan bir DIZIN BILESENININ altinda DURACAK.
#
# NEDEN ALT-DIZE DEGIL (O5-05, bagimsiz denetim 24.08.2026 — P0):
# Once yalniz uzantiya bakiliyordu (kokteki `sahte.pyc` muaf oluyordu), sonra
# `"__pycache__/" in rel` diye ALT-DIZE arandi. Ikincisi de delindi: kokteki
# `evil__pycache__/anahtar.pyc` — icinde GERCEK bir PEM ozel anahtar — BILGI
# SEC-05 alip exit=0 dondurdu; ayni yol `chg_reconcile`i de atlatti. Sizinti
# kapisinda yanlis negatif, hem de tek bir dizin adiyla. (Olculdu; bu turda
# yeniden uretildi.) Artik yol bilesenlerine ayrilir ve `__pycache__` TAM
# ESLESME ile aranir; `parts[:-1]` dosya adini disarida birakir.
#
# KALAN RISK (acikca yazilir): GERCEK `__pycache__/` altindaki bir .pyc, kaynagi
# depoda OLMAYAN bir sir tasiyorsa gorulmez. Bu bilincli takastir — .pyc taranan
# bir .py'nin turevidir ve muafiyet her seferinde loglanir.
ONBELLEK_UZANTILARI = {".pyc"}
ONBELLEK_DIZIN_ADI = "__pycache__"


def _onbellek_yolu(rel):
    """`rel` TAM OLARAK `__pycache__` adli bir dizin bileseni altinda mi."""
    return ONBELLEK_DIZIN_ADI in pathlib.PurePosixPath(rel.replace(os.sep, "/")).parts[:-1]
KISMI_DOC_ENV = re.compile(r"(^|/)(\.env\.example|\.env\.sample|\.env\.template)$")

bulgular, notlar, atlanan = [], [], []
for p in hedef_dosyalar():
    if not p.exists() or not p.is_file():
        continue
    rel = os.path.relpath(p, KOK)
    if (not KISMI) and (p.suffix.lower() in v4.SKIP_BINARY_EXT or p.name in v4.LOCK_NAMES):
        atlanan.append(rel); continue
    if KISMI and p.suffix.lower() in KISMI_IKILI:
        atlanan.append(rel); continue
    if p.suffix.lower() in ONBELLEK_UZANTILARI and _onbellek_yolu(rel):
        bulgular.append({"kural": "SEC-05", "siddet": "BILGI", "konum": rel,
                         "tur": "derleme onbellegi (pyc)",
                         "aciklama": "derleme onbellegi (pyc) — kapsam disi sayildi "
                                     "(O5-02); kaynak .py taraniyor"})
        atlanan.append(rel); continue

    # SEC-01: gercek .env  (YAPISAL — kalip listesine bagli degil, KISMI modda da kosar)
    _dokuman = (KISMI_DOC_ENV.search(rel) if KISMI else v4.DOC_ENV_RE.search(rel))
    if p.name == ".env" or (p.name.startswith(".env.") and not _dokuman):
        bulgular.append({"kural": "SEC-01", "siddet": "P0", "konum": rel,
                         "aciklama": "gercek .env dosyasi degisiklige dahil"})

    try:
        metin = p.read_text(errors="ignore")
    except Exception:
        atlanan.append(rel); continue

    if KISMI:
        # Kalip TABANI yok. Yalniz YAPISAL olarak tartismasiz gostergeler:
        # bunlar bir "kalip listesi" degildir, dosya bicimi imzasidir.
        for kalip, neden in KISMI_IMZALAR:
            for m in re.finditer(kalip, metin):
                satir = metin[: m.start()].count("\n") + 1
                bulgular.append({"kural": "SEC-02", "siddet": "P0",
                                 "konum": f"{rel}:{satir}", "tur": neden,
                                 "aciklama": "yapisal sir imzasi (KISMI mod)"})
        continue

    dokuman_env = bool(v4.DOC_ENV_RE.search(rel))
    for kalip, neden in v4.SECRET_PATTERNS:
        for m in re.finditer(kalip, metin):       # D2: ilk eslesmede DURMA
            satir = metin[: m.start()].count("\n") + 1
            konum = f"{rel}:{satir}"
            yer_tutucu = v4.looks_like_placeholder(m.group(0))
            if yer_tutucu or dokuman_env:
                # OTOMATIK INDIRGEME YOK: gorunur kalir, insana birakilir
                bulgular.append({"kural": "SEC-03", "siddet": "P1", "konum": konum, "tur": neden,
                                 "aciklama": "yer tutucu IPUCU var — indirgeme otomatik olamaz, "
                                             "insan karari gerekir"})
            else:
                bulgular.append({"kural": "SEC-02", "siddet": "P0", "konum": konum, "tur": neden,
                                 "aciklama": "sir kalibi eslesti"})

p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
rapor = {"sema": "SECRET-SCAN/v1", "kalip_kaynagi": v4_yol or "YOK (KISMI MOD)",
         "kismi_mod": KISMI,
         "kalip_sayisi": len(KISMI_IMZALAR) if KISMI else len(v4.SECRET_PATTERNS),
         "taranan_kapsam": "tum-agac" if TUM else "git-diff-HEAD",
         "atlanan_dosya": len(atlanan), "p0": p0, "p1": p1, "bulgular": bulgular}

if JSON_CIK:
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
else:
    for b in bulgular:
        print(f"{b['siddet']} {b['kural']} {b['konum']}: {b['aciklama']}")
    if KISMI:
        print(f"SECRET-SCAN KISMI — TAM tarama CALISTIRILMADI · yapisal imza "
              f"{len(KISMI_IMZALAR)} · P0={p0} P1={p1} · atlanan={len(atlanan)}")
        print("       Bu sonuc 'temiz' DEGILDIR. OLCULMEYEN kaydi acilmali.")
    else:
        print(f"SECRET-SCAN {'FAIL' if p0 else 'PASS'} — kalip kaynagi: {v4_yol} "
              f"({len(v4.SECRET_PATTERNS)} kalip) · P0={p0} P1={p1} · atlanan={len(atlanan)}")
# exit: 1 = bulgu var · 3 = KISMI (bulgu yok ama TAM tarama kosmadi) · 0 = temiz
sys.exit(1 if p0 else (3 if KISMI else 0))
