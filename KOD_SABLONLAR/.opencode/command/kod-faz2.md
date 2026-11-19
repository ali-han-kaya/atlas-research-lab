---
name: kod-faz2
description: KOD KFAZ2 — uygulama, yalniz plandaki dosyalar
agent: kod-implementer
---
# /kod-faz2

1. `_KOSU/01-*` planindaki `degisecek` listesini oku ve **birebir yaz**.
   Bu liste bir izin listesidir; disina cikan her dosya `SCOPE_VIOLATION` = P0.
2. `python3 scripts/freeze_check.py` — exit **2** ise `GATE_TAMPERED`,
   hat TERMINAL durur, dongu sayaci artmaz.
3. `kod-implementer` ajanini calistir. >20 dosya ya da >200K baglam ise
   plan bunu yaziyorsa `kod-implementer-heavy` kullan; **kendi kararinla gecme**.
4. Cikti: kod diff + `_KOSU/02-KFAZ-2-CHANGE-MANIFEST.md` (gomulu makine blogu).
5. `python3 scripts/chg_reconcile.py`
6. `python3 scripts/secret_scan.py`
   Cikis kodlari: `0` TAM tarama temiz · `1` bulgu var · **`3` KISMI mod**
   (toolkit bulunamadi, yalniz yapisal gostergeler tarandi). `3` 'temiz'
   DEGILDIR: `OLCULMEYEN` kaydi ac ve devam edip etmeyecegini insana sor.
   Toolkit yolunu `--v4`, `V4_VERIFY_YOLU` ya da `kod_profil.json`
   icindeki `v4_verify_yolu` ile bildirebilirsin (OLCUM-02 K4).
7. Insan onayi **gerekmez**; dogrudan KFAZ3'e gecilir. Ama exit kodlari 0 degilse
   gecme — kusurlu manifesti kapiya gonderme.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
