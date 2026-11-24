# Mutasyon kapsami — tam kural envanteri

Kaynak: `tools/kapsam.py` (uretilmis dosya; elle duzenlenmez).
Envanter, ATLAS ve KOD kapi betiklerinin satir basi kural bildirimlerinden
ve dosyanin herhangi bir yerindeki `# --- KIMLIK` bolum basliklarindan gelir;
`*_selftest.py` ve `OLCUM-*` referanslari sayilmaz.

Kod icinde string literal olarak uretilen tani/veri kimlikleri kural
envanterine sayilmaz; ama `Kod icinde uretilen kimlikler` bolumunde
gerekcesiyle gorunur. Listede olmayan yeni bir kimlik `make kapsam`i
fail-closed durdurur.

Her kural icin tek soru sorulur: **mutasyon bataryasinda onu ateslettiren
bir HATA veya TERMINAL vakasi var mi?** Yalniz beklenen-bulgu vakasi
olan kural **BEKLENEN BULGU** olarak ayri sayilir; kapsam sayisini
artirmaz. Yoksa iki durumdan biri yazilir: gerekcesi olculmus
**KAPSAM DISI** ya da **BOSLUK**. Bosluk gizlenmez. Tarama dosyanin
TAMAMINI gezer; baska kurala/karara yapilan atiflar kural sayilmaz.

## Sozlesme turleri

| Sozlesme | Temiz taban | Ihlalde beklenen | Kapsam |
|---|---|---|---|
| HATA | sessiz, rc=0 | rc=1 + hedef iz | TEST EDILDI |
| TERMINAL | terminal/FAIL izi yok | rc=2 + GATE_TAMPERED + TERMINAL FAIL | TEST EDILDI |
| BEKLENEN BULGU | hedef iz yok | hedef iz var (rc=0 veya 1) | BEKLENEN BULGU; kapsam sayisina eklenmez |

Yeni bir kural icin gecerli iki yol vardir: mutasyon bataryasinda gercek
bir vaka eklemek ya da `KAPSAM_ISTISNA`ya betik+kural anahtariyla
olculmus gerekce yazmak. Betik adina dayanan eski gerekce yeni kurala
otomatik uygulanmaz.

## Ozet

| Olcum | Deger |
|---|---|
| Taranan betik | 31 |
| Kural bildiren betik | 20 |
| Bildirilen kural (envanter) | 117 |
| — envanter disi: olu kimlik (bildirilir, basilMAZ) | 4 |
| — envanter disi: dis referans | 1 |
| Kod icinde uretilen, envantere alinmayan kimlik | 41 |
| Batarya vakasi (toplam) | 141 |
| — atesleyen (HATA + TERMINAL) | 114 |
| — HATA (rc=1) | 105 |
| — TERMINAL (rc=2) | 9 |
| — beklenen bulgu | 27 |
| Atesleyen vakayla test edilen kural (TEST EDILDI) | 93 |
| Yalniz beklenen-bulgu ile dogrulanan kural (BEKLENEN BULGU) | 24 |
| Toplam dogrulanan kural | 117 |
| Gerekceli kapsam disi | 0 |
| Bosluk (gerekce yok) | 0 |
| — bunlardan yalniz oz-testte anilan | 0 |
| — hicbir testte gecmeyen | 0 |
| Kapsam ratchet tarihsel tabani | 23 |
| Kapsam ratchet guncel tabani | 0 |
| Test edilen kural tabani | 93 |
| Test edilen kural (guncel) | 93 |
| Test edilen kural kaybi | 0 |
| Bosluk tabani | 0 |
| Bosluk artisi | 0 |
| Kapsam regresyon ratchet | PASS |
| Yeni bosluk (test/istisna yok) | 0 |
| Taban boslugu geri dondu | 0 |
| Kapsam ratchet | PASS |

## Kapsam ratchet

Tarihsel taban `3a6d09a` (19.11.2026) idi: 23 bosluk. `4ebb2e9`
ile bu 23 boslugun tamami gercek mutasyon vakasiyla kapatildi;
guncel izinli bosluk **0**. Yeni bir kural icin test veya
`KAPSAM_ISTISNA` gerekcesi yoksa `make kapsam` ve CI kirmizi olur.
Kapanmis bir taban kuralinin yeniden bosluga dusmesi de kirmizi olur.
Ayrica test edilen kural sayisi **93** tabaninin altina veya bosluk
sayisi **0** tabaninin ustune cikarsa regresyon ratchet kirmizi olur.

## Risk sirasi (50 kural)

19.11.2026 envanterinde 51 kural vardi; `DEC-027` bir karar
referansi olarak ayiklandi, kalan 50 kural risk sirasinda. Siralama
saglamlik/etki sirasina gore sabittir. Kapatilan her kural
24.11.2026 itibariyla vaka aldi; durum sutunu guncel envanterden okunur.

