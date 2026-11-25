# Rule catalogue — generated from code

**This file is generated; do not edit it by hand.**
Source: `tools/kural_katalogu.py` (gate scripts + `tools/mutasyon_sonuc.json`).
Refresh: `make katalog-kurallar` · Staleness check: `make katalog-kurallar-kontrol` (CI).

## What is counted — and what is not

| Measure | Value | Where it comes from |
|---|---|---|
| Gate scripts scanned | 31 | `kapsam.DIZINLER` |
| Identifiers reported in source | 121 | line-start and `# --- ID` section headers |
| — rules in the inventory | 117 | after excluding dead identities and references |
| — firing-tested (HATA/TERMINAL) | 93 | mutation case turns the gate red |
| — expected-finding-only | 24 | case emits a marker, gate stays green |
| — dead identities (excluded) | 4 | declared but no code branch ever prints them |
| — external references (excluded) | 1 | a decision id, not a rule |
| Out-of-scope rules with a measured reason | 0 | `KAPSAM_DISI` (currently empty) |
| Gaps (no reason, no case) | 0 | must stay 0 |

A rule is a rule only if some code branch can emit it. An identifier that
is merely *declared* in a header is not a gate: it cannot turn red, so it
cannot protect anything. Those are listed separately with a reason rather
than being counted as covered.

**Evidence is a run, not a definition.** `Firing-tested` in the tables below
comes from the last real battery run recorded in `tools/mutasyon_sonuc.json`
(freshness: source SHA-256 of the battery and every gate script). If the
evidence is missing or stale, the status reads `KANITSIZ` instead of a pass.

Evidence state for this generation: **fresh**.

## Architecture: how a violation travels

```text
1. gate scripts           ATLAS_SABLONLAR/scripts + KOD_SABLONLAR/scripts
2. mutation battery       tools/mutasyon_bataryasi.py
3. run evidence           tools/mutasyon_sonuc.json
4. scope                  tools/kapsam.py
5. single entry gate      tools/dogrula.py
6. claim ledger           tools/iddia.py
7. tree attestation       tools/kanit.py + attestation.json
```

| Layer | Artifact | What it does |
|---|---|---|
| gate scripts | `ATLAS_SABLONLAR/scripts + KOD_SABLONLAR/scripts` | Each rule is declared in one script and emits rc=1 (error) or rc=2 (terminal). |
| mutation battery | `tools/mutasyon_bataryasi.py` | Silent clean baseline, one violation, then undo; every case also checks label leakage and that the gate turns green again. |
| run evidence | `tools/mutasyon_sonuc.json` | Per-case outcome of the last real run; coverage status is derived from it. |
| scope | `tools/kapsam.py` | Inventory, severity and evidence; a ratchet pins the tested/gap counts. |
| single entry gate | `tools/dogrula.py` | H1..H5 hygiene and secrets plus T1..T3 self-tests; eight checks, raw output printed. |
| claim ledger | `tools/iddia.py` | Every numeric claim in the public docs is re-measured by running its command. |
| tree attestation | `tools/kanit.py + attestation.json` | Commit/tree SHA-256; the entry gate recomputes it (KANIT-06). |

A single violation therefore has to survive four independent questions:
does the gate fire (rc/marker), does only *its* label fire (no leakage),
does the clean baseline stay silent, and does undoing it turn the gate
green again. The battery asks all four for every case.

## The 117 rules, by gate script

Status legend: **firing** = a HATA/TERMINAL case turns the gate red;
**expected** = the case emits the expected marker and the gate stays green;
`KANITSIZ` = a case exists but the last run produced no fresh evidence.

### `ATLAS_SABLONLAR/scripts/check_models.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| MOD-01 | — | `model:` satiri var (yoksa UYARI: global varsayilana duser) | expected |
| MOD-02 | — | Saglayici yetkili (auth.json ile ayni kume) | firing |
| MOD-03 | — | Model katalogda VAR | firing |
| MOD-04 | — | `deprecated` degil (opencode bunu otomatik disable eder) | firing |
| MOD-05 | — | reasoning=true ve tool_call=true | firing |
| MOD-06 | — | '~' takma adi kullanilmiyor (hareketli hedef, yeniden uretilemez) | firing |
| MOD-07 | — | Prompt govdesindeki model adi frontmatter ile celismiyor | expected |
| MOD-08 | — | Symlink hedefi kirik veya denetim koku disindaysa reddedilir | firing |

