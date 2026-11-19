---
name: kod-faz3
description: KOD KFAZ3 — test kaniti (makine karar verir)
agent: kod-tester
---
# /kod-faz3

1. `kod_profil.json` icindeki `test_komutu`'nu **oldugu gibi** calistir.
   Filtre ekleme, `-k` ile daraltma, komutu degistirme.
2. Cikis kodunu ve makine okunur raporu kaydet.
3. Cikti: `_KOSU/03-KFAZ-3-TEST-EVIDENCE.json` — `sonuc` alanini **raporu
   okuyarak** doldur, hatirlayarak degil.
4. `python3 scripts/test_attest.py` — bu betik senin beyanini KULLANMAZ,
   JUnit XML'i bagimsiz ayristirir ve beyaninla karsilastirir. Uyusmazlik
   `EVIDENCE_UNVERIFIED` = P0'dir. **Exit kodunu yaz.**
5. Sonucu **duzeltmeye calisma**. Kirmizi ise kirmizi bildir.
6. `test_rapor_formati` `yok` ise `CALISTIRILMADI` yaz ve `OLCULMEYEN` ac.
   "Elle bakildi, geciyor" kanit degildir.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
