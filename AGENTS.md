# AGENTS.md — AI ARAŞTIRMA LABI

Bu dosyayı okuyan her ajan (Codex, opencode, başka bir asistan) **önce bunu uygular.**
Lab: akademik makale (ATLAS hattı) ve yazılım (KOD hattı) üreten, kanıt disiplinli bir laboratuvar.
Sahibi: Ali Han Kaya. Sürüm bilgisi `SURUM.md`'deki **`Sürüm:` satırındadır**.

## 0. İLK 5 DAKİKA — şunları oku, sonra başla
1. `SURUM.md` içindeki `Sürüm:` satırı → güncel sürüm
2. `docs/` içindeki **en son DEVIR** dosyası → labın son sözü
   ⚠ Dosya adlarına göre sıralama YANILTIR: hangisinin son söz olduğunu `SURUM.md` söyler.
3. `docs/DERSLER_v1_2026-08-30.md` → kabul VE reddedilen düzeltmeler. **Reddedilenleri yeniden açma.**
4. `AI_CALISMA_SISTEMI_v1.md` → 38 kurallık oturum sözleşmesi

## 1. BAĞLAYICI İLKELER — ihlal = iş başarısız
- **I1. Kanıt ≠ beyan.** Bir dosya "PASS" diyorsa bu bir *iddiadır*; komutu çalıştırıp çıktıyı görmek *ölçümdür*.
- **I2. Uydurma yok.** Ölçmediğine "muhtemelen doğru" deme. `OLCULMEYEN` yaz.
- **I3. İki modelin anlaşması doğruluk değildir.** Nihai hakem **birincil kayıttır**
  (ölçüldü: 22 modelden 21'i ZIP-215 hakkında aynı yanlışta anlaştı).
- **I4. Adil ol.** Belgelenmiş gerekçeli tasarım kararı kusur değildir — **önce gerekçeyi ara**
  (`docs/DEVIR-*.md`, `DERSLER`). Bu kural 63M'lik arşivin yanlış commit'lenmesini engelledi.
- **I5. Asgarilik.** Her düzeltme **tek mekanizmayı** hedefler ve **ayrı commit** alır.
- **I6. Reddedilenler kaydedilir.** Yanlış satırı **silme** — üstüne düzeltme notu koy.
- **I7. Fail-closed.** Kritik belirsizlikte geç değil, **DUR**.
- **I8. Ahlak → teknik kural.** sıdk: kanıtsız iddia yok · emanet: yetkisiz değişiklik yok ·
  adalet: hoşuna giden sonuç ile gerçek sonuç ayrılır · tevazu: bilinmiyorsa OLCULMEYEN ·
  ihtiyat: şüphede fail-closed · hesap verebilirlik: her kararın izi bulunur · hata kabulü: geri alınır ama silinmez.
- **I9. Bootstrap.** Kapı/test değişikliği **kendi aday sürümüyle değerlendirilemez.** Öncesiyle karşılaştır:
  `git archive <onceki-commit> | tar -x -C /tmp/oncesi && cd /tmp/oncesi && python3 ATLAS_SABLONLAR/scripts/atlas_selftest.py`

## 2. DOĞRULAMA — her iş bittiğinde koş
```bash
python3 ATLAS_SABLONLAR/scripts/atlas_selftest.py     # beklenen: 126/126 (bu Mac'te)
python3 KOD_SABLONLAR/scripts/kod_selftest.py         # beklenen: 172/172 (bu Mac'te)
git status --porcelain                                 # beklenen: bos
git fsck                                               # beklenen: hatasiz
```
ATLAS pinli envanterin tamamını geçmelidir. Etkin sayı ve kimliklerin kaynağı
`ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` (`sayi`, `kimlikler`), son kayıtlı ATLAS/KOD
sonuçlarının kaynağı `docs/OLGULAR.md` makine bloğudur. Her görevde canlı sonuçla karşılaştır;
başarısız/eksik test veya önceki koşuya göre sayı düşüşü kabul edilmez.

## 3. ÇIKTI SÖZLEŞMESİ — bunlar olmadan iş "bitti" sayılmaz
- **A. `IDDIA vs DOGRULAMA` tablosu** — her adım için bir satır: `| # | İddia | Komut | Çıktı | Exit |`
  **Çalıştırılmamış hiçbir iddia tabloya girmez.**
- **B. `OLCULMEYEN` bölümü** — boş olamaz. Ölçemediğin her şey, gerekçesiyle.
- **C. `docs/DERSLER_v1_2026-08-30.md`'ye satır ekle** — kabul edilen VE reddedilen her düzeltme:
  `tarih | örüntü | öneri | Δ_içeride | Δ_dışarıda | karar | gerekçe`
  Kabul kuralı: **KABUL ⟺ Δ_iç ≥ 0 ∧ Δ_dış ≥ 0 ∧ max(Δ) > 0**
  Δ_dışarıda ölçülemiyorsa **0 yaz ve "sonraki koşuda ölçülecek" de. UYDURMA.**
- **D. `docs/DEVIR-YYYY-MM-DD-HHMM.md`** — pencere kapanış devri. Dosya adında **gerçek saati** kullan.
- **E. `SURUM.md`** güncellemesi.
- **Mekanizma commit zinciri:** Her mekanizmanın uygulama + belge commit'i zincirinde
  `docs/DERSLER_v1_2026-08-30.md` dosyasına en az bir ders satırı eklenmelidir.
- **WARN/FAIL ayrımı (AUD-04):** `check_integrity.sh --full`, OLGU-06 başarısızlığını **WARN**
  sayıp devam eder (exit bozmaz); `olgu_lint.py --dersler` eksik DERSLER kaydında
  **FAIL OLGU-06**, exit **1** üretir. Kapanış için bağımsız OLGU-06 PASS gerekir.
- **Biri eksikse "bitti" DEME.** Eksik iş bildirmek ayıp değil; tamam diye bildirmek ayıptır.

## 4. COMMIT DİSİPLİNİ — labın en pahalı hatası buydu
Her mantıksal adım **ayrı commit** (I5). Pencere sonunda **ağaç temiz** bırakılır.
Commit'siz bırakılan iş, "kayıt gerçeğin gerisinde kalıyor" örüntüsünü yeniden başlatır — bu örüntünün
gerçek zararı, yanlış bir Fatḥ al-Bārī sayfa numarasının dergiye gitmesiydi.
Git kimliği yapılandırılmamış olabilir; global ayarı **değiştirme** (emanet), commit'te geç:
```bash
git -c user.name="Ali Han Kaya" -c user.email="alikaya.metu@icloud.com" commit -m "..."
```

Codex worktree'de `.git/index.lock` yazma kısıtı nedeniyle commit yapamazsa, kullanıcı
terminalden commit'i kendisi atar. Bu bir hata değil, bilinen ortam sınırıdır.

## 5. KIRMIZI ÇİZGİLER — dokunma
- `DENEME/` — **bilerek dondurulmuş kusurlu koşu**, denetim dersi olarak duruyor.
- `docs/_ARSIV-scratch_olcum07_FJdD/` — 63M, **iç içe git deposu**. Belgelenmiş karar
  (`docs/DEVIR-2026-08-26-1713.md:59`): *"commitlenmez, silinmez"*. `.gitignore`'da korunuyor.
- `~/Desktop/DIVINELOVE` ve `~/Desktop/gpt-mideo-kopyası` — **yalnız oku**, değiştirme.
- MIDÉO makalesinin **içeriği** — ayrı iş, dokunma.
- **Dizin yapısını değiştirme.** 9-klasörlük göç önerisi reddedildi (öneren modeller diske hiç bakmamıştı).
- **"Atlas" adını değiştirme.** Karar verildi, red DERSLER'de kayıtlı.
- **MOD-1 / MOD-2 testlerini "onarmaya" çalışma** — ortam farkı oldukları ÖLÇÜLDÜ; bu Mac'te ellenmeden geçiyorlar.
- **Özel Ed25519 / ZIP-215 doğrulayıcı yazma.** ZIP-215 doğrulamayı **gevşetir** (birincil kayıtta ölçüldü:
  *"admits more solutions… not fewer"*). Mevcut HMAC + git tag yeterli.
- **SLSA Build seviyeleri / KMS / transparency log kurma.** v1.9'un "her koşu BLOCKED" hastalığını tekrarlar.
- **Öğrenim döngüsünü otomatikleştirme.** Eşik: 3 gerçek döngü + 1 gerçek red.
- Şu araçları **kurma** — varlıkları doğrulanamadı: `opencode-teamwork`, `opencode-orchestrator`,
  `regent-code`, `provbind`, `scitex`, `fromwhere`, "Oroboros".

## 6. "BİTTİ" DEMENİN ŞARTLARI — BEŞİ birden, her biri komutla
1. Öz-test sayıları önceki koşudan **düşük değil** (bu Mac'te ATLAS 126/126, KOD 172/172)
2. `git status --porcelain` **boş**
3. `IDDIA vs DOGRULAMA` tablosu dolu — her satırda gerçek komut ve **ham çıktı**
4. `OLCULMEYEN` bölümü **dolu**
5. `DERSLER_v1`'e satır eklendi (kabul **veya** red)

## 7. YASAK CÜMLELER — ölçüm olmadan bunları kurma
- "her şey hazır" · "teslime hazır" · "sorunsuz çalışıyor" · "tamamen tamamlandı"
- "muhtemelen çalışır" · "büyük ihtimalle doğru" · "sorun görünmüyor"
- "gerekli tüm kontroller yapıldı" — **hangi kontroller, hangi komut, hangi çıktı?**

Yerine: **ölçtüğünü rakamla söyle, ölçmediğini `OLCULMEYEN`'e yaz.**
Çıktı sütununa komutun **ham çıktısı** girer — senin ürettiğin özet etiket değil
(`GIT_STATUS_UNCHANGED=yes` gibi bir şey ham çıktı DEĞİLDİR).

## 8. HABER VERME BORCU — sessizce ilerleme yok
Şunlardan biri olursa **işi DURDUR ve Ali'ye söyle.** Kendi başına karar verme:
- **Görev tanımı diskle uyuşmuyorsa** (sürüm numarası, dosya sayısı, yol, satır no)
- **Bir düzeltme başka bir şeyi bozuyorsa** — sayı düştüyse, kapı kırıldıysa
- **Geri alınamaz bir işlem gerekiyorsa** — silme, tarih yeniden yazma, `--force`, büyük dosyayı commit'leme
- **Kırmızı çizgiye dokunman gerekiyorsa**
- **Bir şeyi ölçemiyorsan ve o ölçüm kararı değiştiriyorsa** (I7: fail-closed)

"Küçük bir şeydi, ben hallettim" **YOK.** Ali'nin haberi olmadan kapatılan konu, kapatılmamış konudur.

## 9. ÇALIŞAN ŞEYİ BOZMA
Bir şey şu an çalışıyorsa (ATLAS 126/126, KOD 172/172, temiz ağaç, geçen kapı), ona dokunmanın **yazılı gerekçesi** olmalı.
Düzeltmeden **önce ve sonra AYNI ölçümü** al, ikisini de tabloya yaz.
**Sayı düşerse geri al** — açıklama arama, önce geri al, sonra konuş.
Aynı anda iki mekanizma değiştirme (I5): hangisinin işe yaradığını bilemezsin.

## 9A. İNSAN POLİTİKASI VE ÖĞRENME
- `HUMAN_REVIEW_REQUIRED`, `PASS-PENDING-ETHICS`, pivotal uyuşmazlık veya açık etik soru varsa
  yetkili, lab sahibi ya da onun yazılı olarak atadığı kişidir; model insan kararını varsayamaz.
- Çalışmanın mevcut karar kaydına, yoksa DEVIR'ine yazılır: yetkilinin adı ve rolü; kararın kapsamı ve ilgili
  artefakt/commit; karar ve gerekçesinin kanıtı; tarih-saat; bekleyişin teslim üzerindeki etkisi.
  Kayıt yokken etkilenen teslim `BLOCKED` veya `PASS-PENDING-ETHICS` kalır.
- Bağımsız dış değerlendirme; yayımlama/sürüm öncesi yüksek etkili veya pivotal iddiada, çözülmeyen
  panel uyuşmazlığında, çıkar çatışmasında ya da lab sahibinin talebinde açılır.
- Lab sahibi değerlendiriciyi üretim ve iç denetim zincirinin dışından seçer. Adı/kurumu veya sistem-model
  kimliği, konu rolü/yeterliği ve çıkar ilişkisi kaydedilir; iç ajanlar bağımsız dış hakem sayılmaz.
- Dış değerlendirme kanıtı; incelenen sürüm/commit ve artefakt hash'i, gönderilen tam soru ve malzeme,
  tarihli değiştirilmemiş yanıt/rapor ve nihai kararla eşleştirmeyi içerir. Eksikse `OLCULMEYEN` yazılır;
  dış model değerlendirmesi insan kararının yerine geçmez.
- Öğrenme döngüsü bu eşik sağlanana kadar elle yürütülür: **en az 3 gerçek kullanım döngüsü + 1 gerçek red**.
  Gerçek kullanım, kuralın gerçek bir teslimde uygulanıp karar ve sonucunun kaydedilmesidir; sentetik,
  kuru koşu ve tekrar oynatma sayılmaz. Gerçek red, yetkili insanın belirli bir öneriyi kayıtlı gerekçeyle reddetmesidir.
  Sayılan her döngü ve red, RUN/teslim kimliği ve DERSLER kaydıyla izlenebilir olmalıdır.
- Eşiğin sağlanması otomatikleştirme yetkisi vermez. Lab sahibinin yazılı kararı ve ayrı doğrulaması
  olmadan öğrenme kuralı, eşik veya ders kaydı kendiliğinden değiştirilemez.

## 9B. ÖĞRENİLEN ÖLÇÜM VE TEST KURALLARI
1. `$?` başka komutla aynı satırda kullanılmaz; önce `rc=$?` ile yakala.
2. Mutasyonda yanmayan kural kaldırılır; sahte güven verir.
3. Tek gövdeli test fonksiyonuna blok eklerken ad çakışmasını `grep` ile ölç, sonra yaz.

## 10. SIRADAKİ İŞ
P1-1..P1-9 paketi kapandı (`docs/YENI_IS_P1_2026-08-30.md`); fecr-ai stabilizasyon ve prod turları
(KFAZ1-5 + FAZ A-F + TUR 2) KFAZ5 PASS ile kapandı. Kapalı işi yeniden açma.
Sıradaki iş için `SURUM.md` güncel kaydının gösterdiği DEVIR, DERSLER kararları ve
kullanıcının güncel görevini esas al.
