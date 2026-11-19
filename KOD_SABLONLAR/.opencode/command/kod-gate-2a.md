---
name: kod-gate-2a
description: KOD KFAZ4 — kapi 2A kor denetim
agent: kod-gate-2a
---
# /kod-gate-2a

1. Bu ajan plani ve manifesti **okuyamaz** (teknik blok, ricadan ibaret degil).
   Elindekiler: `_KOSU/00-*` sozlesmesi ve `git diff HEAD`.
2. Tek soru: **bu kod, sozlesmedeki kabul olcutlerini karsiliyor mu?**
3. Cikti: `_KOSU/gate/KOD-gate-2a.json`
4. Her `checks` kaydinin `evidence` alani ZORUNLU: birebir alinti ya da
   komut+cikti+exit kodu. `GECTI` + bos kanit = P0.
5. Uc dizi de bossa kapi PASS **veremez** (`NO_INSPECTION_EVIDENCE`).
6. `python3 -c "import json;json.load(open('_KOSU/gate/KOD-gate-2a.json'))"` —
   exit kodunu yaz; bozuk JSON kapi yok demektir.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
