#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutasyon_bataryasi — yayimlanan kapilarin GERCEKTEN atesledigini olcer.

NEDEN VAR
  Bir kapi "PASS" diyorsa, o kapinin tanimli sozlesmesini uyguladigi ayri bir
  olcumle gosterilmelidir. Aksi halde yesil, kapinin degil girdinin ozelligidir.
  Bu betik her vaka icin once TEMIZ TABAN alir (hedef bulgu tabanda YOKTUR), sonra
  ayni kopyada tek bir ihlal uretir. Hata vakasinda kapi rc!=0 vermeli ve yalniz
  hedef kural kimligini basmalidir; beklenen-bulgu vakasinda rc=0 olabilir, ama
  hedef uyari/bulgu isareti mutasyon sonrasi ciktida BULUNMALIDIR. Temiz taban ve
  sozlesme birlikte saglanmadan vaka GECMEZ.

NE OLCMEZ
  Model cagirmaz, ag kullanmaz, gercek makale uretmez. Olctugu sey kapi
  betiginin kendi kararidir; kapsam disi olan sey raporda yazilidir.

KULLANIM
  python3 tools/mutasyon_bataryasi.py [--ayrintili] [--kisa]

  --kisa : tum batarya degil, HATA/TERMINAL/BEKLENEN_BULGU sozlesmelerini
           temsil eden sabit 6 vakalik hizli duman setini kosar. Bu set tam
           batarya yerine gecmez; taze-klon kurulum kontrolu icindir.

CIKIS
  0  : butun vakalar sozlesmesini sagladi (taban sessiz; hata rc!=0 veya
       beklenen-bulgu isaretli)
  1  : en az bir vaka ateslemedi / taban kirlendi / mutasyon uygulanamadi