| # | Kural | Betik | Grup | Durum | Gerekce |
|---|---|---|---|---|---|
| 1 | TST-08 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Ham test raporu yok/okunamiyor — kanitsiz PASS P0; kapinin kanit temeli. |
| 2 | RECK-06 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | Dondurulmus bolge diff'te — dogrudan tamper sinyali, P0. |
| 3 | DEP-05 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI (24.11.2026) | Izinli lisans listesi disinda bagimlilik — tedarik/uyum P0. |
| 4 | FRZ-08 | `freeze_check.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | Temiz agac iddiasi imzayla baglanmali; imzasiz, gecersiz imzali veya imzalandiktan sonra icerigi degistirilmis taban terminal tamper ya da dusuk guven sayilir. |
| 5 | RECK-01 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | KFAZ0 sozlesmesindeki her REQ plan/eslesmede karsilik bulmali; aksi halde kapsamsiz sozlesme sessizce yesil kalir. |
| 6 | RECK-02 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | "UYGULANMIS" denilen her CHG'nin dosyasi git diff'te olmali; beyan ile gercek degisiklik carpraz denetlenir. |
| 7 | RECK-08 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | Makine bloklarinin alan bicimi semaya uymali; sessizce dusen girdi RECK-01/07'yi devre disi birakir. |
| 8 | RECK-09 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | Plan yokken urun kodu degismemeli; KFAZ0 oncesi degisiklik kapsamsiz ve denetimsiz kalir. |
| 9 | RECK-04 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | 2B kapisinin "KANITLI" dedigi her CHG diff'te olmali; ikinci gozun iddiasi manifest ve diff ile dogrulanir. |
| 10 | RECK-05 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | Hayalet CHG yok: olmayan REQ veya plansiz dosyaya baglanan degisiklik P0; manifest-diff bagini korur. |
| 11 | RECK-07 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (24.11.2026) | Davranissal her REQ tabanda olmayan YENI bir test adina eslenmeli; eski testi gostermek bedava yesildir. |
| 12 | TST-07 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Kanit beyani ham JUnit ile celisemez; kapi kendi beyanina guvenmez. |
| 13 | TST-10 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Rapor kaynaktan eski olamaz; bayat kanit mevcut kodu olcmemis olabilir. |
| 14 | TST-11 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Kanittaki komut kod_profil ile ayni olmali; baska komutun kaniti sayilmaz. |
| 15 | TST-12 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Kanittaki rapor yolu kod_profil ile ayni olmali; baska rapor gosterilemez. |
| 16 | TST-09 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Test komutunun cikis kodu kayitli olmali; kosup kosmadigi bilinmeyen test yesil sayilmaz. |
| 17 | TST-01 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Basarisiz test sayisi sifir olmali; kirmizi testle PASS verilemez. |
| 18 | TST-02 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Hatali test sayisi sifir olmali; altyapi hatasi yesil sayilmaz. |
| 19 | TST-03 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | En az bir test kosmali; sifir test temiz degildir. |
| 20 | TST-05 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (24.11.2026) | Atlanan test tabandan fazla olamaz; test atlayarak yesil olunmaz. |
| 21 | TST-06 | `test_attest.py` | Kanit/yesil butunlugu — P0 | BEKLENEN BULGU (24.11.2026) | Kapsam tabanin bir altina kadar korunmali; sessiz kapsam kaybi P1. |
| 22 | DEP-01 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI | Manifest varken kilit anahtari yok, bos ya da kilit dosyasi eksikse bagimlilik surumleri denetimsiz kalir; kapi P0 verir. |
| 23 | DEP-02 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | ENVANTER DISI (olu kimlik) | Baslikta "Manifestteki paket kilitte yok [P0]" diye bildirilir ama dep_audit kodunda kilit paketlerini manifestle karsilastiran dal yok; yalniz DEP-01/03/04/05/06 dallari uygulanir. |
| 24 | DEP-06 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | BEKLENEN BULGU | Profilde bagimlilik_manifesti bos birakilirsa bagimlilik yuzeyi hic denetlenmez; kapi CALISTIRILMADI/P1 verir. |
| 25 | DEP-03 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | BEKLENEN BULGU | Surum sabitlenmezse (*, latest, bos ya da kilitsiz ^/~) ayni manifest farkli paket surumleri kurabilir; P1. |
| 26 | DEP-04 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | BEKLENEN BULGU | Kilit dosyasi diffte degisirken manifest guncellenmezse beyan edilen bagimlilik ile kilit ayrisir; P1. |
| 27 | TSL-03 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI | Teslim dosyasinin sha256 degeri manifestten farkliysa artefakt yolda degistirilmistir; P0 tahrifat. |
| 28 | TSL-04 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI | Teslim imzasi gecersizse manifest baska anahtarla imzalanmis veya sonradan degistirilmis olabilir; P0. |
| 29 | TSL-06 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI | Zorunlu teslim artefakti manifestte hic yoksa imza eksik kumeyi dogrular; kapsam boslugu P0. |
| 30 | TSL-01 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI | Teslim manifesti yok veya bozuksa imza dogrulanamaz; kapi fail-closed P0 verir. |
| 31 | TSL-02 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI | Manifestte listelenen dosya diskte yoksa teslim kumesi eksiktir; imza eksik artefakti kurtarmaz, P0. |
| 32 | TSL-05 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | BEKLENEN BULGU | Teslim imzasi yoksa butunluk yalniz dusuk guvenle kabul edilir; P1 uyari kapiyi kapatmaz. |
| 33 | API-02 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI | KFAZ0 envanterindeki disa acik imza kaybolursa mevcut cagiranlar sessizce kirilir; P0. |
| 34 | API-03 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | ENVANTER DISI (olu kimlik) | Baslikta "imza degismis (parametre/donus) [P0]" diye bildirilir ama api_surface yalniz kayip imza (API-02) ve regex adayi (API-04) dallarini uygular; imza degisimi karsilastirmasi kodda yok. |
| 35 | API-01 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | BEKLENEN BULGU | KFAZ0 API envanteri yoksa disa acik yuzey karsilastirilamaz; kapi CALISTIRILMADI/P1 verir. |
| 36 | API-05 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | BEKLENEN BULGU | API kademelerinden hicbiri kosmazsa disa acik yuzey denetimi tamamen korlesir; CALISTIRILMADI/P1. |
| 37 | API-04 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | BEKLENEN BULGU | Regex taramasi bir adayi kacirirsa disa acik yuzey eksik sayilir; DUSUK_GUVEN/P1. |
| 38 | OZT-01 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI | Oz-test taban dosyasi yok veya bozuksa onceki test envanteriyle karsilastirma yapilamaz; fail-closed P0. |
| 39 | OZT-02 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI | Tabandaki bir test kimligi bu kosuda yoksa test sessizce silinmistir; P0 kapsam kaybi. |
| 40 | OZT-03 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI | Kosuda hic test yoksa sifir test yesil sayilmamali; fail-closed P0. |
| 41 | OZT-04 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | ENVANTER DISI (olu kimlik) | Kaldirilmis sayac kurali. Baslikta yalniz "OZT-04 NICIN YOK" aciklamasi olarak gecer; kodda bu kimligi basan dal yok. Kimlik sayisi dususu zaten OZT-02 ile yakalanir. |
| 42 | OZT-05 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | BEKLENEN BULGU | Tabanda olmayan yeni bir test kimligi gorulurse pin guncellenmelidir; aksi halde envanter gercek kosuyu yansitmaz, P1. |
| 43 | OZT-06 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI | Taban kimlik hash degeri kendi listesiyle uyusmazsa taban elle kurcalanmistir; test envanteri guvenilmez olur, P0. |
| 44 | OLGU-04 | `olgu_lint.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI | Kamu attestation kaydi yok veya bozuksa kamu iddialari gercek commit ve agac kanitiyla baglanamaz; FAIL. |
| 45 | OLGU-05 | `olgu_lint.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI | ATLAS, attest ve KOD ciktilarindaki sayilar kanonik kayda uymazsa yayimlanan olcum yanlis olur; FAIL. |
| 46 | OLGU-06 | `olgu_lint.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI | Son DEVIR sonrasi mekanizma commit hash degerleri DERSLER kaydinda yok veya cozulmuyorsa degisiklik izi kopar; FAIL. |
| 47 | CHK-01 | `provenance_check.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI (24.11.2026) | Her zorunlu SCOPE-ID MASTER icinde markdown basligi olarak bulunmali; metinde gecmesi yetmez. |
| 48 | CHK-02 | `provenance_check.py` | Test envanteri, olcum ve provenance — P0/P1 | TEST EDILDI (24.11.2026) | Her zorunlu ID PROVENANCE tablosunda kapsiyor durumunda olmali. |
| 49 | CHK-05 | `provenance_check.py` | Test envanteri, olcum ve provenance — P0/P1 | BEKLENEN BULGU (24.11.2026) | Basliklar benzersiz olmali; tekrar eden baslik izlenebilirligi bozar. |
| 50 | SEC-04 | `secret_scan.py` | Bilgi seviyesi / olu kimlik — P1 | ENVANTER DISI (olu kimlik) | Baslikta "Ikili/kilit dosyasi atlandi [bilgi]" diye bildirilir ama hiçbir dal bu kimligi basmiyor; atlanan dosyalar yalniz sayilir, kimlikli BILGI satiri uretilmez. |

## Sonraki dilim

24.11.2026 itibariyla kapatilmayan bosluk yok (0). Dokuz eski boslugun her biri
gercek bir mutasyon vakasiyla kapatildi; 27 beklenen-bulgu vakasi
uyari modunda, digerleri kirmizi/terminal hukumle dogrulandi.


## Envanter disi kimlikler

Asagidaki kimlikler satir basinda veya `# --- KIMLIK` bolum basliginda **bildirilir** ama betigin hicbir kod dalinda **basilmaz**. Bir hukum uretmedikleri icin kural degildirler: mutasyonla ateslenemezler ve envantere katilirlarsa "kapsanan kural" sayisini sisirirler. Bu yuzden sayilmazlar; gerekceleri asagida satir satir durur.

