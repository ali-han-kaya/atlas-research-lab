# DENETİM RAPORU v3 — SIFIR GÖZLE TAM TARAMA · AI ARAŞTIRMA LABI

**Tarih:** 30 Ağustos 2026 · **Sürüm:** v1.7.68 · **Yöntem:** komutla ölçüm, beyan değil
**Kapsam:** 4 klasör · lab 32 bileşen · DIVINELOVE 14 klasör · git 986db74
**Ölçen:** 4 alt ajan + canlı komutlar · **Yazan:** Muse Spark (opencode)

> Önceki v2 raporu 20 bulgu vermişti. Bu v3, o bulguları tek tek yeniden ölçer, 1 hatasını düzeltir, yeni durumu kaydeder. Hüküm daralır: yapı sağlam, kayıt geride, toolkit kendi kapısından geçmiyor.

---

## 0. NE ÖLÇÜLDÜ, NE ÖLÇÜLMEDİ — DÜRÜSTLÜK KAYDI (v3)

| Ölçüldü | Komut | Sonuç |
|---|---|---|
| SHA bütünlüğü | `shasum -c SHA256SUMS.txt` 14_LIVRAISON | **21/21 OK** |
| Atlas öz-test | `atlas_selftest.py` | **68/68 PASS** |
| Toolkit öz-test | `v4_selftest.py` | **37/39 ENGEL_VAR** |
| Toolkit tutarlılık | `v4_consistency.py` | **P0:1 ENGEL_VAR** |
| Git durumu | `git log/status/diff` | v1.7.38 → v1.7.68, 30 sürüm bekliyor |
| Kılavuz + SURUM | `cat/grep` | B-1, B-2 yeniden doğrulandı |
| Web araştırması | 6 konuda canlı search | 6 kaynak toplandı |

| Ölçülmedi | Neden |
|---|---|
| Model kataloğu canlı koşusu | opencode modelleri bu ortamda yok — fail-closed testi izole yapıldı |
| iCloud yedeği birebirliği | bağlı klasör dışında, `shasum -c` teyidi yapılmadı |
| DOI Crossref canlılığı | proxy 403 → verify_doi WARN veriyor, FAIL değil (tasarım) |
| Arapça/Fransızca filoloji | süreç denetlendi, içerik değil |
| Canlı ücretli ATLAS koşusu | ağ koşusu yok — maliyetler belge üzerinden |
| 14 hakemin API faturası | beyan + TUR2_OZET.json, fatura bağımsız doğrulanmadı |

---

## 1. KURULUM DURUMU — DOĞRULANDI

| Bileşen | Beklenen | Ölçülen | Hüküm |
|---|---|---|---|
| `.opencode/agent` | 13 ajan symlink | 13 symlink → `ATLAS_SABLONLAR/.opencode/agent` | OK, tek kaynak |
| `.opencode/command` | 8 komut symlink | 8 symlink → `ATLAS_SABLONLAR/.opencode/command` | OK |
| `opencode.json` lab kökü | modelsiz, provider openrouter | openrouter + opus-5/deepseek/glm/kimi | OK |
| `opencode.json` KOD_SABLONLAR | deepseek-v4-flash sabit | `openrouter/deepseek/deepseek-v4-flash` | OK, fail-closed |
| `.mcp.json` | ruflo MCP | `npx ruflo mcp start` + hybrid memory | OK |
| `.claude-flow` / `.swarm` | swarm topoloji | 2 klasör var, `hierarchical-mesh` `max 15` | OK, kuruldu |
| `.agents` / `.claude` | — | var, engineering/exa/langfuse eklentileri | OK |

**Yorum:** Kurulum tamam. Lab opencode üzerinden çalışmaya hazır. Sorun kurulumda değil, kayıtta.

---

## 2. LAB DEĞİŞİMİ — SON 4 GÜN

- **Son commit:** `986db74 v1.7.38` 26 Ağs 15:54
- **SURUM:** v1.7.68 30 Ağs (57 satır ek)
- **Fark:** `git status` → 1 değişmiş (SURUM.md) + 33 izlenmeyen (32 DEVIR + NEXT_AI_KOMUT + main_mideo artefact’leri) + `.claude-flow/.swarm`
- **Tek ek dosya:** `NEXT_AI_KOMUT.md` 153 satır, sha `78c5fd62...` — v1.7.67 labını diğer yapay zekaya aktaran tek-yapıştırma komutu. 2026 bağlam mühendisliği (budgeting, delimiter, caching, structured output, few-shot) uygulanmış.
- **Yedek:** `ATLAS_SABLONLAR/docs/CHANGELOG-v5.md` dışında iCloud yedeği bu turda alınmadı (SURUM v1.7.67 teyidi yok).

