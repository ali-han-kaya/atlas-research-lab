# ATLAS — architecture and gate demo

ATLAS is a verification-first, multi-agent research lab. It publishes the mechanism that
produces research and code, not the papers or generated corpora. A delivery is judged by
fail-closed gates that run over its own bytes; a model saying "done" is only a claim.

## Architecture in one view

```text
brief / source / code change
          │
          ├── ATLAS pipeline   scope → three review lenses → targeted fixes
          │                    → MASTER → 2-of-2 acceptance
          └── KOD pipeline     scope → mandatory baseline → implementation
                               → 2A / 2B / 2C gates
          ▼
gate scripts                 one rule per branch; rc=1 (error) or rc=2 (terminal)
          ▼
mutation battery             silent clean baseline → one violation → red/expected → undo
          ▼
run evidence                 tools/mutasyon_sonuc.json, fresh against gate source hashes
          ▼
scope ratchet                tools/kapsam.py; no unmeasured gap may hide
          ▼
make dogrula                 H1–H5 hygiene/syntax/secrets + T1–T3 self-test suites
          ▼
make iddia                   every published number re-measured from its command
          ▼
attestation.json             commit, tree and file SHA-256; rechecked by T1 / KANIT
          ▼
public scope                 tools/yayin_manifest.json; no papers, secrets or private paths
```

Three properties make the chain useful:

- **Evidence is a run, not a definition.** Coverage comes from the last real mutation
  battery, bound to the source SHA-256 of the gate scripts. Editing a gate invalidates its
  old evidence instead of silently preserving a green label.
- **Every mutation is reversible.** The battery starts from a silent clean baseline,
  injects one violation, checks that only the expected label fires, then undoes it and
  checks green again.
- **Unmeasured is not a pass.** A missing network, account or fixture is reported as
  `OLCULMEDI`, never converted into `PASS`.

The generated [`KURAL-KATALOGU.md`](../KURAL-KATALOGU.md) lists every rule and how it is
proven. [`DURUM.md`](../DURUM.md) holds the current counters; the prose here does not copy
them.

## Which gate catches what

| Gate | Catches | What a failure looks like |
|---|---|---|
| `make dogrula` | Repository hygiene, Python/shell syntax errors, live secrets, regressed self-tests, and a stale tree attestation. | One of H1–H5 or T1–T3 is `FAIL`; the summary is not `8/8`. |
| `make mutasyon` | A gate that never fires, fires for the wrong label, leaks a marker into the clean baseline, or stays red after the violation is undone. | The case has no silent baseline, no expected red/terminal marker, or no green rerun. |
| `make iddia` | A number in the public docs that no longer matches the command that produced it, including a changed raw output line. | An `IDD-*` claim is named as stale or mismatched. |
| `make katalog-kayit-dogrula` | A malformed or reordered evidence row, a wrong commit/tree/tree hash, a changed definition hash, or an evidence row edited after it was committed. | `KATALOG KAYIT DOGRULA: FAIL` with the exact row and reason. |
| `make kanit-dogrula` | An `attestation.json` whose commit, tree, file list or SHA-256 no longer describes the tree. | `KANIT` fails rather than falling back to an older record. |
| `make yayin-kapisi` | An unlisted file, a generated paper/corpus trace, a secret, or a personal absolute path crossing the public boundary. | `YAYIN-KAPISI: FAIL`; publishing stops before bytes move. |
| `./demo` | The historical contradiction: the frozen fix manifest claims eight fixes while the master text contains two, and the gate of that day still said `PASS`. | The expected **red** verdict, `rc=1`; this is a demo, not a broken checkout. |

`make dogrula` is the single local entry point. `make mutasyon`, `make iddia` and the
public-scope checks are separate questions: a gate can be syntactically green and still
fail to catch anything, or the prose can be green while its numbers are stale.

## Real FAIL → PASS transcript

This was captured on 27 November 2026 in a **throwaway clone**, so the tampered row never
enters the working repository. The first row's `model` field is changed in the working
tree; the verifier requires the record to equal `HEAD`, so even an uncommitted edit
cannot remain green.

```console
$ git clone -q https://github.com/ali-han-kaya/atlas-research-lab.git /tmp/atlas-gate-demo
$ cd /tmp/atlas-gate-demo
$ make katalog-kayit-dogrula
KATALOG KAYIT DOGRULA: PASS — sema+sira+agac+tanim+append-only

$ python3 -c "import json,pathlib; p=pathlib.Path('docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl'); rows=[json.loads(x) for x in p.read_text().splitlines()]; rows[0]['model']='TAMPER-DEMO'; p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))"
$ make katalog-kayit-dogrula
KATALOG KAYIT DOGRULA: FAIL — 1 hata
  calisma agaci HEAD ile ayni degil; once kaydi commit edin (elle duzenlenmis satir kanit sayilmaz)

$ git checkout -- docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl
$ make katalog-kayit-dogrula
KATALOG KAYIT DOGRULA: PASS — sema+sira+agac+tanim+append-only
```

The verifier did not trust the row's fields. It checked that the working file equals
`HEAD` and that every historical version of the record is a byte-prefix of the next one.
Restoring the row restored the verdict. If the same tampered row is committed, the gate
still fails, with `append-only ihlali: <commit> surumu onceki surumun bayt oneki degil`.

## Three-command quick path

The smallest gate above needs only Python's standard library: no model call, network
access, API key or third-party package.

```bash
git clone https://github.com/ali-han-kaya/atlas-research-lab.git
cd atlas-research-lab
make katalog-kayit-dogrula
```

Expected last line:

```text
KATALOG KAYIT DOGRULA: PASS — sema+sira+agac+tanim+append-only
```

For the full eight-check local gate, install `requirements-dev.txt` in an isolated
virtual environment and run `make dogrula`; the longer English route is in
[`QUICKSTART.md`](QUICKSTART.md).
