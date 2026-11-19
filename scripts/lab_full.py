#!/usr/bin/env python3
"""lab_full.py — LABIN TEK KAPANIS GIRISI (fail-closed).

NEDEN (9 Kasim 2026): Kapanis protokolu AGENTS.md §2'de 4 komut, benim
kullandigim pratikte 8 komut olarak DAGINIK duruyordu. Her seferinde elle
tek tek kosuluyordu; biri atlanirsa kimse fark etmez. Otomasyonun ilk sarti:
TEK GIRIS, ve eksik kosan kapi PASS sayilmaz.

NE YAPAR: 8 kalemi SIRAYLA kosar, her birinin rc'sini ve ham ciktisinin son
satirini yazar, en sonda TEK HUKUM verir.

NE YAPMAZ — ve bu onemli: BU BETIK HAKEM DEGILDIR. Kendi isini onaylamaz
(`DENETIM_TIPI: OZ_DENETIM`). Yaptigi sey: kapilari kosmak ve rc'leri
toplamak. Hukum, rc'lerin toplamindan CIKAR, betigin gorusunden degil.

Kullanim:
    python3 scripts/lab_full.py            # tam (~125 s)
    python3 scripts/lab_full.py --hizli    # agir kapilar atlanir (~6 s)
    python3 scripts/lab_full.py --json     # makine okunur
    python3 scripts/lab_full.py --proje-zorunlu   # proje kirmizisi FAIL olsun

CIKIS KODU: 0 = hepsi gecti · 1 = en az bir kalem FAIL · 2 = kosulamadi
"""
import json
import os
import subprocess
import sys
import time

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BURASI)

# (kimlik, aciklama, komut, agir_mi)
KALEMLER = [
    ('K1', 'skill_lint (sayac)', [sys.executable, 'scripts/skill_lint.py',
                                  'SKILL.md'], False),
    ('K2', 'skill_lint --metin (yasak cumle)', [sys.executable,
                                                'scripts/skill_lint.py',
                                                '--metin', 'SKILL.md'], False),
    ('K3', 'kapi_farki --taban (taban bozulmadi)', [sys.executable,
                                                    'scripts/kapi_farki.py',
                                                    '--taban',
                                                    'scripts/tests/kapi_taban.json'],
     False),
    ('K4', 'mutasyon_tara (kanit sayaci)', [sys.executable,
                                            'scripts/mutasyon_tara.py'], False),
    ('K5', 'olgu_lint --dersler (OLGU-06)', [sys.executable,
                                             'ATLAS_SABLONLAR/scripts/olgu_lint.py',
                                             '--dersler'], False),
    ('K6', 'git fsck', ['git', 'fsck'], False),
    ('K7', 'git status --porcelain (bos olmali)', ['git', 'status',
                                                   '--porcelain'], False),
    ('K8', 'atlas_selftest (agir)', [sys.executable,
                                     'ATLAS_SABLONLAR/scripts/atlas_selftest.py'],
     True),
    ('K9', 'kod_selftest (agir)', [sys.executable,
                                   'KOD_SABLONLAR/scripts/kod_selftest.py'], True),
]

def proje_hukmu(proje_dizini):
    """Projenin KENDI FINAL-GATE hukmu (`gate/FINAL-GATE*.json` -> `verdict`).

    NEDEN (15 Kasim 2026, OLCULDU): `projeler_tara` bir projeyi yalniz
    `check_integrity.sh --full` DONUS KODUNA bakarak siniflandiriyordu. Oysa
    `silat-makale`nin kendi kapisi `PASS-PENDING-ETHICS` hukmu veriyor
    (`DEC-035/036` OPEN) ve projenin kaydi bunu "istenen davranis, hata
    degildir" diye yaziyor (`00-FAZ-0-...md:78`). rc ile siniﬂandirma, devir
    belgesi yazildigi anda o projeyi **YESIL** gosterirdi: kapinin kendi
    hukmu "insan onayi bekliyor" iken lab panosunda yesil yanmak SAHTE YESILdir.
    Hukum okunamazsa bos dizge doner; o zaman eski davranis (rc) gecerlidir —
    ama "hukum yok" ile "hukum YESIL" ayni sey sayilmaz.
    """
    try:
        for ad in sorted(os.listdir(os.path.join(proje_dizini, 'gate'))):
            if ad.startswith('FINAL-GATE') and ad.endswith('.json'):
                with open(os.path.join(proje_dizini, 'gate', ad),
                          encoding='utf-8') as f:
                    return str(json.load(f).get('verdict', '')).strip()
    except Exception:
        return ''
    return ''


