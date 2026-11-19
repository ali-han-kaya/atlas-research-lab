> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# PROFİL: BELGE

Ortak çekirdeğe **ek** kontroller. Rapor, teklif, blog yazısı, başvuru metni,
teknik doküman, sunum notu, e-posta taslağı. Koşmayan kontrol `CALISTIRILMADI` = `P1`.

---

## CHK-IDDIA — iddia ↔ kanıt

Her önemli cümleyi sınıflandır: `OLGU` / `YORUM` / `TAVSIYE` / `VAAT` / `SPEKULASYON`.

- `OLGU` etiketli her cümlenin bir kaynağı olmalı. Yoksa → `CLAIM_UNSUPPORTED` `P1`.
- `TAVSIYE` cümleleri hangi olguya dayandığını göstermeli.
- `VAAT` cümleleri (taahhüt, teslim tarihi, sonuç garantisi) ayrıca işaretlenir;
  gerçekleştirilebilirliği belirsizse `P1` + uyarı.
- Kaynağı olmayan sayı, tarih, yüzde veya isim → `CLAIM_UNSUPPORTED` `P1`.

## CHK-TERIM — terim ve ton tutarlılığı

- Aynı kavram tek terimle mi anılıyor? (`yapay zekâ` / `YZ` / `AI` karışımı → `P1`)
- Kısaltma ilk kullanımda açılmış mı, sonra tutarlı mı?
- Hitap tutarlı mı? (`siz` / `sen` / edilgen karışımı → `P1`)
- Zaman kipi tutarlı mı? (yapıldı / yapılıyor / yapılacak karışımı → `P1`)
- Sayı biçimi tutarlı mı? (`1.500` ↔ `1500` ↔ `bin beş yüz`)

## CHK-YAPI — yapı ve gezinilebilirlik

- Başlık hiyerarşisi atlamasız mı? (H1→H2→H3)
- Başlıklar benzersiz mi? Tekrar eden başlık → `P2`.
- Her başlık altındaki içerik başlığı karşılıyor mu?
- Paragraf uzunluğu okunabilir mi? (tek cümlelik ve 15+ cümlelik paragraflar → `P2`)
- İç referanslar (`yukarıda`, `Bölüm 3'te`, `Tablo 2`) gerçekten var olan şeylere
  mi işaret ediyor? Kırık referans → `P1`.
- Liste ve tablolar biçimsel olarak geçerli mi?
- Belgenin ilk 5 satırı okuyucunun "bu benim işime yarar mı" sorusunu cevaplıyor mu?

## CHK-KITLE — hedef kitle uyumu

Önce **hedef kitleyi tespit et ve yaz** (belgeden çıkar; belirsizse `UNKNOWN`
yazıp en geniş kitleyi varsay).

Sonra ölç:
- Kitlenin bilmediği varsayılan jargon açıklanmadan kullanılmış mı?
- Kitlenin zaten bildiği şey gereksiz açıklanmış mı? (yer israfı, `P2`)
- İstenen eylem (`call to action`) net mi ve tek mi?
- Belge uzunluğu kitlenin ayıracağı süreyle uyumlu mu? (kaba ölçü: 200 kelime/dk)
- Kanal doğru mu? (e-posta olması gereken bir şey 12 sayfalık rapor olmuş mu)

## CHK-MANTIK — akıl yürütme kusurları

- Non sequitur: sonuç öncüllerden çıkmıyor.
- Kategori hatası: yöntemsel bir ifade bulgu gibi sunulmuş.
- Yanlış ikilem: ikiden fazla seçenek varken iki seçenek sunulmuş.
- Döngüsel gerekçe: iddia kendisiyle destekleniyor.
- Korelasyon → nedensellik atlaması.
- Kapsam aşımı: örneklem küçük, genelleme geniş.
- Gizli varsayım: sonucun dayandığı ama hiç yazılmamış öncül.

Her biri `LOGICAL_ERROR`; belgenin ana savını çürütüyorsa `P0`, yan argümanı
zayıflatıyorsa `P1`.

## CHK-DENGE — karşı görüş ve seçici sunum

- Belgenin savına karşı en güçlü itiraz ele alınmış mı? Alınmamışsa `P1`.
- Destekleyici kanıt seçilip aleyhte kanıt atlanmış mı? → `LOGICAL_ERROR` `P1`.
- Belirsizlik dürüstçe ifade edilmiş mi, yoksa kesinlik diliyle mi örtülmüş?
- Sınırlılıklar bölümü var mı ve gerçek sınırları mı yazıyor?

## CHK-EYLEM — kesi testi

Belgeyi bitirince tek soru sor ve cevabını rapora yaz:

> **"Bu belgeyi okuyan kişi yarın bunu kullansa, nerede tıkanır?"**

Cevap somut bir eksik gösteriyorsa (eksik adım, eksik bilgi, eksik yetki, eksik
kaynak) bu bir bulgudur — `P1`.

## KORUMA — bu profilde korumalı türler

Her sayı, tarih, isim, kurum · birebir alıntılar · kaynak künyeleri · şart ve
istisna cümleleri ("ancak", "hariç", "koşuluyla") · sorumluluk sınırlaması
ifadeleri · sınırlılık maddeleri · yasal uyarılar.

**Bu profilde özel kural:** bir şart/istisna cümlesinin ("... koşuluyla",
"... hariç") "akıcılık için" silinmesi anlamı tersine çevirebilir. Bu tür
kayıplar `DATA_LOSS` `P0`'dır ve otomatik kapatılamaz.
