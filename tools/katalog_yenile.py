#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""katalog_yenile.py — katalog yenileme akisinin 1-4. adimlarini tek komutta kosar.

NE YAPAR
  1. Canli models.dev katalogunu indirir (veya --api-dosya ile verilen ayni
     anlik goruntuyu kullanir).
  2. Yalniz izlenen aktif kaynaklardan `openrouter/...` kimliklerini cikarir.
  3. `tools/model_katalog_uret.py` ile adayi uretir.
  4. Adayi ayni anlik goruntuyle `tools/katalog_kontrol.py` uzerinden dogrular
     ve `tools/model_katalog.json` ile diff'ini denetler.

  BASARILI olsa bile `tools/model_katalog.json` DOSYASINA DOKUNMAZ ve `cp`
  YAPMAZ. Aday ile diff'in yollarini basar; yerleştirme, diff'i inceleyen
  insanin ayri ve acik kararidir.

  Fail-closed: ag/JSON, kimlik cikarma, uretim, kontrol veya diff
  denetimlerinden biri basarisizsa rc != 0 olur ve hedef katalog degismez.
  Yalniz `_kaynak` tarihi degisen aday, incelemeye sunulmadan reddedilir.

KULLANIM
  python3 tools/katalog_yenile.py
  python3 tools/katalog_yenile.py --api-dosya /tmp/models.dev-api.json
  python3 tools/katalog_yenile.py --tarih 2026-11-27 --timeout 30

CIKIS
  0 = aday ve diff hazir; hedef katalog degismedi (cp yapilmadi)
  1 = aday reddedildi (eksik/gecersiz kimlik, kontrol FAIL, anlamsiz diff)
  2 = olculemedi (ag, JSON, git, dosya yazma)
