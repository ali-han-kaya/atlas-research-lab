#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iddia.py — public sayisal iddialari kendi kaynagindan yeniden olcer.

NEDEN VAR: README ve docs icindeki sayilar betiklerden gelir, ama betikten
belgeye aktarim elle yapilir; elle aktarilan sayi bayatlayabilir. Bu betik her
iddiayi gectigi dosyadaki BIREBIR cumleye baglar, onu ureten komutu kosar ve
beyan ile olcumu karsilastirir. Tutmayan satir kimligiyle (IDD-07) kirmizi
basilir ve rc=1 doner.

HAM KANIT: her OLCULDU satirinin son olculen ham cikti SATIRI defterdeki
`olcum_dosyasi` yolunda (tek gecerli deger: `tools/iddia_olcum.json`) ayni
IDD-* anahtariyla saklanir; defter bu yolu adlandirir, betik dogrular.
Varsayilan kosu uc seyi birden ister:
  1. ham kanit satiri guncel komut ciktisinda BIREBIR ayni olmali,
  2. ham kanit kendi desenine uymali ve beyan edilen degeri vermeli,
  3. ham kanitin komutu/rc'si defterdeki satirla ayni olmali.
Kanit bayat veya bozuksa satir kirmizi olur; `--yaz` yeni anlik goruntuyu
uretir. Boylece iddia -> komut -> ham kanit zinciri defterden okunur.

DURUMLAR
  OLCULDU    komut kosar; ham kanit + desen + beklenen deger ucu de tutmali
  AG_GEREKLI ag ister; varsayilan kosuda ATLANIR, --ag ile olculur. --ag'da
  dis servis yoksa satir AG kalir ve exit 2 doner; sahte FAIL uretilmez.
  BEYAN      tarihli/makineye bagli kayit; yeniden kosulmaz, gerekce zorunlu
  OLCULMEDI  bu agacta yeniden uretilemez; gerekce zorunlu

YESILE ZORLAMA YOK: AG_GEREKLI, BEYAN ve OLCULMEDI satirlari PASS sayilmaz;
ozet satirinda ayri ayri sayilir, gerekceleri ve "ham kanit yok" durumu
yaninda basilir.

HIZLI KIP: --hizli, AGIR_BETIKLER'deki (dogrula, mutasyon) komutlari kosmaz;
bu satirlari ATLANDI basar ve PASS saymaz. --yaz ile birlesemez (kismi anlik
goruntu tam kaniti silerdi); varsayilan tam kosu aynen kalir.

KAPSAM KAPISI: defter yalniz kendi satirlarini degil kapsamini da denetler.
README.en.md, README.md, README.tr.md, docs/README.md ve docs/EN/QUICKSTART.md icindeki her sayisal olcum
iddiasi (oran `8/8`, olcum adi tasiyan sayi `116 vaka`, uretilmis sayac
`incelenmedi=0`) ya defterdeki bir alintinin icinde olmali ya da
`kapsam.sayisal_istisna` icindeki dar ve gerekceli bir desenle eslesmelidir.
Kimlik (KANIT-05), surum (v5.5.4), tarih (2026-11-19) ve cikis kodu (rc=1) bu
tanimin disindadir. Kapsanmayan tek bir iddia rc=2 ile kirmizi olur; hicbir
iddiayi kapsamayan olu istisna veya uc satirdan genis istisna da kirmizidir.

CIKIS: 0 = olculen OLCULDU satirlari ham kanitiyla tuttu (--hizli'da agir
       satirlar ATLANDI) · 1 = en az bir iddia tutmadi (veya --yaz sirasinda
       bir satir kirmizi) · 2 = defter/olcum dosyasi bozuk (sema, dosya,
       alinti, eksik/fazla kanit), kapsam istisnasi gecersiz, kapsanmayan
       sayisal iddia var veya hizli kipte olculecek satir yok

