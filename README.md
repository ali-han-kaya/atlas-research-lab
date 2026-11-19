## ATLAS Research Lab — in brief

**A verification-first, multi-agent research lab.** ATLAS treats verification as the
product: a delivery is judged by gates that run over its own bytes, never by a model's
claim that the work was done.

- **What it does.** Academic audit and hardening (scope → three parallel review lenses →
targeted fixes → master revision → 2-of-2 acceptance) and a code pipeline (KFAZ0–5 with a
mandatory baseline and 2A/2B/2C gates). Generated papers, corpora and session handoffs
are deliberately excluded — this repository is the mechanism, not the archive.
- **Which gates exist.** An eight-predicate revision gate (count drift, claim IDs,
body/title consistency, class scan, residue bucket, measurement freshness, version
marker, source level — all eight must be zero); a closed severity list P0/P1/P2 where any
unknown label becomes `SCHEMA_INVALID` → P0; KEEP fingerprints so silent deletion becomes
visible; evidence levels (`BIRINCIL`/`DIJITAL`/`BEYAN`/`OLCULMEDI`); fail-closed handling
(unmeasured is never a pass); and tamper detection (`GATE_TAMPERED` → P0).
- **How claims are verified.** `make dogrula` (hygiene, syntax, secret scan, three
self-test suites), `make mutasyon` (five gate rules must actually fire: clean baseline +
one violation + a red verdict), and `tools/yayinla.py` (publish parity: 0 new / 0 changed
/ 0 deleted). The same commands run in CI on GitHub Actions.
- **Measured state.** `make dogrula` → **6 pass / 0 fail / 1 not run** (T1 is reported as
`CALISTIRILMADI` and never counted as a pass); KOD self-test **174/174**; mutation battery
**5/5**; CI green.

---

# ATLAS Research Lab

**Kanıt disiplinli, çok ajanlı üretim laboratuvarı.** Akademik metin ve yazılım
üretimini "model şöyle dedi" üzerine değil, **teslimin kendi baytları üzerinde
koşan kapılar** üzerine kurar.

Bu depo laboratuvarın kendisidir: hatlar, ajanlar, şablonlar, kapı betikleri,
ölçüm kayıtları ve öğrenim defteri. Laboratuvarın ürettiği makaleler ve kitapçıklar
burada **yoktur** — kapsam ve gerekçesi: [docs/README.md](docs/README.md).

Sürüm: ATLAS hattı **v5.5.4** · Komut Toolkit **v4** · KOD hattı **KFAZ0–5**

---

## Temel iddia

Bir teslimin doğruluğu, onu üreten modelin beyanıyla ölçülmez. Ölçülebilir üç şey vardır:

1. **koşan komut**, 2. o komutun **ham çıktısı**, 3. o çıktının bağlı olduğu **birincil kayıt**.

Geri kalan her cümle bir *iddiadır* ve iddia `OLCULMEYEN` alanına yazılır.
Buradan iki tasarım kuralı çıkar:

- **Fail-closed:** ölçülemeyen şey "geçti" sayılmaz. Boş bir denetim (`findings: []`)
  olumlu karar üretemez; koşmayan bir kapı `PASS` değildir.
- **Beyan ≠ kanıt:** kapı, ajanın "8/8 düzeltme uygulandı" beyanını değil, metinde
  gerçekten bulunan `FIX-###` kimliklerini sayar.

Bu ikinci kuralın neden var olduğu depoda kanıtıyla durur: `DENEME/` bilerek
dondurulmuş **kusurlu** bir koşudur — sekiz düzeltmenin ikisi uygulanmışken bütün
zincir `FULL PASS` vermişti. Ders kaybolmasın diye düzeltilmedi; regresyon fikstürü
olarak saklandı.

---

## Hatlar

| Katman | Klasör | Ne yapar |
|---|---|---|
| **ATLAS** | `ATLAS_SABLONLAR/` | Akademik denetim + sertleştirme: FAZ0 kapsam → FAZ1 üç lens paralel → FAZ2 hedefli düzeltme → FAZ3 MASTER → FAZ4 2-of-2 kapı. Her fazda insan onayı; `/atlas-full` **kasten yoktur**. |
| **KOD** | `KOD_SABLONLAR/` | Üretim hattı KFAZ0–5: kapsam, tasarım, uygulama, kanıt, 2A/2B/2C kapıları, teslim. Kod hattının akademik hatta olmayan zorunlu artefaktı **taban (BASELINE)**. |
| **Toolkit** | `KOMUT_TOOLKIT_v4/` | Tek yapıştırmalık, model-agnostik oturum disiplini: C1 sözleşme · C2 koruma · C3 sınıflandırıcı · C4 pipeline · C5 kapılar · C6 ahlak + `ARACLAR/` altındaki çalıştırılabilir denetimler. |
| **Rafine** | `RAFINE_SABLON/` | Elde metin varken bir sürüm ileri taşıma: asgari müdahale + KEEP parmak izi + kapanış kontrolü. Yeni iddia üretmez. |
| **Hakem** | `HAKEM_HEYETI/` | Çok modelli hakem paneli sözleşmesi (F0–F6) ve iki turlu acımasız denetim komutu. |
| **Ortak** | `ORTAK/` | İki hattın paylaştığı kapı (`ortak_gate.py`), yönlendirme ve bütçe koruması. |
| **Kayıt** | `docs/` | Ölçüm koşuları, denetim raporları, ders defteri, kanonik olgu tablosu. |
| **Mutasyon** | `tools/mutasyon_bataryasi.py` | Kapı kuralları gerçekten ateşliyor mu: temiz taban + tek ihlal + kırmızı hüküm. Tek dosya, kişisel yol yok, `SKILL.md` bağımlılığı yok. |

