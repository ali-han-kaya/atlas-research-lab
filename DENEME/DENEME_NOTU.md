# DENEME_NOTU — bu koşu KUSURLUDUR, bilerek saklanmıştır

Sürüm: v1 · Tarih: 23 Ağustos 2026 · Durum: **DONDURULDU — düzeltilmeyecek**

## Neden saklandı

Bu koşu kusurlu: `02-FAZ-2-FIX-MANIFEST.md` 8 FIX'i "UYGULANMIŞ" ilan etti, ama
MASTER'a yalnız 2'si yansımıştı. Buna rağmen `check_integrity.sh --full`
`FULL PASS v5.5.2` verdi. **FULL PASS yanlış pozitifti.** Denetim dersi olarak
saklandı; düzeltilirse ders kaybolur.

## Kanıt (23 Ağustos 2026 denetimi)

| Kanıt | Yer |
|---|---|
| Manifesto 8 FIX, hepsi UYGULANMIŞ | `02-FAZ-2-FIX-MANIFEST.md` düzeltme tablosu |
| MASTER "FIX-001 ve FIX-002 uygulanmıştır" der | `03-FAZ-3-MASTER-v5.5.md:84` |
| MASTER'da yalnız FIX-001, FIX-002 geçer | `grep -o 'FIX-[0-9]\{3\}' 03-FAZ-3-MASTER-v5.5.md` |
| FIX-007/008'in iddia ettiği ifadeler yok | "seçim önyargısı" 0, "elle müdahale" 0, "veri envanteri" 0 eşleşme |
| Kapı yine de PASS dedi | `gate/STRONG-gate-2b-v5.5.json` → 8/8 `UYGULANMIŞ_KANITLI` |
| Bütün zincir PASS | `bash scripts/check_integrity.sh --full` → `FULL PASS v5.5.2` |

## Kök neden

`gate_merge.py` ajanın **sayı** beyanına güvenmez (iyi), ama **kanıt** beyanını
doğrulayamaz. 2B "8/8 kanıt MASTER'da görünür" yazdı; hiçbir makine bunu
denetlemedi. Sayı mutabakatı kör noktasıydı.

## Alınan önlem

`scripts/fix_reconcile.py` yazıldı (v1.2): FAZ1 bulgu ↔ FAZ2 FIX ↔ MASTER kanıt
sayı ve ID mutabakatını makine ile denetler; `check_integrity.sh --faz3`'e
bağlandı. Bu koşu üzerinde çalıştırılırsa **FAIL vermelidir** — regresyon testi
olarak kullanılabilir.

## Uyarı

- `DENEME/scripts/` bu tarihte donduruldu; `ATLAS_SABLONLAR/scripts/` sonradan
  güncellendi. İkisi artık **bilerek** farklıdır. Güncel betikler için
  `ATLAS_SABLONLAR/scripts/` kullanılır.
- Bu klasördeki hiçbir dosya şablon olarak kopyalanmaz.
