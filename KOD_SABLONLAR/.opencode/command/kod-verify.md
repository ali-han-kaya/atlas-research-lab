---
name: kod-verify
description: KOD — butun makine kapilarini sirayla kosturur, karar vermez
agent: kod-orchestrator
---
# /kod-verify

Butun makine kapilarini sirayla kostur ve **her birinin exit kodunu tabloya yaz**.
Hicbirini yorumlama, hicbirini atlama.

```
bash   scripts/check_code_integrity.sh --full
python3 scripts/freeze_check.py
python3 scripts/perm_lint.py
python3 scripts/chg_reconcile.py
python3 scripts/test_attest.py
python3 scripts/api_surface.py
python3 scripts/secret_scan.py
python3 scripts/dep_audit.py
python3 scripts/kod_selftest.py
bash    scripts/kur.sh . --dogrula
```

`secret_scan.py` **exit=3** = KISMI mod (toolkit yok). Tabloya `3` yaz ve
`OLCULMEYEN` kaydi ac; `0` ile karistirma.

Tablo su bicimde olsun:

| Kapi | Komut | exit | Ozet satiri |
|---|---|---|---|

`freeze_check.py` **2** dondurdugunde tabloyu tamamla ama sonuna sunu yaz ve dur:
`GATE_TAMPERED — TERMINAL. Hat durdu, dongu sayaci artmadi.`

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