Ajan tanımları `.opencode/agent/` ve `.opencode/command/` altındadır; her girdi
`ATLAS_SABLONLAR/.opencode/` içindeki tek kaynağa **göreli symlink**'tir — ikinci
nüsha yoktur.

---

## Kapı mimarisi

- **Kapalı şiddet listesi.** Yalnız `P0` (teslimi engeller), `P1`, `P2`. Tanınmayan
  her etiket (`CRITICAL`, `high`, boşluklu `"P0 "`, …) `SCHEMA_INVALID` üretir ve
  `P0` sayılır: "tanımadım, saymadım" yasaktır.
- **Koruma sözleşmesi (KEEP).** Her bölüm için parmak izi alınır; sessiz silme
  görünür hale gelir. Hacim anlam değildir: içerik kelimesi tutma oranı da ölçülür.
- **Sekiz yüklemli revizyon kapısı** (`docs/README.md` → kaynaklar): sayım farkı,
  iddia kimliği, gövde-başlık tutarlılığı, sınıf taraması, artık kova, ölçüm tazeliği,
  sürüm işaretçisi, kaynak seviyesi. Sekizi de `0` olmadan yeni sürüm kabul edilmez.
- **Kanıt seviyeleri.** `BIRINCIL` (yayıncı/orijinal) · `DIJITAL` (dijital nüsha) ·
  `BEYAN` (kaynak beyanı var, bağımsız doğrulama yok) · `OLCULMEDI`.
  İki modelin aynı şeyi söylemesi kanıt değildir; bağımsızlık birincil kayıttan gelir.
- **Kapı kendini indiremez.** Eşik ve muafiyetler işin başında yazılır; sonda
  değişmişse `GATE_TAMPERED` → `P0` ve terminal.

---

## Hızlı başlangıç

```bash
git clone https://github.com/ali-han-kaya/atlas-research-lab.git
cd atlas-research-lab
python3 -m pip install -r requirements-dev.txt   # DOI doğrulaması için requests
make dogrula
```

`make dogrula` tek giriştir; yedi kalemi sırayla koşar ve **ham çıktılarını** yazar:
depo hijyeni, Python sözdizimi, kabuk sözdizimi, sır taraması ve üç öz-test paketi
(ATLAS · KOD · Toolkit). Sayıları README'ye elle yazmayız — betikler kendileri basar.
Model çağrısı yoktur: yerel batarya **$0**.

Paketleri ayrı ayrı koşmak istersen (yollar depo köküne görelidir):

```bash
python3 ATLAS_SABLONLAR/scripts/atlas_selftest.py        # OLG-1 → CALISTIRILMADI
python3 KOD_SABLONLAR/scripts/kod_selftest.py
(cd KOMUT_TOOLKIT_v4/ARACLAR/betikler && python3 v4_selftest.py)
```

`make mutasyon` ayrı bir kanıttır: her kural için önce **temiz taban** (`rc=0`)
alır, aynı kopyada tek bir ihlal üretir ve kapının **kırmızıya döndüğünü** ölçer.
İkisi birlikte olmadan vaka geçmez — yani yeşil, kapının değil girdinin özelliği
olamaz. Model, ağ ve yerel katalog gerekmez.

Model kataloğu depoda **sabittir** (`tools/model_katalog.json`): MOD-1/MOD-2
yaşayan kataloğa değil bu allowlist anlık görüntüsüne bakar, böylece KOD sayısı
her klonda ve runner'da aynı çıkar. Canlı katalogla denetim isteğe bağlıdır:
`ATLAS_MODEL_KATALOG=~/.cache/opencode/models.json make dogrula`.

### Bir projede ATLAS hattını kullanmak

```bash
mkdir -p proje
cp -r ATLAS_SABLONLAR/.opencode ATLAS_SABLONLAR/opencode.json \
      ATLAS_SABLONLAR/AGENTS.md ATLAS_SABLONLAR/routing.profiles.json \
      ATLAS_SABLONLAR/scripts ATLAS_SABLONLAR/templates ATLAS_SABLONLAR/docs proje/
chmod +x proje/scripts/*.sh proje/scripts/*.py
cd proje && opencode
```

