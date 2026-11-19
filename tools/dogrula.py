#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dogrula.py — bu deponun TEK GIRIS dogrulamasi (fail-closed).

NEDEN VAR: "bitti" diyen sey bir his olmamali. Kalemler sirayla kosar, her
kalemin ham ciktisinin son satiri basilir ve hukum rc'lerin toplamindan cikar.
Bir kalem FAIL verdiginde de kalanlar kosar ki tek turda tam manzara gorunsun.

Iki kip vardir:

  (varsayilan)        Tam kapi. Laboratuvarin kendi ortaminda (macOS + yerel
                      opencode model katalogu) her sey kosar.
  --ci                Runner kipi. Yalnizca bu ortamda OLCULEBILEN kalemler
                      hukme girer: hijyen, sozdizimi, sir taramasi, Toolkit.
                      ATLAS ve KOD paketleri kosar ama RAPOR olarak basilir —
                      cunku ikisi de yerel modele/tarihceye baglidir ve baska
                      bir makinede ayni sayiyi uretmez. Gizlenmez, basilir.

ORTAK BAGLI KALEM: ATLAS'taki OLG-1, SURUM.md makine blogunun bagli oldugu
commit ve kanit setini arar; bu depo ozel agacin tarihcesini tasimaz. Test bu
yuzden KOSULLU raporlanir — PASS degil.