KULLANIM
  python3 tools/iddia.py                  # agsiz tam dogrulama
  python3 tools/iddia.py --hizli          # dogrula/mutasyon satirlarini atla
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
OZET_DOSYASI = KOK / 'docs' / 'IDDIA-OZET.md'
OZET_BASLA = '<!-- IDDIA-OZET:BASLA -->'
OZET_BITIR = '<!-- IDDIA-OZET:BITIR -->'
ZAMAN_ASIMI = 600
DURUMLAR = ('OLCULDU', 'AG_GEREKLI', 'BEYAN', 'OLCULMEDI')
# --hizli bu betikleri kosan satirlari atlar; varsayilan kosu hepsini olcer.
AGIR_BETIKLER = ('tools/dogrula.py', 'tools/mutasyon_bataryasi.py')
# Kapsam kapisi: bir istisna en fazla bu kadar satiri kapsayabilir. Daha genis
# bir desen, kapsami kapali degil acik hale getirir; bu yuzden kirmizidir.
AZAMI_ISTISNA_SATIR = 3

# Sayisal jeton: tarih, binlik ayiracli oran, surum, oran ve sade sayi.
# Harfe yapisik rakamlar (KANIT-05, KFAZ0, P0, UTF-8) jeton degildir.
KAPSAM_JETON = re.compile(r"""
    (?<![\w.])
    (?:
        \d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|
                       Eylül|Ekim|Kasım|Aralık|January|February|March|April|
                       May|June|July|August|September|October|November|
                       December)\s+\d{4}
      | \d{4}-\d{2}-\d{2}
      | \d{1,3}(?:\.\d{3})+(?:/\d{1,3}(?:\.\d{3})+)?
      | v?\d+(?:\.\d+)+
      | \d+/\d+(?:/\d+)?
      | \d+(?:[.,]\d+)?
    )
    (?!\w)
""", re.X)
TARIH_JETON = re.compile(
    r'^(?:\d{1,2}\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|'
    r'Eylül|Ekim|Kasım|Aralık|January|February|March|April|May|June|July|'
    r'August|September|October|November|December)\s+\d{4}|'
    r'\d{4}-\d{2}-\d{2})$', re.I)
# Olcum adi/birimi: sayinin yaninda (en fazla uc kelime) gorunurse jeton bir
# olcum iddiasidir. Sonuc sozcukleri (yeni/degisen/silinen/new/changed/deleted)
# yalniz hemen yanindaysa sayilir; "0 `olmadan` yeni" bir iddia degildir.
OLCUM_SOZCUK = re.compile(r"""
    \b(?:
        vaka|kural|dosya|bulgu|model|commit|kalem|test|sat[ıi]r|kay[ıi]t|rol|
        kenar|saniye|dakika|bayt|hata|kimlik|ajan|senaryo|ko[sş]um|
        gecen|kalan|ge[cç]|pass\b|fail\b|case|rule|file|finding|check|second|
        role|line|record|token|gate|kap[ıi]|lens|iddia|kan[ıi]t|
        s[ıi]n[ıi]r|limit|scope|gap|fix
    )\w*
  | %
""", re.X | re.I)
SONUC_SOZCUK = re.compile(r'^(?:yeni|degisen|silinen|new|changed|deleted)\b',
                          re.I)
# Uretilmis sayac alanlari: kalem=8, incelenmedi=0, planda=217 ...
SAYAC_ALAN = re.compile(
    r'(?<![A-Za-z0-9_])(?:kalem|gecen|kalan|calistirilmadi|olculdu|atlandi|'
    r'olculmedi|planda|yeni|degisen|ayni|silinecek|taranan|incelenmedi|'
    r'onay|aktif|aday|komut|dosya)=(\d+)')


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
    # Ham kanit yolu defterden okunur ve tek gecerli yola kilitlenir; boylece
    # iddia -> komut -> ham kanit zinciri defterin kendisinden izlenir.
    beklenen_olcum = OLCUM.relative_to(KOK).as_posix()
    if defter.get('olcum_dosyasi') != beklenen_olcum:
        raise DefterHatasi(
            'sema: olcum_dosyasi %r olmali, bulunan %r'
            % (beklenen_olcum, defter.get('olcum_dosyasi')))
    return defter


def ozet_satiri(defter):
    """Defterin durum dagilimini belgelenen tek satir biciminde dondur."""
    sayim = {durum: 0 for durum in DURUMLAR}
    for kayit in defter['iddialar']:
        sayim[kayit['durum']] += 1
    return ('olculdu=%d · ag=%d · beyan=%d · olculmedi=%d'
            % (sayim['OLCULDU'], sayim['AG_GEREKLI'],
               sayim['BEYAN'], sayim['OLCULMEDI']))


