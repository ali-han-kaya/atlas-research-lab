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
import importlib.util
import re
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
KOD_ICI = re.compile(r'''["']([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})["']''')
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
KAPSAM_DISI = {
    # OLCULDU: bu dort kimlik yalniz baslikta/riski kaydinda bildirilir; betikte
    # bu kimligi basan bir dal yoktur. Bu yuzden mutasyonla ateslenemezler.
    'ATLAS_SABLONLAR/scripts/oztest_attest.py':
        ('olu-kimlik', 'OZT-04 kaldirilmis sayac kuralidir; kodda bu kimligi '
                       'basan dal yok, kimlik sayisi dususu OZT-02 ile yakalanir'),
    'KOD_SABLONLAR/scripts/api_surface.py':
        ('olu-kimlik', 'API-03 baslikta bildirilir ama api_surface yalniz kayip '
                       'imza (API-02) ve regex adayi (API-04) dallarini uygular; '
                       'imza degisimi karsilastirmasi kodda yok'),
    'KOD_SABLONLAR/scripts/dep_audit.py':
        ('olu-kimlik', 'DEP-02 baslikta bildirilir ama dep_audit kodunda kilit '
                       'paketlerini manifestle karsilastiran dal yok; yalniz '
                       'DEP-01/03/04/05/06 dallari uygulanir'),
    # OLCULDU (19.11.2026): SEC-04 baslikta bildirilir ama secret_scan'in
    # hicbir dalinda bu kimlikle bulgu BASILMAZ; atlanan dosyalar yalniz sayilir.
    # Kural kimligi olu oldugu icin mutasyonla ateslenemez; gercek bulgu uretmez.
    'KOD_SABLONLAR/scripts/secret_scan.py':
        ('olu-kimlik', 'SEC-04 yalniz baslikta bildirilir; hicbir kod dali bu '
                       'kimligi basmiyor (atlanan dosyalar yalniz sayilir)'),
}

# Bu betiklerdeki mevcut kapsam-disi kurallar tabandir. Ayni betige YENI bir
# kural eklenirse script gerekcesi otomatik olarak ona da uygulanmaz; yeni
# kural ya mutasyon vakasi ya asagidaki KAPSAM_ISTISNA kaydi ister.
TABAN_KAPSAM_DISI = frozenset({
    ('ATLAS_SABLONLAR/scripts/oztest_attest.py', 'OZT-04'),
    ('KOD_SABLONLAR/scripts/api_surface.py', 'API-03'),
    ('KOD_SABLONLAR/scripts/dep_audit.py', 'DEP-02'),
    ('KOD_SABLONLAR/scripts/secret_scan.py', 'SEC-04'),
})

# Yeni bir kural gercekten test edilemiyorsa gerekcesi buraya ACIKCA yazilir:
#   ('KOD_SABLONLAR/scripts/ornek.py', 'ORN-07'): 'olculmus gerekce',
# Anahtar betik+yeni kuraldir; betik adi tek basina yeni kurala gerekce vermez.
KAPSAM_ISTISNA = {}


# Baska kurala/karara yapilan atiflar envantere girmez. Her satir
# (betik, kimlik) -> olculmus gerekce. Ornek: verify_doi.py icindeki DEC-027
# bir karar kimligidir; verify_doi bu kurali uygulamaz, yalniz
# bolum-farkindaligi politikasina atif yapar.
REFERANS = {
    ('ATLAS_SABLONLAR/scripts/verify_doi.py', 'DEC-027'):
        'DEC karar kimligi; verify_doi bu kurali uygulamaz, DEC-027 '
        'bolum-farkindaligi politikasina atif yapar',
}

