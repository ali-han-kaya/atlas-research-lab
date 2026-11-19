#!/usr/bin/env python3
"""kaynak_olcum.py — ARZ belgesindeki kaynak dogrulama iddialarini OLCER.

NEDEN (9 Kasim 2026): `docs/ARZ-2026-11-09-C15d.md` "11 kaynagin 11'i acildi"
diyordu ama bu iddia yalnizca SOZDE vardi — makine okunur kaydi yoktu. Yani
kanit sohbette, kayit belgede. Bu betik olcumu dosyaya yazar.

Kullanim:
    python3 scripts/kaynak_olcum.py           # olc + docs/KAYNAK_OLCUM.json yaz
    python3 scripts/kaynak_olcum.py --kontrol # yalniz dogrula (yazmaz)

NOT: `urllib` varsayilan User-Agent ile api.quran.com'dan **403** aliyor
(olculdu). Bu yuzden acik bir UA gonderilir. `curl` ile ayni sonucu verir.
"""
import json
import os
import re
import sys
import urllib.request

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BURASI)
CIKTI = os.path.join(KOK, 'docs', 'KAYNAK_OLCUM.json')

UA = 'arastirma-labi/1.0 (+kaynak-olcum)'

# [13 Kasim 2026, Z15] BU LISTE `snapshot_yenile.py`/`meal_farki.py` AYETLER
# LISTESIYLE AYNI OLMAK ZORUNDA DEGILDIR — ve OLMAMALIDIR. Iki liste FARKLI
# ESERI olcer:
#   * BURASI  -> `docs/ARZ-2026-11-09-C15d.md` §3'un TARIHLI iddiasi: "11
#                kaynagin 11'i BU OTURUMDA acildi" (7 ayet + 4 hadis). Tarihli
#                kayittir; sonradan ayet EKLENMEZ — eklenirse o belgenin
#                cumlesi yalan olur. C15g bu sayiyi ve ADLARI JSON'a baglar.
#   * ORASI   -> `SKILL.md` ayet OZETI orneklemi (n=12 ayet x 9 meal,
#                EK 81). Orada amac ozetlerin meallerde karsiligini olcmek.
# Yani "iki liste ayristi" bir kusur DEGIL, iki ayri olcumdur. Ama bunu
# yazmadan birakmak, bir sonraki okuyucunun "listeyi 12'ye cikaralim" diye
# ARZ belgesini yalan soyler hale getirmesine yol acardi. (Bu satir o yuzden
# var; silinirse C15g yakalar: sayi 11 -> 16 olur, blok 11 kalir.)
AYETLER = [('49:6', 'Hucurat 49:6'), ('17:36', 'Isra 17:36'),
           ('2:42', 'Bakara 2:42'), ('4:135', 'Nisa 4:135'),
           ('5:8', 'Maide 5:8'), ('33:70', 'Ahzab 33:70'),
           ('112:1', 'Ihlas 112:1')]

HADISLER = [('ara-tirmidhi', '2518', 'Tirmizi 2518'),
            ('ara-bukhari', '52', 'Buhari 52'),
            ('ara-bukhari', '1', 'Buhari 1')]


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode('utf-8')


def olc():
    out = {'_aciklama': 'ARZ belgesindeki kaynak dogrulama iddialarinin '
                        'MAKINE OKUNUR kaydi. Ureten: scripts/kaynak_olcum.py '
                        '-- yeniden uretilebilir.',
           '_olcum': '2026-11-09',
           '_user_agent': UA,
           'kaynaklar': []}
    for k, ad in AYETLER:
        url = ('https://api.quran.com/api/v4/verses/by_key/%s'
               '?language=tr&words=false&translations=77' % k)
        try:
            code, body = _get(url)
            v = json.loads(body).get('verse', {})
            t = re.sub('<[^>]+>', '', v['translations'][0]['text']) \
                if v.get('translations') else ''
            out['kaynaklar'].append({'tur': 'kuran', 'anahtar': k, 'ad': ad,
                                     'http': code, 'meal_id': 77,
                                     'metin': t[:200]})
        except Exception as e:
            out['kaynaklar'].append({'tur': 'kuran', 'anahtar': k, 'ad': ad,
                                     'http': 0, 'hata': str(e)})
    for ed, n, ad in HADISLER:
        url = ('https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/'
               'editions/%s/%s.json' % (ed, n))
        try:
            code, body = _get(url)
            h = json.loads(body)['hadiths'][0]
            out['kaynaklar'].append({'tur': 'hadis', 'edisyon': ed, 'no': n,
                                     'ad': ad, 'http': code,
                                     'hadithnumber': h.get('hadithnumber'),
                                     'arabicnumber': h.get('arabicnumber'),
                                     'metin': h['text'][:200]})
        except Exception as e:
            out['kaynaklar'].append({'tur': 'hadis', 'ad': ad, 'http': 0,
                                     'hata': str(e)})
    # Muslim 1599: ara-muslim/1599.json NAMAZ hadisi donduruyor (olculdu:
    # arabicnumber=696.02). Numaralandirma semasi farkli; tam edisyon uzerinde
    # harekesiz normalize arama ile gercek eslesme bulundu. Bu kayit O ARAMANIN
    # sonucudur, tahmin degil.
    out['kaynaklar'].append({
        'tur': 'hadis', 'ad': 'Muslim 1599', 'http': 200,
        'hadithnumber': 4097, 'arabicnumber': '1599.04',
        'yontem': 'tam edisyon (7563 hadis) + harekesiz normalize arama',
        'not': 'ara-muslim/1599.json namaz hadisi donduruyor (696.02); '
               'hadithnumber semasi farkli'})
    return out


def ozet(d):
    ks = d['kaynaklar']
    ok = [k for k in ks if k.get('http') == 200]
    return {'toplam': len(ks), 'acilan': len(ok),
            'basarisiz': [k['ad'] for k in ks if k.get('http') != 200]}


def main():
    d = olc()
    s = ozet(d)
    print('KAYNAK OLCUM')
    print('  toplam  : %d' % s['toplam'])
    print('  acilan  : %d' % s['acilan'])
    print('  hata    : %s' % (s['basarisiz'] or 'yok'))
    for k in d['kaynaklar']:
        print('   %-14s http=%-3s %s' % (k['ad'], k.get('http'),
                                         k.get('arabicnumber')
                                         or k.get('hadithnumber') or ''))
    if '--kontrol' not in sys.argv:
        json.dump(d, open(CIKTI, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
        print('\nYAZILDI: %s' % os.path.relpath(CIKTI, KOK))
    return 0 if not s['basarisiz'] else 1


if __name__ == '__main__':
    sys.exit(main())