def ozet_denetle(defter):
    """Belgelenen ozet satiri defterin durum dagilimiyla birebir ayni olmali.
    Ozet otomatik yazilmaz; ayrisma sessiz kayma degil, rc=2 kirmizidir."""
    yol = OZET_DOSYASI.relative_to(KOK)
    try:
        metin = OZET_DOSYASI.read_text(encoding='utf-8')
    except OSError as e:
        raise DefterHatasi('%s okunamadi: %s' % (yol, e))
    if OZET_BASLA not in metin or OZET_BITIR not in metin:
        raise DefterHatasi('%s: %s ... %s blogu yok'
                           % (yol, OZET_BASLA, OZET_BITIR))
    blok = metin.split(OZET_BASLA, 1)[1].split(OZET_BITIR, 1)[0]
    satirlar = [s.strip() for s in blok.splitlines() if s.strip()]
    if len(satirlar) != 1:
        raise DefterHatasi('%s: ozet blogu tek satir olmali (bulunan=%d)'
                           % (yol, len(satirlar)))
    beklenen = ozet_satiri(defter)
    if satirlar[0] != beklenen:
        raise DefterHatasi('%s: ozet drift — belge %r, defter %r'
                           % (yol, satirlar[0], beklenen))
    return beklenen


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


def _anlamli_desen(desen):
    """Istisna deseni en az uc harf tasimali: `.*` ve `\d+` gibi genel
    desenler kapsami sessizce acamaz."""
    sade = re.sub(r'\\.', '', desen)
    sade = re.sub(r'\[[^\]]*\]', '', sade)
    return len(re.findall(r'[A-Za-zÇĞİÖŞÜçğıöşü]', sade)) >= 3


def _olcum_penceresi(satir, bas, son):
    """Jetonun iki yanindaki en fazla uc kelime; uzak bir olcum adi jetonu
    iddia yapmaz."""
    once = satir[:bas].split()[-3:]
    sonra = satir[son:].split()[:3]
    return ' '.join(once + sonra)


def _kimlik_mi(satir, bas):
    """KANIT-05, FIX-003, OLG-1, DEVIR-...-1945 gibi kimlik parcasi mi?
    Tirenden once buyuk harf ya da rakam varsa jeton kimlige aittir."""
    return (bas >= 2 and satir[bas - 1] == '-'
            and (satir[bas - 2].isupper() or satir[bas - 2].isdigit()))


def _protokol_mu(satir, bas, son):
    """2-of-2, KFAZ0-5 gibi protokol sabiti mi?"""
    dilim = satir[max(0, bas - 8):son + 8]
    return bool(re.search(r'\d+\s*[-–]\s*of\s*[-–]\s*\d+', dilim)
                or re.search(r'KFAZ0[–-]5', dilim))


def _cikis_kodu_mu(satir, bas, son):
    """rc=1, rc!=0, exit code 2, Exit 1 gibi cikis kodu degeri mi?"""
    once = satir[max(0, bas - 20):bas]
    return bool(re.search(r'(?:rc|exit(?:\s+code)?|kod\w*)\s*(?:[=!]=?)?\s*$',
                          once, re.I))


def _tablo_hucre_mi(satir, bas, son):
    """Tabloda yalin sayi hucresi mi? Cikis kodu tablolarinda deger sabittir;
    olcum iddiasi degildir. `52 s` gibi birimli hucre iddia olarak kalir."""
    if '|' not in satir:
        return False
    sol = satir.rfind('|', 0, bas)
    sag = satir.find('|', son)
    if sol == -1 or sag == -1:
        return False
    hucre = satir[sol + 1:sag].strip().strip('*` ')
    return hucre == satir[bas:son]


def _sira_numarasi_mi(satir, bas, son):
    """Markdown madde/shell case numarasi mi (1., 3., 0))?"""
    once = satir[:bas]
    if not once.strip() and satir[son:son + 1] in ('.', ')'):
        return True
    return bool(re.match(r'^#{1,6}\s+$', once)
                and satir[son:son + 1] == '.')


def _secenek_mi(satir, bas, son):
    """--limit=1, --depth 1, fetch-depth: 0 gibi komut secenegi mi?"""
    once = satir[max(0, bas - 28):bas]
    return bool(re.search(r'(?:--[\w-]+[= ]|fetch-depth:\s*)$', once))


