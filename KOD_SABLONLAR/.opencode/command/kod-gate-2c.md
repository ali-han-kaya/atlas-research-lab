---
name: kod-gate-2c
description: KOD KFAZ4 — KOSULLU guvenlik oyu (kimlik/ag/kripto/bagimlilik)
agent: kod-gate-2c-security
---
# /kod-gate-2c

**Kosulludur.** Yalniz diff'te su dort yuzeyden biri gorunuyorsa calistirilir:
kimlik dogrulama · ag · kripto · bagimlilik. Kosul yoksa bu komutu calistirma
ve `FINAL` birlestirmesini 2-of-2 olarak yap.

1. `python3 scripts/secret_scan.py`
2. `python3 scripts/dep_audit.py`
3. Ikisinin de exit kodunu kanit olarak yaz. Betigi kosturamadiysan bulguyu
   `CALISTIRILMADI` yaz — "elle baktim, temiz" kanit degildir.
4. Cikti: `_KOSU/gate/KOD-gate-2c.json` (2A ile ayni sema).
5. Yer tutucu ipucu tasiyan sir bulgusunu **otomatik indirgeme**; P1'de birakip
   insana yolla.
6. Ag yasagi (`curl`/`wget`/`sh -c` ile asilabilir) teknik duvar degil
   **acik taahhuttur** — asma.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
