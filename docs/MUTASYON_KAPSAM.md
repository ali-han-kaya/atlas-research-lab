# Mutasyon kapsami — tam kural envanteri

Kaynak: `tools/kapsam.py` (uretilmis dosya; elle duzenlenmez).
Envanter, ATLAS ve KOD kapi betiklerinin satir basi kural bildirimlerinden
ve dosyanin herhangi bir yerindeki `# --- KIMLIK` bolum basliklarindan gelir;
`*_selftest.py` ve `OLCUM-*` referanslari sayilmaz.

Her kural icin tek soru sorulur: **mutasyon bataryasinda onu ateslettiren
bir vaka var mi?** Yoksa iki durumdan biri yazilir: gerekcesi olculmus
**KAPSAM DISI** ya da **BOSLUK**. Bosluk gizlenmez.

## Ozet

| Olcum | Deger |
|---|---|
| Kapi betigi | 21 |
| Bildirilen kural | 122 |
| Mutasyon vakasi olan (TEST EDILDI) | 83 |
| Gerekceli kapsam disi | 27 |
| Bosluk (gerekce yok) | 12 |
| — bunlardan yalniz oz-testte anilan | 10 |
| — hicbir testte gecmeyen | 2 |

## Risk sirasi (51 kural)

19.11.2026 itibariyla mutation kapsami olmayan 51 kural; siralama
saglamlik/etki sirasina gore sabittir. Kapatilan her kural bu turda
vaka aldi; durum sutunu guncel envanterden okunur.

