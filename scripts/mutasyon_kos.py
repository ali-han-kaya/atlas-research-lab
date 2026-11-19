#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutasyon_kos.py — deklaratif mutasyon KOSUCUSU (14 Kasim 2026, Z33)

NEDEN (olculdu): `mutasyon_tara` 95 kapinin 47'sinde SERT kanit buluyor ama
o kanitlarin neredeyse tamami ELLE yazilmis tablo satirlari (`| 0 | **1** |`).
Satiri URETEN bir kosum kaydi yoktu. Yani "kanit" hala IDDIA duzeyindeydi:
satirin dogru oldugunu kimse olcmedi. Bu betik mutasyonu KOSAR, cikis kodunu
ve kapi satirini OLCER, satiri URETIR.

TASARIM — her adim tek amacli:
  1. `git status --porcelain` BOS degilse DUR (fail-closed). Temiz olmayan
     agacta mutasyon kosmak, kullanicinin isini geri alma riski tasir.
  2. Taban lint bir kez kosar; hedef kapi tabanda PASS degilse UYARI verilir
     (kirmizi kapiyi mutasyonla "kanitlamak" kanit degildir).
  3. Her mutasyon: `eski` metni dosyada TAM 1 kez gecmeli. 0 ya da >1 ise
     DUR — belirsiz mutasyon kanit uretmez.
  4. Mutasyon uygulanir -> lint kosar -> kapi satiri + rc kaydedilir.
  5. `finally`: dosya BAYT duzeyinde geri yazilir, sha256 KARSILASTIRILIR.
     Farkli ise FAIL (sessiz bozulma yok).
  6. `atexit` + SIGINT/SIGTERM: kesinti halinde de geri yazilir.

CIKTI: `| <kapi> | <ad> | <once> | **<sonra>** | <cikti> |` satiri — yani
`mutasyon_tara._SERT_EXIT` deseninin (`\\|\\s*[01]\\s*\\|\\s*\\*\\*[01]\\*\\*\\s*\\|`)
ARADIGI bicim. Boylece kanit, onu URETEN kosumla AYNI satirda durur.

KULLANIM:
  python3 scripts/mutasyon_kos.py --kuru            # sadece eski metin kontrolu
  python3 scripts/mutasyon_kos.py                   # listeyi kos
  python3 scripts/mutasyon_kos.py --kapi C14e       # tek kapi
  python3 scripts/mutasyon_kos.py --yaz             # docs/MUTASYON_KOSUM.md'ye ekle
