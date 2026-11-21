#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demo — DENEME/ dondurulmus kusurlu kosusunu tek komutla gosterir.

NEDEN VAR
  Depoda duran en guclu kanit, 23 Agustos 2026 kosusudur: manifesto 8 FIX'i
  "UYGULANMIS" ilan etti, MASTER'a yalniz 2'si yansidi, dondurulmus FINAL GATE
  yine de PASS dedi. Bu betik o kosuyu OKUMAZ, oldugu gibi kullanir: iddia ile
  kaniti karsilastirir ve bugunku mutabakat kapisini (fix_reconcile) kosturur.

CIKIS KODLARI
  0 = YESIL: iddia == kanit ve mutabakat PASS (celiski yok)
  1 = KIRMIZI: kapi PASS dedi ama iddia > kanit (tarihsel hata yeniden uretildi)
  2 = FIKSTUR BOZUK: dosya yok/bozuk, kapi PASS degil ya da mutabakat okunamadi

KULLANIM
  ./demo                 (kanonik; kabuk kodu dogrudan betikten gelir)
  python3 tools/demo.py  (ayni)
  ./demo --kok <dizin>   (baska bir fikstur koku; varsayilan DENEME/)
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
VARSAYILAN = KOK / 'DENEME'
FIX_RE = re.compile(r'FIX-\d{3}')
MANIFEST_AD = '02-FAZ-2-FIX-MANIFEST.md'
MASTER_ADLAR = ('03-FAZ-3-MASTER-v5.5.md', '03-FAZ-3-MASTER-v5.4.md',
                '03-FAZ-3-MASTER-v5.2.md', 'MASTER.md')
GATE_AD = 'gate/FINAL-GATE-v5.5.json'
GATE2B_AD = 'gate/STRONG-gate-2b-v5.5.json'
FAZ1_AD = '01-FAZ-1-LENS-ANALYSIS.json'
RECONCILE = KOK / 'ATLAS_SABLONLAR' / 'scripts' / 'fix_reconcile.py'


def _kok(argv):
    if '--kok' in argv:
        i = argv.index('--kok')
        if i + 1 >= len(argv):
            print('HATA: --kok <dizin> ister')
            sys.exit(2)
        return Path(argv[i + 1]).resolve()
    return VARSAYILAN


def fikstur(kok):
    """(iddia, kanit, gate_verdict, gate_yolu) ya da (None, sebep)."""
    manifest = kok / MANIFEST_AD
    master = next((kok / a for a in MASTER_ADLAR if (kok / a).is_file()), None)
    gate = kok / GATE_AD
    for yol in (manifest, master, gate):
        if yol is None or not yol.is_file():
            return None, 'dosya yok: %s' % (yol or MANIFEST_AD)
    iddia = len(re.findall(
        r'^\|\s*(FIX-\d{3})\s*\|.*\|\s*UYGULANMI[ŞS]\s*\|',
        manifest.read_text(encoding='utf-8'), re.M))
    kanit = sorted(set(FIX_RE.findall(master.read_text(encoding='utf-8'))))
    try:
        verdict = json.loads(gate.read_text(encoding='utf-8')).get('verdict')
    except ValueError:
        return None, 'gecersiz JSON: %s' % gate.name
    return (iddia, kanit, verdict, gate), None


def mutabakat(kok):
    ortam = dict(os.environ,
                 ATLAS_FAZ1_FILE=str(kok / FAZ1_AD),
                 ATLAS_FAZ2_FILE=str(kok / MANIFEST_AD),
                 ATLAS_GATE2B_FILE=str(kok / GATE2B_AD))
    try:
        r = subprocess.run([sys.executable, str(RECONCILE)], cwd=str(kok),
                           capture_output=True, text=True, timeout=120,
                           env=ortam)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, 'mutabakat kosulamadi: %s' % e
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()


def main(argv):
    kok = _kok(argv)
    etiket = 'DENEME/' if kok == VARSAYILAN else str(kok)
    if kok == VARSAYILAN:
        print('DEMO — DENEME/ dondurulmus kusurlu kosu (v5.5.2, 23 Agustos 2026)')
    else:
        print('DEMO — harici fikstur: %s' % etiket)
    if kok == VARSAYILAN:
        print('kaynak: %s — bilerek duzeltilmedi; regresyon fiksturu.' % etiket)
    else:
        print('kaynak: %s — harici fikstur.' % etiket)
    print()

    veri, hata = fikstur(kok)
    if hata:
        print('  FIKSTUR DEGISTI — %s' % hata)
        print('HUKUM: DEMO KIRIK — fikstur okunamadi (rc=2).')
        return 2
    iddia, kanit, verdict, gate = veri

    print('  manifesto iddiasi : %d FIX "UYGULANMIS"' % iddia)
    print("  MASTER'da gorunen : %d FIX" % len(kanit))
    try:
        gate_etiket = str(gate.relative_to(KOK))
    except ValueError:
        gate_etiket = str(gate)
    print('  dondurulmus kapi  : %s  (%s)' % (verdict, gate_etiket))
    print()

    rc, cikti = mutabakat(kok)
    if rc is None:
        print('  FIKSTUR DEGISTI — %s' % cikti)
        print('HUKUM: DEMO KIRIK — mutabakat kosulamadi (rc=2).')
        return 2
    print('  bugunku mutabakat : %s  (fix_reconcile, rc=%d)'
          % ('FAIL' if rc else 'PASS', rc))
    print()
    for satir in cikti.splitlines():
        if satir.startswith(('FAIL', 'PASS')):
            print('  ' + satir)
    print()

    if verdict == 'PASS' and iddia > len(kanit):
        print('HUKUM: FAIL — iddia %d, kanit %d; dondurulmus kapi PASS dedi.'
              % (iddia, len(kanit)))
        print('BEKLENEN KIRMIZI — bu komut bilerek rc=1 doner.')
        return 1

    if rc == 0 and iddia == len(kanit):
        print('HUKUM: PASS — iddia %d, kanit %d; kapi %s, mutabakat PASS.'
              % (iddia, len(kanit), verdict))
        print('YESIL — iddia ve kanit uyumlu (rc=0).')
        return 0

    print('HUKUM: DEMO KIRIK — kapi=%s, iddia=%d, kanit=%d, mutabakat rc=%d.'
          % (verdict, iddia, len(kanit), rc))
    print('FIKSTUR DEGISTI — beklenen celiski ya da yesil durum yok (rc=2).')
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
