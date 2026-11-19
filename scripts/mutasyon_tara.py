#!/usr/bin/env python3
"""mutasyon_tara.py — hangi kapinin YANMA kaniti kayitli?

NEDEN (9 Kasim 2026): "mutasyonu olmayan kapi, kapi degildir" ilkesi var ama
81 kapinin kacinda kanit oldugu HIC SAYILMADI. Bu betik sayar.

NE YAPAR: her kapi kimligi icin repodaki kanit havuzunu tarar ve AYNI SATIRDA
hem kimlik hem yanma ifadesi arayarak ADAY kanit cikarir.

NE YAPMAZ: aday kaniti ONAYLAMAZ. Aday != kanit. Deftere yazmak ayri bir
islemdir (`--yaz`) ve her satir kaynak dosya + satir no tasir.

Kullanim:
    python3 scripts/mutasyon_tara.py              # rapor
    python3 scripts/mutasyon_tara.py --json       # makine okunur
    python3 scripts/mutasyon_tara.py --yaz        # defteri guncelle
"""
import json
import os
import re
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BURASI)
DEFTER = os.path.join(BURASI, 'tests', 'mutasyon_defteri.json')

# Kanit havuzu: bu dosyalarda "su kapi yandi" kaydi aranir.
HAVUZ_DIZINLER = ['docs']
HAVUZ_DOSYALAR = ['SURUM.md']

# Yanma ifadesi — DUZ, YALIN. Bu ifade tek basina yetmez; asagidaki
# TABLO_YANMA ile birlikte kullanilir.
YANMA = re.compile(
    r'(rc\s*=\s*1|rc=1|YAKALADI|yand[ıi]|YANDI|yan[ıi]yor|k[ıi]rm[ıi]z[ıi]|'
    r'mutasyon[^.]{0,60}(?:FAIL|rc=1|yakalad)|'
    r'(?:FAIL|rc=1)[^.]{0,40}mutasyon)',
    re.IGNORECASE)

# [DUZELTME 2026-11-09] SAYACIN KENDISI KORDU. Olculdu: 5 kapi "kanitsiz"
# gorunuyordu ama kanit FARKLI BICIMDE yazilmisti:
#   | `C1c` | ... | 0 | **1** | `C1c ... FAIL ...` |   -> once_exit/sonra_exit
#   | `C13z`, `C13z-a` | 2/2 |                          -> yanma orani
#   | `7d3a082` | ... | `C14f/g` | 2/2 |                -> EGIK CIZGI kisaltma
# Yani "kanit yok" dedigim 5 kapinin 5'inde de kanit VARDI. Sayac yanlis
# raporluyordu. Bu, sayacin kendisinin KAPI_DEGIL olmasi demektir.
#
# Genisletme SARTLI yapilir (yoksa yanlis pozitif patlar):
#   (a) satir tablo satiri olmali (| ile baslamali)  VE
#   (b) satirdan geriye 80 satir icinde "mutasyon" gecmeli (bolum baglami).
# Bu iki sart saglanmadan `2/2` veya `**1**` YANMA SAYILMAZ.
TABLO_YANMA = re.compile(r'(\|\s*\d+/\d+\s*\|)|(\|\s*\*\*1\*\*\s*\|)|'
                         r'(sonra_exit)', re.IGNORECASE)

