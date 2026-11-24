# docs/ — yayımlanan ölçüm ve öğrenim kayıtları

Geri dönüş: [depo README'si](../README.tr.md) · [kısa tur](ATLAS-KISA-TUR.md) · [yayın sözleşmesi](YAYIN-SOZLESMESI.md) · [English quickstart](EN/QUICKSTART.md)

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

## Parite notu — 2026-11-23

Bu depo özel çalışma kopyasının yayımlanabilir kopyasıdır ve parite tamdır:
`planda=218 · yeni=0 · degisen=0 · ayni=218 · silinecek=0`. Eski `arsiv`
remote'u (`ATLAS_Research_Lab`) `7948525`te durur; oradan bu depoya bir aktarım,
43 dosyada attestation ve kanıt araçları, OLGULAR/model politikası ve DERSLER
iyileştirmelerini geri alır. Bu yüzden aktarım yönü tek yönlüdür: özel çalışma
kopyası → bu depo.

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
| Kök `scripts/` (kişisel exocortex bataryası) | 33 dosya yayımlanmayan `SKILL.md`'yi okur; ayrıca sahibinin mutlak yolunu (`KOK = '<ev-yolu>/…'`) taşıyordu. Laboratuvarın kendi mekanizması ATLAS/KOD ağaçlarındaki `scripts/` klasörlerindedir; bu küme kişisel çalışma sözleşmesine aittir (kendi başlığı: *Proprietary*). |
| `silat-makale` gibi proje adları | Yalnız kod **yorumlarında** ("hangi gerçek koşuda ölçüldü" kanıtı) ve `SURUM.md` bakım kaydında geçer. Makale metni, PDF, veri dosyası yoktur; adı silmek ölçümün kanıt izini silmek olurdu. |

Bu sınır yüzünden `DERSLER` ve ölçüm dosyalarındaki bazı atıflar yayımlanmayan
devir dosyalarını gösterir. Bu bir kırık bağ değil, **bilinçli yayın sınırıdır**:
kayıt yerinde durur; bu atıflar arşiv notudur, `OLG-1` kanıtı değildir.

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
ve betik `rc=1` ile çıkar. Güncel katalog **123 vaka = 104 hata + 19 beklenen-bulgu**;
ölçülen kurallar ve katmanları çıktıda ada basmadır.

**Neyi ölçmez:** kuralın *doğru tasarlandığını* ölçmez — yalnız kodun o ihlali
yakaladığını ölçer. Mutasyon uygulanamazsa (desen bulunamazsa) bu da sessiz
geçmez, `MUTASYON_UYGULANMADI` olarak kırmızı sayılır.

## Sentetik temiz teslim ve kenar fikstürleri

`make temiz-teslim`, `DENEME/`'ye dokunmadan makale metni taşımayan sentetik bir
teslim kökü kurar. Kök 22 zorunlu SCOPE-ID başlığını, PROVENANCE satırlarını ve
sentetik FIX kayıtlarını taşır; gövdesinde makale paragrafı, kaynakça, DOI veya
alıntı yoktur. Ardından temiz kökten beş kenar kökü türetir. Her kök iki gerçek
komutla ölçülür: `tools/demo.py --kok <kök>` ve
`scripts/check_integrity.sh --full`. Fikstürler `tempfile` altında üretilir;
`DENEME/` yalnız betik kopyalamak için okunur.

| Fikstür | `demo` | `check_integrity --full` | Ne ölçülür |
|---|---:|---:|---|
| `temiz` | 0 | 0 | Meşru teslim: iddia == kanıt, mutabakat PASS, tüm fazlar PASS |
| `eksik-kanit` | 1 | 0 | Manifestin "UYGULANMIŞ" dediği FIX MASTER'da yok |
| `hayalet-kanit` | 2 | 0 | MASTER'da manifestoda tanımsız FIX-ID var |
| `sahte-2b` | 2 | 0 | Gate 2B, MASTER'da kanıtı olmayan FIX'i KANITLI ilan ediyor |
| `bozuk-final` | 2 | 1 | FINAL-GATE JSON'u okunamıyor |
| `eksik-kapsam` | 0 | 1 | Zorunlu SCOPE-ID MASTER'da başlık olarak yok |

Son iki satır, `demo`'nun kapsamadığı yapısal kapıyı; ilk üç kenar ise
`check_integrity`'nin kapsamadığı kanıt mutabakatını ayrı katmanda gösterir.
Temiz kökün `rc=0` sonucu, `DENEME/`'nin kırmızı regresyonundan bağımsız bir
meşru teslim kanıtıdır; `DENEME/` fikstürü değişmez.

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

Sabit allowlist'in models.dev'de hâlâ geçerli olup olmadığını ölçen canlı kapı
`make katalog-kontrol`tür. Ağ gerektirir; **CI dışında**, elle/yerel koşulur;
CI yalnız çevrimdışı `make katalog-selftest` testini `make dogrula-ci` üzerinden
çalıştırır. Canlı kapı yalnız allowlist'i değil, `profiller.bedava` altındaki on
rolü de canlı kayıtla karşılaştırır. Eksik/çelişkili kayıt veya bedava koşulu
ihlali `rc=1`, ölçülemeyen ağ/JSON `rc=2` ve **`OLCULMEDI`**dır; PASS sayılmaz.
Her koşu commit/tree/tree_sha256 ve tanım SHA-256'larıyla append-only
`docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl` kaydına eklenir; istenirse `--kayit <yol>`
ile ayrı dosyaya yazılır. Kanonik kod ayrımı `python3 tools/katalog_kontrol.py`
ile alınır (GNU make tarif hatasını 2'ye çevirir).

Farkın nereden geldiği ölçüldü (19 Kasım 2026): aynı 9 modellik içerik başka bir
yolda **174/174**, yerel tam katalog (390 model) **174/174**, katalog yok **170/174**
(`K8-1`, `K8-2`, `O3-09c`, `O3-09d`). Yani fark makineden değil **katalog
içeriğinden** geliyordu; sabit katalog bu değişkeni kaldırdı.

CI aynı kuralları kullanır: `make dogrula-ci` için ayrı muafiyet yoktur; iki kipin
çıktısı başlık dışında birebirdir.

Neden attestation: testler sağlam; eksik olan kamu ağacında yeniden üretilebilir
bir ağaç kanıtıydı. Bu ağacın kendi `attestation.json`'ı, tarihsel commit
zincirinin yerine geçen **tek** kamu kanıtıdır; sahte commit çıpası yoktur.
Ayrıntı aşağıdaki bölümdedir.

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
komut kümesini de değiştirmek için `--komut` yinelenebilir.

### Paketi bağımsız doğrulama

```bash
make kanit-paket-dogrula
```

Bu komut `kanit-paketi/` dizinini tek başına okumaz; dört kanıt katmanını
birbirine bağlar:

1. `sonuc.json`, `schemas/atlas-dogrulama-sonuc.schema.json` ile JSON Schema
   doğrulamasından geçer.
2. Paket içindeki `attestation.json`, `tools/kanit_dogrula.py` ile gerçek
   commit/ağaç ve güncel HEAD üzerinden doğrulanır.
3. `manifest.sha256`, paketteki bütün dosyaları (kendisi hariç) kapsar; her
   satırdaki SHA-256 yeniden hesaplanır.
4. Her `komutlar/NN-<id>.stdout.txt` ve `.stderr.txt`, `sonuc.json` içindeki
   komut kaydıyla; çıkış kodu, bayt sayısı, SHA-256 ve `finding_ids` ile
   karşılaştırılır.

Başarılı doğrulama şu iki satırı basar:

```text
PASS PAKET commit=<paket commit> komut=3 dosya=8
PAKET: TEMIZ — sonuc semasi, attestation, manifest ve ham komut kayitlari tutuyor.
```

`make kanit-paket-dogrula` paket yoksa, `manifest.sha256` eksik/bozuksa veya
herhangi bir hash tutmuyorsa sıfır olmayan kodla çıkar. `jsonschema` bağımlılığı
`requirements-dev.txt` içinde sabittir; `make kur` sonrası kurulum yeterlidir.

CI bu paketi `dogrula` işinde üretir ve `atlas-kanit-paketi` adıyla artifact
olarak yükler. CI üretimi `make kanit KANIT_ARGS="--cikti $RUNNER_TEMP/atlas-attestation.json"`
ile yapılır; böylece izlenen `attestation.json` değişmez. Paket doğrulanmadan
ve `git status --porcelain --untracked-files=no` temiz görülmeden artifact
adımına geçilmez. İndirme ve aynı commit'te doğrulama:

```bash
RUN_ID=$(gh run list --workflow=dogrula.yml --branch=main --limit=1 --json databaseId --jq '.[0].databaseId')
INDIR=$(mktemp -d)
gh run download "$RUN_ID" -n atlas-kanit-paketi -D "$INDIR"
python3 tools/kanit_paketi_dogrula.py --paket "$INDIR"
```

Artifact, `sonuc.json` içindeki commit'e bağlıdır; farklı bir HEAD'de paket
attestation'ı `KANIT-05` ile kırmızı olur. Üçüncü kişi kendi klonunda önce
`git fetch && git checkout <sonuc.json commit>` yapmalı, sonra yukarıdaki
doğrulamayı koşmalıdır. `gh` yoksa artifact GitHub Actions çalışma sayfasındaki
**Artifacts → `atlas-kanit-paketi`** bağlantısından da indirilebilir.

**Seçim — yol 1:** `OLG-1` emekliye ayrılmadı. `olgu_lint`, yalnız bu kamu
ağacındaki `attestation.json` dosyasını `tools/kanit_dogrula.py` ile doğrular ve
`OLGU-04`'ün commit zinciri çıpası yerine bu ağacın gerçek commit/tree kanıtını
kullanır. Böylece dış lab tarihçesi public ağaçta aranmaz; sahte commit çıpası
yazılmaz. `docs/OLGULAR.md` makine bloğundan tarihsel taban commit alanı,
mekanizma sayacı ve mekanizma listesi **çıkarıldı**; kamu kanıtı
`kamu_kaniti: attestation.json` ile adlandırıldı. Tarihsel tablo ve DERSLER
taşınları silinmedi; bunlar arşiv kaydıdır, OLG-1 kanıtı değildir. `OLG-06`
atlanmaz: eksik iki DERSLER satırı (`89fb3da`, `df0d083`) gerçek commit'lerle
eklendi ve `--dersler` PASS verir.

`attestation.json` yoksa `OLG-1` **`KANIT_YOK`** ile FAIL olur; dosya bozuksa
`KANIT_GECERSIZ` olur. İkisi de tarihsel commit denetimine dönmez ve
`CALISTIRILMADI` olarak gizlenmez. Negatif kontrol: attestation silindiğinde
`KANIT_YOK`, kayıtlı commit/tree bozulduğunda `KANIT_GECERSIZ` ve
`atlas_selftest` içinde `KALDI OLG-1` görülür. Bu kontrol CI'da
`make olgu-negatif` ile geçici bir klonda her koşuda yeniden ölçülür; ana ağaç
değişmez.
`make dogrula` bu depoda **8/8** verir; T1 PASS'tir. Kod değişince `make kanit`
yeniden üretilmelidir; `make kanit-dogrula` ve CI bayat kaydı `KANIT-05` ile
kırmızıya çevirir. `make kanit-dogrula` CI'da tam geçmişle (`fetch-depth: 0`)
koşar.

## Sabit model kataloğunu yenileme

`tools/model_katalog.json` canlı kataloğun kopyası değil, **yalnız aktif hatlarda
geçen** OpenRouter kimliklerinin allowlist'idir. Yenileme iki kümenin
kesişimidir: **aktif hat kaynakları ∩ models.dev**. Canlıdan bütün modelleri
almak MOD-1/MOD-2'nin "depoda geçmeyen model" disiplinini bozar.

KOD `bedava` profiline kimlik seçimi ve emekli kimlik değişimi daha sıkıdır:
[`KOD_BEDAVA_MODEL_POLITIKASI.md`](KOD_BEDAVA_MODEL_POLITIKASI.md).

**Aktif kaynaklar:** `ATLAS_SABLONLAR/.opencode/agent/`,
`KOD_SABLONLAR/.opencode/agent/`, iki `routing.profiles.json`, üç
`opencode.json` (kök, ATLAS ve KOD). `docs/`, `SURUM.md`, tarihsel `OLCUM-*`
ve test fikstürleri taranmaz: oradaki emekli kimlikler tarihsel kanıttır,
allowlist'e geri girmemelidir. Bu satırların aktif atıf taşımadığı ayrı
`make model-kimlik` kontrolüyle ölçülür. Yeni bir aktif ajan ağacı eklenirse
aşağıdaki `git grep` yol listesine de eklenir.

### Ne zaman yenilenir

- `python3 tools/katalog_kontrol.py` **rc=1**: allowlist'teki kimlik canlıda
  yok, `deprecated`, `reasoning`/`tool_call` değişmiş veya
  `profiller.bedava` koşullarından biri düşmüş. (`make katalog-kontrol` GNU
  make nedeniyle `rc=2` döndürür; kanonik ölçüm Python çıkışıdır.)
- Aktif kaynaklarda bir `model: openrouter/...` satırı eklendi, silindi veya
  değişti. Yeni kimlik katalogda yoksa `make dogrula` MOD-1/MOD-2'de kırmızıya
  döner; silinen kimlik "yalnız depoda geçen" kuralını bozar.
- models.dev'de allowlist'teki bir modelin yetenek bayrağı değişti (yine
  `rc=1`).

### Ne zaman yenilenmez

- `rc=0` ise: canlıda yeni modeller görünse bile dosya yenilenmez; allowlist
  bilinçli olarak dardır.
- `rc=2` ise: ağ/JSON ölçülemedi; sonuç `OLCULMEDI`dır, bayatlama bulgusu
  değildir.
- Yalnız `docs/`, `SURUM.md`, tarihsel `OLCUM-*` veya test fikstürleri
  değiştiyse: bunlar aktif model kaynağı değildir.
- Sadece `_kaynak` tarihi değişsin diye: tarih, gerçek yenileme günüdür.

### Haftalık kanarya

Aynı canlı kapı, required olmayan haftalık bir iş olarak da koşar:
`.github/workflows/katalog-canary.yml` (Pazartesi 04:00 UTC) yalnız
`python3 tools/katalog_kontrol.py` çalıştırır; PR/push hükmüne girmez ve
`make dogrula` ile mevcut CI hükmünü değiştirmez. `rc=1` kimlik/uyuşmazlık,
`rc=2` ölçülemedi demektir; ikisi de PASS sayılmaz ve iş, aynı başlıklı açık
issue'yu güncelleyerek (yoksa açarak) kırmızı kalır. Kanarya yalnız haber
verir; allowlist'i kendisi yenilemez — yenileme yine aşağıdaki elle adımlarla
ve diff incelemesiyle yapılır. Elle tetikleme: `workflow_dispatch`.

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
```

`git grep` yalnız **izlenen** dosyaları tarar; yeni ajan dosyası henüz
izlenmiyorsa önce `git add` yapın. Çıktıda emekli/tarihsel kimlik varsa yol
listesi yanlıştır; o kimliği kataloğa geri eklemeyin.

### 3. Canlı kayıttan allowlist'i üret

```bash
python3 tools/model_katalog_uret.py \
  --api-dosya /tmp/models.dev-api.json \
  --kimlik-dosya /tmp/atlas-model-ids.txt \
  --cikti /tmp/model_katalog.json
```

Araç eksik, `deprecated` veya bozuk tek bir kimlikte **hiçbir şey yazmadan**
`rc=1` verir; girdi okunamazsa `rc=2`. Eksik modeli canlı katalogdan
uydurmayın; önce aktif kaynak referansını düzeltin. Sözleşme
`make katalog-selftest` içinde sınanır.

21 Kasım 2026 canlı kontrolü: **9/9 kimlik geçerli**; aday depodaki katalogla
aynıydı (tek fark `_kaynak` tarihi), bu yüzden `cp` yapılmadı.

### 4. Üretileni aynı anlık görüntüyle doğrula, sonra yerleştir

```bash
set -euo pipefail

python3 tools/katalog_kontrol.py \
  --katalog /tmp/model_katalog.json \
  --api-dosya /tmp/models.dev-api.json

# diff 0 = fark yok, 1 = beklenen fark, 2+ = okunamadi/beklenmedik.
# Yalnız 1 devam eder; 0 veya 2+ cp'ye geçemez.
diff_rc=0
diff -u tools/model_katalog.json /tmp/model_katalog.json \
  > /tmp/model_katalog.diff || diff_rc=$?
case "$diff_rc" in
  1) : ;;
  0) echo 'HATA: beklenen katalog farki yok'; exit 1 ;;
  *) echo "HATA: diff okunamadi (rc=$diff_rc)"; exit 1 ;;
