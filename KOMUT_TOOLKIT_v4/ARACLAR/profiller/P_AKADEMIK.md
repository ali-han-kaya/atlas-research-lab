> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# PROFİL: AKADEMIK

Ortak çekirdeğe **ek** kontroller. Her kontrol bir `CHK-` kaydı üretir; koşmayan
kontrol `CALISTIRILMADI` = `P1` olur ve `OLCULMEYEN`'e düşer.

---

## CHK-ATIF — atıf ↔ kaynakça çift yönlü

- Metindeki her atıf kaynakçada var mı? (yoksa: **öksüz atıf** → `CITATION_MISSING` `P1`)
- Kaynakçadaki her kayıt metinde kullanılmış mı? (kullanılmamış → `P2`)
- Yazar adı yazılışı her yerde aynı mı? (`Akın, A.` / `Akın` / `Akin` karışımı → `P1`)
- Yıl metin ↔ kaynakça tutarlı mı? (farklı → `P1`)
- **Uydurma kaynak kontrolü:** dergi adı + cilt + yıl + sayfa üçlemesi kendi
  içinde tutarlı mı? Var olmayan bir dergi-cilt kombinasyonu → `FACTUAL_ERROR` `P0`.

## CHK-DOI — biçim ve erişim

- Biçim: `10.\d{4,9}/\S+` desenine uyuyor mu? Uymuyorsa `CITATION_MISSING` `P1`.
- **MODE-A + ağ:** her benzersiz DOI için gerçek istek. HTTP 200 → `DOGRULANDI`;
  200 dışı **gerçek yanıt** → `FACTUAL_ERROR` `P0`; ağ hatası (istisna) →
  `UNVERIFIED_SOURCE`, **`P0` değil** — doğrulanamamak, yanlış olmakla aynı şey değil.
- **MODE-B:** yalnız biçim. Her DOI `UNVERIFIED_SOURCE` etiketli kalır. Erişim
  doğruladığını **yazma**.
- DOI seçimi deterministik olsun (sıralı), rastgele örnekleme yapma.

## CHK-IDDIA — iddia ↔ kanıt haritası

Her önemli iddiayı sınıflandır ve kanıtını eşle:

| Sınıf | Kanıt gereksinimi |
|---|---|
| `OLGU` | birincil kaynak veya ölçüm |
| `YORUM` | gerekçe + alternatif yorumun ele alınması |
| `YONTEMSEL` | yöntem bölümünde tanımlı olmalı |
| `HIPOTEZ` | test edilebilir ifade + test sonucu |
| `ALINTI` | tırnak + sayfa numarası |
| `CIKARIM` | dayandığı öncüller açık |
| `SPEKULASYON` | açıkça "spekülatif" etiketli |
| `SONUC` | bulgulara dayanmalı, bulgulardan geniş olamaz |

**Desteksiz kritik iddia → `CLAIM_UNSUPPORTED` `P0`.** Finale geçemez.
**Kapsam aşımı:** sonuç, bulguların desteklediğinden geniş bir genelleme yapıyorsa
→ `LOGICAL_ERROR` `P1` ("tüm Almanya'da uygulanabilir" ↔ `n=12` tek merkez).

## CHK-ISTATISTIK — iç tutarlılık

- Aynı istatistik her yerde aynı değer mi? (χ²=13.23 vs 13.232 → `P1` hassasiyet)
- `N` alt kırılımları toplamı tutuyor mu? (4250 = 4068+182 → doğrula)
- Oran/yüzde aritmetiği doğru mu? (%9.61 = 147/1529 → doğrula)
- Güven aralığı sınırları mantıklı mı? (alt < ortalama < üst)
- Test istatistiği ↔ serbestlik derecesi ↔ p-değeri birbiriyle tutarlı mı?
- Etki büyüklüğü ↔ güven aralığı ↔ p-değeri **aynı yönü** mü gösteriyor?
- `p < 0.05` deniyor ama güven aralığı sıfırı içeriyor mu? → `LOGICAL_ERROR` `P0`
- Ondalık hassasiyeti tutarlı mı? (2 ↔ 3 ondalık karışımı → `P2`)
- Çoklu karşılaştırma yapılmış ama düzeltme (Bonferroni/FDR) anılmamış mı? → `P1`

**Alan-özel uyarı:** bu kontrollerin ölçütü kullanılan **yönteme göre** yeniden
yazılır. χ² tabanlı bir ölçüt Bayes faktörü kullanan bir çalışmada anlamsızdır.
Yöntem farklıysa ölçütü uyarlamak ve bunu rapora yazmak zorunludur.

## CHK-YONTEM — tekrar üretilebilirlik (9 madde, hepsi cevaplanır)

1. Araştırma sorusu net ve tek mi?
2. Örneklem seçimi ve büyüklük gerekçesi var mı? Güç analizi?
3. Değişkenler operasyonel olarak tanımlı mı?
4. Veri toplama prosedürü başkası tarafından tekrarlanabilir mi?
5. Dışlama/dahil etme ölçütleri önceden mi belirlenmiş?
6. Analiz planı önceden mi (pre-registration) yoksa post hoc mu?
7. Eksik veri nasıl ele alınmış? Belirtilmiş mi?
8. Kod/veri erişilebilir mi? Erişilemiyorsa gerekçesi yazılı mı?
9. Sınırlılıklar bölümü gerçek sınırları mı yazıyor, yoksa kozmetik mi?

Cevaplanmayan her madde `CALISTIRILMADI` olarak kayda geçer.

## CHK-ETIK — etik ve veri beyanı

- Etik kurul onayı bölümü var mı? Onay numarası veya "gerekmedi" gerekçesi?
- İnsan/hayvan verisi varsa aydınlatılmış onam beyanı?
- Kişisel veri işleniyorsa hukuki dayanak ve saklama süresi?
- Çıkar çatışması ve finansman beyanı?
- Yapay zekâ kullanımı beyan edilmiş mi (dergi politikası gereği)?

**Kilit kural:** etik onay açık/beklemedeyken metinde "yayına hazır",
"submission-ready", "kesin sonuç" **kullanılamaz** → `LOGICAL_ERROR` `P0`.
Doğrusu: "çalışma tamamlandı, etik onay bekliyor".

## CHK-DIL — akademik dil (yalnız `P1`/`P2`)

Birinci tekil şahıs; belirsiz zarflar (`çok`, `oldukça`, `son derece`) kantitatif
karşılığı olmadan; bağlamsız değer yargıları (`önemli`, `ilginç`); 40+ kelimelik
alıntıda tırnak+sayfa eksikliği; kısaltmanın ilk kullanımda açılmaması;
başlık hiyerarşisi atlama (H1→H3).

## KORUMA — bu profilde korumalı türler

Atıf ve kaynakça kayıtları · her sayı+birim · tablo satırları · tanım cümleleri ·
birebir alıntılar · yöntem adımları · sınırlılık maddeleri.

Bunların kaybı `BEYAN_EDILDI` olsa bile otomatik kapatılamaz — insan onayı ister.
Bir sınırlılık maddesinin "akış için" silinmesi, bu profildeki en ağır ihlaldir.
