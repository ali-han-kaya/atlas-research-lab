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
  python3 tools/sir_kapisi.py --staged          # indeksteki degisiklikler (pre-commit)
  python3 tools/sir_kapisi.py --tum             # calisma agaci (CI)
  python3 tools/sir_kapisi.py --dosyalar a b    # verilen dosyalar
  python3 tools/sir_kapisi.py --aralik A..B     # commit araligi
  python3 tools/sir_kapisi.py --push YEREL UZAK REMOTE
                                                # pre-push: yalniz YENI commit'ler;
                                                # eski gecmis yalniz sayilir, engellemez

CIKIS: 0 temiz · 1 bulgu · 2 kullanim/aralik hatasi
SIR DEGERI BASILMAZ: yalniz dosya, satir, kural adi ve sayi yazilir.
"""
import os
import re
import subprocess
import sys

PAT_DSN = re.compile(r'postgres(?:ql)?://([^\s:/@]+):([^\s@]+)@')
PAT_NPG = re.compile(r'npg_[A-Za-z0-9]{8,}')
SIFIR = '0' * 40

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


def _rev_list(*args):
    r = _git('rev-list', *args)
    if r.returncode != 0:
        return None
    return r.stdout.split()


def _commit_bulgulari(sha_listesi):
    """Commit'lerin EKLEDIGI satirlardaki eslesmeler; icerik basilmaz.

    Tum agaci taramak, eski bir commit'te duran siri yeni commit'in agacinda
    yeniden bulur ve push'u yanlislikla kilitler. Bu yuzden yalnizca diff'in
    `+` satirlari taranir; eski sirlar yalniz uyari sayiminda kalir.
    """
    bulgular = []
    for sha in sha_listesi:
        g = subprocess.run(
            ['git', 'show', '--format=', '--unified=0', '--no-ext-diff',
             '--find-renames', sha],
            capture_output=True, text=True)
        if g.returncode != 0:
            continue
        yol = None
        yeni_satir = 0
        for satir in g.stdout.splitlines():
            if satir.startswith('+++ '):
                p = satir[4:].strip()
                if p == '/dev/null':
                    yol = None
                else:
                    yol = p[2:] if p.startswith('b/') else p
                continue
            m = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)', satir)
            if m:
                yeni_satir = int(m.group(1))
                continue
            if yol is None:
                continue
            if satir.startswith('+') and not satir.startswith('+++'):
                icerik = satir[1:]
                etiket = '%s:%s' % (sha[:8], yol)
                for k, p in PAT_DSN.findall(icerik):
                    if not yer_tutucu(k, p):
                        bulgular.append((etiket, yeni_satir, 'canli-dsn'))
                if PAT_NPG.search(icerik):
                    bulgular.append((etiket, yeni_satir, 'neon-token'))
                yeni_satir += 1
            elif satir.startswith(' '):
                yeni_satir += 1
    return bulgular


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
    sha_listesi = _rev_list(aralik)
    if sha_listesi is None:
        print('HATA: gecersiz aralik: %s' % aralik)
        return None
    return _commit_bulgulari(sha_listesi)


def _remote_ref_var(uzak_ad):
    r = _git('for-each-ref', '--format=%(refname)',
             'refs/remotes/%s' % uzak_ad)
    return r.returncode == 0 and bool(r.stdout.strip())


def yeni_commitler(yerel_sha, uzak_sha, uzak_ad):
    """Push ile remote'a YENI gidecek commit'ler.

    Yeni dalda uzak_sha sifirdir; remote'ta zaten bulunan tum commit'ler
    dislanir. Boylece 696 eski commit yeniden taranip push kilitlenmez.
    Remote tamamen bos ise (ilk push) tum commit'ler yenidir ve taranir.
    """
    if uzak_sha and uzak_sha != SIFIR:
        return _rev_list('%s..%s' % (uzak_sha, yerel_sha))
    if _remote_ref_var(uzak_ad):
        return _rev_list(yerel_sha, '--not', '--remotes=%s' % uzak_ad)
    return _rev_list(yerel_sha)


def eski_commitler(uzak_sha, uzak_ad):
    """Remote'ta zaten bulunan eski commit'ler (yalniz uyari sayimi)."""
    if uzak_sha and uzak_sha != SIFIR:
        return _rev_list(uzak_sha)
    if _remote_ref_var(uzak_ad):
        return _rev_list('--remotes=%s' % uzak_ad)
    return []


def _kural_sayilari(bulgular):
    sayilar = {}
    for _etiket, _no, kural in bulgular:
        sayilar[kural] = sayilar.get(kural, 0) + 1
    return sayilar


def _bulgu_ozeti(bulgular):
    dosyalar = {}
    for etiket, _no, kural in bulgular:
        dosyalar.setdefault(etiket, set()).add(kural)
    for etiket in sorted(dosyalar):
        print('BULGU %s · %s' % (etiket, ','.join(sorted(dosyalar[etiket]))))
    print('SIR-KAPISI FAIL — %d eslesme · %d commit-dosya'
          % (len(bulgular), len(dosyalar)))


def push_kontrol(yerel_sha, uzak_sha, uzak_ad):
    """Yeni commit'lerdeki sirlari engelle; eski gecmisi yalniz say.

    Eski gecmis sirlari push'u kilitlemez; sayi ve kural adi basilir, deger
    asla basilmaz. Boylece mevcut tarihce temizlenmeden de ilerlenebilir.
    """
    yeni = yeni_commitler(yerel_sha, uzak_sha, uzak_ad)
    if yeni is None:
        print('HATA: push araligi cozulemedi: %s' % yerel_sha)
        return 2

    eski = eski_commitler(uzak_sha, uzak_ad)
    if eski is None:
        print('SIR-KAPISI UYARI: eski gecmis taranamadi · deger BASILMADI')
    elif eski:
        eski_bulgular = _commit_bulgulari(eski)
        sayilar = _kural_sayilari(eski_bulgular)
        detay = ', '.join('%s=%d' % (k, sayilar[k]) for k in sorted(sayilar))
        if detay:
            detay = ' (%s)' % detay
        print('SIR-KAPISI UYARI: eski gecmis %d commit · %d desen%s · '
              'deger BASILMADI'
              % (len(eski), len(eski_bulgular), detay))

    yeni_bulgular = _commit_bulgulari(yeni)
    if yeni_bulgular:
        _bulgu_ozeti(yeni_bulgular)
        return 1
    print('SIR-KAPISI PASS — push araligi temiz (%d yeni commit)' % len(yeni))
    return 0


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
        _bulgu_ozeti(bulgular)
        return 1
    elif '--push' in argv:
        i = argv.index('--push')
        if i + 3 >= len(argv):
            print('HATA: --push <yerel_sha> <uzak_sha> <uzak_ad> ister')
            return 2
        return push_kontrol(argv[i + 1], argv[i + 2],
                            argv[i + 3] or 'origin')
    else:
        print('kullanim: --staged | --tum | --dosyalar <yollar> | '
              '--aralik <A..B> | --push <yerel_sha> <uzak_sha> <uzak_ad>')
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
