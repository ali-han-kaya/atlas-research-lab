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
  SEC-06  Kisisel e-posta (guvenli ornek alanlari disinda)                 [P0]
  SEC-07  Git gecmisi tarama hatasi / eksik tarihce                       [P0]

SATIR BOLUNMUS ESLESME: bir sir veya kisisel e-posta satir sonunda
bolunmusse, ard arda 2..3 satir newline olmadan birlestirilerek de taranir.
Bu bir bulgu turudur; ayni kalip tek satirda da eslesiyorsa yinelenmez.
Git gecmisi modu TUM commit'leri, commit/blob nesnelerini ve commit
ustverisini tarar; sig (shallow) klon, okunamayan nesne veya bos tarihce
PASS uretmez.

Kullanim: python3 scripts/secret_scan.py [--diff] [--dizin .] [--json]
  --diff : yalniz `git diff --name-only HEAD` dosyalarini tarar (varsayilan)
  --tum  : calisma agacindaki tum metin dosyalarini tarar
  --git-gecmis : tum ref'lerdeki commit ve blob gecmisini tarar (fail-closed)
"""
import hashlib, importlib.util, json, os, pathlib, re, subprocess, sys

JSON_CIK = "--json" in sys.argv
TUM = "--tum" in sys.argv
GECMIS = "--git-gecmis" in sys.argv
dizin = "."
if "--dizin" in sys.argv:
    i = sys.argv.index("--dizin")
    if i + 1 < len(sys.argv):
        dizin = sys.argv[i + 1]
KOK = pathlib.Path(dizin).resolve()
ARAC_KOK = pathlib.Path(__file__).resolve().parents[2]

# Tam agac taramasinda UCUNCU TARAF agaclarini gezme. Bunlar taranan urunun
# kaynagi degil, kurulumun getirdigi bagimliliklardir; burada bulunan bir ornek
# deponun sizintisi degildir. .git zaten disaridaydi; .venv/node_modules gibi
# agaclar ayni sinifta. KOD'un kendi `tools/secret_fixtures.json` gibi istisna
# kayitlari bu filtreden etkilenmez (onlar birinci taraf agacindadir).
TUM_ATLA_DIZIN = {".git", ".venv", "venv", "node_modules", "site-packages",
                  ".pytest_cache", ".mypy_cache", ".ruff_cache"}

# Fikstur muafiyeti YALNIZ bu iki birinci taraf dosyada ve YALNIZ tam satir
# hash'i eslesirse gecerlidir. Dosya adi tek basina yetmez; desen, uzanti veya
# dizin adiyla toplu muafiyet YOKTUR. Boylece ayni sahte deger baska bir dosyaya
# tasinir ya da ayni satira gercek bir sir eklenirse kapi yine atesler.
FIKSTUR_DOSYALARI = {
    "docs/OLCUM-02-CANLI-KOSU.md",
    "KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_selftest.py",
}
FIKSTUR_DOSYASI = ARAC_KOK / "tools" / "secret_fixtures.json"

def _satir_hash(satir):
    return hashlib.sha256(satir.encode("utf-8")).hexdigest()


def fikstur_kayitlari():
    """(dosya, satir_sha256) -> kayit. Manifest yoksa bos; bozuksa FAIL-CLOSED.

    Manifest TARANAN agactan degil, ARACIN KENDI deposundan okunur. `--dizin`
    ile baska bir depo taranirken hedefin kendi manifestiyle kendini muaf
    tutmasi boylece MUMKUN DEGILDIR. Yalniz KOK == ARAC_KOK iken uygulanir.
    """
    if not FIKSTUR_DOSYASI.is_file() or KOK != ARAC_KOK:
        return {}
    try:
        d = json.loads(FIKSTUR_DOSYASI.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL SEC-00: fikstur manifesti okunamadi: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(d, dict) or not isinstance(d.get("fiksturler"), list):
        print("FAIL SEC-00: fikstur manifesti semasi gecersiz", file=sys.stderr)
        sys.exit(1)
    kayitlar = {}
    for k in d["fiksturler"]:
        if not isinstance(k, dict):
            print("FAIL SEC-00: fikstur kaydi nesne degil", file=sys.stderr)
            sys.exit(1)
        dosya = str(k.get("dosya", "")).replace("\\", "/")
        h = str(k.get("satir_sha256", ""))
        if (dosya not in FIKSTUR_DOSYALARI or
                not re.fullmatch(r"[0-9a-f]{64}", h) or
                not str(k.get("gerekce", "")).strip() or
                not str(k.get("kanit", "")).strip()):
            print(f"FAIL SEC-00: fikstur kaydi gecersiz/izinli dosya disinda: {dosya!r}",
                  file=sys.stderr)
            sys.exit(1)
        if (dosya, h) in kayitlar:
            print(f"FAIL SEC-00: yinelenen fikstur kaydi: {dosya}", file=sys.stderr)
            sys.exit(1)
        kayitlar[(dosya, h)] = k
    return kayitlar


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
        if getattr(m, "SECRET_PATTERNS", None):
            return m, str(a)
    return None, None


v4, v4_yol = v4_yukle()
KISMI = v4 is None
FIKSTUR = {} if KISMI else fikstur_kayitlari()
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
        return [p for p in KOK.rglob("*")
                if p.is_file()
                and not any(x in TUM_ATLA_DIZIN for x in p.relative_to(KOK).parts[:-1])]
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


# --------------------------------------------------------------- ORTAK TARAMA
# Satir bolunmus bir sir, iki ayri satirin newline ile ayrilmis halidir. Kalip
# tek basina satirlarda eslesmez; ancak parcalar newline olmadan birlestirilince
# eslesir. Pencereyi kasten kisa tutuyoruz: butun dosyayi newline'siz birlestirmek
# ilgisiz iki satiri birbirine yapistirip yanlis pozitif uretir.
SATIR_PENCERESI = 3
EPOSTA_KALIBI = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# Bunlar gercek bir kisiye ait olmayan, belgelenmis ornek/robot adresleridir.
# `.invalid`, `.test` ve `.localhost` RFC 2606/6761 geregi cozulmez; burada
# kullanilanlar test fiksturudur, gercek bir hesaba isaret etmez.
GUVENLI_EPOSTA_TAM = {
    "noreply@example.com",
    "noreply@codebuff.com",
    "git@github.com",
    "noreply@github.com",
}
GUVENLI_EPOSTA_ALANLARI = {
    "example.com", "example.org", "example.net",
    "users.noreply.github.com",
}
GUVENLI_EPOSTA_SONEKLERI = (
    ".example.com", ".example.org", ".example.net",
    ".invalid", ".test", ".localhost",
)


def _eposta_guvenli(adres):
    """Ornek/robot/test adresi mi? Kisisel adresler burada True OLMAZ."""
    adres = str(adres).strip().lower().rstrip(".")
    if adres in GUVENLI_EPOSTA_TAM:
        return True
    if "@" not in adres:
        return False
    alan = adres.rsplit("@", 1)[1]
    if alan in GUVENLI_EPOSTA_ALANLARI:
        return True
    return any(alan.endswith(son) for son in GUVENLI_EPOSTA_SONEKLERI)


def _satir_araligi_muaf(rel, satirlar, bas, son):
    """Bir eslesmenin degdigi BUTUN satirlar tam-hash fiksturu mu?"""
    rel = str(rel).replace("\\", "/")
    if not FIKSTUR or rel not in FIKSTUR_DOSYALARI:
        return False
    if bas < 1 or son < bas or son > len(satirlar):
        return False
    for i in range(bas - 1, son):
        if (rel, _satir_hash(satirlar[i])) not in FIKSTUR:
            return False
    return True


def _blob_muaf(yollar, satirlar, bas, son):
    """Ayni blob birden fazla yolda ise hepsi muaf olmadan susturma yok."""
    if not yollar:
        return False
    return all(_satir_araligi_muaf(y, satirlar, bas, son) for y in yollar)


def _sir_ham(metin, satirlar):
    """Sir kaliplarini tek metinde ve 2..3 satirlik pencerelerde bul.

    Donus: (bas_satir, son_satir, neden, bolunmus, eslesme). Eslesme yalniz
    yer tutucu notu icin kullanilir; rapora ASLA yazilmaz. Ayni eslesme hem
    tam metinde hem pencerede bulunursa pencere kopyasi eklenmez.
    """
    kayitlar, gorulen = [], set()

    def ekle(bas, son, neden, bolunmus, eslesme):
        # Ayni satir araliginda tam metin ve bolunmus pencere eslesmesi
        # birlikte olusabilir; ikinci kaydi ayni bulgu saymamak icin anahtar
        # `bolunmus` alanini icermez.
        anahtar = (bas, son, neden)
        if anahtar in gorulen:
            return
        gorulen.add(anahtar)
        kayitlar.append((bas, son, neden, bolunmus, eslesme))

    for kalip, neden in v4.SECRET_PATTERNS:
        kalip_re = re.compile(kalip)
        for m in kalip_re.finditer(metin):
            bas = metin.count("\n", 0, m.start()) + 1
            son = metin.count("\n", 0, m.end()) + 1
            ekle(bas, son, neden, False, m.group(0))
        for n in range(2, SATIR_PENCERESI + 1):
            for i in range(0, len(satirlar) - n + 1):
                parcalar = satirlar[i:i + n]
                if any(kalip_re.search(x) for x in parcalar):
                    continue
                birlesik = "".join(parcalar)
                m = kalip_re.search(birlesik)
                if m:
                    ekle(i + 1, i + n, neden, True, m.group(0))
    return kayitlar


def _pii_ham(satirlar):
    """Kisisel e-posta adaylarini tek satir ve bolunmus pencerelerde bul."""
    kayitlar, gorulen = [], set()

    def ekle(bas, son):
        if (bas, son) not in gorulen:
            gorulen.add((bas, son))
            kayitlar.append((bas, son))

    for i, satir in enumerate(satirlar):
        if any(not _eposta_guvenli(m.group(0))
               for m in EPOSTA_KALIBI.finditer(satir)):
            ekle(i + 1, i + 1)
    for n in range(2, SATIR_PENCERESI + 1):
        for i in range(0, len(satirlar) - n + 1):
            parcalar = satirlar[i:i + n]
            if any(not _eposta_guvenli(m.group(0))
                   for x in parcalar for m in EPOSTA_KALIBI.finditer(x)):
                continue
            for m in EPOSTA_KALIBI.finditer("".join(parcalar)):
                if not _eposta_guvenli(m.group(0)):
                    ekle(i + 1, i + n)
                    break
    return kayitlar


def _git_calistir(argumanlar, veri=None):
    """Git komutunu calistir; rc!=0 veya zaman asimi fail-closed'dir."""
    try:
        r = subprocess.run(["git"] + argumanlar, cwd=str(KOK), input=veri,
                           capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError("git calistirilamadi: %s" % str(e)[:160])
    if r.returncode != 0:
        hata = (r.stderr or b"").decode("utf-8", "replace").strip()[:180]
        raise RuntimeError("git %s exit=%d%s" % (
            " ".join(argumanlar), r.returncode, (": " + hata) if hata else ""))
    return r.stdout


def _gecmis_nesneleri():
    """Tum ref'lerdeki nesneleri ve yol eslemelerini oku; hata = istisna."""
    shallow = _git_calistir(["rev-parse", "--is-shallow-repository"])
    if shallow.decode("utf-8", "replace").strip().lower() == "true":
        raise RuntimeError("sig (shallow) klon: tum gecmis yerelde yok")

    ham = _git_calistir(["rev-list", "--all", "--objects"])
    if not ham.strip():
        raise RuntimeError("ref/commit yok: taranacak git gecmisi bulunamadi")
    sira, yollar = [], {}
    for satir in ham.decode("utf-8", "replace").splitlines():
        parca = satir.split(" ", 1)
        sha = parca[0].strip()
        if not sha:
            continue
        if sha not in yollar:
            sira.append(sha)
            yollar[sha] = []
        if len(parca) == 2 and parca[1]:
            yollar[sha].append(parca[1])
    # rev-list tag nesnesini her zaman listelemez; tag mesajindaki e-posta da
    # gecmisin parcasi oldugu icin refs/tags nesnelerini ayrica ekle.
    for satir in _git_calistir(["for-each-ref", "--format=%(objectname)",
                                "refs/tags"]).decode("utf-8", "replace").splitlines():
        sha = satir.strip()
        if sha and sha not in yollar:
            sira.append(sha)
            yollar[sha] = []

    cevap = _git_calistir(["cat-file", "--batch"],
                          ("\n".join(sira) + "\n").encode("utf-8"))
    nesneler, konum = [], 0
    for sha in sira:
        nl = cevap.find(b"\n", konum)
        if nl < 0:
            raise RuntimeError("cat-file basligi eksik")
        baslik = cevap[konum:nl]
        konum = nl + 1
        parca = baslik.split()
        if len(parca) == 2 and parca[1] == b"missing":
            raise RuntimeError("nesne okunamadi: %s" % sha[:12])
        if len(parca) < 3:
            raise RuntimeError("cat-file basligi gecersiz: %s" % sha[:12])
        try:
            boyut = int(parca[2])
        except ValueError:
            raise RuntimeError("cat-file boyutu gecersiz: %s" % sha[:12])
        if boyut < 0 or konum + boyut > len(cevap):
            raise RuntimeError("cat-file govdesi eksik: %s" % sha[:12])
        icerik = cevap[konum:konum + boyut]
        konum += boyut
        if konum < len(cevap) and cevap[konum:konum + 1] == b"\n":
            konum += 1
        nesneler.append((sha, parca[1].decode("utf-8", "replace"), icerik,
                         yollar.get(sha, [])))
    if konum != len(cevap):
        raise RuntimeError("cat-file ciktisinda artan veri var")
    return nesneler


def _ikili_mi(yollar, icerik):
    if b"\x00" in icerik:
        return True
    if not yollar:
        return False
    return all(pathlib.PurePosixPath(y).suffix.lower() in v4.SKIP_BINARY_EXT
               for y in yollar)


def _gecmis_tara():
    """Tum ref'lerdeki commit/blob/commit-ustverisi taramasini yurut."""
    bulgular, atlanan = [], 0
    fikstur_muaf = 0
    commit_sayisi = blob_sayisi = 0

    def ekle(kural, konum, tur, aciklama):
        bulgular.append({"kural": kural, "siddet": "P0", "konum": konum,
                         "tur": tur, "aciklama": aciklama})

    try:
        nesneler = _gecmis_nesneleri()
        for sha, tur, icerik, yollar in nesneler:
            if tur == "blob":
                blob_sayisi += 1
                if _ikili_mi(yollar, icerik):
                    atlanan += 1
                    bulgular.append({"kural": "SEC-04", "siddet": "BILGI",
                                     "konum": (yollar[0] if yollar else "blob/" + sha[:12]),
                                     "tur": "ikili nesne",
                                     "aciklama": "ikili blob atlandi — icerik taranmadi"})
                    continue
                metin = icerik.decode("utf-8", "ignore")
                satirlar = metin.splitlines()
                for bas, son, neden, bolunmus, _es in _sir_ham(metin, satirlar):
                    if _blob_muaf(yollar, satirlar, bas, son):
                        fikstur_muaf += 1
                        continue
                    konum = "%s:%d%s" % (
                        (yollar[0] if yollar else "blob/" + sha[:12]), bas,
                        ("-%d" % son) if son > bas else "")
                    ekle("SEC-02", konum, neden,
                         "sir kalibi eslesti" + (" (satir bolunmus)" if bolunmus else ""))
                for bas, son in _pii_ham(satirlar):
                    konum = "%s:%d%s" % (
                        (yollar[0] if yollar else "blob/" + sha[:12]), bas,
                        ("-%d" % son) if son > bas else "")
                    ekle("SEC-06", konum, "kisisel e-posta",
                         "guvenli ornek/robot alani olmayan e-posta")
            elif tur in ("commit", "tag"):
                if tur == "commit":
                    commit_sayisi += 1
                metin = icerik.decode("utf-8", "ignore")
                satirlar = metin.splitlines()
                for bas, son, neden, bolunmus, _es in _sir_ham(metin, satirlar):
                    konum = "%s/%s:%d%s" % (tur, sha[:12], bas,
                                             ("-%d" % son) if son > bas else "")
                    ekle("SEC-02", konum, neden,
                         "commit ustverisinde sir kalibi" +
                         (" (satir bolunmus)" if bolunmus else ""))
                for bas, son in _pii_ham(satirlar):
                    konum = "%s/%s:%d%s" % (tur, sha[:12], bas,
                                             ("-%d" % son) if son > bas else "")
                    ekle("SEC-06", konum, "kisisel e-posta",
                         "commit ustverisinde guvenli olmayan e-posta")
    except Exception as e:
        print("FAIL SEC-07: git gecmisi taranamadi: %s" % str(e)[:240],
              file=sys.stderr)
        return 1

    p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
    rapor = {
        "sema": "SECRET-SCAN/v1", "kalip_kaynagi": v4_yol or "YOK",
        "kismi_mod": False, "kalip_sayisi": len(v4.SECRET_PATTERNS),
        "taranan_kapsam": "git-gecmis", "commit_sayisi": commit_sayisi,
        "blob_sayisi": blob_sayisi, "atlanan_dosya": atlanan,
        "fikstur_muafiyeti": fikstur_muaf, "p0": p0, "p1": 0,
        "bulgular": bulgular,
    }
    if JSON_CIK:
        print(json.dumps(rapor, ensure_ascii=False, indent=2))
    else:
        for b in bulgular:
            print("%s %s %s: %s" % (b["siddet"], b["kural"], b["konum"],
                                      b["aciklama"]))
        print("SECRET-SCAN GECMIS %s — commit=%d blob=%d · P0=%d · "
              "atlanan=%d · fikstur=%d" %
              ("FAIL" if p0 else "PASS", commit_sayisi, blob_sayisi, p0,
               atlanan, fikstur_muaf))
    return 1 if p0 else 0


if GECMIS:
    if KISMI:
        print("SECRET-SCAN GECMIS KISMI — kalip tabani yok; tam tarama yapilmadi",
              file=sys.stderr)
        sys.exit(3)
    sys.exit(_gecmis_tara())


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

bulgular, notlar, atlanan, fikstur_muaf = [], [], [], []
for p in hedef_dosyalar():
    if not p.exists() or not p.is_file():
        continue
    rel = os.path.relpath(p, KOK)
    # SEC-04: atlama SESSIZ DEGIL. Ikili/kilit dosyasi taranmadi bilgisi hem
    # insan ciktisina hem JSON bulgularina duser; P0/P1 sayacina GIRMEZ.
    if (not KISMI) and (p.suffix.lower() in v4.SKIP_BINARY_EXT or p.name in v4.LOCK_NAMES):
        bulgular.append({"kural": "SEC-04", "siddet": "BILGI", "konum": rel,
                         "tur": "ikili/kilit dosyasi",
                         "aciklama": "ikili/kilit dosyasi atlandi — icerik taranmadi "
                                     "(bilgi; P0/P1 degil)"})
        atlanan.append(rel); continue
    if KISMI and p.suffix.lower() in KISMI_IKILI:
        bulgular.append({"kural": "SEC-04", "siddet": "BILGI", "konum": rel,
                         "tur": "ikili dosya (KISMI)",
                         "aciklama": "ikili dosya atlandi — TAM kalip taramasi "
                                     "yapilmadi (bilgi; P0/P1 degil)"})
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

    satirlar = metin.splitlines()
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
    sir_konumlari = set()
    for kalip, neden in v4.SECRET_PATTERNS:
        for m in re.finditer(kalip, metin):       # D2: ilk eslesmede DURMA
            satir = metin[: m.start()].count("\n") + 1
            konum = f"{rel}:{satir}"
            _h = _satir_hash(satirlar[satir - 1]) if 0 < satir <= len(satirlar) else ""
            if (rel.replace("\\", "/"), _h) in FIKSTUR:
                fikstur_muaf.append(konum)
                continue
            sir_konumlari.add((satir, neden))
            yer_tutucu = v4.looks_like_placeholder(m.group(0))
            if yer_tutucu or dokuman_env:
                # OTOMATIK INDIRGEME YOK: gorunur kalir, insana birakilir
                bulgular.append({"kural": "SEC-03", "siddet": "P1", "konum": konum, "tur": neden,
                                 "aciklama": "yer tutucu IPUCU var — indirgeme otomatik olamaz, "
                                             "insan karari gerekir"})
            else:
                bulgular.append({"kural": "SEC-02", "siddet": "P0", "konum": konum, "tur": neden,
                                 "aciklama": "sir kalibi eslesti"})

    # Bolunmus fikstur: iki/uc satira yayilmis bir sir, tek satirda eslesmez.
    # Satirlar newline olmadan birlestirilir; yalniz TEK satirda eslesmeyen
    # pencereler raporlanir ki ayni bulgu iki kez sayilmasin.
    for n in range(2, SATIR_PENCERESI + 1):
        for i in range(0, len(satirlar) - n + 1):
            parcalar = satirlar[i:i + n]
            for kalip, neden in v4.SECRET_PATTERNS:
                kalip_re = re.compile(kalip)
                if any(kalip_re.search(x) for x in parcalar):
                    continue
                m = kalip_re.search("".join(parcalar))
                if not m:
                    continue
                bas, son = i + 1, i + n
                if (bas, neden) in sir_konumlari:
                    continue
                if _satir_araligi_muaf(rel, satirlar, bas, son):
                    fikstur_muaf.append(f"{rel}:{bas}-{son}")
                    continue
                konum = f"{rel}:{bas}-{son}"
                yer_tutucu = v4.looks_like_placeholder(m.group(0))
                if yer_tutucu or dokuman_env:
                    bulgular.append({"kural": "SEC-03", "siddet": "P1", "konum": konum,
                                     "tur": neden,
                                     "aciklama": "satir bolunmus eslesme; yer tutucu/ belge "
                                                 "ipucu var — insan karari gerekir"})
                else:
                    bulgular.append({"kural": "SEC-02", "siddet": "P0", "konum": konum,
                                     "tur": neden,
                                     "aciklama": "satir bolunmus sir kalibi eslesti"})

    # Kisisel e-posta: guvenli ornek/robot alanlari disinda P0. Adresin kendisi
    # rapora yazilmaz; yalniz konum ve kural gorunur.
    for bas, son in _pii_ham(satirlar):
        konum = f"{rel}:{bas}" + (f"-{son}" if son > bas else "")
        bulgular.append({"kural": "SEC-06", "siddet": "P0", "konum": konum,
                         "tur": "kisisel e-posta",
                         "aciklama": "guvenli ornek/robot alani olmayan e-posta"})

p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
rapor = {"sema": "SECRET-SCAN/v1", "kalip_kaynagi": v4_yol or "YOK (KISMI MOD)",
         "kismi_mod": KISMI,
         "kalip_sayisi": len(KISMI_IMZALAR) if KISMI else len(v4.SECRET_PATTERNS),
         "taranan_kapsam": "tum-agac" if TUM else "git-diff-HEAD",
         "haric_dizinler": sorted(TUM_ATLA_DIZIN) if TUM else [],
         "atlanan_dosya": len(atlanan), "fikstur_muafiyeti": len(fikstur_muaf),
         "p0": p0, "p1": p1, "bulgular": bulgular}

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
              f"({len(v4.SECRET_PATTERNS)} kalip) · P0={p0} P1={p1} · "
              f"atlanan={len(atlanan)} · fikstur={len(fikstur_muaf)}")
# exit: 1 = bulgu var · 3 = KISMI (bulgu yok ama TAM tarama kosmadi) · 0 = temiz
sys.exit(1 if p0 else (3 if KISMI else 0))
