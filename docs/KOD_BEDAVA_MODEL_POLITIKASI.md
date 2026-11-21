# KOD `bedava` profili — model seçim ve emeklilik politikası

> **Yürürlük:** 21 Kasım 2026 · **Kapsam:** `KOD_SABLONLAR/routing.profiles.json`
> → `profiller.bedava` · **Bağlayıcı:** bu politikadaki koşullar sağlanmadan
> profil değiştirilmez. İhlal, `make katalog-kontrol`, `make dogrula` veya
> `make model-kimlik` hükümlerinden birini kırmızıya çevirir.

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

## 2. Seçim koşulları — dördü birden

Bir kimlik `bedava` profiline ancak aşağıdaki dört koşulun **tamamı** ölçülerek
geçer. Koşullardan biri eksikse kimlik seçilmez; "muhtemelen uygundur" kaydı
yoktur, `OLCULMEDI` yazılır ve karar bekler.

| # | Koşul | Kanıt alanı | Geçme ölçütü |
|---|---|---|---|
| 1 | **Aynı aile** | models.dev `name`, `family`; `tools/model_kimlik_istisna.json` gerekçesi | `name` `Nemotron 3` ile başlar, sağlayıcı `nvidia`dır; `family` değeri kayda geçirilir; emekli kimliğin aile aidiyeti defter gerekçesinde yazılıdır |
| 2 | **Sıfır maliyet** | models.dev `cost.input`, `cost.output`, varsa diğer `cost.*` alanları | hepsi `0`; `:free` soneki **tek başına kanıt değildir** |
| 3 | **reasoning** | models.dev `reasoning` + `tools/model_katalog.json` aynı alan | canlı ve yerel değer ikisi de `true` |
| 4 | **tool_call** | models.dev `tool_call` + `tools/model_katalog.json` aynı alan | canlı ve yerel değer ikisi de `true` |
| 5 | **Canlı kayıt** | models.dev `status` | alan yok/`null` ya da `deprecated` değil |
| 6 | **Bağlam** | models.dev `limit.context`, `limit.output` | fazın `max_tokens` ve bağlam ihtiyacını karşılar |

**Aynı aile ölçütü.** Aile, model adındaki `Nemotron 3` kuşağı ve `nvidia`
sağlayıcısıdır; canlı `family` alanı (ölçümde `nemotron-ultra-free`) ayrıca
kaydedilir. Eski kimliğin tam değeri `tools/model_kimlik_istisna.json`
içindedir ve canlı katalogda artık bulunmadığı için eski kaydın canlı `family`
alanıyla karşılaştırılması **OLCULMEDI**dir. Farklı bir aileye geçiş emeklilik
değil, **yeni model ailesi kararıdır**: prosedür durur ve lab sahibinin yazılı
kararını ister.

**Bağlam alt sınırı.** Ölçülen kimlik 1.000.000 bağlam ve 65.536 çıktı tokenı
verir. Aday, koşulacak fazın `max_tokens` değerinin altındaysa reddedilir; bu
kontrol `limit.output` alanından okunur, tahmin edilmez.

## 3. Canlı models.dev kanıtı — koşullar ve kayıt

### 3.1 Kanonik ölçüm

```bash
python3 tools/katalog_kontrol.py     # kanonik rc
make katalog-kontrol                 # isteğe bağlı sarmalayıcı; GNU make hatayı 2'ye çevirir
```

- Kaynak: `https://models.dev/api.json` (ağ gerekir; **CI'da koşmaz**).
- `rc=0` ve `SONUC: 9/9 gecerli · 0 bulgu` zorunludur.
- `rc=1` → en az bir kimlik yok, `deprecated` veya yetenek alanı çelişkili:
  kimlik **emekli** sayılır, prosedür başlar.
- `rc=2` → ağ/JSON okunamadı: sonuç `OLCULMEDI`dir; PASS'a çevrilmez, profil
  değiştirilmez.

### 3.2 Kayıt alanları

Her ölçüm kaydı şunları taşır; kayıt **append-only**dir, eski satır silinmez:

- tarih (UTC) ve ölçen komut,
- `id`, `name`, `family`, `status`, `reasoning`, `tool_call`,
- `cost` nesnesinin tamamı, `limit.context`, `limit.output`,
- komutun ham son satırı ve `rc`,
- ölçüm anındaki dosya kimlikleri:
  `tools/model_katalog.json`, `KOD_SABLONLAR/routing.profiles.json`,
  `KOD_SABLONLAR/opencode.json` SHA-256.

Yerel allowlist (`tools/model_katalog.json`) canlı kataloğun kopyası değildir;
yalnız aktif hatlarda geçen kimlikleri taşır. MOD-1/MOD-2 kapıları bu sabit
allowlist'e bakar ve hermetiktir; canlı kanıt bu kapıların yerine geçmez,
onları **tamamlar**.

## 4. Emekli kimlik değişim prosedürü

Sıra bağlayıcıdır. Bir adım yeşil olmadan sonrakine geçilmez.

### P0 — Tespit

`python3 tools/katalog_kontrol.py` `rc=1` verdiğinde veya canlı kayıt
`MODEL_YOK` / `DURUM deprecated` / `YETENEK_FARKLI` ürettiğinde emeklilik
başlar. Ham çıktı dosyaya alınır; özetle yetinilmez.

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
python3 tools/model_kimlik.py --oztest    # 11/11
make mutasyon            # 98/98 kural + 18/18 beklenen bulgu
make dogrula             # 8/8 · H2 65
make kapsam              # ratchet PASS
```

`make model-kimlik` FAIL verirse aktif atıf kaldırılır; tarihsel satır
değiştirilmez. Bayat istisna (`BAYAT ISTISNA`) varsa satır hash'i yeniden
ölçülür; satır gerçekten değişmişse bu bir tahrifattır ve istisna defteriyle
gizlenmez.

### P7 — Kayıt, commit ve CI

- `SURUM.md` yeni sürüm kaydı (ölçülen sayılarla),
- `docs/OLGULAR.md` → `lab_surum`,
- `docs/DERSLER_v1_2026-08-30.md` ders satırı,
- sayısal iddia değiştiyse `tools/iddia_defteri.json` + `make iddia-yaz`,
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

Bu tablo bir **anlık görüntüdür**; sonraki ölçüm yeni satır olarak eklenir,
eskisi değiştirilmez. Sayılar bu dosyada elle güncellenmez; güncel allowlist
denetimi `make iddia` ve `make katalog-kontrol` ile yeniden ölçülür.

## 7. İlgili komutlar ve dosyalar

| Yol / komut | İşlev |
|---|---|
| `KOD_SABLONLAR/routing.profiles.json` | `profiller.bedava` — on rolün model eşlemesi |
| `KOD_SABLONLAR/opencode.json` | birincil sürücü ve `_model_notu` |
| `tools/model_katalog.json` | hermetik allowlist (MOD-1/MOD-2) |
| `tools/katalog_kontrol.py` | canlı models.dev karşılaştırması (ağ; CI dışı) |
| `tools/model_kimlik.py` | emekli kimlik taraması, `--oztest`, `--envanter` |
| `tools/model_kimlik_istisna.json` | emekli kimlik + satır hash'leri + `onay` |
| `make katalog-kontrol` | canlı ölçüm sarmalayıcısı |
| `make model-kimlik` | aktif atıf denetimi (fail-closed ön koşul) |
| `make mutasyon` | korumaların geri alınamazlığı (116 vaka) |
| `make dogrula` | sekiz kalemlik ana kapı (MOD-1/MOD-2 dahil) |