Sonra `/atlas-faz0` ile başlanır; her fazın sonunda insan onayı vardır.
Yalnız `.opencode` + `opencode.json` kopyalamak yetmez — komutlar `scripts/`'i çağırır,
yapılandırma `AGENTS.md`'yi yükler.

### Kod hattı

Giriş: [`KOD_SABLONLAR/00_KOD_OKU_BENI.md`](KOD_SABLONLAR/00_KOD_OKU_BENI.md) ·
operatör komutları: [`KOD_SABLONLAR/OPERATOR_SURME.md`](KOD_SABLONLAR/OPERATOR_SURME.md).
Hattı **dışarıdan bir operatör** sürer; faz ajanı bir sonraki fazı başlatmaz.

### ToolKit (tek dosya, herhangi bir sohbet)

`KOMUT_TOOLKIT_v4/000_ONCE_BUNU_YAPISTIR.md` dosyasını olduğu gibi bir sohbete
yapıştırın: araç envanterini yoklar, sınıflandırır ve F0–F6 zincirini yürütür.
Makine denetimleri `KOMUT_TOOLKIT_v4/ARACLAR/betikler/` altındadır.

---

## Depo haritası

```
ATLAS_SABLONLAR/   akademik hat: ajanlar, komutlar, şablonlar, 22 denetim betiği
KOD_SABLONLAR/     kod hattı: KFAZ0-5 ajanları, kapılar, test/sır/izin denetimleri
KOMUT_TOOLKIT_v4/  tek komut + C1-C6 çekirdeği + çalıştırılabilir araçlar
RAFINE_SABLON/     sürüm yükseltme: KEEP listesi, komut şablonu, kapanış kontrolü
HAKEM_HEYETI/      hakem paneli sözleşmesi + iki turlu denetim komutu
ORTAK/             paylaşılan kapı, yönlendirme, bütçe koruması
DENEME/            bilerek kusurlu, dondurulmuş örnek koşu
docs/              ölçümler, denetimler, ders defteri, olgu tablosu
tools/             bu deponun kendi araçları (doğrulama, yayın aktarımı)
```

---

## Otomasyon

| Ne | Nasıl |
|---|---|
| Tek giriş doğrulama | `make dogrula` → `tools/dogrula.py` (yedi kalem, fail-closed) |
| Runner doğrulaması | `make dogrula-ci` — yalnız o ortamda ölçülebilen kalemler hükme girer, öz-testler rapor |
| Sürekli doğrulama | `.github/workflows/dogrula.yml` — her push/PR ve haftalık |
| Özel ağaçtan aktarım | `tools/yayinla.py --lab <yol>` (kuru koşu) · `--uygula` (yazar) |

`tools/yayinla.py` yalnız **açık listedeki** mekanizma yollarını taşır; liste dışına
çıkmaz, hedefte liste dışı dosya bırakmaz ve yazmadan önce sır taraması yapar —
bulgu varsa hiçbir şey yazmaz.

---

## Neyi ölçer, neyi ölçmez

- Öz-testler **kapıların davranışını** ölçer: her betik pozitif ve negatif fikirle
  sınanır. İçeriğin doğruluğunu ölçmez.
- Hat, testin **yokluğunu** ölçer; **boşluğunu** ölçmez. Boş gövdeli, her zaman geçen
  bir test bütün kapıları geçer. Bu risk `KOD_SABLONLAR/00_KOD_OKU_BENI.md` içinde
  açıkça yazılıdır ve katmanlı savunmayla daraltılır, sıfırlanmaz.
- `DENEME/` kapanış kapısının yanlış pozitif verebildiğini gösterir; kapı sonradan
  `fix_reconcile.py` ile sertleştirildi, ama "kapı her şeyi görür" iddiası yoktur.
- Makale içerikleri, kaynak korpusları ve oturum devir kayıtları bu depoda yoktur.
  Bu yüzden `DERSLER` ve ölçüm dosyalarındaki bazı atıflar özel ağaçtaki devir
  dosyalarına işaret eder; kapsam notu: [docs/README.md](docs/README.md).
- Verisi bu depoda olmayan kalemler açıkça **`CALISTIRILMADI`** basılır ve hükme
  sayılmaz: bugün yalnız **OLG-1** (özel ağacın commit zinciri ve canlı kanıt
  seti). `PASS` da `KOSULLU` da yazılmaz; kimlik açık listededir ve gerekçe her
  satırda yazılıdır. Model kalemleri sabit katalogla koşar; katalog yoksa onlar da
  `CALISTIRILMADI` olur. Ayrıntı: [docs/README.md](docs/README.md).

---

## Lisans

MIT — bkz. [LICENSE](LICENSE). Akademik hat ve araçlar bu lisansla kullanılabilir;
laboratuvarın ürettiği makaleler bu deponun parçası değildir.

**Sahip:** Ali Han Kaya
