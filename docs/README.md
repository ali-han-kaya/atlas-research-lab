# docs/ — yayımlanan ölçüm ve öğrenim kayıtları

Bu klasör laboratuvarın **kendi üzerine** tuttuğu kayıtları taşır: canlı koşu
ölçümleri, denetim raporları, ders defteri ve kanonik olgu tablosu. Amaç, deponun
"biz iyiyiz" demesi değil, **hangi sayının hangi komuttan geldiğini** göstermesi.

## Nedir, ne değildir

| Dosya | Ne taşır |
|---|---|
| `OLGULAR.md` | Kanonik sayısal olgu tablosu. Çelişkide bu tablo kazanır; her satır birincil kayda bağlıdır. `atlas_selftest` bu dosyayı okur. |
| `DERSLER_v1_2026-08-30.md` | Öğrenim defteri: kabul **ve** reddedilen düzeltmeler, Δ_içeride / Δ_dışarıda ile. Reddedilen düzeltme yeniden açılmaz. |
| `OLCUM-01…07` | Canlı koşu ölçümleri: izin globlarının gerçek davranışı, tam koşu, düzeltme sonrası ölçüm, taze kurulum taraması, maliyet tahmini ↔ gerçekleşen. |
| `DENETIM-*` | Laboratuvarın kendisine yapılmış tam tarama ve sıfır gözle denetim raporları. |
| `MUTASYON_KOSUM.md` | Mutasyon koşusu: kural gerçekten yakalıyor mu, yoksa süs mü. |
| `CORRIGENDUM-*` | Kendi hatasının ilanı ve düzeltmesi. |

## Neden ayrı bir temiz depo

Bu depo, aynı laboratuvarın **özel** çalışma deposunun (`ATLAS_Research_Lab`,
artık **arşivli / salt okunur**) yayımlanabilir kısmıdır. Sıfırdan yeni bir depo açılmasının üç nedeni var:

1. **Kapsam:** özel depo üretilmiş makaleleri, konu korpuslarını ve oturum
   devirlerini taşır. Bu depo yalnız **mekanizmayı** taşır.
2. **Temiz geçmiş:** özel deponun 924 commit'lik tarihçesi yayımlanmaması gereken
   içerik ve bir kimlik bilgisi kaydı taşıyor. Geçmişi yeniden yazmak yerine temiz
   bir tarihçe başlatıldı; böylece buradaki her satır **bilinçli bir aktarım**.
3. **Lisans ve niyet:** özel depo kişisel çalışma sözleşmesine bağlıydı; bu depo
   MIT lisanslıdır ve başkasının kullanımına açıktır.

Eski depo arşivlendiği için push kabul etmez; tarihçeler **birleştirilmez**.
Aktarım yolu `tools/yayinla.py` ve kapsam tablosudur (aşağıda).

## Yayın kapsamı

**Dahil:** hatların mekanizması (ajanlar, komutlar, şablonlar, kapı betikleri),
üç öz-test paketi, mutasyon bataryası (`tools/mutasyon_bataryasi.py`), Toolkit v4
çekirdeği, kusurlu örnek koşu (`DENEME/`), yukarıdaki ölçüm ve ders kayıtları.

**Hariç — ve neden:**

