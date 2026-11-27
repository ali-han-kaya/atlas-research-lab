#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sir_gecmis_selftest — Git gecmisi sır/kisisel veri kapisinin regresyonu.

NEDEN VAR
  `secret_scan.py --git-gecmis` yalniz calisma agacini degil, tum ref'lerdeki
  commit ve blob'lari tarar. Bu kapi iki yonde sessizce korlesebilir:
    * eski bir commit'te kalan sır/kişisel e-posta gorulmez,
    * satir sonunda bolunmus bir deger tek satirda eslesmedigi icin kacar.
  Ayrica sig klon veya bozuk Git nesnesi "temiz" diye raporlanmamalidir.

NASIL
  Her vaka kendi gecici Git deposunu kurar; ana depoya YAZILMAZ. Gizli degerler
  test kaynaginda butun halde tutulmaz, parcalardan runtime'da uretilir. Boylece
  bu test dosyasi da taranirken kendi fiksturunu sir gibi gostermez.

KULLANIM
  python3 tools/sir_gecmis_selftest.py

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KAPI = KOK / 'KOD_SABLONLAR' / 'scripts' / 'secret_scan.py'
V4_DIZIN = KOK / 'KOMUT_TOOLKIT_v4' / 'ARACLAR' / 'betikler'
V4 = V4_DIZIN / 'v4_verify.py'
SONUCLAR = []

# Degerler runtime'da birlestirilir; kaynakta tam bir anahtar/adres yoktur.
SIR_PARCA_1 = 'AKIA2E1F'
SIR_PARCA_2 = '4B7C9D0E3F9A'
SIR = SIR_PARCA_1 + SIR_PARCA_2
EPOSTA_PARCA_1 = 'kisi@'
EPOSTA_PARCA_2 = 'ornek-firma.xyz'
EPOSTA_GUVENSIZ = EPOSTA_PARCA_1 + EPOSTA_PARCA_2


def kontrol(ad, gecti, ayrinti=''):
    SONUCLAR.append((ad, bool(gecti)))
    print('  %-5s %s%s' % ('PASS' if gecti else 'FAIL', ad,
                           ('' if gecti else ' :: %s' % ayrinti)))


def git(repo, *args, env=None, check=True):
    r = subprocess.run(['git'] + list(args), cwd=str(repo), env=env,
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError('git %s: %s' % (' '.join(args),
                                           (r.stderr or r.stdout).strip()[:200]))
    return r


def repo_kur(tmp, ad):
    repo = Path(tmp) / ad
    repo.mkdir(parents=True)
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.name', 'ATLAS Test')
    git(repo, 'config', 'user.email', 'noreply@example.com')
    return repo


def yaz_ve_commit(repo, rel, metin, mesaj='test', env=None):
    yol = repo / rel
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding='utf-8')
    git(repo, 'add', rel, env=env)
    git(repo, 'commit', '-q', '-m', mesaj, env=env)


def kapi(repo, *ek, kapi_yolu=None, v4=None):
    komut = [sys.executable, str(kapi_yolu or KAPI), '--git-gecmis',
             '--dizin', str(repo), '--v4', str(v4 or V4), '--json'] + list(ek)
    r = subprocess.run(komut, cwd=str(repo), capture_output=True, text=True)
    cikti = (r.stdout or '') + (r.stderr or '')
    try:
        rapor = json.loads(r.stdout)
    except ValueError:
        rapor = None
    return r.returncode, rapor, cikti


def p0(rapor, kural):
    return [b for b in (rapor or {}).get('bulgular', [])
            if b.get('kural') == kural and b.get('siddet') == 'P0']


def vaka_temiz(tmp):
    repo = repo_kur(tmp, 'temiz')
    yaz_ve_commit(repo, 'docs/notlar.md', '# Notlar\nBu temiz bir tabandir.\n')
    rc, rapor, cikti = kapi(repo)
    kontrol('temiz taban PASS', rc == 0 and rapor is not None
            and rapor.get('p0') == 0 and rapor.get('commit_sayisi', 0) >= 1,
            'rc=%d rapor=%s' % (rc, str(rapor or cikti)[:180]))


