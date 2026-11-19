#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sir_kapisi — canli kimlik bilgisi tasiyan DSN'i commit/push etmeden durdurur.

KURALLAR
  R1 canli-dsn   : postgres(ql)://<kullanici>:<parola>@<host>
  R2 neon-token  : npg_<8+ karakter>

YER TUTUCULAR GECER (engellenmez):
  NEON_KULLANICI:NEON_PAROLA · KULLANICI:PAROLA · USER:PASSWORD
  <kullanici>:<parola> · ${DB_USER}:${DB_PASS}

KULLANIM
  python3 scripts/sir_kapisi.py --staged          # indeksteki degisiklikler (pre-commit)
  python3 scripts/sir_kapisi.py --tum             # calisma agaci (CI)
  python3 scripts/sir_kapisi.py --dosyalar a b    # verilen dosyalar
  python3 scripts/sir_kapisi.py --aralik A..B     # commit araligi (pre-push)

CIKIS: 0 temiz · 1 bulgu · 2 kullanim hatasi
SIR DEGERI BASILMAZ: yalniz dosya, satir ve kural adi yazilir.
"""
import os
import re
import subprocess
import sys

PAT_DSN = re.compile(r'postgres(?:ql)?://([^\s:/@]+):([^\s@]+)@')
PAT_NPG = re.compile(r'npg_[A-Za-z0-9]{8,}')

KULLANICI_YER = {'NEON_KULLANICI', 'KULLANICI', 'USER', 'USERNAME',
                 'DB_USER', 'DB_KULLANICI', 'ROL'}
PAROLA_YER = {'NEON_PAROLA', 'PAROLA', 'PASSWORD', 'SIFRE', '***', '...',
              'CHANGEME', 'DEGISTIR', 'PLACEHOLDER'}

ATLA_DIZIN = {'.git', '__pycache__', 'node_modules', '.pytest_cache',
              '.ruff_cache', '.venv', '.venv-token'}
ATLA_UZANTI = {'.pyc', '.pyo', '.png', '.jpg', '.jpeg', '.gif', '.pdf',
               '.zip', '.bundle', '.woff', '.woff2', '.ttf'}


def _sarili(x):
    """<...>, ${...}, $(...), $VAR bicimleri yer tutucudur."""
    return x[:1] == '<' or x[:2] in ('${', '$(') or x[:1] == '$'


def yer_tutucu(kullanici, parola):
    if _sarili(kullanici) or _sarili(parola):
        return True
    return (kullanici.upper() in KULLANICI_YER
            and parola.upper() in PAROLA_YER)


def tara(metin, etiket):
    """(etiket, satir, kural) listesi. Metin asla basilmaz."""
    bulgular = []
    for no, satir in enumerate(metin.splitlines(), 1):
        for k, p in PAT_DSN.findall(satir):
            if not yer_tutucu(k, p):
                bulgular.append((etiket, no, 'canli-dsn'))
        if PAT_NPG.search(satir):
            bulgular.append((etiket, no, 'neon-token'))
    return bulgular


def _git(*args):
    return subprocess.run(['git'] + list(args), capture_output=True, text=True)


def gez():
    for dirpath, dizinler, dosyalar in os.walk('.'):
        dizinler[:] = [d for d in dizinler if d not in ATLA_DIZIN]
        for ad in dosyalar:
            if os.path.splitext(ad)[1] in ATLA_UZANTI:
                continue
            yield os.path.relpath(os.path.join(dirpath, ad), '.')


def oku(yol):
    try:
        with open(yol, 'rb') as f:
            return f.read().decode('utf-8')
    except (OSError, UnicodeDecodeError):
        return None


def tarama_staged():
    r = _git('diff', '--cached', '--name-only', '--diff-filter=ACM')
    bulgular = []
    for yol in r.stdout.splitlines():
        icerik = None
        g = subprocess.run(['git', 'show', ':%s' % yol], capture_output=True)
        if g.returncode == 0:
            try:
                icerik = g.stdout.decode('utf-8')
            except UnicodeDecodeError:
                icerik = None
        if icerik:
            bulgular += tara(icerik, yol)
    return bulgular


def tarama_tum():
    bulgular = []
    for yol in gez():
        metin = oku(yol)
        if metin:
            bulgular += tara(metin, yol)
    return bulgular


def tarama_dosyalar(yollar):
    bulgular = []
    for yol in yollar:
        metin = oku(yol)
        if metin:
            bulgular += tara(metin, yol)
    return bulgular


def tarama_aralik(aralik):
    """Commit araligindaki her commit icin icerik git'ten okunur, basilmaz."""
    r = _git('rev-list', aralik)
    if r.returncode != 0:
        print('HATA: gecersiz aralik: %s' % aralik)
        return None
    bulgular = []
    for sha in r.stdout.split():
        g = subprocess.run(
            ['git', 'grep', '-n', '-E',
             r'postgres(ql)?://[^[:space:]]+@|npg_[A-Za-z0-9]{8,}', sha],
            capture_output=True, text=True)
        if g.returncode != 0:
            continue
        for satir in g.stdout.splitlines():
            parcalar = satir.split(':', 2)
            if len(parcalar) < 3:
                continue
            _, no, icerik = parcalar
            for k, p in PAT_DSN.findall(icerik):
                if not yer_tutucu(k, p):
                    bulgular.append(('%s:%s' % (sha[:8], _),
                                     int(no) if no.isdigit() else 0, 'canli-dsn'))
            if PAT_NPG.search(icerik):
                bulgular.append(('%s:%s' % (sha[:8], _),
                                 int(no) if no.isdigit() else 0, 'neon-token'))
    return bulgular


def main(argv):
    if '--staged' in argv:
        bulgular = tarama_staged()
    elif '--tum' in argv:
        bulgular = tarama_tum()
    elif '--dosyalar' in argv:
        yol = argv[argv.index('--dosyalar') + 1:]
        if not yol:
            print('HATA: --dosyalar en az bir yol ister')
            return 2
        bulgular = tarama_dosyalar(yol)
    elif '--aralik' in argv:
        i = argv.index('--aralik')
        if i + 1 >= len(argv):
            print('HATA: --aralik <A..B> ister')
            return 2
        bulgular = tarama_aralik(argv[i + 1])
        if bulgular is None:
            return 2
        if not bulgular:
            print('SIR-KAPISI: aralik temiz (%s)' % argv[i + 1])
            return 0
        dosyalar = {}
        for etiket, _no, kural in bulgular:
            dosyalar.setdefault(etiket, set()).add(kural)
        for etiket in sorted(dosyalar):
            print('BULGU %s · %s' % (etiket, ','.join(sorted(dosyalar[etiket]))))
        print('SIR-KAPISI FAIL — %d eslesme · %d commit-dosya'
              % (len(bulgular), len(dosyalar)))
        return 1
    else:
        print('kullanim: --staged | --tum | --dosyalar <yollar> | --aralik <A..B>')
        return 2

    if not bulgular:
        print('SIR-KAPISI PASS — canli DSN/Neon token yok')
        return 0
    for etiket, no, kural in bulgular:
        print('FAIL %s:%d · %s' % (etiket, no, kural))
    print('SIR-KAPISI FAIL — %d bulgu · deger BASILMADI' % len(bulgular))
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