| Ne | Neden |
|---|---|
| Laboratuvarın ürettiği makaleler, kitapçıklar, PDF'ler | Bu depo **üretim mekanizmasıdır**, ürün arşivi değil. |
| Konu korpusları (`KOMUT_TOOLKIT_v4/yahudikaynaklar/`, `moschiach/`, `sebatay-sevi-kaynaklari/`) | Araştırma malzemesi; mekanizmanın parçası değil. |
| `projeler/` | Devam eden/yayımlanmamış çalışmalar. |
| `docs/DEVIR-*` (oturum devirleri) | Kişisel çalışma bağlamı taşır; en az biri **kimlik bilgisi** (veritabanı bağlantı dizesi) içerir. Böyle bir dosya hiçbir koşulda yayımlanmaz. **Tek istisna:** kapıların pinlediği kanonik OLGU-06 devri `DEVIR-2026-09-03-1945-AUD-06-07.md` — kimlik bilgisi içermez, sürüm satırı ve OLGU-06 lint'i ona bağlıdır. |
| `SURUM.md` dışındaki iş günlükleri | `SURUM.md` **dahildir** (kapılar sürüm satırını oradan okur); proje-özel devir ve iş kayıtları hariçtir. |
| `gate/FINAL-GATE-*.json` | Bir **projenin** kapı hükmü; mekanizmanın değil. |
| `DENEME/gate/FINAL-GATE-v5.5.json` | **Bilinçli istisna:** kök `gate/` hükmü dışlanır, bu dosya ise `DENEME/` fikstürünün içindedir ve dondurulmuş yanlış `PASS`in kanıtıdır. Makale metni taşımaz (ölçüldü: `silat/makale` desenlerinde 0 eşleşme); yalnız kapı sayıları ve tarih. |
| Kök `scripts/` (kişisel exocortex bataryası) | 33 dosya yayımlanmayan `SKILL.md`'yi okur; ayrıca sahibinin mutlak yolunu (`KOK = '/Users/…'`) taşıyordu. Laboratuvarın kendi mekanizması ATLAS/KOD ağaçlarındaki `scripts/` klasörlerindedir; bu küme kişisel çalışma sözleşmesine aittir (kendi başlığı: *Proprietary*). |
| `silat-makale` gibi proje adları | Yalnız kod **yorumlarında** ("hangi gerçek koşuda ölçüldü" kanıtı) ve `SURUM.md` bakım kaydında geçer. Makale metni, PDF, veri dosyası yoktur; adı silmek ölçümün kanıt izini silmek olurdu. |

Bu sınır yüzünden `DERSLER` ve ölçüm dosyalarındaki bazı atıflar özel ağaçtaki
devir dosyalarını gösterir. Bu bir kırık bağ değil, **bilinçli yayın sınırıdır**:
kayıt yerinde durur, kanıtı özel ağaçta kalır.

## Mutasyon bataryası

Öz-test "kapı kodu doğru mu" sorusunu sorar; mutasyon bataryası başka bir soruyu
sorar: **kapı gerçekten kırmızıya dönüyor mu.** Her vaka kendi geçici kopyasında
çalışır ve üç adımı birlikte ister:

1. **Temiz taban** — ihlalsiz kopyada kapı `rc=0` vermeli.
2. **Tek ihlal** — aynı kopyada yalnız o kuralı kıran değişiklik yapılır.
3. **Kırmızı hüküm** — kapı `rc!=0` vermeli ve beklenen kural kimliğini basmalı.

Üçünden biri eksikse vaka `ATESLEMEDI` / `TABAN_KIRIK` olarak raporlanır ve betik
`rc=1` ile çıkar. Ölçülen kurallar ve hangi katmana ait oldukları çıktıda ada
basmadır; sayı README'ye elle yazılmaz.

**Neyi ölçmez:** kuralın *doğru tasarlandığını* ölçmez — yalnız kodun o ihlali
yakaladığını ölçer. Mutasyon uygulanamazsa (desen bulunamazsa) bu da sessiz
geçmez, `MUTASYON_UYGULANMADI` olarak kırmızı sayılır.

## CALISTIRILMADI kalemler

`make dogrula` üç öz-test paketini koşar. Verisi bu depoda bulunmayan bir kalem
**`CALISTIRILMADI`** olarak raporlanır — `PASS` değil, `KOSULLU` da değil: o kalem
koşmadı ve **hükme sayılmaz**. Her `CALISTIRILMADI` satırı nedenini yanında taşır.

Koşul serttir: kalan **bütün** test kimlikleri aşağıdaki açık listenin içinde
olmalı ve beklenen kanıt dizgisi çıktıda görünmelidir. Liste dışı tek bir test
kalırsa hüküm `FAIL`'dir; gerekçe başka bir hatayı örtmez.

