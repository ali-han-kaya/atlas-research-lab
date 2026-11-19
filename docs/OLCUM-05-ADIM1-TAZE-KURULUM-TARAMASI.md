# ÖLÇÜM-05 · ADIM 1 — TAZE KURULUM KAPI TARAMASI

Tarih: 24 Ağustos 2026 · Python 3.14.6 · Sürüm: **v1.7.9** (v1.7.8 mikro turu + bağımsız denetimin iki P0'ının düzeltmesi) · Maliyet **$0.00**
Koşu yeri: scratchpad (`.../scratchpad/KARSILASTIRMA/{once,sonra}`), **mtrx dışında**
Canlı model koşusu: **YOK** — bu adım tamamen yerel; ÖLÇÜM-05'in ajan koşusu bu turun DIŞINDA.

## SONUÇ — TEK CÜMLE

**Taze kurulan bir depoda, KFAZ3'ün yan ürünü (.pyc) diskteyken kapı taramasının tamamı
yeşil (`chg_reconcile` · `secret_scan` · `dep_audit` exit=0, `kod_selftest` 148/148) — ve
aynı depoya konan DÜŞMAN dosyası (`evil__pycache__/anahtar.pyc`, içinde gerçek PEM özel
anahtar) her iki kapıda da P0/exit=1 alıyor.** v1.7.7'de normal senaryonun üçü de
kırmızıydı; v1.7.8'de düşman senaryosu her iki kapıyı birden atlatıyordu (O5-05).

## KANIT SINIFLARI

- **A — ölçüldü:** komut + çıktı + exit kodu bu belgede.
- **C — ölçülmedi:** açıkça "doğrulanamadı" denir.

## 1. SENARYO (iki tarafta BİREBİR aynı)

```
taze git deposu (birim/hesap.py + tests/test_hesap.py, tek taban commit)
  → kur.sh <hedef>            (TEK koşu)
  → _KOSU/ KFAZ0+KFAZ1+KFAZ2 makine blokları + BASELINE.json
  → birim/hesap.py + tests/test_hesap.py'ye plana uygun değişiklik
  → python3 -m compileall birim tests      (KFAZ3'ün .pyc yan ürünü)
  → V4_VERIFY_YOLU export edilir           (00_KOD_OKU_BENI.md'nin önerdiği kullanım)
  → kapılar sırayla koşar
```

**ÖLÇÜLMEDİ (sınıf C):** `pytest` bu makinede kurulu değil (`No module named pytest`).
KFAZ3'ün `.pyc` yan ürünü `python3 -m compileall birim tests` ile üretildi — ürettiği
dosyalar (`birim/__pycache__/*.pyc`, `tests/__pycache__/*.pyc`) pytest'in ürettiğiyle
aynı sınıftır, ama **pytest'in kendisi bu turda koşmadı**.

## 2. ÖNCE / SONRA (sınıf A)

Önce = `git archive HEAD` ile çıkarılan **v1.7.7** ağacı (commit 0d8fb9c).

| Kapı | v1.7.7 | v1.7.8 |
|---|---|---|
| `kur.sh` | exit=0 | exit=0 (+ `.gitignore guncellendi: __pycache__/ *.pyc`) |
| untracked `.pyc` | **3** | **0** |
| `chg_reconcile` | **exit=1** · 2×P0 | **exit=0** · P0=0 |
| `secret_scan` (TAM mod) | **exit=1** · 2×P0 | **exit=0** · P0=0 |
| `dep_audit` | exit=0 | exit=0 |
| `kod_selftest` | **exit=1** · 116/121 | **exit=0** · 141/141 |

v1.7.7'nin P0 satırları (birebir):

```
P0 RECK-03 SCOPE_VIOLATION diff'te olan 'birim/__pycache__/hesap.cpython-314.pyc' KFAZ1 planinda YOK
P0 RECK-03 SCOPE_VIOLATION diff'te olan 'tests/__pycache__/test_hesap.cpython-314.pyc' KFAZ1 planinda YOK
P0 SEC-02 scripts/kod_selftest.py:528: sir kalibi eslesti
P0 SEC-02 scripts/kod_selftest.py:552: sir kalibi eslesti
```

Ayrı bir koşuda `secret_scan` **3×P0** verdi: üçüncü eşleşme
`scripts/__pycache__/kod_selftest.cpython-314.pyc:121` idi — `kur.sh` labın `scripts/`
dizinini `cp -R` ile kopyaladığı için lab tarafında derlenmiş `.pyc` de hedefe gidiyordu.
Bu üçüncü eşleşme de v1.7.8'de yok: parçalı yazım `.pyc`'ye tek parça sabit yazılmasını da
engelliyor (aşağıda ölçüldü).

## 3. KAPI KAPI EXIT KODLARI — taze kurulum (sınıf A)

### 3a. NORMAL SENARYO — v1.7.9 ölçümü

```
python3 scripts/chg_reconcile.py                exit=0   CHG-RECONCILE PASS — diff'te 50 dosya (urun 2 + kurulum 48 + onbellek 0) · P0=0 P1=1
python3 scripts/secret_scan.py                  exit=0   SECRET-SCAN PASS — 9 kalip · P0=0 P1=0
python3 scripts/dep_audit.py                    exit=0   DEP-AUDIT PASS — P0=0 P1=1
python3 scripts/perm_lint.py --sessiz           exit=0   PERM-LINT PASS — 10 izin blogu temiz
python3 scripts/budget_guard.py --preflight KFAZ0  exit=0   OK preflight KFAZ0: butce yeterli.
python3 scripts/api_surface.py                  exit=0   API-SURFACE PASS — kademe=T3 (CALISTIRILMADI, karar YOK)
python3 scripts/kod_selftest.py                 exit=0   KOD OZ-TEST: 148/148 gecti
python3 scripts/freeze_check.py                 exit=1   FREEZE-CHECK FAIL — [HICBIR HASH KARSILASTIRILMADI]
python3 scripts/test_attest.py                  exit=1   TEST-ATTEST FAIL — P0=3
bash    scripts/check_code_integrity.sh         exit=1   CODE-INTEGRITY FAIL — 3 hata, 1 uyari
```

(Öz-test kurulu kopyada 148, lab ağacında 149 — fark SUR-2, yalnız lab'da koşar.)

Son üç kapının `exit=1`'i **doğru fail-closed**tır, gürültü değildir — gerekçeleri:

```
freeze_check          P0 FRZ-06 CALISTIRILMADI  BASELINE.json'da `kod_profil_sha256` anahtari YOK
                      P0 FRZ-06 CALISTIRILMADI  BASELINE.json'da `scripts_sha256` anahtari YOK
test_attest           P0 TST-08 EVIDENCE_UNVERIFIED  _KOSU/03-KFAZ-3-TEST-EVIDENCE.json yok
check_code_integrity  FAIL ITG-11  _KOSU/gate/KOD-gate-2a.json yok
                      FAIL ITG-11  _KOSU/gate/KOD-gate-2b.json yok
                      FAIL ITG-20  FINAL-KOD-GATE.json yok — kapi birlestirilmemis
```

Üçü de **henüz üretilmemiş artefaktı** işaret ediyor (KFAZ3 kanıtı, KFAZ4 kapıları, tam
BASELINE). ÖLÇÜM-05 bu artefaktları ürettikçe kapanmaları beklenir; kapanmazlarsa o zaman
bulgudur.

### 3b. DÜŞMAN SENARYOSU — aynı taze kurulum (v1.7.9 ölçümü)

Aynı depoya `evil__pycache__/anahtar.pyc` konuyor (içinde tam PEM özel anahtar). `.gitignore`
`*.pyc` içerdiği için dosya `git add -f` ile zorla ekleniyor — gerçek bir saldırgan da böyle
yapar. İki kapı da yakalamalı:

```
chg_reconcile   exit=1   P0 RECK-03 SCOPE_VIOLATION diff'te olan 'evil__pycache__/anahtar.pyc' KFAZ1 planinda YOK
secret_scan     exit=1   P0 SEC-02 evil__pycache__/anahtar.pyc:1: sir kalibi eslesti
```

Karşı-olgu, **aynı depoda aynı dosyayla**, v1.7.8 kodu (`git archive HEAD`):

```
v1.7.8 chg_reconcile   exit=0   ·  0 adet P0
v1.7.8 secret_scan     exit=0   ·  0 adet P0
```

Bu, O5-05'in kapandığının doğrudan kanıtıdır: aynı girdi, aynı ortam, karşıt sonuç.

## 4. BU TURDA KAPATILAN GÜRÜLTÜ

### O5-01 — öz-fikstür sahte sırları (v1.7.7'nin açık bulgusu) · KAPANDI
`kod_selftest.py`'nin PEM fikstürleri kaynakta **tek parça** yazılıydı. Hat hedef depoya
kendi `scripts/`'ini de götürdüğü için bu satırlar **izlenmeyen** duruyor ve TAM mod taraması
onları gerçek sır sanıyordu. Çözüm: dize çalışma zamanında birleştirilir (`sahte_anahtar()`),
**yazılan dosya yine tam ve geçerli bir PEM** — fikstürün dişleri aynen duruyor.

Ölçülen ayrıntı: `"-----BEGIN RSA" + " PRIVATE KEY-----"` biçimi **yetmiyor** — CPython AST
optimizeri iki dize literalinin `+`'sını derleme zamanında **katlıyor** ve katlanmış sabit
`.pyc`'ye tek parça yazılıyor. `"".join((...))` çalışma zamanında koşar; `.pyc`'de parçalar
ayrı durur. Ölçüm:

```
"a" + "b"          -> pyc'de tam dize VAR
"".join((a, b))    -> pyc'de tam dize YOK
scripts/__pycache__/kod_selftest.cpython-314.pyc  tam dize var mi: False
```

### O5-02 — `__pycache__` gürültüsü · KAPANDI
Kök neden: hedef deponun `.gitignore`'unda `__pycache__/` ve `*.pyc` yok; kapılar diff
kümesini `git ls-files --others --exclude-standard` ile kuruyor. **Çözüm kaynakta:**
`kur.sh` kurulumda bu iki satırı hedefin `.gitignore`'una ekliyor (idempotent — varsa
DOKUNMUYOR) ve `--dogrula` eksikse FAIL sayıyor. **Ek savunma:** `chg_reconcile` ve
`secret_scan` `.pyc` uzantısını **loglu** muafiyetle kapsam dışı bırakıyor
(`BILGI RECK-03 ONBELLEK ...`, `BILGI SEC-05 ... pyc`). Sessiz muafiyet yok; muafiyet
hem **uzantıya** hem **yola** özgü (aşağıda) — izlenmeyen bir `.py` hâlâ P0.

Bu turda ölçülen yan etki: `kur.sh` artık hedefe `.gitignore` yazdığı için, taze depoda
o dosya **izlenmeyen doğuyor** ve `chg_reconcile` onu SCOPE_VIOLATION sayıyordu (kapatılan
gürültünün aynısı, başka kapıda). `.gitignore` de `KURULUM_KALIPLARI`'na alındı — loglu.

**Muafiyetin daraltılması (turun kendi denetiminde bulundu).** İlk sürüm yalnız uzantıya
bakıyordu (`yol.endswith(".pyc")`). Düşman senaryosu bunu kırdı:

```
sahte.pyc  (depo kökünde, içinde GERÇEK bir PEM özel anahtar)
  secret_scan  -> BILGI SEC-05 ... kapsam disi        ← YANLIŞ NEGATİF (sızıntı kapısında!)
  chg_reconcile-> muaf                                 ← plansız dosya kapsam denetiminden kaçıyor
```

Muafiyet **iki koşullu** yapıldı: dosya hem `.pyc` uzantılı olacak **hem de** bir
`__pycache__/` dizini içinde duracak. CPython 3 bytecode'u her zaman `__pycache__/` altına
yazar (pytest dâhil), dolayısıyla daraltmanın gerçek bir maliyeti yok. Daraltma sonrası ölçüm:

```
P0 SEC-02 sahte.pyc:1: sir kalibi eslesti
P0 RECK-03 SCOPE_VIOLATION diff'te olan 'sahte.pyc' KFAZ1 planinda YOK
BILGI SEC-05 birim/__pycache__/hesap.cpython-314.pyc: ... kapsam disi
BILGI RECK-03 ONBELLEK derleme onbellegi: birim/__pycache__/hesap.cpython-314.pyc ...
```

Katmanlı savunma da ölçüldü: KFAZ1 planında **açıkça `dondurulan`** ilan edilen bir `.pyc`
muafiyeti ezer ve `RECK-06 P0` verir.

### O5-03 — `V4_VERIFY_YOLU` ortam sızıntısı · KAPANDI (bu turda bulundu)
`00_KOD_OKU_BENI.md` operatöre `V4_VERIFY_YOLU=<yol>` demeyi öneriyor. Değişken **export**
edilmişse alt süreçlere sızıyor ve `secret_scan`'i KISMI modda sınayan 5 fikstür yanlış
kırmızı veriyordu. **Bu turdan önce de vardı** — kanıt, v1.7.7 ağacında (`git archive HEAD`):

```
v1.7.7 · env YOK  -> KOD OZ-TEST: 122/122 gecti
v1.7.7 · env VAR  -> KOD OZ-TEST: 117/122 gecti
                     FAIL K4-1, E2E-1, JSON-1, JSON-2, O4-03a
```

Kapılarda kusur yok; kusur öz-testin **ortama bağlı** olmasıydı. Çözüm: değişken başta
`os.environ`'dan çıkarılır; TAM modu isteyen fikstürler yolu açıkça `--v4` ile verir.
v1.7.8 iki ortamda da **142/142**.

### Kalan risk (açıkça yazılır)
`__pycache__/` altındaki bir `.pyc`, kaynağı depoda **olmayan** bir sır taşıyorsa `secret_scan`
onu görmez. Bilinçli takas: `.pyc` taranan bir `.py`'nin türevidir ve muafiyet **her seferinde
loglanır**. Asıl savunma `kur.sh`'ın `.gitignore` adımıdır; kapı muafiyeti yalnız ek savunmadır.

## 4b. v1.7.9'DA KAPATILAN İKİ P0 (bağımsız denetimin bulgusu)

### O5-05 — muafiyetin yol koşulu alt-dize arıyordu · **P0, iki kapılı kaçış** · KAPANDI
v1.7.8 muafiyeti `"__pycache__/" in yol` diye **alt-dize** arıyordu. Bu yüzden `__pycache__`
olmayan bir dizin — adında o dizeyi taşıması yeterli — önbellek sanılıyordu. Bu turda
yeniden üretildi (sınıf A):

```
evil__pycache__/anahtar.pyc   (takipli, içinde tam PEM özel anahtar)
  v1.7.8 chg_reconcile -> BILGI ONBELLEK  exit=0     ← kapsam kapısı atlandı
  v1.7.8 secret_scan   -> BILGI SEC-05    exit=0     ← sızıntı kapısı atlandı
```

Tek bir dizin adıyla **iki kapı birden** atlatılıyordu. Düzeltme: yol artık bileşenlerine
ayrılıp `__pycache__` **tam eşleşme** ile aranıyor (`PurePosixPath(yol).parts[:-1]`);
`parts[:-1]` dosya adının kendisini dışarıda bırakır. Alt-dize hiçbir yerde kullanılmıyor.
Düzeltme sonrası aynı dosya, aynı depo:

```
P0 RECK-03 SCOPE_VIOLATION diff'te olan 'evil__pycache__/anahtar.pyc' KFAZ1 planinda YOK   exit=1
P0 SEC-02 evil__pycache__/anahtar.pyc:1: sir kalibi eslesti                                 exit=1
BILGI RECK-03 ONBELLEK  birim/__pycache__/hesap.cpython-314.pyc  (GERÇEK önbellek, muaf)
BILGI SEC-05            birim/__pycache__/hesap.cpython-314.pyc  (GERÇEK önbellek, muaf)
```

### O5-06 — `secret_scan` kardeş ağaçtan yabancı Python import ediyordu · **P0, güven sınırı** · KAPANDI
`v4_aday_yollar()` hedefin **ebeveyninde özyinelemeli** `**/KOMUT_TOOLKIT_v4/.../v4_verify.py`
arıyor, bulduğunu `exec_module` ile **çalıştırıyordu**. Bu turda yeniden üretildi (sınıf A):
kardeş ağaca konan sahte bir `v4_verify.py`

1. **import edildi ve diske yazdı** (`IMPORT_EDILDIM.iz` dosyası oluştu),
2. kendi boş `SECRET_PATTERNS`'ini dayatarak depodaki **gerçek PEM anahtarını gizledi**,
3. `SECRET-SCAN PASS ... exit=0` verdirdi.

Yani kötü niyetli bir kardeş ağaç, hem keyfî kod çalıştırıyor hem de sızıntı kapısını
körleştiriyordu. Kötü niyet olmadan da bozuyordu: denetim klonu sistem temp kökündeyken
ilgisiz bir temp projesi bulunuyor ve öz-test **137/142**'ye düşüyordu.

Düzeltme: **özyinelemeli ebeveyn araması kaldırıldı.** Kalan kaynaklar — açık `--v4`,
`V4_VERIFY_YOLU`, `kod_profil.json`, taranan deponun **kendi içi**, ve dışarıdan tek
**sabit, özyinelemesiz** yol `KOK.parent/KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_verify.py`.
Bulunamazsa KISMI mod (exit=3) — mevcut fail-closed davranış korundu. Ölçüm:

```
kardeş sahte toolkit varken:  SECRET-SCAN KISMI ... exit=3   ·  IMPORT_EDILDIM.iz OLUŞMADI
açık --v4 ile:                SECRET-SCAN PASS   ... exit=0   ·  meşru yol kırılmadı
```

Ortam bağımlılığı da bitti — dört kombinasyonda aynı sonuç:

| | sistem TMPDIR | izole TMPDIR |
|---|---|---|
| `V4_VERIFY_YOLU` yok | **149/149** | **149/149** |
| `V4_VERIFY_YOLU` var | **149/149** | **149/149** |

Karşı-olgu (`git archive HEAD`, v1.7.8): sistem TMPDIR'ında **137/142** —
kırmızılar K4-1, E2E-1, JSON-1, JSON-2, O5-03b.

## 5. AÇIK BULGU

### O5-04 — `kur.sh` ikinci kez koşturulunca dizinleri iç içe kopyalıyor · **AÇIK** (P1)
`kopyala()` `cp -R "$SABLON/$parca" "$HEDEF/$parca"` yapıyor; hedef dizin **zaten varsa**
`cp -R` kaynağı onun **içine** kopyalıyor. Yeniden üretim (v1.7.7 ağacında da aynı → bu
turdan önce de var):

```
bash kur.sh <hedef>   # iki kez
ls -d .opencode/.opencode scripts/scripts templates/templates
  .opencode/.opencode   scripts/scripts   templates/templates
```

Sonuç: `chg_reconcile` `templates/templates/...` diye 30+ ek kurulum dosyası görüyor
(P0 değil, BILGI — ama ağaç kirleniyor). **v1.7.8'de de aynen sürüyor** (yeniden ölçüldü;
`.gitignore` adımı idempotent ama `cp -R` değil). **Bu turda DÜZELTİLMEDİ**: düzeltme kurulumun
çekirdek kopyalama yolunu (`cp -R` semantiği) değiştirmeyi gerektiriyor ve bu turun iki
maddesinin dışında. ÖLÇÜM-05 için operatör notu: **kur.sh'ı aynı hedefte iki kez koşturma**;
gerekiyorsa hedefi silip yeniden kur.

