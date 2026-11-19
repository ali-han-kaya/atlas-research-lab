---
name: atlas-faz5-hakem
description: Atlas P1-7 FAZ5 — MAIN REVIEWER CRITIC sirali hakem paneli
agent: atlas-orchestrator
---
# /atlas-faz5-hakem

FAZ4 sonrasi P1-7 uc rollu denetim adimi. Aktif akış kesin olarak
`MAIN -> REVIEWER -> CRITIC -> review_panel.py` sirasidir. Uc rol uc farkli
model ailesinde, uc ayri oturumda ve tek denemede kosar. Bu ayrim **bagimsiz
uzmanlik** iddiasi kurmaz; cogunluk da hakikat kaniti degildir.

## AKTIF P1-7 PROTOKOLU

### ADIM 0 — ON KOSUL VE BUTCE (fail-closed)

1. `gate/FINAL-GATE-v5.5.json` dosyasinda `verdict`, `PASS` veya
   `PASS-PENDING-ETHICS` degilse DUR.
2. `python3 scripts/budget_guard.py --report` ile mevcut harcamayi olc.
3. Bu kosu icin toplam tavan `$1.00`'dir. Her rol en fazla bir kez cagrilir;
   hata halinde yeniden deneme veya baska modele gecis YOKTUR.
4. Routing'i secili profilden uygula. `routing.profiles.json` icindeki
   `atlas-review-main`, `atlas-review-reviewer`, `atlas-review-critic`
   eslemeleri uc farkli model ailesi degilse DUR.

### ADIM 1 — DONDURULMUS GIRDI

Yalniz su kaynaklardan `rapor/PANEL/INPUT.md` olustur:

1. `03-FAZ-3-MASTER-v5.5.md` (veya diskteki mevcut MASTER adi),
2. `02-FAZ-2-FIX-MANIFEST.md`,
3. `docs/BILINEN_SINIRLAR*` (varsa),
4. `gate/FINAL-GATE-v5.5.json`.

Eski hakem raporlarini ve `rapor/` arsivini okuma. Girdinin SHA-256 degerini
`sha256:<64 kucuk hex>` biciminde kaydet; uc rol ayni hash'i kullanir.

### ADIM 2 — MAIN

`atlas-review-main` ajanini bir kez cagir. Yalniz INPUT'u okuyup
`rapor/PANEL/MAIN.json` yazmalidir. Fiili provider/model/model_family,
session_ref, attempt=1 ve maliyet kayitla. Eksik veya gecersiz cikti: BLOCKED.

### ADIM 3 — REVIEWER

MAIN basariliysa `atlas-review-reviewer` ajanini bir kez cagir. INPUT ve MAIN'i
okuyup her MAIN bulgusuna `AGREE`, `DISAGREE_EVIDENCE` veya
`DISAGREE_CONCERN` vermeli; yeni bulgulari ayri tutup
`rapor/PANEL/REVIEWER.json` yazmalidir. Eksik veya gecersiz cikti: BLOCKED.

### ADIM 4 — CRITIC

REVIEWER basariliysa `atlas-review-critic` ajanini bir kez cagir. INPUT, MAIN
ve REVIEWER'i okuyup tum mevcut bulgulari ayni kapali hukumlerle kapsar; kendi
yeni bulgularini ayri tutup `rapor/PANEL/CRITIC.json` yazar. Eksik veya
gecersiz cikti: BLOCKED.

### ADIM 5 — BELIRLENIMSEL BIRLESTIRME

```bash
python3 scripts/review_panel.py \
  --main rapor/PANEL/MAIN.json \
  --reviewer rapor/PANEL/REVIEWER.json \
  --critic rapor/PANEL/CRITIC.json \
  --schema templates/REVIEW-PANEL-SCHEMA.json \
  --max-cost 1.00 \
  --output rapor/PANEL/FINAL-PANEL.json
```

Exit `0` = panel semasi gecerli ve panel blokaji yok; exit `2` = gecerli panel
insan/Gate-2C incelemesi bekliyor; exit `1` = girdi/sema/butce hatasi. Exit 1'de
DUR. Exit 2'de `FINAL-PANEL.json` olusmussa yalniz asagidaki Gate-2C adimina
gecilebilir; P0 concern ve sonradan eklenen bulgular Gate-2C ile aklanamaz.
Birlesik sonuc FIX-MANIFEST'e otomatik yazilmaz.