**Hüküm:** Lab dosyalarına cerrahi ek yapıldı, 30 sürümün kaydı commitlenmedi. B-3 devam ediyor, büyüdü (29 → 30).

---

## 3. ÖNCEKİ 20 BULGUNUN GÜNCEL DURUMU (v3 yeniden ölçüm)

### 3.0 ÖNCEKİ RAPORUN KENDİ HATASININ DÜZELTMESİ

**B-21 düzeltmesi [YÜKSEK — rapor hatası]:** v2’de “14 model iddiası kaynağında 0 kez, F0 0 kez, uydurma” denmişti. **Yanlış.**

- `00_OKU_BENI.md:30` satırı doğru: “14 modellik acımasız hakem komutu” — bu, *gerçek koşunun* adı.
- `HAKEM_BRUTAL_2TUR_KOMUT_v2.md` (186 satır) içinde “14” 0 kez geçmesi normal — o dosya *şablon*. İçinde “2 model yeter” (satır 170) **minimum** eşiği, maksimum değil.
- Canlı kanıt: `docs/DEVIR-2026-08-26-2230.md:11` — 26 Ağs TUR2: **14 modele OpenRouter API ile gönderildi, 14/14 rapor geldi, toplam $2.119** (prompt 42-68K, completion 2-8K, ort 108s). 14 `HAKEM_*_TUR2.md` dosyası `~/Desktop/26auTUR2_v6_2026-08-26/` altında toplandı.
- `HAKEM_BRUTAL:174` satırı da uyarır: “aynı aileden 2 model benzer körlük yapar” — çeşitlilik bilinci şablonda var.

**Doğru hüküm:** “14 model” uydurma değil, *koşulmuş* bir sayı. Şablonun “2 model yeter” cümlesi ile koşunun “14 model” gerçeği çelişmiyor; biri eşik, diğeri örneklem. Düzeltilmesi gereken, şablonun başına koşu sayısını yazmak değil; `00_OKU_BENI.md`’de “14 model”in **şablonun değil, 26 Ağs koşusunun** sayısı olduğunu bir parantezle belirtmek.

Bu düzeltme B-22/B-23’ü hafifletmez; ama B-21’in kendisi P0 değil, **P2** belgelendirme eksiği.

---

### ÖRÜNTÜ 1 — Kayıt gerçeğin gerisinde

| ID | Başlık | v2 | v3 güncel | Kanıt |
|---|---|---|---|---|
| B-1 | Kılavuz kanonu tanımıyor | YÜKSEK | **YÜKSEK — açık** | `DIVINELOVE/00_KLASOR_KILAVUZU/README.md` hâlâ `12_SON_TESLIM...` listeliyor; `14_LIVRAISON` kanon ama kılavuzda “SON TESLİM” etiketi yok. `grep -c "13_REVIZYON\|14_LIVRAISON" README.md` → 0 |
| B-2 | SURUM eski Fatḥ değeri | YÜKSEK | **YÜKSEK — kısmen açık** | SURUM.md’de düzeltme kaydı var (v1.7.54: “p.344 → p.349-355 (noyau 351-352)”), ama `VERIFIED_ISSUES v1.7.64` hâlâ `FATH-PAGE P1` olarak `XI,340-347 (metin 340-341, çekirdek 344-345)` öneriyor — üç farklı aralık (344, 349-355, 340-347) aynı repo içinde yaşıyor. Tek kaynak `OLGULAR.md` yok. |
| B-17 | Hedef dergi/transliterasyon çelişiği | YÜKSEK | **YÜKSEK — açık** | 13/REVIZYON “APA7 IJMES”, 14/HAKEM “MIDÉO IFAO-Idéo?”, 14/CHECKLIST ☐ işaretsiz. Hâlâ tek satır karar yok. |
| B-3 | Git 29 sürüm geride | ORTA | **ORTA → YÜKSEK, açık** | `git log -1` 986db74 26 Ağs; SURUM v1.7.68 30 Ağs. 1 modified + 33 untracked. 30 sürümün tamamı MIDÉO teslim zinciri. |
| B-18 | SHA kilidi 4 kez kırılmış | ORTA | **ORTA — açık, donduruldu sayılır** | 14/ klasöründe `.bak/.new2/.new3/.new4` hâlâ duruyor. v1.7.62’den sonra yeni kırılma yok — ama temizlik yapılmadı. |
| B-19 | Manifest %32 kapsam | ORTA | **ORTA — açık** | SHA 21/21 OK ama klasörde 65 dosya var (`.DS_Store` + ZIP’ler + sidecar). 9 ZIP ana manifestte değil. |
| B-5 | PLAN_v2 model tablosu bayat | ORTA | **ORTA — açık** | `PLAN_v2.md` “orkestrasyon = opus-5”, `routing.profiles.json` “kalite profilinde bile Sonnet 5, Opus gömülü değil” — plan ↔ config çelişiği sürüyor. `opencode.json`’da opus-5 reasoning high hâlâ duruyor (hiçbir ajan kullanmıyor). |

