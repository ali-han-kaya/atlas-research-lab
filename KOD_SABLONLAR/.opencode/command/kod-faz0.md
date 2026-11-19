---
name: kod-faz0
description: KOD KFAZ0 — kapsam, kabul olcutu, taban cizgisi
agent: kod-scoper
---
# /kod-faz0

1. Kullaniciya sor: "Ne insa edilecek? Hangi depo, hangi giris modu
   (`YESIL_SAHA` / `MEVCUT_KOD`)?"
2. `python3 scripts/budget_guard.py --preflight KFAZ0` — exit 0 degilse **DUR**.
   (OLCUM-02 K3: bu komut eskiden `bilinmeyen faz 'KFAZ0'` deyip exit=1
   veriyordu ve hat ILK MAKINE KOMUTUNDA duruyordu. Duzeltildi.)
   Kurulum eksikse once `bash scripts/kur.sh <hedef> --dogrula` kostur.
3. `kod-scoper` ajanini calistir.
4. Uc artefakt: `_KOSU/00-KFAZ-0-SPEC-CONTRACT-ve-REGISTER.md` (gomulu
   ```json makine blogu ZORUNLU) · `_KOSU/gate/BASELINE.json` · `kod_profil.json`
5. `MEVCUT_KOD` modunda tabani **olcerek** doldur: test komutunu calistir,
   cikis kodunu ve JUnit XML'i kaydet, SHA256'lari hesapla.
6. `python3 scripts/api_surface.py --json` — `kademe` T1 degilse dis imza
   envanteri olumlu karar **uretemez**, `DUSUK_GUVEN` notu dus.
7. `bash scripts/check_code_integrity.sh`
8. Kullaniciya goster, **onay bekle**. Onaysiz KFAZ1'e gecme.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
