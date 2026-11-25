# DURUM — ÜRETİLMİŞ GÜNCEL SAYILAR

> **Bu dosya üretilmiştir; elle düzenlenmez.** Kaynak: kanonik öz-test kayıtları,
> `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` ve `SURUM.md` C15f makine bloğu;
> CI canlı koşuyla doğrular.
> Yenile: `make durum-yaz` · Bayatlık denetimi: `make durum-kontrol` (CI).

## Öz-testler (son kayıtlı canlı ölçüm; CI yeniden koşar)

| Kalem | Sonuç | Komut |
|---|---|---|
| ATLAS öz-testi | 146/146 | `python3 ATLAS_SABLONLAR/scripts/atlas_selftest.py --sessiz` |
| KOD öz-testi | 174/174 | `python3 KOD_SABLONLAR/scripts/kod_selftest.py` |

## Envanter

| Kalem | Değer | Kaynak |
|---|---|---|
| ATLAS pinli test envanteri | 146 | `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` (`sayi`) |
| ATLAS envanter kimlik hash'i | `sha256:03acd842a198ba5cdf9ff0a3ec902693cc471bf070226fff387020038a30327c` | `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` (`kimlik_hash`) |
| Python dosya sayısı (H2) | 82 | `make dogrula` H2 taraması |
| Kapı lint kontrolü | 95 | `SURUM.md` C15f (`skill_lint_kontrol`) |
| Kapı envanteri | 95 | `SURUM.md` C15f (`skill_kapi_sayisi`) |
| Kapı taban kimlik | 90 | `SURUM.md` C15f (`kapi_taban_kimlik`) |
| `SKILL.md` satır | 500 | `SURUM.md` C15f (`SKILL_md_satir`) |

## Çapraz kontrol

- ATLAS: canlı 146/146 = pinli envanter 146 = OLGULAR 146 = SURUM 146
- KOD: canlı 174/174 = OLGULAR 174

Bu üç eşitlikten biri bozulursa `make durum-kontrol` kırmızı olur;
sayılar belgeye elle yazılmaz.
