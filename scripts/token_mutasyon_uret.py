#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""token_mutasyon_uret.py — `_gerek` DEMETLERINDEN mutasyon uretir (Z38).

NEDEN (olculdu, EK 108): `capa_mutasyon_uret.py` yalniz duz string literali
topluyordu. `C13` tablosunda kapi kurali `[(token, adet), ...]` DEMETLERIYLE
yazili; harvester adet kosulunu okuyamadigi icin 24 kapida 7 aday buldu ve
yalniz 1'i atesledi.

BU BETIK UC SEY YAPAR:
  1. `CAPA` ve `C13` tablolarini AST ile okur (literal_eval; cozulemeyen
     eleman ATLANIR ve sayisi yazilir).
  2. Her token icin gercek sayimi lint'in KENDI kurallariyla yapar:
       CAPA : token, o bolumun govdesinde GECMELI (`in`)
       C13  : token, TUM belgede TAM `n` kez gecmeli
     (`R:` regex, `H:` ham, digerleri `_katla` uzerinden — lint ne yapiyorsa o.)
  3. Mutasyonu BELLEKTE uygular ve HANGI KAPILARIN DONDUGUNU onceden olcer.
     Boylece kosum oncesi "bu mutasyon hedefi kiriyor mu" sorusu cevaplanir.

BU ONCEDEN OLCUM BIR KANIT DEGILDIR: kanit, mutasyonu `mutasyon_kos.py`nin
kosup lint'in `rc=1` vermesidir. Buradaki olcum yalniz ADAY SEÇMEK icindir.

KULLANIM:
  python3 scripts/token_mutasyon_uret.py --kalan <json> --cikti <json>
