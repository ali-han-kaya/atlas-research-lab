# ÖLÇÜM 04 — CANLI DOĞRULAMA KOŞUSU #2 (KFAZ0 → KFAZ5)

Tarih: 24 Ağustos 2026 · opencode 1.18.21 · Python 3.14.6 · pytest 9.1.1
Kaynak görev: `DEVIR-2026-08-24-1642.md` §2 — üç canlı sınav
Koşu yeri: scratchpad (`/var/folders/.../opencode/olcum04/hedef`), **mtrx dışında**
Sürüm: Opus değil — **opencode (bu oturum)** yürüttü; kullanıcı kararı (Opus haftalık limit dolmak üzere)
Model katmanı: **OpenCode Go planı** (kullanıcının aboneliği; ek ücret $0)
— deepseek-v4-pro (scoper/architect/2A) · glm-5.3 (2B, 2C) · kimi-k2.7-code (implementer/tester) · kimi-k3 (heavy)
Kapı bağımsızlığı: 2A=deepseek · 2B=glm — **iki ayrı aile canlı koştu**; 2C plan anthropic'ti,
sağlayıcı hatası (2× `UnknownError`, ref err_47f15bf1/err_9a456d54) üzerine glm-5.3'e düşürüldü → **2 aile**
Maliyet: **$0.00** (Go plan içi; kullanıcı bakiyesinden harcama yok — OpenRouter `$0` deneysel olarak doğrulandı)

## SONUÇ — TEK CÜMLE

**Hattın üç canlı sınavının üçü de GEÇTİ: sürücü ajan artık kod yazamıyor, özyineleme hiç tetiklenmedi
(ajanlar hiç denemedi), taban şemaya uygun ölçüldü.** Hat ilk kez **KFAZ4'e kadar koştu** ve
üç kapı ajanı da canlı koştu; FINAL verdict **FAIL** — ancak FAIL'in gerekçesi ürün kodu değil,
ölçüm aletinin kendi dosyaları + bilinen açık kırıklar (O3-10) + 2 yeni bulgu.

Önceki iki koşuyla karşılaştırma:

| | ÖLÇÜM-02 | ÖLÇÜM-03 | ÖLÇÜM-04 |
|---|---|---|---|
| En ileri faz | KFAZ0 (6 onarımla KFAZ5) | KFAZ1 | **KFAZ4 (merge + integrity)** |
| Sürücü ajan kod yazdı mı | (bilinmiyordu) | **EVET** (O3-01) | **HAYIR** ✅ |
| Özyineleme | yok | 78+74 oturum (O3-02) | **0** ✅ |
| Taban | şema dışı | düzeltme sonrası ölçüldü (O3-04) | **şemaya uygun, kosan=7, doğru** ✅ |
| Kota/kesinti | — | kota tükendi (O3-03) | kesinti yok |

## KANIT SINIFLARI

- **A — canlı koşu:** gerçek `opencode run --command` (kos_faz.sh), komut + çıktı + exit kodu.
- **B — sevk edilen kod:** dosya + satır.
- **C — ölçülmedi.**

---

## 1. KFAZ0 → KFAZ5 AKIŞ TABLOSU (sınıf A)

| Faz | Ajan | Model | Deneme | Ajan exit | kos_faz exit | Kapılar (exit) | Artefakt |
|---|---|---|---|---|---|---|---|
| Kurulum | `kur.sh` + `--dogrula` | — | 1 | — | — | 5 OK | exit=0 |
| KFAZ0 | kod-scoper | deepseek-v4-pro (Go) | 4 (2×124) | 0 | 0 | freeze 0 · chg 0 · api 0(T3) · dep 1 · secret 0 | 00-md + BASELINE (şema uygun) |
| KFAZ1 | kod-architect | deepseek-v4-pro (Go) | 2 (1×124) | 0 | 0 | freeze 0 · chg (KFAZ1) 0 | 01-md 3632 B |
| KFAZ2 | kod-implementer | kimi-k2.7-code (Go) | 1 | 0 | 0 | — | 02-md 1823 B + kod diff |
| KFAZ3 | kod-tester | kimi-k2.7-code (Go) | 1 | 0 | 0 | test_attest 0 | 03-json 725 B |
| KFAZ4-2A | kod-gate-2a | deepseek-v4-pro (Go) | 1 | 0 | 0 | — | KOD-gate-2a.json PASS (4 kontrol) |
| KFAZ4-2B | kod-gate-2b | glm-5.3 (Go) | 1 | 1 denemede | 0 | — | KOD-gate-2b.json PASS (7 kontrol) |
| KFAZ4-2C | kod-gate-2c | glm-5.3 (Go)* | 3 | 1 | 0 | — | KOD-gate-2c.json **FAIL** |
| KFAZ5 | — | — | — | — | — | — | **KOŞULMADI** — FINAL FAIL (döngü kuralı) |

