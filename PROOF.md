# PROOF — ATLAS KANIT ÖZETİ

> Bu dosya üretilmiştir; elle düzenlenmez. Kaynak: `attestation.json`,
> canlı doğrulama komutları ve son `dogrula.yml` CI koşusu.
> Yenile: `make proof`.

## Kanıtlanan ağaç

| Alan | Değer |
|---|---|
| Commit | `49d040063270b10b1f969388aef965e267d23b14` |
| Tree | `69892b0f2455cb454c3a45891d064dd8f5ed78eb` |
| Tree SHA-256 | `1804d6753d1efc7002d3bf87e1bf45b36d7adf2b17a9d4ba3cf1a26ccc4ccb53` |
| İzlenen dosya | 304 |
| Kanıt zamanı | `2026-11-27T14:01:13Z` |

> Üretim anındaki HEAD: `49d040063270` — attestation ile aynı.

## Doğrulama komutları

| Komut | Hüküm | Süre | Özet |
|---|---|---|---|
| `make dogrula` | **PASS** (rc=0) | 236.0 s | HUKUM: PASS — 8/8 kalem gecti |
| `make kanit-dogrula` | **PASS** (rc=0) | 7.1 s | PASS KANIT commit=49d040063270b10b1f969388aef965e267d23b14 tree=69892b0f2455cb454c3a45891d064dd8f5ed78eb dosya=304 tree_sha256=1804d6753d1efc7002d3bf87e1bf45b36d7adf2b17a9d4ba3cf1a26ccc4ccb53 |
| `make iddia` | **PASS** (rc=0) | 222.4 s | HUKUM: PASS — 42/42 olculen iddia ham kanitiyla beyanla ayni |

## CI durumu

| Alan | Değer |
|---|---|
| İş akışı | `dogrula` |
| Hüküm | **success** |
| Koşu | [`45994842220`](https://github.com/ali-han-kaya/atlas-research-lab/actions/runs/45994842220) |
| Commit | `2e3c666bb2a26e04cf11fece9000e6163671733b` |
| Zaman | `2026-11-27T11:58:56Z` |
| Bu kanıt commit'ini kapsıyor | **HAYIR** |

## Neyin ölçüldüğü

- Yukarıdaki doğrulama komutlarının tamamı canlı koşuldu ve `PASS` döndü.
- `attestation.json`, 304 izlenen dosyayı ve ağaç SHA-256'sını kapsıyor.

## Neyin ölçülmediği

- Son CI koşusu bu commit'i kapsamıyor; koşu `2e3c666bb2a26e04cf11fece9000e6163671733b` commit'ine ait.
- Bu komutlar tarayıcı/UI, harici ağ servisleri, farklı işletim sistemleri veya temiz klon kurulumunu ölçmez.