Olcum yontemi: her kapi betigi AST ile gezilir; kimlik docstring DISINDA bir string sabiti olarak kodda akiyorsa basilabilir sayilir. Yeni bir olu kimlik gerekcesiz belirirse ya da bir dal eklenip kimlik basilirsa `make kapsam` fail-closed durur.

| Betik | Kimlik | Olcum | Gerekce |
|---|---|---|---|
| `oztest_attest.py` | OZT-04 | kodda basilmiyor | Kaldirilmis sayac kurali. Baslikta yalniz "OZT-04 NICIN YOK" aciklamasi olarak gecer; kodda bu kimligi basan dal yok. Kimlik sayisi dususu zaten OZT-02 ile yakalanir. |
| `api_surface.py` | API-03 | kodda basilmiyor | Baslikta "imza degismis (parametre/donus) [P0]" diye bildirilir ama api_surface yalniz kayip imza (API-02) ve regex adayi (API-04) dallarini uygular; imza degisimi karsilastirmasi kodda yok. |
| `dep_audit.py` | DEP-02 | kodda basilmiyor | Baslikta "Manifestteki paket kilitte yok [P0]" diye bildirilir ama dep_audit kodunda kilit paketlerini manifestle karsilastiran dal yok; yalniz DEP-01/03/04/05/06 dallari uygulanir. |
| `secret_scan.py` | SEC-04 | kodda basilmiyor | Baslikta "Ikili/kilit dosyasi atlandi [bilgi]" diye bildirilir ama hiçbir dal bu kimligi basmiyor; atlanan dosyalar yalniz sayilir, kimlikli BILGI satiri uretilmez. |