### `ATLAS_SABLONLAR/scripts/cite_match.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| CITE-01 | — | Metinde anilan her kaynak kaynakcada var (eksik kaynak) | firing |
| CITE-02 | — | Kaynakcadaki her girdi metinde en az bir kez anilir (oksuz kaynak) | firing |
| CITE-03 | — | Ayni soyad icin celisen yil kullanimi (UYARI) | expected |

### `ATLAS_SABLONLAR/scripts/declaration_check.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| DEC-01 | — | Etik Kurul / Ethics Committee — numara veya "gerekmedi" gerekcesi | firing |
| DEC-02 | — | Cikar Catismasi / Conflict of Interest | firing |
| DEC-03 | — | Finansman / Funding | firing |
| DEC-04 | — | Yazar Katkisi / CRediT / Author Contributions | firing |
| DEC-05 | — | Veri/Materyal Erisilebilirligi / Data Availability | firing |
| DEC-06 | — | YZ Kullanimi Beyani / AI Use Disclosure (emanet geregi) | firing |
| DEC-07 | — | DPIA — kosullu: kisisel veri isleniyorsa ZORUNLU, yoksa gerekceli N/A | firing |

### `ATLAS_SABLONLAR/scripts/fix_reconcile.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| REC-01 | — | FAZ1 bulgu sayisi == FAZ2 FIX sayisi | firing |
| REC-02 | — | P0/P1 dagilimi FAZ1 ile FAZ2 arasinda ayni | firing |
| REC-03 | — | Her FAZ1 bulgu ID'si FAZ2 metninde geciyor (izlenebilirlik) | firing |
| REC-04 | — | "UYGULANMIS" ilan edilen her FIX-ID MASTER metninde gorunur | firing |
| REC-05 | — | gate 2B'de "KANITLI" denen her fix_id MASTER metninde gorunur | firing |
| REC-06 | — | MASTER'da gecen her FIX-ID manifestoda tanimli (hayalet kanit yok) | firing |

### `ATLAS_SABLONLAR/scripts/olgu_lint.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| OLGU-04 | — | , yalniz bu kamu agacinin `attestation.json` kanitini kullanir ve | firing |
| OLGU-05 | — | , verilen ATLAS/attest/KOD ciktilarindaki sayilari kanonik kayitla | firing |
| OLGU-06 | — | , son kanonik DEVIR'den sonraki mekanizma commit hash'lerinin bicimsel | firing |

### `ATLAS_SABLONLAR/scripts/oztest_attest.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| OZT-01 | P0 | taban dosyasi yok / bozuk -> kapi ACILMAZ (fail-closed) | firing |
| OZT-02 | P0 | tabandaki kimlik bu kosuda YOK -> test SILINMIS | firing |
| OZT-03 | P0 | kosuda hicbir test yok -> sifir test "temiz" degildir | firing |
| OZT-05 | P1 | tabanda olmayan YENI kimlik var -> taban guncellenmeli | expected |
| OZT-06 | P0 | taban kimlik_hash'i kendi listesiyle tutmuyor -> taban kurcalanmis | firing |