CIKIS: 0 = hepsi gecti veya kosullu · 1 = en az bir kalem FAIL · 2 = kosulamadi
"""
import os
import re
import subprocess
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIZLI = '--hizli' in sys.argv
CI = '--ci' in sys.argv

ATLA_DIZIN = {'.git', '__pycache__', 'node_modules', '.pytest_cache',
              '.ruff_cache', '.venv', '.venv-token'}
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
# Kendi sir tarayicisinin test fiksturleri: deger uydurma, bicim gercek.
FIKSTUR = ('AKIAXXX', 'AKIA1234567890')
# Gercek PEM anahtarinin basligin ALTINDA uzun base64 govdesi vardir. Ornek
# komutlarda gecen `-----BEGIN ... KEY-----\\nMII...` bu desene uymaz; ham grep
# saymak yerine gercek bicimi ariyoruz.
ANAHTAR = re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----\r?\n[A-Za-z0-9+/=]{64,}')

# kid -> (izinli kimlikler, ciktida aranan ek kanit, gerekce)
ORTAM_BAGLI = {
    'T1': ({'OLG-1', 'MOD-1', 'MOD-2'}, 'OLGU-04',
           'SURUM.md makine blogu ozel agacin HEAD/kanit setine bagli (OLGU-04)'),
    'T2': ({'MOD-1', 'MOD-2'}, 'check_models',
           'yerel opencode model katalogu yok'),
}

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


def sir_tarama():
    kotu = []
    for tam in gez():
        if os.path.getsize(tam) > 2 * 1024 * 1024:
            continue
        try:
            with open(tam, encoding='utf-8') as f:
                metin = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        for no, satir in enumerate(metin.splitlines(), 1):
            if any(f in satir for f in FIKSTUR):
                continue
            for ad, kalip in SIR_KALIPLARI:
                if kalip.search(satir):
                    kotu.append('%s:%d (%s)' % (os.path.relpath(tam, KOK), no, ad))
        for m in ANAHTAR.finditer(metin):
            kotu.append('%s:%d (private-key)'
                        % (os.path.relpath(tam, KOK),
                           metin[:m.start()].count('\n') + 1))
    return not kotu, '%d bulgu' % len(kotu), kotu


KOMUTLAR = [
    ('T1', 'ATLAS oz-testi',
     [sys.executable, 'ATLAS_SABLONLAR/scripts/atlas_selftest.py', '--sessiz']),
    ('T2', 'KOD oz-testi',
     [sys.executable, 'KOD_SABLONLAR/scripts/kod_selftest.py']),
    ('T3', 'Toolkit oz-testi', [sys.executable, 'v4_selftest.py'],
     os.path.join(KOK, 'KOMUT_TOOLKIT_v4', 'ARACLAR', 'betikler')),
]


def kos(komut, cwd=None):
    try:
        r = subprocess.run(komut, cwd=cwd or KOK, capture_output=True,
                           text=True, timeout=900)
        return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()
    except subprocess.TimeoutExpired:
        return 124, 'ZAMAN ASIMI (900 s)'
    except OSError as e:
        return 125, 'KOSULAMADI: %s' % e


def kimlikler(cikti):
    kimlik = set()
    for satir in cikti.splitlines():
        m = re.match(r'\s*KALDI\s+([A-Za-z0-9_.-]+):', satir)
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
    kalan = kimlikler(cikti)
    if not kalan or not kalan <= izinli:
        return None
    if ek_kanit not in cikti:
        return None
    return gerekce


def main():
    kip = 'CI' if CI else ('HIZLI' if HIZLI else 'TAM')
    print('ATLAS — tek giris dogrulama · %s' % kip)
    print('kok: %s' % KOK)
    print()

    kalemler = []
    for kid, ad, fn in (('H1', 'depo hijyeni', hijyen),
                        ('H2', 'python sozdizimi', py_sozdizimi),
                        ('H3', 'kabuk sozdizimi', sh_sozdizimi),
                        ('H4', 'sir taramasi', sir_tarama)):
        gecti, ozet, detay = fn()
        kalemler.append((kid, ad, True if gecti else False, ozet,
                         detay if not gecti else [], ''))

    rapor = []
    for kalem in KOMUTLAR:
        kid, ad = kalem[0], kalem[1]
        if HIZLI:
            kalemler.append((kid, ad, None, '--hizli: agir kapi atlandi', [],
                             'agir kapi atlandi'))
            continue
        cwd = kalem[3] if len(kalem) > 3 else None
        rc, cikti = kos(kalem[2], cwd)
        satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
        son = satirlar[-1][:110] if satirlar else '(bos cikti)'

        if CI and kid in CI_RAPOR:
            rapor.append((kid, ad, rc, son))
            continue
        if rc == 0:
            kalemler.append((kid, ad, True, son, [], ''))
            continue
        sebep = ortam_bagli_mi(kid, cikti)
        if sebep:
            kalan = [s for s in satirlar if re.match(r'\s*KALDI', s)][:20]
            kalemler.append((kid, ad, None, son, kalan,
                             'ortam bagli: %s' % sebep))
            continue
        kalan = [s for s in satirlar if re.match(r'\s*KALDI', s)][:20]
        kalemler.append((kid, ad, False, son, kalan or satirlar[-6:], ''))

    for kid, ad, durum, ozet, detay, not_metni in kalemler:
        etiket = 'ATLANDI' if durum is None else ('PASS' if durum else 'FAIL')
        print('  %-3s %-24s %-7s %s' % (kid, ad, etiket, ozet))
        if not_metni:
            print('        · %s' % not_metni)
        for satir in detay:
            print('        | %s' % satir[:400])

    if rapor:
        print()
        print('  --- RAPOR (hukme GIRMEZ: bu ortamda uretilen sayi tasinabilir '
              'degil) ---')
        for kid, ad, rc, son in rapor:
            print('  %-3s %-24s %-7s %s'
                  % (kid, ad, 'rc=0' if rc == 0 else 'rc=%d' % rc, son))

    kalan = [k for k in kalemler if k[2] is False]
    atlanan = [k for k in kalemler if k[2] is None]
    print()
    print('  kalem=%d · gecen=%d · kalan=%d · kosullu=%d · rapor=%d'
          % (len(kalemler), len(kalemler) - len(kalan) - len(atlanan),
             len(kalan), len(atlanan), len(rapor)))
    print('  NOT: bu betik hakem degildir; rc toplar (OZ_DENETIM).')
    if kalan:
        print('  HUKUM: FAIL — %s' % ', '.join(k[0] for k in kalan))
        return 1
    if atlanan:
        print('  HUKUM: KOSULLU — %s kosullu (gerekce yukarida); PASS degildir'
              % ', '.join(k[0] for k in atlanan))
        return 0
    print('  HUKUM: PASS — %d/%d kalem gecti' % (len(kalemler), len(kalemler)))
    if rapor:
        print('  Tam oz-testler icin (yerel ortam): make dogrula')
    return 0


if __name__ == '__main__':
    sys.exit(main())