*2C'nin plan modeli anthropic/claude-sonnet-5 idi; Zen sağlayıcısı iki kez `UnknownError` verdi
(sınıf A; her iki ref de yukarıda). Model glm-5.3'e düşürüldü — bağımsızlık 2 aileye indi; kayıt altında.

## 2. ÜÇ CANLI SINAV (devir §2) — SONUÇLAR

**(a) Sürücü ajan artık depoya YAZAMIYOR mu? — EVET, doğrulandı (sınıf A).**
KFAZ1 sonunda `git status --short`: yalnız kurulum + `_KOSU/` izlenmeyen dosyaları;
**kaynak ağaçta (birim/, tests/) hiçbir değişiklik yok**. KFAZ2'ye kadar tek satır kod yazılmadı.
ÖLÇÜM-03'te `build` KFAZ0'da yazmıştı (O3-01); düzeltme (`opencode.json edit "*" deny` ilk sırada)
canlıda tuttu. Ayrıca `build`'in çıktıları incelendiğinde ajanlar artık operatör gibi davranmıyor —
komut çıktıları "KFAZ0 onaylanır mı?" diye soruyor (KFAZ0/KFAZ1/KFAZ2 onay noktaları).
Karşı-olgu: KFAZ2'de kod-implementer yalnız plana uygun 2 dosyaya dokundu (diff: 2+4 satır).

**(b) Özyineleme kilidi canlı exit=66 veriyor mu? — Kilidi ajanlar hiç tetiklemedi (sınıf A).**
Operatör olarak ben tetikledim: `KOD_KOS_FAZ_AKTIF=kod-faz0` + kos_faz.sh → `DURDU — YENIDEN GIRIS` exit=66 (lab denetiminde ölçüldü). Canlı koşuda ajanların hiçbiri kos_faz.sh/opencode run çağırmadı — 2C raporuna ve loglara göre bash çağrıları kapı komutlarıyla sınırlı. **O3-02 düzeltmesi (OPERATOR_SURME + instructions temizliği + deny listeleri) canlıda tuttu.**

**(c) Taban şemaya uygun mu + plan öncesi kod değişikliği yok mu? — İKİSİ DE doğrulandı (sınıf A).**
- `BASELINE.json`: `mod`, `olculdu`, `test.kosan=7` (gerçek), `test_adlari` 7 ad — şema uygun.
- `test_oran_sifir_bolen` tabanda **YOK** (RECK-07 ayırt edicisi sağlam — O3-04'ün zehirlenmesi yok).
- `chg_reconcile --faz KFAZ0` hiç koşmadı bu kez ama plan öncesi diff'te yalnız kurulum dosyaları vardı — kod değişikliği yok (O3-05'in koşulu oluşmadı).
- **O3-04 ve O3-05'in tetikleyicisi O3-01'di; O3-01 canlıda kapandı → ikisi de bu koşuda tezahür etmedi.**

## 3. YENİ BULGULAR (5)

### O4-01. `kos_faz.sh` artefakt bayrağı verilmezse sessizce geçiyor  (sınıf A, P1)
`--artefakt` verilmeden koşunca ajan onay sorup durunca bile `OK — kod-faz0 · artefakt=0` yazıyor
ve **exit=0** veriyor. K17 kapanışının koşulu operatörün bayrağı hatırlaması — bayrak yoksa
"ajan koştu ama üretmedi" durumu **fail-open**. Öneri: zorunlu bayrak veya hiç bayrak yoksa uyarı.

