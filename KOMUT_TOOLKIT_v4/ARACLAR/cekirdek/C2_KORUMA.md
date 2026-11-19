> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# C2 — KORUMA SÖZLEŞMESİ (normatif kaynak)

**Bu bölüm paketteki diğer tüm talimatları ezer.** Bir çelişki varsa koruma kazanır.

Amaç tek cümle: *iyileştirme adı altında kaliteli içerik kaybolmayacak.*

---

## 1. VARSAYILAN İŞLEM: EKLEME, YENİDEN YAZMA DEĞİL

Bir bölüme dokunmak için o bölüme ait **en az bir P0 veya P1 bulgu** ve o bulgunun
**birebir kanıt satırı** gerekir. Kanıtı olmayan bölüme dokunulmaz.

- Sadeleştirmek bir gerekçe değildir.
- Özetlemek bir gerekçe değildir.
- "Gereksizdi" bir gerekçe değildir.
- "Akış daha iyi oldu" bir gerekçe değildir.

**Belirsizlikte KORU.** Bir içeriğin değerli olup olmadığından emin değilsen
silme; `UNKNOWN_DEGER` etiketiyle yerinde bırak ve rapora yaz.

## 2. KEEP KAYDI — birebir metin DEĞİL, bölüm parmak izi

Başlamadan önce, girdideki **her bölüm** için tek satır üret:

```
KEEP-<NNN> | <konum> | sha256:<16 hex> | <karakter sayisi> | <cumle sayisi>
```

`sha256` şu normalizasyondan **sonra** hesaplanır:

1. Unicode NFC
2. Ardışık boşluk → tek boşluk, satır sonu boşlukları at
3. Tipografik tırnak/kesme (`“ ” ‘ ’ „ « »`) → ASCII (`" '`)
4. Uzun tire/kısa tire varyantları (`— – −`) → `-`
5. Baştan/sondan boşluk at

> **Neden birebir metin değil:** birebir metni kırpmak (ör. ilk 200 karakter)
> bir çapa değil, bir ön ektir. Ölçülmüş saldırı: 1247 karakterlik bir bölümün
> ilk 200 karakteri korunup gerisi silindiğinde ve yerine "(bu bölüm
> özetlenmiştir)" yazıldığında, ön ek tabanlı koruma **GEÇTİ** verir; gerçek
> kayıp %84'tür. Ayrıca birebir metin bağlam maliyetini patlatır: 19 bin
> karakterlik bir hukuk belgesinde birebir KEEP listesi belgenin **1,11 katı**
> yer kaplar; 200 sayfalık bir tezde liste bağlama sığmaz, model listeyi kısaltır
> ve koruma **tam da en gerekli olduğu yerde** çöker. Parmak izi tabanlı kayıt
> bölüm başına tek satırdır; 200 sayfalık tezde toplam maliyet belgenin ~%2'sidir.

## 3. KARŞILAŞTIRMA KURALI

Çıktıdaki her bölüm için KEEP kaydıyla karşılaştır:

| Durum | Karar |
|---|---|
| Hash eşleşiyor | `KORUNDU` — hiçbir şey yapma |
| Hash farklı, karakter ≥ %95, cümle ≥ %95 **ve** içerik kelimesi ≥ %70 | `CONTENT_CHANGED` → `P1`, farkı göster |
| Hash farklı **ve** içerik kelimesi tutma oranı < %70 | `CONTENT_LOST` → `P0` — **hacim anlam değildir** |
| Hash farklı **ve** (karakter < %95 **veya** cümle < %95) | `CONTENT_LOST` → `P0` |
| KEEP kaydı çıktıda hiç yok | `CONTENT_LOST` → `P0` |
| KEEP listesi boş **veya** girdideki bölüm sayısından az | `CONTRACT_INCOMPLETE` → `P0` |

> **Hacim anlam değildir (ölçülmüş saldırı).** Bir bölüm aynı uzunlukta kalıp
> içeriği dolgu metniyle değiştirilebilir: "Sınırlılıklar" bölümü aynı karakter
> ve cümle sayısında bir övgü paragrafına çevrildiğinde, salt oran testi bunu
> `P1` sayar. Bu yüzden **içerik kelimesi tutma oranı** ayrıca ölçülür: girdideki
> anlamlı kelimelerin yüzde kaçı çıktıda hâlâ duruyor? %70'in altı `P0`'dır.

**Sessiz değer değişimi kaybın üstündedir:** aynı konumda hem girdide hem çıktıda
var olan bir sayı/tarih/isim **farklı değere** dönmüşse bu `P0`'dır, oran ne
olursa olsun. Silmek görülür; değiştirmek görülmez.

