#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dogrula.py — bu deponun TEK GIRIS dogrulamasi (fail-closed).

NEDEN VAR: "bitti" diyen sey bir his olmamali. Kalemler sirayla kosar, her
kalemin ham ciktisinin son satiri basilir ve hukum rc'lerin toplamindan cikar.
Bir kalem FAIL verdiginde de kalanlar kosar ki tek turda tam manzara gorunsun.

Iki kip vardir:

  (varsayilan)        Tam kapi. Laboratuvarin kendi ortaminda (macOS + yerel
                      opencode model katalogu) her sey kosar.
  --ci                Runner kipi. Hukum AYNI kurallarla verilir: ayri bir
                      muafiyet yoktur. Kalan fark yalnizca basliktadir; sabit
                      katalog sayesinde sayilar runner'da da ayni cikar.

OLG-1: bu agac kendi `attestation.json` kanitini kullanir; `atlas_selftest`
icindeki OLG-1 kosar. Attestation yoksa/bozuksa OLG-1 FAIL'dir.
Her kalemin kendi hukum satiri basilir; stderr'e dusen bir uyari (or. urllib3
NotOpenSSLWarning) hukum satiri sayilmaz. JSON rapor basan aracin ozeti kendi
sayaclarindan uretilir.

CALISTIRILMADI yalniz gercekten olculemeyen kalemler icin (or. --hizli veya
model katalogu yoklugu) basilir ve hukme SAYILMAZ; her satir nedenini tasir.

PARITE (OPSIYONEL): `ATLAS_LAB` tanimliysa once `tools/yayinla.py` kuru kosusu
calisir; sifir suruklenme yoksa hukum FAIL olur. Tanimsizsa bu kontrol
atlanir, cunku public klonda dis lab yoktur; 8/8 hukmu degismez.

MODEL KATALOGU: varsayilan kosu DEPODAKI sabit katalogu kullanir
(`tools/model_katalog.json`) ve makinedeki `~/.cache/opencode/models.json`
dosyasini OKUMAZ. Boylece ayni commit her klonda ayni sayiyi verir. Sabit
katalog bir ALLOWLIST anlik goruntusudur: kapi, ajanlarin bu listedeki modelleri
kullandigini denetler. Canli katalogla denetim icin `ATLAS_MODEL_KATALOG=<yol>`
verin; fark yalnizca katalog ICERIGINDEN gelir, makineden degil.

MODEL KIMLIGI: emekli bir model kimligi yalnizca `tools/model_kimlik_istisna.json`
icinde dosya + tam satir SHA-256'siyla kayitli tarihsel `SURUM`/`OLCUM`
satirlarinda kalabilir. Aktif kod/config/test/dokumanda tek bir atif bile
hukmu FAIL eder. Aday dosyalarin tamami incelenir: UTF-8 cozulenler satir
satir, cozulemeyen veya NUL icerenler ikili guvenli bayt aramasiyla ve boyut
siniri olmadan taranir; onay listesinde olmayan tek bir incelenemeyen dosya da
FAIL uretir. Bu kontrol sayilan sekiz kaleme eklenmez; demo gibi bir on
kosuldur ve `make dogrula`yi fail-closed durdurur.

CIKIS: 0 = hukme giren kalemlerin hepsi gecti (CALISTIRILMADI varsa bile) ·
       1 = en az bir kalem FAIL · 2 = kosulamadi

