#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kapsam_selftest — kapsam ratchet'inin gercekten kirmizi oldugunu olc.

Test gercek agaci degistirmez. Her senaryo icin deponun gecici bir kopyasi
kurulur ve gercek `make kapsam` / `make kapsam-yaz` girisleri calistirilir:

  1. Yeni bir kural eklenir; testi veya KAPSAM_ISTISNA gerekcesi yoksa
     `make kapsam` sifirdan farkli doner ve kurali adlandirir.
  2. Ayni kurala gerekceli bir KAPSAM_ISTISNA eklenince, tablo yenilendikten
     sonra `make kapsam` PASS olur.
  3. Ayni kurala gercek bir mutasyon vakasi eklenince, vaka `make mutasyon-kisa`
     ile kosar; tablo yenilendikten sonra `make kapsam` PASS olur.
  4. Bir kapi betigine belgelenmemis kod-ici kimlik eklenince `make kapsam`
     kimligi adlandirarak kirmizi doner; ayni kimlige `KOD_ICI_GEREKCE`
     gerekcesi eklenip tablo yenilenince PASS olur. Aile oneki tek basina
     gerekce yerine gecmez; yalniz tam kimlik anahtari kabul edilir.
  5. Kural kimligi olmayan yeni bir kapi betigi siniflandirilmadan eklenirse
     `make kapsam` onu adlandirarak durur.

Kopyalar `.git`, `.venv` ve kanit paketi disarida tutulur; canli agac ve
`docs/MUTASYON_KAPSAM.md` degismeden kalir.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
GECICI_KURAL = "ATLAS_SABLONLAR/scripts/kapsam_negatif_gecici.py"
KOD_ICI_BETIK = "ATLAS_SABLONLAR/scripts/ai_disclosure.py"
GECICI_KOD_ICI = "AI-98"
GECICI_KIMLIKSIZ = "ATLAS_SABLONLAR/scripts/kapsam_kimliksiz_gecici.py"
IGNORE = shutil.ignore_patterns(
    ".git", ".venv", ".venv-token", "kanit-paketi", "__pycache__",
    ".pytest_cache", ".ruff_cache", ".mypy_cache", ".tox",
    "build", "dist", ".DS_Store")


def _kopyala(hedef):
    shutil.copytree(KOK, hedef, ignore=IGNORE, symlinks=True)


def _make(kok, *argumanlar, timeout=600):
    komut = ["make", "-C", str(kok)] + list(argumanlar)
    komut.append("PY=%s" % sys.executable)
    return subprocess.run(komut, cwd=str(kok), capture_output=True, text=True,
                          timeout=timeout)


def _cikti(r):
    return (r.stdout or "") + (r.stderr or "")


def _git_durum():
    r = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=str(KOK), capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else "GIT_YOK"


def _yeni_kural(kok):
    yol = kok / GECICI_KURAL
    yol.write_text(
        "#!/usr/bin/env python3\n"
        "# --- ORN-99 gecici kapsam kurali\n"
        "import sys\n"
        "from pathlib import Path\n"
        "if (Path.cwd() / 'sandbox' / 'orn_ihlal.md').is_file():\n"
        "    print('FAIL ORN-99')\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n",
        encoding="utf-8")


def _kod_ici_ekle(kok):
    """Kapi betigine, envanterde karsiligi olmayan bir kod-ici kimlik ekle."""
    yol = kok / KOD_ICI_BETIK
    metin = yol.read_text(encoding="utf-8")
    if GECICI_KOD_ICI in metin:
        raise RuntimeError("gecici kod-ici kimlik betikte zaten var")
    yol.write_text(
        metin.rstrip() + "\n\n"
        "# kapsam_selftest: asagidaki string literal bilincli olarak "
        "belgelenmemis bir kod-ici kimliktir.\n"
        "KOD_ICI_GECICI = \"%s\"\n" % GECICI_KOD_ICI,
        encoding="utf-8")


def _kimliksiz_ekle(kok):
    """Kural kimligi bildirmeyen gecici bir kapi betigi ekle."""
    yol = kok / GECICI_KIMLIKSIZ
    if yol.exists():
        raise RuntimeError("gecici kimliksiz betik zaten var")
    yol.write_text(
        "#!/usr/bin/env python3\n"
        "# kapsam_selftest: kural kimligi yok; siniflandirma olmadan gecmemeli.\n"
        "print('KAPSAM KIMLIKSIZ GECICI KAPI')\n",
        encoding="utf-8")


