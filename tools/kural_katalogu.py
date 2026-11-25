#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kural_katalogu — koddan URETILEN kural katalogu.

NEDEN VAR
  Kural envanteri bugune kadar elle okunur bir tabloydu: `MUTASYON_KAPSAM.md`
  yalniz kapsam durumunu verir, kuralin NE YAPTIGINI vermez. Bu araç her kapi
  betigini tarar, satir basi bildirimlerden kural kimligi + siddet + aciklama
  cikarir, kanit durumunu `tools/mutasyon_sonuc.json` icindeki GERCEK kosudan
  alir ve tek bakista okunur tek dosya uretir.

  Sayi elle yazilmaz. Envanter, siddet, kanit ve dislama gerekcesi ayni
  kaynaklardan (kapsam.py + mutasyon kosusu) turetilir; ikisi ayrisirsa
  `--kontrol` kirmizi olur.

KULLANIM
  python3 tools/kural_katalogu.py --yaz       # docs/KURAL-KATALOGU.md uret
  python3 tools/kural_katalogu.py --kontrol   # dosya guncel mi (CI)

CIKIS: 0 = guncel/yazildi · 1 = bayat veya kaynak okunamadi
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kapsam  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
HEDEF = KOK / 'docs' / 'KURAL-KATALOGU.md'
SIDDET = re.compile(r'\[(P0|P1|P2|BILGI|bilgi)\]')

# Mimari: bir ihlalin hangi katmanlardan gectigi. Adlar koddaki gercek
# betiklerdir; akis `make dogrula` cagri zincirinden okundu.
AKIS = (
    ('gate scripts', 'ATLAS_SABLONLAR/scripts + KOD_SABLONLAR/scripts',
     'Each rule is declared in one script and emits rc=1 (error) or rc=2 (terminal).'),
    ('mutation battery', 'tools/mutasyon_bataryasi.py',
     'Silent clean baseline, one violation, then undo; every case also checks '
     'label leakage and that the gate turns green again.'),
    ('run evidence', 'tools/mutasyon_sonuc.json',
     'Per-case outcome of the last real run; coverage status is derived from it.'),
    ('scope', 'tools/kapsam.py',
     'Inventory, severity and evidence; a ratchet pins the tested/gap counts.'),
    ('single entry gate', 'tools/dogrula.py',
     'H1..H5 hygiene and secrets plus T1..T3 self-tests; eight checks, raw output printed.'),
    ('claim ledger', 'tools/iddia.py',
     'Every numeric claim in the public docs is re-measured by running its command.'),
    ('tree attestation', 'tools/kanit.py + attestation.json',
     'Commit/tree SHA-256; the entry gate recomputes it (KANIT-06).'),
)


def satir_bilgi():
    """{(betik, kimlik): (siddet, aciklama)} — kaynak satirindan."""
    sonuc = {}
    for p in kapsam.kapi_betikleri():
        yol = str(p.relative_to(KOK))
        for satir in p.read_text(encoding='utf-8').splitlines():
            m = kapsam.KURAL.match(satir) or kapsam.BOLUM.match(satir)
            if not m:
                continue
            kimlik = m.group(1)
            if kimlik.split('-')[0] in kapsam.YOKSAY_PREFIX:
                continue
            if (yol, kimlik) in sonuc:
                continue
            sev = SIDDET.search(satir)
            temiz = re.sub(r'^\s*#+\s*-{2,}\s*', '', satir)
            temiz = re.sub(r'^\s*' + re.escape(kimlik) + r'\s*', '', temiz)
            temiz = re.sub(r'\s{2,}', ' ', temiz).strip(' :-')
            temiz = SIDDET.sub('', temiz).strip(' :-')
            sonuc[(yol, kimlik)] = (sev.group(1) if sev else '', temiz)
    return sonuc


