#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""taze_klon — public agacin temiz bir klonda sifirdan kurulabildigini olcer.

NEDEN VAR
  Bir depo kendi gelistirme agacinda yesil olabilir; gizli bir dosya, yerel
  .venv, parent dizindeki bir modul veya izlenmeyen bir fikstur olmadan ayni
  komutlarin calisip calismadigini yalnizca temiz bir klon gosterir.

NE YAPAR
  1. Git deposunun commit'lenmis HEAD'ini gecici bir klona sabitler.
  2. Klonun temiz oldugunu (untracked dahil) ve .venv tasimadigini denetler.
  3. Kendi .venv'ini kurup requirements-dev.txt'i kurar.
  4. `make dogrula` -> rc=0 ve 8/8 PASS.
  5. `make kanit-dogrula` -> rc=0 ve KANIT: TEMIZ.
  6. `make demo` -> beklenen rc=2 ve BEKLENEN KIRMIZI.
  7. `make iddia` -> agsiz tam iddia defteri rc=0 ve HUKUM: PASS.
  8. Klonun izlenen dosyalarinin eksiksiz ve agacin temiz kaldigini denetler.

NE OLCMEZ
  Uzak sunucudaki public URL'nin erisilebilirligini olcmez; varsayilan kaynak
  bu depodur. `--kaynak <git-url>` ile uzak depo da verilebilir. Komutlarin
  sadece semayi/sozlesmeyi tutmasi olculur; akademik icerik dogrulugu bu
  kabul testinin kapsaminda degildir.

KULLANIM
  python3 tools/taze_klon.py [--kaynak YOL_VEYA_URL] [--tut]

CIKIS
  0 : klon kuruldu, dort komut da beklenen sozlesmeyi verdi ve agac temiz
  1 : klon, kurulum, eksik dosya, kirli agac veya komut sozlesmesi basarisiz
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
    """Yerel kaynagin temiz oldugunu denetle ve tam HEAD'i dondur."""
    if not yerel:
        return None
    if not kaynak.is_dir():
        raise Hata('kaynak dizin yok: %s' % kaynak)
    for ad in ('Makefile', 'demo', 'requirements-dev.txt'):
        if not (kaynak / ad).is_file():
            raise Hata('kaynakta zorunlu dosya yok: %s' % ad)
    kirli = git_kos(kaynak, 'status', '--porcelain', '--untracked-files=all')
    if kirli:
        raise Hata('kaynak agac kirli; taze klondan once commit/temizle:\n%s'
                   % kirli)
    return git_kos(kaynak, 'rev-parse', 'HEAD').strip()


