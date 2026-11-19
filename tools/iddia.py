#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iddia.py — public sayisal iddialari kendi kaynagindan yeniden olcer.

NEDEN VAR: README ve docs icindeki sayilar betiklerden gelir, ama betikten
belgeye aktarim elle yapilir; elle aktarilan sayi bayatlayabilir. Bu betik her
iddiayi gectigi dosyadaki BIREBIR cumleye baglar, onu ureten komutu kosar ve
beyan ile olcumu karsilastirir. Tutmayan satir kimligiyle (IDD-07) kirmizi
basilir ve rc=1 doner.

DURUMLAR
  OLCULDU    komut kosar; cikti deseni beklenen degerle ayni olmali
  AG_GEREKLI ag ister; varsayilan kosuda ATLANIR, --ag ile olculur
  BEYAN      tarihli/makineye bagli kayit; yeniden kosulmaz, gerekce zorunlu
  OLCULMEDI  bu agacta yeniden uretilemez; gerekce zorunlu

YESILE ZORLAMA YOK: AG_GEREKLI, BEYAN ve OLCULMEDI satirlari PASS sayilmaz;
ozet satirinda ayri ayri sayilir ve gerekceleri yaninda basilir.

CIKIS: 0 = butun OLCULDU satirlari beyanla ayni · 1 = en az bir iddia tutmadi
       (veya komut/desen basarisiz) · 2 = defter bozuk (sema, dosya, alinti)

KULLANIM
  python3 tools/iddia.py              # agsiz tam kosu
  python3 tools/iddia.py --ag         # ag gerektiren satirlari da olc
  python3 tools/iddia.py --sadece IDD-01,IDD-24
"""
import json
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / 'tools' / 'iddia_defteri.json'
ZAMAN_ASIMI = 600
DURUMLAR = ('OLCULDU', 'AG_GEREKLI', 'BEYAN', 'OLCULMEDI')


class DefterHatasi(Exception):
    pass


def _metin(yol):
    try:
        return (KOK / yol).read_text(encoding='utf-8')
    except OSError as e:
        raise DefterHatasi('%s okunamadi: %s' % (yol, e))


def yukle():
    try:
        defter = json.loads(DEFTER.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise DefterHatasi('defter okunamadi: %s' % e)
    if not isinstance(defter, dict) or not isinstance(defter.get('iddialar'), list):
        raise DefterHatasi('sema: "iddialar" listesi yok')
    if not defter['iddialar']:
        raise DefterHatasi('sema: defter bos')
    return defter


def denetle(defter):
    """Sema + alinti dogrulamasi. Alinti dosyada birebir yoksa defter bozuktur:
    uydurulmus iddia metni kapiya giremez."""
    kimlikler = set()
    for sira, kayit in enumerate(defter['iddialar'], 1):
        yer = 'kayit %d' % sira
        if not isinstance(kayit, dict):
            raise DefterHatasi('%s: nesne degil' % yer)
        for alan in ('id', 'iddia', 'durum', 'kaynaklar'):
            if alan not in kayit:
                raise DefterHatasi('%s: "%s" alani yok' % (yer, alan))
        eid = kayit['id']
        if not re.match(r'^IDD-\d{2,3}$', str(eid)):
            raise DefterHatasi('%s: gecersiz id: %r' % (yer, eid))
        if eid in kimlikler:
            raise DefterHatasi('%s: yinelenen id: %s' % (yer, eid))
        kimlikler.add(eid)
        if kayit['durum'] not in DURUMLAR:
            raise DefterHatasi('%s (%s): gecersiz durum: %r'
                               % (yer, eid, kayit['durum']))
        kaynaklar = kayit['kaynaklar']
        if not isinstance(kaynaklar, list) or not kaynaklar:
            raise DefterHatasi('%s (%s): kaynak yok' % (yer, eid))
        for kaynak in kaynaklar:
            if not isinstance(kaynak, dict) or not kaynak.get('dosya') \
                    or not kaynak.get('alinti'):
                raise DefterHatasi('%s (%s): kaynak dosya/alinti eksik'
                                   % (yer, eid))
            metin = _metin(kaynak['dosya'])
            if kaynak['alinti'] not in metin:
                raise DefterHatasi(
                    '%s (%s): alinti %s icinde birebir yok: %r'
                    % (yer, eid, kaynak['dosya'], kaynak['alinti'][:70]))
        if kayit['durum'] in ('OLCULDU', 'AG_GEREKLI'):
            komut = kayit.get('komut')
            if not (isinstance(komut, list) and komut
                    and all(isinstance(a, str) for a in komut)):
                raise DefterHatasi('%s (%s): komut listesi yok' % (yer, eid))
            desen = kayit.get('ayikla')
            if not isinstance(desen, str) or not desen:
                raise DefterHatasi('%s (%s): ayikla deseni yok' % (yer, eid))
            try:
                rx = re.compile(desen, re.MULTILINE)
            except re.error as e:
                raise DefterHatasi('%s (%s): desen bozuk: %s' % (yer, eid, e))
            if rx.groups < 1:
                raise DefterHatasi('%s (%s): desende yakalama grubu yok'
                                   % (yer, eid))
            if not isinstance(kayit.get('beklenen'), str):
                raise DefterHatasi('%s (%s): beklenen deger yok' % (yer, eid))
        elif not kayit.get('gerekce'):
            raise DefterHatasi('%s (%s): %s icin gerekce zorunlu'
                               % (yer, eid, kayit['durum']))


def komut_kos(argv, onbellek):
    anahtar = tuple(argv)
    if anahtar in onbellek:
        return onbellek[anahtar]
    gercek = [sys.executable if a == '{py}' else a for a in argv]
    try:
        sonuc = subprocess.run(gercek, cwd=str(KOK), capture_output=True,
                               text=True, timeout=ZAMAN_ASIMI)
        kayit = (sonuc.returncode, (sonuc.stdout or '') + (sonuc.stderr or ''))
    except subprocess.TimeoutExpired:
        kayit = (124, 'ZAMAN ASIMI (%d s)' % ZAMAN_ASIMI)
    except OSError as e:
        kayit = (125, 'KOSULAMADI: %s' % e)
    onbellek[anahtar] = kayit
    return kayit


def olc(kayit, onbellek):
    """(gecti, deger, ayrinti) — desen yoksa/rc saparsa/deger tutmazsa FAIL."""
    rc, cikti = komut_kos(kayit['komut'], onbellek)
    eslesme = re.search(kayit['ayikla'], cikti)
    if not eslesme:
        return False, '-', 'desen bulunamadi (rc=%d)' % rc
    parcalar = [g for g in eslesme.groups() if g is not None]
    deger = '/'.join(parcalar)
    beklenen_rc = int(kayit.get('rc_beklenen', 0))
    if rc != beklenen_rc:
        return False, deger, 'rc=%d (beklenen %d)' % (rc, beklenen_rc)
    if deger != kayit['beklenen']:
        return False, deger, 'beyan %s, olcum %s' % (kayit['beklenen'], deger)
    return True, deger, ''


def _kisa(metin, sinir=64):
    metin = ' '.join(str(metin).split())
    return metin if len(metin) <= sinir else metin[:sinir - 1] + '…'


def main(argv):
    ag = '--ag' in argv
    sadece = set()
    for i, arg in enumerate(argv):
        if arg == '--sadece' and i + 1 < len(argv):
            sadece = {x.strip() for x in argv[i + 1].split(',') if x.strip()}
    try:
        defter = yukle()
        denetle(defter)
    except DefterHatasi as e:
        print('DEFTER BOZUK: %s' % e)
        print('HUKUM: DEFTER BOZUK — hicbir iddia olculmedi')
        return 2

    kapsam = defter.get('kapsam') or {}
    print('ATLAS — iddia defteri · %s' % DEFTER.relative_to(KOK))
    print('kapsam: %s' % ' · '.join(kapsam.get('dahil') or []))
    for haric in kapsam.get('haric') or []:
        print('  haric: %s — %s' % (haric.get('desen'), haric.get('neden')))
    if sadece:
        print('filtre: %s' % ', '.join(sorted(sadece)))
    print()

    onbellek = {}
    satirlar = []
    for kayit in defter['iddialar']:
        eid = kayit['id']
        if sadece and eid not in sadece:
            continue
        durum = kayit['durum']
        ilk_kaynak = kayit['kaynaklar'][0]['dosya']
        if durum == 'OLCULDU' or (durum == 'AG_GEREKLI' and ag):
            gecti, deger, ayrinti = olc(kayit, onbellek)
            etiket = 'PASS' if gecti else 'FAIL'
            not_metni = ayrinti or ('= %s' % kayit['beklenen'])
            satirlar.append((etiket, eid, kayit['iddia'], deger, not_metni,
                             ilk_kaynak, durum))
        elif durum == 'AG_GEREKLI':
            satirlar.append(('AG', eid, kayit['iddia'],
                             '—', 'ag gerekli — kosulmadi', ilk_kaynak, durum))
        elif durum == 'BEYAN':
            satirlar.append(('BEYAN', eid, kayit['iddia'],
                             '—', _kisa(kayit['gerekce'], 70), ilk_kaynak, durum))
        else:
            satirlar.append(('OLCULMEDI', eid, kayit['iddia'],
                             '—', _kisa(kayit['gerekce'], 70), ilk_kaynak, durum))

    for etiket, eid, iddia, deger, not_metni, dosya, _durum in satirlar:
        print('  %-9s %-7s %-34s %-12s %s'
              % (etiket, eid, _kisa(iddia, 34), deger, not_metni))
        print('  %-9s %-7s %s' % ('', '', 'kaynak: %s' % dosya))

    olculen = [s for s in satirlar if s[0] in ('PASS', 'FAIL')]
    kalan = [s for s in satirlar if s[0] == 'FAIL']
    ag_sayisi = len([s for s in satirlar if s[0] == 'AG'])
    beyan = len([s for s in satirlar if s[0] == 'BEYAN'])
    olculmedi = len([s for s in satirlar if s[0] == 'OLCULMEDI'])

    print()
    print('  olculdu=%d · gecen=%d · kalan=%d · ag=%d · beyan=%d · olculmedi=%d'
          % (len(olculen), len(olculen) - len(kalan), len(kalan), ag_sayisi,
             beyan, olculmedi))
    if kalan:
        print('  HUKUM: FAIL — %s' % ', '.join(s[1] for s in kalan))
        for s in kalan:
            print('    · %s: %s' % (s[1], s[4]))
        return 1
    if not olculen:
        print('  HUKUM: OLCULMEDI — filtrelenen defterde OLCULDU satiri yok')
        return 2
    print('  HUKUM: PASS — %d/%d olculen iddia beyanla ayni'
          % (len(olculen) - len(kalan), len(olculen)))
    if ag_sayisi or beyan or olculmedi:
        print('  NOT: %d ag, %d beyan, %d olculmedi ayri sayildi — PASS degil.'
              % (ag_sayisi, beyan, olculmedi))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