def durum_belirle(rc, hukum):
    """(rc, proje hukmu) -> YESIL / KIRMIZI / INSAN_BEKLIYOR.

    Insan karari bekleyen hukukler YESIL sayilmaz. Liste ACIK: yeni bir
    "bekleme" hukmu eklenirse buraya da eklenir; sessizce YESIL'e dusmez.
    """
    if rc != 0:
        return 'KIRMIZI'
    for on_ek in ('PASS-PENDING', 'BLOCKED', 'HUMAN_REVIEW'):
        if hukum.upper().startswith(on_ek):
            return 'INSAN_BEKLIYOR'
    return 'YESIL'


def projeler_tara(kok=None):
    """`projeler/*/` altindaki makale projelerinin durumunu OLCER.

    NEDEN (10 Kasim 2026): Lab kapanisi 9 kalemle kendi kapilarini dogruluyordu
    ama ICINDE BARINDIRDIGI makale projelerini HIC gormuyordu. Olculdu: lab 6
    proje barindiriyor, 1'i YESIL, 2'si KIRMIZI, 3'u baslamamis — ve bu durum
    herhangi bir kapanis ciktisinda GORUNMUYORDU. Gorunmeyen durum, olmayan
    durum degildir ama oyle sanilir.

    SINIFLANDIRMA — ve neden boyle:
      BASLAMADI : `00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md` yok. Proje henuz
                  ATLAS hattina girmemis; FAIL saymak yanlis olur (yanlis
                  alarm, gercek alarmi degersizlestirir).
      YESIL     : faz0 var + `--full` rc=0.
      KIRMIZI   : faz0 var + `--full` rc!=0. GERCEK kusur.

    BU KALEM HUKME GIRMEZ (gorunurluk kalemi). Sebep: `projeler/` altindaki
    isler AYRI islerdir; MIDEO makalesinin icerigi AGENTS.md §5 geregi
    dokunulmaz. Lab kapanisini onlarin durumuna baglamak, labi kapatamaz hale
    getirir. Bunun yerine durum HER KOSUDA basilir — sessizlik yasak.
    `--proje-zorunlu` verilirse KIRMIZI proje labi FAIL yapar.

    Donus: (liste, ozet_metni)
    """
    kok = kok or KOK
    kok_dizin = os.path.join(kok, 'projeler')
    if not os.path.isdir(kok_dizin):
        return [], 'projeler/ yok'
    satirlar = []
    for ad in sorted(os.listdir(kok_dizin)):
        d = os.path.join(kok_dizin, ad)
        if not os.path.isdir(d):
            continue
        faz0 = os.path.join(d, '00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md')
        if not os.path.exists(faz0):
            satirlar.append({'ad': ad, 'durum': 'BASLAMADI', 'rc': None,
                             'son': 'faz0 yok'})
            continue
        # Projenin KENDI betigi varsa o kullanilir; yoksa ATLAS sablonu.
        kendi = os.path.join(d, 'scripts', 'check_integrity.sh')
        betik = kendi if os.path.exists(kendi) else os.path.join(
            kok, 'ATLAS_SABLONLAR', 'scripts', 'check_integrity.sh')
        try:
            r = subprocess.run(['bash', betik, '--full'], cwd=d,
                               capture_output=True, text=True, timeout=300)
            cikti = (r.stdout or '') + (r.stderr or '')
            rc = r.returncode
        except subprocess.TimeoutExpired:
            cikti, rc = 'ZAMAN ASIMI (300 s)', 124
        except Exception as e:
            cikti, rc = 'KOSULAMADI: %s' % e, 125
        satir_liste = [s for s in cikti.splitlines() if s.strip()]
        son = satir_liste[-1].strip()[:110] if satir_liste else '(bos cikti)'
        _hukum = proje_hukmu(d)
        _durum = durum_belirle(rc, _hukum)
        if _durum == 'INSAN_BEKLIYOR':
            son = ('kendi hukmu: %s · %s' % (_hukum, son))[:150]
        satirlar.append({'ad': ad, 'durum': _durum, 'rc': rc, 'son': son,
                         'hukum': _hukum})
    yesil = sum(1 for s in satirlar if s['durum'] == 'YESIL')
    kirmizi = sum(1 for s in satirlar if s['durum'] == 'KIRMIZI')
    insan = sum(1 for s in satirlar if s['durum'] == 'INSAN_BEKLIYOR')
    bas = sum(1 for s in satirlar if s['durum'] == 'BASLAMADI')
    ozet = ('proje=%d · yesil=%d · kirmizi=%d · insan_bekliyor=%d · baslamadi=%d'
            % (len(satirlar), yesil, kirmizi, insan, bas))
    return satirlar, ozet