"""
import datetime
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
MUTASYON_KATALOG = KOK / 'tools' / 'mutasyon_katalog.json'
GERCEK_KATALOG = KOK / 'tools' / 'model_katalog.json'
# MOD-04/05 fiksturlerinin kullandigi kimlikler. Gercek katalogdan bir kimlik
# duserse batarya ESKI kimlikle kosmaya devam etmemeli: asagidaki tutarlilik
# kontrolu her kosuda fail-closed calisir.
MOD_FIKSTUR_KIMLIKLERI = (
    'anthropic/claude-opus-5',
    'deepseek/deepseek-v4-flash',
    'z-ai/glm-5.2',
)
# check_models sabit katalogu kullanir (ag/canli models.dev gerekmez).
os.environ.setdefault('ATLAS_MODEL_KATALOG', str(MUTASYON_KATALOG))
AYRINTILI = '--ayrintili' in sys.argv
KISA = '--kisa' in sys.argv
KISA_VAKALAR = ('KOD-SEC-02', 'ATLAS-PL-10', 'FRZ-08', 'FRZ-08-IMZA',
                 'TST-06', 'PL-12')
ATLA = shutil.ignore_patterns('.git', '__pycache__', 'node_modules', '.pytest_cache',
                              '.ruff_cache', '.mypy_cache', '.tox', '.venv', 'venv',
                              'build', 'dist', '.DS_Store')

# Ayrik sozlesmeler: her vaka tek bir sozlesmeye baglidir. HATA rc=1 ister;
# TERMINAL rc=2 + GATE_TAMPERED/TERMINAL FAIL ister; BEKLENEN_BULGU yalniz
# hedef bulgu isaretini ister (rc=0 veya rc=1 olabilir). Beklenen bulgu,
# kirmizi ates sayisina dahil edilmez.
SOZLESME_HATA = 'HATA'
SOZLESME_TERMINAL = 'TERMINAL'
SOZLESME_BULGU = 'BEKLENEN_BULGU'
SOZLESMELER = frozenset({SOZLESME_HATA, SOZLESME_TERMINAL, SOZLESME_BULGU})

# Anahtar PARCALI yazilir: bu dosya depoda durur ve sir tarayicisi (H4) bitisik
# deseni yakalar. Parcali literal tarayiciyi yaniltmak icin degil, gercek bir
# anahtarin depoya sizmasini onlemek icin boyle: fikstur oldugu gorunur.
SAHTE_ANAHTAR = 'AKIA' + 'Z7Q2M4XK9PLR3TWV'

DEC_BASLIKLAR = ['Etik Kurul', 'Cikar Catismasi', 'Finansman', 'credit',
                 'Veri Erisilebilirligi', 'Yapay Zeka']
# Yalniz REC ailesi: "tek ihlal -> yalniz hedef FAIL etiketi" ve "ihlali geri al
# -> yeniden yesil" sozlesmesini her kosuda zorunlu kilar.
FAIL_ETIKET = re.compile(r'\bFAIL\s+([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})\b')
# iz degerinden izinli kural kimlikleri turetilirken kullanilir.
KIMLIK_ARAMA = re.compile(r'[A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3}')
ONEK_ARAMA = re.compile(r'[A-Z]{2,8}-\Z')

# Genel kontroller HER vakada aciktir (varsayilan). Case bazinda yalniz
# kapatilabilir; kapatma gerekcesi vaka kaydindaki opsiyonda gorunur.
VARSAYILAN_YALNIZ = True
VARSAYILAN_KONTROL = True


def kontrol_yedek(kok):
    """Geri-alma yedegi: depo kopyasinin TAMAMI (kardes fiksturler dahil).

    Bazi vakalar fiksturu depo kopyasinin YANINA kurar (or. PL-19 icin
    `kok.parent/sandbox_pl19`). Yalniz `kok`u yedeklemek o dosyalari geri
    almaz ve kontrol yanlislikla kirmizi kalirdi.
    """
    yedek = Path(tempfile.mkdtemp(prefix='atlas_mut_kontrol_'))
    kopya = yedek / 'kopya'
    shutil.copytree(kok.parent, kopya, symlinks=True)
    return yedek, kopya


def kontrol_geri(kok, yedek, kopya):
    """Ihlali geri al: gecici calisma agacini yedekten aynen kur."""
    shutil.rmtree(kok.parent)
    shutil.copytree(kopya, kok.parent, symlinks=True)
    shutil.rmtree(yedek, ignore_errors=True)


def izinli_etiketler(iz):
    """`iz`den izinli kural etiketleri kumesini turet.

    - somut kimlik ('REC-05')  -> {'REC-05'}
    - tuple ('FRZ-01','FRZ-02') -> iki kimlik
    - onek ('SEC-')             -> ONEK modu; bu onekle baslayan her etiket
    - etiketsiz ('FAIL — ikili') -> bos kume (kapi kural kimligi basmiyor)
    """
    parcalar = [iz] if isinstance(iz, str) else list(iz)
    onekler = tuple(p for p in parcalar
                    if isinstance(p, str) and ONEK_ARAMA.match(p))
    if onekler:
        return 'ONEK', onekler
    kume = set()
    for p in parcalar:
        if isinstance(p, str):
            kume.update(KIMLIK_ARAMA.findall(p))
    return 'KUME', frozenset(kume)


def sizan_etiketler(iz, cikti):
    """Ciktida gecen ama `iz`in izin verdigi kumenin disinda kalan FAIL etiketleri."""
    tur, kume = izinli_etiketler(iz)
    etiketler = set(FAIL_ETIKET.findall(cikti))
    if tur == 'ONEK':
        return sorted(e for e in etiketler if not e.startswith(kume))
    return sorted(etiketler - set(kume))
REC_KONTROL = {'kontrol': True, 'yalniz': True}


def kos(komut, cwd=None, env=None):
    r = subprocess.run([str(k) for k in komut], cwd=str(cwd or KOK), env=env,
                       capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding='utf-8')


def ekle(kok, rel, metin):
    """Mutasyon: dosyanin sonuna ekle. Hedef yoksa HATA dondurur."""
    yol = kok / rel
    if not yol.is_file():
        return 'HATA: hedef yok: %s' % rel
    with yol.open('a', encoding='utf-8') as f:
        f.write(metin)
    return None


def degistir(kok, rel, eski, yeni):
    """Mutasyon: TAM bir metin parcasini degistir (tek eslesme sarti)."""
    yol = kok / rel
    if not yol.is_file():
        return 'HATA: hedef yok: %s' % rel
    metin = yol.read_text(encoding='utf-8')
    adet = metin.count(eski)
    if adet != 1:
        return 'HATA: %s icinde desen %d kez gecti (1 bekleniyordu)' % (rel, adet)
    yol.write_text(metin.replace(eski, yeni, 1), encoding='utf-8')
    return None


def dec_govde(basliklar):
    return '# Makale\n\n' + '\n\n'.join('## %s\n\nBeyan metni.' % b for b in basliklar) + '\n'


# --- saf ayristirici fiksturleri (ag/model/imza/tarihce/git gerektirmez) ------
REC_FAZ1 = ('{"findings": [{"id": "F-001", "priority": "P0"}, '
            '{"id": "F-002", "priority": "P1"}]}\n')
REC_MANIFEST = (
    '# manifest\n\n| FIX-ID | Severity | Kategori | Bulgu | Durum | Kanit |\n'
    '|---|---|---|---|---|---|\n'
    '| FIX-001 | P0 | A | F-001 | UYGULANMI\u015e | SC-001 |\n'
    '| FIX-002 | P1 | B | F-002 | UYGULANMI\u015e | SC-002 |\n')
REC_MASTER = '# MASTER\n\nFIX-001 ve FIX-002 uyguland\u0131.\n'
REC_GATE2B = ('{"manifest_reconciliation": ['
              '{"fix_id": "FIX-001", "status": "UYGULANMIS_KANITLI"}, '
              '{"fix_id": "FIX-002", "status": "UYGULANMIS_KANITLI"}]}\n')

SINIF_MD = (
    '# Makale\n\n## PROVENANCE\n\n'
    '| SCOPE-ID | Bolum | Kaynak | Satir Referansi | Kaynak Sinifi | Durum |\n'
    '|---|---|---|---|---|---|\n'
    '| SC-001 | Giris | K | 1 | BIRINCIL | kapsandi |\n'
    '| SC-002 | Yontem | K | 2 | IKINCIL | kapsandi |\n')

# SRC-01 tablo fiksturu bataryadan ayrildi: temiz taban ve bozuk varyant
# ayni izlenen dosyadan uretilir. Tek ihlal, MAKALE'nin sinifini degistirir;
# KAYNAK SINIFLANDIRMA tablosu degismeden kalir.
SRC01_FIKSTUR = 'tools/src01_kaynak_siniflandirma_fiksturu.md'
SRC01_SANDBOX = 'sandbox/sinif_src01.md'
SRC01_BOZUK_ESKI = '| SC-002 | Yontem | MAKALE | 2 | IKINCIL | kapsandi |'
SRC01_BOZUK_YENI = '| SC-002 | Yontem | MAKALE | 2 | BIRINCIL | kapsandi |'

# teslim_imza.py'nin ZORUNLU listesiyle ayni olmali. Liste betikte degisirse
# temiz taban TSL-06 ile kirilir; fikstur sessizce eski listeye bagli kalmaz.
TESLIM_ZORUNLU = [
    '00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md',
    '01-FAZ-1-LENS-ANALYSIS.json',
    '02-FAZ-2-FIX-MANIFEST.md',
    '03-FAZ-3-MASTER-v5.5.md',
    '04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md',
    'gate/STRONG-gate-2a-v5.5.json',
    'gate/STRONG-gate-2b-v5.5.json',
    'gate/FINAL-GATE-v5.5.json',
]

JUNIT_TST5 = ('<?xml version="1.0"?><testsuite tests="5" failures="0" errors="0" '
              'skipped="0"></testsuite>')
JUNIT_TST2 = ('<?xml version="1.0"?><testsuite tests="2" failures="0" errors="0" '
              'skipped="0"></testsuite>')
JUNIT_TST5_FAIL = ('<?xml version="1.0"?><testsuite tests="5" failures="1" errors="0" '
                   'skipped="0"></testsuite>')
JUNIT_TST5_ERROR = ('<?xml version="1.0"?><testsuite tests="5" failures="0" errors="1" '
                    'skipped="0"></testsuite>')
JUNIT_TST0 = ('<?xml version="1.0"?><testsuite tests="0" failures="0" errors="0" '
              'skipped="0"></testsuite>')
JUNIT_TST5_SKIP = ('<?xml version="1.0"?><testsuite tests="6" failures="0" errors="0" '
                   'skipped="1"></testsuite>')

SCOPE_TR = '# SCOPE\n\nTransliterasyon sistemi: DMG (DIN 31635).\n'
METIN_TR = '# Makale\n\nMetinde sek\u00eene terimi bir kez ge\u00e7er.\n'

CITE_MD = ('# Makale\n\nGovde metni (Yazar, 2020).\n\n## Kaynakca\n\n'
           '- Yazar, A. (2020). Kitap. Yayin.\n')

PL_MD = ('---\ndescription: uyari testi\nmode: subagent\n---\n\n'
         'CALISTIRILMADI. python3 scripts/mevcut.py cikis kodunu denetler.\n')

# PL-19 icin izole sema fiksturu: gercek prompt agacini ve symlink'lerini
# taramadan yalniz bir prompt + bir hedef sema kurulur. Gerekli alan
# eksiltmek kirmizi, semada olmayan alan eklemek uyaridir; ikisi karistirilmaz.
PL19_SCHEMA = {
    "$defs": {
        "main": {
            "type": "object",
            "required": ["schema", "run_id", "input_sha256"],
            "properties": {
                "schema": {"type": "string"},
                "run_id": {"type": "string"},
                "input_sha256": {"type": "string"},
            },
        }
    }
}
PL19_MD = ('---\ndescription: PL-19 izole sema testi\nmode: subagent\n---\n\n'
           'CALISTIRILMADI.\n\n```json\n'
           '{\n  "schema": "ATLAS-TEST/v1",\n  "run_id": "run-test-001",\n'
           '  "input_sha256": "sha256:test"\n}\n```\n')
PERM_MD = ('---\ndescription: izin testi\nmode: subagent\npermission:\n'
           '  read:\n    "*": allow\n  edit:\n    "*": allow\n'
           '  bash:\n    "*": allow\n---\n\nCALISTIRILMADI\n')
QR_BASE = ('# Baslik\n\n' + ('Bu govde metni oran olcumunu dengelemek icin '
           'yeterince uzun tutulmustur ve alinti icermez. ' * 8) + '\n')
QR_MUT = ('# Baslik\n\n' + ('"Bu uzun bir alinti metnidir ve oran esigini asar."\n\n'
          'Kisa govde.\n'))
QR_DENGE = ('# Baslik\n\n' + ('Bu govde metni oran olcumunu dengelemek icin '
            'yeterince uzun tutulmustur ve alinti icermez. ' * 8) +
            'Bu metinde tek bir " isaret var.\n')
SEC_ORNEK = ('api_key = "sk-' + 'test-AbCdEfGhIjKlMnOpQrStUvWxYz012345"\n')

DEC_MD = ('# Makale\n\n'
          '## Etik Kurul\n\nGerekmedi; gerekce: insan katilimci yok.\n\n'
          '## Cikar Catismasi\n\nYok.\n\n'
          '## Finansman\n\nYok.\n\n'
          '## Yazar Katkisi\n\nTek yazar.\n\n'
          '## Veri Erisilebilirligi\n\nYok.\n\n'
          '## Yapay Zeka\n\nKullanilmadi.\n\n'
          '## DPIA\n\nKisisel veri islenmedi.\n')


def qr_govde(uzun_mu):
    # 40+ kelime ESIGI gercek sayimla gecilir; sayi uydurulmaz (ATLAS kapisi da
    # kelime sayar). Uzunluk calisirken olculur, yorumda iddia edilmez.
    if uzun_mu:
        alinti = ('Bu paragraf kirk kelimelik esigi asan bir alintinin nasil '
                  'gorundugunu olcmek icin yazilmistir ve gercekten uzun bir '
                  'alintidir; boylece kapi uzun alinti uclusunu denetlemek zorunda '
                  'kalir ve sayfa numarasi verilmedigi icin kirmizi yanmasi '
                  'gerekir, cunku ucuncu unsur eksiktir ve bu eksiklik sessiz '
                  'gecilmemelidir.')
        atif = '(Kaya, 2020).'
    else:
        alinti = 'Kisa bir alinti.'
        atif = '(Kaya, 2020, s. 12).'
    return ('# Makale\n\nGovde metni burada baslar.\n\n'
            '"%s" %s\n\n## Kaynakca\n\nKaya, A. (2020). Deneme.\n' % (alinti, atif))


def _sozlesme_etiketi(deger):
    """Bir vaka etiketini/opsiyonunu sabit sozlesme adina cevir."""
    if not isinstance(deger, str):
        raise SystemExit('SOZLESME: etiket metin olmali: %r' % (deger,))
    anahtar = deger.strip().upper().replace('-', '_').replace(' ', '_')
    takma = {
        'HATA': SOZLESME_HATA,
        'TERMINAL': SOZLESME_TERMINAL,
        'BULGU': SOZLESME_BULGU,
        'BEKLENEN_BULGU': SOZLESME_BULGU,
        'BEKLENEN': SOZLESME_BULGU,
    }
    if anahtar not in takma:
        raise SystemExit('SOZLESME: bilinmeyen etiket %r (gecerli: %s)'
                         % (deger, ', '.join(sorted(SOZLESMELER))))
    return takma[anahtar]


def vaka_sozlesmesi(vaka):
    """(sozlesme, opsiyon) dondur; eski BULGU/terminal kayitlari da okunur.

    Yeni kayitlar `{'sozlesme': SOZLESME_*}` ile acikca etiketlenebilir. Eski
    `BULGU` konumu ve `terminal=True` alanlari geriye donuk uyumluluk icin
    ayni sabitlere cevrilir; ayni vakada celiskili iki etiket kabul edilmez.
    """
    if not isinstance(vaka, (tuple, list)) or len(vaka) < 7:
        raise SystemExit('SOZLESME: eksik vaka kaydi: %r' % (vaka,))
    etiket = None
    opsiyon = {}
    if len(vaka) > 7:
        if isinstance(vaka[7], str):
            etiket = _sozlesme_etiketi(vaka[7])
            if len(vaka) > 8:
                if not isinstance(vaka[8], dict):
                    raise SystemExit('SOZLESME: opsiyon sozluk olmali: %r' % (vaka,))
                opsiyon = vaka[8]
        elif isinstance(vaka[7], dict):
            opsiyon = vaka[7]
            if len(vaka) > 8:
                raise SystemExit('SOZLESME: fazla vaka alani: %r' % (vaka,))
        else:
            raise SystemExit('SOZLESME: gecersiz vaka etiketi: %r' % (vaka,))
    acik = opsiyon.get('sozlesme')
    if acik is not None:
        acik = _sozlesme_etiketi(acik)
        if etiket is not None and etiket != acik:
            raise SystemExit('SOZLESME: celiskili etiketler: %s / %s'
                             % (etiket, acik))
        etiket = acik
    if etiket is None:
        etiket = SOZLESME_TERMINAL if opsiyon.get('terminal') else SOZLESME_HATA
    if opsiyon.get('terminal') and etiket != SOZLESME_TERMINAL:
        raise SystemExit('SOZLESME: terminal=True ile %s birlikte olamaz' % etiket)
    return etiket, opsiyon


def taban_ve_mutasyon(kok, kapi, argumanlar, mutasyon, iz, taban_rc=0, cwd=None,
                      terminal=False, env=None, kontrol=VARSAYILAN_KONTROL,
                      yalniz=VARSAYILAN_YALNIZ, taban_bilgi=None):
    """(durum, ayrinti) dondurur. taban_rc: temiz kopyada beklenen cikis kodu.

    `iz` bir dize veya dize dizisi olabilir; hepsi mutasyon ciktisinda aranir.
    terminal=True ise temiz tabanda GATE_TAMPERED/TERMINAL izi BULUNMAZ, mutasyon
    sonrasi rc=2, `GATE_TAMPERED` ve `TERMINAL FAIL` birlikte aranir; yalniz
    kirmizi yanmak terminal sozlesmesini kanitlamaz.
    taban_bilgi: temiz tabanda yalniz `BILGI ... IMZALI` satirinda gorunmesi
    beklenen kural; gecerli imzali taban bu bilgi satirini uretir, terminal
    sozlesmesini ihlal etmez. Diger her gorunum hala TABAN_KIRLI sayilir.
    kontrol=True ise ihlal uygulandiktan sonra fikstur yedekten geri yuklenir ve
    ayni kapi tekrar kosulur: rc=taban_rc ve FAIL etiketi yok. Boylece vaka
    "her mutasyonda kirmizi" olan vacuous bir test degildir.
    yalniz=True ise mutasyon ciktisindaki FAIL etiketleri tam olarak `iz` olmali;
    baska bir kuralin FAIL etiketi sizarsa vaka yanlis etiketlenmistir.
    """
    betik = kok / kapi
    if not betik.is_file():
        return 'EKSIK', 'kapi betigi yok: %s' % kapi

    izler = [iz] if isinstance(iz, str) else list(iz)
    komut = [sys.executable, betik] + argumanlar(kok)
    calisma = cwd or kok
    yedek = None
    yedek = kopya = None
    if kontrol:
        yedek, kopya = kontrol_yedek(kok)

    rc0, o0 = kos(komut, cwd=calisma, env=env)
    if rc0 != taban_rc:
        return 'TABAN_KIRIK', 'taban rc=%d (beklenen %d) · %s' % (
            rc0, taban_rc, o0.strip().splitlines()[-1] if o0.strip() else '')
    if yalniz and FAIL_ETIKET.findall(o0):
        return 'TABAN_KIRLI', 'temiz tabanda FAIL etiketi var: %s' % (
            ', '.join(sorted(set(FAIL_ETIKET.findall(o0)))))
    if terminal:
        yasak = ('GATE_TAMPERED', 'TERMINAL FAIL') + tuple(izler)
        if taban_bilgi and any(
                taban_bilgi in satir and 'BILGI' in satir and 'IMZALI' in satir
                for satir in o0.splitlines()):
            # Gecerli imzali taban, kendi BILGI satirini uretir; bu bir ihlal degil.
            yasak = tuple(x for x in yasak if x != taban_bilgi)
        if any(x in o0 for x in yasak):
            return 'TABAN_KIRLI', 'temiz tabanda terminal/iz bulgusu var: %s' % (
                o0.strip().splitlines()[-1] if o0.strip() else 'bos cikti')

    hata = mutasyon(kok)
    if hata:
        return 'MUTASYON_UYGULANMADI', hata

    rc1, o1 = kos(komut, cwd=calisma, env=env)
    if terminal:
        if rc1 != 2:
            return 'ATESLEMEDI', 'mutasyon rc=%d (terminal icin 2 bekleniyordu)' % rc1
        eksik = [x for x in ('GATE_TAMPERED', 'TERMINAL FAIL') if x not in o1]
        if eksik:
            return 'ATESLEMEDI', 'rc=2 ama terminal izi eksik: %s' % ', '.join(eksik)
    elif rc1 == 0:
        return 'ATESLEMEDI', 'mutasyon sonrasi rc=0 (kapi kirmiziya donmedi)'
    eksik_iz = [x for x in izler if x not in o1]
    if eksik_iz:
        return 'ATESLEMEDI', 'rc=%d ama beklenen iz(ler) (%s) ciktida yok' % (
            rc1, ', '.join(eksik_iz))
    if yalniz:
        diger = sizan_etiketler(iz, o1)
        if diger:
            return 'ATESLEMEDI', 'baska kural etiketi sizdi: %s' % ', '.join(diger)

    if kontrol:
        kontrol_geri(kok, yedek, kopya)
        rc2, o2 = kos(komut, cwd=calisma, env=env)
        if rc2 != taban_rc:
            return 'KONTROL_KIRMIZI', 'kontrol rc=%d (beklenen %d) · %s' % (
                rc2, taban_rc, o2.strip().splitlines()[-1] if o2.strip() else '')
        if yalniz and FAIL_ETIKET.findall(o2):
            return 'KONTROL_KIRMIZI', 'kontrol ciktisinda FAIL etiketi var: %s' % (
                ', '.join(sorted(set(FAIL_ETIKET.findall(o2)))))
        if terminal and any(x in o2 for x in ('GATE_TAMPERED', 'TERMINAL FAIL')):
            return 'KONTROL_KIRMIZI', 'kontrol ciktisinda terminal izi var'

    if terminal:
        return 'GECTI-TERMINAL', (
            'taban rc=0 · FAIL iz yok · mutasyon rc=2 · '
            'GATE_TAMPERED+TERMINAL · FAIL iz=%s (yalniz) · '
            'kontrol rc=0 · FAIL iz yok' % '+'.join(izler))
    if kontrol:
        return 'GECTI', ('taban rc=0 · FAIL iz yok · mutasyon rc=%d · '
                         'FAIL iz=%s (yalniz) · kontrol rc=0 · FAIL iz yok' % (
                             rc1, '+'.join(izler)))
    return 'GECTI', 'taban rc=0 · mutasyon rc=%d · iz=%s' % (rc1, '+'.join(izler))


def taban_ve_terminal(kok, kapi, argumanlar, mutasyon, iz, **kwargs):
    """Ayrik terminal sozlesmesi: rc=2 ve iki terminal izi birlikte aranir."""
    kwargs.pop('terminal', None)
    return taban_ve_mutasyon(kok, kapi, argumanlar, mutasyon, iz,
                             terminal=True, **kwargs)


def _sha(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def _json_duzenle(k, rel, fn):
    p = k / rel
    veri = json.loads(p.read_text(encoding='utf-8'))
    fn(veri)
    p.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return None


def _frz06(k):
    return _json_duzenle(k, '_KOSU/gate/BASELINE.json',
                         lambda v: v.pop('scripts_sha256', None))


def _frz07(k):
    return _json_duzenle(k, '_KOSU/gate/BASELINE.json',
                         lambda v: v.__setitem__('temiz_agac', False))


def _frz08_hazirla(k):
    """FRZ-08: temiz tabanda imza iddiasi YOK; imza kontrolu sessiz kalir."""
    return _json_duzenle(k, '_KOSU/gate/BASELINE.json',
                         lambda v: (v.pop('temiz_agac', None),
                                    v.pop('temiz_agac_imzasi', None)))


def _frz08(k):
    """Tek ihlal: temiz_agac:true + gecersiz imza; anahtar ortamda var."""
    return _json_duzenle(k, '_KOSU/gate/BASELINE.json',
                         lambda v: (v.__setitem__('temiz_agac', True),
                                    v.__setitem__('temiz_agac_imzasi', '0' * 64)))


def _frz08_env():
    # Anahtar yalniz bu vaka icin ortamda; depoya yazilmaz.
    return dict(os.environ, LAB_IMZA_ANAHTARI='a' * 64)


def _frz08_imza_hazirla(k):
    """FRZ-08 imzali taban: gecerli HMAC uret, temiz tabani imzala."""
    taban = k / '_KOSU' / 'gate' / 'BASELINE.json'
    sonuc = subprocess.run(
        [sys.executable, str(k / 'KOD_SABLONLAR' / 'scripts' / 'imzala.py'),
         '--taban', str(taban)],
        cwd=str(k), env=_frz08_env(), capture_output=True, text=True, timeout=120)
    if sonuc.returncode != 0:
        raise RuntimeError('FRZ-08 imza hazirlanamadi: %s' % (
            (sonuc.stdout + sonuc.stderr).strip() or 'rc=%d' % sonuc.returncode))
    veri = json.loads(taban.read_text(encoding='utf-8'))
    if not veri.get('temiz_agac_imzasi'):
        raise RuntimeError('FRZ-08 imza hazirlanamadi: imza alani yok')
    return None


def _frz08_imza(k):
    """Imzali tabanin icerigini sonradan degistir; eski imza uyusmaz."""
    return _json_duzenle(k, '_KOSU/gate/BASELINE.json',
                         lambda v: v.__setitem__('imza_kurcalama', True))


def _frz08_yanlis_anahtar(k):
    """Tek ihlal: gecerli taban imzasini FARKLI bir anahtarla yeniden hesapla.

    Bozuk bir imza dizesinden farkli olarak bu imza bicimsel olarak gecerlidir;
    yalniz anahtar uyusmaz. Boylece kapi, imzayi yalniz uzunluk/karakter
    kontrolunden gecirmekle yetinmedigini de kanitlar.
    """
    taban = k / '_KOSU' / 'gate' / 'BASELINE.json'
    veri = json.loads(taban.read_text(encoding='utf-8'))
    kanonik = json.dumps({a: b for a, b in veri.items() if a != 'temiz_agac_imzasi'},
                         sort_keys=True, ensure_ascii=False,
                         separators=(',', ':')).encode('utf-8')
    imza = hmac.new(bytes.fromhex('b' * 64), kanonik, hashlib.sha256).hexdigest()
    return _json_duzenle(k, '_KOSU/gate/BASELINE.json',
                         lambda v: v.__setitem__('temiz_agac_imzasi', imza))


def _frz08_p1(k):
    """Tek ihlal: temiz_agac:true, imza YOK; P1 DUSUK_GUVEN."""
    return _json_duzenle(k, '_KOSU/gate/BASELINE.json',
                         lambda v: v.__setitem__('temiz_agac', True))


def _frz01_kayip(k):
    """FRZ-01 kayip dali: profil dosyasi silinir; terminal GATE_TAMPERED."""
    (k / 'kod_profil.json').unlink()
    return None


def _frz02_kayip(k):
    """FRZ-02 kayip dali: dondurulmus kapi betigi silinir; terminal GATE_TAMPERED."""
    (k / 'scripts' / 'kapi.py').unlink()
    return None


def _dep01_hazirla(k):
    """DEP-01: manifest + kilit dosyasi birlikte var; taban sessiz."""
    yaz(k / 'bagimlilik-manifest.txt', 'requests==2.32.0\n')
    yaz(k / 'bagimlilik-kilit.txt', 'requests==2.32.0\n')
    return _json_duzenle(k, 'kod_profil.json', lambda v: (
        v.__setitem__('bagimlilik_manifesti', ['bagimlilik-manifest.txt']),
        v.__setitem__('kilit_dosyasi', ['bagimlilik-kilit.txt'])))


def _dep01(k):
    """Tek ihlal: kilit_dosyasi anahtari profilden silinir."""
    return _json_duzenle(k, 'kod_profil.json',
                         lambda v: v.pop('kilit_dosyasi', None))


def _teslim_hazirla(k, imzala=False):
    """8 zorunlu artefakt + kapi betiginin kendi --uret manifesti.

    imzala=True ise sabit test anahtari yalniz bu alt surece verilir; depoya
    yazilmaz. Boylece TSL-04 temiz tabani gercekten gecerli bir imza tasir.
    """
    sandbox = k / 'sandbox_teslim'
    for ad in TESLIM_ZORUNLU:
        yaz(sandbox / ad, '# artefakt\n')
    env = dict(os.environ)
    if imzala:
        env['LAB_IMZA_ANAHTARI'] = 'a' * 64
    r = subprocess.run(
        [sys.executable, str(k / 'ATLAS_SABLONLAR' / 'scripts' / 'teslim_imza.py'),
         '--uret'], cwd=str(sandbox), capture_output=True, text=True, timeout=120,
        env=env)
    if r.returncode != 0:
        # Taban TSL-01/TSL-06 ile kirilir; sessizce yesil kalmasin.
        yaz(sandbox / 'URETIM-HATASI.txt',
            (r.stdout or '') + (r.stderr or '') + '\n')


def _tsl03_hazirla(k):
    return _teslim_hazirla(k, imzala=False)


def _tsl04_hazirla(k):
    return _teslim_hazirla(k, imzala=True)


def _tsl03(k):
    """Tek ihlal: manifest uretildikten sonra bir artefakt degistirilir."""
    yaz(k / 'sandbox_teslim' / '03-FAZ-3-MASTER-v5.5.md', '# artefakt degisti\n')


def _tsl04(k):
    """Tek ihlal: gecerli imzanin ilk hanesi bozulur."""
    return _json_duzenle(
        k, 'sandbox_teslim/TESLIM-MANIFEST.json',
        lambda v: v.__setitem__(
            'imza', ('0' if v['imza'][0] != '0' else '1') + v['imza'][1:]))


def _tsl06(k):
    """Tek ihlal: manifestten zorunlu bir artefakt kaydi cikarilir."""
    return _json_duzenle(
        k, 'sandbox_teslim/TESLIM-MANIFEST.json',
        lambda v: v['dosyalar'].pop('04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md'))


def _sil(k, rel):
    """Tek ihlal: hedef dosyayi sil; yoksa HATA dondur."""
    p = k / rel
    if not p.is_file():
        return 'HATA: hedef yok: %s' % rel
    p.unlink()
    return None


def _git_komut(k, *args):
    """Gecici depo icin kimlik enjekte edilmis git cagrisi."""
    r = subprocess.run(
        ['git', '-C', str(k), '-c', 'user.name=Atlas Test',
         '-c', 'user.email=test@example.invalid', *args],
        capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError('git %s: %s' % (
            ' '.join(args), (r.stderr or r.stdout).strip()[:200]))
    return r


def _dep_hazirla(k):
    """DEP-03/04/06: gecici git deposu + manifest/kilit cifti."""
    sandbox = k / 'sandbox_dep'
    yaz(sandbox / 'bagimlilik-manifest.txt', 'requests==2.32.0\n')
    yaz(sandbox / 'bagimlilik-kilit.txt', 'requests==2.32.0\n')
    yaz(sandbox / 'kod_profil.json', json.dumps({
        'profil': 'test',
        'bagimlilik_manifesti': ['bagimlilik-manifest.txt'],
        'kilit_dosyasi': ['bagimlilik-kilit.txt'],
    }, ensure_ascii=False, indent=2) + '\n')
    _git_komut(sandbox, 'init', '-q')
    _git_komut(sandbox, 'add', '-A')
    _git_komut(sandbox, 'commit', '-qm', 'DEP tabani')


def _dep_argumanlar(k):
    return ['--profil', str(k / 'sandbox_dep' / 'kod_profil.json')]


def _dep03(k):
    return ekle(k, 'sandbox_dep/bagimlilik-manifest.txt', 'flask==latest\n')


def _dep04(k):
    return ekle(k, 'sandbox_dep/bagimlilik-kilit.txt', '# lock bump\n')


def _dep06(k):
    return _json_duzenle(
        k, 'sandbox_dep/kod_profil.json',
        lambda v: v.__setitem__('bagimlilik_manifesti', []))


def _tsl01(k):
    return _sil(k, 'sandbox_teslim/TESLIM-MANIFEST.json')


def _tsl02(k):
    return _sil(k, 'sandbox_teslim/03-FAZ-3-MASTER-v5.5.md')


def _tsl05(k):
    return _json_duzenle(
        k, 'sandbox_teslim/TESLIM-MANIFEST.json',
        lambda v: v.pop('imza', None))


def _api_hazirla(k, t2=False):
    sandbox = k / 'sandbox_api'
    yaz(sandbox / 'kaynak.py',
        'def foo():\n    return 1\n\ndef bar():\n    return 2\n')
    yaz(sandbox / 'imza-envanter.txt', 'foo\nbar\n')
    profil = {'profil': 'test'}
    if not t2:
        profil['imza_komutu'] = 'cat imza-envanter.txt'
    yaz(sandbox / 'kod_profil.json',
        json.dumps(profil, ensure_ascii=False, indent=2) + '\n')
    yaz(sandbox / '_KOSU' / 'gate' / 'BASELINE.json',
        json.dumps({'dis_imza': ['foo', 'bar']},
                   ensure_ascii=False, indent=2) + '\n')


def _api04_hazirla(k):
    return _api_hazirla(k, t2=True)


def _api_argumanlar(k):
    return ['--profil', str(k / 'sandbox_api' / 'kod_profil.json'),
            '--taban', str(k / 'sandbox_api' / '_KOSU' / 'gate' /
                           'BASELINE.json')]


def _api01(k):
    return _json_duzenle(
        k, 'sandbox_api/_KOSU/gate/BASELINE.json',
        lambda v: v.pop('dis_imza', None))


def _api02(k):
    return _json_duzenle(
        k, 'sandbox_api/_KOSU/gate/BASELINE.json',
        lambda v: v['dis_imza'].append('kayip'))


def _api04(k):
    return degistir(k, 'sandbox_api/kaynak.py', 'def foo():', 'def baz():')


def _api05(k):
    return _json_duzenle(
        k, 'sandbox_api/kod_profil.json',
        lambda v: v.__setitem__('imza_komutu', 'false'))


def _ozt_taban(kimlikler):
    return {
        'sema': 'OZTEST-TABAN/v1',
        'sayi': len(kimlikler),
        'kimlikler': list(kimlikler),
        'kimlik_hash': 'sha256:' + hashlib.sha256(
            '\n'.join(sorted(kimlikler)).encode('utf-8')).hexdigest(),
    }


def _ozt_hazirla(k):
    sandbox = k / 'sandbox_ozt'
    yaz(sandbox / 'OZTEST-TABAN.json',
        json.dumps(_ozt_taban(['AA-1', 'BB-1']),
                   ensure_ascii=False, indent=2) + '\n')
    yaz(sandbox / 'cikti.txt',
        '  OK   AA-1: gecti\n  OK   BB-1: gecti\n')


def _ozt_argumanlar(k):
    return ['--cikti', str(k / 'sandbox_ozt' / 'cikti.txt'),
            '--taban', str(k / 'sandbox_ozt' / 'OZTEST-TABAN.json')]


def _ozt01(k):
    return _sil(k, 'sandbox_ozt/OZTEST-TABAN.json')


def _ozt02(k):
    yaz(k / 'sandbox_ozt' / 'cikti.txt', '  OK   BB-1: gecti\n')


def _ozt03(k):
    yaz(k / 'sandbox_ozt' / 'cikti.txt', '')


def _ozt05(k):
    return ekle(k, 'sandbox_ozt/cikti.txt', '  OK   CC-1: gecti\n')


def _ozt06(k):
    return _json_duzenle(
        k, 'sandbox_ozt/OZTEST-TABAN.json',
        lambda v: v.__setitem__('kimlik_hash', 'sha256:' + '0' * 64))


def _olgu_hazirla(k):
    """OLGU-04/05/06: tek commit'li gecici depo + taze attestation."""
    _git_komut(k, 'init', '-q')
    _git_komut(k, 'add', '-A')
    _git_komut(k, 'commit', '-qm', 'OLGU tabani')
    r = subprocess.run(
        [sys.executable, str(k / 'tools' / 'kanit.py'), '--paketsiz'],
        cwd=str(k), capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError('OLGU attestation uretilemedi: %s' % (
            (r.stdout or '') + (r.stderr or '')).strip()[:300])
    metin = (k / 'docs' / 'OLGULAR.md').read_text(encoding='utf-8')
    m = re.search(
        r'<!-- OLGULAR_JSON_BASLA -->\s*```json\s*(\{.*?\})\s*```\s*'
        r'<!-- OLGULAR_JSON_BITIR -->', metin, re.DOTALL)
    if not m:
        raise RuntimeError('OLGU fiksturu: OLGULAR JSON blogu okunamadi')
    v = json.loads(m.group(1))
    out = k / 'sandbox_olgu'
    yaz(out / 'atlas-cikti.txt',
        'OZ-TEST: %d/%d gecti\n' % (v['atlas_son_gecen'],
                                    v['atlas_envanter_sayisi']))
    yaz(out / 'kod-cikti.txt',
        'KOD OZ-TEST: %d/%d gecti\n' % (v['kod_son_gecen'],
                                        v['kod_son_gecen']))
    yaz(out / 'attest-cikti.json', json.dumps({
        'sema': 'OZTEST-ATTEST/v1',
        'canli_sayi': v['attest_canli'],
        'taban_sayi': v['attest_taban'],
        'p0': v['attest_p0'],
        'p1': v['attest_p1'],
    }, ensure_ascii=False, indent=2) + '\n')


def _olgu_argumanlar(k):
    return ['--kok', str(k), '--git-kok', str(k)]


def _olgu05_argumanlar(k):
    return _olgu_argumanlar(k) + [
        '--atlas-cikti', str(k / 'sandbox_olgu' / 'atlas-cikti.txt'),
        '--attest-cikti', str(k / 'sandbox_olgu' / 'attest-cikti.json'),
        '--kod-cikti', str(k / 'sandbox_olgu' / 'kod-cikti.txt'),
    ]


def _olgu04(k):
    return _sil(k, 'attestation.json')


def _olgu05(k):
    p = k / 'sandbox_olgu' / 'atlas-cikti.txt'
    metin = p.read_text(encoding='utf-8')
    m = re.search(r'OZ-TEST: (\d+)/(\d+)', metin)
    if not m:
        return 'HATA: atlas-cikti ozeti yok'
    eski = m.group(0)
    yeni = 'OZ-TEST: %d/%s' % (int(m.group(1)) - 1, m.group(2))
    p.write_text(metin.replace(eski, yeni, 1), encoding='utf-8')
    return None


def _olgu06(k):
    p = k / 'SURUM.md'
    metin = p.read_text(encoding='utf-8')
    yeni = re.sub(r'^Kanonik OLGU-06 DEVIR:.*\n', '', metin,
                  flags=re.MULTILINE)
    if yeni == metin:
        return 'HATA: SURUM.md kanonik DEVIR satiri yok'
    p.write_text(yeni, encoding='utf-8')
    try:
        _git_komut(k, 'add', 'SURUM.md')
        _git_komut(k, 'commit', '-qm', 'OLGU-06 mutasyonu')
        r = subprocess.run(
            [sys.executable, str(k / 'tools' / 'kanit.py'), '--paketsiz'],
            cwd=str(k), capture_output=True, text=True, timeout=300)
    except RuntimeError as e:
        return 'HATA: %s' % e
    if r.returncode != 0:
        return 'HATA: attestation yenilenemedi: %s' % (
            (r.stdout or '') + (r.stderr or '')).strip()[:200]
    return None


def _frz01_02(k):
    """Tek ihlal: profil ve kapi betigi birlikte degistirilir (FRZ-01+FRZ-02)."""
    hata = degistir(k, 'kod_profil.json', '{"profil": "test"}\n',
                    '{"profil": "degisti"}\n')
    if hata:
        return hata
    return degistir(k, 'scripts/kapi.py', '# test kapi betigi\n',
                    '# degistirilmis kapi\n')


def _src01_fikstur(kok, bozuk=False):
    """Izlenen SRC-01 fiksturunden temiz veya tek-ihlalli metni uretir."""
    yol = kok / SRC01_FIKSTUR
    if not yol.is_file():
        raise FileNotFoundError('SRC-01 fiksturu yok: %s' % SRC01_FIKSTUR)
    metin = yol.read_text(encoding='utf-8')
    if not bozuk:
        return metin
    adet = metin.count(SRC01_BOZUK_ESKI)
    if adet != 1:
        raise ValueError('SRC-01 fiksturunde mutasyon satiri %d kez gecti '
                         '(1 bekleniyordu)' % adet)
    return metin.replace(SRC01_BOZUK_ESKI, SRC01_BOZUK_YENI, 1)


def _src01(k):
    """Tek ihlal: fiksturden turetilen bozuk surumu yaz."""
    try:
        yaz(k / SRC01_SANDBOX, _src01_fikstur(k, bozuk=True))
    except (OSError, ValueError) as e:
        return 'HATA: %s' % e
    return None


def _git_kur(d):
    """Kucuk fikstur deposu: git diff tabanli kapilar icin tek commit."""
    for komut in (['git', 'init', '-q', '.'], ['git', 'add', '-A'],
                  ['git', '-c', 'user.email=t@t', '-c', 'user.name=t',
                   'commit', '-qm', 'taban']):
        subprocess.run(komut, cwd=str(d), capture_output=True, text=True, timeout=120)


def _reck_hazirla(k):
    """RECK-01/02/03/04/06: KFAZ0/1/2 makine bloklari + temiz kucuk git deposu."""
    kosu = k / 'sandbox_reck' / '_KOSU'
    yaz(kosu / '00-KFAZ-0-SPEC.md', '# spec\n\n```json\n' + json.dumps({
        'sema': 'KFAZ0/v1',
        'req': [{'id': 'REQ-001', 'tur': 'yapisal', 'kabul': 'x'}],
    }, ensure_ascii=False) + '\n```\n')
    yaz(kosu / '01-KFAZ-1-PLAN.md', '# plan\n\n```json\n' + json.dumps({
        'sema': 'KFAZ1/v1',
        'degisecek': ['src/eski.py'],
        'dondurulan': ['dondurulan.md'],
        'req_test': {'REQ-001': []},
    }, ensure_ascii=False) + '\n```\n')
    yaz(kosu / 'gate' / 'BASELINE.json',
        json.dumps({'test_adlari': []}, ensure_ascii=False, indent=2) + '\n')
    depo = k / 'sandbox_reck' / 'gitdepo'
    yaz(depo / 'src' / 'eski.py', 'x = 1\n')
    yaz(depo / 'dondurulan.md', '# dondurulmus bolge\n')
    _git_kur(depo)


def _reck_plan_hazirla(k):
    """RECK-01/02/04: planli, henuz uygulanmamis tek CHG + bos 2B raporu."""
    _reck_hazirla(k)
    kosu = k / 'sandbox_reck' / '_KOSU'
    yaz(kosu / '02-KFAZ-2-MANIFEST.md', '# manifest\n\n```json\n' + json.dumps({
        'sema': 'KFAZ2/v1',
        'chg': [{'id': 'CHG-001', 'dosya': 'src/eski.py',
                 'durum': 'PLANLANDI', 'req': 'REQ-001'}],
    }, ensure_ascii=False) + '\n```\n')
    # Bos rapor: RECK-04 temiz tabanda sessiz kalsin; mutasyon tek iddia ekler.
    yaz(kosu / 'gate' / 'KOD-gate-2b.json',
        json.dumps({'manifest_reconciliation': []}, ensure_ascii=False) + '\n')


def _md_json_duzenle(k, rel, fn):
    """Markdown icindeki ```json blogunu duzenler; blogu YENIDEN yazar."""
    p = k / rel
    metin = p.read_text(encoding='utf-8')
    m = re.search(r'```json\s*(\{.*?\})\s*```', metin, re.S)
    if not m:
        return 'HATA: %s icinde json blogu yok' % rel
    veri = json.loads(m.group(1))
    fn(veri)
    yeni = json.dumps(veri, ensure_ascii=False, indent=2)
    p.write_text(metin[:m.start(1)] + yeni + metin[m.end(1):], encoding='utf-8')
    return None


def _reck01(k):
    """Tek ihlal: KFAZ0'daki REQ-001 planin req_test eslemesinden cikarilir."""
    return _md_json_duzenle(k, 'sandbox_reck/_KOSU/01-KFAZ-1-PLAN.md',
                            lambda v: v.__setitem__('req_test', {}))


def _reck02(k):
    """Tek ihlal: CHG-001 PLANLANDI -> UYGULANMIS; dosya diff'te yok."""
    return _md_json_duzenle(k, 'sandbox_reck/_KOSU/02-KFAZ-2-MANIFEST.md',
                            lambda v: v['chg'][0].__setitem__('durum', 'UYGULANMIS'))


def _reck04(k):
    """Tek ihlal: 2B, diff'te olmayan CHG-001 icin KANITLI der."""
    return yaz(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'KOD-gate-2b.json',
               json.dumps({'manifest_reconciliation': [
                   {'chg_id': 'CHG-001', 'status': 'KANITLI'}]},
                   ensure_ascii=False) + '\n')


def _reck05(k):
    """Tek ihlal: CHG-001, KFAZ0'da olmayan REQ-999'a baglanir."""
    return _md_json_duzenle(k, 'sandbox_reck/_KOSU/02-KFAZ-2-MANIFEST.md',
                            lambda v: v['chg'][0].__setitem__('req', 'REQ-999'))


def _reck03(k):
    return yaz(k / 'sandbox_reck' / 'gitdepo' / 'src' / 'plansiz.py', 'y = 1\n')


def _reck06(k):
    """Tek ihlal: KFAZ1 planinda dondurulan dosya degistirilir."""
    return yaz(k / 'sandbox_reck' / 'gitdepo' / 'dondurulan.md', '# bozulmus bolge\n')


def _reck09_hazirla(k):
    """RECK-09: KFAZ0 var, KFAZ1 plani henuz yok; temiz agacta diff bos."""
    _reck_hazirla(k)
    (k / 'sandbox_reck' / '_KOSU' / '01-KFAZ-1-PLAN.md').unlink()
    return None


def _reck09(k):
    """Tek ihlal: plan yokken URUN kodu eklenir."""
    return yaz(k / 'sandbox_reck' / 'gitdepo' / 'src' / 'plansiz.py', 'y = 1\n')


def _tst08(k):
    """Tek ihlal: kanit JSON'undan ham rapor baglantisi cikarilir."""
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: v.pop('rapor', None))


def _tst07(k):
    """Tek ihlal: beyan basarisiz=1 der; ham JUnit 0 basarisizdir."""
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: v['sonuc'].__setitem__('basarisiz', 1))


def _tst09(k):
    """Tek ihlal: kanittan test komutunun cikis kodu silinir."""
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: v.pop('cikis_kodu', None))


def _tst01(k):
    """Tek ihlal: ham JUnit 1 basarisiz test der; beyan da ayni gercegi soyler."""
    yaz(k / 'sandbox_tst' / 'gate' / 'junit.xml', JUNIT_TST5_FAIL)
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: (v['sonuc'].__setitem__('basarisiz', 1),
                                    v.__setitem__('cikis_kodu', 1)))


def _tst02(k):
    """Tek ihlal: ham JUnit 1 hatali test der; beyan da ayni gercegi soyler."""
    yaz(k / 'sandbox_tst' / 'gate' / 'junit.xml', JUNIT_TST5_ERROR)
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: (v['sonuc'].__setitem__('hata', 1),
                                    v.__setitem__('cikis_kodu', 1)))


def _tst_zero_hazirla(k):
    """TST-03: taban kosan=0; boylece sifir-test ihlali TST-04'u tetiklemez."""
    _tst_hazirla(k)
    return _json_duzenle(k, 'sandbox_tst/gate/BASELINE.json',
                         lambda v: v['test'].__setitem__('kosan', 0))


def _tst03(k):
    """Tek ihlal: ham JUnit sifir test der; beyan da sifir kosan der."""
    yaz(k / 'sandbox_tst' / 'gate' / 'junit.xml', JUNIT_TST0)
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: v['sonuc'].__setitem__('kosan', 0))


def _tst05(k):
    """Tek ihlal: ham JUnit 1 atlanan test der; beyan da ayni gercegi soyler."""
    yaz(k / 'sandbox_tst' / 'gate' / 'junit.xml', JUNIT_TST5_SKIP)
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: v['sonuc'].__setitem__('atlanan', 1))


def _tst06(k):
    """Tek ihlal: kapsam tabanin bir altindan da dusuk (80 -> 70)."""
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: v['sonuc'].__setitem__('kapsam_yuzde', 70))


def _tst10(k):
    """Tek ihlal: rapor, takipli kaynak dosyadan daha eski zaman damgasi tasir."""
    rapor = k / 'sandbox_tst' / 'gate' / 'junit.xml'
    kaynak = k / 'sandbox_tst' / 'gitdepo' / 'olcum.py'
    eski = kaynak.stat().st_mtime - 30
    os.utime(rapor, (eski, eski))
    return None


def _tst11(k):
    """Tek ihlal: kanittaki komut kod_profil.test_komutu ile uyusmaz."""
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: v.__setitem__('komut', 'pytest -x'))


def _tst12(k):
    """Tek ihlal: kanit baska bir rapor dosyasini gosterir."""
    rapor = k / 'sandbox_tst' / 'gate' / 'baska.xml'
    yaz(rapor, JUNIT_TST5)
    return _json_duzenle(k, 'sandbox_tst/03-KFAZ-3-TEST-EVIDENCE.json',
                         lambda v: v.__setitem__('rapor', str(rapor)))


CHK_SCOPE = '''# SCOPE

| ID | Baslik | Zorunluluk | Kaynak | Gerekce |
|---|---|---|---|---|
| SC-001 | Giris | ZORUNLU | K | x |
| SC-002 | Yontem | ZORUNLU | K | x |
'''
CHK_MASTER = '''# CHK MASTER

## SC-001 Giris

Metin.

## SC-002 Yontem

Metin.

## PROVENANCE

| SCOPE-ID | Bolum | Kaynak | Satir Referansi | Durum |
|---|---|---|---|---|
| SC-001 | Giris | K | 1 | kapsiyor |
| SC-002 | Yontem | K | 2 | kapsiyor |
'''


def _chk_hazirla(k):
    d = k / 'sandbox_chk'
    yaz(d / '00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md', CHK_SCOPE)
    yaz(d / '03-FAZ-3-MASTER-v5.5.md', CHK_MASTER)
    return None


def _chk01(k):
    """Tek ihlal: zorunlu SC-002 basligi kaybolur."""
    return degistir(k, 'sandbox_chk/03-FAZ-3-MASTER-v5.5.md',
                    '## SC-002 Yontem', '## Yontem')


def _chk02(k):
    """Tek ihlal: SC-002 PROVENANCE durumu kapsiyor degil."""
    return degistir(k, 'sandbox_chk/03-FAZ-3-MASTER-v5.5.md',
                    '| SC-002 | Yontem | K | 2 | kapsiyor |',
                    '| SC-002 | Yontem | K | 2 | MISSING |')


def _chk05(k):
    """Tek ihlal: ayni markdown basligi ikinci kez eklenir (WARN)."""
    return ekle(k, 'sandbox_chk/03-FAZ-3-MASTER-v5.5.md',
                '\n## SC-001 Giris\n')


def _reck08(k):
    """Tek ihlal: KFAZ2.chg liste degil; sema RECK-08 P0 verir."""
    return _md_json_duzenle(k, 'sandbox_reck/_KOSU/02-KFAZ-2-MANIFEST.md',
                            lambda v: v.__setitem__('chg', 'bozuk'))


def _reck07_hazirla(k):
    """RECK-07: tabanda zaten var olan test adi tek basina yetmez."""
    _reck_plan_hazirla(k)
    return _json_duzenle(k, 'sandbox_reck/_KOSU/gate/BASELINE.json',
                         lambda v: v.__setitem__('test_adlari', ['eski_test']))


def _reck07(k):
    """Tek ihlal: REQ davranissal olur ve yalniz TABANDAKI test adina eslenir."""
    hata = _md_json_duzenle(k, 'sandbox_reck/_KOSU/00-KFAZ-0-SPEC.md',
                            lambda v: v['req'][0].__setitem__('tur', 'davranissal'))
    if hata:
        return hata
    return _md_json_duzenle(k, 'sandbox_reck/_KOSU/01-KFAZ-1-PLAN.md',
                            lambda v: v.__setitem__('req_test', {'REQ-001': ['eski_test']}))


def _tst_hazirla(k):
    """TST-04: ham JUnit + taban; git deposu tazelik taramasini temiz tutar."""
    tst = k / 'sandbox_tst'
    depo = tst / 'gitdepo'
    yaz(depo / 'olcum.py', 'x = 1\n')
    _git_kur(depo)
    # Rapor ve kanit COMMIT'TEN SONRA yazilir: TST-10 onlari kaynaktan yeni gorur.
    yaz(tst / 'gate' / 'junit.xml', JUNIT_TST5)
    yaz(tst / 'gate' / 'BASELINE.json', json.dumps({
        'test': {'kosan': 5, 'atlanan': 0, 'kapsam_yuzde': 80},
        'test_adlari': [],
    }, ensure_ascii=False, indent=2) + '\n')
    yaz(tst / '03-KFAZ-3-TEST-EVIDENCE.json', json.dumps({
        'komut': 'pytest -q',
        'cikis_kodu': 0,
        'rapor': str(tst / 'gate' / 'junit.xml'),
        'rapor_formati': 'junit-xml',
        'sonuc': {'kosan': 5, 'basarisiz': 0, 'hata': 0, 'atlanan': 0,
                  'kapsam_yuzde': 80},
    }, ensure_ascii=False, indent=2) + '\n')
    # TST-11/12 koken karsilastirmasi: profil kanittaki komut/raporla ayni olmali.
    yaz(k / 'kod_profil.json', json.dumps({
        'profil': 'test',
        'test_komutu': 'pytest -q',
        'test_raporu': str(tst / 'gate' / 'junit.xml'),
    }, ensure_ascii=False, indent=2) + '\n')


def _tst04(k):
    """Tek ihlal: test sayisi 5 -> 2; kanit da ayni gercegi soyler."""
    tst = k / 'sandbox_tst'
    yaz(tst / 'gate' / 'junit.xml', JUNIT_TST2)
    p = tst / '03-KFAZ-3-TEST-EVIDENCE.json'
    veri = json.loads(p.read_text(encoding='utf-8'))
    veri['sonuc']['kosan'] = 2
    p.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return None


def _satir_sil(k, rel, anahtar):
    """Verilen anahtari tasiyan satiri fiksturden cikarir."""
    p = k / rel
    satirlar = [s for s in p.read_text(encoding='utf-8').splitlines(True) if anahtar not in s]
    p.write_text(''.join(satirlar), encoding='utf-8')
    return None


def _pl04(k):
    """Kok disina isaret eden symlink: PL-04 icin tek ihlal."""
    hedef = k.parent / 'atlas-dis-hedef.md'
    hedef.write_text('# dis\n', encoding='utf-8')
    (k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-dis-link.md').symlink_to(hedef)
    return None


def _mod08_kok_disi(k):
    """MOD-08 kok-disi symlink dali: hedef gercek bir dosya ama kok disinda."""
    hedef = k.parent / 'atlas-mod08-dis.md'
    hedef.write_text('# dis hedef\n', encoding='utf-8')
    (k / 'sandbox_mod/.opencode/agent/kokdisi.md').symlink_to(hedef)
    return None


def _mod08_dosya_degil(k):
    """MOD-08 symlink hedefi dosya degil dali: hedef kok icinde bir dizin."""
    hedef = k / 'sandbox_mod' / 'hedef-dizin'
    hedef.mkdir()
    (k / 'sandbox_mod/.opencode/agent/dizin-link.md').symlink_to(hedef)
    return None


def _rec04(k):
    """Tek ihlal: UYGULANMIS FIX-002 MASTER'da yok; Gate 2B de onu iddia etmez."""
    hata = yaz(k / '03-FAZ-3-MASTER-v5.5.md',
               '# MASTER\n\nFIX-001 uyguland\u0131.\n')
    if hata:
        return hata
    return yaz(k / 'gate' / 'STRONG-gate-2b-v5.5.json',
               '{"manifest_reconciliation": ['
               '{"fix_id": "FIX-001", "status": "UYGULANMIS_KANITLI"}]}\n')


def _rec02_cift_oncelik(k):
    """Tek ihlal: FIX-001 ayni manifestoda P2 ile tekrar eder."""
    return ekle(k, '02-FAZ-2-FIX-MANIFEST.md',
                '| FIX-001 | P2 | A | F-001 | UYGULANMI\u015e | SC-001 |\n')


def _rec05_bozuk_json(k):
    """Tek ihlal: Gate 2B gecersiz JSON; REC-05 fail-closed."""
    return yaz(k / 'gate' / 'STRONG-gate-2b-v5.5.json', '{bozuk json\n')


def _rec05_rekonsiliasyon_bozuk(k):
    """Tek ihlal: manifest_reconciliation liste degil."""
    return yaz(k / 'gate' / 'STRONG-gate-2b-v5.5.json',
               '{"manifest_reconciliation": "bozuk"}\n')


def _rec06_coklu_hayalet(k):
    """Tek ihlal: MASTER'da iki tanimsiz FIX-ID."""
    return ekle(k, '03-FAZ-3-MASTER-v5.5.md', 'FIX-003\nFIX-004\n')


# --- model_kimlik: kor noktasiz taramanin geri alinma mutantlari ---------------
# Her mutant kapiyi GERCEKTEN zayiflatir; beklenen bulgu, kapinin kendi
# --oztest vakasinin adidir (veya --kontrol'un defter hatasidir). Kapi kurali
# silinirse vaka ATESLEMEDI olur ve batarya yesil donemez.
def _mk_ikili(k):
    return degistir(
        k, 'tools/model_kimlik.py',
        'def _bayt_tara(sonuc, yol, ham, kimlikler, tanim):\n',
        'def _bayt_tara(sonuc, yol, ham, kimlikler, tanim):\n'
        '    return  # MUTANT: ikili bayt taramasi devre disi\n')


def _mk_buyuk_atla(k):
    return degistir(
        k, 'tools/model_kimlik.py',
        "        if b'\\x00' in ham:\n",
        '        if len(ham) > 4 * 1024 * 1024:\n'
        '            continue  # MUTANT: 4 MB ustu sessizce atlandi\n'
        "        if b'\\x00' in ham:\n")


def _mk_onaysiz_sessiz(k):
    return degistir(
        k, 'tools/model_kimlik.py',
        '        else:\n            sonuc.incelenmeyen.append((rel, sebep))\n',
        '        else:\n            pass  # MUTANT: onaysiz incelenemeyen sessizce atlandi\n')


def _mk_genel_onay(k):
    return degistir(
        k, 'tools/model_kimlik.py',
        '        kayit = onay.get(rel)\n',
        "        kayit = {'tur': 'okunamaz'} if onay else None  # MUTANT: genel onay\n")


def _mk_defter_tanim_sil(k):
    p = k / 'tools' / 'model_kimlik_istisna.json'
    veri = json.loads(p.read_text(encoding='utf-8'))
    veri['onay'] = [{
        'dosya': 'docs/gecici-onay-yok.md', 'tur': 'okunamaz', 'sha256': None,
        'gerekce': 'MUTANT: defterin kendi tanim onayi kaldirildi.'}]
    p.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + '\n',
                 encoding='utf-8')
    return None


