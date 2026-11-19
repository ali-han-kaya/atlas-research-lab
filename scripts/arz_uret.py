#!/usr/bin/env python3
"""arz_uret.py — ARZ belgesinin OLCUM BLOGUNU uretir (elle yazilmaz).

NEDEN (9 Kasim 2026): `docs/ARZ-2026-11-09-C15d.md` sayilarla dolu ve sayilar
DOGRUYDU — ama ELLE yazilmisti. Elle yazilan sayi kayar; kaydiginda kimse fark
etmez. Bu betik blogu JSON kaynaklarindan uretir; `C15g` kapisi her lint'te
canli olcumle karsilastirir.

Kullanim:
    python3 scripts/arz_uret.py docs/ARZ-....md          # blogu yaz/guncelle
    python3 scripts/arz_uret.py docs/ARZ-....md --kontrol # yazmaz, dogrular
"""
import json
import os
import re
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BURASI)

BASLA = '<!-- ARZ_OLCUM:basla -->'
BITTI = '<!-- ARZ_OLCUM:bitti -->'


def degerler():
    """Bloktaki TUM degerler — hepsi JSON kaynagindan, elle yazilmaz."""
    d = {}
    p = os.path.join(KOK, 'docs', 'MADDE_KAPANIS.json')
    kay = json.load(open(p, encoding='utf-8'))
    ms = kay['maddeler']
    d['madde_sayisi'] = len(ms)
    d['kapanmadi_toplam'] = sum(int(m['kapanmadi']) for m in ms)
    d['kapandi_min'] = min(int(m['kapandi']) for m in ms)
    d['kapandi_max'] = max(int(m['kapandi']) for m in ms)
    cv = [int(m['cevapsiz']) for m in ms]
    d['cevapsiz_min'] = min(cv)
    d['cevapsiz_max'] = max(cv)
    d['model_blogu'] = int(kay['kaynak']['model_blogu'])
    et = sorted(set(str(m.get('etiket')) for m in ms))
    d['etiket_tekil'] = len(et)
    d['etiket'] = et[0] if len(et) == 1 else 'KARISIK'

    kp = os.path.join(KOK, 'docs', 'KAYNAK_OLCUM.json')
    if os.path.exists(kp):
        ko = json.load(open(kp, encoding='utf-8'))
        ks = ko['kaynaklar']
        d['kaynak_toplam'] = len(ks)
        d['kaynak_acilan'] = sum(1 for k in ks if k.get('http') == 200)
    else:
        d['kaynak_toplam'] = 0
        d['kaynak_acilan'] = 0
    return d


def blok_metni(d):
    satirlar = [BASLA]
    for k in ('madde_sayisi', 'kapanmadi_toplam', 'kapandi_min', 'kapandi_max',
              'cevapsiz_min', 'cevapsiz_max', 'model_blogu',
              'etiket_tekil', 'etiket', 'kaynak_toplam', 'kaynak_acilan'):
        satirlar.append('%s: %s' % (k, d[k]))
    satirlar.append(BITTI)
    return '\n'.join(satirlar)


def ayristir(metin):
    m = re.search(re.escape(BASLA) + r'(.*?)' + re.escape(BITTI), metin, re.S)
    if not m:
        return None
    d = {}
    for ln in m.group(1).splitlines():
        ln = ln.strip()
        if not ln or ':' not in ln:
            continue
        k, v = ln.split(':', 1)
        k, v = k.strip(), v.strip()
        d[k] = int(v) if re.fullmatch(r'-?\d+', v) else v
    return d


def main():
    if len(sys.argv) < 2:
        print('kullanim: arz_uret.py <ARZ-dosyasi> [--kontrol]')
        return 2
    p = sys.argv[1]
    if not os.path.exists(p):
        print('YOK: %s' % p)
        return 2
    d = degerler()
    s = open(p, encoding='utf-8').read()
    yeni = blok_metni(d)
    if BASLA in s:
        s2 = re.sub(re.escape(BASLA) + r'.*?' + re.escape(BITTI), yeni, s,
                    flags=re.S)
    else:
        # Blok ILK `## ` basligindan hemen ONCE yerlestirilir: kimlik ve amac
        # satirlari ustte kalir, olcum blogu icerigin basinda durur.
        m = re.search(r'^##\s', s, re.M)
        if not m:
            print('BASLIK YOK: %s' % p)
            return 2
        ek = ('## Olcum blogu (makine uretir — `C15g` dogrular)\n\n'
              'Asagidaki sayilar **elle yazilmaz**; `scripts/arz_uret.py` '
              'JSON kaynaklarindan uretir. Uyusmazsa kapı FAIL verir.\n\n'
              + yeni + '\n\n---\n\n')
        s2 = s[:m.start()] + ek + s[m.start():]
    if '--kontrol' in sys.argv:
        mevcut = ayristir(s2)
        fark = {k: (mevcut.get(k), v) for k, v in d.items() if mevcut.get(k) != v}
        if fark:
            print('BAYAT: %s' % fark)
            return 1
        print('GUNCEL: %d anahtar' % len(d))
        return 0
    if s2 != s:
        open(p, 'w', encoding='utf-8').write(s2)
        print('YAZILDI: %s (%d anahtar)' % (p, len(d)))
    else:
        print('DEGISMEDI: %s' % p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