### ÖRÜNTÜ 2 — Güvenlik ağı var, bağlı değil

| ID | Başlık | v2 | v3 güncel | Kanıt |
|---|---|---|---|---|
| B-24 | KEEP korumasız — çözüm labda | YÜKSEK | **YÜKSEK — açık, en ucuz kazanç** | `RAFINE_SABLON/` 4 .md, 0 betik. `KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_preserve.py` SHA256 önce/sonra + sessiz kayıp=P0 hâlâ RAFINE FAZ3’e bağlı değil. `grep -rl KEEP-LISTESI **/*.py **/*.sh` → 0. |
| B-15 | Gate-2B sayaç körlüğü | YÜKSEK | **ORTA — kısmen açık, tanımlı** | v2’de “0 kontrolle PASS” denmişti. v3’te `FINAL-GATE counts` 2B’yi `manifest_reconciliation` altında 15 öğeyle sayıyor (kanıtlı). Toplayıcı `checks`’e bakıyor, `atlas_selftest` GM-5 testi yalnız `checks`’i sayıyor → 2B’ye kör. 2B boş olsa aynı kaydı üretirdi. Düzeltme: iki kapı aynı şemaya yazsın. |
| B-13 | KOD model doğrulaması elle | ORTA | **ORTA — bilinçli, belgeli** | `check_models.py` KOD’da yok — `KOD_SABLONLAR/scripts/README.md` gerekçe: `kur.sh ../ATLAS_SABLONLAR` referansı hedefte kırılır. Doğru karar, ama otomatik kapıya bağlı değil. `kod_selftest`’e “katalog varsa doğrula, yoksa atla ve yaz” eklenmeli. |
| B-20 | Bağlam mühendisliği tek seferlik | ORTA | **ORTA — açık** | `11_MIDEO_2027_WORKING/PIPELINE/CONTEXT_ENGINEERING.md` + `PROMPT_ENGINEERING.md` (3 katman, güven, kapalı şema, öz-eleştiri) hiçbir şablona geri beslenmemiş. `grep -rl "IFAO\|horizon-track" ATLAS_SABLONLAR KOMUT_TOOLKIT` → 0. ATLAS’ta `translit_check.py` varken PIPELINE elle-diff icat etmiş. |

### ÖRÜNTÜ 3 — Sayılar tutmuyor

