#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fikstur_muafiyet_selftest — sir fiksturu muafiyetinin REGRESYON testi.

NEDEN VAR
  `tools/secret_fixtures.json` belgelenmis sahte satirlari susturur. Bu
  muafiyet dar olmali, yoksa kapi sessizce korlesir:
    * yalniz tam satir SHA-256'si eslesirse susmali,
    * satir degisirse veya ayni deger baska dosyaya tasinirsa P0 yanmali,
    * manifest bozuksa kapi "temiz" dememeli (fail-closed).
  Bu uc davranis bugune kadar yalniz canli kapi ciktisindan gozleniyordu;
  negatif fiksturu olmayan kapi test edilmemis sayilir.

NASIL
  Gercek kapi calistirilir: minimal gecici agacta `secret_scan.py --tum --json`
  kosar (KOK == ARAC_KOK oldugu icin muafiyet devreye girer). Ayrica H4
  (`dogrula.sir_tarama`) ayni sozlesme icin modul duzeyinde sinanir — izinli
  dosya listesi dahil: manifest, kodda sayilan listenin DISINDA bir dosyayi
  susturamaz (besinci zayiflama).
  Ana agaca YAZILMAZ; her vaka kendi gecici agacini kurar.

KULLANIM
  python3 tools/fikstur_muafiyet_selftest.py

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KAPI = 'KOD_SABLONLAR/scripts/secret_scan.py'
# Desen kaynagi ve KARDESLERI (v4_verify, v4_common'e import eder).
V4_DIZIN = 'KOMUT_TOOLKIT_v4/ARACLAR/betikler'
V4 = V4_DIZIN + '/v4_verify.py'
# Muafiyetin izin verdigi iki dosya (secret_scan.FIKSTUR_DOSYALARI ile ayni).
IZINLI_A = 'docs/OLCUM-02-CANLI-KOSU.md'
IZINLI_B = 'KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_selftest.py'
# `AKIA[0-9A-Z]{16}` desenine GERCEKTEN uyan, ama yer tutucu ipucu tasimayan
# sentetik deger. Ikisi de zorunlu: yer tutucu olsa kapi SEC-03 (P1) derdi;
# desene uymasa "sessiz kaldi" testi bos yere gecerdi (vacuous pass).
# Literal ikiye BOLUNUR: butun halde yazilsaydi bu aracin kendi kaynagi
# YAYIN-03 tarafindan sir deseni olarak yakalanirdi (olculdu) ve muafiyet
# listesini genisletmek gerekirdi; o da kapıyı zayıflatırdı.
SAHTE = 'AKIA' + '2E1F4B7C9D0E3F9A'

SONUCLAR = []


def kontrol(ad, gecti, ayrinti=''):
    SONUCLAR.append((ad, bool(gecti)))
    print('  %-5s %s%s' % ('PASS' if gecti else 'FAIL', ad,
                           ('' if gecti else ' :: %s' % ayrinti)))


def satir_hash(satir):
    return hashlib.sha256(satir.encode('utf-8')).hexdigest()


