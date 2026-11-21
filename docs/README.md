# docs/ — yayımlanan ölçüm ve öğrenim kayıtları

Geri dönüş: [depo README'si](../README.md) · [English quickstart](EN/QUICKSTART.md)

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
sorar: **kapı, tanımlı sözleşmesini gerçekten uyguluyor mu.** Her vaka kendi geçici
kopyasında çalışır ve iki sözleşmeden birini ölçer:

1. **Temiz taban (ortak ön koşul)** — ihlalsiz kopyada kapı `rc=0` vermeli ve hedef
   bulgu tabanda **bulunmamalıdır**.
2. **Tek ihlal** — aynı kopyada yalnız o kuralı kıran değişiklik yapılır.
3. **Hata vakası** — kapı `rc!=0` vermeli ve yalnız hedef kural kimliğini basmalıdır.
   **Beklenen-bulgu vakası** — kapı `rc=0` dönebilir; ancak hedef uyarı/bulgu işareti
   mutasyon sonrası çıktıda görünmelidir.

Temiz taban veya sözleşme eksikse vaka `ATESLEMEDI` / `TABAN_KIRIK` olarak raporlanır
ve betik `rc=1` ile çıkar. Güncel katalog **109 vaka = 91 hata + 18 beklenen-bulgu**;
ölçülen kurallar ve katmanları çıktıda ada basmadır.

**Neyi ölçmez:** kuralın *doğru tasarlandığını* ölçmez — yalnız kodun o ihlali
yakaladığını ölçer. Mutasyon uygulanamazsa (desen bulunamazsa) bu da sessiz
geçmez, `MUTASYON_UYGULANMADI` olarak kırmızı sayılır.

## CALISTIRILMADI kalemler

`make dogrula` üç öz-test paketini koşar. Standart koşuda bu depoda
`CALISTIRILMADI` kalem **yoktur**: `OLG-1` artık aşağıdaki `attestation.json`
kanıtıyla koşar. `CALISTIRILMADI` yalnız `--hizli` veya model kataloğu yokluğu
gibi gerçekten ölçülemeyen kalemlerde basılır — `PASS` değil, `KOSULLU` da
değil: o kalem koşmadı ve **hükme sayılmaz**.

Koşul serttir: kalan **bütün** test kimlikleri açık listenin içinde olmalı ve
beklenen kanıt dizgisi çıktıda görünmelidir. Liste dışı tek bir test kalırsa
hüküm `FAIL`'dir; gerekçe başka bir hatayı örtmez.

| Test | Neyi ölçer | Neden koşmuyor | Nerede koşar |
|---|---|---|---|
| `MOD-1`, `MOD-2` (ATLAS + KOD) | Ajan `model:` satırları katalogda geçerli mi | Katalog makineye bağlı (`~/.cache/opencode/models.json`) | `ATLAS_MODEL_KATALOG=<yol>` verilerek |

**Determinizm.** Bu ağaçta `make dogrula` çıktısı yalnız deponun içeriğine ve git
geçmişine bağlıdır: aynı commit'in iki temiz klonu aynı satırları basar. Yerel
makinenin `~/.cache` durumu bu satırları değiştirmez.

Ölçülen: bu ağaçta ATLAS ve KOD öz-testleri [`DURUM.md`](DURUM.md)deki güncel
sayılarla geçer; `make dogrula` **8/8** verir ve T1 artık `CALISTIRILMADI` değildir.

**Model kataloğu depoda sabittir:** `tools/model_katalog.json`. MOD-1/MOD-2
yaşayan kataloğa değil bu **allowlist anlık görüntüsüne** bakar; böylece KOD
sayısı runner'da da aynı çıkar. Canlı katalogla denetim isteğe bağlıdır:
`ATLAS_MODEL_KATALOG=~/.cache/opencode/models.json make dogrula`.

Sabit allowlist'in models.dev'de hâlâ geçerli olup olmadığını ölçen ayrı bir
isteğe bağlı kontrol vardır: `make katalog-kontrol`. **Ağ gerektirir ve CI'da
koşmaz**; eksik model adıyla `rc=1`, ölçülemeyen ağ/JSON için `rc=2` döner.
Kanonik kod ayrımı `python3 tools/katalog_kontrol.py` ile alınır (GNU make
tarif hatasını 2'ye çevirir).

Farkın nereden geldiği ölçüldü (19 Kasım 2026): aynı 9 modellik içerik başka bir
yolda **174/174**, yerel tam katalog (390 model) **174/174**, katalog yok **170/174**
(`K8-1`, `K8-2`, `O3-09c`, `O3-09d`). Yani fark makineden değil **katalog
içeriğinden** geliyordu; sabit katalog bu değişkeni kaldırdı.

CI aynı kuralları kullanır: `make dogrula-ci` için ayrı muafiyet yoktur; iki kipin
çıktısı başlık dışında birebirdir.

Neden attestation: testler sağlam; eksik olan özel ağacın tarihsel canlı
kanıtıydı. Bu ağacın kendi `attestation.json`'ı, tarihsel commit zincirinin
yerine geçen **gerçek** bir ağaç kanıtıdır; sahte commit çıpası yoktur. Ayrıntı
aşağıdaki bölümdedir.

## Ağaç kanıtı — `make kanit`

`make kanit`, bu depodaki **gerçek HEAD commit'ini** ve izlenen dosyaların
sha256'sını `attestation.json` içine yazar. Aynı üretimde makine-okur bir
**doğrulama paketi** de oluşturur. Özel ağacı okumaz, ağa bağlanmaz; `OLG-1`'in
canlı kanıt setine bağımlı değildir. Betik yalnız **temiz izlenen ağaçta**
çalışır: `attestation.json` dışında commit edilmemiş değişiklik varsa
`KIRLI_AGAC` ile durur.

| Alan | Anlam |
|---|---|
| `schema` | `ATLAS-KANIT/v1` |
| `commit` | Üretim anındaki gerçek HEAD (40 hex) |
| `tree` | O commit'in Git ağaç nesnesi (40 hex) |
| `files[]` | İzlenen her dosya: `path`, `mode`, `size`, `sha256` |
| `tree_sha256` | `files[]` üzerinden deterministik sha256 |
| `tool_versions` | Üretim ortamının Python/Git/Make/platform sürümleri |
| `scope` | Kapsam ve `attestation.json` istisnası |

`attestation.json` kendini kapsamaz. `commit` alanı, dosyayı ekleyen commit
değil, üretimin yapıldığı HEAD'dir; böylece commit hash'i kendi içeriğine bağlı
değildir ve hash döngüsü oluşmaz. Kapı, bu commit'in gerçekten var olduğunu ve
HEAD'in atası olduğunu `git` ile doğrular; **sahte commit çıpası yoktur**.

`make kanit-dogrula` fail-closed doğrular:

| Kod | Kural |
|---|---|
| `KANIT-00` | Dosya yok/okunamadı — kapı açılmaz |
| `KANIT-01` | Şema, alan, tip veya hash biçimi geçersiz |
| `KANIT-02` | Commit yok, HEAD'in atası değil veya tree uyuşmuyor |
| `KANIT-03` | Kayıtlı dosya hash'leri commit ağacıyla uyuşmuyor |
| `KANIT-04` | `tree_sha256` yeniden hesapla tutmuyor |
| `KANIT-05` | Güncel HEAD ağacı kayıtlı ağaçtan farklı (sürüklenme) |
| `KANIT-06` | İzlenen ağaç kirli (`attestation.json` dışında) |

**Ne kanıtlar:** kayıt gerçek bir commit'ten üretilmiştir; o commit'in ağacındaki
dosyaların sha256'ları kayıttakiyle aynıdır; kapı çalıştığı anda güncel HEAD
aynı ağacı taşır (attestation dosyası hariç); araç sürümleri kayıtlıdır.

**Ne kanıtlamaz:** imza, yazar/köken, dış zaman damgası veya değiştirilemezlik
yoktur; yazma yetkisi olan biri kanıtı yeniden üretebilir. Testlerin geçtiğini,
içeriğin doğru olduğunu, üretilen makalelerin varlığını veya `.git` dışındaki
izlenmeyen dosyaları kapsamaz. `tool_versions` üretim ortamını **tanımlar**;
doğrulayıcının sürümleriyle eşit olması istenmez. `generated_at` bir beyandır;
dış saatle doğrulanmaz.

### Taşınabilir doğrulama paketi

`make kanit`, attestation'ı yazdıktan sonra sırasıyla `make dogrula`,
`make kapsam` ve `make iddia` komutlarını çalıştırır; çıktıları ve çıkış
kodlarını `kanit-paketi/` dizinine kaydeder:

| Yol | İçerik |
|---|---|
| `sonuc.json` | `ATLAS-DOGRULAMA/v1`: commit, ağaç, komut çıkış kodları, bulgu kimlikleri, dosya manifesti |
| `attestation.json` | Aynı üretimde yazılan ağaç kanıtının kopyası |
| `manifest.sha256` | Paketteki dosyaların SHA-256 listesi (`sha256  yol`) |
| `komutlar/` | Her komutun ham stdout/stderr kaydı; adları sıra ve komut kimliğini taşır |

Şema `schemas/atlas-dogrulama-sonuc.schema.json` dosyasındadır. `sonuc.json`
komut başına `exit_code` ve `status` (`PASS`/`FAIL`/`ERROR`), `finding_ids`,
stdout/stderr özet hash'leri ve süre taşır; üst düzeyde toplu `exit_code`,
`verdict`, `findings[]` ve izlenen dosyaların SHA-256 manifesti bulunur.
Paket git'e eklenmez (`.gitignore`); taşımak için dizini kopyalamak yeterlidir.
`manifest.sha256` paket dosyalarını doğrular; attestation'ın kendisi ayrıca
`make kanit-dogrula` ile commit ve ağaca bağlanır.

Bir komut başarısız olursa paket yine yazılır, `verdict` `FAIL` olur ve
`make kanit` sıfır olmayan kodla çıkar. Yalnız attestation üretmek için eski
davranış `make kanit` yerine `python3 tools/kanit.py --paketsiz` ile alınır;
komut kümesini değiştirmek için `--komut` yinelenebilir.

**Seçim — yol 1:** `OLG-1` emekliye ayrılmadı. `olgu_lint`, `attestation.json`
varsa `tools/kanit_dogrula.py` ile onu doğrular ve `OLGU-04`'ün commit zinciri
çıpası yerine bu ağacın gerçek commit/tree kanıtını kullanır. Böylece özel
ağacın 36 tarihsel commit'i public ağaçta aranmaz; sahte commit çıpası yazılmaz.
`docs/OLGULAR.md` içindeki tarihsel `baseline_commit` ve mekanizma listesi
**silinmedi**; public ağaçta makine kanıtı sayılmaz, tarihsel kayıt olarak durur.
Özel ağaçta (145/145) kaydı da tarihseldir; public ağaçta yeniden üretilmez.
`OLG-06` atlanmaz: eksik iki DERSLER satırı (`89fb3da`, `df0d083`) gerçek
commit'lerle eklendi ve `--dersler` PASS verir.

`attestation.json` yoksa `OLG-1` tarihsel commit denetimine döner ve bu public
ağaçta `OLGU-04` ile **FAIL** olur; dosya bozuksa `KANIT_GECERSIZ` olur. İkisi
de `CALISTIRILMADI` olarak gizlenmez. Negatif kontrol: kayıtlı commit/tree
bozulduğunda `olgu_lint` rc=1 ve `atlas_selftest` içinde `KALDI OLG-1` görülür.
`make dogrula` bu depoda **8/8** verir; T1 PASS'tir. Kod değişince `make kanit`
yeniden üretilmelidir; `make kanit-dogrula` ve CI bayat kaydı `KANIT-05` ile
kırmızıya çevirir. `make kanit-dogrula` CI'da tam geçmişle (`fetch-depth: 0`)
koşar.

## Sabit model kataloğunu yenileme

`tools/model_katalog.json` canlı kataloğun tam kopyası değildir; **yalnız aktif
hatlarda geçen** OpenRouter kimliklerinin allowlist'idir. Canlıdan bütün modelleri
almak MOD-1/MOD-2'nin "depoda geçmeyen model" disiplinini bozar. Yenileme iki
kümenin kesişimidir: **aktif hat kaynakları ∩ models.dev**.

**Aktif kaynaklar:** `ATLAS_SABLONLAR/.opencode/agent/`,
`KOD_SABLONLAR/.opencode/agent/`, iki `routing.profiles.json`, üç
`opencode.json` (kök, ATLAS ve KOD). `docs/`, `SURUM.md`, tarihsel `OLCUM-*`
ve test fikstürleri bilinçli olarak taranmaz: oradaki emekli kimlikler tarihsel
kanıttır, güncel allowlist'e geri girmemelidir. Yeni bir aktif ajan ağacı
eklenirse aşağıdaki `git grep` yol listesine de eklenir.

### Ne zaman yenilenir

- `python3 tools/katalog_kontrol.py` **rc=1** verdiğinde: allowlist'teki bir kimlik
  canlıda yok, `deprecated` veya `reasoning`/`tool_call` değeri değişmiş.
  (`make katalog-kontrol` bulguyu GNU make nedeniyle `rc=2`ye çevirir; kanonik
  ölçüm Python çıkışıdır.)
- Aktif kaynaklarda bir `model: openrouter/...` satırı eklendiğinde, silindiğinde
  veya değiştiğinde. Yeni kimlik katalogda yoksa `make dogrula` MOD-1/MOD-2'de
  kırmızıya döner; silinen kimlik ise "yalnız depoda geçen" kuralını bozar.
- models.dev'de allowlist'teki bir modelin yetenek bayrağı değiştiğinde (yine
  `rc=1`).

### Ne zaman yenilenmez

- `rc=0` ise: canlı katalogda yeni modeller görünse bile dosya yenilenmez;
  allowlist bilinçli olarak dardır.
- `rc=2` ise: ağ/JSON ölçülemedi; bu bir bayatlama bulgusu değildir, katalog
  suçlanmaz.
- Yalnız `docs/`, `SURUM.md`, tarihsel `OLCUM-*` veya test fikstürleri değiştiyse:
  bunlar aktif model kaynağı değildir.
- Sadece `_kaynak` tarihi değişsin diye: tarih, gerçek yenileme günüdür.

### 1. Canlı kataloğu indir

```bash
curl -fsSL https://models.dev/api.json -o /tmp/models.dev-api.json
```

### 2. Yalnız aktif model kimliklerini çıkar

```bash
git grep -h -o -E 'openrouter/[A-Za-z0-9._:/-]+' -- \
  ATLAS_SABLONLAR/.opencode/agent \
  KOD_SABLONLAR/.opencode/agent \
  ATLAS_SABLONLAR/routing.profiles.json \
  KOD_SABLONLAR/routing.profiles.json \
  ATLAS_SABLONLAR/opencode.json \
  KOD_SABLONLAR/opencode.json \
  opencode.json \
| sort -u > /tmp/atlas-model-ids.txt
test -s /tmp/atlas-model-ids.txt
cat /tmp/atlas-model-ids.txt
```

`git grep` yalnız **izlenen** dosyaları tarar; yeni bir ajan dosyası henüz
izlenmiyorsa önce `git add` ile izlemeye alın. Çıktıda emekli/tarihsel bir kimlik
görünüyorsa yol listesi yanlıştır; o kimliği kataloğa geri eklemeyin.

### 3. Canlı kayıttan allowlist'i üret

```bash
python3 - <<'PY'
import datetime
import json
import pathlib
import sys

api = json.loads(pathlib.Path('/tmp/models.dev-api.json').read_text(encoding='utf-8'))
ids = [s for s in pathlib.Path('/tmp/atlas-model-ids.txt').read_text(
    encoding='utf-8').splitlines() if s.strip()]
if not ids:
    sys.exit('HATA: aktif model kimligi bulunamadi')

aciklama = (
    'Sabit model katalogu (allowlist anlik goruntusu). MOD-1/MOD-2 kapilari '
    'ajanlarin BU listedeki modelleri kullandigini denetler; boylece sayi her '
    'klonda ayni cikar. Canli katalogla denetim icin ATLAS_MODEL_KATALOG=<yol> '
    'verin. Tazelik icin: make katalog-kontrol (ag gerekir; CI\'da kosmaz).')
kaynak = ('models.dev semasi; yalniz depoda gecen model kimlikleri, %s'
          % datetime.date.today().isoformat())

saglayicilar = {}
for tam in sorted(set(ids)):
    saglayici, ayrac, model = tam.partition('/')
    if not ayrac or not saglayici or not model:
        sys.exit('HATA: gecersiz kimlik: %s' % tam)
    modeller = ((api.get(saglayici) or {}).get('models') or {})
    kayit = modeller.get(model)
    if not isinstance(kayit, dict):
        sys.exit('HATA: canli katalogda yok: %s' % tam)
    if kayit.get('status') == 'deprecated':
        sys.exit('HATA: canli katalogda deprecated: %s' % tam)
    for alan in ('reasoning', 'tool_call'):
        if not isinstance(kayit.get(alan), bool):
            sys.exit('HATA: %s boolean degil: %s' % (alan, tam))
    saglayicilar.setdefault(saglayici, {})[model] = {
        'reasoning': kayit['reasoning'], 'tool_call': kayit['tool_call']}

satirlar = ['{',
            ' "_aciklama": %s,' % json.dumps(aciklama, ensure_ascii=False),
            ' "_kaynak": %s,' % json.dumps(kaynak, ensure_ascii=False)]
for i, (saglayici, modeller) in enumerate(sorted(saglayicilar.items())):
    satirlar += [' %s: {' % json.dumps(saglayici), '  "models": {']
    for j, (model, kayit) in enumerate(sorted(modeller.items())):
        virgul = ',' if j < len(modeller) - 1 else ''
        satirlar.append('   %s: %s%s' % (
            json.dumps(model), json.dumps(kayit), virgul))
    satirlar += ['  }', ' }' + (',' if i < len(saglayicilar) - 1 else '')]
satirlar.append('}')
pathlib.Path('/tmp/model_katalog.json').write_text(
    '\n'.join(satirlar) + '\n', encoding='utf-8')
print('yazildi: /tmp/model_katalog.json (%d model)'
      % sum(len(v) for v in saglayicilar.values()))
PY
```

Betik, canlıda bulunmayan veya `deprecated` olan tek bir kimlikte bile **hiçbir
şey yazmadan** çıkar. Eksik modeli canlı katalogdan uydurmayın; önce aktif
kaynak referansını düzeltin.

### 4. Üretileni aynı anlık görüntüyle doğrula, sonra yerleştir

```bash
python3 tools/katalog_kontrol.py \
  --katalog /tmp/model_katalog.json \
  --api-dosya /tmp/models.dev-api.json

diff -u tools/model_katalog.json /tmp/model_katalog.json
cp /tmp/model_katalog.json tools/model_katalog.json
```

Kontrol `rc=0` vermeden `cp` yapmayın. `diff` yalnız beklenen model değişikliğini
göstermiyorsa durun; dosyayı elle düzenleyerek farkı susturmayın.

### 5. Canlı ve depo kontrolleri

```bash
python3 tools/katalog_kontrol.py
make dogrula
git diff --check
```

`make dogrula` bu yayımlanan ağaçta 8/8 verir; T1 artık attestation ile koşar.
MOD-1/MOD-2 katalogdan geçiyorsa ve canlı kontrol `rc=0` ise değişiklik commit
edilebilir. Katalogla birlikte yalnız gerçekten
değişen aktif referansları commit edin; tarihsel `OLCUM`/`SURUM` satırlarını
katalog yenilemesi bahanesiyle yeniden yazmayın.

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

## İddia defteri ve kapsam sınırı

`make iddia`, bu depodaki public sayısal iddiaları `tools/iddia_defteri.json`
üzerinden yeniden ölçer; her `OLCULDU` satırının son ölçülen ham çıktı satırı
`tools/iddia_olcum.json` içinde aynı `IDD-*` anahtarıyla saklanır. Ham kanıt güncel
çıktıyla birebir aynı değilse veya beyanla çelişirse satır kırmızı olur; anlık
görüntü yalnızca `make iddia-yaz` ile yenilenir. Defter üç dokümanı tarar: kök
`README.md`, bu dosya ve `docs/EN/QUICKSTART.md`. Tarihli kayıtlar (`OLCUM-*`, `SURUM.md`) ve üretilmiş
tablolar (`MUTASYON_KAPSAM.md`, `GUVENLIK.md`) kapsam dışıdır: bunlar yeniden
koşulacak iddia değil, ölçümün o günkü kaydıdır. Kapsam dışı dosyalar yeşil
sayılmaz; defterin `kapsam.haric` bloğunda gerekçeleriyle listelenir.
