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
  python3 tools/mutasyon_bataryasi.py [--ayrintili]

CIKIS
  0  : butun vakalar sozlesmesini sagladi (taban sessiz; hata rc!=0 veya
       beklenen-bulgu isaretli)
  1  : en az bir vaka ateslemedi / taban kirlendi / mutasyon uygulanamadi
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
# check_models sabit katalogu kullanir (ag/canli models.dev gerekmez).
os.environ.setdefault('ATLAS_MODEL_KATALOG', str(KOK / 'tools' / 'mutasyon_katalog.json'))
AYRINTILI = '--ayrintili' in sys.argv
ATLA = shutil.ignore_patterns('.git', '__pycache__', 'node_modules', '.pytest_cache',
                              '.ruff_cache', '.DS_Store')

# Anahtar PARCALI yazilir: bu dosya depoda durur ve sir tarayicisi (H4) bitisik
# deseni yakalar. Parcali literal tarayiciyi yaniltmak icin degil, gercek bir
# anahtarin depoya sizmasini onlemek icin boyle: fikstur oldugu gorunur.
SAHTE_ANAHTAR = 'AKIA' + 'Z7Q2M4XK9PLR3TWV'

DEC_BASLIKLAR = ['Etik Kurul', 'Cikar Catismasi', 'Finansman', 'credit',
                 'Veri Erisilebilirligi', 'Yapay Zeka']
# Yalniz REC ailesi: "tek ihlal -> yalniz hedef FAIL etiketi" ve "ihlali geri al
# -> yeniden yesil" sozlesmesini her kosuda zorunlu kilar.
FAIL_ETIKET = re.compile(r'\bFAIL\s+([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})\b')
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


