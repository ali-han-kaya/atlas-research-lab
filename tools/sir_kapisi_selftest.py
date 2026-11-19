#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sir_kapisi oz-testi — kapi gercekten atesliyor mu, yoksa sus mu?

NEDEN VAR
  Bir koruma "calisiyor" demek icin once temiz girdide sessiz kaldigini, sonra
  tek bir canli desende kirmiziya dondugunu olcmek gerekir. Bu test dort betik
  vakasi, iki gercek `git commit` vakasi ve iki `git push` vakasi kosar; canli
  DSN'in ciktida GORUNMEDIGINI de ayrica dogrular (sizinti testi).

KULLANIM
  python3 tools/sir_kapisi_selftest.py

CIKIS: 0 = 8/8 gecti · 1 = en az bir vaka kirmizi
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KAPI = KOK / 'tools' / 'sir_kapisi.py'

# Degerler PARCALI kurulur: bu dosya depoda durur ve H4 sir tarayicisi bitisik
# deseni yakalar. Parcali yazim tarayiciyi yaniltmak icin degil, gercek bir
# degerin depoya sizmamasini garantilemek icindir (fikstur oldugu gorunur).
CANLI = 'postgresql://' + 'kullanici' + ':' + 'gercekparola123' + '@host/db'
TOKEN = 'npg_' + 'A1b2C3d4E5f6'
YER = 'postgresql://' + 'NEON_KULLANICI' + ':' + 'NEON_PAROLA' + '@host/db'
TEMIZ = 'baglanti yok; bu dosyada sir yok.\n'


def _kos(komut, cwd):
    return subprocess.run(komut, cwd=str(cwd), capture_output=True, text=True)


def _yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding='utf-8')


