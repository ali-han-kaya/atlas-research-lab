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

CIKIS: 0 = 11/11 gecti · 1 = en az bir vaka kirmizi
"""
import json
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


def profil(farkli=None):
    """On rollu, tek kimlikli bedava profili fiksturu."""
    bedava = {rol: 'openrouter/m1' for rol in ROLLER}
    if farkli:
        bedava.update(farkli)
    return {
        'profiller': {'bedava': bedava},
        'bedava_politika': {'asgari_limit': dict(ASGARI)},
    }


def yerel(*kimlikler):
    return {'openrouter': {'models': {
        k: {'reasoning': True, 'tool_call': True} for k in kimlikler}}}


def canli(*kimlikler, **degisiklik):
    modeller = {}
    for k in kimlikler:
        model = {
            'id': k,
            'name': 'Test Model',
            'family': 'test-family',
            'status': None,
            'reasoning': True,
            'tool_call': True,
            'cost': {'input': 0, 'output': 0},
            'limit': {'context': 100000, 'output': 10000},
        }
        for alan, deger in degisiklik.get(k, {}).items():
            if isinstance(deger, dict) and isinstance(model.get(alan), dict):
                model[alan].update(deger)
            else:
                model[alan] = deger
        modeller[k] = model
    return {'openrouter': {'models': modeller}}


def vaka(ad, yerel_veri, canli_veri, beklenen_rc, iz, profil_veri=None):
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
             '--api-dosya', str(api)],
            cwd=str(KOK), capture_output=True, text=True)
        cikti = (r.stdout or '') + (r.stderr or '')

        if r.returncode != beklenen_rc:
            return False, 'rc=%d (beklenen %d) · %s' % (
                r.returncode, beklenen_rc, cikti.strip()[:160])
        if iz not in cikti:
            return False, 'iz yok (%s) · %s' % (iz, cikti.strip()[:160])
        if 'OLCULEMEDI' in cikti:
            return False, 'eski yazim OLCULEMEDI · %s' % cikti.strip()[:160]
        if beklenen_rc == 2 and 'OLCULMEDI' not in cikti:
            return False, 'rc=2 ama OLCULMEDI yok · %s' % cikti.strip()[:160]
        if beklenen_rc != 2 and 'OLCULMEDI' in cikti:
            return False, 'FAIL/PASS ciktisinda OLCULMEDI · %s' % cikti.strip()[:160]
        if beklenen_rc == 0 and 'BEDAVA: 10/10' not in cikti:
            return False, 'PASS ama BEDAVA: 10/10 yok · %s' % cikti.strip()[:160]
        return True, 'rc=%d · %s' % (r.returncode, iz)
    return False, 'gecici dizin kurulamadi'


def main():
    print('KATALOG KONTROL OZ-TESTI — ag yok, yerel api.json + profil fiksturu')
    dokuz = profil()
    del dokuz['profiller']['bedava']['kod-tester']
    vakalar = [
        ('guncel katalog', yerel('m1'), canli('m1'), 0, 'BEDAVA: 10/10'),
        ('maliyet drifti', yerel('m1'),
         canli('m1', m1={'cost': {'input': 0.5}}), 1, 'MALIYET'),
        ('limit drifti', yerel('m1'),
         canli('m1', m1={'limit': {'context': 1000}}), 1, 'LIMIT_YETERSIZ'),
        ('yetenek drifti', yerel('m1'),
         canli('m1', m1={'reasoning': False}), 1, 'YETENEK_FARKLI'),
        ('deprecated model', yerel('m1'),
         canli('m1', m1={'status': 'deprecated'}), 1, 'DURUM'),
        ('kimlik drifti', yerel('m1', 'm2'), canli('m1', 'm2'), 1,
         'TEK_KIMLIK_DEGIL',
         profil({'kod-tester': 'openrouter/m2'})),
        ('eksik model adiyla', yerel('m1', 'm2'), canli('m1'), 1,
         'openrouter/m2'),
        ('eksik saglayici', yerel('m1'),
         {'baska': {'models': {}}}, 1, 'SAGLAYICI_YOK'),
        ('bozuk api json', yerel('m1'), [], 2, 'OLCULMEDI'),
        ('bozuk yerel katalog', {'openrouter': {}}, canli('m1'), 2,
         'OLCULMEDI'),
        ('profil rol sayisi', yerel('m1'), canli('m1'), 1,
         'rol sayisi 9', dokuz),
    ]
    gecen = 0
    for v in vakalar:
        ad, y, c, rc, iz = v[:5]
        profil_veri = v[5] if len(v) > 5 else None
        try:
            ok, ayrinti = vaka(ad, y, c, rc, iz, profil_veri)
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
