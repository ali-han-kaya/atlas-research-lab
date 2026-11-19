---
name: kod-faz1
description: KOD KFAZ1 — tasarim plani ve dondurulacak bolgeler
agent: kod-architect
---
# /kod-faz1

1. `_KOSU/00-*` sozlesmesini oku. REQ listesini **say** ve sayiyi yaz.
2. `kod-architect` ajanini calistir.
3. Cikti: `_KOSU/01-KFAZ-1-DESIGN-PLAN.md` — gomulu ```json blogunda
   `degisecek`, `dondurulan`, `req_test`, `req_dosya`, `gerekce`.
4. Davranissal her REQ **tabanda OLMAYAN** bir test adina baglanmali.
   Taban adlari `_KOSU/gate/BASELINE.json` -> `test_adlari`. **Oku, hatirlama.**
5. `python3 scripts/chg_reconcile.py --faz KFAZ1` — RECK-01 ve RECK-07
   simdiden temiz olmali. **Not (OLCUM-02 K10):** betik eskiden KFAZ2
   artefaktini KOSULSUZ istiyordu ve KFAZ2 tanim geregi henuz yoktu;
   bu faz ASLA exit=0 alamiyordu. Artik `--faz` ile (ya da artefaktlardan
   cikarimla) sirasi gelmemis artefakt P1 CALISTIRILMADI sayilir.
6. `python3 scripts/freeze_check.py` — dondurulan dosyalarin SHA256'si tabana islendi mi.
7. `bash scripts/check_code_integrity.sh`
8. Kullaniciya goster, **onay bekle**. Onaysiz KFAZ2'ye gecme.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