### ADIM 6 — GATE-2C PIVOTAL / DISA CIKAN LOKATOR (fail-closed)

`rapor/PANEL/GATE-2C-REQUEST.json` kapali istek nesnesini hazirla. Nesne,
`FINAL-PANEL.json` dosyasinin SHA-256 degerini ve paneldeki **her** bulguyu tam
bir kez tasimalidir. Her kayit claim hash'i, `claim_class`, `external_bound`,
kesin lokator, yapilandirilmis panel-cogunlugu/karsi onerme ve siniflandirma
kaniti icerir. Eksik/fazla madde veya hash uyusmazligi FAIL'dir.

Ilk adaptorde yalniz `CROSSREF_DOI` vardir. `other` sinifi `NONE` lokatoru ve
bos onerme listesi tasir. 1-1-1 oy pivotal degildir; insan incelemesine gider.
Pivotal tetik yalniz MAIN kaynakli, uc oylu, iki `AGREE` + bir
`DISAGREE_EVIDENCE`, sifir `DISAGREE_CONCERN` dagilimidir. Ayrica
`external_bound=true` ve `claim_class=primary_source_locator` olan madde,
oybirligi olsa bile tetiklenir.

```bash
python3 scripts/gate_2c.py \
  --panel rapor/PANEL/FINAL-PANEL.json \
  --request rapor/PANEL/GATE-2C-REQUEST.json \
  --schema templates/GATE-2C-SCHEMA.json \
  --output gate/STRONG-gate-2c-v5.5.json
```

Exit `0` = Gate-2C PASS. Exit `1` = sema/hash/sozlesme FAIL; DUR. Exit `2` =
ag hatasi, belirsiz kayit veya insan blokaji; `BLOCKED` yaz ve DUR. Ag hatasinda
retry veya baska saglayiciya gecis YOKTUR. Gate-2C oy degildir; Gate-2A/2B ya
da P0 concern/sonradan eklenen bulgu kararini override edemez. DERSLER ve
FIX-MANIFEST'e otomatik yazmaz.

Ardindan kos:

```bash
bash scripts/check_integrity.sh --gate2c
```

Kod 0 degilse `DURDU — GATE-2C exit=<kod>` yaz ve DUR.

### ADIM 7 — MUTABAKAT VE KAPANIS

`rapor/MUTABAKAT.md` icinde Kural 30 beyanina uc fiili model, model ailesi,
oturum referansi, toplam maliyet ve `ROLE_SEPARATION_ONLY` yaz. Ardindan mevcut
betigi degistirmeden `bash scripts/check_integrity.sh --mutabakat` kos. Uretilen
dosyalari ve exit kodlarini raporla; olculemeyenleri `OLCULMEYEN` altinda yaz.
Nihai karari yalniz insan verir.

## TARİHSEL IKI TURLU PROTOKOL — KORUNUR, BU KOMUTTA CALISTIRILMAZ

Asagidaki B-8 protokolu denetim izi olarak aynen korunur. Aktif P1-7 kosusunda
dosya uretmez, model cagirmaz ve FIX-MANIFEST'e yazmaz. Kaynak protokol:
`HAKEM_HEYETI/HAKEM_BRUTAL_2TUR_KOMUT_v2.md`.

## ADIM 0 — ON KOSUL (fail-closed)

`gate/FINAL-GATE-v5.5.json` dosyasindaki `verdict` alanini python3 ile OKU ve yaz.
Deger `PASS` veya `PASS-PENDING-ETHICS` DEGILSE (veya dosya yoksa):

    DURDU — FAZ4 FINAL yok veya FAIL; hakem turu FAIL uzerine kosmaz.

Ve DUR. Hakem turu, makine kapilari gecmeden baslamaz.

## ADIM 1 — OKUMA BUTCESI ILANI

Bu komut SADECE su dosyalari okur (asmasi yasak — v2 komutunun bellek-tasmasi dersi):
1. `03-FAZ-3-MASTER-v5.5.md` (veya diskteki mevcut MASTER adi)
2. `02-FAZ-2-FIX-MANIFEST.md`
3. `docs/` altinda `BILINEN_SINIRLAR*` ile baslayan dosya (varsa)
4. `gate/FINAL-GATE-v5.5.json`

