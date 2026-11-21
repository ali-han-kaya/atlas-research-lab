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
CALISTIRILMADI yalniz gercekten olculemeyen kalemler icin (or. --hizli veya
model katalogu yoklugu) basilir ve hukme SAYILMAZ; her satir nedenini tasir.

PARITE (OPSIYONEL): `ATLAS_LAB` tanimliysa once `tools/yayinla.py` kuru kosusu
calisir; sifir suruklenme yoksa hukum FAIL olur. Tanimsizsa bu kontrol
atlanir, cunku public klonda ozel agac yoktur; 8/8 hukmu degismez.

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
import hashlib
import json
import os
import re
import subprocess
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIZLI = '--hizli' in sys.argv
CI = '--ci' in sys.argv

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
    rc, cikti = kos([sys.executable,
                     os.path.join(KOK, 'tools', 'sir_kapisi_selftest.py')])
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    son = satirlar[-1][:110] if satirlar else '(bos cikti)'
    return rc == 0, son, ([] if rc == 0 else satirlar[-6:])


def demo_oztesti():
    """demo'nun 0/2 sozlesmesini gecici fiksturlerle on kontrol olarak kosar.

    Sayilan sekiz kaleme dahil degildir; parite gibi bir on kosuldur. Yine de
    basarisizsa dogrula yesil donmez.
    """
    rc, cikti = kos([sys.executable,
                     os.path.join(KOK, 'tools', 'demo_selftest.py')])
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    son = satirlar[-1][:110] if satirlar else '(bos cikti)'
    return rc == 0, son, ([] if rc == 0 else satirlar[-8:])


def model_kimlik():
    """Emekli model kimligi taramasini on kosul olarak kosar.

    Sayilan sekiz kaleme dahil degildir; demo gibi bir on kosuldur. Aktif bir
    atif veya bayat istisna varsa dogrula yesil donmez.
    """
    rc, cikti = kos([sys.executable,
                     os.path.join(KOK, 'tools', 'model_kimlik.py'),
                     '--kontrol'])
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    baslik = [s for s in satirlar if s.startswith('MODEL KIMLIK')]
    son = (baslik[0] if baslik else (satirlar[-1] if satirlar else '(bos cikti)'))
    return rc == 0, son[:150], ([] if rc == 0 else satirlar[-8:])


KOMUTLAR = [
    ('T1', 'ATLAS oz-testi',
     [sys.executable, 'ATLAS_SABLONLAR/scripts/atlas_selftest.py', '--sessiz']),
    ('T2', 'KOD oz-testi',
     [sys.executable, 'KOD_SABLONLAR/scripts/kod_selftest.py']),
    ('T3', 'Toolkit oz-testi', [sys.executable, 'v4_selftest.py'],
     os.path.join(KOK, 'KOMUT_TOOLKIT_v4', 'ARACLAR', 'betikler')),
]


def kos(komut, cwd=None):
    env = dict(os.environ)
    if not env.get('ATLAS_MODEL_KATALOG'):
        env['ATLAS_MODEL_KATALOG'] = (KATALOG_SABIT
                                      if os.path.isfile(KATALOG_SABIT)
                                      else KATALOG_YOK)
    try:
        r = subprocess.run(komut, cwd=cwd or KOK, capture_output=True,
                           text=True, env=env, timeout=900)
        return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()
    except subprocess.TimeoutExpired:
        return 124, 'ZAMAN ASIMI (900 s)'
    except OSError as e:
        return 125, 'KOSULAMADI: %s' % e


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


def _ozet_satiri(satirlar):
    """Aracin kendi huküm satirini secer; stderr uyarisini PASS kaniti diye basmaz."""
    for satir in reversed(satirlar):
        if re.search(r'\d+/\d+ gecti', satir):
            return satir[:110]
    return satirlar[-1][:110] if satirlar else '(bos cikti)'


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
            print()
            print('  HUKUM: FAIL — PARITE (yayinla kuru kosusu)')
            return 1
        print()

    demo_gecti, demo_ozet, demo_detay = demo_oztesti()
    print('  %-24s %-7s %s' % ('demo 0/2 oz-testi',
                                'PASS' if demo_gecti else 'FAIL', demo_ozet))
    for satir in demo_detay:
        print('        | %s' % satir[:400])
    if not demo_gecti:
        print()
        print('  HUKUM: FAIL — DEMO 0/2 OZ-TESTI')
        return 1
    print()

    model_gecti, model_ozet, model_detay = model_kimlik()
    print('  %-24s %-7s %s' % ('model kimligi',
                                'PASS' if model_gecti else 'FAIL', model_ozet))
    for satir in model_detay:
        print('        | %s' % satir[:400])
    if not model_gecti:
        print()
        print('  HUKUM: FAIL — MODEL KIMLIK (aktif atif veya bayat istisna)')
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
        rc, cikti = kos(kalem[2], cwd)
        satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
        son = _ozet_satiri(satirlar)
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
            kalan = [s for s in satirlar if re.match(r'\s*KALDI', s)][:20]
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
        kalan = [s for s in satirlar if re.match(r'\s*KALDI', s)][:20]
        kalemler.append((kid, ad, False, son, kalan or satirlar[-6:], ''))

    for kid, ad, durum, ozet, detay, not_metni in kalemler:
        etiket = 'CALISTIRILMADI' if durum is None else ('PASS' if durum else 'FAIL')
        print('  %-3s %-24s %-7s %s' % (kid, ad, etiket, ozet))
        if not_metni:
            print('        · %s' % not_metni)
        for satir in detay:
            print('        | %s' % satir[:400])

    kalan = [k for k in kalemler if k[2] is False]
    atlanan = [k for k in kalemler if k[2] is None]
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
    sys.exit(main())