| Test | Neyi ölçer | Neden koşmuyor | Nerede koşar |
|---|---|---|---|
| `OLG-1` (ATLAS) | `SURUM.md` makine bloğunun sürüm/commit/canlı ölçüm bağını (`OLGU-03/04/05`) | Bu depo özel ağacın commit zincirini ve canlı kanıt setini taşımıyor; `OLGU-04` çıpası yok | Özel ağaçta (145/145) |
| `MOD-1`, `MOD-2` (ATLAS + KOD) | Ajan `model:` satırları katalogda geçerli mi | Katalog makineye bağlı (`~/.cache/opencode/models.json`) | `ATLAS_MODEL_KATALOG=<yol>` verilerek |

**Determinizm.** Bu ağaçta `make dogrula` çıktısı yalnız deponun içeriğine ve git
geçmişine bağlıdır: aynı commit'in iki temiz klonu aynı satırları basar. Yerel
makinenin `~/.cache` durumu bu satırları değiştirmez.

Ölçülen: özel ağaçta (tarihçe yerindeyken) ATLAS 145/145, KOD 174/174. Yayımlanan
bu ağaçta ATLAS 144/145 (OLG-1), KOD 174/174; `make dogrula` T1'i
**`CALISTIRILMADI`** basar, PASS değil.

**Model kataloğu depoda sabittir:** `tools/model_katalog.json`. MOD-1/MOD-2
yaşayan kataloğa değil bu **allowlist anlık görüntüsüne** bakar; böylece KOD
sayısı runner'da da aynı çıkar. Canlı katalogla denetim isteğe bağlıdır:
`ATLAS_MODEL_KATALOG=~/.cache/opencode/models.json make dogrula`.

Farkın nereden geldiği ölçüldü (19 Kasım 2026): aynı 9 modellik içerik başka bir
yolda **174/174**, yerel tam katalog (390 model) **174/174**, katalog yok **170/174**
(`K8-1`, `K8-2`, `O3-09c`, `O3-09d`). Yani fark makineden değil **katalog
içeriğinden** geliyordu; sabit katalog bu değişkeni kaldırdı.

CI aynı kuralları kullanır: `make dogrula-ci` için ayrı muafiyet yoktur; iki kipin
çıktısı başlık dışında birebirdir.

Neden düzeltilmiyor: testler sağlam; eksik olan veri. Testi "onarmak" kanıtı
değil kaydı değiştirmek olurdu. Sahte bir commit çıpası yazmak ise kaydı
yanlışlardı; yapılmadı.

## Ağacı yenileme

```bash
python3 tools/yayinla.py --lab ~/Desktop/MTRX/AI_ARASTIRMA_LABI            # kuru koşu
python3 tools/yayinla.py --lab ~/Desktop/MTRX/AI_ARASTIRMA_LABI --uygula
make dogrula
```

Aktarım yalnız `tools/yayinla.py` içindeki **açık listede** yazan yolları taşır.
Listeye yeni bir yol eklemek bilinçli bir karardır: eklenen dosya bir daha
sır taramasından geçer ve bulgu varsa hiçbir şey yazılmaz.

Aktarımın iki mekanik kuralı vardır ve ikisi de ölçülebilir:

1. **Yol normalizasyonu.** Metin dosyalarında sahibin ev yolu öneki (`/Users/…`)
   `~/` olarak yazılır. Ölçüm kaydının anlamı değişmez; klonlayan için sert
   referans kalmaz. Parite kontrolü **normalize kaynak ↔ ham hedef** üzerinden
   yapılır, yani bu dönüşüm bir farkı gizlemez.
2. **Ürün yasağı.** Planda `.pdf`, `.docx`, `.tex`, `.zip`, `.bundle` gibi üretilmiş
   ürün/arşiv uzantısı görünürse aktarım **hiç yazmadan** çıkar.