### `ATLAS_SABLONLAR/scripts/prompt_lint.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| PL-01 | — | Frontmatter var ve description tasiyor | firing |
| PL-02 | — | mode kapali listede (primary\|subagent\|all) | firing |
| PL-04 | — | Symlink hedefi repo koku icinde | firing |
| PL-09 | — | FAZ1 lensleri KARAR VERMEZ (verdict/gate_decision alani yasak) | firing |
| PL-10 | — | "kanit GEREKMEZ" tarzi vacuous-PASS muafiyeti yok | firing |
| PL-11 | — | "her zaman PASS" tarzi kalici muafiyet yok | firing |
| PL-12 | — | Belirsizlik cikisi var (DOGRULANAMADI\|CALISTIRILMADI\|NOT_EXECUTED\|UNKNOWN) | expected |
| PL-13 | — | Belirsizlik etiketi yasaklanmiyor ("etiketlerini birakma" kalibi) | firing |
| PL-14 | — | Betik cagiran ajan exit kodundan soz ediyor (fail-closed) | expected |
| PL-16 | — | Cagirilan scripts/*.py gercekten var | firing |
| PL-18 | — | Symlink kirik degil | firing |
| PL-19 | — | Eslenmis promptun JSON alanlari hedef semanin required/properties alanlariyla uyumlu | firing |

### `ATLAS_SABLONLAR/scripts/provenance_check.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| CHK-01 | — | her ZORUNLU ID bir MARKDOWN BASLIGINDA var mi? | firing |
| CHK-02 | — | her ZORUNLU ID provenance tablosunda "kapsiyor" (veya DEC-027 | firing |
| CHK-05 | — | Baslik benzersizligi | expected |

### `ATLAS_SABLONLAR/scripts/quote_ratio.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| QR-01 | — | Alinti orani = alinti_karakteri / govde_karakteri (bilgi/harici karsilastirma yok) | expected |
| QR-02 | — | 40+ kelimelik her alintida bitisik atif + ayni atifta sayfa no (eksikse P0) | firing |

### `ATLAS_SABLONLAR/scripts/scope_profile_check.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| SP-01 | P0 | `ALAN_PROFILI:` beyani var ve kapali listede | firing |
| SP-02 | P0 | Profil disi ZORUNLU SC-ID yok (or. filolojik profilde Null Model) | firing |
| SP-03 | P0 | Profilin ORTAK zorunlulari eksiksiz | firing |
| SP-04 | P0 | Profile ozgu 4 yuva (SC-002/007/009/010) ZORUNLU olarak var | firing |
| SP-05 | P1 | SC-017 DPIA ZORUNLU ise kisisel veri beyani var | expected |
| SP-06 | P0 | ZORUNLU SC-ID hic bulunamadi (vacuous PASS kapali) | firing |
| SP-07 | P0 | Gerekli tablo basliklari eksiksiz ve benzersiz | firing |

### `ATLAS_SABLONLAR/scripts/source_class_check.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| SRC-01 | — | PROVENANCE tablosunda Kaynak Sinifi sutunu var mi? (yoksa CALISTIRILMADI) | firing |
| SRC-02 | — | Her satirda sinif degeri gecerli mi? BIRINCIL\|IKINCIL\|UCUNCUL\|AKTARMA (bos/yanlis P1) | firing |
| SRC-03 | — | AKTARMA satirlarinda "asil kaynak gorulmedi" beyanı var mi? (yoksa P1) | firing |

### `ATLAS_SABLONLAR/scripts/teslim_imza.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| TSL-01 | P0 | manifest yok / bozuk -> kapi ACILMAZ (fail-closed) | firing |
| TSL-02 | P0 | manifestte listelenen dosya diskte YOK | firing |
| TSL-03 | P0 | dosya sha256'si manifesttekiyle tutmuyor -> TAHRIFAT | firing |
| TSL-04 | P0 | imza var ama GECERSIZ -> manifest tahrif edilmis / baska anahtar | firing |
| TSL-05 | — | ile DUSUK_GUVEN (P1) der ve kapiyi KAPATMAZ — mevcut teslimler kirilmaz. | expected |
| TSL-06 | P0 | ZORUNLU teslim artefakti manifestte hic yok -> kapsam eksigi | firing |

### `ATLAS_SABLONLAR/scripts/translit_check.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| TR-01 | — | SCOPE'ta transliterasyon sistemi ilan edilmis mi? (yoksa P1) | firing |
| TR-02 | — | MASTER'da ayni kavram icin birden fazla farkli yazim var mi? | firing |

### `KOD_SABLONLAR/scripts/api_surface.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| API-01 | — | KFAZ0 envanteri yok [CALISTIRILMADI P1] | expected |
| API-02 | P0 | T1: kaybolan disa acik imza | firing |
| API-04 | — | T2: regex taramasinda kayip aday [DUSUK_GUVEN P1] | expected |
| API-05 | — | T3: hicbir kademe kosmadi [CALISTIRILMADI P1] | expected |

### `KOD_SABLONLAR/scripts/chg_reconcile.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| RECK-01 | P0 | KFAZ0'daki her REQ, KFAZ1 planinda karsiligini bulur | firing |
| RECK-02 | P0 | "UYGULANMIS" her CHG'nin dosyasi `git diff`te | firing |
| RECK-03 | — | Diff'teki her URUN dosyasi planda var [SCOPE_VIOLATION P0] | firing |
| RECK-04 | P0 | 2B kapisinin iddia ettigi her CHG diff'te | firing |
| RECK-05 | P0 | Hayalet CHG yok (olmayan REQ'e / plansiz dosyaya baglanmis) | firing |
| RECK-06 | P0 | Dondurulmus bolge diff'te GORUNMEZ | firing |
| RECK-07 | P0 | Davranissal her REQ, TABANDA OLMAYAN bir test adina eslenir | firing |
| RECK-08 | — | Makine bloklarinin ALAN BICIMI semaya uyar [SCHEMA_INVALID P0] | firing |
| RECK-09 | — | KFAZ0'da (plan oncesi) URUN kodu diff'te GORUNMEZ | firing |

### `KOD_SABLONLAR/scripts/dep_audit.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| DEP-01 | P0 | Manifest var, kilit ANAHTARI YOK | firing |
| DEP-03 | P1 | Sabitlenmemis surum (`*`, `latest`, bos, `^`/`~` kilitsiz) | expected |
| DEP-04 | P1 | Diff kilit dosyasina dokunuyor ama manifeste dokunmuyor | expected |
| DEP-05 | P0 | Lisans catismasi (izinli listenin disinda) | firing |
| DEP-06 | — | Profilde `bagimlilik_manifesti` bos [CALISTIRILMADI P1 + OLCULMEYEN] | expected |

### `KOD_SABLONLAR/scripts/freeze_check.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| FRZ-01 | — | `kod_profil.json` SHA256 tabandan farkli [GATE_TAMPERED P0 TERMINAL] | firing |
| FRZ-02 | — | Kapi betigi (scripts/*.py\|sh) SHA256 farkli [GATE_TAMPERED P0 TERMINAL] | firing |
| FRZ-03 | P0 | KFAZ1'de dondurulan dosya degismis | firing |
| FRZ-04 | P0 | Tabanda kayitli dosya artik yok | firing |
| FRZ-05 | — | BASELINE.json yok / okunamiyor [CALISTIRILMADI P1 + OLCULMEYEN] | firing |
| FRZ-06 | — | BASELINE.json SEMASI eksik [CALISTIRILMADI P0 — FAIL-CLOSED] | firing |
| FRZ-07 | — | Taban KIRLI agacta olculmus (`temiz_agac`: false) | firing |
| FRZ-08 | — | IMZALI TABAN (C4, TUR-8 WP4) | firing |

### `KOD_SABLONLAR/scripts/perm_lint.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| PERM-01 | P0 | Olu kural yok: her kural kendi ornek yolunda kendi kararini kazanir | firing |
| PERM-02 | P0 | Cift kalip: her deny hem kok hem ic ice yolu kapsar (IK-1) | firing |
| PERM-03 | P1 | `**/*.uzanti` kalibi kok seviyeyi kacirir (IK-4) | expected |
| PERM-04 | P0 | ACILMAZ cizgesi read'te deny ise edit'te de deny (tek yonlu; politika) | firing |
| PERM-05 | P2 | Yalniz `{"*": "deny"}` iceren harita dize bicimiyle yazilmali (IK-5) | expected |
| PERM-06 | P1 | Kritik sinir `ask`e birakilmamis (IK-6: --auto ask'i allow yapar) | expected |
| PERM-07 | P1 | Yol kalibi mutlak degil, worktree'ye goreli (IK-7) | expected |
| PERM-08 | P1 | `bash` deny'i tek basina sinir degildir — asilabilir (IK-8) | expected |

### `KOD_SABLONLAR/scripts/secret_scan.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| SEC-01 | P0 | Gercek `.env` dosyasi diff'te | firing |
| SEC-02 | P0 | Eslesen sir kalibi (yer tutucu ipucu tasisa bile DUSURULMEZ) | firing |
| SEC-03 | — | Yer tutucu ipucu tasiyan eslesme [P1 + insan karari] | expected |
| SEC-05 | bilgi | TAM `__pycache__` dizinindeki .pyc kapsam disi | expected |