"""

import argparse
import atexit
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BURASI)
LINT = os.path.join(BURASI, 'skill_lint.py')
LISTE = os.path.join(BURASI, 'tests', 'mutasyon_listesi.json')
KAYIT = os.path.join(BURASI, 'tests', 'mutasyon_kosum.json')
KOSUM_MD = os.path.join(KOK, 'docs', 'MUTASYON_KOSUM.md')

_HIZ = 2400          # tek lint kosumu icin ust sinir (s)
_GERI = []           # (yol, orijinal baytlar) — kesintide geri yazilir
# (Z43) DOSYA OLUSTURAN mutasyonlar: kesintide SILINIR. Ayri liste cunku
# `_GERI` '(yol, bayt)' tutar; yeni dosyanin bayti YOKTUR — silinmesi
# gerekir, geri yazilmasi degil.
_YENI = []           # olusturulan dosya yollari — kesintide silinir


# --- yardimcilar -----------------------------------------------------------
def _sha(yol):
    h = hashlib.sha256()
    with open(yol, 'rb') as f:
        for parca in iter(lambda: f.read(1 << 16), b''):
            h.update(parca)
    return h.hexdigest()


def _kapi_satiri(satir):
    """`k()` ciktisini (kimlik, durum, ayrinti) olarak ayirir.

    Bicim: `'  %-3s %-46s %s %s' % (no, ad, durum, ayrinti)`.
    Yani kimlik en az 3, ad alani en az 46 genis. Durum, ad alanindan SONRA
    gelir; bu yuzden tarama `ad_bas + 47`den baslar. Ad 46'dan uzunsa durum
    daha saga kayar — tarama bunu karsilar.
    """
    m = re.match(r'^  (\S+) ', satir)
    if not m:
        return None
    kim = m.group(1)
    ad_bas = 2 + max(3, len(kim)) + 1
    p = ad_bas + 47
    while p < len(satir) - 4:
        if (satir[p - 1] == ' ' and satir[p:p + 4] in ('PASS', 'FAIL')
                and (p + 4 == len(satir) or satir[p + 4] == ' ')):
            return kim, satir[p:p + 4], satir[p + 5:].strip()
        p += 1
    return None


def _geri_yaz():
    """Kesinti/ozi olursa dokunulmus dosyalari orijinal baytlarina dondur."""
    for yol, bayt in _GERI:
        try:
            with open(yol, 'wb') as f:
                f.write(bayt)
        except Exception:
            pass
    del _GERI[:]
    for yol in list(_YENI):
        try:
            if os.path.exists(yol):
                os.unlink(yol)
        except Exception:
            pass
    del _YENI[:]


def _sinyal(say, _cerceve):
    _geri_yaz()
    print('\nKESINTI: dosyalar geri yazildi (signal %s)' % say)
    sys.exit(130)


atexit.register(_geri_yaz)
for _s in (signal.SIGINT, signal.SIGTERM):
    try:
        signal.signal(_s, _sinyal)
    except Exception:
        pass


def lint_kos():
    """lint'i kosar; kapi satirlarini sozluga cevirir."""
    t0 = time.time()
    try:
        # TIMEOUT LITERAL olmali: `C15j` subprocess cagrilarini STATIK tarar
        # ve `timeout=zaman` gibi degisken ifadeyi cozemez (olculdu: ilk
        # kosumda C15j FAIL verdi — "mutasyon_kos.py:116"). Bu yuzden sayi
        # burada acikca yazilir; `_HIZ` yalniz belge amacli durur.
        r = subprocess.run([sys.executable, LINT],
                           capture_output=True, text=True, timeout=2400)
    except subprocess.TimeoutExpired:
        return {'rc': None, 'zaman_asimi': True,
                'sure': round(time.time() - t0, 1), 'kapi': {},
                'son': '(ZAMAN ASIMI)'}
    kapi = {}
    for satir in r.stdout.splitlines():
        a = _kapi_satiri(satir)
        if a:
            kapi[a[0]] = (a[1], a[2])
    son = [s for s in r.stdout.splitlines() if s.startswith('SONUC:')]
    return {'rc': r.returncode, 'zaman_asimi': False,
            'sure': round(time.time() - t0, 1), 'kapi': kapi,
            'son': son[-1] if son else '(SONUC satiri yok)'}


def _temiz_mi(yol_rel):
    try:
        r = subprocess.run(['git', 'status', '--porcelain', '--', yol_rel],
                           cwd=KOK, capture_output=True, text=True, timeout=120)
    except Exception as e:
        return False, 'git status cagrilamadi: %s' % e
    if r.returncode != 0:
        return False, 'git status rc=%d' % r.returncode
    return (r.stdout.strip() == ''), r.stdout.strip()


_KAPI_ADI = re.compile(r'(?<![A-Za-z0-9])C\d+[a-z]?(?:-[a-z])?(?![0-9])')


def _maskele(metin, kapi):
    """Cikti hucresindeki BASKA kapi kimliklerini maskeler.

    NEDEN (olculdu, Z33): C18 satirinin ciktisi, H:tek kaynak C14t-a ciktisi
    capasini aniyor. `mutasyon_tara.tara()` satirdaki HER kimligi
    ayri ayri kaydettigi icin `C14t-a` da SERT kanitli gorundu — oysa satir
    `C18` hakkinda. Yani bir kapinin kaniti BASKA kapinin kaniti sayildi.
    Ayni sinif: toplu anma. Cozum: baska kimlikler hucrede maskelenir.
    """
    return _KAPI_ADI.sub(lambda m: m.group(0) if m.group(0) == kapi else '<baska-kapi>',
                         metin)


