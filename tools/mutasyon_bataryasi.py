#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutasyon_bataryasi — yayimlanan kapilarin GERCEKTEN atesledigini olcer.

NEDEN VAR
  Bir kapi "PASS" diyorsa, o kapinin bir ihlali yakalayabildigi ayri bir olcumle
  gosterilmelidir. Aksi halde yesil, kapinin degil girdinin ozelligidir. Bu betik
  her vaka icin once TEMIZ TABAN alir, sonra ayni kopyada tek bir ihlal uretir ve
  kapinin kirmiziya dondugunu olcer. Ikisi birlikte olmadan vaka GECMEZ.

NE OLCMEZ
  Model cagirmaz, ag kullanmaz, gercek makale uretmez. Olctugu sey kapi
  betiginin kendi kararidir; kapsam disi olan sey raporda yazilidir.

KULLANIM
  python3 tools/mutasyon_bataryasi.py [--ayrintili]

CIKIS
  0  : butun vakalar atesledi (taban temiz + mutasyon kirmizi)
  1  : en az bir vaka ateslemedi / taban kirlendi / mutasyon uygulanamadi
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
# check_models sabit katalogu kullanir (ag/canli models.dev gerekmez).
os.environ.setdefault('ATLAS_MODEL_KATALOG', str(KOK / 'tools' / 'model_katalog.json'))
AYRINTILI = '--ayrintili' in sys.argv
ATLA = shutil.ignore_patterns('.git', '__pycache__', 'node_modules', '.pytest_cache',
                              '.ruff_cache', '.DS_Store')

# Anahtar PARCALI yazilir: bu dosya depoda durur ve sir tarayicisi (H4) bitisik
# deseni yakalar. Parcali literal tarayiciyi yaniltmak icin degil, gercek bir
# anahtarin depoya sizmasini onlemek icin boyle: fikstur oldugu gorunur.
SAHTE_ANAHTAR = 'AKIA' + 'Z7Q2M4XK9PLR3TWV'

DEC_BASLIKLAR = ['Etik Kurul', 'Cikar Catismasi', 'Finansman', 'credit',
                 'Veri Erisilebilirligi', 'Yapay Zeka']


def kos(komut, cwd=None):
    r = subprocess.run([str(k) for k in komut], cwd=str(cwd or KOK),
                       capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding='utf-8')


def ekle(kok, rel, metin):
    """Mutasyon: dosyanin sonuna ekle. Hedef yoksa HATA dondurur."""
    yol = kok / rel
    if not yol.is_file():
        return 'HATA: hedef yok: %s' % rel
    with yol.open('a', encoding='utf-8') as f:
        f.write(metin)
    return None


def degistir(kok, rel, eski, yeni):
    """Mutasyon: TAM bir metin parcasini degistir (tek eslesme sarti)."""
    yol = kok / rel
    if not yol.is_file():
        return 'HATA: hedef yok: %s' % rel
    metin = yol.read_text(encoding='utf-8')
    adet = metin.count(eski)
    if adet != 1:
        return 'HATA: %s icinde desen %d kez gecti (1 bekleniyordu)' % (rel, adet)
    yol.write_text(metin.replace(eski, yeni, 1), encoding='utf-8')
    return None


def dec_govde(basliklar):
    return '# Makale\n\n' + '\n\n'.join('## %s\n\nBeyan metni.' % b for b in basliklar) + '\n'


# --- saf ayristirici fiksturleri (ag/model/imza/tarihce/git gerektirmez) ------
REC_FAZ1 = ('{"findings": [{"id": "F-001", "priority": "P0"}, '
            '{"id": "F-002", "priority": "P1"}]}\n')
REC_MANIFEST = (
    '# manifest\n\n| FIX-ID | Severity | Kategori | Bulgu | Durum | Kanit |\n'
    '|---|---|---|---|---|---|\n'
    '| FIX-001 | P0 | A | F-001 | UYGULANMI\u015e | SC-001 |\n'
    '| FIX-002 | P1 | B | F-002 | UYGULANMI\u015e | SC-002 |\n')
REC_MASTER = '# MASTER\n\nFIX-001 ve FIX-002 uyguland\u0131.\n'
REC_GATE2B = ('{"manifest_reconciliation": ['
              '{"fix_id": "FIX-001", "status": "UYGULANMIS_KANITLI"}, '
              '{"fix_id": "FIX-002", "status": "UYGULANMIS_KANITLI"}]}\n')

