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

## Yayın kapsamı

**Dahil:** hatların mekanizması (ajanlar, komutlar, şablonlar, kapı betikleri,
ölçüm bataryası), üç öz-test paketi, Toolkit v4 çekirdeği, kusurlu örnek koşu
(`DENEME/`), yukarıdaki ölçüm ve ders kayıtları.

**Hariç — ve neden:**

| Ne | Neden |
|---|---|
| Laboratuvarın ürettiği makaleler, kitapçıklar, PDF'ler | Bu depo **üretim mekanizmasıdır**, ürün arşivi değil. |
| Konu korpusları (`KOMUT_TOOLKIT_v4/yahudikaynaklar/`, `moschiach/`, `sebatay-sevi-kaynaklari/`) | Araştırma malzemesi; mekanizmanın parçası değil. |
| `projeler/` | Devam eden/yayımlanmamış çalışmalar. |
| `docs/DEVIR-*` (oturum devirleri) | Kişisel çalışma bağlamı taşır; en az biri **kimlik bilgisi** (veritabanı bağlantı dizesi) içerir. Böyle bir dosya hiçbir koşulda yayımlanmaz. **Tek istisna:** kapıların pinlediği kanonik OLGU-06 devri `DEVIR-2026-09-03-1945-AUD-06-07.md` — kimlik bilgisi içermez, sürüm satırı ve OLGU-06 lint'i ona bağlıdır. |
| `SURUM.md` dışındaki iş günlükleri | `SURUM.md` **dahildir** (kapılar sürüm satırını oradan okur); proje-özel devir ve iş kayıtları hariçtir. |
| `gate/FINAL-GATE-*.json` | Bir **projenin** kapı hükmü; mekanizmanın değil. |

Bu sınır yüzünden `DERSLER` ve ölçüm dosyalarındaki bazı atıflar özel ağaçtaki
devir dosyalarını gösterir. Bu bir kırık bağ değil, **bilinçli yayın sınırıdır**:
kayıt yerinde durur, kanıtı özel ağaçta kalır.

## Ortam bağlı kalemler

`make dogrula` üç öz-test paketini koşar. İki kalem, ölçüm ortamı yokluğunda
**`KOSULLU`** raporlanır — asla `PASS` değil. Koşul serttir: kalan **bütün** test
kimlikleri aşağıdaki açık listenin içinde olmalı ve gerekçe çıktıda görünmelidir.
Liste dışı tek bir test kalırsa hüküm `FAIL`'dir; ortam gerekçesi başka bir hatayı
örtermez.

| Test | Neyi ölçer | Neden koşamıyor | Nasıl ölçülür |
|---|---|---|---|
| `OLG-1` (ATLAS) | `SURUM.md` makine bloğunun sürüm/commit/canlı ölçüm bağını (`OLGU-03/04/05`) | Bu depo özel ağacın commit zincirini taşımıyor; `OLGU-04` çıpası yok | Özel ağaçta koşulur |
| `MOD-1`, `MOD-2` (ATLAS + KOD) | Ajan `model:` satırları yerel katalogda geçerli mi | Runner'da `~/.cache/opencode/models.json` yok | `ATLAS_MODEL_KATALOG=<yol>` verilerek |

Ölçülen: özel ağaçta (tarihçe ve katalog yerindeyken) ATLAS 145/145, KOD 174/174.
Yayımlanan bu ağaçta macOS'ta ATLAS 144/145 (OLG-1), KOD 174/174; `make dogrula`
T1'i **`KOSULLU`** basar, PASS değil.

Aynı sayılar Linux runner'da üretilmez: katalog yoktur ve KOD'un `MOD-2` fikstürü
kataloğun içeriğine duyarlıdır (ölçüldü: 170/174 katalogsuz, 173/174 herhangi bir
dış katalogla). Bu yüzden CI, `make dogrula-ci` ile yalnız **runner'da
ölçülebilen** kalemleri hükme sokar — hijyen, Python/kabuk sözdizimi, sır taraması,
Toolkit paketi — ve ATLAS/KOD paketlerini **RAPOR** olarak basar. Rapor hükme
girmez ama gizlenmez: rc ve özet satırı her koşuda logdadır.

Bu, "başka makinede yeşil görünmek" için testi yumuşatmak değildir: hükme giren
kalemler gerçekten koşar, girmeyenler etiketiyle basılır. Tam koşu yerel ortamda
`make dogrula` ile alınır.

Neden düzeltilmiyor: testler sağlam; eksik olan ortam. Testi "onarmak" kanıtı
değil kaydı değiştirmek olurdu. Laboratuvarın kendi kuralı da bunu yasaklar
(`AGENTS.md`: MOD-1/MOD-2 ortam farkıdır, "onarılmaz").

## Ağacı yenileme

```bash
python3 tools/yayinla.py --lab ~/Desktop/MTRX/AI_ARASTIRMA_LABI            # kuru koşu
python3 tools/yayinla.py --lab ~/Desktop/MTRX/AI_ARASTIRMA_LABI --uygula
make dogrula
```

Aktarım yalnız `tools/yayinla.py` içindeki **açık listede** yazan yolları taşır.
Listeye yeni bir yol eklemek bilinçli bir karardır: eklenen dosya bir daha
sır taramasından geçer ve bulgu varsa hiçbir şey yazılmaz.
