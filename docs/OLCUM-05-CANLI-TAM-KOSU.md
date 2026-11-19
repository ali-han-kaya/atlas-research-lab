# ÖLÇÜM-05 — KFAZ0→KFAZ5 İLK TAM CANLI KOŞU (FINAL PASS)

Tarih: 24 Ağustos 2026 · Sürücü: opencode 1.18.21 (operatör kabuğu) · Ajan modelleri: **denge** profili
Sürücü model: `openrouter/deepseek/deepseek-v4-flash` (KOD_SABLONLAR/opencode.json, v1.7.10)
Kaynak lab commit zinciri: `034b7eb` (v1.7.10) → `b95801a` (v1.7.11, koşu sırasında) → v1.7.12 (bu rapor)

---

## 1. Kurulum

- Hedef depo: sistem scratchpad'inde taze dizin (`…/T/opencode/olcum05/hedef-depo`), mtrx DIŞI.
- Ürün: `birim/hesap.py` (topla/cikar/carp/bol; sifira bolmede ZeroDivisionError) + `tests/test_hesap.py` (5 test) + boş `conftest.py`.
- Taban commit'ler: `cc3fd9b` (ürün+test), `9a94d69` (profil).
- `bash KOD_SABLONLAR/scripts/kur.sh <hedef>` **TEK koşu** (O5-04 disiplini): **7/7 OK, "KURULUM TAM", exit=0.**
  İkinci koşum yapılmadı; sonraki doğrulamalar yalnızca `--dogrula` (kopyalamaz) ile yapıldı — o da exit=0.
- `apply_routing.py denge --kuru`: "değişiklik yok — zaten bu profildesin"; ağaç temiz kaldı.

## 2. Profil kararları (kod_profil.json)

| Karar | Değer | Gerekçe |
|---|---|---|
| pytest | `pip3 install --user --break-system-packages` → **pytest 9.1.1** | makinede pytest yoktu (v1.7.9 denetimi); kullanıcı kararı: pip --user |
| test_komutu | `python3 -m pytest -q --junitxml=_KOSU/gate/junit.xml` | bare `pytest` PATH'te DEĞİL (`~/Library/Python/3.14/bin`); şablondan tek sapma, profilde belgelendi |
| bagimlilik_manifesti | `["pyproject.toml"]` (+ dosya oluşturuldu, `dependencies = []`) | DEP-06 P1'in önü kesildi; manifest diskte var |
| kilit_dosyasi | `[]` (BİLİNÇLİ beyan) | ürün yalnız stdlib → dep_audit **PASS P0=0 P1=0**, yalnız DEP-01 BILGI |
| v4_verify_yolu | lab toolkit mutlak yolu | secret_scan TAM mod şart (yoksa KISMI exit=3 = OLCULMEYEN); secret_scan **PASS 9 kalıp P0=0** |

Profil SHA256'sı KFAZ0'da tabana işlendi: `61d83f9768b6…` (BASELINE.json ↔ disk birebir doğrulandı).

## 3. Faz zinciri — komut, çıktı, exit

| Faz | Komut/Ajan | Deneme | Sonuç | Kanıt |
|---|---|---|---|---|
| KFAZ0 | `kos_faz.sh --komut kod-faz0 --ajan kod-scoper` | 2. istemle 1/1 | **exit=4 → exit=0** | `_KOSU/00-KFAZ-0-SPEC-CONTRACT-ve-REGISTER.md` + `_KOSU/gate/BASELINE.json` + junit.xml |
| KFAZ1 | kod-faz1 / kod-architect | 1/1 | exit=0 | `_KOSU/01-KFAZ-1-DESIGN-PLAN.md`; benim koşum: chg_reconcile PASS (P1=1 beklenen-KFAZ2), freeze exit=0 |
| KFAZ2 | kod-faz2 / kod-implementer | 1/1 | exit=0 | `_KOSU/02-KFAZ-2-CHANGE-MANIFEST.md`; diff yalnız tests +61 satır; benim pytest: **20/20** |
| KFAZ3 | kod-faz3 / kod-tester | 1/1 | exit=0 | `_KOSU/03-KFAZ-3-TEST-EVIDENCE.json`; benim test_attest: PASS P0=0 |
| KFAZ4 | kod-gate-2a ×2 tur + kod-gate-2b + merge | 2A ilk tur 3 deneme, ikinci tur 1/1 | **FINAL PASS** | `FINAL-KOD-GATE.json` 2-of-2, P0=0 P1=0 |
| KFAZ5 | kod-teslim / kod-orchestrator | 1/1 | exit=0 | `_KOSU/05-KFAZ-5-TESLIM.md` + commit taslağı |

