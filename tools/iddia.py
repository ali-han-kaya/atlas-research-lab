#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iddia.py — public sayisal iddialari kendi kaynagindan yeniden olcer.

NEDEN VAR: README ve docs icindeki sayilar betiklerden gelir, ama betikten
belgeye aktarim elle yapilir; elle aktarilan sayi bayatlayabilir. Bu betik her
iddiayi gectigi dosyadaki BIREBIR cumleye baglar, onu ureten komutu kosar ve
beyan ile olcumu karsilastirir. Tutmayan satir kimligiyle (IDD-07) kirmizi
basilir ve rc=1 doner.

HAM KANIT: her OLCULDU satirinin son olculen ham cikti SATIRI
`tools/iddia_olcum.json` icinde ayni IDD-* anahtariyla saklanir. Varsayilan
kosu uc seyi birden ister:
  1. ham kanit satiri guncel komut ciktisinda BIREBIR ayni olmali,
  2. ham kanit kendi desenine uymali ve beyan edilen degeri vermeli,
  3. ham kanitin komutu/rc'si defterdeki satirla ayni olmali.
Kanit bayat veya bozuksa satir kirmizi olur; `--yaz` yeni anlik goruntuyu
uretir. Boylece iddia -> komut -> ham kanit zinciri defterden okunur.

DURUMLAR
  OLCULDU    komut kosar; ham kanit + desen + beklenen deger ucu de tutmali
  AG_GEREKLI ag ister; varsayilan kosuda ATLANIR, --ag ile olculur
  BEYAN      tarihli/makineye bagli kayit; yeniden kosulmaz, gerekce zorunlu
  OLCULMEDI  bu agacta yeniden uretilemez; gerekce zorunlu

YESILE ZORLAMA YOK: AG_GEREKLI, BEYAN ve OLCULMEDI satirlari PASS sayilmaz;
ozet satirinda ayri ayri sayilir, gerekceleri ve "ham kanit yok" durumu
yaninda basilir.

CIKIS: 0 = butun OLCULDU satirlari ham kanitiyla tuttu · 1 = en az bir iddia
       tutmadi (veya --yaz sirasinda bir satir kirmizi) · 2 = defter/olcum
       dosyasi bozuk (sema, dosya, alinti, eksik/fazla kanit)

KULLANIM
  python3 tools/iddia.py                  # agsiz dogrulama
  python3 tools/iddia.py --kanit          # her PASS satirinin ham kanitini da bas
  python3 tools/iddia.py --ag             # ag gerektiren satirlari da olc
  python3 tools/iddia.py --sadece IDD-01,IDD-24
  python3 tools/iddia.py --yaz            # ham kanit anlik goruntusunu yenile