def agac(tmp, satirlar=None, kayitlar=None, manifest=None):
    """Minimal gecici agac: kapi betigi + desen kaynagi + manifest + fikstur."""
    agac = Path(tmp) / 'depo'
    # Yalniz desen kaynagi ve bagimliligi. `v4_selftest.py` KOPYALANMAZ:
    # icinde deponun GERCEK fikstur satirlari var; kopyalansaydi sentetik
    # manifestte olmadiklari icin P0 yanar ve "sessiz" vakasi bulanirdi.
    hedef_v4 = agac / V4_DIZIN
    hedef_v4.mkdir(parents=True, exist_ok=True)
    for ad in ('v4_verify.py', 'v4_common.py'):
        shutil.copy2(KOK / V4_DIZIN / ad, hedef_v4 / ad)
    hedef = agac / KAPI
    hedef.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(KOK / KAPI, hedef)
    satirlar = satirlar or {}
    for rel, satir_listesi in satirlar.items():
        yol = agac / rel
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text('\n'.join(satir_listesi) + '\n', encoding='utf-8')
    (agac / 'tools').mkdir(parents=True, exist_ok=True)
    if manifest is None:
        manifest = {'sema': 'SECRET-SCAN-FIKSTUR/v1',
                    'fiksturler': kayitlar or []}
    (agac / 'tools' / 'secret_fixtures.json').write_text(
        manifest if isinstance(manifest, str)
        else json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    return agac


def kayit(dosya, satir):
    return {'dosya': dosya, 'satir': 1, 'satir_sha256': satir_hash(satir),
            'gerekce': 'regresyon fiksturu; gercek sir degil',
            'kanit': 'fikstur_muafiyet_selftest'}


def kapi_kos(agac):
    r = subprocess.run([sys.executable, KAPI, '--tum', '--v4', str(agac / V4),
                        '--json'], cwd=str(agac), capture_output=True, text=True)
    cikti = (r.stdout or '') + (r.stderr or '')
    try:
        rapor = json.loads(r.stdout)
    except ValueError:
        rapor = None
    return r.returncode, rapor, cikti


def vaka_sessiz(tmp):
    """Bilinen satir sessiz kalmali: P0 yok, muafiyet sayaci > 0.

    ON KOSUL: ayni agac BOS manifestle P0 vermeli. Vermezse "sessiz kaldi"
    iddiasi bos yere gecer (vacuous): deger zaten bir sir degildir.
    """
    on = agac(Path(tmp) / 'on', {IZINLI_A: ['# olcum kaydi', SAHTE, '# son']}, [])
    rc0, rapor0, cikti0 = kapi_kos(on)
    kontrol('on kosul: fikstur gercekten sir sayiliyor',
            rapor0 is not None and rapor0['p0'] >= 1,
            'bos manifest p0=%s rc=%d · %s'
            % (rapor0['p0'] if rapor0 else '?', rc0, cikti0.strip()[-120:]))
    if rapor0 is None or rapor0['p0'] < 1:
        return
    agac_yolu = agac(Path(tmp) / 'son', {IZINLI_A: ['# olcum kaydi', SAHTE, '# son']},
                     [kayit(IZINLI_A, SAHTE)])
    rc, rapor, cikti = kapi_kos(agac_yolu)
    if rapor is None:
        kontrol('bilinen satir sessiz', False, 'JSON okunamadi: %s' % cikti[-160:])
        return
    kontrol('bilinen satir sessiz',
            rc == 0 and rapor['p0'] == 0 and rapor['fikstur_muafiyeti'] >= 1,
            'rc=%d p0=%d fikstur=%d' % (rc, rapor['p0'],
                                        rapor['fikstur_muafiyeti']))


def vaka_satir_degisti(tmp):
    """Ayni dosyada satir degisince hash tutmaz: SEC-02 P0 yanmali."""
    degismis = SAHTE + 'A'
    agac_yolu = agac(tmp, {IZINLI_A: ['# olcum kaydi', degismis, '# son']},
                     [kayit(IZINLI_A, SAHTE)])
    rc, rapor, cikti = kapi_kos(agac_yolu)
    if rapor is None:
        kontrol('satir degisince P0', False, 'JSON okunamadi: %s' % cikti[-160:])
        return
    p0 = [b for b in rapor['bulgular'] if b['siddet'] == 'P0']
    kontrol('satir degisince P0',
            rc == 1 and rapor['p0'] >= 1 and rapor['fikstur_muafiyeti'] == 0
            and any(b['kural'] == 'SEC-02' and IZINLI_A in b['konum'] for b in p0),
            'rc=%d p0=%d fikstur=%d bulgular=%s' % (
                rc, rapor['p0'], rapor['fikstur_muafiyeti'],
                [b['kural'] for b in rapor['bulgular']][:3]))


def vaka_dosya_degisti(tmp):
    """Ayni deger izinli BASKA dosyaya tasinirsa muafiyet uygulanmamali."""
    agac_yolu = agac(tmp, {IZINLI_B: ['# test dosyasi', SAHTE, '# son']},
                     [kayit(IZINLI_A, SAHTE)])
    rc, rapor, cikti = kapi_kos(agac_yolu)
    if rapor is None:
        kontrol('dosya degisince P0', False, 'JSON okunamadi: %s' % cikti[-160:])
        return
    p0 = [b for b in rapor['bulgular'] if b['siddet'] == 'P0']
    kontrol('dosya degisince P0',
            rc == 1 and rapor['p0'] >= 1 and rapor['fikstur_muafiyeti'] == 0
            and any(IZINLI_B in b['konum'] for b in p0),
            'rc=%d p0=%d fikstur=%d konum=%s' % (
                rc, rapor['p0'], rapor['fikstur_muafiyeti'],
                [b['konum'] for b in rapor['bulgular']][:2]))


def vaka_bozuk_manifest(tmp):
    """Bozuk manifest fail-closed olmali: 'temiz' denmemeli."""
    agac_yolu = agac(tmp, {IZINLI_A: ['# bos', '# son']},
                     manifest='{ "fiksturler": [ olsun ')
    rc, rapor, cikti = kapi_kos(agac_yolu)
    kontrol('bozuk manifest fail-closed',
            rc == 1 and 'SEC-00' in cikti and 'fikstur manifesti' in cikti
            and 'SECRET-SCAN PASS' not in cikti,
            'rc=%d cikti=%s' % (rc, cikti.strip().splitlines()[-1][:140]))


def vaka_gecersiz_kayit(tmp):
    """Gecersiz kayitlar (bozuk hash, izinsiz dosya, yinelenen) reddedilmeli."""
    vakalar = {
        'bozuk hash': [{'dosya': IZINLI_A, 'satir_sha256': 'abc',
                        'gerekce': 'x', 'kanit': 'y'}],
        'izinsiz dosya': [dict(kayit(IZINLI_A, SAHTE), dosya='docs/BASKA.md')],
        'gerekcesiz': [{'dosya': IZINLI_A, 'satir_sha256': satir_hash(SAHTE),
                        'gerekce': ' ', 'kanit': 'y'}],
        'yinelenen': [kayit(IZINLI_A, SAHTE), kayit(IZINLI_A, SAHTE)],
    }
    for ad, kayitlar in vakalar.items():
        alt = Path(tmp) / ('g_' + ad.replace(' ', '_'))
        agac_yolu = agac(alt, {IZINLI_A: ['# bos', '# son']}, kayitlar)
        rc, rapor, cikti = kapi_kos(agac_yolu)
        kontrol('gecersiz kayit reddedilir: %s' % ad,
                rc == 1 and 'SEC-00' in cikti and 'SECRET-SCAN PASS' not in cikti,
                'rc=%d cikti=%s' % (rc, cikti.strip().splitlines()[-1][:120]))


def _secret_scan_izinli():
    """`secret_scan.FIKSTUR_DOSYALARI` kumesini KAYNAKTAN oku (import etmeden).

    Betik import edilirse modul duzeyinde tarama kosar; bu yuzden AST ile
    yalniz atama dugumu okunur. Bulunamazsa None doner ve parite testi kalir.
    """
    try:
        kaynak = (KOK / KAPI).read_text(encoding='utf-8')
        agac_ast = ast.parse(kaynak)
    except (OSError, SyntaxError):
        return None
    for dugum in ast.walk(agac_ast):
        if isinstance(dugum, ast.Assign) and any(
                isinstance(h, ast.Name) and h.id == 'FIKSTUR_DOSYALARI'
                for h in dugum.targets):
            try:
                return set(ast.literal_eval(dugum.value))
            except (ValueError, TypeError):
                return None
    return None


def h4_vakalari(tmp):
    """H4 (`dogrula.sir_tarama`) ayni sozlesmeyi korumali."""
    sys.path.insert(0, str(KOK / 'tools'))
    import dogrula

    eski_kok, eski_fikstur = dogrula.KOK, dogrula.FIKSTUR_DOSYASI
    try:
        # H4-1: bilinen satir sessiz.
        agac_yolu = agac(Path(tmp) / 'h4a',
                         {IZINLI_A: ['# olcum kaydi', SAHTE, '# son']},
                         [kayit(IZINLI_A, SAHTE)])
        dogrula.KOK = str(agac_yolu)
        dogrula.FIKSTUR_DOSYASI = str(agac_yolu / 'tools' / 'secret_fixtures.json')
        gecti, ozet, detay = dogrula.sir_tarama()
        kontrol('H4 bilinen satir sessiz', gecti and '0 bulgu' in ozet,
                'gecti=%s ozet=%s detay=%s' % (gecti, ozet, detay[:2]))

        # H4-2: satir degisince H4 kirilmali.
        agac_yolu = agac(Path(tmp) / 'h4b',
                         {IZINLI_A: ['# olcum kaydi', SAHTE + 'A', '# son']},
                         [kayit(IZINLI_A, SAHTE)])
        dogrula.KOK = str(agac_yolu)
        dogrula.FIKSTUR_DOSYASI = str(agac_yolu / 'tools' / 'secret_fixtures.json')
        gecti, ozet, detay = dogrula.sir_tarama()
        kontrol('H4 satir degisince kirilir',
                (not gecti) and any(IZINLI_A in d for d in detay),
                'gecti=%s ozet=%s detay=%s' % (gecti, ozet, detay[:2]))

        # H4-3: bozuk manifest fail-closed.
        agac_yolu = agac(Path(tmp) / 'h4c', {IZINLI_A: ['# bos', '# son']},
                         manifest='{ bozuk')
        dogrula.KOK = str(agac_yolu)
        dogrula.FIKSTUR_DOSYASI = str(agac_yolu / 'tools' / 'secret_fixtures.json')
        gecti, ozet, detay = dogrula.sir_tarama()
        kontrol('H4 bozuk manifest fail-closed',
                (not gecti) and 'manifesti' in (ozet + str(detay)),
                'gecti=%s ozet=%s detay=%s' % (gecti, ozet, detay[:2]))

        # BESINCI ZAYIFLAMA: manifest, izinli listenin DISINDA bir dosyayi
        # susturmaya calisirsa H4 "temiz" DEMEMELI. On kosul sart: ayni satir
        # manifest yokken gercekten yakalanmali (yoksa test bos yere gecer).
        satir = 'AWS_ACCESS_KEY_ID=' + SAHTE
        on = agac(Path(tmp) / 'h4d', {'src/rastgele.py': [satir]}, [])
        dogrula.KOK = str(on)
        dogrula.FIKSTUR_DOSYASI = str(on / 'tools' / 'secret_fixtures.json')
        gecti0, ozet0, detay0 = dogrula.sir_tarama()
        kontrol('H4 on kosul: izinsiz dosyadaki sir yakalaniyor',
                (not gecti0) and any('src/rastgele.py' in d for d in detay0),
                'gecti=%s ozet=%s detay=%s' % (gecti0, ozet0, detay0[:2]))
        if (not gecti0) and any('src/rastgele.py' in d for d in detay0):
            agac_yolu = agac(Path(tmp) / 'h4e', {'src/rastgele.py': [satir]},
                             [kayit('src/rastgele.py', satir)])
            dogrula.KOK = str(agac_yolu)
            dogrula.FIKSTUR_DOSYASI = str(agac_yolu / 'tools' / 'secret_fixtures.json')
            gecti, ozet, detay = dogrula.sir_tarama()
            kontrol('H4 izinsiz dosya kaydi susturamaz (besinci zayiflama)',
                    (not gecti) and ('izinsiz' in (ozet + str(detay))),
                    'gecti=%s ozet=%s detay=%s' % (gecti, ozet, detay[:2]))

        # Izin listesi koddan gelir ve secret_scan ile AYNI olmali: biri
        # genisletilip oteki unutulursa iki kapi farkli sey soyler.
        h4_izinli = getattr(dogrula, 'FIKSTUR_DOSYALARI', None)
        kapi_izinli = _secret_scan_izinli()
        kontrol('H4 izin listesi secret_scan ile ayni',
                h4_izinli == kapi_izinli == {IZINLI_A, IZINLI_B},
                'H4=%s secret_scan=%s beklenen=%s' % (
                    sorted(h4_izinli or []), sorted(kapi_izinli or []),
                    sorted({IZINLI_A, IZINLI_B})))
    finally:
        dogrula.KOK, dogrula.FIKSTUR_DOSYASI = eski_kok, eski_fikstur


def main():
    print('FIKSTUR MUAFIYET OZ-TESTI — sir tarayicisinin muafiyet siniri')
    print('kaynak: %s' % KOK.name)
    print()
    tmp = tempfile.mkdtemp(prefix='fikstur_muafiyet_')
    try:
        vaka_sessiz(Path(tmp) / 'a')
        vaka_satir_degisti(Path(tmp) / 'b')
        vaka_dosya_degisti(Path(tmp) / 'c')
        vaka_bozuk_manifest(Path(tmp) / 'd')
        vaka_gecersiz_kayit(Path(tmp) / 'e')
        h4_vakalari(Path(tmp) / 'f')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    kirik = [ad for ad, gecti in SONUCLAR if not gecti]
    print()
    print('  vaka=%d · gecen=%d · kalan=%d'
          % (len(SONUCLAR), len(SONUCLAR) - len(kirik), len(kirik)))
    if kirik:
        print('HUKUM: FAIL — muafiyet siniri korunmuyor: %s' % ', '.join(kirik))
        return 1
    print('HUKUM: PASS — muafiyet yalniz tam satir hash\'inde susuyor; '
          'satir/dosya degisimi P0, bozuk manifest fail-closed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
