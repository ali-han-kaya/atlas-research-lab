#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kapi farki — ARAC_DEGISTI mi, KIMLIK_DEGISTI mi? (dis denetim D11, 8 Kasim 2026)

NEDEN (olculmus kusur): kimlik listesi her komutun cagirdigi betigin sha256'sini
tasir. Betige YENI BIR KAPI eklenince sha degisir; metin ise "yeni kapi eklemek
KIMLIK_DEGISTI degil EKLENEN sayilir" diyordu. Bu, kapilari ZAYIFLATAN bir
degisikligin de "EKLENEN" diye beyan edilmesine kapi acar — ayirt eden OLCUM yoktu.

Bu betik olcer: iki surum arasinda
  EKLENEN    : yeni kapi kimligi (zararsiz — kaydedilir)
  KALDIRILAN : kapi kayboldu            -> rc=1 (KIMLIK_DEGISTI)
  GEVSETILEN : capa/count gevsetildi    -> rc=1 (KIMLIK_DEGISTI)
  KOSUL_DEGISTI : ayni kimlik, DEGISIK boolean olcut -> rc=1 (D11)
  AYNI       : kimlik kumesi ayni, capalar ayni, kosullar ayni

Kullanim:
  kapi_farki.py --taban scripts/tests/kapi_taban.json      # karsilastir
  kapi_farki.py --taban A.py --guncel B.py                 # iki dosya
  kapi_farki.py --yaz T.json --kabul C14p,C14q             # taban yaz (KABUL ADIYLA)
  kapi_farki.py --yaz T.json                              # fark varsa REDDEDER

NEDEN `--kabul` ZORUNLU (12 Kasim 2026, olculdu): Z1 turunda `--yaz` cagrildi ve
`C14o`nun kosul parmak izi sessizce tabana yazildi. Degisiklik beklendikti ama
"beklenen miydi" sorusu HIC sorulmadi; fark ancak elle okundu. Bu, gercek bir
olcut degisikligini "taban guncellendi" cilasi altinda gizleyebilir. Artik:
  * fark VARSA ve `--kabul` yoksa  -> RED, rc=1, degisenler listelenir
  * `--kabul` listesinde OLMAYAN degisiklik -> RED, rc=1
  * fark YOKSA -> yazar (kabul gerekmez)
