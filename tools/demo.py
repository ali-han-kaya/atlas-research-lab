#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demo — DENEME/ dondurulmus kusurlu kosusunu tek komutla gosterir.

NEDEN VAR
  Depoda duran en guclu kanit, 23 Agustos 2026 kosusudur: manifesto 8 FIX'i
  "UYGULANMIS" ilan etti, MASTER'a yalniz 2'si yansidi, dondurulmus FINAL GATE
  yine de PASS dedi. Bu betik o kosuyu OKUMAZ, oldugu gibi kullanir: iddia ile
  kaniti karsilastirir ve bugunku mutabakat kapisini (fix_reconcile) kosturur.
  Beklenen sonuc KIRMIZI'dir; kirmizi degilse fikstur ya da kapi bozulmustur.

KULLANIM
  make demo   (veya: python3 tools/demo.py)

CIKIS
  1 = beklenen kirmizi (iddia 8, kanit 2, dondurulmus kapi PASS)
  2 = fikstur beklenen bicimde degil (test kirilmis, demo degil)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DENEME = KOK / 'DENEME'
MANIFEST = DENEME / '02-FAZ-2-FIX-MANIFEST.md'
MASTER = DENEME / '03-FAZ-3-MASTER-v5.5.md'
GATE = DENEME / 'gate' / 'FINAL-GATE-v5.5.json'
RECONCILE = KOK / 'ATLAS_SABLONLAR' / 'scripts' / 'fix_reconcile.py'

BEKLENEN_IDDIA = 8
BEKLENEN_KANIT = 2


def main():
    iddia_satirlari = re.findall(
        r'^\|\s*(FIX-\d{3})\s*\|.*\|\s*UYGULANMI[ŞS]\s*\|',
        MANIFEST.read_text(encoding='utf-8'), re.M)
    iddia = len(iddia_satirlari)
    master_metni = MASTER.read_text(encoding='utf-8')
    kanit = sorted(set(re.findall(r'FIX-\d{3}', master_metni)))
    gate = json.loads(GATE.read_text(encoding='utf-8'))

    print('DEMO — DENEME/ dondurulmus kusurlu kosu (v5.5.2, 23 Agustos 2026)')
    print('kaynak: DENEME/ — bilerek duzeltilmedi; regresyon fiksturu.')
    print()
    print('  manifesto iddiasi : %d FIX "UYGULANMIS"' % iddia)
    print('  MASTER\'da gorunen : %d FIX' % len(kanit))
    print('  dondurulmus kapi  : %s  (%s)'
          % (gate.get('verdict'), GATE.relative_to(KOK)))
    print()

    if iddia != BEKLENEN_IDDIA or len(kanit) != BEKLENEN_KANIT:
        print('FIKSTUR DEGISTI — iddia=%d (beklenen %d), kanit=%d (beklenen %d)'
              % (iddia, BEKLENEN_IDDIA, len(kanit), BEKLENEN_KANIT))
        print('HUKUM: DEMO KIRIK — fikstur beklenen bicimde degil (rc=2).')
        return 2

    r = subprocess.run([sys.executable, str(RECONCILE)], cwd=str(DENEME),
                       capture_output=True, text=True, timeout=120)
    cikti = ((r.stdout or '') + (r.stderr or '')).strip()
    print('  bugunku mutabakat : %s  (fix_reconcile, rc=%d)'
          % ('FAIL' if r.returncode else 'PASS', r.returncode))
    print()
    for satir in cikti.splitlines():
        if satir.startswith(('FAIL', 'PASS')):
            print('  ' + satir)
    print()

    if r.returncode == 0:
        print('HUKUM: DEMO KIRIK — mutabakat kirmizi yanmadi (rc=2).')
        return 2

    print('HUKUM: FAIL — iddia %d, kanit %d; dondurulmus kapi PASS dedi.' % (iddia, len(kanit)))
    print('BEKLENEN KIRMIZI — bu komut bilerek rc=1 doner.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
