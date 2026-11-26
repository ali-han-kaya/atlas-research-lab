# KOD `bedava` profili — model seçim ve emeklilik politikası

> **Yürürlük:** 21 Kasım 2026 · **Kapsam:** `KOD_SABLONLAR/routing.profiles.json`
> → `profiller.bedava` · **Bağlayıcı:** bu politikadaki koşullar sağlanmadan
> profil değiştirilmez. İhlal, `make katalog-kontrol` (CI dışında elle),
> `make dogrula` veya `make model-kimlik` hükümlerinden birini kırmızıya
> çevirir.

## 1. Profil ne için var, ne için yok

`bedava` profili KOD hattının **on rolünü** tek bir ücretsiz modele bağlar:
`kod-orchestrator`, `kod-scoper`, `kod-architect`, `kod-implementer`,
`kod-implementer-heavy`, `kod-tester`, `kod-gate-2a`, `kod-gate-2b`,
`kod-gate-2c-security`, `kod-gate`. Amaç duman ve doğrulama koşularını **$0 model
maliyetiyle** çalıştırmaktır.

Profil `bagimsizlik_feragati: true` taşır: 2A = 2B = 2C = aynı sağlayıcı
(`nvidia`). Bu yüzden KFAZ4 kapı sonuçları **bağımsızlık açısından karar değeri
taşımaz**; üretim ve karar koşusu `denge` veya `ekonomi` profiliyle yapılır.

**Sıfır maliyet iddiasının sınırı:** $0 yalnız bu on role aittir.
`KOD_SABLONLAR/opencode.json` içindeki **birincil sürücü** ayrı bir ayardır ve
ücretli olabilir; uçtan uca $0 iddiası için sürücünün de ücretsiz olduğu ve
günlük ücretsiz kotanın dolu olmadığı ölçülmelidir. Ücretsiz kotanın günlük
sınırı vardır; `:free` sınırsız erişim demek değildir.

## 2. Seçim koşulları — altısı birden

Bir kimlik `bedava` profiline ancak aşağıdaki altı koşulun **tamamı** ölçülerek
geçer. Koşullardan biri eksikse kimlik seçilmez; "muhtemelen uygundur" kaydı
yoktur, `OLCULMEDI` yazılır ve karar bekler.

| # | Koşul | Kanıt alanı | Geçme ölçütü |
|---|---|---|---|
| 1 | **Aynı aile** | models.dev `name`, `family`; `tools/model_kimlik_istisna.json` gerekçesi | `name` `Nemotron 3` ile başlar, sağlayıcı `nvidia`dır; `family` değeri kayda geçirilir; emekli kimliğin aile aidiyeti defter gerekçesinde yazılıdır |
| 2 | **Sıfır maliyet** | models.dev `cost.input`, `cost.output`, varsa diğer `cost.*` alanları | hepsi `0`; `:free` soneki **tek başına kanıt değildir** |
| 3 | **reasoning** | models.dev `reasoning` + `tools/model_katalog.json` aynı alan | canlı ve yerel değer ikisi de `true` |
| 4 | **tool_call** | models.dev `tool_call` + `tools/model_katalog.json` aynı alan | canlı ve yerel değer ikisi de `true` |
| 5 | **Canlı kayıt** | models.dev `status` | alan yok/`null` ya da `deprecated` değil |
| 6 | **Bağlam** | models.dev `limit.context`, `limit.output`; `bedava_politika.asgari_limit` | 200.000 bağlam / 32.768 çıktı tabanının altına düşmez |

**Aynı aile ölçütü.** Aile, model adındaki `Nemotron 3` kuşağı ve `nvidia`
sağlayıcısıdır; canlı `family` alanı (ölçümde `nemotron-ultra-free`) ayrıca
kaydedilir. Eski kimliğin tam değeri `tools/model_kimlik_istisna.json`
içindedir ve canlı katalogda artık bulunmadığı için eski kaydın canlı `family`
alanıyla karşılaştırılması **OLCULMEDI**dir. Farklı bir aileye geçiş emeklilik
değil, **yeni model ailesi kararıdır**: prosedür durur ve lab sahibinin yazılı
kararını ister.