# K7 ozel: CIKTISI BOS olmali. Bos olmayan cikti = FAIL (temiz agac degil).
BOS_OLMALI = {'K7'}


def kos(kalem, agir_atla, kok=None):
    kok = kok or KOK
    kid, ad, cmd, agir = kalem
    if agir and agir_atla:
        return {'id': kid, 'ad': ad, 'rc': None, 'durum': 'ATLANDI',
                'son': '--hizli: agir kapi atlandi', 'sure': 0.0}
    t0 = time.time()
    try:
        # SNAPSHOT_ONLY=1: ag kapilari (C14l/m/n/r) 90 s timeout'a takilmasin.
        # OLCULDU: bu degisken olmadan K1 1.76 s yerine **42.44 s** surdu.
        env = dict(os.environ, SNAPSHOT_ONLY='1')
        r = subprocess.run(cmd, cwd=kok, capture_output=True, text=True,
                           timeout=600, env=env)
        cikti = (r.stdout or '') + (r.stderr or '')
        rc = r.returncode
    except subprocess.TimeoutExpired:
        cikti, rc = 'ZAMAN ASIMI (600 s)', 124
    except Exception as e:
        cikti, rc = 'KOSULAMADI: %s' % e, 125
    sure = round(time.time() - t0, 2)

    satirlar = [s for s in cikti.splitlines() if s.strip()]
    # Ozet satiri secimi: bazi betiklerde son satir basliktir, bilgi degildir.
    # OLCULDU: mutasyon_tara'nin son satiri "KAPI_DEGIL (aday kanit yok):" —
    # hicbir sey soylemiyor; asil bilgi "oran" satirinda.
    onemli = {'K4': 'oran'}
    son = None
    for aranan in ([onemli[kid]] if kid in onemli else []):
        for s in satirlar:
            if aranan in s.lower():
                son = s.strip()
                break
    if son is None:
        son = satirlar[-1].strip() if satirlar else '(bos cikti)'
    son = son[:150]

    if kid in BOS_OLMALI:
        # Bos cikti = temiz agac = PASS. Dolu cikti = FAIL.
        ok = (rc == 0 and not cikti.strip())
        return {'id': kid, 'ad': ad, 'rc': rc,
                'durum': 'PASS' if ok else 'FAIL',
                'son': son if cikti.strip() else '(bos — temiz agac)',
                'sure': sure}
    return {'id': kid, 'ad': ad, 'rc': rc,
            'durum': 'PASS' if rc == 0 else 'FAIL',
            'son': son, 'sure': sure}


def _secili(argv):
    """--kalem K7,K2 : yalniz bu kalemleri kos (olcum icin).

    NEDEN: K7'yi tek basina olcmek gerekti. Butun kalemleri kosmak zorunda
    kalmak, "K7 mi FAIL verdi yoksa K1 mi" sorusunu cevapsiz birakiyordu.
    """
    for i, a in enumerate(argv):
        if a == '--kalem' and i + 1 < len(argv):
            return {x.strip().upper() for x in argv[i + 1].split(',') if x.strip()}
        if a.startswith('--kalem='):
            return {x.strip().upper() for x in a.split('=', 1)[1].split(',')
                    if x.strip()}
    return None


def _kok(argv):
    """--kok <dizin> : kapilari baska bir agac uzerinde kos (olcum icin)."""
    for i, a in enumerate(argv):
        if a == '--kok' and i + 1 < len(argv):
            return os.path.abspath(argv[i + 1])
    return None


