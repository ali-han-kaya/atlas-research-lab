# Mutasyon kapsami — olculmus

Kaynak: `tools/kapsam.py` (uretilmis dosya; elle duzenlenmez).
Envanter, kapi betiklerinin basliklarinda bildirdigi kural
kimlikleridir; `*_selftest.py` ve `OLCUM-*` referanslari sayilmaz.

## Ozet

| Olcum | Deger |
|---|---|
| Kapi betigi | 20 |
| Bildirilen kural | 117 |
| Mutasyonla ateslenen | 5 |
| Yalniz oz-testte gecen | 61 |
| Hicbir testte gecmeyen | 51 |

**Okuma:** "mutasyonla ateslenen", bataryanin temiz taban + tek
ihlal + kirmizi huküm ucluyle o kurali gercekten kosturdugu
anlamina gelir. "Yalniz oz-testte gecen" kural, bir testte
anilir ama ihlalde atesledigi ayri bir mutasyonla kanitlanmamis
demektir; "hicbir testte gecmeyen" ise hicbir kaniti olmayan
kuraldir.

## GATE_TAMPERED — kritik kural

| Betik | Kural | Durum |
|---|---|---|
| `freeze_check.py` | FRZ-01 | HIC TEST YOK |
| `freeze_check.py` | FRZ-02 | yalniz oz-test |

`GATE_TAMPERED` bir kural degil bir koddur; onu ureten
kurallar yukaridadir. Mutasyon bataryasinda bu betik icin
vaka yoktur; KOD oz-testi bu davranisi ayri fiksturlerle
kilitler. Fark kapatilmadikca tablo bunu gizlemez.

## Betik bazinda

| Kapi betigi | Kural | Mutasyon | Yalniz oz-test | Hic test yok |
|---|---|---|---|---|
| `check_models.py` | 8 | — | MOD-03, MOD-08 | MOD-01, MOD-02, MOD-04, MOD-05, MOD-06, MOD-07 |
| `cite_match.py` | 3 | — | CITE-01, CITE-02, CITE-03 | — |
| `declaration_check.py` | 7 | DEC-03 | DEC-02, DEC-04, DEC-05, DEC-06, DEC-07 | DEC-01 |
| `fix_reconcile.py` | 6 | — | REC-01, REC-02, REC-03, REC-04, REC-05, REC-06 | — |
| `olgu_lint.py` | 2 | — | OLGU-05, OLGU-06 | — |
| `oztest_attest.py` | 6 | — | OZT-01, OZT-02, OZT-03, OZT-05, OZT-06 | OZT-04 |
| `prompt_lint.py` | 12 | PL-10 | PL-04, PL-09, PL-11, PL-13, PL-18 | PL-01, PL-02, PL-12, PL-14, PL-16, PL-19 |
| `quote_ratio.py` | 2 | QR-02 | QR-01 | — |
| `scope_profile_check.py` | 7 | — | SP-01, SP-02, SP-04, SP-06, SP-07 | SP-03, SP-05 |
| `source_class_check.py` | 3 | — | SRC-02, SRC-03 | SRC-01 |
| `teslim_imza.py` | 6 | — | TSL-01, TSL-02, TSL-03, TSL-04, TSL-05, TSL-06 | — |
| `translit_check.py` | 2 | — | TR-01, TR-02 | — |
| `verify_doi.py` | 1 | — | DEC-027 | — |
| `api_surface.py` | 5 | — | — | API-01, API-02, API-03, API-04, API-05 |
| `chg_reconcile.py` | 9 | — | RECK-03, RECK-06, RECK-07, RECK-08, RECK-09 | RECK-01, RECK-02, RECK-04, RECK-05 |
| `dep_audit.py` | 6 | — | DEP-01 | DEP-02, DEP-03, DEP-04, DEP-05, DEP-06 |
| `freeze_check.py` | 7 | — | FRZ-02, FRZ-03, FRZ-06, FRZ-07 | FRZ-01, FRZ-04, FRZ-05 |
| `perm_lint.py` | 8 | PERM-01 | PERM-02 | PERM-03, PERM-04, PERM-05, PERM-06, PERM-07, PERM-08 |
| `secret_scan.py` | 5 | SEC-02 | SEC-05 | SEC-01, SEC-03, SEC-04 |
| `test_attest.py` | 12 | — | TST-04, TST-10, TST-11, TST-12 | TST-01, TST-02, TST-03, TST-05, TST-06, TST-07, TST-08, TST-09 |