def _mk_defter_hash_sil(k):
    p = k / 'tools' / 'model_kimlik_istisna.json'
    veri = json.loads(p.read_text(encoding='utf-8'))
    veri['_kural'] += ' MUTANT: icerik degisti, tanim hash guncellenmedi.'
    p.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + '\n',
                 encoding='utf-8')
    return None


def _mk_aktif_sayac_sil(k):
    return degistir(
        k, 'tools/model_kimlik.py',
        "            'aktif=0'\n",
        "            ''\n")


def taban_ve_bulgu(kok, kapi, argumanlar, mutasyon, iz, cwd=None, env=None,
                   kontrol=VARSAYILAN_KONTROL, yalniz=VARSAYILAN_YALNIZ):
    """Kirmizi uretmeyen kural icin: temiz tabanda iz YOK, ihlalde iz VAR."""
    betik = kok / kapi
    if not betik.is_file():
        return 'EKSIK', 'kapi betigi yok: %s' % kapi
    komut = [sys.executable, betik] + argumanlar(kok)
    calisma = cwd or kok
    yedek = kopya = None
    if kontrol:
        yedek, kopya = kontrol_yedek(kok)
    rc0, o0 = kos(komut, cwd=calisma, env=env)
    if rc0 != 0:
        return 'TABAN_KIRIK', 'taban rc=%d (beklenen 0) · %s' % (
            rc0, o0.strip().splitlines()[-1] if o0.strip() else '')
    if iz in o0:
        return 'TABAN_KIRLI', 'beklenen bulgu (%s) temiz tabanda da var' % iz
    hata = mutasyon(kok)
    if hata:
        return 'MUTASYON_UYGULANMADI', hata
    rc1, o1 = kos(komut, cwd=calisma, env=env)
    if iz not in o1:
        return 'ATESLEMEDI', 'beklenen bulgu (%s) mutasyon sonrasi ciktida yok (rc=%d)' % (iz, rc1)
    if yalniz:
        diger = sizan_etiketler(iz, o1)
        if diger:
            return 'ATESLEMEDI', 'baska kural etiketi sizdi: %s' % ', '.join(diger)
    if kontrol:
        kontrol_geri(kok, yedek, kopya)
        rc2, o2 = kos(komut, cwd=calisma, env=env)
        if rc2 != 0:
            return 'KONTROL_KIRMIZI', 'kontrol rc=%d (beklenen 0) · %s' % (
                rc2, o2.strip().splitlines()[-1] if o2.strip() else '')
        if iz in o2:
            return 'KONTROL_KIRMIZI', 'kontrol ciktisinda hala bulgu var: %s' % iz
        if FAIL_ETIKET.findall(o2):
            return 'KONTROL_KIRMIZI', 'kontrol ciktisinda FAIL etiketi var: %s' % (
                ', '.join(sorted(set(FAIL_ETIKET.findall(o2)))))
    return 'GECTI-BULGU', ('taban sessiz · mutasyon bulgusu=%s (rc=%d) · '
                            'kontrol rc=0 · FAIL iz yok' % (iz, rc1))