def main():
    agir_atla = '--hizli' in sys.argv
    kok = _kok(sys.argv)
    secili = _secili(sys.argv)
    kalemler = [k for k in KALEMLER if secili is None or k[0] in secili]
    if secili is not None and not kalemler:
        print('HATA: --kalem eslesmedi: %s' % sorted(secili))
        return 2
    print('LAB KAPANIS — tek giris · %s%s'
          % ('HIZLI' if agir_atla else 'TAM',
             '' if secili is None else ' · kalem=%s' % ','.join(sorted(secili))))
    print('kok: %s' % (kok or KOK))
    print()
    sonuclar = []
    for kalem in kalemler:
        s = kos(kalem, agir_atla, kok)
        sonuclar.append(s)
        print('  %-3s %-42s %-7s %5.2fs  %s'
              % (s['id'], s['ad'], s['durum'], s['sure'], s['son']))

    # --- PROJE MANZARASI (K10) — gorunurluk kalemi, hukme GIRMEZ -----------
    # `projeler/` altindaki makale isleri ayri islerdir (MIDEO: AGENTS.md §5
    # dokunulmaz). Lab kapanisini onlara baglamak labi kapatamaz hale getirir.
    # Ama SESSIZ de birakilamaz: olculdu ki 6 projenin 2'si KIRMIZI ve bu
    # durum hicbir kapanis ciktisinda gorunmuyordu.
    projeler, proje_ozet = ([], 'projeler/ yok')
    try:
        projeler, proje_ozet = projeler_tara(kok)
    except Exception as e:
        proje_ozet = 'CALISTIRILAMADI: %s' % e
    print()
    print('  --- PROJE MANZARASI (K10 · gorunurluk, hukme girmez) ---')
    for _p in projeler:
        print('    %-18s %-10s rc=%-4s %s'
              % (_p['ad'], _p['durum'],
                 '-' if _p['rc'] is None else _p['rc'], _p['son']))
    print('    %s' % proje_ozet)
    _insan = [p2['ad'] for p2 in projeler if p2['durum'] == 'INSAN_BEKLIYOR']
    if _insan:
        print('    INSAN_BEKLIYOR: %s — kendi kapisi insan karari bekliyor;'
              ' YESIL sayilmaz (sahte yesil yasak)' % ', '.join(_insan))
    _kirmizi = [p2['ad'] for p2 in projeler if p2['durum'] == 'KIRMIZI']
    if _kirmizi:
        print('    KIRMIZI: %s — ayri is, lab hukmunu degistirmez'
              % ', '.join(_kirmizi))
        print('    (zorunlu kilmak icin: --proje-zorunlu)')

    gecen = [s for s in sonuclar if s['durum'] == 'PASS']
    kalan = [s for s in sonuclar if s['durum'] == 'FAIL']
    atlanan = [s for s in sonuclar if s['durum'] == 'ATLANDI']
    toplam_sure = round(sum(s['sure'] for s in sonuclar), 2)

    print()
    print('  kalem=%d · gecen=%d · kalan=%d · atlanan=%d · sure=%.2fs'
          % (len(sonuclar), len(gecen), len(kalan), len(atlanan),
             toplam_sure))
    if kalan:
        print('  KALAN: %s' % ', '.join(s['id'] for s in kalan))
        hukum = 'FAIL'
        rc = 1
    elif atlanan:
        # Fail-closed: atlanan kalem varsa "hepsi gecti" DENMEZ.
        print('  HUKUM: KOSULLU — %s atlandi, tam kosu GEREKLI'
              % ', '.join(s['id'] for s in atlanan))
        hukum = 'KOSULLU'
        rc = 0
    else:
        hukum = 'PASS'
        rc = 0

    if _kirmizi and '--proje-zorunlu' in sys.argv:
        # Kullanici acikca istediyse proje kirmizisi labi FAIL yapar.
        print('  HUKUM: FAIL — %d proje kirmizi (--proje-zorunlu)'
              % len(_kirmizi))
        hukum, rc = 'FAIL', 1

    if kalan:
        print('  HUKUM: FAIL — %d kalem kirmizi' % len(kalan))
    elif not atlanan:
        print('  HUKUM: PASS — %d/%d kalem gecti' % (len(gecen),
                                                     len(sonuclar)))
    print()
    print('  DENETIM_TIPI: OZ_DENETIM — bu betik hakem degildir; rc toplar.')

    if '--json' in sys.argv:
        print()
        print(json.dumps({'hukum': hukum, 'kalemler': sonuclar,
                          'sure': toplam_sure, 'projeler': projeler,
                          'proje_ozet': proje_ozet},
                         ensure_ascii=False, indent=2))
    return rc


if __name__ == '__main__':
    sys.exit(main())