def _kimliksiz_kural_ekle(kok):
    """Kimliksiz betigi envanter disi 'kural' diye etiketlemeyi dene."""
    yol = kok / "tools" / "kapsam.py"
    metin = yol.read_text(encoding="utf-8")
    eski = "KIMLIKSIZ_SINIFLAR = {\n"
    yeni = (
        "KIMLIKSIZ_SINIFLAR = {\n"
        "    '%s': ('kural',\n"
        "         'kapsam_selftest: kimliksiz betik kural sayilamaz; "
        "envanter baglantisi yok.'),\n" % GECICI_KIMLIKSIZ)
    if metin.count(eski) != 1:
        raise RuntimeError("KIMLIKSIZ_SINIFLAR baslangici bulunamadi")
    yol.write_text(metin.replace(eski, yeni, 1), encoding="utf-8")


def _kod_ici_onek_gerekce_ekle(kok):
    """Gecici kimlige aile oneki anahtarli, tam olmayan gerekce ekle."""
    yol = kok / "tools" / "kapsam.py"
    metin = yol.read_text(encoding="utf-8")
    eski = "KOD_ICI_GEREKCE = {\n"
    yeni = (
        "KOD_ICI_GEREKCE = {\n"
        "    ('%s', '%s'):\n"
        "        ('tani-kodu',\n"
        "         'aile oneki; tam kimlik olmadigi icin gerekce olamaz.'),\n"
        % (KOD_ICI_BETIK, GECICI_KOD_ICI.split("-", 1)[0]))
    if metin.count(eski) != 1:
        raise RuntimeError("KOD_ICI_GEREKCE baslangici bulunamadi")
    yol.write_text(metin.replace(eski, yeni, 1), encoding="utf-8")


def _kod_ici_gerekce_ekle(kok):
    """Gecici kod-ici kimlige tam (betik, kimlik) ve kaynak gerekcesi ekle."""
    yol = kok / "tools" / "kapsam.py"
    metin = yol.read_text(encoding="utf-8")
    kaynak = kok / KOD_ICI_BETIK
    satir = next(
        (no for no, metin_satiri in enumerate(
            kaynak.read_text(encoding="utf-8").splitlines(), 1)
         if GECICI_KOD_ICI in metin_satiri),
        None,
    )
    if satir is None:
        raise RuntimeError("gecici kod-ici kimlik kaynakta bulunamadi")
    eski = "KOD_ICI_GEREKCE = {\n"
    yeni = (
        "KOD_ICI_GEREKCE = {\n"
        "    ('%s', '%s'):\n"
        "        ('tani-kodu',\n"
        "         'kapsam_selftest: gecici kod-ici kimlik; gercek kapi kurali '\n"
        "         'degil, yalniz tarama davranisini olcmek icin eklendi. '"
        "         'Kaynak: %s:%d.'),\n"
        % (KOD_ICI_BETIK, GECICI_KOD_ICI, KOD_ICI_BETIK, satir))
    if metin.count(eski) != 1:
        raise RuntimeError("KOD_ICI_GEREKCE baslangici bulunamadi")
    yol.write_text(metin.replace(eski, yeni, 1), encoding="utf-8")


def _istisna_ekle(kok):
    yol = kok / "tools" / "kapsam.py"
    eski = "KAPSAM_ISTISNA = {}\n"
    yeni = (
        "KAPSAM_ISTISNA = {\n"
        "    ('%s', 'ORN-99'):\n"
        "        'kapsam_selftest: gecici kural; gercek kapi degil ve '\n"
        "        'mutasyonu yok.',\n"
        "}\n" % GECICI_KURAL)
    metin = yol.read_text(encoding="utf-8")
    if metin.count(eski) != 1:
        raise RuntimeError("KAPSAM_ISTISNA bos sozluk olarak bulunamadi")
    yol.write_text(metin.replace(eski, yeni, 1), encoding="utf-8")


