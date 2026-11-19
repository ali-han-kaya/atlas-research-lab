> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# PROFİL: GIRISIM

Ortak çekirdeğe **ek** kontroller. Koşmayan kontrol `CALISTIRILMADI` = `P1`.

**Bu profil bir yatırım tavsiyesi üretmez.** Yalnızca iddiaların kanıtla
eşleşip eşleşmediğini ve aritmetiğin tutup tutmadığını ölçer.

---

## CHK-IDDIA-KAYNAK — her sayının bir kaynağı olmalı

Belgedeki **her sayısal iddia** için kaynak sütunu doldurulur:

| İddia | Değer | Kaynak | Tür | Durum |
|---|---|---|---|---|
| Pazar büyüklüğü | 4,2 mlr € | <rapor adı, yıl, sayfa> | ikincil | `DOGRULANDI` / `UNVERIFIED_SOURCE` |

Kaynağı olmayan her sayı → `CLAIM_UNSUPPORTED` `P1`.
Kaynağı **var ama erişilemiyor** → `UNVERIFIED_SOURCE`, `P0` değil.
Kaynağı **uydurma** (var olmayan rapor/kurum) → `FACTUAL_ERROR` `P0`.

## CHK-PAZAR — pazar büyüklüğü türetimi

- TAM / SAM / SOM ayrı ayrı tanımlı mı, yoksa tek bir büyük sayı mı verilmiş?
- **Yukarıdan aşağı** (rapor sayısı × pay) ve **aşağıdan yukarı** (müşteri sayısı
  × fiyat) türetimleri **birbirini tutuyor mu**? Aralarında 3 kattan fazla fark
  varsa → `LOGICAL_ERROR` `P1`, ikisini de göster.
- SOM, elde edilebilir pazar payı gerekçesiyle mi hesaplanmış, yoksa "%1'ini
  alsak" ile mi? İkincisi → `CLAIM_UNSUPPORTED` `P1`.
- Coğrafi ve zamansal kapsam belirtilmiş mi? (hangi ülke, hangi yıl)

## CHK-BIRIM-EKONOMI — aritmetik

Şu beş büyüklük varsa yeniden hesapla ve tutarlılığı kontrol et:

| Büyüklük | Kontrol |
|---|---|
| Müşteri edinme maliyeti (CAC) | pazarlama gideri ÷ yeni müşteri — dönem aynı mı? |
| Yaşam boyu değer (LTV) | ARPU × brüt marj × ömür — ömür churn'den mi türetilmiş? |
| LTV/CAC | verilen oran, verilen LTV ve CAC'den çıkıyor mu? |
| Geri ödeme süresi | CAC ÷ aylık katkı payı — tutuyor mu? |
| Runway | nakit ÷ net aylık yakım — hangi ay, hangi yakım? |

Verilen oran, verilen bileşenlerden çıkmıyorsa → `FACTUAL_ERROR` `P0`.
Brüt marj ile net marj karıştırılmışsa → `P0`.
Yıllık ↔ aylık dönem karışımı → `P0` (en sık sessiz hata).

## CHK-RAKIP — rakip iddiaları doğrulanabilir mi

- "İlk", "tek", "lider", "en hızlı" gibi üstünlük iddiaları var mı? Her biri için
  kaynak ve ölçüt gerekir. Yoksa → `CLAIM_UNSUPPORTED` `P1`.
  (Hukuki not: bazı pazarlarda kanıtsız üstünlük iddiası reklam mevzuatına takılır.)
- Rakip karşılaştırma tablosu adil mi? Rakibin güçlü olduğu boyutlar tabloda var mı?
  Yoksa **seçici kanıt** → `LOGICAL_ERROR` `P1`.
- "Rakibimiz yok" iddiası → neredeyse her zaman `P1`; alternatif çözüm (Excel,
  elle yapma, hiç yapmama) rakiptir.

## CHK-YASAL — uyum bayrakları (tespit, tavsiye değil)

Şu tetikleyicilerden biri varsa **bayrak kaldır ve uzman gerekliliğini yaz**:

| Tetikleyici | Bayrak |
|---|---|
| Kişisel veri işleniyor | veri koruma yükümlülükleri — hukuk görüşü gerekir |
| Sağlık/bakım verisi veya sağlık iddiası | özel kategori veri + olası tıbbi cihaz sınıflandırması |
| Yapay zekâ çıktısı son kullanıcıya gösteriliyor | yapay zekâ şeffaflık yükümlülüğü |
| Ödeme/finans akışı | finansal düzenleme + lisans sorusu |
| Çocuklara yönelik | ek koruma yükümlülükleri |
| Sınır ötesi veri aktarımı | aktarım mekanizması sorusu |

**Kural:** "uyumludur" / "GDPR-konform" / "yasal engel yok" ifadelerini **yazma**.
Doğrusu: `VERIFY REQUIRED — <hangi uzman>, <hangi soru>`.
Uyum beyanı bir hukuk görüşü gerektirir; bu araç hukuk görüşü vermez.

## CHK-VAAT — sunulan ile yapılan arasındaki mesafe

Belgede geçen her özellik/vaat için: **şu an var mı, geliştirme aşamasında mı,
planda mı?** Üç durum karışıksa → `P1`.
"Kullanıyor" ↔ "pilot" ↔ "ilgilendi" ayrımı net mi? Müşteri sayısı iddiası hangi
tanıma dayanıyor?
Gelecek zaman kipi ile geçmiş zaman kipi karışmış mı? (`entegre ediyoruz` vs
`entegre edildi`)

## KORUMA — bu profilde korumalı türler

Her sayı+birim+dönem · kaynak künyeleri · varsayım listeleri · risk maddeleri ·
rakip tablosu satırları · yasal bayraklar.

**Bu profilde özel kural:** bir risk maddesinin veya varsayımın "sunumu
zayıflatıyor" gerekçesiyle silinmesi `DATA_LOSS` `P0`'dır ve otomatik kapatılamaz.
Yatırımcıya gösterilecek bir belgeden risk çıkarmak, bu araçla yapılamaz.