**Bağlam alt sınırı.** Eşik `KOD_SABLONLAR/routing.profiles.json` →
`bedava_politika.asgari_limit` içinde **200.000 bağlam / 32.768 çıktı** olarak
yapılandırılmıştır; bu ölçülmüş bir maksimum değil, KOD fazlarının çok dosyalı
bağlam ve tek yanıt ihtiyacı için kabul edilen **politika tabanıdır**. Ölçülen
kimlik 1.000.000/65.536 verir; aday `limit.context` veya `limit.output` ile bu
tabanın altına düşerse `LIMIT_YETERSIZ` ile reddedilir, tahmin edilmez.

## 3. Canlı models.dev kanıtı — koşullar ve kayıt

### 3.1 Kanonik ölçüm ve otomasyon

```bash
python3 tools/katalog_kontrol.py     # kanonik rc
make katalog-kontrol                 # sarmalayıcı + append-only kayıt; GNU make hatayı 2'ye çevirir
```

- Kaynak: `https://models.dev/api.json`.
- **Canlı ölçüm CI dışındadır.** `make katalog-kontrol` ağ gerektirir; elle
  veya yerel zamanlanmış bir işle çalıştırılır. CI yalnız çevrimdışı
  `make katalog-selftest` testini `make dogrula-ci` üzerinden koşar.
- Ölçüm **on rolün tamamını** kapsar: `profiller.bedava` altındaki her `kod-*`
  anahtarı canlı kayda çözülür ve rol rol basılır. Rol sayısı 10 değilse kapı
  `ROL_SAYISI` hatasıyla kırmızıdır.
- `rc=0`, `SONUC: 9/9 gecerli · 0 bulgu` **ve** `BEDAVA: 10/10 rol ... cost 0/0
  ... reasoning/tool_call true` zorunludur.
- `rc=1` → allowlist sapması veya bedava koşulu ihlali. Adlandırılmış bulgular:
  `MODEL_YOK`, `SAGLAYICI_YOK`, `DURUM` (`deprecated`), `MALIYET`
  (`cost.input`/`cost.output` veya diğer sayısal alan ≠ 0), `YETENEK_FARKLI`
  (canlı `reasoning`/`tool_call` true değil veya yerel allowlist ile çelişiyor),
  `LIMIT_YETERSIZ` (`limit.context`/`limit.output` < `asgari_limit`),
  `KATALOGDA_YOK`, `TEK_KIMLIK_DEGIL`, `ROL_BOZUK`, `ROL_SAYISI`. Kimlik
  emekli sayılır ve §4 başlar.
- `rc=2` → ağ/JSON okunamadı: sonuç **`OLCULMEDI`**dir. Ölçüm kırmızıdır;
  PASS'a çevrilmez, profil değiştirilmez. `OLCULMEDI` satırı ham gerekçeyi
  (`models.dev okunamadi: ...`) taşır.

### 3.2 Kayıt alanları

Her ölçüm kaydı şunları taşır; kayıt **append-only**dir, eski satır silinmez:

- tarih (UTC), `kaynak` (`ci`/`yerel`), varsa `github_run_id`,
- `commit`, `tree`, `tree_sha256` — `make kanit` ile aynı ağaç özeti,
- `id`, `name`, `family`, `status`, `reasoning`, `tool_call`,
- `cost` nesnesinin tamamı, `limit.context`, `limit.output`,
- `asgari_limit` ve `roller` sayısı,
- sonuç (`PASS`/`FAIL`/`OLCULMEDI`), sebep ve komutun ham satırları,
- ölçüm anındaki tanım dosyalarının SHA-256'sı:
  `tools/model_katalog.json`, `KOD_SABLONLAR/routing.profiles.json`,
  `KOD_SABLONLAR/opencode.json`.

Makine kaydı `docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl` (satır başına bir JSON) ve
insan özeti §6'dır. `make katalog-kontrol` temiz ağaçta bu dosyaya ekler; ağaç
kirliyse kayıt `OLCULMEDI` olur ve PASS sayılmaz, çünkü `commit`/`tree` ölçülen
dosyalarla eşleşmez. CI aynı şemayı `$RUNNER_TEMP/bedava-katalog.jsonl` altına
yazar, `$GITHUB_STEP_SUMMARY`'ye basar ve `bedava-katalog-kaniti` artifact'ı
olarak yükler. Depodaki append-only kayda bu artifact'ın JSON satırı eklenir;
böylece depo kaydı CI koşusunun kendi commit/tree/hash'lerini taşır. CI belirteci salt-okunur olduğu için satırı bot commit etmez; depoya girişi ayrı
bir kanıt commit'idir ve o commit attestation commit'iyle birlikte push edilir;
kanıt zinciri bu çift için yeniden üretilir.

