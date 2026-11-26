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
  denetlenebilir olur; yeni bir aktif atif sessizce gecemez.

KOR NOKTASIZ TARAMA
  Denetimin gordugu dosya kumesi ile inceledigi kume arasinda sessiz fark
  yoktur: her aday dosyanin ham baytlari okunur. UTF-8 cozulen dosyalar satir
  satir (satir SHA-256 muafiyetiyle), cozulemeyen veya NUL iceren dosyalar
  ikili guvenli bayt aramasiyla (UTF-8 + UTF-16LE/BE) taranir; boyut siniri
  yoktur. Okunamayan dosya `tools/model_kimlik_istisna.json` icindeki `onay`
  listesinde gerekcesiyle yoksa hukum FAIL'dir ve raporda "incelenmedi"
  sayilir. Istisna defteri taranir ama eslesmeleri "tanim" sayilir; bu
  muafiyet de ayni `onay` listesinde kayitlidir. Boylece kontrol, bulamadigi
  icin degil bakamadigi icin de PASS veremez.

  Git'in yok saydigi dosyalar ayri bir kumede tutulur. Her biri defterdeki
  `gorulmedi` desenlerinden biriyle gerekcesine baglanmalidir; eslesmeyen tek
  dosya FAIL eder. Boylece `.gitignore` arkasina saklanan kimlik sessizce PASS
  veremez; raporda `gorulmedi` dosya ve gerekce sayisi birlikte gorunur.

KULLANIM
  python3 tools/model_kimlik.py --kontrol   # aday dosyalarin tamami + defter
  python3 tools/model_kimlik.py --oztest    # sentetik pozitif/negatif vakalar
  python3 tools/model_kimlik.py --envanter  # mevcut eslesmeleri hash'le listele
"""
import contextlib
import fnmatch
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / 'tools' / 'model_kimlik_istisna.json'
DEFTER_REL = 'tools/model_kimlik_istisna.json'
TARIHsel_DOSYA = re.compile(r'^(?:SURUM\.md|docs/OLCUM-[^/]+\.md)$')
TARIH = re.compile(r'^\d{4}-\d{2}-\d{2}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
ATLA_DIZIN = {'.git', '__pycache__', 'node_modules', '.pytest_cache',
              '.ruff_cache', '.venv', '.venv-token', 'kanit-paketi'}
ONAY_TUR = ('tanim', 'okunamaz')
KODLAMALAR = ('utf-8', 'utf-16-le', 'utf-16-be')


class DefterHatasi(Exception):
    """Istisna defteri okunamadi veya sozlesmeyi ihlal ediyor."""


def tarihsel_dosya(yol):
    return TARIHsel_DOSYA.match(yol) is not None


def defter_tanim_sha256(veri):
    """Defterin `onay` listesi disindaki iceriginin kanonik SHA-256'si.

    Kendi kendini hash'leyen bir alan tanimsizdir; bu yuzden defterin
    kimlik/istisna icerigi hash'lenir, `onay` listesi disarida kalir. Onay
    listesine kayit eklemek bu hash'i degistirmez; onu asagidaki yapisal
    kurallar denetler (yalniz defter `tanim` olabilir, `okunamaz` kaydi
    gercekten okunamayan dosyaya bagli olmali).
    """
    kopya = {k: v for k, v in veri.items() if k != 'onay'}
    ham = json.dumps(kopya, sort_keys=True, ensure_ascii=False,
                     separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(ham).hexdigest()


def _git_kok(kok):
    """Kok gercek bir git koku ise None; degilse hata metni dondurur."""
    try:
        ust = subprocess.run(['git', '-C', str(kok), 'rev-parse',
                              '--show-toplevel'],
                             capture_output=True, check=True)
        if (os.path.realpath(ust.stdout.decode('utf-8').strip())
                != os.path.realpath(str(kok))):
            return 'kok git ust dizini degil'
        return None
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as e:
        return 'git kok bulunamadi: %s' % (e,)


def _git_dosyalar(kok):
    """Izlenen + yeni (yok sayilmayan) dosyalar; kok bir git koku degilse None."""
    if _git_kok(kok) is not None:
        return None
    try:
        r = subprocess.run(['git', '-C', str(kok), 'ls-files', '-z',
                            '--cached', '--others', '--exclude-standard'],
                           capture_output=True, check=True)
        return [p for p in r.stdout.decode('utf-8').split('\0') if p]
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        return None


def _git_ignored_dosyalar(kok):
    """Yalniz gitignore'un yok saydigi dosyalar; git yoksa None.

    Bu kume taranmaz. Raporda gorunmesi ve defterdeki bir gerekceye baglanmasi
    zorunludur; aksi halde `hukum` FAIL verir.
    """
    if _git_kok(kok) is not None:
        return None
    try:
        r = subprocess.run(['git', '-C', str(kok), 'ls-files', '-z',
                            '--others', '--ignored', '--exclude-standard'],
                           capture_output=True, check=True)
        return sorted(p for p in r.stdout.decode('utf-8').split('\0') if p)
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        return None


def _yuruyus_dosyalar(kok):
    yollar = []
    for dizin, alt, dosyalar in os.walk(kok):
        alt[:] = [d for d in alt if d not in ATLA_DIZIN]
        for ad in dosyalar:
            yollar.append(os.path.relpath(os.path.join(dizin, ad), kok))
    return sorted(yollar)


def aday_dosyalar(kok=KOK):
    """Denetimin gordugu kume; git varsa git'in kumesi, yoksa yuruyus."""
    yollar = _git_dosyalar(kok)
    if yollar is None:
        yollar = _yuruyus_dosyalar(kok)
    return sorted(set(yollar))