SINIF_MD = (
    '# Makale\n\n## PROVENANCE\n\n'
    '| SCOPE-ID | Bolum | Kaynak | Satir Referansi | Kaynak Sinifi | Durum |\n'
    '|---|---|---|---|---|---|\n'
    '| SC-001 | Giris | K | 1 | BIRINCIL | kapsandi |\n'
    '| SC-002 | Yontem | K | 2 | IKINCIL | kapsandi |\n')

SCOPE_TR = '# SCOPE\n\nTransliterasyon sistemi: DMG (DIN 31635).\n'
METIN_TR = '# Makale\n\nMetinde sek\u00eene terimi bir kez ge\u00e7er.\n'

CITE_MD = ('# Makale\n\nGovde metni (Yazar, 2020).\n\n## Kaynakca\n\n'
           '- Yazar, A. (2020). Kitap. Yayin.\n')

DEC_MD = ('# Makale\n\n'
          '## Etik Kurul\n\nGerekmedi; gerekce: insan katilimci yok.\n\n'
          '## Cikar Catismasi\n\nYok.\n\n'
          '## Finansman\n\nYok.\n\n'
          '## Yazar Katkisi\n\nTek yazar.\n\n'
          '## Veri Erisilebilirligi\n\nYok.\n\n'
          '## Yapay Zeka\n\nKullanilmadi.\n\n'
          '## DPIA\n\nKisisel veri islenmedi.\n')


def qr_govde(uzun_mu):
    # 40+ kelime ESIGI gercek sayimla gecilir; sayi uydurulmaz (ATLAS kapisi da
    # kelime sayar). Uzunluk calisirken olculur, yorumda iddia edilmez.
    if uzun_mu:
        alinti = ('Bu paragraf kirk kelimelik esigi asan bir alintinin nasil '
                  'gorundugunu olcmek icin yazilmistir ve gercekten uzun bir '
                  'alintidir; boylece kapi uzun alinti uclusunu denetlemek zorunda '
                  'kalir ve sayfa numarasi verilmedigi icin kirmizi yanmasi '
                  'gerekir, cunku ucuncu unsur eksiktir ve bu eksiklik sessiz '
                  'gecilmemelidir.')
        atif = '(Kaya, 2020).'
    else:
        alinti = 'Kisa bir alinti.'
        atif = '(Kaya, 2020, s. 12).'
    return ('# Makale\n\nGovde metni burada baslar.\n\n'
            '"%s" %s\n\n## Kaynakca\n\nKaya, A. (2020). Deneme.\n' % (alinti, atif))


def taban_ve_mutasyon(kok, kapi, argumanlar, mutasyon, iz, taban_rc=0):
    """(durum, ayrinti) dondurur. taban_rc: temiz kopyada beklenen cikis kodu."""
    betik = kok / kapi
    if not betik.is_file():
        return 'EKSIK', 'kapi betigi yok: %s' % kapi

    komut = [sys.executable, betik] + argumanlar(kok)

    rc0, o0 = kos(komut, cwd=kok)
    if rc0 != taban_rc:
        return 'TABAN_KIRIK', 'taban rc=%d (beklenen %d) · %s' % (
            rc0, taban_rc, o0.strip().splitlines()[-1] if o0.strip() else '')

    hata = mutasyon(kok)
    if hata:
        return 'MUTASYON_UYGULANMADI', hata

    rc1, o1 = kos(komut, cwd=kok)
    if rc1 == 0:
        return 'ATESLEMEDI', 'mutasyon sonrasi rc=0 (kapi kirmiziya donmedi)'
    if iz not in o1:
        return 'ATESLEMEDI', 'rc=%d ama beklenen iz (%s) ciktida yok' % (rc1, iz)
    return 'GECTI', 'taban rc=0 · mutasyon rc=%d · iz=%s' % (rc1, iz)


def _satir_sil(k, rel, anahtar):
    """Verilen anahtari tasiyan satiri fiksturden cikarir."""
    p = k / rel
    satirlar = [s for s in p.read_text(encoding='utf-8').splitlines(True) if anahtar not in s]
    p.write_text(''.join(satirlar), encoding='utf-8')
    return None