Toplam envanter disi kimlik: **4**; her biri için ölçüm `tools/kapsam.py --oztest` ile her koşuda yeniden alinir.

## Envanter disi dis referanslar

Baska bir kurala/karara yapilan atiflar kural sayilmaz; her biri gerekceli ve iki yonlu dogrulanir.

| Betik | Kimlik | Gerekce |
|---|---|---|
| `verify_doi.py` | DEC-027 | DEC karar kimligi; verify_doi bu kurali uygulamaz, DEC-027 bolum-farkindaligi politikasina atif yapar |

Toplam envanter disi dis referans: **1**.

## Kod icinde uretilen kimlikler

Asagidaki kimlikler `KURALLAR` basliginda veya `# --- KIMLIK`
bolum basliginda bildirilmez; betik kodu tarafindan string literal
olarak uretilir. Her biri tek tek denetlendi: bagimsiz bir
`KURALLAR` sozlesmesi degil, ilgili kapinin alt tanisi veya
sozlesme bolum verisidir. Bu yuzden envantere kural olarak eklenmez;
gerekce sessizce dusulmez. Ayni ailede yeni bir kimlik belirse bile
`make kapsam` fail-closed durur:

| Betik | Sinif | Kimlikler | Gerekce |
|---|---|---|---|
| `ai_disclosure.py` | tani-kodu | AI-04 | --check cikti uyusmazligi; AI-1 selftestinde kilitli cikti butunlugu alt tanisi. |
| `ai_disclosure.py` | tani-kodu | AI-03 | Beyan yazma I/O hatasi; hukum uretmeyen operasyonel tani. |
| `ai_disclosure.py` | tani-kodu | AI-02 | Entry alan/usage/evidence dogrulamasi; AI-1 selftestinin alt tanisi. |
| `ai_disclosure.py` | tani-kodu | AI-01 | Manifest kok/schema/scope/entries sozlesmesi; AI-1 selftestinin alt tanisi. |
| `ai_disclosure.py` | tani-kodu | AI-00 | Manifest veya sema yok/bozuk; AI-1 onkosul tanisi, bagimsiz KURALLAR kurali degil. |
| `olgu_lint.py` | tani-kodu | OLGU-03 | Ic deger uyusmazligi; OLGU-04..06 kapsamindaki tarihce denetiminin alt tanisi. |
| `olgu_lint.py` | tani-kodu | OLGU-02 | OLGULAR JSON/sema girdisi gecersiz; onkosul tanisi. |
| `olgu_lint.py` | tani-kodu | OLGU-01 | OLGULAR kanonu yok; olgu_lint onkosulu, OLGU-04..06 kurallarindan ayri. |
| `review_panel.py` | tani-kodu | HJ-07 | Attempt/maliyet siniri; HJ-1 selftestinin alt tanisi. |
| `review_panel.py` | tani-kodu | HJ-03 | Hukum kapsami/yinelenen kimlik/severity; HJ-1 selftestinin alt tanisi. |
| `review_panel.py` | tani-kodu | HJ-01 | JSON/kapali sema/alan sozlesmesi; HJ-1 selftestinin alt tanisi. |
| `review_panel.py` | tani-kodu | HJ-06 | Model ailesi/session cesitliligi; HJ-1 selftestinin alt tanisi. |
| `review_panel.py` | tani-kodu | HJ-08 | Panel ciktisi yazma I/O hatasi; operasyonel tani. |
| `review_panel.py` | tani-kodu | HJ-00 | Panel semasi okunamadi/kimlik uyusmadi; HJ-1 onkosul tanisi. |
| `review_panel.py` | tani-kodu | HJ-05 | Rol/session kimligi; HJ-1 selftestinin alt tanisi. |
| `review_panel.py` | tani-kodu | HJ-02 | Run/input uyusmazligi; HJ-1 selftestinin alt tanisi. |
| `review_panel.py` | tani-kodu | HJ-04 | Verdict/evidence butunlugu; HJ-1 selftestinin alt tanisi. |
| `scope_profile_check.py` | veri-kimligi | SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007, SC-008, SC-009, SC-010, SC-011, SC-012, SC-013, SC-014, SC-015, SC-016, SC-017, SC-018, SC-019, SC-020, SC-021, SC-022, SC-030 | Kapsam sozlesmesindeki zorunlu bolum kimligi; SP-01..07 kuraldir. |
| `chg_reconcile.py` | tani-kodu | RECK-00 | Ortak girdi/JSON/sema hatasi; RECK-08 sema kurali, RECK-01..09 ayri kurallardir. |

Not: `verify_doi.py` tarandi; bildirilen kural kimligi yok.
Dosyadaki `DEC-027` bir karar referansidir, kural degil; bu
yuzden `ag` sinifi envanterde kural olarak temsil edilmiyor.


