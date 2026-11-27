#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutasyon_anlatim_kapisi — mutasyon sayilarini katalogdan turet ve anlatimi denetle.

NEDEN VAR
  Mutasyon bataryasi iki sozlesmeli: kirmizi atesleyen vakalar (HATA/TERMINAL)
  ve beklenen-bulgu vakalari. Tarihsel 12.128 snapshot'i 109 vaka = 91
  atesleyen + 18 beklenen-bulgu; guncel katalog 146 vaka = 117 atesleyen
  (109 HATA + 8 TERMINAL) + 29 beklenen-bulgu. Bu sayilar README, docs ve
  iddia defterine elle yazilir; biri guncellenmezse anlati sessizce tek
  sozlesmeli "hepsi kirmizi" bicimine geri kayabilir.

  Bu kapi sayilari vaka katalogundan yeniden turetir:
    * guncel: tools/mutasyon_sonuc.json icindeki her vakanin sozlesmesi,
    * tarihsel: tools/mutasyon_tarihsel_snapshot.json uyeligi + guncel
      katalogdaki sozlesme (FRZ-01T -> FRZ-01 takma adiyla).
  Sonra README.tr.md, README.en.md, docs/README.md, docs/EN/QUICKSTART.md,
  docs/DERSLER_v1_2026-08-30.md ve tools/iddia_defteri.json icindeki sayilari
  birebir karsilastirir. Tek-sozlesmeli ifadeler (146/146, 141/141, 140/140, "her vaka
  kirmizi") ve guncel baglamda tarihsel 109 toplami fail-closed reddedilir.

NE OLCMEZ
  Bataryayi yeniden kosmaz; son kosunun tools/mutasyon_sonuc.json kaydini
  okur. Bataryanin kaynak sha256'si ve canli atesleme sonucu `make mutasyon`
  ile olculur; bu kapi yalniz katalog ile kamu anlatimi arasindaki sayisal
  tutarliligi olcer.

KULLANIM
  python3 tools/mutasyon_anlatim_kapisi.py --kontrol
  python3 tools/mutasyon_anlatim_kapisi.py --kontrol --json
  python3 tools/mutasyon_anlatim_kapisi.py --kontrol --kok /gecici/kok

CIKIS
  0 : tarihsel ve guncel sayilar katalogdan turetildi; butun kaynak capalari
      ve iddia defteri satirlari tuttu; tek-sozlesmeli ifade yok
  1 : katalog/manifest bozuk, sayi tutmuyor, capa eksik/fazla veya yasak
      ifade var
  2 : kullanim hatasi
"""
import argparse
import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SONUC = Path('tools/mutasyon_sonuc.json')
TARIHsel = Path('tools/mutasyon_tarihsel_snapshot.json')
DEFTER = Path('tools/iddia_defteri.json')

SOZLESMELER = ('HATA', 'TERMINAL', 'BEKLENEN_BULGU')
DURUMLAR = {
    'HATA': 'GECTI',
    'TERMINAL': 'GECTI-TERMINAL',
    'BEKLENEN_BULGU': 'GECTI-BULGU',
}
# 12.128 / 588082a tarihsel snapshot'inin katalogdan turetilen sabit ozeti:
# (vaka, HATA, TERMINAL, atesleyen, beklenen-bulgu). Bu dortlu degisirse yeni
# bir snapshot kaydi gerekir; mevcut belgeler sessizce yeniden yazilmaz.
BEKLENEN_TARIHsel = (109, 84, 7, 91, 18)

GUNCEL_DOSYALAR = (
    'README.md',
    'README.tr.md',
    'README.en.md',
    'docs/README.md',
    'docs/EN/QUICKSTART.md',
)

# Her capa: dosya, desen, kac sayi grubu ve hangi turetilmis alanlara karsilik
# geldigi. Desen TAM 1 kez gecmelidir; yeni bir kopya sessizce sayilmaz.
CAPALAR = (
    {
        'ad': 'README.tr guncel batarya',
        'dosya': 'README.tr.md',
        'kaynak': 'guncel',
        'desen': (r'Mutation battery \*\*(\d+)/(\d+) firing cases'
                  r'(?: \([^)]*\))? \+ '
                  r'(\d+)/(\d+) expected findings\*\*'),
        'alanlar': ('atesleyen', 'atesleyen', 'bulgu', 'bulgu'),
    },
    {
        'ad': 'README.tr katalog dokumu',
        'dosya': 'README.tr.md',
        'kaynak': 'guncel',
        'desen': (r'Katalog (\d+) vakadır:\s*(\d+) ateşleyen '
                  r'\((\d+) HATA \+ (\d+) TERMINAL\) \+ '
                  r'(\d+) beklenen-bulgu\.'),
        'alanlar': ('vaka', 'atesleyen', 'hata', 'terminal', 'bulgu'),
    },
    {
        'ad': 'README.en guncel batarya',
        'dosya': 'README.en.md',
        'kaynak': 'guncel',
        'desen': (r'current battery is \*\*(\d+)/(\d+)\*\* firing cases'
                  r'(?: \([^)]*\))? plus \*\*(\d+)/(\d+)\*\* expected findings'),
        'alanlar': ('atesleyen', 'atesleyen', 'bulgu', 'bulgu'),
    },
    {
        'ad': 'docs/README guncel katalog',
        'dosya': 'docs/README.md',
        'kaynak': 'guncel',
        'desen': (r'Güncel katalog \*\*(\d+) vaka = (\d+) ateşleyen '
                  r'\((\d+) HATA \+ (\d+) TERMINAL\)\s*\+ '
                  r'(\d+) beklenen-bulgu\*\*'),
        'alanlar': ('vaka', 'atesleyen', 'hata', 'terminal', 'bulgu'),
    },
    {
        'ad': 'QUICKSTART guncel SONUC',
        'dosya': 'docs/EN/QUICKSTART.md',
        'kaynak': 'guncel',
        'desen': (r'SONUC: (\d+)/(\d+) kural atesledi · '
                  r'(\d+)/(\d+) beklenen bulgu dogrulandi'),
        'alanlar': ('atesleyen', 'atesleyen', 'bulgu', 'bulgu'),
    },
    {
        'ad': 'QUICKSTART guncel SOZLESME',
        'dosya': 'docs/EN/QUICKSTART.md',
        'kaynak': 'guncel',
        'desen': (r'SOZLESME: (\d+)/(\d+) HATA \(rc=1\) · '
                  r'(\d+)/(\d+) TERMINAL \(rc=2\) · '
                  r'(\d+)/(\d+) BEKLENEN_BULGU'),
        'alanlar': ('hata', 'hata', 'terminal', 'terminal', 'bulgu', 'bulgu'),
    },
    {
        'ad': 'DERSLER 12.128 tarihsel esitlik',
        'dosya': 'docs/DERSLER_v1_2026-08-30.md',
        'kaynak': 'tarihsel',
        'desen': r'(\d+) = (\d+) hata \+ (\d+) beklenen-bulgu',
        'alanlar': ('vaka', 'atesleyen', 'bulgu'),
    },
    {
        'ad': 'DERSLER 12.128 tarihsel sayac',
        'dosya': 'docs/DERSLER_v1_2026-08-30.md',
        'kaynak': 'tarihsel',
        'desen': r'(\d+) vaka; (\d+) kırmızı; (\d+) beklenen-bulgu',
        'alanlar': ('vaka', 'atesleyen', 'bulgu'),
    },
    {
        'ad': 'DERSLER 12.130 tarihsel sayac',
        'dosya': 'docs/DERSLER_v1_2026-08-30.md',
        'kaynak': 'tarihsel',
        'desen': r'(\d+) vaka / (\d+) ateşleme \+ (\d+) beklenen bulgu',
        'alanlar': ('vaka', 'atesleyen', 'bulgu'),
    },
    {
        'ad': 'DERSLER 12.166 guncel sayac',
        'dosya': 'docs/DERSLER_v1_2026-08-30.md',
        'kaynak': 'guncel',
        'desen': r'(\d+) vaka = (\d+) atesleyen \+ (\d+) beklenen',
        'alanlar': ('vaka', 'atesleyen', 'bulgu'),
    },
)

# Tek-sozlesmeli anlatimin dogrudan imzalari. Tarihsel DERSLER satirlari bu
# taramaya girmez; orada gecmis bir uygulamanin kaydi mesru olabilir.
YASAK_IFADELER = (
    (r'\b146/146\b', '146/146 (tum guncel vakalar kirmizi)'),
    (r'\b141/141\b', '141/141 (tum guncel vakalar kirmizi)'),
    (r'\b140/140\b', '140/140 (tum guncel vakalar kirmizi)'),
    # 109/109 artik guncel HATA alt-sayacidir (SOZLESME satiri); yalniz
    # HATA etiketi olmadan gecen tarihsel tum-vaka iddiasini reddet.
    (r'\b109/109\b(?!\s*HATA)', '109/109 (tum tarihsel vakalar kirmizi)'),
    (r'\bher vaka(?:sı|si)?\s+kırmızı\b', 'her vaka kirmizi'),
    (r'\btüm vakalar\s+kırmızı\b', 'tum vakalar kirmizi'),
    (r'\bbütün vakalar\s+kırmızı\b', 'butun vakalar kirmizi'),
    (r'\bevery case (?:is )?red\b', 'every case red'),
    (r'\ball cases (?:are )?red\b', 'all cases red'),
)


class KapiHatasi(Exception):
    """Sayi veya anlatim sozlesmesi tutmadi; kapi fail-closed kapanir."""


def _oku(kok, yol):
    try:
        return (kok / yol).read_text(encoding='utf-8')
    except OSError as exc:
        raise KapiHatasi('%s okunamadi: %s' % (yol, exc))


def _json(kok, yol):
    try:
        return json.loads(_oku(kok, yol))
    except ValueError as exc:
        raise KapiHatasi('%s JSON bozuk: %s' % (yol, exc))


def _katalog(kok):
    """Guncel vaka katalogunu ve sozlesme sayimlarini dondur."""
    veri = _json(kok, SONUC)
    if not isinstance(veri, dict) or veri.get('schema') != 'MUTASYON-SONUC/v1':
        raise KapiHatasi('%s: schema MUTASYON-SONUC/v1 degil' % SONUC)
    vakalar = veri.get('vakalar')
    if not isinstance(vakalar, list) or not vakalar:
        raise KapiHatasi('%s: vakalar listesi bos veya yok' % SONUC)
    sayim = dict.fromkeys(SOZLESMELER, 0)
    by_id = {}
    for sira, vaka in enumerate(vakalar, 1):
        if not isinstance(vaka, dict):
            raise KapiHatasi('%s: vaka %d nesne degil' % (SONUC, sira))
        kimlik = vaka.get('id')
        sozlesme = vaka.get('sozlesme')
        if not isinstance(kimlik, str) or not kimlik:
            raise KapiHatasi('%s: vaka %d id yok' % (SONUC, sira))
        if kimlik in by_id:
            raise KapiHatasi('%s: yinelenen vaka ID: %s' % (SONUC, kimlik))
        if sozlesme not in SOZLESMELER:
            raise KapiHatasi('%s: %s gecersiz sozlesme: %r'
                             % (SONUC, kimlik, sozlesme))
        if vaka.get('gecti') is not True:
            raise KapiHatasi('%s: %s gecti=true degil; batarya yesil degil'
                             % (SONUC, kimlik))
        if vaka.get('durum') != DURUMLAR[sozlesme]:
            raise KapiHatasi('%s: %s durum %r, sozlesme %s icin %r olmali'
                             % (SONUC, kimlik, vaka.get('durum'), sozlesme,
                                DURUMLAR[sozlesme]))
        sayim[sozlesme] += 1
        by_id[kimlik] = vaka
    sayilar = veri.get('sayilar')
    if not isinstance(sayilar, dict) or sayilar.get('vaka') != len(vakalar):
        raise KapiHatasi('%s: sayilar.vaka %r, liste %d'
                         % (SONUC, (sayilar or {}).get('vaka'), len(vakalar)))
    atesleyen = sayim['HATA'] + sayim['TERMINAL']
    if atesleyen + sayim['BEKLENEN_BULGU'] != len(vakalar):
        raise KapiHatasi('%s: sozlesme toplami vaka sayisina esit degil'
                         % SONUC)
    return {
        'vaka': len(vakalar),
        'hata': sayim['HATA'],
        'terminal': sayim['TERMINAL'],
        'atesleyen': atesleyen,
        'bulgu': sayim['BEKLENEN_BULGU'],
        'by_id': by_id,
    }


def _tarihsel(kok, guncel):
    """Tarihsel uyeligi guncel katalog sozlesmeleriyle coz ve turet."""
    veri = _json(kok, TARIHsel)
    if not isinstance(veri, dict) or veri.get('schema') != 'MUTASYON-TARIHsel/v1':
        raise KapiHatasi('%s: schema MUTASYON-TARIHsel/v1 degil' % TARIHsel)
    for alan in ('surum', 'commit', 'kaynak'):
        if not isinstance(veri.get(alan), str) or not veri[alan]:
            raise KapiHatasi('%s: %s alani bos' % (TARIHsel, alan))
    sha = veri.get('kaynak_sha256')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha):
        raise KapiHatasi('%s: kaynak_sha256 64 hex degil' % TARIHsel)
    kimlikler = veri.get('vakalar')
    if not isinstance(kimlikler, list) or not kimlikler:
        raise KapiHatasi('%s: vakalar listesi bos veya yok' % TARIHsel)
    if len(kimlikler) != len(set(kimlikler)):
        raise KapiHatasi('%s: tarihsel vaka ID yineleniyor' % TARIHsel)
    takma = veri.get('takma_adlar') or {}
    if not isinstance(takma, dict):
        raise KapiHatasi('%s: takma_adlar nesne degil' % TARIHsel)
    for eski, yeni in takma.items():
        if eski not in kimlikler:
            raise KapiHatasi('%s: olu takma ad: %s' % (TARIHsel, eski))
        if eski == yeni:
            raise KapiHatasi('%s: takma ad kendine cozuluyor: %s'
                             % (TARIHsel, eski))
        if yeni not in guncel['by_id']:
            raise KapiHatasi('%s: takma ad hedefi katalogda yok: %s -> %s'
                             % (TARIHsel, eski, yeni))
    sayim = dict.fromkeys(SOZLESMELER, 0)
    for kimlik in kimlikler:
        hedef = takma.get(kimlik, kimlik)
        vaka = guncel['by_id'].get(hedef)
        if vaka is None:
            raise KapiHatasi('%s: tarihsel vaka guncel katalogda yok: %s'
                             % (TARIHsel, kimlik))
        sozlesme = vaka['sozlesme']
        if kimlik in takma and sozlesme == 'BEKLENEN_BULGU':
            raise KapiHatasi('%s: takma ad bulguya cozulemez: %s -> %s'
                             % (TARIHsel, kimlik, hedef))
        sayim[sozlesme] += 1
    atesleyen = sayim['HATA'] + sayim['TERMINAL']
    ozet = {
        'vaka': len(kimlikler),
        'hata': sayim['HATA'],
        'terminal': sayim['TERMINAL'],
        'atesleyen': atesleyen,
        'bulgu': sayim['BEKLENEN_BULGU'],
        'takma': tuple(sorted(takma)),
    }
    turetilen = (ozet['vaka'], ozet['hata'], ozet['terminal'],
                 ozet['atesleyen'], ozet['bulgu'])
    if turetilen != BEKLENEN_TARIHsel:
        raise KapiHatasi(
            '%s: tarihsel sayilar %r, beklenen %r (vaka/HATA/TERMINAL/'
            'atesleyen/bulgu)' % (TARIHsel, turetilen, BEKLENEN_TARIHsel))
    return ozet


def _satir_no(metin, konum):
    return metin.count('\n', 0, konum) + 1


def _capa_denetle(kok, capa, guncel, tarihsel):
    metin = _oku(kok, capa['dosya'])
    eslesmeler = list(re.finditer(capa['desen'], metin, re.S))
    if len(eslesmeler) != 1:
        raise KapiHatasi(
            '%s: "%s" deseni %d kez gecti (tam 1 olmali)'
            % (capa['dosya'], capa['ad'], len(eslesmeler)))
    eslesme = eslesmeler[0]
    sayilar = tuple(int(g) for g in eslesme.groups())
    ozet = guncel if capa['kaynak'] == 'guncel' else tarihsel
    beklenen = tuple(ozet[alan] for alan in capa['alanlar'])
    if sayilar != beklenen:
        raise KapiHatasi(
            '%s:%d "%s": %r, katalogdan turetilen %r'
            % (capa['dosya'], _satir_no(metin, eslesme.start()),
               capa['ad'], sayilar, beklenen))
    return 1


def _bayat_109_tara(kok):
    """Guncel kamu dosyalarinda tarihsel 109 toplami etiketsiz gecmemeli."""
    for dosya in GUNCEL_DOSYALAR:
        metin = _oku(kok, dosya)
        for eslesme in re.finditer(r'\b109\b', metin):
            satir = metin[metin.rfind('\n', 0, eslesme.start()) + 1:
                          metin.find('\n', eslesme.start())
                          if metin.find('\n', eslesme.start()) != -1
                          else len(metin)]
            # 109 artik guncel HATA alt-sayacidir; tarihsel tum-vaka
            # toplamiyla karistirilmamali.
            if '109 HATA' in satir or re.search(r'\b109/109\s+HATA\b', satir):
                continue
            if not re.search(r'vaka|case|mutasyon|mutation|firing|ateş|'
                             r'beklenen|bulgu', satir, re.I):
                continue
            if re.search(r'tarih|historical|snapshot|ara snapshot|588082a|'
                         r'12\.(?:128|130|166)', satir, re.I):
                continue
            raise KapiHatasi(
                '%s:%d tarihsel 109 toplami guncel baglamda etiketsiz: %s'
                % (dosya, _satir_no(metin, eslesme.start()), satir.strip()[:160]))
    return 0


def _tek_sozlesme_tara(kok):
    for dosya in GUNCEL_DOSYALAR:
        metin = _oku(kok, dosya)
        for desen, ad in YASAK_IFADELER:
            eslesme = re.search(desen, metin, re.I)
            if eslesme:
                raise KapiHatasi(
                    '%s:%d tek-sozlesmeli ifade (%s): %s'
                    % (dosya, _satir_no(metin, eslesme.start()), ad,
                       metin[eslesme.start():eslesme.end()]))
    return 0


def _defter_denetle(kok, guncel, tarihsel):
    defter = _json(kok, DEFTER)
    if not isinstance(defter, dict) or not isinstance(defter.get('iddialar'), list):
        raise KapiHatasi('%s: iddialar listesi yok' % DEFTER)
    by_id = {}
    for kayit in defter['iddialar']:
        if isinstance(kayit, dict) and isinstance(kayit.get('id'), str):
            by_id[kayit['id']] = kayit
    beklenenler = (
        ('IDD-04', '%d/%d' % (guncel['atesleyen'], guncel['atesleyen']), ()),
        ('IDD-05', '%d/%d' % (guncel['bulgu'], guncel['bulgu']), ()),
        ('IDD-39', '%d' % guncel['vaka'],
         ('%d' % guncel['atesleyen'], '%d' % guncel['bulgu'])),
        ('IDD-52', '%d/%d' % (guncel['hata'], guncel['hata']),
         ('%d/%d' % (guncel['terminal'], guncel['terminal']),
          '%d/%d' % (guncel['bulgu'], guncel['bulgu']))),
        ('IDD-56', '%d/%d/%d' % (tarihsel['vaka'], tarihsel['atesleyen'],
                                 tarihsel['bulgu']), ()),
    )
    for kimlik, beklenen, ekler in beklenenler:
        kayit = by_id.get(kimlik)
        if kayit is None:
            raise KapiHatasi('%s: %s satiri yok' % (DEFTER, kimlik))
        if kayit.get('beklenen') != beklenen:
            raise KapiHatasi(
                '%s: %s beklenen %r, katalogdan turetilen %r'
                % (DEFTER, kimlik, kayit.get('beklenen'), beklenen))
        iddia = kayit.get('iddia')
        if not isinstance(iddia, str) or beklenen not in iddia:
            raise KapiHatasi(
                '%s: %s iddia metni turetilen %r degerini tasimiyor'
                % (DEFTER, kimlik, beklenen))
        for ek in ekler:
            if ek not in iddia:
                raise KapiHatasi(
                    '%s: %s iddia metni %r parcacigini tasimiyor'
                    % (DEFTER, kimlik, ek))
    return len(beklenenler)


def denetle(kok):
    guncel = _katalog(kok)
    tarihsel = _tarihsel(kok, guncel)
    capa = sum(_capa_denetle(kok, c, guncel, tarihsel) for c in CAPALAR)
    _bayat_109_tara(kok)
    _tek_sozlesme_tara(kok)
    iddia = _defter_denetle(kok, guncel, tarihsel)
    return guncel, tarihsel, capa, iddia


def _json_satiri(guncel, tarihsel, capa, iddia):
    return json.dumps({
        'schema': 'MUTASYON-ANLATIM/v1',
        'guncel': '%d/%d/%d' % (guncel['vaka'], guncel['atesleyen'],
                                guncel['bulgu']),
        'tarihsel': '%d/%d/%d' % (tarihsel['vaka'], tarihsel['atesleyen'],
                                  tarihsel['bulgu']),
        'guncel_ayrinti': {k: guncel[k] for k in
                           ('vaka', 'hata', 'terminal', 'atesleyen', 'bulgu')},
        'tarihsel_ayrinti': {k: tarihsel[k] for k in
                             ('vaka', 'hata', 'terminal', 'atesleyen', 'bulgu')},
        'capa': capa,
        'iddia': iddia,
    }, ensure_ascii=False, sort_keys=True)


def main(argv=None):
    ayristirici = argparse.ArgumentParser(
        description='Mutasyon sayilarini katalogdan turet ve anlatimi denetle.')
    ayristirici.add_argument('--kontrol', action='store_true',
                             help='varsayilan: denetimi kos')
    ayristirici.add_argument('--json', action='store_true',
                             help='tek satir makine okur ozet bas')
    ayristirici.add_argument('--kok', default=None,
                             help='depo koku (oz-test icin); varsayilan bu agac')
    args = ayristirici.parse_args(argv)
    kok = Path(args.kok).resolve() if args.kok else KOK
    try:
        guncel, tarihsel, capa, iddia = denetle(kok)
    except KapiHatasi as exc:
        if args.json:
            print(json.dumps({'schema': 'MUTASYON-ANLATIM/v1',
                              'hukum': 'FAIL', 'hata': str(exc)},
                             ensure_ascii=False, sort_keys=True))
        else:
            print('HUKUM: FAIL — %s' % exc)
        return 1

    if args.json:
        print(_json_satiri(guncel, tarihsel, capa, iddia))
        return 0

    print('MUTASYON ANLATIM KAPISI')
    print('kaynak: %s' % kok)
    print('KATALOG: guncel %d vaka = %d atesleyen (%d HATA + %d TERMINAL) '
          '+ %d beklenen-bulgu' % (
              guncel['vaka'], guncel['atesleyen'], guncel['hata'],
              guncel['terminal'], guncel['bulgu']))
    print('TARIHsel: %d vaka = %d atesleyen (%d HATA + %d TERMINAL) '
          '+ %d beklenen-bulgu' % (
              tarihsel['vaka'], tarihsel['atesleyen'], tarihsel['hata'],
              tarihsel['terminal'], tarihsel['bulgu']))
    if tarihsel['takma']:
        print('  takma ad: %s' % ', '.join(
            '%s -> guncel katalog' % k for k in tarihsel['takma']))
    print('CAPA: %d/%d kaynak ifadesi katalogla ayni' % (capa, len(CAPALAR)))
    print('IDDIA: %d/%d defter satiri katalogla ayni' % (iddia, 5))
    print('TEK SOZLESME: 0 yasak ifade · 0 etiketsiz tarihsel 109')
    print('HUKUM: PASS — 109/91/18 ve guncel sayilar katalogdan turetildi; '
          'README, docs ve iddia defteri tuttu.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