def vaka_dosya(ad, icerik, beklenen_rc, iz, sizinti=None):
    tmp = Path(tempfile.mkdtemp(prefix='sir_kapi_'))
    try:
        f = tmp / 'deneme.md'
        _yaz(f, icerik)
        r = _kos([sys.executable, str(KAPI), '--dosyalar', str(f)], KOK)
        cikti = (r.stdout or '') + (r.stderr or '')
        if r.returncode != beklenen_rc:
            return False, 'rc=%d (beklenen %d) · %s' % (r.returncode, beklenen_rc,
                                                        cikti.strip()[:120])
        if iz and iz not in cikti:
            return False, 'iz yok (%s) · %s' % (iz, cikti.strip()[:120])
        if sizinti and sizinti in cikti:
            return False, 'SIZINTI: deger ciktida gorundu'
        return True, 'rc=%d · %s' % (r.returncode, iz or 'temiz')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def vaka_hook(icerik, beklenen_basarili, iz=None):
    """Gercek git commit: hook devrede mi?"""
    tmp = Path(tempfile.mkdtemp(prefix='sir_hook_'))
    try:
        depo = tmp / 'depo'
        _yaz(depo / 'tools' / 'sir_kapisi.py', KAPI.read_text(encoding='utf-8'))
        for ad in ('pre-commit', 'pre-push'):
            _yaz(depo / '.githooks' / ad,
                 (KOK / '.githooks' / ad).read_text(encoding='utf-8'))
        for ad in ('pre-commit', 'pre-push'):
            os.chmod(str(depo / '.githooks' / ad), 0o755)
        ortam = dict(os.environ, GIT_TERMINAL_PROMPT='0')
        for komut in (['git', 'init', '-q'],
                      ['git', 'config', 'user.name', 'Oz Test'],
                      ['git', 'config', 'user.email', 'oztest@example.invalid'],
                      ['git', 'config', 'core.hooksPath', '.githooks']):
            r = _kos(komut, depo)
            if r.returncode != 0:
                return False, 'hazirlik: %s' % (r.stderr or r.stdout).strip()[:120]
        _yaz(depo / 'deneme.md', icerik)
        _kos(['git', 'add', 'deneme.md'], depo)
        r = subprocess.run(['git', 'commit', '-q', '-m', 'test'], cwd=str(depo),
                           capture_output=True, text=True, env=ortam)
        cikti = (r.stdout or '') + (r.stderr or '')
        basarili = r.returncode == 0
        if basarili != beklenen_basarili:
            return False, 'commit rc=%d (beklenen basarili=%s)' % (
                r.returncode, beklenen_basarili)
        if iz and iz not in cikti:
            return False, 'iz yok (%s)' % iz
        return True, 'commit rc=%d · %s' % (r.returncode, iz or 'yer tutucu gecti')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def vaka_push(yeni_sir, beklenen_basarili, iz, sizinti=None):
    """Gercek git push: eski sirlu gecmis engellemez, yeni sir engeller."""
    tmp = Path(tempfile.mkdtemp(prefix='sir_push_'))
    try:
        depo = tmp / 'depo'
        uzak = tmp / 'uzak.git'
        depo.mkdir()
        r = _kos(['git', 'init', '--bare', '-q', str(uzak)], tmp)
        if r.returncode != 0:
            return False, 'uzak hazirlik: %s' % (r.stderr or r.stdout).strip()[:120]
        for komut in (['git', 'init', '-q'],
                      ['git', 'config', 'user.name', 'Oz Test'],
                      ['git', 'config', 'user.email', 'oztest@example.invalid']):
            r = _kos(komut, depo)
            if r.returncode != 0:
                return False, 'depo hazirlik: %s' % (r.stderr or r.stdout).strip()[:120]

        # Eski commit'te canli desen var; hook kurulmadan remote'a gonderilir.
        _yaz(depo / 'eski.md', CANLI)
        _kos(['git', 'add', 'eski.md'], depo)
        r = _kos(['git', 'commit', '-q', '-m', 'eski'], depo)
        if r.returncode != 0:
            return False, 'eski commit: %s' % (r.stderr or r.stdout).strip()[:120]
        _kos(['git', 'remote', 'add', 'origin', str(uzak)], depo)
        r = _kos(['git', 'push', '-q', 'origin', 'HEAD:refs/heads/main'], depo)
        if r.returncode != 0:
            return False, 'eski push: %s' % (r.stderr or r.stdout).strip()[:120]

        # Yeni dal: eski sirlu tabandan bir commit daha.
        _kos(['git', 'checkout', '-q', '-b', 'dene'], depo)
        _yaz(depo / 'yeni.md', CANLI if yeni_sir else TEMIZ)
        _kos(['git', 'add', 'yeni.md'], depo)
        r = _kos(['git', 'commit', '-q', '-m', 'yeni'], depo)
        if r.returncode != 0:
            return False, 'yeni commit: %s' % (r.stderr or r.stdout).strip()[:120]

        # Hook'lari simdi kur: commit'ler hazir, push korumasi devrede.
        _yaz(depo / 'tools' / 'sir_kapisi.py', KAPI.read_text(encoding='utf-8'))
        for ad in ('pre-commit', 'pre-push'):
            _yaz(depo / '.githooks' / ad,
                 (KOK / '.githooks' / ad).read_text(encoding='utf-8'))
            os.chmod(str(depo / '.githooks' / ad), 0o755)
        for komut in (['git', 'config', 'core.hooksPath', '.githooks'],):
            r = _kos(komut, depo)
            if r.returncode != 0:
                return False, 'hook hazirlik: %s' % (r.stderr or r.stdout).strip()[:120]

        ortam = dict(os.environ, GIT_TERMINAL_PROMPT='0')
        r = subprocess.run(['git', 'push', 'origin', 'dene'], cwd=str(depo),
                           capture_output=True, text=True, env=ortam)
        cikti = (r.stdout or '') + (r.stderr or '')
        basarili = r.returncode == 0
        if basarili != beklenen_basarili:
            return False, 'push rc=%d (beklenen basarili=%s) · %s' % (
                r.returncode, beklenen_basarili, cikti.strip()[:160])
        if iz and iz not in cikti:
            return False, 'iz yok (%s) · %s' % (iz, cikti.strip()[:160])
        if sizinti and sizinti in cikti:
            return False, 'SIZINTI: deger ciktida gorundu'
        return True, 'push rc=%d · %s' % (r.returncode, iz)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print('SIR KAPISI OZ-TESTI — canli desen kirmizi, yer tutucu sessiz')
    vakalar = [
        ('canli DSN kirmizi', lambda: vaka_dosya('canli', CANLI, 1, 'canli-dsn',
                                                sizinti='gercekparola123')),
        ('npg_ token kirmizi', lambda: vaka_dosya('token', TOKEN, 1, 'neon-token',
                                                  sizinti=TOKEN)),
        ('yer tutucu sessiz', lambda: vaka_dosya('yer', YER, 0, None)),
        ('temiz dosya sessiz', lambda: vaka_dosya('temiz', TEMIZ, 0, None)),
        ('hook canli commit engeller', lambda: vaka_hook(CANLI, False, 'canli-dsn')),
        ('hook yer tutucuyu gecirir', lambda: vaka_hook(YER, True)),
        ('push eski siri uyariyla gecirir',
         lambda: vaka_push(False, True,
                           'SIR-KAPISI UYARI: eski gecmis 1 commit · 1 desen',
                           sizinti='gercekparola123')),
        ('push yeni siri engeller',
         lambda: vaka_push(True, False, 'canli-dsn',
                           sizinti='gercekparola123')),
    ]
    gecen = 0
    for ad, fn in vakalar:
        try:
            ok, ayrinti = fn()
        except Exception as e:  # noqa: BLE001 - test kosucusu hatayi yutmaz, raporlar
            ok, ayrinti = False, 'ISTISNA: %s' % e
        gecen += 1 if ok else 0
        print('  %-28s %-4s %s' % (ad, 'PASS' if ok else 'FAIL', ayrinti))
    print()
    if gecen == len(vakalar):
        print('SIR KAPISI OZ-TEST: %d/%d gecti' % (gecen, len(vakalar)))
        return 0
    print('SIR KAPISI OZ-TEST: FAIL — %d/%d' % (gecen, len(vakalar)))
    return 1


if __name__ == '__main__':
    sys.exit(main())
