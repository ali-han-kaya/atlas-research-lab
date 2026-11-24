# Security Policy

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting for this repository:

https://github.com/ali-han-kaya/atlas-research-lab/security/advisories/new

Do not open a public issue containing exploit details. In the private report, include the affected path and commit, impact, reproduction steps and a minimal proof of concept. Do not include live credentials or third-party data; revoke or rotate any credential you believe was exposed.

The private advisory thread is the coordination channel for validation, fixes and disclosure. No response-time guarantee is implied.

## Scope

This repository is a source-code and verification mechanism, not a hosted service. Generated papers, corpora, private-lab work and session handoffs are not published here.

In scope:

- the public gate scripts, self-tests, CI workflows, templates and agents in this repository;
- a defect that can make a gate report a false pass, bypass fail-closed handling, expose secrets in output, or execute unintended code from repository content.

Out of scope:

- the private lab, generated papers/corpora and unpublished data;
- third-party dependencies and services (report those upstream);
- issues that require a compromised GitHub or maintainer account, or write access to the repository;
- testing against other people's data or systems.

Please test only against your own checkout and do not disrupt CI or other users.

## What the secret gate catches — and what it does not

`tools/sir_kapisi.py` blocks live PostgreSQL connection strings that contain inline credentials, and Neon `npg_` tokens, in staged, changed or pushed lines. The independent `KOD_SABLONLAR/scripts/secret_scan.py` check covers known token formats and PEM private-key blocks, and CI runs it over the tree. Exact known fixture lines may be exempted by hash; there is no file- or pattern-level blanket exemption.

These are bounded checks, not proof that the tree is secret-free. They do not reliably catch:

- unknown or custom credential formats, or secrets split across lines;
- secrets already present in history or outside the scanned diff;
- credentials embedded in images, archives or other binary files;
- encoded, encrypted or otherwise transformed values;
- secrets held in external services, logs or browser storage.

If a credential is exposed, revoke or rotate it first; removing it from the working tree does not make it safe. Use GitHub secret scanning and provider-side revocation as separate layers.