| # | Kural | Betik | Grup | Durum | Gerekce |
|---|---|---|---|---|---|
| 1 | TST-08 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (bu tur) | Ham test raporu yok/okunamiyor — kanitsiz PASS P0; kapinin kanit temeli. |
| 2 | RECK-06 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (bu tur) | Dondurulmus bolge diff'te — dogrudan tamper sinyali, P0. |
| 3 | DEP-05 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | TEST EDILDI (bu tur) | Izinli lisans listesi disinda bagimlilik — tedarik/uyum P0. |
| 4 | FRZ-08 | `freeze_check.py` | Kapsam/degisiklik butunlugu — P0 | BOSLUK (sonraki dilim) | Temiz agac iddiasi imzayla baglanmali; imzasiz veya yanlis anahtarli taban tamper ya da dusuk guven sayilir. |
| 5 | RECK-01 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (bu tur) | KFAZ0 sozlesmesindeki her REQ plan/eslesmede karsilik bulmali; aksi halde kapsamsiz sozlesme sessizce yesil kalir. |
| 6 | RECK-02 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (bu tur) | "UYGULANMIS" denilen her CHG'nin dosyasi git diff'te olmali; beyan ile gercek degisiklik carpraz denetlenir. |
| 7 | RECK-08 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | BOSLUK (sonraki dilim) | Makine bloklarinin alan bicimi semaya uymali; sessizce dusen girdi RECK-01/07'yi devre disi birakir. |
| 8 | RECK-09 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | BOSLUK (sonraki dilim) | Plan yokken urun kodu degismemeli; KFAZ0 oncesi degisiklik kapsamsiz ve denetimsiz kalir. |
| 9 | RECK-04 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (bu tur) | 2B kapisinin "KANITLI" dedigi her CHG diff'te olmali; ikinci gozun iddiasi manifest ve diff ile dogrulanir. |
| 10 | RECK-05 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | TEST EDILDI (bu tur) | Hayalet CHG yok: olmayan REQ veya plansiz dosyaya baglanan degisiklik P0; manifest-diff bagini korur. |
| 11 | RECK-07 | `chg_reconcile.py` | Kapsam/degisiklik butunlugu — P0 | BOSLUK (sonraki dilim) | Davranissal her REQ tabanda olmayan YENI bir test adina eslenmeli; eski testi gostermek bedava yesildir. |
| 12 | TST-07 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (bu tur) | Kanit beyani ham JUnit ile celisemez; kapi kendi beyanina guvenmez. |
| 13 | TST-10 | `test_attest.py` | Kanit/yesil butunlugu — P0 | BOSLUK (sonraki dilim) | Rapor kaynaktan eski olamaz; bayat kanit mevcut kodu olcmemis olabilir. |
| 14 | TST-11 | `test_attest.py` | Kanit/yesil butunlugu — P0 | BOSLUK (sonraki dilim) | Kanittaki komut kod_profil ile ayni olmali; baska komutun kaniti sayilmaz. |
| 15 | TST-12 | `test_attest.py` | Kanit/yesil butunlugu — P0 | BOSLUK (sonraki dilim) | Kanittaki rapor yolu kod_profil ile ayni olmali; baska rapor gosterilemez. |
| 16 | TST-09 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (bu tur) | Test komutunun cikis kodu kayitli olmali; kosup kosmadigi bilinmeyen test yesil sayilmaz. |
| 17 | TST-01 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (bu tur) | Basarisiz test sayisi sifir olmali; kirmizi testle PASS verilemez. |
| 18 | TST-02 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (bu tur) | Hatali test sayisi sifir olmali; altyapi hatasi yesil sayilmaz. |
| 19 | TST-03 | `test_attest.py` | Kanit/yesil butunlugu — P0 | TEST EDILDI (bu tur) | En az bir test kosmali; sifir test temiz degildir. |
| 20 | TST-05 | `test_attest.py` | Kanit/yesil butunlugu — P0 | BOSLUK (sonraki dilim) | Atlanan test tabandan fazla olamaz; test atlayarak yesil olunmaz. |
| 21 | TST-06 | `test_attest.py` | Kanit/yesil butunlugu — P0 | BOSLUK (sonraki dilim) | Kapsam tabanin bir altina kadar korunmali; sessiz kapsam kaybi P1. |
| 22 | DEP-01 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 23 | DEP-02 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 24 | DEP-06 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 25 | DEP-03 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 26 | DEP-04 | `dep_audit.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 27 | TSL-03 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 28 | TSL-04 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 29 | TSL-06 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 30 | TSL-01 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 31 | TSL-02 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 32 | TSL-05 | `teslim_imza.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 33 | API-02 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 34 | API-03 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 35 | API-01 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 36 | API-05 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 37 | API-04 | `api_surface.py` | Tedarik, teslim ve disa acik yuzey — P0/P1 | KAPSAM DISI | Tedarik, teslim ve disa acik yuzey — P0/P1 |
| 38 | OZT-01 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 39 | OZT-02 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 40 | OZT-03 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 41 | OZT-04 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 42 | OZT-05 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 43 | OZT-06 | `oztest_attest.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 44 | OLGU-04 | `olgu_lint.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 45 | OLGU-05 | `olgu_lint.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 46 | OLGU-06 | `olgu_lint.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 47 | CHK-01 | `provenance_check.py` | Test envanteri, olcum ve provenance — P0/P1 | BOSLUK (sonraki dilim) | Her zorunlu SCOPE-ID MASTER icinde markdown basligi olarak bulunmali; metinde gecmesi yetmez. |
| 48 | CHK-02 | `provenance_check.py` | Test envanteri, olcum ve provenance — P0/P1 | BOSLUK (sonraki dilim) | Her zorunlu ID PROVENANCE tablosunda kapsiyor durumunda olmali. |
| 49 | CHK-05 | `provenance_check.py` | Test envanteri, olcum ve provenance — P0/P1 | BOSLUK (sonraki dilim) | Basliklar benzersiz olmali; tekrar eden baslik izlenebilirligi bozar. |
| 50 | DEC-027 | `verify_doi.py` | Test envanteri, olcum ve provenance — P0/P1 | KAPSAM DISI | Test envanteri, olcum ve provenance — P0/P1 |
| 51 | SEC-04 | `secret_scan.py` | Bilgi seviyesi / olu kimlik — P1 | KAPSAM DISI | Bilgi seviyesi / olu kimlik — P1 |

## Sonraki dilim

