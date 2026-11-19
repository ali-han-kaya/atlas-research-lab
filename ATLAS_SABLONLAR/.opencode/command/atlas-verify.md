---
name: atlas-verify
description: Atlas v5.5 Tam Dogrulama
agent: atlas-orchestrator
---
# /atlas-verify

1. `python3 scripts/verify_doi.py --require-master`
2. `python3 scripts/provenance_check.py`
3. `bash scripts/check_integrity.sh --full`
4. `python3 scripts/budget_guard.py --report`
5. Yukaridaki 4 komutun tam stdout ciktisini topla; her biri icin PASS/FAIL
   durumunu ozetle. Asagidaki formatta `05-VERIFICATION-REPORT-v5.5.md`
   dosyasini YAZ (bu adim atlanamaz, rapor kendiliginden olusmaz):

   ```
   # VERIFICATION REPORT v5.5.4
   ## verify_doi.py: PASS|FAIL
   <ilgili stdout ozeti>
   ## provenance_check.py: PASS|FAIL
   <ilgili stdout ozeti>
   ## check_integrity.sh --full: PASS|FAIL
   <ilgili stdout ozeti>
   ## budget_guard.py --report: OK|FAIL
   <ilgili stdout ozeti>
   ## GENEL SONUC: PASS|FAIL
   ```
6. `ls -la 05-VERIFICATION-REPORT-v5.5.md` ile dosyanin gercekten yazildigini dogrula.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `NOT_EXECUTED: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
