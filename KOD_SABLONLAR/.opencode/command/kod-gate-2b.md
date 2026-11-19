---
name: kod-gate-2b
description: KOD KFAZ4 — kapi 2B manifest dogrulama
agent: kod-gate-2b
---
# /kod-gate-2b

1. Bu ajan 2A ve 2C ciktilarini **okuyamaz**. Ayni kaynagi okuyan iki kapi
   tek kapidir; `kod_gate_merge.py` birebir ayni icerigi
   `IDENTICAL_GATE_INPUTS` = P0 sayar.
2. Her `CHG-XXX` icin `git diff HEAD -- <dosya>` calistir, exit kodunu ve
   ilgili satirlari kanit olarak yaz.
3. Cikti: `_KOSU/gate/KOD-gate-2b.json` — `manifest_reconciliation` dizisi
   **ve** `checks` dizisi. ZORUNLU SEMA asagidadir; alan adlari birebir.
4. `UYGULANMIS_KANITLI` demek **iddiadir ve denetlenir**: RECK-04 o CHG'nin
   dosyasini diff'te arar, bulamazsa P0 **senin kapina** yazilir.
5. `python3 scripts/chg_reconcile.py` — exit kodunu yaz.

## ZORUNLU SEMA

> **O4-02 (OLCUM-04, 24.08.2026) — `checks[i].status` ZORUNLUDUR.** Canli kosuda
> glm-5.3 `checks` girdilerini `status` alani OLMADAN yazdi; `ortak_gate.py`
> her kaydi "durum alani YOK -> P0" saydi, **10x P0** cikti ve senin beyan
> ettigin PASS, FINAL'de FAIL'e cevrildi. Katmanli savunma calisti ama kapin
> bosa kostu. Her `checks` kaydi UC alani da tasimak zorundadir:

```json
{
  "kapi": "2B",
  "verdict": "PASS|FAIL",
  "checks": [
    {"id": "MR-01", "status": "GECTI", "kanit": "git diff HEAD -- birim/olcek.py exit=0, +2 satir"},
    {"id": "MR-02", "status": "KALDI", "kanit": "CHG-002 dosyasi diff'te YOK"}
  ],
  "manifest_reconciliation": [
    {"chg_id": "CHG-001", "status": "UYGULANMIS_KANITLI|KANITSIZ|UYGULANMAMIS",
     "evidence": "git diff ciktisindan birebir satir"}
  ],
  "findings": [],
  "metadata": {"p0_count": 0, "p1_count": 0}
}
```

**Kapali listeler (`ORTAK/scripts/ortak_gate.py:42-43`):**
`checks[i].status` -> gecer: `GECTI` `GECER` `PASS` `PASSED` `OK` `TAMAM` ·
kalir: `KALDI` `FAIL` `FAILED` `HATA` `RED` · olculemedi: `CALISTIRILMADI` (P1).
Bu listelerin **disindaki** her deger P0'dir; alanin **yoklugu** da P0'dir.
`kanit` alani bos birakilirsa kayit denetlenemez — kanitsiz `GECTI` yazma.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `CALISTIRILMADI: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
