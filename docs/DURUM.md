# DURUM — ÜRETİLMİŞ GÜNCEL SAYILAR

> **Bu dosya üretilmiştir; elle düzenlenmez.** Kaynak: kanonik öz-test kayıtları,
> `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` ve `SURUM.md` C15f makine bloğu;
> CI canlı koşuyla doğrular.
> Yenile: `make durum-yaz` · Bayatlık denetimi: `make durum-kontrol` (CI).

## Öz-testler (son kayıtlı canlı ölçüm; CI yeniden koşar)

| Kalem | Sonuç | Komut |
|---|---|---|
| ATLAS öz-testi | 145/145 | `python3 ATLAS_SABLONLAR/scripts/atlas_selftest.py --sessiz` |
| KOD öz-testi | 174/174 | `python3 KOD_SABLONLAR/scripts/kod_selftest.py` |

## Envanter

| Kalem | Değer | Kaynak |
|---|---|---|
| ATLAS pinli test envanteri | 145 | `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` (`sayi`) |
| ATLAS envanter kimlik hash'i | `sha256:bc2286bf172241b6cde56bf23742e1c70b1a7d396094188bdd39e5c77046bb10` | `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` (`kimlik_hash`) |
| Python dosya sayısı (H2) | 71 | `make dogrula` H2 taraması |
| Kapı lint kontrolü | 95 | `SURUM.md` C15f (`skill_lint_kontrol`) |
| Kapı envanteri | 95 | `SURUM.md` C15f (`skill_kapi_sayisi`) |
| Kapı taban kimlik | 90 | `SURUM.md` C15f (`kapi_taban_kimlik`) |
| `SKILL.md` satır | 500 | `SURUM.md` C15f (`SKILL_md_satir`) |

## Çapraz kontrol

- ATLAS: canlı 145/145 = pinli envanter 145 = OLGULAR 145 = SURUM 145
- KOD: canlı 174/174 = OLGULAR 174

Bu üç eşitlikten biri bozulursa `make durum-kontrol` kırmızı olur;
sayılar belgeye elle yazılmaz.
