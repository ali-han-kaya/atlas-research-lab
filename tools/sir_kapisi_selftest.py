#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sir_kapisi oz-testi — kapi gercekten atesliyor mu, yoksa sus mu?

NEDEN VAR
  Bir koruma "calisiyor" demek icin once temiz girdide sessiz kaldigini, sonra
  tek bir canli desende kirmiziya dondugunu olcmek gerekir. Bu test dokuz betik
  vakasi, iki gercek `git commit` vakasi, iki `git push` vakasi ve dort git
  kenari kosar; canli DSN'in ciktida GORUNMEDIGINI de ayrica dogrular.

KULLANIM
  python3 tools/sir_kapisi_selftest.py

CIKIS: 0 = 17/17 gecti · 1 = en az bir vaka kirmizi
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
MASKE = 'postgresql://' + 'USER' + ':' + '***' + '@host/db'
DOLAR_CANLI = 'postgresql://' + 'USER' + ':' + '$gercek123' + '@host/db'
DEGISKEN = 'postgresql://' + 'USER' + ':' + '$DB_PASS' + '@host/db'
SUSLU_DEGISKEN = 'postgresql://' + 'USER' + ':' + '${DB_PASS}' + '@host/db'
ADMIN_KOSELI = 'postgresql://' + 'admin' + ':' + '<parola>' + '@host/db'
TEMIZ = 'baglanti yok; bu dosyada sir yok.\n'
SIFIR = '0' * 40


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


def _git(depo, *args):
    return _kos(['git'] + list(args), depo)


def _kimlik(depo):
    """Klonda global git kimligine guvenme; test hermetik olsun."""
    for komut in (['git', 'config', 'user.name', 'Oz Test'],
                  ['git', 'config', 'user.email', 'oztest@example.invalid']):
        r = _kos(komut, depo)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:120])


def _depo_hazir(depo, ad='main'):
    depo.mkdir(parents=True)
    r = _kos(['git', 'init', '-q', '-b', ad], depo)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:120])
    _kimlik(depo)


def _commit(depo, mesaj):
    _git(depo, 'add', '-A')
    r = _git(depo, 'commit', '-q', '-m', mesaj)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:120])
    return _git(depo, 'rev-parse', 'HEAD').stdout.strip()


def _git_vaka(komut, depo, iz, sizinti=None):
    """Bir git kenarini kosar; ciktiyi yalniz kural/rc ile dogrular."""
    r = _kos(komut, depo)
    cikti = (r.stdout or '') + (r.stderr or '')
    if r.returncode != 1:
        return False, 'rc=%d (beklenen 1) · %s' % (r.returncode, cikti.strip()[:160])
    if iz not in cikti:
        return False, 'iz yok (%s) · %s' % (iz, cikti.strip()[:160])
    if sizinti and sizinti in cikti:
        return False, 'SIZINTI: deger ciktida gorundu'
    return True, 'rc=1 · %s' % iz