def agac_yollari(klon):
    """HEAD agacindaki butun yollari NUL-guvenli bicimde dondur."""
    try:
        p = subprocess.run(
            ['git', '-C', str(klon), 'ls-tree', '-r', '-z', '--name-only',
             'HEAD'], capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Hata('git ls-tree kosulamadi: %s' % type(e).__name__)
    if p.returncode != 0:
        raise Hata('git ls-tree rc=%d' % p.returncode)
    yollar = []
    for ham in p.stdout.split(b'\0'):
        if not ham:
            continue
        try:
            yollar.append(ham.decode('utf-8'))
        except UnicodeDecodeError as e:
            raise Hata('agac yolu UTF-8 degil: %s' % e)
    return sorted(yollar)


def eksik_dosyalar(klon):
    """HEAD'de olup calisma agacinda bulunmayan izlenen yollari dondur."""
    return [yol for yol in agac_yollari(klon)
            if not os.path.lexists(str(klon / yol))]


def _commit_var(klon, sha):
    try:
        p = subprocess.run(
            ['git', '-C', str(klon), 'cat-file', '-e', sha + '^{commit}'],
            capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Hata('git cat-file kosulamadi: %s' % type(e).__name__)
    return p.returncode == 0


def klonla(kaynak, hedef, yerel, beklenen_head=None):
    cmd = ['git', 'clone', '--quiet']
    if yerel:
        # Yerel kopyada hardlink/parent .git sizmasini engelle; commit'lenmis
        # agac disinda hicbir sey klona girmez.
        cmd.append('--no-local')
    cmd += [str(kaynak), str(hedef)]
    p = kos(cmd, KOK)
    if p.returncode != 0:
        raise Hata('git clone rc=%d' % p.returncode)
    if beklenen_head:
        # Klonun varsayilan dali degil, kaynagin o anki HEAD'i olculur.
        # Detached HEAD bir ref'e bagli olmayabilir; nesneyi acikca getir.
        if not _commit_var(hedef, beklenen_head):
            git_kos(hedef, 'fetch', '--quiet', str(kaynak), beklenen_head)
        git_kos(hedef, 'checkout', '--quiet', '--detach', beklenen_head)
    head = git_kos(hedef, 'rev-parse', 'HEAD').strip()
    if beklenen_head and head != beklenen_head:
        raise Hata('klon HEAD uyusmuyor: beklenen=%s bulunan=%s'
                   % (beklenen_head, head))
    kirli = git_kos(hedef, 'status', '--porcelain', '--untracked-files=all')
    if kirli:
        raise Hata('yeni klon temiz degil:\n%s' % kirli)
    if (hedef / '.venv').exists():
        raise Hata('klonda kaynak .venv tasinmis')
    eksik = eksik_dosyalar(hedef)
    if eksik:
        raise Hata('yeni klonda eksik izlenen dosya: %s'
                   % ', '.join(eksik[:5]))
    return head


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


def sozlesme_kanit(p):
    if p.returncode != 0:
        raise Hata('make kanit-dogrula rc=%d' % p.returncode)
    metin = (p.stdout or '') + (p.stderr or '')
    if 'KANIT: TEMIZ' not in metin:
        raise Hata('make kanit-dogrula KANIT: TEMIZ hukmunu basmadi')


def sozlesme_iddia(p):
    if p.returncode != 0:
        raise Hata('make iddia rc=%d' % p.returncode)
    metin = (p.stdout or '') + (p.stderr or '')
    if 'HUKUM: PASS' not in metin:
        raise Hata('make iddia HUKUM: PASS hukmunu basmadi')
    if 'HUKUM: HIZLI' in metin:
        raise Hata('make iddia hizli kipte kaldi; agsiz tam kosu bekleniyor')


def agac_kontrol(klon, asama):
    """Eksik izlenen dosya ve standart (ignore disi) kirli agaci fail-closed ele."""
    eksik = eksik_dosyalar(klon)
    if eksik:
        raise Hata('%s: eksik izlenen dosya: %s'
                   % (asama, ', '.join(eksik[:5])))
    kirli = git_kos(klon, 'status', '--porcelain', '--untracked-files=all')
    if kirli:
        raise Hata('%s: klon izlenen agaci kirli:\n%s' % (asama, kirli))


def calistir(kaynak_arg, tut):
    kaynak_ham = Path(kaynak_arg).expanduser()
    yerel = kaynak_ham.exists()
    kaynak = kaynak_ham.resolve() if yerel else kaynak_arg
    kaynak_head = kaynak_dogrula(kaynak, True) if yerel else None
    python3 = shutil.which('python3') or sys.executable
    make = shutil.which('make')
    if not make:
        raise Hata('make bulunamadi')

    tmp = Path(tempfile.mkdtemp(prefix='atlas_taze_klon_'))
    klon = tmp / 'repo'
    basarili = False
    try:
        print('TAZE KLON — commit edilmis HEAD\'ten kabul testi')
        print('kaynak: %s' % kaynak)
        head = klonla(kaynak, klon, yerel, kaynak_head)
        print('klon HEAD: %s' % head)
        agac_kontrol(klon, 'klon sonrasi')
        venv, py = venv_kur(klon, python3)
        print('venv: %s' % venv)
        env = ortam(venv, py)
        sozlesme_dogrula(kos([make, 'dogrula'], klon, env=env, timeout=900))
        sozlesme_kanit(kos([make, 'kanit-dogrula'], klon, env=env, timeout=180))
        sozlesme_demo(kos([make, 'demo'], klon, env=env, timeout=180))
        sozlesme_iddia(kos([make, 'iddia'], klon, env=env, timeout=1800))
        agac_kontrol(klon, 'komutlardan sonra')
        basarili = True
        print('\nHUKUM: PASS — taze klon; dogrula 8/8, kanit temiz, demo rc=2, '
              'agsiz iddia PASS')
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