Yerel allowlist (`tools/model_katalog.json`) canlı kataloğun kopyası değildir;
yalnız aktif hatlarda geçen kimlikleri taşır. MOD-1/MOD-2 kapıları bu sabit
allowlist'e bakar ve hermetiktir; canlı kanıt bu kapıların yerine geçmez,
onları **tamamlar**.

## 4. Emekli kimlik değişim prosedürü

Sıra bağlayıcıdır. Bir adım yeşil olmadan sonrakine geçilmez.

### P0 — Tespit

`make katalog-kontrol` (CI dışında elle) `rc=1`
verdiğinde ya da canlı kayıt `MODEL_YOK` / `DURUM deprecated` / `YETENEK_FARKLI`
/ `MALIYET` / `LIMIT_YETERSIZ` ürettiğinde emeklilik başlar. `rc=2` ise
emeklilik değil **ölçüm tekrarı** gerekir: `OLCULMEDI` bir sapma kanıtı değildir.
Ham çıktı dosyaya alınır; özetle yetinilmez.

### P1 — Kanıtı dondur

`SURUM.md` ve `docs/OLCUM-*.md` içindeki tarihsel ham satırlar **değiştirilmez**.
Emeklilik kararı ve ham çıktı yeni bir tarihli kayda (bu dosyanın §6 tablosu
veya yeni bir `docs/OLCUM-*`) yazılır. Eski satırı silmek veya yeniden yazmak
tarihsel kanıtı tahrif eder; istisna defteri bunun için değil, **korunan**
satırlar için vardır.

### P2 — Aday seç

Aday §2'deki altı ölçütün tamamını sağlamalıdır. Sağlamıyorsa durulur; kısmi
uygunlukla profil değiştirilmez. Aynı ailede aday yoksa bu bir **aile
değişikliğidir** ve lab sahibinin yazılı kararı gerekir.

### P3 — Canlı kanıt

Aday önce `tools/model_katalog.json` allowlist'ine eklenir (eski kimlik, geçiş
tamamlanana kadar listede kalır), sonra:

```bash
python3 tools/katalog_kontrol.py
```

`rc=0` alınmadan routing değiştirilmez. Adayın §3.2 alanları kayda geçirilir.
`rc=2` ise ölçüm yoktur; karar da yoktur.

### P4 — Geçiş

Yalnız `profiller.bedava` altındaki on rol değiştirilir; `denge`, `kalite` ve
`ekonomi` profillerine dokunulmaz (istek açıkça onları da kapsamıyorsa).
Değişecek dosyalar:

1. `KOD_SABLONLAR/routing.profiles.json` → `profiller.bedava` (on rol),
2. `tools/model_katalog.json` → yeni kimlik; artık hiçbir aktif satırda
   geçmeyen eski kimlik listeden çıkarılır,
3. `KOD_SABLONLAR/opencode.json` → yalnız birincil sürücü de değişiyorsa
   `_model_notu` ve ilgili alan,
4. ajan frontmatter'ında sabit model varsa yalnız o satır.

Geçişten sonra `make dogrula` MOD-1/MOD-2'yi yeşil vermelidir; yeni kimlik
allowlist'te yoksa veya eski kimlik aktif bir satırda kaldıysa kapı kırmızıdır.

### P5 — Emekli kimliği deftere bağla

Eski kimlik silinmez; `tools/model_kimlik_istisna.json` içine kaydedilir.

1. `emekli_kimlikler` dizisine kayıt ekle:
   `kimlik`, `yerine` (yeni kimlik), `tarih` (`YYYY-MM-DD`), `gerekce`
   (neden emekli, hangi canlı kanıt).
2. Hayatta kalan **tarihsel** ham satırları bul:

   ```bash
   python3 tools/model_kimlik.py --envanter
   ```

   Çıktıdaki her `(dosya, satır SHA-256)` çifti `istisnalar` dizisine
   gerekçesiyle eklenir. Aynı çift iki kez yazılamaz.
