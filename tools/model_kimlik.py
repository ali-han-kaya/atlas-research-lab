#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_kimlik — emekli model kimliginin yalniz tarihsel ham satirlarda kaldigini denetler.

NEDEN VAR
  Bir model kimligi canli katalogdan kalkinca yalniz allowlist'i duzeltmek
  yetmez: ayni kimlik routing, ajan, test veya dokumanda kalirsa kapi ile
  belge farkli modeli anlatir. Bu betik aktif agacta emekli kimlige SIFIR
  atif ister. Yalnizca `SURUM.md` ve `docs/OLCUM-*.md` icindeki, tam satir
  SHA-256'siyla onceden kaydedilmis tarihsel ham satirlar muaftir.

  Muafiyet satir bazlidir: tarihsel satir degisirse hash tutmaz, kayit
  bayatlar ve kontrol FAIL verir. Boylece "tarihsel kaydi koru" sozu
  denetlenebilir olur; yeni bir aktif atif sessizce gecemez. Istisna
  defterinin kendisi taranmaz: kimligi tanimlamak icin onu tasimak zorundadir.

KULLANIM
  python3 tools/model_kimlik.py --kontrol   # aktif agac + istisna defteri
  python3 tools/model_kimlik.py --oztest    # sentetik pozitif/negatif vakalar
  python3 tools/model_kimlik.py --envanter  # mevcut eslesmeleri hash'le listele
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / 'tools' / 'model_kimlik_istisna.json'
DEFTER_REL = 'tools/model_kimlik_istisna.json'
TARIHsel_DOSYA = re.compile(r'^(?:SURUM\.md|docs/OLCUM-[^/]+\.md)$')
TARIH = re.compile(r'^\d{4}-\d{2}-\d{2}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
ATLA_DIZIN = {'.git', '__pycache__', 'node_modules', '.pytest_cache',
              '.ruff_cache', '.venv', '.venv-token', 'kanit-paketi'}
AZAMI_BAYT = 4 * 1024 * 1024


class DefterHatasi(Exception):
    """Istisna defteri okunamadi veya sozlesmeyi ihlal ediyor."""


def tarihsel_dosya(yol):
    return TARIHsel_DOSYA.match(yol) is not None


def _git_dosyalar():
    try:
        r = subprocess.run(['git', '-C', str(KOK), 'ls-files', '-z',
                            '--cached', '--others', '--exclude-standard'],
                           capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [p for p in r.stdout.decode('utf-8').split('\0') if p]


def _yuruyus_dosyalar():
    yollar = []
    for kok, dizinler, dosyalar in os.walk(KOK):
        dizinler[:] = [d for d in dizinler if d not in ATLA_DIZIN]
        for ad in dosyalar:
            yollar.append(os.path.relpath(os.path.join(kok, ad), KOK))
    return sorted(yollar)


def metinler():
    """(goreli yol, metin) — izlenen tum okunabilir metin dosyalari.

    Istisna defteri taranmaz; kimligi tanimlayan tek yer odur. Diger hicbir
    dosya adi/uzantisi muaf degildir; boylece yeni bir aktif atif gizlenemez.
    """
    yollar = _git_dosyalar()
    if yollar is None:
        yollar = _yuruyus_dosyalar()
    for rel in yollar:
        if rel == DEFTER_REL:
            continue
        p = KOK / rel
        try:
            if not p.is_file() or p.stat().st_size > AZAMI_BAYT:
                continue
            yield rel, p.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue


def _gerekce(veri, alan, en_az, baglam):
    deger = veri.get(alan)
    if not isinstance(deger, str) or len(deger.strip()) < en_az:
        raise DefterHatasi('%s: %s bos veya cok kisa' % (baglam, alan))
    return deger.strip()


def defter_dogrula(veri):
    """Defteri fail-closed dogrular; (kimlikler, izinli) dondurur."""
    if not isinstance(veri, dict):
        raise DefterHatasi('kok nesne degil')
    kayitlar = veri.get('emekli_kimlikler')
    if not isinstance(kayitlar, list) or not kayitlar:
        raise DefterHatasi('emekli_kimlikler bos veya liste degil')
    kimlikler = []
    for i, kayit in enumerate(kayitlar):
        if not isinstance(kayit, dict):
            raise DefterHatasi('emekli_kimlikler[%d] nesne degil' % i)
        kimlik = kayit.get('kimlik')
        if (not isinstance(kimlik, str) or not kimlik.strip()
                or '/' not in kimlik or any(c.isspace() for c in kimlik)):
            raise DefterHatasi('emekli_kimlikler[%d].kimlik gecersiz' % i)
        if kimlik in kimlikler:
            raise DefterHatasi('yinelenen emekli kimlik: %s' % kimlik)
        _gerekce(kayit, 'yerine', 3, 'emekli_kimlikler[%d]' % i)
        tarih = _gerekce(kayit, 'tarih', 10, 'emekli_kimlikler[%d]' % i)
        if not TARIH.match(tarih):
            raise DefterHatasi('emekli_kimlikler[%d].tarih YYYY-MM-DD degil' % i)
        _gerekce(kayit, 'gerekce', 24, 'emekli_kimlikler[%d]' % i)
        kimlikler.append(kimlik)

    istisnalar = veri.get('istisnalar')
    if not isinstance(istisnalar, list):
        raise DefterHatasi('istisnalar liste degil')
    izinli = {}
    for i, kayit in enumerate(istisnalar):
        if not isinstance(kayit, dict):
            raise DefterHatasi('istisnalar[%d] nesne degil' % i)
        yol = kayit.get('dosya')
        if not isinstance(yol, str) or not tarihsel_dosya(yol):
            raise DefterHatasi(
                'istisnalar[%d].dosya tarihsel kayit degil: %r' % (i, yol))
        satirlar = kayit.get('satirlar')
        if not isinstance(satirlar, list) or not satirlar:
            raise DefterHatasi('istisnalar[%d].satirlar bos' % i)
        gerekce = _gerekce(kayit, 'gerekce', 16, 'istisnalar[%d]' % i)
        for h in satirlar:
            if not isinstance(h, str) or not SHA.match(h):
                raise DefterHatasi(
                    'istisnalar[%d].satirlar gecersiz SHA-256: %r' % (i, h))
            anahtar = (yol, h)
            if anahtar in izinli:
                raise DefterHatasi('yinelenen istisna: %s · %s' % (yol, h))
            izinli[anahtar] = gerekce
    return kimlikler, izinli


def defter_oku(yol=DEFTER):
    try:
        veri = json.loads(Path(yol).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise DefterHatasi('%s okunamadi: %s' % (yol, e))
    return defter_dogrula(veri)


def tara(metinler, kimlikler, izinli):
    """(bulunan, aktif, bayat) — satir hash'i ile satir bazli tarama.

    bulunan: {(dosya, sha256): [satir no, ...]}
    aktif  : [(dosya, satir no, kimlik)] — izinsiz eslesme
    bayat  : [(dosya, sha256)] — defterde olup agacta bulunmayan kayit
    """
    bulunan = {}
    aktif = []
    for yol, metin in metinler:
        for no, satir in enumerate(metin.splitlines(), 1):
            for kimlik in kimlikler:
                if kimlik not in satir:
                    continue
                h = hashlib.sha256(satir.encode('utf-8')).hexdigest()
                bulunan.setdefault((yol, h), []).append(no)
                if (yol, h) not in izinli:
                    aktif.append((yol, no, kimlik))
                break
    bayat = sorted(set(izinli) - set(bulunan))
    return bulunan, aktif, bayat


def oztest():
    """Sentetik vakalarla tarama ve satir-hash muafiyetini sinar."""
    eski = 'nvidia/nemotron-3-' + 'super-120b-' + 'a12b:free'
    tarihsel = 'docs/OLCUM-99-oztest.md'
    satir = 'kanit: openrouter/' + eski
    h = hashlib.sha256(satir.encode('utf-8')).hexdigest()
    izinli = {(tarihsel, h): 'sentetik tarihsel satir'}
    kimlikler = [eski]

    bulunan, aktif, bayat = tara([('README.md', satir + '\n')],
                                 kimlikler, izinli)
    if len(aktif) != 1 or not bayat or (tarihsel, h) in bulunan:
        raise SystemExit('MODEL KIMLIK OZTEST: FAIL — aktif atif yakalanmadi')

    bulunan, aktif, bayat = tara([(tarihsel, satir + '\n')],
                                 kimlikler, izinli)
    if aktif or bayat or (tarihsel, h) not in bulunan:
        raise SystemExit('MODEL KIMLIK OZTEST: FAIL — tarihsel satir muafti')

    bulunan, aktif, bayat = tara([(tarihsel, satir + ' x\n')],
                                 kimlikler, izinli)
    if len(aktif) != 1 or not bayat:
        raise SystemExit('MODEL KIMLIK OZTEST: FAIL — degisen satir bayatladi')

    try:
        defter_dogrula({
            'emekli_kimlikler': [{'kimlik': eski, 'yerine': 'yeni/model',
                                  'tarih': '2026-11-19', 'gerekce': 'x' * 24}],
            'istisnalar': [{'dosya': 'README.md', 'satirlar': [h],
                            'gerekce': 'aktif dosya muaf olamaz'}],
        })
    except DefterHatasi:
        pass
    else:
        raise SystemExit('MODEL KIMLIK OZTEST: FAIL — aktif dosya muafiyeti')

    print('MODEL KIMLIK OZTEST: PASS — 4/4 (aktif, tarihsel, bayat, defter)')


def _yaz_envanter(kimlikler, izinli):
    bulunan, aktif, bayat = tara(metinler(), kimlikler, izinli)
    for (yol, h), satirlar in sorted(bulunan.items()):
        print('%s\t%s\t%s\t%s' % (
            yol, h, ','.join(str(n) for n in satirlar),
            'ISTISNA' if (yol, h) in izinli else 'AKTIF'))
    print('ENVANTER: %d tekil satir · %d aktif · %d bayat'
          % (len(bulunan), len(aktif), len(bayat)))
    return 0


def main(argv):
    if '--oztest' in argv:
        oztest()
        return 0
    try:
        kimlikler, izinli = defter_oku()
    except DefterHatasi as e:
        print('MODEL KIMLIK: FAIL — istisna defteri: %s' % e)
        return 1
    if '--envanter' in argv:
        return _yaz_envanter(kimlikler, izinli)

    bulunan, aktif, bayat = tara(metinler(), kimlikler, izinli)
    if aktif or bayat:
        print('MODEL KIMLIK: FAIL — aktif atif=%d · bayat istisna=%d'
              % (len(aktif), len(bayat)))
        for yol, no, kimlik in aktif:
            print('  AKTIF %s:%d — emekli kimlik: %s' % (yol, no, kimlik))
        for yol, h in bayat:
            print('  BAYAT ISTISNA %s — satir sha256=%s…' % (yol, h[:16]))
        print('  Cozum: aktif atfi kaldir; tarihsel ham satiri DEGISTIRME. '
              'Istisna degistiyse defteri bilincli olarak guncelle.')
        return 1

    tekil = len(bulunan)
    adet = sum(len(v) for v in bulunan.values())
    dosya = len({y for y, _h in bulunan})
    print('MODEL KIMLIK: PASS — %d emekli kimlik · %d tarihsel satir '
          '(%d tekil hash) · %d dosya · 0 aktif atif'
          % (len(kimlikler), adet, tekil, dosya))
    print('ISTISNA: %d kayit · %d dosya · 0 bayat'
          % (len(izinli), len({y for y, _h in izinli})))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