| ID | Başlık | v2 | v3 güncel |
|---|---|---|---|
| B-21 | “14 model” kaynağında yok | YÜKSEK | **DÜZELTİLDİ — rapor hatası, gerçek P2** — bkz §3.0 |
| B-22 | Kural 30 beyanı yok | YÜKSEK | **YÜKSEK — açık** `grep -i "aynı model\|kopya" MUTABAKAT + BRUTAL` → 0. “sıdk” 10+ kez geçiyor ama zorunlu cümle yok. Mutabakat şablonuna zorunlu alan eklenmeli. |
| B-23 | Toolkit kendi kapısından geçmiyor | YÜKSEK | **YÜKSEK — açık, canlı** `v4_selftest 37/39` (SP-7 `__pycache__` 6 .pyc, TUT-1 Türkçe makine anahtarı + olmayan dosya referansı), `v4_consistency P0:1` (kökte `000_ONCE_BUNU_YAPISTIR.md` bulunamadı). 30dk’da kapanır. |
| B-16 | PIPELINE terk dal | ORTA | **ORTA — açık, sessiz** `11 ↔ 14 hash 0/65`, `horizon-track.json` 27 Ağs 07:45’ten beri dokunulmadı, `DOGRULANAMADI` 19/19. Klasörde “TERK EDİLDİ” etiketi yok. |
| B-9 | ATLAS maliyeti ölçülmedi | ORTA | **ORTA — açık** `OLCUM-01..07` hepsi KOD hattı (KFAZ0-5). ATLAS için canlı ATLAS koşusu yok. `routing.profiles.json` “denge ~$2.3” tahmin. Tek denge koşusunda tahmin $0.82 → gerçek $1.15 (%40 sapma). |
| B-8 | DENEME dersi yanlış ağaçta tersine öğretir | ORTA | **ORTA — açık** `DENEME/scripts/check_integrity.sh --full` (donmuş) → FULL PASS v5.5.2 EXIT 0 (tarihi hatayı tekrar eder), `ATLAS_SABLONLAR/scripts/... --faz3` → FAIL EXIT 1 (doğru). `DENEME_NOTU.md` ana cümlede yol belirtmiyor. |
| B-25/B-26 | Hakem bağımsızlığında çatlak (model çakışması + tek imza) | ORTA | **ORTA — açık** 18 hakemde Gemini 1.5 + Perplexity(gemini) ayrı sayılmış; tek kişinin “tek aykırı, şişirme” eleme kararı ikinci kapısız. |
| B-10/11/12 | Küçük kesin düzeltmeler | DÜŞÜK | **DÜŞÜK — açık** B-10: `check_integrity.sh:52` DEC-036 (kapalı) vs DEC-035 (açık) — 1 kelime. B-11: FULL PASS DOI’leri doğrulamaz (WARN vs FAIL dili). B-12: `budget_guard.py fiyatlar()` ölü kod. |
| B-6/7/27 | Tutarlılık pürüzleri | DÜŞÜK | **DÜŞÜK — açık** B-6: varsayılan gate-2B glm-5.2 vs ajan 5.3; B-7: kanonda 9 eski ZIP 4 MB; B-27: `00_OKU_BENI` vs `AI_CALISMA_SISTEMI` hiyerarşi tek taraflı. |

**Sayım:** 20 bulgudan **1’i rapor hatası olarak düzeltildi** (B-21 → P2), **19’u açık**. Hiçbiri içerik hatası değil — hepsi kayıt/kapı/belge katmanında.

---

## 4. DOĞRULANAN GÜÇLÜ YANLAR (v3 canlı)

- **SHA 21/21 OK** — `shasum -c` 0 FAILED, deterministik. En güçlü iddia doğrulandı.
- **Atlas öz-test 68/68 PASS** — v2’de 48/50’ydi, şimdi 68/68. Fail-closed, GM-5, PE-1..3, SP-1..6 hepsi yeşil.
- **DENEME dersi çalışıyor** — güncel `fix_reconcile.py` donmuş kusuru isim isim yakalar (`REC-04 6/8 UYGULANMIS FIX MASTER’da yok`). Ders gerçek, yalnız yolu karanlık (B-8).
- **Hash tutarlılığı** — 01↔02 ortak ekler bayt birebir; 09/10/12 PDF/HTML/MD üçlüsü üç klasör boyunca aynı hash. Sessiz sapma yok.
- **Dürüst itiraf** — `001_SORUN_CIKARSA_OKU.md:97` “Tek sohbette gerçek körlük yoktur.” — körlük şişirilmemiş.
- **P1 kapatma** — `b. → ibn` 11 yerde, ölüm tarihleri 10 yazarda dosya üzerinde doğrulandı.
- **İlke** — “İki modelin anlaşması doğruluk değildir” — Anjum künyesinde Claude+GPT yanıldı, Crossref çözdü. Labın BUILD sözleşmesine yazılmış.

---

## 5. WEB ARAŞTIRMASI — 2026 GÜNCEL NE DİYOR

