---
name: atlas-faz2
description: Atlas v5.5 FAZ2 — Fixer
agent: atlas-orchestrator
---
# /atlas-faz2

1. `01-FAZ-1-LENS-ANALYSIS.json` oku
2. Her P0/P1 bulgu icin FIX-XXX (ardisik, benzersiz) olustur
3. Kullaniciya sor: "Hangi FIX'ler uygulansin?" (evet/hayir)
4. Uygulanan her FIX icin: MASTER'da once→sonra alinti kaniti
5. `02-FAZ-2-FIX-MANIFEST.md` yaz:
   | FIX-ID | CHK-Kaynak | Aciklama | Severity | Durum | Kanit |
6. `bash scripts/check_integrity.sh --faz2`
7. Kullaniciya goster, onay bekle.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `NOT_EXECUTED: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
