#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""katalog_yenile_selftest.py — tek komutlu katalog yenileme akisinin negatif kilidi.

Gecici bir git kokunde gercek `model_katalog_uret.py` ve sahte bir
`katalog_kontrol.py` ile calisir; aga cikmaz. Sunlari olcer:

  - yalniz `_kaynak` tarihi degisen aday incelemeye sunulmadan reddedilir,
  - fark yoksa aday hazir sayilmaz,
  - beklenen model farki varsa aday hazir olur ama hedef katalog DEGISMEZ,
  - uretim/kontrol hatasinda ve izlenmeyen aktif dosyada hedef degismez.

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / 'tools'))
import katalog_yenile as ky  # noqa: E402

STUB = '''#!/usr/bin/env python3
import argparse
import json
import os
import sys

p = argparse.ArgumentParser()
p.add_argument("--katalog", required=True)
p.add_argument("--api-dosya", required=True)
a = p.parse_args()
for yol in (a.katalog, a.api_dosya):
    try:
        with open(yol, encoding="utf-8") as f:
            json.load(f)
    except Exception as hata:
        print("STUB: okunamadi: %s" % hata)
        sys.exit(2)
print("SONUC: 9/9 gecerli · 0 bulgu")
print("HUKUM: GUNCEL")
sys.exit(int(os.environ.get("STUB_RC", "0")))
'''


def _git(kok, *args):
    subprocess.run(
        ['git', '-C', str(kok), *args], check=True, capture_output=True,
        text=True)


def _kur(kok, katalog):
    (kok / 'tools').mkdir(parents=True)
    shutil.copy2(KOK / 'tools' / 'model_katalog_uret.py',
                 kok / 'tools' / 'model_katalog_uret.py')
    (kok / 'tools' / 'model_katalog.json').write_text(
        (KOK / 'tools' / 'model_katalog.json').read_text(encoding='utf-8'),
        encoding='utf-8')
    (kok / 'tools' / 'katalog_kontrol.py').write_text(STUB, encoding='utf-8')

    for rel in ky.KIMLIK_YOLLARI:
        p = kok / rel
        if p.suffix == '.json':
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('{}\n', encoding='utf-8')
        else:
            p.mkdir(parents=True, exist_ok=True)
            (p / 'agent.md').write_text('', encoding='utf-8')
    kimlikler = ['openrouter/' + ad
                 for ad in katalog['openrouter']['models']]
    (kok / 'KOD_SABLONLAR' / 'opencode.json').write_text(
        '\n'.join(kimlikler) + '\n', encoding='utf-8')

    _git(kok, 'init', '-q')
    _git(kok, 'add', '-A')
    _git(kok, '-c', 'user.email=test@example.invalid',
         '-c', 'user.name=Atlas Test', 'commit', '-qm', 'fikstur')


def _api(katalog, degisiklik=None):
    modeller = {}
    for ad, kayit in katalog['openrouter']['models'].items():
        modeller[ad] = {
            'reasoning': kayit['reasoning'],
            'tool_call': kayit['tool_call'],
        }
    for ad in modeller:
        if ad.startswith('nvidia/'):
            modeller[ad].update({
                'name': 'Nemotron 3 Ultra 550B A55B (free)',
                'family': 'nemotron-ultra-free',
                'id': ad,
                'cost': {'input': 0, 'output': 0},
                'limit': {'context': 1000000, 'output': 65536},
            })
    if degisiklik:
        for ad, alanlar in degisiklik.items():
            modeller[ad].update(alanlar)
    return {'openrouter': {'models': modeller}}


def _api_yaz(kok, ad, veri):
    yol = kok / ('%s.json' % ad)
    yol.write_text(json.dumps(veri, ensure_ascii=False), encoding='utf-8')
    return yol


def _kos(kok, api_yolu, tarih, stub_rc=0):
    hedef = kok / 'tools' / 'model_katalog.json'
    once = hedef.read_bytes()
    eski_stub = os.environ.get('STUB_RC')
    os.environ['STUB_RC'] = str(stub_rc)
    aday_metni = diff_metni = ''
    try:
        with tempfile.TemporaryDirectory(prefix='katalog-yenile-kos-') as td:
            aday, diff, _ = ky.yenile(
                kok, Path(td), api_dosya=api_yolu, tarih=tarih,
                yazdir=lambda _: None)
            aday_metni = Path(aday).read_text(encoding='utf-8')
            diff_metni = Path(diff).read_text(encoding='utf-8')
            return 0, '', aday_metni, diff_metni, hedef.read_bytes() == once
    except ky.Hata as hata:
        return hata.rc, str(hata), aday_metni, diff_metni, \
            hedef.read_bytes() == once
    finally:
        if eski_stub is None:
            os.environ.pop('STUB_RC', None)
        else:
            os.environ['STUB_RC'] = eski_stub