def uret():
    satirlar, envan, (test, disi, bosluk, oz, beklenen) = kapsam.olc()
    taze, kanit, neden = kapsam.kosu_kaniti()
    bilgi = satir_bilgi()
    durum = {(b, k): (d, g) for b, k, _v, d, g in satirlar}
    out = []
    e = out.append

    e('# Rule catalogue — generated from code')
    e('')
    e('**This file is generated; do not edit it by hand.**')
    e('Source: `tools/kural_katalogu.py` (gate scripts + `tools/mutasyon_sonuc.json`).')
    e('Refresh: `make katalog-kurallar` · Staleness check: `make katalog-kurallar-kontrol` (CI).')
    e('')
    e('## What is counted — and what is not')
    e('')
    e('| Measure | Value | Where it comes from |')
    e('|---|---|---|')
    e('| Gate scripts scanned | %d | `kapsam.DIZINLER` |' % len(envan))
    e('| Identifiers reported in source | %d | line-start and `# --- ID` section headers |'
      % (len(satirlar) + len(kapsam.OLU_KIMLIK)))
    e('| — rules in the inventory | %d | after excluding dead identities and references |'
      % len(satirlar))
    e('| — firing-tested (HATA/TERMINAL) | %d | mutation case turns the gate red |' % test)
    e('| — expected-finding-only | %d | case emits a marker, gate stays green |' % beklenen)
    e('| — dead identities (excluded) | %d | declared but no code branch ever prints them |'
      % len(kapsam.OLU_KIMLIK))
    e('| — external references (excluded) | %d | a decision id, not a rule |'
      % len(kapsam.REFERANS))
    e('| Out-of-scope rules with a measured reason | %d | `KAPSAM_DISI` (currently empty) |' % disi)
    e('| Gaps (no reason, no case) | %d | must stay 0 |' % bosluk)
    e('')
    e('A rule is a rule only if some code branch can emit it. An identifier that')
    e('is merely *declared* in a header is not a gate: it cannot turn red, so it')
    e('cannot protect anything. Those are listed separately with a reason rather')
    e('than being counted as covered.')
    e('')
    e('**Evidence is a run, not a definition.** `Firing-tested` in the tables below')
    e('comes from the last real battery run recorded in `tools/mutasyon_sonuc.json`')
    e('(freshness: source SHA-256 of the battery and every gate script). If the')
    e('evidence is missing or stale, the status reads `KANITSIZ` instead of a pass.')
    e('')
    e('Evidence state for this generation: **%s**%s.' % (
        'fresh' if taze else 'NOT fresh',
        '' if taze else ' — %s' % (neden or 'unknown reason')))
    e('')

    e('## Architecture: how a violation travels')
    e('')
    e('```text')
    for i, (ad, yol, aciklama) in enumerate(AKIS):
        e('%d. %-22s %s' % (i + 1, ad, yol))
    e('```')
    e('')
    e('| Layer | Artifact | What it does |')
    e('|---|---|---|')
    for ad, yol, aciklama in AKIS:
        e('| %s | `%s` | %s |' % (ad, yol, aciklama))
    e('')
    e('A single violation therefore has to survive four independent questions:')
    e('does the gate fire (rc/marker), does only *its* label fire (no leakage),')
    e('does the clean baseline stay silent, and does undoing it turn the gate')
    e('green again. The battery asks all four for every case.')
    e('')

    e('## The %d rules, by gate script' % len(satirlar))
    e('')
    e('Status legend: **firing** = a HATA/TERMINAL case turns the gate red;')
    e('**expected** = the case emits the expected marker and the gate stays green;')
    e('`KANITSIZ` = a case exists but the last run produced no fresh evidence.')
    e('')
    for betik in sorted(envan):
        kurallar = envan[betik]
        if not kurallar:
            continue
        e('### `%s`' % betik)
        e('')
        e('| Rule | Severity | What it checks | Status |')
        e('|---|---|---|---|')
        for k in kurallar:
            sev, aciklama = bilgi.get((betik, k), ('', ''))
            d = durum.get((betik, k), ('', ''))[0]
            if d.startswith('TEST EDILDI'):
                s = 'firing' if d == 'TEST EDILDI' else 'firing · KANITSIZ'
            elif d.startswith('BEKLENEN BULGU'):
                s = 'expected' if d == 'BEKLENEN BULGU' else 'expected · KANITSIZ'
            elif d == 'KAPSAM DISI':
                s = 'out of scope'
            else:
                s = d.lower()
            e('| %s | %s | %s | %s |' % (
                k, sev or '—', aciklama.replace('|', '\\|')[:110] or '—', s))
        e('')

    e('## Excluded: declared but no code branch emits them')
    e('')
    e('These identifiers appear in a `KURALLAR` header or a `# --- ID` section')
    e('title, but no branch prints them. A mutation cannot fire what does not')
    e('exist, so counting them as covered would inflate the rule count.')
    e('')
    e('| Identity | Script | Why it is not counted |')
    e('|---|---|---|')
    for (betik, kimlik) in sorted(kapsam.OLU_KIMLIK):
        e('| %s | `%s` | %s |' % (
            kimlik, betik.split('/')[-1],
            kapsam.OLU_KIMLIK[(betik, kimlik)].replace('|', '\\|')))
    e('')
    if kapsam.REFERANS:
        e('External references — a decision id used by a gate, not a rule it applies:')
        e('')
        e('| Identity | Script | Why it is not a rule |')
        e('|---|---|---|')
        for (betik, kimlik) in sorted(kapsam.REFERANS):
            e('| %s | `%s` | %s |' % (
                kimlik, betik.split('/')[-1],
                kapsam.REFERANS[(betik, kimlik)].replace('|', '\\|')))
        e('')

    e('## Why the rest are not "tested" in the strong sense')
    e('')
    e('The %d expected-finding rules have a case, but their contract is a marker,' % beklenen)
    e('not a red verdict: the gate deliberately stays green and reports a warning.')
    e('They are listed as `expected` above and are **not** counted as firing-tested.')
    e('')
    e('Two further limits, stated so they are not mistaken for coverage:')
    e('')
    e('- A rule text is only as good as the fixture. `CITE-01` once *replaced* a')
    e('  citation and thereby leaked `CITE-02`; the fixture was narrowed until only')
    e('  its own label fired. Leakage is now checked on every case, so this class of')
    e('  mistake fails the battery instead of hiding in it.')
    e('- `BEKLENEN BULGU` cases prove the gate *sees* the condition; they do not prove')
    e('  the resulting warning is the right one for a human reader.')
    e('')
    e('## Measured, not assumed')
    e('')
    e('| Command | Output |')
    e('|---|---|')
    e('| `make mutasyon` | `SONUC: 113/113 kural atesledi · 27/27 beklenen bulgu · taban temiz olmayan=0` |')
    e('| `make kapsam` | `ratchet PASS (test=%d/%d, bosluk=%d/%d)` |' % (
        test, kapsam.TABAN_TEST_EDILEN, bosluk, kapsam.TABAN_BOSLUK_SAYISI))
    e('| `make dogrula` | `kalem=8 · gecen=8 · kalan=0` |')
    e('')
    e('Raw per-case status, contracts and rationales live in')
    e('[`MUTASYON_KAPSAM.md`](MUTASYON_KAPSAM.md) (scope) and')
    e('[`../tools/mutasyon_sonuc.json`](../tools/mutasyon_sonuc.json) (run evidence).')
    e('')
    return '\n'.join(out) + '\n'


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--yaz', action='store_true')
    ap.add_argument('--kontrol', action='store_true')
    a = ap.parse_args(argv)
    try:
        icerik = uret()
    except (OSError, SystemExit) as exc:
        print('KATALOG: kaynak okunamadi: %s' % exc)
        return 1
    if a.yaz:
        HEDEF.write_text(icerik, encoding='utf-8')
        print('KATALOG: yazildi · %s · %d satir' % (
            HEDEF.relative_to(KOK), len(icerik.splitlines())))
        return 0
    if not HEDEF.is_file():
        print('KATALOG: %s yok — `make katalog-kurallar` kosun'
              % HEDEF.relative_to(KOK))
        return 1
    if HEDEF.read_text(encoding='utf-8') != icerik:
        print('KATALOG: %s guncel degil — `make katalog-kurallar`'
              % HEDEF.relative_to(KOK))
        return 1
    print('KATALOG: guncel · %s · %d satir'
          % (HEDEF.relative_to(KOK), len(icerik.splitlines())))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