3. **Aktif** bir dosya `onay` listesine yazılamaz; `onay` listesindeki tek
   `tanim` kaydı istisna defterinin kendisidir. Okunamayan bir dosya gerçekten
   varsa `okunamaz` kaydı gerekçesiyle eklenir; dosya okunabilir hâle gelirse
   kontrol `ONAY GEREKSIZ` diyerek kırmızı olur.
4. Defterin kimlik/istisna içeriği değiştiği için `onay[0].sha256` bayatlar.
   Güncel tanım hash'ini üret ve yaz:

   ```bash
   python3 - <<'PY'
   import importlib.util, json
   s = importlib.util.spec_from_file_location('m', 'tools/model_kimlik.py')
   m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
   print(m.defter_tanim_sha256(json.load(open('tools/model_kimlik_istisna.json'))))
   PY
   ```

   Bu hash `onay` listesini kapsamaz; yalnız kimlik ve istisna içeriğini
   bağlar. Hash güncellenmezse kontrol `defter tanim hash tutmuyor` ile FAIL
   verir.

### P6 — Kapılar

Sırayla, hepsi yeşil olmadan commit yok:

```bash
make model-kimlik        # PASS · incelenmedi=0 · onay=1 kayit · aktif=0
                         # onayli okunamaz: PASS · incelenmedi=1 · onay=2 kayit · aktif=0
python3 tools/model_kimlik.py --oztest    # 15/15
make mutasyon            # 113/113 kural + 29/29 beklenen bulgu (142 vaka)
make dogrula             # 8/8 · H2 84
make kapsam              # ratchet PASS
make katalog-kontrol     # canli: allowlist + on rol; OLCULMEDI PASS degil
```

`make model-kimlik` FAIL verirse aktif atıf kaldırılır; tarihsel satır
değiştirilmez. Temiz ağaçta PASS satırı `incelenmedi=0 · onay=1` taşır; `onay`
listesinde gerekçeli bir `okunamaz` kaydı varsa meşru PASS satırı
`incelenmedi=1 (onayli=1 · onaysiz=0) · onay=2` olur. Bu, atlamanın gizlendiği
değil, gerekçeli onayla görünür kaldığı durumdur. Bayat istisna
(`BAYAT ISTISNA`) varsa satır hash'i yeniden
ölçülür; satır gerçekten değişmişse bu bir tahrifattır ve istisna defteriyle
gizlenmez.

### P7 — Kayıt, commit ve CI

