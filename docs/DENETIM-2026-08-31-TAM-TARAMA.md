# TAM TARAMA — 18 betiğin bağımsız adversaryal denetimi — 2026-08-31

Yöntem: her betik grubu, **kodu görmemiş** ayrı bir alt ajana verildi; ajanlara yazarın
gerekçeleri söylenmedi, "koda bak" dendi, zorunlu ÖLÇEMEDİKLERİM istendi. Ajan bulguları
**birincil kayıtta** (gerçek lab, gerçek `ORTAK/`) tek tek doğrulandı. Doğrulanamayanlar
`BEYAN` olarak işaretlendi; çürüyenler reddedildi.

Kapsam: 18 betik. Ajanlar 4 grupta koştu. **Bu belge bulguları kaydeder, düzeltmez.**
Düzeltme ayrı ve tek mekanizmalı commit'lerle yapılacaktır.

---

## A. YAPISAL BULGU — en ağırı

**A-1 [P0, ÖLÇÜLDÜ] · Üç makale kapısı hiçbir şey tarafından çağrılmıyor.**

```
grep -oE '\$BETIKLER/[a-z_]+\.(py|sh)' check_integrity.sh | sort -u
→ fix_reconcile · provenance_check · source_class_check · teslim_imza · translit_check · verify_doi
```
18 betikten **6'sı** zincirde. Ajan promptları (`.opencode/`) da tarandı; oradan çağrılanlar
düşüldükten sonra geriye **hiçbir yerden çağrılmayan** üç makale kapısı kalıyor:

| Betik | Ne denetler | Öz-test | Zincir | Ajan promptu |
|---|---|---|---|---|
| `cite_match.py` | atıf ↔ kaynakça %100 eşleşme (CITE-01/02/03) | **8 test var** | YOK | YOK |
| `quote_ratio.py` | alıntı oranı / intihal yakınlığı | **HİÇ TEST YOK** | YOK | YOK |
| `declaration_check.py` | yapay zekâ + etik beyanları (ICMJE) | **HİÇ TEST YOK** | YOK | YOK |

Yani makalenin atıfları kaynakçayla eşleşiyor mu, alıntı oranı nedir, yapay zekâ beyanı var mı —
**hiçbiri gerçek işte ölçülmüyor.** `cite_match` için sekiz regresyon testi yazılmış ama betik
hiç koşmuyor: test edilen ama kullanılmayan kapı.

**Belge çelişkisi (I4 gereği arandı, gerekçe BULUNAMADI):**
`ATLAS_SABLONLAR/docs/PIPELINE.md:75` — *"`check_integrity.sh` … alt denetimleri **zincirler**"*
ve aynı tabloda `cite_match.py` bir denetim betiği olarak listeleniyor. Disk bunu yalanlıyor.
Bu bir tasarım kararı değil, **belge–disk sapmasıdır**.

**A-2 [P1, ÖLÇÜLDÜ] · `PIPELINE.md` bayat.** Tablo 18 betiğin **8'ini** listeliyor; öz-test için
*"34 testlik regresyon paketi … 34/34 beklenir"* diyor. Gerçek: **103 test**.

**Adil olma notu — reddedilen aday bulgular:** `scope_profile_check.py` zincirde yok ama
`atlas-faz0.md:11` ve `atlas-scoper.md:91` onu açıkça çağırıyor → yetim DEĞİL.
`gate_merge.py` artefakt **üretir**, `--gate` onun çıktısını doğrular → tasarım gereği.
`oztest_attest.py` zincire bilerek bağlanmadı (özyineleme; belgeli).
`budget_guard`/`apply_routing`/`check_models` koşu-öncesi planlama katmanıdır.

---

## B. KARAR KATMANI — gate_merge · provenance_check · fix_reconcile

