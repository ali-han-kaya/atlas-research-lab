#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""taze_klon — public agacin temiz bir klonda sifirdan kurulabildigini olcer.

NEDEN VAR
  Bir depo kendi gelistirme agacinda yesil olabilir; gizli bir dosya, yerel
  .venv, parent dizindeki bir modul veya izlenmeyen bir fikstur olmadan ayni
  komutlarin calisip calismadigini yalnizca temiz bir klon gosterir.

NE YAPAR
  1. Git deposunun commit'lenmis HEAD'inden gecici bir klon uretir.
  2. Klonun temiz oldugunu (untracked dahil) ve .venv tasimadigini denetler.
  3. Kendi .venv'ini kurup requirements-dev.txt'i kurar.
  4. `make demo` -> beklenen rc=2 ve BEKLENEN KIRMIZI.
  5. `make dogrula` -> rc=0 ve 8/8 PASS.
  6. `make mutasyon-kisa` -> rc=0 ve KISA SET PASS.
  7. Klonun izlenen agacinda degisiklik kalmadigini denetler.

NE OLCMEZ
  Uzak sunucudaki public URL'nin erisilebilirligini olcmez; varsayilan kaynak
  bu depodur. `--kaynak <git-url>` ile uzak depo da verilebilir. Tam mutasyon
  bataryasi bu kontrolun yerine gecmez; `--kisa` setinin disinda kalan 117
  vaka icin `make mutasyon` ayrica kosulmalidir.

KULLANIM
  python3 tools/taze_klon.py [--kaynak YOL_VEYA_URL] [--tut]

CIKIS
  0 : klon kuruldu, uc komut da beklenen sozlesmeyi verdi
  1 : klon, kurulum veya komut sozlesmesi basarisiz (fail-closed)
