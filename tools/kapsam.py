#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kapsam — yayimlanan ATLAS/KOD kapı kurallarinin TAM envanteri ve kapsami.

NEDEN VAR
  "5/5 kural atesledi" cumlesi, kac kuralin hic test edilmedigini soylemez.
  Bu betik her kurali tek tek listeler; mutasyon vakasi olmayan her kural icin
  ya OLCULMUS bir kapsam-disi gerekcesi ya da "BOSLUK" yazar. Gerekce uydurulmaz:
  siniflandirma betiklerin gercek bagimliliklarina dayanir (asagidaki tablo).
  Cikti docs/MUTASYON_KAPSAM.md'ye yazilir.

KULLANIM
  python3 tools/kapsam.py            # markdown'i ekrana bas
  python3 tools/kapsam.py --yaz     # docs/MUTASYON_KAPSAM.md'yi yaz
  python3 tools/kapsam.py --kontrol # dosya guncel mi (CI; farkliysa rc=1)
"""
import contextlib
import importlib.util
import io
import json
import re
import subprocess
import sys
from pathlib import Path

import kapi_cikti

KOK = Path(__file__).resolve().parents[1]
HEDEF = KOK / 'docs' / 'MUTASYON_KAPSAM.md'
DIZINLER = ('ATLAS_SABLONLAR/scripts', 'KOD_SABLONLAR/scripts')

KURAL = re.compile(r'^\s{0,8}([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})\b')
# Dosyanin herhangi bir yerindeki bolum basligi: `# --- FRZ-08 ...`.
# Bu, ust KURALLAR listesine yazilmamis ama kodda hukum ureten kurali yakalar.
BOLUM = re.compile(r'^\s*#+\s*-{2,}\s*([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})\b')
# Kod icinde string literal olarak uretilen kimlikler (or. AI-00, HJ-01).
# Bunlar KURALLAR basligi veya bolum basligi degildir; envantere kural olarak
# eklenmezler ama asagidaki KOD_ICI_GEREKCE ile sessizce gizlenmeleri engellenir.
KOD_ICI_TAM = re.compile(r'[A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3}')
KOD_ICI = re.compile(r'''["']([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})["']''')
# Ayni kimligi kelime ici ve uzun sayili varyantlardan ayirir; test kaniti
# taramasinda `SC-0010` gibi bir kimlik `SC-001` sayilmaz.
KOD_ICI_REFERANS = re.compile(
    r'(?<![\w-])(' + KOD_ICI_TAM.pattern + r')(?![\w-])')
# Her kod-ici dislama gerekcesi kaynak dosyayi ve satir araligini tasir.
# Fonksiyon referansi istege baglidir; varsa gercek bir fonksiyon olmalidir.
KOD_ICI_KAYNAK = re.compile(
    r'Kaynak:\s+(?P<yol>[A-Za-z0-9_./-]+\.py):(?P<ilk>[1-9][0-9]*)'
    r'(?:-(?P<son>[1-9][0-9]*))?'
    r'(?:\s+\((?P<fonksiyon>[A-Za-z_][A-Za-z0-9_]*)\))?')
# OLCUM-* bir kapi kurali degil, olcum kaydinin referansidir.
YOKSAY_PREFIX = {'OLCUM'}

# 23 bosluk 19.11.2026 tarihli 3a6d09a tablosunda tabandi; 20.11.2026'da
# 4ebb2e9 ile 23'unun tamami gercek mutasyon vakasiyla kapatildi. Bu liste
# tarihsel tabandir: kapanmis bir kural yeniden bosluga duserse ratchet kirmizi
# olur; yeni kural ise ancak test veya KAPSAM_ISTISNA ile gecebilir.
TABAN_BOSLUK_TARIHI = '3a6d09a'
TABAN_BOSLUKLAR = frozenset({
    'CHK-01', 'CHK-02', 'CHK-05',
    'RECK-01', 'RECK-02', 'RECK-04', 'RECK-05', 'RECK-06',
    'RECK-07', 'RECK-08', 'RECK-09',
    'FRZ-08',
    'TST-01', 'TST-02', 'TST-03', 'TST-05', 'TST-06',
    'TST-07', 'TST-08', 'TST-09', 'TST-10', 'TST-11', 'TST-12',
})
GUNCEL_IZINLI_BOSLUKLAR = frozenset()
# Regresyon ratchet tabani: mevcut tabloda 83 kural atesleyen vakayla test
# edilmis, bosluk 0'dir. Bu sayilar yalniz ARTABILIR; test edilen kural azalirsa
# (or. bir kural yalniz beklenen-bulguya donerse) veya bosluk artarsa kirmizi.
TABAN_TEST_EDILEN = 93
TABAN_BOSLUK_SAYISI = 0

# Kapsam disi gerekceleri BETIKLERIN GERCEK BAGIMLILIKLARINA dayanir:
#   api_surface  : _KOSU/gate/BASELINE.json (KFAZ0 imza envanteri) yoksa CALISTIRILMADI
#   dep_audit    : `git diff --name-only HEAD` ile degisen dosyalari okur
#   olgu_lint    : SURUM.md makine blogunu HEAD/commit hashleriyle karsilastirir
#   oztest_attest: butun agacin selftest hash tabanini + ham kosu ciktisini ister
#   teslim_imza  : HMAC anahtari (LAB_IMZA_ANAHTARI veya ~/.config/lab_imza.key)
#   verify_doi   : kural kimligi bildirmiyor; DEC-027 bir karar referansi
# OLU KIMLIK — satir basinda/bolum basliginda BILDIRILIR ama betigin hicbir
# kod dalinda BASILMAZ. Yani bir hukum uretmezler: mutasyonla ateslenemezler ve
# envantere katildiklarinda "kapsanan kural" sayisini sisirirler.
#
# OLCUM (`tools/kapsam.py --oztest`, AST): her kapi betigi gezilir; kimlik
# docstring DISINDA bir string sabiti olarak kodda akiyorsa basilabilir sayilir.
# Bu uc kimlikte akmaz. Envanter onlari SAYMAZ (`bildirilen` 121 -> 118);
# gerekce burada ve `docs/MUTASYON_KAPSAM.md` tablosunda gorunur.
# Iki yonlu fail-closed: (a) olculen her olu kimlik burada gerekceli olmali,
# (b) buradaki her kayit hala olculen bir olu kimlik olmali. Dal eklenip kimlik
# basilirsa kayit bayatlar ve `make kapsam` kirmizi olur.
OLU_KIMLIK = {
    ('ATLAS_SABLONLAR/scripts/oztest_attest.py', 'OZT-04'):
        'Kaldirilmis sayac kurali. Baslikta yalniz "OZT-04 NICIN YOK" '
        'aciklamasi olarak gecer; kodda bu kimligi basan dal yok. Kimlik '
        'sayisi dususu zaten OZT-02 ile yakalanir.',
    ('KOD_SABLONLAR/scripts/api_surface.py', 'API-03'):
        'OLCULDU: AST string sabiti ve `batarya` vakasi yok. T1 dali '
        '`onceki - sonraki` ad kumesiyle yalniz API-02 (kayip) uretir; '
        'parametre/donus bilgisi tasinmadigi icin degisen imza ayirt edilemez. '
        'Bu bir uygulama boslugu; P0 vaadi karsilanmiyor.',
    ('KOD_SABLONLAR/scripts/dep_audit.py', 'DEP-02'):
        'OLCULDU: AST string sabiti ve `batarya` vakasi yok. `dep_audit.py` '
        'yalniz kilit dosyasinin varligini denetler; kilit paket adlarini '
        'manifestle karsilastiran dal yok. Bu bir uygulama boslugu; P0 vaadi '
        'karsilanmiyor.',
}
# Kolaylik: kimlik -> (betik, gerekce). RISK tablosu kimlikle arar.
OLU_KIMLIKLER = {k: (b, g) for (b, k), g in OLU_KIMLIK.items()}

# Betik duzeyinde kapsam-disi gerekce. OLCULDU: bos — kalan uc olu kimlik
# OLU_KIMLIK sinifinda; SEC-04 artik kodda basilip kural envanterine girdi.
KAPSAM_DISI = {}
TABAN_KAPSAM_DISI = frozenset()

# Uc mutasyon kumesi: her canli kuralin bir vakasi olmali; olu kimlik ise
# yalniz gerekceli olarak ayri tutulur. Kural listesi envanterden turetilir;
# burada kimlik listesi tekrarlanmaz.
KAPSAM_KUMELERI = {
    'teslim_imza': 'ATLAS_SABLONLAR/scripts/teslim_imza.py',
    'api_surface': 'KOD_SABLONLAR/scripts/api_surface.py',
    'dep_audit': 'KOD_SABLONLAR/scripts/dep_audit.py',
}

# Meta araclar kural envanterine girmez (KURAL kimlikleri yoktur), ama
# mutasyon bataryasinda kendi negatif testleriyle temsil edilmelidir. Bu
# sozluk iki yonlu fail-closed'dir: her hedefin en az bir META vakasi olmali;
# bir META vakasinin hedefi buradaki dosyayla ayni olmali. Meta vakalari
# test edilen kural sayacina ve kapsam ratchet'ina eklenmez.
META_ARACLARI = {
    'iddia': 'tools/iddia.py',
    'kanit': 'tools/kanit.py',
    'durum': 'tools/durum.py',
    'kapsam': 'tools/kapsam.py',
}

# Yeni bir kural gercekten test edilemiyorsa gerekcesi buraya ACIKCA yazilir:
#   ('KOD_SABLONLAR/scripts/ornek.py', 'ORN-07'): 'olculmus gerekce',
# Anahtar betik+yeni kuraldir; betik adi tek basina yeni kurala gerekce vermez.
KAPSAM_ISTISNA = {
    ('KOD_SABLONLAR/scripts/secret_scan.py', 'SEC-06'):
        'Olculdu: tools/sir_gecmis_selftest.py vaka_bolunmus_eposta + '
        'vaka_eski_kisisel_eposta ile PII kuralini uctan uca atesler; '
        'mutasyon bataryasinin kopyasi .git tasimadigi icin ayni Git '
        'senaryosu orada kurulmuyor. Gelecekte ayni fixture bataryaya '
        'tasinirsa bu istisna kaldirilmalidir.',
    ('KOD_SABLONLAR/scripts/secret_scan.py', 'SEC-07'):
        'Olculdu: tools/sir_gecmis_selftest.py vaka_shallow + vaka_git_yok '
        'ile eksik/bozuk Git gecmisini fail-closed atesler; batarya kopyasi '
        '.git tasimadigi icin bu senaryo dogrudan bataryada kurulamiyor. '
        'Gercek kapi make dogrula on kosulu olarak kosar.',
}


# Baska kurala/karara yapilan atiflar envantere girmez. Her satir
# (betik, kimlik) -> olculmus gerekce. Ornek: verify_doi.py icindeki DEC-027
# bir karar kimligidir; verify_doi bu kurali uygulamaz, yalniz
# bolum-farkindaligi politikasina atif yapar.
REFERANS = {
    ('ATLAS_SABLONLAR/scripts/verify_doi.py', 'DEC-027'):
        'DEC karar kimligi; verify_doi bu kurali uygulamaz, DEC-027 '
        'bolum-farkindaligi politikasina atif yapar',
}

# Kural kimligi bildirmeyen ama kapi gorevi goren betikler. Bunlar kural
# envanterine giremez (kimlikleri yok), fakat tarama disinda da birakilamaz:
# her biri tanı, kutuphane veya gerekceli kapsam disi siniflarindan biriyle ve
# olculmus gerekceyle kaydedilir. Kimliksiz bir betik "kural" diye
# etiketlenemez: kural sayilabilmesi icin envanterde bir KURAL kimligi ve
# mutasyon/vaka bagi gerekir. Yeni bir kimliksiz betik eklenirse `make kapsam`
# fail-closed durur; betik sonradan kural kimligi kazanirsa eski siniflandirma
# bayat sayilir.
KIMLIKSIZ_SINIFLAR = {
    'ATLAS_SABLONLAR/scripts/ai_disclosure.py': (
        'tani',
        'AI beyan uretici/checker; AI-00..04 alt tani kodlari var, '
        'bagimsiz KURAL kimligi yok; AI-1 testiyle olculur.'),
    'ATLAS_SABLONLAR/scripts/apply_routing.py': (
        'kutuphane',
        'Yonlendirme profili uygulayici; ORTAK masterinin birebir kopyasi '
        've RT-1/RT-2 testleri var; kapi kurali degil.'),
    'ATLAS_SABLONLAR/scripts/budget_guard.py': (
        'kapsam-disi',
        'Butce on-kontrol kapisi (--preflight); BG-1..BG-4 testleri var, '
        'ancak bagimsiz KURAL kimligi ve kural mutasyon vakasi yok. '
        'Envantere alinmadi; betik duzeyinde gerekceli kapsam disi.'),
    'ATLAS_SABLONLAR/scripts/gate_2c.py': (
        'kapsam-disi',
        'Gate-2C pivotal istisna kapisi; G2C-00..05 hata/tani kodlari var, '
        'ancak KURAL kimligi yok. Gercek kapi `check_integrity.sh --gate2c` '
        'ile harici panel ve Crossref DOI girdisi ister; ag hatasinda '
        'BLOCKED doner. Hermetik atlas_selftest G2C matrisi davranisi '
        'olcer, kural basina mutasyon vakasi yoktur; envantere alinmadi.'),
    'ATLAS_SABLONLAR/scripts/gate_merge.py': (
        'kapsam-disi',
        '2A/2B birlestirici; P0/P1 degerlerini ham dizilerden yeniden '
        'hesaplar ve GM testleri vardir, ancak bagimsiz KURAL kimligi ve '
        'kural mutasyon vakasi yok. Envantere alinmadi.'),
    'ATLAS_SABLONLAR/scripts/review_panel.py': (
        'kapsam-disi',
        'MAIN/REVIEWER/CRITIC panel sema ve hukum dogrulayicisi; HJ-* '
        'tani kodlari var, ancak KURAL kimligi yok. HJ-1 matrisi davranisi '
        'olcer; kural basina mutasyon vakasi olmadigi icin envantere alinmadi.'),
    'ATLAS_SABLONLAR/scripts/verify_doi.py': (
        'tani',
        'DOI/UNVERIFIED checker; DEC-027 yalniz karar referansi, KURAL '
        'kimligi yok; VD testleriyle olculur.'),
    'KOD_SABLONLAR/scripts/apply_routing.py': (
        'kutuphane',
        'Yonlendirme profili uygulayici; ORTAK masterinin birebir kopyasi '
        've RT-1/RT-2 testleri var; kapi kurali degil.'),
    'KOD_SABLONLAR/scripts/budget_guard.py': (
        'kapsam-disi',
        'Butce on-kontrol kapisi (--preflight); BG-1..BG-4 testleri var, '
        'ancak bagimsiz KURAL kimligi ve kural mutasyon vakasi yok. '
        'Envantere alinmadi; betik duzeyinde gerekceli kapsam disi.'),
    'KOD_SABLONLAR/scripts/imzala.py': (
        'kutuphane',
        'BASELINE HMAC imza yardimcisi; freeze_check tarafindan tuketilir, '
        'tek basina kapi kurali degil.'),
    'KOD_SABLONLAR/scripts/kod_gate_merge.py': (
        'kapsam-disi',
        'KOD 2-of-2/3-of-3 birlestirici; ORTAK/scripts/ortak_gate.py '
        'ilkelerini import eder ve GM testleri vardir, ancak bagimsiz '
        'KURAL kimligi ve kural mutasyon vakasi yok. Envantere alinmadi.'),
    'KOD_SABLONLAR/scripts/katalog_kontrol.py': (
        'kapsam-disi',
        'Canli models.dev katalog kapisi; allowlist ve bedava profili '
        'testleriyle olculur, ancak bagimsiz KURAL kimligi ve kural '
        'mutasyon vakasi yok. Envantere alinmadi.'),
}

KIMLIKSIZ_ETIKETLER = {
    'tani': 'tanı',
    'kutuphane': 'kütüphane',
    'kapsam-disi': 'kapsam dışı',
}

# Baslikta bildirilmeyen ama betik kodunda string literal olarak uretilen
# kimlikler. Anahtar (betik, TAM kimlik); yeni bir kimlik ayni ailede bile
# otomatik kabul edilmez. Aile oneki anahtar olarak kabul edilmez; aksi halde
# yeni bir kimlik sessizce ayni gerekceye duserdi. Bunlar bagimsiz kapi kurali
# degil, tani/veri kimligidir; bu yuzden 118'lik kural envanterine ve mutasyon
# ratchet'ine sayilmazlar. Her kaydin gerekcesi burada, tek makine-okunur
# kaynaktadir.
KOD_ICI_GEREKCE = {
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-00'):
        ('tani-kodu', 'Manifest veya sema yok/bozuk; AI-1 onkosul tanisi, '
                      'bagimsiz KURALLAR kurali degil. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/ai_disclosure.py:144 '
                      '(manifest_dogrula).'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-01'):
        ('tani-kodu', 'Manifest kok/schema/scope/entries sozlesmesi; '
                      'AI-1 selftestinin alt tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/ai_disclosure.py:145 '
                      '(manifest_dogrula).'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-02'):
        ('tani-kodu', 'Entry alan/usage/evidence dogrulamasi; AI-1 '
                      'selftestinin alt tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/ai_disclosure.py:131 '
                      '(_metin_al).'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-03'):
        ('tani-kodu', 'Beyan yazma I/O hatasi; hukum uretmeyen operasyonel '
                      'tani. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/ai_disclosure.py:314 (main).'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-04'):
        ('tani-kodu', '--check cikti uyusmazligi; AI-1 selftestinde kilitli '
                      'cikti butunlugu alt tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/ai_disclosure.py:302 (main).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-00'):
        ('tani-kodu', 'Panel semasi okunamadi/kimlik uyusmadi; HJ-1 '
                      'onkosul tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/review_panel.py:106 '
                      '(sema_dogrula).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-01'):
        ('tani-kodu', 'JSON/kapali sema/alan sozlesmesi; HJ-1 selftestinin '
                      'alt tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/review_panel.py:73 (json_oku).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-02'):
        ('tani-kodu', 'Run/input uyusmazligi; HJ-1 selftestinin alt tanisi. '
                      'Kaynak: ATLAS_SABLONLAR/scripts/review_panel.py:206 '
                      '(panel_uret).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-03'):
        ('tani-kodu', 'Hukum kapsami/yinelenen kimlik/severity; HJ-1 '
                      'selftestinin alt tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/review_panel.py:179 (dizi).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-04'):
        ('tani-kodu', 'Verdict/evidence butunlugu; HJ-1 selftestinin alt '
                      'tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/review_panel.py:164 '
                      '(judgment_dogrula).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-05'):
        ('tani-kodu', 'Rol/session kimligi; HJ-1 selftestinin alt tanisi. '
                      'Kaynak: ATLAS_SABLONLAR/scripts/review_panel.py:121 '
                      '(ortak_dogrula).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-06'):
        ('tani-kodu', 'Model ailesi/session cesitliligi; HJ-1 selftestinin '
                      'alt tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/review_panel.py:211 '
                      '(panel_uret).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-07'):
        ('tani-kodu', 'Attempt/maliyet siniri; HJ-1 selftestinin alt tanisi. '
                      'Kaynak: ATLAS_SABLONLAR/scripts/review_panel.py:93 '
                      '(maliyet).'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-08'):
        ('tani-kodu', 'Panel ciktisi yazma I/O hatasi; operasyonel tani. '
                      'Kaynak: ATLAS_SABLONLAR/scripts/review_panel.py:397 '
                      '(main).'),
    ('ATLAS_SABLONLAR/scripts/olgu_lint.py', 'OLGU-01'):
        ('tani-kodu', 'OLGULAR kanonu yok; olgu_lint onkosulu, OLGU-04..06 '
                      'kurallarindan ayri. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/olgu_lint.py:458 (main).'),
    ('ATLAS_SABLONLAR/scripts/olgu_lint.py', 'OLGU-02'):
        ('tani-kodu', 'OLGULAR JSON/sema girdisi gecersiz; onkosul tanisi. '
                      'Kaynak: ATLAS_SABLONLAR/scripts/olgu_lint.py:466 '
                      '(main).'),
    ('ATLAS_SABLONLAR/scripts/olgu_lint.py', 'OLGU-03'):
        ('tani-kodu', 'Ic deger uyusmazligi; OLGU-04..06 kapsamindaki tarihce '
                      'denetiminin alt tanisi. Kaynak: '
                      'ATLAS_SABLONLAR/scripts/olgu_lint.py:510 (main).'),
    ('KOD_SABLONLAR/scripts/chg_reconcile.py', 'RECK-00'):
        ('tani-kodu', 'Ortak girdi/JSON/sema hatasi; RECK-08 sema kurali, '
                      'RECK-01..09 ayri kurallardir. Kaynak: '
                      'KOD_SABLONLAR/scripts/chg_reconcile.py:90 '
                      '(makine_blogu).'),
}
# SC kimlikleri kapsam sozlesmesinin zorunlu BOLUM numaralaridir; kapi
# kurali degildir. Tam liste: yeni bir SC kimligi kendiliginden gecmesin.
# Her kimlik icin kaynak satiri ayridir; tablo gruplama yapmadan 41 kaydi
# gosterir ve `kod_ici_kaynak_dogrula` bu satirin kimligi tasidigini sınar.
SC_KAYNAK_SATIRLARI = {
    'SC-001': 36, 'SC-002': 39, 'SC-003': 36, 'SC-004': 36,
    'SC-005': 36, 'SC-006': 36, 'SC-007': 39, 'SC-008': 36,
    'SC-009': 39, 'SC-010': 39, 'SC-011': 36, 'SC-012': 37,
    'SC-013': 37, 'SC-014': 37, 'SC-015': 37, 'SC-016': 37,
    'SC-017': 143, 'SC-018': 37, 'SC-019': 37, 'SC-020': 38,
    'SC-021': 38, 'SC-022': 38, 'SC-030': 38,
}
for _sc, _sc_satir in SC_KAYNAK_SATIRLARI.items():
    if _sc == 'SC-017':
        _sc_gerekce = (
            'Kapsam sozlesmesindeki DPIA zorunlu bolum kimligi; SP-05 '
            'kosulunda denetlenir. Kaynak: '
            'ATLAS_SABLONLAR/scripts/scope_profile_check.py:%d.' % _sc_satir
        )
    else:
        _sc_gerekce = (
            'Kapsam sozlesmesindeki zorunlu bolum kimligi; SP-01..07 kuraldir. '
            'Kaynak: ATLAS_SABLONLAR/scripts/scope_profile_check.py:%d.'
            % _sc_satir
        )
    KOD_ICI_GEREKCE[('ATLAS_SABLONLAR/scripts/scope_profile_check.py', _sc)] = (
        'veri-kimligi', _sc_gerekce)
del _sc, _sc_satir, _sc_gerekce

# 41 kod-ici kimligin test kaniti. Anahtar (betik, tam kimlik); durum:
#   oz-test : kimligi dogrudan denetleyen bir assertion/test adi var
#   fikstur : yalniz test girdisi/verisi; bagimsiz assertion yok, TEST YOK
#   yok     : hicbir test dosyasinda gecmiyor
# Fiksturde gecmek test kaniti sayilmaz; bu yuzden fikstur satirlari tabloda
# TEST YOK olarak gorunur. Varsayilan `yok`tur: yeni bir test referansi
# belirirse asagidaki kayit guncellenmeden `kod_ici_kanit_dogrula` durur.
KOD_ICI_TEST_KANITI = {
    anahtar: ('yok', '', '') for anahtar in KOD_ICI_GEREKCE
}
KOD_ICI_TEST_KANITI.update({
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-00'):
        ('oz-test', 'AI-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-01'):
        ('oz-test', 'AI-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-02'):
        ('oz-test', 'AI-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-04'):
        ('oz-test', 'AI-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),

    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-00'):
        ('oz-test', 'HJ-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-01'):
        ('oz-test', 'HJ-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-02'):
        ('oz-test', 'HJ-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-03'):
        ('oz-test', 'HJ-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-04'):
        ('oz-test', 'HJ-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-05'):
        ('oz-test', 'HJ-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-06'):
        ('oz-test', 'HJ-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-07'):
        ('oz-test', 'HJ-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),

    ('ATLAS_SABLONLAR/scripts/olgu_lint.py', 'OLGU-01'):
        ('oz-test', 'OLG-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/olgu_lint.py', 'OLGU-03'):
        ('oz-test', 'OLG-1', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),

    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-002'):
        ('oz-test', 'SRC-01/SRC-02',
         'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-005'):
        ('oz-test', 'PC-3', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-006'):
        ('oz-test', 'PC-4', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-007'):
        ('oz-test', 'SP-2', 'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-022'):
        ('oz-test', 'eksik-kapsam', 'tools/temiz_teslim_selftest.py'),

    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-001'):
        ('fikstur', 'temel kapsam fiksturu',
         'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-003'):
        ('fikstur', 'REC-01/SP-02 fiksturu',
         'tools/mutasyon_bataryasi.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-008'):
        ('fikstur', 'VD bolum capasi',
         'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-009'):
        ('fikstur', 'SP profil fiksturu',
         'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-010'):
        ('fikstur', 'SP profil fiksturu',
         'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
    ('ATLAS_SABLONLAR/scripts/scope_profile_check.py', 'SC-030'):
        ('fikstur', 'temel kapsam fiksturu',
         'ATLAS_SABLONLAR/scripts/atlas_selftest.py'),
})

# Risk sirasi — 19.11.2026'daki 51 mutation-kapsamsiz kuralin tamami.
# Siralama ilkesi: once sahte yesil/tamper (P0), sonra tedarik/teslim/yuzey,
# sonra test envanteri/olcum/provenance; bilgi seviyesindeki olu kimlik sonda.
# Liste sabittir: vakalar eklense de siralama degismez, durum sutunu guncellenir.
# Tablodaki kapanis durumu takvim gunune baglidir; kalici olmayan ifade
# yerine tarih tek yerde tutulur.
KAPSAM_TARIHI = '24.11.2026'

RISK_GRUPLARI = {
    'KANIT': 'Kanit/yesil butunlugu — P0',
    'KAPSAM': 'Kapsam/degisiklik butunlugu — P0',
    'TEDARIK': 'Tedarik, teslim ve disa acik yuzey — P0/P1',
    'ENVANTER': 'Test envanteri, olcum ve provenance — P0/P1',
    'BILGI': 'Bilgi seviyesi — P0/P1 disi',
}
RISK_SIRASI = [
    ('TST-08', 'KANIT'), ('RECK-06', 'KAPSAM'), ('DEP-05', 'TEDARIK'),
    ('FRZ-08', 'KAPSAM'), ('RECK-01', 'KAPSAM'), ('RECK-02', 'KAPSAM'),
    ('RECK-08', 'KAPSAM'), ('RECK-09', 'KAPSAM'), ('RECK-04', 'KAPSAM'),
    ('RECK-05', 'KAPSAM'), ('RECK-07', 'KAPSAM'), ('TST-07', 'KANIT'),
    ('TST-10', 'KANIT'), ('TST-11', 'KANIT'), ('TST-12', 'KANIT'),
    ('TST-09', 'KANIT'), ('TST-01', 'KANIT'), ('TST-02', 'KANIT'),
    ('TST-03', 'KANIT'), ('TST-05', 'KANIT'), ('TST-06', 'KANIT'),
    ('DEP-01', 'TEDARIK'), ('DEP-02', 'TEDARIK'), ('DEP-06', 'TEDARIK'),
    ('DEP-03', 'TEDARIK'), ('DEP-04', 'TEDARIK'), ('TSL-03', 'TEDARIK'),
    ('TSL-04', 'TEDARIK'), ('TSL-06', 'TEDARIK'), ('TSL-01', 'TEDARIK'),
    ('TSL-02', 'TEDARIK'), ('TSL-05', 'TEDARIK'), ('API-02', 'TEDARIK'),
    ('API-03', 'TEDARIK'), ('API-01', 'TEDARIK'), ('API-05', 'TEDARIK'),
    ('API-04', 'TEDARIK'), ('OZT-01', 'ENVANTER'), ('OZT-02', 'ENVANTER'),
    ('OZT-03', 'ENVANTER'), ('OZT-04', 'ENVANTER'), ('OZT-05', 'ENVANTER'),
    ('OZT-06', 'ENVANTER'), ('OLGU-04', 'ENVANTER'), ('OLGU-05', 'ENVANTER'),
    ('OLGU-06', 'ENVANTER'), ('CHK-01', 'ENVANTER'), ('CHK-02', 'ENVANTER'),
    ('CHK-05', 'ENVANTER'), ('SEC-04', 'BILGI'),
]
RISK_EKLENEN = {'TST-08', 'RECK-06', 'DEP-05',
               'RECK-01', 'RECK-02', 'RECK-04',
               'RECK-05', 'TST-07', 'TST-09',
               'TST-01', 'TST-02', 'TST-03',
               'TST-05', 'RECK-08', 'RECK-07',
               'FRZ-08', 'RECK-09', 'TST-06',
               'TST-10', 'TST-11', 'TST-12',
               'CHK-01', 'CHK-02', 'CHK-05'}
RISK_NOT = {
    'TST-08': 'Ham test raporu yok/okunamiyor — kanitsiz PASS P0; kapinin kanit temeli.',
    'RECK-06': 'Dondurulmus bolge diff\'te — dogrudan tamper sinyali, P0.',
    'DEP-05': 'Izinli lisans listesi disinda bagimlilik — tedarik/uyum P0.',
    'RECK-01': 'KFAZ0 sozlesmesindeki her REQ plan/eslesmede karsilik bulmali; '
               'aksi halde kapsamsiz sozlesme sessizce yesil kalir.',
    'RECK-02': '"UYGULANMIS" denilen her CHG\'nin dosyasi git diff\'te olmali; '
               'beyan ile gercek degisiklik carpraz denetlenir.',
    'RECK-04': '2B kapisinin "KANITLI" dedigi her CHG diff\'te olmali; ikinci '
               'gozun iddiasi manifest ve diff ile dogrulanir.',
    'FRZ-08': 'Temiz agac iddiasi imzayla baglanmali; imzasiz, gecersiz imzali '
               'veya imzalandiktan sonra icerigi degistirilmis taban terminal '
               'tamper ya da dusuk guven sayilir.',
    'RECK-05': 'Hayalet CHG yok: olmayan REQ veya plansiz dosyaya baglanan '
               'degisiklik P0; manifest-diff bagini korur.',
    'RECK-07': 'Davranissal her REQ tabanda olmayan YENI bir test adina '
               'eslenmeli; eski testi gostermek bedava yesildir.',
    'RECK-08': 'Makine bloklarinin alan bicimi semaya uymali; sessizce dusen '
               'girdi RECK-01/07\'yi devre disi birakir.',
    'RECK-09': 'Plan yokken urun kodu degismemeli; KFAZ0 oncesi degisiklik '
               'kapsamsiz ve denetimsiz kalir.',
    'TST-01': 'Basarisiz test sayisi sifir olmali; kirmizi testle PASS verilemez.',
    'TST-02': 'Hatali test sayisi sifir olmali; altyapi hatasi yesil sayilmaz.',
    'TST-03': 'En az bir test kosmali; sifir test temiz degildir.',
    'TST-05': 'Atlanan test tabandan fazla olamaz; test atlayarak yesil olunmaz.',
    'TST-06': 'Kapsam tabanin bir altina kadar korunmali; sessiz kapsam kaybi P1.',
    'TST-07': 'Kanit beyani ham JUnit ile celisemez; kapi kendi beyanina guvenmez.',
    'TST-09': 'Test komutunun cikis kodu kayitli olmali; kosup kosmadigi '
               'bilinmeyen test yesil sayilmaz.',
    'TST-10': 'Rapor kaynaktan eski olamaz; bayat kanit mevcut kodu olcmemis olabilir.',
    'TST-11': 'Kanittaki komut kod_profil ile ayni olmali; baska komutun kaniti '
               'sayilmaz.',
    'TST-12': 'Kanittaki rapor yolu kod_profil ile ayni olmali; baska rapor '
               'gosterilemez.',
    'CHK-01': 'Her zorunlu SCOPE-ID MASTER icinde markdown basligi olarak '
               'bulunmali; metinde gecmesi yetmez.',
    'CHK-02': 'Her zorunlu ID PROVENANCE tablosunda kapsiyor durumunda olmali.',
    'CHK-05': 'Basliklar benzersiz olmali; tekrar eden baslik izlenebilirligi bozar.',
}

# Risk tablosunda grup etiketi tek basina gerekce degildir. Asagidaki kayitlar
# her kuralin somut riskini tek cumlede tutar; yeni kural icin kayit zorunludur.
RISK_NOT.update({
    'DEP-01': 'Manifest varken kilit anahtari yok, bos ya da kilit dosyasi eksikse bagimlilik surumleri denetimsiz kalir; kapi P0 verir.',
    'DEP-02': 'OLU KIMLIK: `dep_audit.py` yalniz kilit dosyasi varligini denetler; kilit paketlerini manifestle karsilastiran dal ve string sabiti yok. Ayrintili olcum Envanter disi tablosunda.',
    'DEP-06': 'P1: profilde `bagimlilik_manifesti` bos liste ise CALISTIRILMADI + OLCULMEYEN uretir; vaka DEP-06 listeyi bosaltir, rc=0. Bagimlilik denetimi hic kosmaz.',
    'DEP-03': 'P1: regex `*`, `latest`, `^`, `~` veya bos surumu yakalar; vaka DEP-03 `flask==latest` ekler, rc=0. Bu bir uyari dalidir, P0 degildir.',
    'DEP-04': 'P1: `git diff --name-only HEAD` yalniz kilit dosyasini gorurse uyarir; vaka DEP-04 kilit dosyasina dokunur, manifest sabit kalir, rc=0.',
    'TSL-01': 'Teslim manifesti yok veya bozuksa imza dogrulanamaz; kapi fail-closed P0 verir.',
    'TSL-02': 'Manifestte listelenen dosya diskte yoksa teslim kumesi eksiktir; imza eksik artefakti kurtarmaz, P0.',
    'TSL-03': 'Teslim dosyasinin sha256 degeri manifestten farkliysa artefakt yolda degistirilmistir; P0 tahrifat.',
    'TSL-04': 'Teslim imzasi gecersizse manifest baska anahtarla imzalanmis veya sonradan degistirilmis olabilir; P0.',
    'TSL-05': 'P1: `teslim_imza.py` imza alani YOKSA veya imza VAR ama anahtar yoksa DUSUK_GUVEN uretir; iki dal da rc=0 dondurur. Vaka TSL-05 imza alanini siler; P0 dali yoktur.',
    'TSL-06': 'Zorunlu teslim artefakti manifestte hic yoksa imza eksik kumeyi dogrular; kapsam boslugu P0.',
    'API-01': 'P1: `api_surface.py` taban.get("dis_imza") None ise CALISTIRILMADI uretir; vaka API-01 bu alani siler, rc=0. Karsilastirma yapilamaz, P0 yolu yoktur.',
    'API-02': 'KFAZ0 envanterindeki disa acik imza kaybolursa mevcut cagiranlar sessizce kirilir; P0.',
    'API-03': 'OLU KIMLIK: `api_surface.py` kodunda API-03 string sabiti yok; T1 yalniz ad kumesi karsilastirir, parametre/donus tasimaz. Ayrintili olcum Envanter disi tablosunda.',
    'API-04': 'P1: T2 regex taramasi `foo` adayini bulamazsa DUSUK_GUVEN uretir; vaka API-04 `def foo` -> `def baz` yapar, rc=0. T2 tek basina P0 uretemez.',
    'API-05': 'P1: `imza_komutu` exit!=0 veya T1/T2 yoksa CALISTIRILMADI uretir; vaka API-05 komutu `false` yapar, rc=0. Hicbir kademe P0 karari uretmez.',
    'OZT-01': 'Oz-test taban dosyasi yok veya bozuksa onceki test envanteriyle karsilastirma yapilamaz; fail-closed P0.',
    'OZT-02': 'Tabandaki bir test kimligi bu kosuda yoksa test sessizce silinmistir; P0 kapsam kaybi.',
    'OZT-03': 'Kosuda hic test yoksa sifir test yesil sayilmamali; fail-closed P0.',
    'OZT-04': 'OZT-04 kaldirilmis bir sayac kuralidir; kimlik sayisi dususu zaten OZT-02 tarafindan yakalandigi icin ayri vaka uretmez.',
    'OZT-05': 'Tabanda olmayan yeni bir test kimligi gorulurse pin guncellenmelidir; aksi halde envanter gercek kosuyu yansitmaz, P1.',
    'OZT-06': 'Taban kimlik hash degeri kendi listesiyle uyusmazsa taban elle kurcalanmistir; test envanteri guvenilmez olur, P0.',
    'OLGU-04': 'Kamu attestation kaydi yok veya bozuksa kamu iddialari gercek commit ve agac kanitiyla baglanamaz; FAIL.',
    'OLGU-05': 'ATLAS, attest ve KOD ciktilarindaki sayilar kanonik kayda uymazsa yayimlanan olcum yanlis olur; FAIL.',
    'OLGU-06': 'Son DEVIR sonrasi mekanizma commit hash degerleri DERSLER kaydinda yok veya cozulmuyorsa degisiklik izi kopar; FAIL.',
    'SEC-04': 'Ikili veya kilit dosyasi taranmadan atlanirsa icine gomulmus bir sir gorunmez; atlama yalniz BILGI olarak raporlanir.',
})

# 24.11.2026 itibariyla kapatilamayan bosluk kalmadi; liste bos. Yeni bir bosluk
# olusursa buraya risk sirasiyla yazilir ve markdown bolumu yeniden acilir.
SONRAKI_DILIM = []
SONRAKI_NOT = {
    'FRZ-08': 'Temiz agac imzasi: gecersiz imza ve imzali taban iceriginin '
              'sonradan kurcalanmasi iki ayri terminal rc=2 vakasiyla kapsanir.',
    'RECK-09': 'Plan yokken urun kodu degisimi; KFAZ1 yoklugu P1 urettigi '
               'icin ayri fikstur gerektirir.',
    'TST-10': 'Rapor kaynaktan eski olamaz; bayat kanit mevcut kodu '
              'olcmemis olabilir.',
}


def risk_tablosu(satirlar):
    durum = {k: d for _b, k, _v, d, _g in satirlar}
    betik = {k: b.split('/')[-1] for b, k, _v, _d, _g in satirlar}
    if len(RISK_SIRASI) != 50 or len({r for r, _g in RISK_SIRASI}) != 50:
        raise SystemExit('RISK_SIRASI 50 tekil kural icermeli')
    # Envanter disi olan (olu kimlik) risk satirlari da tabloda kalir: risk
    # listesi envanter degildir, "bu kural uygulanmiyor" bilgisi kaybolmasin.
    eksik = [r for r, _g in RISK_SIRASI
             if r not in durum and r not in OLU_KIMLIKLER]
    if eksik:
        raise SystemExit('RISK_SIRASI envanterde yok: %s' % ', '.join(eksik))
    out = ['| # | Kural | Betik | Grup | Durum | Gerekce |', '|---|---|---|---|---|---|']
    for i, (kural, grup) in enumerate(RISK_SIRASI, 1):
        if kural in OLU_KIMLIKLER:
            _betik, _gerekce = OLU_KIMLIKLER[kural]
            out.append('| %d | %s | `%s` | %s | ENVANTER DISI (olu kimlik) | %s |'
                       % (i, kural, _betik.split('/')[-1],
                          RISK_GRUPLARI[grup], _gerekce))
            continue
        _durum = durum[kural]
        _temel = _durum.split('\u00b7')[0]
        if _temel == 'TEST EDILDI' and kural in RISK_EKLENEN:
            _durum = 'TEST EDILDI (%s)' % KAPSAM_TARIHI
        elif _temel == 'BEKLENEN BULGU' and kural in RISK_EKLENEN:
            _durum = 'BEKLENEN BULGU (%s)' % KAPSAM_TARIHI
        elif _durum == 'BOSLUK':
            # Gizli sayi dusumu yok: kalan her bosluk acikca bir sonraki
            # dilimin kaydidir; kapsam disi gibi etiketlenmez.
            _durum = 'BOSLUK (sonraki dilim)'
        if kural not in RISK_NOT:
            raise SystemExit('RISK_NOT eksik: %s' % kural)
        gerekce = RISK_NOT[kural]
        out.append('| %d | %s | `%s` | %s | %s | %s |' % (
            i, kural, betik[kural], RISK_GRUPLARI[grup], _durum, gerekce))
    return out


def kapi_betikleri():
    for d in DIZINLER:
        for p in sorted((KOK / d).glob('*.py')):
            if not p.name.endswith('_selftest.py'):
                yield p


def _ham_kimlikler(p):
    """Dosyadaki TUM satir basi/bolum bildirimleri — hicbir filtre yok.

    Eski surum yalniz ilk 100 satiri okuyordu; FRZ-08 114. satirdaki bolum
    basliginda kaldigi icin envanterde hic gorunmiyordu. Artik sinir yok.
    """
    baslik, bolum = set(), set()
    for satir in p.read_text(encoding='utf-8').splitlines():
        m = KURAL.match(satir)
        if m and m.group(1).split('-')[0] not in YOKSAY_PREFIX:
            baslik.add(m.group(1))
        m = BOLUM.match(satir)
        if m and m.group(1).split('-')[0] not in YOKSAY_PREFIX:
            bolum.add(m.group(1))
    return baslik, bolum


def _kimlikler(p):
    """ENVANTERE GIREN kimlikler: ham bildirimler eksi REFERANS ve OLU_KIMLIK.

    Baska kurala/karara yapilan atiflar (`REFERANS`, or. DEC-027) ve hicbir kod
    dalinda basılmayan bildirimler (`OLU_KIMLIK`) kural sayilmaz.
    """
    baslik, bolum = _ham_kimlikler(p)
    yol = str(p.relative_to(KOK))
    for (ref_yol, ref_kimlik) in REFERANS:
        if ref_yol == yol:
            baslik.discard(ref_kimlik)
            bolum.discard(ref_kimlik)
    for (olu_yol, olu_kimlik) in OLU_KIMLIK:
        if olu_yol == yol:
            baslik.discard(olu_kimlik)
            bolum.discard(olu_kimlik)
    return baslik, bolum


def _kod_sabitleri(metin):
    """Docstring DISINDAKI string sabitleri (sirayla)."""
    import ast
    agac = ast.parse(metin)
    docstringler = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, (ast.Module, ast.FunctionDef,
                              ast.AsyncFunctionDef, ast.ClassDef)):
            govde = dugum.body
            if (govde and isinstance(govde[0], ast.Expr)
                    and isinstance(govde[0].value, ast.Constant)
                    and isinstance(govde[0].value.value, str)):
                docstringler.add(id(govde[0].value))
    return [d.value for d in ast.walk(agac)
            if isinstance(d, ast.Constant) and isinstance(d.value, str)
            and id(d) not in docstringler]


def kodda_akan_kimlikler(p):
    """Kimliklerin kodda STRING SABITI olarak aktigi kume (docstring haric).

    "Basılıyor" olcutu budur: docstring'de anlatilan bir kimlik de, yalniz
    yorumda gecen bir kimlik de hicbir dala bagli degildir; cikti uretemez.
    Kod icinde `"kural": "DEP-02"` ya da `f"FAIL SEC-00: ..."` gibi bir sabit
    varsa kimlik en az bir dalda basilabilir demektir.
    """
    kume = set()
    for sabit in _kod_sabitleri(p.read_text(encoding='utf-8')):
        kume.update(KURAL_ARAMA.findall(sabit))
    return kume


def bulgu_etiketi_mi(sabit, kimlik):
    """Sabit, kimligi BULGU/hukum etiketi olarak mi tasiyor?

    Bir kapi kurali bulgu sozlugunde (`"kural": "FRZ-08"`) ya da satir basinda
    siddetle (`FAIL X-01 ...`, `BILGI SEC-05 ...`) basilir. Yalniz `[DEC-027]
    muaf bolum sayisi` gibi bilgi etiketi olarak gecen kimlik kural degildir.
    """
    if kimlik not in sabit:
        return False
    if '"kural"' in sabit or "'kural'" in sabit:
        return True
    return bool(re.match(r'\s*(?:FAIL|KALDI|BILGI|UYARI|P0|P1)\b', sabit))


def olu_kimlik_olc():
    """Tum kapi betikleri: bildirilen ama kodda basilmayan kimlikler.

    REFERANS kayitlari burada da disarida tutulur: DEC-027 bir karar kimligidir,
    "olu kural" degildir; iki sinif ayri raporlanir.
    """
    sonuc = {}
    for p in kapi_betikleri():
        yol = str(p.relative_to(KOK))
        baslik, bolum = _ham_kimlikler(p)
        akan = kodda_akan_kimlikler(p)
        for kimlik in sorted((baslik | bolum) - akan):
            if (yol, kimlik) in REFERANS:
                continue
            sonuc[(yol, kimlik)] = 'bildirim var, kodda string sabiti yok'
    return sonuc


def olu_kimlik_dogrula():
    """Iki yonlu fail-closed: gerekcesiz olu kimlik ve bayat gerekce yok."""
    olculen = olu_kimlik_olc()
    gerekcesiz = sorted(set(olculen) - set(OLU_KIMLIK))
    if gerekcesiz:
        raise SystemExit(
            'OLU KIMLIK: gerekcesiz kayit %s; OLU_KIMLIK sozlugune (betik, '
            'kimlik) ve gerekce ekleyin'
            % ', '.join('%s·%s' % (b.split('/')[-1], k) for b, k in gerekcesiz))
    bayat = sorted(set(OLU_KIMLIK) - set(olculen))
    if bayat:
        raise SystemExit(
            'OLU KIMLIK: gerekce bayat %s; ya dal eklendi (kaydi silin, kural '
            'envantere doner) ya da kimlik artik bildirilmiyor'
            % ', '.join('%s·%s' % (b.split('/')[-1], k) for b, k in bayat))
    for (betik, kimlik), gerekce in sorted(OLU_KIMLIK.items()):
        if not isinstance(gerekce, str) or len(gerekce.strip()) < 40:
            raise SystemExit(
                'OLU KIMLIK: gerekce cok kisa: %s·%s' % (betik, kimlik))
    # Dis referanslar da iki yonlu: her REFERANS hala ham bildirimde olmali.
    ham = {}
    for p in kapi_betikleri():
        b, bl = _ham_kimlikler(p)
        ham[str(p.relative_to(KOK))] = b | bl
    for (betik, kimlik) in sorted(REFERANS):
        if kimlik not in ham.get(betik, set()):
            raise SystemExit(
                'REFERANS: bayat kayit %s·%s; betikte bu kimlik artik yok'
                % (betik.split('/')[-1], kimlik))
        # Referans, uygulanan kurala donusmemis olmali: bulgu etiketi olarak
        # basiliyorsa artik kuraldir ve envantere girmelidir.
        for sabit in _kod_sabitleri((KOK / betik).read_text(encoding='utf-8')):
            if bulgu_etiketi_mi(sabit, kimlik):
                raise SystemExit(
                    'REFERANS: %s artik bulgu etiketi olarak basiliyor '
                    '(%s); kaydi silin, kural envantere girmeli'
                    % (kimlik, sabit.strip()[:80]))
        if not isinstance(REFERANS[(betik, kimlik)], str) \
                or len(REFERANS[(betik, kimlik)].strip()) < 40:
            raise SystemExit(
                'REFERANS: gerekce cok kisa: %s·%s' % (betik, kimlik))


def kod_ici_sinifla(yol, kimlik):
    """Tek kod-ici kimligi (sinif, gerekce) olarak cozer; yoksa fail-closed.

    Anahtar TAM (betik, kimlik) ciftidir. Boylece ayni oneke sahip yeni bir
    kimlik (or. AI-99) aile gerekcesiyle sessizce gecemez. Onek anahtarlari
    burada ve kaynak dogrulamasinda reddedilir.
    """
    if not KOD_ICI_TAM.fullmatch(str(kimlik)):
        raise SystemExit(
            'KOD-ICI KAPSAM: tam kimlik bekleniyor: %r · %s; '
            'aile oneki anahtar olarak kullanilamaz' % (kimlik, yol))
    anahtar = (yol, kimlik)
    if anahtar not in KOD_ICI_GEREKCE:
        raise SystemExit(
            'KOD-ICI KAPSAM: belgelenmemis kimlik %s · %s; '
            'KOD_ICI_GEREKCEye (betik, tam kimlik) gerekcesi yaz'
            % (kimlik, yol))
    return KOD_ICI_GEREKCE[anahtar]


def kod_ici_kaynak_dogrula():
    """Her dislama kaydinin tam kimlik, sinif, gerekce ve kaynak tasidigini sinar.

    Kaynak referansi yalniz metin degildir: dosya gercekten var olmali,
    satir araligi dosya sinirinda olmali ve aralikta kimlik gecmelidir.
    Boylece tablodaki her dislama gerekcesi denetlenebilir bir koda baglanir.
    """
    for (yol, kimlik), (sinif, gerekce) in KOD_ICI_GEREKCE.items():
        if not KOD_ICI_TAM.fullmatch(str(kimlik)):
            raise SystemExit(
                'KOD-ICI KAPSAM: gerekce anahtari TAM kimlik olmali: %r · %s; '
                'aile oneki anahtar olarak kabul edilmez' % (kimlik, yol))
        if sinif not in ('tani-kodu', 'veri-kimligi'):
            raise SystemExit(
                'KOD-ICI KAPSAM: gecersiz sinif %r · %s · %s' % (sinif, kimlik, yol))
        if not isinstance(gerekce, str) or len(gerekce.strip()) < 12:
            raise SystemExit(
                'KOD-ICI KAPSAM: gerekcesiz kimlik %s · %s; '
                'KOD_ICI_GEREKCEye gerekce yaz' % (kimlik, yol))
        m = KOD_ICI_KAYNAK.search(gerekce)
        if not m:
            raise SystemExit(
                'KOD-ICI KAYNAK: gerekcede kaynak yok: %s · %s; '
                '"Kaynak: <dosya>:<satir>" ekleyin' % (kimlik, yol))
        kaynak_yolu = m.group('yol')
        kaynak = KOK / kaynak_yolu
        if not kaynak.is_file():
            raise SystemExit(
                'KOD-ICI KAYNAK: dosya yok: %s · %s' % (kaynak_yolu, kimlik))
        satirlar = kaynak.read_text(encoding='utf-8').splitlines()
        ilk = int(m.group('ilk'))
        son = int(m.group('son') or ilk)
        if ilk > son or son > len(satirlar):
            raise SystemExit(
                'KOD-ICI KAYNAK: satir araligi gecersiz: %s:%s-%s · %s'
                % (kaynak_yolu, ilk, son, kimlik))
        if not any(kimlik in satir for satir in satirlar[ilk - 1:son]):
            raise SystemExit(
                'KOD-ICI KAYNAK: %s:%s-%s kimligi icermiyor · %s'
                % (kaynak_yolu, ilk, son, kimlik))
        fonksiyon = m.group('fonksiyon')
        if fonksiyon:
            import ast
            agac = ast.parse(kaynak.read_text(encoding='utf-8'))
            adlar = {dugum.name for dugum in ast.walk(agac)
                     if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if fonksiyon not in adlar:
                raise SystemExit(
                    'KOD-ICI KAYNAK: fonksiyon yok: %s · %s · %s'
                    % (fonksiyon, kaynak_yolu, kimlik))


def kod_ici_oztest():
    """Sahte kimligin, aile onekinin ve kaynaksiz gerekcenin reddedildigini sinar."""
    kod_ici_kaynak_dogrula()
    # Kaynak referansi zorunlu; gerekceden cikarilinca fail-closed olmali.
    yedek = dict(KOD_ICI_GEREKCE)
    try:
        anahtar = sorted(KOD_ICI_GEREKCE)[0]
        sinif, _gerekce = KOD_ICI_GEREKCE[anahtar]
        KOD_ICI_GEREKCE[anahtar] = (
            sinif, 'kapsam_selftest: kaynak referansi olmayan gerekce.')
        try:
            kod_ici_kaynak_dogrula()
        except SystemExit as exc:
            if 'kaynak yok' not in str(exc):
                raise
        else:
            raise SystemExit('KOD-ICI OZTEST: FAIL — kaynaksiz gerekce kabul edildi')
    finally:
        KOD_ICI_GEREKCE.clear()
        KOD_ICI_GEREKCE.update(yedek)
    sahte = 'x = "AI-99"\n'
    try:
        for kimlik in KOD_ICI.findall(sahte):
            kod_ici_sinifla('ATLAS_SABLONLAR/scripts/ai_disclosure.py', kimlik)
    except SystemExit as exc:
        if 'belgelenmemis kimlik' not in str(exc):
            raise
    else:
        raise SystemExit('KOD-ICI OZTEST: FAIL — sahte AI-99 kabul edildi')
    kod_ici_sinifla('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-00')

    try:
        kod_ici_sinifla('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI')
    except SystemExit as exc:
        if 'tam kimlik' not in str(exc):
            raise
    else:
        raise SystemExit('KOD-ICI OZTEST: FAIL — aile oneki lookup kabul etti')

    # Aile oneki tek basina anahtar olamaz: AI-99'u AI-00'in gerekcesine
    # dusurmek fail-closed engellenir.
    yedek = dict(KOD_ICI_GEREKCE)
    try:
        KOD_ICI_GEREKCE[('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI')] = (
            'tani-kodu', 'aile oneki; tam kimlik degil, gerekce olamaz.')
        try:
            kod_ici_kaynak_dogrula()
        except SystemExit as exc:
            if 'TAM kimlik' not in str(exc):
                raise
        else:
            raise SystemExit('KOD-ICI OZTEST: FAIL — aile oneki kabul edildi')
    finally:
        KOD_ICI_GEREKCE.clear()
        KOD_ICI_GEREKCE.update(yedek)
    # Gerekce ve test kaniti ayni kaynaktan okunur; biri guncellenip digeri
    # unutulursa burada fail-closed durur.
    kod_ici_kanit_dogrula()


def tarama_oztest():
    """Tarama sinirinin iki gercek olgusunu olcer (sentetik fikstur yok).

    (1) 100. satirdan sonraki kural bulunur: `FRZ-08` bolum basligi
        `KOD_SABLONLAR/scripts/freeze_check.py` icinde 100'den sonra duruyor.
        Eski 100 satirlik sinir onu envanterden tamamen kaciriyordu.
    (2) Dis referans kural sayilmaz: `DEC-027` `ATLAS_SABLONLAR/scripts/
        verify_doi.py` icinde bolum basligi gibi gorunur; `REFERANS` kaydi
        olmasa envantere kural olarak girerdi.
    (3) `REFERANS` yol kapsamlidir: ayni kimlik baska betikte kural sayilir.
    """
    def _bolum_satiri(yol, kimlik):
        metin = (KOK / yol).read_text(encoding='utf-8').splitlines()
        for no, satir in enumerate(metin, 1):
            m = BOLUM.match(satir)
            if m and m.group(1) == kimlik:
                return no
        return None

    yol = 'KOD_SABLONLAR/scripts/freeze_check.py'
    no = _bolum_satiri(yol, 'FRZ-08')
    if no is None:
        raise SystemExit('TARAMA OZTEST: FAIL — FRZ-08 bolum basligi bulunamadi')
    if no <= 100:
        raise SystemExit(
            'TARAMA OZTEST: FAIL — FRZ-08 %d. satirda; testin amaci 100. '
            'satirdan sonrasini olcmek (fikstur kaydi)' % no)
    baslik, bolum = _kimlikler(KOK / yol)
    if 'FRZ-08' not in (baslik | bolum):
        raise SystemExit('TARAMA OZTEST: FAIL — FRZ-08 envanterde yok')

    ref_yol = 'ATLAS_SABLONLAR/scripts/verify_doi.py'
    if _bolum_satiri(ref_yol, 'DEC-027') is None:
        raise SystemExit('TARAMA OZTEST: FAIL — DEC-027 basligi dosyada yok; '
                         'test kendi varsayimini kaybetti')
    if (ref_yol, 'DEC-027') not in REFERANS:
        raise SystemExit('TARAMA OZTEST: FAIL — REFERANS kaydi yok')
    r_baslik, r_bolum = _kimlikler(KOK / ref_yol)
    if 'DEC-027' in (r_baslik | r_bolum):
        raise SystemExit('TARAMA OZTEST: FAIL — DEC-027 kural sayildi '
                         '(REFERANS uygulanmadi)')
    if any('DEC-027' in kimlikler for kimlikler in envanter().values()):
        raise SystemExit('TARAMA OZTEST: FAIL — DEC-027 envanterde gorunuyor')

    # Ayiklama regex'in isi degil: ham tarama DEC-027'yi YAKALAR, sonra
    # REFERANS dusurur. Ikisi birlikte olculmezse "sayilmadi" sessiz kalirdi.
    ham = set()
    for satir in (KOK / ref_yol).read_text(encoding='utf-8').splitlines():
        m = KURAL.match(satir) or BOLUM.match(satir)
        if m:
            ham.add(m.group(1))
    if 'DEC-027' not in ham:
        raise SystemExit('TARAMA OZTEST: FAIL — ham tarama DEC-027 yakalamiyor; '
                         'REFERANS testi bosa dusmus')

    # Satir ortasindaki atif ("... (DEC-027) kapsaminda") hic eslesmez.
    orta = '# bkz. (DEC-027) kapsaminda degerlendirilir'
    if KURAL.match(orta) or BOLUM.match(orta):
        raise SystemExit('TARAMA OZTEST: FAIL — satir ortasi atif kural sayildi')


def olu_kimlik_oztest():
    """Olcum mekanizmasinin kendisini sentetik kaynakla sınar.

    Uc olcum: (a) docstring'deki kimlik "basılıyor" saymaz, (b) yorumdaki
    kimlik saymaz, (c) bulgu sozlugundeki kimlik basılıyor sayar. Ayrica iki
    yonlu fail-closed: gerekcesiz olu kimlik ve bayat gerekce kirmizi olur.
    """
    kaynak = (
        '"""Fikstur.\n\nKURALLAR\n  ORN-01  docstring' + 'te anlatilan kural\n"""\n'
        '# ORN-02 yalniz yorumda gecer\n'
        'def f():\n'
        '    """ORN-03 fonksiyon docstring' + 'i"""\n'
        '    bulgular = [{"kural": "ORN-04", "siddet": "P0"}]\n'
        '    return bulgular\n')
    akan = set()
    for sabit in _kod_sabitleri(kaynak):
        akan.update(KURAL_ARAMA.findall(sabit))
    if 'ORN-01' in akan or 'ORN-03' in akan:
        raise SystemExit('OLU KIMLIK OZTEST: docstring kimligi basilmiş sayildi')
    if 'ORN-02' in akan:
        raise SystemExit('OLU KIMLIK OZTEST: yorum kimligi basilmiş sayildi')
    if 'ORN-04' not in akan:
        raise SystemExit('OLU KIMLIK OZTEST: bulgu sozlugu kimligi gorulmedi')

    # Referans sinifi: bilgi etiketi kural degil, bulgu etiketi kuraldir.
    if bulgu_etiketi_mi('[DEC-027] muaf bolum sayisi: 1', 'DEC-027'):
        raise SystemExit('OLU KIMLIK OZTEST: bilgi etiketi kural sayildi')
    if not bulgu_etiketi_mi('{"kural": "DEC-027", "siddet": "P0"}', 'DEC-027'):
        raise SystemExit('OLU KIMLIK OZTEST: bulgu etiketi kural sayilmadi')

    # Iki yonlu fail-closed: gercek listeyi gecici bozarak olc.
    yedek = dict(OLU_KIMLIK)
    try:
        anahtar = sorted(OLU_KIMLIK)[0]
        OLU_KIMLIK.pop(anahtar)
        OLU_KIMLIKLER.pop(anahtar[1], None)
        try:
            olu_kimlik_dogrula()
        except SystemExit as exc:
            if 'gerekcesiz kayit' not in str(exc):
                raise
        else:
            raise SystemExit('OLU KIMLIK OZTEST: gerekcesiz olu kimlik gecTI')
    finally:
        OLU_KIMLIK.clear()
        OLU_KIMLIK.update(yedek)
        OLU_KIMLIKLER.clear()
        OLU_KIMLIKLER.update({k: (b, g) for (b, k), g in yedek.items()})

    yedek = dict(OLU_KIMLIK)
    try:
        OLU_KIMLIK[('KOD_SABLONLAR/scripts/secret_scan.py', 'SEC-99')] = (
            'uydurma kayit; olcumde boyle bir bildirim yok, bayat gerekce '
            'fail-closed yakalamali')
        try:
            olu_kimlik_dogrula()
        except SystemExit as exc:
            if 'gerekce bayat' not in str(exc):
                raise
        else:
            raise SystemExit('OLU KIMLIK OZTEST: bayat gerekce gecTI')
    finally:
        OLU_KIMLIK.clear()
        OLU_KIMLIK.update(yedek)


def kod_ici_kimlikler():
    """Baslikta bildirilmeyen, kodda string literal olarak uretilen kimlikler.

    Bunlar kural degildir; envantere eklenmez. Yine de sessizce kaybolmaz:
    her kimlik KOD_ICI_GEREKCE ile bir sinira ve gerekceye baglanir. Yeni bir
    kimlik (ayni ailede olsa bile) belgelenmeden `make kapsam` fail-closed durur.
    """
    sonuc = []
    for p in kapi_betikleri():
        baslik, bolum = _kimlikler(p)
        metin = p.read_text(encoding='utf-8')
        yol = str(p.relative_to(KOK))
        for kimlik in sorted(set(KOD_ICI.findall(metin)) - baslik - bolum):
            if kimlik.split('-')[0] in YOKSAY_PREFIX:
                continue
            sinif, gerekce = kod_ici_sinifla(yol, kimlik)
            sonuc.append((yol, kimlik, sinif, gerekce))
    return sonuc


def test_dosyalari():
    """Kod-ici kimlik kaniti tasiyan selftest ve fikstur dosyalari."""
    for d in DIZINLER + ('tools',):
        for p in sorted((KOK / d).glob('*_selftest.py')):
            # kapsam_selftest gecici AI-98 gibi kimlikleri kendi kaynaginda
            # tasir; bu bir urun testi degil, kapsam mekanizmasinin meta-testidir.
            if p.name == 'kapsam_selftest.py':
                continue
            yield p
    p = KOK / 'tools' / 'mutasyon_bataryasi.py'
    if p.is_file():
        yield p


def test_referanslari():
    """{kimlik: [test/fikstur dosyasi]} — docstring ve yorumlar haric.

    Yalniz AST string sabitleri taranir. Boylece bir kimligin testte yalniz
    yorumda gecmesi kanit sayilmaz; fikstur verisi ise ayri bir tur olarak
    gorunur ve `kod_ici_kanit_dogrula` tarafindan assertion'tan ayrilir.
    """
    sonuc = {}
    for p in test_dosyalari():
        yol = str(p.relative_to(KOK))
        try:
            sabitler = _kod_sabitleri(p.read_text(encoding='utf-8'))
        except (OSError, SyntaxError) as exc:
            raise SystemExit(
                'KOD-ICI KANIT: test dosyasi okunamadi: %s (%s)' % (yol, exc))
        for sabit in sabitler:
            for kimlik in KOD_ICI_REFERANS.findall(sabit):
                sonuc.setdefault(kimlik, set()).add(yol)
    return {k: sorted(v) for k, v in sonuc.items()}


def kod_ici_kanit_dogrula():
    """Test kaniti kaydi ile gercek test referanslarini iki yonlu denetle.

    - Her KOD_ICI_GEREKCE anahtarinin bir kanit kaydi olmali; stale kayit yok.
    - `yok` bir kimlik hicbir test dosyasinda gecmemeli.
    - `oz-test` ve `fikstur` kaynagi gercekten kimligi icermeli; oz-test
      kaynagi bir `*_selftest.py` olmali ve test adi kaynakta bulunmali.
    Bu, fixture metnini yanlislikla "test edildi" diye saymayi engeller.
    """
    eksik = sorted(set(KOD_ICI_GEREKCE) - set(KOD_ICI_TEST_KANITI))
    if eksik:
        raise SystemExit(
            'KOD-ICI KANIT: kayit yok: %s' %
            ', '.join('%s·%s' % (b.split('/')[-1], k) for b, k in eksik))
    bayat = sorted(set(KOD_ICI_TEST_KANITI) - set(KOD_ICI_GEREKCE))
    if bayat:
        raise SystemExit(
            'KOD-ICI KANIT: bayat kayit: %s' %
            ', '.join('%s·%s' % (b.split('/')[-1], k) for b, k in bayat))
    referanslar = test_referanslari()
    for (betik, kimlik), (sinif, _gerekce) in sorted(KOD_ICI_GEREKCE.items()):
        tur, test, kaynak = KOD_ICI_TEST_KANITI[(betik, kimlik)]
        if tur not in ('oz-test', 'fikstur', 'yok'):
            raise SystemExit(
                'KOD-ICI KANIT: gecersiz tur %r · %s' % (tur, kimlik))
        if tur == 'yok':
            if referanslar.get(kimlik):
                raise SystemExit(
                    'KOD-ICI KANIT: %s testte geciyor (%s); kaydi '
                    'oz-test/fikstur olarak guncelle'
                    % (kimlik, ', '.join(referanslar[kimlik])))
            continue
        if not kaynak or not test:
            raise SystemExit(
                'KOD-ICI KANIT: %s icin kaynak/test adi bos' % kimlik)
        if kaynak not in referanslar.get(kimlik, []):
            raise SystemExit(
                'KOD-ICI KANIT: %s · %s kaynagi kimligi icermiyor'
                % (kimlik, kaynak))
        if tur == 'oz-test':
            if not kaynak.endswith('_selftest.py'):
                raise SystemExit(
                    'KOD-ICI KANIT: %s oz-test kaynagi selftest degil: %s'
                    % (kimlik, kaynak))
            metin = (KOK / kaynak).read_text(encoding='utf-8')
            for ad in test.split('/'):
                if ad and ad not in metin:
                    raise SystemExit(
                        'KOD-ICI KANIT: %s test adi kaynakta yok: %s · %s'
                        % (kimlik, ad, kaynak))
        elif tur != 'fikstur':
            raise SystemExit(
                'KOD-ICI KANIT: %s icin bilinmeyen tur %r' % (kimlik, tur))


def kod_ici_kanitlari():
    """41 kimligi kanit turu, kaynagi ve uc durumdan biriyle listele."""
    kod_ici_kanit_dogrula()
    satirlar = []
    for (betik, kimlik), (sinif, _gerekce) in sorted(
            KOD_ICI_GEREKCE.items()):
        tur, test, kaynak = KOD_ICI_TEST_KANITI[(betik, kimlik)]
        if tur == 'oz-test':
            durum = 'ÖZ-TEST'
            kanit = '`%s` · %s' % (kaynak.split('/')[-1], test)
        elif tur == 'fikstur':
            durum = 'YALNIZ TANI' if sinif == 'tani-kodu' else 'TEST YOK'
            kanit = '`%s` · yalnız fikstür (%s)' % (
                kaynak.split('/')[-1], test)
        else:
            durum = 'YALNIZ TANI' if sinif == 'tani-kodu' else 'TEST YOK'
            kanit = '—'
        satirlar.append((betik, kimlik, sinif, kanit, durum))
    return satirlar


def kod_ici_kanit_tablosu(satirlar):
    out = ['| Betik | Kimlik | Sinif | Test kaniti | Durum |',
           '|---|---|---|---|---|']
    for betik, kimlik, sinif, kanit, durum in satirlar:
        out.append('| `%s` | %s | %s | %s | %s |' % (
            betik.split('/')[-1], kimlik, sinif, kanit, durum))
    return out


def kod_ici_kanit_sayilari(satirlar):
    """Durum dagilimi; fikstur ve hic referans olmayan veri ayrica sayilir."""
    sayilar = {'ÖZ-TEST': 0, 'YALNIZ TANI': 0, 'TEST YOK': 0}
    fikstur = referanssiz = 0
    for betik, kimlik, sinif, _kanit, durum in satirlar:
        sayilar[durum] += 1
        tur = KOD_ICI_TEST_KANITI[(betik, kimlik)][0]
        if tur == 'fikstur':
            fikstur += 1
        elif tur == 'yok' and sinif == 'veri-kimligi':
            referanssiz += 1
    return sayilar, fikstur, referanssiz


def kod_ici_tablosu(kimlikler):
    gruplar = {}
    for betik, kimlik, sinif, gerekce in kimlikler:
        gruplar.setdefault((betik, sinif, gerekce), []).append(kimlik)
    out = ['| Betik | Sinif | Kimlikler | Gerekce |', '|---|---|---|---|']
    for (betik, sinif, gerekce), ids in sorted(gruplar.items()):
        out.append('| `%s` | %s | %s | %s |' % (
            betik.split('/')[-1], sinif, ', '.join(ids), gerekce))
    return out


def envanter():
    """{betik_goreli: [kural, ...]} — tum bildirimler + bolum basliklari.

    Kural bildirmeyen betik de anahtarla yer alir (bos liste); boylece
    'kac betik tarandi' sayisi ile 'kac kural bildirildi' sayisi karismaz.
    """
    sonuc = {}
    for p in kapi_betikleri():
        baslik, bolum = _kimlikler(p)
        sonuc[str(p.relative_to(KOK))] = sorted(baslik | bolum)
    return sonuc


def tarama():
    """Her kapinin baslik/bolum kimlik kumeleri; sayim kaniti icin."""
    sonuc = []
    for p in kapi_betikleri():
        baslik, bolum = _kimlikler(p)
        sonuc.append((str(p.relative_to(KOK)), sorted(baslik), sorted(bolum),
                      sorted(baslik | bolum)))
    return sonuc


def kimliksiz_betikler():
    """Kural kimligi bildirmeyen, fakat kapi taramasinda kalan betikler.

    Kapsam envanteri yalniz kural kimligi tasiyan satirlari sayar. Bu fonksiyon
    envanterde karsiligi olmayan dosyalari kaybetmez: her biri asagidaki uc
    siniftan biriyle ve gerekceyle eslesmek zorundadir. Eslesme yoksa
    `make kapsam` fail-closed durur.
    """
    sonuc = []
    for p in kapi_betikleri():
        baslik, bolum = _kimlikler(p)
        if baslik or bolum:
            continue
        yol = str(p.relative_to(KOK))
        kayit = KIMLIKSIZ_SINIFLAR.get(yol)
        if kayit is None:
            raise SystemExit(
                'KIMLIKSIZ KAPSAM: siniflandirilmamis betik %s; '
                'KIMLIKSIZ_SINIFLAR icin tani/kutuphane/kapsam-disi '
                'gerekcesi yaz' % yol)
        kategori, gerekce = kayit
        sonuc.append((yol, kategori, gerekce))
    return sonuc


def kimliksiz_dogrula():
    """Kimliksiz betik siniflandirmasini iki yonlu fail-closed denetle."""
    olculen = {yol for yol, _kategori, _gerekce in kimliksiz_betikler()}
    bayat = sorted(set(KIMLIKSIZ_SINIFLAR) - olculen)
    if bayat:
        raise SystemExit(
            'KIMLIKSIZ KAPSAM: siniflandirma bayat %s; betik artik kural '
            'kimligi bildiriyor veya dosya yok' % ', '.join(bayat))
    for yol, (kategori, gerekce) in sorted(KIMLIKSIZ_SINIFLAR.items()):
        if kategori not in KIMLIKSIZ_ETIKETLER:
            raise SystemExit(
                'KIMLIKSIZ KAPSAM: gecersiz sinif %r · %s' % (kategori, yol))
        if not isinstance(gerekce, str) or len(gerekce.strip()) < 40:
            raise SystemExit(
                'KIMLIKSIZ KAPSAM: gerekce cok kisa · %s' % yol)


def kimliksiz_tablosu():
    """Kimliksiz betikleri sinif ve olculmus gerekceyle listele."""
    out = ['| Betik | Sinif | Gerekce |', '|---|---|---|']
    for yol, kategori, gerekce in kimliksiz_betikler():
        out.append('| `%s` | %s | %s |' % (
            yol, KIMLIKSIZ_ETIKETLER[kategori], gerekce))
    return out


def batarya_modu():
    yol = KOK / 'tools' / 'mutasyon_bataryasi.py'
    spec = importlib.util.spec_from_file_location('mb', str(yol))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def batarya():
    return batarya_modu().vakalar()


def sozlesme_oztest():
    """Ayrik sozlesmelerin siniflandigini ve celiskiyi reddettigini sinar."""
    mod = batarya_modu()
    taban = ('X-01', 'KOD', 'test', 'x.py', lambda k: [], lambda k: None, 'X-01')
    if mod.vaka_sozlesmesi(taban)[0] != mod.SOZLESME_HATA:
        raise SystemExit('SOZLESME OZTEST: etiketsiz vaka HATA degil')
    bulgu = taban + ('BULGU', {})
    if mod.vaka_sozlesmesi(bulgu)[0] != mod.SOZLESME_BULGU:
        raise SystemExit('SOZLESME OZTEST: BULGU etiketi beklenen-bulgu degil')
    terminal = taban[:-1] + (taban[6], {'sozlesme': mod.SOZLESME_TERMINAL})
    if mod.vaka_sozlesmesi(terminal)[0] != mod.SOZLESME_TERMINAL:
        raise SystemExit('SOZLESME OZTEST: terminal sozlesmesi taninmadi')
    try:
        mod.vaka_sozlesmesi(taban + ('BULGU', {'sozlesme': mod.SOZLESME_TERMINAL}))
    except SystemExit:
        pass
    else:
        raise SystemExit('SOZLESME OZTEST: celiskili etiket kabul edildi')
    gercek = {v[0]: v for v in mod.vakalar()}
    if mod.vaka_sozlesmesi(gercek['TST-06'])[0] != mod.SOZLESME_BULGU:
        raise SystemExit('SOZLESME OZTEST: TST-06 beklenen-bulgu degil')
    if mod.vaka_sozlesmesi(gercek['FRZ-08'])[0] != mod.SOZLESME_TERMINAL:
        raise SystemExit('SOZLESME OZTEST: FRZ-08 terminal degil')


def normalize(kimlik):
    for onek in ('KOD-', 'ATLAS-'):
        if kimlik.startswith(onek):
            return kimlik[len(onek):]
    return kimlik


KURAL_KIMLIK = re.compile(r'^[A-Z]{2,8}-\d{2,3}$')
KURAL_ARAMA = re.compile(r'[A-Z]{2,8}-\d{2,3}')


def vaka_anahtarlari(vaka):
    """Vakayi bagli oldugu kural(lar)a esle.

    Kimlik sonu ekli olabilir (REC-05-BOZUK-JSON); hedef kural `iz` alanindadir.
    `iz` bir kural kimligi ise onu, tuple ise her birini kullan; aksi halde
    kimlikten turet. Boylece alternatif vakalar da envanterde gorunur.
    """
    kimlik = vaka[0]
    iz = vaka[6] if len(vaka) > 6 else ''
    if isinstance(iz, str) and KURAL_KIMLIK.match(iz):
        return [normalize(iz)]
    if isinstance(iz, str):
        # UYARI QR-02-denge / WARN CHK-05 gibi isaretli bulgularda kural
        # kimligi metnin icindedir; yoksa yeni uyari vakasi kendi kimligine
        # baglanip kapsam tablosunda yanlis bir "kural" gibi gorunur.
        m = KURAL_ARAMA.search(iz)
        if m:
            return [normalize(m.group(0))]
    if isinstance(iz, (list, tuple)):
        hedefler = [normalize(x) for x in iz
                    if isinstance(x, str) and KURAL_KIMLIK.match(x)]
        if hedefler:
            return hedefler
    return [normalize(kimlik)]


def oz_testler():
    metin = ''
    for d in DIZINLER:
        for p in sorted((KOK / d).glob('*_selftest.py')):
            metin += p.read_text(encoding='utf-8')
    return metin


SONUC_DOSYASI = KOK / 'tools' / 'mutasyon_sonuc.json'
SONUC_SEMA = 'MUTASYON-SONUC/v1'
GECEN_DURUMLAR = ('GECTI', 'GECTI-TERMINAL', 'GECTI-BULGU')


def kaynak_imzasi():
    """Batarya + tum kapi betiklerinin icerik ozeti (mutasyon_bataryasi ile ayni)."""
    import hashlib
    parcalar = [KOK / 'tools' / 'mutasyon_bataryasi.py']
    for d in DIZINLER:
        parcalar += sorted((KOK / d).glob('*.py'))
    h = hashlib.sha256()
    for p in parcalar:
        h.update(str(p.relative_to(KOK)).encode('utf-8'))
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\n')
    return h.hexdigest()


def kosu_kaniti():
    """Son mutasyon kosusundan (taze ise {(betik, kural): gecti}) cikar.

    Taze degilse (dosya yok, sema farkli, baska HEAD, kirli agac, kisa kosu)
    kanit YOK sayilir: 'vaka var' ile 'son kosuda gecti' ayrilir.
    """
    if not SONUC_DOSYASI.is_file():
        return False, {}, 'sonuc dosyasi yok'
    try:
        veri = json.loads(SONUC_DOSYASI.read_text(encoding='utf-8'))
    except ValueError as e:
        return False, {}, 'sonuc JSON bozuk: %s' % e
    if veri.get('schema') != SONUC_SEMA:
        return False, {}, 'sema farkli: %r' % veri.get('schema')
    if veri.get('kisa'):
        return False, {}, 'kisa kosu (tam batarya degil)'
    # Tazelik HEAD'e degil KAYNAK ICERIGINE baglidir: kanit dosyasini commit
    # etmek HEAD'i degistirir, kaynagi degistirmez. Kapi betigi veya batarya
    # degistiyse kanit bayattir.
    imza = kaynak_imzasi()
    if veri.get('kaynak_sha256') != imza:
        return False, {}, 'kaynak degismis (kanit bayat)'
    kanit = {}
    onekler = {}
    for v in veri.get('vakalar') or []:
        betik = v.get('betik') or ''
        kural = v.get('kural') or ''
        onek = v.get('kural_onek') or ''
        gecti = bool(v.get('gecti')) and v.get('durum') in GECEN_DURUMLAR
        if betik and onek:
            anahtar = (betik, onek)
            onekler[anahtar] = onekler.get(anahtar, True) and gecti
        elif betik and kural:
            anahtar = (betik, kural)
            kanit[anahtar] = kanit.get(anahtar, True) and gecti
    kanit['__onek__'] = onekler
    return True, kanit, ''


def kanit_gecti(kanit, betik, kural):
    """Bu (betik, kural) icin son kosu kaniti var ve gecti mi?"""
    if not kanit:
        return False
    onekler = kanit.get('__onek__') or {}
    for (b, onek), gecti in onekler.items():
        if b == betik and kural.startswith(onek):
            return bool(gecti)
    return bool(kanit.get((betik, kural), False))


def olc():
    """[(betik, kural, vaka|None, durum, gerekce)] + ozet sayilari.

    Kapsam sayaci yalniz ATESLEYEN sozlesmeleri (HATA/TERMINAL) artirir.
    BEKLENEN_BULGU ayri sayilir; boylece P1 uyarisini rc=1 gibi gostermeyiz.
    """
    mod = batarya_modu()
    envan = envanter()
    testler = {}
    kontratlar = {}
    for vaka in mod.vakalar():
        betik = vaka[3]
        sozlesme = mod.vaka_sozlesmesi(vaka)[0]
        for anahtar in vaka_anahtarlari(vaka):
            testler.setdefault(betik, {}).setdefault(anahtar, []).append(vaka[0])
            kontratlar.setdefault(betik, {}).setdefault(anahtar, set()).add(sozlesme)
    oz = oz_testler()
    taze, kanit, _neden = kosu_kaniti()

    satirlar = []
    test = beklenen = disi = bosluk = oz_anilan = 0
    for betik, kurallar in envan.items():
        for k in kurallar:
            vakalar = testler.get(betik, {}).get(k)
            if vakalar:
                turler = kontratlar.get(betik, {}).get(k, set())
                etiket = ', '.join(vakalar)
                # 'vaka var' ile 'son kosuda gecti' ayri seylerdir: kanit
                # yoksa durum etiketi bunu acikca soyler, sessizce PASS demez.
                gecti = taze and kanit_gecti(kanit, betik, k)
                ek = '' if gecti else '·KANITSIZ'
                if turler & {mod.SOZLESME_HATA, mod.SOZLESME_TERMINAL}:
                    test += 1
                    satirlar.append((betik, k, etiket, 'TEST EDILDI' + ek,
                                     ('son kosuda gecti: %s' % etiket) if gecti
                                     else ('vaka var, son kosu kaniti YOK: %s'
                                           % etiket)))
                else:
                    beklenen += 1
                    satirlar.append((betik, k, etiket, 'BEKLENEN BULGU' + ek,
                                     ('son kosuda gecti: %s' % etiket) if gecti
                                     else ('vaka var, son kosu kaniti YOK: %s'
                                           % etiket)))
            elif (betik, k) in KAPSAM_ISTISNA:
                disi += 1
                satirlar.append((betik, k, None, 'KAPSAM DISI',
                                 'istisna: %s' % KAPSAM_ISTISNA[(betik, k)]))
            elif (betik, k) in TABAN_KAPSAM_DISI:
                disi += 1
                sinif, gerekce = KAPSAM_DISI[betik]
                satirlar.append((betik, k, None, 'KAPSAM DISI',
                                 '%s: %s' % (sinif, gerekce)))
            else:
                bosluk += 1
                if k in oz:
                    oz_anilan += 1
                    gerekce = 'BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok'
                else:
                    gerekce = 'BOSLUK — hicbir testte gecmiyor'
                satirlar.append((betik, k, None, 'BOSLUK', gerekce))
    return satirlar, envan, (test, disi, bosluk, oz_anilan, beklenen)


def ratchet(satirlar):
    """(yeni bosluklar, geri donen taban bosluklari, test kaybi, bosluk artisi).

    23 tarihsel bosluk `3a6d09a` tabanidir; `4ebb2e9` ile hepsi kapatildi.
    Guncel izinli bosluk 0'dir: ne yeni kural ne de kapanmis bir taban kurali
    test/istisna olmadan bosluga donebilir. Ayrica test edilen kural sayisi
    `TABAN_TEST_EDILEN`in altina, bosluk sayisi `TABAN_BOSLUK_SAYISI`nin
    ustune cikamaz; test artisi ve bosluk azalisi serbesttir.
    """
    if len(TABAN_BOSLUKLAR) != 23:
        raise SystemExit('TABAN_BOSLUKLAR 23 tekil kural icermeli')
    bosluklar = [(b, k, g) for b, k, _v, d, g in satirlar if d == 'BOSLUK']
    yeni = [x for x in bosluklar if x[1] not in TABAN_BOSLUKLAR]
    geri = [x for x in bosluklar if x[1] in TABAN_BOSLUKLAR]
    test = sum(1 for _b, _k, _v, d, _g in satirlar
               if d.split('\u00b7')[0] == 'TEST EDILDI')
    test_eksik = max(0, TABAN_TEST_EDILEN - test)
    bosluk_fazla = max(0, len(bosluklar) - TABAN_BOSLUK_SAYISI)
    return yeni, geri, test_eksik, bosluk_fazla


def ratchet_oztest():
    """Taban sayilarinin iki yonde de gercekten kirmizi oldugunu sınar."""
    temel = [('x.py', 'K-%03d' % i, 'v', 'TEST EDILDI', '')
             for i in range(TABAN_TEST_EDILEN)]
    yeni, geri, test_eksik, bosluk_fazla = ratchet(temel)
    if yeni or geri or test_eksik or bosluk_fazla:
        raise SystemExit('KAPSAM RATCHET OZTEST: temel taban temiz degil')
    _y, _g, test_eksik, _b = ratchet(temel[:-1])
    if test_eksik != 1:
        raise SystemExit('KAPSAM RATCHET OZTEST: test kaybi yakalanmadi')
    beklenen = temel[:-1] + [('x.py', 'K-%03d' % (TABAN_TEST_EDILEN - 1),
                              'v', 'BEKLENEN BULGU', 'hedef bulgu')]
    _y, _g, test_eksik, _b = ratchet(beklenen)
    if test_eksik != 1:
        raise SystemExit('KAPSAM RATCHET OZTEST: beklenen-bulguya donus yakalanmadi')
    fazla = temel + [('x.py', 'YENI-BOSLUK', 'v', 'BOSLUK', 'yok')]
    _y, _g, _t, bosluk_fazla = ratchet(fazla)
    if bosluk_fazla != 1:
        raise SystemExit('KAPSAM RATCHET OZTEST: bosluk artisi yakalanmadi')


def olu_kimlik_tablosu():
    """Envanter disi kimlikler: her satir olculmus gerekce tasir."""
    olculen = olu_kimlik_olc()
    out = ['| Betik | Kimlik | Olcum | Gerekce |', '|---|---|---|---|']
    for (betik, kimlik) in sorted(OLU_KIMLIK):
        durum = ('kodda basilmiyor' if (betik, kimlik) in olculen
                 else 'OLCULMEDI')
        out.append('| `%s` | %s | %s | %s |'
                   % (betik.split('/')[-1], kimlik, durum,
                      OLU_KIMLIK[(betik, kimlik)]))
    out += ['', 'Toplam envanter disi kimlik: **%d**; her biri i\u00e7in ölçüm '
            '`tools/kapsam.py --oztest` ile her ko\u015fuda yeniden alinir.'
            % len(OLU_KIMLIK)]
    if REFERANS:
        out += ['', '## Envanter disi dis referanslar', '',
                'Baska bir kurala/karara yapilan atiflar kural sayilmaz; her biri '
                'gerekceli ve iki yonlu dogrulanir.', '',
                '| Betik | Kimlik | Gerekce |', '|---|---|---|']
        for (betik, kimlik) in sorted(REFERANS):
            out.append('| `%s` | %s | %s |'
                       % (betik.split('/')[-1], kimlik, REFERANS[(betik, kimlik)]))
        out += ['', 'Toplam envanter disi dis referans: **%d**.' % len(REFERANS)]
    return out


def sinif_tablosu(satirlar):
    siniflar = {}
    for betik, k, _v, durum, gerekce in satirlar:
        if durum != 'KAPSAM DISI':
            continue
        sinif = gerekce.split(':', 1)[0]
        siniflar.setdefault(sinif, {'gerekce': gerekce.split(': ', 1)[1],
                                    'betik': set(), 'kural': 0})
        siniflar[sinif]['betik'].add(betik.split('/')[-1])
        siniflar[sinif]['kural'] += 1
    out = ['| Sinif | Gerekce (betikte olculen bagimlilik) | Betik | Kural |',
           '|---|---|---|---|']
    for sinif in sorted(siniflar):
        v = siniflar[sinif]
        out.append('| %s | %s | %s | %d |' % (
            sinif, v['gerekce'], ', '.join(sorted(v['betik'])), v['kural']))
    return out


def tarama_tablosu():
    out = ['| Betik | Baslikta | Bolum basligi | Yeni | Envanter |',
           '|---|---|---|---|---|']
    for betik, baslik, bolum, birlesik in tarama():
        yeni = len(set(bolum) - set(baslik))
        out.append('| `%s` | %d | %d | %d | %d |' % (
            betik.split('/')[-1], len(baslik), len(bolum), yeni, len(birlesik)))
    return out


def referans_tablosu():
    out = ['| Betik | Ayiklanan kimlik | Gerekce |', '|---|---|---|']
    for (yol, kimlik), gerekce in sorted(REFERANS.items()):
        out.append('| `%s` | %s | %s |' % (yol.split('/')[-1], kimlik, gerekce))
    return out


def rec_tablosu(vakalar):
    out = ['| Vaka | Hedef kural | Aciklama |', '|---|---|---|']
    for v in vakalar:
        kimlik = v[0]
        if not kimlik.startswith('REC-'):
            continue
        iz = v[6] if len(v) > 6 else ''
        hedef = iz if isinstance(iz, str) else '+'.join(iz)
        out.append('| %s | %s | %s |' % (kimlik, hedef, v[2]))
    return out


def kume_kanitlari(satirlar):
    """TSL/API/DEP kumelerinde her canli kuralin vaka kanitini denetler.

    Kural kimlikleri elle tekrarlanmaz: envanterden ve `OLU_KIMLIK`ten gelir.
    Canli bir kuralin vakasi yoksa fail-closed; olu kimlik ise vakasiz kalabilir
    ama gerekcesi `OLU_KIMLIK`te zorunludur. Donus: (ayrinti, ozet) satirlari.
    """
    durum = {(b, k): (v, d, g) for b, k, v, d, g in satirlar}
    ayrinti = []
    ozet = []
    for kume, betik in sorted(KAPSAM_KUMELERI.items()):
        canli = sorted((b, k) for b, k, _v, _d, _g in satirlar if b == betik)
        olu = sorted((b, k) for b, k in OLU_KIMLIK if b == betik)
        if not canli and not olu:
            raise SystemExit('KUME KAPSAM: betikte kural yok: %s' % betik)
        test = beklenen = 0
        for b, k in canli:
            vaka, d, gerekce = durum[(b, k)]
            temel = d.split('\u00b7')[0]
            if temel == 'TEST EDILDI':
                test += 1
            elif temel == 'BEKLENEN BULGU':
                beklenen += 1
            elif temel == 'BOSLUK' or temel == 'KAPSAM DISI':
                raise SystemExit('KUME KAPSAM: %s/%s durum=%s; once vaka veya '
                                 'olculmus istisna gerekir' % (kume, k, temel))
            if not vaka:
                raise SystemExit('KUME KAPSAM: %s/%s canli kuralin vakasi yok'
                                 % (kume, k))
            ayrinti.append((kume, k, temel, vaka, gerekce))
        for _b, k in olu:
            ayrinti.append((kume, k, 'OLU KIMLIK', '—',
                            OLU_KIMLIK[(_b, k)]))
        ozet.append((kume, len(canli), test, beklenen, len(olu)))
    return ayrinti, ozet


def _meta_opsiyon(vaka):
    """META vakasinin opsiyon sozlugunu dondur (etiketli/eski kayitlar dahil)."""
    if len(vaka) > 7 and isinstance(vaka[7], dict):
        return vaka[7]
    if len(vaka) > 8 and isinstance(vaka[8], dict):
        return vaka[8]
    return {}


def meta_arac_denetle(vakalar=None):
    """Meta araclarin her biri icin negatif test vakasi var mi? Fail-closed."""
    vakalar = vakalar if vakalar is not None else batarya()
    gorulen = {}
    for vaka in vakalar:
        ops = _meta_opsiyon(vaka)
        ad = ops.get('meta')
        if not ad:
            continue
        if ad not in META_ARACLARI:
            raise SystemExit('META KAPSAM: bilinmeyen arac %r · %s'
                             % (ad, vaka[0]))
        hedef = ops.get('hedef')
        if hedef != META_ARACLARI[ad]:
            raise SystemExit(
                'META KAPSAM: %s hedefi %r, beklenen %r'
                % (vaka[0], hedef, META_ARACLARI[ad]))
        if not (KOK / hedef).is_file():
            raise SystemExit('META KAPSAM: hedef yok: %s' % hedef)
        gorulen.setdefault(ad, []).append(vaka)
    eksik = sorted(set(META_ARACLARI) - set(gorulen))
    if eksik:
        raise SystemExit('META KAPSAM: vakasiz arac: %s' % ', '.join(eksik))
    return gorulen


def meta_arac_tablosu(vakalar):
    """tools/ altindaki meta araclarin mutasyon kapsamini listeler."""
    gruplar = meta_arac_denetle(vakalar)
    out = ['| Arac | Hedef | Vaka | Test kapisi | Sozlesme |',
           '|---|---|---|---|---|']
    for ad in sorted(gruplar):
        for vaka in gruplar[ad]:
            out.append('| %s | `%s` | %s | `%s` | %s |'
                       % (ad, META_ARACLARI[ad], vaka[0],
                          vaka[3], vaka_sozlesmesi_adi(vaka)))
    out.append('| **Toplam** | **%d araç** | **%d vaka** | | |'
               % (len(gruplar), sum(len(v) for v in gruplar.values())))
    return out


def vaka_sozlesmesi_adi(vaka):
    """Kapsam tablosu icin sozlesme adi; batarya modulunu tek yerden kullanir."""
    return batarya_modu().vaka_sozlesmesi(vaka)[0]


def kume_tablosu(ayrinti, ozet):
    """Kume ozeti ve her kuralin vakasini tek yerde gosterir."""
    out = ['| Kume | Canli kural | TEST EDILDI | BEKLENEN BULGU | OLU KIMLIK |',
           '|---|---|---|---|---|']
    for kume, canli, test, beklenen, olu in ozet:
        out.append('| %s | %d | %d | %d | %d |'
                   % (kume, canli, test, beklenen, olu))
    out.append('| **Toplam** | **%d** | **%d** | **%d** | **%d** |'
               % (sum(o[1] for o in ozet), sum(o[2] for o in ozet),
                  sum(o[3] for o in ozet), sum(o[4] for o in ozet)))
    out += ['', '| Kume | Kural | Durum | Vaka | Kanit / gerekce |',
            '|---|---|---|---|---|']
    for kume, k, durum, vaka, kanit in ayrinti:
        out.append('| %s | %s | %s | %s | %s |'
                   % (kume, k, durum, vaka or '—',
                      str(kanit).replace('|', '\\|')))
    return out


def markdown():
    satirlar, envan, (test, disi, bosluk, oz_anilan, beklenen_test) = olc()
    yeni, geri, test_eksik, bosluk_fazla = ratchet(satirlar)
    kod_ici = kod_ici_kimlikler()
    kanit_satirlari = kod_ici_kanitlari()
    (kanit_sayilari, fikstur_sayisi,
     referanssiz_sayisi) = kod_ici_kanit_sayilari(kanit_satirlari)
    kimliksiz = kimliksiz_betikler()
    mod = batarya_modu()
    vakalar = mod.vakalar()
    toplam_vaka = len(vakalar)
    sozlesmeler = [mod.vaka_sozlesmesi(v)[0] for v in vakalar]
    hata_vaka = sozlesmeler.count(mod.SOZLESME_HATA)
    terminal_vaka = sozlesmeler.count(mod.SOZLESME_TERMINAL)
    beklenen_bulgu = sozlesmeler.count(mod.SOZLESME_BULGU)
    atesleyen_vaka = hata_vaka + terminal_vaka
    out = ['# Mutasyon kapsami — tam kural envanteri', '',
           'Kaynak: `tools/kapsam.py` (uretilmis dosya; elle duzenlenmez).',
           'Envanter, ATLAS ve KOD kapi betiklerinin satir basi kural bildirimlerinden',
           've dosyanin herhangi bir yerindeki `# --- KIMLIK` bolum basliklarindan gelir;',
           '`*_selftest.py` ve `OLCUM-*` referanslari sayilmaz.', '',
           'Kod icinde string literal olarak uretilen tani/veri kimlikleri kural',
           'envanterine sayilmaz; ama `Kod icinde uretilen kimlikler` bolumunde',
           'gerekcesiyle gorunur. Listede olmayan yeni bir kimlik `make kapsam`i',
           'fail-closed durdurur.', '',
           'Her kural icin tek soru sorulur: **mutasyon bataryasinda onu ateslettiren',
           'bir HATA veya TERMINAL vakasi var mi?** Yalniz beklenen-bulgu vakasi',
           'olan kural **BEKLENEN BULGU** olarak ayri sayilir; kapsam sayisini',
           'artirmaz. Yoksa iki durumdan biri yazilir: gerekcesi olculmus',
           '**KAPSAM DISI** ya da **BOSLUK**. Bosluk gizlenmez. Tarama dosyanin',
           'TAMAMINI gezer; baska kurala/karara yapilan atiflar kural sayilmaz.', '',
           '## Sozlesme turleri', '',
           '| Sozlesme | Temiz taban | Ihlalde beklenen | Kapsam |',
           '|---|---|---|---|',
           '| HATA | sessiz, rc=0 | rc=1 + hedef iz | TEST EDILDI |',
           '| TERMINAL | terminal/FAIL izi yok | rc=2 + GATE_TAMPERED + TERMINAL FAIL | TEST EDILDI |',
           '| BEKLENEN BULGU | hedef iz yok | hedef iz var (rc=0 veya 1) | BEKLENEN BULGU; kapsam sayisina eklenmez |', '',
           'Yeni bir kural icin gecerli iki yol vardir: mutasyon bataryasinda gercek',
           'bir vaka eklemek ya da `KAPSAM_ISTISNA`ya betik+kural anahtariyla',
           'olculmus gerekce yazmak. Betik adina dayanan eski gerekce yeni kurala',
           'otomatik uygulanmaz.', '',
           '## Kanit kaynagi: gercek kosu, yalniz vaka listesi degil', '',
           'Durum etiketleri `tools/mutasyon_sonuc.json` dosyasindan turetilir.',
           'Bu dosya `make mutasyon`un son kosusunda yazilir ve her vaka icin',
           'GERCEKLESEN durumu tasir. Iki sey ayri seylerdir:', '',
           '- **vaka var** — bataryada o kurali atesleyen bir vaka tanimli',
           '- **son kosuda gecti** — o vaka son kosuda temiz taban + tek ihlal +',
           '  kirmizi/terminal sozlesmesini gercekten sagladi', '',
           'Kanit tazeligi HEAD\'e degil KAYNAK ICERIGINE baglidir: batarya ve kapi',
           'betiklerinin SHA-256 ozeti degistiyse kanit bayatlar ve etiket',
           '`KANITSIZ` olur. Boylece kanit dosyasini commit etmek kaniti',
           'gecersiz kilmaz, ama kapi kodunu degistirmek kiler.', '',
           '## Ozet', '',
           '| Olcum | Deger |', '|---|---|',
           '| Taranan betik | %d |' % len(envan),
           '| Kural bildiren betik | %d |' % sum(1 for v in envan.values() if v),
           '| Bildirilen kural (envanter) | %d |' % len(satirlar),
           '| — envanter disi: olu kimlik (bildirilir, basilMAZ) | %d |'
           % len(OLU_KIMLIK),
           '| — envanter disi: dis referans | %d |' % len(REFERANS),
           '| Kod icinde uretilen, envantere alinmayan kimlik | %d |' % len(kod_ici),
           '| — öz-test assertion | %d |' % kanit_sayilari['ÖZ-TEST'],
           '| — yalnız tanı kodu (test yok) | %d |' % kanit_sayilari['YALNIZ TANI'],
           '| — test yok (veri kimliği) | %d |' % kanit_sayilari['TEST YOK'],
           '| — bunlardan yalnız fikstürde geçen | %d |' % fikstur_sayisi,
           '| — bunlardan hiç test referansı olmayan | %d |' % referanssiz_sayisi,
           '| Kimliksiz kapi betigi | %d |' % len(kimliksiz),
           '| — tanı | %d |' % sum(1 for _y, k, _g in kimliksiz if k == 'tani'),
           '| — kütüphane | %d |' % sum(1 for _y, k, _g in kimliksiz if k == 'kutuphane'),
           '| — kapsam dışı | %d |' % sum(1 for _y, k, _g in kimliksiz if k == 'kapsam-disi'),
           '| Batarya vakasi (toplam) | %d |' % toplam_vaka,
           '| — atesleyen (HATA + TERMINAL) | %d |' % atesleyen_vaka,
           '| — HATA (rc=1) | %d |' % hata_vaka,
           '| — TERMINAL (rc=2) | %d |' % terminal_vaka,
           '| — beklenen bulgu | %d |' % beklenen_bulgu,
           '| Atesleyen vakayla test edilen kural (TEST EDILDI) | %d |' % test,
           '| — bunlardan son kosuda GECEN (kanitli) | %d |'
           % sum(1 for _b, _k, _v, d, _g in satirlar if d == 'TEST EDILDI'),
           '| — vaka VAR, son kosu kaniti YOK | %d |'
           % sum(1 for _b, _k, _v, d, _g in satirlar
                 if d == 'TEST EDILDI\u00b7KANITSIZ'),
           '| Yalniz beklenen-bulgu ile dogrulanan kural (BEKLENEN BULGU) | %d |' % beklenen_test,
           '| — bunlardan son kosuda GECEN (kanitli) | %d |'
           % sum(1 for _b, _k, _v, d, _g in satirlar if d == 'BEKLENEN BULGU'),
           '| — vaka VAR, son kosu kaniti YOK | %d |'
           % sum(1 for _b, _k, _v, d, _g in satirlar
                 if d == 'BEKLENEN BULGU\u00b7KANITSIZ'),
           '| Toplam dogrulanan kural | %d |' % (test + beklenen_test),
           '| Gerekceli kapsam disi kural | %d |' % disi,
           '| Bosluk (gerekce yok) | %d |' % bosluk,
           '| — bunlardan yalniz oz-testte anilan | %d |' % oz_anilan,
           '| — hicbir testte gecmeyen | %d |' % (bosluk - oz_anilan),
           '| Kapsam ratchet tarihsel tabani | 23 |',
           '| Kapsam ratchet guncel tabani | %d |' % len(GUNCEL_IZINLI_BOSLUKLAR),
           '| Test edilen kural tabani | %d |' % TABAN_TEST_EDILEN,
           '| Test edilen kural (guncel) | %d |' % test,
           '| Test edilen kural kaybi | %d |' % test_eksik,
           '| Bosluk tabani | %d |' % TABAN_BOSLUK_SAYISI,
           '| Bosluk artisi | %d |' % bosluk_fazla,
           '| Kapsam regresyon ratchet | %s |' % (
               'PASS' if not test_eksik and not bosluk_fazla else 'FAIL'),
           '| Yeni bosluk (test/istisna yok) | %d |' % len(yeni),
           '| Taban boslugu geri dondu | %d |' % len(geri),
           '| Kapsam ratchet | %s |' % ('PASS' if not yeni and not geri else 'FAIL'),
           '',
           '## Kapsam ratchet', '',
           'Tarihsel taban `%s` (19.11.2026) idi: 23 bosluk. `4ebb2e9`'
           % TABAN_BOSLUK_TARIHI,
           'ile bu 23 boslugun tamami gercek mutasyon vakasiyla kapatildi;',
           'guncel izinli bosluk **%d**. Yeni bir kural icin test veya'
           % len(GUNCEL_IZINLI_BOSLUKLAR),
           '`KAPSAM_ISTISNA` gerekcesi yoksa `make kapsam` ve CI kirmizi olur.',
           'Kapanmis bir taban kuralinin yeniden bosluga dusmesi de kirmizi olur.',
           'Ayrica test edilen kural sayisi **%d** tabaninin altina veya bosluk'
           % TABAN_TEST_EDILEN,
           'sayisi **%d** tabaninin ustune cikarsa regresyon ratchet kirmizi olur.'
           % TABAN_BOSLUK_SAYISI, '',
           '## Risk sirasi (50 kural)', '',
           '19.11.2026 envanterinde 51 kural vardi; `DEC-027` bir karar',
           'referansi olarak ayiklandi, kalan 50 kural risk sirasinda. Siralama',
           'saglamlik/etki sirasina gore sabittir. Kapatilan her kural',
           '%s itibariyla vaka aldi; durum sutunu guncel envanterden okunur.'
           % KAPSAM_TARIHI, '']
    out += risk_tablosu(satirlar)
    kume_ayrinti, kume_ozet = kume_kanitlari(satirlar)
    out += ['', '## Uc kume: teslim_imza, api_surface, dep_audit', '',
            'Bu kesim, adi gecen uc betikteki butun canli kurallari ve varsa '
            'olu kimlikleri tek tabloda toplar. Kural listesi envanterden '
            'turetilir; canli kuralin mutasyon vakasi yoksa `make kapsam` '
            'fail-closed durur.', '']
    out += kume_tablosu(kume_ayrinti, kume_ozet)
    out += ['', '## Meta arac mutasyonlari (tools/)', '',
            'Bu araçlar kural kimliği taşımadıkları için kural envanterine ve '
            'test edilen kural sayacına girmez. Yine de kendi negatif testleri '
            'mutasyon bataryasında koşar: temiz taban PASS, aracın tek bir '
            'güvenlik dalı bozulunca test FAIL vermek zorundadır. Bir hedefin '
            'vakası silinirse veya hedefi değişirse `make kapsam` fail-closed '
            'durur.', '']
    out += meta_arac_tablosu(vakalar)
    out += ['', 'Ayrintili P1/P0 gerekcesi risk tablosunda; kodda hic '
            'basilmayan kimliklerin gerekcesi Envanter disi tablosundadir.']
    if bosluk:
        out += ['', '## Sonraki dilim', '',
                'Asagidaki kural(lar) %s itibariyla kapatilmadi; kalan %d boslugun risk'
                % (KAPSAM_TARIHI, bosluk),
                'sirasindaki ilk %d tanesidir. Bir sonraki dilimde gercek vakayla' % len(SONRAKI_DILIM),
                'kapatilacak; sessizce sayidan dusulmedi.', '',
                '| Kural | Betik | Neden test edilemedi / neyi korur |',
                '|---|---|---|']
        _risk_durum = {k: d for _b, k, _v, d, _g in satirlar}
        _risk_betik = {k: b.split('/')[-1] for b, k, _v, _d, _g in satirlar}
        for _k in SONRAKI_DILIM:
            if _risk_durum.get(_k) != 'BOSLUK':
                raise SystemExit('SONRAKI_DILIM artik bosluk degil: %s' % _k)
            out.append('| %s | `%s` | %s |' % (_k, _risk_betik[_k], SONRAKI_NOT[_k]))
        if _risk_durum.get('TST-06') == 'BOSLUK':
            out += ['', 'Not: TST-06 yalniz P1 uretir; rc=1 sartini karsilamadigi',
                    'icin bu dilimde sayiya eklenmedi, P1 kaydi olarak ayri tutulur.']
    else:
        out += ['', '## Sonraki dilim', '',
                '%s itibariyla kapatilmayan bosluk yok (0). Dokuz eski boslugun her biri'
                % KAPSAM_TARIHI,
                'gercek bir mutasyon vakasiyla kapatildi; %d beklenen-bulgu vakasi' % beklenen_bulgu,
                'uyari modunda, digerleri kirmizi/terminal hukumle dogrulandi.', '']
    out += ['', '## Envanter disi kimlikler', '',
            'Asagidaki kimlikler satir basinda veya `# --- KIMLIK` bolum '
            'basliginda **bildirilir** ama betigin hicbir kod dalinda '
            '**basilmaz**. Bir hukum uretmedikleri icin kural degildirler: '
            'mutasyonla ateslenemezler ve envantere katilirlarsa "kapsanan '
            'kural" sayisini sisirirler. Bu yuzden sayilmazlar; gerekceleri '
            'asagida satir satir durur.', '',
            'Olcum yontemi: her kapi betigi AST ile gezilir; kimlik docstring '
            'DISINDA bir string sabiti olarak kodda akiyorsa basilabilir '
            'sayilir. Yeni bir olu kimlik gerekcesiz belirirse ya da bir dal '
            'eklenip kimlik basilirsa `make kapsam` fail-closed durur.', '']
    out += olu_kimlik_tablosu()
    if disi:
        out += ['', '## Kapsam disi siniflari', '',
                'Gerekceler tahmin degil; her satir betigin kodundaki '
                'bagimliliga dayanir (asagida betik adiyla birlikte yazili).', '']
        out += sinif_tablosu(satirlar)
    out += ['', '## Kimliksiz kapi betikleri', '',
            'Asagidaki betiklerde `KURALLAR` basligi veya `# --- KIMLIK` '
            'bolum basligi yok. Bu yuzden kural envanterine kural olarak '
            'girmezler; ancak tarama disinda da birakilmazlar. Her biri '
            '**tanı**, **kütüphane** veya **gerekceli kapsam dışı** '
            'sınıflarından birine baglanir. Kimliksiz bir betik **kural** '
            'sayılmaz; kural sayılması için envanterde bir KURAL kimliği ve '
            'mutasyon/vaka bağı gerekir. Sınıflandırılmamış yeni bir betik '
            'veya sonradan kural kimliği kazanan eski bir kayit `make kapsam` '
            'tarafından fail-closed durdurulur; bu bolum kural kapsamı sayacina '
            'eklenmez ve mevcut ratchet tabanlarini degistirmez.', '']
    out += kimliksiz_tablosu()
    out += ['', 'Toplam kimliksiz kapi betigi: **%d**.' % len(kimliksiz),
            'Sınıf dağılımı: **%d tanı · %d kütüphane · %d kapsam dışı**.'
            % (sum(1 for _y, k, _g in kimliksiz if k == 'tani'),
               sum(1 for _y, k, _g in kimliksiz if k == 'kutuphane'),
               sum(1 for _y, k, _g in kimliksiz if k == 'kapsam-disi')),
            'Bu betik düzeyi sınıflandırma, kural düzeyi `KAPSAM_DISI` sayacına '
            'girmez: burada kural kimliği yoktur; sayaç yalnız envanterdeki '
            'kuralların gerekçeli istisnalarını sayar.', '']
    out += ['', '## Kod icinde uretilen kimlikler', '',
            'Asagidaki kimlikler `KURALLAR` basliginda veya `# --- KIMLIK`',
            'bolum basliginda bildirilmez; betik kodu tarafindan string literal',
            'olarak uretilir. Her biri tek tek denetlendi: bagimsiz bir',
            '`KURALLAR` sozlesmesi degil, ilgili kapinin alt tanisi veya',
            'sozlesme bolum verisidir. Bu yuzden envantere kural olarak eklenmez;',
            'gerekce sessizce dusulmez. Her gerekcede `Kaynak: <dosya>:<satir>`',
            'referansi vardir; `kod_ici_kaynak_dogrula` dosyanin varligini, satir',
            'araligini ve kimligin o satirda gectigini her kosuda denetler.',
            'Ayni gerekce ve kaynak satirini paylasan kimlikler tek tablo satirinda',
            'gruplanir; kaynak, gruptaki her kimligin gercekten gectigi satiri',
            'gosterir. Ayni ailede yeni bir kimlik belirse bile `make kapsam`',
            'fail-closed durur:', '']
    out += kod_ici_tablosu(kod_ici)
    out += ['', '## Kod icinde uretilen kimliklerin test kaniti', '',
            'Her kimlik icin test dosyalari AST ile tarandi; docstring ve '
            'yorumlar sayilmaz. **ÖZ-TEST**, kimligi dogrudan denetleyen bir '
            'assertion veya test adi varsa yazilir. **YALNIZ TANI**, hicbir '
            'test referansi olmayan `tani-kodu` sinifidir. **TEST YOK**, '
            'dogrudan test assertion\'i olmayan veri kimligidir; yalniz fikstür '
            'verisinde gecmek test kaniti sayilmaz. Fikstürde gecen kimlikler '
            '`yalnız fikstür` olarak ayrica isaretlenir ve TEST YOK sayilir.', '']
    out += kod_ici_kanit_tablosu(kanit_satirlari)
    out += ['', 'Toplam: **%d** kod-ici kimlik · **%d** öz-test · '
            '**%d** yalnız tanı · **%d** test yok '
            '(bunlardan **%d** yalnız fikstür, **%d** hiç test referansı yok).'
            % (len(kanit_satirlari), kanit_sayilari['ÖZ-TEST'],
               kanit_sayilari['YALNIZ TANI'], kanit_sayilari['TEST YOK'],
               fikstur_sayisi, referanssiz_sayisi), '']
    if not envan.get('ATLAS_SABLONLAR/scripts/verify_doi.py'):
        out += ['', 'Not: `verify_doi.py` tarandi; bildirilen kural kimligi yok.',
                'Dosyadaki `DEC-027` bir karar referansidir, kural degil; bu',
                'yuzden `ag` sinifi envanterde kural olarak temsil edilmiyor.', '']
    out += ['', '## Tarama kaniti', '',
            '`Baslikta` satir basindaki kural bildirimleridir. `Bolum basligi`',
            'dosyanin herhangi bir yerindeki `# --- KIMLIK` basliklaridir; ilk 100',
            'satir siniri YOKTUR. `Yeni`, yalniz bolum basliginda gorunen ve ust',
            'listeye yazilmamis kimliklerdir. Envanter, iki kumenin birlesimidir.',
            'Tarama `read_text().splitlines()` uzerinden tum dosyayi gezer;',
            '`FRZ-08` 114. satirda bildirildigi halde envanterdedir. Bu, ilk 100',
            'satir sinirinin olmadiginin canli kanitidir.', '',
            '`DEC-10/12` ve `GM-17/18` gibi degisiklik etiketleri kural kimligi',
            'degildir; yalnizca kural bildirimleri ve `# --- KIMLIK` basliklari',
            'envantere alinir. `CHK-00` gibi ara kodlar ile kod icinde string',
            'literal olarak uretilen AI/HJ/OLGU/SC/RECK kimlikleri yukaridaki',
            '`Kod icinde uretilen kimlikler` tablosunda gerekcesiyle ayri tutulur;',
            'sessizce yok sayilmaz.', '']
    _tarama = tarama()
    out += tarama_tablosu()
    out += ['', 'Toplam: %d betik · %d tekil kural; her satirda Envanter = '
            'Baslikta ∪ Bolum basligi.' % (
                len(_tarama), sum(len(x[3]) for x in _tarama)), '']
    out += ['## Referans olarak ayiklanan kimlikler', '',
            'Asagidaki kimlikler bir betigin urettigi kural degil, baska bir',
            'kurala/karara yapilan atiftir; envantere sayilmaz.', '']
    out += referans_tablosu()
    out += ['', '## REC ailesi vakalari', '',
            'Her satir `make mutasyon` ile kosulur: temiz taban rc=0 ve FAIL izi',
            'yok; tek ihlal yalniz hedef kuralin FAIL etiketiyle rc=1; ihlal geri',
            'alininca kontrol kosusu rc=0. Alternatif satirlar ayni kuralin ikinci',
            'tip ihlalidir; kopya degil, farkli hata dalidir.', '']
    out += rec_tablosu(vakalar)
    out += ['', '## Tam envanter', '',
            '| Betik | Kural | Mutasyon vakasi | Durum | Gerekce |',
            '|---|---|---|---|---|']
    for betik, k, vaka, durum, gerekce in satirlar:
        out.append('| `%s` | %s | %s | %s | %s |' % (
            betik.split('/')[-1], k, vaka or '—', durum, gerekce))
    out.append('')
    return '\n'.join(out)


def json_rapor():
    """Kapı çıktısını sürümlü zarfla üret; serbest metin ayrıştırması yok."""
    oztest_gecti = True
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            kod_ici_oztest()
            sozlesme_oztest()
            ratchet_oztest()
            tarama_oztest()
            olu_kimlik_oztest()
            olu_kimlik_dogrula()
            kimliksiz_dogrula()
            _kume_ayrinti, _kume_ozet = kume_kanitlari(olc()[0])
    except SystemExit:
        oztest_gecti = False
        _kume_ozet = []
    satirlar, envan, (test, disi, bosluk, oz_anilan, beklenen) = olc()
    yeni, geri, test_eksik, bosluk_fazla = ratchet(satirlar)
    testte_gecmeyen = max(0, bosluk - oz_anilan)
    bildirilen = sum(len(v) for v in envan.values())
    toplam_dogrulanan = test + beklenen
    kanitli = sum(1 for _b, _k, _v, d, _g in satirlar
                  if d in ('TEST EDILDI', 'BEKLENEN BULGU'))
    kanitsiz = sum(1 for _b, _k, _v, d, _g in satirlar if 'KANITSIZ' in d)
    ratchet_gecti = not (yeni or geri or test_eksik or bosluk_fazla)
    kontroller = [
        kapi_cikti.kontrol('KAPSAM.oztest', 'kapsam ic oz-testleri',
                           'PASS' if oztest_gecti else 'FAIL',
                           deger='PASS' if oztest_gecti else 'FAIL',
                           ham='kapsam oz-testleri %s' % (
                               'PASS' if oztest_gecti else 'FAIL')),
        kapi_cikti.kontrol('KAPSAM.kume', 'TSL/API/DEP canli kural kapsami',
                           'PASS' if _kume_ozet else 'FAIL',
                           deger='%d canli / %d olu'
                           % (sum(o[1] for o in _kume_ozet),
                              sum(o[4] for o in _kume_ozet)),
                           ham='kume_ozet=%s' % (_kume_ozet,)),
        kapi_cikti.kontrol('KAPSAM.ratchet', 'kapsam regresyon ratchet',
                           'PASS' if ratchet_gecti else 'FAIL',
                           deger='PASS' if ratchet_gecti else 'FAIL',
                           ayrinti=('yeni=%d, taban gerilemesi=%d, test kaybi=%d, '
                                    'bosluk artisi=%d'
                                    % (len(yeni), len(geri), test_eksik,
                                       bosluk_fazla)),
                           ham='KAPSAM ratchet %s' % (
                               'PASS' if ratchet_gecti else 'FAIL')),
        kapi_cikti.kontrol('KAPSAM.test_edilen', 'atesleyen vakayla test edilen kural',
                           'PASS', deger=str(test),
                           ham='test_edilen=%d' % test),
        kapi_cikti.kontrol('KAPSAM.bildirilen', 'bildirilen kural',
                           'PASS', deger=str(bildirilen),
                           ham='bildirilen=%d' % bildirilen),
        kapi_cikti.kontrol('KAPSAM.olu_kimlik', 'envanter disi olu kimlik',
                           'PASS', deger=str(len(OLU_KIMLIK)),
                           ham='olu_kimlik=%d' % len(OLU_KIMLIK)),
        kapi_cikti.kontrol('KAPSAM.referans', 'envanter disi dis referans',
                           'PASS', deger=str(len(REFERANS)),
                           ham='referans=%d' % len(REFERANS)),
        kapi_cikti.kontrol('KAPSAM.kapsam_disi', 'gerekceli kapsam disi',
                           'PASS', deger=str(disi),
                           ham='kapsam_disi=%d' % disi),
        kapi_cikti.kontrol('KAPSAM.bosluk', 'gerekce yok',
                           'PASS', deger=str(bosluk),
                           ham='bosluk=%d' % bosluk),
        kapi_cikti.kontrol('KAPSAM.oz_anilan', 'yalniz oz-testte anilan',
                           'PASS', deger=str(oz_anilan),
                           ham='oz_anilan=%d' % oz_anilan),
        kapi_cikti.kontrol('KAPSAM.testte_gecmeyen', 'hicbir testte gecmeyen',
                           'PASS', deger=str(testte_gecmeyen),
                           ham='testte_gecmeyen=%d' % testte_gecmeyen),
        kapi_cikti.kontrol('KAPSAM.toplam_dogrulanan', 'toplam dogrulanan kural',
                           'PASS', deger=str(toplam_dogrulanan),
                           ham='toplam_dogrulanan=%d' % toplam_dogrulanan),
        kapi_cikti.kontrol('KAPSAM.kanitli', 'son kosuda gecen kural',
                           'PASS', deger=str(kanitli),
                           ham='kanitli=%d' % kanitli),
        kapi_cikti.kontrol('KAPSAM.kanitsiz', 'vaka var, son kosu kaniti yok',
                           'PASS', deger=str(kanitsiz),
                           ham='kanitsiz=%d' % kanitsiz),
    ]
    gecti = oztest_gecti and ratchet_gecti
    return kapi_cikti.uret('kapsam', kontroller,
                           rc=0 if gecti else 1,
                           hata=None if gecti else (
                               'ratchet ihlali' if not ratchet_gecti
                               else 'kapsam oz-testi FAIL'))


def main(argv):
    if '--json' in argv:
        try:
            rapor = json_rapor()
        except SystemExit as e:
            rapor = kapi_cikti.uret(
                'kapsam', [], rc=int(e.code or 1), hukum='FAIL',
                hata='kapsam hesaplanamadi')
        sys.stdout.write(kapi_cikti.yaz(rapor))
        return 0 if rapor['hukum'] == 'PASS' else 1
    if '--oztest' in argv:
        kod_ici_oztest()
        sozlesme_oztest()
        ratchet_oztest()
        tarama_oztest()
        olu_kimlik_oztest()
        olu_kimlik_dogrula()
        kimliksiz_dogrula()
        kume_ayrinti, kume_ozet = kume_kanitlari(olc()[0])
        print('KUME KAPSAM: PASS — %d kume · %d canli kural · %d olu kimlik'
              % (len(KAPSAM_KUMELERI), sum(o[1] for o in kume_ozet),
                 sum(o[4] for o in kume_ozet)))
        meta = meta_arac_denetle(batarya())
        print('META KAPSAM: PASS — %d arac · %d vaka'
              % (len(meta), sum(len(v) for v in meta.values())))
        print('KAPSAM OZTEST: PASS — kimlik ve kaynak fail-closed · sozlesme ayrik · '
              'ratchet iki yonlu · FRZ-08 >100 · DEC-027 referans · '
              'olu kimlik %d gerekceli · kimliksiz %d siniflandirilmis · '
              'meta %d arac'
              % (len(OLU_KIMLIK), len(KIMLIKSIZ_SINIFLAR), len(meta)))
        return 0
    if '--kontrol' in argv or '--yaz' in argv:
        kod_ici_oztest()
        print('KOD-ICI OZTEST: PASS — kaynak, bilinmeyen kimlik ve aile oneki fail-closed')
        sozlesme_oztest()
        print('SOZLESME OZTEST: PASS — HATA/TERMINAL/BEKLENEN_BULGU ayrik')
        ratchet_oztest()
        print('KAPSAM RATCHET OZTEST: PASS — test=%d, bosluk=%d'
              % (TABAN_TEST_EDILEN, TABAN_BOSLUK_SAYISI))
        tarama_oztest()
        print('TARAMA OZTEST: PASS — >100 kural bulunur · dis referans sayilmaz')
        olu_kimlik_oztest()
        olu_kimlik_dogrula()
        kimliksiz_dogrula()
        kume_kanitlari(olc()[0])
        print('KUME KAPSAM: PASS — TSL/API/DEP canli kurallarin tamami vakali')
        meta = meta_arac_denetle(batarya())
        print('META KAPSAM: PASS — %d arac · %d vaka'
              % (len(meta), sum(len(v) for v in meta.values())))
        print('OLU KIMLIK: PASS — %d envanter disi kimlik · hepsi olculen ve '
              'gerekceli · %d dis referans' % (len(OLU_KIMLIK), len(REFERANS)))
        print('KIMLIKSIZ KAPSAM: PASS — %d betik uc siniftan biriyle '
              'gerekceli' % len(KIMLIKSIZ_SINIFLAR))
    satirlar, _envan, (test, _disi, bosluk, _ozanilan, _beklenen_test) = olc()
    yeni, geri, test_eksik, bosluk_fazla = ratchet(satirlar)
    if '--kontrol' in argv or '--yaz' in argv:
        if yeni or geri or test_eksik or bosluk_fazla:
            print('KAPSAM: FAIL — kapsam regresyon ratchet ihlali '
                  '(yeni=%d, taban gerilemesi=%d, test kaybi=%d, '
                  'bosluk artisi=%d)'
                  % (len(yeni), len(geri), test_eksik, bosluk_fazla))
            for betik, kural, gerekce in yeni:
                print('  YENI %s · %s — %s' % (kural, betik, gerekce))
            for betik, kural, gerekce in geri:
                print('  TABAN GERI DONDU %s · %s — %s'
                      % (kural, betik, gerekce))
            print('  Cozum: mutasyon vakasi ekle veya KAPSAM_ISTISNAya '
                  'betik+kural gerekcesi yaz.')
            return 1

    metin = markdown()
    if '--kontrol' in argv:
        if not HEDEF.is_file():
            print('KAPSAM: %s yok — `make kapsam-yaz` kosun' % HEDEF.name)
            return 1
        if HEDEF.read_text(encoding='utf-8') != metin:
            print('KAPSAM: docs/MUTASYON_KAPSAM.md guncel degil — `make kapsam-yaz`')
            return 1
        print('KAPSAM: guncel (%d satir) · ratchet PASS '
              '(test=%d/%d, bosluk=%d/%d, tarihsel taban=%d, guncel izinli=%d)'
              % (len(metin.splitlines()), test, TABAN_TEST_EDILEN,
                 bosluk, TABAN_BOSLUK_SAYISI, len(TABAN_BOSLUKLAR),
                 len(GUNCEL_IZINLI_BOSLUKLAR)))
        return 0
    if '--yaz' in argv:
        HEDEF.parent.mkdir(parents=True, exist_ok=True)
        HEDEF.write_text(metin, encoding='utf-8')
        print('KAPSAM: yazildi · %s · ratchet PASS '
              '(test=%d/%d, bosluk=%d/%d)'
              % (HEDEF.relative_to(KOK), test, TABAN_TEST_EDILEN,
                 bosluk, TABAN_BOSLUK_SAYISI))
        return 0
    print(metin)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