def _vaka_ekle(kok):
    yol = kok / "tools" / "mutasyon_bataryasi.py"
    metin = yol.read_text(encoding="utf-8")
    eski = (
        "        ('OLGU-06', 'ATLAS', 'kanonik DEVIR satiri yok',\n"
        "         'ATLAS_SABLONLAR/scripts/olgu_lint.py',\n"
        "         _olgu_argumanlar, _olgu06, 'OLGU-06',\n"
        "         {'kur': _olgu_hazirla}),\n"
        "    ]\n\n\ndef hazirla")
    yeni = (
        "        ('OLGU-06', 'ATLAS', 'kanonik DEVIR satiri yok',\n"
        "         'ATLAS_SABLONLAR/scripts/olgu_lint.py',\n"
        "         _olgu_argumanlar, _olgu06, 'OLGU-06',\n"
        "         {'kur': _olgu_hazirla}),\n"
        "        ('ORN-99', 'ATLAS', 'gecici kapsam kurali',\n"
        "         '%s',\n"
        "         lambda k: [],\n"
        "         lambda k: yaz(k / 'sandbox' / 'orn_ihlal.md', 'ihlal\\n'),\n"
        "         'ORN-99'),\n"
        "    ]\n\n\ndef hazirla" % GECICI_KURAL)
    if metin.count(eski) != 1:
        raise RuntimeError("vakalar listesinin sonu bulunamadi")
    yol.write_text(metin.replace(eski, yeni, 1), encoding="utf-8")

    eski_kisa = (
        "KISA_VAKALAR = ('KOD-SEC-02', 'ATLAS-PL-10', 'FRZ-08', 'FRZ-08-IMZA',\n"
        "                 'TST-06', 'PL-12')")
    yeni_kisa = (
        "KISA_VAKALAR = ('KOD-SEC-02', 'ATLAS-PL-10', 'FRZ-08', 'FRZ-08-IMZA',\n"
        "                 'TST-06', 'PL-12', 'ORN-99')")
    metin = yol.read_text(encoding="utf-8")
    if metin.count(eski_kisa) != 1:
        raise RuntimeError("KISA_VAKALAR listesi bulunamadi")
    yol.write_text(metin.replace(eski_kisa, yeni_kisa, 1), encoding="utf-8")


