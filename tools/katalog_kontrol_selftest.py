#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""katalog_kontrol_selftest.py — katalog kontrolu sahte GUNCEL uretmesin.

NEDEN VAR
  Ag gerektiren kontrolun kendisi bir kapidir: temiz katalogda GUNCEL, eksik
  modelde BAYAT, bedava kosulu ihlalinde adlandirilmis FAIL, okunamayan
  JSON'da OLCULMEDI vermelidir. Bu test aga cikmaz; `--api-dosya` ve
  `--profil-dosya` ile yerel fikstur kullanir. `make dogrula` ve
  `make dogrula-ci` hedeflerinin on kosuludur; boylece kapinin negatif
  davranisi commit'li bir regresyon kilidi tasir.

KULLANIM
  python3 tools/katalog_kontrol_selftest.py
  python3 tools/katalog_kontrol_selftest.py --ci-denetim [--kok <depo>]

  --ci-denetim: zorunlu push/pull_request workflow'larinda `make
  katalog-kontrol`, canli `tools/katalog_kontrol.py` veya models.dev adimi
  olmadigini; `dogrula-ci` hedefinin cevrimdisi `katalog-selftest` onkosulunu
  korudugunu denetler. Schedule/manual canary kapsam disidir.

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ARAC = KOK / 'tools' / 'katalog_kontrol.py'
ROLLER = (
    'kod-orchestrator',
    'kod-scoper',
    'kod-architect',
    'kod-implementer',
    'kod-implementer-heavy',
    'kod-tester',
    'kod-gate-2a',
    'kod-gate-2b',
    'kod-gate-2c-security',
    'kod-gate',
)
ASGARI = {'context': 10000, 'output': 1000}
AILE = {'aile': 'nemotron', 'ad_oneki': 'Nemotron 3', 'saglayici': 'nvidia'}
OLCULMEDI = 'OLCULMEDI'
# Eski/yazim kaymasi ciktiya sizarsa test bunu ayri bir hata olarak yakalar.
ESKI_OLCULMEDI = ('OLCULEMEDI', 'OLCULMADI')
AG_ADRESI = 'http://127.0.0.1:9'


def _kimlik(ad):
    """Fikstur kisaltmasini gercek `nvidia/<model>` bicimine cevir."""
    return ad if '/' in ad else 'nvidia/' + ad


def profil(farkli=None, politika=None):
    """On rollu, tek kimlikli ve aile sozlesmeli bedava profili fiksturu."""
    bedava = dict.fromkeys(ROLLER, 'openrouter/nvidia/m1')
    if farkli:
        bedava.update(farkli)
    beklenti = dict(AILE)
    beklenti['asgari_limit'] = dict(ASGARI)
    if politika:
        beklenti.update(politika)
    return {
        'profiller': {'bedava': bedava},
        'bedava_politika': beklenti,
    }


def yerel(*kimlikler, **degisiklik):
    return {'openrouter': {'models': {
        _kimlik(ham): {'reasoning': True, 'tool_call': True,
                       **degisiklik.get(ham, degisiklik.get(_kimlik(ham), {}))}
        for ham in kimlikler}}}


def canli(*kimlikler, **degisiklik):
    return {'openrouter': {'models': {
        _kimlik(ham): {
            'name': 'Nemotron 3 Ultra (free)',
            'family': 'nemotron-ultra-free',
            'reasoning': True,
            'tool_call': True,
            'cost': {'input': 0, 'output': 0},
            'limit': {'context': 100000, 'output': 10000},
            **degisiklik.get(ham, degisiklik.get(_kimlik(ham), {})),
        } for ham in kimlikler}}}


def vaka(yerel_veri, canli_veri, beklenen_rc, iz, profil_veri=None,
         ek_args=()):
    with tempfile.TemporaryDirectory(prefix='katalog_kontrol_') as tmp:
        yol = Path(tmp)
        katalog = yol / 'katalog.json'
        api = yol / 'api.json'
        profil_yolu = yol / 'profil.json'
        katalog.write_text(json.dumps(yerel_veri), encoding='utf-8')
        api.write_text(json.dumps(canli_veri), encoding='utf-8')
        profil_yolu.write_text(
            json.dumps(profil_veri if profil_veri is not None else profil()),
            encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(ARAC),
             '--katalog', str(katalog),
             '--profil-dosya', str(profil_yolu),
             '--api-dosya', str(api)] + list(ek_args),
            cwd=str(KOK), capture_output=True, text=True)
        cikti = (r.stdout or '') + (r.stderr or '')

        if r.returncode != beklenen_rc:
            return False, 'rc=%d (beklenen %d) · %s' % (
                r.returncode, beklenen_rc, cikti.strip()[:160])
        izler = (iz,) if isinstance(iz, str) else iz
        eksik = [x for x in izler if x not in cikti]
        if eksik:
            return False, 'iz yok (%s) · %s' % (
                ', '.join(eksik), cikti.strip()[:160])
        if any(eski in cikti for eski in ESKI_OLCULMEDI):
            return False, 'eski yazim OLCULMEDI · %s' % cikti.strip()[:160]
        if (OLCULMEDI in cikti) != (beklenen_rc == 2):
            return False, '%s beklentisi tutmadi · %s' % (
                OLCULMEDI, cikti.strip()[:160])
        if beklenen_rc == 0 and 'BEDAVA: 10/10' not in cikti:
            return False, 'PASS ama BEDAVA: 10/10 yok · %s' % cikti.strip()[:160]
        return True, 'rc=%d · %s' % (r.returncode, ', '.join(izler))


def vaka_ag():
    """Erisilemeyen `--api-url` gercekten OLCULMEDI/rc=2 mi?

    JSON bozuklugu ayri bir daldir; burada gercek ag hatasi (connection
    refused) sinanir. Boylece `--api-dosya` fiksturleri ag dalini
    maskeleyemez.
    """
    with tempfile.TemporaryDirectory(prefix='katalog_kontrol_ag_') as tmp:
        yol = Path(tmp)
        katalog = yol / 'katalog.json'
        profil_yolu = yol / 'profil.json'
        katalog.write_text(json.dumps(yerel('m1')), encoding='utf-8')
        profil_yolu.write_text(json.dumps(profil()), encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(ARAC),
             '--katalog', str(katalog),
             '--profil-dosya', str(profil_yolu),
             '--api-url', AG_ADRESI, '--timeout', '1'],
            cwd=str(KOK), capture_output=True, text=True, timeout=30)
        cikti = (r.stdout or '') + (r.stderr or '')
        if r.returncode != 2:
            return False, 'rc=%d (beklenen 2) · %s' % (
                r.returncode, cikti.strip()[:180])
        for iz in ('KATALOG KONTROL: ' + OLCULMEDI,
                   'BEDAVA: ' + OLCULMEDI):
            if iz not in cikti:
                return False, 'ag izi yok (%s) · %s' % (
                    iz, cikti.strip()[:180])
        if any(eski in cikti for eski in ESKI_OLCULMEDI):
            return False, 'eski yazim OLCULMEDI · %s' % cikti.strip()[:180]
        if 'HUKUM: GUNCEL' in cikti or 'BEDAVA: 10/10' in cikti:
            return False, 'ag hatasinda yesil hukum · %s' % cikti.strip()[:180]
        return True, 'rc=2 · %s' % AG_ADRESI


def _workflow_tetikleri(metin):
    """`on:` altindaki push/pull_request gibi tetikleri kabaca oku."""
    satirlar = metin.splitlines()
    tetikler = set()
    for i, satir in enumerate(satirlar):
        m = re.match(r'^on\s*:\s*(.*)$', satir)
        if not m:
            continue
        satir_ici = m.group(1).strip()
        if satir_ici:
            tetikler.update(re.findall(r'[A-Za-z_]+', satir_ici))
        for alt in satirlar[i + 1:]:
            if not alt.strip():
                continue
            if not alt.startswith((' ', '\t')):
                break
            m2 = re.match(r'^\s+([A-Za-z_]+)\s*:', alt)
            if m2:
                tetikler.add(m2.group(1))
        break
    return tetikler


def _run_bloklari(metin):
    """Yalniz YAML `run:` bloklarini (satir numarasi, metin) dondur."""
    satirlar = metin.splitlines()
    i = 0
    while i < len(satirlar):
        m = re.match(r'^(\s*)(?:-\s+)?run\s*:\s*(.*)$', satirlar[i])
        if not m:
            i += 1
            continue
        girinti = len(m.group(1)) + (2 if satirlar[i].lstrip().startswith('-')
                                      else 0)
        deger = m.group(2).strip()
        if deger and not deger.startswith(('|', '>')):
            yield i + 1, deger
            i += 1
            continue
        i += 1
        while i < len(satirlar):
            satir = satirlar[i]
            if satir.strip() and len(satir) - len(satir.lstrip()) <= girinti:
                break
            if satir.strip():
                yield i + 1, satir
            i += 1


def _emir(satir):
    """Kabuk yorumunu at; bos/yorum satiri canli komut sayilmaz."""
    satir = satir.strip()
    if not satir or satir.startswith('#'):
        return ''
    return satir.split(' #', 1)[0].strip()


def _canli_bulgu(satir):
    """Bir run satirinda canli katalog/models.dev izi varsa neden dondur."""
    if re.search(r'\bmodels\.dev\b', satir, re.IGNORECASE):
        return 'models.dev ag adimi'
    if re.search(r'\bmake(?:\s+[^\n;&|]*)?\s+(?:katalog|bedava)-kontrol\b',
                 satir):
        return 'canli katalog hedefi'
    if re.search(r'\btools/katalog_kontrol\.py\b', satir):
        # Yalniz loopback/yerel dosya fiksturuyle calisan dal cevrimdisidir;
        # varsayilan URL veya --api-url olmadan canli katalogdur.
        if ('--profil-only' in satir
                and ('127.0.0.1' in satir or '--api-dosya' in satir)):
            return None
        return 'tools/katalog_kontrol.py canli cagrisi'
    return None


def _make_hedef_govdesi(metin, hedef):
    """Makefile'daki bir hedefin tab ile baslayan govde satirlarini dondur."""
    satirlar = metin.splitlines()
    basladi = False
    govde = []
    for satir in satirlar:
        if re.match(r'^%s\s*:' % re.escape(hedef), satir):
            basladi = True
            continue
        if basladi:
            if satir.startswith('\t'):
                govde.append(satir)
            elif satir.strip():
                break
    return govde


def _make_hedef_satiri(metin, hedef):
    for satir in metin.splitlines():
        m = re.match(r'^%s\s*:\s*(.*)$' % re.escape(hedef), satir)
        if m:
            return m.group(1)
    return None


def ci_katalog_denetle(kok):
    """Zorunlu CI workflow'larinda canli katalog izini ve offline kapıyı denetle."""
    bulgular = []
    kok = Path(kok)
    wf_dizin = kok / '.github' / 'workflows'
    if not wf_dizin.is_dir():
        return ['CI-KATALOG-01 workflow dizini yok: %s' % wf_dizin], []
    wf_dosyalari = sorted(list(wf_dizin.glob('*.yml'))
                          + list(wf_dizin.glob('*.yaml')))
    if not wf_dosyalari:
        return ['CI-KATALOG-01 workflow dosyasi yok'], []

    zorunlu = []
    for yol in wf_dosyalari:
        try:
            metin = yol.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as e:
            bulgular.append('CI-KATALOG-02 %s okunamadi: %s'
                            % (yol.relative_to(kok), type(e).__name__))
            continue
        tetikler = _workflow_tetikleri(metin)
        if not ({'push', 'pull_request', 'pull_request_target'} & tetikler):
            continue
        rel = str(yol.relative_to(kok))
        zorunlu.append(rel)
        for no, satir in _run_bloklari(metin):
            emir = _emir(satir)
            neden = _canli_bulgu(emir) if emir else None
            if neden:
                bulgular.append('CI-KATALOG-03 %s:%d canli katalog: %s'
                                % (rel, no, neden))

    if not zorunlu:
        bulgular.append('CI-KATALOG-01 push/pull_request workflow yok')

    try:
        make = (kok / 'Makefile').read_text(encoding='utf-8')
    except (OSError, UnicodeError) as e:
        bulgular.append('CI-KATALOG-02 Makefile okunamadi: %s'
                        % type(e).__name__)
        return bulgular, zorunlu

    dogrula_ci = _make_hedef_satiri(make, 'dogrula-ci')
    if dogrula_ci is None:
        bulgular.append('CI-KATALOG-04 dogrula-ci hedefi yok')
    else:
        onkosullar = dogrula_ci.split(';', 1)[0].split()
        if 'katalog-selftest' not in onkosullar:
            bulgular.append('CI-KATALOG-04 dogrula-ci katalog-selftest '
                            'onkosulu yok')
        if any(x in onkosullar for x in ('katalog-kontrol', 'bedava-kontrol')):
            bulgular.append('CI-KATALOG-03 dogrula-ci canli katalog hedefi '
                            'iceriyor')
    for satir in _make_hedef_govdesi(make, 'dogrula-ci'):
        emir = _emir(satir)
        if (re.search(r'\b(?:katalog|bedava)-kontrol\b', emir)
                or re.search(r'\bmodels\.dev\b', emir, re.IGNORECASE)):
            bulgular.append('CI-KATALOG-03 dogrula-ci canli katalog komutu '
                            'iceriyor')
            break

    offline_govde = _make_hedef_govdesi(make, 'katalog-selftest')
    if not any('katalog_kontrol_selftest.py' in satir
               for satir in offline_govde):
        bulgular.append('CI-KATALOG-05 katalog-selftest cevrimdisi '
                        'selftesti cagirmiyor')
    for satir in offline_govde:
        emir = _emir(satir)
        if (re.search(r'\b(?:katalog|bedava)-kontrol\b', emir)
                or re.search(r'\bmodels\.dev\b', emir, re.IGNORECASE)):
            bulgular.append('CI-KATALOG-03 katalog-selftest canli katalog '
                            'komutu iceriyor')
            break

    # dogrula-ci gercekten zorunlu bir workflow'da kosuyor mu? Aksi halde
    # offline on kosul kagitta kalir.
    dogrula_ci_workflow = False
    for rel in zorunlu:
        metin = (kok / rel).read_text(encoding='utf-8')
        for _no, satir in _run_bloklari(metin):
            if re.search(r'\bmake(?:\s+[^\n;&|]*)?\s+dogrula-ci\b',
                         _emir(satir)):
                dogrula_ci_workflow = True
                break
    if not dogrula_ci_workflow:
        bulgular.append('CI-KATALOG-06 zorunlu workflow make dogrula-ci '
                        'cagirmiyor')
    return bulgular, zorunlu


def ci_katalog_denetim(argv):
    kok = KOK
    if '--kok' in argv:
        i = argv.index('--kok')
        if i + 1 >= len(argv):
            print('CI-KATALOG: FAIL — --kok degeri yok')
            return 2
        kok = Path(argv[i + 1])
    print('CI-KATALOG DENETIMI — zorunlu push/pull_request workflowlari')
    try:
        bulgular, zorunlu = ci_katalog_denetle(kok)
    except (OSError, UnicodeError, ValueError) as e:
        print('CI-KATALOG: FAIL — arac: %s' % type(e).__name__)
        return 2
    if zorunlu:
        print('  kapsam: %s' % ', '.join(zorunlu))
    if bulgular:
        for bulgu in bulgular:
            print('FAIL ' + bulgu)
        print('CI-KATALOG: FAIL — %d bulgu' % len(bulgular))
        return 1
    print('  canli katalog/models.dev adimi: yok')
    print('  cevrimdisi katalog selftesti: dogrula-ci -> katalog-selftest')
    print('CI-KATALOG: PASS — 0 bulgu')
    return 0


def main():
    if '--ci-denetim' in sys.argv:
        return ci_katalog_denetim(sys.argv)
    print('KATALOG KONTROL OZ-TESTI — ag yok, yerel api.json + profil fiksturu')
    dokuz = profil()
    del dokuz['profiller']['bedava']['kod-tester']
    meta = {rol: 'openrouter/meta/m1' for rol in ROLLER}
    vakalar = [
        ('guncel katalog', yerel('m1'), canli('m1'), 0,
         'BEDAVA: 10/10', None),
        ('maliyet drifti', yerel('m1'),
         canli('m1', m1={'cost': {'input': 0.5, 'output': 0}}), 1,
         'MALIYET', None),
        ('limit drifti', yerel('m1'),
         canli('m1', m1={'limit': {'context': 1000, 'output': 10000}}), 1,
         'LIMIT_YETERSIZ', None),
        ('maliyet yok', yerel('m1'), canli('m1', m1={'cost': None}), 1,
         'MALIYET_YOK', None),
        ('limit yok', yerel('m1'), canli('m1', m1={'limit': None}), 1,
         'LIMIT_YOK', None),
        ('yetenek drifti', yerel('m1'),
         canli('m1', m1={'reasoning': False}), 1, 'YETENEK_FARKLI', None),
        ('eksik alan', yerel('m1'), canli('m1', m1={'reasoning': None}), 1,
         'ALAN_YOK', None),
        ('deprecated model', yerel('m1'),
         canli('m1', m1={'status': 'deprecated'}), 1, 'DURUM', None),
        ('aile adi drifti', yerel('m1'),
         canli('m1', m1={'name': 'Baska Model'}), 1, 'AILE_FARKLI', None),
        ('aile family drifti', yerel('m1'),
         canli('m1', m1={'family': 'other-family'}), 1,
         'AILE_FARKLI', None),
        ('aile saglayici drifti', yerel('meta/m1'), canli('meta/m1'), 1,
         'AILE_FARKLI', profil(meta)),
        # Uc vaka beklentinin koddan degil `bedava_politika`dan okundugunu
        # kanitlar: canli kayit ayni kalir, yalniz politika alani sapar.
        ('aile politikasi drifti', yerel('m1'), canli('m1'), 1,
         'AILE_FARKLI', profil(politika={'aile': 'baska'})),
        ('ad oneki politikasi drifti', yerel('m1'), canli('m1'), 1,
         'AILE_FARKLI', profil(politika={'ad_oneki': 'Baska Model'})),
        ('saglayici politikasi drifti', yerel('m1'), canli('m1'), 1,
         'AILE_FARKLI', profil(politika={'saglayici': 'meta'})),
        ('aile politikasi eksik', yerel('m1'), canli('m1'), 1,
         ('BEDAVA: FAIL', 'bedava_politika.aile'),
         profil(politika={'aile': None})),
        ('kimlik drifti', yerel('m1', 'm2'), canli('m1', 'm2'), 1,
         'TEK_KIMLIK_DEGIL',
         profil({'kod-tester': 'openrouter/nvidia/m2'})),
        ('eksik model adiyla', yerel('m1', 'm2'), canli('m1'), 1,
         'openrouter/nvidia/m2', None),
        ('allowlist disi', yerel('m2'), canli('m1'), 1, 'KATALOGDA_YOK',
         None),
        ('yerel yetenek', yerel('m1', m1={'tool_call': False}), canli('m1'),
         1, 'KATALOG_YETENEK', None),
        ('bozuk yerel alan', yerel('m1', m1={'reasoning': 'yes'}),
         canli('m1'), 1, 'KATALOG_BOZUK', None),
        ('eksik saglayici', yerel('m1'), {'baska': {'models': {}}}, 1,
         ('SAGLAYICI_YOK', 'ROL kod-orchestrator'), None),
        ('bozuk saglayici', yerel('m1'), {'openrouter': {}}, 1,
         'SAGLAYICI_BOZUK', None),
        ('bozuk rol', yerel('m1'), canli('m1'), 1,
         ('ROL_BOZUK', 'ROL_SAYISI'), profil({'kod-tester': 'm2'})),
        ('bozuk api json', yerel('m1'), [], 2, 'OLCULMEDI', None),
        ('bozuk yerel katalog', {'openrouter': {}}, canli('m1'), 2,
         'OLCULMEDI', None),
        ('profil 9 rol', yerel('m1'), canli('m1'), 1, 'rol sayisi 9', dokuz),
        ('profil-only', yerel('m1'), canli('m1'), 0,
         ('KATALOG KONTROL — yalniz bedava profili', 'BEDAVA: 10/10'),
         None, '--profil-only'),
    ]
    gecen = 0
    for ad, y, c, rc, iz, profil_veri, *ek_args in vakalar:
        try:
            ok, ayrinti = vaka(y, c, rc, iz, profil_veri, tuple(ek_args))
        except Exception as e:  # noqa: BLE001 - test kosucusu hatayi raporlar
            ok, ayrinti = False, 'ISTISNA: %s' % e
        gecen += 1 if ok else 0
        print('  %-28s %-4s %s' % (ad, 'PASS' if ok else 'FAIL', ayrinti))
    try:
        ok, ayrinti = vaka_ag()
    except Exception as e:  # noqa: BLE001 - test kosucusu hatayi raporlar
        ok, ayrinti = False, 'ISTISNA: %s' % e
    gecen += 1 if ok else 0
    print('  %-28s %-4s %s' % ('ag erisilemez', 'PASS' if ok else 'FAIL',
                               ayrinti))

    print()
    toplam = len(vakalar) + 1
    if gecen == toplam:
        print('KATALOG KONTROL OZ-TEST: %d/%d gecti' % (gecen, toplam))
        return 0
    print('KATALOG KONTROL OZ-TEST: FAIL — %d/%d' % (gecen, toplam))
    return 1


if __name__ == '__main__':
    sys.exit(main())