OLG-1'in kaniti `attestation.json`'dir; yoksa/bozuksa FAIL'dir, CALISTIRILMADI
degil. Sahte canak (commit, tarihce) uretilmez.
"""
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
import sys

import kapi_cikti

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIZLI = '--hizli' in sys.argv
CI = '--ci' in sys.argv
JSON = '--json' in sys.argv
JSON_RAPOR = None

ATLA_DIZIN = {'.git', '__pycache__', 'node_modules', '.pytest_cache',
              '.ruff_cache', '.venv', '.venv-token', 'kanit-paketi'}
ATLA_UZANTI = {'.pyc', '.pyo'}

SIR_KALIPLARI = [
    ('postgres-dsn', re.compile(r'postgres(?:ql)?://[^\s:/]+:[^\s@]+@')),
    ('neon', re.compile(r'npg_[A-Za-z0-9]{8,}')),
    ('openai', re.compile(r'sk-(?:proj-)?[A-Za-z0-9]{24,}')),
    ('github', re.compile(r'ghp_[A-Za-z0-9]{30,}')),
    ('aws', re.compile(r'AKIA[0-9A-Z]{16}')),
    ('slack', re.compile(r'xox[bap]-[A-Za-z0-9-]{10,}')),
    ('google', re.compile(r'AIza[0-9A-Za-z_-]{35}')),
]
# Kendi sir tarayicisinin test fiksturleri DESEN/DOSYA ile degil, tam satir
# SHA-256'siyla susturulur. Manifest aracin kendi deposundadir; hedefin
# getirdigi bir manifest otomatik okunmaz.
FIKSTUR_DOSYASI = os.path.join(KOK, 'tools', 'secret_fixtures.json')
# Gercek PEM anahtarinin basligin ALTINDA uzun base64 govdesi vardir. Ornek
# komutlarda gecen `-----BEGIN ... KEY-----\\nMII...` bu desene uymaz; ham grep
# saymak yerine gercek bicimi ariyoruz.
ANAHTAR = re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----\r?\n[A-Za-z0-9+/=]{64,}')

# kid -> (izinli kimlikler, ciktida aranan ek kanit, gerekce)
# T1 (OLG-1) artik attestation ile kosar; attestation arzasi CALISTIRILMADI
# degil FAIL'dir. Bu yuzden T1 icin ortam istisnasi YOKTUR.
ORTAM_BAGLI = {
    # KOD'un katalog yoklugunda kosamayan dort testi AYRI AYRI adlandirilir;
    # kanit dizgisi olmadan bu kimlikler CALISTIRILMADI sayilmaz.
    'T2': ({'MOD-1', 'MOD-2', 'K8-1', 'K8-2', 'O3-09c', 'O3-09d'},
           'model katalogu yok',
           'model katalogu verilmedi (ATLAS_MODEL_KATALOG)'),
}

# Depoda tasinan sabit katalog (allowlist anlik goruntusu).
KATALOG_SABIT = os.path.join(KOK, 'tools', 'model_katalog.json')
# Sabit katalog yoksa: makinedeki onbellegi okumayan yokluk isareti.
KATALOG_YOK = os.path.join(KOK, '.model-katalog-verilmedi.json')

# Bu ortamda olculemeyen, yalnizca raporlanan paketler (yalniz --ci'da).
CI_RAPOR = {'T1', 'T2'}


def gez():
    for kok, dizinler, dosyalar in os.walk(KOK):
        dizinler[:] = [d for d in dizinler if d not in ATLA_DIZIN]
        for ad in dosyalar:
            if os.path.splitext(ad)[1] in ATLA_UZANTI:
                continue
            yield os.path.join(kok, ad)


def hijyen():
    kotu = []
    for tam in gez():
        rel = os.path.relpath(tam, KOK)
        if os.path.islink(tam) and not os.path.exists(tam):
            kotu.append('kirik symlink: %s -> %s' % (rel, os.readlink(tam)))
            continue
        if os.path.basename(tam) == '.DS_Store':
            kotu.append('macOS artefakti: %s' % rel)
        elif os.path.getsize(tam) > 5 * 1024 * 1024:
            kotu.append('5 MB ustu: %s' % rel)
    return not kotu, '%d bulgu' % len(kotu), kotu


def py_sozdizimi():
    kotu = []
    sayi = 0
    for tam in gez():
        if not tam.endswith('.py'):
            continue
        sayi += 1
        try:
            with open(tam, 'rb') as f:
                compile(f.read(), tam, 'exec')
        except SyntaxError as e:
            kotu.append('%s:%s %s' % (os.path.relpath(tam, KOK), e.lineno, e.msg))
    return not kotu, '%d dosya' % sayi, kotu


def sh_sozdizimi():
    kotu = []
    sayi = 0
    for tam in gez():
        if not tam.endswith('.sh'):
            continue
        sayi += 1
        r = subprocess.run(['bash', '-n', tam], capture_output=True, text=True)
        if r.returncode != 0:
            kotu.append('%s: %s' % (os.path.relpath(tam, KOK),
                                    (r.stderr or '').strip()[:120]))
    return not kotu, '%d dosya' % sayi, kotu


def _fikstur_kumesi():
    try:
        with open(FIKSTUR_DOSYASI, encoding='utf-8') as f:
            veri = json.load(f)
        if not isinstance(veri, dict) or not isinstance(veri.get('fiksturler'), list):
            raise ValueError('fiksturler listesi yok')
        kume = set()
        for k in veri['fiksturler']:
            if not isinstance(k, dict):
                raise ValueError('fikstur kaydi nesne degil')
            rel = str(k.get('dosya', '')).replace('\\', '/')
            h = str(k.get('satir_sha256', ''))
            if (not rel or rel.startswith('/') or '..' in rel.split('/')
                    or not re.fullmatch(r'[0-9a-f]{64}', h)
                    or not str(k.get('gerekce', '')).strip()
                    or not str(k.get('kanit', '')).strip()):
                raise ValueError('gecersiz kayit: %r' % rel)
            if (rel, h) in kume:
                raise ValueError('yinelenen kayit: %r' % rel)
            kume.add((rel, h))
        return kume, None
    except Exception as e:
        # Fail-closed: manifest okunamazsa sir taramasi temiz sayilmaz.
        return None, str(e)[:180]


def sir_tarama():
    fikstur, hata = _fikstur_kumesi()
    if fikstur is None:
        return False, 'fikstur manifesti hatasi', [hata]
    kotu = []
    for tam in gez():
        if os.path.getsize(tam) > 2 * 1024 * 1024:
            continue
        try:
            with open(tam, encoding='utf-8') as f:
                metin = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        rel = os.path.relpath(tam, KOK)
        for no, satir in enumerate(metin.splitlines(), 1):
            h = hashlib.sha256(satir.encode('utf-8')).hexdigest()
            if (rel, h) in fikstur:
                continue
            for ad, kalip in SIR_KALIPLARI:
                if kalip.search(satir):
                    kotu.append('%s:%d (%s)' % (rel, no, ad))
        for m in ANAHTAR.finditer(metin):
            kotu.append('%s:%d (private-key)'
                        % (rel, metin[:m.start()].count('\n') + 1))
    return not kotu, '%d bulgu' % len(kotu), kotu


def kapi_oztesti():
    """sir_kapisi oz-testi: canli desen kirmizi, yer tutucu sessiz (H5)."""
    rc, cikti, _ = kos([sys.executable,
                        os.path.join(KOK, 'tools', 'sir_kapisi_selftest.py')])
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    son = satirlar[-1][:110] if satirlar else '(bos cikti)'
    return rc == 0, son, ([] if rc == 0 else satirlar[-6:])


def demo_oztesti():
    """demo'nun 0/1/2 sozlesmesini gecici fiksturlerle on kontrol olarak kosar.

    Sayilan sekiz kaleme dahil degildir; parite gibi bir on kosuldur. Yine de
    basarisizsa dogrula yesil donmez.
    """
    rc, cikti, _ = kos([sys.executable,
                        os.path.join(KOK, 'tools', 'demo_selftest.py')])
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    son = satirlar[-1][:110] if satirlar else '(bos cikti)'
    return rc == 0, son, ([] if rc == 0 else satirlar[-8:])


def model_kimlik():
    """Emekli model kimligi taramasini on kosul olarak kosar.

    Sayilan sekiz kaleme dahil degildir; demo gibi bir on kosuldur. Aktif bir
    atif veya bayat istisna varsa dogrula yesil donmez.
    """
    rc, cikti, _ = kos([sys.executable,
                        os.path.join(KOK, 'tools', 'model_kimlik.py'),
                        '--kontrol'])
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    baslik = [s for s in satirlar if s.startswith('MODEL KIMLIK')]
    son = (baslik[0] if baslik else (satirlar[-1] if satirlar else '(bos cikti)'))
    return rc == 0, son[:150], ([] if rc == 0 else satirlar[-8:])


def kamu_temizligi():
    """Ozel yol/eski alan/sahte hash geri sizmasini on kosul olarak yakalar.

    Sayilan sekiz kaleme dahil degildir; demo ve model kimligi gibi bir on
    kosuldur. Kontrolun kendi negatif fiksturleri de ayni cagrida kosar.
    """
    rc, cikti, _ = kos([sys.executable,
                        os.path.join(KOK, 'tools', 'kamu_lint.py'),
                        '--kontrol', '--oztest'])
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    baslik = [s for s in satirlar if s.startswith('KAMU-LINT:')]
    son = (baslik[-1] if baslik else (satirlar[-1] if satirlar else '(bos cikti)'))
    return rc == 0, son[:150], ([] if rc == 0 else satirlar[-10:])


def yayin_kapisi():
    """Yayin manifesti + makale/sir/ozel yol kapisini on kosul yapar.

    Sayilan sekiz kaleme dahil degildir; kamu temizligi gibi bir on kosuldur.
    Kendi negatif fiksturlerini de ayni cagrida kosar.
    """
    rc, cikti, _ = kos([sys.executable,
                        os.path.join(KOK, 'tools', 'yayin_kapisi.py'),
                        '--kontrol', '--oztest'])
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    baslik = [s for s in satirlar if s.startswith('YAYIN-KAPISI:')]
    son = (baslik[-1] if baslik else (satirlar[-1] if satirlar else '(bos cikti)'))
    return rc == 0, son[:150], ([] if rc == 0 else satirlar[-12:])


KOMUTLAR = [
    ('T1', 'ATLAS oz-testi',
     [sys.executable, 'ATLAS_SABLONLAR/scripts/atlas_selftest.py', '--sessiz']),
    ('T2', 'KOD oz-testi',
     [sys.executable, 'KOD_SABLONLAR/scripts/kod_selftest.py']),
    ('T3', 'Toolkit oz-testi', [sys.executable, 'v4_selftest.py'],
     os.path.join(KOK, 'KOMUT_TOOLKIT_v4', 'ARACLAR', 'betikler')),
]


def _json_kontrol(kid, ad, durum, deger=None, ayrinti=None, ham=None):
    return kapi_cikti.kontrol(kid, ad, durum, deger=deger,
                              ayrinti=ayrinti, ham=ham)


def _json_yaz(kontroller, rc, hata=None):
    """JSON kipinin tek çıkışı; normal metin çıktısıyla karışmaz."""
    global JSON_RAPOR
    JSON_RAPOR = kapi_cikti.uret('dogrula', list(kontroller), rc=rc, hata=hata)


def _json_erken(kid, ad, ozet, hata):
    global JSON_RAPOR
    JSON_RAPOR = kapi_cikti.uret(
        'dogrula', [_json_kontrol(kid, ad, 'FAIL', deger=ozet,
                                  ayrinti=hata, ham=ozet)],
        rc=1, hukum='FAIL', hata=hata)


def _oran(ozet):
    """Özet metninden ilk n/n sayısını ayıkla; düzenli ifade kullanma."""
    for parca in str(ozet or '').replace(':', ' ').split():
        if parca.count('/') == 1:
            a, b = parca.split('/', 1)
            if a.isdigit() and b.isdigit():
                return parca
    return None


def _sayi(ozet):
    """İlk sayıyı döndür; yoksa özetin kendisini döndür."""
    for parca in str(ozet or '').split():
        if parca.isdigit():
            return parca
    return str(ozet or '')


def kos(komut, cwd=None):
    """(rc, stdout, stderr) — akislar AYRI doner.

    Ayirma kozmetik degil: birlestirilmis ciktida stderr uyarisi son satir
    olabiliyor ve "aracin ozeti" diye basilabiliyordu (olculmus kusur).
    """
    env = dict(os.environ)
    if not env.get('ATLAS_MODEL_KATALOG'):
        env['ATLAS_MODEL_KATALOG'] = (KATALOG_SABIT
                                      if os.path.isfile(KATALOG_SABIT)
                                      else KATALOG_YOK)
    try:
        r = subprocess.run(komut, cwd=cwd or KOK, capture_output=True,
                           text=True, env=env, timeout=900)
        return r.returncode, (r.stdout or ''), (r.stderr or '')
    except subprocess.TimeoutExpired:
        return 124, '', 'ZAMAN ASIMI (900 s)'
    except OSError as e:
        return 125, '', 'KOSULAMADI: %s' % e


def kimlikler(cikti, fail_de=False):
    """Kalan test kimlikleri. `fail_de` yalniz KOD paketi icin acilir: o paket
    `KALDI` degil `FAIL <kimlik>` basar. ATLAS'ta FAIL satirlari ayrinti metnidir,
    kimlik sayilirsa gercek kalem yanlis etiketlenir."""
    desen = (r'\s*(?:KALDI|FAIL)\s+([A-Za-z0-9_.-]+)' if fail_de
             else r'\s*KALDI\s+([A-Za-z0-9_.-]+):')
    kimlik = set()
    for satir in cikti.splitlines():
        m = re.match(desen, satir)
        if m:
            kimlik.add(m.group(1))
    return kimlik


def ortam_bagli_mi(kid, cikti):
    """Ortam bagliysa gerekce, degilse None. Kosul sert: butun kalan kimlikler
    izinli kumenin icinde olmali ve beklenen kanit dizgisi gorunmeli."""
    kural = ORTAM_BAGLI.get(kid)
    if not kural:
        return None
    izinli, ek_kanit, gerekce = kural
    kalan = kimlikler(cikti, fail_de=(kid == 'T2'))
    if not kalan or not kalan <= izinli:
        return None
    if ek_kanit not in cikti:
        return None
    return gerekce


# stderr'deki uyari satirlari hukum satiri degildir. Desen hem
# `<dosya>:<satir>: XWarning:` hem de `warnings.warn(` bicimini tanir.
UYARI_SATIRI = re.compile(r':\d+: [A-Za-z_]*Warning:|^warnings\.warn\(')


def _json_raporu(metin):
    """Aracin saf JSON raporunu okur; JSON degilse None (tahmin yok)."""
    try:
        veri = json.loads(metin)
    except ValueError:
        return None
    return veri if isinstance(veri, dict) else None


def _json_ozeti(metin):
    """JSON raporun ozetini KENDI sayaclarindan uretir.

    Sayilar bicim dizesine yazilmaz; alanlar eksik veya sayaclar hukumle
    celiskili ise None doner ve metin satirlarina dusulur — uydurma ozet
    basilmaz. Boylece T3'un `}` satiri yerine gercek toplam gorunur.
    """
    d = _json_raporu(metin)
    if d is None:
        return None
    sayilar = [d.get(anahtar) for anahtar in ('toplam', 'gecti', 'kaldi')]
    if not all(isinstance(x, int) and not isinstance(x, bool) for x in sayilar):
        return None
    toplam, gecen, kalan = sayilar
    hukum = d.get('verdict')
    if hukum not in ('ENGEL_YOK', 'ENGEL_VAR'):
        return None
    if gecen < 0 or kalan < 0 or gecen + kalan != toplam:
        return None
    if (kalan == 0) != (hukum == 'ENGEL_YOK'):
        return None
    ad = str(d.get('kapi') or 'OZ-TEST')[:40]
    if toplam == 0:
        return '%s: 0/0 test · HUKUM YOK (bos rapor)' % ad
    if kalan:
        return '%s: %d/%d gecti · %d kaldi · %s' % (ad, gecen, toplam, kalan, hukum)
    return '%s: %d/%d gecti · %s' % (ad, gecen, toplam, hukum)


def _ozet_satiri(metinler, satirlar):
    """Aracin kendi hukum satirini secer.

    Sirasiyla: (1) JSON rapor ozeti, (2) `N/N gecti` tasiyan hukum satiri,
    (3) uyari olmayan son satir. stderr uyarisi hicbir adimda PASS kaniti
    diye basilamaz; akislar ayri geldigi icin uyari ozete hic karismaz.
    """
    for metin in metinler:
        ozet = _json_ozeti(metin or '')
        if ozet:
            return ozet[:110]
    for satir in reversed(satirlar):
        if not UYARI_SATIRI.search(satir) and re.search(r'\d+/\d+ gecti', satir):
            return satir[:110]
    for satir in reversed(satirlar):
        if not UYARI_SATIRI.search(satir):
            return satir[:110]
    return '(bos cikti)'


def _kalan_satirlari(metin, satirlar):
    """Kalan testleri adlandirir: JSON raporda `testler`, metinde `KALDI`."""
    d = _json_raporu(metin or '')
    if d is not None and isinstance(d.get('testler'), list):
        adlar = []
        for test in d['testler']:
            if not isinstance(test, dict) or test.get('sonuc') == 'GECTI':
                continue
            adlar.append('KALDI %s: %s :: %s' % (test.get('id'),
                                                test.get('aciklama'),
                                                test.get('ayrinti')))
        return adlar[:20]
    return [s for s in satirlar if re.match(r'\s*KALDI', s)][:20]


def _kanit_capasi():
    """T1'in dayandigi attestation commit/tree capasi; okunamazsa 'yok' der."""
    try:
        with open(os.path.join(KOK, 'attestation.json'), encoding='utf-8') as f:
            d = json.load(f)
        return 'KANIT commit=%s tree=%s' % (str(d['commit'])[:7], str(d['tree'])[:7])
    except (OSError, ValueError, KeyError):
        return 'KANIT yok'