## 6. BEYAN DÜZELTMELERİ (v1.7.9 turunda, bağımsız denetimin bulgusu)

Bu raporun v1.7.8 sürümünde ve o turun kapanış tablosunda üç beyan hatası vardı.
İşlev hükmünü değiştirmiyorlar, ama kayıt yanlış kalmasın:

| Beyan | Yazılan | Git gerçeği |
|---|---|---|
| `kod_selftest.py` | +280 / −14 | **+269 / −11** |
| `chg_reconcile.py` | +48 | **+45 / −3** |
| Değişen dosya kapsamı | "yalnız `scripts/` altında 4" | **6 dosya** (4 betik + SURUM.md + bu rapor) |

Kök neden: `git show --stat`'ın satır toplamı (`45 +++---` = 48 değişen satır) *eklenen*
satır sanıldı. Doğru kaynak `git show --numstat`. Toplam yine `579 ekleme / 14 silme`.

**`diff -r fark 0` beyanı hakkında:** ölçüm anında doğruydu; sonradan iCloud
senkronizasyonu v1.7.8 yedeğinde üç **boş** çatışma dizini yarattı — `KOD_SABLONLAR 2`
(20:19), `.git 2` ve `ORTAK 2` (20:22; son ikisi denetçinin izinli indeks onarımı
sırasında). Şu an ölçüldü: `diff -r` bu üçünü `Only in ...` diye gösteriyor; hepsi **0
öğe** içeriyor, kaynakta yok, v1.7.7 yedeğinde de yok. Manifest boş dizinleri saymadığı
için `MANIFEST_SHA256_v1.7.8.txt` **794/794 hâlâ geçerli** (eksik dosya 0 — yeniden
ölçüldü). Silinmediler: eski yedeğe dokunmak kırmızı çizgi; **kullanıcı kararı bekliyor.**

## 7. KIRMIZI ÇİZGİLER

Commit `ddabe5d` **6 dosya** değiştirdi: 4 betik + `SURUM.md` + bu rapor
(git gerçeği: `6 files changed, 579 insertions(+), 14 deletions(-)`). `yahuditurk/`, `portfolyo/`,
`TRUTH_MAKALE*`, `isimlendir/`, `CIKTI_ALLAHASKI`, ATLAS/toolkit orijinalleri, `DENEME/`,
`ATLAS_SABLONLAR`, mtrx kökü — **dokunulmadı**. Eski iCloud yedekleri silinmedi.
Bütün koşular scratchpad'de, mtrx dışında.