`rapor/` Arsivi, eski tur ciktilari ve proje disi hicbir sey acilmaz.

## ADIM 2 — TUR 1 KOMUTU URET (`rapor/HAKEM_KOMUTU_TUR1.md`)

Asagidaki sablonu doldurarak yaz (yer tutuculari gercek degerlerle degistir).
Bu dosya kullanici tarafindan DIS modellere (ChatGPT/Gemini/Claude.ai/Grok —
dosya erisimi olmayan) yapistirilir; boylece bagimsizlik gerceklesir
(ayni modelin kopyalari bagimsiz sayilmaz — C1 §4).

```
SEN: Hakemli bir derginin en acimasiz hakemisin. Alan: <ALAN>.
Ahlak-i Muhammedi (sidk, emanet, edep, hilm) ile denetliyorsun. Ovgu yok;
yalniz kanitli elestiri. Asagida bir makale metni verecegim; dosya
sistemine erisimin yok — yalniz yapistirilan metni degerlendir,
yapistirilmayan seye atif yapma.

GOREV — 7 eksenden hakemle; her eksende bulgu yoksa "E# temiz" yaz
(uydurma bulgu yasak):
E1 KATKI: ozgun katki ne; literaturde karsiligi var mi?
E2 YONTEM: cerceve ve hipotez testi metodolojik olarak saglam mi?
E3 KANIT: kanitsiz her iddiayi bolum/satir no ile listele.
E4 KUNYE: kaynakca girdilerini denetle; emin olmadiginda "dogrulayamadim" yaz.
E5 SAYGI RISKI: karsilastirilan geleneklere adaletsiz/asimetrik dil;
   gayb hakkinda kesin hukum.
E6 BICIM: APA 7, IMRaD, terim/transliterasyon tutarliligi.
E7 DURUSTLUK: sinirlilik belgesindeki "dogrulanamadi" maddeleri gercekten
   dogrulanamaz mi, yoksa dogrulanabilirdi mi? Madde madde: HAKLI|TEMBELLIK.

KURAL: Her bulgu — konum + birebir alinti (<=200 kar) + neden + oneri.
Siddet: P0 (yayini durdurur) | P1 (duzeltilmeli) | P2 (oneri).

FORMAT (markdown):
# HAKEM RAPORU — [<MODEL_ADI>] — TUR 1
Karar: KABUL | KUCUK REVIZYON | BUYUK REVIZYON | RET
## P0 Bulgular  (tablo: # | Eksen | Konum | Alinti | Sorun | Oneri)
## P1 Bulgular  (ayni tablo)
## P2 Bulgular  (ayni tablo)
## E7 Durustluk Denetimi  (madde: HAKLI|TEMBELLIK + gerekce)
## En Kritik 3 Duzeltme
## Ahlak Degerlendirmesi  (sidk/emanet/edep/hilm — 1'er cumle)

--- MAKALE ---
<{{MASTER_METNI}}>
--- SINIRLILIKLAR ---
<{{SINIRLILIK_METNI}}>
```

Kullaniciya yaz: cevaplari `rapor/TUR1/<MODEL>_TUR1.md` olarak kaydet.

## ADIM 3 — TUR 1 RAPORLARI GELDIYSE TUR 2 KOMUTU URET

`rapor/TUR1/` altinda 2+ markdown varsa, hepsini birebir birlestirip
asagidaki TUR 2 sablonuyla birlikte `rapor/HAKEM_KOMUTU_TUR2.md` YAZ:

