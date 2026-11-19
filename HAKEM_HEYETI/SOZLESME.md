> **NOT:** Bu dosya bir **örnek proje sözleşmesidir**. Aşağıdaki Run-B (`SEKINE-2026-08-20-B`) `isimlendir/` çalışma tezgâhındaki dosyalara atıfta bulunur. Bu dış kaynaklar lab'a kopyalanmamıştır; yollar `AI_ARASTIRMA_LABI/ISARETCILER.md`'de listelenmiştir.

# SOZLESME — Audit Contract (run SEKINE-2026-08-20-B)

**Run ID:** SEKINE-2026-08-20-B
**Date:** 20 August 2026
**Input document:** `sekinemruhum_MAKALE.md` (692 lines; baseline copy: `girdi/sekinemruhum_orijinal.md`, SHA256 `5f88f41a7d3775ccad3a8cd32217a8a01c1da82c43466d310766d7f94970d20f`)
**Mode:** MODE-A (file reading, code execution, and network access enabled)
**Classification:** TIP=AKADEMIK | SINYAL=kural-2 | GUVEN=YUKSEK

## 1. Scope

The goal is the finalization of the English-language academic paper `sekinemruhum_MAKALE.md`
(*The Divine Attribute Rahīm in the Basmala: A Comparative Study with the Jewish Mystical Concept
of Shekhinah*) by filling all fillable voids, using the tools, gadgets, and data located in the
`isimlendir` root folder:

- `ALI_KOMUT_TOOLKIT_v4.zip` (F0–F6 pipeline discipline: contract, preservation, gates)
- `portfolyo/04-ARACLAR/DENETIM-BORU-HATTI.md` (KATMAN 0–3 specialist swarm template)
- `rapor/` records and `TRUTH_MAKALE-v2.0.md` (reference implementation of the verification protocol)

Void classes in scope:

1. **Declared verification limits** (paper §5.5; Appendix C declared limits):
   (a) content-level access to Goldziher 1893 — candidate full text at real.mtak.hu/118233;
   (b) Goldziher 1896 and Jeffery 1938 catalog-level records — candidate full texts;
   (c) missing specific tafsir citation for the *Raḥmān*/*Rahīm* exegetical distinction;
   (d) Zohar "Vaʾera II, 32a" citation mapping to the Pritzker edition.
2. **Missing audit artifacts** referenced by Appendix D but absent from `rapor/`:
   `rapor/keep.json`, `rapor/SOZLESME.md`, `rapor/bulgular.json` (17 findings), `rapor/parcalar/*`,
   `rapor/kapilar/A_koruma.json`, `rapor/kapilar/B_fix.json`, `nihai_rapor.md`, PDF packaging.
3. **Swarm-discovered consistency defects** (KATMAN 1–3), body-only.
4. **Run-B audit records** (findings, fixes, verification, known limits) in English.

Out of scope: opportunistic strengthening (new claims, new sections, new tables, extra citations
beyond what the evidence supports); edits to Appendix A; edits to `TRUTH_MAKALE*.md` or `portfolyo/`
content.

## 2. Preservation contract (posture)

- **Least data-losing option at every decision point.**
- Appendix A of the paper ("Original Text, Verbatim") remains byte-identical:
  SHA256 of the Appendix A span (lines 301–692 of the run-B input) is frozen at baseline.
- Every lexical change to the body is (a) confined to documented fixes, (b) keyed to a finding,
  (c) reflected in the correction records.
- No finding is silently dropped. Unverifiable items are marked
  `UNVERIFIED_SOURCE` / `NOT_AVAILABLE` / `DOGRULANAMADI` — never assumed true.
- No fabricated sources; no fabricated content-level verification.
- No personal data enters any artifact.

## 3. Posture budget

The audit defaults to the least data-losing option at every decision point (budget: 3 points).
Points are spent only when the evidence genuinely forces a body edit; a declared limit that cannot
be filled remains a declared limit.

## 4. Verification protocol

Each verification check is recorded with its status:

| Status | Meaning |
|---|---|
| `DOGRULANDI` | Record confirmed as stated (content or catalog level, basis given) |
| `KISMEN_DOGRULANDI` | Confirmed with caveats; the caveat is stated |
| `KAYIT_DUZELTILDI` | Record corrected on the basis of verification |
| `UNVERIFIED_SOURCE` | Could not be verified at the level indicated |
| `NOT_AVAILABLE` | Source does not provide the datum (e.g., no volume/page on site) |
| `DOGRULANAMADI` | Verification attempted and failed |

## 5. Pipeline stages

| Stage | Operation | Record |
|---|---|---|
| F0 | Baseline capture; section inventory with fingerprints | `girdi/sekinemruhum_orijinal.md`; `rapor/keep.json` (68 sections) |
| F1 | Contract | `rapor/SOZLESME.md` (this file) |
| F2 | Evidence collection and verification (claim inventory + specialist swarm) | `rapor/bulgular.json`; `rapor/dogrulama.json`; Appendix C |
| F3 | Composition (body fixes + appendices updates) | `rapor/parcalar/*.md`; `sekinemruhum_MAKALE.md` |
| F4 | Preservation gate | `rapor/kapilar/A_koruma.json` |
| F5 | Quality gate | `rapor/kapilar/B_fix.json` |
| F6 | Packaging | `sekinemruhum_MAKALE.md`; `sekinemruhum_MAKALE.pdf`; `nihai_rapor.md`; `rapor/BILINEN_SINIRLAR-SEKINE.md` |

## 6. Gate classes (final gate)

A internal contradiction · B factual slip · C honesty defect · D harm to user · E language · F omission.
D is an unconditional BLOCK.