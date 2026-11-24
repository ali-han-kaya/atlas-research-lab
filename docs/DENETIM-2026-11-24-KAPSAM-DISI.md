# KAPSAM DIŞI DENETİMİ — 2026-11-24

**Soru:** "Kapsam dışı kalan 26 kuralın gerekçelerini bağımsız olarak yeniden denetle."

**Önce ölçüm, sonra cevap:** diskte **26 kapsam dışı kural yok.** `tools/kapsam.py`
envanterinde kapsam dışı sayısı **0**'dır. Sayı bir noktada 4 idi; 24.11.2026'da
(`c9ff2f1`) bu dört kayıt *ölü kimlik* sınıfına taşındı ve envanterden çıkarıldı.
Bugünkü ölçüm:

```
$ python3 -c "import sys; sys.path.insert(0,'tools'); import kapsam; \
  s,_,(t,d,b,o,k)=kapsam.olc(); print(len(s),t,k,d,b)"
117 93 24 0 0
```

| Küme | Adet | Ölçüm |
|---|---|---|
| TEST EDİLDİ (ateşleyen mutasyon) | 93 | `batarya` HATA/TERMINAL sözleşmesi |
| BEKLENEN BULGU (yalnız işaretçi) | 24 | vaka var, sözleşme `BEKLENEN_BULGU` |
| Ölü kimlik (envanter dışı) | 4 | `kodda_akan_kimlikler` → yok |
| Dış referans (envanter dışı) | 1 | `DEC-027`, kural değil |
| Kapsam dışı / boşluk | 0 / 0 | ratchet PASS |

Buna ek olarak kapsam kapısının **hiç taramadığı** betiklerde bildirilen kurallar
ölçüldü (aşağıda §3). Yani "kapsam dışı" denen şey tek bir sayı değil, üç ayrı
küme. Bu rapor o üç kümeyi ayırır ve **hiçbirini test edilmiş saymaz** —
93 dışındaki hiçbir kural bu belgede "test edildi" olarak işaretlenmemiştir.

---

## 1. Yöntem (her satır komutla)

| Ölçüm | Komut | Çıktı |
|---|---|---|
| Envanter durumları | `kapsam.olc()` | `117 · test=93 · beklenen=24 · dışı=0 · boşluk=0` |
| Kodda basılıyor mu | `kapsam.kodda_akan_kimlikler()` (AST, docstring hariç) | aşağıdaki tablolarda `akan` |
| Mutasyon vakası | `kapsam.batarya_modu().vakalar()` + `vaka_anahtarlari` | `bat=` |
| Öz-testte anılıyor mu | tüm `*selftest*.py` metni | `oz=` |
| Tarama dışı betikler | `git ls-files '*.py'` − `kapsam.DIZINLER` | `38 kayıt / 31 tekil` |

`akan=False` = kimlik bildirilir ama hiçbir kod dalında basılmaz (ölü).
`bat=1` fakat sözleşme `BEKLENEN_BULGU` = mutasyon **ateşlenmiyor**, yalnız
hedef iz işaretçiyle doğrulanıyor.

---

## 2. Gerçekten mutasyona uygun olmayanlar

### 2a. Kasıtlı kaldırılmış (mutasyon anlamsız) — **1 kural**

| Kural | Betik | Kanıt | Karar |
|---|---|---|---|
| `OZT-04` | `oztest_attest.py` | `akan=False`, `bat=0`; dosyada yalnız "OZT-04 NICIN YOK" açıklaması | **Doğru dışarıda.** Kural silinmiş; sayaç düşüşü zaten `OZT-02` ile yakalanıyor. Mutasyonu yok çünkü uygulaması yok |

### 2b. İlan edilen ama uygulanmayan — **3 kural** (bu bir *kusur*, gerekçe değil)

| Kural | Betik | Başlıktaki vaat | Kanıt |
|---|---|---|---|
| `API-03` | `api_surface.py` | `[P0] imza degismis (parametre/donus)` | `akan=False`; kodda yalnız `API-02` (kayıp) ve `API-04` (regex adayı) dalları var |
| `DEP-02` | `dep_audit.py` | `[P0] Manifestteki paket kilitte yok` | `akan=False`; dallar `DEP-01/03/04/05/06` |
| `SEC-04` | `secret_scan.py` | `[bilgi] Ikili/kilit dosyasi atlandi` | `akan=False`; atlananlar yalnız sayılıyor, kimlikli satır üretilmiyor |

