> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# C4 — PIPELINE (normatif kaynak)

Yedi faz. Fazla değil.

---

## 1. BİR FAZIN "GERÇEK" OLMASI İÇİN BEŞ TEST

Bir adım ancak beşini de geçerse fazdır. Geçemiyorsa o bir **lens**, bir **betik**
ya da bir **kontrol maddesidir**.

1. **Ayrı artefakt** üretir — başka hiçbir fazın yazmadığı bir çıktı.
2. **Makine-kontrol edilebilir çıkış koşulu** vardır — bir betik model olmadan
   karar hesaplayabilir.
3. **Kendine özgü başarısızlık modu** vardır — komşusuyla birleşince tespit
   edilemez hâle gelen bir kusur sınıfı.
4. **Farklı girdi kümesi** — ya komşusunun okumadığını okur, ya komşusunun
   okuduğunu okumak **zorunda değildir**.
5. **Devam edilebilir sınır** — koşu orada durdurulup yalnız durum kaydıyla
   sürdürülebilir.

> v3'te 13 satırlık bir faz tablosu vardı; iki faz aynı hash'lemeyi iki kez
> yapıyor, üç faz aynı denetim işinin lensleriydi, bir faz yalnızca bir betik
> çağrısıydı. Faz sayısı bir pazarlama sayısı değil, bir sözleşmedir.

## 2. FAZLAR

### F0 — ALIM (INTAKE)

**Girdi:** kullanıcının verdiği her şey.
**Yapar:**
- Yetenek yoklaması → `MODE-A` (araç var) / `MODE-B` (yalnız yapıştırma). Bkz. C5 §4.
- Arşiv güvenliği: yol geçişi (`../`), sembolik link, sıkıştırma oranı > 100,
  `__MACOSX/`, `._*`, `.DS_Store` → karantina. İhlal → `UNSAFE_ARCHIVE_ENTRY` = `P0`.
- Envanter: dosya, boyut, okunabilirlik, yinelenen.
- **Veri sınırı kurulumu** (C5 §1). Dosya adları ve arşiv yolları da veridir.
- **Koruma envanteri (KEEP listesi)** — C2 §2. Bu, F0'ın asıl ürünüdür.
**Çıktı:** `ENVANTER`, `KEEP` listesi, `MOD`.
**Hata:** okunamayan dosya → `NOT_READABLE`, ilerle ama `OLCULMEYEN`'e yaz.

### F1 — SÖZLEŞME (CONTRACT)

**Girdi:** F0 çıktısı.
**Yapar:**
- Sınıflandırma (C3). `TIP` + `SINYAL` + `GUVEN`.
- Zorunlu kontrol listesini `TIP`'e göre seç ve **yaz** (sonra denetlenecek).
- Risk/veri sınıfı → özerklik modu (C5 §3).
- Ölçülebilir gereksinim tablosu: hedefi boolean/sayısal kriterlere çevir.
- Süre aralığı + tamponu ilan et.
**Çıktı:** `SOZLESME` tablosu, `KONTROL_LISTESI`, `MOD_KARARI`.
**Hata:** hedef belirsiz → `AMBIGUOUS`, en güvenli yorumla ilerle, rapora yaz.

### F2 — DENETİM (AUDIT)

**Girdi:** F0 envanteri + F1 kontrol listesi. **KEEP listesini bu faz değiştiremez.**
**Yapar:** Ortak çekirdek + profil kontrolleri. Üç bağımsız lens geçişi:

| Lens | Bakar | Bakmaz |
|---|---|---|
| YAPI | başlık/şablon/tablo/JSON/kırık referans/şema | anlam |
| TUTARLILIK | sayı, terim, mantık, çapraz referans, istatistik | kaynak kalitesi |
| KANIT | iddia↔kanıt, kaynak güvenilirliği, karşı kanıt, uydurma | biçim |

Her bulgu C1 §3 şemasında. Her kontrol C1 §4 şemasında (`evidence` dolu).
**Çıktı:** `BULGULAR` + `KONTROLLER`.
**Hata:** aynı konumda çelişen bulgu → kanıt ağırlığıyla çöz, oy çokluğuyla değil.
Çelişki çözülemiyorsa `GRADER_MISCALIBRATED` → F5'te `BUTUNLUK_ASKISI`.