## Tarama kaniti

`Baslikta` satir basindaki kural bildirimleridir. `Bolum basligi`
dosyanin herhangi bir yerindeki `# --- KIMLIK` basliklaridir; ilk 100
satir siniri YOKTUR. `Yeni`, yalniz bolum basliginda gorunen ve ust
listeye yazilmamis kimliklerdir. Envanter, iki kumenin birlesimidir.
Tarama `read_text().splitlines()` uzerinden tum dosyayi gezer;
`FRZ-08` 114. satirda bildirildigi halde envanterdedir. Bu, ilk 100
satir sinirinin olmadiginin canli kanitidir.

`DEC-10/12` ve `GM-17/18` gibi degisiklik etiketleri kural kimligi
degildir; yalnizca kural bildirimleri ve `# --- KIMLIK` basliklari
envantere alinir. `CHK-00` gibi ara kodlar ile kod icinde string
literal olarak uretilen AI/HJ/OLGU/SC/RECK kimlikleri yukaridaki
`Kod icinde uretilen kimlikler` tablosunda gerekcesiyle ayri tutulur;
sessizce yok sayilmaz.

| Betik | Baslikta | Bolum basligi | Yeni | Envanter |
|---|---|---|---|---|
| `ai_disclosure.py` | 0 | 0 | 0 | 0 |
| `apply_routing.py` | 0 | 0 | 0 | 0 |
| `budget_guard.py` | 0 | 0 | 0 | 0 |
| `check_models.py` | 8 | 0 | 0 | 8 |
| `cite_match.py` | 3 | 3 | 0 | 3 |
| `declaration_check.py` | 7 | 0 | 0 | 7 |
| `fix_reconcile.py` | 6 | 6 | 0 | 6 |
| `gate_2c.py` | 0 | 0 | 0 | 0 |
| `gate_merge.py` | 0 | 0 | 0 | 0 |
| `olgu_lint.py` | 3 | 0 | 0 | 3 |
| `oztest_attest.py` | 5 | 0 | 0 | 5 |
| `prompt_lint.py` | 12 | 0 | 0 | 12 |
| `provenance_check.py` | 0 | 3 | 3 | 3 |
| `quote_ratio.py` | 2 | 1 | 0 | 2 |
| `review_panel.py` | 0 | 0 | 0 | 0 |
| `scope_profile_check.py` | 7 | 5 | 0 | 7 |
| `source_class_check.py` | 3 | 0 | 0 | 3 |
| `teslim_imza.py` | 6 | 0 | 0 | 6 |
| `translit_check.py` | 2 | 2 | 0 | 2 |
| `verify_doi.py` | 0 | 0 | 0 | 0 |
| `api_surface.py` | 4 | 0 | 0 | 4 |
| `apply_routing.py` | 0 | 0 | 0 | 0 |
| `budget_guard.py` | 0 | 0 | 0 | 0 |
| `chg_reconcile.py` | 9 | 0 | 0 | 9 |
| `dep_audit.py` | 5 | 0 | 0 | 5 |
| `freeze_check.py` | 7 | 3 | 1 | 8 |
| `imzala.py` | 0 | 0 | 0 | 0 |
| `kod_gate_merge.py` | 0 | 0 | 0 | 0 |
| `perm_lint.py` | 8 | 0 | 0 | 8 |
| `secret_scan.py` | 4 | 0 | 0 | 4 |
| `test_attest.py` | 12 | 1 | 0 | 12 |

Toplam: 31 betik · 117 tekil kural; her satirda Envanter = Baslikta ∪ Bolum basligi.

## Referans olarak ayiklanan kimlikler

Asagidaki kimlikler bir betigin urettigi kural degil, baska bir
kurala/karara yapilan atiftir; envantere sayilmaz.

| Betik | Ayiklanan kimlik | Gerekce |
|---|---|---|
| `verify_doi.py` | DEC-027 | DEC karar kimligi; verify_doi bu kurali uygulamaz, DEC-027 bolum-farkindaligi politikasina atif yapar |

## REC ailesi vakalari

Her satir `make mutasyon` ile kosulur: temiz taban rc=0 ve FAIL izi
yok; tek ihlal yalniz hedef kuralin FAIL etiketiyle rc=1; ihlal geri
alininca kontrol kosusu rc=0. Alternatif satirlar ayni kuralin ikinci
tip ihlalidir; kopya degil, farkli hata dalidir.

| Vaka | Hedef kural | Aciklama |
|---|---|---|
| REC-01 | REC-01 | FAZ1 bulgu == FAZ2 FIX |
| REC-02 | REC-02 | oncelik dagilimi ayni |
| REC-02-CIFT-ONCELIK | REC-02 | ayni FIX-ID iki farkli oncelikle |
| REC-03 | REC-03 | FAZ1 bulgusu FAZ2 de atifli |
| REC-04 | REC-04 | UYGULANMIS FIX MASTER da gorunur |
| REC-05 | REC-05 | gate 2B KANITLI iddiasi dogrulanir |
| REC-05-BOZUK-JSON | REC-05 | gate 2B JSON bozuk |
| REC-05-REKONSILIASYON-BOZUK | REC-05 | manifest_reconciliation liste degil |
| REC-06 | REC-06 | hayalet kanit yok |
| REC-06-COKLU-HAYALET | REC-06 | birden fazla hayalet FIX-ID |