| # | Bulgu | Seviye | Durum |
|---|---|---|---|
| B-1 | `gate_merge` etik dalı şiddeti okumuyor: `id="PENDING_ETHICS"` olan bir bulgu `priority="P0"` olsa da sayılmıyor → **P0 aklama** | P0 | BEYAN (ajan `ortak_gate` vekiliyle ölçtü; gerçek `ORTAK/` ile tekrar edilmeli) |
| B-2 | `manifest_reconciliation` liste yerine **sözlük** olursa iki katman da sessizce atlıyor; sıfır uygulanmış düzeltmeyle `--full` geçiyor | P0 | BEYAN |
| B-3 | `fix_reconcile`: `g2b` `null` ise **REC-05 çıktıdan tamamen kayboluyor** (ne FAIL ne NOT) — bilinen `null` örüntüsü | P0 | BEYAN |
| B-4 | `provenance_check` CHK-02 alt-dize: `"covered" in durum` → **`NOT COVERED` kabul ediliyor** | P0 | **ÖLÇÜLDÜ** — `provenance_check.py:110` |
| B-5 | CHK-02 PROVENANCE tablosunu **başlıkla sınırlamıyor**: MASTER'da "PROVENANCE" kelimesi hiç geçmese de PASS | P0 | BEYAN |
| B-6 | CHK-01 tüm başlıkları tek dizeye yapıştırıp alt-dize arıyor; tek olumsuz başlık 8 ID'yi birden karşılıyor | P0 | BEYAN |
| B-7 | `gate_merge.imza()` tanımlı ama **hiçbir yerden çağrılmıyor** → docstring'in "IDENTICAL_GATE_INPUTS bu P0'dır" kuralı **uygulanmamış** | P0 | **ÖLÇÜLDÜ** — `grep -n imza gate_merge.py` → yalnız 166/167 |
| B-8 | VACUOUS TEST: FR-6 yalnız `"REC-05" in o` diyor; kural silinse satır `PASS REC-05` olur ve test yeşil kalır | P1 | BEYAN |
| B-9 | CHK-05 için **hiç test yok**; `grep "CHK-05" atlas_selftest.py` boş | P1 | **ÖLÇÜLDÜ** |
| B-10 | `int(metadata.p0_count)` tip denetimsiz → 6/8 varyantta traceback ("temiz FAIL" kuralı ihlali) | P1 | BEYAN |
| B-11 | VACUOUS PASS: bloklamayan tek bir P2 bulgu "denetim kanıtı" sayılıyor; `checks_calisan=0` iken FINAL PASS | P1 | BEYAN |

### 31.08 05:48 CEST — B-1/B-2/B-3 YENİDEN ÖLÇÜM DÜZELTME NOTU

Yukarıdaki tarihsel `BEYAN` satırları I6 gereği silinmedi. Gerçek `ORTAK/` ve tam ATLAS
fikstürüyle tekrar ölçüm sonuçları:

| Bulgu | Düzeltme öncesi ham sonuç | Karar / commit | Düzeltme sonrası ham sonuç |
|---|---|---|---|
| B-1 | `B-1 rc=0 FINAL PASS-PENDING-ETHICS 2A=PASS(P0:0,P1:0) 2B=PASS(P0:0,P1:0) -> PASS-PENDING-ETHICS` | **DOĞRULANDI / KAPATILDI** · `b11ed8f` | `B-1 rc=1 FINAL FAIL 2A=PASS(P0:0,P1:0) 2B=FAIL(P0:1,P1:0) METADATA_MISMATCH -> FAIL` |
| B-2 | `B-2-FULL rc=0 FULL PASS v5.5.4 — tum fazlar + sayi/ID mutabakati + gate + devir dogrulandi` | **DOĞRULANDI / KAPATILDI** · `019b7c3` | `B-2 merge_rc=1 full_rc=1 FINAL FAIL 2A=PASS(P0:0,P1:0) 2B=FAIL(P0:1,P1:0) METADATA_MISMATCH -> FAIL` |
| B-3 | `B-3 rc=0 REC-05-var=False FIX-RECONCILE PASS — 2 bulgu / 2 FIX / 2 MASTER kaniti mutabik` | **DOĞRULANDI / KAPATILDI** · `ee6c660` | `B-3 rc=1 REC-05-var=True FIX-RECONCILE FAIL — 1 mutabakat ihlali` |

Ek commit denetimi bulgusu: `teslim_imza.py`, hash değeri `null`, `0`, `false` veya `{}`
olduğunda traceback üretiyordu. `067af4e` ile hash biçimi dosya erişiminden önce doğrulandı;
son bozuk-girdi matrisi `TESLIM_MATRIKS vaka=18 kapandi=18 traceback=0` verdi.

---

## C. AKADEMİK DÜRÜSTLÜK KATMANI — cite_match · quote_ratio · source_class · translit