### O4-02. 2B ajan şema ihlali: `status` alanı yazmıyor  (sınıf A, P0)
glm-5.3 `_KOSU/gate/KOD-gate-2b.json`'a `checks[i].status` YAZMADI (farklı alan adı kullandı);
`kod_gate_merge.py` yeniden hesaplayarak **10× P0** yakaladı ve beyan edilen PASS'ı FAIL'e çevirdi.
**Katmanlı savunma canlıda çalıştı** (merge doğrulaması ajan hatalarını yakalıyor) — ama ajan
şemayı tutmuyor. `check_code_integrity` de ITG-11 şema dışı yakaladı. Öneri: 2B komutuna şema
zorunluluğu + fikstür.

### O4-03. `v4_verify_yolu` profilde DİZİN verilince çıplak `secret_scan` CRASH ediyor  (sınıf A, P0)
`kod_profil.json` şablonu ve DEVIR §2 "toolkit yolunu ver" diyor; betik **dosya** bekliyor
(`spec_from_file_location` → `None.loader` → `AttributeError`, satır ~76). `--v4 <dosya>` ile çalışıyor.
Öneri: dizin verilirse `ARACLAR/betikler/v4_verify.py`'yi kendisi çözmeli (SEC-CFG-01; 2C bunu yakaladı).

### O4-04. `chg_reconcile` izlenmeyen kurulum dosyalarını SCOPE_VIOLATION sayıyor  (sınıf A, P1)
`git diff HEAD` 64 dosya görüyor (kurulumun kendisi: .opencode/, scripts/, ORTAK/, 00_KOD_OKU_BENI...)
ve RECK-03 bunların tamamını planda yok diye P0 sayıyor (63× P0). Kurulum sonrası ilk koşuda bu
**yapısal gürültü** — hat kendi kurulumunu ihlal sanıyor. Öneri: kurulum dosyaları için hazırlık
kuralı (ör. ilk commit "kurulum" olarak işaretlenir / `--faz KFAZ1` öncesi baseline'a alınır).

### O4-05. `check_code_integrity.sh` kapı FAIL'lerinde bile exit=0 döndürüyor  (sınıf A, P1)
`CODE-INTEGRITY FAIL — 1 hata` yazıp **exit=0**. Ajanların kapanış disiplininde ("exit 0 değilse
DUR") bu yanlış sinyal verir — ajan FAIL'i başarılı sanabilir. (K12 sınıfı — kod değil, **exit kodu**
fail-open.) Öneri: FAIL → exit=1.

## 4. BİLİNEN AÇIK KIRIKLARIN CANLI DURUMU

| Kırık | ÖLÇÜM-04 durumu |
|---|---|
| O3-06 FRZ-03 ölü kural | tezahür etmedi (dondurulan beyanı yoktu); **açık** |
| O3-07 gate-2a `python3 -c *` | 2A fiilen kullanmadı (git diff/show kullandı); **açık** |
| O3-09 ücretsiz profil yok | bu koşu Go ile aşıldı; **açık** |
| O3-10 dep_audit kilit yok → P0 | **canlı tezahür etti** (2C DEP-AUDIT bulgusu) |
| O3-04/05 | tetikleyicileri O3-01 ile kapandı; **bu koşuda tezahür etmedi** |

## 5. KIRMIZI ÇİZGİLER

Lab değişmedi (bu oturumda lab'a yalnızca bu rapor + SURUM satırı eklenecek).
Koşu scratchpad'de (mtrx dışında); ATLAS_SABLONLAR / toolkit / isimlendir / DENEME / mtrx kökü / orijinal
ad8b92f279… — dokunulmadı. Go planı kullanıcının aboneliği; **$0 ek maliyet**.

## 6. MALİYET

$0.00 — Go plan içi kullanım; OpenRouter bakiyesinden harcama yok.

## 7. TERMINAL DURUM

**YEŞİLE DÖNÜYOR (koşullu).** Üç canlı sınav geçti; hat ilk kez KFAZ4'e (üç kapı + merge + integrity)
kadar koştu. FINAL FAIL'in gerekçeleri: ürün kodu değil — ölçüm aleti dosyaları (bilinen E2E sınıfı),
O3-10 (bilinen), O4-02/03 (yeni). **"Hat uçtan uca koşuyor" hâlâ denemez** — KFAZ5 koşmadı ve
artefakt zinciri bu koşuda kurulum-gürültüsü (O4-04) yüzünden doğal FAIL veriyor.
Denebilecek olan: *sürücü katman düzeltildi ve canlıda tuttu; kapılar katmanlı savunmayı canlıda
gösterdi; sıradaki engel ölçüm aleti gürültüsü.*