- `SURUM.md` yeni sürüm kaydı (ölçülen sayılarla),
- `docs/OLGULAR.md` → `lab_surum`,
- `docs/DERSLER_v1_2026-08-30.md` ders satırı,
- sayısal iddia değiştiyse `tools/iddia_defteri.json` + `make iddia-yaz`,
- `make katalog-kontrol` çıktısı ve `docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl`
  satırı (commit/tree/tree_sha256 + tanım SHA-256'ları),
- `make kanit` zinciri (`kanit`, `kanit-dogrula`, `kanit-paket-dogrula`,
  `durum-kontrol`), commit, `origin/main`e push, o commit'in CI koşusu
  `success`.

### P8 — Geri alma

Canlı kanıt geçişten sonra düşerse (kimlik kalktı, `deprecated` oldu, yetenek
bayrağı değişti) routing ve katalog **yeni bir commit** ile geri alınır.
Geçmiş yeniden yazılmaz (`reset --hard`, `push --force` yok). Emekli kimlik
emekli kalır: eski tarihsel satırlar ve defter kayıtları silinmez; geri alma
yalnız aktif yönlendirmeyi düzeltir.

## 5. Yasaklar — fail-closed

- `reasoning` veya `tool_call` `false` olan ücretsiz kimliği `bedava`ya almak.
- Maliyeti yalnız `:free` sonekinden okumak; `cost` alanlarını ölçmemek.
- Aile değişikliğini "emeklilik" diye sessizce yapmak; lab sahibi kararı
  olmadan farklı aileye geçmek.
- Tarihsel `SURUM`/`OLCUM` ham satırlarını silmek, yeniden yazmak veya
  hash'ini gizlemek.
- Aktif bir dosyayı `onay` listesine `okunamaz`/`tanim` diye yazmak; defter
  dışında kendi kendini muaf ilan etmek.
- Canlı ölçüm `rc=2` iken "muhtemelen güncel" demek; ağ yokluğunu PASS saymak.
- `docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl` satırını silmek, yeniden yazmak veya
  `FAIL`/`OLCULMEDI` satırını sonraki `PASS` ile gizlemek.
- `bedava` profilinde kapı bağımsızlığı iddia etmek veya KFAZ4 sonucunu karar
  kanıtı saymak.
- Kapsam dışı profilleri (`denge`, `kalite`, `ekonomi`) aynı commit'te
  gerekçesiz değiştirmek.

## 6. Ölçüm kaydı (append-only)

| Tarih (UTC) | Komut | Ham sonuç | rc | Dosya kimlikleri |
|---|---|---|---|---|
| 2026-11-21 | `python3 tools/katalog_kontrol.py` | `saglayici=1 · model=9` · `SONUC: 9/9 gecerli · 0 bulgu` · `HUKUM: GUNCEL` | 0 | katalog `0424fbde…` · routing `5d45f7ad…` · opencode `fbed4ce1…` |

Aynı ölçümde canlı kayıt (`https://models.dev/api.json`,
`openrouter.models["nvidia/nemotron-3-ultra-550b-a55b:free"]`):

| Alan | Değer |
|---|---|
| `id` | `nvidia/nemotron-3-ultra-550b-a55b:free` |
| `name` | `Nemotron 3 Ultra (free)` |
| `family` | `nemotron-ultra-free` |
| `status` | `null` |
| `reasoning` | `true` |
| `tool_call` | `true` |
| `cost` | `{"input": 0, "output": 0}` |
| `limit` | `{"context": 1000000, "output": 65536}` |
| `modalities.input` | `["text"]` |
| Emekli kimlik canlıda | **yok** (`False`) |

Bu tablo 21.11.2026'da **elle** alınmış tarihsel kayıttır; sonraki ölçüm yeni
satır olarak eklenir, eskisi değiştirilmez. Bu tarihten sonra ölçüm
**sürekli değildir**: canlı ölçüm ağ gerektirdiği için CI dışında, elle/yerel
koşulur; on rolü canlı models.dev'den yeniden ölçer; sonuç
`docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl` kaydına commit/tree/tree_sha256 ve tanım
SHA-256'larıyla eklenir. Tek günlük anlık görüntüye bağımlılık yoktur; ağ
okunamazsa kayıt `OLCULMEDI` olur; PASS sayılmaz.

### 6.1 Otomatik kayıt sözleşmesi

`docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl` satır başına bir JSON nesnesi taşır;
alanlar §3.2'dedir. Kayıt yalnız eklenir: eski satır silinmez, yeniden
yazılmaz. Bir satırın `sonuc` alanı `FAIL` veya `OLCULMEDI` ise bu, sonraki
`PASS` tarafından gizlenmez; P0–P8 izi olarak kalır. Kayıt yerel dosyada
tutulur; CI artifact'ı yoktur.

## 7. İlgili komutlar ve dosyalar

| Yol / komut | İşlev |
|---|---|
| `KOD_SABLONLAR/routing.profiles.json` | `profiller.bedava` — on rolün model eşlemesi |
| `KOD_SABLONLAR/opencode.json` | birincil sürücü ve `_model_notu` |
| `tools/model_katalog.json` | hermetik allowlist (MOD-1/MOD-2) |
| `tools/katalog_kontrol.py` | canlı models.dev kapısı: allowlist + on rol + append-only kayıt (ağ) |
| `tools/model_kimlik.py` | emekli kimlik taraması, `--oztest`, `--envanter` |
| `tools/model_kimlik_istisna.json` | emekli kimlik + satır hash'leri + `onay` |
| `make katalog-kontrol` | canlı ölçüm + `docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl` kaydı |
| `.github/workflows/dogrula.yml` | `dogrula` ve `iddia` işleri; canlı katalog işi yok |
| `make model-kimlik` | aktif atıf denetimi (fail-closed ön koşul) |
| `make mutasyon` | korumaların geri alınamazlığı (142 vaka) |
| `make dogrula` | sekiz kalemlik ana kapı (MOD-1/MOD-2 dahil) |