def _pl04(k):
    """Kok disina isaret eden symlink: PL-04 icin tek ihlal."""
    hedef = k.parent / 'atlas-dis-hedef.md'
    hedef.write_text('# dis\n', encoding='utf-8')
    (k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-dis-link.md').symlink_to(hedef)
    return None


def vakalar():
    """Her vaka: (kimlik, katman, kural, kapi, argumanlar, mutasyon, iz)."""
    return [
        ('KOD-SEC-02', 'KOD', 'gercek sir kalibi P0', 'KOD_SABLONLAR/scripts/secret_scan.py',
         lambda k: ['--tum', '--dizin', str(k / 'sandbox')],
         lambda k: ekle(k, 'sandbox/notlar.md', '\nanahtar = "%s"\n' % SAHTE_ANAHTAR),
         'SEC-'),
        ('KOD-PERM-01', 'KOD', 'olu kural yok (findLast sirasi)', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: degistir(
             k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-gate-2a.md',
             '  bash:\n    "*": allow\n    "git commit*": deny\n',
             '  bash:\n    "git commit*": deny\n    "*": allow\n'),
         'PERM-01'),
        ('ATLAS-PL-10', 'ATLAS', 'vacuous PASS muafiyeti yok', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: ekle(k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-scoper.md',
                        '\nKanit GEREKMEZ.\n'),
         'PL-10'),
        ('ATLAS-DEC-03', 'ATLAS', 'beyan basligi zorunlu', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'MASTER.md')],
         lambda k: yaz(k / 'sandbox' / 'MASTER.md',
                       dec_govde([b for b in DEC_BASLIKLAR if b != 'Finansman'])),
         'DEC-03'),
        ('ATLAS-QR-02', 'ATLAS', '40+ kelimelik alintida uclu', 'ATLAS_SABLONLAR/scripts/quote_ratio.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'makale.md')],
         lambda k: yaz(k / 'sandbox' / 'makale.md', qr_govde(uzun_mu=True)),
         'QR-02'),
        # --- fix_reconcile: saf dosya ayristirici -----------------------------
        ('REC-01', 'ATLAS', 'FAZ1 bulgu == FAZ2 FIX', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: ekle(k, '02-FAZ-2-FIX-MANIFEST.md',
                        '| FIX-003 | P2 | C | F-003 | UYGULANMI\u015e | SC-003 |\n'),
         'REC-01'),
        ('REC-02', 'ATLAS', 'oncelik dagilimi ayni', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: degistir(k, '02-FAZ-2-FIX-MANIFEST.md',
                            '| FIX-002 | P1 |', '| FIX-002 | P2 |'),
         'REC-02'),
        ('REC-03', 'ATLAS', 'FAZ1 bulgusu FAZ2 de atifli', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: degistir(k, '02-FAZ-2-FIX-MANIFEST.md', 'F-002', 'F-999'),
         'REC-03'),
        ('REC-04', 'ATLAS', 'UYGULANMIS FIX MASTER da gorunur', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: yaz(k / '03-FAZ-3-MASTER-v5.5.md', '# MASTER\n\nFIX-001 uyguland\u0131.\n'),
         'REC-04'),
        ('REC-05', 'ATLAS', 'gate 2B KANITLI iddiasi dogrulanir', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: yaz(k / 'gate' / 'STRONG-gate-2b-v5.5.json',
                       '{"manifest_reconciliation": ['
                       '{"fix_id": "FIX-001", "status": "UYGULANMIS_KANITLI"}, '
                       '{"fix_id": "FIX-002", "status": "UYGULANMIS_KANITLI"}, '
                       '{"fix_id": "FIX-009", "status": "UYGULANMIS_KANITLI"}]}\n'),
         'REC-05'),
        ('REC-06', 'ATLAS', 'hayalet kanit yok', 'ATLAS_SABLONLAR/scripts/fix_reconcile.py',
         lambda k: [],
         lambda k: ekle(k, '03-FAZ-3-MASTER-v5.5.md', 'FIX-003\n'),
         'REC-06'),
        # --- source_class_check ----------------------------------------------
        ('SRC-02', 'ATLAS', 'Kaynak Sinifi gecerli', 'ATLAS_SABLONLAR/scripts/source_class_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'sinif.md')],
         lambda k: degistir(k, 'sandbox/sinif.md', '| BIRINCIL |', '| BELIRSIZ |'),
         'SRC-02'),
        ('SRC-03', 'ATLAS', 'AKTARMA beyani zorunlu', 'ATLAS_SABLONLAR/scripts/source_class_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'sinif.md')],
         lambda k: degistir(k, 'sandbox/sinif.md', '| IKINCIL |', '| AKTARMA |'),
         'SRC-03'),
        # --- translit_check --------------------------------------------------
        ('TR-01', 'ATLAS', 'SCOPE ta sistem ilani', 'ATLAS_SABLONLAR/scripts/translit_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'metin_tr.md'),
                    '--scope', str(k / 'sandbox' / 'scope_tr.md')],
         lambda k: degistir(k, 'sandbox/scope_tr.md',
                            'Transliterasyon sistemi: DMG (DIN 31635).\n',
                            'Sistem belirtilmedi.\n'),
         'TR-01'),
        ('TR-02', 'ATLAS', 'tek yazim tutarliligi', 'ATLAS_SABLONLAR/scripts/translit_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'metin_tr.md'),
                    '--scope', str(k / 'sandbox' / 'scope_tr.md')],
         lambda k: ekle(k, 'sandbox/metin_tr.md', 'Ikinci yazim: sak\u012bna.\n'),
         'TR-02'),
        # --- cite_match ------------------------------------------------------
        ('CITE-01', 'ATLAS', 'metindeki atif kaynakcada', 'ATLAS_SABLONLAR/scripts/cite_match.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'cite.md')],
         lambda k: degistir(k, 'sandbox/cite.md', '(Yazar, 2020)', '(Diger, 2021)'),
         'CITE-01'),
        ('CITE-02', 'ATLAS', 'kaynakcadaki girdi anilir', 'ATLAS_SABLONLAR/scripts/cite_match.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'cite.md')],
         lambda k: ekle(k, 'sandbox/cite.md', '- Kaya, B. (2019). Ek. Yayin.\n'),
         'CITE-02'),
        # --- declaration_check ----------------------------------------------
        ('DEC-01', 'ATLAS', 'Etik Kurul beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md',
                            '## Etik Kurul\n\nGerekmedi; gerekce: insan katilimci yok.\n\n', ''),
         'DEC-01'),
        ('DEC-02', 'ATLAS', 'Cikar Catismasi beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md', '## Cikar Catismasi\n\nYok.\n\n', ''),
         'DEC-02'),
        ('DEC-04', 'ATLAS', 'Yazar Katkisi beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md', '## Yazar Katkisi\n\nTek yazar.\n\n', ''),
         'DEC-04'),
        ('DEC-05', 'ATLAS', 'Veri Erisilebilirligi beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md', '## Veri Erisilebilirligi\n\nYok.\n\n', ''),
         'DEC-05'),
        ('DEC-06', 'ATLAS', 'Yapay Zeka beyani', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(k, 'sandbox/dec.md', '## Yapay Zeka\n\nKullanilmadi.\n\n', ''),
         'DEC-06'),
        ('DEC-07', 'ATLAS', 'DPIA kosullu zorunlu', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'dec.md')],
         lambda k: degistir(
             k, 'sandbox/dec.md', '## DPIA\n\nKisisel veri islenmedi.\n',
             '## Katilimci Verisi\n\n'
             'Bu bolumde calismanin veri toplama sureci aciklanmaktadir. Surec, etik '
             'ilkelere uygun olarak planlanmis ve yurutulmustur. Tum adimlar kayit '
             'altina alinmistir.\n\nKatilimcilardan gorusme ile veri toplandi.\n'),
         'DEC-07'),
        # --- secret_scan: yapisal .env tespiti --------------------------------
        ('SEC-01', 'KOD', 'gercek .env P0', 'KOD_SABLONLAR/scripts/secret_scan.py',
         lambda k: ['--tum', '--dizin', str(k / 'sandbox')],
         lambda k: yaz(k / 'sandbox' / '.env', 'TOKEN=degil-gercek\n'),
         'SEC-01'),
        # --- prompt_lint: saf metin/frontmatter kurallari ---------------------
        ('PL-01', 'ATLAS', 'frontmatter description', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\nmode: subagent\n---\n\nCALISTIRILMADI\n'),
         'PL-01'),
        ('PL-02', 'ATLAS', 'mode kapali liste', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\ndescription: test\nmode: expert\n---\n\nCALISTIRILMADI\n'),
         'PL-02'),
        ('PL-04', 'ATLAS', 'symlink kok icinde', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         _pl04,
         'PL-04'),
        ('PL-09', 'ATLAS', 'lens karar vermez', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-lens-test.md',
                       '---\ndescription: test\nmode: subagent\n---\n\n'
                       'CALISTIRILMADI\n\n```json\n{"verdict": "PASS"}\n```\n'),
         'PL-09'),
        ('PL-11', 'ATLAS', 'kalici muafiyet yok', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\ndescription: test\nmode: subagent\n---\n\n'
                       'CALISTIRILMADI. Bu kapi her zaman PASS verir.\n'),
         'PL-11'),
        ('PL-13', 'ATLAS', 'belirsizlik yasagi yok', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\ndescription: test\nmode: subagent\n---\n\n'
                       'CALISTIRILMADI. Belirsizlik etiketlerini birakma.\n'),
         'PL-13'),
        ('PL-16', 'ATLAS', 'cagrilan betik var', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: yaz(k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-pl-test.md',
                       '---\ndescription: test\nmode: subagent\n---\n\n'
                       'CALISTIRILMADI. python3 scripts/olmayan_kapi_xyz.py cikis kodunu denetler.\n'),
         'PL-16'),
        ('PL-18', 'ATLAS', 'kirik symlink reddedilir', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: (k / 'ATLAS_SABLONLAR/.opencode/agent/atlas-kirik-link.md').symlink_to(
             k / 'ATLAS_SABLONLAR' / 'yok-hedef.md'),
         'PL-18'),
        # --- perm_lint: saf YAML izin kurallari -------------------------------
        ('PERM-02', 'KOD', 'deny cift kalip', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: degistir(
             k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-gate-2a.md',
             '    "*FIX-MANIFEST*": deny\n',
             '    "*FIX-MANIFEST*": deny\n    "docs/*.md": deny\n'),
         'PERM-02'),
        ('PERM-04', 'KOD', 'acilmaz cizgisi read+edit', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: degistir(
             k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-gate-2a.md',
             '    "*FIX-MANIFEST*": deny\n',
             '    "*FIX-MANIFEST*": deny\n    "portfolyo": deny\n'),
         'PERM-04'),
        # --- scope_profile_check: saf SCOPE ayristirici -----------------------
        ('SP-01', 'ATLAS', 'profil beyani zorunlu', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: degistir(k, 'sandbox/scope.md',
                            'ALAN_PROFILI: ampirik', 'ALAN_PROFILI: bilinmeyen'),
         'SP-01'),
        ('SP-02', 'ATLAS', 'profil disi baslik yok', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: degistir(k, 'sandbox/scope.md',
                            '| SC-003 | Y\u00f6ntem |',
                            '| SC-003 | Transliterasyon Y\u00f6ntemi |'),
         'SP-02'),
        ('SP-03', 'ATLAS', 'ortak zorunlular eksiksiz', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: _satir_sil(k, 'sandbox/scope.md', '| SC-001 |'),
         'SP-03'),
        ('SP-04', 'ATLAS', 'profile ozgu yuvalar var', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: _satir_sil(k, 'sandbox/scope.md', '| SC-002 |'),
         'SP-04'),
        ('SP-06', 'ATLAS', 'vacuous PASS kapali', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: yaz(k / 'sandbox' / 'scope.md',
                       (k / 'sandbox' / 'scope.md').read_text(encoding='utf-8')
                       .replace('ZORUNLU', 'OPSIYONEL')),
         'SP-06'),
        ('SP-07', 'ATLAS', 'tablo basliklari zorunlu', 'ATLAS_SABLONLAR/scripts/scope_profile_check.py',
         lambda k: ['--scope', str(k / 'sandbox' / 'scope.md')],
         lambda k: degistir(k, 'sandbox/scope.md',
                            '| ID | Ba\u015fl\u0131k | Zorunluluk |',
                            '| ID | Baslik | Zorunluluk |'),
         'SP-07'),
        # --- check_models: sabit katalog, saf frontmatter ----------------------
        ('MOD-02', 'ATLAS', 'saglayici yetkili', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'model: openrouter/', 'model: diger/'),
         'MOD-02'),
        ('MOD-03', 'ATLAS', 'model katalogda var', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'openrouter/anthropic/claude-opus-5', 'openrouter/yok/model'),
         'MOD-03'),
        ('MOD-06', 'ATLAS', 'tilde takma adi yok', 'ATLAS_SABLONLAR/scripts/check_models.py',
         lambda k: ['--dizin', str(k / 'sandbox_mod')],
         lambda k: degistir(k, 'sandbox_mod/.opencode/agent/ajan.md',
                            'openrouter/anthropic/claude-opus-5', '~/anthropic/claude-opus-5'),
         'MOD-06'),
    ]


