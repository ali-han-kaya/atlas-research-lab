# Yayın sözleşmesi — public ağaç

Bu belge, `atlas-research-lab` public deposuna **neyin** girebileceğini ve
giren şeyin nasıl denetlendiğini tanımlar. Sözleşmenin makine-okunur tek
kaynağı [`../tools/yayin_manifest.json`](../tools/yayin_manifest.json)
dosyasıdır; bu belge onun insan-okunur açıklamasıdır.

## Temel ilke

Public depo, özel laboratuvarın **ürün arşivi değil, üretim mekanizmasının
seçilmiş kopyasıdır.** Bir dosya "yararlı" olduğu için değil, yayın kapsamına
açıkça yazıldığı için girer. Listede olmayan dosya, temiz görünse bile yayına
girmez.

## Kapsam

| Durum | Kapsam | Gerekçe |
|---|---|---|
| **Dahil** | ATLAS/KOD/Toolkit hatları, ajan ve komut tanımları, şablonlar, kapı betikleri, testler, mutasyon kataloğu, `DENEME/` regresyon fikstürü, seçilmiş ölçüm ve ders kayıtları, README/Makefile/LICENSE, bu sözleşme ve yayın kapısı | Mekanizmayı okutan, çalıştıran ve denetleyen asgari küme |
| **Hariç** | Üretilmiş makale metinleri, PDF/DOCX/LaTeX, konu korpusları, ham veri ve büyük veri dosyaları, `projeler/` altındaki çalışmalar, kişisel oturum devirleri, sırlar ve kimlik bilgileri | Ürün/özel bağlam arşivi; yayın mekanizmasının parçası değil |
| **İstisna** | Kapıların pinlediği kanonik OLGU-06 devri | Sürüm satırı ve `olgu_lint` bu kayda bağlı; kimlik bilgisi taşımadığı ölçüldü |

Bir makale veya ham çıktı, "sadece örnek" diye dahi public ağaca eklenmez.
Örnek gerekiyorsa sentetik ve makale metni taşımayan bir fikstür kullanılır;
`DENEME/` bunun bilinçli örneğidir.

## Manifest neyi listeler?

`tools/yayin_manifest.json` üç bölüm taşır:

- `izinli`: public ağaçta bulunabilecek **her** dosyanın açık yolu.
- `yasak_yollar`: makale/korpus/veri/proje/arşiv kümelerinin yol önekleri.
- `yasak_uzantilar`: PDF, LaTeX, ofis, arşiv ve büyük veri uzantıları.

Manifestte olup ağaçta olmayan yol da hatadır. Böylece kapı iki yönlü parite
kurar: **ağaçta fazlalık** ve **manifestte ölü kayıt** ayrı ayrı kırmızıdır.

### Yeni dosya ekleme prosedürü

1. Dosyanın gerçekten mekanizmaya ait olduğunu ve makale/ham çıktı olmadığını
   yazılı olarak gerekçelendir.
2. Yolu `izinli` listesine ekle; kategori ve gerekçeyi aynı değişiklikte tut.
3. `python3 tools/yayin_kapisi.py --kontrol --oztest` koş.
4. `make dogrula` ve `make iddia` koş.
5. Kapı temizse içerik commit'i, ardından yeni ağaç için attestation commit'i
   üret.

Listeye eklenmeyen dosya `YAYIN-01` ile durur. "Önce commit, sonra manifest"
sırası yasaktır; kapı push edilecek ağacın tamamını görmeden yeşil dönmez.

## Kapı neyi arar?

`tools/yayin_kapisi.py` hem izlenen hem de ignore edilmemiş izlenmeyen
dosyaları `git ls-files --cached --others --exclude-standard` ile görür.
Böylece "henüz eklemedim" denilen bir sızıntı da gözden kaçmaz. Buna ek olarak
H1 (`tools/dogrula.py` → `hijyen`) ignore edilmiş dosyaları da tarar: `.gitignore`
bir savunma katmanıdır, tek başına hüküm değildir. Aynı yasak yol/uzantı listesi
H1, yayın kapısı ve `yayinla.py` tarafından `yayin_manifest.json` üzerinden
okunur; liste kopyalanmaz.