def _github_ozeti(kalemler, kalan, atlanan):
    """Actions is ozeti: 6/7 ile yesil CI arasindaki farki gorunur kilar."""
    yol = os.environ.get('GITHUB_STEP_SUMMARY')
    if not yol:
        return
    satirlar = ['## dogrula', '', '| Kalem | Hukum |', '|---|---|']
    for kid, ad, durum, _ozet, _detay, _not in kalemler:
        etiket = 'CALISTIRILMADI' if durum is None else ('PASS' if durum else 'FAIL')
        satirlar.append('| %s %s | %s |' % (kid, ad, etiket))
    satirlar.append('')
    if atlanan:
        satirlar.append('**Kabul edilen borc:** %s kosmuyor (%d kalem).'
                        % (', '.join(k[0] for k in atlanan), len(atlanan)))
    if kalan:
        satirlar.append('**FAIL:** %s' % ', '.join(k[0] for k in kalan))
    try:
        with open(yol, 'a', encoding='utf-8') as f:
            f.write('\n'.join(satirlar) + '\n')
    except OSError:
        pass


def parite_kontrolu():
    """ATLAS_LAB varsa yayin kuru kosusunu on kosul yapar.

    Donus: (None, '') = tanimsiz/atlandi · (True, ozet) = temiz ·
    (False, ozet) = drift ya da kosulamadi.
    """
    lab = os.environ.get('ATLAS_LAB')
    if not lab:
        return None, ''
    lab = os.path.expanduser(lab)
    if not os.path.isdir(lab):
        return False, 'ATLAS_LAB dizini yok: %s' % lab
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(KOK, 'tools', 'yayinla.py'),
             '--lab', lab], capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, 'parite kosulamadi: %s' % e
    cikti = ((r.stdout or '') + (r.stderr or '')).strip()
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    parite = [s for s in satirlar if s.startswith('PARITE:')]
    if r.returncode == 0:
        return True, (parite[-1] if parite else 'PARITE: TEMIZ')
    return False, (parite[-1] if parite else
                   (satirlar[-1] if satirlar else 'rc=%d' % r.returncode))