def main():
    vakalar = []

    def kaydet(ad, ok, ayrinti=''):
        vakalar.append((ad, ok, ayrinti))

    katalog = json.loads(
        (KOK / 'tools' / 'model_katalog.json').read_text(encoding='utf-8'))
    tarih_eski = katalog['_kaynak'].rsplit(', ', 1)[-1]
    tarih_yeni = (datetime.date.fromisoformat(tarih_eski)
                  + datetime.timedelta(days=1)).isoformat()
    icerik_modeli = next(
        ad for ad in katalog['openrouter']['models']
        if not ad.startswith('nvidia/'))

    with tempfile.TemporaryDirectory(prefix='katalog-yenile-selftest-') as td:
        kok = Path(td) / 'depo'
        _kur(kok, katalog)

        api_temiz = _api(katalog)
        api_temiz_yolu = _api_yaz(kok, 'api-temiz', api_temiz)

        rc, hata, _, _, korundu = _kos(
            kok, api_temiz_yolu, tarih_yeni)
        kaydet('yalniz _kaynak tarihi reddedilir',
               rc == 1 and 'yalniz _kaynak tarihi' in hata and korundu,
               'rc=%d · %s' % (rc, hata[:100]))

        rc, hata, _, _, korundu = _kos(
            kok, api_temiz_yolu, tarih_eski)
        kaydet('fark yoksa aday hazir sayilmaz',
               rc == 1 and 'beklenen katalog farki yok' in hata and korundu,
               'rc=%d · %s' % (rc, hata[:100]))

        api_icerik = _api(katalog, {
            icerik_modeli: {'reasoning': False},
        })
        api_icerik_yolu = _api_yaz(kok, 'api-icerik', api_icerik)
        rc, hata, aday, diff, korundu = _kos(
            kok, api_icerik_yolu, tarih_yeni)
        kaydet('gercek model farki aday uretir, cp yapmaz',
               rc == 0 and '"reasoning": false' in aday
               and '"reasoning": false' in diff and korundu,
               'rc=%d · aday=%d · diff=%d' % (rc, len(aday), len(diff)))

        api_eksik = _api(katalog)
        del api_eksik['openrouter']['models'][icerik_modeli]
        api_eksik_yolu = _api_yaz(kok, 'api-eksik', api_eksik)
        rc, hata, _, _, korundu = _kos(
            kok, api_eksik_yolu, tarih_yeni)
        kaydet('uretim hatasinda hedef korunur',
               rc == 1 and 'model katalog uretimi' in hata and korundu,
               'rc=%d · %s' % (rc, hata[:100]))

        rc, hata, _, _, korundu = _kos(
            kok, api_icerik_yolu, tarih_yeni, stub_rc=1)
        kaydet('kontrol FAIL hedefi degistirmez',
               rc == 1 and 'aday katalog kontrolu FAIL' in hata and korundu,
               'rc=%d · %s' % (rc, hata[:100]))

        rc, hata, _, _, korundu = _kos(
            kok, api_icerik_yolu, tarih_yeni, stub_rc=2)
        kaydet('kontrol OLCULMEDI hedefi degistirmez',
               rc == 2 and 'OLCULMEDI' in hata and korundu,
               'rc=%d · %s' % (rc, hata[:100]))

        yeni = kok / 'KOD_SABLONLAR' / '.opencode' / 'agent' / 'yeni.md'
        yeni.write_text('openrouter/%s\n' % icerik_modeli, encoding='utf-8')
        rc, hata, _, _, korundu = _kos(
            kok, api_temiz_yolu, tarih_yeni)
        kaydet('izlenmeyen aktif dosya fail-closed',
               rc == 1 and 'izlenmeyen dosya' in hata and korundu,
               'rc=%d · %s' % (rc, hata[:100]))
        yeni.unlink()

    for ad, ok, ayrinti in vakalar:
        print('  %-48s %-4s %s'
              % (ad, 'PASS' if ok else 'FAIL', ayrinti))
    print()
    gecen = sum(1 for _, ok, _ in vakalar if ok)
    if gecen == len(vakalar):
        print('KATALOG YENILE OZ-TEST: %d/%d gecti' % (gecen, len(vakalar)))
        return 0
    print('KATALOG YENILE OZ-TEST: FAIL — %d/%d'
          % (gecen, len(vakalar)))
    return 1


if __name__ == '__main__':
    sys.exit(main())