| Kod | Anlam |
|---|---|
| `YAYIN-01` | Manifestte listelenmemiş dosya |
| `YAYIN-02` | Yasak yol veya uzantı (makale/PDF/proje/arşiv) |
| `YAYIN-03` | Sır/token deseni veya private-key bloğu |
| `YAYIN-04` | Okunamayan veya 5 MB üstü dosya (fail-closed) |
| `YAYIN-05` | Kişisel mutlak yol |
| `YAYIN-06` | Makale iskeleti işareti |
| `YAYIN-07` | Manifestte olup ağaçta olmayan yol |

Bulgu satırı yalnız **dosya, satır ve kural kimliği** yazar; sır değerini veya
eşleşen metni basmaz. Bir dosya okunamıyorsa "temiz" sayılmaz: `YAYIN-04` ile
durdurur.

### Commit ateş duvarı

`.githooks/pre-commit` sır kapısından sonra `yayin_kapisi.py --staged` çalıştırır.
Staged dosyalarda yasak yol/uzantı veya 5 MB üstü boyut varsa commit fail-closed
durur. `git commit --no-verify` ile bu kapı atlansa bile H1 çalışma ağacında,
CI ise push edilen ağaçta aynı ihlali yakalar. `.gitignore` aynı kapsamı ayrıca
ignore eder; fakat ignore edilmiş bir dosya H1 tarafından görülmeye devam eder.

### Tek komut

```bash
python3 tools/yayin_kapisi.py --kontrol --oztest
python3 tools/yayin_kapisi.py --staged   # pre-commit kısa yolu
```

`--oztest` geçici bir git deposunda temiz tabanı ve beş ihlali (listesiz dosya,
yasak yol/uzantı, sır, kişisel yol, makale iskeleti) ayrı ayrı ateşler. Ana
ağaca yazmaz. `make yayin-kapisi` aynı komutun kısa yoludur; `make dogrula`
bunu **ön koşul** olarak çağırır.

## Parite ve kaynak laboratuvar

Public ağaç, kaynak laboratuvardan `tools/yayinla.py` ile aktarılır. Aracın
açık `KOKLER`/`DOSYALAR` listesi ile public manifest birbirini tamamlar:

```bash
# Kaynak labdan public'e kuru aktarım; hiçbir şey yazmaz.
python3 tools/yayinla.py --lab <kaynak-lab-koku>
```

Beklenen sonuç `PARITE: TEMIZ — 0 yeni / 0 değişen / 0 silinen`dır. Drift varsa
önce kaynak ve public ağaç hizalanır; `--uygula` körlemesine çalıştırılmaz.
`yayinla` kaynak listesini, `yayin_kapisi` hedef ağacın manifestini denetler;
biri diğerinin yerine geçmez.

## Sınırlar

- Kapı, makale **içeriğinin akademik doğruluğunu** ölçmez; yalnız güçlü makale
  iskeleti izlerini ve yasak uzantıları yakalar.
- Sır taraması bilinen desenlerle sınırlıdır; bilinmeyen bir biçimi garanti
  etmez. Bu yüzden `make dogrula` içindeki bağımsız sır taraması ve
  `sir_kapisi` de ayrıca koşar.
- Manifest bakımı insan kararıdır; kapı yanlış bir dosyanın listeye eklenmesini
  tek başına engelleyemez. Bu yüzden ekleme gerekçesi ve iki bağımsız kapı
  zorunludur.
- Dış/bağımsız insan denetimi bu belgenin kapsamında değildir; ölçülmeyen
  kısımlar `OLCULMEYEN` olarak kalır.