### `KOD_SABLONLAR/scripts/test_attest.py`

| Rule | Severity | What it checks | Status |
|---|---|---|---|
| TST-01 | P0 | basarisiz = 0 | firing |
| TST-02 | P0 | hata = 0 | firing |
| TST-03 | P0 | kosan >= 1 (sifir test "temiz" degildir) | firing |
| TST-04 | P0 | kosan >= taban.kosan (test SILINEREK yesil yapilamaz) | firing |
| TST-05 | P0 | atlanan <= taban.atlanan (test ATLANARAK yesil yapilamaz) | firing |
| TST-06 | P1 | kapsam >= taban.kapsam - 1 | expected |
| TST-07 | — | TEST-EVIDENCE.json beyani ham raporla celisiyor [EVIDENCE_UNVERIFIED P0] | firing |
| TST-08 | — | rapor dosyasi yok / bos / ayristirilamiyor [EVIDENCE_UNVERIFIED P0] | firing |
| TST-09 | P0 | test komutunun cikis kodu kayitli degil | firing |
| TST-10 | — | rapor KAYNAKTAN ESKI (bayat kanit) [STALE_EVIDENCE P0] | firing |
| TST-11 | — | kanittaki `komut` kod_profil.test_komutu ile ayni degil [EVIDENCE_UNVERIFIED P0] | firing |
| TST-12 | — | kanittaki `rapor` kod_profil.test_raporu ile ayni degil [EVIDENCE_UNVERIFIED P0] | firing |

