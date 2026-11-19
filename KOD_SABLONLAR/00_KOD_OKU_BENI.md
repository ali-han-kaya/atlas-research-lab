# KOD/ÜRÜN HATTI — oku beni

Bu hat **üretir**, sonra denetler. ATLAS hattı ise kullanıcının verdiği taslağı
**denetler ve sertleştirir**. İki hattın fazları bu yüzden ters sıradadır ve kod
hattında akademik hatta hiç olmayan bir artefakt zorunludur: **taban (BASELINE)**.

## İzin mimarisi — ÖLÇÜLMÜŞ davranışa dayanır

`docs/OLCUM-01-IZIN-GLOB.md` (paket dışı, özeti yukarıda) şunu ölçtü: opencode kuralları **`findLast`** ile
değerlendirir (en son eşleşen kazanır) ve birleştirme sırası şudur:

    yerleşik varsayılan  →  opencode.json `permission`  →  ajanın kendi bloğu

Bu yüzden kırmızı çizgiler **`opencode.json`'da** durur ve ajanlar `read` altına
`"*"` **yazmaz** — yazsalardı kendi `"*": allow` satırları global yasakları
öldürürdü (genel kural). **İstisna:** `kod-gate-2a` kör denetimi `read: "*": allow` + dar deny listesi ile çalışır — körlük için gerekçeli istisna (ÖLÇÜM-02 K14, körlük gönüllü kalmıştı). `edit` altına `"*": allow` yazmak zorunda olan tek iki ajan
(`kod-implementer`, `kod-implementer-heavy`) yasakları **kendi bloklarında
tekrarlar**. Bu tekrar süs değildir; glob'lar miras alınmaz.

`perm_lint.py` bu kuralları makine olarak denetler (PERM-01..08).

## HATTI KİM SÜRER — ajanlar için tek kural  (ÖLÇÜM-03 O3-02)

Hattı **dışarıdan bir operatör** sürer. Bir faz ajanı olarak sen:

- `scripts/kos_faz.sh`'i **çağırmazsın**. Onu çağıran betik zaten seni çalıştırdı.
- `opencode run`'u **çağırmazsın** (`--command`, `--agent`, hiçbir biçimde).
- Bir sonraki fazı **başlatmazsın**. Kendi artefaktını yazar, kapanış
  disiplinini uygular ve **durursun**.

Bunu ihlal eden çağrı özyinelemeye ve kota tükenmesine yol açar; `kos_faz.sh`
artık yeniden girişi makine olarak reddeder (`KOD_KOS_FAZ_AKTIF`, exit=66).

Kurulum ve sürme komutlarının tamamı `OPERATOR_SURME.md`'dedir — o dosya
bilerek `instructions` dışındadır ve senin bağlamına yüklenmez.

## Fazlar

| Faz | Ad | Ajan | Çıktı | İnsan onayı |
|---|---|---|---|---|
| KFAZ0 | KAPSAM & KABUL | `kod-scoper` | `_KOSU/00-…md` + `gate/BASELINE.json` + `kod_profil.json` | **EVET** |
| KFAZ1 | TASARIM & DONDURMA | `kod-architect` | `_KOSU/01-…md` | **EVET** |
| KFAZ2 | UYGULAMA | `kod-implementer` | kod diff + `_KOSU/02-…md` | hayır |
| KFAZ3 | KANIT | `kod-tester` | `_KOSU/03-…json` | hayır (makine karar verir) |
| KFAZ4 | ÇİFT/ÜÇLÜ KAPI | `kod-gate-2a/2b/2c` + `kod-gate` | `gate/*.json` + `FINAL-KOD-GATE.json` | koşullu (P0 varsa) |
| KFAZ5 | TESLİM | `kod-orchestrator` | `_KOSU/05-…md` + commit mesajı **taslağı** | **EVET** |

`/kod-full` **yoktur** ve yazılmayacaktır — `/atlas-full`'ün kasten yokluğuyla
aynı gerekçe: tek komutla baştan sona koşan bir hat, insan onay noktalarını
törensel hale getirir.

- **Maliyet notu:** Yerel batarya (`atlas_selftest`/`kod_selftest`) **$0** (model koşusu yok); canlı KOD koşusu `denge` ~$2.3 (OpenRouter, `routing.profiles.json` faz_maliyet 9 girdi) — SNIP `maliyet` yalnız yerel bataryayı anlatır.

| Config | Model sabiti | Kullanım | Maliyet |
|---|---|---|---|
| Lab kökü `opencode.json` | YOK (kullanıcı varsayılanı) | yerel batarya | $0 |
| `KOD_SABLONLAR/opencode.json` | `deepseek-v4-flash` sabit | canlı KOD koşusu | `denge` ~$2.3 |

## Makine bloğu zorunluluğu

KFAZ0/1/2 artefaktları `.md`'dir ama her biri gövdesinde bir ` ```json ` bloğu
taşımak **zorundadır**. `chg_reconcile.py` markdown tablosu ayrıştırmaz:
sessiz yanlış okuma bu labda P0'dır. Blok yoksa kontrol `CALISTIRILMADI` sayılır.

## `secret_scan` KISMI modu — exit=3  (ÖLÇÜM-02 K4)

Kalıp listesi `KOMUT_TOOLKIT_v4`'ten gelir ve **kopyalanmaz**. Toolkit hedef
depoda yoksa betik eskiden exit=1 ile duruyordu ve KFAZ2 yapısal olarak
kapalıydı. Artık kaynak üç yoldan bildirilebilir:

```
python3 scripts/secret_scan.py --v4 <yol>
V4_VERIFY_YOLU=<yol> python3 scripts/secret_scan.py
# ya da kod_profil.json içinde: "v4_verify_yolu": "<yol>"
```

Bulunamazsa **KISMI mod**: yalnız yapısal göstergeler (gerçek `.env`, özel
anahtar başlığı) taranır ve **exit=3** döner. `3` "temiz" DEĞİLDİR — tam tarama
koşmadı demektir ve `OLCULMEYEN` kaydı açılmalıdır. `0` yalnız TAM tarama
koştuğunda döner.

## Kalan risk — açıkça yazılıdır

Boş gövdeli, her zaman geçen bir test bütün kapıları geçer. Hat testin
**yokluğunu** ölçer, **boşluğunu** ölçmez. `RECK-07` yeni davranışı tabanda
olmayan bir test adına bağlayarak riski daraltır, sıfırlamaz.

ÖLÇÜM-02 K18 bunu genişletti: hat testin **koşmuş olmasını** da ölçmüyordu —
elle uydurulmuş bir JUnit XML `test_attest.py`'yi geçiyordu. `TST-10` (rapor
kaynaktan eski olamaz), `TST-11`/`TST-12` (kanıttaki komut ve rapor yolu
`kod_profil.json` ile eşleşmeli) bu boşluğu **daraltır**. Sıfırlamaz: raporu
uydurup profili de tutarlı yazan bir saldırgan geçebilir — ama o değişiklik
`freeze_check` FRZ-01 `GATE_TAMPERED`'a takılır. Savunma katmanlıdır.

`bash` deny kalıpları **aşılabilir** (`/bin/rm`, `sh -c "…"`; ÖLÇÜM 01 §8 canlı
kanıt). Bash yasağı danışmandır, kapı değildir. Gerçek sınır `edit`/`read`
izinleri ve makine kapılarıdır.