def taban_ve_mutasyon(kok, kapi, argumanlar, mutasyon, iz, taban_rc=0, cwd=None,
                      terminal=False, env=None, kontrol=False, yalniz=False):
    """(durum, ayrinti) dondurur. taban_rc: temiz kopyada beklenen cikis kodu.

    `iz` bir dize veya dize dizisi olabilir; hepsi mutasyon ciktisinda aranir.
    terminal=True ise temiz tabanda GATE_TAMPERED/TERMINAL izi BULUNMAZ, mutasyon
    sonrasi rc=2, `GATE_TAMPERED` ve `TERMINAL FAIL` birlikte aranir; yalniz
    kirmizi yanmak terminal sozlesmesini kanitlamaz.
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
    if kontrol:
        yedek = kok.parent / (kok.name + '_kontrol_yedek')
        if yedek.exists():
            shutil.rmtree(yedek)
        shutil.copytree(kok, yedek, symlinks=True)

    rc0, o0 = kos(komut, cwd=calisma, env=env)
    if rc0 != taban_rc:
        return 'TABAN_KIRIK', 'taban rc=%d (beklenen %d) · %s' % (
            rc0, taban_rc, o0.strip().splitlines()[-1] if o0.strip() else '')
    if yalniz and FAIL_ETIKET.findall(o0):
        return 'TABAN_KIRLI', 'temiz tabanda FAIL etiketi var: %s' % (
            ', '.join(sorted(set(FAIL_ETIKET.findall(o0)))))
    if terminal and any(x in o0 for x in ('GATE_TAMPERED', 'TERMINAL FAIL') + tuple(izler)):
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
        etiketler = FAIL_ETIKET.findall(o1)
        if iz not in etiketler:
            return 'ATESLEMEDI', 'beklenen FAIL %s yok; FAIL etiketleri=%s' % (
                iz, ', '.join(sorted(set(etiketler))) or 'yok')
        diger = sorted(set(etiketler) - {iz})
        if diger:
            return 'ATESLEMEDI', 'baska kural etiketi sizdi: %s' % ', '.join(diger)

    if kontrol:
        shutil.rmtree(kok)
        shutil.copytree(yedek, kok, symlinks=True)
        shutil.rmtree(yedek)
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
        return 'GECTI', ('taban rc=0 · FAIL iz yok · mutasyon rc=2 · '
                         'GATE_TAMPERED+TERMINAL · FAIL iz=%s (yalniz) · '
                         'kontrol rc=0 · FAIL iz yok' % '+'.join(izler))
    if kontrol:
        return 'GECTI', ('taban rc=0 · FAIL iz yok · mutasyon rc=%d · '
                         'FAIL iz=%s (yalniz) · kontrol rc=0 · FAIL iz yok' % (
                             rc1, '+'.join(izler)))
    return 'GECTI', 'taban rc=0 · mutasyon rc=%d · iz=%s' % (rc1, '+'.join(izler))


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


def _tsl03_hazirla(k):
    """TSL-03: 8 zorunlu artefakt + kapi betiginin kendi --uret manifesti."""
    sandbox = k / 'sandbox_teslim'
    for ad in TESLIM_ZORUNLU:
        yaz(sandbox / ad, '# artefakt\n')
    r = subprocess.run(
        [sys.executable, str(k / 'ATLAS_SABLONLAR' / 'scripts' / 'teslim_imza.py'),
         '--uret'], cwd=str(sandbox), capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        # Taban TSL-01/TSL-06 ile kirilir; sessizce yesil kalmasin.
        yaz(sandbox / 'URETIM-HATASI.txt',
            (r.stdout or '') + (r.stderr or '') + '\n')


def _tsl03(k):
    """Tek ihlal: manifest uretildikten sonra bir artefakt degistirilir."""
    yaz(k / 'sandbox_teslim' / '03-FAZ-3-MASTER-v5.5.md', '# artefakt degisti\n')


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


def taban_ve_bulgu(kok, kapi, argumanlar, mutasyon, iz, cwd=None, env=None):
    """Kirmizi uretmeyen kural icin: temiz tabanda iz YOK, ihlalde iz VAR."""
    betik = kok / kapi
    if not betik.is_file():
        return 'EKSIK', 'kapi betigi yok: %s' % kapi
    komut = [sys.executable, betik] + argumanlar(kok)
    calisma = cwd or kok
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
    return 'GECTI-BULGU', 'taban sessiz · mutasyon bulgusu=%s (rc=%d)' % (iz, rc1)


def vakalar():
    """Her vaka: (kimlik, katman, kural, kapi, argumanlar, mutasyon, iz[, 'BULGU'])."""
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
        ('CITE-01', 'ATLAS', 'metindeki atif kaynakcada', 'ATLAS_SABLONLAR/scripts/cite_match.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'cite.md')],
         lambda k: degistir(k, 'sandbox/cite.md', '(Yazar, 2020)', '(Diger, 2021)'),
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
        ('FRZ-01T', 'KOD', 'profil tamperi GATE_TAMPERED terminal',
         'KOD_SABLONLAR/scripts/freeze_check.py',
         lambda k: ['--taban', str(k / '_KOSU' / 'gate' / 'BASELINE.json')],
         lambda k: yaz(k / 'kod_profil.json', '{"profil": "degisti"}\n'),
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
         'FRZ-08', {'terminal': True, 'kur': _frz08_hazirla, 'env': _frz08_env()}),
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
         'TST-06', 'BULGU', {'cwd': 'sandbox_tst/gitdepo', 'kur': _tst_hazirla}),
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
         lambda k: degistir(k, 'sandbox_perm/.opencode/agent/ajan.md',
                            '  read:\n    "*": allow\n',
                            '  read:\n    "*": allow\n    "**/*.log": deny\n'),
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
         lambda k: degistir(k, 'sandbox_perm/.opencode/agent/ajan.md',
                            '  read:\n    "*": allow\n',
                            '  read:\n    "*": allow\n    "/etc/passwd": deny\n'),
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


def main():
    print('MUTASYON BATARYASI — ATLAS + KOD kapi kurallari')
    print('kaynak: %s' % KOK.name)
    print('kural: once TEMIZ TABAN, sonra tek ihlal; kirmizi veya beklenen bulgu.')
    print()

    try:
        _src01_fikstur(KOK, bozuk=True)
    except (OSError, ValueError) as e:
        print('HUKUM: FAIL — %s' % e)
        return 1

    gecen = 0
    gecen_bulgu = 0
    satirlar = []
    tum = vakalar()
    kimlikler = [v[0] for v in tum]
    yinelenen = sorted({k for k in kimlikler if kimlikler.count(k) > 1})
    if yinelenen:
        print('HUKUM: FAIL — yinelenen vaka ID: %s' % ', '.join(yinelenen))
        return 1
    for vaka in tum:
        opsiyon = {}
        if len(vaka) >= 8 and vaka[7] == 'BULGU':
            kimlik, katman, kural, kapi, argumanlar, mutasyon, iz = vaka[:7]
            bulgu_modu = True
            if len(vaka) >= 9 and isinstance(vaka[8], dict):
                opsiyon = vaka[8]
        else:
            kimlik, katman, kural, kapi, argumanlar, mutasyon, iz = vaka[:7]
            bulgu_modu = False
            if len(vaka) == 8 and isinstance(vaka[7], dict):
                opsiyon = vaka[7]
        tmp = Path(tempfile.mkdtemp(prefix='atlas_mut_'))
        try:
            hedef = tmp / 'depo'
            shutil.copytree(KOK, hedef, symlinks=True, ignore=ATLA)
            hazirla(hedef, opsiyon)
            calisma = hedef / opsiyon['cwd'] if opsiyon.get('cwd') else hedef
            if bulgu_modu:
                durum, ayrinti = taban_ve_bulgu(
                    hedef, kapi, argumanlar, mutasyon, iz, cwd=calisma,
                    env=opsiyon.get('env'))
            else:
                durum, ayrinti = taban_ve_mutasyon(
                    hedef, kapi, argumanlar, mutasyon, iz, cwd=calisma,
                    terminal=bool(opsiyon.get('terminal')),
                    env=opsiyon.get('env'),
                    kontrol=bool(opsiyon.get('kontrol')),
                    yalniz=bool(opsiyon.get('yalniz')))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        if durum == 'GECTI':
            gecen += 1
        elif durum == 'GECTI-BULGU':
            gecen_bulgu += 1
        satirlar.append((kimlik, katman, kural, durum, ayrinti))
        print('  [%d/%d] %-13s %-6s %-34s %s' % (
            len(satirlar), len(tum), kimlik, katman, durum, kural))
        print('         %s' % ayrinti)

    print()
    toplam_bulgu = sum(1 for v in tum if len(v) >= 8 and v[7] == 'BULGU')
    print('SONUC: %d/%d kural atesledi · %d/%d beklenen bulgu dogrulandi · '
          'taban temiz olmayan=%d' % (
              gecen, len(tum) - toplam_bulgu, gecen_bulgu, toplam_bulgu,
              sum(1 for s in satirlar if s[3] in ('TABAN_KIRIK', 'TABAN_KIRLI'))))

    kirik = [s for s in satirlar if s[3] not in ('GECTI', 'GECTI-BULGU')]
    if kirik:
        print('HUKUM: FAIL — ateslemeyen vaka var; kapi kaniti eksik.')
        return 1
    print('HUKUM: PASS — her vaka temiz tabanda sessiz, ihlalde kirmizi/beklenen bulgu.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
