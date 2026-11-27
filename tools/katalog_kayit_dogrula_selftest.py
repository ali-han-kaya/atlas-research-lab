#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""katalog_kayit_dogrula_selftest.py — kayit dogrulayicisinin negatif kilidi.

NEDEN VAR
  Bir kanit dogrulayicisi yalniz "saglam dosyada PASS" diyorsa, sema veya
  append-only kontrolu sessizce kapanabilir. Bu test gecici bir git deposunda
  gercek commit'ler uretir; her vakada tek bir kurali bozar ve dogrulayicinin
  FAIL verdigini olcer. Ana agaca yazmaz.

KULLANIM
  python3 tools/katalog_kayit_dogrula_selftest.py

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ARAC = KOK / 'tools' / 'katalog_kayit_dogrula.py'
KAYIT_REL = 'docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl'
TANIM_DOSYALARI = (
    'tools/model_katalog.json',
    'KOD_SABLONLAR/routing.profiles.json',
    'KOD_SABLONLAR/opencode.json',
)


def _modul():
    spec = importlib.util.spec_from_file_location('katalog_kayit_dogrula', ARAC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _modul()


def _git(kok, *args):
    r = subprocess.run(['git', '-C', str(kok)] + list(args),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError('git %s: %s' % (
            ' '.join(args), (r.stderr or '').strip()[:180]))
    return r.stdout


def _yaz(kok, rel, metin):
    yol = Path(kok) / rel
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding='utf-8')


def _commit(kok, mesaj):
    _git(kok, 'add', '-A')
    _git(kok, 'commit', '-q', '-m', mesaj)
    return _git(kok, 'rev-parse', 'HEAD').strip()


def _tanim_hash(kok, commit):
    return {
        rel: hashlib.sha256(
            _git(kok, 'show', '%s:%s' % (commit, rel)).encode('utf-8')
        ).hexdigest()
        for rel in TANIM_DOSYALARI
    }


def _kayit(kok, commit, zaman):
    return {
        'agac_kirli': False,
        'asgari_limit': {'context': 200000, 'output': 32768},
        'aile_politikasi': {
            'aile': 'nemotron',
            'ad_oneki': 'Nemotron 3',
            'saglayici': 'nvidia',
        },
        'canli': {
            'id': 'nvidia/nemotron-3-ultra-550b-a55b:free',
            'name': 'Nemotron 3 Ultra (free)',
            'family': 'nemotron-ultra-free',
            'status': None,
            'reasoning': True,
            'tool_call': True,
            'cost': {'input': 0, 'output': 0},
            'limit': {'context': 1000000, 'output': 65536},
        },
        'commit': commit,
        'github_run_id': None,
        'ham': ['KATALOG KONTROL — test', 'HUKUM: GUNCEL'],
        'kaynak': 'yerel',
        'model': 'nvidia/nemotron-3-ultra-550b-a55b:free',
        'profil': 'bedava',
        'roller': 10,
        'sebep': '',
        'sonuc': 'PASS',
        'surum': 1,
        'tanim_sha256': _tanim_hash(kok, commit),
        'tree': _git(kok, 'rev-parse', commit + '^{tree}').strip(),
        'tree_sha256': MOD._agac_ozeti(
            MOD._agac_dosyalari(kok, commit)),
        'zaman': zaman,
    }


def _satir(veri):
    return json.dumps(veri, ensure_ascii=False, sort_keys=True) + '\n'


def _depo(tmp, iki_satir=False):
    """Gecerli config + bir veya iki append-only kayit satiri kur."""
    kok = Path(tmp)
    kok.mkdir(parents=True, exist_ok=True)
    _git(kok, 'init', '-q')
    _git(kok, 'config', 'user.name', 'Katalog Test')
    _git(kok, 'config', 'user.email', 'katalog@example.invalid')
    _yaz(kok, TANIM_DOSYALARI[0],
         '{"openrouter": {"models": {"nvidia/m1": {}}}}\n')
    _yaz(kok, TANIM_DOSYALARI[1],
         '{"profiller": {"bedava": {}}, "bedava_politika": {}}\n')
    _yaz(kok, TANIM_DOSYALARI[2], '{"model": "test"}\n')
    ilk = _commit(kok, 'config')
    zaman = datetime(2026, 11, 27, 10, 0, 0)
    row1 = _kayit(kok, ilk, zaman.strftime('%Y-%m-%dT%H:%M:%SZ'))
    kayit = kok / KAYIT_REL
    kayit.parent.mkdir(parents=True, exist_ok=True)
    kayit.write_text(_satir(row1), encoding='utf-8')
    _commit(kok, 'kayit 1')
    if iki_satir:
        ikinci = _git(kok, 'rev-parse', 'HEAD').strip()
        row2 = _kayit(kok, ikinci,
                      (zaman + timedelta(minutes=1)).strftime(
                          '%Y-%m-%dT%H:%M:%SZ'))
        with kayit.open('a', encoding='utf-8') as f:
            f.write(_satir(row2))
        _commit(kok, 'kayit 2')
    return kok, kayit


def _kos(kok, kayit):
    spec = importlib.util.spec_from_file_location(
        'katalog_kayit_dogrula_test', ARAC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.dogrula(kok, kayit)


def _vaka(ad, kur, bekle_ok, iz):
    with tempfile.TemporaryDirectory(prefix='katalog_kayit_') as tmp:
        try:
            kok, kayit = kur(tmp)
            ok, hatalar = _kos(kok, kayit)
        except Exception as e:  # noqa: BLE001 - test kosucusu raporlar
            print('  %-30s FAIL ISTISNA: %s' % (ad, e))
            return False
    metin = ' · '.join(hatalar)
    if ok != bekle_ok:
        print('  %-30s FAIL ok=%s beklenen=%s · %s'
              % (ad, ok, bekle_ok, metin[:220]))
        return False
    if iz and iz not in metin:
        print('  %-30s FAIL iz yok (%s) · %s' % (ad, iz, metin[:220]))
        return False
    print('  %-30s PASS %s' % (ad, metin[:150]))
    return True


def _tek_satir(tmp):
    return _depo(tmp, iki_satir=False)


def _iki_satir(tmp):
    return _depo(tmp, iki_satir=True)


_SIL = object()


def _tek_satir_bozuk(alan, deger):
    def kur(tmp):
        kok, kayit = _depo(tmp)
        satir = json.loads(kayit.read_text(encoding='utf-8'))
        if deger is _SIL:
            del satir[alan]
        else:
            satir[alan] = deger
        kayit.write_text(_satir(satir), encoding='utf-8')
        _commit(kok, 'bozuk %s' % alan)
        return kok, kayit
    return kur


def _ters_sira(tmp):
    kok, kayit = _depo(tmp, iki_satir=True)
    satirlar = kayit.read_text(encoding='utf-8').splitlines()
    kayit.write_text('\n'.join(reversed(satirlar)) + '\n',
                     encoding='utf-8')
    _commit(kok, 'satirlari ters cevir')
    return kok, kayit


def _elle_duzenle(tmp):
    kok, kayit = _depo(tmp, iki_satir=True)
    satirlar = kayit.read_text(encoding='utf-8').splitlines()
    veri = json.loads(satirlar[0])
    veri['ham'] = ['elle degistirilmis kanit']
    satirlar[0] = json.dumps(veri, ensure_ascii=False, sort_keys=True)
    kayit.write_text('\n'.join(satirlar) + '\n', encoding='utf-8')
    _commit(kok, 'elle duzenle')
    return kok, kayit


def _calisma_agaci_duzenle(tmp):
    kok, kayit = _depo(tmp)
    veri = json.loads(kayit.read_text(encoding='utf-8'))
    veri['ham'] = ['commit edilmemis elle duzenleme']
    kayit.write_text(_satir(veri), encoding='utf-8')
    return kok, kayit


def main():
    print('KATALOG KAYIT DOGRULA OZ-TESTI — gecici git depolarinda')
    vakalar = [
        ('saglam tek satir', _tek_satir, True, ''),
        ('saglam iki append satiri', _iki_satir, True, ''),
        ('eksik zorunlu alan',
         _tek_satir_bozuk('commit', _SIL), False, 'zorunlu alan'),
        ('gecersiz sonuc',
         _tek_satir_bozuk('sonuc', 'YESIL'), False, 'sonuc'),
        ('yanlis tree',
         _tek_satir_bozuk('tree', '0' * 40), False, 'tree'),
        ('yanlis tree_sha256',
         _tek_satir_bozuk('tree_sha256', '0' * 64), False,
         'tree_sha256'),
        ('yanlis tanim hash',
         _tek_satir_bozuk('tanim_sha256', {
             'tools/model_katalog.json': '0' * 64,
             'KOD_SABLONLAR/routing.profiles.json': '0' * 64,
             'KOD_SABLONLAR/opencode.json': '0' * 64,
         }), False, 'tanim_sha256'),
        ('ters satir sirasi', _ters_sira, False, 'sira'),
        ('elle duzenlenmis satir', _elle_duzenle, False, 'append-only'),
        ('commit edilmemis satir', _calisma_agaci_duzenle, False,
         'calisma agaci'),
    ]
    gecen = 0
    for ad, kur, bekle_ok, iz in vakalar:
        gecen += 1 if _vaka(ad, kur, bekle_ok, iz) else 0
    print()
    if gecen == len(vakalar):
        print('KATALOG KAYIT DOGRULA OZ-TEST: %d/%d gecti'
              % (gecen, len(vakalar)))
        return 0
    print('KATALOG KAYIT DOGRULA OZ-TEST: FAIL — %d/%d'
          % (gecen, len(vakalar)))
    return 1


if __name__ == '__main__':
    sys.exit(main())