## Excluded: declared but no code branch emits them

These identifiers appear in a `KURALLAR` header or a `# --- ID` section
title, but no branch prints them. A mutation cannot fire what does not
exist, so counting them as covered would inflate the rule count.

| Identity | Script | Why it is not counted |
|---|---|---|
| OZT-04 | `oztest_attest.py` | Kaldirilmis sayac kurali. Baslikta yalniz "OZT-04 NICIN YOK" aciklamasi olarak gecer; kodda bu kimligi basan dal yok. Kimlik sayisi dususu zaten OZT-02 ile yakalanir. |
| API-03 | `api_surface.py` | Baslikta "imza degismis (parametre/donus) [P0]" diye bildirilir ama api_surface yalniz kayip imza (API-02) ve regex adayi (API-04) dallarini uygular; imza degisimi karsilastirmasi kodda yok. |
| DEP-02 | `dep_audit.py` | Baslikta "Manifestteki paket kilitte yok [P0]" diye bildirilir ama dep_audit kodunda kilit paketlerini manifestle karsilastiran dal yok; yalniz DEP-01/03/04/05/06 dallari uygulanir. |
| SEC-04 | `secret_scan.py` | Baslikta "Ikili/kilit dosyasi atlandi [bilgi]" diye bildirilir ama hiçbir dal bu kimligi basmiyor; atlanan dosyalar yalniz sayilir, kimlikli BILGI satiri uretilmez. |

External references — a decision id used by a gate, not a rule it applies:

| Identity | Script | Why it is not a rule |
|---|---|---|
| DEC-027 | `verify_doi.py` | DEC karar kimligi; verify_doi bu kurali uygulamaz, DEC-027 bolum-farkindaligi politikasina atif yapar |

## Why the rest are not "tested" in the strong sense

The 24 expected-finding rules have a case, but their contract is a marker,
not a red verdict: the gate deliberately stays green and reports a warning.
They are listed as `expected` above and are **not** counted as firing-tested.

Two further limits, stated so they are not mistaken for coverage:

- A rule text is only as good as the fixture. `CITE-01` once *replaced* a
  citation and thereby leaked `CITE-02`; the fixture was narrowed until only
  its own label fired. Leakage is now checked on every case, so this class of
  mistake fails the battery instead of hiding in it.
- `BEKLENEN BULGU` cases prove the gate *sees* the condition; they do not prove
  the resulting warning is the right one for a human reader.

## Measured, not assumed

| Command | Output |
|---|---|
| `make mutasyon` | `SONUC: 113/113 kural atesledi · 27/27 beklenen bulgu · taban temiz olmayan=0` |
| `make kapsam` | `ratchet PASS (test=93/93, bosluk=0/0)` |
| `make dogrula` | `kalem=8 · gecen=8 · kalan=0` |

Raw per-case status, contracts and rationales live in
[`MUTASYON_KAPSAM.md`](MUTASYON_KAPSAM.md) (scope) and
[`../tools/mutasyon_sonuc.json`](../tools/mutasyon_sonuc.json) (run evidence).