"""
import concurrent.futures
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / 'tools' / 'iddia_defteri.json'
OLCUM = KOK / 'tools' / 'iddia_olcum.json'
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


def olcum_yukle(gerekli=True):
    if not OLCUM.is_file():
        if gerekli:
            raise DefterHatasi('%s yok — `make iddia-yaz` ile uretin'
                               % OLCUM.relative_to(KOK))
        return {'olcumler': {}}
    try:
        veri = json.loads(OLCUM.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise DefterHatasi('olcum dosyasi okunamadi: %s' % e)
    if not isinstance(veri, dict) or not isinstance(veri.get('olcumler'), dict):
        raise DefterHatasi('olcum semasi: "olcumler" nesnesi yok')
    return veri


def denetle_olcum(defter, olcum):
    """OLCULDU kumesi ile ham kanit kumesi birebir ayni olmali: eksik kanit da
    fazla (bayat) kanit da kabul edilmez."""
    kayitlar = olcum['olcumler']
    beklenen = {k['id'] for k in defter['iddialar'] if k['durum'] == 'OLCULDU'}
    fazla = set(kayitlar) - beklenen
    if fazla:
        raise DefterHatasi('olcum dosyasinda defterde olmayan kayit: %s'
                           % ', '.join(sorted(fazla)))
    eksik = beklenen - set(kayitlar)
    if eksik:
        raise DefterHatasi('OLCULDU satiri icin ham kanit yok: %s — '
                           '`make iddia-yaz`' % ', '.join(sorted(eksik)))
    for eid, kanit in kayitlar.items():
        if not isinstance(kanit, dict):
            raise DefterHatasi('%s: olcum kaydi nesne degil' % eid)
        for alan in ('komut', 'rc', 'ham', 'deger'):
            if alan not in kanit:
                raise DefterHatasi('%s: olcum kaydinda "%s" yok' % (eid, alan))
        if not isinstance(kanit['ham'], str) or not kanit['ham'].strip():
            raise DefterHatasi('%s: ham kanit bos' % eid)
        if not isinstance(kanit['komut'], list):
            raise DefterHatasi('%s: ham kanit komutu liste degil' % eid)


def _komut_calistir(argv):
    gercek = [sys.executable if a == '{py}' else a for a in argv]
    try:
        sonuc = subprocess.run(gercek, cwd=str(KOK), capture_output=True,
                               text=True, timeout=ZAMAN_ASIMI)
        return (sonuc.returncode, (sonuc.stdout or '') + (sonuc.stderr or ''))
    except subprocess.TimeoutExpired:
        return (124, 'ZAMAN ASIMI (%d s)' % ZAMAN_ASIMI)
    except OSError as e:
        return (125, 'KOSULAMADI: %s' % e)


def komut_kos(argv, onbellek):
    anahtar = tuple(argv)
    if anahtar in onbellek:
        return onbellek[anahtar]
    kayit = _komut_calistir(argv)
    onbellek[anahtar] = kayit
    return kayit


def _tekil_komutlar(defter, sadece, ag, yaz):
    """Ayni olcum komutunu bir kez kos; defter sirasini koru."""
    komutlar = []
    gorulen = set()
    for kayit in defter['iddialar']:
        if sadece and kayit['id'] not in sadece:
            continue
        durum = kayit['durum']
        if durum == 'OLCULDU' or (durum == 'AG_GEREKLI' and ag and not yaz):
            anahtar = tuple(kayit['komut'])
            if anahtar not in gorulen:
                gorulen.add(anahtar)
                komutlar.append(anahtar)
    return komutlar


def _paralel_olc(komutlar, onbellek):
    """Bagimsiz olcumleri paralel kos; cikti sirasi defter sirasinda kalir."""
    if not komutlar:
        return
    with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(4, len(komutlar))) as havuz:
        gelecekler = {anahtar: havuz.submit(_komut_calistir, list(anahtar))
                      for anahtar in komutlar}
        for anahtar, gelecek in gelecekler.items():
            onbellek[anahtar] = gelecek.result()


def taze(kayit, onbellek):
    """(gecti, deger, ayrinti, ham_satir, rc) — komut + desen + beklenen."""
    rc, cikti = komut_kos(kayit['komut'], onbellek)
    eslesme = re.search(kayit['ayikla'], cikti)
    if not eslesme:
        return False, '-', 'desen bulunamadi (rc=%d)' % rc, '', rc
    parcalar = [g for g in eslesme.groups() if g is not None]
    deger = '/'.join(parcalar)
    satir = cikti.splitlines()[cikti[:eslesme.start()].count('\n')]
    # Bazi ham kanit satirlari commit/tree gibi degisken provenance tasir;
    # ham_grup yalniz eslesen sayisal parcayi saklar, iddia zayiflamaz.
    if kayit.get('ham_grup'):
        satir = eslesme.group(0)
    beklenen_rc = int(kayit.get('rc_beklenen', 0))
    if rc != beklenen_rc:
        return False, deger, 'rc=%d (beklenen %d)' % (rc, beklenen_rc), satir, rc
    if deger != kayit['beklenen']:
        return False, deger, ('beyan %s, olcum %s'
                              % (kayit['beklenen'], deger)), satir, rc
    return True, deger, '', satir, rc


def olc(kayit, onbellek, kanit):
    """Taze olcum + saklanan ham kanit. Uc celiski de kirmizi sayilir."""
    gecti, deger, ayrinti, satir, rc = taze(kayit, onbellek)
    if not gecti:
        return False, deger, ayrinti
    if kanit['komut'] != kayit['komut']:
        return False, deger, 'ham kanit farkli komuttan uretilmis'
    if int(kanit['rc']) != rc:
        return False, deger, ('ham kanit rc=%s, guncel rc=%d'
                              % (kanit['rc'], rc))
    if kanit['deger'] != kayit['beklenen']:
        return False, deger, ('ham kanit degeri %s, beyan %s'
                              % (kanit['deger'], kayit['beklenen']))
    eslesme = re.search(kayit['ayikla'], kanit['ham'])
    if not eslesme:
        return False, deger, 'ham kanit kendi desenine uymuyor'
    ham_deger = '/'.join(g for g in eslesme.groups() if g is not None)
    if ham_deger != kayit['beklenen']:
        return False, deger, ('ham kanit beyanla celisiyor: %s != %s'
                              % (ham_deger, kayit['beklenen']))
    if kanit['ham'] != satir:
        return False, deger, ('ham kanit guncel cikti satiriyla ayni degil — '
                              'make iddia-yaz')
    return True, deger, ''


def _kisa(metin, sinir=64):
    metin = ' '.join(str(metin).split())
    return metin if len(metin) <= sinir else metin[:sinir - 1] + '…'


def main(argv):
    ag = '--ag' in argv
    yaz = '--yaz' in argv
    kanit_goster = '--kanit' in argv
    sadece = set()
    for i, arg in enumerate(argv):
        if arg == '--sadece' and i + 1 < len(argv):
            sadece = {x.strip() for x in argv[i + 1].split(',') if x.strip()}
    if yaz and sadece:
        print('DEFTER BOZUK: --yaz ile --sadece birlikte kullanilamaz')
        print('HUKUM: DEFTER BOZUK — hicbir iddia olculmedi')
        return 2
    try:
        defter = yukle()
        denetle(defter)
        if yaz:
            olcum = {'olcumler': {}}
        else:
            olcum = olcum_yukle(gerekli=True)
            denetle_olcum(defter, olcum)
    except DefterHatasi as e:
        print('DEFTER BOZUK: %s' % e)
        print('IDDIA FAIL — defter: %s' % e)
        print('HUKUM: DEFTER BOZUK — hicbir iddia olculmedi')
        return 2

    kapsam = defter.get('kapsam') or {}
    print('ATLAS — iddia defteri · %s' % DEFTER.relative_to(KOK))
    print('ham kanit: %s' % OLCUM.relative_to(KOK))
    print('kapsam: %s' % ' · '.join(kapsam.get('dahil') or []))
    for haric in kapsam.get('haric') or []:
        print('  haric: %s — %s' % (haric.get('desen'), haric.get('neden')))
    if sadece:
        print('filtre: %s' % ', '.join(sorted(sadece)))
    if yaz:
        print('kip: YAZ — ham kanit anlik goruntusu yenilenecek')
    print()

    onbellek = {}
    komutlar = _tekil_komutlar(defter, sadece, ag, yaz)
    if komutlar:
        print('  olcum: %d tekil komut paralel kosuldu' % len(komutlar))
    _paralel_olc(komutlar, onbellek)
    satirlar = []
    yeni_olcum = {}
    for kayit in defter['iddialar']:
        eid = kayit['id']
        if sadece and eid not in sadece:
            continue
        durum = kayit['durum']
        ilk_kaynak = kayit['kaynaklar'][0]['dosya']
        kanit_metni = ''
        if durum == 'OLCULDU':
            if yaz:
                gecti, deger, ayrinti, ham, rc = taze(kayit, onbellek)
                if gecti:
                    yeni_olcum[eid] = {'komut': kayit['komut'], 'rc': rc,
                                       'ham': ham, 'deger': deger}
                    kanit_metni = ham
            else:
                gecti, deger, ayrinti = olc(kayit, onbellek,
                                            olcum['olcumler'][eid])
                if gecti:
                    kanit_metni = olcum['olcumler'][eid]['ham']
            etiket = 'PASS' if gecti else 'FAIL'
            not_metni = ayrinti or ('= %s' % kayit['beklenen'])
            satirlar.append((etiket, eid, kayit['iddia'], deger, not_metni,
                             ilk_kaynak, durum, kanit_metni))
        elif durum == 'AG_GEREKLI' and ag:
            # Canli olcumun kalici ham kaniti yoktur; --ag anlik olcer.
            gecti, deger, ayrinti, ham, _rc = taze(kayit, onbellek)
            etiket = 'PASS' if gecti else 'FAIL'
            not_metni = ayrinti or ('= %s (canli)' % kayit['beklenen'])
            satirlar.append((etiket, eid, kayit['iddia'], deger, not_metni,
                             ilk_kaynak, durum, ham if gecti else ''))
        elif durum == 'AG_GEREKLI':
            satirlar.append(('AG', eid, kayit['iddia'], '—',
                             'ham kanit yok (ag gerekli) — kosulmadi',
                             ilk_kaynak, durum, ''))
        elif durum == 'BEYAN':
            satirlar.append(('BEYAN', eid, kayit['iddia'], '—',
                             'ham kanit yok (beyan) — %s'
                             % _kisa(kayit['gerekce'], 58),
                             ilk_kaynak, durum, ''))
        else:
            satirlar.append(('OLCULMEDI', eid, kayit['iddia'], '—',
                             'ham kanit yok (olculmedi) — %s'
                             % _kisa(kayit['gerekce'], 54),
                             ilk_kaynak, durum, ''))

    for etiket, eid, iddia, deger, not_metni, dosya, _durum, kanit in satirlar:
        print('  %-9s %-7s %-34s %-12s %s'
              % (etiket, eid, _kisa(iddia, 34), deger, not_metni))
        print('  %-9s %-7s kaynak: %s' % ('', '', dosya))
        if kanit_goster and kanit:
            print('  %-9s %-7s kanit: %s' % ('', '', _kisa(kanit, 120)))

    olculen = [s for s in satirlar if s[0] in ('PASS', 'FAIL')]
    kalan = [s for s in satirlar if s[0] == 'FAIL']

    if kalan:
        beklenenler = {k['id']: k.get('beklenen', '—')
                       for k in defter['iddialar']}
        kaynaklar = {}
        for kayit in defter['iddialar']:
            kaynaklar[kayit['id']] = ', '.join(dict.fromkeys(
                x['dosya'] for x in kayit['kaynaklar']))
        print('IDDIA FAIL — ' + ' | '.join(
            '%s: beyan=%s · olcum=%s · kaynak=%s · %s'
            % (s[1], beklenenler.get(s[1], '—'), s[3],
               kaynaklar.get(s[1], '—'), s[4]) for s in kalan))
    ag_sayisi = len([s for s in satirlar if s[0] == 'AG'])
    beyan = len([s for s in satirlar if s[0] == 'BEYAN'])
    olculmedi = len([s for s in satirlar if s[0] == 'OLCULMEDI'])

    print()
    print('  olculdu=%d · gecen=%d · kalan=%d · ag=%d · beyan=%d · olculmedi=%d'
          % (len(olculen), len(olculen) - len(kalan), len(kalan), ag_sayisi,
             beyan, olculmedi))
    if yaz:
        if kalan:
            print('  HUKUM: FAIL — ham kanit yazilmadi: %s'
                  % ', '.join(s[1] for s in kalan))
            for s in kalan:
                print('    · %s: %s' % (s[1], s[4]))
            return 1
        veri = {
            '_aciklama': ('Her OLCULDU iddiasinin son olculen HAM cikti satiri. '
                          'tools/iddia.py bu satirin guncel komut ciktisinda '
                          'birebir ayni olmasini ve beyanla tutmasini ister.'),
            'zaman': datetime.datetime.now(datetime.timezone.utc)
                             .strftime('%Y-%m-%dT%H:%M:%SZ'),
            'olcumler': yeni_olcum,
        }
        OLCUM.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + '\n',
                         encoding='utf-8')
        print('  HAM KANIT YAZILDI: %s (%d satir)'
              % (OLCUM.relative_to(KOK), len(yeni_olcum)))
        return 0
    if kalan:
        print('  HUKUM: FAIL — %s' % ', '.join(s[1] for s in kalan))
        for s in kalan:
            print('    · %s: %s' % (s[1], s[4]))
        return 1
    if not olculen:
        print('  HUKUM: OLCULMEDI — filtrelenen defterde OLCULDU satiri yok')
        return 2
    print('  HUKUM: PASS — %d/%d olculen iddia ham kanitiyla beyanla ayni'
          % (len(olculen) - len(kalan), len(olculen)))
    if ag_sayisi or beyan or olculmedi:
        print('  NOT: %d ag, %d beyan, %d olculmedi ayri sayildi — PASS degil.'
              % (ag_sayisi, beyan, olculmedi))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