MUTASYON_HUKUM = ('HUKUM: PASS — her vaka temiz tabanda sessiz, '
                  'ihlalde kirmizi/beklenen bulgu.')


def _make_hedefleri():
    """Makefile'daki hedef adlarini dondur."""
    try:
        with open(os.path.join(KOK, 'Makefile'), encoding='utf-8') as f:
            satirlar = f.readlines()
    except OSError:
        return set()
    hedefler = set()
    for satir in satirlar:
        m = re.match(r'^([A-Za-z0-9_.%/-]+)\s*:(?!=)', satir)
        if m:
            hedefler.add(m.group(1))
    return hedefler


def _make_referanslari(metin):
    """Yalniz kod span'i ve fenced bloklardaki make cagrilarini topla."""
    parcalar = []
    for m in re.finditer(r'`([^`\n]+)`', metin):
        parcalar.append((m.group(1), metin.count('\n', 0, m.start()) + 1))
    ic = False
    for no, satir in enumerate(metin.splitlines(), 1):
        if satir.strip().startswith('```'):
            ic = not ic
            continue
        if ic:
            parcalar.append((satir, no))
    refs = []
    for parca, no in parcalar:
        for m in re.finditer(r'(?<![\w./-])make\s+([A-Za-z0-9_.-]+)', parca):
            refs.append((m.group(1), no))
    return refs