| # | Bulgu | Seviye | Durum |
|---|---|---|---|
| C-1 | `cite_match` `ad[0].isupper()` filtresi `al-`, `ʿ`, `ʾ` önekli adları siliyor — İslam/Yahudi çalışmalarının **standart ad biçimi**; uydurma atıflar görünmez | P0 | BEYAN (gerçek betikle ölçüldü) |
| C-2 | `quote_ratio`: tırnaksız birebir aktarım = 0 span → oran %0.0 → PASS. İntihal yakınlığı ölçüsünün tam da ölçmesi gereken hâl | P0 | BEYAN |
| C-3 | `quote_ratio` QR-02 üçlüsü sahte doluyor: sayfa numarası **alıntının kendi içinde** aranıyor, atıf 400 karakterlik pencerede alakasız olabiliyor | P0 | BEYAN |
| C-4 | `source_class_check`: tablo ortasındaki **tek boş satır** `break` ile taramayı bitiriyor; sonraki ihlaller görünmez | P0 | BEYAN |
| C-5 | `translit_check` `SISTEMLER` listesinde **çıplak `DIN`, `ALA`, `ISO`** var ve eşleşme alt-dize → karşılaştırmalı **din** laboratuvarında "din" kelimesi sistem ilanı sayılıyor | P0 | **ÖLÇÜLDÜ** — `translit_check.py:68,74` |
| C-6 | `translit_check` hiçbir terim bulunamazsa `CALISTIRILMADI` yazıp aynı çıktıda **"PASS — TR-02 tutarli"** diyor: ölçülmeyen şey olumlanıyor | P0 | BEYAN |
| C-7 | TR-02 deseni docstring'in **kendi örneğini** (`sakīna`, makronlu) yakalamıyor | P0 | BEYAN |
| C-8 | `quote_ratio` çakışan span'ları topluyor → **%193.3** gibi aritmetik olarak imkânsız oran | P1 | BEYAN |
| C-9 | Eşik regex'i `(\d+)\s*%`; Türkçe yazım **`%15` hiç eşleşmiyor** — docstring'in kendi örneği tespit edilemiyor | P1 | BEYAN |
| C-10 | Eşik aşılsa bile `exit 0` ve son satır yine "PASS" | P1 | BEYAN |
| C-11 | VACUOUS: SRC-02, TR-02, TR-01 sistem-adı dalı, CITE-03, QR-02 **tamamen silinse** 12 testin 12'si yeşil kalıyor | P1 | BEYAN (ajan mutasyon matrisi) |

---

## D. PARA VE MODEL KATMANI — budget_guard · apply_routing · check_models

| # | Bulgu | Seviye | Durum |
|---|---|---|---|
| D-1 | Bozuk DB `"KISMI:"` döndürür; fail-closed dalı yalnız `"OLCULMEDI"` arar → **kapı $0.00 ile AÇILIR** | P0 | BEYAN |
| D-2 | Varsayılan (`--kuresel`siz) çağrı `os.getcwd()` alt-dizgisiyle filtreler; **proje yeniden adlandırılırsa harcama $0.00** görünür ve kapı açılır | P0 | BEYAN |
| D-3 | `apply_routing._aile()` yolun 2. parçasını alır; `openrouter/anthropic/claude-opus-5` ile `opencode-go/claude-opus-5` **aynı model** olduğu hâlde "2-of-2 bağımsızlık" kapısını geçiyor | P1 | BEYAN |
| D-4 | Fiyat bloğu olmayan model **$0.000** fiyatlanıyor ve uydurma bir "%29 düşüş" raporlanıyor | P1 | BEYAN |
| D-5 | `check_models` symlink ajan dosyalarını atlıyor → `sayim=0` iken **"0 ajan dosyasinin tamami gecerli"** PASS | P1 | BEYAN |
| D-6 | `check_models` `ATLAS_MODEL_KATALOG` desteklemiyor → hermetik değil; öz-testin kendi ilkesini çiğniyor | P1 | BEYAN |
| D-7 | **14/18 mutasyon hayatta kaldı.** `gercek_harcama` gövdesi tamamen silinse BG-1..BG-4 dördü de yeşil | P1 | BEYAN (ajan mutasyon matrisi) |

---

## E. BEYAN KATMANI — declaration_check · scope_profile_check · prompt_lint · verify_doi