def _satir_uret(kapi, ad, once_rc, sonra_rc, durum, ayrinti):
    """DEVIR/markdown kanit satiri. `rc=` YANMA sinyalidir: `tara()` once onu
    arar, bulamazsa satiri HIC okumaz (ilk kosumda olculdu)."""
    return ('| `%s` | %s | %s | **%s** | rc=%s · %s |'
            % (kapi, _kisa(ad or '-'), once_rc, sonra_rc, sonra_rc,
               _maskele(_kisa('%s %s' % (durum, ayrinti), 58), kapi)))


def _kisa(metin, n=70):
    """Hucreye girecek metin: `|` YASAK (tablo sutununu boler)."""
    metin = (metin or '').replace('|', '/').replace('\n', ' ')
    metin = re.sub(r'\s+', ' ', metin).strip()
    return metin[:n]


# --- ana is ----------------------------------------------------------------
def kos(kayitlar, taban, yaz=False, ara=0.0):
    sonuclar = []
    for i, mk in enumerate(kayitlar, 1):
        kapi = mk['kapi']
        yol_rel = mk['dosya']
        yol = os.path.join(KOK, yol_rel)
        ad = mk.get('ad') or ''
        print('\n[%d/%d] %s · %s' % (i, len(kayitlar), kapi, yol_rel))

        # (Z43) IKI MUTASYON BICIMI:  `eski -> yeni` (metin)  ·  `yeni_dosya`
        # (dosya OLUSTUR). Ikincisi ZORUNLU: bazi kapilar FAIL yolunu ancak
        # YENI bir dosyayla gosterir (or. `C14x`: manifest disi yetim dosya —
        # mevcut bir dosyayi bozmak o yolu ACIMIYOR). Fail-closed: hedef
        # ONCEDEN VARSA dur; kullanicinin dosyasini ezme riski tasinmaz.
        yeni_mod = 'yeni_dosya' in mk
        if yeni_mod:
            if 'eski' in mk or 'yeni' in mk:
                print('  ATLANDI: `yeni_dosya` ile `eski/yeni` BIRLIKTE olamaz')
                sonuclar.append({'kapi': kapi, 'durum': 'BICIM_HATASI'})
                continue
            if os.path.exists(yol):
                print('  ATLANDI: hedef dosya ZATEN VAR: %s' % yol_rel)
                sonuclar.append({'kapi': kapi, 'durum': 'DOSYA_ZATEN_VAR'})
                continue
            if not os.path.isdir(os.path.dirname(yol)):
                print('  ATLANDI: ust dizin yok: %s'
                      % os.path.dirname(yol_rel))
                sonuclar.append({'kapi': kapi, 'durum': 'DIZIN_YOK'})
                continue
            orijinal = None
            metin = eski = yeni = None
            sha_once = None
        else:
            if not os.path.exists(yol):
                print('  ATLANDI: dosya yok')
                sonuclar.append({'kapi': kapi, 'durum': 'DOSYA_YOK'})
                continue

            temiz, kirli = _temiz_mi(yol_rel)
            if not temiz:
                print('  ATLANDI: dosyada commit edilmemis degisiklik: %s'
                      % kirli[:60])
                sonuclar.append({'kapi': kapi, 'durum': 'KIRLI_AGAC'})
                continue

            with open(yol, 'rb') as f:
                orijinal = f.read()
            metin = orijinal.decode('utf-8')
            eski = mk['eski']
            yeni = mk['yeni']
            sayi = metin.count(eski)
            if sayi != 1:
                print('  ATLANDI: `eski` metni %d kez geciyor (TAM 1 olmali)'
                      % sayi)
                sonuclar.append({'kapi': kapi, 'durum': 'BELIRSIZ',
                                 'gecis': sayi})
                continue

            sha_once = hashlib.sha256(orijinal).hexdigest()
        once_durum, _ = taban['kapi'].get(kapi, ('YOK', ''))
        if once_durum != 'PASS':
            print('  UYARI: kapi tabanda %s — mutasyon "kirmizi kapiyi kirmizi '
                  'gostermek" olabilir' % once_durum)

        if yeni_mod:
            _YENI.append(yol)
        else:
            _GERI.append((yol, orijinal))
        try:
            if yeni_mod:
                with open(yol, 'w', encoding='utf-8') as f:
                    f.write(mk['yeni_dosya'])
            else:
                with open(yol, 'wb') as f:
                    f.write(metin.replace(eski, yeni, 1).encode('utf-8'))
            s = lint_kos()
        finally:
            if yeni_mod:
                if os.path.exists(yol):
                    os.unlink(yol)
                if yol in _YENI:
                    _YENI.remove(yol)
            else:
                with open(yol, 'wb') as f:
                    f.write(orijinal)
                _GERI.remove((yol, orijinal))

        if yeni_mod:
            geri_ok = not os.path.exists(yol)
        else:
            sha_sonra = hashlib.sha256(open(yol, 'rb').read()).hexdigest()
            geri_ok = (sha_sonra == sha_once)
        if not geri_ok:
            print('  FAIL: geri alma BASARISIZ (dosya durumu bozuk) — DUR')
            sonuclar.append({'kapi': kapi, 'durum': 'GERI_ALMA_BASARISIZ'})
            return sonuclar

        durum, ayrinti = s['kapi'].get(kapi, ('YOK', ''))
        print('  lint rc=%s (%.1f s) · %s tabanda %s -> mutasyonda %s'
              % (s['rc'], s['sure'], kapi, once_durum, durum))
        print('  %s' % (ayrinti[:100] or '(ayrinti yok)'))
        # YAN ETKI: hedef disinda PASS->FAIL olan kapilar. Bunlar YOKSAYILMAZ;
        # "tek mutasyon tek kapi" iddiasi ancak bu liste olculerek kurulabilir.
        yan = sorted(k for k, (d, _a) in s['kapi'].items()
                     if taban['kapi'].get(k, ('YOK',))[0] == 'PASS' and d == 'FAIL')
        yan = [k for k in yan if k != kapi]
        if yan:
            print('  YAN ETKI (%d): %s' % (len(yan), ', '.join(yan[:10])))

        sonuc = {
            'kapi': kapi,
            'ad': ad,
            'dosya': yol_rel,
            'durum': 'OK',
            'zaman_asimi': s['zaman_asimi'],
            'lint_rc_once': taban['rc'],
            'lint_rc_sonra': s['rc'],
            'kapi_once': once_durum,
            'kapi_sonra': durum,
            'ayrinti_sonra': ayrinti,
            'yan_etki': yan,
            'sha_ayni': geri_ok,
            # `mutasyon_tara.tara()` ONCE yanma sinyali arar (rc=1 / YAKALADI /
            # yandi / kirmizi); sinyal yoksa satir HIC okunmaz ve SERT deseni
            # bosuna aranir. Ilk kosumda satiri `FAIL ...` diye yazdim, 5 kanit
            # deftere GIRMEDI (olculdu). Bu yuzden rc hucreye acikca girer.
            'satir': _satir_uret(kapi, ad, taban['rc'], s['rc'],
                                 durum, ayrinti),
        }
        sonuclar.append(sonuc)
        if ara:
            time.sleep(ara)
    return sonuclar