Asagidaki kural(lar) bu turda kapatilmadi; hala hicbir testte
gorunmeyen 2 kuralin risk sirasindaki ilk 2 tanesidir. Bir sonraki
dilimde gercek vakayla kapatilacak; sessizce sayidan dusulmedi.

| Kural | Betik | Neden test edilemedi / neyi korur |
|---|---|---|
| TST-05 | `test_attest.py` | Atlanan test tabandan fazla olamaz; test atlayarak yesil olunmaz. |
| TST-06 | `test_attest.py` | Kapsam tabanin bir altina kadar korunmali; sessiz kapsam kaybi P1. |

## Kapsam disi siniflari

Gerekceler tahmin degil; her satir betigin kodundaki bagimliliga dayanir
(asagida betik adiyla birlikte yazili).

| Sinif | Gerekce (betikte olculen bagimlilik) | Betik | Kural |
|---|---|---|---|
| ag | requests ile api.crossref.org sorgusu; batarya agsiz kosar | verify_doi.py | 1 |
| depo-durumu | `git diff --name-only HEAD` ile degisen dosyalari okur | dep_audit.py | 5 |
| gizli-anahtar | HMAC anahtari ister (LAB_IMZA_ANAHTARI / ~/.config/lab_imza.key); anahtar depoya konmaz | teslim_imza.py | 6 |
| kosu-durumu | butun agacin selftest hash tabanini ve ham kosu ciktisini ister | api_surface.py, oztest_attest.py | 11 |
| olu-kimlik | SEC-04 yalniz baslikta bildirilir; hicbir kod dali bu kimligi basmiyor (atlanan dosyalar yalniz sayilir) | secret_scan.py | 1 |
| tarihce | SURUM.md makine blogunu HEAD/commit hashleriyle karsilastirir | olgu_lint.py | 3 |

## Tarama kaniti

`Baslikta` satir basindaki kural bildirimleridir. `Bolum basligi`
dosyanin herhangi bir yerindeki `# --- KIMLIK` basliklaridir; ilk 100
satir siniri YOKTUR. `Yeni`, yalniz bolum basliginda gorunen ve ust
listeye yazilmamis kimliklerdir. Envanter, iki kumenin birlesimidir.

`DEC-10/12` ve `GM-17/18` gibi degisiklik etiketleri kural kimligi
degildir; yalnizca kural bildirimleri ve `# --- KIMLIK` basliklari
taranir. `CHK-00` gibi bolum basligi olmayan ara kodlar da bu
envanterin konusu degildir.

| Betik | Baslikta | Bolum basligi | Yeni | Envanter |
|---|---|---|---|---|
| `check_models.py` | 8 | 0 | 0 | 8 |
| `cite_match.py` | 3 | 3 | 0 | 3 |
| `declaration_check.py` | 7 | 0 | 0 | 7 |
| `fix_reconcile.py` | 6 | 6 | 0 | 6 |
| `olgu_lint.py` | 3 | 0 | 0 | 3 |
| `oztest_attest.py` | 6 | 0 | 0 | 6 |
| `prompt_lint.py` | 12 | 0 | 0 | 12 |
| `provenance_check.py` | 0 | 3 | 3 | 3 |
| `quote_ratio.py` | 2 | 1 | 0 | 2 |
| `scope_profile_check.py` | 7 | 5 | 0 | 7 |
| `source_class_check.py` | 3 | 0 | 0 | 3 |
| `teslim_imza.py` | 6 | 0 | 0 | 6 |
| `translit_check.py` | 2 | 2 | 0 | 2 |
| `verify_doi.py` | 1 | 1 | 0 | 1 |
| `api_surface.py` | 5 | 0 | 0 | 5 |
| `chg_reconcile.py` | 9 | 0 | 0 | 9 |
| `dep_audit.py` | 6 | 0 | 0 | 6 |
| `freeze_check.py` | 7 | 3 | 1 | 8 |
| `perm_lint.py` | 8 | 0 | 0 | 8 |
| `secret_scan.py` | 5 | 0 | 0 | 5 |
| `test_attest.py` | 12 | 1 | 0 | 12 |

