---
name: atlas-faz1
description: Atlas v5.5 FAZ1 — Lens Swarm
agent: atlas-orchestrator
---
# /atlas-faz1

1. `wc -c 00-FAZ-0-*.md` — token tahmini: ≤50K SINGLE, >50K PAIRWISE
2. 3 lens paralel:
   - `atlas-lens-structure` (GLM 5.3) → structure JSON
   - `atlas-lens-consistency` (DeepSeek V4 Pro) → consistency JSON
   - `atlas-lens-editor` (Claude Opus 5) → editor JSON
3. Ham JSON'lari al, celişen bulgulari tara (ayni konumda farkli severity)
4. Çelişkileri orchestrator cozer — kanit agirligi, lens cogunlugu DEGIL
5. Birlesik bulgu listesini `01-FAZ-1-LENS-ANALYSIS.json` olarak yaz
6. `bash scripts/check_integrity.sh --faz1`
7. `python3 scripts/budget_guard.py`
8. Bulgulari P0 > P1 > P2 sirasiyla goster, otomatik uygulama YAPMA.

## KAPANIS — atlanamaz (fail-closed)

1. Yukarida cagirdigin HER komutun **exit kodunu** yaz.
2. Biri 0 degilse "tamamlandi" YAZMA. Sunu yaz ve dur:
   `DURDU — <komut> exit=<kod> · ilk FAIL satiri: <satir>`
3. `ls -la <uretilen dosya>` ile ciktinin gercekten olustugunu goster.
   Rapor kendiliginden olusmaz; yazmadiysan yazilmamistir.
4. Calistiramadigin kontrol icin `NOT_EXECUTED: <neden>` yaz.
   **Calistirmadigin bir kontrolu gecmis sayma.**
5. `OLCULMEYEN:` satirini doldur — bos birakilamaz.