| # | Bulgu | Seviye | Durum |
|---|---|---|---|
| E-1 | `declaration_check` alt-dize eşleşmesi: **hiç beyan içermeyen** bir makale 6/6 PASS alıyor (`"credit"` ← "Accreditation", `"yapay zeka"` ← "Yapay Zeka Tarihi") | P0 | BEYAN |
| E-2 | Başlıklar **kod bloğu içinden** de toplanıyor → doldurulmamış şablon tam not alıyor | P0 | BEYAN |
| E-3 | `verify_doi` **NFD kaçışı**: macOS normalizasyonuyla yazılmış `[DOĞRULANMADI]` hiçbir kalıba takılmıyor → aynı metin PASS/FAIL ayrımı yapıyor | P0 | BEYAN |
| E-4 | Muafiyet bölgesi başlık seviyesine kapanıyor: **H1 seviyesinde** bir `# §8 … (M1)` başlığı belgenin geri kalanının tamamını muaf yapıyor | P0 | BEYAN |
| E-5 | `prompt_lint`: `disable: true` satırı dosyanın **herhangi bir yerinde** (kod bloğu içinde bile) tüm kuralları atlatıyor | P0 | BEYAN |
| E-6 | `prompt_lint` sağlam symlink prompt dosyalarını hiç denetlemiyor → **0 dosya denetlenip PASS** | P0 | BEYAN |
| E-7 | `scope_profile_check` tablo kolonlarını **konumsal** okuyor; kolon sırası değişince SP-02 tamamen ölüyor ama yine "22 zorunlu ID" deyip PASS veriyor | P0 | BEYAN |
| E-8 | **VD-1 bir deliği çiviliyor:** "MASTER yok → exit 0" fail-open'ı düzeltilirse VD-1 kırmızı yanıyor. Test, kusuru koruyor | P1 | BEYAN |
| E-9 | CrossRef DOI doğrulamasının **tamamı** silinse 15/15 test yeşil kalıyor | P1 | BEYAN |
| E-10 | PL-13 kalıbı **kendi docstring'inin** kusur olarak alıntıladığı dizgeyi tutmuyor; PL-11'in bir alternatifi U+0307 içeren **bozuk dizge** (ölü kod) | P1 | BEYAN |

---

## OLCULMEYEN

1. **B, C, D, E bölümlerindeki `BEYAN` işaretli bulguların çoğu alt ajan ölçümüdür ve gerçek
   labda tekrarlanmamıştır.** Ajanlar eksik ağaçta koştu: `ORTAK/scripts/ortak_gate.py`,
   `routing.profiles.json`, model kataloğu, `.opencode/` prompt korpusu **yüklenmemişti**.
   Özellikle **B-1 ve B-2** `ortak_gate` vekiliyle ölçüldü — gerçek `ORTAK/` ile tekrar şart.