Toplam: 21 betik · 122 tekil kural; her satirda Envanter = Baslikta ∪ Bolum basligi.

## Tam envanter

| Betik | Kural | Mutasyon vakasi | Durum | Gerekce |
|---|---|---|---|---|
| `check_models.py` | MOD-01 | MOD-01 | TEST EDILDI | mutasyon vakasi: MOD-01 |
| `check_models.py` | MOD-02 | MOD-02 | TEST EDILDI | mutasyon vakasi: MOD-02 |
| `check_models.py` | MOD-03 | MOD-03 | TEST EDILDI | mutasyon vakasi: MOD-03 |
| `check_models.py` | MOD-04 | MOD-04 | TEST EDILDI | mutasyon vakasi: MOD-04 |
| `check_models.py` | MOD-05 | MOD-05 | TEST EDILDI | mutasyon vakasi: MOD-05 |
| `check_models.py` | MOD-06 | MOD-06 | TEST EDILDI | mutasyon vakasi: MOD-06 |
| `check_models.py` | MOD-07 | MOD-07 | TEST EDILDI | mutasyon vakasi: MOD-07 |
| `check_models.py` | MOD-08 | MOD-08 | TEST EDILDI | mutasyon vakasi: MOD-08 |
| `cite_match.py` | CITE-01 | CITE-01 | TEST EDILDI | mutasyon vakasi: CITE-01 |
| `cite_match.py` | CITE-02 | CITE-02 | TEST EDILDI | mutasyon vakasi: CITE-02 |
| `cite_match.py` | CITE-03 | CITE-03 | TEST EDILDI | mutasyon vakasi: CITE-03 |
| `declaration_check.py` | DEC-01 | DEC-01 | TEST EDILDI | mutasyon vakasi: DEC-01 |
| `declaration_check.py` | DEC-02 | DEC-02 | TEST EDILDI | mutasyon vakasi: DEC-02 |
| `declaration_check.py` | DEC-03 | ATLAS-DEC-03 | TEST EDILDI | mutasyon vakasi: ATLAS-DEC-03 |
| `declaration_check.py` | DEC-04 | DEC-04 | TEST EDILDI | mutasyon vakasi: DEC-04 |
| `declaration_check.py` | DEC-05 | DEC-05 | TEST EDILDI | mutasyon vakasi: DEC-05 |
| `declaration_check.py` | DEC-06 | DEC-06 | TEST EDILDI | mutasyon vakasi: DEC-06 |
| `declaration_check.py` | DEC-07 | DEC-07 | TEST EDILDI | mutasyon vakasi: DEC-07 |
| `fix_reconcile.py` | REC-01 | REC-01 | TEST EDILDI | mutasyon vakasi: REC-01 |
| `fix_reconcile.py` | REC-02 | REC-02 | TEST EDILDI | mutasyon vakasi: REC-02 |
| `fix_reconcile.py` | REC-03 | REC-03 | TEST EDILDI | mutasyon vakasi: REC-03 |
| `fix_reconcile.py` | REC-04 | REC-04 | TEST EDILDI | mutasyon vakasi: REC-04 |
| `fix_reconcile.py` | REC-05 | REC-05 | TEST EDILDI | mutasyon vakasi: REC-05 |
| `fix_reconcile.py` | REC-06 | REC-06 | TEST EDILDI | mutasyon vakasi: REC-06 |
| `olgu_lint.py` | OLGU-04 | — | KAPSAM DISI | tarihce: SURUM.md makine blogunu HEAD/commit hashleriyle karsilastirir |
| `olgu_lint.py` | OLGU-05 | — | KAPSAM DISI | tarihce: SURUM.md makine blogunu HEAD/commit hashleriyle karsilastirir |
| `olgu_lint.py` | OLGU-06 | — | KAPSAM DISI | tarihce: SURUM.md makine blogunu HEAD/commit hashleriyle karsilastirir |
| `oztest_attest.py` | OZT-01 | — | KAPSAM DISI | kosu-durumu: butun agacin selftest hash tabanini ve ham kosu ciktisini ister |
| `oztest_attest.py` | OZT-02 | — | KAPSAM DISI | kosu-durumu: butun agacin selftest hash tabanini ve ham kosu ciktisini ister |
| `oztest_attest.py` | OZT-03 | — | KAPSAM DISI | kosu-durumu: butun agacin selftest hash tabanini ve ham kosu ciktisini ister |
| `oztest_attest.py` | OZT-04 | — | KAPSAM DISI | kosu-durumu: butun agacin selftest hash tabanini ve ham kosu ciktisini ister |
| `oztest_attest.py` | OZT-05 | — | KAPSAM DISI | kosu-durumu: butun agacin selftest hash tabanini ve ham kosu ciktisini ister |
| `oztest_attest.py` | OZT-06 | — | KAPSAM DISI | kosu-durumu: butun agacin selftest hash tabanini ve ham kosu ciktisini ister |
| `prompt_lint.py` | PL-01 | PL-01 | TEST EDILDI | mutasyon vakasi: PL-01 |
| `prompt_lint.py` | PL-02 | PL-02 | TEST EDILDI | mutasyon vakasi: PL-02 |
| `prompt_lint.py` | PL-04 | PL-04 | TEST EDILDI | mutasyon vakasi: PL-04 |
| `prompt_lint.py` | PL-09 | PL-09 | TEST EDILDI | mutasyon vakasi: PL-09 |
| `prompt_lint.py` | PL-10 | ATLAS-PL-10 | TEST EDILDI | mutasyon vakasi: ATLAS-PL-10 |
| `prompt_lint.py` | PL-11 | PL-11 | TEST EDILDI | mutasyon vakasi: PL-11 |
| `prompt_lint.py` | PL-12 | PL-12 | TEST EDILDI | mutasyon vakasi: PL-12 |
| `prompt_lint.py` | PL-13 | PL-13 | TEST EDILDI | mutasyon vakasi: PL-13 |
| `prompt_lint.py` | PL-14 | PL-14 | TEST EDILDI | mutasyon vakasi: PL-14 |
| `prompt_lint.py` | PL-16 | PL-16 | TEST EDILDI | mutasyon vakasi: PL-16 |
| `prompt_lint.py` | PL-18 | PL-18 | TEST EDILDI | mutasyon vakasi: PL-18 |
| `prompt_lint.py` | PL-19 | PL-19 | TEST EDILDI | mutasyon vakasi: PL-19 |
| `provenance_check.py` | CHK-01 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `provenance_check.py` | CHK-02 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `provenance_check.py` | CHK-05 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `quote_ratio.py` | QR-01 | QR-01 | TEST EDILDI | mutasyon vakasi: QR-01 |
| `quote_ratio.py` | QR-02 | ATLAS-QR-02 | TEST EDILDI | mutasyon vakasi: ATLAS-QR-02 |
| `scope_profile_check.py` | SP-01 | SP-01 | TEST EDILDI | mutasyon vakasi: SP-01 |
| `scope_profile_check.py` | SP-02 | SP-02 | TEST EDILDI | mutasyon vakasi: SP-02 |
| `scope_profile_check.py` | SP-03 | SP-03 | TEST EDILDI | mutasyon vakasi: SP-03 |
| `scope_profile_check.py` | SP-04 | SP-04 | TEST EDILDI | mutasyon vakasi: SP-04 |
| `scope_profile_check.py` | SP-05 | SP-05 | TEST EDILDI | mutasyon vakasi: SP-05 |
| `scope_profile_check.py` | SP-06 | SP-06 | TEST EDILDI | mutasyon vakasi: SP-06 |
| `scope_profile_check.py` | SP-07 | SP-07 | TEST EDILDI | mutasyon vakasi: SP-07 |
| `source_class_check.py` | SRC-01 | SRC-01 | TEST EDILDI | mutasyon vakasi: SRC-01 |
| `source_class_check.py` | SRC-02 | SRC-02 | TEST EDILDI | mutasyon vakasi: SRC-02 |
| `source_class_check.py` | SRC-03 | SRC-03 | TEST EDILDI | mutasyon vakasi: SRC-03 |
| `teslim_imza.py` | TSL-01 | — | KAPSAM DISI | gizli-anahtar: HMAC anahtari ister (LAB_IMZA_ANAHTARI / ~/.config/lab_imza.key); anahtar depoya konmaz |
| `teslim_imza.py` | TSL-02 | — | KAPSAM DISI | gizli-anahtar: HMAC anahtari ister (LAB_IMZA_ANAHTARI / ~/.config/lab_imza.key); anahtar depoya konmaz |
| `teslim_imza.py` | TSL-03 | — | KAPSAM DISI | gizli-anahtar: HMAC anahtari ister (LAB_IMZA_ANAHTARI / ~/.config/lab_imza.key); anahtar depoya konmaz |
| `teslim_imza.py` | TSL-04 | — | KAPSAM DISI | gizli-anahtar: HMAC anahtari ister (LAB_IMZA_ANAHTARI / ~/.config/lab_imza.key); anahtar depoya konmaz |
| `teslim_imza.py` | TSL-05 | — | KAPSAM DISI | gizli-anahtar: HMAC anahtari ister (LAB_IMZA_ANAHTARI / ~/.config/lab_imza.key); anahtar depoya konmaz |
| `teslim_imza.py` | TSL-06 | — | KAPSAM DISI | gizli-anahtar: HMAC anahtari ister (LAB_IMZA_ANAHTARI / ~/.config/lab_imza.key); anahtar depoya konmaz |
| `translit_check.py` | TR-01 | TR-01 | TEST EDILDI | mutasyon vakasi: TR-01 |
| `translit_check.py` | TR-02 | TR-02 | TEST EDILDI | mutasyon vakasi: TR-02 |
| `verify_doi.py` | DEC-027 | — | KAPSAM DISI | ag: requests ile api.crossref.org sorgusu; batarya agsiz kosar |
| `api_surface.py` | API-01 | — | KAPSAM DISI | kosu-durumu: KFAZ0 _KOSU/gate/BASELINE.json imza envanterini ister; envanter yoksa CALISTIRILMADI |
| `api_surface.py` | API-02 | — | KAPSAM DISI | kosu-durumu: KFAZ0 _KOSU/gate/BASELINE.json imza envanterini ister; envanter yoksa CALISTIRILMADI |
| `api_surface.py` | API-03 | — | KAPSAM DISI | kosu-durumu: KFAZ0 _KOSU/gate/BASELINE.json imza envanterini ister; envanter yoksa CALISTIRILMADI |
| `api_surface.py` | API-04 | — | KAPSAM DISI | kosu-durumu: KFAZ0 _KOSU/gate/BASELINE.json imza envanterini ister; envanter yoksa CALISTIRILMADI |
| `api_surface.py` | API-05 | — | KAPSAM DISI | kosu-durumu: KFAZ0 _KOSU/gate/BASELINE.json imza envanterini ister; envanter yoksa CALISTIRILMADI |
| `chg_reconcile.py` | RECK-01 | RECK-01 | TEST EDILDI | mutasyon vakasi: RECK-01 |
| `chg_reconcile.py` | RECK-02 | RECK-02 | TEST EDILDI | mutasyon vakasi: RECK-02 |
| `chg_reconcile.py` | RECK-03 | RECK-03 | TEST EDILDI | mutasyon vakasi: RECK-03 |
| `chg_reconcile.py` | RECK-04 | RECK-04 | TEST EDILDI | mutasyon vakasi: RECK-04 |
| `chg_reconcile.py` | RECK-05 | RECK-05 | TEST EDILDI | mutasyon vakasi: RECK-05 |
| `chg_reconcile.py` | RECK-06 | RECK-06 | TEST EDILDI | mutasyon vakasi: RECK-06 |
| `chg_reconcile.py` | RECK-07 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `chg_reconcile.py` | RECK-08 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `chg_reconcile.py` | RECK-09 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `dep_audit.py` | DEP-01 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-02 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-03 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-04 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-05 | DEP-05 | TEST EDILDI | mutasyon vakasi: DEP-05 |
| `dep_audit.py` | DEP-06 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `freeze_check.py` | FRZ-01 | FRZ-01 | TEST EDILDI | mutasyon vakasi: FRZ-01 |
| `freeze_check.py` | FRZ-02 | FRZ-02 | TEST EDILDI | mutasyon vakasi: FRZ-02 |
| `freeze_check.py` | FRZ-03 | FRZ-03 | TEST EDILDI | mutasyon vakasi: FRZ-03 |
| `freeze_check.py` | FRZ-04 | FRZ-04 | TEST EDILDI | mutasyon vakasi: FRZ-04 |
| `freeze_check.py` | FRZ-05 | FRZ-05 | TEST EDILDI | mutasyon vakasi: FRZ-05 |
| `freeze_check.py` | FRZ-06 | FRZ-06 | TEST EDILDI | mutasyon vakasi: FRZ-06 |
| `freeze_check.py` | FRZ-07 | FRZ-07 | TEST EDILDI | mutasyon vakasi: FRZ-07 |
| `freeze_check.py` | FRZ-08 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `perm_lint.py` | PERM-01 | KOD-PERM-01 | TEST EDILDI | mutasyon vakasi: KOD-PERM-01 |
| `perm_lint.py` | PERM-02 | PERM-02 | TEST EDILDI | mutasyon vakasi: PERM-02 |
| `perm_lint.py` | PERM-03 | PERM-03 | TEST EDILDI | mutasyon vakasi: PERM-03 |
| `perm_lint.py` | PERM-04 | PERM-04 | TEST EDILDI | mutasyon vakasi: PERM-04 |
| `perm_lint.py` | PERM-05 | PERM-05 | TEST EDILDI | mutasyon vakasi: PERM-05 |
| `perm_lint.py` | PERM-06 | PERM-06 | TEST EDILDI | mutasyon vakasi: PERM-06 |
| `perm_lint.py` | PERM-07 | PERM-07 | TEST EDILDI | mutasyon vakasi: PERM-07 |
| `perm_lint.py` | PERM-08 | PERM-08 | TEST EDILDI | mutasyon vakasi: PERM-08 |
| `secret_scan.py` | SEC-01 | SEC-01 | TEST EDILDI | mutasyon vakasi: SEC-01 |
| `secret_scan.py` | SEC-02 | KOD-SEC-02 | TEST EDILDI | mutasyon vakasi: KOD-SEC-02 |
| `secret_scan.py` | SEC-03 | SEC-03 | TEST EDILDI | mutasyon vakasi: SEC-03 |
| `secret_scan.py` | SEC-04 | — | KAPSAM DISI | olu-kimlik: SEC-04 yalniz baslikta bildirilir; hicbir kod dali bu kimligi basmiyor (atlanan dosyalar yalniz sayilir) |
| `secret_scan.py` | SEC-05 | SEC-05 | TEST EDILDI | mutasyon vakasi: SEC-05 |
| `test_attest.py` | TST-01 | TST-01 | TEST EDILDI | mutasyon vakasi: TST-01 |
| `test_attest.py` | TST-02 | TST-02 | TEST EDILDI | mutasyon vakasi: TST-02 |
| `test_attest.py` | TST-03 | TST-03 | TEST EDILDI | mutasyon vakasi: TST-03 |
| `test_attest.py` | TST-04 | TST-04 | TEST EDILDI | mutasyon vakasi: TST-04 |
| `test_attest.py` | TST-05 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-06 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-07 | TST-07 | TEST EDILDI | mutasyon vakasi: TST-07 |
| `test_attest.py` | TST-08 | TST-08 | TEST EDILDI | mutasyon vakasi: TST-08 |
| `test_attest.py` | TST-09 | TST-09 | TEST EDILDI | mutasyon vakasi: TST-09 |
| `test_attest.py` | TST-10 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `test_attest.py` | TST-11 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `test_attest.py` | TST-12 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