def hazirla(kok):
    """Temiz kopya + vakalarin temiz taban fiksturleri."""
    yaz(kok / 'sandbox' / 'notlar.md', '# Notlar\n\nBu dosyada sir yok.\n')
    yaz(kok / 'sandbox' / 'MASTER.md', dec_govde(DEC_BASLIKLAR))
    yaz(kok / 'sandbox' / 'makale.md', qr_govde(uzun_mu=False))
    # fix_reconcile varsayilan adlari kokerde arar.
    yaz(kok / '01-FAZ-1-LENS-ANALYSIS.json', REC_FAZ1)
    yaz(kok / '02-FAZ-2-FIX-MANIFEST.md', REC_MANIFEST)
    yaz(kok / '03-FAZ-3-MASTER-v5.5.md', REC_MASTER)
    yaz(kok / 'gate' / 'STRONG-gate-2b-v5.5.json', REC_GATE2B)
    yaz(kok / 'sandbox' / 'sinif.md', SINIF_MD)
    yaz(kok / 'sandbox' / 'scope_tr.md', SCOPE_TR)
    yaz(kok / 'sandbox' / 'metin_tr.md', METIN_TR)
    yaz(kok / 'sandbox' / 'cite.md', CITE_MD)
    yaz(kok / 'sandbox' / 'dec.md', DEC_MD)
    yaz(kok / 'sandbox_mod' / '.opencode' / 'agent' / 'ajan.md',
        '---\ndescription: test ajani\nmode: subagent\n'
        'model: openrouter/anthropic/claude-opus-5\n---\n\nCALISTIRILMADI\n')
    # scope_profile_check: depodaki gercek sozlesme + profil beyani.
    sozlesme = (KOK / 'DENEME' / '00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md').read_text(
        encoding='utf-8').replace(
            '| SC-022 | Provenance Durumu | ZORUNLU | \u00dcretilecek | CHK-02 |',
            '| SC-022 | Provenance Durumu | ZORUNLU | \u00dcretilecek | CHK-02 |\n'
            '| SC-030 | Kapsam Kapanisi | ZORUNLU | \u00dcretilecek | Kapanis kontrolu |')
    yaz(kok / 'sandbox' / 'scope.md', 'ALAN_PROFILI: ampirik\n\n' + sozlesme)


