#!/usr/bin/env python3
"""P1-8 Gate-2C — pivotal/high-stakes birincil kaynak istisnasi.

Gate-2C bir oy DEGILDIR. P1-7 panelinin ham oylarini yeniden hesaplar ve
yalniz iki AGREE + bir DISAGREE_EVIDENCE (concern yok) ya da disa cikacak
primary_source_locator icin kesin Crossref DOI kaydina bakar. Ag hatasi,
bozuk yanit ve eksik kanit fail-closed BLOCKED olur; retry yapilmaz.

Exit kodlari:
  0  Gate-2C PASS veya kayitli PASS ciktisi gecerli
  1  Girdi/sema/hash sozlesmesi gecersiz
  2  Ag/belirsizlik/insan incelemesi nedeniyle BLOCKED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import unicodedata


SEMA_KIMLIGI = "ATLAS-GATE-2C-SCHEMA/v1"
ISTEK_SURUMU = "ATLAS-GATE-2C-REQUEST/v1"
SONUC_SURUMU = "ATLAS-GATE-2C-RESULT/v1"
HUKUMLER = {"AGREE", "DISAGREE_EVIDENCE", "DISAGREE_CONCERN"}
ROLLER = {"MAIN", "REVIEWER", "CRITIC"}
SINIFLAR = {"primary_source_locator", "other"}
SAGLAYICILAR = {"CROSSREF_DOI", "NONE"}
TARAFLAR = {"PANEL_MAJORITY", "EVIDENCE_MINORITY"}
TETIKLER = {
    "PIVOTAL_EVIDENCE_DISAGREEMENT",
    "HIGH_STAKES_PRIMARY_SOURCE_LOCATOR",
}
BLOK_DURUMLARI = {"BLOCKED_HUMAN_REVIEW_REQUIRED", "HUMAN_REVIEW_REQUIRED"}
SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FINDING_RE = re.compile(r"^HJ-(?:[0-9]{3}|R[0-9]{3}|C[0-9]{3})$")
KANIT_RE = re.compile(r"^(?:artifact|source):\S+$")
DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$", re.I)

PANEL_ALANLARI = {
    "schema", "run_id", "input_sha256", "status", "reason_codes",
    "independence", "models", "cost_usd", "max_cost_usd", "retries",
    "items", "fix_manifest_written",
}
PANEL_MADDE_ALANLARI = {
    "finding_id", "source_role", "severity", "claim", "votes", "status",
    "reason", "evidence_refs",
}
MODEL_ALANLARI = {
    "role", "provider", "model", "model_family", "session_ref",
}
ISTEK_ALANLARI = {"schema", "run_id", "panel_sha256", "items"}
ISTEK_MADDE_ALANLARI = {
    "finding_id", "claim_sha256", "claim_class", "external_bound",
    "locator", "propositions", "classification_evidence_ref",
}
LOKATOR_ALANLARI = {"provider", "identifier"}
ONERME_ALANLARI = {"side", "expected"}
BEKLENTI_ALANLARI = {"doi", "title", "published_year"}
SONUC_ALANLARI = {
    "schema", "run_id", "panel_sha256", "request_sha256", "verdict",
    "reason_codes", "network_calls", "retries", "items",
    "dersler_written", "fix_manifest_written",
}
SONUC_MADDE_ALANLARI = {
    "finding_id", "panel_status", "triggered", "trigger_reasons", "provider",
    "status", "winner_side", "wrong_sides", "http_status", "primary_record",
    "response_sha256",
}
KAYIT_ALANLARI = {"doi", "title", "published_years"}


class Gate2CHatasi(Exception):
    def __init__(self, kod: str, mesaj: str):
        super().__init__(mesaj)
        self.kod = kod
        self.mesaj = mesaj


def hata(kod: str, mesaj: str) -> None:
    raise Gate2CHatasi(kod, mesaj)


def sha256(ham: bytes) -> str:
    return "sha256:" + hashlib.sha256(ham).hexdigest()


def metin_sha256(metin: str) -> str:
    return sha256(metin.encode("utf-8"))


def json_oku(yol: pathlib.Path, etiket: str) -> tuple[dict, bytes]:
    try:
        ham = yol.read_bytes()
    except OSError as exc:
        hata("G2C-00", f"{etiket} okunamadi: {exc}")
    try:
        veri = json.loads(ham.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        hata("G2C-01", f"{etiket} JSON gecersiz: {exc}")
    if not isinstance(veri, dict):
        hata("G2C-01", f"{etiket} kok nesnesi object olmali")
    return veri, ham


def tam_alanlar(nesne: dict, beklenen: set[str], etiket: str) -> None:
    if not isinstance(nesne, dict):
        hata("G2C-01", f"{etiket} object olmali")
    gercek = set(nesne)
    if gercek != beklenen:
        hata(
            "G2C-01",
            f"{etiket} kapali sema ihlali; "
            f"eksik={sorted(beklenen - gercek)} fazla={sorted(gercek - beklenen)}",
        )


def dolu_metin(deger, etiket: str) -> str:
    if not isinstance(deger, str) or not deger.strip():
        hata("G2C-01", f"{etiket} dolu metin olmali")
    return deger.strip()


def sha_dogrula(deger, etiket: str) -> str:
    if not isinstance(deger, str) or not SHA_RE.fullmatch(deger):
        hata("G2C-01", f"{etiket} sha256:<64 kucuk hex> olmali")
    return deger


def sema_dogrula(yol: pathlib.Path) -> None:
    sema, _ = json_oku(yol, "Gate-2C semasi")
    if sema.get("$id") != SEMA_KIMLIGI:
        hata("G2C-00", f"sema kimligi beklenenden farkli: {sema.get('$id')!r}")
    try:
        siniflar = set(sema["$defs"]["claimClass"]["enum"])
        saglayicilar = set(sema["$defs"]["provider"]["enum"])
        sonuc_durumlari = set(
            sema["$defs"]["resultItem"]["properties"]["status"]["enum"]
        )
    except (KeyError, TypeError):
        hata("G2C-00", "sema kapali sinif/saglayici/sonuc listelerini tasimiyor")
    beklenen_durumlar = {
        "PANEL_STATUS_STANDS", "RESOLVED_BY_PRIMARY_SOURCE",
        "BLOCKED_HUMAN_REVIEW_REQUIRED", "HUMAN_REVIEW_REQUIRED",
    }
    if siniflar != SINIFLAR or saglayicilar != SAGLAYICILAR:
        hata("G2C-00", "sema kodun sinif/saglayici sozlesmesiyle uyusmuyor")
    if sonuc_durumlari != beklenen_durumlar:
        hata("G2C-00", "sema kodun sonuc sozlesmesiyle uyusmuyor")


def panel_dogrula(panel: dict) -> dict[str, dict]:
    tam_alanlar(panel, PANEL_ALANLARI, "panel")
    if panel["schema"] != "ATLAS-REVIEW-PANEL-RESULT/v1":
        hata("G2C-01", "panel.schema beklenen ATLAS-REVIEW-PANEL-RESULT/v1")
    dolu_metin(panel["run_id"], "panel.run_id")
    sha_dogrula(panel["input_sha256"], "panel.input_sha256")
    if panel["status"] not in {"PASS", "BLOCKED"}:
        hata("G2C-01", "panel.status PASS|BLOCKED olmali")
    if not isinstance(panel["reason_codes"], list) or not all(
            isinstance(x, str) and x for x in panel["reason_codes"]):
        hata("G2C-01", "panel.reason_codes metin listesi olmali")
    if panel["independence"] != "ROLE_SEPARATION_ONLY":
        hata("G2C-01", "panel.independence ROLE_SEPARATION_ONLY olmali")
    if type(panel["retries"]) is not int or panel["retries"] != 0:
        hata("G2C-01", "panel.retries sifir olmali")
    if panel["fix_manifest_written"] is not False:
        hata("G2C-01", "panel FIX-MANIFEST'e yazmis olamaz")
    if not isinstance(panel["models"], list) or len(panel["models"]) != 3:
        hata("G2C-01", "panel.models uc kayit olmali")
    roller = set()
    for i, model in enumerate(panel["models"]):
        tam_alanlar(model, MODEL_ALANLARI, f"panel.models[{i}]")
        if model["role"] not in ROLLER:
            hata("G2C-01", f"panel.models[{i}].role gecersiz")
        roller.add(model["role"])
        for alan in ("provider", "model", "model_family", "session_ref"):
            dolu_metin(model[alan], f"panel.models[{i}].{alan}")
    if roller != ROLLER:
        hata("G2C-01", "panel.models MAIN/REVIEWER/CRITIC tam olmali")
    if not isinstance(panel["items"], list) or not panel["items"]:
        hata("G2C-01", "panel.items bos olamaz")
    sonuc = {}
    for i, madde in enumerate(panel["items"]):
        etiket = f"panel.items[{i}]"
        tam_alanlar(madde, PANEL_MADDE_ALANLARI, etiket)
        kimlik = dolu_metin(madde["finding_id"], f"{etiket}.finding_id")
        if not FINDING_RE.fullmatch(kimlik) or kimlik in sonuc:
            hata("G2C-01", f"{etiket}.finding_id gecersiz/yinelenen")
        if madde["source_role"] not in ROLLER:
            hata("G2C-01", f"{etiket}.source_role gecersiz")
        if madde["severity"] not in {"P0", "P1", "P2"}:
            hata("G2C-01", f"{etiket}.severity gecersiz")
        dolu_metin(madde["claim"], f"{etiket}.claim")
        dolu_metin(madde["status"], f"{etiket}.status")
        dolu_metin(madde["reason"], f"{etiket}.reason")
        if not isinstance(madde["votes"], dict) or not madde["votes"]:
            hata("G2C-01", f"{etiket}.votes object olmali")
        if not set(madde["votes"]) <= ROLLER or not all(
                v in HUKUMLER for v in madde["votes"].values()):
            hata("G2C-01", f"{etiket}.votes kapali hukumleri asmamali")
        if not isinstance(madde["evidence_refs"], list) or not madde["evidence_refs"]:
            hata("G2C-01", f"{etiket}.evidence_refs bos olamaz")
        if not all(isinstance(x, str) and KANIT_RE.fullmatch(x)
                   for x in madde["evidence_refs"]):
            hata("G2C-01", f"{etiket}.evidence_refs gecersiz")
        sonuc[kimlik] = madde
    return sonuc


def pivotal(madde: dict) -> bool:
    if madde["source_role"] != "MAIN" or set(madde["votes"]) != ROLLER:
        return False
    oylar = list(madde["votes"].values())
    return (
        oylar.count("AGREE") == 2
        and oylar.count("DISAGREE_EVIDENCE") == 1
        and oylar.count("DISAGREE_CONCERN") == 0
    )


def doi_norm(deger: str) -> str:
    d = unicodedata.normalize("NFC", deger).strip()
    d = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", d, flags=re.I)
    return d.casefold()


def metin_norm(deger: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", deger)).strip().casefold()


def istek_dogrula(istek: dict, panel: dict, panel_ham: bytes,
                  panel_maddeleri: dict[str, dict]) -> dict[str, dict]:
    tam_alanlar(istek, ISTEK_ALANLARI, "request")
    if istek["schema"] != ISTEK_SURUMU:
        hata("G2C-01", f"request.schema beklenen {ISTEK_SURUMU}")
    if istek["run_id"] != panel["run_id"]:
        hata("G2C-02", "request.run_id panel ile uyusmuyor")
    sha_dogrula(istek["panel_sha256"], "request.panel_sha256")
    if istek["panel_sha256"] != sha256(panel_ham):
        hata("G2C-02", "request.panel_sha256 gercek panel hash'iyle uyusmuyor")
    if not isinstance(istek["items"], list) or not istek["items"]:
        hata("G2C-01", "request.items bos olamaz")
    sonuc = {}
    for i, madde in enumerate(istek["items"]):
        etiket = f"request.items[{i}]"
        tam_alanlar(madde, ISTEK_MADDE_ALANLARI, etiket)
        kimlik = dolu_metin(madde["finding_id"], f"{etiket}.finding_id")
        if not FINDING_RE.fullmatch(kimlik) or kimlik in sonuc:
            hata("G2C-01", f"{etiket}.finding_id gecersiz/yinelenen")
        sha_dogrula(madde["claim_sha256"], f"{etiket}.claim_sha256")
        if kimlik not in panel_maddeleri:
            hata("G2C-02", f"request panelde olmayan madde tasiyor: {kimlik}")
        if madde["claim_sha256"] != metin_sha256(panel_maddeleri[kimlik]["claim"]):
            hata("G2C-02", f"{kimlik} claim hash uyusmazligi")
        if madde["claim_class"] not in SINIFLAR:
            hata("G2C-01", f"{kimlik} claim_class kapali listede degil")
        if type(madde["external_bound"]) is not bool:
            hata("G2C-01", f"{kimlik} external_bound boolean olmali")
        if not KANIT_RE.fullmatch(str(madde["classification_evidence_ref"])):
            hata("G2C-01", f"{kimlik} classification_evidence_ref gecersiz")
        tam_alanlar(madde["locator"], LOKATOR_ALANLARI, f"{etiket}.locator")
        provider = madde["locator"]["provider"]
        identifier = dolu_metin(madde["locator"]["identifier"],
                                f"{etiket}.locator.identifier")
        if provider not in SAGLAYICILAR:
            hata("G2C-01", f"{kimlik} locator.provider kapali listede degil")
        if not isinstance(madde["propositions"], list):
            hata("G2C-01", f"{kimlik}.propositions liste olmali")
        taraflar = set()
        for j, onerme in enumerate(madde["propositions"]):
            oetiket = f"{etiket}.propositions[{j}]"
            tam_alanlar(onerme, ONERME_ALANLARI, oetiket)
            if onerme["side"] not in TARAFLAR or onerme["side"] in taraflar:
                hata("G2C-01", f"{oetiket}.side gecersiz/yinelenen")
            taraflar.add(onerme["side"])
            tam_alanlar(onerme["expected"], BEKLENTI_ALANLARI,
                        f"{oetiket}.expected")
            beklenen = onerme["expected"]
            if not DOI_RE.fullmatch(str(beklenen["doi"])):
                hata("G2C-01", f"{oetiket}.expected.doi gecersiz")
            dolu_metin(beklenen["title"], f"{oetiket}.expected.title")
            if (type(beklenen["published_year"]) is not int
                    or not 1000 <= beklenen["published_year"] <= 9999):
                hata("G2C-01", f"{oetiket}.expected.published_year gecersiz")
        if madde["claim_class"] == "other":
            if madde["external_bound"] or provider != "NONE" \
                    or identifier != "UYGULANMAZ" or madde["propositions"]:
                hata("G2C-01", f"{kimlik} other sinifi NONE/bos olmali")
        else:
            if provider != "CROSSREF_DOI" or not DOI_RE.fullmatch(identifier):
                hata("G2C-01", f"{kimlik} ilk adaptorde kesin Crossref DOI ister")
            if "PANEL_MAJORITY" not in taraflar:
                hata("G2C-01", f"{kimlik} PANEL_MAJORITY onermesi zorunlu")
            if pivotal(panel_maddeleri[kimlik]) and "EVIDENCE_MINORITY" not in taraflar:
                hata("G2C-01", f"{kimlik} pivotal karsi onerme eksik")
        sonuc[kimlik] = madde
    if set(sonuc) != set(panel_maddeleri):
        eksik = sorted(set(panel_maddeleri) - set(sonuc))
        fazla = sorted(set(sonuc) - set(panel_maddeleri))
        hata("G2C-02", f"request paneli tam kapsamiyor; eksik={eksik} fazla={fazla}")
    return sonuc


def tetik_nedenleri(panel_maddesi: dict, istek_maddesi: dict) -> list[str]:
    sonuc = []
    pvt = pivotal(panel_maddesi)
    beyan_pvt = panel_maddesi["status"] == "PIVOTAL_PENDING_GATE_2C"
    if pvt != beyan_pvt:
        hata("G2C-03", f"{panel_maddesi['finding_id']} pivotal beyan/oy uyusmazligi")
    if pvt:
        sonuc.append("PIVOTAL_EVIDENCE_DISAGREEMENT")
    if (istek_maddesi["external_bound"]
            and istek_maddesi["claim_class"] == "primary_source_locator"):
        sonuc.append("HIGH_STAKES_PRIMARY_SOURCE_LOCATOR")
    return sonuc


def crossref_kaydi(identifier: str) -> tuple[str, dict | None, int | None, str | None]:
    try:
        import requests
    except ImportError:
        return "BLOCKED_HUMAN_REVIEW_REQUIRED", None, None, None
    try:
        yanit = requests.get(
            f"https://api.crossref.org/works/{identifier}",
            timeout=10,
            headers={"User-Agent": "Atlas-Gate-2C/v1 (mailto:atlas@local)"},
        )
    except Exception:
        return "BLOCKED_HUMAN_REVIEW_REQUIRED", None, None, None
    durum = getattr(yanit, "status_code", None)
    if type(durum) is not int:
        return "BLOCKED_HUMAN_REVIEW_REQUIRED", None, None, None
    if durum == 429 or durum >= 500:
        return "BLOCKED_HUMAN_REVIEW_REQUIRED", None, durum, None
    if durum != 200:
        return "HUMAN_REVIEW_REQUIRED", None, durum, None
    try:
        ham_veri = yanit.json()
        mesaj = ham_veri["message"]
        doi = dolu_metin(mesaj["DOI"], "Crossref.message.DOI")
        basliklar = mesaj["title"]
        if not isinstance(basliklar, list) or not basliklar:
            raise ValueError("title yok")
        baslik = dolu_metin(basliklar[0], "Crossref.message.title[0]")
        yillar = set()
        for alan in ("published", "published-print", "published-online", "issued"):
            parcalar = mesaj.get(alan, {}).get("date-parts", [])
            if isinstance(parcalar, list):
                for parca in parcalar:
                    if (isinstance(parca, list) and parca
                            and type(parca[0]) is int and 1000 <= parca[0] <= 9999):
                        yillar.add(parca[0])
        if not yillar or doi_norm(doi) != doi_norm(identifier):
            raise ValueError("DOI/yil kaydi uyusmuyor")
        kayit = {
            "doi": doi_norm(doi),
            "title": baslik,
            "published_years": sorted(yillar),
        }
        cevap_hash = sha256(json.dumps(
            ham_veri, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"))
        return "OK", kayit, durum, cevap_hash
    except Exception:
        return "BLOCKED_HUMAN_REVIEW_REQUIRED", None, durum, None


def onerme_eslesir(onerme: dict, kayit: dict) -> bool:
    beklenen = onerme["expected"]
    return (
        doi_norm(beklenen["doi"]) == kayit["doi"]
        and metin_norm(beklenen["title"]) == metin_norm(kayit["title"])
        and beklenen["published_year"] in kayit["published_years"]
    )


def sonuc_uret(panel: dict, panel_ham: bytes, istek: dict, istek_ham: bytes,
               panel_maddeleri: dict[str, dict],
               istek_maddeleri: dict[str, dict]) -> dict:
    maddeler = []
    nedenler = []
    ag_cagrisi = 0
    ag_kesildi = False
    for kimlik in sorted(panel_maddeleri):
        pm = panel_maddeleri[kimlik]
        im = istek_maddeleri[kimlik]
        tetikler = tetik_nedenleri(pm, im)
        durum = "PANEL_STATUS_STANDS"
        kazanan = None
        yanlislar = []
        http = None
        kayit = None
        cevap_hash = None
        provider = im["locator"]["provider"]
        panel_insan = pm["status"] == "HUMAN_REVIEW_REQUIRED"
        if tetikler:
            if provider != "CROSSREF_DOI":
                durum = "HUMAN_REVIEW_REQUIRED"
            elif ag_kesildi:
                durum = "BLOCKED_HUMAN_REVIEW_REQUIRED"
            else:
                ag_cagrisi += 1
                dis_durum, kayit, http, cevap_hash = crossref_kaydi(
                    im["locator"]["identifier"])
                if dis_durum != "OK":
                    durum = dis_durum
                    if dis_durum == "BLOCKED_HUMAN_REVIEW_REQUIRED":
                        ag_kesildi = True
                else:
                    eslesenler = [p["side"] for p in im["propositions"]
                                  if onerme_eslesir(p, kayit)]
                    if len(eslesenler) == 1:
                        kazanan = eslesenler[0]
                        yanlislar = sorted(
                            p["side"] for p in im["propositions"]
                            if p["side"] != kazanan
                        )
                        durum = "RESOLVED_BY_PRIMARY_SOURCE"
                    else:
                        durum = "HUMAN_REVIEW_REQUIRED"
            if panel_insan and durum == "RESOLVED_BY_PRIMARY_SOURCE":
                durum = "HUMAN_REVIEW_REQUIRED"
        elif panel_insan:
            durum = "HUMAN_REVIEW_REQUIRED"
        if durum in BLOK_DURUMLARI:
            nedenler.append(f"{kimlik}:{durum}")
        maddeler.append({
            "finding_id": kimlik,
            "panel_status": pm["status"],
            "triggered": bool(tetikler),
            "trigger_reasons": tetikler,
            "provider": provider,
            "status": durum,
            "winner_side": kazanan,
            "wrong_sides": yanlislar,
            "http_status": http,
            "primary_record": kayit,
            "response_sha256": cevap_hash,
        })
    return {
        "schema": SONUC_SURUMU,
        "run_id": panel["run_id"],
        "panel_sha256": sha256(panel_ham),
        "request_sha256": sha256(istek_ham),
        "verdict": "BLOCKED" if nedenler else "PASS",
        "reason_codes": sorted(nedenler),
        "network_calls": ag_cagrisi,
        "retries": 0,
        "items": maddeler,
        "dersler_written": False,
        "fix_manifest_written": False,
    }


def kayit_dogrula(kayit, etiket: str) -> None:
    tam_alanlar(kayit, KAYIT_ALANLARI, etiket)
    if not DOI_RE.fullmatch(str(kayit["doi"])):
        hata("G2C-04", f"{etiket}.doi gecersiz")
    dolu_metin(kayit["title"], f"{etiket}.title")
    if not isinstance(kayit["published_years"], list) or not kayit["published_years"]:
        hata("G2C-04", f"{etiket}.published_years bos olamaz")
    if not all(type(y) is int and 1000 <= y <= 9999 for y in kayit["published_years"]):
        hata("G2C-04", f"{etiket}.published_years gecersiz")


def sonuc_dogrula(sonuc: dict, panel: dict, panel_ham: bytes,
                  istek: dict, istek_ham: bytes,
                  panel_maddeleri: dict[str, dict],
                  istek_maddeleri: dict[str, dict]) -> None:
    tam_alanlar(sonuc, SONUC_ALANLARI, "result")
    if sonuc["schema"] != SONUC_SURUMU or sonuc["run_id"] != panel["run_id"]:
        hata("G2C-04", "result schema/run_id uyusmazligi")
    if sonuc["panel_sha256"] != sha256(panel_ham):
        hata("G2C-04", "result panel_sha256 bayat/yanlis")
    if sonuc["request_sha256"] != sha256(istek_ham):
        hata("G2C-04", "result request_sha256 bayat/yanlis")
    if sonuc["verdict"] not in {"PASS", "BLOCKED"}:
        hata("G2C-04", "result.verdict gecersiz")
    if type(sonuc["network_calls"]) is not int or sonuc["network_calls"] < 0:
        hata("G2C-04", "result.network_calls gecersiz")
    if sonuc["retries"] != 0 or sonuc["dersler_written"] is not False \
            or sonuc["fix_manifest_written"] is not False:
        hata("G2C-04", "result retry/otomatik yazma sozlesmesini ihlal ediyor")
    if not isinstance(sonuc["items"], list):
        hata("G2C-04", "result.items liste olmali")
    gorulen = set()
    bloklar = []
    for i, madde in enumerate(sonuc["items"]):
        etiket = f"result.items[{i}]"
        tam_alanlar(madde, SONUC_MADDE_ALANLARI, etiket)
        kimlik = madde["finding_id"]
        if kimlik not in panel_maddeleri or kimlik in gorulen:
            hata("G2C-04", f"{etiket}.finding_id gecersiz/yinelenen")
        gorulen.add(kimlik)
        tetikler = tetik_nedenleri(panel_maddeleri[kimlik], istek_maddeleri[kimlik])
        if madde["panel_status"] != panel_maddeleri[kimlik]["status"]:
            hata("G2C-04", f"{kimlik} panel_status uyusmazligi")
        if madde["triggered"] is not bool(tetikler) or madde["trigger_reasons"] != tetikler:
            hata("G2C-04", f"{kimlik} tetik beyan/hesap uyusmazligi")
        if madde["provider"] != istek_maddeleri[kimlik]["locator"]["provider"]:
            hata("G2C-04", f"{kimlik} provider uyusmazligi")
        if madde["status"] not in {
            "PANEL_STATUS_STANDS", "RESOLVED_BY_PRIMARY_SOURCE",
            "BLOCKED_HUMAN_REVIEW_REQUIRED", "HUMAN_REVIEW_REQUIRED",
        }:
            hata("G2C-04", f"{kimlik} status gecersiz")
        if madde["winner_side"] is not None and madde["winner_side"] not in TARAFLAR:
            hata("G2C-04", f"{kimlik} winner_side gecersiz")
        if not isinstance(madde["wrong_sides"], list) or not all(
                x in TARAFLAR for x in madde["wrong_sides"]):
            hata("G2C-04", f"{kimlik} wrong_sides gecersiz")
        if madde["response_sha256"] is not None:
            sha_dogrula(madde["response_sha256"], f"{etiket}.response_sha256")
        if madde["primary_record"] is not None:
            kayit_dogrula(madde["primary_record"], f"{etiket}.primary_record")
        if madde["status"] == "RESOLVED_BY_PRIMARY_SOURCE":
            if not tetikler or madde["primary_record"] is None \
                    or madde["response_sha256"] is None:
                hata("G2C-04", f"{kimlik} cozum kaniti eksik")
            eslesenler = [
                p["side"] for p in istek_maddeleri[kimlik]["propositions"]
                if onerme_eslesir(p, madde["primary_record"])
            ]
            if len(eslesenler) != 1 or madde["winner_side"] != eslesenler[0]:
                hata("G2C-04", f"{kimlik} cozum yeniden hesaplamayla uyusmuyor")
            beklenen_yanlis = sorted(
                p["side"] for p in istek_maddeleri[kimlik]["propositions"]
                if p["side"] != eslesenler[0]
            )
            if madde["wrong_sides"] != beklenen_yanlis:
                hata("G2C-04", f"{kimlik} wrong_sides uyusmuyor")
        if not tetikler and panel_maddeleri[kimlik]["status"] != "HUMAN_REVIEW_REQUIRED" \
                and madde["status"] != "PANEL_STATUS_STANDS":
            hata("G2C-04", f"{kimlik} tetiksiz hukum degistirilemez")
        if panel_maddeleri[kimlik]["status"] == "HUMAN_REVIEW_REQUIRED" \
                and madde["status"] != "HUMAN_REVIEW_REQUIRED":
            hata("G2C-04", f"{kimlik} insan blokaji override edilemez")
        if madde["status"] in BLOK_DURUMLARI:
            bloklar.append(f"{kimlik}:{madde['status']}")
    if gorulen != set(panel_maddeleri):
        hata("G2C-04", "result panel maddelerini tam kapsamiyor")
    beklenen_verdict = "BLOCKED" if bloklar else "PASS"
    if sonuc["verdict"] != beklenen_verdict or sonuc["reason_codes"] != sorted(bloklar):
        hata("G2C-04", "result verdict/reason_codes yeniden hesaplamayla uyusmuyor")


def argumanlar() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--panel", required=True, type=pathlib.Path)
    p.add_argument("--request", required=True, type=pathlib.Path)
    p.add_argument(
        "--schema", type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parent.parent
        / "templates" / "GATE-2C-SCHEMA.json",
    )
    p.add_argument("--output", type=pathlib.Path)
    p.add_argument("--check-output", type=pathlib.Path)
    return p.parse_args()


def main() -> int:
    args = argumanlar()
    try:
        sema_dogrula(args.schema)
        panel, panel_ham = json_oku(args.panel, "FINAL-PANEL")
        panel_maddeleri = panel_dogrula(panel)
        istek, istek_ham = json_oku(args.request, "GATE-2C-REQUEST")
        istek_maddeleri = istek_dogrula(
            istek, panel, panel_ham, panel_maddeleri)
        # Pivotal beyan/oy celiskisini agdan once, her maddede fail-closed denetle.
        for kimlik in sorted(panel_maddeleri):
            tetik_nedenleri(panel_maddeleri[kimlik], istek_maddeleri[kimlik])
        if args.check_output:
            sonuc, _ = json_oku(args.check_output, "GATE-2C-RESULT")
            sonuc_dogrula(
                sonuc, panel, panel_ham, istek, istek_ham,
                panel_maddeleri, istek_maddeleri,
            )
            print(
                f"GATE-2C CHECK {sonuc['verdict']} "
                f"items={len(sonuc['items'])} retries=0"
            )
            return 0 if sonuc["verdict"] == "PASS" else 2
        sonuc = sonuc_uret(
            panel, panel_ham, istek, istek_ham,
            panel_maddeleri, istek_maddeleri,
        )
        sonuc_dogrula(
            sonuc, panel, panel_ham, istek, istek_ham,
            panel_maddeleri, istek_maddeleri,
        )
        metin = json.dumps(sonuc, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
        if args.output:
            try:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(metin, encoding="utf-8")
            except OSError as exc:
                hata("G2C-05", f"cikti yazilamadi: {exc}")
            print(
                f"GATE-2C {sonuc['verdict']} calls={sonuc['network_calls']} "
                f"retries=0 output={args.output}"
            )
        else:
            sys.stdout.write(metin)
        return 0 if sonuc["verdict"] == "PASS" else 2
    except Gate2CHatasi as exc:
        print(f"FAIL {exc.kod}: {exc.mesaj}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
