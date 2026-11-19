---
name: atlas-faz0
description: Atlas v5.5 FAZ0 — Kapsam Sozlesmesi
agent: atlas-scoper
---
# /atlas-faz0

1. Kullaniciya sor: "Ne yazacaksin? 7 alan nasil baglaniyor?" (1-2 cümle RQ)
2. `atlas-scoper` ajanini calistir (Claude Opus 5)
3. Cikti: `00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md`
4. `python3 scripts/scope_profile_check.py` — ALAN_PROFILI beyani ve profil disi
   ZORUNLU ID denetimi (B-1). Exit kodunu yaz; 0 degilse SCOPE'u duzelt.
5. `bash scripts/check_integrity.sh --faz0`
6. `python3 scripts/provenance_check.py`
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
