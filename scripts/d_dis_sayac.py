#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""d_dis_sayac.py — dis denetim cevap dosyasini FORMAT TOLERANSLI sayar.

NEDEN VAR (8 Kasim 2026, kendi hatam — Nisa 4:135):
Ucuncu tur raporuna "17 model - 270 karar - 37 acik hucre" yazdim. Uc sayinin
UCU DE YANLISTI. Kok neden benim ayristiricimdi, denetci degil:

  (a) 10. model (Mimo v2.6) kararlarini TEK SATIRDA yazmis:
        "D1, D10, D17 -> KAPANMADI; D11 -> YENI_KUSUR; kalan 12 -> KAPANDI"
      Ilk ayristirici yalniz `D<n> : KARAR` bicimini ariyordu -> onun 4 ACIK
      hucresi (D1, D10, D17, D11) hic sayilmadi. 37 + 4 = 41.
  (b) 9. model (Glm 5.3 flash) cevabini citli blok icinde vermis; blok icindeki
      "1." maddesini model basligi sandim -> model 17 yerine 18.

DERS: sayan betik, saydigi BICIMI ilan etmek zorunda. Bu betik iki bicimi de
ayristirir ve HER IKISINI birden raporlar; hangi bicimin kac tane urettigini
gizlemez. Cozemedigi satir olursa `COZULEMEDI` yazar — sessizce atlamaz.

KULLANIM
    python3 scripts/d_dis_sayac.py <cevap.md>            # insan okur ozet
    python3 scripts/d_dis_sayac.py <cevap.md> --json     # makine okur
    python3 scripts/d_dis_sayac.py <cevap.md> --hucre   # hucre matrisi

CIKIS KODU
    0  ayristirildi, cozulemeyen satir yok
    1  ayristirildi ama COZULEMEDI satiri var (iddia zayif)
    2  model bloku bulunamadi / dosya yok
