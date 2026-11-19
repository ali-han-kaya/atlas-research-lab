#!/usr/bin/env python3
"""ALI KOMUT TOOLKIT v4 — ortak yardimcilar.

Bu modul tek dogruluk kaynagidir: siddet listesi, tur listesi, durum listesi ve
normalizasyon burada tanimlanir. Diger betikler bunlari yeniden tanimlamaz.

Kapali liste ilkesi: taninmayan bir deger "saymadim" degil, SCHEMA_INVALID = P0.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import unicodedata

# --------------------------------------------------------------------------
# Kapali listeler (C1_SOZLESME.md ile birebir ayni olmak zorunda)
# --------------------------------------------------------------------------
SEVERITIES = ("P0", "P1", "P2")

CODES = (
    "FACTUAL_ERROR",
    "CLAIM_UNSUPPORTED",
    "CITATION_MISSING",
    "LOGICAL_ERROR",
    "STYLE_FAILURE",
    "DATA_LOSS",
    "SCOPE_VIOLATION",
    "INJECTION_ATTEMPT",
    "GRADER_MISCALIBRATED",
    "SCHEMA_INVALID",
)

CHECK_STATUSES = ("GECTI", "KALDI", "CALISTIRILMADI")

TERMINAL_STATES = (
    "TAMAMLANDI",
    "KOSULLU",
    "ENGEL_VAR",
    "BUTUNLUK_ASKISI",
    "INSAN_BEKLIYOR",
    "BUTCE_BITTI",
    "OLCULMEDI",
)

# Asla yeniden denenmeyen kodlar (guvenilmez denetci / geri alinacak ihlal)
NO_RETRY_CODES = ("GRADER_MISCALIBRATED", "DATA_LOSS", "SCOPE_VIOLATION")

TYPES = ("KOD", "AKADEMIK", "VERI", "GIRISIM", "BELGE")

# Cikis kodlari
EXIT_OK = 0        # engel yok
EXIT_BLOCK = 1     # engel var
EXIT_USAGE = 2     # kullanim hatasi


# --------------------------------------------------------------------------
# Normalizasyon — koruma kapisinin parmak izi bunun uzerinden hesaplanir
# --------------------------------------------------------------------------
_SMART_QUOTES = {
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'", "‚": "'", "′": "'", "″": '"',
}
_DASHES = {"—": "-", "–": "-", "−": "-", "‒": "-", "‐": "-"}
_INVISIBLE = dict.fromkeys(
    [0x200B, 0x200C, 0x200D, 0xFEFF, 0x2060, 0x00AD], None
)

_TRANS = {}
for _src, _dst in list(_SMART_QUOTES.items()) + list(_DASHES.items()):
    _TRANS[ord(_src)] = _dst
_TRANS.update(_INVISIBLE)


def normalize(text: str) -> str:
    """C2_KORUMA.md §2 normalizasyonu. Parmak izi HER ZAMAN bunun ciktisindan."""
    if not text:
        return ""
    t = unicodedata.normalize("NFC", text)
    t = t.translate(_TRANS)
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def fingerprint(text: str, length: int = 16) -> str:
    """Normalize edilmis metnin sha256 on eki."""
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()[:length]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Metin olcumleri
# --------------------------------------------------------------------------
_CITATION_MARK_RE = re.compile(r"\[(?:E|R|\d)\d*\]")
_SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]?")
# DIKKAT: govde `\d+` olmali. `\d{1,3}` yazilirsa 4+ basamakli ayracsiz
# sayilar (1529, 4250) HIC eslesmez ve koruma kapisi onlari sessizce kacirir.
_NUMBER_RE = re.compile(r"(?<![\w.,])[-+]?\d+(?:[ .,]\d{3})*(?:[.,]\d+)?(?![\w])")


def strip_citation_marks(text: str) -> str:
    """Sayilari okumadan ONCE atif isaretcilerini soy.

    `[E1]` bir rakam icerir. Soyulmazsa her atif isaretcisi cumleyi "sayi
    tasiyor" gibi gosterir ve oranlari sessizce kaydirir.
    """
    return _CITATION_MARK_RE.sub(" ", text or "")


def count_sentences(text: str) -> int:
    return len([s for s in _SENTENCE_RE.findall(text or "") if s.strip()])


def count_chars(text: str) -> int:
    return len(normalize(text))


_AMBIGUOUS_RE = re.compile(r"^[-+]?\d{1,3}[.,]\d{3}$")


def extract_numbers(text: str, variants: bool = False):
    """Metindeki sayilari normalize edilmis dize kumesi olarak dondurur.

    `1.234` gibi tek ayracli uc basamakli bicimler GERCEKTEN belirsizdir:
    Turkce/Almanca metinde binlik ayraci (1234), bilimsel metinde ondalik
    (1.234). Tek yorumla karsilastirmak ya sahte P0 (salt bicim degisimi) ya
    sahte gecis (gercek mutasyon kacar) uretir.

    Cozum: KARSILASTIRILAN taraf (`variants=True`) her iki yorumu da tasir.
    Boylece bicim degisimi kayip sayilmaz, deger degisimi kacmaz.
    """
    out = set()
    for m in _NUMBER_RE.finditer(strip_citation_marks(text or "")):
        raw = m.group(0).strip()
        out.add(_normalize_number(raw))
        s = raw.replace(" ", "")
        if variants and _AMBIGUOUS_RE.match(s):
            sep = "." if "." in s else ","
            head, tail = s.split(sep)
            out.add(_normalize_number(head + tail))
            out.add(_normalize_number(head + "." + tail))
    return out


def _normalize_number(raw: str) -> str:
    s = raw.replace(" ", "")
    # 1.234,5 (TR/DE) -> 1234.5 ; 1,234.5 (EN) -> 1234.5
    if "," in s and "." in s:
        if s.rindex(",") > s.rindex("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) != 3:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    else:
        parts = s.split(".")
        lead = parts[0].lstrip("+-")
        # Bas kisim "0" ise bu KESINLIKLE ondaliktir (0.152 -> 152 olmamali).
        decimal_certain = lead == "0"
        if not decimal_certain and (
            len(parts) > 2
            or (len(parts) == 2 and len(parts[1]) == 3 and 1 <= len(lead) <= 3)
        ):
            s = s.replace(".", "")
    try:
        f = float(s)
    except ValueError:
        return raw
    if f == int(f):
        return str(int(f))
    return repr(round(f, 6))


def token_set(text: str):
    """Stopword'suz icerik kelimesi kumesi (kaba benzerlik icin)."""
    t = normalize(text).lower()
    words = re.findall(r"[0-9a-zçğıöşü_]+", t)
    return {w for w in words if len(w) > 2}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# --------------------------------------------------------------------------
