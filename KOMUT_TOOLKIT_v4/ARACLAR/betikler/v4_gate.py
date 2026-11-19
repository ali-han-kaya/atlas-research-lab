#!/usr/bin/env python3
"""ALI KOMUT TOOLKIT v4 — KARAR BIRLESTIRICI (fail-closed)

    python3 v4_gate.py <kapiA.json> <kapiB.json> [...] [--hedef <klasor|dosya>]
                       [--out rapor.json] [--sessiz]

Karar HER ZAMAN ham `findings` ve `checks` dizilerinden yeniden hesaplanir.
Hicbir dis "verdict" veya sayac beyanina guvenilmez.

Kapatilan somut delikler (hepsi gercek kod uzerinde olculdu):
  D1  Bos JSON (`{}`) iki kapi olarak verildiginde olumlu karar cikiyordu.
      -> Olumlu karar icin en az bir `checks` kaydi ve DOLU `evidence` sart.
  D2  Taninmayan siddet etiketi (`CRITICAL`, `BLOCKER`, `"P0 "`, `SEV0`)
      sessizce sayilmiyordu; dort kritik bulgu olumlu karar aliyordu.
      -> Kapali liste; liste disi deger P0 sayilir.
  D3  Ayni dosya iki kez verildiginde "2-of-2" gorunuyordu.
      -> Ayni icerik ozeti -> IDENTICAL_GATE_INPUTS = P0.
  D4  Bozuk sayac alani (`p0_count: "abc"`) yakalanmamis istisna atiyordu.
      -> Bicimli fail-closed rapor.
  D5  Denetcinin kendi guvenilirligi hic olculmuyordu.
      -> --hedef verilirse her `evidence` literal alt-dize olarak aranir;
         dogrulanamayan oran > %20 ise GRADER_MISCALIBRATED -> BUTUNLUK_ASKISI.

Cikis: 0 = engel yok, 1 = engel var, 2 = kullanim hatasi.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v4_common import (  # noqa: E402
    CHECK_STATUSES, EXIT_BLOCK, EXIT_OK, EXIT_USAGE, SEVERITIES, emit,
    fail_closed, finding, normalize,
)

MISCALIBRATION_THRESHOLD = 0.20


def load_gate(path):
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        return None, f"okunamadi: {e}", ""
    try:
        data = json.loads(raw)
    except Exception as e:
        return None, f"JSON gecersiz: {e}", hashlib.sha256(raw.encode()).hexdigest()[:16]
    if not isinstance(data, dict):
        return None, "JSON kok nesnesi sozluk degil", hashlib.sha256(raw.encode()).hexdigest()[:16]
    digest = hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    return data, None, digest


def evaluate(gate, label, target_text):
    """Bir kapi ciktisini BAGIMSIZ degerlendir. Beyanina bakma."""
    out = {"label": label, "p0": 0, "p1": 0, "p2": 0, "notes": [],
           "checks_ok": 0, "checks_total": 0, "unverifiable": 0, "findings_total": 0}

    findings = gate.get("findings")
    if findings is None:
        findings = []
    if not isinstance(findings, list):
        out["notes"].append(f"{label}: `findings` liste degil -> SCHEMA_INVALID")
        out["p0"] += 1
        findings = []

    for f in findings:
        out["findings_total"] += 1
        if not isinstance(f, dict):
            out["p0"] += 1
            out["notes"].append(f"{label}: bulgu sozluk degil -> P0")
            continue
        sev = f.get("severity", f.get("priority"))
        if sev == "P0":
            out["p0"] += 1
        elif sev == "P1":
            out["p1"] += 1
        elif sev == "P2":
            out["p2"] += 1
        else:
            # D2: taninmayan/eksik siddet 'saymadim' DEGIL, P0.
            out["p0"] += 1
            out["notes"].append(
                f"{label}: kapali liste disi siddet {sev!r} (bulgu {f.get('id')}) -> P0")
        # D5: kanit gercekten hedefte var mi?
        if target_text is not None:
            ev = normalize(str(f.get("evidence", "")))
            if ev and len(ev) >= 12 and ev not in target_text:
                out["unverifiable"] += 1
                out["notes"].append(
                    f"{label}: {f.get('id')} kaniti hedefte literal bulunamadi")

    checks = gate.get("checks")
    if checks is None:
        checks = []
    if not isinstance(checks, list):
        out["notes"].append(f"{label}: `checks` liste degil -> SCHEMA_INVALID")
        out["p0"] += 1
        checks = []

    for c in checks:
        if not isinstance(c, dict):
            out["p0"] += 1
            continue
        out["checks_total"] += 1
        st = c.get("status")
        ev = str(c.get("evidence", "")).strip()
        if st not in CHECK_STATUSES:
            out["p0"] += 1
            out["notes"].append(f"{label}: kapali liste disi kontrol durumu {st!r} -> P0")
            continue
        if st == "GECTI":
            if not ev:
                # Kanitsiz 'gecti' bir olcum degil, bir beyandir.
                out["p0"] += 1
                out["notes"].append(f"{label}: {c.get('id')} GECTI ama evidence bos -> P0")
            else:
                out["checks_ok"] += 1
        elif st == "KALDI":
            out["p1"] += 1
        elif st == "CALISTIRILMADI":
            out["p1"] += 1
            out["notes"].append(f"{label}: {c.get('id')} calistirilmadi -> OLCULMEYEN")

    # D1: olculdugunun kaniti yoksa olumlu karar YOK.
    if out["checks_ok"] == 0:
        out["p0"] += 1
        out["notes"].append(
            f"{label}: NO_INSPECTION_EVIDENCE - kanitli tek bir kontrol kaydi yok")

    # Beyan karsilastirmasi (yalniz seffaflik; karar buna dayanmaz)
    meta = gate.get("metadata") if isinstance(gate.get("metadata"), dict) else {}
    for field, real in (("p0_count", out["p0"]), ("p1_count", out["p1"])):
        dec = meta.get(field, gate.get(field))
        if dec is None:
            continue
        try:
            dec_i = int(dec)  # D4: bozuk deger istisna atmaz
        except (TypeError, ValueError):
            out["p0"] += 1
            out["notes"].append(f"{label}: {field}={dec!r} sayiya cevrilemedi -> P0")
            continue
        if dec_i != real:
            out["p0"] += 1
            out["notes"].append(
                f"{label}: beyan {field}={dec_i} ama yeniden hesap={real} -> METADATA_MISMATCH")

    declared = str(gate.get("verdict", "")).upper()
    real_verdict = "ENGEL_VAR" if out["p0"] else ("KOSULLU" if out["p1"] else "ENGEL_YOK")
    if declared:
        norm = {"PASS": "ENGEL_YOK", "FAIL": "ENGEL_VAR", "ENGEL_YOK": "ENGEL_YOK",
                "ENGEL_VAR": "ENGEL_VAR", "KOSULLU": "KOSULLU"}.get(declared, declared)
        if norm != real_verdict:
            out["p0"] += 1
            out["notes"].append(
                f"{label}: beyan verdict={declared} ama yeniden hesap={real_verdict} -> METADATA_MISMATCH")
    out["verdict"] = "ENGEL_VAR" if out["p0"] else ("KOSULLU" if out["p1"] else "ENGEL_YOK")
    out["declared_verdict"] = declared or None
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="ALI KOMUT TOOLKIT v4 - fail-closed karar birlestirici")
    ap.add_argument("kapilar", nargs="*", help="kapi cikti JSON dosyalari (en az 2)")
    ap.add_argument("--hedef", help="denetlenen dosya/klasor - kanit dogrulamasi icin")
    ap.add_argument("--out")
    ap.add_argument("--sessiz", action="store_true")
    args = ap.parse_args(argv)

    if len(args.kapilar) < 2:
        fail_closed("en az 2 kapi cikti dosyasi gerekir (tek kapi bagimsizlik saglamaz)",
                    args.out)

    target_text = None
    if args.hedef:
        parts = []
        if os.path.isfile(args.hedef):
            try:
                with open(args.hedef, encoding="utf-8", errors="replace") as f:
                    parts.append(f.read())
            except OSError:
                pass
        elif os.path.isdir(args.hedef):
            for dp, dn, fns in os.walk(args.hedef):
                dn[:] = [d for d in dn if d not in
                         {".git", "node_modules", "__pycache__", "__MACOSX"}]
                for fn in fns:
                    p = os.path.join(dp, fn)
                    try:
                        if os.path.getsize(p) > 4_000_000:
                            continue
                        with open(p, encoding="utf-8", errors="replace") as f:
                            parts.append(f.read())
                    except OSError:
                        continue
        target_text = normalize("\n".join(parts)) if parts else ""

    results, digests, load_errors = [], {}, []
    for i, path in enumerate(args.kapilar):
        label = chr(ord("A") + i)
        data, err, digest = load_gate(path)
        digests.setdefault(digest, []).append(f"{label}({os.path.basename(path)})")
        if data is None:
            load_errors.append(f"{label}: {path}: {err}")
            continue
        results.append(evaluate(data, label, target_text))

    extra_findings, n = [], [0]

    def add(code, sev, loc, ev, fix):
        n[0] += 1
        extra_findings.append(finding(f"KAP-{n[0]:03d}", code, sev, loc, ev, fix))

    for e in load_errors:
        add("SCHEMA_INVALID", "P0", "girdi", e, "kapi ciktisini gecerli JSON olarak uret")

    # D3: ayni icerik iki kapi sayilmaz
    for digest, labels in digests.items():
        if len(labels) > 1 and digest:
            add("SCHEMA_INVALID", "P0", "bagimsizlik",
                f"IDENTICAL_GATE_INPUTS: {', '.join(labels)} ayni icerige sahip",
                "iki kapiyi farkli oturumda/farkli girdiyle uret")

    p0 = sum(r["p0"] for r in results) + sum(1 for f in extra_findings if f["severity"] == "P0")
    p1 = sum(r["p1"] for r in results)
    p2 = sum(r["p2"] for r in results)

    # D5: denetci kalibrasyonu
    integrity_hold = False
    if target_text is not None:
        tot = sum(r["findings_total"] for r in results)
        unv = sum(r["unverifiable"] for r in results)
        if tot and unv / tot > MISCALIBRATION_THRESHOLD:
            integrity_hold = True
            add("GRADER_MISCALIBRATED", "P0", "denetci",
                f"{unv}/{tot} bulgunun kaniti hedefte literal bulunamadi (esik %20)",
                "BUTUNLUK_ASKISI: yeniden deneme YASAK, ham bulgulari insana goster")
            p0 += 1

    if len(results) < 2:
        add("SCHEMA_INVALID", "P0", "bagimsizlik",
            f"yalniz {len(results)} kapi degerlendirilebildi, en az 2 gerekir",
            "eksik kapi ciktisini uret")
        p0 += 1

    if integrity_hold:
        verdict = "BUTUNLUK_ASKISI"
    elif p0:
        verdict = "ENGEL_VAR"
    elif p1:
        verdict = "KOSULLU"
    else:
        verdict = "ENGEL_YOK"

    notes = [nt for r in results for nt in r["notes"]]
    report = {
        "arac": "ALI_KOMUT_TOOLKIT_v4",
        "kapi": "BIRLESTIRICI",
        "verdict": verdict,
        "kapi_sayisi": len(results),
        "kapilar": [
            {"label": r["label"], "verdict": r["verdict"],
             "declared_verdict": r["declared_verdict"],
             "P0": r["p0"], "P1": r["p1"], "P2": r["p2"],
             "kanitli_kontrol": r["checks_ok"], "kontrol_toplam": r["checks_total"],
             "dogrulanamayan_kanit": r["unverifiable"]}
            for r in results
        ],
        "kanit_dogrulamasi": "yapildi" if target_text is not None else "NOT_EXECUTED (--hedef verilmedi)",
        "counts": {"P0": p0, "P1": p1, "P2": p2},
        "notlar": notes,
        "findings": extra_findings,
    }
    emit(report, args.out, args.sessiz)
    return EXIT_OK if verdict == "ENGEL_YOK" else EXIT_BLOCK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        fail_closed(f"beklenmeyen hata: {type(exc).__name__}: {exc}")
        sys.exit(EXIT_USAGE)