def main():
    ap = argparse.ArgumentParser(description='Deklaratif mutasyon kosucusu.')
    ap.add_argument('--liste', default=LISTE, help='mutasyon listesi (JSON)')
    ap.add_argument('--kapi', action='append', default=None,
                    help='yalniz bu kimlik(ler); birden fazla verilebilir')
    ap.add_argument('--yaz', action='store_true',
                    help='docs/MUTASYON_KOSUM.md dosyasina satirlari EKLE')
    ap.add_argument('--kuru', action='store_true',
                    help='lint KOSMAZ; yalniz `eski` metni TAM 1 kez geciyor mu')
    ap.add_argument('--json', action='store_true', help='sonucu JSON yaz')
    ap.add_argument('--md', action='store_true',
                    help='docs/MUTASYON_KOSUM.md dosyasini KAYITTAN yeniden uret')
    a = ap.parse_args()

    if a.md:
        if not os.path.exists(KAYIT):
            print('KAYIT YOK: %s' % KAYIT)
            return 2
        with open(KAYIT, encoding='utf-8') as f:
            _y = json.load(f)
        kosumlar = _y if isinstance(_y, list) else [_y]
        # Satir KAYITTAN DEGIL ALANLARDAN uretilir: eski formatli kayitlar
        # da (rc= eklenmeden once yazilmis) dogru satiri versin.
        satirlar = []
        for kk in kosumlar:
            for x in kk.get('sonuclar', []):
                if (x.get('durum') == 'OK' and x.get('kapi_once') == 'PASS'
                        and x.get('kapi_sonra') == 'FAIL'):
                    satirlar.append(_satir_uret(
                        x['kapi'], x.get('ad'), x['lint_rc_once'],
                        x['lint_rc_sonra'], x['kapi_sonra'],
                        x.get('ayrinti_sonra', '')))
        with open(KOSUM_MD, 'w', encoding='utf-8') as f:
            f.write('# MUTASYON KOŞUM KAYDI (üretilmiş)\n\n'
                    'Bu dosya **elle yazılmaz**. Üreten: `scripts/mutasyon_kos.py`. '
                    'Her satır gerçek bir mutasyon koşumundan gelir; `once | '
                    '**sonra**` hücreleri lint çıkış kodudur. Çıktı hücresinde '
                    '**başka** kapı kimlikleri `<baska-kapi>` diye maskelenir: '
                    'satır tek bir kapının kanıtıdır, başka kapıya kredi '
                    'yazılmasın diye.\n\n'
                    '| kapı | mutasyon | once | sonra | çıktı |\n'
                    '|---|---|---|---|---|\n')
            for sat in satirlar:
                f.write(sat + '\n')
        print('YAZILDI: %s · %d satir · %d kosum (kayittan)'
              % (os.path.relpath(KOSUM_MD, KOK), len(satirlar), len(kosumlar)))
        return 0

    if not os.path.exists(a.liste):
        print('LISTE YOK: %s' % a.liste)
        return 2
    with open(a.liste, encoding='utf-8') as f:
        kayitlar = json.load(f)
    if a.kapi:
        kayitlar = [k for k in kayitlar if k['kapi'] in set(a.kapi)]
    if not kayitlar:
        print('SECIM BOS: listede/--kapi icinde kayit yok')
        return 2

    # --- KURU: yalniz metin kontrolu
    if a.kuru:
        kotu = 0
        for mk in kayitlar:
            yol = os.path.join(KOK, mk['dosya'])
            if 'yeni_dosya' in mk:
                # (Z43) yeni dosya: VAR OLMAMALI ve ust dizin BULUNMALI
                var = os.path.exists(yol)
                dizin = os.path.isdir(os.path.dirname(yol))
                im = 'OK' if (not var and dizin) else (
                    'DOSYA ZATEN VAR' if var else 'UST DIZIN YOK')
                print('  %-8s %-30s %s' % (mk['kapi'], mk['dosya'], im))
                if var or not dizin:
                    kotu += 1
                continue
            if not os.path.exists(yol):
                print('  %-8s DOSYA YOK: %s' % (mk['kapi'], mk['dosya']))
                kotu += 1
                continue
            sayi = open(yol, encoding='utf-8').read().count(mk['eski'])
            im = 'OK' if sayi == 1 else 'TAM 1 OLMALI (%d)' % sayi
            print('  %-8s %-30s %s' % (mk['kapi'], mk['dosya'], im))
            if sayi != 1:
                kotu += 1
        print('\nKURU: %d kayit · %d sorunlu' % (len(kayitlar), kotu))
        return 0 if kotu == 0 else 1

    # --- fail-closed: agac temiz olmali
    r = subprocess.run(['git', 'status', '--porcelain'], cwd=KOK,
                       capture_output=True, text=True, timeout=180)
    if r.stdout.strip():
        print('DUR: agac temiz degil — mutasyon kosumu kullanicinin isini '
              'geri alma riski tasir. Once commit et.')
        print(r.stdout.strip()[:400])
        return 2

    print('MUTASYON KOSUMU · %d kayit' % len(kayitlar))
    t0 = time.time()
    print('taban lint kosuyor...')
    taban = lint_kos()
    print('  taban rc=%s (%.1f s) · %d kapi satiri'
          % (taban['rc'], taban['sure'], len(taban['kapi'])))
    if taban['zaman_asimi'] or taban['rc'] not in (0, 1):
        print('DUR: taban kosum saglikli degil (rc=%s)' % taban['rc'])
        return 2
    if taban['rc'] != 0:
        print('DUR: taban lint TEMIZ degil (rc=%s) — once onu duzelt'
              % taban['rc'])
        return 2

    sonuclar = kos(kayitlar, taban, yaz=a.yaz)

    ok = [s for s in sonuclar if s.get('durum') == 'OK']
    kanit = [s for s in ok
             if s['kapi_once'] == 'PASS' and s['kapi_sonra'] == 'FAIL'
             and s['lint_rc_sonra'] == 1 and s['sha_ayni']]
    print('\n%s' % ('=' * 66))
    print('KOSUM: %d kayit · %d kosuldu · %d KANIT (PASS->FAIL, rc 1, sha ayni)'
          % (len(sonuclar), len(ok), len(kanit)))
    for s in sonuclar:
        if s.get('durum') != 'OK':
            print('  ATLANDI %-8s %s' % (s['kapi'], s['durum']))
        elif not (s['kapi_once'] == 'PASS' and s['kapi_sonra'] == 'FAIL'):
            print('  KANIT DEGIL %-8s %s -> %s'
                  % (s['kapi'], s['kapi_once'], s['kapi_sonra']))
    print()
    print('URETILEN SATIRLAR:')
    for s in kanit:
        print('  ' + s['satir'])

    kayit = {'tarih': time.strftime('%Y-%m-%d %H:%M'),
             'taban_rc': taban['rc'], 'taban_sure': taban['sure'],
             'sure': round(time.time() - t0, 1),
             'kanit': len(kanit), 'sonuclar': sonuclar}
    # KAYIT BIRIKIMLI: onceki kosumlar SILINMEZ. Ilk surum tek kosum
    # tutuyordu ve `--md` ikinci partide birinci partinin satirlarini
    # SILEcekti (olculdu: tasarim hatasi, kosum yapilmadan fark edildi).
    _gecmis = []
    if os.path.exists(KAYIT):
        try:
            with open(KAYIT, encoding='utf-8') as f:
                _g = json.load(f)
            _gecmis = _g if isinstance(_g, list) else [_g]
        except Exception:
            _gecmis = []
    _gecmis.append(kayit)
    with open(KAYIT, 'w', encoding='utf-8') as f:
        json.dump(_gecmis, f, ensure_ascii=False, indent=1)
    print('\nKAYIT: %s (%d bayt)'
          % (os.path.relpath(KAYIT, KOK), os.path.getsize(KAYIT)))

    if a.yaz and kanit:
        yeni_mi = not os.path.exists(KOSUM_MD)
        with open(KOSUM_MD, 'a', encoding='utf-8') as f:
            if yeni_mi:
                f.write('# MUTASYON KOŞUM KAYDI (üretilmiş)\n\n'
                        'Bu dosya **elle yazılmaz**. Üreten: '
                        '`scripts/mutasyon_kos.py`. Her satır gerçek bir '
                        'mutasyon koşumundan gelir; `| once | **sonra** |` '
                        'hücreleri lint çıkış kodudur.\n\n'
                        '| kapı | mutasyon | once | sonra | çıktı |\n'
                        '|---|---|---|---|---|\n')
            f.write('\n## Koşum %s · %d kanıt\n\n'
                    % (time.strftime('%Y-%m-%d %H:%M'), len(kanit)))
            for s in kanit:
                f.write(s['satir'] + '\n')
        print('YAZILDI: %s (%d bayt)'
              % (os.path.relpath(KOSUM_MD, KOK), os.path.getsize(KOSUM_MD)))

    if a.json:
        print(json.dumps({'kanit': len(kanit),
                          'kapilar': [s['kapi'] for s in kanit]},
                         ensure_ascii=False))
    return 0 if len(kanit) == len(sonuclar) else 1


if __name__ == '__main__':
    sys.exit(main())
