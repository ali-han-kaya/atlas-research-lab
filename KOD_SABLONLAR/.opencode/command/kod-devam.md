---
name: kod-devam
description: KOD — yarim kalan kosuya artefaktlardan devam et
agent: kod-orchestrator
---
# /kod-devam

1. `ls -la _KOSU/ _KOSU/gate/` — hangi artefaktlar var, **listele**.
2. Kalinan fazi **artefakt adlarindan** cikar, tahmin etme:
   `00-*` var `01-*` yok -> KFAZ1'desin, ve boyle devam.
3. `_KOSU/gate/DONGU.json` varsa tur sayisini oku. Ayni bulgu kimligi iki turda
   **siddeti dusmeden** goruluyorsa hat durur, karar insana gider.
4. `bash scripts/check_code_integrity.sh --full` ve
   `python3 scripts/freeze_check.py` — ikisinin exit kodunu yaz.
   Devam etmeden once zincirin saglam oldugunu **kanitla**.
5. `python3 scripts/budget_guard.py --report` — kalan butceyi yaz.
6. Sonra tam olarak sunu yaz ve **DUR**:
   `KALINAN FAZ: KFAZ<n> · SIRADAKI: /<komut> · DONGU: <n>/3`

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
