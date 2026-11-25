#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutasyon_anlatim_kapisi_selftest — anlatim kapisinin negatif kontrolleri.

Kapi gercekten reddediyor mu? Her vaka gecici bir kokte kurulur; taban
katalog 109 tarihsel + 31 guncel vakadan olusur. Pozitif taban PASS vermeli;
tek bir sayi, sozlesme, uyelik, takma ad veya defter satiri bozulunca kapi
rc=1 ile kapanmalidir.

KULLANIM
  python3 tools/mutasyon_anlatim_kapisi_selftest.py

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ARAC = KOK / 'tools' / 'mutasyon_anlatim_kapisi.py'


def _vaka(kimlik, sozlesme):
    durum = {
        'HATA': 'GECTI',
        'TERMINAL': 'GECTI-TERMINAL',
        'BEKLENEN_BULGU': 'GECTI-BULGU',
    }[sozlesme]
    return {'id': kimlik, 'sozlesme': sozlesme, 'durum': durum,
            'gecti': True}


def _katalog():
    """109 tarihsel + 31 guncel = 140 vaka."""
    vakalar = []
    for i in range(84):
        vakalar.append(_vaka('H-%03d' % (i + 1), 'HATA'))
    for i in range(6):
        vakalar.append(_vaka('T-%03d' % (i + 1), 'TERMINAL'))
    for i in range(18):
        vakalar.append(_vaka('B-%03d' % (i + 1), 'BEKLENEN_BULGU'))
    vakalar.append(_vaka('T-ALIAS', 'TERMINAL'))
    for i in range(21):
        vakalar.append(_vaka('H2-%03d' % (i + 1), 'HATA'))
    vakalar.append(_vaka('T2-001', 'TERMINAL'))
    for i in range(9):
        vakalar.append(_vaka('B2-%03d' % (i + 1), 'BEKLENEN_BULGU'))
    return vakalar


def _yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding='utf-8')


def _json_yaz(yol, veri):
    _yaz(yol, json.dumps(veri, ensure_ascii=False, indent=2) + '\n')


def _taban(kok):
    vakalar = _katalog()
    tarihsel = [v['id'] for v in vakalar[:109]]
    _json_yaz(kok / 'tools' / 'mutasyon_sonuc.json', {
        'schema': 'MUTASYON-SONUC/v1',
        'kaynak_sha256': 'b' * 64,
        'kisa': False,
        'sayilar': {'vaka': len(vakalar), 'gecti': len(vakalar), 'kalan': 0},
        'vakalar': vakalar,
    })
    _json_yaz(kok / 'tools' / 'mutasyon_tarihsel_snapshot.json', {
        'schema': 'MUTASYON-TARIHsel/v1',
        'surum': '12.128',
        'commit': '588082a',
        'kaynak': 'tools/mutasyon_bataryasi.py',
        'kaynak_sha256': 'a' * 64,
        'takma_adlar': {'T-ALIAS': 'T-001'},
        'vakalar': tarihsel,
    })
    _json_yaz(kok / 'tools' / 'iddia_defteri.json', {
        'iddialar': [
            {'id': 'IDD-04',
             'iddia': 'mutasyon bataryasi 113/113 vaka atesledi',
             'beklenen': '113/113'},
            {'id': 'IDD-05',
             'iddia': 'mutasyon bataryasi 27/27 beklenen bulgu',
             'beklenen': '27/27'},
            {'id': 'IDD-39',
             'iddia': 'mutasyon katalogunda 140 vaka '
                      '(113 atesleyen + 27 beklenen-bulgu)',
             'beklenen': '140'},
            {'id': 'IDD-52',
             'iddia': 'ayrik sozlesme ozeti 105/105 HATA, 8/8 TERMINAL, '
                      '27/27 beklenen-bulgu',
             'beklenen': '105/105'},
            {'id': 'IDD-56',
             'iddia': 'tarihsel 109 vakalik snapshot: 109/91/18',
             'beklenen': '109/91/18'},
        ],
    })
    _yaz(kok / 'README.md', '# ATLAS\n')
    _yaz(kok / 'README.tr.md',
         'Mutation battery **113/113 firing cases + 27/27 expected findings** '
         'over 117 verified rules.\n\n'
         'Katalog 140 vakadır:\n'
         '113 ateşleyen (105 HATA + 8 TERMINAL) + 27 beklenen-bulgu.\n')
    _yaz(kok / 'README.en.md',
         'The current battery is **113/113** firing cases plus **27/27** '
         'expected findings over **117** verified rules.\n')
    _yaz(kok / 'docs' / 'README.md',
         'Güncel katalog **140 vaka = 113 ateşleyen (105 HATA + 8 TERMINAL)\n'
         '+ 27 beklenen-bulgu**; 117 doğrulanan kural.\n')
    _yaz(kok / 'docs' / 'EN' / 'QUICKSTART.md',
         'SONUC: 113/113 kural atesledi · 27/27 beklenen bulgu dogrulandi · '
         'taban temiz olmayan=0\n'
         'SOZLESME: 105/105 HATA (rc=1) · 8/8 TERMINAL (rc=2) · '
         '27/27 BEKLENEN_BULGU\n')
    _yaz(kok / 'docs' / 'DERSLER_v1_2026-08-30.md',
         '| 12.128 | tarihsel | 109 vaka; 91 kırmızı; 18 beklenen-bulgu | '
         '109 = 91 hata + 18 beklenen-bulgu | 0 | 0 | KABUL | test |\n'
         '| 12.130 | tarihsel | 109 vaka / 91 ateşleme + 18 beklenen bulgu | '
         '0 | 0 | KOSULLU | test |\n'
         '| 12.166 | guncel | 140 vaka = 113 atesleyen + 27 beklenen | '
         '0 | 0 | KABUL | test |\n')