def main():
    hatalar = []
    toplam = 0

    def bekle(ad, kosul, ayrinti=""):
        nonlocal toplam
        toplam += 1
        if kosul:
            print("PASS  " + ad)
        else:
            print("FAIL  " + ad)
            if ayrinti:
                print("      " + ayrinti.replace("\n", "\n      ")[-1800:])
            hatalar.append(ad)

    canli_kapsam = (KOK / "docs" / "MUTASYON_KAPSAM.md").read_bytes()
    canli_git = _git_durum()

    with tempfile.TemporaryDirectory(prefix="kapsam-negatif-") as gecici:
        temel = Path(gecici) / "temel"
        _kopyala(temel)

        # 1) Taban: mevcut agac kapsam ratchet'inden gecmeli.
        r = _make(temel, "kapsam")
        bekle("taban kapsam PASS",
              r.returncode == 0 and "KAPSAM: guncel" in _cikti(r), _cikti(r))

        # 2) Yeni kural, test veya istisna yok: ratchet kirmizi.
        vaka = Path(gecici) / "yeni-kural"
        shutil.copytree(temel, vaka, symlinks=True)
        _yeni_kural(vaka)
        r = _make(vaka, "kapsam")
        cikti = _cikti(r)
        bekle("yeni kural kapsam rc!=0", r.returncode != 0, cikti)
        bekle("yeni kural ciktida adlandirilir", "YENI ORN-99" in cikti, cikti)

        # 3) Gerekceli KAPSAM_ISTISNA: tablo yenilenince ratchet yesil.
        vaka = Path(gecici) / "istisna"
        shutil.copytree(temel, vaka, symlinks=True)
        _yeni_kural(vaka)
        _istisna_ekle(vaka)
        r = _make(vaka, "kapsam-yaz")
        bekle("gerekceli istisna kapsam-yaz PASS", r.returncode == 0, _cikti(r))
        r = _make(vaka, "kapsam")
        bekle("gerekceli istisna kapsam PASS",
              r.returncode == 0 and "KAPSAM: guncel" in _cikti(r), _cikti(r))

        # 4) Gercek mutasyon vakasi: vaka kosar, tablo yenilenince ratchet yesil.
        vaka = Path(gecici) / "mutasyon"
        shutil.copytree(temel, vaka, symlinks=True)
        _yeni_kural(vaka)
        _vaka_ekle(vaka)
        r = _make(vaka, "mutasyon-kisa", timeout=600)
        cikti = _cikti(r)
        bekle("gercek mutasyon vakasi GECTI",
              r.returncode == 0 and "ORN-99" in cikti
              and "GECTI" in cikti, cikti)
        r = _make(vaka, "kapsam-yaz")
        bekle("mutasyon sonrasi kapsam-yaz PASS", r.returncode == 0, _cikti(r))
        r = _make(vaka, "kapsam")
        bekle("mutasyon sonrasi kapsam PASS",
              r.returncode == 0 and "KAPSAM: guncel" in _cikti(r), _cikti(r))

        # 5) Kimliksiz yeni kapi siniflandirilmadan gecmez.
        vaka = Path(gecici) / "kimliksiz"
        shutil.copytree(temel, vaka, symlinks=True)
        _kimliksiz_ekle(vaka)
        r = _make(vaka, "kapsam")
        cikti = _cikti(r)
        bekle("kimliksiz betik kapsam rc!=0", r.returncode != 0, cikti)
        bekle("kimliksiz betik adlandirilir",
              GECICI_KIMLIKSIZ in cikti and "KIMLIKSIZ KAPSAM" in cikti,
              cikti)

        # 6) Kimliksiz betik "kural" etiketiyle envanter disi birakilamaz.
        vaka = Path(gecici) / "kimliksiz-kural"
        shutil.copytree(temel, vaka, symlinks=True)
        _kimliksiz_ekle(vaka)
        _kimliksiz_kural_ekle(vaka)
        r = _make(vaka, "kapsam")
        cikti = _cikti(r)
        bekle("kimliksiz kural etiketi rc!=0", r.returncode != 0, cikti)
        bekle("kimliksiz kural etiketi reddedilir",
              "gecersiz sinif" in cikti, cikti)

        # 7) Aile oneki tam kimlik yerine gecmez.
        vaka = Path(gecici) / "kod-ici-onek"
        shutil.copytree(temel, vaka, symlinks=True)
        _kod_ici_ekle(vaka)
        _kod_ici_onek_gerekce_ekle(vaka)
        r = _make(vaka, "kapsam")
        cikti = _cikti(r)
        bekle("aile oneki kod-ici kapsam rc!=0", r.returncode != 0, cikti)
        bekle("aile oneki tam kimlik ister", "TAM kimlik" in cikti, cikti)

        # 8) Kod-ici kimlik: belgelenmemis kimlik kirmizi, gerekceyle yesil.
        vaka = Path(gecici) / "kod-ici"
        shutil.copytree(temel, vaka, symlinks=True)
        _kod_ici_ekle(vaka)
        r = _make(vaka, "kapsam")
        cikti = _cikti(r)
        bekle("belgelenmemis kod-ici kimlik kapsam rc!=0",
              r.returncode != 0, cikti)
        bekle("belgelenmemis kod-ici kimlik adlandirilir",
              GECICI_KOD_ICI in cikti and "belgelenmemis kimlik" in cikti
              and "KOD-ICI KAPSAM" in cikti, cikti)
        _kod_ici_gerekce_ekle(vaka)
        r = _make(vaka, "kapsam-yaz")
        bekle("kod-ici gerekce kapsam-yaz PASS", r.returncode == 0, _cikti(r))
        r = _make(vaka, "kapsam")
        bekle("kod-ici gerekce kapsam PASS",
              r.returncode == 0 and "KAPSAM: guncel" in _cikti(r), _cikti(r))

    bekle("canli kapsam tablosu degismedi",
          (KOK / "docs" / "MUTASYON_KAPSAM.md").read_bytes() == canli_kapsam,
          "canli docs/MUTASYON_KAPSAM.md degisti")
    bekle("canli git durumu degismedi", _git_durum() == canli_git,
          "canli agac test tarafindan degistirildi")

    if hatalar:
        print("\nKAPSAM NEGATIF TEST: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nKAPSAM NEGATIF TEST: PASS — %d/%d" % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