esac
test -s /tmp/model_katalog.diff
grep -q '^[+-][^+-]' /tmp/model_katalog.diff

# İNCELEME KAPISI: diff'i açın. Yalnız beklenen model değişikliği varsa `e`
# yazın; boş veya başka cevap cp'yi çalıştırmaz.
read -r -p 'Diff beklenen model degisikligi mi? [e/H] ' onay
test "$onay" = 'e'
cp /tmp/model_katalog.json tools/model_katalog.json
```

Kontrol `rc=0` vermeden, diff 1 dışında kod döndürmeden veya inceleme onayı
olmadan `cp` yapmayın. Diff yalnız beklenen model değişikliğini göstermiyorsa
durun; dosyayı elle düzenleyerek farkı susturmayın.

### 5. Canlı ve depo kontrolleri

```bash
python3 tools/katalog_kontrol.py
make dogrula
git diff --check
```

`make dogrula` bu yayımlanan ağaçta 8/8 verir; T1 artık attestation ile koşar.
MOD-1/MOD-2 katalogdan geçiyor ve canlı kontrol `rc=0` ise değişiklik commit
edilebilir. Katalogla birlikte yalnız gerçekten değişen aktif referansları
commit edin; tarihsel `OLCUM`/`SURUM` satırlarını yenileme bahanesiyle yeniden
yazmayın.

## Emekli model kimliği — resmi istisna

19 Kasım 2026'da models.dev canlı kataloğundan kalkan eski Nemotron Super free
kimliği **silinmedi**: tarihsel ham satırlar kanıttır ve yeniden yazılmaz.
Eski kimliğin tam değeri, yerine geçen kimlik ve gerekçesi
`tools/model_kimlik_istisna.json` içindeki `emekli_kimlikler` kaydındadır.
Kimlik yalnız `SURUM.md`deki tarihsel sürüm satırında ve
`docs/OLCUM-01/02/03/06` ham komut/çıktı satırlarında yaşar.

İstisna **dosya adıyla değil, dosya + tam satır SHA-256'sıyla** verilir. Bir
tarihsel satır değişirse hash tutmaz, kayıt bayatlar ve kontrol kırmızı olur;
yeni bir tarihsel satır kendiliğinden muaf olmaz. Aktif kod, config, test ve
dokümanlarda eski kimliğe **sıfır atıf** zorunludur:

```bash
make model-kimlik   # python3 tools/model_kimlik.py --kontrol
make kamu-lint      # ozel mutlak yol/eski alan/sahte hash taramasi
make kamu-selftest  # kamu lint negatif fiksturleri
```

Kontrol `make dogrula`nın ön koşuludur (sayılan sekiz kaleme eklenmez): aktif
tek bir atıf veya bayat bir istisna hükmü FAIL eder. Tarama
`git ls-files --cached --others --exclude-standard` ile izlenen ve henüz
izlenmeyen (yok sayılmayan) dosyaları gezer. **Gördüğü küme ile incelediği küme
arasında sessiz fark yoktur:** her aday dosyanın ham baytları okunur; UTF-8
çözülen dosyalar satır satır, çözülemeyen veya NUL içeren dosyalar ikili
güvenli bayt aramasıyla (UTF-8 + UTF-16LE/BE) ve **boyut sınırı olmadan**
taranır. Okunamayan bir dosya varsa ve `tools/model_kimlik_istisna.json`
içindeki `onay` listesinde gerekçesiyle kayıtlı değilse hüküm FAIL olur; PASS
satırı `aday=… · taranan=… · incelenmedi=0 · onay=1 kayit · aktif=0`
sayaçlarını taşır.

`onay` listesine yalnız istisna defterinin kendisi `tanim` olarak yazılabilir
(kimliği tanımlamak için onu taşımak zorundadır); defter taranır, eşleşmeleri
"tanım" sayılır. `okunamaz` kaydı yalnız gerçekten okunamayan dosya içindir ve
dosya okunabilir hâle gelirse "onay gereksiz" diye FAIL eder; yani hiçbir dosya
kendi kendini muaf ilan edemez. `--oztest` on bir vakayı kanıtlar: temiz ağaç
(`incelenmedi=0`), tarihsel satırın muafiyeti, aktif metin, 4 MB üstü metin,
ikili dosya (UTF-8 + UTF-16LE), onaysız incelenemeyen dosya, gereksiz onay,
bozulan tarihsel satır, aktif dosyaya tanım onayı, defterin kendi `tanim`
onayının zorunluluğu ve PASS raporunun `aday/taranan/incelenmedi/onay/aktif`
sayaçları. Okunamayan dosya yolu gerçek ağaçta da ölçüldü: `chmod 000` →
`FAIL incelenmedi=1`; aynı dosya `onay` listesine gerekçesiyle eklendiğinde
`PASS incelenmedi=1 onay=2`; izin geri açıldığında `FAIL ONAY GEREKSIZ`;
onay kaldırıldığında `PASS incelenmedi=0 onay=1`.

Bu korumaların geri alınamaması `make mutasyon` içindeki yedi adlandırılmış
mutantla ölçülür: ikili bayt araması, 4 MB üstü sessiz atlama, onaysız
incelenemeyenin sessiz geçilmesi, tek genel onayın tüm incelenemeyenleri
kapsaması, defterin kendi tanım onayının silinmesi, defter tanım SHA-256'sının
doğrulanmaması ve PASS raporundan aktif sayacının çıkarılması. Her mutant
kapının kendi `--oztest`/`--kontrol` bulgusunu üretir; kural silinirse vaka
`ATESLEMEDI` olur ve batarya yeşil dönemez. Yeni bir emekli kimlik
eklenirse önce tarihsel satırlar değiştirilmeden deftere satır hash'leriyle
kaydedilir, sonra aktif atıflar temizlenir.

## Ağacı yenileme

```bash
python3 tools/yayinla.py --lab <LAB_KOKU>            # kuru koşu
python3 tools/yayinla.py --lab <LAB_KOKU> --uygula
make dogrula
```

Aktarım yalnız `tools/yayinla.py` içindeki **açık listede** yazan yolları taşır.
Listeye yeni bir yol eklemek bilinçli bir karardır: eklenen dosya bir daha
sır taramasından geçer ve bulgu varsa hiçbir şey yazılmaz.

Aktarımın iki mekanik kuralı vardır ve ikisi de ölçülebilir:

1. **Yol normalizasyonu.** Metin dosyalarında sahibin mutlak ev yolu öneki
   (`<ev-yolu>/…`) `~/` olarak yazılır. Ölçüm kaydının anlamı değişmez; klonlayan için sert
   referans kalmaz. Parite kontrolü **normalize kaynak ↔ ham hedef** üzerinden
   yapılır, yani bu dönüşüm bir farkı gizlemez.
2. **Ürün yasağı.** Planda `.pdf`, `.docx`, `.tex`, `.zip`, `.bundle` gibi üretilmiş
   ürün/arşiv uzantısı görünürse aktarım **hiç yazmadan** çıkar.

## İddia defteri ve kapsam sınırı

`make iddia`, bu depodaki public sayısal iddiaları `tools/iddia_defteri.json`
üzerinden yeniden ölçer; her `OLCULDU` satırının son ölçülen ham çıktı satırı
`tools/iddia_olcum.json` içinde aynı `IDD-*` anahtarıyla saklanır. Ham kanıt güncel
çıktıyla birebir aynı değilse veya beyanla çelişirse satır kırmızı olur; anlık
görüntü yalnızca `make iddia-yaz` ile yenilenir. Defter dört dokümanı tarar: kök
`README.md`, `README.tr.md`, bu dosya ve `docs/EN/QUICKSTART.md`. Tarihli kayıtlar (`OLCUM-*`, `SURUM.md`) ve üretilmiş
tablolar (`MUTASYON_KAPSAM.md`, `GUVENLIK.md`) kapsam dışıdır: bunlar yeniden
koşulacak iddia değil, ölçümün o günkü kaydıdır. Kapsam dışı dosyalar yeşil
sayılmaz; defterin `kapsam.haric` bloğunda gerekçeleriyle listelenir.

Kapsam kapısı bu sınırı makineye bağlar: üç public dokümandaki sayısal ölçüm
iddiaları — oranlar, ölçüm adı taşıyan sayılar ve üretilmiş sayaçlar — defterdeki
bir alıntının içinde değilse `kapsam.sayisal_istisna` içindeki dar ve gerekçeli
bir istisnayla eşleşmek zorundadır. Eşleşmeyen iddia `dosya:satır` ve jetonla,
gerekçesiz, ölü veya çok geniş istisna da kendi adıyla kırmızı olur. Kimlik,
sürüm, tarih ve çıkış kodu değerleri bu tanımın dışındadır; kapsamın kendisi
böylece her koşuda denetlenir.

Defterin üst düzeyindeki `olcum_dosyasi` alanı ham kanıt dosyasını adlandırır
(`tools/iddia_olcum.json`); `make iddia` bu yolun tam olarak o dosya olduğunu
doğrular. Defterin durum dağılımı [`IDDIA-OZET.md`](IDDIA-OZET.md) içindeki
makine okunur özetle her koşuda karşılaştırılır; ayrışma `rc=2` ile kırmızıdır.
Tek bir satırın defter → komut → ham kanıt izi kök README'deki *Tek bir
iddiayı elle izlemek* bölümündedir.

`make iddia-hizli` yalnız hızlı satırları ölçer; `dogrula` ve `mutasyon`
komutlarını koşmaz. Atlanan satırlar `ATLANDI` olarak basılır ve PASS sayılmaz;
varsayılan `make iddia` tam koşu olarak değişmez. `--yaz --hizli` reddedilir,
çünkü kısmi anlık görüntü diğer satırların ham kanıtını silerdi.