| Konu | Özet | Kaynak |
|---|---|---|
| Harness self-improvement | Reset-free döngüde harness kendi prompt/skill/hafızasını mid-episode düzenliyor. Voyager skill library + iteratif self-verification, Reflexion sözel hafıza. Low-budget high-budget’ı %60 ucuza geçebiliyor. | arxiv 2605.09998 |
| Context engineering | Write/Select/Compress/Isolate 4 işlem. RAG + re-rank + bütçe + memory > tek akıllı prompt. Claude XML sever, GPT-5 concise, Gemini 2 Pro long-context’te soru sona. | thetechpost.com 2026 playbook |
| Verify chain / SLSA | SLSA Build L3 + in-toto + DSSE, hosted izole builder, `slsa-verifier` + Sigstore keyless, deployment gate’te fail-closed. | slsa.dev/spec/draft |
| Swarm orchestration | Hierarchical topoloji, max 6-8, strategy specialized, queen drift engeller, AgentDB hybrid memory. Tek mesajda `run_in_background:true`, polling yok. | deepwiki ruvnet/claude-flow |
| Ed25519 | libsodium `crypto_sign_detached`, RFC8032 + FIPS 186-5: s mod order indirgenmemeli, R small-order (8 nokta) kontrolü şart, `verify_strict()` seç. | libsodium doc |
| Fail-closed | Policy timeout/IdP/audit sink erişilemezse 503 ile blokla. PERMIT/DENY/SILENCE üçlüsü, belirsizlik = DENY. EU AI Act 12/26 + DORA uyumu. | deepinspect.ai |

**Çıkarım:** Labın “2-of-2 farklı aile = bağımsızlık” varsayımı `Nine Judges (2.2 effective votes)` bulgusuyla çürüyor; belirleyici aile değil, eğitim paradigması. v1.9’un İlke 6’sı (“model ailesi çeşitliliği tek başına bağımsızlık değildir”) labın routing’inden daha doğru. Çözüm kapıyı kaldırmak değil, **Kapı 2C: birincil kayıt** eklemek.

---

## 6. MTRX v1.9 DEĞERLENDİRMESİ — KALİBRASYON SORUNU

v1.9 454 satır, 10 bölüm, C1–C14, Ed25519 + RFC8785 + 14 negatif test. **Çekirdek sağlam.** Üç güçlü isabet: Alan-bağlamlı DOMAIN_HASH (uzunluk önekli), bootstrap kuralı (kapı kendi adayını değerlendiremez — TUF/in-toto içgörüsü), İlke 3 “kanıt ≠ beyan”.

**Kritik sorun — ölçek uyumsuzluğu:** Sözleşme KMS/HSM + append-only revocation + atomik run registry + out-of-band trust + “2 bağımsız insan onayı” zorunlu kılıyor. Tek kişilik araştırmacıda her koşu **BLOCKED** çıkar. Her zaman blokeleyen kapı atlanan kapıya döner — kapısız olmaktan kötüdür.

**Çözüm — iki profil, aynı tablo:**

| Gereklilik | TAM | SOLO (öneri) |
|---|---|---|
| İmza | KMS/HSM | yerel Ed25519, `KEY_CUSTODY=LOCAL` beyanı zorunlu |
| 2. insan | 2 yetkili | zaman ayrımı: aynı kişi 24s sonra ayrı oturum, `REVIEW_MODE=TEMPORAL_SEPARATION` |
| Revocation | imzalı servis | yerel append-only dosya + git zinciri, `REVOCATION_SOURCE=LOCAL_APPEND_ONLY` |
| Run registry | atomik dağıtık | `flock + append-only JSONL`, 96-bit nonce korunur |
| Trust anchor | out-of-band + şeffaflık | iCloud + git etiketi = iki ortam, `OUT_OF_BAND=TWO_MEDIA` |
| Bootstrap/fail-closed/14 test | aynen | **indirimsiz** — disiplin işi |

Profil adı çıktı JSON’unda **zorunlu alan** olmalı.

**İkinci sorun — akademik ikizi yok:** HEAD/merge/canary/rollback yazılım dili. Eşleme: `SUBMIT_STATUS`, `CONTENT_HASH`, `DIFF_HASH`, hakem turu=canary, hermetic rollback=deterministik PDF yeniden üretimi, KMA-1=transliterasyon+atıf eşleşmesi, trust anchor=birincil kayıt (Crossref/Şâmile/foto).