def vaka_eski_commit_sir(tmp):
    repo = repo_kur(tmp, 'eski_sir')
    eski = 'config/eski.txt'
    yaz_ve_commit(repo, eski, 'AWS_KEY = "' + SIR + '"\n', 'eski sır')
    git(repo, 'rm', '-q', eski)
    git(repo, 'commit', '-q', '-m', 'sırrı kaldır')
    rc, rapor, cikti = kapi(repo)
    kontrol('eski commit sirri yakalanir',
            rc == 1 and rapor is not None and p0(rapor, 'SEC-02')
            and any('config/eski.txt' in b.get('konum', '')
                    for b in p0(rapor, 'SEC-02')),
            'rc=%d p0=%d' % (rc, len(p0(rapor, 'SEC-02'))))
    kontrol('sir degeri ciktiya sizmaz', SIR not in cikti,
            'ham sır stdout/stderr icinde')


def vaka_bolunmus_sir(tmp):
    repo = repo_kur(tmp, 'bolunmus_sir')
    # Iki satir; newline kaldirilinca AKIA + 16 karakter olusur.
    yaz_ve_commit(repo, 'config/bolunmus.txt',
                  'AWS_KEY = "AKIA2E1F\n4B7C9D0E3F9A"\n', 'bolunmus sır')
    rc, rapor, cikti = kapi(repo)
    kayit = p0(rapor, 'SEC-02')
    kontrol('satir bolunmus sir yakalanir',
            rc == 1 and rapor is not None and bool(kayit)
            and any('bolunmus' in b.get('aciklama', '').lower()
                    or ':' in b.get('konum', '') and '-' in b.get('konum', '')
                    for b in kayit),
            'rc=%d p0=%d' % (rc, len(kayit)))
    kontrol('bolunmus sir degeri ciktiya sizmaz', SIR not in cikti,
            'ham sır stdout/stderr icinde')


def vaka_eski_kisisel_eposta(tmp):
    repo = repo_kur(tmp, 'eski_eposta')
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = 'Test'
    env['GIT_AUTHOR_EMAIL'] = EPOSTA_GUVENSIZ
    env['GIT_COMMITTER_NAME'] = 'Test'
    env['GIT_COMMITTER_EMAIL'] = EPOSTA_GUVENSIZ
    yaz_ve_commit(repo, 'docs/notlar.md', '# Notlar\n', 'kimlik testi', env=env)
    rc, rapor, cikti = kapi(repo)
    kayit = p0(rapor, 'SEC-06')
    kontrol('eski commit kisisel e-postasi yakalanir',
            rc == 1 and rapor is not None and bool(kayit)
            and any(b.get('konum', '').startswith('commit/') for b in kayit),
            'rc=%d p0=%d' % (rc, len(kayit)))
    kontrol('kisisel e-posta ciktiya sizmaz', EPOSTA_GUVENSIZ not in cikti,
            'ham adres stdout/stderr icinde')


def vaka_bolunmus_eposta(tmp):
    repo = repo_kur(tmp, 'bolunmus_eposta')
    yaz_ve_commit(repo, 'docs/iletisim.txt',
                  'Iletisim: kisi@\norner-firma.xyz\n', 'bolunmus e-posta')
    rc, rapor, cikti = kapi(repo)
    kayit = p0(rapor, 'SEC-06')
    kontrol('satir bolunmus kisisel e-posta yakalanir',
            rc == 1 and rapor is not None and bool(kayit),
            'rc=%d p0=%d' % (rc, len(kayit)))


def vaka_shallow(tmp):
    kaynak = repo_kur(tmp, 'shallow_kaynak')
    yaz_ve_commit(kaynak, 'a.txt', 'bir\n', 'bir')
    yaz_ve_commit(kaynak, 'a.txt', 'iki\n', 'iki')
    hedef = Path(tmp) / 'shallow_klon'
    r = subprocess.run(['git', 'clone', '-q', '--depth', '1',
                        kaynak.as_uri(), str(hedef)], capture_output=True, text=True)
    if r.returncode != 0:
        kontrol('sig klon fail-closed', False, 'klon kurulamadi: %s' % r.stderr[-160:])
        return
    rc, rapor, cikti = kapi(hedef)
    kontrol('sig klon fail-closed',
            rc != 0 and rapor is None and 'SEC-07' in cikti
            and 'shallow' in cikti.lower(),
            'rc=%d cikti=%s' % (rc, cikti.strip()[-180:]))


def vaka_git_yok(tmp):
    bos = Path(tmp) / 'git_yok'
    bos.mkdir()
    rc, rapor, cikti = kapi(bos)
    kontrol('git gecmisi yokken fail-closed',
            rc != 0 and rapor is None and 'SEC-07' in cikti,
            'rc=%d cikti=%s' % (rc, cikti.strip()[-180:]))


