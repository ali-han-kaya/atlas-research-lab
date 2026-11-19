#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""katalog_kontrol_selftest.py — katalog kontrolu sahte GUNCEL uretmesin.

NEDEN VAR
  Ag gerektiren kontrolun kendisi bir kapidir: temiz katalogda GUNCEL, eksik
  modelde BAYAT, okunamayan JSON'da OLCULEMEDI vermelidir. Bu test aga cikmaz;
  `--api-dosya` ile yerel fikstur kullanir. CI'nin bir parcasi degildir.

KULLANIM
  python3 tools/katalog_kontrol_selftest.py

CIKIS: 0 = 7/7 gecti · 1 = en az bir vaka kirmizi
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ARAC = KOK / 'tools' / 'katalog_kontrol.py'


def yerel(*kimlikler):
    return {'openrouter': {'models': {
        k: {'reasoning': True, 'tool_call': True} for k in kimlikler}}}


def canli(*kimlikler, **degisiklik):
    modeller = {}
    for k in kimlikler:
        model = {'reasoning': True, 'tool_call': True}
        model.update(degisiklik.get(k, {}))
        modeller[k] = model
    return {'openrouter': {'models': modeller}}


def vaka(ad, yerel_veri, canli_veri, beklenen_rc, iz):
    with tempfile.TemporaryDirectory(prefix='katalog_kontrol_') as tmp:
        yol = Path(tmp)
        katalog = yol / 'katalog.json'
        api = yol / 'api.json'
        katalog.write_text(json.dumps(yerel_veri), encoding='utf-8')
        api.write_text(json.dumps(canli_veri), encoding='utf-8')
        r = subprocess.run(
            [sys.executable, str(ARAC), '--katalog', str(katalog),
             '--api-dosya', str(api)],
            cwd=str(KOK), capture_output=True, text=True)
        cikti = (r.stdout or '') + (r.stderr or '')
        if r.returncode != beklenen_rc:
            return False, 'rc=%d (beklenen %d) · %s' % (
                r.returncode, beklenen_rc, cikti.strip()[:160])
        if iz not in cikti:
            return False, 'iz yok (%s) · %s' % (iz, cikti.strip()[:160])
        return True, 'rc=%d · %s' % (r.returncode, iz)
    return False, 'gecici dizin kurulamadi'


def main():
    print('KATALOG KONTROL OZ-TESTI — ag yok, yerel api.json fiksturu')
    vakalar = [
        ('guncel katalog', yerel('m1'), canli('m1'), 0, 'GUNCEL'),
        ('eksik model adiyla', yerel('m1', 'm2'), canli('m1'), 1,
         'openrouter/m2'),
        ('yetenek farki adiyla', yerel('m1'), canli('m1', m1={'reasoning': False}),
         1, 'reasoning'),
        ('eksik saglayici', yerel('m1'), {'baska': {'models': {}}}, 1,
         'openrouter'),
        ('deprecated model', yerel('m1'), canli('m1', m1={'status': 'deprecated'}),
         1, 'deprecated'),
        ('bozuk api json', yerel('m1'), [], 2, 'OLCULEMEDI'),
        ('bozuk yerel katalog', {'openrouter': {}}, canli('m1'), 2, 'OLCULEMEDI'),
    ]
    gecen = 0
    for ad, y, c, rc, iz in vakalar:
        try:
            ok, ayrinti = vaka(ad, y, c, rc, iz)
        except Exception as e:  # noqa: BLE001 - test kosucusu hatayi raporlar
            ok, ayrinti = False, 'ISTISNA: %s' % e
        gecen += 1 if ok else 0
        print('  %-28s %-4s %s' % (ad, 'PASS' if ok else 'FAIL', ayrinti))
    print()
    if gecen == len(vakalar):
        print('KATALOG KONTROL OZ-TEST: %d/%d gecti' % (gecen, len(vakalar)))
        return 0
    print('KATALOG KONTROL OZ-TEST: FAIL — %d/%d' % (gecen, len(vakalar)))
    return 1


if __name__ == '__main__':
    sys.exit(main())
