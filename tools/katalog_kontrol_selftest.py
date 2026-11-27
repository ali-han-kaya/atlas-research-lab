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

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
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
OLCULMEDI = 'OLCULMEDI'
# Eski/yazim kaymasi ciktiya sizarsa test bunu ayri bir hata olarak yakalar.
ESKI_OLCULMEDI = ('OLCULEMEDI', 'OLCULMADI')
AG_ADRESI = 'http://127.0.0.1:9'


def _kimlik(ad):
    """Fikstur kisaltmasini gercek `nvidia/<model>` bicimine cevir."""
    return ad if '/' in ad else 'nvidia/' + ad


def profil(farkli=None):
    """On rollu, tek kimlikli bedava profili fiksturu."""
    bedava = dict.fromkeys(ROLLER, 'openrouter/nvidia/m1')
    if farkli:
        bedava.update(farkli)
    return {
        'profiller': {'bedava': bedava},
        'bedava_politika': {'asgari_limit': dict(ASGARI)},
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


def main():
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