def vakalar():
    """Her vaka: (kimlik, katman, kural, kapi, argumanlar, mutasyon, iz[, etiket[, opsiyon]]).

    Etiket `BULGU` ya da `TERMINAL` olabilir; yeni kayitlarda `opsiyon` icine
    `sozlesme` yazmak tercih edilir. Etiketsiz/opsiyonsuz vaka HATA'dir.
    """
    return [
        ('KOD-SEC-02', 'KOD', 'gercek sir kalibi P0', 'KOD_SABLONLAR/scripts/secret_scan.py',
         lambda k: ['--tum', '--dizin', str(k / 'sandbox')],
         lambda k: ekle(k, 'sandbox/notlar.md', '\nanahtar = "%s"\n' % SAHTE_ANAHTAR),
         'SEC-'),
        ('KOD-PERM-01', 'KOD', 'olu kural yok (findLast sirasi)', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: degistir(
             k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-gate-2a.md',
             '  bash:\n    "*": allow\n    "git commit*": deny\n',
             '  bash:\n    "git commit*": deny\n    "*": allow\n'),
         'PERM-01'),
        ('ATLAS-PL-10', 'ATLAS', 'vacuous PASS muafiyeti yok', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: ekle(k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-scoper.md',
                        '\nKanit GEREKMEZ.\n'),
         'PL-10'),
        ('ATLAS-DEC-03', 'ATLAS', 'beyan basligi zorunlu', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'MASTER.md')],
         lambda k: yaz(k / 'sandbox' / 'MASTER.md',
                       dec_govde([b for b in DEC_BASLIKLAR if b != 'Finansman'])),
         'DEC-03'),
        ('ATLAS-QR-02', 'ATLAS', '40+ kelimelik alintida uclu', 'ATLAS_SABLONLAR/scripts/quote_ratio.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'makale.md')],
         lambda k: yaz(k / 'sandbox' / 'makale.md', qr_govde(uzun_mu=True)),
         'QR-02'),
        # --- fix_reconcile: saf dosya ayristirici -----------------------------
        ('REC-01', 'ATLAS', 'FAZ1 bulgu == FAZ2 FIX', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: ekle(k, '02-FAZ-2-FIX-MANIFEST.md',
                        '| FIX-003 | P2 | C | F-003 | PLANLANDI | SC-003 |\n'),
         'REC-01', REC_KONTROL),
        ('REC-02', 'ATLAS', 'oncelik dagilimi ayni', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: degistir(k, '02-FAZ-2-FIX-MANIFEST.md',
                            '| FIX-002 | P1 |', '| FIX-002 | P2 |'),
         'REC-02', REC_KONTROL),
        ('REC-02-CIFT-ONCELIK', 'ATLAS', 'ayni FIX-ID iki farkli oncelikle',
         'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         _rec02_cift_oncelik,
         'REC-02', REC_KONTROL),
        ('REC-03', 'ATLAS', 'FAZ1 bulgusu FAZ2 de atifli', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: degistir(k, '02-FAZ-2-FIX-MANIFEST.md', 'F-002', 'F-999'),
         'REC-03', REC_KONTROL),
        ('REC-04', 'ATLAS', 'UYGULANMIS FIX MASTER da gorunur', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         _rec04,
         'REC-04', REC_KONTROL),
        ('REC-05', 'ATLAS', 'gate 2B KANITLI iddiasi dogrulanir', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: yaz(k / 'gate' / 'STRONG-gate-2b-v5.5.json',
                       '{"manifest_reconciliation": ['
                       '{"fix_id": "FIX-001", "status": "UYGULANMIS_KANITLI"}, '
                       '{"fix_id": "FIX-002", "status": "UYGULANMIS_KANITLI"}, '
                       '{"fix_id": "FIX-009", "status": "UYGULANMIS_KANITLI"}]}\n'),
         'REC-05', REC_KONTROL),
        ('REC-05-BOZUK-JSON', 'ATLAS', 'gate 2B JSON bozuk',
         'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         _rec05_bozuk_json,
         'REC-05', REC_KONTROL),
        ('REC-05-REKONSILIASYON-BOZUK', 'ATLAS', 'manifest_reconciliation liste degil',
         'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         _rec05_rekonsiliasyon_bozuk,
         'REC-05', REC_KONTROL),
        ('REC-06', 'ATLAS', 'hayalet kanit yok', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: ekle(k, '03-FAZ-3-MASTER-v5.5.md', 'FIX-003\n'),
         'REC-06', REC_KONTROL),
        ('REC-06-COKLU-HAYALET', 'ATLAS', 'birden fazla hayalet FIX-ID',
         'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         _rec06_coklu_hayalet,
         'REC-06', REC_KONTROL),
        # --- source_class_check ----------------------------------------------
        ('SRC-02', 'ATLAS', 'Kaynak Sinifi gecerli', 'ATLAS_SABLONLAR/scripts/source_class_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'sinif.md')],
         lambda k: degistir(k, 'sandbox/sinif.md', '| BIRINCIL |', '| BELIRSIZ |'),
         'SRC-02'),
        ('SRC-03', 'ATLAS', 'AKTARMA beyani zorunlu', 'ATLAS_SABLONLAR/scripts/source_class_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'sinif.md')],
         lambda k: degistir(k, 'sandbox/sinif.md', '| IKINCIL |', '| AKTARMA |'),
         'SRC-03'),
        # --- translit_check --------------------------------------------------
        ('TR-01', 'ATLAS', 'SCOPE ta sistem ilani', 'ATLAS_SABLONLAR/scripts/translit_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'metin_tr.md'),
                    '--scope', str(k / 'sandbox' / 'scope_tr.md')],
         lambda k: degistir(k, 'sandbox/scope_tr.md',
                            'Transliterasyon sistemi: DMG (DIN 31635).\n',
                            'Sistem belirtilmedi.\n'),
         'TR-01'),
        ('TR-02', 'ATLAS', 'tek yazim tutarliligi', 'ATLAS_SABLONLAR/scripts/translit_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'metin_tr.md'),
                    '--scope', str(k / 'sandbox' / 'scope_tr.md')],
         lambda k: ekle(k, 'sandbox/metin_tr.md', 'Ikinci yazim: sak\u012bna.\n'),
         'TR-02'),
        # --- cite_match ------------------------------------------------------
        # EKLEME, degistirme degil: mevcut atif korunur ki CITE-02 (kaynakca
        # girdisi anilmiyor) sizmasin; tek ihlal kaynakcada olmayan yeni atif.
        ('CITE-01', 'ATLAS', 'metindeki atif kaynakcada', 'ATLAS_SABLONLAR/scripts/cite_match.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'cite.md')],
         lambda k: degistir(k, 'sandbox/cite.md',
                            'Govde metni (Yazar, 2020).',
                            'Govde metni (Yazar, 2020) ve (Yabanci, 2021).'),
         'CITE-01'),
        ('CITE-02', 'ATLAS', 'kaynakcadaki girdi anilir', 'ATLAS_SABLONLAR/scripts/cite_match.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'cite.md')],
         lambda k: ekle(k, 'sandbox/cite.md', '- Kaya, B. (2019). Ek. Yayin.\n'),
         'CITE-02'),
        # --- declaration_check ----------------------------------------------
        ('DEC-01', 'ATLAS', 'Etik Kurul beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md',
                            '## Etik Kurul\n\nGerekmedi; gerekce: insan katilimci yok.\n\n', ''),
         'DEC-01'),
        ('DEC-02', 'ATLAS', 'Cikar Catismasi beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md', '## Cikar Catismasi\n\nYok.\n\n', ''),
         'DEC-02'),
        ('DEC-04', 'ATLAS', 'Yazar Katkisi beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md', '## Yazar Katkisi\n\nTek yazar.\n\n', ''),
         'DEC-04'),
        ('DEC-05', 'ATLAS', 'Veri Erisilebilirligi beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md', '## Veri Erisilebilirligi\n\nYok.\n\n', ''),
         'DEC-05'),
        ('DEC-06', 'ATLAS', 'Yapay Zeka beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md', '## Yapay Zeka\n\nKullanilmadi.\n\n', ''),
         'DEC-06'),
        ('DEC-07', 'ATLAS', 'DPIA kosullu zorunlu', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(
             k, 'sandbox/dec.md', '## DPIA\n\nKisisel veri islenmedi.\n',
             '## Katilimci Verisi\n\n'
             'Bu bolumde calismanin veri toplama sureci aciklanmaktadir. Surec, etik '
             'ilkelere uygun olarak planlanmis ve yurutulmustur. Tum adimlar kayit '
             'altina alinmistir.\n\nKatilimcilardan gorusme ile veri toplandi.\n'),
         'DEC-07'),
        # --- secret_scan: yapisal .env tespiti --------------------------------
        ('SEC-01', 'KOD', 'gercek .env P0', 'KOD_SABLONLAR/scripts/secret_scan.py',
         lambda k: ['--tum', '--dizin', str(k / 'sandbox')],
         lambda k: yaz(k / 'sandbox' / '.env', 'TOKEN=degil-gercek\n'),
         'SEC-01'),
        # --- prompt_lint: saf metin/frontmatter kurallari ---------------------
        ('PL-01', 'ATLAS', 'frontmatter description', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\nmode: subagent\n---\n\nCALISTIRILMADI\n'),
         'PL-01'),
        ('PL-02', 'ATLAS', 'mode kapali liste', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\ndescription: test\nmode: expert\n---\n\nCALISTIRILMADI\n'),
         'PL-02'),
        ('PL-04', 'ATLAS', 'symlink kok icinde', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         _pl04,
         'PL-04'),
        ('PL-09', 'ATLAS', 'lens karar vermez', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-lens-test.md',
                       '---\ndescription: test\nmode: subagent\n---\n\n'
                       'CALISTIRILMADI\n\n```json\n{"verdict": "PASS"}\n```\n'),
         'PL-09'),
        ('PL-11', 'ATLAS', 'kalici muafiyet yok', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\ndescription: test\nmode: subagent\n---\n\n'
                       'CALISTIRILMADI. Bu kapi her zaman PASS verir.\n'),
         'PL-11'),
        ('PL-13', 'ATLAS', 'belirsizlik yasagi yok', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\ndescription: test\nmode: subagent\n---\n\n'
                       'CALISTIRILMADI. Belirsizlik etiketlerini birakma.\n'),
         'PL-13'),
        ('PL-16', 'ATLAS', 'cagrilan betik var', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\ndescription: test\nmode: subagent\n---\n\n'
                       'CALISTIRILMADI. python3 scripts/olmayan_kapi_xyz.py cikis kodunu denetler.\n'),
         'PL-16'),
        ('PL-18', 'ATLAS', 'kirik symlink reddedilir', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: (k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-kirik-link.md').symlink_to(
             k / 'ATLAS_SABLONLAR' / 'yok-hedef.md'),
         'PL-18'),
        # --- perm_lint: saf YAML izin kurallari -------------------------------
        ('PERM-02', 'KOD', 'deny cift kalip', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: degistir(
             k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-gate-2a.md',
             '    "*FIX-MANIFEST*": deny\n',
             '    "*FIX-MANIFEST*": deny\n    "docs/*.md": deny\n'),
         'PERM-02'),
        ('PERM-04', 'KOD', 'acilmaz cizgisi read+edit', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: degistir(
             k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-gate-2a.md',
             '    "*FIX-MANIFEST*": deny\n',
             '    "*FIX-MANIFEST*": deny\n    "portfolyo": deny\n'),
         'PERM-04'),
        # --- scope_profile_check: saf SCOPE ayristirici -----------------------
        ('SP-01', 'ATLAS', 'profil beyani zorunlu', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: degistir(k, 'sandbox/scope.md',
                            'ALAN_PROFILI: ampirik', 'ALAN_PROFILI: bilinmeyen'),
         'SP-01'),
        ('SP-02', 'ATLAS', 'profil disi baslik yok', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: degistir(k, 'sandbox/scope.md',
                            '| SC-003 | Y\u00f6ntem |',
                            '| SC-003 | Transliterasyon Y\u00f6ntemi |'),
         'SP-02'),
        ('SP-03', 'ATLAS', 'ortak zorunlular eksiksiz', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: _satir_sil(k, 'sandbox/scope.md', '| SC-001 |'),
         'SP-03'),
        ('SP-04', 'ATLAS', 'profile ozgu yuvalar var', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: _satir_sil(k, 'sandbox/scope.md', '| SC-002 |'),
         'SP-04'),
        ('SP-06', 'ATLAS', 'vacuous PASS kapali', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: yaz(k / 'sandbox' / 'scope.md',
                       (k / 'sandbox' / 'scope.md').read_text(encoding='utf-8')
                       .replace('ZORUNLU', 'OPSIYONEL')),
         'SP-06'),
        ('SP-07', 'ATLAS', 'tablo basliklari zorunlu', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: degistir(k, 'sandbox/scope.md',
                            '| ID | Ba\u015fl\u0131k | Zorunluluk |',
                            '| ID | Baslik | Zorunluluk |'),
         'SP-07'),
        # --- check_models: sabit katalog, saf frontmatter ----------------------
        ('MOD-02', 'ATLAS', 'saglayici yetkili', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'model: openrouter/', 'model: diger/'),
         'MOD-02'),
        ('MOD-03', 'ATLAS', 'model katalogda var', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'openrouter/anthropic/claude-opus-5', 'openrouter/yok/model'),
         'MOD-03'),
        ('MOD-06', 'ATLAS', 'tilde takma adi yok', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'openrouter/anthropic/claude-opus-5', '~/anthropic/claude-opus-5'),
         'MOD-06'),
        # --- freeze_check: SHA256 taban karsilastirmasi ----------------------
        ('FRZ-01', 'KOD', 'profil tamperi GATE_TAMPERED terminal',
         'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         lambda k: yaz(k / 'kod_profil.json', '{"profil": "degisti"}\n'),
         'FRZ-01', {'terminal': True}),
        ('FRZ-01-KAYIP', 'KOD', 'profil kaybi GATE_TAMPERED terminal',
         'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz01_kayip,
         'FRZ-01', {'terminal': True}),
        ('FRZ-01-02', 'KOD', 'profil+betik tamperi GATE_TAMPERED terminal',
         'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz01_02, ('FRZ-01', 'FRZ-02'), {'terminal': True}),
        ('FRZ-02', 'KOD', 'kapi betigi dondurulmus', 'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         lambda k: yaz(k / 'scripts' / 'kapi.py', '# degistirilmis kapi\n'),
         'FRZ-02', {'terminal': True}),
        ('FRZ-02-KAYIP', 'KOD', 'betik kaybi GATE_TAMPERED terminal',
         'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz02_kayip,
         'FRZ-02', {'terminal': True}),
        ('FRZ-03', 'KOD', 'dondurulan bolge degismez', 'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         lambda k: yaz(k / 'dondurulan.md', '# bozulmus bolge\n'),
         'FRZ-03'),
        ('FRZ-04', 'KOD', 'dondurulan dosya kaybolmaz', 'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         lambda k: (k / 'dondurulan.md').unlink(),
         'FRZ-04'),
        ('FRZ-05', 'KOD', 'taban yoksa temiz denmez', 'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         lambda k: (k / '_KOSU' / 'gate' / 'BASELINE.json').unlink(),
         'FRZ-05'),
        ('FRZ-06', 'KOD', 'taban semasi eksik olamaz', 'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz06,
         'FRZ-06'),
        ('FRZ-07', 'KOD', 'taban kirli agacta olculmez', 'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz07,
         'FRZ-07'),
        ('FRZ-08', 'KOD', 'temiz agac imzasi dogrulanir', 'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz08,
         'FRZ-08', {'sozlesme': SOZLESME_TERMINAL, 'kur': _frz08_hazirla,
                    'env': _frz08_env()}),
        ('FRZ-08-IMZA', 'KOD', 'imzali taban icerigi kurcalanamaz',
         'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz08_imza,
         'FRZ-08', {'sozlesme': SOZLESME_TERMINAL, 'kur': _frz08_imza_hazirla,
                    'env': _frz08_env(), 'taban_bilgi': 'FRZ-08'}),
        ('FRZ-08-GECERSIZ-IMZA', 'KOD',
         'gecersiz imzali temiz taban terminal rc=2 TAMPERED',
         'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz08_yanlis_anahtar,
         ('FRZ-08', 'TAMPERED'), {'sozlesme': SOZLESME_TERMINAL,
                                  'kur': _frz08_imza_hazirla,
                                  'env': _frz08_env(), 'taban_bilgi': 'FRZ-08'}),
        ('FRZ-08-P1', 'KOD', 'imzasiz temiz taban dusuk guven',
         'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         _frz08_p1,
         'FRZ-08 DUSUK_GUVEN', 'BULGU', {'sozlesme': SOZLESME_BULGU,
                                          'kur': _frz08_hazirla}),
        ('DEP-01', 'KOD', 'manifest varken kilit beyani zorunlu',
         'KOD_SABLONLAR/scripts/dep_audit.py',
         lambda k: [],
         _dep01,
         'DEP-01', {'kur': _dep01_hazirla, 'kontrol': True}),
        ('DEP-05', 'KOD', 'lisans catismasi P0', 'KOD_SABLONLAR/scripts/dep_audit.py',
         lambda k: [],
         lambda k: yaz(k / 'LICENSES.json', '{"paket": "GPL-3.0"}\n'),
         'DEP-05'),
        ('TSL-03', 'ATLAS', 'teslim artefakti tahrifati yakalanir',
         'ATLAS_SABLONLAR/scripts/teslim_imza.py',
         lambda k: ['--dogrula'],
         _tsl03,
         'TSL-03', {'cwd': 'sandbox_teslim', 'kur': _tsl03_hazirla,
                    'kontrol': True}),
        ('TSL-04', 'ATLAS', 'gecersiz teslim imzasi yakalanir',
         'ATLAS_SABLONLAR/scripts/teslim_imza.py',
         lambda k: ['--dogrula'],
         _tsl04,
         'TSL-04', {'cwd': 'sandbox_teslim', 'kur': _tsl04_hazirla,
                    'kontrol': True,
                    'env': dict(os.environ, LAB_IMZA_ANAHTARI='a' * 64)}),
        ('TSL-06', 'ATLAS', 'zorunlu artefakt manifestte eksik olamaz',
         'ATLAS_SABLONLAR/scripts/teslim_imza.py',
         lambda k: ['--dogrula'],
         _tsl06,
         'TSL-06', {'cwd': 'sandbox_teslim', 'kur': _tsl03_hazirla,
                    'kontrol': True}),
        # --- chg_reconcile: git diff + plan kapsami ----------------------------
        ('RECK-01', 'KOD', 'her REQ planinda karsilik bulur',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ2'],
         _reck01,
         'RECK-01', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck_plan_hazirla}),
        ('RECK-02', 'KOD', 'UYGULANMIS CHG diff te olmali',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ2'],
         _reck02,
         'RECK-02', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck_plan_hazirla}),
        ('RECK-04', 'KOD', '2B KANITLI iddiasi diff te dogrulanir',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ2',
                    '--gate2b', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'KOD-gate-2b.json')],
         _reck04,
         'RECK-04', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck_plan_hazirla}),
        ('RECK-05', 'KOD', 'hayalet CHG olmayan REQ e baglanamaz',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ2'],
         _reck05,
         'RECK-05', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck_plan_hazirla}),
        ('RECK-08', 'KOD', 'makine blogu semaya uymali',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ2'],
         _reck08,
         'RECK-08', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck_plan_hazirla}),
        ('RECK-07', 'KOD', 'davranissal REQ yeni test adi ister',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ2'],
         _reck07,
         'RECK-07', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck07_hazirla}),
        ('RECK-03', 'KOD', 'plansiz urun dosyasi kapsam ihlali',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ1'],
         _reck03,
         'RECK-03', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck_hazirla}),
        ('RECK-06', 'KOD', 'dondurulmus bolge degismez',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ1'],
         _reck06,
         'RECK-06', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck_hazirla}),
        ('RECK-09', 'KOD', 'plan yokken urun kodu degismez',
         'KOD_SABLONLAR/scripts/chg_reconcile.py',
         lambda k: ['--kosu', str(k / 'sandbox_reck' / '_KOSU'),
                    '--taban', str(k / 'sandbox_reck' / '_KOSU' / 'gate' / 'BASELINE.json'),
                    '--faz', 'KFAZ0'],
         _reck09,
         'RECK-09', {'cwd': 'sandbox_reck/gitdepo', 'kur': _reck09_hazirla}),
        # --- test_attest: ham JUnit taban karsilastirmasi ----------------------
        ('TST-04', 'KOD', 'test silinerek yesil olmaz',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst04,
         'TST-04', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-08', 'KOD', 'test kaniti olmadan PASS yok',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst08,
         'TST-08', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-07', 'KOD', 'kanit beyani ham raporla celisemez',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst07,
         'TST-07', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-09', 'KOD', 'test komutunun cikis kodu kayitli',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst09,
         'TST-09', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-01', 'KOD', 'basarisiz test sifir olmali',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst01,
         'TST-01', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-02', 'KOD', 'hatali test sifir olmali',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst02,
         'TST-02', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-03', 'KOD', 'sifir test temiz degildir',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst03,
         'TST-03', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_zero_hazirla}),
        ('TST-05', 'KOD', 'atlanan test tabandan fazla olamaz',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst05,
         'TST-05', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-06', 'KOD', 'kapsam tabanin bir altina kadar korunur',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst06,
         'TST-06', 'BULGU', {'sozlesme': SOZLESME_BULGU,
                            'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-10', 'KOD', 'rapor kaynaktan eski olamaz',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst10,
         'TST-10', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-11', 'KOD', 'kanit komutu kod_profil ile ayni',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst11,
         'TST-11', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        ('TST-12', 'KOD', 'kanit raporu kod_profil ile ayni',
         'KOD_SABLONLAR/scripts/test_attest.py',
         lambda k: ['--kanit', str(k / 'sandbox_tst' / '03-KFAZ-3-TEST-EVIDENCE.json'),
                    '--taban', str(k / 'sandbox_tst' / 'gate' / 'BASELINE.json'),
                    '--profil', str(k / 'kod_profil.json'),
                    '--kosu', str(k / 'sandbox_tst')],
         _tst12,
         'TST-12', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
        # --- uyari/bilgi kurallari: beklenen bulgu (rc=0 olabilir) ------------
        ('PL-12', 'ATLAS', 'belirsizlik cikisi var', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k / 'sandbox_pl')],
         lambda k: degistir(k, 'sandbox_pl/.opencode/agent/ajan.md',
                            'CALISTIRILMADI', 'Karar verildi'),
         'PL-12', 'BULGU'),
        ('PL-14', 'ATLAS', 'exit kodu fail-closed', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k / 'sandbox_pl')],
         lambda k: degistir(k, 'sandbox_pl/.opencode/agent/ajan.md',
                            'cikis kodunu denetler', 'denetler'),
         'PL-14', 'BULGU'),
        ('QR-01', 'ATLAS', 'alinti orani esigi', 'ATLAS_SABLONLAR/scripts/quote_ratio.py',
         lambda k: ['--dosya', str(k / 'sandbox_qr' / 'makale.md'), '--esik', '50'],
         lambda k: yaz(k / 'sandbox_qr' / 'makale.md', QR_MUT),
         'UYARI QR-01', 'BULGU'),
        ('QR-02-DENGE', 'ATLAS', 'dengesiz tirnak uyarisi',
         'ATLAS_SABLONLAR/scripts/quote_ratio.py',
         lambda k: ['--dosya', str(k / 'sandbox_qr' / 'makale.md')],
         lambda k: yaz(k / 'sandbox_qr' / 'makale.md', QR_DENGE),
         'UYARI QR-02-denge', 'BULGU'),
        ('PERM-03', 'KOD', 'uzanti kalibi kok seviye', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k / 'sandbox_perm')],
         # Cift kalipla yazilir: kok "*.log" ve ic ice "**/*.log" birlikte.
         # Yalniz "**/*.log" verilince PERM-01 (olu kural) ve PERM-02 (esdes
         # kalip eksik) da atesler ve PERM-03'u izole etmek mumkun olmazdi.
         lambda k: degistir(k, 'sandbox_perm/.opencode/agent/ajan.md',
                            '  read:\n    "*": allow\n',
                            '  read:\n    "*": allow\n'
                            '    "*.log": deny\n    "**/*.log": deny\n'),
         'PERM-03', 'BULGU'),
        ('PERM-05', 'KOD', 'tek deny dize bicimi', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k / 'sandbox_perm')],
         lambda k: degistir(k, 'sandbox_perm/.opencode/agent/ajan.md',
                            '  bash:\n    "*": allow\n',
                            '  bash:\n    "*": deny\n'),
         'PERM-05', 'BULGU'),
        ('PERM-06', 'KOD', 'kirmizi cizgi ask degil', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k / 'sandbox_perm')],
         lambda k: degistir(k, 'sandbox_perm/.opencode/agent/ajan.md',
                            '  bash:\n    "*": allow\n',
                            '  bash:\n    "*": allow\n    "ATLAS/*": ask\n'),
         'PERM-06', 'BULGU'),
        ('PERM-07', 'KOD', 'yol kalibi goreli', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k / 'sandbox_perm')],
         # Mutlak yol kalibi ciftiyle yazilir; tek basina PERM-02 (ic ice yol
         # korunmuyor) sizardi. Amac yalniz PERM-07 uyarisini izole etmek.
         lambda k: degistir(k, 'sandbox_perm/.opencode/agent/ajan.md',
                            '  read:\n    "*": allow\n',
                            '  read:\n    "*": allow\n'
                            '    "/etc/passwd": deny\n'
                            '    "**//etc/passwd": deny\n'),
         'PERM-07', 'BULGU'),
        ('PERM-08', 'KOD', 'bash deny tek sinir degil', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k / 'sandbox_perm')],
         lambda k: degistir(k, 'sandbox_perm/.opencode/agent/ajan.md',
                            '  bash:\n    "*": allow\n',
                            '  bash:\n    "*": allow\n    "rm *": deny\n'),
         'PERM-08', 'BULGU'),
        ('SEC-03', 'KOD', 'yer tutucu gorunur kalir', 'KOD_SABLONLAR/scripts/secret_scan.py',
         lambda k: ['--tum', '--dizin', str(k / 'sandbox_sec')],
         lambda k: ekle(k, 'sandbox_sec/notlar.md', '\n' + SEC_ORNEK),
         'SEC-03', 'BULGU'),
        ('SEC-05', 'KOD', 'pyc onbellegi loglanir', 'KOD_SABLONLAR/scripts/secret_scan.py',
         lambda k: ['--tum', '--dizin', str(k / 'sandbox_sec')],
         lambda k: yaz(k / 'sandbox_sec' / '__pycache__' / 'x.pyc', 'onbellek\n'),
         'SEC-05', 'BULGU'),
        ('SP-05', 'ATLAS', 'DPIA kosullu beyan', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: degistir(k, 'sandbox/scope.md',
                            '\nKisisel veri islenmemektedir.\n', '\n'),
         'SP-05', 'BULGU'),
        ('CITE-03', 'ATLAS', 'ayni soyad yil celiskisi', 'ATLAS_SABLONLAR/scripts/cite_match.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'cite_yil.md')],
         lambda k: (degistir(k, 'sandbox/cite_yil.md', '## Kaynakca',
                             '(Yazar, 2021).\n\n## Kaynakca') or
                    ekle(k, 'sandbox/cite_yil.md', '- Yazar, A. (2021). Ikinci. Yayin.\n')),
         'UYARI CITE-03', 'BULGU'),
        ('MOD-01', 'ATLAS', 'model satiri var', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'model: openrouter/anthropic/claude-opus-5\n', ''),
         'MOD-01', 'BULGU'),
        ('MOD-04', 'ATLAS', 'deprecated model yok', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'openrouter/anthropic/claude-opus-5',
                            'openrouter/deepseek/deepseek-v4-flash'),
         'MOD-04', {'kontrol': True, 'yalniz': True}),
        ('MOD-05', 'ATLAS', 'reasoning destekli', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'openrouter/anthropic/claude-opus-5',
                            'openrouter/z-ai/glm-5.2'),
         'MOD-05', {'kontrol': True, 'yalniz': True}),
        ('MOD-05-TOOLCALL', 'ATLAS', 'tool_call destekli', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'openrouter/anthropic/claude-opus-5',
                            'openrouter/moonshotai/kimi-k3'),
         'MOD-05', {'kontrol': True, 'yalniz': True}),
        ('MOD-07', 'ATLAS', 'govde-frontmatter celismez', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: ekle(k, 'sandbox_mod/.opencode/agent/ajan.md',
                        '\nDeepSeek modeli anildi.\n'),
         'MOD-07', 'BULGU'),
        ('MOD-08', 'ATLAS', 'symlink hedefi gecerli', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: (k / 'sandbox_mod/.opencode/agent/kirik.md').symlink_to(
             k / 'sandbox_mod' / 'yok-hedef.md'),
         'MOD-08', {'kontrol': True, 'yalniz': True}),
        ('MOD-08-KOK-DISI', 'ATLAS', 'kök-dışı symlink reddedilir',
         'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         _mod08_kok_disi,
         'MOD-08', {'kontrol': True, 'yalniz': True}),
        ('MOD-08-DOSYA-DEGIL', 'ATLAS', 'symlink hedefi dosya olmalı',
         'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         _mod08_dosya_degil,
         'MOD-08', {'kontrol': True, 'yalniz': True}),
        ('SRC-01', 'ATLAS', 'sinyal tablosu ile sinif uyumu', 'ATLAS_SABLONLAR/scripts/source_class_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'sinif_src01.md')],
         _src01,
         'SRC-01'),
        ('PL-19', 'ATLAS', 'prompt-sema zorunlu alan', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k.parent / 'sandbox_pl19')],
         lambda k: _satir_sil(k.parent, 'sandbox_pl19/.opencode/agent/atlas-review-main.md',
                              '"input_sha256"'),
         'PL-19', {'yalniz': True}),
        ('PL-19-UYARI', 'ATLAS', 'semada olmayan alan uyarıdır',
         'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k.parent / 'sandbox_pl19')],
         lambda k: degistir(k.parent, 'sandbox_pl19/.opencode/agent/atlas-review-main.md',
                            '  "run_id": "run-test-001",',
                            '  "run_id": "run-test-001",\n  "beklenmeyen_alan": true,'),
         'UYARI PL-19', 'BULGU'),
        ('PL-19-JSON-YOK', 'ATLAS', 'JSON orneği yoksa kırmızı',
         'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k.parent / 'sandbox_pl19')],
         lambda k: _satir_sil(k.parent, 'sandbox_pl19/.opencode/agent/atlas-review-main.md',
                              '```json'),
         'PL-19', {'yalniz': True}),
        # --- provenance_check: SCOPE sozlesmesi + MASTER + PROVENANCE -------------
        ('CHK-01', 'ATLAS', 'zorunlu SCOPE-ID baslik olmali',
         'ATLAS_SABLONLAR/scripts/provenance_check.py',
         lambda k: [],
         _chk01,
         'CHK-01', {'cwd': 'sandbox_chk', 'kur': _chk_hazirla}),
        ('CHK-02', 'ATLAS', 'zorunlu ID provenance tablosunda kapsiyor',
         'ATLAS_SABLONLAR/scripts/provenance_check.py',
         lambda k: [],
         _chk02,
         'CHK-02', {'cwd': 'sandbox_chk', 'kur': _chk_hazirla}),
        ('CHK-05', 'ATLAS', 'baslik benzersizligi',
         'ATLAS_SABLONLAR/scripts/provenance_check.py',
         lambda k: [],
         _chk05,
         'WARN CHK-05', 'BULGU', {'cwd': 'sandbox_chk', 'kur': _chk_hazirla}),
        # --- model_kimlik: "bakamadigi icin PASS verme" kuralinin geri alinmasi --
        ('MODELKIM-IKILI-BAYT', 'ATLAS', 'ikili dosyada bayt aramasi zorunlu',
         'tools/model_kimlik.py', lambda k: ['--oztest'],
         _mk_ikili, 'FAIL — ikili', {'kontrol': True}),
        ('MODELKIM-BUYUK-ATLA', 'ATLAS', '4 MB ustu dosya sessizce atlanamaz',
         'tools/model_kimlik.py', lambda k: ['--oztest'],
         _mk_buyuk_atla, 'FAIL — buyuk', {'kontrol': True}),
        ('MODELKIM-ONAYSIZ-SESSIZ', 'ATLAS', 'onaysiz incelenemeyen FAIL eder',
         'tools/model_kimlik.py', lambda k: ['--oztest'],
         _mk_onaysiz_sessiz, 'FAIL — onaysiz', {'kontrol': True}),
        ('MODELKIM-GENEL-ONAY', 'ATLAS', 'tek onay tum incelenemeyenleri kapsamaz',
         'tools/model_kimlik.py', lambda k: ['--oztest'],
         _mk_genel_onay, 'FAIL — onaysiz', {'kontrol': True}),
        ('MODELKIM-DEFTER-TANIM', 'ATLAS', 'defter kendi tanim onayini tasir',
         'tools/model_kimlik.py', lambda k: ['--kontrol'],
         _mk_defter_tanim_sil, 'onay listesi', {'kontrol': True}),
        ('MODELKIM-DEFTER-HASH', 'ATLAS', 'defter tanim SHA-256 dogrulanir',
         'tools/model_kimlik.py', lambda k: ['--kontrol'],
         _mk_defter_hash_sil, 'tanim hash tutmuyor', {'kontrol': True}),
        ('MODELKIM-AKTIF-SAYAC', 'ATLAS', 'PASS raporu aktif sayacini tasir',
         'tools/model_kimlik.py', lambda k: ['--oztest'],
         _mk_aktif_sayac_sil, 'FAIL — rapor', {'kontrol': True}),
        # --- kapsam disi kalan uygulanabilir kurallar: sentetik fikstur ------
        # dep_audit: DEP-03/04/06 P1'dir; rc=0 oldugu icin beklenen-bulgu.
        ('DEP-03', 'KOD', 'sabitlenmemis surum P1',
         'KOD_SABLONLAR/scripts/dep_audit.py',
         _dep_argumanlar, _dep03, 'DEP-03', 'BULGU',
         {'cwd': 'sandbox_dep', 'kur': _dep_hazirla}),
        ('DEP-04', 'KOD', 'kilit/manifest diff uyusmazligi P1',
         'KOD_SABLONLAR/scripts/dep_audit.py',
         _dep_argumanlar, _dep04, 'DEP-04', 'BULGU',
         {'cwd': 'sandbox_dep', 'kur': _dep_hazirla}),
        ('DEP-06', 'KOD', 'bos bagimlilik manifesti P1',
         'KOD_SABLONLAR/scripts/dep_audit.py',
         _dep_argumanlar, _dep06, 'DEP-06', 'BULGU',
         {'cwd': 'sandbox_dep', 'kur': _dep_hazirla}),
        # teslim_imza: TSL-01/02 P0, TSL-05 P1.
        ('TSL-01', 'ATLAS', 'manifest yok fail-closed',
         'ATLAS_SABLONLAR/scripts/teslim_imza.py',
         lambda k: ['--dogrula'], _tsl01, 'TSL-01',
         {'cwd': 'sandbox_teslim', 'kur': _teslim_hazirla}),
        ('TSL-02', 'ATLAS', 'manifestteki dosya diskte yok',
         'ATLAS_SABLONLAR/scripts/teslim_imza.py',
         lambda k: ['--dogrula'], _tsl02, 'TSL-02',
         {'cwd': 'sandbox_teslim', 'kur': _teslim_hazirla}),
        ('TSL-05', 'ATLAS', 'imza yok dusuk guven',
         'ATLAS_SABLONLAR/scripts/teslim_imza.py',
         lambda k: ['--dogrula'], _tsl05, 'TSL-05', 'BULGU',
         {'cwd': 'sandbox_teslim', 'kur': _tsl04_hazirla,
          'env': _frz08_env()}),
        # api_surface: API-02 P0; API-01/04/05 P1.
        ('API-01', 'KOD', 'KFAZ0 imza envanteri yok P1',
         'KOD_SABLONLAR/scripts/api_surface.py',
         _api_argumanlar, _api01, 'API-01', 'BULGU',
         {'cwd': 'sandbox_api', 'kur': _api_hazirla}),
        ('API-02', 'KOD', 'disa acik imza kayboldu',
         'KOD_SABLONLAR/scripts/api_surface.py',
         _api_argumanlar, _api02, 'API-02',
         {'cwd': 'sandbox_api', 'kur': _api_hazirla}),
        ('API-04', 'KOD', 'T2 regex adayi kayboldu P1',
         'KOD_SABLONLAR/scripts/api_surface.py',
         _api_argumanlar, _api04, 'API-04', 'BULGU',
         {'cwd': 'sandbox_api', 'kur': _api04_hazirla}),
        ('API-05', 'KOD', 'imza komutu kosmadi P1',
         'KOD_SABLONLAR/scripts/api_surface.py',
         _api_argumanlar, _api05, 'API-05', 'BULGU',
         {'cwd': 'sandbox_api', 'kur': _api_hazirla}),
        # oztest_attest: OZT-01/02/03/06 P0; OZT-05 P1.
        ('OZT-01', 'ATLAS', 'taban yok fail-closed',
         'ATLAS_SABLONLAR/scripts/oztest_attest.py',
         _ozt_argumanlar, _ozt01, 'OZT-01',
         {'cwd': 'sandbox_ozt', 'kur': _ozt_hazirla}),
        ('OZT-02', 'ATLAS', 'tabandaki test kosuda yok',
         'ATLAS_SABLONLAR/scripts/oztest_attest.py',
         _ozt_argumanlar, _ozt02, 'OZT-02',
         {'cwd': 'sandbox_ozt', 'kur': _ozt_hazirla}),
        ('OZT-03', 'ATLAS', 'sifir test temiz degil',
         'ATLAS_SABLONLAR/scripts/oztest_attest.py',
         _ozt_argumanlar, _ozt03, 'OZT-03',
         {'cwd': 'sandbox_ozt', 'kur': _ozt_hazirla}),
        ('OZT-05', 'ATLAS', 'tabanda olmayan yeni test P1',
         'ATLAS_SABLONLAR/scripts/oztest_attest.py',
         _ozt_argumanlar, _ozt05, 'OZT-05', 'BULGU',
         {'cwd': 'sandbox_ozt', 'kur': _ozt_hazirla}),
        ('OZT-06', 'ATLAS', 'taban hash kurcalanmis',
         'ATLAS_SABLONLAR/scripts/oztest_attest.py',
         _ozt_argumanlar, _ozt06, 'OZT-06',
         {'cwd': 'sandbox_ozt', 'kur': _ozt_hazirla}),
        # olgu_lint: gecici git deposu + taze attestation; OLGU-04/05/06 FAIL.
        ('OLGU-04', 'ATLAS', 'attestation yok',
         'ATLAS_SABLONLAR/scripts/olgu_lint.py',
         _olgu_argumanlar, _olgu04, 'OLGU-04',
         {'kur': _olgu_hazirla}),
        ('OLGU-05', 'ATLAS', 'kanit sayisi kanonikten farkli',
         'ATLAS_SABLONLAR/scripts/olgu_lint.py',
         _olgu05_argumanlar, _olgu05, 'OLGU-05',
         {'kur': _olgu_hazirla}),
        ('OLGU-06', 'ATLAS', 'kanonik DEVIR satiri yok',
         'ATLAS_SABLONLAR/scripts/olgu_lint.py',
         _olgu_argumanlar, _olgu06, 'OLGU-06',
         {'kur': _olgu_hazirla}),
    ]