# SERT KANIT (14 Kasim 2026, Z31a) -------------------------------------------
# NEDEN: defter kapı başına EN FAZLA 2 kanıt tutuyor ve sırası
# `(yanma != 'duz', kaynak)` — yani ALFABETİK. `SURUM.md` her zaman önde
# olduğu için defter EN YENİ kanıtı değil, EN ESKİ kaydı gösteriyordu.
# ÖLÇÜLDÜ (14 Kasım 2026): `C15n` için cap öncesi **8** aday, cap sonrası **2**
# (`SURUM.md:37`, `SURUM.md:39`). EK 101'in kendi kanıt satırı
# (`DEVIR-2026-11-08-0931.md:11154`, `M158/M159/M160 rc=1 YAKALADI`) TARANIYOR
# AMA DEFTERE GİRMİYORDU. Yani "kanıt var mı, nerede" sorusunun cevabı
# yanlış yeri gösteriyordu.
#
# SERT = satır bir MUTASYON KİMLİĞİ (`M20`, `M154`) ya da bir TABLO ORANI
# (`| 2/2 |`) taşıyor. Serbest düzyazıdaki `rc=1` tek başına SERT değildir:
# "rc=1" yazan bir cümle, mutasyonun KOŞULDUĞUNU değil YAZILDIĞINI gösterir.
_SERT_M_ID = re.compile(r'(?<![A-Za-z0-9])M\d{2,3}(?![0-9])')
_SERT_ORAN = re.compile(r'\|\s*\d+/\d+\s*\|')
# EXIT GECISI (14 Kasim 2026, Z32a): `| 0 | **1** |` — mutasyon ONCESI ve
# SONRASI cikis kodu AYRI HUCRELERDE. Bu, duzyazidan guclu: hangi mutasyonun
# hangi exit kodunu urettigini yapisal olarak soyler.
# REDDEDILEN GENISLETME (olculdu): `yanma == 'tablo'` sinifini SERT saymak
# 36 -> 67 yapiyordu ama 31 "yeni" kapinin 21'i TEK bir DERSLER satirindan
# (satir 513, "SAYACIN KENDISI KAPI_DEGIL olabilir") geliyordu; o satir 21
# kapi kimligini birlikte aniyor ve icinde "mutasyon" kelimesi gectigi icin
# `tablo_baglami` onu BASLIK sayiyor. Yani toplu anma, SERT kanit gibi
# gorunuyordu — YIKAMA olurdu. Dar tanim korundu.
_SERT_EXIT = re.compile(r'\|\s*[01]\s*\|\s*\*\*[01]\*\*\s*\|')


def sert_mi(kayit):
    """Bu kanıt satırı bir mutasyon KİMLİĞİ ya da tablo ORANI taşıyor mu?"""
    try:
        metin = kayit['metin']
    except Exception:
        return False
    return bool(_SERT_M_ID.search(metin) or _SERT_ORAN.search(metin)
                or _SERT_EXIT.search(metin))


def sert_kimlikler(kimlikler, aday):
    """SERT kaniti olan kapilar (sirali). Ratchet'in canli tarafi."""
    return sorted(k for k in kimlikler
                  if any(sert_mi(a) for a in aday.get(k) or []))


def _kanit_sirasi(x):
    """Defter seçimi: SERT önce, sonra SURUM dışı, sonra ada/satıra göre."""
    return (0 if sert_mi(x) else 1,
            1 if x['kaynak'] == 'SURUM.md' else 0,
            x['kaynak'], x['satir'])

# TABLO BASLIGI: "mutasyon" kelimesinin 80 satir gerisinde olmasi YETMEZ —
# kelime bir paragrafta gecer, sonraki tablolar da "mutasyon tablosu" sayilir.
# Sarti sikilastirdik: geriye dogru yururken ILK `|` satirina bakilir; o satir
# ya baslik (icerigi `---` ise bir UST `|` satiri basliktir) ya da ayni
# tablonun govdesidir. Tablo disina cikildiginda (bos satir) arama DURUR.
BASLIK = re.compile(r'mutasyon', re.IGNORECASE)


def tablo_baglami(satirlar, no):
    """`no` (1-tabanli) satiri bir MUTASYON TABLOSUNUN icinde mi?"""
    i = no - 2                      # 0-tabanli, bir onceki satir
    while i >= 0:
        s = satirlar[i]
        if not s.strip():
            return False            # tablo bitti
        if s.lstrip().startswith('|'):
            # ayirici satir (|---|---|) ise baslik bir ust satirdir
            if set(s.replace('|', '').replace('-', '').replace(':', '')
                   .replace(' ', '')) == set():
                i -= 1
                if i >= 0 and satirlar[i].lstrip().startswith('|'):
                    return bool(BASLIK.search(satirlar[i]))
                return False
            # govde satiri: tablonun basligini yukari dogru ara
            j = i
            while j >= 0 and satirlar[j].strip():
                if satirlar[j].lstrip().startswith('|') and BASLIK.search(satirlar[j]):
                    return True
                j -= 1
            return False
        i -= 1
    return False

# EGIK CIZGI kisaltma: `C14f/g` -> C14f, C14g. Ayri yakalanir cunku KIMLIK
# deseni `C14f`i gorur, `/g`i gormez.
EGIK = re.compile(r'(?<![A-Za-z0-9])(C\d{1,2})([a-z])/([a-z]{1,4})(?![A-Za-z0-9])')

KIMLIK = re.compile(r'(?<![A-Za-z0-9])(C\d{1,2}(?:[a-z][a-z-]*)?)(?![A-Za-z0-9])')

