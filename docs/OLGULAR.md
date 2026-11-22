# OLGULAR — TEK KAYNAK SAYISAL TABLO (tohum v1)

**Amaç:** Makale ve SURUM’daki sayısal olgular düzyazıda değil burada yaşar. Çelişki çıkarsa bu tablo kazanır. Her satır birincil kayda bağlıdır.

| # | Olgu | Değer | Birincil kayıt | Son teyit | Durum |
|---|---|---|---|---|---|
| 1 | Fatḥ al-Bārī Salafiyya XI noyau | 349-355 (noyau 351-352) | Shamela kütüphanesi + islamweb (باب التواضع) | 28.08.2026 | DOĞRULANDI (dijital) |
| 2 | Fatḥ al-Bārī Dār al-Maʿrife XI | 341-344 | Dār al-Maʿrife baskısı | 28.08 | NOT: Salafiyya ile karıştırılmamalı |
| 3 | Fatḥ al-Bārī metin aralığı (FATH-PAGE revizyonu) | 340-347 (metin 340-341, çekirdek 344-345) | VERIFIED_ISSUES v1.7.64 (Shamela 6712 ص340, 6713 ص341, 6716 ص344) | 29.08 | ÖNERİ — basılı foto bekleniyor |
| 4 | Toplam hakem model sayısı (TUR2) | 14 model | `docs/DEVIR-2026-08-26-2230.md` — OpenRouter 14/14 rapor, $2.119 | 26.08 | DOĞRULANDI |
| 5 | Şablon minimum eşiği | 2 model yeter | `HAKEM_BRUTAL:170` | — | ŞABLON KURALI |
| 6 | Makale kelime sayısı (ANONYME) | 6254 kel (190 satır) | `docs/VERIFIED_ISSUES` kanon hash 25764929… | 29.08 | DOĞRULANDI |
| 7 | Teslim bütünlüğü | SHA 21/21 OK | `14_LIVRAISON/SHA256SUMS.txt` + `shasum -c` | 30.08 | DOĞRULANDI |
| 8 | Atlas öz-test | 68/68 PASS | `atlas_selftest.py` 30.08 | 30.08 | DOĞRULANDI |
| 9 | Toolkit öz-test | 37/39 ENGEL_VAR | `v4_selftest.py` 30.08 (SP-7, TUT-1) | 30.08 | AÇIK |
| 10 | Maliyet denge profili (tahmin) | ~$2.3 | `routing.profiles.json` denge | 23.08 | TAHMİN — canlı ATLAS ölçümü yok |
| 11 | Maliyet TUR2 gerçek | $2.119 (14 model) | `DEVIR-2026-08-26-2230` | 26.08 | DOĞRULANDI |
| 12 | Maliyet OLCUM-07 | tahmin $0.82 → gerçek $1.15 | `OLCUM-07:124` | 26.08 | %40 sapma, DOĞRULANDI |

**Kural:** Bu tablo dışındaki sayısal beyanlar bu tabloya referans vermeli. Yeni sayısal olgu eklenirse bu tabloya satır eklenir.

**Sonraki eklenecekler (tohum):** Lumbard/Anjum DOI’leri, Ibn Manẓūr/Mufradāt sayfaları, Qušayrī/Iḥyāʾ locator’ları, Rāzī 2:165/5:54 doğrulaması.

## KAMU AĞACI KANITI — OLG-1

`OLG-1` artık dış labın tarihsel commit listesini aramaz. Tek makine kanıtı
bu kamu ağacındaki `attestation.json` dosyasıdır; `olgu_lint`, onu
`tools/kanit_dogrula.py` ile gerçek commit/tree ve dosya hash'leri üzerinden
doğrular. Dosya yoksa veya bozuksa sonuç **FAIL** olur; başka bir kanıt
kaynağına düşmez.

Eski tarihsel taban commit alanı, mekanizma sayacı ve mekanizma listesi makine
bloğundan çıkarıldı. Yukarıdaki tarihsel tablo ve `DERSLER` içindeki eski
hash atıfları silinmedi; bunlar arşiv kaydıdır, `OLG-1` kanıtı değildir.

## MAKİNE-OKUNUR KAYIT

Bu tek ve katı JSON bloğu `olgu_lint.py` tarafından okunur. Tarihsel tablo lint girdisi değildir.

<!-- OLGULAR_JSON_BASLA -->
```json
{
  "schema": "OLGULAR/v2",
  "lab_surum": "v1.7.419",
  "kamu_kaniti": "attestation.json",
  "atlas_envanter_sayisi": 145,
  "atlas_son_gecen": 145,
  "kod_son_gecen": 174,
  "attest_canli": 134,
  "attest_taban": 134,
  "attest_p0": 0,
  "attest_p1": 0
}
```
<!-- OLGULAR_JSON_BITIR -->