def main():
    print('MUTASYON BATARYASI — ATLAS + KOD kapi kurallari')
    print('kaynak: %s' % KOK.name)
    print('kural: once TEMIZ TABAN (rc=0), sonra tek ihlal, sonra KIRMIZI (rc!=0 + iz).')
    print()

    gecen = 0
    satirlar = []
    for kimlik, katman, kural, kapi, argumanlar, mutasyon, iz in vakalar():
        tmp = Path(tempfile.mkdtemp(prefix='atlas_mut_'))
        try:
            hedef = tmp / 'depo'
            shutil.copytree(KOK, hedef, symlinks=True, ignore=ATLA)
            hazirla(hedef)
            durum, ayrinti = taban_ve_mutasyon(hedef, kapi, argumanlar, mutasyon, iz)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        if durum == 'GECTI':
            gecen += 1
        satirlar.append((kimlik, katman, kural, durum, ayrinti))
        print('  [%d/%d] %-13s %-6s %-34s %s' % (
            len(satirlar), len(vakalar()), kimlik, katman, durum, kural))
        print('         %s' % ayrinti)

    print()
    print('SONUC: %d/%d kural atesledi · taban temiz olmayan=%d' % (
        gecen, len(vakalar()),
        sum(1 for s in satirlar if s[3] == 'TABAN_KIRIK')))

    kirik = [s for s in satirlar if s[3] != 'GECTI']
    if kirik:
        print('HUKUM: FAIL — ateslemeyen vaka var; kapi kaniti eksik.')
        return 1
    print('HUKUM: PASS — her kural temiz tabanda sessiz, ihlalde kirmizi.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