def vaka_v4_yok(tmp):
    repo = repo_kur(tmp, 'v4_yok')
    yaz_ve_commit(repo, 'a.txt', 'temiz\n')
    rc, rapor, cikti = kapi(repo, v4=Path(tmp) / 'olmayan_v4.py')
    kontrol('kalip tabani yokken KISMI/fail-closed',
            rc == 3 and 'KISMI' in cikti and rapor is None,
            'rc=%d cikti=%s' % (rc, cikti.strip()[-180:]))


def vaka_fikstur(tmp):
    """Tarihsel fikstur satiri sessiz; ayni dosyaya yeni sir eklenince P0."""
    arac = Path(tmp) / 'arac'
    for rel in ('KOD_SABLONLAR/scripts/secret_scan.py',
                'KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_verify.py',
                'KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_common.py'):
        hedef = arac / rel
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(KOK / rel, hedef)
    fikstur_yolu = 'docs/OLCUM-02-CANLI-KOSU.md'
    satir = 'AWS_KEY = "AKIA' + '2E1F4B7C9D0E3F9A"'
    (arac / 'docs').mkdir(parents=True, exist_ok=True)
    (arac / 'docs' / 'OLCUM-02-CANLI-KOSU.md').write_text(
        '# kayit\n' + satir + '\n', encoding='utf-8')
    (arac / 'tools').mkdir(parents=True, exist_ok=True)
    manifest = {'sema': 'SECRET-SCAN-FIKSTUR/v1', 'fiksturler': [{
        'dosya': fikstur_yolu, 'satir': 2,
        'satir_sha256': hashlib.sha256(satir.encode('utf-8')).hexdigest(),
        'gerekce': 'gecmis kapisi regresyon fiksturu; gercek sir degil',
        'kanit': 'sir_gecmis_selftest',
    }]}
    (arac / 'tools' / 'secret_fixtures.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    git(arac, 'init', '-q')
    git(arac, 'config', 'user.name', 'ATLAS Test')
    git(arac, 'config', 'user.email', 'noreply@example.com')
    git(arac, 'add', '.')
    git(arac, 'commit', '-q', '-m', 'fikstur')
    yerel_kapi = arac / 'KOD_SABLONLAR' / 'scripts' / 'secret_scan.py'
    rc, rapor, cikti = kapi(arac, kapi_yolu=yerel_kapi)
    kontrol('tarihsel fikstur satiri sessiz',
            rc == 0 and rapor is not None and rapor.get('p0') == 0
            and rapor.get('fikstur_muafiyeti', 0) >= 1,
            'rc=%d p0=%s fikstur=%s' % (
                rc, (rapor or {}).get('p0'), (rapor or {}).get('fikstur_muafiyeti')))
    # Ayni dosyaya yeni bir sır ekle: eski satir muaf, yeni satir degil.
    with (arac / 'docs' / 'OLCUM-02-CANLI-KOSU.md').open('a', encoding='utf-8') as f:
        f.write('AWS_KEY = "AKIA' + '3E1F4B7C9D0E3F9A"\n')
    git(arac, 'add', '.')
    git(arac, 'commit', '-q', '-m', 'yeni sır')
    rc, rapor, cikti = kapi(arac, kapi_yolu=yerel_kapi)
    kontrol('fikstur disi yeni satir P0',
            rc == 1 and rapor is not None and bool(p0(rapor, 'SEC-02')),
            'rc=%d p0=%s' % (rc, (rapor or {}).get('p0')))


def main():
    print('SIR GECMISI OZ-TEST — fail-closed + bolunmus satir')
    with tempfile.TemporaryDirectory(prefix='atlas-sir-gecmis-') as tmp:
        vaka_temiz(tmp)
        vaka_eski_commit_sir(tmp)
        vaka_bolunmus_sir(tmp)
        vaka_eski_kisisel_eposta(tmp)
        vaka_bolunmus_eposta(tmp)
        vaka_shallow(tmp)
        vaka_git_yok(tmp)
        vaka_v4_yok(tmp)
        vaka_fikstur(tmp)
    gecen = sum(1 for _, ok in SONUCLAR if ok)
    toplam = len(SONUCLAR)
    print()
    print('HUKUM: %s — %d/%d gecti' % (
        'PASS' if gecen == toplam else 'FAIL', gecen, toplam))
    return 0 if gecen == toplam else 1


if __name__ == '__main__':
    sys.exit(main())