**Bağımsız denetim sonucu:** bu üçü "mutasyona uygun değil" diye dışarıda
bırakılmış gibi görünüyor ama gerçek durum farklı — **kapı, uygulamadığı bir
kuralı ilan ediyor.** İkisi P0. Bu, sessiz bir güven açığıdır: `MUTASYON_KAPSAM.md`
okuyucusu "API-03 ve DEP-02 korunuyor" sanır, oysa iki dal hiç yok.

İki yol var, ikisi de bu raporun kapsamı dışında (karar Ali'nin):
(1) dalı gerçekten yaz + mutasyon vakası ekle, ya da (2) başlıktaki bildirimi
kaldır ve kuralı envanterden düşür. Şu anki hâl — bildirimi tutup envanter dışı
saymak — en zayıf seçenek, çünkü vaat ile davranış ayrışıyor.

---

## 3. Yanlışlıkla dışarıda bırakılanlar — **31 tekil kural** (38 kayıt)

Kapsam kapısı yalnız `ATLAS_SABLONLAR/scripts` ve `KOD_SABLONLAR/scripts`
dizinlerini tarar (`kapsam.DIZINLER`). `tools/` altındaki kapı betikleri
bildirdikleri kurallarla birlikte **tamamen görünmez**:

| Betik | Kural | Kayıt | Kendi koşucusu | Koşucu çıktısı |
|---|---|---|---|---|
| `tools/kamu_lint.py` | `KAMU-01…06` | 6 | `--kontrol --oztest` | `KAMU-LINT OZ-TEST: PASS — 7/7` |
| `tools/kanit_dogrula.py` + `kanit_negatif.py` | `KANIT-00…06` | 7+7 | `make kanit-negatif` | `KANIT NEGATIF: PASS — 14/14` |
| `tools/yayin_kapisi.py` | `YAYIN-01…07` | 7 | `--kontrol --oztest` | `YAYIN-KAPISI OZ-TEST: PASS — 5/5` |
| `tools/kanit_paketi_dogrula.py` | `PAKET-00…10` | 11 | **yok** | — |

Ölçüm: bu 38 kaydın **hepsi `akan=True`** (kodda gerçekten basılıyor) ve
**hepsinde `bat=0`** — yani mutasyon bataryasında hiç ateşlenmiyorlar.

İki alt grup:

- **20 kural** (`KAMU`, `KANIT`, `YAYIN`) — kendi fikstür koşucusu CI'da zaten
  koşuyor (`dogrula.py` ön koşulları + `make kanit-negatif`). Bunlar "test
  edilmemiş" değil, **envanterin saymadığı test edilmiş** kural. Envanter
  sayısına katılmadıkları için `117` bir alt sınırdır.
- **11 kural** (`PAKET-00…10`) — kendi negatif koşucusu yok; yalnız gerçek bir
  `kanit-paketi/` dizini varken koşar (CI'da "Kanit paketi uret" adımından sonra).
  Bunlar ne mutasyonla ne fikstürle kanıtlanmış: **en zayıf grup.**

**Bu bir gerekçe değil, kapsam boşluğu:** `DIZINLER` iki dizinle sınırlı olduğu
için 31 kural ratchet'in dışında kalıyor; sayı düşse de kimse görmez. Düzeltme
`DIZINLER`'e `tools/` eklemek olurdu — ancak o zaman 31 kural "boşluk" olarak
belirir ve `TABAN_TEST_EDILEN` ratchet'i kırmızı verir. Bu yüzden bu rapor
yalnız ölçer, kapsamı değiştirmez.

`DENEME/scripts/verify_doi.py` taranmadı: `AGENTS.md` §5 kırmızı çizgi
("bilerek dondurulmuş kusurlu koşu").

---

## 4. Eksik ortam gereksinimleri — **6 kural** (+11 `PAKET`)

Bu kurallar dal olarak var ama **bu makinede/CI'da tetiklenemez**, çünkü
gereksinim ortamda yok. Bu "mutasyona uygun değil" değil, "ortam eksik".

| Kural | Gereksinim | Kanıt |
|---|---|---|
| `MOD-01`, `MOD-07` | opencode model kataloğu | `ENV: ~/.cache/opencode/models.json` veya `ATLAS_MODEL_KATALOG`; katalog yokken çıktı `FAIL MOD-00: model katalogu yok` — MOD-01/07 hiç ateşlenmez |
| `API-01`, `API-05` | KFAZ0 imza envanteri / `imza_komutu` | `api_surface.py` taban yoksa `CALISTIRILMADI` |
| `DEP-06` | profilde `bagimlilik_manifesti` | `CALISTIRILMADI P1 + OLCULMEYEN` |
| `TSL-05` | HMAC anahtarı | `LAB_IMZA_ANAHTARI` env veya `~/.config/lab_imza.key` |
| `DEP-04` | git diff bağlamı | `git diff --name-only HEAD` |
| `PAKET-00…10` | gerçek `kanit-paketi/` dizini | paket yoksa araç `rc=2` ile durur |

Ölçüm: `env -i HOME=/tmp/bos_ev python3 ATLAS_SABLONLAR/scripts/check_models.py`
→ `FAIL MOD-00: model katalogu yok`. Yani CI'da `MOD-01/07` daima sessizdir;
mutasyonla kanıtlanmaları katalog fikstürü gerektirir (bu depo `tools/model_katalog.json`
sabitini taşıyor ve `oztest_mutasyon` onu env ile veriyor — aynı yol burada da kullanılabilir).

---

## 5. Yalnız işaretçiyle doğrulanan 24 kural

Bunlar envanterde **BEKLENEN BULGU** olarak sayılıyor: bataryada vakaları var ama
sözleşme `BEKLENEN_BULGU` (rc=0 + hedef iz), yani **kırmızı hüküm üretmiyorlar**.
Bu rapor onları "mutasyonla test edilmiş" saymaz.

| Mutasyona uygun (18) | Ortam gerektiren (6) |
|---|---|
| `CITE-03`, `OZT-05`, `PL-12`, `PL-14`, `CHK-05`, `QR-01`, `SP-05`, `API-04`, `DEP-03`, `DEP-04`, `PERM-03`, `PERM-05`, `PERM-06`, `PERM-07`, `PERM-08`, `SEC-03`, `SEC-05`, `TST-06` | `MOD-01`, `MOD-07`, `API-01`, `API-05`, `DEP-06`, `TSL-05` |

Sol sütundaki 18 kural bugün **işaretçiyle** doğrulanıyor; HATA sözleşmesine
çevrilebilecekleri ölçülmedi (her biri için temiz taban + ihlal fikstürü
gerekiyor). Sağ sütundakiler ancak ortam sağlanırsa denenebilir.

---

## 6. Sonuç tablosu

| Kategori | Adet | Durum |
|---|---|---|
| Ateşleyen mutasyonla kanıtlı (TEST EDİLDİ) | 93 | değişmedi |
| Yalnız işaretçi (BEKLENEN BULGU) | 24 | 18'i mutasyona uygun, 6'sı ortam |
| Ölü kimlik | 4 | 1 kasıtlı, 3 ilan-uygulama uyuşmazlığı (2'si P0) |
| Dış referans (`DEC-027`) | 1 | kural değil |
| Kapsam kapısının görmediği | 31 | 20'si kendi koşucusunda, 11'i koşucusuz |
| **Kanıtlanmış-test sayılan toplam** | **93** | geri kalan **59 kural test edilmiş sayılmadı** |

`93 + 24 + 4 + 31 = 152` kayıt; tekil kural olarak `93 + 24 + 4 + 31 = 152`
(kanıt: `31` tekil, `38` kayıt farkı `KANIT` kimliklerinin iki betikte
bildirilmesinden).

---

## 7. OLCULMEYEN

- **Sol sütundaki 18 kuralın HATA sözleşmesine çevrilebilirliği** ölçülmedi;
  her biri için fikstür yazmak gerekir.
- **`PAKET-00…10`** için tek bir negatif vaka koşulmadı: paket üretimi
  (`make kanit-paketi`) ayrı bir koşu gerektiriyor.
- **`KAMU/KANIT/YAYIN`** kurallarının fikstür koşucuları PASS veriyor; bunların
  *mutasyonla* ateşlendiği (kaynağı bozunca kırmızı olduğu) ölçülmedi.
- **26 sayısının kaynağı** bulunamadı: repoda ne `docs/`, ne `tools/`, ne git
  geçmişinde "26 kapsam dışı kural" kaydı yok (`grep -rn "26 kural"` → 0).
  En yakın gerçek kümeler `24` (işaretçi) ve `31` (görünmez). Sayı bilinçli
  olarak **hiçbir yere yazılmadı**; uydurulmadı.

---

## 8. Karar gereken üç nokta (model karar veremez)

1. `API-03` ve `DEP-02`: dal yazılsın mı, bildirim mi kaldırılsın? (ikisi de P0 vaadi)
2. `DIZINLER`'e `tools/` eklensin mi? (31 kural envantere girer, ratchet tabanı
   yeniden kurulur — sayılar düşer görünecek, gerçekte görünür olacak)
3. `PAKET-00…10` için fikstür koşucusu yazılsın mı?
