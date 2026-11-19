# Mutasyon kapsami — tam kural envanteri

Kaynak: `tools/kapsam.py` (uretilmis dosya; elle duzenlenmez).
Envanter, ATLAS ve KOD kapi betiklerinin basliklarinda bildirdigi
kural kimlikleridir; `*_selftest.py` ve `OLCUM-*` referanslari sayilmaz.

Her kural icin tek soru sorulur: **mutasyon bataryasinda onu ateslettiren
bir vaka var mi?** Yoksa iki durumdan biri yazilir: gerekcesi olculmus
**KAPSAM DISI** ya da **BOSLUK**. Bosluk gizlenmez.

## Ozet

| Olcum | Deger |
|---|---|
| Kapi betigi | 20 |
| Bildirilen kural | 117 |
| Mutasyon vakasi olan (TEST EDILDI) | 43 |
| Gerekceli kapsam disi | 26 |
| Bosluk (gerekce yok) | 48 |
| — bunlardan yalniz oz-testte anilan | 17 |
| — hicbir testte gecmeyen | 31 |

## Kapsam disi siniflari

Gerekceler tahmin degil; her satir betigin kodundaki bagimliliga dayanir
(asagida betik adiyla birlikte yazili).

| Sinif | Gerekce (betikte olculen bagimlilik) | Betik | Kural |
|---|---|---|---|
| ag | requests ile api.crossref.org sorgusu; batarya agsiz kosar | verify_doi.py | 1 |
| depo-durumu | `git diff --name-only HEAD` ile degisen dosyalari okur | dep_audit.py | 6 |
| gizli-anahtar | HMAC anahtari ister (LAB_IMZA_ANAHTARI / ~/.config/lab_imza.key); anahtar depoya konmaz | teslim_imza.py | 6 |
| kosu-durumu | butun agacin selftest hash tabanini ve ham kosu ciktisini ister | api_surface.py, oztest_attest.py | 11 |
| tarihce | SURUM.md makine blogunu HEAD/commit hashleriyle karsilastirir | olgu_lint.py | 2 |

## Tam envanter

| Betik | Kural | Mutasyon vakasi | Durum | Gerekce |
|---|---|---|---|---|
| `check_models.py` | MOD-01 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `check_models.py` | MOD-02 | MOD-02 | TEST EDILDI | mutasyon vakasi: MOD-02 |
| `check_models.py` | MOD-03 | MOD-03 | TEST EDILDI | mutasyon vakasi: MOD-03 |
| `check_models.py` | MOD-04 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `check_models.py` | MOD-05 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `check_models.py` | MOD-06 | MOD-06 | TEST EDILDI | mutasyon vakasi: MOD-06 |
| `check_models.py` | MOD-07 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `check_models.py` | MOD-08 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `cite_match.py` | CITE-01 | CITE-01 | TEST EDILDI | mutasyon vakasi: CITE-01 |
| `cite_match.py` | CITE-02 | CITE-02 | TEST EDILDI | mutasyon vakasi: CITE-02 |
| `cite_match.py` | CITE-03 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
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
| `prompt_lint.py` | PL-12 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `prompt_lint.py` | PL-13 | PL-13 | TEST EDILDI | mutasyon vakasi: PL-13 |
| `prompt_lint.py` | PL-14 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `prompt_lint.py` | PL-16 | PL-16 | TEST EDILDI | mutasyon vakasi: PL-16 |
| `prompt_lint.py` | PL-18 | PL-18 | TEST EDILDI | mutasyon vakasi: PL-18 |
| `prompt_lint.py` | PL-19 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `quote_ratio.py` | QR-01 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `quote_ratio.py` | QR-02 | ATLAS-QR-02 | TEST EDILDI | mutasyon vakasi: ATLAS-QR-02 |
| `scope_profile_check.py` | SP-01 | SP-01 | TEST EDILDI | mutasyon vakasi: SP-01 |
| `scope_profile_check.py` | SP-02 | SP-02 | TEST EDILDI | mutasyon vakasi: SP-02 |
| `scope_profile_check.py` | SP-03 | SP-03 | TEST EDILDI | mutasyon vakasi: SP-03 |
| `scope_profile_check.py` | SP-04 | SP-04 | TEST EDILDI | mutasyon vakasi: SP-04 |
| `scope_profile_check.py` | SP-05 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `scope_profile_check.py` | SP-06 | SP-06 | TEST EDILDI | mutasyon vakasi: SP-06 |
| `scope_profile_check.py` | SP-07 | SP-07 | TEST EDILDI | mutasyon vakasi: SP-07 |
| `source_class_check.py` | SRC-01 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
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
| `chg_reconcile.py` | RECK-01 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `chg_reconcile.py` | RECK-02 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `chg_reconcile.py` | RECK-03 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `chg_reconcile.py` | RECK-04 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `chg_reconcile.py` | RECK-05 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `chg_reconcile.py` | RECK-06 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `chg_reconcile.py` | RECK-07 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `chg_reconcile.py` | RECK-08 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `chg_reconcile.py` | RECK-09 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `dep_audit.py` | DEP-01 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-02 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-03 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-04 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-05 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `dep_audit.py` | DEP-06 | — | KAPSAM DISI | depo-durumu: `git diff --name-only HEAD` ile degisen dosyalari okur |
| `freeze_check.py` | FRZ-01 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `freeze_check.py` | FRZ-02 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `freeze_check.py` | FRZ-03 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `freeze_check.py` | FRZ-04 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `freeze_check.py` | FRZ-05 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `freeze_check.py` | FRZ-06 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `freeze_check.py` | FRZ-07 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `perm_lint.py` | PERM-01 | KOD-PERM-01 | TEST EDILDI | mutasyon vakasi: KOD-PERM-01 |
| `perm_lint.py` | PERM-02 | PERM-02 | TEST EDILDI | mutasyon vakasi: PERM-02 |
| `perm_lint.py` | PERM-03 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `perm_lint.py` | PERM-04 | PERM-04 | TEST EDILDI | mutasyon vakasi: PERM-04 |
| `perm_lint.py` | PERM-05 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `perm_lint.py` | PERM-06 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `perm_lint.py` | PERM-07 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `perm_lint.py` | PERM-08 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `secret_scan.py` | SEC-01 | SEC-01 | TEST EDILDI | mutasyon vakasi: SEC-01 |
| `secret_scan.py` | SEC-02 | KOD-SEC-02 | TEST EDILDI | mutasyon vakasi: KOD-SEC-02 |
| `secret_scan.py` | SEC-03 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `secret_scan.py` | SEC-04 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `secret_scan.py` | SEC-05 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `test_attest.py` | TST-01 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-02 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-03 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-04 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `test_attest.py` | TST-05 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-06 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-07 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-08 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-09 | — | BOSLUK | BOSLUK — hicbir testte gecmiyor |
| `test_attest.py` | TST-10 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `test_attest.py` | TST-11 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
| `test_attest.py` | TST-12 | — | BOSLUK | BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok |
