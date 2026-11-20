## ATLAS Research Lab — in brief

[![dogrula](https://github.com/ali-han-kaya/atlas-research-lab/actions/workflows/dogrula.yml/badge.svg)](https://github.com/ali-han-kaya/atlas-research-lab/actions/workflows/dogrula.yml)

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
- **How claims are verified.** `make dogrula` (hygiene, syntax, secret scan, secret-gate
self-test, three self-test suites), `make mutasyon` (seventy-seven gate rules, exercised by
61 battery cases: clean baseline + one violation + a red verdict), and `tools/yayinla.py`
(publish parity: 0 new / 0 changed / 0 deleted). The same commands run in CI on GitHub Actions.
`make iddia` closes the remaining gap: it re-measures the numbers printed in this README.
- **Reproduce it.** `./demo` prints the frozen 8-vs-2 failure with a **red verdict and
exit code 1** (fixture drift: 2; consistent fixture: 0). `make demo` is only a thin
wrapper and cannot carry 1 vs 2, because GNU make always exits 2 on a failing recipe. `make dogrula` → **8 pass / 0 fail / 0 not run** (T1, `OLG-1`, now
runs against this tree's `attestation.json`); KOD self-test
**174/174**; mutation battery **61/61 cases red + 17/17 expected findings** over 77 rules. Mutation-tested vs untested gate rules are measured
in [`docs/MUTASYON_KAPSAM.md`](docs/MUTASYON_KAPSAM.md); dependent-package findings in
[`docs/GUVENLIK.md`](docs/GUVENLIK.md); CI green. Non-Turkish readers:
[`docs/EN/QUICKSTART.md`](docs/EN/QUICKSTART.md).

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
python3 -m pip install -r requirements-dev.txt   # sürümler sabit: requests + pip-audit
make kur       # commit/push korumasını bu klonda etkinleştirir
make dogrula
./demo         # beklenen: rc=1 (kırmızı)
```

`make dogrula` tek giriştir; **sekiz kalemi** sırayla koşar ve **ham çıktılarını** yazar:
depo hijyeni, Python sözdizimi, kabuk sözdizimi, sır taraması, sır kapısı öz-testi ve üç
öz-test paketi (ATLAS · KOD · Toolkit). Sayıları README'ye elle yazmayız — betikler
kendileri basar. Model çağrısı yoktur: yerel batarya **$0**. İngilizce hızlı başlangıç:
[`docs/EN/QUICKSTART.md`](docs/EN/QUICKSTART.md).

### `./demo` — tek komutla kırmızı hüküm

`DENEME/` 23 Ağustos 2026'da dondurulmuş, bilerek kusurlu bir koşudur: manifesto 8 FIX'i
"UYGULANMIŞ" ilan etti, MASTER'a yalnız 2'si yansıdı, o günün FINAL GATE'i yine de PASS
dedi. Komut fikstürü olduğu gibi okur, bugünkü mutabakat kapısını (`fix_reconcile`) koşar
ve **kırmızı** döner:

```text
DEMO — DENEME/ dondurulmus kusurlu kosu (v5.5.2, 23 Agustos 2026)
kaynak: DENEME/ — bilerek duzeltilmedi; regresyon fiksturu.

  manifesto iddiasi : 8 FIX "UYGULANMIS"
  MASTER'da gorunen : 2 FIX
  dondurulmus kapi  : PASS  (DENEME/gate/FINAL-GATE-v5.5.json)

  bugunku mutabakat : FAIL  (fix_reconcile, rc=1)

  PASS REC-01: FAZ1 8 bulgu == FAZ2 8 FIX
  PASS REC-02: oncelik dagilimi ayni {'P0': 3, 'P1': 5}
  PASS REC-03: 8 bulgunun tamami FAZ2'de atifli
  PASS REC-06: MASTER'daki 2 FIX-ID manifestoda tanimli
  FAIL REC-04: 6/8 'UYGULANMIS' FIX MASTER'da yok: ['FIX-003', 'FIX-004', 'FIX-005', 'FIX-006', 'FIX-007', 'FIX-008']
  FAIL REC-05: gate 2B '6' FIX'i KANITLI ilan etti ama MASTER'da yok: ['FIX-003', 'FIX-004', 'FIX-005', 'FIX-006', 'FIX-007', 'FIX-008']

HUKUM: FAIL — iddia 8, kanit 2; dondurulmus kapi PASS dedi.
BEKLENEN KIRMIZI — bu komut bilerek rc=1 doner.
```

Kanonik komut kökteki `./demo`'dur; kabuk çıkış kodu doğrudan `tools/demo.py`'den gelir
(bu turda `echo $?` ile ölçüldü):

| Durum | Kod |
|---|---|
| Kırmızı — iddia > kanıt, dondurulmuş kapi PASS | **1** |
| Fikstür bozuk — dosya yok/bozuk, kapi PASS değil, beklenen çelişki yok | **2** |
| Yeşil — iddia == kanıt ve mutabakat PASS | **0** |

`make demo` yalnız bunun ince bir sarmalayıcısıdır ve GNU make tarif hatasını her zaman
**2** ile bildirdiği için 1/2 ayrımını **taşımaz**. Kod ayrımı gerekiyorsa `./demo`
(veya `python3 tools/demo.py`) koşulur; README hiçbir yerde make için "1 döner" demez.
Kırmızı, bozulmuş bir testten değil iddia/kanıt farkından gelir; fikstür kayarsa demo
`FIKSTUR DEGISTI` yazar ve 2 döner.

### Ölçülen süreler

| Komut | Süre | Ölçüm |
|---|---|---|
| `make dogrula` | 52 s | macOS 27.2 · arm64 · Python 3.9.6 · 2026-11-19 |
| `make mutasyon` | 66 s | aynı makine ve oturum |
| `./demo` | < 1 s | aynı makine ve oturum |

CI süreleri runner'a bağlıdır; burada iddia edilmez, iş akışı kaydı esastır.

Paketleri ayrı ayrı koşmak istersen (yollar depo köküne görelidir):

```bash
python3 ATLAS_SABLONLAR/scripts/atlas_selftest.py        # OLG-1 → 145/145 (attestation)
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

Sabit allowlist'in models.dev'de hâlâ geçerli olup olmadığını ölçmek için
`make katalog-kontrol` vardır. Ağ gerektirir ve **CI'da koşmaz**; eksik model
adıyla `rc=1`, ağ/JSON okunamazsa `rc=2` döner. Kanonik kod ayrımı için
`python3 tools/katalog_kontrol.py` kullanılır; GNU make, tarif hatasını 2'ye
çevirir.

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
| Tek giriş doğrulama | `make dogrula` → `tools/dogrula.py` (sekiz kalem, fail-closed) |
| Kırmızı hüküm demosu | `./demo` → `tools/demo.py` (kanonik; beklenen `rc=1`, fikstür bozuksa `rc=2`, yeşilde `rc=0`) |
| Mutasyon kapsamı | `make kapsam` → `docs/MUTASYON_KAPSAM.md` güncel mi (üretilmiş tablo) |
| Katalog tazeliği (isteğe bağlı) | `make katalog-kontrol` → models.dev canlı kataloğu; ağ gerekir, CI'da koşmaz |
| İddia defteri | `make iddia` → README/docs sayısal iddialarını üreten komutla ve ham kanıt satırıyla yeniden ölçer; tutmayan satır `IDD-*` ile kırmızı |
| Ham kanıt yenileme | `make iddia-yaz` → bilinçli değişiklikten sonra `tools/iddia_olcum.json` anlık görüntüsünü yeniler |
| Bağımlılık denetimi | `make guvenlik` → `pip-audit`; her bulgu `docs/GUVENLIK.md` içinde adıyla |
| Commit/push koruması | `make kur` → `core.hooksPath=.githooks`; canlı DSN commit edilemez |
| Runner doğrulaması | `make dogrula-ci` — yalnız o ortamda ölçülebilen kalemler hükme girer, öz-testler rapor |
| Sürekli doğrulama | `.github/workflows/dogrula.yml` — her push/PR ve haftalık |
| Özel ağaçtan aktarım | `tools/yayinla.py --lab <yol>` (kuru koşu) · `--uygula` (yazar) |

`tools/yayinla.py` yalnız **açık listedeki** mekanizma yollarını taşır; liste dışına
çıkmaz, hedefte liste dışı dosya bırakmaz ve yazmadan önce sır taraması yapar —
bulgu varsa hiçbir şey yazmaz.

## İddia defteri

Bu README'deki sayısal ölçümler `tools/iddia_defteri.json` içinde tek tek satırdır:
iddia metni, geçtiği dosya ve **birebir cümle**, onu üreten komut ve son ölçülen
değer. Son ölçümün **ham çıktı satırı** `tools/iddia_olcum.json` içinde aynı
`IDD-*` anahtarıyla durur; `make iddia` bu satırın güncel çıktıda birebir aynı
olmasını, kendi desenine uymasını ve beyanla aynı değeri vermesini ister. Kanıt
bayatsa veya bozulursa satır kırmızıdır; `make iddia-yaz` anlık görüntüyü yeniler.

`make iddia` her satırı yeniden koşar; beyan ile ölçüm tutmazsa satırı
kimliğiyle (`IDD-07`) kırmızı basar ve `rc=1` döner. Alıntısı dosyasında birebir
bulunmayan bir satır defteri bozuk sayar (`rc=2`): iddia metni uydurulamaz.

Üç durum yeşile zorlanmaz, ayrı sayılır: `AG_GEREKLI` (ağ ister; varsayılan koşuda
atlanır), `BEYAN` (tarihli/makineye bağlı kayıt) ve `OLCULMEDI` (bu ağaçta yeniden
üretilemez; gerekçesi satırda yazılı). Bu üç durumun ham kanıtı yoktur ve çıktıda
`ham kanit yok (...)` olarak ayrıca işaretlenir; hiçbiri PASS sayılmaz. Defter
`make dogrula` hükmüne girmez; 8/8 hükmü attestation ile ayrıca doğrulanır.

Defterin kapsamı üç public dokümandır: `README.md`, `docs/README.md`,
`docs/EN/QUICKSTART.md`. Tarihli `docs/OLCUM-*`, `SURUM.md` ve üretilmiş
`MUTASYON_KAPSAM.md` / `GUVENLIK.md` kapsam dışıdır; gerekçeleri defterin
`kapsam` bloğundadır. Allowlist'in canlı katalogda 9/9 geçerli olup olmadığı
`make iddia-ag` ile ölçülür; ağsız koşuda bu satır `AG_GEREKLI` sayılır ve kapıyı
kırmaz.

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
- Bu depoda standart `make dogrula` koşusunda **`CALISTIRILMADI` kalem yoktur**:
  `OLG-1` bu ağacın kendi `attestation.json` kanıtıyla koşar. `attestation.json`
  yoksa `OLG-1` tarihsel commit denetiminde **FAIL** olur; bozuksa
  `KANIT_GECERSIZ` olur; ikisi de `CALISTIRILMADI` olarak gizlenmez. Model
  kalemleri sabit katalogla koşar; katalog yoksa onlar `CALISTIRILMADI` olur.
  Ayrıntı: [docs/README.md](docs/README.md).

---

## OLG-1 ve ağaç kanıtı

`T1` (`OLG-1`) artık özel ağacın commit zincirini aramaz: `olgu_lint`, bu depodaki
`attestation.json`'ı `make kanit-dogrula` ile doğrular ve gerçek commit/tree
kanıtını kullanır. Tarihsel `docs/OLGULAR.md` kayıtları silinmedi; public ağaçta
makine kanıtı sayılmaz. `OLGU-06` iki gerçek DERSLER satırıyla kapatıldı. Sahte
commit çıpası yoktur; `make dogrula` bu depoda **8/8** verir ve T1 PASS'tir.
Attestation yoksa/bozuksa OLG-1 FAIL olur. Koşu çıktısı T1 satırında çıpayı
görünür basar — `OZ-TEST: 145/145 gecti · KANIT commit=<sha> tree=<sha>` —
yani PASS, doğrulanan ağacın kanıtıyla birlikte okunur; kanıt satırı stderr
uyarısı değildir. T1 herhangi bir nedenle koşmazsa satır
`KABUL EDİLEN BORÇ: T1 koşmuyor — <sebep>` olur ve hüküm `PASS 7/8` diye
yazılır; 8/8 denmez. Ayrıntı ve negatif kontrol:
[docs/README.md](docs/README.md).

## Mutasyon kapsamı

`make mutasyon` yetmiş sekiz vakanın gerçekten ateşlediğini kanıtlar; **her kuralın** durumu ise
[`docs/MUTASYON_KAPSAM.md`](docs/MUTASYON_KAPSAM.md) içinde tek tek yazılıdır. Tablo
`tools/kapsam.py` tarafından üretilir (elle yazılmaz) ve üç durum ayırır:

- **TEST EDİLDİ** — 77 kural (mutasyon vakası adıyla)
- **KAPSAM DIŞI** — 27 kural, her biri ölçülmüş bir gerekçeyle: ağ
  (`verify_doi`), gizli anahtar (`teslim_imza`), tarihçe (`olgu_lint`), koşu durumu
  (`api_surface`, `oztest_attest`), depo durumu (`dep_audit`), ölü kural kimliği
  (`secret_scan` SEC-04 hiçbir kod dalında basılmıyor)
- **BOŞLUK** — 18 kural: 10'u yalnız öz-testte anılıyor, 8'i hiçbir testte geçmiyor

Boşluk "kapsam dışı" diye etiketlenmez; gerekçesi yoksa boşluk olarak kalır ve tabloda
adıyla durur. `make kapsam` tablonun güncelliğini denetler; CI'da bu adım kırılırsa
tablo bayatlamış demektir.

## Lisans

MIT — bkz. [LICENSE](LICENSE). Akademik hat ve araçlar bu lisansla kullanılabilir;
laboratuvarın ürettiği makaleler bu deponun parçası değildir.

**Sahip:** Ali Han Kaya