## Tam envanter

| Betik | Kural | Mutasyon vakasi | Durum | Gerekce |
|---|---|---|---|---|
| `check_models.py` | MOD-01 | MOD-01 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: MOD-01 |
| `check_models.py` | MOD-02 | MOD-02 | TEST EDILDI | atesleyen mutasyon vakasi: MOD-02 |
| `check_models.py` | MOD-03 | MOD-03 | TEST EDILDI | atesleyen mutasyon vakasi: MOD-03 |
| `check_models.py` | MOD-04 | MOD-04 | TEST EDILDI | atesleyen mutasyon vakasi: MOD-04 |
| `check_models.py` | MOD-05 | MOD-05, MOD-05-TOOLCALL | TEST EDILDI | atesleyen mutasyon vakasi: MOD-05, MOD-05-TOOLCALL |
| `check_models.py` | MOD-06 | MOD-06 | TEST EDILDI | atesleyen mutasyon vakasi: MOD-06 |
| `check_models.py` | MOD-07 | MOD-07 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: MOD-07 |
| `check_models.py` | MOD-08 | MOD-08, MOD-08-KOK-DISI, MOD-08-DOSYA-DEGIL | TEST EDILDI | atesleyen mutasyon vakasi: MOD-08, MOD-08-KOK-DISI, MOD-08-DOSYA-DEGIL |
| `cite_match.py` | CITE-01 | CITE-01 | TEST EDILDI | atesleyen mutasyon vakasi: CITE-01 |
| `cite_match.py` | CITE-02 | CITE-02 | TEST EDILDI | atesleyen mutasyon vakasi: CITE-02 |
| `cite_match.py` | CITE-03 | CITE-03 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: CITE-03 |
| `declaration_check.py` | DEC-01 | DEC-01 | TEST EDILDI | atesleyen mutasyon vakasi: DEC-01 |
| `declaration_check.py` | DEC-02 | DEC-02 | TEST EDILDI | atesleyen mutasyon vakasi: DEC-02 |
| `declaration_check.py` | DEC-03 | ATLAS-DEC-03 | TEST EDILDI | atesleyen mutasyon vakasi: ATLAS-DEC-03 |
| `declaration_check.py` | DEC-04 | DEC-04 | TEST EDILDI | atesleyen mutasyon vakasi: DEC-04 |
| `declaration_check.py` | DEC-05 | DEC-05 | TEST EDILDI | atesleyen mutasyon vakasi: DEC-05 |
| `declaration_check.py` | DEC-06 | DEC-06 | TEST EDILDI | atesleyen mutasyon vakasi: DEC-06 |
| `declaration_check.py` | DEC-07 | DEC-07 | TEST EDILDI | atesleyen mutasyon vakasi: DEC-07 |
| `fix_reconcile.py` | REC-01 | REC-01 | TEST EDILDI | atesleyen mutasyon vakasi: REC-01 |
| `fix_reconcile.py` | REC-02 | REC-02, REC-02-CIFT-ONCELIK | TEST EDILDI | atesleyen mutasyon vakasi: REC-02, REC-02-CIFT-ONCELIK |
| `fix_reconcile.py` | REC-03 | REC-03 | TEST EDILDI | atesleyen mutasyon vakasi: REC-03 |
| `fix_reconcile.py` | REC-04 | REC-04 | TEST EDILDI | atesleyen mutasyon vakasi: REC-04 |
| `fix_reconcile.py` | REC-05 | REC-05, REC-05-BOZUK-JSON, REC-05-REKONSILIASYON-BOZUK | TEST EDILDI | atesleyen mutasyon vakasi: REC-05, REC-05-BOZUK-JSON, REC-05-REKONSILIASYON-BOZUK |
| `fix_reconcile.py` | REC-06 | REC-06, REC-06-COKLU-HAYALET | TEST EDILDI | atesleyen mutasyon vakasi: REC-06, REC-06-COKLU-HAYALET |
| `olgu_lint.py` | OLGU-04 | OLGU-04 | TEST EDILDI | atesleyen mutasyon vakasi: OLGU-04 |
| `olgu_lint.py` | OLGU-05 | OLGU-05 | TEST EDILDI | atesleyen mutasyon vakasi: OLGU-05 |
| `olgu_lint.py` | OLGU-06 | OLGU-06 | TEST EDILDI | atesleyen mutasyon vakasi: OLGU-06 |
| `oztest_attest.py` | OZT-01 | OZT-01 | TEST EDILDI | atesleyen mutasyon vakasi: OZT-01 |
| `oztest_attest.py` | OZT-02 | OZT-02 | TEST EDILDI | atesleyen mutasyon vakasi: OZT-02 |
| `oztest_attest.py` | OZT-03 | OZT-03 | TEST EDILDI | atesleyen mutasyon vakasi: OZT-03 |
| `oztest_attest.py` | OZT-05 | OZT-05 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: OZT-05 |
| `oztest_attest.py` | OZT-06 | OZT-06 | TEST EDILDI | atesleyen mutasyon vakasi: OZT-06 |
| `prompt_lint.py` | PL-01 | PL-01 | TEST EDILDI | atesleyen mutasyon vakasi: PL-01 |
| `prompt_lint.py` | PL-02 | PL-02 | TEST EDILDI | atesleyen mutasyon vakasi: PL-02 |
| `prompt_lint.py` | PL-04 | PL-04 | TEST EDILDI | atesleyen mutasyon vakasi: PL-04 |
| `prompt_lint.py` | PL-09 | PL-09 | TEST EDILDI | atesleyen mutasyon vakasi: PL-09 |
| `prompt_lint.py` | PL-10 | ATLAS-PL-10 | TEST EDILDI | atesleyen mutasyon vakasi: ATLAS-PL-10 |
| `prompt_lint.py` | PL-11 | PL-11 | TEST EDILDI | atesleyen mutasyon vakasi: PL-11 |
| `prompt_lint.py` | PL-12 | PL-12 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: PL-12 |
| `prompt_lint.py` | PL-13 | PL-13 | TEST EDILDI | atesleyen mutasyon vakasi: PL-13 |
| `prompt_lint.py` | PL-14 | PL-14 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: PL-14 |
| `prompt_lint.py` | PL-16 | PL-16 | TEST EDILDI | atesleyen mutasyon vakasi: PL-16 |
| `prompt_lint.py` | PL-18 | PL-18 | TEST EDILDI | atesleyen mutasyon vakasi: PL-18 |
| `prompt_lint.py` | PL-19 | PL-19, PL-19-UYARI, PL-19-JSON-YOK | TEST EDILDI | atesleyen mutasyon vakasi: PL-19, PL-19-UYARI, PL-19-JSON-YOK |
| `provenance_check.py` | CHK-01 | CHK-01 | TEST EDILDI | atesleyen mutasyon vakasi: CHK-01 |
| `provenance_check.py` | CHK-02 | CHK-02 | TEST EDILDI | atesleyen mutasyon vakasi: CHK-02 |
| `provenance_check.py` | CHK-05 | CHK-05 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: CHK-05 |
| `quote_ratio.py` | QR-01 | QR-01 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: QR-01 |
| `quote_ratio.py` | QR-02 | ATLAS-QR-02, QR-02-DENGE | TEST EDILDI | atesleyen mutasyon vakasi: ATLAS-QR-02, QR-02-DENGE |
| `scope_profile_check.py` | SP-01 | SP-01 | TEST EDILDI | atesleyen mutasyon vakasi: SP-01 |
| `scope_profile_check.py` | SP-02 | SP-02 | TEST EDILDI | atesleyen mutasyon vakasi: SP-02 |
| `scope_profile_check.py` | SP-03 | SP-03 | TEST EDILDI | atesleyen mutasyon vakasi: SP-03 |
| `scope_profile_check.py` | SP-04 | SP-04 | TEST EDILDI | atesleyen mutasyon vakasi: SP-04 |
| `scope_profile_check.py` | SP-05 | SP-05 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: SP-05 |
| `scope_profile_check.py` | SP-06 | SP-06 | TEST EDILDI | atesleyen mutasyon vakasi: SP-06 |
| `scope_profile_check.py` | SP-07 | SP-07 | TEST EDILDI | atesleyen mutasyon vakasi: SP-07 |
| `source_class_check.py` | SRC-01 | SRC-01 | TEST EDILDI | atesleyen mutasyon vakasi: SRC-01 |
| `source_class_check.py` | SRC-02 | SRC-02 | TEST EDILDI | atesleyen mutasyon vakasi: SRC-02 |
| `source_class_check.py` | SRC-03 | SRC-03 | TEST EDILDI | atesleyen mutasyon vakasi: SRC-03 |
| `teslim_imza.py` | TSL-01 | TSL-01 | TEST EDILDI | atesleyen mutasyon vakasi: TSL-01 |
| `teslim_imza.py` | TSL-02 | TSL-02 | TEST EDILDI | atesleyen mutasyon vakasi: TSL-02 |
| `teslim_imza.py` | TSL-03 | TSL-03 | TEST EDILDI | atesleyen mutasyon vakasi: TSL-03 |
| `teslim_imza.py` | TSL-04 | TSL-04 | TEST EDILDI | atesleyen mutasyon vakasi: TSL-04 |
| `teslim_imza.py` | TSL-05 | TSL-05 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: TSL-05 |
| `teslim_imza.py` | TSL-06 | TSL-06 | TEST EDILDI | atesleyen mutasyon vakasi: TSL-06 |
| `translit_check.py` | TR-01 | TR-01 | TEST EDILDI | atesleyen mutasyon vakasi: TR-01 |
| `translit_check.py` | TR-02 | TR-02 | TEST EDILDI | atesleyen mutasyon vakasi: TR-02 |
| `api_surface.py` | API-01 | API-01 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: API-01 |
| `api_surface.py` | API-02 | API-02 | TEST EDILDI | atesleyen mutasyon vakasi: API-02 |
| `api_surface.py` | API-04 | API-04 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: API-04 |
| `api_surface.py` | API-05 | API-05 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: API-05 |
| `chg_reconcile.py` | RECK-01 | RECK-01 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-01 |
| `chg_reconcile.py` | RECK-02 | RECK-02 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-02 |
| `chg_reconcile.py` | RECK-03 | RECK-03 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-03 |
| `chg_reconcile.py` | RECK-04 | RECK-04 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-04 |
| `chg_reconcile.py` | RECK-05 | RECK-05 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-05 |
| `chg_reconcile.py` | RECK-06 | RECK-06 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-06 |
| `chg_reconcile.py` | RECK-07 | RECK-07 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-07 |
| `chg_reconcile.py` | RECK-08 | RECK-08 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-08 |
| `chg_reconcile.py` | RECK-09 | RECK-09 | TEST EDILDI | atesleyen mutasyon vakasi: RECK-09 |
| `dep_audit.py` | DEP-01 | DEP-01 | TEST EDILDI | atesleyen mutasyon vakasi: DEP-01 |
| `dep_audit.py` | DEP-03 | DEP-03 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: DEP-03 |
| `dep_audit.py` | DEP-04 | DEP-04 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: DEP-04 |
| `dep_audit.py` | DEP-05 | DEP-05 | TEST EDILDI | atesleyen mutasyon vakasi: DEP-05 |
| `dep_audit.py` | DEP-06 | DEP-06 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: DEP-06 |
| `freeze_check.py` | FRZ-01 | FRZ-01, FRZ-01-KAYIP, FRZ-01T, FRZ-01-02 | TEST EDILDI | atesleyen mutasyon vakasi: FRZ-01, FRZ-01-KAYIP, FRZ-01T, FRZ-01-02 |
| `freeze_check.py` | FRZ-02 | FRZ-01-02, FRZ-02, FRZ-02-KAYIP | TEST EDILDI | atesleyen mutasyon vakasi: FRZ-01-02, FRZ-02, FRZ-02-KAYIP |
| `freeze_check.py` | FRZ-03 | FRZ-03 | TEST EDILDI | atesleyen mutasyon vakasi: FRZ-03 |
| `freeze_check.py` | FRZ-04 | FRZ-04 | TEST EDILDI | atesleyen mutasyon vakasi: FRZ-04 |
| `freeze_check.py` | FRZ-05 | FRZ-05 | TEST EDILDI | atesleyen mutasyon vakasi: FRZ-05 |
| `freeze_check.py` | FRZ-06 | FRZ-06 | TEST EDILDI | atesleyen mutasyon vakasi: FRZ-06 |
| `freeze_check.py` | FRZ-07 | FRZ-07 | TEST EDILDI | atesleyen mutasyon vakasi: FRZ-07 |
| `freeze_check.py` | FRZ-08 | FRZ-08, FRZ-08-IMZA, FRZ-08-GECERSIZ-IMZA, FRZ-08-P1 | TEST EDILDI | atesleyen mutasyon vakasi: FRZ-08, FRZ-08-IMZA, FRZ-08-GECERSIZ-IMZA, FRZ-08-P1 |
| `perm_lint.py` | PERM-01 | KOD-PERM-01 | TEST EDILDI | atesleyen mutasyon vakasi: KOD-PERM-01 |
| `perm_lint.py` | PERM-02 | PERM-02 | TEST EDILDI | atesleyen mutasyon vakasi: PERM-02 |
| `perm_lint.py` | PERM-03 | PERM-03 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: PERM-03 |
| `perm_lint.py` | PERM-04 | PERM-04 | TEST EDILDI | atesleyen mutasyon vakasi: PERM-04 |
| `perm_lint.py` | PERM-05 | PERM-05 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: PERM-05 |
| `perm_lint.py` | PERM-06 | PERM-06 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: PERM-06 |
| `perm_lint.py` | PERM-07 | PERM-07 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: PERM-07 |
| `perm_lint.py` | PERM-08 | PERM-08 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: PERM-08 |
| `secret_scan.py` | SEC-01 | SEC-01 | TEST EDILDI | atesleyen mutasyon vakasi: SEC-01 |
| `secret_scan.py` | SEC-02 | KOD-SEC-02 | TEST EDILDI | atesleyen mutasyon vakasi: KOD-SEC-02 |
| `secret_scan.py` | SEC-03 | SEC-03 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: SEC-03 |
| `secret_scan.py` | SEC-05 | SEC-05 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: SEC-05 |
| `test_attest.py` | TST-01 | TST-01 | TEST EDILDI | atesleyen mutasyon vakasi: TST-01 |
| `test_attest.py` | TST-02 | TST-02 | TEST EDILDI | atesleyen mutasyon vakasi: TST-02 |
| `test_attest.py` | TST-03 | TST-03 | TEST EDILDI | atesleyen mutasyon vakasi: TST-03 |
| `test_attest.py` | TST-04 | TST-04 | TEST EDILDI | atesleyen mutasyon vakasi: TST-04 |
| `test_attest.py` | TST-05 | TST-05 | TEST EDILDI | atesleyen mutasyon vakasi: TST-05 |
| `test_attest.py` | TST-06 | TST-06 | BEKLENEN BULGU | yalniz beklenen-bulgu sozlesmesi: TST-06 |
| `test_attest.py` | TST-07 | TST-07 | TEST EDILDI | atesleyen mutasyon vakasi: TST-07 |
| `test_attest.py` | TST-08 | TST-08 | TEST EDILDI | atesleyen mutasyon vakasi: TST-08 |
| `test_attest.py` | TST-09 | TST-09 | TEST EDILDI | atesleyen mutasyon vakasi: TST-09 |
| `test_attest.py` | TST-10 | TST-10 | TEST EDILDI | atesleyen mutasyon vakasi: TST-10 |
| `test_attest.py` | TST-11 | TST-11 | TEST EDILDI | atesleyen mutasyon vakasi: TST-11 |
| `test_attest.py` | TST-12 | TST-12 | TEST EDILDI | atesleyen mutasyon vakasi: TST-12 |
