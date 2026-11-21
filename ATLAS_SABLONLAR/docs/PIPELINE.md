# Atlas v5.5 — Pipeline Haritası

> Bu belge, önceki sürümlerde `opencode.json` içine (şema-dışı olarak) gömülen
> `version` / `description` / `pipeline` / model→rol eşleme bilgisini taşır.
> opencode `Config` şeması `additionalProperties: false` olduğu için bu alanlar
> `opencode.json`'da bulunamaz (yoksa opencode `ConfigInvalidError` ile başlamaz).
> Bilgi buraya taşındı; makine tarafından okunmaz, yalnızca referanstır.

- **version:** v5.5.4 (v5.5.3'un guvenlik + tutarlilik sikilastirmasi uzerine; pipeline artefakt token'ı `v5.5` olarak korunur)
- **description:** Atlas Akademik v5.5 — çok-ajanlı makale yazım/denetim pipeline (sinirbilim/felsefe/teoloji/bilişsel)

## Model → Rol Eşlemesi

| Model | Roller |
|-------|--------|
| `openrouter/anthropic/claude-opus-5` | orchestrator, scoper, writer-master, editor-lens, gate-orchestrator |
| `openrouter/z-ai/glm-5.3` | structure-lens, gate-2b |
| `openrouter/deepseek/deepseek-v4-pro` | consistency-lens, gate-2a |
| `openrouter/moonshotai/kimi-k3` | (kodlama; bagli ajan yok) |

## Faz Haritası

| Faz | Ajan(lar) | Model(ler) | Komut | Mod | Çıktı |
|-----|-----------|-----------|-------|-----|-------|
| FAZ0 | atlas-scoper | claude-opus-5 | `/atlas-faz0` | — | `00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md` |
| FAZ1 | atlas-lens-structure + atlas-lens-consistency + atlas-lens-editor | glm-5.3 + deepseek-v4-pro + claude-opus-5 | `/atlas-faz1` | PARALLEL | `01-FAZ-1-LENS-ANALYSIS.json` |
| FAZ2 | orchestrator (fixer) | claude-opus-5 | `/atlas-faz2` | — | `02-FAZ-2-FIX-MANIFEST.md` |
| FAZ3 | atlas-writer-master | claude-opus-5 | `/atlas-faz3` | — | `03-FAZ-3-MASTER-v5.5.md` |
| FAZ4 | atlas-gate-2a + atlas-gate-2b + gate_merge.py | deepseek-v4-pro + glm-5.3 | `/atlas-gate-2a`, `/atlas-gate-2b` | 2-of-2 voting | `gate/FINAL-GATE-v5.5.json`, `04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md` |

## Girdi Modeli (önemli)

Atlas bir **denetim + sertleştirme** aracıdır. FAZ1 lens'leri `MASTER.md`'yi
denetler; bu nedenle pipeline'a girmeden önce **kullanıcı bir taslak MASTER
sağlar** (veya elindeki A/B kaynak paketlerinden bir taslak üretir). Akış:

```
[Kullanıcı taslak MASTER + A/B kaynak paketleri]
   → FAZ0 (scope sözleşmesi)
   → FAZ1 (3 lens taslağı denetler, paralel)
   → FAZ2 (fixer: seçilen P0/P1 düzeltmeleri, kullanıcı onayıyla)
   → FAZ3 (writer: düzeltmeleri işleyip MASTER'ı finalize eder)
   → FAZ4 (2-of-2 gate)
```

Her faz sonunda kullanıcı onayı zorunludur. `/atlas-full` KULLANILMAZ.

## Çekirdek vs Alan-Özel Kontroller (P1-13)

CHK-01/02/04/05 gibi kontroller **çekirdek** (her çalışmada geçerli). Ancak
aşağıdakiler bu Atlas kurulumunun **örnek/alan-özel profilinden** gelir ve
farklı bir çalışma için scoper/lens-consistency/gate ajanlarında uyarlanmalıdır:

- **CHK-06 (chi-square tutarlılığı):** yalnızca χ² istatistiği kullanan
  çalışmalar için anlamlıdır. Farklı istatistiksel yöntem kullanan bir
  çalışmada bu check'in ölçütü (lens-consistency §5) o yönteme göre
  yeniden yazılmalıdır.
- **DEC-027 / §8 M1 (sentetik veri istisnası):** belirli bir çalışmanın
  sentetik-veri kararıdır; her çalışmada M1/§8 bölümü olmayabilir.
- **DEC-035 (QURAN_AYET) / DEC-036 (etik-teoloji):** teolojik alan içeren
  çalışmalara özgüdür; sinirbilim-only bir çalışmada gereksizdir.