"""
import ast
import hashlib
import json
import os
import sys


# Bir kapinin olcutunu kuran TOLERANS ifadeleri (14 Kasim 2026, Z29).
# Yalniz liste/sozluk/kume toplayicilari — bunlar "olcutu BUYUTEN" cagrilardir.
# `print`/`sys.exit` gibi yan etkiler BILEREK disarida: parmak izini
# gurultulendirir, sinyali eritir.
_MUTASYON = frozenset({'append', 'extend', 'add', 'update', 'insert',
                       'setdefault', 'appendleft'})


def _kosul_metni(dugum):
    """`if/while/for` dugumunun OLCUT kismi (govde haric)."""
    try:
        if isinstance(dugum, (ast.If, ast.While)):
            return ast.unparse(dugum.test)
        if isinstance(dugum, (ast.For, ast.AsyncFor)):
            return '%s in %s' % (ast.unparse(dugum.target),
                                 ast.unparse(dugum.iter))
    except Exception:
        return ''
    return ''


def _tanimlar(agac):
    """isim -> [(yer, tanim kaynagi)] — HER YERDEN, yalniz modul duzeyinden degil.

    M-B mutasyonu (11.11.2026): ilk yazim yalniz `agac.body` geziyordu. `_g14v_ok`
    modul duzeyinde `= False` tanimli ama gercek atama bir `try:` blogunun icinde;
    `_g14v_ok = True` yapildiginda arac AYNI dedi (rc=0, beklenen 1). Yani dolayli
    gevsetme gorunmez kaldi — duzeltmenin kendisi ayni kusuru tasiyordu.

    UCUNCU HALKA (Z29, 14 Kasim 2026) — TOLERANS + KONTROL AKISI -------------
    NEDEN (olculdu): eski surum yalniz Assign/AnnAssign/AugAssign/def topluyordu.
    Bir kapinin olcutu cogu zaman TOLERANS ile kurulur:

        if _n_htar != 0:
            _h15.append('ters_hukum_fark=%d ...' % _n_htar)

    Iki parca da TANIM SAYILMIYORDU: `_h15.append(...)` bir `ast.Expr`, `if` bir
    `ast.If`. OLCULDU (skill_lint.py): `_h15.append` cagrisi **15 adet**, `_h15`
    tanim sayisi **1** (yalniz bos liste atamasi) -> 15 hata kosulundan HICBIRI
    izlenmiyordu. OLCULDU (etki): dort somut mutasyon araca **GORUNMEDI**
    ("SONUC: AYNI"):
      M154 `_INKAR15_MESAFE_ZAYIF = 25 -> 60`   (Z28 duzeltmesini gevsetir)
      M155 `_YASAK15` listesine yeni desen ekleme
      M156 `if _n_htar != 0:` -> `if False and ...`
      M157 `if not _d_notr:`   -> `if False and ...`
    Yani C15n'in olcutunu degistirmek taban farkinda gorunmuyordu; Z28'de
    yaptigim duzeltmenin KENDISI bu kapidan gecmedi.

    DUZELTME IKI PARCALI (ikincisi ilk denemede EKSIKTI, olculdu):
      (a) toplayici cagrilar (`append/extend/add/...`) ilgili adin tanimi sayilir;
      (b) o cagriyi SARMALAYAN `if/while/for` KOSULU da ayni adin tanimi sayilir.
          (a) tek basina yetmedi: append metni kosulu icermiyor.
    Parca metni `yer` (satir no) ile siralanir; sira kararli kalir.
    """
    m = {}
    for d in ast.walk(agac):
        hedefler = []
        if isinstance(d, ast.Assign):
            hedefler = [x.id for x in d.targets if isinstance(x, ast.Name)]
        elif isinstance(d, ast.AnnAssign):
            hedefler = [d.target.id] if isinstance(d.target, ast.Name) else []
        elif isinstance(d, ast.AugAssign):
            hedefler = [d.target.id] if isinstance(d.target, ast.Name) else []
        elif isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            hedefler = [d.name]
        elif isinstance(d, ast.Expr) and isinstance(d.value, ast.Call) \
                and isinstance(d.value.func, ast.Attribute) \
                and d.value.func.attr in _MUTASYON \
                and isinstance(d.value.func.value, ast.Name):
            hedefler = [d.value.func.value.id]
        for ad in hedefler:
            m.setdefault(ad, []).append((d.lineno, ast.unparse(d)))
    # (b) sarmalayici kontrol akisi kosullari — ayni adin tanimi sayilir.
    for kok in ast.walk(agac):
        if not isinstance(kok, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            continue
        kosul = _kosul_metni(kok)
        if not kosul:
            continue
        for alt in kok.body + list(getattr(kok, 'orelse', [])):
            for d in ast.walk(alt):
                if isinstance(d, ast.Expr) and isinstance(d.value, ast.Call) \
                        and isinstance(d.value.func, ast.Attribute) \
                        and d.value.func.attr in _MUTASYON \
                        and isinstance(d.value.func.value, ast.Name):
                    m.setdefault(d.value.func.value.id, []).append(
                        (d.lineno, kosul))
    # (c) BEKCI kosullari: `if X: continue` bir mutasyonu ATLAR — yani kapinin
    # olcutunun parcasidir, ama ne mutasyon ne atamadir. OLCULDU (M154):
    # `_inkar15_var(...): continue` bekcisi kapanista YOKTU; `_INKAR15_MESAFE_ZAYIF`
    # 25->60 yapildiginda arac "AYNI" dedi. Bekci, ait oldugu dongudeki tum
    # toplayicilarin tanimi sayilir.
    for kok in ast.walk(agac):
        if not isinstance(kok, (ast.If,)):
            continue
        if not _sonlanir(kok.body):
            continue
        kosul = _kosul_metni(kok)
        if not kosul:
            continue
        for dongu in _donguler(agac):
            if not _kapsar(dongu, kok):
                continue
            for d in ast.walk(dongu):
                if isinstance(d, ast.Expr) and isinstance(d.value, ast.Call) \
                        and isinstance(d.value.func, ast.Attribute) \
                        and d.value.func.attr in _MUTASYON \
                        and isinstance(d.value.func.value, ast.Name):
                    m.setdefault(d.value.func.value.id, []).append(
                        (d.lineno, kosul))
    return {ad: [x[1] for x in sorted(v)] for ad, v in m.items()}


def _sonlanir(govde):
    """Govde `continue`/`break`/`return`/`raise` ile kesiliyor mu?"""
    for d in govde:
        if isinstance(d, (ast.Continue, ast.Break, ast.Return, ast.Raise)):
            return True
        if isinstance(d, ast.If) and _sonlanir(d.body) and _sonlanir(d.orelse):
            return True
    return any(isinstance(x, (ast.Continue, ast.Break, ast.Return, ast.Raise))
               for d in govde for x in ast.walk(d)
               if isinstance(x, (ast.Continue, ast.Break, ast.Return)))


def _donguler(agac):
    return [d for d in ast.walk(agac)
            if isinstance(d, (ast.For, ast.AsyncFor, ast.While))]


def _kapsar(dongu, dugum):
    """`dugum`, `dongu`nun govdesinde mi (ic ice olabilir)?"""
    for d in ast.walk(dongu):
        if d is dugum:
            return True
    return False


def _kosul_parmak(kosul, tanimlar, derinlik=None):
    """Kapinin kosulu + ona BAGLI olan tum tanimlar -> sha256.

    D11 (11.11.2026): kimlik dizesi kapinin NE dedigini, kosul ise NE OLCUTUGUNU
    soyler. Yalniz kimligi hash'lemek, olcutu degistirip adi birakma yolunu acik
    birakiyordu: `not _bulunan_sayac` -> `True` yazildiginda arac AYNI diyordu.

    DERINLIK: SABIT DEGIL, KAPANIS (C-#3, 14 Kasim 2026) ---------------------
    NEDEN (olculdu): eski imza `derinlik=2` idi. Kapinin kosulu bir yardimciyi
    cagiriyorsa o yardimcinin GOVDESI kapsama giriyordu; ama o yardimcinin
    cagirdigi UCUNCU halkadaki kod GIRMIYORDU. Olculdu: skill_lint.py'de
    **189 ad** yalniz derinlik>=3'te gorunuyor (`YOL` -> 26 kapi,
    `_bayrak` -> 26, `_h` -> 23). Yani bir kapinin olcumunu derinde
    GUVCLENDIRMEK parmak izini DEGISTIRMIYORDU -> arac `AYNI` diyordu.
    Bu, D11'in kapattigi kusurun (olcutu degistir, adi birak) bir halka
    derindeki kopyasidir.
    Artik kuyruk KAPANISA kadar bosaltilir (`gorulen` kumesi donguyu keser).
    `derinlik=N` yalniz OLCUM icin verilebilir (eski davranisi yeniden uretmek).
    BEDELI (gizlenmez): baglasim artar — ayni yardimciyi okuyan kapilar
    birlikte degisir. Ortalama **14,4 ad/kapi**; 57 kapinin 55'i farkli
    parmak izi TASIYOR (yani sinyal tek izde erimiyor, olculdu).
    """
    parcalar = [ast.unparse(kosul)]
    gorulen, kuyruk = set(), [kosul]
    tur = 0
    while kuyruk and (derinlik is None or tur < derinlik):
        yeni = []
        for dugum in kuyruk:
            for dugum2 in ast.walk(dugum):
                if isinstance(dugum2, ast.Name) and dugum2.id in tanimlar \
                        and dugum2.id not in gorulen:
                    gorulen.add(dugum2.id)
                    for kaynak in tanimlar[dugum2.id]:
                        parcalar.append(kaynak)
                        try:
                            yeni.append(ast.parse(kaynak).body[0])
                        except SyntaxError:
                            pass
        kuyruk = yeni
        tur += 1
    return hashlib.sha256('\n'.join(parcalar).encode('utf-8')).hexdigest()[:16]


def kapilar(yol):
    """Kaynak dosyadan kapi kimlikleri + C13 capalari + KOSUL parmak izleri."""
    kaynak = open(yol, encoding='utf-8').read()
    agac = ast.parse(kaynak)
    tanimlar = _tanimlar(agac)
    kimlikler = []
    capalar = {}
    kosullar = {}
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Call) and isinstance(dugum.func, ast.Name) \
                and dugum.func.id == 'k' and dugum.args:
            ilk = dugum.args[0]
            if isinstance(ilk, ast.Constant) and isinstance(ilk.value, str):
                kimlikler.append(ilk.value)
                if len(dugum.args) >= 3:
                    kosullar.setdefault(ilk.value, []).append(
                        _kosul_parmak(dugum.args[2], tanimlar))
        if isinstance(dugum, ast.Assign) and dugum.targets \
                and isinstance(dugum.targets[0], ast.Name) \
                and dugum.targets[0].id == 'C13':
            for oge in dugum.value.elts:
                if not isinstance(oge, ast.Tuple) or len(oge.elts) < 3:
                    continue
                ad = oge.elts[0]
                cap = oge.elts[2]
                if not isinstance(ad, ast.Constant):
                    continue
                liste = []
                if isinstance(cap, ast.List):
                    for ikili in cap.elts:
                        if isinstance(ikili, ast.Tuple) and len(ikili.elts) == 2:
                            try:
                                liste.append([ast.literal_eval(ikili.elts[0]),
                                              ast.literal_eval(ikili.elts[1])])
                            except Exception:
                                liste.append(['<okunamadi>', None])
                capalar[ad.value] = liste
    return {'kimlikler': sorted(set(kimlikler) | set(capalar.keys())),
            'capalar': capalar,
            'kosullar': {ad: sorted(v) for ad, v in kosullar.items()}}


def karsilastir(eski, yeni):
    a, b = set(eski['kimlikler']), set(yeni['kimlikler'])
    eklenen = sorted(b - a)
    kaldirilan = sorted(a - b)
    gevsetilen = []
    for ad in sorted(a & b):
        once = eski['capalar'].get(ad)
        sonra = yeni['capalar'].get(ad)
        if once is None and sonra is None:
            continue
        if once != sonra:
            # GEVSETME: capa kaldirilmis ya da beklenen sayi DUSMUS.
            d = []
            if once and not sonra:
                d.append('capalar silindi')
            else:
                once_m = {c[0]: c[1] for c in (once or [])}
                sonra_m = {c[0]: c[1] for c in (sonra or [])}
                for k, v in once_m.items():
                    if k not in sonra_m:
                        d.append('capa kaldirildi: %s' % k[:30])
                    elif isinstance(v, int) and isinstance(sonra_m[k], int) \
                            and sonra_m[k] < v:
                        d.append('beklenen dustu: %s %s->%s' % (k[:24], v, sonra_m[k]))
            if d:
                gevsetilen.append({'kapi': ad, 'neden': d})
    # KOSUL DEGISIMI (D11, 11.11.2026): kimlik ayni kalip olcut degisebilir.
    # Gevseme mi sikilasma mi oldugu KARAR PROBLEMI — ikisi de taban guncellemesi
    # (ayri commit + denetim) ister. Fail-closed: degisim varsa rc=1.
    kok = []
    ko, kn = eski.get('kosullar'), yeni.get('kosullar')
    if ko is None:
        kok.append({'kapi': '<TABAN>',
                    'neden': ["tabanda 'kosullar' yok — kosul denetimi KAPALI",
                              'taban --yaz ile yeniden uretilmeli']})
    else:
        # M-C (11.11.2026): yalniz IKI TARAFTA DA olan kimlikler. Yeni kimlik
        # EKLENEN'dir; parmak izi None -> <hash> diye KOSUL_DEGISTI sayilamaz.
        for ad in sorted(set(ko) & set(kn or {})):
            if ko[ad] != kn[ad]:
                kok.append({'kapi': ad, 'neden': ['kosul parmak izi degisti']})
    return eklenen, kaldirilan, gevsetilen, kok


def main(argv):
    taban = guncel = None
    yaz = None
    kabul = None
    i = 1
    while i < len(argv):
        if argv[i] == '--taban':
            taban = argv[i + 1]; i += 2
        elif argv[i] == '--guncel':
            guncel = argv[i + 1]; i += 2
        elif argv[i] == '--yaz':
            yaz = argv[i + 1]; i += 2
        elif argv[i] == '--kabul':
            kabul = [x.strip() for x in argv[i + 1].split(',') if x.strip()]
            i += 2
        else:
            print('HATA: bilinmeyen arguman %s' % argv[i]); return 2
    hedef = guncel or __file__.replace('kapi_farki.py', 'skill_lint.py')
    if yaz:
        veri = kapilar(hedef)
        # KORKULUK (12 Kasim 2026): taban yazmak, olcut degisikligini ONAYLAMAK
        # demektir. Onay ADIYLA verilir; aksi halde sessiz gecis olur.
        if os.path.exists(yaz):
            try:
                eski = json.load(open(yaz, encoding='utf-8'))
            except Exception as _e:
                print('HATA: taban okunamadi (%s) — yazma REDDEDILDI' % _e)
                return 1
            eklenen, kaldirilan, gevsetilen, kok = karsilastir(eski, veri)
            degisen = sorted(set(kaldirilan) | set(eklenen)
                             | {g['kapi'] for g in gevsetilen}
                             | {g['kapi'] for g in kok})
            if degisen:
                print('TABAN DEGISECEK (%d): %s' % (len(degisen), ', '.join(degisen)))
                if kaldirilan:
                    print('  KALDIRILAN: %s' % ', '.join(kaldirilan))
                for g in gevsetilen:
                    print('  GEVSETILEN %s — %s' % (g['kapi'], '; '.join(g['neden'])))
                for g in kok:
                    print('  KOSUL_DEGISTI %s — %s' % (g['kapi'], '; '.join(g['neden'])))
                if kabul is None:
                    print('RED: --kabul <kimlik,...> gerekli.')
                    print('     Her degisikligi ADIYLA kabul et; "hepsi" diye '
                          'toplu kabul YOK.')
                    print('     Kabul edilecekler: %s' % ','.join(degisen))
                    return 1
                fazla = [x for x in degisen if x not in kabul]
                if fazla:
                    print('RED: kabul listesinde OLMAYAN degisiklik: %s'
                          % ', '.join(fazla))
                    return 1
                print('KABUL: %s' % ', '.join(sorted(kabul)))
            else:
                print('TABAN DEGISMIYOR (fark yok)')
        # ATOMIK YAZ (12 Kasim 2026, Z8): eski hali
        # `json.dump(veri, open(yaz, 'w'))` idi — hata olursa taban YARIM kalir.
        # Olculdu (ayni desen): 44 bayt -> 9 bayt, icerik `{"veri": `.
        from atomik_yaz import yaz_json
        n = yaz_json(yaz, veri, indent=1, sort_keys=True)
        print('YAZILDI: %s · %d kimlik · %d bayt (atomik)'
              % (yaz, len(veri['kimlikler']), n))
        return 0
    if not taban:
        print('HATA: --taban ya da --yaz gerekli'); return 2
    eski = json.load(open(taban, encoding='utf-8'))
    yeni = kapilar(hedef)
    eklenen, kaldirilan, gevsetilen, kok = karsilastir(eski, yeni)
    print('EKLENEN: %s' % (', '.join(eklenen) if eklenen else '-'))
    print('KALDIRILAN: %s' % (', '.join(kaldirilan) if kaldirilan else '-'))
    if gevsetilen:
        print('GEVSETILEN:')
        for g in gevsetilen:
            print('  %s — %s' % (g['kapi'], '; '.join(g['neden'])))
    else:
        print('GEVSETILEN: -')
    if kok:
        print('KOSUL_DEGISTI:')
        for g in kok:
            print('  %s — %s' % (g['kapi'], '; '.join(g['neden'])))
    else:
        print('KOSUL_DEGISTI: -')
    if kaldirilan or gevsetilen:
        print('SONUC: KIMLIK_DEGISTI (kapi kaldirildi/gevsetildi)')
        return 1
    if kok:
        print('SONUC: KOSUL_DEGISTI (kapi olcutu degisti — taban + denetim gerekli)')
        return 1
    if eklenen:
        print('SONUC: ARAC_DEGISTI (yalniz ekleme — taban guncellenmeli)')
        return 0
    print('SONUC: AYNI')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