"""
import argparse
import ast
import io
import json
import re
import sys

KOK = '/Users/alikaya/Desktop/MTRX/AI_ARASTIRMA_LABI'
sys.path.insert(0, KOK + '/scripts')

from capa_mutasyon_uret import katla as _katla, ham_desen  # noqa: E402


def _tablo(ad):
    """`skill_lint.py` icindeki modul duzeyi listeyi eleman eleman cozer."""
    src = io.open(KOK + '/scripts/skill_lint.py', encoding='utf-8').read()
    agac = ast.parse(src)
    for d in agac.body:
        if (isinstance(d, ast.Assign) and isinstance(d.value, ast.List)
                and any(getattr(t, 'id', None) == ad for t in d.targets)):
            cikan, atlanan = [], 0
            for el in d.value.elts:
                try:
                    cikan.append(ast.literal_eval(el))
                except Exception:
                    atlanan += 1
            return cikan, atlanan
    return [], 0


def _bolum_aralik(ham):
    """{bolum_no: (bas, son)} — `## N.` basliklarina gore ham dilim."""
    parca = list(re.finditer(r'^## (\d+)\..*$', ham, re.M))
    aralik = {}
    for i, m in enumerate(parca):
        son = parca[i + 1].start() if i + 1 < len(parca) else len(ham)
        aralik[m.group(1)] = (m.start(), son)
    return aralik


def _katli_govdeler(ham):
    parcalar = re.split(r'^(## \d+\..*)$', ham, flags=re.M)
    sonuc, su = {}, None
    for p in parcalar:
        m = re.match(r'^## (\d+)\.', p)
        if m:
            su = m.group(1)
            sonuc.setdefault(su, '')
        elif su:
            sonuc[su] += p
    return {k: _katla(v) for k, v in sonuc.items()}


def _sayimlar(ham):
    """CAPA + C13 kapilarinin BELLEKTEKI durumu (lint'in kendi kurallari)."""
    govde = _katli_govdeler(ham)
    duz = _katla(ham)
    capa = _tablo('CAPA')[0]
    c13 = _tablo('C13')[0]
    durum = {}
    for no, _ad, bol, gerek in capa:
        g = govde.get(bol, '')
        durum[no] = all(_katla(t) in g for t in gerek)
    for no, _ad, bek in c13:
        ok = True
        for t, n in bek:
            if t.startswith('R:'):
                ger = len(re.findall(t[2:], ham))
            elif t.startswith('H:'):
                ger = ham.count(t[2:])
            else:
                ger = duz.count(_katla(t))
            if ger != n:
                ok = False
        durum[no] = ok
    return durum


def _aday_token(ham, kapi, gerek, bol):
    """Hedef kapı için token seçer ve BENZERSİZ bir ham dilim üretir.

    İKİ EKSİK GİDERİLDİ (Z39, ölçüldü):
      1. `adet > 1` token'lar atılıyordu. Oysa bir tanesini bozmak sayımı
         `n-1` yapar ve kural `TAM n` istediği için kapı DÜŞER.
      2. `eski` dosyada TAM 1 kez geçmeli (koşucunun şartı). Token 2+ kez
         geçiyorsa dilim SAĞA/SOLA GENİŞLETİLEREK benzersizleştirilir.
    """
    duz = _katla(ham)
    govde = _katli_govdeler(ham)
    aday = []
    for _e in gerek:
        t, n = (_e, 1) if isinstance(_e, str) else (_e[0], _e[1])
        if t.startswith('R:'):
            continue                     # regex çapası: bozmak ayrı iş
        ham_mu = t.startswith('H:')
        tok = t[2:] if ham_mu else t
        kt = tok if ham_mu else _katla(tok)
        if n < 1:
            continue
        if bol is not None:
            # CAPA: token bölüm gövdesinde GEÇMELİ; bir tanesini bozmak için
            # gövdede TAM 1 kez olmalı.
            if govde.get(bol, '').count(_katla(kt)) != 1:
                continue
        else:
            if (ham.count(kt) if ham_mu else duz.count(_katla(kt))) != n:
                continue
        pat = re.escape(kt) if ham_mu else ham_desen(kt)
        ms = list(re.finditer(pat, ham, re.I))
        if bol is not None:
            # CAPA: yalniz HEDEF BOLUMUN govdesindeki eslesme ise yarar.
            # (`§3.3/3` belgede 2 kez: biri §6 govdesinde, biri `§3.3/3b`
            #  onekinde — ikincisi onek yuzunden desene de takiliyor.)
            _b0, _b1 = _bolum_aralik(ham).get(bol, (0, 0))
            ms = [m for m in ms if _b0 <= m.start() < _b1]
        if len(ms) < n:
            continue                     # desen ile sayım uyuşmuyor -> güvenli değil
        for m in ms:
            s0, e0 = m.start(), m.end()
            if e0 - s0 < 6:
                continue
            s, e, adim = s0, e0, 0
            while ham.count(ham[s:e]) != 1 and adim < 80:
                adim += 1
                if s > 0:
                    s -= 1
                    if ham.count(ham[s:e]) == 1:
                        break
                if e < len(ham):
                    e += 1
            if ham.count(ham[s:e]) != 1:
                continue
            mm = re.search(pat, ham[s:e], re.I)
            if not mm:
                continue
            orta = s + mm.start() + (mm.end() - mm.start()) // 2
            aday.append((e - s, kt, ham[s:orta], ham[orta:e]))
    if not aday:
        return None
    aday.sort(key=lambda x: x[0])        # en KISA benzersiz dilim
    _, kt, sol, sag = aday[0]
    return kt, sol + 'Q' + sag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kalan', required=True)
    ap.add_argument('--cikti', required=True)
    a = ap.parse_args()

    kalan = set(json.load(io.open(a.kalan, encoding='utf-8')))
    ham = io.open(KOK + '/SKILL.md', encoding='utf-8').read()
    taban = _sayimlar(ham)

    capa, capa_at = _tablo('CAPA')
    c13, c13_at = _tablo('C13')
    print('CAPA eleman=%d (cozulemeyen %d) · C13 eleman=%d (cozulemeyen %d)'
          % (len(capa), capa_at, len(c13), c13_at))

    hedefler = []
    for no, ad, bol, gerek in capa:
        if no in kalan:
            hedefler.append((no, ad, gerek, bol))
    for no, ad, bek in c13:
        if no in kalan:
            hedefler.append((no, ad, bek, None))
    print('hedef kapı (kalan icinde + tabloda): %d' % len(hedefler))

    oneri, bulunamayan = [], []
    for no, ad, gerek, bol in hedefler:
        if not taban.get(no, False):
            print('  %-7s ATLANDI: taban durumu PASS degil' % no)
            continue
        sec = _aday_token(ham, no, gerek, bol)
        if not sec:
            bulunamayan.append(no)
            print('  %-7s --  TAM 1 gecen bozulabilir token yok' % no)
            continue
        tok, yeni = sec
        # `eski`, `yeni`den Q cikarilarak degil DOGRUDAN uretilir: dilim
        # benzersizlestirmek icin genisletildigi icin Q'nun yeri dilimin
        # ortasi DEGILDIR.
        eski = yeni.replace('Q', '', 1)
        if len(eski) < 6:
            bulunamayan.append(no)
            print('  %-7s --  dilim cok kisa (%d): %r' % (no, len(eski), eski))
            continue
        # BELLEKTE on olcum: mutasyon uygulanmis metinde hangi kapilar donuyor?
        mutlu = ham.replace(eski, yeni, 1)
        sonra = _sayimlar(mutlu)
        donen = sorted(g for g in sonra if taban.get(g) and not sonra[g])
        if no not in donen:
            bulunamayan.append(no)
            print('  %-7s --  on olcum: mutasyon bu kapıyı KIMILDATMIYOR' % no)
            continue
        oneri.append({'kapi': no, 'ad': 'token bozuldu: %s' % tok[:44],
                      'dosya': 'SKILL.md', 'eski': eski, 'yeni': yeni,
                      'on_olcum_donen': donen})
        etiket = '' if donen == [no] else '  YAN ETKI(ON): %s' % ','.join(
            x for x in donen if x != no)
        print('  %-7s OK  %-44r donen=%s%s'
              % (no, eski[:42], ','.join(donen), etiket))

    # PAYLASILAN: ayni `eski` birden fazla kapıya yazilmaz (tek mutasyon = tek kanit)
    sayac = {}
    for o in oneri:
        sayac.setdefault(o['eski'], []).append(o['kapi'])
    paylasilan = {e for e, ks in sayac.items() if len(ks) > 1}
    if paylasilan:
        print('\nPAYLASILAN (elendi): %s' % {e[:30]: [o['kapi'] for o in oneri
                                                     if o['eski'] == e]
                                             for e in paylasilan})
    oneri = [o for o in oneri if o['eski'] not in paylasilan]

    io.open(a.cikti, 'w', encoding='utf-8').write(
        json.dumps(oneri, ensure_ascii=False, indent=1))
    print('\nYAZILDI: %s · %d oneri · %d kapi icin token yok'
          % (a.cikti, len(oneri), len(bulunamayan)))
    if bulunamayan:
        print('TOKEN YOK: %s' % ', '.join(sorted(bulunamayan)))


if __name__ == '__main__':
    main()