# TOPLU KANIT: `C13a–C13r` gibi ARALIK yazimi. Olculdu (9 Kasim 2026):
# "C13a-C13r araliginda 81 icinde olan kapi: 18" — yani aralik gercek 18 kapiyi
# kapsiyor, uydurma degil. Ama aralik kaniti TEK bir iddia satirina dayanir;
# bu yuzden ayri etiketlenir (`tip: aralik`), tek tek kanitle ayni agirlikta
# SAYILMAZ (Mutaffifin 83: olcude sisme yok).
ARALIK = re.compile(
    r'(?<![A-Za-z0-9])(C\d{1,2})([a-z])\s*[-\u2013\u2014]\s*\1([a-z])(?![A-Za-z0-9])')


def kapi_kimlikleri(verilen=None):
    """Kapi kimlikleri. `verilen` varsa subprocess YOK (ozyineleme korumasi)."""
    if verilen:
        return list(verilen)
    import subprocess
    env = dict(os.environ, SNAPSHOT_ONLY='1')
    # timeout (13 Kasim 2026, Z14): bu cagri skill_lint'i kosar ve 60-120 s
    # surer. Timeout'suz birakildiginda lint asili kalirsa bu betik SONSUZA
    # KADAR beklerdi — FAIL degil, HIC DONMEZ. C15j bunu olcer.
    r = subprocess.run([sys.executable, os.path.join(BURASI, 'skill_lint.py'),
                        os.path.join(KOK, 'SKILL.md')],
                       capture_output=True, text=True, env=env, timeout=900)
    out = r.stdout + r.stderr
    ks = []
    for sat in out.splitlines():
        m = re.match(r'\s{1,4}(C\d{1,2}[a-z-]*)\s', sat)
        if m and m.group(1) not in ks:
            ks.append(m.group(1))
    return ks


def havuz():
    yollar = []
    for d in HAVUZ_DIZINLER:
        kok = os.path.join(KOK, d)
        for ad in sorted(os.listdir(kok)):
            if ad.endswith('.md'):
                yollar.append(os.path.join(kok, ad))
    for ad in HAVUZ_DOSYALAR:
        p = os.path.join(KOK, ad)
        if os.path.exists(p):
            yollar.append(p)
    return yollar


def tara(verilen_kimlikler=None):
    """kimlik -> [aday kanit] sozlugu dondurur."""
    kimlikler = kapi_kimlikleri(verilen_kimlikler)
    aday = {k: [] for k in kimlikler}
    for p in havuz():
        try:
            satirlar = open(p, encoding='utf-8').read().splitlines()
        except Exception:
            continue
        rel = os.path.relpath(p, KOK)
        for no, sat in enumerate(satirlar, 1):
            # --- yanma sinyali: duz ifade VEYA (tablo satiri + bolum baglami)
            duz = bool(YANMA.search(sat))
            tablo = False
            if not duz and sat.lstrip().startswith('|') and TABLO_YANMA.search(sat):
                tablo = tablo_baglami(satirlar, no)
            if not (duz or tablo):
                continue
            tip_yanma = 'duz' if duz else 'tablo'
            dokunulan = set()
            # (a) tekil kimlikler
            for k in KIMLIK.findall(sat):
                if k in aday:
                    dokunulan.add(k)
                    aday[k].append({'tip': 'tekil', 'yanma': tip_yanma,
                                    'kaynak': rel, 'satir': no,
                                    'metin': sat.strip()[:180]})
            # (b) egik cizgi kisaltma: C14f/g -> C14f + C14g
            for _pfx, _ilk, _kalan in EGIK.findall(sat):
                for _h in [_ilk] + list(_kalan):
                    k = '%s%s' % (_pfx, _h)
                    if k in aday:
                        dokunulan.add(k)
                        aday[k].append({'tip': 'egik', 'yanma': tip_yanma,
                                        'kaynak': rel, 'satir': no,
                                        'metin': sat.strip()[:180]})
            # (c) aralik kimlikler: C13a-C13r -> C13a..C13r genisletilir
            for _pfx, _bas, _son in ARALIK.findall(sat):
                for _c in range(ord(_bas), ord(_son) + 1):
                    k = '%s%s' % (_pfx, chr(_c))
                    if k in aday:
                        dokunulan.add(k)
                        aday[k].append({'tip': 'aralik', 'yanma': tip_yanma,
                                        'kaynak': rel, 'satir': no,
                                        'metin': sat.strip()[:180]})
            # ayni satirdan gelen cift kayitlari tekillestir (yalniz dokunulanlar)
            for k in dokunulan:
                gorulen = set()
                yeni = []
                for a in aday[k]:
                    imza = (a['kaynak'], a['satir'], a['tip'])
                    if imza in gorulen:
                        continue
                    gorulen.add(imza)
                    yeni.append(a)
                aday[k] = yeni
    return kimlikler, aday


