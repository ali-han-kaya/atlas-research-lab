# ATLAS Research Lab — English summary

[![dogrula](https://github.com/ali-han-kaya/atlas-research-lab/actions/workflows/dogrula.yml/badge.svg)](https://github.com/ali-han-kaya/atlas-research-lab/actions/workflows/dogrula.yml)

ATLAS Research Lab proves that a delivery's correctness must be judged by gates that run over its own bytes, not by a model's claim that the work was done. It ships the production mechanism itself — the academic audit and code pipelines, agents, templates, executable gates, self-tests and a mutation battery — and deliberately excludes the papers, corpora and session handoffs it produces. Its sharpest evidence is a frozen defective run (`DENEME/`): the fix manifest declared every fix applied while only a fraction reached the master text, and the gate of that day still said `PASS`; `./demo` reproduces that false `PASS` and returns a red verdict by design.

**Canonical document:** [`README.md`](README.md) (Turkish) is the canonical description of this repository. This English file is a summary, not a translation; where the two differ, `README.md` wins.

## Quick start

Requirements: `python3` (3.9+), `make`, `git`. Verification needs no model calls, no network access and no API keys.

```bash
git clone https://github.com/ali-han-kaya/atlas-research-lab.git
cd atlas-research-lab
python3 -m pip install -r requirements-dev.txt   # pinned: requests, pip-audit
make kur                                         # enable commit/push guards in this clone
make dogrula
./demo                                           # expected: exit code 1 (red)
```

`./demo` is the canonical demo entry point. Its exit code is exactly **1** for the expected red, **2** for a broken fixture and **0** for a consistent fixture. `make demo` is only a thin wrapper: GNU make reports every failing recipe as **2**, so it cannot carry the 1-versus-2 distinction. Use `./demo` when the code matters.

## What is measured

| Command | What it proves |
|---|---|
| `make dogrula` | One entry point for repository hygiene, syntax, secret scan and the self-test suites. It prints its own raw output; a check that does not run is printed as `CALISTIRILMADI` and is never counted as a pass. |
| `make mutasyon` | For each gate rule, a clean baseline must pass, one violation must be injected, and the gate must turn red with the expected finding. A green baseline alone is not a passing case. |
| `./demo` | Reproduces the frozen `DENEME/` contradiction: the manifest claims more fixes than the master text contains, while the frozen gate says `PASS`. The expected result is a red verdict. |
| `make iddia` | Re-measures the numeric claims printed in the public docs and requires each stored raw output line to match the current output. A mismatch is named by `IDD-*`. It does not change the `make dogrula` verdict. |
| `tools/yayinla.py` | Publication parity: copies only an explicit allowlist from the private lab tree, refuses out-of-scope artefacts, scans for secrets and reports new/changed/deleted files. |

CI runs the runner form of the checks, the mutation battery, scope freshness, dependency audit and the demo assertion in `.github/workflows/dogrula.yml`.

## Honest limits

- **OLG-1 (`T1`) now runs against this tree's `attestation.json`.** `olgu_lint` verifies the real commit/tree evidence and no longer needs the private tree's commit history; `make dogrula` reports 8/8 and T1 is a pass. If the attestation is missing or corrupt, OLG-1 fails; it is not reported as not run.
- **The archive is out of scope.** Generated papers, corpora and session handoffs are deliberately not published. This repository is the mechanism; some documents still cite handoff files that live in the private tree.
- **Tests measure gate behaviour, not content truth.** They show that a gate fires on a known violation. They do not prove that the content is correct, and an empty test can still pass a gate; the layering reduces that risk but does not eliminate it.
- **`DENEME/` is frozen on purpose.** It is a deliberately defective run kept as a regression fixture. Do not "fix" it: the defect is the lesson.
- **Network checks are optional.** The live model-catalogue check needs network, is not part of CI and is never required for the local battery.

## Read more

- [`README.md`](README.md) — canonical Turkish documentation.
- [`docs/EN/QUICKSTART.md`](docs/EN/QUICKSTART.md) — longer English quickstart.
- [`docs/README.md`](docs/README.md) — published scope and exclusions.
- [`docs/MUTASYON_KAPSAM.md`](docs/MUTASYON_KAPSAM.md) — which gate rules are mutation-tested, out of scope or still gaps.