def _iddia_mi(jeton, satir, bas, son):
    """Jeton bir sayisal olcum iddiasi mi? Kimlik, tarih, protokol sabiti,
    cikis kodu, tablo kodu, sira numarasi ve komut secenegi degilse; oran/
    yuzde, olcum adi yaninda, uretilmis sayac, dolar tutari veya N-vs-M ise
    evet."""
    if _kimlik_mi(satir, bas) or TARIH_JETON.match(jeton):
        return False
    if _protokol_mu(satir, bas, son) or _cikis_kodu_mu(satir, bas, son):
        return False
    if _tablo_hucre_mi(satir, bas, son) or _sira_numarasi_mi(satir, bas, son):
        return False
    if _secenek_mi(satir, bas, son):
        return False
    if '/' in jeton or satir[son:son + 1] == '%':
        return True
    if bas > 0 and satir[bas - 1] == '$':
        return True
    if re.match(r'-vs-\d', satir[son:son + 8]) or \
            re.search(r'\d-vs-$', satir[max(0, bas - 8):bas]):
        return True
    if re.match(r'\s+vs\.?\s+\d', satir[son:son + 10]) or \
            re.search(r'\d\s+vs\.?\s+$', satir[max(0, bas - 10):bas]):
        return True
    if re.match(r'\s*s\b', satir[son:son + 4]):
        return True
    if SONUC_SOZCUK.match(satir[son:].lstrip()):
        return True
    for eslesme in SAYAC_ALAN.finditer(satir):
        if eslesme.start(1) == bas and eslesme.end(1) == son:
            return True
    return bool(OLCUM_SOZCUK.search(_olcum_penceresi(satir, bas, son)))


def kapsam_denetle(defter):
    """Public dokumanlardaki her sayisal olcum iddiasini defterin alintilariyla
    ya da gerekceli, dar bir istisnayla eslestir. Eksik varsa hepsini dondur;
    istisna semasi bozuksa DefterHatasi yukselt (fail-closed)."""
    kapsam = defter.get('kapsam') or {}
    dosyalar = kapsam.get('dahil')
    if not (isinstance(dosyalar, list) and dosyalar
            and all(isinstance(d, str) and d for d in dosyalar)):
        raise DefterHatasi('kapsam.dahil: public dokuman listesi yok')
    istisnalar = kapsam.get('sayisal_istisna') or []
    if not isinstance(istisnalar, list):
        raise DefterHatasi('kapsam.sayisal_istisna: liste degil')
    kurallar = []
    for sira, kayit in enumerate(istisnalar, 1):
        yer = 'kapsam.sayisal_istisna[%d]' % sira
        if not isinstance(kayit, dict) or not kayit.get('desen') \
                or not kayit.get('neden'):
            raise DefterHatasi('%s: desen ve neden zorunlu' % yer)
        desen = kayit['desen']
        try:
            rx = re.compile(desen)
        except re.error as e:
            raise DefterHatasi('%s: desen bozuk: %s' % (yer, e))
        if not _anlamli_desen(desen):
            raise DefterHatasi('%s: desen cok genis — en az uc harf tasimali: '
                               '%r' % (yer, desen))
        kurallar.append({'rx': rx, 'desen': desen, 'satirlar': set(),
                         'kullanildi': 0})

    sayisal = kapsanan = istisna = 0
    eksikler = []
    for dosya in dosyalar:
        metin = _metin(dosya)
        kapali = bytearray(len(metin))
        for kayit in defter['iddialar']:
            for kaynak in kayit['kaynaklar']:
                if kaynak['dosya'] != dosya:
                    continue
                alinti = kaynak['alinti']
                bas = metin.find(alinti)
                while bas != -1:
                    kapali[bas:bas + len(alinti)] = b'\x01' * len(alinti)
                    bas = metin.find(alinti, bas + 1)
        ofset = 0
        for satir_no, satir in enumerate(metin.split('\n'), 1):
            for eslesme in KAPSAM_JETON.finditer(satir):
                jeton = eslesme.group(0)
                if not _iddia_mi(jeton, satir, eslesme.start(), eslesme.end()):
                    continue
                sayisal += 1
                bas = ofset + eslesme.start()
                son = ofset + eslesme.end()
                if all(kapali[bas:son]):
                    kapsanan += 1
                    continue
                for kural in kurallar:
                    if kural['rx'].search(satir):
                        kural['satirlar'].add((dosya, satir_no))
                        kural['kullanildi'] += 1
                        istisna += 1
                        break
                else:
                    eksikler.append((dosya, satir_no, jeton, satir.strip()))
            ofset += len(satir) + 1

    for kural in kurallar:
        if len(kural['satirlar']) > AZAMI_ISTISNA_SATIR:
            raise DefterHatasi(
                'kapsam.sayisal_istisna: %r cok genis — %d satiri kapsiyor '
                '(azami %d); kapsami daraltin'
                % (kural['desen'], len(kural['satirlar']),
                   AZAMI_ISTISNA_SATIR))
        if not kural['kullanildi']:
            raise DefterHatasi(
                'kapsam.sayisal_istisna: %r hicbir sayisal iddiayi '
                'kapsamiyor (olu istisna)' % kural['desen'])
    return {'dosyalar': dosyalar, 'sayisal': sayisal, 'kapsanan': kapsanan,
            'istisna': istisna, 'eksikler': eksikler}


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