- **SC-006 [YENİ] / CHK-07:** örnek çalışmanın kasıtlı istisna deseni.

**Yeni bir çalışma için:** scoper'ın SC-023..SC-030 esnek slotlarını
kullanarak alan-özel gereksinimleri tanımla; lens-consistency §5'i
kullanılan istatistiksel yönteme göre uyarla; DEC-035/036 gibi alan-özel
DEC'leri çalışmanın gerçek etik/teolojik durumuna göre ekle veya çıkar.

## Denetim betikleri (v5.5.4)

Hepsi proje klasöründen çalıştırılır: `bash scripts/<ad>` veya `python3 scripts/<ad>`.

| Betik | Ne denetler | Yazar mı |
|---|---|---|
| `check_integrity.sh` | FAZ0–4 varlık/boyut/içerik + gate verdict + FINAL tazelik; `--full`, FAZ3 sonrasında `cite_match.py` → `quote_ratio.py` → `declaration_check.py` denetimlerini zincirler | hayır |
| `provenance_check.py` | CHK-01 zorunlu SC-ID'ler başlık mı, CHK-02 PROVENANCE "kapsıyor" mu, CHK-05 başlık benzersizliği | hayır |
| `source_class_check.py` | SRC-01/02/03: `Kaynak Sınıfı` sütunu ve değerleri; varsa `KAYNAK SINIFLANDIRMA` sinyal-sınıf tablosuyla çelişki; tablo yoksa eski kademeli davranış | hayır |
| `fix_reconcile.py` | REC-01..06 FAZ1 bulgu ↔ FAZ2 FIX ↔ MASTER kanıt sayı/ID mutabakatı | hayır |
| `cite_match.py` | CITE-01/02/03 atıf ↔ kaynakça %100 eşleşme; `check_integrity.sh --full` zincirindedir, ayrıca tek başına çalıştırılabilir | hayır |
| `verify_doi.py` | DEC-027 istisnası dışında `[DOĞRULANMADI]` etiketi + DOI geçerliliği | hayır |
| `budget_guard.py` | token/maliyet bütçesi ($30/ay) | `--report` hariç EVET |
| `gate_merge.py` | 2A+2B'yi bağımsız yeniden hesaplayıp FINAL üretir | EVET |
| `atlas_selftest.py` | ATLAS regresyon paketi; sayı ve kimlikler `scripts/OZTEST-TABAN.json` ile pinlidir | hayır (geçici klasör) |

Değişiklikten sonra **her zaman** `python3 scripts/atlas_selftest.py` çalıştırılır;
pinli envanterin tamamı geçmeli, önceki koşuya göre sayı düşmemelidir. Son kayıtlı sonuç
depo kökündeki `docs/OLGULAR.md` makine bloğundan, canlı sonuç komut çıktısından okunur.
AUD-04 başlangıç ölçümü (03.09.2026): **125/125**, exit **0**; önceki belgede de 125 test yazıyordu.

### KAYNAK SINIFLANDIRMA tablosu (isteğe bağlı)

`PROVENANCE` tablosundaki `Kaynak` hücresinde geçen sinyalleri kaynak sınıfına
bağlayan isteğe bağlı tablo. Biçim:

| Sinyal | Sınıf |
|--------|-------|
| KURAN | BIRINCIL |
| SCHOLEM | IKINCIL |
| <kaynak-sinyali> | BIRINCIL\|IKINCIL\|UCUNCUL\|AKTARMA |

`Sinyal`, `Kaynak` hücresinde büyük/küçük harf duyarsız aranır; tabloda ilk
eşleşen sinyalin sınıfı beklenir. Tablo varsa ve aynı PROVENANCE satırındaki
`Kaynak Sınıfı` bu sınıftan farklıysa `source_class_check.py` **FAIL SRC-01**
verir. Tablo yoksa eski kademeli davranış korunur: `Kaynak Sınıfı` sütunu yoksa
`CALISTIRILMADI`, sütun varsa SRC-02 denetimi geçerlidir. Şablon ve tam örnek:
`templates/PROVENANCE-TEMPLATE.md`.

**Düzeltme notu (AUD-04, 03.09.2026):** Eski tabloda `cite_match.py` için "hariç" ve
"ayrı çalıştırılır, `check_integrity.sh --full` zincirinde değildir" yazıyordu.
Bu ifadeler `731811d` ile eklenen zinciri yansıtmıyordu. Etkin zincirin kaynağı
`scripts/check_integrity.sh` içindeki `--full` dalıdır; MASTER denetimlerinin ilk hatasında durur.