"""

import hashlib
import json
import re
import sys

KARARLAR = ('KAPANDI', 'KAPANMADI', 'YENI_KUSUR', 'KISMEN', 'OLCULMEDI')
_FORM = r'(?:%s)' % '|'.join(KARARLAR)

# --- BICIM 1: `D<n> : KARAR` / `D<n> - KARAR` / em-dash ---------------------
_BICIM1 = re.compile(r'\bD(\d+)\s*[:\-\u2014\u2013]\s*(' + _FORM + r')\b')

# --- BICIM 2: `D1, D10, D17 -> KAPANMADI` / `... → KAPANMADI` ---------------
_BICIM2 = re.compile(
    r'((?:D\d+\s*[,;]\s*)*D\d+)\s*(?:\u2192|->|=>)\s*(' + _FORM + r')\b')

# --- BICIM 2b: `kalan 12 -> KAPANDI` (sayiyla beyan) -----------------------
_BICIM2B = re.compile(
    r'kalan\s+(\d+)\s*(?:madde\s*)?(?:\u2192|->|=>)\s*(' + _FORM + r')\b',
    re.I)

# --- MODEL BASLIGI: satir basinda `N. Ad` ----------------------------------
# TUZAK (olculdu): citli blok icindeki "1. Hedef eser bu oturuma girmedi."
# satiri da bu desene uyar. Cozum: numara ARTMAK zorunda; 1'e geri donus
# (blok ici madde listesi) yeni model sayilmaz.
_BASLIK = re.compile(r'^(\d{1,2})\.\s+(\S.{1,58})$')


def _modeller(satirlar):
    """[(baslangic_satiri, numara, ad)] — numara artan sirada."""
    out = []
    for i, l in enumerate(satirlar, 1):
        m = _BASLIK.match(l)
        if not m:
            continue
        n = int(m.group(1))
        if out and n <= out[-1][1]:        # 1'e geri donus = citli blok icerigi
            continue
        out.append((i, n, m.group(2).strip().rstrip('. ')))
    return out


def _blok(satirlar, model):
    """Bir modelin satir araligi."""
    sinir = [m[0] for m in model] + [len(satirlar) + 1]
    out = []
    for k, (i, n, ad) in enumerate(model):
        out.append((i, n, ad, '\n'.join(satirlar[i - 1:sinir[k + 1] - 1])))
    return out


def ayristir(yol):
    raw = open(yol, 'rb').read()
    s = raw.decode('utf-8')
    satirlar = s.splitlines()
    model = _modeller(satirlar)
    if not model:
        return None, 'MODEL BLOKU YOK'

    hucre = []          # (model_no, model_adi, D, karar, bicim, satir_no)
    sayi_beyan = []     # (model_no, adet, karar)
    cozulemedi = []

    for i, n, ad, blok in _blok(satirlar, model):
        b1 = _BICIM1.findall(blok)
        b2 = _BICIM2.findall(blok)
        b2b = _BICIM2B.findall(blok)

        for d, k in b1:
            hucre.append((n, ad, 'D%d' % int(d), k.upper(), 'bicim1', i))
        for grup, k in b2:
            for d in re.findall(r'D(\d+)', grup):
                hucre.append((n, ad, 'D%d' % int(d), k.upper(), 'bicim2', i))
        for adet, k in b2b:
            sayi_beyan.append((n, ad, int(adet), k.upper()))

        # Cozulemeyen satir: 'D<n>' gecer ama KARAR gecmez ve satir uzunsa
        if not (b1 or b2 or b2b):
            for l in blok.splitlines():
                if re.search(r'\bD\d+\b', l) and len(l) > 60:
                    cozulemedi.append((n, ad, l.strip()[:110]))
                    break

    return {
        'dosya': yol,
        'sha256': hashlib.sha256(raw).hexdigest(),
        'bayt': len(raw),
        'satir': s.count('\n'),
        'model_sayisi': len(model),
        'modeller': [{'no': n, 'ad': ad, 'satir': i} for i, n, ad in model],
        'hucre': hucre,
        'sayi_beyan': sayi_beyan,
        'cozulemedi': cozulemedi,
    }, None


def ozet(veri):
    import collections
    hucre = veri['hucre']
    dag = collections.Counter(h[3] for h in hucre)
    toplam_adlandirilmis = len(hucre)
    toplam_beyan = sum(b[2] for b in veri['sayi_beyan'])
    acik = [h for h in hucre if h[3] in ('KAPANMADI', 'YENI_KUSUR')]

    print('DOSYA   : %s' % veri['dosya'])
    print('SHA256  : %s' % veri['sha256'])
    print('BOYUT   : %d B · satir %d' % (veri['bayt'], veri['satir']))
    print('MODEL   : %d' % veri['model_sayisi'])
    for m in veri['modeller']:
        print('   %2d. %-26s L%d' % (m['no'], m['ad'], m['satir']))

    print('\n--- BICIM DAGILIMI (hangi bicim kac hucre uretti) ---')
    bd = collections.Counter(h[4] for h in hucre)
    for b, c in sorted(bd.items()):
        print('   %-8s %d' % (b, c))
    if veri['sayi_beyan']:
        print('   sayi-beyan (%d kayit, toplam %d hucre):'
              % (len(veri['sayi_beyan']), toplam_beyan))
        for n, ad, adet, k in veri['sayi_beyan']:
            print('      model %d (%s): %d hucre -> %s' % (n, ad, adet, k))

    print('\n--- KARAR DAGILIMI ---')
    for k in KARARLAR:
        if dag.get(k):
            print('   %-12s %d' % (k, dag[k]))
    print('   ADLANDIRILMIS HUCRE : %d' % toplam_adlandirilmis)
    print('   SAYIYLA BEYAN       : %d' % toplam_beyan)
    print('   TOPLAM              : %d' % (toplam_adlandirilmis + toplam_beyan))

    print('\n--- ACIK HUCRELER (KAPANMADI + YENI_KUSUR) ---')
    print('   toplam: %d' % len(acik))
    dd = collections.Counter(h[2] for h in acik)
    for d in sorted(dd, key=lambda x: int(x[1:])):
        tip = collections.Counter(h[3] for h in acik if h[2] == d)
        print('   %-5s %2d  %s' % (d, dd[d], dict(tip)))

    if veri['cozulemedi']:
        print('\n--- COZULEMEDI (%d) — iddia ZAYIF ---' % len(veri['cozulemedi']))
        for n, ad, l in veri['cozulemedi']:
            print('   model %d (%s): %s' % (n, ad, l))
    else:
        print('\nCOZULEMEDI: yok')
    return 1 if veri['cozulemedi'] else 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    yol = argv[1]
    try:
        veri, hata = ayristir(yol)
    except FileNotFoundError:
        print('DOSYA YOK: %s' % yol)
        return 2
    if hata:
        print('HATA: %s' % hata)
        return 2
    if '--json' in argv:
        print(json.dumps(veri, ensure_ascii=False, indent=2))
        return 1 if veri['cozulemedi'] else 0
    if '--hucre' in argv:
        for n, ad, d, k, b, L in veri['hucre']:
            print('%2d\t%-24s\t%-5s\t%-11s\t%-8s\tL%d' % (n, ad, d, k, b, L))
        return 1 if veri['cozulemedi'] else 0
    return ozet(veri)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