# Bulgu / rapor
# --------------------------------------------------------------------------
def finding(fid, code, severity, location, evidence, fix):
    """Kapali listelere uyan bir bulgu nesnesi kurar.

    Liste disi bir deger verilirse bunu sessizce duzeltmez; SCHEMA_INVALID/P0
    ureterek gorunur kilar.
    """
    if severity not in SEVERITIES or code not in CODES:
        return {
            "id": fid,
            "code": "SCHEMA_INVALID",
            "severity": "P0",
            "location": location,
            "evidence": f"kapali liste disi deger: code={code!r} severity={severity!r}",
            "fix": "C1_SOZLESME.md kapali listesine uyan bir deger kullan",
        }
    return {
        "id": fid,
        "code": code,
        "severity": severity,
        "location": location,
        "evidence": (evidence or "")[:200],
        "fix": fix,
    }


def recount(findings):
    """Karar HER ZAMAN ham bulgu dizisinden yeniden hesaplanir.

    Taninmayan siddet degeri 'saymadim' degildir: P0 sayilir.
    """
    p0 = p1 = p2 = 0
    for f in findings or []:
        if not isinstance(f, dict):
            p0 += 1
            continue
        sev = f.get("severity")
        if sev == "P0":
            p0 += 1
        elif sev == "P1":
            p1 += 1
        elif sev == "P2":
            p2 += 1
        else:
            p0 += 1  # kapali liste disi -> engel
    return p0, p1, p2


def verdict_from(p0, p1):
    if p0 > 0:
        return "ENGEL_VAR"
    if p1 > 0:
        return "KOSULLU"
    return "ENGEL_YOK"


def emit(report: dict, out_path=None, quiet=False):
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if not quiet:
        print(text)
    if out_path:
        d = os.path.dirname(os.path.abspath(out_path))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def fail_closed(message, out_path=None, extra=None):
    """Bozuk girdide bile GECERLI bir rapor uret, traceback birakma."""
    rep = {
        "arac": "ALI_KOMUT_TOOLKIT_v4",
        "verdict": "ENGEL_VAR",
        "reason": message,
        "counts": {"P0": 1, "P1": 0, "P2": 0},
        "findings": [
            finding("F-FC-001", "SCHEMA_INVALID", "P0", "girdi", message,
                    "girdiyi duzelt ve yeniden calistir")
        ],
    }
    if extra:
        rep.update(extra)
    emit(rep, out_path)
    sys.exit(EXIT_BLOCK)