def _text_bloklari(metin):
    """Dokumandaki ```text bloklarini sirayla dondur."""
    bloklar = []
    ic = False
    dil = ''
    satirlar = []
    for satir in metin.splitlines():
        if satir.strip().startswith('```'):
            if not ic:
                ic = True
                dil = satir.strip()[3:].strip()
                satirlar = []
            else:
                ic = False
                if dil == 'text':
                    bloklar.append(satirlar)
            continue
        if ic:
            satirlar.append(satir)
    return bloklar


def _cikti_satirlari(stdout, stderr):
    return {s.strip() for s in ((stdout or '') + (stderr or '')).splitlines()
            if s.strip()}


def _kapi_ornek(satir, ham):
    """QUICKSTART metin ornegini surumlu zarfin ham kanitiyla eslestir.

    Ornekler kullanicinin gordugu normal ciktidir; kanit ise `dogrula --json`
    zarfidir. Karsilastirma yine deger uzerinden yapilir: ornekteki H1/H3/H4
    sayisi veya H5 orani zarftaki PASS degeriyle ayni olmalidir.
    """
    if satir in ham:
        return True
    parca = satir.split()
    if not parca:
        return False
    kid = parca[0]
    if kid in ('H1', 'H3', 'H4'):
        try:
            i = parca.index('PASS')
            deger = parca[i + 1]
        except (ValueError, IndexError):
            return False
        return ('dogrula %s PASS %s' % (kid, deger)) in ham
    if kid == 'H5':
        oran = _oran(satir)
        return bool(oran) and ('dogrula H5 PASS %s' % oran) in ham
    if satir.startswith('kalem='):
        return ('dogrula ' + satir) in ham
    if satir.startswith('HUKUM: PASS'):
        # 8/8 kalem ornegini RAPOR zarfindaki gecen/kalan ile karsilastir.
        for adet in str(satir).split():
            if adet.count('/') == 1:
                gecen, toplam = adet.split('/', 1)
                if gecen.isdigit() and toplam.isdigit():
                    return any(
                        h.startswith('dogrula kalem=%s' % toplam)
                        and 'gecen=%s' % gecen in h and 'kalan=0' in h
                        for h in ham)
        return False
    return False