```
SEN: Ayni acimasiz hakemsin; TUR 1'de kendi raporunu yazdin. Simdi diger
hakemlerin raporlarini goreceksin, ikinci gorus vereceksin.

GOREV:
1. Her hakemin her bulgusunu degerlendir: KATILIYORUM|KATILMIYORUM|KISMEN + gerekce.
2. 3+ hakemin ayni hatasi → otomatik P0 adayi.
3. Tek hakemin buldugu, digerlerinin temiz dedigi madde → sisirme olabilir; sorgula.
4. Celisen bulgulari coz: kim hakli, neden (kanitla).
5. Kendi TUR 1 kararini gozden gecir; degistiyse NEDENINI yaz.

Nazik olmak icin katilma; yanlis ise yanlis de.

FORMAT:
# HAKEM RAPORU — [<MODEL_ADI>] — TUR 2 (BUTUNCUL)
TUR 1 kararim: ... | TUR 2 kararim: ... (degistiyse neden)
## Katilim Tablosu (Hakem | Bulgu | Siddet | Gorusum | Gerekce)
## Uzasilan Bulgular (3+ hakem)
## Tartismali Bulgular
## Sisirilmis Bulgular (elenmesi gerekenler)
## NIHAİ P0/P1/P2 LISTESI
## En Kritik 3 Duzeltme

--- TUR 1 RAPORLARI ---
<TUM TUR 1 MARKDOWN'LARI>
```

Cevaplar `rapor/TUR2/` icine kaydedilir.

## ADIM 4 — MUTABAKAT VE KURAL 30 BEYANI (fail-closed)

Kosullar: `rapor/TUR2/` altinda en az 1 rapor varsa.
Tum TUR 2 raporlarini birlestirip `rapor/MUTABAKAT.md` dosyasini su sablonla YAZ:

```
# MUTABAKAT

## KURAL 30 — BAGIMSIZLIK BEYANI

Ic ajanlar ayni modelin kopyalaridir; bagimsiz uzman sayilmaz. Gercek bagimsizlik
dis modellerle kurulur: <kullanilan dis model ve ortamlar; yoksa YOK — OLCULMEYEN>.

## HAKEM ENVANTERI

| Hakem/model | Ortam | Ic ajan / dis model | Bagimsizlik durumu |
|---|---|---|---|
| ... | ... | ... | ... |

## UZASILAN BULGULAR

...

## TARTISMALI VE ELENEN BULGULAR

...

## NIHAI P0/P1/P2 LISTESI

...
```

Kural 30 alanini ve `<>` yer tutucusunu gercek kosu bilgisiyle doldur; dis model
yoksa bunu `YOK — OLCULMEYEN` diye acikca yaz. Bos veya genel bir "sidk esastir"
cumlesi beyan sayilmaz. Ardindan kos ve exit kodunu yaz:

    bash scripts/check_integrity.sh --mutabakat

Kod 0 degilse `DURDU — MUTABAKAT-01 exit=<kod>` yaz ve DUR.

## ADIM 5 — GERI BESLEME: uzasilan bulgular → FIX-MANIFEST (B-8'in amaci)

Kosullar: `rapor/TUR2/` altinda en az 1 rapor varsa.
1. Tum TUR 2 raporlarindan **uzasilan** (2+ hakem katilani) P0/P1 bulgularini cikar.
2. `02-FAZ-2-FIX-MANIFEST.md` tablosuna YENI satirlar ekle:
   `| FIX-<max+1'den devam> | <P0|P1> | HAKEM | <bulgu ozeti> | PLANLANDI | TUR2-<hakem-sayisi>oy |`
   FIX-ID mevcut en buyuk numaradan DEVAM EDER; mevcut satirlar DEGISMEZ.
3. FAZ1 eslesmesi bölümüne `<BULGU-KAYNAK>→FIX-<n>` satirlarini ekle.
4. Kanit zorunlu: her yeni FIX icin rapor dosya adi + hakem oy sayisi kanittir;
   kanitsiz FIX satiri acma (REC-04/REC-05 bunlari yakalar).
5. Ardindan sunlari kos ve EXIT KODLARINI yaz:
   - `bash scripts/check_integrity.sh --faz2`
   - `bash scripts/check_integrity.sh --faz3`
6. Kod 0 degilse `DURDU — <komut> exit=<kod>` yaz; sessiz gecis yok.

## ADIM 6 — KAPANIS (fail-closed)

1. Uretilen her dosyanin yolunu `ls -la` ile kanitla.
2. Kosulmayan adimlari `NOT_EXECUTED: <neden>` ile yaz
   (orn. TUR 1 raporlari henuz yoksa ADIM 3-5 CALISTIRILMADI'dir — bu normaldir,
   ilk cagrıda yalniz ADIM 2 beklenir).
3. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
4. Kimse raporu onaylayamaz: nihai karari kullanici verir; sen yalniz
   uretim + mutabakat + exit kodlari bildirirsin.