"""
import argparse
import datetime
import difflib
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KATALOG = KOK / 'tools' / 'model_katalog.json'
URET = KOK / 'tools' / 'model_katalog_uret.py'
KONTROL = KOK / 'tools' / 'katalog_kontrol.py'
API_URL = 'https://models.dev/api.json'
AZAMI_API_BAYT = 20 * 1024 * 1024

# docs/README.md "2. Yalniz aktif model kimliklerini cikar" ile ayni yol
# listesi. Yeni bir aktif agac eklenirse iki yer birlikte guncellenir.
KIMLIK_YOLLARI = (
    'ATLAS_SABLONLAR/.opencode/agent',
    'KOD_SABLONLAR/.opencode/agent',
    'ATLAS_SABLONLAR/routing.profiles.json',
    'KOD_SABLONLAR/routing.profiles.json',
    'ATLAS_SABLONLAR/opencode.json',
    'KOD_SABLONLAR/opencode.json',
    'opencode.json',
)
KIMLIK_DESENI = re.compile(r'openrouter/[A-Za-z0-9._:/-]+')
KAYNAK_SATIRI = re.compile(
    r'^[+-]\s*"_kaynak"\s*:\s*"(?P<govde>.*)"\s*,?\s*$')


class Hata(Exception):
    """Aday uretilemedi veya reddedildi; rc=1."""

    rc = 1


class OlcumHatasi(Hata):
    """Girdi/ag/dosya nedeniyle olcum yapilamadi; rc=2."""

    rc = 2


def _calistir(komut, cwd, timeout=120):
    try:
        return subprocess.run(
            [str(x) for x in komut], cwd=str(cwd), capture_output=True,
            text=True, encoding='utf-8', errors='replace', timeout=timeout)
    except (OSError, subprocess.SubprocessError) as hata:
        raise OlcumHatasi('komut kosulamadi: %s (%s)'
                          % (' '.join(str(x) for x in komut), hata))


def _metin(cikti):
    return ((cikti.stdout or '') + (cikti.stderr or '')).strip()


def _yaz_atomik(yol, veri):
    """Yolun yaninda gecici dosya yaz, sonra atomik olarak yerine koy."""
    yol = Path(yol)
    gecici = yol.with_name(yol.name + '.tmp')
    try:
        if isinstance(veri, bytes):
            gecici.write_bytes(veri)
        else:
            gecici.write_text(veri, encoding='utf-8')
        os.replace(str(gecici), str(yol))
    except OSError as hata:
        try:
            gecici.unlink()
        except OSError:
            pass
        raise OlcumHatasi('yazilamadi: %s (%s)' % (yol, hata))


def _json_oku(yol, etiket):
    try:
        metin = Path(yol).read_text(encoding='utf-8')
        veri = json.loads(metin)
    except (OSError, UnicodeError, ValueError) as hata:
        raise OlcumHatasi('%s okunamadi/JSON degil: %s (%s)'
                          % (etiket, yol, hata))
    if not isinstance(veri, dict):
        raise OlcumHatasi('%s kok nesne degil: %s' % (etiket, yol))
    return veri


def _api_hazirla(api_dosya, hedef, api_url, timeout):
    """Canli katalogu indir veya verilen anlik goruntuyu kopyala."""
    if api_dosya:
        try:
            ham = Path(api_dosya).read_bytes()
        except OSError as hata:
            raise OlcumHatasi('api dosyasi okunamadi: %s (%s)'
                              % (api_dosya, hata))
        kaynak = str(api_dosya)
    else:
        istek = urllib.request.Request(
            api_url,
            headers={'User-Agent': 'atlas-katalog-yenile/1.0',
                     'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(istek, timeout=timeout) as cevap:
                ham = cevap.read()
        except (urllib.error.URLError, OSError, ValueError) as hata:
            raise OlcumHatasi('models.dev indirilemedi: %s' % hata)
        kaynak = api_url

    if not ham:
        raise OlcumHatasi('api bos: %s' % kaynak)
    if len(ham) > AZAMI_API_BAYT:
        raise OlcumHatasi('api cok buyuk (%d bayt): %s'
                          % (len(ham), kaynak))
    try:
        veri = json.loads(ham.decode('utf-8'))
    except (UnicodeDecodeError, ValueError) as hata:
        raise OlcumHatasi('api JSON degil: %s (%s)' % (kaynak, hata))
    if not isinstance(veri, dict):
        raise OlcumHatasi('api kok nesne degil: %s' % kaynak)
    _yaz_atomik(hedef, ham)
    return hedef, kaynak


def _izlenmeyenleri_denetle(kok):
    """Aktif yollarda izlenmeyen dosya varsa git grep onu sessizce atlar."""
    komut = ['git', '-C', str(kok), 'ls-files', '--others',
             '--exclude-standard', '--'] + list(KIMLIK_YOLLARI)
    sonuc = _calistir(komut, kok, timeout=60)
    if sonuc.returncode != 0:
        raise OlcumHatasi('git ls-files basarisiz: %s' % _metin(sonuc))
    izlenmeyen = [satir.strip() for satir in (sonuc.stdout or '').splitlines()
                  if satir.strip()]
    if izlenmeyen:
        raise Hata('aktif yolda izlenmeyen dosya var; once `git add`: %s'
                   % ', '.join(izlenmeyen[:10]))


def _kimlikleri_cikar(kok, cikti):
    _izlenmeyenleri_denetle(kok)
    komut = ['git', '-C', str(kok), 'grep', '-h', '-o', '-E',
             KIMLIK_DESENI.pattern, '--'] + list(KIMLIK_YOLLARI)
    sonuc = _calistir(komut, kok, timeout=60)
    if sonuc.returncode not in (0, 1):
        raise OlcumHatasi('git grep basarisiz: %s' % _metin(sonuc))
    kimlikler = sorted({satir.strip() for satir in (sonuc.stdout or '').splitlines()
                        if satir.strip()})
    if sonuc.returncode == 1 or not kimlikler:
        raise Hata('aktif model kimligi bulunamadi')
    for kimlik in kimlikler:
        if not KIMLIK_DESENI.fullmatch(kimlik):
            raise Hata('gecersiz model kimligi: %r' % kimlik)
    _yaz_atomik(cikti, '\n'.join(kimlikler) + '\n')
    return kimlikler


def _aday_uret(kok, api, kimlikler, aday, tarih):
    komut = [sys.executable, str(Path(kok) / 'tools' / 'model_katalog_uret.py'),
             '--api-dosya', str(api),
             '--kimlik-dosya', str(kimlikler),
             '--cikti', str(aday)]
    if tarih:
        komut += ['--tarih', tarih]
    sonuc = _calistir(komut, kok, timeout=60)
    if sonuc.returncode != 0:
        ayrinti = _metin(sonuc)
        if sonuc.returncode == 2:
            raise OlcumHatasi('model katalog uretimi OLCULMEDI: %s' % ayrinti)
        raise Hata('model katalog uretimi FAIL: %s' % ayrinti)
    try:
        if not Path(aday).is_file() or Path(aday).stat().st_size == 0:
            raise OSError('aday bos veya yok')
    except OSError as hata:
        raise OlcumHatasi('aday dogrulanamadi: %s' % hata)
    return _metin(sonuc)


def _adayi_dogrula(kok, aday, api):
    komut = [sys.executable, str(Path(kok) / 'tools' / 'katalog_kontrol.py'),
             '--katalog', str(aday), '--api-dosya', str(api)]
    sonuc = _calistir(komut, kok, timeout=120)
    ayrinti = _metin(sonuc)
    if sonuc.returncode == 2:
        raise OlcumHatasi('aday katalog kontrolu OLCULMEDI: %s' % ayrinti)
    if sonuc.returncode != 0:
        raise Hata('aday katalog kontrolu FAIL: %s' % ayrinti)
    return ayrinti


def _kaynak_govde(satir):
    """`_kaynak` satirinin tarih disindaki govdesini dondur; okunamazsa None."""
    m = KAYNAK_SATIRI.match(satir)
    if not m:
        return None
    return re.sub(r',\s*\d{4}-\d{2}-\d{2}$', '', m.group('govde'))


def _diff_denetle(hedef, aday, diff_yolu):
    try:
        eski = Path(hedef).read_text(encoding='utf-8')
        yeni = Path(aday).read_text(encoding='utf-8')
    except (OSError, UnicodeError) as hata:
        raise OlcumHatasi('katalog okunamadi: %s' % hata)
    if eski == yeni:
        raise Hata('beklenen katalog farki yok')

    diff = ''.join(difflib.unified_diff(
        eski.splitlines(keepends=True), yeni.splitlines(keepends=True),
        fromfile=str(hedef), tofile=str(aday)))
    if not diff.strip():
        raise Hata('diff uretilemedi (degisiklik satiri yok)')
    _yaz_atomik(diff_yolu, diff)

    degisen = [satir for satir in diff.splitlines()
               if re.match(r'^[+-][^+-]', satir)]
    if not degisen:
        raise Hata('diff degisiklik satiri yok')
    kaynak = [satir for satir in degisen
              if re.match(r'^[+-]\s*"_kaynak"\s*:', satir)]
    if len(degisen) == 2 and len(kaynak) == 2:
        eski_satir = next((s for s in kaynak if s.startswith('-')), None)
        yeni_satir = next((s for s in kaynak if s.startswith('+')), None)
        eski_govde = _kaynak_govde(eski_satir) if eski_satir else None
        yeni_govde = _kaynak_govde(yeni_satir) if yeni_satir else None
        if eski_govde is None or yeni_govde is None:
            raise Hata('_kaynak satiri okunamadi; guvenli degil')
        if eski_govde == yeni_govde:
            raise Hata('yalniz _kaynak tarihi degisti; '
                       'anlamsiz yenileme reddedildi')
    return diff_yolu


def _ozet(yol):
    try:
        return hashlib.sha256(Path(yol).read_bytes()).hexdigest()
    except OSError as hata:
        raise OlcumHatasi('hedef katalog okunamadi: %s (%s)' % (yol, hata))


def yenile(kok, calisma, api_dosya=None, tarih=None, timeout=30,
           yazdir=print):
    """1-4. adimlari kos; (aday, diff, hedef) dondur; hedefe asla yazma."""
    kok = Path(kok)
    calisma = Path(calisma)
    try:
        calisma.mkdir(parents=True, exist_ok=True)
    except OSError as hata:
        raise OlcumHatasi('calisma dizini olusturulamadi: %s (%s)'
                          % (calisma, hata))

    hedef = kok / 'tools' / 'model_katalog.json'
    ilk_ozet = _ozet(hedef)
    if tarih is None:
        tarih = datetime.date.today().isoformat()
    elif isinstance(tarih, datetime.date):
        tarih = tarih.isoformat()

    yazdir('KATALOG YENILE — 1-4. adimlar · cp yapilmayacak')
    yazdir('  hedef: %s' % hedef)

    api, kaynak = _api_hazirla(
        api_dosya, calisma / 'models.dev-api.json', API_URL, timeout)
    yazdir('  [1/4] canli katalog: %s' % kaynak)

    kimlikler = _kimlikleri_cikar(kok, calisma / 'atlas-model-ids.txt')
    yazdir('  [2/4] aktif kimlik: %d' % len(kimlikler))

    aday = calisma / 'model_katalog.json'
    uretim = _aday_uret(
        kok, api, calisma / 'atlas-model-ids.txt', aday, tarih)
    if uretim:
        yazdir('  [3/4] %s' % uretim.replace('\n', ' · '))

    kontrol = _adayi_dogrula(kok, aday, api)
    if kontrol:
        yazdir('  [4/4] aday kontrolu:')
        for satir in kontrol.splitlines():
            yazdir('    %s' % satir)

    diff = _diff_denetle(hedef, aday, calisma / 'model_katalog.diff')
    if _ozet(hedef) != ilk_ozet:
        raise OlcumHatasi('hedef katalog degisti; cp yasak')
    yazdir('  hedef katalog degismedi; cp yapilmadi')
    return aday, diff, hedef


def main(argv=None):
    ayrac = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ayrac.add_argument(
        '--api-dosya', help='canli indirme yerine bu anlik goruntuyu kullan')
    ayrac.add_argument('--tarih', type=datetime.date.fromisoformat,
                       help='_kaynak tarihi (varsayilan: bugun)')
    ayrac.add_argument('--timeout', type=int, default=30,
                       help='models.dev indirme zaman asimi (saniye)')
    secim = ayrac.parse_args(argv)
    if secim.timeout <= 0:
        print('KATALOG YENILE: OLCULMEDI — timeout pozitif olmali')
        return 2

    try:
        calisma = Path(tempfile.mkdtemp(prefix='atlas-katalog-yenile-'))
    except OSError as hata:
        print('KATALOG YENILE: OLCULMEDI — gecici dizin: %s' % hata)
        return 2

    try:
        aday, diff, hedef = yenile(
            KOK, calisma, api_dosya=secim.api_dosya,
            tarih=secim.tarih, timeout=secim.timeout)
    except Hata as hata:
        etiket = 'OLCULMEDI' if hata.rc == 2 else 'FAIL'
        print('KATALOG YENILE: %s — %s' % (etiket, hata))
        print('  hedef degismedi: %s' % (KOK / 'tools' / 'model_katalog.json'))
        print('  calisma dizini: %s' % calisma)
        return hata.rc

    print()
    print('ADAY HAZIR — cp YAPILMADI')
    print('  aday: %s' % aday)
    print('  diff: %s' % diff)
    print('  incele: diff -u %s %s'
          % (shlex.quote(str(hedef)), shlex.quote(str(aday))))
    print('  yerleştirme (bu komut yapmadi): cp %s %s'
          % (shlex.quote(str(aday)), shlex.quote(str(hedef))))
    print('  diff yalniz beklenen model degisikligini gosteriyorsa cp yapin.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
