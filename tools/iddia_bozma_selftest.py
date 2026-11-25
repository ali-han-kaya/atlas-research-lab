#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iddia_bozma_selftest — gercek depo kopyasinda IDD-04'u boz, kapiyi kirmizi gor.

NEDEN VAR
  Kapiyi "gercekten yakaliyor mu" diye sinamanin en dogrudan yolu, gercek
  defteri bozup gercek kapinin kirmizi yandigini gormektir. Bunu main uzerinde
  yapmak TEST commit'leri birakir. Bu arac isi GECICI KOPYADA yapar:
  ana agac okunur, kopya bozulur, kapi kopyada kosar, kopya silinir.

  Iki vaka:
    1. KANITSIZ  — IDD-04'un ham kanit satiri kopyadan silinir. Kapi komut
                   kosmadan, `DEFTER BOZUK` ile rc=2 vermelidir (hizli vaka).
    2. BEYAN     — IDD-04'un beklenen degeri 999/999 yapilir. Bu ancak gercek
                   kosuyla yakalanir; kapi rc=1 ile `beyan=999/999` demelidir.
                   `--hizli` bu agir vakayi atlar ve OLCULMEDI basar.

  Her iki vakadan sonra ana agacin `git status` ciktisi degismemis olmalidir:
  "main gecmisi temiz kalir" iddiasi olcumle dogrulanir, sozle degil.

KULLANIM
  python3 tools/iddia_bozma_selftest.py            # iki vaka (agir dahil)
  python3 tools/iddia_bozma_selftest.py --hizli    # yalniz kanitsiz vaka

CIKIS: 0 = iki vaka da beklendigi gibi kirmizi · 1 = beklenti tutmadi
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
HEDEF = 'IDD-04'


DEFTERLER = ('tools/iddia_defteri.json', 'tools/iddia_olcum.json')


def _imza():
    """Ana agacin DOKUNULMAMASI gereken izleri.

    Tum agacin `git status`'u degil, aracin yazabilecegi iki defterin icerigi
    ve HEAD karsilastirilir. Boylece baska birinin eszamanli duzenlemesi bu
    vakanin kirmizisi gibi gorunmez; buna karsilik gecmisin (HEAD) ve
    defterlerin degismedigi kesin olarak olculur.
    """
    import hashlib
    iz = {}
    for rel in DEFTERLER:
        p = KOK / rel
        iz[rel] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else '<yok>'
    r = subprocess.run(['git', '-C', str(KOK), 'rev-parse', 'HEAD'],
                       capture_output=True, text=True)
    iz['HEAD'] = r.stdout.strip() if r.returncode == 0 else '<okunamadi>'
    return iz


def _kopya(tmp):
    """Commit'li agacin klonu — CI checkout'uyla ayni gorunum.

    Klasor kopyasi YETMEZ: bazi kapilar (or. `model_kimlik`) git kokunde
    `git ls-files` kullanir, `.git` olmayan kopyada dosya sistemini tarar ve
    sayilar tutmaz; o zaman kapi alakasiz bir satirdan kirmizi yanar ve vaka
    kaniti bulanir. Klon, izlenen agaci birebir getirir; `.gitignore` edilmis
    calisma dizinleri (or. `kanit-paketi/`) CI'da da yoktur.

    Sonuc: commit edilmemis degisiklikler kapsam disidir; kanit, commit'li
    agacin kanitidir.
    """
    hedef = tmp / 'depo'
    hedef.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks',
                        str(KOK), str(hedef)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('klon kurulamadi: %s'
                           % ((r.stderr or r.stdout).strip()[:200]))
    return hedef


def _kos(kopya, zaman_asimi):
    basladi = time.time()
    r = subprocess.run([sys.executable, 'tools/iddia.py'], cwd=str(kopya),
                       capture_output=True, text=True, timeout=zaman_asimi)
    return r.returncode, (r.stdout or '') + (r.stderr or ''), time.time() - basladi


def _defter_oku(kopya):
    return json.loads((kopya / 'tools' / 'iddia_defteri.json')
                      .read_text(encoding='utf-8'))


