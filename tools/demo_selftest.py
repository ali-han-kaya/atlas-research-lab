#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demo_selftest.py — demo'nun 0/2 sozlesmesini gecici fiksturlerle sinar.

NEDEN VAR
  ./demo'nun 0 (yesil) ve 2 (bozuk) cikis kodlari yalniz elle olculmustu.
  Bu betik iki gecici fikstur kurar ve gercek demo betigini --kok ile kosar:
    yesil  : DENEME/'nin kopyasi, MASTER'da eksik FIX-ID'ler tamamlanir -> rc=0
    bozuk  : ayni kopya, FINAL-GATE dosyasi silinir                     -> rc=2

  Kaynak DENEME/ DEGISTIRILMEZ; butun yazma islemi tempfile altinda olur.
  CIKIS: 0 = iki senaryo da beklendigi gibi · 1 = en az bir sapma/kurulum hatasi
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DEMO = KOK / 'tools' / 'demo.py'
DENEME = KOK / 'DENEME'
MANIFEST = '02-FAZ-2-FIX-MANIFEST.md'
MASTER = '03-FAZ-3-MASTER-v5.5.md'
GATE = Path('gate') / 'FINAL-GATE-v5.5.json'
FIX_RE = re.compile(r'FIX-\d{3}')


def calistir(kok):
    """demo'yu verilen gecici kokle kos; (rc, birlesik cikti) dondur."""
    try:
        r = subprocess.run(
            [sys.executable, str(DEMO), '--kok', str(kok)],
            cwd=str(KOK), capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, 'demo kosulamadi: %s' % e
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()


def yesil_kur(kok):
    """DENEME/'yi kopyala ve MASTER'da eksik olan manifest FIX-ID'lerini ekle."""
    shutil.copytree(DENEME, kok)
    manifest = (kok / MANIFEST).read_text(encoding='utf-8')
    master_yolu = kok / MASTER
    master = master_yolu.read_text(encoding='utf-8')
    eksik = sorted(set(FIX_RE.findall(manifest)) - set(FIX_RE.findall(master)))
    if eksik:
        with master_yolu.open('a', encoding='utf-8') as f:
            f.write('\n' + '\n'.join(eksik) + '\n')


def senaryo(ad, kok, beklenen_rc, izler):
    """Bir senaryoyu kos ve rc ile cikti izlerini birlikte dogrula."""
    rc, cikti = calistir(kok)
    sorun = []
    if rc != beklenen_rc:
        sorun.append('rc=%r, beklenen=%d' % (rc, beklenen_rc))
    for iz in izler:
        if iz not in cikti:
            sorun.append('cikti %r icermiyor' % iz)
    if sorun:
        print('KALDI %s: %s' % (ad, '; '.join(sorun)))
        for satir in cikti.splitlines()[-12:]:
            print('  | %s' % satir)
        return False
    print('GECTI %s: rc=%d · izler=%s' % (ad, rc, ', '.join(izler)))
    return True


def main():
    if not DENEME.is_dir():
        print('KALDI kurulum: DENEME/ dizini yok: %s' % DENEME)
        return 1

    with tempfile.TemporaryDirectory(prefix='atlas-demo-oztest-') as tmp:
        gecici = Path(tmp)
        yesil = gecici / 'yesil'
        bozuk = gecici / 'bozuk'
        try:
            yesil_kur(yesil)
            shutil.copytree(yesil, bozuk)
            (bozuk / GATE).unlink()
        except OSError as e:
            print('KALDI kurulum: gecici fikstur olusturulamadi: %s' % e)
            return 1

        sonuclar = [
            senaryo('yesil', yesil, 0, ('YESIL', 'HUKUM: PASS')),
            senaryo('bozuk', bozuk, 2, ('FIKSTUR DEGISTI', 'DEMO KIRIK')),
        ]

    gecen = sum(1 for s in sonuclar if s)
    print('SONUC: %d/2 senaryo gecti' % gecen)
    if gecen == 2:
        print('HUKUM: PASS — demo 0/2 sozlesmesi gecici fiksturlerle dogrulandi.')
        return 0
    print('HUKUM: FAIL — demo 0/2 sozlesmesi beklenen kodlari vermedi.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
