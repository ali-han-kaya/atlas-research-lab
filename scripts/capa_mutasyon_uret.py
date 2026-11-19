#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capa_mutasyon_uret.py — SERT olmayan kapilar icin mutasyon ONERISI uretir.

Yontem (olculur, uydurulmaz):
  1. `SKILL.md` `_katla`dan gecirilir (lint'in kendi katlama fonksiyonu).
  2. Her kapi kimligi icin `skill_lint.py` kaynaginda o kimligin +-800 karakter
     cevresindeki STRING LITERALLER toplanir.
  3. Bir literal, katlanmis metinde TAM 1 kez geciyorsa CAPA adayidir.
  4. Aday, ham metinde Turkce/backtick toleransli desenle aranir; TAM 1 eslesme
     yoksa atilir.
  5. Mutasyon: eslesen ham dilimin ORTASINA `Q` sokulur (capa kaybolur).
     `Q` secildi cunku `_katla` onu degistirmez — yani kayip KESIN.
"""
import ast
import io
import json
import re
import sys

KOK = '/Users/alikaya/Desktop/MTRX/AI_ARASTIRMA_LABI'
sys.path.insert(0, KOK + '/scripts')

_TR = {'İ': 'i', 'I': 'i', 'ı': 'i', 'Ş': 's', 'ş': 's', 'Ğ': 'g', 'ğ': 'g',
       'Ü': 'u', 'ü': 'u', 'Ö': 'o', 'ö': 'o', 'Ç': 'c', 'ç': 'c',
       'Â': 'a', 'â': 'a'}


def katla(s):
    for g in ('\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u00ad', '\u2024'):
        s = s.replace(g, ' ')
    for a, b in _TR.items():
        s = s.replace(a, b)
    s = s.replace('**', '').replace('`', '').replace('*', '')
    s = s.replace('\u2019', "'").replace('\u2018', "'")
    import unicodedata
    s = unicodedata.normalize('NFKC', s)
    return ' '.join(s.split()).lower()


_SINIF = {'c': 'cçCÇ', 'g': 'gğGĞ', 'i': 'iIıİ', 'o': 'oöOÖ',
          's': 'sşSŞ', 'u': 'uüUÜ', 'a': 'aâAÂ'}


def ham_desen(anchor):
    """Katlanmis capadan, ham metinde arayacak desen uretir."""
    parca = []
    for ch in anchor:
        if ch.isspace():
            parca.append(r'\s+')
        elif ch in _SINIF:
            parca.append('[' + _SINIF[ch] + ']')
        else:
            parca.append(re.escape(ch).replace('\\ ', ' '))
    return r'[\*`\u200b\u200c\u200d]*'.join(parca)


_LIT = re.compile(r"(['\"])((?:[^'\"\\\n]|\\.){8,200})\1")


def adaylar(kaynak, kapi):
    """Kaynakta kapi kimliginin cevresindeki string literalleri toplar.

    NOT: `ast.parse` ile dilim ayristirmak COKTU (dilim blok ortasindan
    basliyor -> IndentationError, 43/43 kapi "aday bulunamadi" cikti).
    Bu yuzden duz REGEX ile toplanir; literal olmayanlar zaten desen
    kontrolunde elenir.
    """
    # PENCERE = GIRDI SINIRI (14 Kasim 2026, Z34d).
    # NEDEN: ilk surum +-800 karakter aliyordu; bu pencere KOMSUSUNDAKI kapi
    # girdilerinin capalarini da topluyordu -> 12 mutasyonun 10'u hedef kapıyı
    # KIMILDATDI (olculdu: isabet 2/12). Simdi pencere, kimligin ICINDE
    # bulundugu girdiyle sinirli: girdi basi `('Cxx',` ya da `k('Cxx',`) ile
    # baslar, BIR SONRAKI girdi basinda biter.
    cikti = []
    for m in re.finditer(r"\(\s*'%s'\s*," % re.escape(kapi), kaynak):
        bas = m.start()
        nxt = re.search(r"\n\s*(?:\(\s*'C\d|k\(\s*'C\d)", kaynak[m.end():])
        son = m.end() + (nxt.start() if nxt else 3000)
        son = min(son, m.end() + 3000)
        for lm in _LIT.finditer(kaynak[bas:son]):
            v = lm.group(2)
            if re.search(r'[\\\[\]{}()]', v):
                continue
            cikti.append(v)
    return list(dict.fromkeys(cikti))


def main():
    kalan = json.load(open(sys.argv[1], encoding='utf-8'))
    kaynak = io.open(KOK + '/scripts/skill_lint.py', encoding='utf-8').read()
    ham = io.open(KOK + '/SKILL.md', encoding='utf-8').read()
    duz = katla(ham)

    oneri = []
    for kapi in kalan:
        bulundu = None
        for lit in adaylar(kaynak, kapi):
            a = katla(lit)
            if len(a) < 8 or duz.count(a) != 1:
                continue
            esles = list(re.finditer(ham_desen(a), ham))
            if len(esles) != 1:
                continue
            m = esles[0]
            eski = m.group(0)
            if ham.count(eski) != 1:
                continue
            k = len(eski) // 2
            yeni = eski[:k] + 'Q' + eski[k:]
            bulundu = {'kapi': kapi, 'ad': 'capa bozuldu: %s' % a[:44],
                       'dosya': 'SKILL.md', 'eski': eski, 'yeni': yeni,
                       'capa': a[:70]}
            break
        if bulundu:
            oneri.append(bulundu)
            print('  %-8s OK  %s' % (kapi, bulundu['eski'][:60].replace('\n', ' ')))
        else:
            print('  %-8s --  capa adayi bulunamadi' % kapi)
    # --- PAYLASILAN CAPA ELENIR -----------------------------------------
    # NEDEN: `C13a`..`C13h` ayni capayi (`2026-11-07 yeniden olcum`) aldi;
    # `C13o`..`C13r` de ayni capayi. Tek mutasyon 8 kapiya kredi yazarsa
    # kanit kapiya AIT olmaz — bu, Z32'de reddedilen "toplu anma" sinifinin
    # aynisi. Paylasilan capalar ELENIR ve olculur, gizlenmez.
    sayac = {}
    for o in oneri:
        sayac.setdefault(o['eski'], []).append(o['kapi'])
    paylasilan = {e: ks for e, ks in sayac.items() if len(ks) > 1}
    if paylasilan:
        print('\nPAYLASILAN CAPA (%d grup) — ELENDI:' % len(paylasilan))
        for e, ks in paylasilan.items():
            print('   %-46r -> %s' % (e[:42].replace('\n', ' '), ', '.join(ks)))
    oneri = [o for o in oneri if o['eski'] not in paylasilan]

    out = (sys.argv[2] if len(sys.argv) > 2
           else KOK + '/scripts/tests/mutasyon_listesi_2.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        json.dump(oneri, f, ensure_ascii=False, indent=1)
    print('\nYAZILDI: %s · %d oneri' % (out, len(oneri)))


if __name__ == '__main__':
    main()