**Tek istisna:** o konumu kapsayan **imzalı** bir `SILME_NIYETI` kaydı varsa
şiddet `P1`'e iner — ama bulgu **rapordan silinmez**; gerekçe ve imza raporda
görünür. Yani değişim artık "sessiz" değildir. Gürültülü bir kapı bypass edilir;
kapatılabilir ama izsiz kapanmayan bir kapı hem kullanılır hem korur.

## 4. TABAN ÇİZGİSİ HER ZAMAN ORİJİNALDİR

Karşılaştırma **daima F0'daki orijinal girdiye** karşı yapılır, bir önceki
turun çıktısına karşı **asla**. Aksi hâlde her turda %4 kayıp her turda geçer ve
beş turda içeriğin beşte biri sessizce yok olur.

## 5. MEŞRU KAYIP — beş yol, hepsi kayıtlı

Bir kayıp yalnızca şunlardan biriyse meşrudur:

| Sınıf | Koşul |
|---|---|
| `BIRLESTIRILDI` | Kaybolan içerik, korunan başka bir bölümün içinde bulunuyor (benzerlik ≥ %90) |
| `TEKRARDI` | Girdide birden fazla kez geçiyordu, en az biri duruyor |
| `BULGUYA_BAGLI` | Konumu bir P0/P1 bulgunun konumuyla örtüşüyor **ve** ona bağlı bir `FIX-` kaydı var |
| `BEYAN_EDILDI` | `SILME_NIYETI` kaydında konum + gerekçe + **insan imzası** var |
| `SABLON` | Otomatik üretilen içerik (içindekiler tablosu, üstbilgi/altbilgi, lisans başlığı) |

Bunların dışındaki her kayıp `BEYANSIZ`'dır ve **P0**'dır.

> **İmza şarttır (ölçülmüş saldırı).** `onay: true` alanı tek başına geçerli
> değildir, çünkü o alanı modelin kendisi yazabilir. Beyan edilmiş bir silme
> bir **insan kaydıdır**: konum + gerekçe + boş olmayan `imza` alanı gerekir.
> İmzasız kayıt `UNSIGNED_WAIVER` sayılır ve kaybı meşrulaştırmaz.

**Korumalı türler** — `BEYAN_EDILDI` olsa bile otomatik kapatılamaz, insan onayı ister:
atıf/kaynak, sayı+birim, test adı veya sayısı, dışa açık fonksiyon/sınıf imzası,
yapılandırma anahtarı, bağımlılık adı+sürümü.

## 6. HEDEFLİ YENİDEN DENEME (dondurulmuş bölgeler)

Bir bulgu düzeltilirken **yalnız o bulgunun `location` alanındaki bölüm** yeniden
yazılır. Diğer bölümler `DONDURULMUS` ilan edilir.

- Düzeltmeden önce dondurulmuş bölgelerin hash'i kaydedilir.
- Düzeltmeden sonra yeniden hesaplanır.
- Eşleşmiyorsa `SCOPE_VIOLATION` → `P0` → **değişiklik geri alınır**, yeniden denenmez.

Global yeniden yazım yasaktır. "Tümünü baştan yazdım, daha iyi oldu" bir
düzeltme değil, bir koruma ihlalidir.

## 7. EKLEME KONTROLÜ (anti-halüsinasyon)

Çıktıda girdide olmayan yeni bir **atıf, DOI, sayı veya istatistik** varsa ve
kaynağı ne girdide ne de sağlanan kanıtta bulunuyorsa: `CLAIM_UNSUPPORTED` → `P1`
+ `KAYNAKSIZ_EKLEME` etiketi. Koruma yalnızca silmeye değil, **uydurmaya** da bakar.

## 8. ÖLÇÜLEMEZLİK = ENGEL

Zorunlu sayılan bir birim türü için girdide **sıfır** birim çıkarıldıysa
(örnek: 40 sayfalık akademik metinde 0 atıf bulunması), bu "temiz" değil
**`BELIRSIZ`** demektir ve `P0` sayılır. Hiçbir şey çıkaramayan bir ölçüm asla
olumlu karar üretmez.

## 9. İKİ ZORUNLU ÖZ-TEST

Koruma kapısı yayınlanmadan önce bunları geçmek zorundadır:

1. **Mutasyon testi:** Girdiden mekanik olarak bir atıf, bir dışa açık fonksiyon
   ve bir sayı silinir. Kapı **tam olarak o üç kaybı** `P0` olarak, doğru konumla
   raporlamalıdır. Raporlamıyorsa kapı bozuktur.
2. **Kimlik testi:** Çıktı girdiyle bit-bit aynıyken kapı **sıfır** bulgu
   vermelidir. Vermiyorsa yanlış pozitif oranı kabul edilemez.

Her ikisi `v4_selftest.py` içinde koşar ve başarısızsa paket yayınlanmaz.