def _kos(kok):
    r = subprocess.run([sys.executable, str(ARAC), '--kok', str(kok),
                        '--kontrol'], cwd=str(kok), capture_output=True,
                       text=True, timeout=60)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def _degistir(kok, rel, eski, yeni):
    yol = kok / rel
    metin = yol.read_text(encoding='utf-8')
    if metin.count(eski) != 1:
        raise RuntimeError('%s: %r tam 1 kez gecmiyor' % (rel, eski))
    yol.write_text(metin.replace(eski, yeni), encoding='utf-8')


def _katalog_degistir(kok, kimlik, alan, deger):
    yol = kok / 'tools' / 'mutasyon_sonuc.json'
    veri = json.loads(yol.read_text(encoding='utf-8'))
    for vaka in veri['vakalar']:
        if vaka['id'] == kimlik:
            vaka[alan] = deger
            break
    else:
        raise RuntimeError('katalogda vaka yok: %s' % kimlik)
    _json_yaz(yol, veri)


def _snapshot_degistir(kok, islem):
    yol = kok / 'tools' / 'mutasyon_tarihsel_snapshot.json'
    veri = json.loads(yol.read_text(encoding='utf-8'))
    islem(veri)
    _json_yaz(yol, veri)


def main():
    hatalar = []
    toplam = 0

    def bekle(ad, kosul, ayrinti=''):
        nonlocal toplam
        toplam += 1
        if kosul:
            print('PASS  ' + ad)
        else:
            print('FAIL  ' + ad)
            if ayrinti:
                print('      ' + ayrinti.replace('\n', '\n      ')[-1800:])
            hatalar.append(ad)

    with tempfile.TemporaryDirectory(prefix='mutasyon-anlatim-') as gecici:
        temel = Path(gecici) / 'taban'
        _taban(temel)

        r, cikti = _kos(temel)
        bekle('pozitif taban PASS', r == 0 and 'HUKUM: PASS' in cikti, cikti)

        # 1) Guncel kamu dosyasinda 140/140: tek-sozlesmeli anlatim.
        kok = Path(gecici) / 'vaka-140-140'
        shutil.copytree(temel, kok)
        _yaz(kok / 'README.md', '# ATLAS\n\n140/140 vaka kirmizi.\n')
        r, cikti = _kos(kok)
        bekle('140/140 tek-sozlesmeli ifade reddedilir',
              r != 0 and '140/140' in cikti, cikti)

        # 2) Tarihsel denklem 109 = 90 + 19: capa sayisi tutmaz.
        kok = Path(gecici) / 'vaka-tarihsel-denklem'
        shutil.copytree(temel, kok)
        _degistir(kok, 'docs/DERSLER_v1_2026-08-30.md',
                  '109 = 91 hata + 18 beklenen-bulgu',
                  '109 = 90 hata + 19 beklenen-bulgu')
        r, cikti = _kos(kok)
        bekle('tarihsel 109/91/18 denklemi reddedilir',
              r != 0 and 'katalogdan turetilen' in cikti, cikti)

        # 3) Katalogda bir bulgu HATA'ya donerse tarihsel turetme 92/17 olur.
        kok = Path(gecici) / 'vaka-katalog-sozlesme'
        shutil.copytree(temel, kok)
        _katalog_degistir(kok, 'B-001', 'sozlesme', 'HATA')
        _katalog_degistir(kok, 'B-001', 'durum', 'GECTI')
        r, cikti = _kos(kok)
        bekle('katalog sozlesme kaymasi reddedilir',
              r != 0 and 'tarihsel sayilar' in cikti, cikti)

        # 4) Tarihsel uyelikten bir ID duserse 109 -> 108.
        kok = Path(gecici) / 'vaka-snapshot-eksik'
        shutil.copytree(temel, kok)
        _snapshot_degistir(kok, lambda v: v['vakalar'].remove('B-018'))
        r, cikti = _kos(kok)
        bekle('eksik tarihsel uyelik reddedilir',
              r != 0 and 'tarihsel sayilar' in cikti, cikti)

        # 5) Takma ad hedefi katalogda yoksa fail-closed.
        kok = Path(gecici) / 'vaka-takma-kayip'
        shutil.copytree(temel, kok)
        _snapshot_degistir(kok, lambda v: v['takma_adlar'].update(
            {'T-ALIAS': 'T-YOK'}))
        r, cikti = _kos(kok)
        bekle('takma ad hedefi yoksa reddedilir',
              r != 0 and 'takma ad hedefi' in cikti, cikti)

        # 6) Takma ad bir bulguya cozulurse kirmizi sayim bozulur.
        kok = Path(gecici) / 'vaka-takma-bulgu'
        shutil.copytree(temel, kok)
        _snapshot_degistir(kok, lambda v: v['takma_adlar'].update(
            {'T-ALIAS': 'B-001'}))
        r, cikti = _kos(kok)
        bekle('takma ad bulguya cozulemez',
              r != 0 and 'bulguya cozulemez' in cikti, cikti)

        # 7) Iddia defteri guncel toplami kayarsa reddedilir.
        kok = Path(gecici) / 'vaka-defter'
        shutil.copytree(temel, kok)
        yol = kok / 'tools' / 'iddia_defteri.json'
        defter = json.loads(yol.read_text(encoding='utf-8'))
        for kayit in defter['iddialar']:
            if kayit['id'] == 'IDD-39':
                kayit['beklenen'] = '139'
        _json_yaz(yol, defter)
        r, cikti = _kos(kok)
        bekle('iddia defteri sayi kaymasi reddedilir',
              r != 0 and 'IDD-39' in cikti, cikti)

        # 8) Guncel kamu dosyasinda etiketsiz 109 toplami reddedilir.
        kok = Path(gecici) / 'vaka-bayat-109'
        shutil.copytree(temel, kok)
        _yaz(kok / 'README.en.md',
             (kok / 'README.en.md').read_text(encoding='utf-8')
             + '\nCurrent scope: 109 cases.\n')
        r, cikti = _kos(kok)
        bekle('guncel baglamda etiketsiz 109 reddedilir',
              r != 0 and 'etiketsiz' in cikti, cikti)

        # 9) Guncel DERSLER sayaci 140/140'a kayarsa reddedilir.
        kok = Path(gecici) / 'vaka-guncel-sayac'
        shutil.copytree(temel, kok)
        _degistir(kok, 'docs/DERSLER_v1_2026-08-30.md',
                  '140 vaka = 113 atesleyen + 27 beklenen',
                  '140 vaka = 140 atesleyen + 0 beklenen')
        r, cikti = _kos(kok)
        bekle('guncel 140/113/27 sayaci reddedilir',
              r != 0 and 'katalogdan turetilen' in cikti, cikti)

        # 10) Yinelenen katalog ID'si sessizce sayilmaz.
        kok = Path(gecici) / 'vaka-yinelenen'
        shutil.copytree(temel, kok)
        yol = kok / 'tools' / 'mutasyon_sonuc.json'
        veri = json.loads(yol.read_text(encoding='utf-8'))
        veri['vakalar'].append(dict(veri['vakalar'][0]))
        veri['sayilar']['vaka'] += 1
        _json_yaz(yol, veri)
        r, cikti = _kos(kok)
        bekle('yinelenen katalog ID reddedilir',
              r != 0 and 'yinelenen vaka ID' in cikti, cikti)

        # 11) Batarya kaydi yesil degilse katalog kanit sayilmaz.
        kok = Path(gecici) / 'vaka-gecti-false'
        shutil.copytree(temel, kok)
        _katalog_degistir(kok, 'H-001', 'gecti', False)
        r, cikti = _kos(kok)
        bekle('gecti=false katalog reddedilir',
              r != 0 and 'gecti=true degil' in cikti, cikti)

    print()
    print('ANLATIM KAPISI OZ-TEST: %d/%d' % (toplam - len(hatalar), toplam))
    if hatalar:
        print('HUKUM: FAIL — %s' % ', '.join(hatalar))
        return 1
    print('HUKUM: PASS — pozitif taban ve 11 negatif vaka beklendigi gibi.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