**Eksik parça — öğrenim döngüsü:** v1.9 kapı, döngü değil. Tarif ettiğin “her iş sonunda lab kendini yazsın” fikrinin adı **Self-Harness** (arxiv 2606.09498). Kazanç: Minimax +21.4, Qwen +14.3, GLM +14.2 (Terminal-Bench-2.0 held-out). Kabul kuralı: `Δ_iç ≥0 ∧ Δ_dış ≥0 ∧ max(Δ)>0` — bilinen hatada kazanıp görülmemiş işte kaybeden düzeltme **reddedilir**. Güvenceler: dış bölme kutsal, asgarilik (tek mekanizma), reddedilenler de kaydedilir.

> ### ⚠ DÜZELTME 31.08.2026 — AŞAĞIDAKİ ZIP-215 ÖNERİSİ YANLIŞTIR
>
> **Birincil kayıt:** <https://zips.z.cash/zip-0215> (31.08.2026'da açıldı, alıntılar birebir)
>
> ZIP-215 Ed25519 doğrulamasını **SIKILAŞTIRMAZ, GEVŞETİR.** Spesifikasyonun kendi cümleleri:
>
> - Doğrulama denklemi cofactor'lüdür: *"The group equation `[8][S]B = [8]R + [8][k]A` MUST be satisfied"*
> - *"Because multiplication by the cofactor **admits more solutions** to the validation equation, **not fewer**, it is compatible with all existing Ed25519 signatures on the chain."*
> - *"**It is not required that A and R are canonical encodings**; in other words, the integer encoding the y-coordinate of the points may be unreduced modulo 2^255−19."*
> - Sıkı olan tek şart `S`: *"S MUST represent an integer S less than ℓ"*
> - Beyan edilen gerekçe (Motivation): *"The lack of clear validity criteria for Ed25519 signatures poses a **maintenance burden.**"* — yani blok zincirinde **tekbiçimlilik ve bakım yükü**; akademik bir laboratuvarın ihtiyacı değil.
>
> **Hüküm:** Teşhis doğruydu (RFC 8032 tek başına kütüphaneler arası tutarsız), **reçete yanlıştı.** ZIP-215 sıkılık değil *tekbiçimlilik* sağlar — üstelik permissive yönde. Aşağıdaki "Ed25519 'strict' için ZIP-215 adıyla belirt" cümlesi **uygulanmayacaktır.**
>
> **Kanıt değeri (I3):** 22 modelden 21'i bu yanlışta anlaştı; yalnız Perplexity-Grok itiraz etti. *İki modelin anlaşması doğruluk değildir* ilkesinin ölçülmüş ikinci kanıtı. Nihai hakem birincil kayıttır.
>
> **Yayılım ölçümü:** `grep -rn "ZIP-215" .` → lab genelinde yalnız bu dosya (satır 168 iddia + satır 209 kaynak listesi). Hiçbir sözleşmeye veya koda girmemiştir; girmeden düzeltilmiştir.
>
> **Karar kaydı:** `docs/DERSLER_v1_2026-08-30.md` → 31.08 REDDEDİLDİ satırı.
> **Aşağıdaki özgün satır I6 gereği SİLİNMEDİ** — reddedilenler kaydedilir.

**Üçüncü öneri — in-toto/SLSA + ZIP-215:** v1.9 büyük kısmı in-toto’yu yeniden icat etmiş. Taşıyıcıyı in-toto Statement yap, C1–C14 senin katkın kalsın. Ed25519 “strict” için **ZIP-215** adıyla belirt.

---

## 7. YOL HARİTASI — SIRAYLA (ilk 3 adım 1 saat)