def vaka_merge():
    """Merge catismasinda yalniz merge commit'ine giren sir yakalanir."""
    tmp = Path(tempfile.mkdtemp(prefix='sir_merge_'))
    try:
        depo = tmp / 'depo'
        _depo_hazir(depo)
        _yaz(depo / 'f.txt', 'base\n')
        base = _commit(depo, 'base')
        _git(depo, 'checkout', '-q', '-b', 'side')
        _yaz(depo / 'f.txt', 'side\n')
        _commit(depo, 'side')
        _git(depo, 'checkout', '-q', 'main')
        _yaz(depo / 'f.txt', 'main\n')
        _commit(depo, 'main')
        if _git(depo, 'merge', 'side').returncode == 0:
            return False, 'merge catismasi bekleniyordu'
        _yaz(depo / 'f.txt', CANLI + '\n')
        _commit(depo, 'merge')
        return _git_vaka([sys.executable, str(KAPI), '--aralik',
                          base + '..HEAD'], depo, 'canli-dsn',
                         sizinti='gercekparola123')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def vaka_rename():
    """Yuksek benzerlikli rename'in YENI yolu staged taramada taranir."""
    tmp = Path(tempfile.mkdtemp(prefix='sir_rename_'))
    try:
        depo = tmp / 'depo'
        _depo_hazir(depo)
        govde = '\n'.join('satir %02d' % i for i in range(1, 31)) + '\n'
        _yaz(depo / 'old.md', govde)
        _commit(depo, 'base')
        _git(depo, 'mv', 'old.md', 'new.md')
        _yaz(depo / 'new.md', govde + 'canli: ' + CANLI + '\n')
        _git(depo, 'add', 'new.md')
        durum = _git(depo, 'diff', '--cached', '-M', '--name-status').stdout
        if not durum.startswith('R'):
            return False, 'rename tespit edilmedi: %s' % durum.strip()[:80]
        return _git_vaka([sys.executable, str(KAPI), '--staged'], depo,
                         'canli-dsn', sizinti='gercekparola123')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def vaka_plus():
    """Icerigi `++` ile baslayan eklenmis satir hunk basligi sanilmaz."""
    tmp = Path(tempfile.mkdtemp(prefix='sir_plus_'))
    try:
        depo = tmp / 'depo'
        _depo_hazir(depo)
        _yaz(depo / 'x.md', 'base\n')
        _commit(depo, 'base')
        _yaz(depo / 'x.md', 'base\n++' + CANLI + '\n')
        _commit(depo, 'plus')
        return _git_vaka([sys.executable, str(KAPI), '--aralik',
                          'HEAD^..HEAD'], depo, 'canli-dsn',
                         sizinti='gercekparola123')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def vaka_shallow():
    """Shallow clone'da yeni commit'in siri, eksik eski tarihçeye ragmen yakalanir."""
    tmp = Path(tempfile.mkdtemp(prefix='sir_shallow_'))
    try:
        kaynak = tmp / 'kaynak'
        _depo_hazir(kaynak)
        _yaz(kaynak / 'a.md', 'temiz\n')
        _commit(kaynak, 'clean')
        depo = tmp / 'shallow'
        r = _kos(['git', 'clone', '-q', '--depth=1',
                  'file://' + str(kaynak), str(depo)], tmp)
        if r.returncode != 0:
            return False, 'clone: %s' % (r.stderr or r.stdout).strip()[:120]
        _kimlik(depo)
        _yaz(depo / 'new.md', CANLI + '\n')
        _commit(depo, 'new')
        yeni = _git(depo, 'rev-parse', 'HEAD').stdout.strip()
        return _git_vaka([sys.executable, str(KAPI), '--push', yeni,
                          SIFIR, 'origin'], depo, 'canli-dsn',
                         sizinti='gercekparola123')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print('SIR KAPISI OZ-TESTI — canli desen kirmizi, yer tutucu sessiz')
    vakalar = [
        ('canli DSN kirmizi', lambda: vaka_dosya('canli', CANLI, 1, 'canli-dsn',
                                                sizinti='gercekparola123')),
        ('USER:*** kirmizi', lambda: vaka_dosya('maske', MASKE, 1, 'canli-dsn')),
        ('$ parolali canli kirmizi',
         lambda: vaka_dosya('dolar', DOLAR_CANLI, 1, 'canli-dsn',
                            sizinti='gercek123')),
        ('USER:$DB_PASS sessiz', lambda: vaka_dosya('degisken', DEGISKEN, 0, None)),
        ('${DB_PASS} sessiz', lambda: vaka_dosya('suslu', SUSLU_DEGISKEN, 0, None)),
        ('admin:<parola> sessiz', lambda: vaka_dosya('admin', ADMIN_KOSELI, 0, None)),
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
        ('merge commit canliyi yakalar', vaka_merge),
        ('rename staged canliyi yakalar', vaka_rename),
        ('++ icerik satiri canliyi yakalar', vaka_plus),
        ('shallow clone yeni siri yakalar', vaka_shallow),
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
