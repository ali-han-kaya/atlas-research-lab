# ATLAS Research Lab

**Kanıt disiplinli, çok ajanlı üretim laboratuvarı.** Akademik metin ve yazılım
üretimini "model şöyle dedi" üzerine değil, **teslimin kendi baytları üzerinde
koşan kapılar** üzerine kurar.

Bu depo laboratuvarın kendisidir: hatlar, ajanlar, şablonlar, kapı betikleri,
ölçüm bataryası ve öğrenim defteri. Laboratuvarın ürettiği makaleler ve kitapçıklar
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
| **Ölçüm** | `scripts/` | Mutasyon koşucusu, kapı farkı, bağımsızlık doğrulaması, enjeksiyon sayacı, kaynak/token ölçümü ve bunların tabanları. |
| **Kayıt** | `docs/` | Ölçüm koşuları, denetim raporları, ders defteri, kanonik olgu tablosu. |

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
scripts/           ölçüm bataryası ve tabanları
docs/              ölçümler, denetimler, ders defteri, olgu tablosu
tools/             bu deponun kendi araçları (doğrulama, yayın aktarımı)
```

---

## Otomasyon

| Ne | Nasıl |
|---|---|
| Tek giriş doğrulama | `make dogrula` → `tools/dogrula.py` (yedi kalem, fail-closed) |
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
- İki kalem ölçüm ortamına bağlıdır: ATLAS'ta **OLG-1** (özel ağacın commit
  zinciri), KOD'da **MOD-1/MOD-2** (yerel opencode model kataloğu). `make dogrula`
  bunları **`KOSULLU`** olarak basar, `PASS` olarak değil; kimlikler açık listededir
  ve gerekçe çıktıda yazılıdır. Ayrıntı: [docs/README.md](docs/README.md).

---

## Lisans

MIT — bkz. [LICENSE](LICENSE). Akademik hat ve araçlar bu lisansla kullanılabilir;
laboratuvarın ürettiği makaleler bu deponun parçası değildir.

**Sahip:** Ali Han Kaya