### KFAZ0'daki ilk duruş (exit=4, K17 kapısı işledi)
Ajan gerçek çalıştı (JUnit'u kendisi üretti: 5/5) ama bağlam sözleşmesi gereği
"2 dosya yazayım mı? 1) evet 2) hayır" diye sordu; başsız koşuda cevap yok,
artefakt 0, `kos_faz.sh` exit=4 verdi. Çözüm operatör düzeyinde: isteme
"ONAY PEŞİNEN VERİLDİ, sorma" bloğu eklendi — sonraki tüm fazlarda aynı kalıp.

### RECK-07 ön-uçuş yakalaması
KFAZ1 öncesi chg_reconcile kaynağı okundu: her davranışsal REQ **tabanda olmayan**
test adı ister (:364). Mimarın planı bunu bilerek karşıladı: mevcut 5 test korunup
her REQ için yeni parametrize fonksiyonlar (`test_topla_param` …). Kapı temiz geçti.

## 4. O5-08 — FINAL'i garanti FAIL'e bağlayan yapısal bulgu (canlı)

İlk KFAZ4'te merge çıktısı:
```
IHLAL 2A: checks[5] (CHK-06) CALISTIRILMADI -> P1
IHLAL 2A: checks[6] (CHK-07) CALISTIRILMADI -> P1
IHLAL 2A: beyan p1_count=2 ama gercek=4
2-of-2 2A=FAIL(P0:0,P1:4) 2B=PASS(P0:0,P1:0) -> FAIL
```
Kök neden: kör kapı 2A'nın bash izin kümesi (O3-07 sertleştirmesi: yalnız
`git *`, `pytest`, `ls`) sözleşmenin betik-temelli yapısal REQ'lerinin
(REQ-006 `dep_audit.py`, REQ-007 `freeze_check.py`) kanıtını üretemiyor.
Ajan dürüstçe CALISTIRILMADI yazdı (checks ×2 + findings ×2 → merge gerçek sayı P1=4;
ajanın beyanı 2'ydi — aynı iki konunun çift listelenmesi). Katmanlı savunma doğru
çalıştı: sahte yeşil üretilmedi; ama bu sözleşme sınıfında FINAL'in FAIL'i yapısal.

**Düzeltme (lab v1.7.11, commit `b95801a`):** 2A bash listesine yalnız iki dar kalıp
eklendi: `"python3 scripts/dep_audit.py*": allow`, `"python3 scripts/freeze_check.py*": allow`
— iki betik de plan/manifest içeriği göstermez; kor denetim bozulmaz.
Batarya: kod_selftest **149/149** · atlas **62/62** · perm_lint 29 blok · prompt_lint 40/0 ·
check_models 23 ajan (5 bilinen uyarı) · toolkit 38 gecti (bilinen TUT-1).

Hedefe tek dosya senkron (SHA256 kaynak↔hedef birebir `36907427a0a9ea98…`; kur.sh İKİNCİ KEZ KOŞULMADI),
hedef perm_lint PASS. Taze 2A koşumu: **1. denemede exit=0, 7/7 checks GECTI** (CHK-06/07 dahil,
kanıt olarak kendi koştuğu iki betiğin çıktısı+exit'i), metadata p0=0 p1=0.

## 5. FINAL kanıtları (koşu sonrası bağımsız tekrar)

```
$ python3 scripts/kod_gate_merge.py _KOSU/gate/KOD-gate-2a.json _KOSU/gate/KOD-gate-2b.json
2-of-2 2A=PASS(P0:0,P1:0) 2B=PASS(P0:0,P1:0) -> PASS          # MERGE_EXIT=0
$ bash scripts/check_code_integrity.sh --full
CODE-INTEGRITY PASS — 1 uyari                                  # ITG_EXIT=0 (uyari: ITG-30 DONGU.json yok)
$ python3 scripts/freeze_check.py                              # FREEZE_EXIT=0
$ python3 scripts/test_attest.py                               # ATTEST_EXIT=0 (kosan=20 basarisiz=0 hata=0)
$ python3 scripts/dep_audit.py ; secret_scan.py ; chg_reconcile.py   # 0 / 0 (TAM) / 0
$ kur.sh <hedef> --dogrula                                     # 7/7 OK, exit=0
$ python3 -m pytest -q                                         # 20 passed
```

## 6. Teslim commitleri (operatör, onaylı)

- `9cfcd18` hijyen: taban commit `.gitignore` YOKKEN `git add -A` alındığı için 3 takipli `.pyc`
  girmişti (kurulum hatası — orchestrator bunu OLCULMEYEN'e yazıp kararı operatöre bıraktı);
  `git rm --cached` ile izden çıkarıldı.
- `780101a` ürün commit — orchestrator'ın taslak mesajı birebir kullanıldı.
- Son durum: takipli değişiklik 0 · pytest 20/20 · integrity --full PASS · freeze exit=0.

## 7. Dürüstlük listesi (ölçülemeyenler)

- **ITG-30:** `DONGU.json` yok — tek turluk akışta döngü bütçesi (KFAZ4→KFAZ2 dönüşü) test edilmedi.
- **2C koşmadı:** diff kimlik/ağ/kripto/bağımlılık yüzeyi taşımıyor → FINAL 2-of-2. Üçlü kapı bu koşuda ölçülmedi.
- `dis_imza`: api_surface kademe=T3 → 0 imza, DÜŞÜK_GÜVEN (BASELINE `olculmeyen` kaydı).
- `kapsam_yuzde`: null (coverage aracı yok — profil boş beyan, kapılar CALISTIRILMADI demedi çünkü alan opsiyonel).
- Maliyet: faz fiyat tablosuna göre tahmini **~$0.55** OpenRouter (KFAZ0 ×2 istem + 2A'nın ilk turunda 240s×2 askı denemesi dahil);
  **gerçek fatura bağımsız teyit edilmedi** (dış sorgu yapılmadı — beyan statüsünde).
- Bu pencerenin asistanı "ox-alpha" (Zen/'unlimited' adayı); sistem beyanı içeriden doğrulanamaz — ÖLÇÜM-05
  koşusu bilinen denge profiliyle sürüldü (tek değişken ilkesi korundu; ox alpha koşuya GİRMEDİ).
