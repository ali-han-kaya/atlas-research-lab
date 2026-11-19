#!/usr/bin/env python3
"""P1-7 uc rollu hakem paneli — tipli ve belirlenimsel birlestirici.

Bu betik model CAGRISI YAPMAZ. MAIN, REVIEWER ve CRITIC artefaktlarini kapali
sema, ayni run/girdi, farkli model ailesi/oturum, tek deneme ve maliyet tavani
acisindan dogrular; sonra hukumleri yeniden hesaplar. Oybirligi kanit degildir.
FIX-MANIFEST'e veya makaleye hicbir zaman yazmaz.

Exit kodlari:
  0  Panel sureci gecerli ve insan blokaji yok (PASS)
  1  Girdi/sema/routing/butce sozlesmesi gecersiz (FAIL)
  2  Panel gecerli ama insan incelemesi gerekir (BLOCKED)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from decimal import Decimal, InvalidOperation


SURUM = "ATLAS-REVIEW-PANEL/v1"
SEMA_KIMLIGI = "ATLAS-REVIEW-PANEL-SCHEMA/v1"
ROLLER = ("MAIN", "REVIEWER", "CRITIC")
HUKUMLER = {"AGREE", "DISAGREE_EVIDENCE", "DISAGREE_CONCERN"}
SIDDETLER = {"P0", "P1", "P2"}
EKSENLER = {f"E{i}" for i in range(1, 8)}
SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
RUN_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
FINDING_RE = re.compile(r"^HJ-(?:[0-9]{3}|R[0-9]{3}|C[0-9]{3})$")
KANIT_RE = re.compile(r"^(?:artifact|source):\S+$")
OTURUM_RE = re.compile(r"^session:\S+$")

ORTAK_ALANLAR = {
    "schema", "run_id", "role", "provider", "model", "model_family",
    "session_ref", "input_sha256", "attempt", "cost_usd",
}
MAIN_ALANLARI = ORTAK_ALANLAR | {"findings"}
DENETCI_ALANLARI = ORTAK_ALANLAR | {"judgments", "new_findings"}
FINDING_ALANLARI = {
    "finding_id", "severity", "axis", "location", "quote", "claim",
    "recommendation", "evidence_ref",
}
JUDGMENT_ALANLARI = {
    "finding_id", "verdict", "severity", "location", "rationale",
    "evidence_ref",
}


class PanelHatasi(Exception):
    def __init__(self, kod: str, mesaj: str):
        super().__init__(mesaj)
        self.kod = kod
        self.mesaj = mesaj


def hata(kod: str, mesaj: str) -> None:
    raise PanelHatasi(kod, mesaj)


def json_oku(yol: pathlib.Path, etiket: str) -> dict:
    try:
        ham = yol.read_text(encoding="utf-8")
    except OSError as exc:
        hata("HJ-00", f"{etiket} okunamadi: {exc}")
    try:
        veri = json.loads(ham)
    except (json.JSONDecodeError, UnicodeError) as exc:
        hata("HJ-00", f"{etiket} JSON gecersiz: {exc}")
    if not isinstance(veri, dict):
        hata("HJ-01", f"{etiket} kok nesnesi JSON object olmali")
    return veri


def tam_alanlar(nesne: dict, beklenen: set[str], etiket: str) -> None:
    gercek = set(nesne)
    if gercek != beklenen:
        eksik = sorted(beklenen - gercek)
        fazla = sorted(gercek - beklenen)
        hata("HJ-01", f"{etiket} kapali sema ihlali; eksik={eksik} fazla={fazla}")


def dolu_metin(deger, etiket: str) -> str:
    if not isinstance(deger, str) or not deger.strip():
        hata("HJ-01", f"{etiket} dolu metin olmali")
    return deger.strip()


def maliyet(deger, etiket: str) -> Decimal:
    if isinstance(deger, bool) or not isinstance(deger, (int, float, str)):
        hata("HJ-07", f"{etiket} sayisal olmali")
    try:
        sonuc = Decimal(str(deger))
    except (InvalidOperation, ValueError):
        hata("HJ-07", f"{etiket} sayisal olmali")
    if not sonuc.is_finite() or sonuc < 0:
        hata("HJ-07", f"{etiket} negatif/sonsuz olamaz")
    return sonuc


def sema_dogrula(yol: pathlib.Path) -> None:
    sema = json_oku(yol, "panel semasi")
    if sema.get("$id") != SEMA_KIMLIGI:
        hata("HJ-00", f"panel sema kimligi beklenenden farkli: {sema.get('$id')!r}")
    try:
        roller = {
            sema["$defs"][ad]["properties"]["role"]["const"]
            for ad in ("main", "reviewer", "critic")
        }
        hukumler = set(sema["$defs"]["verdict"]["enum"])
    except (KeyError, TypeError):
        hata("HJ-00", "panel semasi rol/hukum kapali listelerini tasimiyor")
    if roller != set(ROLLER) or hukumler != HUKUMLER:
        hata("HJ-00", "panel semasi kodun rol/hukum sozlesmesiyle uyusmuyor")


def ortak_dogrula(veri: dict, rol: str) -> Decimal:
    if veri.get("role") != rol:
        hata("HJ-05", f"{rol} dosyasinda role={veri.get('role')!r}")
    if veri.get("schema") != SURUM:
        hata("HJ-01", f"{rol}.schema beklenen {SURUM}")
    run_id = dolu_metin(veri.get("run_id"), f"{rol}.run_id")
    if not RUN_RE.fullmatch(run_id):
        hata("HJ-01", f"{rol}.run_id kanonik degil")
    if not SHA_RE.fullmatch(str(veri.get("input_sha256", ""))):
        hata("HJ-01", f"{rol}.input_sha256 sha256:<64 hex> olmali")
    for alan in ("provider", "model", "model_family"):
        dolu_metin(veri.get(alan), f"{rol}.{alan}")
    if not OTURUM_RE.fullmatch(str(veri.get("session_ref", ""))):
        hata("HJ-05", f"{rol}.session_ref gercek session: kaydi olmali")
    if type(veri.get("attempt")) is not int or veri["attempt"] != 1:
        hata("HJ-07", f"{rol}.attempt yalniz 1 olabilir; retry yasak")
    return maliyet(veri.get("cost_usd"), f"{rol}.cost_usd")


def finding_dogrula(finding: dict, etiket: str) -> str:
    if not isinstance(finding, dict):
        hata("HJ-01", f"{etiket} object olmali")
    tam_alanlar(finding, FINDING_ALANLARI, etiket)
    kimlik = dolu_metin(finding["finding_id"], f"{etiket}.finding_id")
    if not FINDING_RE.fullmatch(kimlik):
        hata("HJ-01", f"{etiket}.finding_id gecersiz: {kimlik}")
    if finding["severity"] not in SIDDETLER:
        hata("HJ-01", f"{etiket}.severity kapali listede degil")
    if finding["axis"] not in EKSENLER:
        hata("HJ-01", f"{etiket}.axis E1..E7 olmali")
    for alan in ("location", "quote", "claim", "recommendation"):
        dolu_metin(finding[alan], f"{etiket}.{alan}")
    if not KANIT_RE.fullmatch(str(finding["evidence_ref"])):
        hata("HJ-01", f"{etiket}.evidence_ref artifact:/source: olmali")
    return kimlik


def judgment_dogrula(judgment: dict, etiket: str) -> str:
    if not isinstance(judgment, dict):
        hata("HJ-01", f"{etiket} object olmali")
    tam_alanlar(judgment, JUDGMENT_ALANLARI, etiket)
    kimlik = dolu_metin(judgment["finding_id"], f"{etiket}.finding_id")
    if not FINDING_RE.fullmatch(kimlik) or kimlik.startswith("HJ-C"):
        hata("HJ-01", f"{etiket}.finding_id gecersiz: {kimlik}")
    if judgment["verdict"] not in HUKUMLER:
        hata("HJ-04", f"{etiket}.verdict kapali listede degil: {judgment['verdict']!r}")
    if judgment["severity"] not in SIDDETLER:
        hata("HJ-01", f"{etiket}.severity kapali listede degil")
    for alan in ("location", "rationale"):
        dolu_metin(judgment[alan], f"{etiket}.{alan}")
    if not KANIT_RE.fullmatch(str(judgment["evidence_ref"])):
        hata("HJ-04", f"{etiket}.evidence_ref kanitli hukum icin zorunlu")
    return kimlik


def dizi(veri: dict, alan: str, etiket: str, bos_olabilir: bool) -> list:
    deger = veri.get(alan)
    if not isinstance(deger, list):
        hata("HJ-01", f"{etiket}.{alan} liste olmali")
    if not bos_olabilir and not deger:
        hata("HJ-03", f"{etiket}.{alan} bos olamaz; denetim kaniti yok")
    return deger


def tekil_harita(ogeler: list, dogrulayici, etiket: str) -> dict[str, dict]:
    sonuc = {}
    for i, oge in enumerate(ogeler):
        kimlik = dogrulayici(oge, f"{etiket}[{i}]")
        if kimlik in sonuc:
            hata("HJ-03", f"{etiket} yinelenen kimlik: {kimlik}")
        sonuc[kimlik] = oge
    return sonuc


def panel_uret(main: dict, reviewer: dict, critic: dict, max_cost: Decimal) -> dict:
    tam_alanlar(main, MAIN_ALANLARI, "MAIN")
    tam_alanlar(reviewer, DENETCI_ALANLARI, "REVIEWER")
    tam_alanlar(critic, DENETCI_ALANLARI, "CRITIC")

    maliyetler = {
        "MAIN": ortak_dogrula(main, "MAIN"),
        "REVIEWER": ortak_dogrula(reviewer, "REVIEWER"),
        "CRITIC": ortak_dogrula(critic, "CRITIC"),
    }
    runlar = {d["run_id"] for d in (main, reviewer, critic)}
    hashler = {d["input_sha256"] for d in (main, reviewer, critic)}
    if len(runlar) != 1 or len(hashler) != 1:
        hata("HJ-02", f"run/input uyusmazligi; run={sorted(runlar)} hash={sorted(hashler)}")

    aileler = [d["model_family"].casefold() for d in (main, reviewer, critic)]
    oturumlar = [d["session_ref"] for d in (main, reviewer, critic)]
    if len(set(aileler)) != 3:
        hata("HJ-06", f"uc rol uc farkli model ailesi olmali: {aileler}")
    if len(set(oturumlar)) != 3:
        hata("HJ-06", "uc rol uc farkli gercek oturum kaydi tasimali")

    toplam = sum(maliyetler.values(), Decimal("0"))
    if toplam > max_cost:
        hata("HJ-07", f"COST_LIMIT: ${toplam} > ${max_cost}; retry/fallback yapma")

    main_h = tekil_harita(
        dizi(main, "findings", "MAIN", False), finding_dogrula, "MAIN.findings")
    reviewer_j = tekil_harita(
        dizi(reviewer, "judgments", "REVIEWER", False), judgment_dogrula,
        "REVIEWER.judgments")
    reviewer_yeni = tekil_harita(
        dizi(reviewer, "new_findings", "REVIEWER", True), finding_dogrula,
        "REVIEWER.new_findings")
    if set(reviewer_j) != set(main_h):
        hata("HJ-03", "REVIEWER, MAIN bulgularinin her birini tam bir kez hukumlemeli")
    if set(main_h) & set(reviewer_yeni):
        hata("HJ-03", "REVIEWER yeni bulgu kimligi MAIN ile cakismamali")

    critic_j = tekil_harita(
        dizi(critic, "judgments", "CRITIC", False), judgment_dogrula,
        "CRITIC.judgments")
    critic_yeni = tekil_harita(
        dizi(critic, "new_findings", "CRITIC", True), finding_dogrula,
        "CRITIC.new_findings")
    critic_beklenen = set(main_h) | set(reviewer_yeni)
    if set(critic_j) != critic_beklenen:
        hata("HJ-03", "CRITIC, MAIN + REVIEWER yeni bulgularinin tamamini hukumlemeli")
    if (set(main_h) | set(reviewer_yeni)) & set(critic_yeni):
        hata("HJ-03", "CRITIC yeni bulgu kimligi onceki kimliklerle cakismamali")

    for kimlik, bulgu in main_h.items():
        if reviewer_j[kimlik]["severity"] != bulgu["severity"]:
            hata("HJ-03", f"{kimlik} REVIEWER severity MAIN ile uyusmuyor")
        if critic_j[kimlik]["severity"] != bulgu["severity"]:
            hata("HJ-03", f"{kimlik} CRITIC severity MAIN ile uyusmuyor")
    for kimlik, bulgu in reviewer_yeni.items():
        if critic_j[kimlik]["severity"] != bulgu["severity"]:
            hata("HJ-03", f"{kimlik} CRITIC severity REVIEWER yeni bulguyla uyusmuyor")

    maddeler = []
    blok_nedenleri = []
    for kimlik in sorted(main_h):
        bulgu = main_h[kimlik]
        rv = reviewer_j[kimlik]["verdict"]
        cv = critic_j[kimlik]["verdict"]
        hukumler = {"MAIN": "AGREE", "REVIEWER": rv, "CRITIC": cv}
        evidence_n = sum(v == "DISAGREE_EVIDENCE" for v in hukumler.values())
        concern_n = sum(v == "DISAGREE_CONCERN" for v in hukumler.values())
        if evidence_n:
            # P1-8: pivotal yalniz gercek 2-1 evidence ayriligidir. Bir AGREE,
            # bir DISAGREE_EVIDENCE ve bir DISAGREE_CONCERN cogu(n)luk degildir;
            # bu 1-1-1 dagilim Gate-2C'ye devredilmeden insana gider.
            if evidence_n == 1 and concern_n == 0:
                durum = "PIVOTAL_PENDING_GATE_2C"
                neden = "PIVOTAL_EVIDENCE_DISAGREEMENT"
            elif evidence_n == 1:
                durum = "HUMAN_REVIEW_REQUIRED"
                neden = "THREE_WAY_SPLIT_HUMAN_REVIEW"
            else:
                durum = "HUMAN_REVIEW_REQUIRED"
                neden = "PANEL_MAJORITY_DISAGREES_EVIDENCE"
            blok_nedenleri.append(f"{kimlik}:{neden}")
        elif concern_n and bulgu["severity"] == "P0":
            durum = "HUMAN_REVIEW_REQUIRED"
            neden = "P0_CONCERN"
            blok_nedenleri.append(f"{kimlik}:{neden}")
        elif concern_n >= 2:
            durum = "HUMAN_REVIEW_REQUIRED"
            neden = "PANEL_MAJORITY_DISAGREES_CONCERN"
            blok_nedenleri.append(f"{kimlik}:{neden}")
        elif concern_n == 1:
            durum = "PANEL_MAJORITY_STANDS"
            neden = "MINORITY_CONCERN_RECORDED"
        else:
            durum = "UNANIMOUS_UNVERIFIED"
            neden = "UNANIMOUS_IS_NOT_EVIDENCE"
        maddeler.append({
            "finding_id": kimlik,
            "source_role": "MAIN",
            "severity": bulgu["severity"],
            "claim": bulgu["claim"],
            "votes": hukumler,
            "status": durum,
            "reason": neden,
            "evidence_refs": sorted({
                bulgu["evidence_ref"], reviewer_j[kimlik]["evidence_ref"],
                critic_j[kimlik]["evidence_ref"],
            }),
        })

    for kimlik in sorted(reviewer_yeni):
        bulgu = reviewer_yeni[kimlik]
        maddeler.append({
            "finding_id": kimlik,
            "source_role": "REVIEWER",
            "severity": bulgu["severity"],
            "claim": bulgu["claim"],
            "votes": {"REVIEWER": "AGREE", "CRITIC": critic_j[kimlik]["verdict"]},
            "status": "HUMAN_REVIEW_REQUIRED",
            "reason": "ADDED_AFTER_MAIN_NO_THREE_VOTES",
            "evidence_refs": sorted({bulgu["evidence_ref"], critic_j[kimlik]["evidence_ref"]}),
        })
        blok_nedenleri.append(f"{kimlik}:ADDED_AFTER_MAIN")

    for kimlik in sorted(critic_yeni):
        bulgu = critic_yeni[kimlik]
        maddeler.append({
            "finding_id": kimlik,
            "source_role": "CRITIC",
            "severity": bulgu["severity"],
            "claim": bulgu["claim"],
            "votes": {"CRITIC": "AGREE"},
            "status": "HUMAN_REVIEW_REQUIRED",
            "reason": "ADDED_BY_FINAL_ROLE_NO_REVIEW",
            "evidence_refs": [bulgu["evidence_ref"]],
        })
        blok_nedenleri.append(f"{kimlik}:ADDED_BY_CRITIC")

    return {
        "schema": "ATLAS-REVIEW-PANEL-RESULT/v1",
        "run_id": main["run_id"],
        "input_sha256": main["input_sha256"],
        "status": "BLOCKED" if blok_nedenleri else "PASS",
        "reason_codes": sorted(blok_nedenleri),
        "independence": "ROLE_SEPARATION_ONLY",
        "models": [
            {
                "role": rol,
                "provider": veri["provider"],
                "model": veri["model"],
                "model_family": veri["model_family"],
                "session_ref": veri["session_ref"],
            }
            for rol, veri in zip(ROLLER, (main, reviewer, critic))
        ],
        "cost_usd": float(toplam),
        "max_cost_usd": float(max_cost),
        "retries": 0,
        "items": sorted(maddeler, key=lambda x: x["finding_id"]),
        "fix_manifest_written": False,
    }


def argumanlar() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main", required=True, type=pathlib.Path)
    p.add_argument("--reviewer", required=True, type=pathlib.Path)
    p.add_argument("--critic", required=True, type=pathlib.Path)
    p.add_argument(
        "--schema", type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent.parent
        / "templates" / "REVIEW-PANEL-SCHEMA.json",
    )
    p.add_argument("--max-cost", default="1.00")
    p.add_argument("--output", type=pathlib.Path)
    return p.parse_args()


def main() -> int:
    args = argumanlar()
    try:
        try:
            max_cost = Decimal(args.max_cost)
        except InvalidOperation:
            hata("HJ-07", "--max-cost sayisal olmali")
        if not max_cost.is_finite() or max_cost <= 0:
            hata("HJ-07", "--max-cost sifirdan buyuk ve sonlu olmali")
        sema_dogrula(args.schema)
        artefaktlar = {
            "MAIN": json_oku(args.main, "MAIN"),
            "REVIEWER": json_oku(args.reviewer, "REVIEWER"),
            "CRITIC": json_oku(args.critic, "CRITIC"),
        }
        sonuc = panel_uret(
            artefaktlar["MAIN"], artefaktlar["REVIEWER"],
            artefaktlar["CRITIC"], max_cost,
        )
        metin = json.dumps(sonuc, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if args.output:
            try:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(metin, encoding="utf-8")
            except OSError as exc:
                hata("HJ-08", f"cikti yazilamadi: {exc}")
            print(
                f"REVIEW-PANEL {sonuc['status']} cost=${sonuc['cost_usd']:.2f}/"
                f"${sonuc['max_cost_usd']:.2f} retries=0 output={args.output}"
            )
        else:
            sys.stdout.write(metin)
        return 0 if sonuc["status"] == "PASS" else 2
    except PanelHatasi as exc:
        print(f"FAIL {exc.kod}: {exc.mesaj}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