def _mutasyon_hukum_uretiliyor():
    """HUKUM satirinin mutasyon aracinin print'i oldugunu denetle."""
    try:
        with open(os.path.join(KOK, 'tools', 'mutasyon_bataryasi.py'),
                  encoding='utf-8') as f:
            kaynak = f.read()
    except OSError:
        return False
    kalip = r"print\((['\"])%s\1\)" % re.escape(MUTASYON_HUKUM)
    return re.search(kalip, kaynak) is not None


def quickstart_kontrolu():
    """QUICKSTART komutlarini ve ornek ciktilarini gercek araclarla karsilastir.

    Makinece uretilen satirlar `iddia_olcum.json`, yayinla ve demo ciktisiyla;
    HUKUM satiri da onu basan aracin kaynagiyla dogrulanir. Ozet/detay donusu
    `main` icin (gecti, ozet, detay) seklindedir.
    """
    hatalar = []
    yol = os.path.join(KOK, 'docs', 'EN', 'QUICKSTART.md')
    try:
        with open(yol, encoding='utf-8') as f:
            metin = f.read()
    except OSError as e:
        return False, 'okunamadi', [str(e)]

    hedefler = _make_hedefleri()
    if not hedefler:
        hatalar.append('Makefile hedefleri okunamadi')
    refs = _make_referanslari(metin)
    for hedef, no in refs:
        if hedef not in hedefler:
            hatalar.append('satir %d: make %s hedefi yok' % (no, hedef))

    bloklar = _text_bloklari(metin)
    if len(bloklar) != 4:
        hatalar.append('text blok sayisi 4 degil: %d' % len(bloklar))
        return False, '%d sorun' % len(hatalar), hatalar

    ham = set()
    try:
        with open(os.path.join(KOK, 'tools', 'iddia_olcum.json'),
                  encoding='utf-8') as f:
            veri = json.load(f)
        ham = {str(v.get('ham', '')).strip()
               for v in veri.get('olcumler', {}).values()
               if str(v.get('ham', '')).strip()}
    except (OSError, ValueError) as e:
        hatalar.append('iddia_olcum okunamadi: %s' % e)

    try:
        yayin = subprocess.run(
            [sys.executable, os.path.join(KOK, 'tools', 'yayinla.py'),
             '--lab', '.'], cwd=KOK, capture_output=True, text=True,
            timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        hatalar.append('yayinla kosulamadi: %s' % e)
        yayin = None
    if yayin is not None and yayin.returncode != 0:
        hatalar.append('yayinla rc=%d' % yayin.returncode)

    try:
        demo = subprocess.run(
            [os.path.join(KOK, 'demo')], cwd=KOK, capture_output=True,
            text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        hatalar.append('demo kosulamadi: %s' % e)
        demo = None
    if demo is not None and demo.returncode != 1:
        hatalar.append('demo rc=%d (beklenen 1)' % demo.returncode)

    yayin_satirlari = (_cikti_satirlari(yayin.stdout, yayin.stderr)
                       if yayin is not None else set())
    demo_satirlari = (_cikti_satirlari(demo.stdout, demo.stderr)
                      if demo is not None else set())
    hukum_kaynakta = _mutasyon_hukum_uretiliyor()
    rol = ('dogrula', 'mutasyon', 'yayinla', 'demo')
    sayi = 0
    for ad, satirlar in zip(rol, bloklar):
        for satir in satirlar:
            s = satir.strip()
            if not s or '...' in s or '<' in s or '>' in s:
                continue
            sayi += 1
            if ad == 'dogrula':
                if not _kapi_ornek(s, ham):
                    hatalar.append('dogrula ornegi yok: %s' % s)
            elif ad == 'mutasyon':
                if s.startswith('HUKUM: PASS'):
                    if s != MUTASYON_HUKUM or not hukum_kaynakta:
                        hatalar.append('mutasyon HUKUM ornegi drift: %s' % s)
                elif s not in ham:
                    hatalar.append('mutasyon ornegi yok: %s' % s)
            elif ad == 'yayinla':
                if s not in yayin_satirlari:
                    hatalar.append('yayinla ornegi yok: %s' % s)
            elif s not in demo_satirlari:
                hatalar.append('demo ornegi yok: %s' % s)

    if hatalar:
        return False, '%d sorun' % len(hatalar), hatalar
    return (True, '%d hedef · %d blok · %d satir'
            % (len(set(h for h, _ in refs)), len(bloklar), sayi), [])


def main():
    kip = 'CI' if CI else ('HIZLI' if HIZLI else 'TAM')
    print('ATLAS — tek giris dogrulama · %s' % kip)
    print('kok: %s' % KOK)
    if os.environ.get('ATLAS_MODEL_KATALOG'):
        print('model katalogu: %s' % os.environ['ATLAS_MODEL_KATALOG'])
    elif os.path.isfile(KATALOG_SABIT):
        print('model katalogu: depo sabiti (tools/model_katalog.json)')
    else:
        print('model katalogu: YOK — model kalemleri CALISTIRILMADI olur')
    print()

    parite, parite_not = parite_kontrolu()
    if parite is not None:
        print('  %-24s %s' % ('parite (yayinla)', parite_not))
        if not parite:
            if JSON:
                _json_erken('ONKOSUL.PARITE', 'parite (yayinla)', parite_not,
                            'parite FAIL')
            print()
            print('  HUKUM: FAIL — PARITE (yayinla kuru kosusu)')
            return 1
        print()

    demo_gecti, demo_ozet, demo_detay = demo_oztesti()
    print('  %-24s %-7s %s' % ('demo 0/1/2 oz-testi',
                                'PASS' if demo_gecti else 'FAIL', demo_ozet))
    for satir in demo_detay:
        print('        | %s' % satir[:400])
    if not demo_gecti:
        if JSON:
            _json_erken('ONKOSUL.DEMO', 'demo 0/1/2 oz-testi', demo_ozet,
                        'demo 0/1/2 oz-testi FAIL')
        print()
        print('  HUKUM: FAIL — DEMO 0/1/2 OZ-TESTI')
        return 1
    print()

    model_gecti, model_ozet, model_detay = model_kimlik()
    print('  %-24s %-7s %s' % ('model kimligi',
                                'PASS' if model_gecti else 'FAIL', model_ozet))
    for satir in model_detay:
        print('        | %s' % satir[:400])
    if not model_gecti:
        if JSON:
            _json_erken('ONKOSUL.MODEL', 'model kimligi', model_ozet,
                        'model kimligi FAIL')
        print()
        print('  HUKUM: FAIL — MODEL KIMLIK (aktif atif veya bayat istisna)')
        return 1
    print()

    kamu_gecti, kamu_ozet, kamu_detay = kamu_temizligi()
    print('  %-24s %-7s %s' % ('kamu temizligi',
                                'PASS' if kamu_gecti else 'FAIL', kamu_ozet))
    for satir in kamu_detay:
        print('        | %s' % satir[:400])
    if not kamu_gecti:
        if JSON:
            _json_erken('ONKOSUL.KAMU', 'kamu temizligi', kamu_ozet,
                        'kamu temizligi FAIL')
        print()
        print('  HUKUM: FAIL — KAMU TEMIZLIGI (ozel yol/eski alan/sahte hash)')
        return 1
    print()

    yayin_gecti, yayin_ozet, yayin_detay = yayin_kapisi()
    print('  %-24s %-7s %s' % ('yayin kapisi',
                                'PASS' if yayin_gecti else 'FAIL', yayin_ozet))
    for satir in yayin_detay:
        print('        | %s' % satir[:400])
    if not yayin_gecti:
        if JSON:
            _json_erken('ONKOSUL.YAYIN', 'yayin kapisi', yayin_ozet,
                        'yayin kapisi FAIL')
        print()
        print('  HUKUM: FAIL — YAYIN KAPISI (manifest/makale/sir/ozel yol)')
        return 1
    print()

    qs_gecti, qs_ozet, qs_detay = quickstart_kontrolu()
    print('  %-24s %-7s %s' % ('quickstart docs',
                                'PASS' if qs_gecti else 'FAIL', qs_ozet))
    for satir in qs_detay:
        print('        | %s' % satir[:400])
    if not qs_gecti:
        if JSON:
            _json_erken('ONKOSUL.QUICKSTART', 'quickstart docs', qs_ozet,
                        'quickstart docs FAIL')
        print()
        print('  HUKUM: FAIL — QUICKSTART (make hedefi/ornek cikti)')
        return 1
    print()

    kalemler = []
    for kid, ad, fn in (('H1', 'depo hijyeni', hijyen),
                        ('H2', 'python sozdizimi', py_sozdizimi),
                        ('H3', 'kabuk sozdizimi', sh_sozdizimi),
                        ('H4', 'sir taramasi', sir_tarama),
                        ('H5', 'sir kapisi oz-testi', kapi_oztesti)):
        gecti, ozet, detay = fn()
        kalemler.append((kid, ad, True if gecti else False, ozet,
                         detay if not gecti else [], ''))

    for kalem in KOMUTLAR:
        kid, ad = kalem[0], kalem[1]
        if HIZLI:
            kalemler.append((kid, ad, None, '--hizli: agir kapi atlandi', [],
                             'agir kapi atlandi'))
            continue
        cwd = kalem[3] if len(kalem) > 3 else None
        rc, stdout, stderr = kos(kalem[2], cwd)
        cikti = ((stdout or '') + (stderr or '')).strip()
        satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
        son = _ozet_satiri([stdout, stderr], satirlar)
        if kid == 'T1' and rc == 0:
            # T1 PASS'i kendi agac kanitiyla birlikte gorunur olsun.
            son = ('%s · %s' % (son, _kanit_capasi()))[:150]

        if CI and kid in CI_RAPOR:
            # Kural tabanli siniflandirma: gecen PASS, ortam gerekceli kalan
            # CALISTIRILMADI, digerleri FAIL. CI'ya ozel muafiyet YOK.
            if rc == 0:
                kalemler.append((kid, ad, True, son, [], ''))
                continue
            sebep = ortam_bagli_mi(kid, cikti)
            kalan = _kalan_satirlari(stdout, satirlar)
            if sebep:
                kalemler.append((kid, ad, None, son, kalan,
                                 'CALISTIRILMADI: %s' % sebep))
            else:
                kalemler.append((kid, ad, False, son, kalan or satirlar[-6:], ''))
            continue
        if rc == 0:
            kalemler.append((kid, ad, True, son, [], ''))
            continue
        sebep = ortam_bagli_mi(kid, cikti)
        if sebep:
            kalan = [s for s in satirlar if re.match(r'\s*KALDI', s)][:20]
            kalemler.append((kid, ad, None, son, kalan,
                             'CALISTIRILMADI: %s' % sebep))
            continue
        kalan = _kalan_satirlari(stdout, satirlar)
        kalemler.append((kid, ad, False, son, kalan or satirlar[-6:], ''))

    kalan = [k for k in kalemler if k[2] is False]
    atlanan = [k for k in kalemler if k[2] is None]

    # Sürümlü kapı çıktısı: serbest metin özeti yerine kimlikli kontroller.
    kontroller = []
    for kid, ad, durum, ozet, _detay, not_metni in kalemler:
        kdurum = 'OLCULMEDI' if durum is None else ('PASS' if durum else 'FAIL')
        if kid in ('T1', 'T2', 'T3'):
            deger = _oran(ozet)
        elif kid == 'H5':
            deger = (ozet.split(':')[-1].strip().split() or [ozet])[0]
        elif kid in ('H1', 'H2', 'H3', 'H4'):
            deger = _sayi(ozet)
        else:
            deger = ozet
        kontroller.append(_json_kontrol(
            kid, ad, kdurum, deger=deger, ayrinti=not_metni,
            ham='dogrula %s %s %s' % (kid, kdurum, deger or '')))

    gecen = len(kalemler) - len(kalan) - len(atlanan)
    kontroller.append(_json_kontrol(
        'RAPOR', 'dogrula rapor sayaclari',
        'PASS' if not kalan else 'FAIL',
        deger='%d/%d' % (gecen, len(kalemler)),
        ham='dogrula kalem=%d · gecen=%d · kalan=%d · calistirilmadi=%d'
            % (len(kalemler), gecen, len(kalan), len(atlanan))))
    kontroller.append(_json_kontrol(
        'RAPOR_TOPLAM', 'kalem toplami', 'PASS',
        deger=str(len(kalemler)), ham='kalem=%d' % len(kalemler)))
    kontroller.append(_json_kontrol(
        'RAPOR_OZET', 'gecen/toplam', 'PASS' if not kalan else 'FAIL',
        deger='%d/%d' % (gecen, len(kalemler)),
        ham='gecen=%d toplam=%d' % (gecen, len(kalemler))))
    kontroller.append(_json_kontrol(
        'RAPOR_SAYIM', 'gecen/kalan/calistirilmadi',
        'PASS' if not kalan else 'FAIL',
        deger='%d/%d/%d' % (gecen, len(kalan), len(atlanan)),
        ham='gecen=%d kalan=%d calistirilmadi=%d'
            % (gecen, len(kalan), len(atlanan))))
    _json_yaz(kontroller, 0 if not kalan else 1,
              None if not kalan else 'dogrula FAIL')

    for kid, ad, durum, ozet, detay, not_metni in kalemler:
        etiket = 'CALISTIRILMADI' if durum is None else ('PASS' if durum else 'FAIL')
        print('  %-3s %-24s %-7s %s' % (kid, ad, etiket, ozet))
        if not_metni:
            print('        · %s' % not_metni)
        for satir in detay:
            print('        | %s' % satir[:400])

    print()
    print('  kalem=%d · gecen=%d · kalan=%d · calistirilmadi=%d'
          % (len(kalemler), len(kalemler) - len(kalan) - len(atlanan),
             len(kalan), len(atlanan)))
    print('  NOT: bu betik hakem degildir; rc toplar (OZ_DENETIM).')
    for k in atlanan:
        if HIZLI:
            break
        sebep = (k[5] or '').replace('CALISTIRILMADI: ', '')
        print('  KABUL EDILEN BORC: %s kosmuyor — %s' % (k[0], sebep))
    _github_ozeti(kalemler, kalan, atlanan)
    if kalan:
        print('  HUKUM: FAIL — %s' % ', '.join(k[0] for k in kalan))
        return 1
    if atlanan:
        print('  HUKUM: PASS %d/%d — %s CALISTIRILMADI, PASS sayilmadi'
              % (len(kalemler) - len(atlanan), len(kalemler),
                 ', '.join(k[0] for k in atlanan)))
        return 0
    print('  HUKUM: PASS — %d/%d kalem gecti' % (len(kalemler), len(kalemler)))
    return 0


if __name__ == '__main__':
    if JSON:
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main()
        if JSON_RAPOR is None:
            JSON_RAPOR = kapi_cikti.uret(
                'dogrula', [], rc=rc, hukum='FAIL',
                hata='dogrula JSON raporu uretemedi')
        sys.stdout.write(kapi_cikti.yaz(JSON_RAPOR))
        sys.exit(rc)
    sys.exit(main())