def _defter_yaz(kopya, veri):
    (kopya / 'tools' / 'iddia_defteri.json').write_text(
        json.dumps(veri, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def vaka_kanitsiz(tmp, zaman_asimi):
    """Ham kanit satiri silinince kapi komut kosmadan kirmizi olmali."""
    kopya = _kopya(tmp)
    yol = kopya / 'tools' / 'iddia_olcum.json'
    veri = json.loads(yol.read_text(encoding='utf-8'))
    if HEDEF not in veri['olcumler']:
        return False, '%s kaydi zaten yok; vaka kurulamadi' % HEDEF, 0.0
    veri['olcumler'].pop(HEDEF)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')
    rc, cikti, sure = _kos(kopya, zaman_asimi)
    if rc != 2:
        return False, 'rc=%d (beklenen 2) · %s' % (rc, cikti.strip()[-200:]), sure
    if 'DEFTER BOZUK' not in cikti or 'ham kanit yok' not in cikti:
        return False, 'DEFTER BOZUK/ham kanit yok izi yok · %s' % cikti.strip()[-200:], sure
    if HEDEF not in cikti:
        return False, 'kirmizi cikti %s adini basmiyor' % HEDEF, sure
    return True, 'rc=2 · DEFTER BOZUK · %s adlandirildi' % HEDEF, sure


def vaka_beyan(tmp, zaman_asimi):
    """Beklenen deger bozulunca gercek kosu kirmizi olmali ve beyani basmali."""
    kopya = _kopya(tmp)
    defter = _defter_oku(kopya)
    kayit = next((k for k in defter['iddialar'] if k['id'] == HEDEF), None)
    if kayit is None:
        return False, '%s defterde yok; vaka kurulamadi' % HEDEF, 0.0
    gercek = kayit.get('beklenen')
    kayit['beklenen'] = '999/999'
    _defter_yaz(kopya, defter)
    rc, cikti, sure = _kos(kopya, zaman_asimi)
    if rc != 1:
        return False, 'rc=%d (beklenen 1) · %s' % (rc, cikti.strip()[-200:]), sure
    if '%s:' % HEDEF not in cikti:
        return False, 'kirmizi cikti %s adini basmiyor' % HEDEF, sure
    if 'beyan=999/999' not in cikti:
        return False, 'beyan=999/999 izi yok · %s' % cikti.strip()[-200:], sure
    if str(gercek) not in cikti:
        return False, 'olculen gercek deger (%s) ciktida yok' % gercek, sure
    return True, 'rc=1 · beyan=999/999 · olcum=%s' % gercek, sure


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--hizli', action='store_true',
                    help='agir (gercek kosu) vakayi atla')
    a = ap.parse_args(argv)

    once = _imza()
    sonuclar = []
    tmp = Path(tempfile.mkdtemp(prefix='iddia_bozma_'))
    try:
        print('IDDIA BOZMA OZ-TESTI — gecici kopyada gercek kapi')
        print('kaynak: %s' % KOK.name)
        print()

        ok, ayrinti, sure = vaka_kanitsiz(tmp / 'a', 300)
        sonuclar.append(('KANITSIZ (ham kanit silindi)', ok))
        print('  %-5s KANITSIZ (ham kanit silindi) %.1fs · %s'
              % ('PASS' if ok else 'FAIL', sure, ayrinti))

        if a.hizli:
            print('  ATLANDI BEYAN (beklenen 999/999) — agir vaka, --hizli')
        else:
            ok, ayrinti, sure = vaka_beyan(tmp / 'b', 1800)
            sonuclar.append(('BEYAN (beklenen 999/999)', ok))
            print('  %-5s BEYAN (beklenen 999/999) %.1fs · %s'
                  % ('PASS' if ok else 'FAIL', sure, ayrinti))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    sonra = _imza()
    temiz = (once == sonra)
    print()
    print('  ana agac: %s · HEAD=%s'
          % ('defterler ve gecmis degismedi' if temiz else 'DEGISTI!',
             sonra['HEAD'][:7]))
    if not temiz:
        for anahtar in sorted(set(once) | set(sonra)):
            if once.get(anahtar) != sonra.get(anahtar):
                print('    %s: %s -> %s' % (anahtar, str(once.get(anahtar))[:16],
                                          str(sonra.get(anahtar))[:16]))

    kirik = [ad for ad, ok in sonuclar if not ok]
    print('  vaka=%d · gecen=%d · kalan=%d'
          % (len(sonuclar), len(sonuclar) - len(kirik), len(kirik)))
    if kirik or not temiz:
        print('HUKUM: FAIL — %s'
              % (', '.join(kirik) if kirik else 'ana agac degisti'))
        return 1
    print('HUKUM: PASS — bozulan defter kirmizi yakildi; ana agac ve gecmis temiz.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
