# Atlas v5.5 — Agent Roster

## Ajanlar — temel kadro ve P1-7 paneli

AUD-04 duzeltmesi (03.09.2026): Eski "9 calisan + 3 deprecated" basligi panel rollerini
icermiyordu. Tam dosya envanteri `.opencode/agent/` altindadir; bu tablo rol rehberidir.
Dosya sutunundaki yollar bu dizine gorelidir. Model eslemelerinde kaynak
`routing.profiles.json` icindeki `profiller.<profil>.<ajan>` alani, uygulanan modelde
ilgili ajan dosyasinin `model:` satiridir. Tablodaki eski sabit model adlari tarihsel kayittir.

| Agent | Model | Rol | Dosya |
|-------|-------|-----|-------|
| **Orchestrator** | Claude Opus 5 | Pipeline beyni, tum FAZ'leri koordine eder | `atlas-orchestrator.md` |
| **Scoper** | Claude Opus 5 | FAZ0 — kapsam sozlesmesi, 30 SCOPE-ID, DEC-REGISTER | `atlas-scoper.md` |
| **Writer Master** | Claude Opus 5 | FAZ3 — MASTER belgesini yazar | `atlas-writer-master.md` |
| **Structure Lens** | GLM 5.3 | FAZ1 — yapisal butunluk, CHK-01..07, tablo/CSV/JSON | `atlas-lens-structure.md` |
| **Consistency Lens** | DeepSeek V4 Pro | FAZ1 — sayisal/terminolojik/mantiksal/istatistiksel tutarlilik | `atlas-lens-consistency.md` |
| **Editor Lens** | Claude Opus 5 | FAZ1 — akademik dil, APA 7, atif, jargon, intihal | `atlas-lens-editor.md` |
| **Gate 2A** | DeepSeek V4 Pro | FAZ4 — kor denetim, FIX gormez, CHK-01..07 | `atlas-gate-2a.md` |
| **Gate 2B** | GLM 5.3 | FAZ4 — manifest dogrulama, FIX kanit arar | `atlas-gate-2b.md` |
| **Gate Orchestrator** | Claude Opus 5 | FAZ4 — 2A+2B birlestirir, 2-of-2 voting | `atlas-gate.md` |
| **MAIN** | Profilde `atlas-review-main` | FAZ5 — yalniz dondurulmus INPUT'u inceler, kanitli bulgulari MAIN.json'a yazar | `atlas-review-main.md` |
| **REVIEWER** | Profilde `atlas-review-reviewer` | FAZ5 — INPUT + MAIN; MAIN bulgularina tipli hukum verir, yeni bulgulari ayirir | `atlas-review-reviewer.md` |
| **CRITIC** | Profilde `atlas-review-critic` | FAZ5 — INPUT + MAIN + REVIEWER; bilinen bulgulari degerlendirir, P0/pivotal uyusmazligi korur | `atlas-review-critic.md` |
| Gate Strong Wrapper | — | atlas-gate-2a yonlendirici (DEPRECATED, `disable: true`) | `atlas-gate-strong.md` |
| Gate Manifest Wrapper | — | atlas-gate-2b yonlendirici (DEPRECATED, `disable: true`) | `atlas-gate-manifest.md` |
| Gate Legacy | — | v4.0 uyumlulugu (DEPRECATED, `disable: true`) | `atlas-gate_2.md` |

**Not:** Varsayilan (primary) ajan `atlas-orchestrator` (opencode.json `default_agent`).
Diger calisan ajanlar `mode: subagent`. Deprecated 3 wrapper `disable: true` — yuklenmez.
Guncel model→rol eslemesi icin `routing.profiles.json`, faz haritasi icin `docs/PIPELINE.md`.
Panel sirasi MAIN → REVIEWER → CRITIC'tir; hukumler `AGREE`, `DISAGREE_EVIDENCE`,
`DISAGREE_CONCERN`. Rol ayrimi bagimsiz uzmanlik iddiasi degildir; nihai karar insandadir.

## Model Maliyet Tablosu — tarihsel kayit

Asagidaki eski model/rol ve goreli maliyet kaydi korunur; guncel model secimi icin
yukaridaki routing isaretcisini kullan. Bu tabloda yeni fiyat olcumu yapilmamistir.

| Model | Rol | Cost |
|-------|-----|------|
| Claude Opus 5 (thinking: high) | Orchestrator, Scoper, Writer, Editor Lens, Gate Orchestrator | $$$ |
| GLM 5.3 | Structure Lens, Gate 2B | $ |
| DeepSeek V4 Pro | Consistency Lens, Gate 2A | $$ |
| Kimi K3 | (kodlama isleri; su an bagli ajan yok) | $$ |