def _gerekce(veri, alan, en_az, baglam):
    deger = veri.get(alan)
    if not isinstance(deger, str) or len(deger.strip()) < en_az:
        raise DefterHatasi('%s: %s bos veya cok kisa' % (baglam, alan))
    return deger.strip()


def defter_dogrula(veri):
    """Defteri fail-closed dogrular; (kimlikler, izinli, onay, gorulmedi) dondurur."""
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

    onay_listesi = veri.get('onay')
    if not isinstance(onay_listesi, list) or not onay_listesi:
        raise DefterHatasi('onay listesi bos veya yok')
    onay = {}
    tanim = []
    for i, kayit in enumerate(onay_listesi):
        if not isinstance(kayit, dict):
            raise DefterHatasi('onay[%d] nesne degil' % i)
        yol = kayit.get('dosya')
        if (not isinstance(yol, str) or not yol.strip() or yol.startswith('/')
                or '..' in yol.split('/')):
            raise DefterHatasi('onay[%d].dosya goreli ve guvenli degil: %r'
                               % (i, yol))
        if yol in onay:
            raise DefterHatasi('yinelenen onay kaydi: %s' % yol)
        tur = kayit.get('tur')
        if tur not in ONAY_TUR:
            raise DefterHatasi('onay[%d].tur gecersiz: %r' % (i, tur))
        gerekce = _gerekce(kayit, 'gerekce', 24, 'onay[%d]' % i)
        h = kayit.get('sha256')
        if tur == 'tanim':
            if yol != DEFTER_REL:
                raise DefterHatasi(
                    'onay[%d]: yalniz istisna defteri tanim olabilir: %r'
                    % (i, yol))
            if not isinstance(h, str) or not SHA.match(h):
                raise DefterHatasi('onay[%d].sha256 gecersiz' % i)
            tanim.append(yol)
        elif h is not None and (not isinstance(h, str) or not SHA.match(h)):
            raise DefterHatasi('onay[%d].sha256 gecersiz: %r' % (i, h))
        onay[yol] = {'tur': tur, 'gerekce': gerekce, 'sha256': h}
    if tanim != [DEFTER_REL]:
        raise DefterHatasi('onay listesi istisna defterini tam bir kez '
                           '"tanim" olarak icermeli')
    if onay[DEFTER_REL]['sha256'] != defter_tanim_sha256(veri):
        raise DefterHatasi('defter tanim hash tutmuyor: onay[0].sha256 '
                           'guncel degil (icerik degismis)')

    gorulmedi_listesi = veri.get('gorulmedi', [])
    if not isinstance(gorulmedi_listesi, list):
        raise DefterHatasi('gorulmedi listesi liste degil')
    gorulmedi = []
    gorulmedi_desenleri = set()
    for i, kayit in enumerate(gorulmedi_listesi):
        if not isinstance(kayit, dict):
            raise DefterHatasi('gorulmedi[%d] nesne degil' % i)
        desen = kayit.get('desen')
        if (not isinstance(desen, str) or not desen.strip()
                or desen.startswith('/') or '..' in desen.split('/')
                or desen in ('*', '**', '*/**', '**/*')):
            raise DefterHatasi('gorulmedi[%d].desen goreli ve yeterince '
                               'dar degil: %r' % (i, desen))
        if desen in gorulmedi_desenleri:
            raise DefterHatasi('yinelenen gorulmedi deseni: %s' % desen)
        gerekce = _gerekce(kayit, 'gerekce', 24, 'gorulmedi[%d]' % i)
        gorulmedi_desenleri.add(desen)
        gorulmedi.append({'desen': desen, 'gerekce': gerekce})
    return kimlikler, izinli, onay, gorulmedi


