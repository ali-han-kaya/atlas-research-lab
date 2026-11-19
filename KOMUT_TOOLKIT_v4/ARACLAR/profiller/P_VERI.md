> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# PROFİL: VERI

Ortak çekirdeğe **ek** kontroller. Koşmayan kontrol `CALISTIRILMADI` = `P1`.

---

## CHK-SEMA — şema ve tip tutarlılığı

- Sütun adları tekil mi, boşluk/Türkçe karakter/büyük-küçük karışımı var mı?
- Her sütunun tipi satırlar boyunca tutarlı mı? (bir sütunda hem `12`, hem `12,5`,
  hem `on iki` → `SCHEMA_INVALID` `P1`)
- Tarih biçimi tek mi? (`2026-08-17` ↔ `17.08.2026` ↔ `08/17/26` karışımı → `P1`)
- Ondalık ayracı tek mi? (`1.234,5` ↔ `1,234.5` karışımı → `P0`, sessiz
  büyüklük hatası üretir)
- Karakter kodlaması tek mi? Bozuk karakter (`Ã¼`, `ÅŸ`) var mı → `P1`.
- Satır sayısı beyan edilenle aynı mı?

## CHK-EKSIK — eksik değer profili

Her sütun için: eksik oranı, eksikliğin **deseni** (rastgele mi, bir grupta mı
yoğunlaşmış mı), eksik değerin nasıl kodlandığı (`NaN`, boş, `-`, `999`, `0`).

**Kilit tuzak:** eksikliği `0` veya `-1` ile kodlamak, ortalamayı sessizce bozar
→ `FACTUAL_ERROR` `P0` (eğer o sütun bir hesaba giriyorsa).
Eksik değer stratejisi (sil / doldur / bırak) belgelenmiş mi? Değilse `P1`.

## CHK-BIRIM — birim ve ölçek tutarlılığı

- Aynı büyüklük farklı birimlerde mi kayıtlı? (kg ↔ lb, €↔$, saniye ↔ ms)
- Yüzde mi oran mı? (`0.15` ↔ `15` aynı sütunda → `P0`)
- Para birimi ve dönemi belirtilmiş mi? (nominal ↔ reel, hangi yıl fiyatı)
- Ölçek dönüşümü yapılmışsa katsayısı yazılı mı?

## CHK-ARITMETIK — toplam ↔ parça

- Alt gruplar toplamı genel toplamı veriyor mu?
- Yüzdeler 100'e (veya beyan edilen paydaya) toplanıyor mu? Yuvarlama farkı
  belirtilmiş mi?
- Türetilmiş sütunlar (oran, fark, büyüme) formülüyle yeniden hesaplandığında
  aynı çıkıyor mu? Rastgele 5 satır seç ve **elle doğrula**, sonucu kanıt yaz.
- Zaman serisinde kümülatif ↔ dönemsel tutarlı mı?

## CHK-AYKIRI — aykırı değer beyanı

- Sayısal sütunlarda min/maks makul aralıkta mı? (yaş = 250, tarih = 1900)
- Aykırı değerler çıkarılmışsa **ölçütü önceden mi belirlenmiş**? Post hoc
  çıkarma → `P1` + şeffaflık notu.
- Yinelenen satır var mı? Yineleme kasıtlı mı?
- Sıfır varyanslı sütun var mı (tek değer)? Analize giriyorsa `P1`.

## CHK-IZLENEBILIRLIK — kaynak ve dönüşüm zinciri

Her sütun için: nereden geldi, hangi dönüşümden geçti, kim/ne zaman üretti.
Ham veri ile işlenmiş veri ayrı mı tutuluyor?
Dönüşüm kodu var mı, yoksa elle mi yapılmış? Elle yapılan dönüşüm → `P1`
(tekrar üretilemez).

**Kilit kural:** ham veriye geri dönülemiyorsa bu `INDETERMINATE`'dir — hiçbir
sonuç doğrulanamaz.

## CHK-GIZLILIK — kişisel veri bayrakları

Doğrudan tanımlayıcı (ad, e-posta, telefon, TCKN, IBAN, IP) var mı?
Dolaylı tanımlayıcı kombinasyonu (posta kodu + doğum tarihi + cinsiyet) yeniden
tanımlamaya izin veriyor mu?
Özel kategori veri (sağlık, biyometrik, din, etnisite, ceza kaydı) var mı?

**Özel kategori veri bulunursa koşu otomatik devam etmez** — bu, tabanda
tanımlı yedi otomatik-olmayan karardan biridir. Duruş ver, insana sor.

## KORUMA — bu profilde korumalı türler

Satır sayısı · sütun adları ve sırası · her sayısal değer · birim etiketleri ·
eksik değer kodları · veri sözlüğü girdileri · dönüşüm adımları.

**Bu profilde özel kural:** "temizlik" adı altında satır silmek varsayılan olarak
`DATA_LOSS` `P0`'dır. Silinen her satır grubu için sayı + ölçüt + gerekçe
yazılmadıkça kabul edilmez. `n` değişiyorsa bu her zaman rapora çıkar.
