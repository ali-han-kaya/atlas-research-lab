#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guvenlik — pip-audit sonucunu SANSRURMEDEN raporlar.

NEDEN VAR
  `pip-audit` bulgu buldugunda CI'i sonsuza kadar kirmizi tutmak da, bulgulari
  `--ignore-vuln` ile sessizce yutmak da yanlis. Bu betik her bulguyu adiyla
  basar, `docs/GUVENLIK.md`ye yazar ve yalnizca ONCEDEN KAYDA GECMIS, gerekcesi
  yazili bulgulari kabul eder. Listede olmayan yeni bir bulgu cikarsa rc=1:
  yani muafiyet sessiz degil, tarihli ve denetlenebilir.

KULLANIM
  python3 tools/guvenlik.py            # tara + raporla + docs/GUVENLIK.md yaz
  python3 tools/guvenlik.py --kontrol  # dosya guncel mi (yazmaz)

CIKIS: 0 = yalniz kabul edilmis bulgular · 1 = kabul edilmemis bulgu · 2 = arac yok
"""
import json
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
HEDEF = KOK / 'docs' / 'GUVENLIK.md'
OLCUM_TARIHI = '2026-11-19'
REQ = 'requirements-dev.txt'

# (paket, surum, ID) -> gerekce. Yalniz duzeltme surumu YAYIMLANMAMIS bulgular.
# Duzeltme ciktiginda satir silinir; boylece muafiyet kendiliginden kuculur.
KABUL = {
    ('requests', '2.32.5', 'PYSEC-2026-2275'):
        'duzeltme 2.33.0 PyPI da yayimlanmamis (pip download ile olculdu)',
    ('urllib3', '2.6.3', 'PYSEC-2026-142'):
        'duzeltme 2.7.0 PyPI da yayimlanmamis (pip download ile olculdu)',
    ('urllib3', '2.6.3', 'PYSEC-2026-141'):
        'duzeltme 2.7.0 PyPI da yayimlanmamis',
    ('urllib3', '2.6.3', 'PYSEC-2026-4175'):
        'duzeltme 2.8.0 PyPI da yayimlanmamis',
    ('urllib3', '2.6.3', 'PYSEC-2026-4176'):
        'duzeltme 2.8.0 PyPI da yayimlanmamis',
    ('urllib3', '2.6.3', 'PYSEC-2026-4177'):
        'duzeltme 2.8.0 PyPI da yayimlanmamis',
    ('msgpack', '1.1.2', 'PYSEC-2026-3625'):
        'duzeltme 1.2.1 PyPI da yayimlanmamis (pip-audit bagimliligi)',
    ('msgpack', '1.1.2', 'GHSA-j586-36cw-2gc2'):
        'duzeltme 1.2.3 PyPI da yayimlanmamis (pip-audit bagimliligi)',
    ('filelock', '3.19.1', 'PYSEC-2026-1374'):
        'duzeltme 3.20.3 PyPI da yayimlanmamis (pip-audit bagimliligi)',
    ('filelock', '3.19.1', 'PYSEC-2026-1375'):
        'duzeltme 3.20.1 PyPI da yayimlanmamis (pip-audit bagimliligi)',
    ('filelock', '3.19.1', 'GHSA-8mx5-7m5m-r77g'):
        'duzeltme 4.2.1 PyPI da yayimlanmamis (pip-audit bagimliligi)',
    ('filelock', '3.19.1', 'GHSA-69hj-f68j-2879'):
        'duzeltme 4.2.1 PyPI da yayimlanmamis (pip-audit bagimliligi)',
}


def tara():
    r = subprocess.run([sys.executable, '-m', 'pip_audit', '-r', REQ,
                        '-f', 'json', '--progress-spinner', 'off'],
                       cwd=str(KOK), capture_output=True, text=True)
    if r.returncode not in (0, 1):
        print('GUVENLIK: pip-audit kosulamadi (rc=%d) — %s'
              % (r.returncode, (r.stderr or '').strip()[:200]))
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        print('GUVENLIK: pip-audit ciktisi JSON degil')
        return None


def satirlar(veri):
    """[(paket, surum, id, duzeltmeler, kabul_gerekcesi|None)]"""
    out = []
    for dep in veri.get('dependencies', []):
        ad = dep.get('name', '')
        surum = dep.get('version', '')
        for v in dep.get('vulns', []):
            vid = v.get('id', '')
            fix = v.get('fix_versions') or []
            out.append((ad, surum, vid, ', '.join(fix) or '—',
                        KABUL.get((ad, surum, vid))))
    return sorted(out)


def markdown(satir_listesi):
    kabul = [s for s in satir_listesi if s[4]]
    yeni = [s for s in satir_listesi if not s[4]]
    out = ['# Bagimlilik guvenligi — `pip-audit`', '',
           'Kaynak: `tools/guvenlik.py` · olcum: %s · hedef: `%s`' % (OLCUM_TARIHI, REQ),
           '',
           '| Olcum | Deger |', '|---|---|',
           '| Toplam bulgu | %d |' % len(satir_listesi),
           '| Kabul edilmis (duzeltme yayimlanmamis) | %d |' % len(kabul),
           '| Kabul edilmemis (yeni) | %d |' % len(yeni),
           '']
    if satir_listesi:
        out += ['| Paket | Surum | ID | Duzeltme | Durum |', '|---|---|---|---|---|']
        for ad, surum, vid, fix, gerekce in satir_listesi:
            durum = 'kabul: %s' % gerekce if gerekce else 'YENI — kabul yok'
            out.append('| %s | %s | %s | %s | %s |' % (ad, surum, vid, fix, durum))
        out.append('')
    out += ['## Neden muafiyet var', '',
            'Her satirin duzeltme surumu PyPI da aranmis ve BULUNAMAMISTIR;',
            'bu yuzden sabitlemek mumkun degildi. Muafiyet sessiz degil:',
            'listede olmayan bir bulgu cikarsa `make guvenlik` kirmizi doner.',
            'Duzeltme yayimlandiginda satir silinir ve surum sabitlenir.',
            '']
    return '\n'.join(out)


def main(argv):
    veri = tara()
    if veri is None:
        return 2
    satir_listesi = satirlar(veri)
    metin = markdown(satir_listesi)
    for ad, surum, vid, fix, gerekce in satir_listesi:
        print('  %-10s %-8s %-22s fix=%-12s %s'
              % (ad, surum, vid, fix, 'kabul' if gerekce else 'YENI'))
    yeni = [s for s in satir_listesi if not s[4]]
    print()
    print('SONUC: %d bulgu · kabul=%d · yeni=%d'
          % (len(satir_listesi), len(satir_listesi) - len(yeni), len(yeni)))
    if '--kontrol' in argv:
        if not HEDEF.is_file() or HEDEF.read_text(encoding='utf-8') != metin:
            print('GUVENLIK: docs/GUVENLIK.md guncel degil — `make guvenlik`')
            return 1
    else:
        HEDEF.write_text(metin, encoding='utf-8')
    if yeni:
        print('HUKUM: FAIL — kabul edilmemis bulgu var (sansur yok).')
        return 1
    print('HUKUM: PASS — tum bulgular tarihli kayitla kabul edilmis.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