def hazirla(kok, opsiyon=None):
    """Temiz kopya + vakalarin temiz taban fiksturleri."""
    yaz(kok / 'sandbox' / 'notlar.md', '# Notlar\n\nBu dosyada sir yok.\n')
    yaz(kok / 'sandbox' / 'MASTER.md', dec_govde(DEC_BASLIKLAR))
    yaz(kok / 'sandbox' / 'makale.md', qr_govde(uzun_mu=False))
    # fix_reconcile varsayilan adlari kokerde arar.
    yaz(kok / '01-FAZ-1-LENS-ANALYSIS.json', REC_FAZ1)
    yaz(kok / '02-FAZ-2-FIX-MANIFEST.md', REC_MANIFEST)
    yaz(kok / '03-FAZ-3-MASTER-v5.5.md', REC_MASTER)
    yaz(kok / 'gate' / 'STRONG-gate-2b-v5.5.json', REC_GATE2B)
    yaz(kok / 'sandbox' / 'sinif.md', SINIF_MD)
    yaz(kok / 'sandbox' / 'scope_tr.md', SCOPE_TR)
    yaz(kok / 'sandbox' / 'metin_tr.md', METIN_TR)
    yaz(kok / 'sandbox' / 'cite.md', CITE_MD)
    yaz(kok / 'sandbox' / 'dec.md', DEC_MD)
    yaz(kok / 'sandbox_mod' / '.opencode' / 'agent' / 'ajan.md',
        '---\ndescription: test ajani\nmode: subagent\n'
        'model: openrouter/anthropic/claude-opus-5\n---\n\nCALISTIRILMADI\n')
    # freeze_check: sabit SHA256 tabanli, saf dosya fiksturu.
    yaz(kok / 'kod_profil.json', '{"profil": "test"}\n')
    yaz(kok / 'scripts' / 'kapi.py', '# test kapi betigi\n')
    yaz(kok / 'dondurulan.md', '# dondurulmus bolge\n')
    yaz(kok / '_KOSU' / 'gate' / 'BASELINE.json', json.dumps({
        'kod_profil_sha256': _sha(kok / 'kod_profil.json'),
        'scripts_sha256': {'scripts/kapi.py': _sha(kok / 'scripts' / 'kapi.py')},
        'dondurulan': {'dondurulan.md': _sha(kok / 'dondurulan.md')},
        'temiz_agac': True,
    }, ensure_ascii=False, indent=2) + '\n')
    # scope_profile_check: depodaki gercek sozlesme + profil beyani.
    sozlesme = (KOK / 'DENEME' / '00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md').read_text(
        encoding='utf-8').replace(
            '| SC-022 | Provenance Durumu | ZORUNLU | \u00dcretilecek | CHK-02 |',
            '| SC-022 | Provenance Durumu | ZORUNLU | \u00dcretilecek | CHK-02 |\n'
            '| SC-030 | Kapsam Kapanisi | ZORUNLU | \u00dcretilecek | Kapanis kontrolu |')
    yaz(kok / 'sandbox' / 'scope.md',
        'ALAN_PROFILI: ampirik\n\n' + sozlesme + '\nKisisel veri islenmemektedir.\n')
    # Uyari-seviyeli kurallar icin yalitilmis fiksturler.
    yaz(kok / 'sandbox_pl' / '.opencode' / 'agent' / 'ajan.md', PL_MD)
    yaz(kok / 'sandbox_pl' / 'scripts' / 'mevcut.py', '# test betigi\n')
    # PL-19 fiksturu diger prompt taramalarinin kokunun DISINDA durur; aksi
    # halde gercek schema ile eslesen ayni adli dosya, ilgisiz PL-XX tabanlarini
    # da kirletir. Testler bu kardes dizini acikca hedefler.
    pl19 = kok.parent / 'sandbox_pl19'
    yaz(pl19 / '.opencode' / 'agent' / 'atlas-review-main.md', PL19_MD)
    yaz(pl19 / 'ATLAS_SABLONLAR' / 'templates' / 'REVIEW-PANEL-SCHEMA.json',
        json.dumps(PL19_SCHEMA, ensure_ascii=False, indent=2) + '\n')
    yaz(kok / 'sandbox_perm' / '.opencode' / 'agent' / 'ajan.md', PERM_MD)
    yaz(kok / 'sandbox_qr' / 'makale.md', QR_BASE)
    yaz(kok / 'sandbox_sec' / 'notlar.md', '# Notlar\n\nBu dosyada sir yok.\n')
    yaz(kok / 'sandbox' / 'cite_yil.md', CITE_MD)
    yaz(kok / SRC01_SANDBOX, _src01_fikstur(kok))
    if opsiyon and callable(opsiyon.get('kur')):
        opsiyon['kur'](kok)