def agir_mi(kayit):
    """--hizli kipte kosulmayacak pahali bir komut mu?"""
    return any(a.replace('\\', '/') in AGIR_BETIKLER
               for a in (kayit.get('komut') or []))


def denetle_olcum(defter, olcum, hizli=False):
    """OLCULDU kumesi ile ham kanit kumesi birebir ayni olmali: eksik kanit da
    fazla (bayat) kanit da kabul edilmez. --hizli'da kosulmayan agir satirin
    kaniti zorunlu degildir; varsa semasi yine denetlenir."""
    kayitlar = olcum['olcumler']
    tum = {k['id'] for k in defter['iddialar'] if k['durum'] == 'OLCULDU'}
    beklenen = {k['id'] for k in defter['iddialar']
                if k['durum'] == 'OLCULDU' and not (hizli and agir_mi(k))}
    fazla = set(kayitlar) - tum
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


def _tekil_komutlar(defter, sadece, ag, yaz, hizli=False):
    """Ayni olcum komutunu bir kez kos; defter sirasini koru."""
    komutlar = []
    gorulen = set()
    for kayit in defter['iddialar']:
        if sadece and kayit['id'] not in sadece:
            continue
        durum = kayit['durum']
        if hizli and durum == 'OLCULDU' and agir_mi(kayit):
            continue
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
        son = cikti.strip().splitlines()[-1] if cikti.strip() else ''
        ayrinti = 'desen bulunamadi (rc=%d)' % rc
        if son:
            ayrinti += ' · ' + son[:160]
        return False, '-', ayrinti, '', rc
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
    hizli = '--hizli' in argv
    kanit_goster = '--kanit' in argv
    sadece = set()
    for i, arg in enumerate(argv):
        if arg == '--sadece' and i + 1 < len(argv):
            sadece = {x.strip() for x in argv[i + 1].split(',') if x.strip()}
    if yaz and sadece:
        print('DEFTER BOZUK: --yaz ile --sadece birlikte kullanilamaz')
        print('HUKUM: DEFTER BOZUK — hicbir iddia olculmedi')
        return 2
    if yaz and hizli:
        print('DEFTER BOZUK: --yaz ile --hizli birlikte kullanilamaz — '
              'kismi anlik goruntu tam kaniti siler')
        print('HUKUM: DEFTER BOZUK — hicbir iddia olculmedi')
        return 2
    try:
        defter = yukle()
        denetle(defter)
        defter_ozeti = ozet_denetle(defter)
        if yaz:
            olcum = {'olcumler': {}}
        else:
            olcum = olcum_yukle(gerekli=True)
            denetle_olcum(defter, olcum, hizli)
    except DefterHatasi as e:
        print('DEFTER BOZUK: %s' % e)
        print('IDDIA FAIL — defter: %s' % e)
        print('HUKUM: DEFTER BOZUK — hicbir iddia olculmedi')
        return 2

    try:
        kapsam_denetimi = kapsam_denetle(defter)
    except DefterHatasi as e:
        print('KAPSAM BOZUK: %s' % e)
        print('HUKUM: KAPSAM BOZUK — kapsam istisnasi gecersiz')
        return 2

    kapsam = defter.get('kapsam') or {}
    print('ATLAS — iddia defteri · %s' % DEFTER.relative_to(KOK))
    print('defter ozeti: %s' % defter_ozeti)
    print('ham kanit: %s' % OLCUM.relative_to(KOK))
    print('kapsam: %s' % ' · '.join(kapsam_denetimi['dosyalar']))
    for haric in kapsam.get('haric') or []:
        print('  haric: %s — %s' % (haric.get('desen'), haric.get('neden')))
    print('sayisal kapsam: %d iddia · alintida=%d · istisnada=%d'
          % (kapsam_denetimi['sayisal'], kapsam_denetimi['kapsanan'],
             kapsam_denetimi['istisna']))
    if kapsam_denetimi['eksikler']:
        eksikler = kapsam_denetimi['eksikler']
        print()
        print('KAPSAM FAIL — %d sayisal iddia defterde ya da gerekceli '
              'istisnada yok:' % len(eksikler))
        for dosya, satir_no, jeton, metin in eksikler[:20]:
            print('  %s:%d · %r · %s'
                  % (dosya, satir_no, jeton, _kisa(metin, 96)))
        if len(eksikler) > 20:
            print('  ... ve %d tane daha' % (len(eksikler) - 20))
        print('  Cozum: iddiayi deftere satir olarak ekleyin (komut + alinti '
              '+ beklenen) veya kapsam.sayisal_istisna icinde dar bir desen '
              've gerekce tanimlayin.')
        print('HUKUM: KAPSAM BOZUK — public sayisal iddialar defterle '
              'eslesmiyor')
        return 2
    if sadece:
        print('filtre: %s' % ', '.join(sorted(sadece)))
    if yaz:
        print('kip: YAZ — ham kanit anlik goruntusu yenilenecek')
    elif hizli:
        print('kip: HIZLI — dogrula/mutasyon satirlari atlanir (PASS degil)')
    print()

    onbellek = {}
    komutlar = _tekil_komutlar(defter, sadece, ag, yaz, hizli)
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
        if durum == 'OLCULDU' and hizli and agir_mi(kayit):
            satirlar.append(('ATLANDI', eid, kayit['iddia'], '—',
                             'hizli kip — pahali komut kosulmadi (PASS degil)',
                             ilk_kaynak, durum, ''))
        elif durum == 'OLCULDU':
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
            # rc=2 dis servisin olculemedigini soyler; bunu sahte FAIL'e
            # cevirmeyiz, AG olarak ayirir ve exit 2 ile raporlariz.
            gecti, deger, ayrinti, ham, rc = taze(kayit, onbellek)
            if not gecti and rc == 2:
                satirlar.append(('AG', eid, kayit['iddia'], '—',
                                 'ag/dis servis yok — olculemedi · %s' % ayrinti,
                                 ilk_kaynak, durum, ''))
            else:
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
    atlandi = len([s for s in satirlar if s[0] == 'ATLANDI'])

    print()
    if hizli:
        print('  olculdu=%d · gecen=%d · kalan=%d · atlandi=%d · ag=%d · '
              'beyan=%d · olculmedi=%d'
              % (len(olculen), len(olculen) - len(kalan), len(kalan),
                 atlandi, ag_sayisi, beyan, olculmedi))
    else:
        print('  olculdu=%d · gecen=%d · kalan=%d · ag=%d · beyan=%d · '
              'olculmedi=%d'
              % (len(olculen), len(olculen) - len(kalan), len(kalan),
                 ag_sayisi, beyan, olculmedi))
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
    if ag and ag_sayisi:
        print('  HUKUM: OLCULMEDI — %d ag iddiasi dis servis olmadan kosulamadi'
              % ag_sayisi)
        return 2
    if not olculen:
        print('  HUKUM: OLCULMEDI — filtrelenen defterde OLCULDU satiri yok')
        return 2
    if hizli:
        print('  HUKUM: HIZLI — %d/%d hizli iddia gecti; %d agir iddia '
              'ATLANDI (PASS sayilmadi)'
              % (len(olculen) - len(kalan), len(olculen), atlandi))
        print('  NOT: tam kosu icin `make iddia`.')
    else:
        print('  HUKUM: PASS — %d/%d olculen iddia ham kanitiyla beyanla ayni'
              % (len(olculen) - len(kalan), len(olculen)))
    if ag_sayisi or beyan or olculmedi:
        print('  NOT: %d ag, %d beyan, %d olculmedi ayri sayildi — PASS degil.'
              % (ag_sayisi, beyan, olculmedi))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