"""

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KISA_BEKLEYEN = 'KISA SET:'


class Hata(Exception):
    pass


def yaz_komut(cmd, cwd):
    print('\n$ (cd %s && %s)' % (shlex.quote(str(cwd)),
                                 ' '.join(shlex.quote(str(x)) for x in cmd)))


def kos(cmd, cwd, env=None, timeout=900):
    yaz_komut(cmd, cwd)
    try:
        p = subprocess.run(
            [str(x) for x in cmd], cwd=str(cwd), env=env,
            capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise Hata('komut bulunamadi: %s' % e)
    except subprocess.TimeoutExpired:
        raise Hata('komut zaman asimina ugradi: %s' % ' '.join(map(str, cmd)))
    if p.stdout:
        print(p.stdout.rstrip())
    if p.stderr:
        print(p.stderr.rstrip())
    return p


def git_kos(cwd, *args, **kwargs):
    p = kos(['git'] + list(args), cwd, **kwargs)
    if p.returncode != 0:
        raise Hata('git %s rc=%d' % (' '.join(args), p.returncode))
    return p.stdout.strip()


def kaynak_dogrula(kaynak, yerel):
    if not yerel:
        return
    if not kaynak.is_dir():
        raise Hata('kaynak dizin yok: %s' % kaynak)
    for ad in ('Makefile', 'demo', 'requirements-dev.txt'):
        if not (kaynak / ad).is_file():
            raise Hata('kaynakta zorunlu dosya yok: %s' % ad)
    kirli = git_kos(kaynak, 'status', '--porcelain', '--untracked-files=all')
    if kirli:
        raise Hata('kaynak agac kirli; taze klondan once commit/temizle:\n%s'
                   % kirli)


def klonla(kaynak, hedef, yerel):
    cmd = ['git', 'clone', '--quiet']
    if yerel:
        # Yerel kopyada hardlink/parent .git sizmasini engelle; commit'lenmis
        # agac disinda hicbir sey klona girmez.
        cmd.append('--no-local')
    cmd += [str(kaynak), str(hedef)]
    p = kos(cmd, KOK)
    if p.returncode != 0:
        raise Hata('git clone rc=%d' % p.returncode)
    kirli = git_kos(hedef, 'status', '--porcelain', '--untracked-files=all')
    if kirli:
        raise Hata('yeni klon temiz degil:\n%s' % kirli)
    if (hedef / '.venv').exists():
        raise Hata('klonda kaynak .venv tasinmis')
    return git_kos(hedef, 'rev-parse', 'HEAD')


def venv_kur(klon, python3):
    venv = klon / '.venv'
    p = kos([python3, '-m', 'venv', str(venv)], klon, timeout=180)
    if p.returncode != 0:
        raise Hata('venv kurulumu rc=%d' % p.returncode)
    py = venv / 'bin' / 'python'
    if not py.is_file():
        raise Hata('venv python yok: %s' % py)
    p = kos([str(py), '-m', 'pip', 'install', '--quiet',
             '--disable-pip-version-check', '-r',
             str(klon / 'requirements-dev.txt')], klon, timeout=900)
    if p.returncode != 0:
        raise Hata('requirements-dev.txt kurulumu rc=%d' % p.returncode)
    return venv, py


def ortam(venv, py):
    env = os.environ.copy()
    for ad in ('PYTHONPATH', 'PYTHONHOME', 'PY', 'VIRTUAL_ENV',
               'ATLAS_LAB', 'ATLAS_MODEL_KATALOG'):
        env.pop(ad, None)
    env['PATH'] = str(venv / 'bin') + os.pathsep + env.get('PATH', '/usr/bin:/bin')
    env['VIRTUAL_ENV'] = str(venv)
    env['PY'] = str(py)
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    return env


def sozlesme_demo(p):
    if p.returncode != 2:
        raise Hata('make demo rc=%d; beklenen 2 (make tarif hatasi)' % p.returncode)
    metin = (p.stdout or '') + (p.stderr or '')
    if 'BEKLENEN KIRMIZI' not in metin:
        raise Hata('make demo BEKLENEN KIRMIZI basmadi')
    if 'FIKSTUR DEGISTI' in metin:
        raise Hata('make demo fikstur kaymasini bildirdi')
    if 'HUKUM: FAIL' not in metin:
        raise Hata('make demo FAIL hukmu basmadi')


def sozlesme_dogrula(p):
    if p.returncode != 0:
        raise Hata('make dogrula rc=%d' % p.returncode)
    metin = (p.stdout or '') + (p.stderr or '')
    if 'HUKUM: PASS' not in metin or '8/8' not in metin:
        raise Hata('make dogrula 8/8 PASS hukmunu basmadi')


def sozlesme_kisa(p):
    if p.returncode != 0:
        raise Hata('make mutasyon-kisa rc=%d' % p.returncode)
    metin = (p.stdout or '') + (p.stderr or '')
    if KISA_BEKLEYEN not in metin or 'HUKUM: PASS' not in metin:
        raise Hata('make mutasyon-kisa KISA SET PASS hukmunu basmadi')


def calistir(kaynak_arg, tut):
    kaynak_ham = Path(kaynak_arg).expanduser()
    yerel = kaynak_ham.exists()
    kaynak = kaynak_ham.resolve() if yerel else kaynak_arg
    if yerel:
        kaynak_dogrula(kaynak, True)
    python3 = shutil.which('python3') or sys.executable
    make = shutil.which('make')
    if not make:
        raise Hata('make bulunamadi')

    tmp = Path(tempfile.mkdtemp(prefix='atlas_taze_klon_'))
    klon = tmp / 'repo'
    basarili = False
    try:
        print('TAZE KLON — commit edilmis agactan sifirdan kurulum')
        print('kaynak: %s' % kaynak)
        head = klonla(kaynak, klon, yerel)
        print('klon HEAD: %s' % head)
        venv, py = venv_kur(klon, python3)
        print('venv: %s' % venv)
        env = ortam(venv, py)
        sozlesme_demo(kos([make, 'demo'], klon, env=env, timeout=180))
        sozlesme_dogrula(kos([make, 'dogrula'], klon, env=env, timeout=900))
        sozlesme_kisa(kos([make, 'mutasyon-kisa'], klon, env=env, timeout=300))

        kirli = git_kos(klon, 'status', '--porcelain', '--untracked-files=all')
        if kirli:
            raise Hata('komutlardan sonra klon izlenen agaci kirli:\n%s' % kirli)
        basarili = True
        print('\nHUKUM: PASS — taze klon; demo rc=2, dogrula 8/8, kisa set PASS')
        return 0
    finally:
        if basarili and not tut:
            shutil.rmtree(tmp, ignore_errors=True)
        elif not basarili:
            print('\nKLON KORUNDU (inceleme icin): %s' % tmp)


def main(argv=None):
    p = argparse.ArgumentParser(description='Temiz klonda sifirdan kurulum kontrolu')
    p.add_argument('--kaynak', default=str(KOK),
                   help='klonlanacak git yolu veya URL (varsayilan: bu depo)')
    p.add_argument('--tut', action='store_true',
                   help='basarili kosuda da gecici klonu silme')
    a = p.parse_args(argv)
    try:
        return calistir(a.kaynak, a.tut)
    except Hata as e:
        print('\nHUKUM: FAIL — %s' % e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