SONUC_DOSYASI = KOK / 'tools' / 'mutasyon_sonuc.json'
SONUC_SEMA = 'MUTASYON-SONUC/v1'
GECEN_DURUMLAR = ('GECTI', 'GECTI-TERMINAL', 'GECTI-BULGU')


def _git_metin(*args):
    try:
        r = subprocess.run(['git', '-C', str(KOK)] + list(args),
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ''
    except OSError:
        return ''


def kaynak_imzasi():
    """Kanitin bagli oldugu kaynaklarin icerik ozeti.

    HEAD'e baglamak ise yaramaz: kanit dosyasini (ve kapsam tablosunu) commit
    etmek HEAD'i degistirir ve kanit sonsuza dek 'bayat' gorunur. Bu yuzden
    olculen seyin KENDISI hash'lenir: batarya + tum kapi betikleri. Kaynak
    degismedikce kanit gecerlidir.
    """
    parcalar = [KOK / 'tools' / 'mutasyon_bataryasi.py']
    for d in ('ATLAS_SABLONLAR/scripts', 'KOD_SABLONLAR/scripts'):
        parcalar += sorted((KOK / d).glob('*.py'))
    h = hashlib.sha256()
    for p in parcalar:
        h.update(str(p.relative_to(KOK)).encode('utf-8'))
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\n')
    return h.hexdigest()


def sonuc_yaz(satirlar, meta, kisa):
    """Makine-okunur kosu sonucu: her vaka icin GERCEKLESEN durum.

    `kapsam.py` bu dosyadan 'vaka var' ile 'son kosuda gecti' ayrimini
    turetir. Cikti DETERMINISTIKTIR (zaman/HEAD yok); tazelik yalniz
    `kaynak_sha256` ile denetlenir. Kisa kosu dosyayi yazmaz.
    """
    if kisa:
        # Kisa kosu kanit DEGILDIR: izlenen kanit dosyasini ezmemeli, yoksa
        # temiz klonda agac kirlenir ve kanit 6 vakaya duser.
        print('SONUC YAZILMADI: kisa kosu (kanit dosyasi korunur)')
        return
    kayitlar = []
    for kimlik, katman, kural, durum, ayrinti in satirlar:
        bilgi = meta.get(kimlik, {})
        kayitlar.append({
            'id': kimlik,
            'katman': katman,
            'aciklama': kural,
            'kural': bilgi.get('kural', ''),
            'kural_onek': bilgi.get('kural_onek', ''),
            'betik': bilgi.get('betik', ''),
            'sozlesme': bilgi.get('sozlesme', ''),
            'durum': durum,
            'gecti': durum in GECEN_DURUMLAR,
            'ayrinti': ayrinti,
        })
    # DETERMINISTIK cikti: zaman/HEAD gibi uçucu alan YOK. Aksi halde her
    # kosu dosyayi degistirir, agac hic temiz kalmaz ve attestation/kamu
    # kollari kirmizi olur. Ayni kaynak + ayni sonuc => ayni bayt.
    veri = {
        'schema': SONUC_SEMA,
        'kaynak_sha256': kaynak_imzasi(),
        'kisa': bool(kisa),
        'sayilar': {
            'vaka': len(kayitlar),
            'gecti': sum(1 for k in kayitlar if k['gecti']),
            'kalan': sum(1 for k in kayitlar if not k['gecti']),
        },
        'vakalar': kayitlar,
    }
    SONUC_DOSYASI.write_text(
        json.dumps(veri, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('SONUC YAZILDI: %s (%d vaka · %d gecti · %d kaldi)' % (
        SONUC_DOSYASI.relative_to(KOK), len(kayitlar),
        veri['sayilar']['gecti'], veri['sayilar']['kalan']))


def _katalog_idleri(yol):
    """`{openrouter: {models: {...}}}` dosyasindan model kimliklerini okur."""
    veri = json.loads(Path(yol).read_text(encoding='utf-8'))
    modeller = (veri.get('openrouter') or {}).get('models')
    if not isinstance(modeller, dict) or not modeller:
        raise ValueError('openrouter.models yok veya bos')
    return set(modeller)


def katalog_tutarliligi(gercek=GERCEK_KATALOG, fikstur=MUTASYON_KATALOG):
    """MOD-04/05 kimlikleri gercek katalogda mi? (hatalar, fikstur_n, gercek_n)

    Fikstur katalogu gercek katalogun ALT KUMESI olmalidir: fiksturde olup
    gercekte olmayan her kimlik, katalog degistikten sonra sessizce eski
    kimlikle kosuldugunun isaretidir.
    """
    try:
        gercek_idler = _katalog_idleri(gercek)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return ['gercek katalog okunamadi: %s: %s' % (gercek, e)], 0, 0
    try:
        fikstur_idler = _katalog_idleri(fikstur)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return ['fikstur katalogu okunamadi: %s: %s' % (fikstur, e)], 0, len(gercek_idler)
    hatalar = []
    for kimlik in MOD_FIKSTUR_KIMLIKLERI:
        if kimlik not in gercek_idler:
            hatalar.append('MOD fikstur kimligi gercek katalogda YOK: %s' % kimlik)
        if kimlik not in fikstur_idler:
            hatalar.append('MOD fikstur kimligi fikstur katalogunda YOK: %s' % kimlik)
    for kimlik in sorted(fikstur_idler - gercek_idler):
        hatalar.append('fikstur katalogunda gercekte olmayan kimlik: %s' % kimlik)
    return hatalar, len(fikstur_idler), len(gercek_idler)


def katalog_kontrolu():
    """Tutarlilik hatasi varsa ayrintili FAIL basar; main bunu kosulsuz cagirir."""
    hatalar, fikstur_n, gercek_n = katalog_tutarliligi()
    if hatalar:
        for hata in hatalar:
            print('KATALOG TUTARSIZ: %s' % hata)
        print('KATALOG TUTARLILIK: FAIL — %d sorun' % len(hatalar))
        return False
    print('KATALOG TUTARLILIK: PASS — %d/%d MOD kimligi gercek katalogda '
          '· fikstur %d / gercek %d' % (
              len(MOD_FIKSTUR_KIMLIKLERI), len(MOD_FIKSTUR_KIMLIKLERI),
              fikstur_n, gercek_n))
    return True


def katalog_oztest():
    """Pozitif + uc negatif: katalog degisimi sessizce gecmemeli."""
    vakalar = []
    hatalar, _, _ = katalog_tutarliligi()
    vakalar.append(('mevcut-katalog', not hatalar))
    with tempfile.TemporaryDirectory(prefix='atlas_katalog_') as td:
        td = Path(td)
        gercek = json.loads(GERCEK_KATALOG.read_text(encoding='utf-8'))
        del gercek['openrouter']['models']['deepseek/deepseek-v4-flash']
        yol = td / 'gercek-eksik.json'
        yol.write_text(json.dumps(gercek, ensure_ascii=False), encoding='utf-8')
        h, _, _ = katalog_tutarliligi(gercek=yol)
        vakalar.append(('gercek-eksik-yakalanir',
                        any('deepseek/deepseek-v4-flash' in x for x in h)))
        fikstur = json.loads(MUTASYON_KATALOG.read_text(encoding='utf-8'))
        del fikstur['openrouter']['models']['z-ai/glm-5.2']
        yol = td / 'fikstur-eksik.json'
        yol.write_text(json.dumps(fikstur, ensure_ascii=False), encoding='utf-8')
        h, _, _ = katalog_tutarliligi(fikstur=yol)
        vakalar.append(('fikstur-eksik-yakalanir',
                        any('z-ai/glm-5.2' in x for x in h)))
        fikstur = json.loads(MUTASYON_KATALOG.read_text(encoding='utf-8'))
        fikstur['openrouter']['models']['yok/model'] = {
            'reasoning': True, 'tool_call': True}
        yol = td / 'fikstur-fazla.json'
        yol.write_text(json.dumps(fikstur, ensure_ascii=False), encoding='utf-8')
        h, _, _ = katalog_tutarliligi(fikstur=yol)
        vakalar.append(('fikstur-fazla-yakalanir', any('yok/model' in x for x in h)))
    for ad, gecti in vakalar:
        print('%s %s' % ('PASS' if gecti else 'FAIL', ad))
    print('KATALOG-TUTARLILIK OZ-TEST: %d/%d' % (
        sum(1 for _, g in vakalar if g), len(vakalar)))
    return all(g for _, g in vakalar)


def main():
    if '--katalog-tutarlilik' in sys.argv:
        return 0 if katalog_kontrolu() else 1
    if '--katalog-tutarlilik-oztest' in sys.argv:
        return 0 if katalog_oztest() else 1
    print('MUTASYON BATARYASI — ATLAS + KOD kapi kurallari')
    print('kaynak: %s' % KOK.name)
    print('kural: once TEMIZ TABAN, sonra tek ihlal; kirmizi veya beklenen bulgu.')
    print()
    if not katalog_kontrolu():
        print('HUKUM: FAIL — katalog tutarsiz; batarya eski kimliklerle kosmaz.')
        return 1

    try:
        _src01_fikstur(KOK, bozuk=True)
    except (OSError, ValueError) as e:
        print('HUKUM: FAIL — %s' % e)
        return 1

    gecen = 0
    gecen_terminal = 0
    gecen_bulgu = 0
    satirlar = []
    tum = vakalar()
    if KISA:
        secili = [v for v in tum if v[0] in KISA_VAKALAR]
        bulunan = {v[0] for v in secili}
        eksik = [k for k in KISA_VAKALAR if k not in bulunan]
        if eksik:
            print('HUKUM: FAIL — kisa sette eksik vaka: %s' % ', '.join(eksik))
            return 1
        tum = secili
        print('KISA SET: %d/%d vaka — %s' % (
            len(tum), len(vakalar()), ', '.join(v[0] for v in tum)))
    sozlesmeler = [vaka_sozlesmesi(v)[0] for v in tum]
    # Kural kimligi: `iz` alanindaki kural kimlikleri (KAPSAM ile ayni turetme).
    meta = {}
    for v in tum:
        tur, kume = izinli_etiketler(v[6])
        kimlikler = sorted(kume) if tur == 'KUME' else []
        meta[v[0]] = {'sozlesme': vaka_sozlesmesi(v)[0], 'betik': v[3],
                      'kural': kimlikler[0] if kimlikler else '',
                      # Onek modu ('SEC-'): kanit ayni onekle baslayan TUM
                      # kurallara baglanir; kimlik listesi anlamsizdir.
                      'kural_onek': kume[0] if tur == 'ONEK' else ''}
    hata_top = sozlesmeler.count(SOZLESME_HATA)
    terminal_top = sozlesmeler.count(SOZLESME_TERMINAL)
    bulgu_top = sozlesmeler.count(SOZLESME_BULGU)
    kimlikler = [v[0] for v in tum]
    yinelenen = sorted({k for k in kimlikler if kimlikler.count(k) > 1})
    if yinelenen:
        print('HUKUM: FAIL — yinelenen vaka ID: %s' % ', '.join(yinelenen))
        return 1
    for vaka in tum:
        sozlesme, opsiyon = vaka_sozlesmesi(vaka)
        kimlik, katman, kural, kapi, argumanlar, mutasyon, iz = vaka[:7]
        tmp = Path(tempfile.mkdtemp(prefix='atlas_mut_'))
        try:
            hedef = tmp / 'depo'
            shutil.copytree(KOK, hedef, symlinks=True, ignore=ATLA)
            hazirla(hedef, opsiyon)
            calisma = hedef / opsiyon['cwd'] if opsiyon.get('cwd') else hedef
            if sozlesme == SOZLESME_BULGU:
                durum, ayrinti = taban_ve_bulgu(
                    hedef, kapi, argumanlar, mutasyon, iz, cwd=calisma,
                    env=opsiyon.get('env'),
                    kontrol=bool(opsiyon.get('kontrol', VARSAYILAN_KONTROL)),
                    yalniz=bool(opsiyon.get('yalniz', VARSAYILAN_YALNIZ)))
            elif sozlesme == SOZLESME_TERMINAL:
                durum, ayrinti = taban_ve_terminal(
                    hedef, kapi, argumanlar, mutasyon, iz, cwd=calisma,
                    env=opsiyon.get('env'),
                    kontrol=bool(opsiyon.get('kontrol', VARSAYILAN_KONTROL)),
                    yalniz=bool(opsiyon.get('yalniz', VARSAYILAN_YALNIZ)),
                    taban_bilgi=opsiyon.get('taban_bilgi'))
            else:
                durum, ayrinti = taban_ve_mutasyon(
                    hedef, kapi, argumanlar, mutasyon, iz, cwd=calisma,
                    env=opsiyon.get('env'),
                    kontrol=bool(opsiyon.get('kontrol', VARSAYILAN_KONTROL)),
                    yalniz=bool(opsiyon.get('yalniz', VARSAYILAN_YALNIZ)),
                    taban_bilgi=opsiyon.get('taban_bilgi'))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        if durum == 'GECTI':
            gecen += 1
        elif durum == 'GECTI-TERMINAL':
            gecen_terminal += 1
        elif durum == 'GECTI-BULGU':
            gecen_bulgu += 1
        satirlar.append((kimlik, katman, kural, durum, ayrinti))
        print('  [%d/%d] %-13s %-6s %-34s %s' % (
            len(satirlar), len(tum), kimlik, katman, durum, kural))
        print('         %s' % ayrinti)

    print()
    print('SONUC: %d/%d kural atesledi · %d/%d beklenen bulgu dogrulandi · '
          'taban temiz olmayan=%d' % (
              gecen + gecen_terminal, hata_top + terminal_top, gecen_bulgu,
              bulgu_top, sum(1 for s in satirlar
                             if s[3] in ('TABAN_KIRIK', 'TABAN_KIRLI'))))
    print('SOZLESME: %d/%d HATA (rc=1) · %d/%d TERMINAL (rc=2) · '
          '%d/%d BEKLENEN_BULGU' % (
              gecen, hata_top, gecen_terminal, terminal_top,
              gecen_bulgu, bulgu_top))

    sonuc_yaz(satirlar, meta, KISA)

    kirik = [s for s in satirlar
             if s[3] not in ('GECTI', 'GECTI-TERMINAL', 'GECTI-BULGU')]
    if kirik:
        print('HUKUM: FAIL — ateslemeyen vaka var; kapi kaniti eksik.')
        return 1
    print('HUKUM: PASS — her vaka temiz tabanda sessiz, ihlalde kirmizi/beklenen bulgu.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