def defter_oku(yol=DEFTER):
    try:
        veri = json.loads(Path(yol).read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise DefterHatasi('%s okunamadi: %s' % (yol, e))
    return defter_dogrula(veri)


class Tarama(object):
    """Bir kokte yapilan taramanin sayaclari ve bulgulari."""

    def __init__(self):
        self.taranan = 0
        self.bulunan = {}
        self.aktif = []
        self.tanim = []
        self.incelenmedi = []
        self.incelenmeyen = []
        self.onayli = []
        self.onay_kullanildi = set()
        self.gorulmedi = []
        self.gorulmedi_onaysiz = []
        self.bayat = []

    def aday(self):
        return self.taranan + self.incelenmedi_sayisi() + self.gorulmedi_sayisi()

    def incelenmedi_sayisi(self):
        """Onayli ve onaysiz tum atlanan dosyalarin toplam sayisi."""
        return len(self.incelenmeyen) + len(self.onayli)

    def gorulmedi_sayisi(self):
        """Gitignore'un yok saydigi, bagli oldugu gerekceyle gorulmeyen dosyalar."""
        return len(self.gorulmedi) + len(self.gorulmedi_onaysiz)

    def gorulmedi_gerekce_sayisi(self):
        return len({gerekce for _yol, _desen, gerekce in self.gorulmedi})


def _satir_tara(sonuc, yol, metin, kimlikler, izinli, tanim):
    for no, satir in enumerate(metin.splitlines(), 1):
        for kimlik in kimlikler:
            if kimlik not in satir:
                continue
            if tanim:
                sonuc.tanim.append((yol, no, kimlik, 'satir'))
                break
            h = hashlib.sha256(satir.encode('utf-8')).hexdigest()
            sonuc.bulunan.setdefault((yol, h), []).append(no)
            if (yol, h) not in izinli:
                sonuc.aktif.append((yol, no, kimlik, 'satir'))
            break


def _bayt_tara(sonuc, yol, ham, kimlikler, tanim):
    """Ikili guvenli arama: kimligin UTF-8 ve UTF-16 bayt dizileri."""
    for kimlik in kimlikler:
        for kodlama in KODLAMALAR:
            dizi = kimlik.encode(kodlama)
            bas = ham.find(dizi)
            while bas != -1:
                if tanim:
                    sonuc.tanim.append((yol, bas, kimlik, 'bayt/%s' % kodlama))
                else:
                    sonuc.aktif.append(
                        (yol, bas, kimlik, 'bayt/%s' % kodlama))
                bas = ham.find(dizi, bas + 1)


def tara_kok(kok, kimlikler, izinli, onay, gorulmedi=None,
             defter_rel=DEFTER_REL):
    """Aday dosyalarin TAMAMINI inceler; okunamayanlar onay listesine bakar."""
    sonuc = Tarama()
    kok = Path(kok)
    gorulmedi = gorulmedi or []
    adaylar = aday_dosyalar(kok)
    for rel in adaylar:
        p = kok / rel
        try:
            if not p.is_file():
                sonuc.incelenmedi.append(
                    (rel, 'dosya degil (dizin, gitlink veya kirik symlink)'))
                continue
            ham = p.read_bytes()
        except OSError as e:
            sonuc.incelenmedi.append(
                (rel, 'okunamadi: %s' % (e.strerror or e)))
            continue
        sonuc.taranan += 1
        tanim = rel == defter_rel
        if tanim:
            sonuc.onay_kullanildi.add(rel)
        if b'\x00' in ham:
            _bayt_tara(sonuc, rel, ham, kimlikler, tanim)
            continue
        try:
            metin = ham.decode('utf-8')
        except UnicodeDecodeError:
            _bayt_tara(sonuc, rel, ham, kimlikler, tanim)
        else:
            _satir_tara(sonuc, rel, metin, kimlikler, izinli, tanim)

    # Gitignore'un yok saydigi dosyalar taranmaz; ancak gorunmez de degildir.
    # Her biri defterdeki bir desen + gerekceye baglanir. Baglanmayan tek dosya
    # hukmu FAIL eder; boylece yeni bir ignored dosya sessizce gecemez.
    ignored = set(_git_ignored_dosyalar(kok) or []) - set(adaylar)
    for rel in sorted(ignored):
        kayit = next((k for k in gorulmedi
                      if fnmatch.fnmatchcase(rel, k['desen'])), None)
        if kayit is not None:
            sonuc.gorulmedi.append((rel, kayit['desen'], kayit['gerekce']))
        else:
            sonuc.gorulmedi_onaysiz.append(
                (rel, 'gitignore; gorulmedi listesinde gerekceli desen yok'))
    for rel, sebep in sonuc.incelenmedi:
        kayit = onay.get(rel)
        if kayit and kayit['tur'] == 'okunamaz':
            sonuc.onayli.append((rel, sebep))
            sonuc.onay_kullanildi.add(rel)
        else:
            sonuc.incelenmeyen.append((rel, sebep))
    sonuc.bayat = sorted(set(izinli) - set(sonuc.bulunan))
    return sonuc


def hukum(sonuc, onay):
    """(gecti, sorunlar) — tarama sonucunu fail-closed hukme cevirir."""
    sorunlar = []
    for yol, konum, kimlik, tur in sonuc.aktif:
        sorunlar.append('AKTIF %s:%s — emekli kimlik (%s): %s'
                        % (yol, konum, tur, kimlik))
    for yol, sebep in sonuc.incelenmeyen:
        sorunlar.append('INCELENMEDI %s — %s (onay listesinde yok)'
                        % (yol, sebep))
    for yol, sebep in sonuc.gorulmedi_onaysiz:
        sorunlar.append('GORULMEDI %s — %s (gorulmedi listesinde yok)'
                        % (yol, sebep))
    for yol, h in sonuc.bayat:
        sorunlar.append('BAYAT ISTISNA %s — satir sha256=%s…'
                        % (yol, h[:16]))
    for yol in sorted(set(onay) - sonuc.onay_kullanildi):
        sorunlar.append('ONAY GEREKSIZ %s — dosya okunabildi ya da yok; '
                        'kaydi onay listesinden cikar' % yol)
    if sonuc.taranan == 0:
        sorunlar.append('TARAMA BOS — aday dosya bulunamadi; kume '
                        'cozumlenemedi')
    return not sorunlar, sorunlar


def ozet_satiri(kimlikler, sonuc, onay):
    """PASS rapor satiri — sayaclarin TEK kaynagi; --oztest bunu denetler.

    `incelenmedi` onayli ve onaysiz tum okunamayan adaylari kapsar;
    `gorulmedi` ise gitignore'un yok saydigi, defterdeki bir gerekceye bagli
    dosyalari kapsar. `onay` defterdeki toplam kayit sayisidir;
    `onayli`/`onaysiz` ise atlanan dosyalarin dagilimidir. Temiz agacta
    incelenmedi=0, gorulmedi defterdeki ignored kume kadar olabilir.
    """
    return ('MODEL KIMLIK: PASS — %d emekli kimlik · aday=%d dosya · '
            'taranan=%d dosya · incelenmedi=%d dosya '
            '(onayli=%d · onaysiz=%d) · gorulmedi=%d dosya '
            '(%d gerekce) · onay=%d kayit · aktif=0'
            % (len(kimlikler), sonuc.aday(), sonuc.taranan,
               sonuc.incelenmedi_sayisi(), len(sonuc.onayli),
               len(sonuc.incelenmeyen), sonuc.gorulmedi_sayisi(),
               sonuc.gorulmedi_gerekce_sayisi(), len(onay)))


def _oz_agac(kok, dosyalar):
    for rel, icerik in dosyalar.items():
        p = Path(kok) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(icerik, bytes):
            p.write_bytes(icerik)
        else:
            p.write_text(icerik, encoding='utf-8')


def _oz_defter(kimlik, tarihsel, satir_hashi):
    veri = {
        'emekli_kimlikler': [{
            'kimlik': kimlik,
            'yerine': 'yeni/model',
            'tarih': '2026-11-19',
            'gerekce': 'Sentetik oztest icin emekli kimlik kaydi.'}],
        'istisnalar': [{
            'dosya': tarihsel,
            'satirlar': [satir_hashi],
            'gerekce': 'Sentetik tarihsel ham satir kaydi.'}],
        'onay': [{
            'dosya': DEFTER_REL,
            'tur': 'tanim',
            'sha256': '',
            'gerekce': 'Kimligi tanimlayan defter; taranir, eslesmeleri '
                       'tanim sayilir.'}],
    }
    veri['onay'][0]['sha256'] = defter_tanim_sha256(veri)
    return veri


def _oz_kos(dosyalar, defter_veri, kirik=False, git=False):
    with tempfile.TemporaryDirectory() as kok:
        _oz_agac(kok, dosyalar)
        if kirik:
            os.symlink('yok.md', os.path.join(kok, 'docs', 'kirik.md'))
        if git:
            subprocess.run(['git', '-C', kok, 'init', '-q'],
                           capture_output=True, check=True)
        kimlikler, izinli, onay, gorulmedi = defter_dogrula(defter_veri)
        sonuc = tara_kok(kok, kimlikler, izinli, onay, gorulmedi)
        gecti, sorunlar = hukum(sonuc, onay)
        return gecti, sorunlar, sonuc


def oztest():
    """Sentetik agaclarla kor noktasiz taramayi ve muafiyetleri sinar."""
    eski = 'nvidia/nemotron-3-' + 'super-120b-' + 'a12b:free'
    tarihsel = 'docs/OLCUM-99-oztest.md'
    satir = 'kanit: openrouter/' + eski
    h = hashlib.sha256(satir.encode('utf-8')).hexdigest()
    veri = _oz_defter(eski, tarihsel, h)
    taban = {DEFTER_REL: json.dumps(veri, ensure_ascii=False),
             tarihsel: satir + '\n', 'README.md': 'temiz agac\n'}
    vaka = []

    def bekle(kosul, ad, ayrinti=''):
        if not kosul:
            raise SystemExit('MODEL KIMLIK OZTEST: FAIL — %s%s'
                             % (ad, (' | ' + ayrinti) if ayrinti else ''))
        vaka.append(ad)

    gecti, sorunlar, sonuc = _oz_kos(taban, veri)
    temiz_sonuc = sonuc
    bekle(gecti and sonuc.taranan == 3 and not sonuc.incelenmedi,
          'temiz', '; '.join(sorunlar))
    bekle(not sonuc.bayat and len(sonuc.bulunan) == 1
          and len(sonuc.tanim) == 1, 'tarihsel-muaf')

    ek = dict(taban)
    ek['docs/aktif.md'] = 'not\n' + satir + '\n'
    gecti, sorunlar, sonuc = _oz_kos(ek, veri)
    bekle(not gecti and len(sonuc.aktif) == 1, 'aktif', '; '.join(sorunlar))

    buyuk = ('dolgu\n' * (1024 * 1024)) + satir + '\n'
    ek = dict(taban)
    ek['docs/buyuk.txt'] = buyuk
    gecti, sorunlar, sonuc = _oz_kos(ek, veri)
    bekle(len(buyuk.encode('utf-8')) > 4 * 1024 * 1024 and not gecti
          and len(sonuc.aktif) == 1, 'buyuk', '; '.join(sorunlar))

    ek = dict(taban)
    ek['docs/ikili-utf8.bin'] = b'\x00\x01' + eski.encode('utf-8') + b'\x02'
    ek['docs/ikili-utf16.bin'] = (b'\x00\xff' + eski.encode('utf-16-le')
                                  + b'\xff\x00')
    gecti, sorunlar, sonuc = _oz_kos(ek, veri)
    bekle(not gecti and len(sonuc.aktif) == 2, 'ikili', '; '.join(sorunlar))

    gecti, sorunlar, sonuc = _oz_kos(taban, veri, kirik=True)
    bekle(not gecti and len(sonuc.incelenmeyen) == 1
          and sonuc.incelenmedi_sayisi() == 1 and not sonuc.onayli
          and any('INCELENMEDI' in s for s in sorunlar),
          'onaysiz', '; '.join(sorunlar))

    # Gitignore'lu dosya aday kumesine girmez; defterdeki gorulmedi
    # desenlerinden biriyle gerekcesine baglanmazsa sessizce gecmemeli.
    ek = dict(taban)
    ek['.gitignore'] = 'gizli/\n'
    ek['gizli/sakli.md'] = satir + '\n'
    gecti, sorunlar, sonuc = _oz_kos(ek, veri, git=True)
    bekle(not gecti and not sonuc.gorulmedi
          and len(sonuc.gorulmedi_onaysiz) == 1
          and sonuc.gorulmedi_sayisi() == 1
          and any('GORULMEDI' in s for s in sorunlar),
          'gorulmedi-onaysiz', '; '.join(sorunlar))

    veri_g = _oz_defter(eski, tarihsel, h)
    veri_g['gorulmedi'] = [{
        'desen': 'gizli/*',
        'gerekce': 'Sentetik gitignore dosyasi; gerekceye bagli gorulmedi.'}]
    veri_g['onay'][0]['sha256'] = defter_tanim_sha256(veri_g)
    ek[DEFTER_REL] = json.dumps(veri_g, ensure_ascii=False)
    gecti, sorunlar, sonuc = _oz_kos(ek, veri_g, git=True)
    _, _, onay_g, _gorulmedi_g = defter_dogrula(veri_g)
    rapor = ozet_satiri([eski], sonuc, onay_g)
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        _yaz_envanter(sonuc, onay_g)
    envanter = tampon.getvalue()
    bekle(
        gecti and len(sonuc.gorulmedi) == 1
        and not sonuc.gorulmedi_onaysiz
        and sonuc.gorulmedi_sayisi() == 1
        and all(x in rapor for x in (
            'gorulmedi=1 dosya', '1 gerekce', 'onay=1 kayit'))
        and all(x in envanter for x in (
            'gorulmedi=1', 'gorulmedi-gerekce=1', 'GORULMEDI')),
        'gorulmedi-onayli', '; '.join(sorunlar))

    veri_h = _oz_defter(eski, tarihsel, h)
    veri_h['gorulmedi'] = [{'desen': 'gizli/*'}]
    veri_h['onay'][0]['sha256'] = defter_tanim_sha256(veri_h)
    try:
        defter_dogrula(veri_h)
    except DefterHatasi:
        pass
    else:
        raise SystemExit('MODEL KIMLIK OZTEST: FAIL — gorulmedi-tanim')
    vaka.append('gorulmedi-tanim')

    # Onayli atlama: okunamayan dosya onayla atlanir; PASS satiri bunu
    # incelenmedi icinde sayar, onayli/onaysiz ayrimini ve toplam onay
    # kaydini gosterir. Envanter ayni anlamlari tasimali.
    veri_onay = _oz_defter(eski, tarihsel, h)
    veri_onay['onay'].append({
        'dosya': 'docs/kirik.md', 'tur': 'okunamaz', 'sha256': None,
        'gerekce': 'Sentetik okunamaz dosya onayi.'})
    ek = dict(taban)
    ek[DEFTER_REL] = json.dumps(veri_onay, ensure_ascii=False)
    gecti, sorunlar, sonuc = _oz_kos(ek, veri_onay, kirik=True)
    _, _, onay_sozluk, _gorulmedi = defter_dogrula(veri_onay)
    rapor = ozet_satiri([eski], sonuc, onay_sozluk)
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        _yaz_envanter(sonuc, onay_sozluk)
    envanter = tampon.getvalue()
    bekle(
        gecti
        and sonuc.incelenmedi_sayisi() == 1
        and len(sonuc.onayli) == 1
        and not sonuc.incelenmeyen
        and all(x in rapor for x in (
            'incelenmedi=1', 'onayli=1', 'onaysiz=0', 'onay=2 kayit'))
        and all(x in envanter for x in (
            'incelenmedi=1', 'onayli=1', 'onaysiz=0', 'onay=2 kayit')),
        'onayli-atlama', '; '.join(sorunlar))

    veri2 = _oz_defter(eski, tarihsel, h)
    veri2['onay'].append({
        'dosya': 'README.md', 'tur': 'okunamaz', 'sha256': None,
        'gerekce': 'Sentetik gereksiz onay: dosya okunabiliyor.'})
    ek = dict(taban)
    ek[DEFTER_REL] = json.dumps(veri2, ensure_ascii=False)
    gecti, sorunlar, _ = _oz_kos(ek, veri2)
    bekle(not gecti and any('ONAY GEREKSIZ' in s for s in sorunlar),
          'gereksiz-onay', '; '.join(sorunlar))

    ek = dict(taban)
    ek[tarihsel] = satir + ' x\n'
    gecti, sorunlar, sonuc = _oz_kos(ek, veri)
    bekle(not gecti and len(sonuc.bayat) == 1, 'bayat', '; '.join(sorunlar))

    veri3 = _oz_defter(eski, tarihsel, h)
    veri3['onay'].append({
        'dosya': 'README.md', 'tur': 'tanim', 'sha256': '0' * 64,
        'gerekce': 'Aktif dosya tanim olamaz; sentetik ihlal.'})
    try:
        defter_dogrula(veri3)
    except DefterHatasi:
        pass
    else:
        raise SystemExit('MODEL KIMLIK OZTEST: FAIL — tanim (aktif dosya)')
    veri4 = _oz_defter(eski, tarihsel, h)
    veri4['emekli_kimlikler'][0]['gerekce'] = 'Degistirilmis sentetik defter.'
    try:
        defter_dogrula(veri4)
    except DefterHatasi:
        pass
    else:
        raise SystemExit('MODEL KIMLIK OZTEST: FAIL — tanim (defter hash)')
    vaka.append('tanim')

    veri5 = _oz_defter(eski, tarihsel, h)
    veri5['onay'] = [{
        'dosya': 'docs/gecici-onaysiz.md', 'tur': 'okunamaz', 'sha256': None,
        'gerekce': 'Defterin kendi tanim onayi yok; sentetik ihlal.'}]
    try:
        defter_dogrula(veri5)
    except DefterHatasi:
        pass
    else:
        raise SystemExit('MODEL KIMLIK OZTEST: FAIL — defter-onay')
    vaka.append('defter-onay')

    _, _, onay_sozluk, _gorulmedi = defter_dogrula(veri)
    rapor = ozet_satiri([eski], temiz_sonuc, onay_sozluk)
    bekle(all(x in rapor for x in ('aday=3', 'taranan=3', 'incelenmedi=0',
                                   'onay=1', 'aktif=0')), 'rapor', rapor)

    print('MODEL KIMLIK OZTEST: PASS — %d/%d (%s)'
          % (len(vaka), len(vaka), ', '.join(vaka)))


def _yaz_envanter(sonuc, onay):
    for (yol, h), satirlar in sorted(sonuc.bulunan.items()):
        print('%s\t%s\t%s\t%s' % (
            yol, h, ','.join(str(n) for n in satirlar), 'ISTISNA'))
    for yol, konum, kimlik, tur in sonuc.aktif:
        print('%s\t%s\t%s\tAKTIF (%s)' % (yol, konum, kimlik, tur))
    gruplar = {}
    for _yol, desen, gerekce in sonuc.gorulmedi:
        adet, _g = gruplar.get(desen, (0, gerekce))
        gruplar[desen] = (adet + 1, gerekce)
    for desen, (adet, gerekce) in sorted(gruplar.items()):
        print('GORULMEDI\t%s\t%d dosya\t%s' % (desen, adet, gerekce))
    for yol, sebep in sonuc.gorulmedi_onaysiz:
        print('%s\tGORULMEDI-ONAYSIZ\t%s' % (yol, sebep))
    print('ENVANTER: aday=%d · taranan=%d · incelenmedi=%d · '
          'onayli=%d · onaysiz=%d · gorulmedi=%d · '
          'gorulmedi-gerekce=%d · onay=%d kayit · '
          '%d tarihsel satir · %d tanim · %d aktif · %d bayat'
          % (sonuc.aday(), sonuc.taranan, sonuc.incelenmedi_sayisi(),
             len(sonuc.onayli), len(sonuc.incelenmeyen),
             sonuc.gorulmedi_sayisi(), sonuc.gorulmedi_gerekce_sayisi(),
             len(onay),
             sum(len(v) for v in sonuc.bulunan.values()),
             len(sonuc.tanim), len(sonuc.aktif), len(sonuc.bayat)))
    return 0


def main(argv):
    if '--oztest' in argv:
        oztest()
        return 0
    try:
        kimlikler, izinli, onay, gorulmedi = defter_oku()
    except DefterHatasi as e:
        print('MODEL KIMLIK: FAIL — istisna defteri: %s' % e)
        return 1
    sonuc = tara_kok(KOK, kimlikler, izinli, onay, gorulmedi)
    if '--envanter' in argv:
        return _yaz_envanter(sonuc, onay)

    gecti, sorunlar = hukum(sonuc, onay)
    if not gecti:
        print('MODEL KIMLIK: FAIL — aday=%d dosya · taranan=%d · '
              'incelenmedi=%d (onayli=%d · onaysiz=%d) · '
              'gorulmedi=%d (%d gerekce) · onay=%d kayit · '
              'aktif=%d · bayat=%d'
              % (sonuc.aday(), sonuc.taranan, sonuc.incelenmedi_sayisi(),
                 len(sonuc.onayli), len(sonuc.incelenmeyen),
                 sonuc.gorulmedi_sayisi(), sonuc.gorulmedi_gerekce_sayisi(),
                 len(onay),
                 len(sonuc.aktif), len(sonuc.bayat)))
        for satir in sorunlar:
            print('  %s' % satir)
        print('  Cozum: aktif atfi kaldir; tarihsel ham satiri DEGISTIRME. '
              'Istisna degistiyse defteri bilincli olarak guncelle. '
              'Okunamayan dosyayi taranabilir hale getir; gercekten '
              "okunamiyorsa onay listesine gerekcesiyle yaz. Gitignore'da "
              'kalan dosyayi gorulmedi listesine gerekcesiyle bagla veya '
              'izlemeye al.')
        return 1

    tekil = len(sonuc.bulunan)
    adet = sum(len(v) for v in sonuc.bulunan.values())
    dosya = len({y for y, _h in sonuc.bulunan})
    print(ozet_satiri(kimlikler, sonuc, onay))
    print('ISTISNA: %d kayit · %d dosya · 0 bayat · %d tarihsel satir '
          '(%d tekil hash) · %d dosya · %d tanim eslesmesi'
          % (len(izinli), len({y for y, _h in izinli}), adet, tekil, dosya,
             len(sonuc.tanim)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