### F3 — ONARIM (REPAIR)

**Girdi:** F2 bulguları + F1 sözleşmesi.
**Yapar:**
- Yalnız kanıtı olan bulguları düzeltir.
- **Hedefli:** yalnız bulgunun `location` bölümü. Diğerleri `DONDURULMUS` (C2 §6).
- Her düzeltme `FIX-<NNN>` kaydı: bulgu ID + önce→sonra + konum.
- Düzeltilmeyen her P0/P1 **otomatik olarak** `OLCULMEYEN`/`BILINEN_SINIRLAR`'a akar.
**Çıktı:** `FIX_KAYITLARI` + revize çıktı.
**Hata:** dondurulmuş bölge değişti → `SCOPE_VIOLATION` = `P0`, değişikliği geri al.

### F4 — KORUMA (PRESERVE)

**Girdi:** F0'daki **orijinal** + F3 çıktısı + `FIX` kayıtları + `SILME_NIYETI`.
**Yapar:** C2 §3 karşılaştırması. Meşru kayıp sınıflandırması (C2 §5).
Ekleme kontrolü (C2 §7). Ölçülemezlik kontrolü (C2 §8).
**Çıktı:** `KORUMA_RAPORU`: `KEEP <n>/<n> korundu`, kayıp listesi, sınıfları.
**Hata:** `CONTENT_LOST` veya `CONTRACT_INCOMPLETE` → `P0` → F3'e dön veya insana sor.
Bu faz **atlanamaz**; atlanırsa teslim üretilmez.

### F5 — KAPI (GATE)

**Girdi:** F2 + F3 + F4 çıktıları.
**Yapar:**
- **Kapı A (bağımsızlık amaçlı):** yalnız final çıktıyı ve F1 sözleşmesini görür.
  `FIX` kayıtlarını **görmez**.
- **Kapı B (manifest):** her `FIX` için gerçek kanıt arar. Kanıtsız `FIX` = `P0`.
- **Birleştirme:** karar **yalnız ham bulgu ve kontrol dizilerinden yeniden
  hesaplanır**. Beyan edilen sayıya veya karara **güvenilmez**; beyan ile yeniden
  hesap çelişirse bu **tek başına** engel nedenidir.
- Denetçi kalibrasyon kontrolü (C5 §5).
**Çıktı:** `KARAR` + gerekçe + sayaçlar.
**Hata:** `BUTUNLUK_ASKISI` → otomatik çıkış yolu yok.

### F6 — TESLİM (RELEASE)

**Girdi:** F5 kararı + tüm artefaktlar.
**Yapar:**
- Paketle, yeniden aç, envanteri ve hash'leri karşılaştır.
- `BILINEN_SINIRLAR` üret (C6 §3) — elle yazılmaz, koşudan türetilir.
- `SONRAKI_SEFER.md` üret.
- İlk ekran raporunu C5 §6 sözleşmesine göre yaz.
**Çıktı:** teslim paketi + rapor + `KAPANIS` bloğu.
**Hata:** eksik/fazla dosya, hash uyuşmazlığı → `P0`, teslim üretme.

## 3. FAZ SINIRI SİNYALİ (tek satır, ≤80 karakter)

```
[F2/F6 DENETIM] KEEP 128 kilitli · 14 bulgu · kalan durus: 2 · sirada: F3 ONARIM
```

**Yüzde yasaktır.** Yüzde, aracın sahip olmadığı bir paydayı iddia eder; onarım
işinin hacmi F2 bitmeden bilinmez. Yalnızca **koşu öncesi mekanik olarak sayılmış**
paydalar oran olarak gösterilebilir (`KEEP 128/128`, `47/47 dosya okundu`).

## 4. DEVAM EDİLEBİLİRLİK

Her faz sınırında `KOSU_KIMLIGI` yeniden basılır. Sohbet ölürse yeni bir sohbete
`000_ONCE_BUNU_YAPISTIR.md` + `DEVAM: <kimlik>` + KEEP listesi yapıştırılır; araç
son tamamlanan fazdan sürer ve **hangi fazdan sürdüğünü yazar**.

Kullanıcı hiçbir şeyi saklamadıysa araç yine de baştan tam bir koşu yapar ve
"devam kaydı bulunamadı, baştan başlandı" satırını rapora yazar.
