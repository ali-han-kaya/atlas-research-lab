#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_katalog_uret_selftest.py — ureticinin sozlesmesini gecici fiksturlerle sinar.

Uretici eksik, deprecated veya bozuk bir kimlikte hicbir sey yazmamali; depodaki
katalogu da birebir yeniden uretmelidir. Test aga cikmaz ve
`make katalog-selftest` uzerinden `make dogrula` on kosuludur.

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ARAC = KOK / 'tools' / 'model_katalog_uret.py'
DEPO = KOK / 'tools' / 'model_katalog.json'
TARIH = '2026-01-02'
API = {'openrouter': {'models': {
    'm1': {'reasoning': True, 'tool_call': True},
    'm2': {'reasoning': True, 'tool_call': False},
}}}
EMEKLI = {'openrouter': {'models': {'m1': {
    'reasoning': True, 'tool_call': True, 'status': 'deprecated'}}}}


def kos(gecici, api, kimlikler, *ek, temizle=True):
    api_yolu = gecici / 'api.json'
    kimlik_yolu = gecici / 'kimlikler.txt'
    cikti = gecici / 'cikti.json'
    if temizle:
        cikti.unlink(missing_ok=True)
    api_yolu.write_text(api if isinstance(api, str) else json.dumps(api),
                        encoding='utf-8')
    kimlik_yolu.write_text('\n'.join(kimlikler) + '\n', encoding='utf-8')
    sonuc = subprocess.run(
        [sys.executable, str(ARAC), '--api-dosya', str(api_yolu),
         '--kimlik-dosya', str(kimlik_yolu), '--cikti', str(cikti),
         '--tarih', TARIH, *ek], capture_output=True, text=True)
    return sonuc, cikti


def depo_fiksturu():
    veri = json.loads(DEPO.read_text(encoding='utf-8'))
    api, kimlikler = {}, []
    for saglayici, govde in veri.items():
        if saglayici.startswith('_'):
            continue
        api[saglayici] = {'models': govde['models']}
        kimlikler += ['%s/%s' % (saglayici, model) for model in govde['models']]
    return veri, api, kimlikler, veri['_kaynak'].rsplit(', ', 1)[-1]


def main():
    vakalar = []

    def kaydet(ad, ok, ayrinti=''):
        vakalar.append((ad, ok, ayrinti))

    with tempfile.TemporaryDirectory(prefix='katalog-uret-') as dizin:
        g = Path(dizin)
        depo, api, kimlikler, tarih = depo_fiksturu()

        r, c = kos(g, api, kimlikler, '--tarih', tarih)
        kaydet('depo katalogu birebir', r.returncode == 0 and c.exists()
               and c.read_text(encoding='utf-8')
               == DEPO.read_text(encoding='utf-8'), 'rc=%d' % r.returncode)

        beklenen = {
            '_aciklama': depo['_aciklama'],
            '_kaynak': ('models.dev semasi; yalniz depoda gecen model '
                        'kimlikleri, ' + TARIH),
            'openrouter': {'models': {
                'm1': {'reasoning': True, 'tool_call': True},
                'm2': {'reasoning': True, 'tool_call': False}}}}
        r, c = kos(g, API, ['openrouter/m2', 'openrouter/m1',
                            'openrouter/m1'])
        kaydet('gecerli fikstur ve sira', r.returncode == 0 and c.exists()
               and json.loads(c.read_text(encoding='utf-8')) == beklenen,
               'rc=%d' % r.returncode)

        r, c = kos(g, API, [])
        kaydet('bos kimlik listesi', r.returncode == 1 and not c.exists(),
               'rc=%d' % r.returncode)

        r, c = kos(g, API, ['openrouter/yok'])
        kaydet('eksik model', r.returncode == 1 and not c.exists()
               and 'canli katalogda yok' in r.stderr, 'rc=%d' % r.returncode)

        r, c = kos(g, EMEKLI, ['openrouter/m1'])
        kaydet('deprecated model', r.returncode == 1 and not c.exists()
               and 'deprecated' in r.stderr, 'rc=%d' % r.returncode)

        bozuk = {'openrouter': {'models': {'m1': {
            'reasoning': 'yes', 'tool_call': True}}}}
        r, c = kos(g, bozuk, ['openrouter/m1'])
        kaydet('boolean olmayan yetenek', r.returncode == 1 and not c.exists()
               and 'boolean degil' in r.stderr, 'rc=%d' % r.returncode)

        r, c = kos(g, API, ['openrouter'])
        kaydet('gecersiz kimlik', r.returncode == 1 and not c.exists()
               and 'gecersiz kimlik' in r.stderr, 'rc=%d' % r.returncode)

        r, c = kos(g, '{', ['openrouter/m1'])
        kaydet('bozuk api json', r.returncode == 2 and not c.exists(),
               'rc=%d' % r.returncode)

        r, c = kos(g, [], ['openrouter/m1'])
        kaydet('api kok nesne degil', r.returncode == 2 and not c.exists(),
               'rc=%d' % r.returncode)

        c = g / 'cikti.json'
        c.write_text('ESKI', encoding='utf-8')
        r, _ = kos(g, EMEKLI, ['openrouter/m1'], temizle=False)
        kaydet('var olan cikti korunur',
               r.returncode == 1
               and c.read_text(encoding='utf-8') == 'ESKI',
               'rc=%d' % r.returncode)

        iki = {'zeta': {'models': {'b': {
                    'reasoning': True, 'tool_call': True}}},
               'alfa': {'models': {'a': {
                    'reasoning': True, 'tool_call': True}}}}
        r, c = kos(g, iki, ['zeta/b', 'alfa/a'])
        veri = json.loads(c.read_text(encoding='utf-8')) if c.exists() else {}
        kaydet('saglayici sirasi',
               r.returncode == 0
               and list(veri) == ['_aciklama', '_kaynak', 'alfa', 'zeta'],
               'rc=%d' % r.returncode)

    for ad, ok, ayrinti in vakalar:
        print('  %-26s %-4s %s' % (ad, 'PASS' if ok else 'FAIL', ayrinti))
    gecen = sum(1 for _, ok, _ in vakalar if ok)
    print()
    if gecen == len(vakalar):
        print('KATALOG URETICI OZ-TEST: %d/%d gecti'
              % (gecen, len(vakalar)))
        return 0
    print('KATALOG URETICI OZ-TEST: FAIL — %d/%d'
          % (gecen, len(vakalar)))
    return 1


if __name__ == '__main__':
    sys.exit(main())
