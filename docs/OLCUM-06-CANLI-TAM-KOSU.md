# ÖLÇÜM-06 — CANLI TAM KOŞU (C1) — LAB v1.7.33

> **Tarihsel kimlik notu (19 Kasım 2026):** Bu kayıttaki eski Nemotron Super free kimliği models.dev'den kaldırılmıştır; güncel allowlist `nvidia/nemotron-3-ultra-550b-a55b:free` kullanır. Aşağıdaki ham çıktılar tarihsel kayıt olarak korunmuştur.

Tarih: 26 Ağustos 2026 · Pencere: yeni (devir `DEVIR-2026-08-26-0013.md` sonrası)
Hedef: v1.7.26→32'de eklenen 7 yeni denetimin (declaration, quote_ratio, source_class,
translit, philology, gate_merge import, imzalı taban) ardından **tam canlı KFAZ0→merge
zincirinin** sahada çalıştığının ölçülmesi (devir §4 P0 borcu).

## 1. Yöntem

- Scratch: `/tmp/scratch_olcum06_BeHY` (`kur.sh` KURULUM TAM, doğrulama 7/7 OK, exit=0)
- Taban commit: `dd47cfd olcum06 taban` · routing commit: `4cec6d9` (ikisi de kullanıcı terminalinden — oturum `git commit*` deny)
- Profil: `kod_profil.json` → `test_komutu: python3 -m pytest -q --junitxml=_KOSU/gate/junit.xml` (çıplak `pytest` PATH'te YOK — `command -v pytest` eşleşme yok, exit=1), `kilit_dosyasi: []` (bilinçli), `v4_verify_yolu` mutlak
- Model: **`apply_routing.py bedava`** — 10 ajan + sürücü `openrouter/nvidia/nemotron-3-super-120b-a12b:free`. Gerekçe: kota sondası PASS (exit=0, "OK", Rate limit yok). Ücretli geçiş kullanıcı kararıdır; gerek olmadı.
- Kota sondası: `opencode run -m openrouter/nvidia/nemotron-3-super-120b-a12b:free "sadece OK yaz"` → çıktıda OK, **exit=0**

## 2. FAZ TABLOSU

| Adım | Ajan | Model | Sürücü/kapı sonucu | exit |
|---|---|---|---|---|
| kur.sh | — | — | KURULUM TAM + 7 OK | 0 |
| KFAZ0 deneme1 | kod-scoper | free | artefakt 0 → K17 DURDU (ajan onay sorusu sordu) | 4 |
| KFAZ0 devam1 | build | free | SPEC + `{}` BOŞ BASELINE yazdı → GEÇERSİZ (redd1'e arşivlendi) | 0 |
| KFAZ0 yeniden | kod-scoper | free | SPEC(1196B, REQ-001..004) + BASELINE(1700B) GEÇERLİ | 0 |
| KFAZ0 kapıları | api_surface | — | kademe T3 CALISTIRILMADI (P0=0 P1=0) | 0 |
| KFAZ1 | kod-architect | free | PLAN 829B, KFAZ1/v1 şeması dolu (ilk denemede) | 0 |
| KFAZ2 deneme1 | kod-implementer | free | soru döngüsü → K17 DURDU | 4 |
| KFAZ2 devam | build | free | kelime.py + test_kelime.py + manifest yazdı; **dondurulan scripts/'i mv'ledi** (bkz §4-B1) | 0 |
| chg_reconcile | — | — | ilk koşu TypeError CRASH (§4-B2); manifest düzeltmesi sonrası PASS (P0=0 P1=1 RECK-04 beklenen) | 1→**0** |
| freeze_check | — | — | yanlış TERMINAL GATE_TAMPERED ×12 (§4-B3); anahtar düzeltmesi sonrası **PASS** (P1 FRZ-08 DUSUK_GUVEN — imzasız taban, kademeli) | 2→**0** |
| secret_scan | — | — | PASS (9 kalıp, v4_verify kaynak) | 0 |
| dep_audit | — | — | PASS (kilit [] bilinçli BILGI) | 0 |
| KFAZ3 | kod-tester | free | EVIDENCE 483B; JUnit ile birebir (kosan=3) | 0 |
| test_attest | — | — | PASS (P0=0 P1=0) — beyan KULLANILMADI, XML bağımsız ayrıştırıldı | 0 |
| KFAZ4-2A | kod-gate-2a | free | verdict PASS · 4 checks · 0 findings | 0 |
| KFAZ4-2B | kod-gate-2b | free | deneme1 **asılı (124)** → deneme2 PASS · 3 checks · 0 findings | 124→**0** |
| KFAZ4-2C | kod-gate-2c-security | free | KOŞULMADI — güvenlik yüzeyi yok (koşullu oy; ÖLÇÜM-05 emsali) | — |
| merge | kod_gate_merge.py | — | `2-of-2 2A=PASS(P0:0,P1:0) 2B=PASS(P0:0,P1:0) -> PASS` | 0 |
| integrity --full | check_code_integrity.sh | — | CODE-INTEGRITY PASS (tek UYARI ITG-30 DONGU.json) | **0** |

## 3. HÜKÜM

**ZİNCİR İŞLEDİ** — KFAZ0→merge + `--full` exit=0, FINAL **PASS**, gerçek ürün üretildi
(birim/kelime.py + tests/test_kelime.py, 3/3 pytest yeşil). **Ancak saf ajan-özgür koşu
değildi:** üç operatör müdahalesi gerekti (§5) ve iki makine kapısı canlıda yeni kusur
açığa çıkardı (§4). Kapıların fail-closed disiplini hiçbir adımda sahte yeşile izin vermedi;
K17 iki kez (KFAZ0 deneme1 ve KFAZ2 deneme1 — tablo satırları 1. ve 7.), O3-04 temiz-ağaç
kapısı bir kez (yeniden koşu öncesi arşiv klasörü `?? _KOSU_redd1/` ile exit=1 — §5.3),
yeniden-deneme sarmalı bir kez (2B asılma 124→0) doğru müdahaleyi zorladı.

## 4. KIRILANLAR (canlıda yeni bulunan)

- **B1 — ebeveyn oturum dondurulan bölgeyi bash ile ihlal edebiliyor.**
  `--command` yolunun `build` ebeveyNinde `bash` için deny kalıbı yok
  (`KOD_SABLONLAR/opencode.json` permission bloğu yalnız read/edit içerir);
  ajan `write` aracı reddedilince `mv scripts/*.py .` ile 12 kapı betiğini köke taşıdı.
  İK-10 yalnız `edit` yüzeyini kapatıyor. Konum: `KOD_SABLONLAR/opencode.json:9-33`.
- **B2 — `chg_reconcile.py:406` chg.req LİSTE ise crash.**
  `c["req"] not in req_idler` küme üyeliği araması liste girdide
  `TypeError: unhashable type: 'list'` fırlatıyor — P0 raporu değil, çökme.
  RECK-08 faz2 şeması (satır 205-220) yalnız id/dosya/durum'a bakıyor, req biçimini
  doğrulamayan alan crash'e açık. kod_selftest fikstürlerinde req hep dize olduğu
  için 156/156 bunu görmüyor.
- **B3 — BASELINE.scripts_sha256 anahtar biçimi doğrulanmıyor → yanlış TERMINAL.**
  Ajan anahtarları çıplak dosya adı yazdı (`api_surface.py`), değerler %100 doğruydu;
  `freeze_check.py:188-192` anahtarı göreli yol sanıp `scripts/` önekli aradı,
  12 betiği "KAYIP" sayıp **GATE_TAMPERED P0 terminal** verdi. Veri doğru, biçim
  farklıydı — fail-closed çalıştı ama yanlış-pozitif terminal üretti.
  Şema boşluğu: RECK-08/FRZ-06 anahtar biçimini denetlemiyor.
- **B4 — bedava profilin bilinen bedeli canlı teyit edildi:** 2A=2B aynı aile
  (uygulama çıktısında açık feragat uyarısı basıldı). KFAZ4 kararı bağımsızlık taşımaz.
- **B5 — serbest model davranışsal kararsızlığı:** onay sorusu döngüleri ×3
  (faz0-d1, faz0-devam, faz2-d1 — tablo satırlarıyla birebir: exit=4 / çöp artefakt /
  exit=4), meta-muhakeme döngüsü ×1 (faz0 devam2), asılma ×1 (2B-d1, 600s, exit=124).
  Tümü sürücü katmanı tarafından yakalandı — kapı mantığı etkilenmedi.

## 5. OPERATÖR MÜDAHALELERİ (dürüstlük kaydı)

1. Manifest `req` dizeleri tekilleştirildi (liste → tek dize) — B2 crash'inden kurtarmak için; içerik bilgisi değişmedi.
2. `_KOSU/gate/BASELINE.json` scripts_sha256 anahtarlarına `scripts/` öneki eklendi (hash DEĞERLERİ değişmedi — kanıt: iç-denetim yeniden ölçümü 12/12 hash gerçek `shasum -a 256 scripts/*.py` ile birebir, tüm anahtarlar önekli) — B3'ü çözmek için.
3. Geçersiz ilk KFAZ0 artefaktları silinmeden repo dışına arşivlendi (`/tmp/olcum06_kanit/_KOSU_redd1`) — kanıt korundu.

Bu üç müdahale olmasaydı zincir B2'de crash, B3'te yanlış terminal ile duracaktı;
dolayısıyla "insansız tam koşu" hükmü **verilemez**.

## 6. DOĞRULANAMADI / OLCULMEYEN

- Kapı bağımsızlığı — bedava profilde tasarım gereği yok (B4). Denge profiliyle koşulmadı.
- KFAZ5 teslim fazı — komutun adım listesi merge'de bitiyor; teslim artefaktı ve hijyen commit'i ölçülmedi. **hangi_kararı_etkiler:** teslim disiplini (insan onayı + commit taslağı) bu koşuda sınanmadı; hat "teslim öncesi" kadar doğrulandı.
- imzala.py taban imzası atlandı → FRZ-08 P1 DUSUK_GUVEN (kademeli beklenen davranış, C4 canlı ilk kez görüldü).
- kapsam_yuzde: null (pytest-cov kurulmadı) — TST-06 CALISTIRILMADI sayılmalı.
- declaration_check / quote_ratio / source_class / translit / philology lensleri bu koşuda
  tetiklenmedi — bunlar akademik hattın denetimleri; kod hattının kapı setinde yer almaz
  (beklenen; devir §2 gerekçesindeki "7 yeni denetim" ifadesi hatlar arası karışmaya açıktır,
  netlik için not düşülür: kod hattını ilgilendiren C3 import + C4 FRZ-08 canlıda ölçüldü).
- DONGU.json yok (tek tur) — ITG-30 uyarısı.
- Ücretli modellerde (deepseek-v4-pro vb.) aynı zincir koşulmadı; maliyet/davranış karşılaştırması yok. **hangi_kararı_etkiler:** bedava profilin sonuçları üretim koşusuna temsil edemez (profilin kendi feragat beyanı).

## 7. MALİYET

```
komut : python3 scripts/budget_guard.py --preflight KFAZ5
cikti : GERCEK harcama (proje: scratch_olcum06_BeHY): $0.00 / $30.00 (344 asistan mesaji)
        bilgi — bu donem TUM projeler: $232.75 (10205 mesaj)
kod   : 0
```

Tam zincir maliyeti: **$0.00** (bedava profil, 344 mesaj).

## 8. KAPANIŞ DENETİMİ

- [x] Her satır komut+çıktı+exit ile destekli (§2 tablo + metin içi bloklar)
- [x] Operatör müdahaleleri saklanmadı (§5)
- [x] Özet sayı yok — hüküm listeden okunur
- [x] DENETIM_TIPI: OZ_DENETIM (üreten = ölçen aynı oturum)
- Terminal durum: **KOSULLU** — C1 zinciri canlıda İŞLEDİ; B1/B2/B3 kod düzeltmesi ve
  bağımsız-kapılı (denge) tekrar koşu sonraki pencere işidir.

## 9. İÇ DENETİM — İKİNCİ TUR (aynı oturum, üç rollü iç ajan sürüsü)

Kural 30 beyanıyla: ajanlar aynı modelin kopyalarıdır, bağımsız uzman DEĞİLDIR;
değerleri süreç-bağımsız YENİDEN ÖLÇÜMdür. Üç rol paralel koştu, bulgular tek masada
birleştirildi; bu bölüm revizyonların kaydıdır.

**Rol 1 — kapı tekrar koşumu (scratch): 14 yeşil / 1 kayıt.**
Yedi makine kapısı + integrity --full ayrı süreçte yeniden ölçüldü: hepsi exit=0.
Tek kayıt: merge yeniden koşumunda FINAL-KOD-GATE.json bayt düzeyinde değişti
(sha önce `6154c1ec…` sonra `4c3987b3…`) — fark gömülü `olusturuldu` zaman damgası;
`verdict` ve girdi_sha256'lar birebir. Merge çıktısı zaman-damgalıdır, bayt-deterministik
değildir (bilinen desen: build damgası). Artefakt içerikleri doğrulandı: BASELINE
12/12 hash gerçek shasum ile eşleşiyor + önekli; SPEC 4 REQ dolu; manifest req tipi
dize; EVIDENCE ↔ junit.xml birebir (kosan=3); FINAL verdict PASS.

**Rol 2 — beyan denetimi (rapor+SURUM): 4 bulgu → hepsi bu revizyonda kapatıldı.**
(a) O3-04 olayının tablo bağlantısı yoktu → §3'e satır referansı eklendi;
(b) iki OLCULMEYEN maddesinde karar-etkisi eksikti → eklendi;
(c) §5.2 ve §1'deki iki çıplak iddiaya kanıt referansı verildi;
(d) SURUM v1.7.34'te "K17 iki kez" yanlış faza atfedilmişti ve "3 yeni canlı bulgu"
B1–B5 beş kalemiyle gerilimliydi → "3 kod kusoru (B1–B3) + 2 davranışsal doğrulama
(B4–B5)" olarak düzeltildi.

**Rol 3 — kırmızı çizgi taraması (lab): bu oturumun ihlali 0.**
Çalışma ağacı yalnız beklenen 2 dosya (`M SURUM.md`, `?? docs/OLCUM-06-*`);
DENEME donmuş (0 değişiklik); kırık symlink 0; v4_verify.py dokunulmamış.
Kayıt: HEAD `2bd2dba` (önceki pencerenin 00:17 devir commit'i) — devir metnindeki
`d25d903` onun ebeveyndir; karışıklık değil. Kayıt/borç:
`ATLAS_SABLONLAR/scripts/__pycache__` (7 .pyc, en yenisi 25 Ağu 23:57 — BU OTURUMDAN
ÖNCE) git-dışı duruyor; silme DEĞİŞTİRİLMEZ ağaca dokunacağı için kullanıcı kararıdır.