def main():
    kimlikler, aday = tara()
    kanitli = [k for k in kimlikler if aday[k]]
    kanitsiz = [k for k in kimlikler if not aday[k]]

    if '--json' in sys.argv:
        print(json.dumps({'toplam': len(kimlikler),
                          'kanitli': len(kanitli),
                          'kanitsiz': len(kanitsiz),
                          'sert_kanitli': len(sert_kimlikler(kimlikler, aday)),
                          'sert_kimlikler': sert_kimlikler(kimlikler, aday),
                          'kanitsiz_kimlikler': kanitsiz,
                          'aday': {k: aday[k] for k in kanitli}},
                         ensure_ascii=False, indent=2))
    else:
        print('MUTASYON SAYACI')
        print('  toplam kapi        : %d' % len(kimlikler))
        print('  aday kanit bulunan : %d' % len(kanitli))
        print('  aday kanit YOK     : %d' % len(kanitsiz))
        print('  oran               : %d/%d' % (len(kanitli), len(kimlikler)))
        _sert = sert_kimlikler(kimlikler, aday)
        print('  SERT kanitli       : %d/%d (M<id> ya da | n/m | tasiyan)'
              % (len(_sert), len(kimlikler)))
        print()
        print('KAPI_DEGIL (aday kanit yok):')
        for k in kanitsiz:
            print('  - %s' % k)

    if '--yaz' in sys.argv:
        # Defter KAYIT icindir, arsiv degil: kapi basina en fazla 2 kanit,
        # metin 120 karakter. Amac "kanit var mi, nerede" — tam metin degil.
        def _ks(a):
            a = sorted(a, key=_kanit_sirasi)
            return [{'tip': x['tip'], 'yanma': x['yanma'], 'kaynak': x['kaynak'],
                     'satir': x['satir'], 'metin': x['metin'][:120]}
                    for x in a[:2]]
        _sert = sert_kimlikler(kimlikler, aday)
        # RATCHET (14 Kasim 2026, Z31b): sert kanit kumesi KUCULTULMEZ.
        # OLCULDU: 95 kapinin yalniz 36'sinda SERT kanit var (M<id> ya da
        # | n/m |). Kalan 59'un kaniti SERBEST DUZYAZI ('rc=1' gecmesi), yani
        # mutasyonun KOSULDUGUNU degil YAZILDIGINI gosterir. Bu bir kusur ama
        # TOPTAN sertlestirme 95 -> 36 yapar ve C15e'yi kirar. Bu yuzden kural
        # taban koruma: bugunku 36 kaybolamaz, artabilir. Boylece kayip
        # SESSIZ olmaz; `--yaz` ile de yikanamaz (taban birlesim alir).
        _eski_sert = []
        try:
            with open(DEFTER, encoding='utf-8') as _f:
                _eski_sert = json.load(_f).get('sert_kimlikler') or []
        except Exception:
            _eski_sert = []
        _taban = sorted(set(_eski_sert) | set(_sert))
        _sert_kayip = sorted(set(_eski_sert) - set(_sert))
        if _sert_kayip:
            print('SERT KANIT KAYBI (taban korunur): %s' % ', '.join(_sert_kayip))
        d = {'_aciklama': 'Kapi basina mutasyon (yanma) kaniti. Ureten: '
                          'scripts/mutasyon_tara.py --yaz. Aday != kanit: her '
                          'satir kaynak dosya + satir tasir; onaysiz silinmez.',
             '_olcum': '9 Kasim 2026',
             'toplam': len(kimlikler),
             'kanitli': len(kanitli),
             'kanitsiz': len(kanitsiz),
             'kanitsiz_kimlikler': kanitsiz,
             'sert_kanitli': len(_sert),
             'sert_kimlikler': _taban,
             'aday': {k: _ks(aday[k]) for k in kanitli}}
        # ATOMIK YAZ (12 Kasim 2026, Z8): ayni desen — hata olursa defter YARIM
        # kalirdi ve `C15e` kanit sayaci bir daha guvenilir olmazdi.
        from atomik_yaz import yaz_json
        n = yaz_json(DEFTER, d, indent=2, sort_keys=False)
        print('\nDEFTER YAZILDI: %s · %d bayt (atomik)'
              % (os.path.relpath(DEFTER, KOK), n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