# Baslikta bildirilmeyen ama betik kodunda string literal olarak uretilen
# kimlikler. Anahtar (betik, TAM kimlik); yeni bir kimlik ayni ailede bile
# otomatik kabul edilmez. Bunlar bagimsiz kapi kurali degil, tani/veri
# kimligidir; bu yuzden 121'lik kural envanterine ve mutasyon ratchet'ine
# sayilmazlar. Her kaydin gerekcesi burada, tek makine-okunur kaynaktadir.
KOD_ICI_GEREKCE = {
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-00'):
        ('tani-kodu', 'Manifest veya sema yok/bozuk; AI-1 onkosul tanisi, '
                      'bagimsiz KURALLAR kurali degil.'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-01'):
        ('tani-kodu', 'Manifest kok/schema/scope/entries sozlesmesi; '
                      'AI-1 selftestinin alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-02'):
        ('tani-kodu', 'Entry alan/usage/evidence dogrulamasi; AI-1 '
                      'selftestinin alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-03'):
        ('tani-kodu', 'Beyan yazma I/O hatasi; hukum uretmeyen operasyonel '
                      'tani.'),
    ('ATLAS_SABLONLAR/scripts/ai_disclosure.py', 'AI-04'):
        ('tani-kodu', '--check cikti uyusmazligi; AI-1 selftestinde kilitli '
                      'cikti butunlugu alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-00'):
        ('tani-kodu', 'Panel semasi okunamadi/kimlik uyusmadi; HJ-1 '
                      'onkosul tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-01'):
        ('tani-kodu', 'JSON/kapali sema/alan sozlesmesi; HJ-1 selftestinin '
                      'alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-02'):
        ('tani-kodu', 'Run/input uyusmazligi; HJ-1 selftestinin alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-03'):
        ('tani-kodu', 'Hukum kapsami/yinelenen kimlik/severity; HJ-1 '
                      'selftestinin alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-04'):
        ('tani-kodu', 'Verdict/evidence butunlugu; HJ-1 selftestinin alt '
                      'tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-05'):
        ('tani-kodu', 'Rol/session kimligi; HJ-1 selftestinin alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-06'):
        ('tani-kodu', 'Model ailesi/session cesitliligi; HJ-1 selftestinin '
                      'alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-07'):
        ('tani-kodu', 'Attempt/maliyet siniri; HJ-1 selftestinin alt tanisi.'),
    ('ATLAS_SABLONLAR/scripts/review_panel.py', 'HJ-08'):
        ('tani-kodu', 'Panel ciktisi yazma I/O hatasi; operasyonel tani.'),
    ('ATLAS_SABLONLAR/scripts/olgu_lint.py', 'OLGU-01'):
        ('tani-kodu', 'OLGULAR kanonu yok; olgu_lint onkosulu, OLGU-04..06 '
                      'kurallarindan ayri.'),
    ('ATLAS_SABLONLAR/scripts/olgu_lint.py', 'OLGU-02'):
        ('tani-kodu', 'OLGULAR JSON/sema girdisi gecersiz; onkosul tanisi.'),
    ('ATLAS_SABLONLAR/scripts/olgu_lint.py', 'OLGU-03'):
        ('tani-kodu', 'Ic deger uyusmazligi; OLGU-04..06 kapsamindaki tarihce '
                      'denetiminin alt tanisi.'),
    ('KOD_SABLONLAR/scripts/chg_reconcile.py', 'RECK-00'):
        ('tani-kodu', 'Ortak girdi/JSON/sema hatasi; RECK-08 sema kurali, '
                      'RECK-01..09 ayri kurallardir.'),
}
# SC kimlikleri kapsam sozlesmesinin zorunlu BOLUM numaralaridir; kapi
# kurali degildir. Tam liste: yeni bir SC kimligi kendiliginden gecmesin.
for _sc in ('SC-%03d' % i for i in list(range(1, 23)) + [30]):
    KOD_ICI_GEREKCE[('ATLAS_SABLONLAR/scripts/scope_profile_check.py', _sc)] = (
        'veri-kimligi',
        'Kapsam sozlesmesindeki zorunlu bolum kimligi; SP-01..07 kuraldir.',
    )
del _sc

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
    'BILGI': 'Bilgi seviyesi / olu kimlik — P1',
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
    'DEP-02': 'Baslikta bildirilir; dep_audit kodunda kilit paketlerini manifestle karsilastiran dal yok, bu yuzden kimlik olu. Uygulanirsa kilit bayatligi P0 olur.',
    'DEP-06': 'Profilde bagimlilik_manifesti bos birakilirsa bagimlilik yuzeyi hic denetlenmez; kapi CALISTIRILMADI/P1 verir.',
    'DEP-03': 'Surum sabitlenmezse (*, latest, bos ya da kilitsiz ^/~) ayni manifest farkli paket surumleri kurabilir; P1.',
    'DEP-04': 'Kilit dosyasi diffte degisirken manifest guncellenmezse beyan edilen bagimlilik ile kilit ayrisir; P1.',
    'TSL-01': 'Teslim manifesti yok veya bozuksa imza dogrulanamaz; kapi fail-closed P0 verir.',
    'TSL-02': 'Manifestte listelenen dosya diskte yoksa teslim kumesi eksiktir; imza eksik artefakti kurtarmaz, P0.',
    'TSL-03': 'Teslim dosyasinin sha256 degeri manifestten farkliysa artefakt yolda degistirilmistir; P0 tahrifat.',
    'TSL-04': 'Teslim imzasi gecersizse manifest baska anahtarla imzalanmis veya sonradan degistirilmis olabilir; P0.',
    'TSL-05': 'Teslim imzasi yoksa butunluk yalniz dusuk guvenle kabul edilir; P1 uyari kapiyi kapatmaz.',
    'TSL-06': 'Zorunlu teslim artefakti manifestte hic yoksa imza eksik kumeyi dogrular; kapsam boslugu P0.',
    'API-01': 'KFAZ0 API envanteri yoksa disa acik yuzey karsilastirilamaz; kapi CALISTIRILMADI/P1 verir.',
    'API-02': 'KFAZ0 envanterindeki disa acik imza kaybolursa mevcut cagiranlar sessizce kirilir; P0.',
    'API-03': 'Baslikta bildirilir; api_surface yalniz kayip imza ve regex adayi dallarini uygular, imza degisimi karsilastirmasi kodda yok; P0 vaadi olu kimliktir.',
    'API-04': 'Regex taramasi bir adayi kacirirsa disa acik yuzey eksik sayilir; DUSUK_GUVEN/P1.',
    'API-05': 'API kademelerinden hicbiri kosmazsa disa acik yuzey denetimi tamamen korlesir; CALISTIRILMADI/P1.',
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
    eksik = [r for r, _g in RISK_SIRASI if r not in durum]
    if eksik:
        raise SystemExit('RISK_SIRASI envanterde yok: %s' % ', '.join(eksik))
    out = ['| # | Kural | Betik | Grup | Durum | Gerekce |', '|---|---|---|---|---|---|']
    for i, (kural, grup) in enumerate(RISK_SIRASI, 1):
        _durum = durum[kural]
        if _durum == 'TEST EDILDI' and kural in RISK_EKLENEN:
            _durum = 'TEST EDILDI (%s)' % KAPSAM_TARIHI
        elif _durum == 'BEKLENEN BULGU' and kural in RISK_EKLENEN:
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


def _kimlikler(p):
    """(satir basi bildirimleri, bolum basligi kimlikleri) — TUM dosya.

    Eski surum yalniz ilk 100 satiri okuyordu; FRZ-08 114. satirdaki bolum
    basliginda kaldigi icin envanterde hic gorunmuyordu. Artik sinir yok.
    Baska kurala/karara yapilan atiflar `REFERANS` ile ayiklanir; ornek DEC-027.
    """
    baslik, bolum = set(), set()
    for satir in p.read_text(encoding='utf-8').splitlines():
        m = KURAL.match(satir)
        if m and m.group(1).split('-')[0] not in YOKSAY_PREFIX:
            baslik.add(m.group(1))
        m = BOLUM.match(satir)
        if m and m.group(1).split('-')[0] not in YOKSAY_PREFIX:
            bolum.add(m.group(1))
    yol = str(p.relative_to(KOK))
    for (ref_yol, ref_kimlik) in REFERANS:
        if ref_yol == yol:
            baslik.discard(ref_kimlik)
            bolum.discard(ref_kimlik)
    return baslik, bolum


def kod_ici_sinifla(yol, kimlik):
    """Tek kod-ici kimligi (sinif, gerekce) olarak cozer; yoksa fail-closed.

    Anahtar TAM (betik, kimlik) ciftidir. Boylece ayni oneke sahip yeni bir
    kimlik (or. AI-99) aile gerekcesiyle sessizce gecemez.
    """
    anahtar = (yol, kimlik)
    if anahtar not in KOD_ICI_GEREKCE:
        raise SystemExit(
            'KOD-ICI KAPSAM: belgelenmemis kimlik %s · %s; '
            'KOD_ICI_GEREKCEye (betik, tam kimlik) gerekcesi yaz'
            % (kimlik, yol))
    return KOD_ICI_GEREKCE[anahtar]


def kod_ici_kaynak_dogrula():
    """Her dislama kaydinin sinif ve bos olmayan gerekce tasidigini sinar."""
    for (yol, kimlik), (sinif, gerekce) in KOD_ICI_GEREKCE.items():
        if sinif not in ('tani-kodu', 'veri-kimligi'):
            raise SystemExit(
                'KOD-ICI KAPSAM: gecersiz sinif %r · %s · %s' % (sinif, kimlik, yol))
        if not isinstance(gerekce, str) or len(gerekce.strip()) < 12:
            raise SystemExit(
                'KOD-ICI KAPSAM: gerekcesiz kimlik %s · %s; '
                'KOD_ICI_GEREKCEye gerekce yaz' % (kimlik, yol))


def kod_ici_oztest():
    """Sahte bir kod-ici kimligin tarama + siniflamada reddedildigini sinar."""
    kod_ici_kaynak_dogrula()
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

    satirlar = []
    test = beklenen = disi = bosluk = oz_anilan = 0
    for betik, kurallar in envan.items():
        for k in kurallar:
            vakalar = testler.get(betik, {}).get(k)
            if vakalar:
                turler = kontratlar.get(betik, {}).get(k, set())
                etiket = ', '.join(vakalar)
                if turler & {mod.SOZLESME_HATA, mod.SOZLESME_TERMINAL}:
                    test += 1
                    satirlar.append((betik, k, etiket, 'TEST EDILDI',
                                     'atesleyen mutasyon vakasi: %s' % etiket))
                else:
                    beklenen += 1
                    satirlar.append((betik, k, etiket, 'BEKLENEN BULGU',
                                     'yalniz beklenen-bulgu sozlesmesi: %s' % etiket))
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
    test = sum(1 for _b, _k, _v, d, _g in satirlar if d == 'TEST EDILDI')
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


def markdown():
    satirlar, envan, (test, disi, bosluk, oz_anilan, beklenen_test) = olc()
    yeni, geri, test_eksik, bosluk_fazla = ratchet(satirlar)
    kod_ici = kod_ici_kimlikler()
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
           '## Ozet', '',
           '| Olcum | Deger |', '|---|---|',
           '| Taranan betik | %d |' % len(envan),
           '| Kural bildiren betik | %d |' % sum(1 for v in envan.values() if v),
           '| Bildirilen kural | %d |' % len(satirlar),
           '| Kod icinde uretilen, envantere alinmayan kimlik | %d |' % len(kod_ici),
           '| Batarya vakasi (toplam) | %d |' % toplam_vaka,
           '| — atesleyen (HATA + TERMINAL) | %d |' % atesleyen_vaka,
           '| — HATA (rc=1) | %d |' % hata_vaka,
           '| — TERMINAL (rc=2) | %d |' % terminal_vaka,
           '| — beklenen bulgu | %d |' % beklenen_bulgu,
           '| Atesleyen vakayla test edilen kural (TEST EDILDI) | %d |' % test,
           '| Yalniz beklenen-bulgu ile dogrulanan kural (BEKLENEN BULGU) | %d |' % beklenen_test,
           '| Toplam dogrulanan kural | %d |' % (test + beklenen_test),
           '| Gerekceli kapsam disi | %d |' % disi,
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
    out += ['', '## Kapsam disi siniflari', '',
            'Gerekceler tahmin degil; her satir betigin kodundaki bagimliliga dayanir',
            '(asagida betik adiyla birlikte yazili).', '']
    out += sinif_tablosu(satirlar)
    out += ['', '## Kod icinde uretilen kimlikler', '',
            'Asagidaki kimlikler `KURALLAR` basliginda veya `# --- KIMLIK`',
            'bolum basliginda bildirilmez; betik kodu tarafindan string literal',
            'olarak uretilir. Her biri tek tek denetlendi: bagimsiz bir',
            '`KURALLAR` sozlesmesi degil, ilgili kapinin alt tanisi veya',
            'sozlesme bolum verisidir. Bu yuzden envantere kural olarak eklenmez;',
            'gerekce sessizce dusulmez. Ayni ailede yeni bir kimlik belirse bile',
            '`make kapsam` fail-closed durur:', '']
    out += kod_ici_tablosu(kod_ici)
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
    satirlar, envan, (test, disi, bosluk, oz_anilan, beklenen) = olc()
    yeni, geri, test_eksik, bosluk_fazla = ratchet(satirlar)
    testte_gecmeyen = max(0, bosluk - oz_anilan)
    bildirilen = sum(len(v) for v in envan.values())
    toplam_dogrulanan = test + beklenen
    ratchet_gecti = not (yeni or geri or test_eksik or bosluk_fazla)
    kontroller = [
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
    ]
    return kapi_cikti.uret('kapsam', kontroller,
                           rc=0 if ratchet_gecti else 1,
                           hata=None if ratchet_gecti else 'ratchet ihlali')


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
    if '--kontrol' in argv or '--yaz' in argv:
        kod_ici_oztest()
        print('KOD-ICI OZTEST: PASS — bilinmeyen kimlik fail-closed')
        sozlesme_oztest()
        print('SOZLESME OZTEST: PASS — HATA/TERMINAL/BEKLENEN_BULGU ayrik')
        ratchet_oztest()
        print('KAPSAM RATCHET OZTEST: PASS — test=%d, bosluk=%d'
              % (TABAN_TEST_EDILEN, TABAN_BOSLUK_SAYISI))
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