1. **v1.7.68’i commit’le** — `SURUM.md` + `NEXT_AI_KOMUT.md` + 32 DEVIR. Sonra `git log --oneline -1` teyidi. · KAPATIR B-3 (30 dk)
2. **v4_preserve.py’yi RAFINE FAZ3’e bağla** — `RAFINE_KOMUT_SABLONU.md`’ye 3. komut olarak ekle. KEEP onur sisteminden kontrole geçer. · KAPATIR B-24 (20 dk)
3. **Gate-2B sayacını düzelt** — 2B `checks`’e de yazsın veya toplayıcı `manifest_reconciliation`’ı saysın. GM-5 körlüğü kalkar. · KAPATIR B-15 (30 dk)
4. **Kayıt hizala (4 metin)** — DIVINELOVE kılavuzuna KULLAN/KULLANMA/KAYIT haritası (B-1) · hedef dergi+transliterasyon tek satır (B-17) · PLAN_v2 tablosunu `routing.profiles.json` işaretçisine çevir (B-5) · PIPELINE’a “TERK EDİLDİ 27.08” (B-16). (1 saat)
5. **OLGULAR.md’yi kur** — Fatḥ + künyeler tek tabloda, makale/SURUM oraya referans versin. Tohum 12 olguyla hazır, kalan eklenmeli. · KAPATIR B-2 kök neden (1–2 saat)
6. **Sayıları doğrult** — “14 model”e “26 Ağs koşusu” parantezi (B-21 P2) · Kural 30 beyanını mutabakat şablonuna zorunlu alan yap (B-22) · `__pycache__` sil + 2 Türkçe makine anahtarını ASCII’le + `000_ONCE...` yolunu düzelt (B-23) · DENEME notuna ağaç yolu (B-8) · DEC-036→035 (B-10). (2 saat)
7. **Kapı 2C: birincil kaynak** — `verify_doi.py` genişlet, kural: “2 model anlaştı ama birincil kayıt yok = P1”. (4–6 saat)
8. **Öz-teste mutabakat ekle** — profil ↔ ajan frontmatter ↔ PLAN uyuyor mu? B-5/B-6 bir daha sessiz oluşamaz. (2–3 saat)
9. **AI beyanını künyele** — rol·model·sürüm·tarih tablosu, `routing.profiles.json`+SURUM’dan üret, ICMJE 2026 uyumu. (1 saat)
10. **Arşiv/maliyet** — 9 ZIP `_ARSIV/`’e (B-7/B-19), ölü kodu sil (B-12), bir ATLAS canlı koşusunu ölç `OLCUM-08`. (1 saat + 1 koşu)
11. **v1.9 SOLO profili + akademik eşleme + DERSLER.md** — v1.9’a SOLO bölümü, kavram tablosu, ve `DERSLER.md` (kabul/red her düzeltme tek satır). Elle bir öğrenim turu: bu 3 örüntüyü al, tek düzeltme öner, ikiye böl, kabul kuralını uygula. (1 makale koşusu)

---

## 8. HÜKÜM

**Makine çalışıyor, kayıt geride — ve bu iyi haber.** 19 bulgunun 4’ü tek satırla kapanıyor (B-24, B-15, B-8, B-10). En pahalı 3 bulgu 1 saatte kapanıyor (adım 1–3). Hiçbir bulgu makale içeriğini vurmuyor; hepsi “hangi dosya geçerli” katmanında.

Labın en büyük borcu **commitlenmemiş 30 sürüm**; en ucuz kazancı **v4_preserve.py’yi bağlamak**. Önceki raporun tek hatası B-21 düzeltildi — bu, denetimin kendini denetlediğinin kanıtı.

*Ölçülen ölçüldü, ölçülmeyen ölçülmedi diye yazıldı.*

---

## 9. KAYNAKLAR

1. Nine Judges, Two Effective Votes — arxiv 2605.29800
2. Correlated Errors in LLM — arxiv 2506.07962
3. ICMJE 2026 AI — link.springer.com 10.1007/s13312-026-00336-1
4. Three Models Agreed. It Was Still Wrong — digitalapplied.com
5. RO-Crate provenance — PLOS One 10.1371/journal.pone.0309210
6. Self-Harness — arxiv 2606.09498
7. SLSA provenance — slsa.dev/spec/draft/verifying-artifacts
8. ATLAS.ti — atlasti.com (isim çarpışması kanıtı)
9. in-toto Attestation — github.com/in-toto/attestation
10. ZIP-215 — zips.z.cash/zip-0215
11. libsodium Ed25519 — doc.libsodium.org
12. Fail-closed gateway — deepinspect.ai

---

## 10. EKLER — CANLI KANIT ÖZETİ

```
shasum -c SHA256SUMS.txt → 21 OK 0 FAILED
atlas_selftest.py → 68/68 PASS
v4_selftest.py → 37/39 ENGEL_VAR (SP-7 __pycache__, TUT-1 tutarlılık)
v4_consistency.py → P0:1 ENGEL_VAR (000_ONCE bulunamadı)
git log -1 → 986db74 2026-08-26 v1.7.38
git status → 1 modified + 33 untracked
SURUM.md → 335 satır, v1.7.68
NEXT_AI_KOMUT.md → 153 satır, sha 78c5fd62
DIVINELOVE 00_KLASOR_KILAVUZU/README.md → 12’yi SON listeliyor, 14 kanon
```

