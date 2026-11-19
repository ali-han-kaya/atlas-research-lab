---
name: kod-teslim
description: KOD KFAZ5 — teslim ozeti ve commit mesaji TASLAGI
agent: kod-orchestrator
---
# /kod-teslim

1. `python3 scripts/kod_gate_merge.py _KOSU/gate/KOD-gate-2a.json _KOSU/gate/KOD-gate-2b.json`
   (2C cagrildiysa ucuncu dosyayi ekle). **Exit kodunu yaz.**
2. `FINAL-KOD-GATE.json` verdict'i `PASS` degilse teslim artefakti **yazilmaz**;
   `check_code_integrity.sh` bunu ITG-22 ile zaten yakalar.
3. `bash scripts/check_code_integrity.sh --full`
4. `python3 scripts/freeze_check.py` — exit 2 ise TERMINAL dur.
5. Cikti: `_KOSU/05-KFAZ-5-TESLIM.md` + commit mesaji **TASLAGI**.
6. **Commit atma.** `git commit`/`git push` izin blogunda deny'dir; bu yasagin
   `sh -c` ile asilabildigi olculmustur — teknik duvar degil, acik taahhut.
7. Kullaniciya goster, **onay bekle**.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