2. Hiçbir bulgu bu turda **düzeltilmedi**. Bu belge kayıttır, çözüm değildir.
3. Ajanların P2 bulguları (traceback'ler, ölü kod, docstring sapmaları) buraya alınmadı;
   ajan raporlarında duruyor ama lab kaydına girmedi — **kayıp risk**.
4. Hiçbir ölçüm **gerçek makale** üzerinde yapılmadı; hepsi sentetik fikstür.
5. `check_integrity.sh`'in `--faz0/--faz1/--faz2` dalları ayrıca denetlenmedi.
6. Tam öz-test lab kökünde koşturulamıyor (`prompt_lint` bağlı diskte asılıyor).

## KIRMIZI ÇİZGİLER

`DENEME/`, `DIVINELOVE`, `gpt-mideo-kopyası`, MIDÉO içeriği — okunmadı, değiştirilmedi.
Bu tur **salt okunurdur**: hiçbir betik değiştirilmedi, yalnız bu kayıt ve DERSLER yazıldı.

## SIRADAKİ GÖREV — öncelik sırası

1. **A-1** — `cite_match`, `quote_ratio`, `declaration_check` zincire bağlansın (veya PIPELINE.md
   düzeltilsin ve dışarıda bırakılma gerekçesi yazılsın). Bağlamadan önce C-1..C-3 ve E-1/E-2
   düzeltilmeli, yoksa zincire **vacuous kapı** eklenmiş olur.
2. **B-1, B-2, B-3** — gerçek `ORTAK/` ile tekrar ölç, doğrulanırsa kapat. Karar katmanı en kritik.
3. **C-5, B-4** — alt-dize kaçakları (tek satırlık düzeltmeler, ölçülmüş).
4. **B-7** — `imza()` çağrılsın veya docstring iddiası kaldırılsın.
5. **A-2** — `PIPELINE.md` gerçekle hizalansın (18 betik, 103 test).

---

## 31.08 06:12 CEST — `OLCULMEYEN` YENİDEN ÖLÇÜM NOTU

Tarihsel `BEYAN` ve `OLCULMEYEN` satırları I6 gereği silinmedi. Bu not gerçek lab,
gerçek `ORTAK/`, gerçek routing/prompt korpusu ve yalnız `/tmp` saldırı fikstürleriyle
alınan ikinci ölçümü kaydeder. Bu tur kod düzeltmesi yapmaz; doğrulanan kusurlar ayrı
tek-mekanizmalı işlere kalır.

| Grup | Sonuç | Ham ölçüm özeti |
|---|---|---|
| B-4..B-7 | **DOĞRULANDI** | B-4/5/6 provenance exit 0; B-7 özdeş kapılar `FINAL PASS`, exit 0 |
| B-8/B-9 | **DOĞRULANDI** | REC-05 mutasyonunda `PASS REC-05` dizgisi FR-6 koşulunu doyurdu; öz-test kaynağında `CHK-05` geçişi `0` |
| B-10 | **KISMEN DÜZELTİLDİ** | Tarihsel `6/8 traceback` yerine seçilen sekizli matriste `4/8 traceback`; `null` ve `false` metadata sessiz kabul |
| B-11 | **DAVRANIŞ DOĞRULANDI / KUSUR RED** | yalnız P2 bulgulu, `checks_calisan=0` iki kapı `FINAL PASS`; belgeli tasarım bulguyu denetim izi sayıyor |
| C-1/C-3..C-9 | **DOĞRULANDI** | al-Ṭabarī görünmedi; sahte QR-02 geçti; SRC boş satır sonrası durdu; DIN alt-dizesi; sakīna görünmedi; `%188.7`; `%15` okunmadı |
| C-2/C-10 | **DAVRANIŞ DOĞRULANDI / KUSUR RED** | tırnaksız metin `0 span`; eşik aşımı `%79.2 > %1` UYARI + exit 0. İkisi de yazılı kapsam/tasarım ile uyumlu |
| C-11 | **DOĞRULANDI** | SRC-02/TR-02/TR-01 sistem-adı/CITE-03/QR-02 etkisiz arşiv: `OZ-TEST: 108/108 gecti` |
| D-1..D-7 | **DOĞRULANDI** | `KISMI` ve ad değişimi bütçeyi açtı; aynı model bağımsız sayıldı; eksik fiyat `%35 düşüş`; 0 symlink sayımı PASS; env katalog yok; bütçe gövdesiz arşiv `108/108` |
| E-1..E-7 | **DOĞRULANDI** | alt-dize beyan, kod bloğu başlığı, NFD, H1 muafiyeti, gövde disable, symlink 0 PASS, kolon sırası kaçışı exit 0 |
| E-8 | **MUTASYON DOĞRU / KUSUR RED** | varsayılan MASTER-yok fail yapılınca `107/108`, yalnız VD-1 düştü; erken-faz gerekçesi ve `--require-master` post-FAZ3 yolu belgeli |
| E-9 | **DOĞRULANDI** | CrossRef döngüsü etkisizleştirilmiş arşiv `108/108` |
| E-10 | **KISMİ** | `Etiketlerini birakma` PL-13 ile exit 1: bu yarı çürüdü. Normal `daima PASS` PL-11’den kaçıp exit 0: bu yarı doğrulandı |
| Faz dalları | **DOĞRULANDI** | `--faz0/1/2` sağlam exit 0; SC-/CHK-/FIX- kesilmiş kopyalar exit 1 |
| Ayrı kapılar | **KARAR DOĞRULANDI** | aynı fikstür: `--full` exit 0, `--mutabakat` exit 1, `--teslim` exit 1 |
| HMAC sınırı | **ÖLÇÜLDÜ** | K1 PASS; K2 TSL-04 exit 1; anahtarsız TSL-05 P1/DOGRULANMADI exit 0 |
| Gerçek artefakt | **HEDEF YOK** | kırmızı çizgi dışı `find` hiçbir MASTER/SCOPE/FAZ/manifest döndürmedi |
| KOD dış koşu | **ÖLÇÜLDÜ / YEŞİL DEĞİL** | gerçek HOME: `KOD OZ-TEST: 157/164`; 7 düşüş, bu turda değiştirilmedi |

### Kalan gerçek `OLCULMEYEN`

1. Bağlı ikinci fiziksel makine yoktur; çapraz-makine N=1 kaldı.
2. Gerçek makale/teslim artefaktı kırmızı çizgi dışındaki labda yoktur; MIDÉO,
   `DENEME/`, DIVINELOVE ve gpt-mideo-kopyası okunmadı.
3. İlk alt ajanların rapora alınmayan P2 listesi diskte bulunamadı; kayıp konuşma çıktısı
   birincil kayıt sayılmadı ve yeniden uydurulmadı.
4. HMAC dış güven sınırı iki yerel anahtar alanıyla ölçüldü; bağımsız kurum/başka fiziksel
   makinede gerçek sır paylaşım süreci çalıştırılmadı.
