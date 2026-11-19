> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# C3 — SINIFLANDIRICI (normatif kaynak)

Kullanıcı ne yapmak istediğini **anlatmaz**. Çalışmasını koyar. Tipi bu tablo bulur.

---

## 1. KARAR TABLOSU — sırayla değerlendir, İLK EŞLEŞEN KAZANIR

| # | Sinyal | Tip |
|---|---|---|
| 1 | Bağımlılık manifestosu var (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile`, `composer.json`) **veya** çalıştırılabilir kaynak dosya oranı > %40 | `KOD` |
| 2 | Kaynakça bölümü var **ve** (DOI / arXiv / BibTeX / `(Yazar, Yıl)` deseni) **veya** IMRaD başlıkları (Giriş–Yöntem–Bulgular–Tartışma) | `AKADEMIK` |
| 3 | `.csv` / `.parquet` / `.xlsx` / satır-tabanlı `.json` ağırlıklı, düzyazı < %20 | `VERI` |
| 4 | Pazar, müşteri, gelir, runway, pitch, rakip, ekip, fiyatlandırma terimleri ≥ 3 farklı başlıkta | `GIRISIM` |
| 5 | Hiçbiri, düzyazı ağırlıklı | `BELGE` |

Sıra normatiftir. `KOD` her zaman `GIRISIM`'i ezer (pitch içeren bir depo koddur).
Bu bilinçli bir tavizdir; alternatifi koşular arası kararsızlıktır.

## 2. ÇIKTI — koşunun ilk bloğu, atlanamaz

```
TIP=<KOD|AKADEMIK|VERI|GIRISIM|BELGE> | SINYAL=<kural no + dosya/kanit> | GUVEN=<YUKSEK|DUSUK>
```

`GUVEN=DUSUK` koşulu: iki tipin sinyali birden var, **veya** hiçbir sinyal yok.

## 3. DÜŞÜK GÜVEN DAVRANIŞI — birleşim, kesişim değil

`GUVEN=DUSUK` ise:

1. **Aday tiplerin zorunlu kontrollerinin BİRLEŞİMİ koşar** (kesişimi değil).
   Karar en katı sonuca göre verilir.
2. Kullanıcıya **tek** soru sorulur (duruş 1/3), ama **cevap beklenmeden** ortak
   çekirdek çalışmaya devam eder.
3. Kullanıcı tek kelimeyle düzeltirse yalnız **profil kuyruğu** yeniden koşar;
   ortak çekirdek çıktıları korunur.

> Gerekçe (ölçülmüş): yanlış sınıflandırma yalnızca "yanlış araç" hatası değildir,
> **sessiz kapı düşürmedir**. Uydurma DOI'li ve `n=12` ile `p<0.001` iddia eden bir
> akademik metin `KOD` hattına verildiğinde arşiv kapısı hiçbir kusur bulamaz ve
> olumlu karar verir — çünkü atıf ve iddia kontrolleri o hatta hiç yoktur.
> Birleşim kuralı bu deliği kapatır: belirsizlikte maliyet artar, ama yanlış tipe
> olumlu karar vermekten ucuzdur.

## 4. ZORUNLU KONTROLLER (tip başına)

Çalıştırılmayan bir zorunlu kontrol `CALISTIRILMADI` olarak kayda geçer, `P1`
sayılır ve `OLCULMEYEN` bölümüne düşer. Sessizce atlanamaz.

| Tip | Zorunlu kontroller |
|---|---|
| `KOD` | ORTAK + sır taraması, bağımlılık/lisans, dışa açık imza envanteri, test kanıtı (attestation), hata yolu incelemesi, README↔gerçeklik |
| `AKADEMIK` | ORTAK + atıf↔kaynakça çift yönlü, DOI biçim/erişim, iddia↔kanıt haritası, istatistik iç tutarlılık, yöntem tekrar-üretilebilirlik, etik/veri beyanı |
| `VERI` | ORTAK + şema/tip tutarlılık, eksik-değer profili, birim/ölçek tutarlılık, toplam-parça aritmetiği, aykırı değer beyanı, veri kaynağı izlenebilirlik |
| `GIRISIM` | ORTAK + sayısal iddia↔kaynak, pazar büyüklüğü türetimi, rakip iddiası doğrulanabilirlik, yasal/uyum bayrakları, birim ekonomi aritmetiği |
| `BELGE` | ORTAK + iddia↔kanıt, terim tutarlılık, yapı/başlık bütünlüğü, hedef kitle uyumu |

**ORTAK ÇEKİRDEK** (her tipte koşar):
koruma envanteri (C2), veri sınırı taraması, iç tutarlılık (sayı/terim/mantık),
çapraz referans bütünlüğü, ölçülmeyenin beyanı.

## 5. YANLIŞ SINIFLANDIRMA MALİYETİ

Ortak çekirdek her tipte koştuğu için yanlış tip **tüm koşuyu değil, yalnız
kuyruğu** boşa harcar. Yeniden koşan iş toplamın ≤ %25'i olmalıdır. Sınıflandırma
raporun ilk sayfasında görünür ve tek kelimeyle düzeltilebilir.
