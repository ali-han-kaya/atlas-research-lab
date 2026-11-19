#!/usr/bin/env python3
"""ALI KOMUT TOOLKIT v4 — KORUMA KAPISI

    python3 v4_preserve.py <ONCE> <SONRA> [--tip AKADEMIK] [--niyet niyet.json]
                           [--bulgular bulgular.json] [--out rapor.json] [--sessiz]

Tek isi var: "iyilestirme" adi altinda kaliteli icerigin kaybolmadigini OLCMEK.

Temel ilkeler (C2_KORUMA.md):
  * Karsilastirma DAIMA orijinale karsi yapilir, onceki tura karsi asla.
  * Parmak izi birebir metin degil, normalize edilmis bolumun sha256'sidir.
    (Birebir metnin ilk N karakterini saklamak bir capa degil, bir on ektir:
     on ek korunurken govde yok edilebilir.)
  * Bir olcum hicbir sey cikaramiyorsa bu "temiz" degil INDETERMINATE'dir = P0.
  * Sessiz deger degisimi kaybin ustundedir: P0. Tek istisna, o konumu
    kapsayan IMZALI niyet kaydidir; o zaman P1'e iner ama rapordan
    SILINMEZ - gerekce ve imza gorunur, yani degisim 'sessiz' kalmaz.

Cikis: 0 = engel yok, 1 = engel var, 2 = kullanim hatasi.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v4_common import (  # noqa: E402
    EXIT_BLOCK, EXIT_OK, EXIT_USAGE, count_chars, count_sentences, emit,
    extract_numbers, fail_closed, finding, fingerprint, jaccard, normalize,
    recount, token_set, verdict_from,
)

TEXT_EXT = {".md", ".txt", ".rst", ".org", ".tex", ".markdown", ""}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb",
            ".php", ".c", ".h", ".cpp", ".hpp", ".cs", ".kt", ".swift", ".sh"}
DATA_EXT = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env", ".csv", ".tsv"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".docx",
            ".xlsx", ".pptx", ".zip", ".gz", ".woff", ".woff2", ".ttf", ".mp4"}
SKIP_DIR = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next",
            "dist", "build", ".pytest_cache", "__MACOSX", ".mypy_cache"}

# Sablon / otomatik uretilen icerik: kaybi mesru sayilir
TEMPLATE_PATTERNS = [
    r"^icindekiler$", r"^table of contents$", r"^toc$", r"^inhaltsverzeichnis$",
    r"^lisans$", r"^license$", r"^copyright", r"^\s*$",
]

# --- desenler -------------------------------------------------------------
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*$", re.M)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)
ARXIV_RE = re.compile(r"\barXiv:\s*\d{4}\.\d{4,5}(v\d+)?\b", re.I)
URL_RE = re.compile(r"https?://[^\s)\]}>\"']+")
AUTHORYEAR_RE = re.compile(r"\(([A-ZÇĞİÖŞÜ][\wçğıöşü'’-]+(?:\s+(?:ve|and|&|et al\.?)\s*[\wçğıöşü'’.-]*)?),\s*(1[89]\d{2}|20\d{2})[a-z]?\)")
EMARK_RE = re.compile(r"\[E\d+\]")

PY_TEST_RE = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)\s*\(", re.M)
JS_TEST_RE = re.compile(r"""^\s*(?:it|test)\s*\(\s*['"`](.+?)['"`]""", re.M)

JS_FUNC_RE = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)", re.M)
JS_ARROW_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>", re.M)
JS_CLASS_RE = re.compile(r"^\s*(?:export\s+)?class\s+(\w+)", re.M)
GO_FUNC_RE = re.compile(r"^func\s+(?:\([^)]*\)\s*)?(\w+)\s*\(([^)]*)\)", re.M)
RS_FUNC_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+(\w+)\s*\(([^)]*)\)", re.M)
JAVA_METH_RE = re.compile(
    r"^\s*(?:public|protected)\s+(?:static\s+)?[\w<>\[\],\s]+\s+(\w+)\s*\(([^)]*)\)", re.M)
SH_FUNC_RE = re.compile(r"^\s*(?:function\s+)?(\w+)\s*\(\)\s*\{", re.M)

ENVKEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]{2,})\s*=", re.M)

TOKEN_RETENTION_MIN = 0.70  # hacim korunsa bile icerik kelimesi tutma esigi

PROTECTED_KINDS = {"CITATION", "NUMBER", "SYMBOL", "TEST", "CONFIG_KEY", "DEPENDENCY"}
P0_KINDS = {"CITATION", "NUMBER", "SYMBOL", "TEST", "CONFIG_KEY", "DEPENDENCY", "SECTION"}

# Tip -> girdide en az 1 birim bekledigimiz turler.
# Bos cikarsa sonuc INDETERMINATE (= P0), "temiz" DEGIL.
REQUIRED_KINDS = {
    "AKADEMIK": ["SECTION", "CITATION", "NUMBER"],
    "KOD": ["SYMBOL"],
    "VERI": ["NUMBER"],
    "GIRISIM": ["NUMBER"],
    "BELGE": ["SECTION"],
}


# --------------------------------------------------------------------------
# Dosya toplama
# --------------------------------------------------------------------------
def collect(root):
    root = os.path.abspath(root)
    out = {}
    if os.path.isfile(root):
        out[os.path.basename(root)] = _read(root)
        return out
    if not os.path.isdir(root):
        return None
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR]
        for fn in sorted(filenames):
            if fn.startswith("._") or fn == ".DS_Store":
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_EXT:
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) > 8_000_000:
                    continue
            except OSError:
                continue
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            txt = _read(p)
            if txt is not None:
                out[rel] = txt
    return out


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


# --------------------------------------------------------------------------
# Birim cikarma
# --------------------------------------------------------------------------
def split_sections(rel, text):
    """Markdown baslik yoluna gore bolumlere ayir. Baslik yoksa tek bolum."""
    if text is None:
        return []
    heads = list(HEADING_RE.finditer(text))
    if not heads:
        return [(f"{rel}", text)]
    out = []
    pre = text[: heads[0].start()]
    if pre.strip():
        out.append((f"{rel}::<giris>", pre))
    stack = []
    for i, m in enumerate(heads):
        level = len(m.group(1))
        title = normalize(m.group(2)).lower()
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        path = " > ".join(t for _, t in stack)
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[m.end(): end]
        out.append((f"{rel}::{path}", body))
    return out


def extract_citations(text):
    out = set()
    for m in DOI_RE.finditer(text):
        out.add("doi:" + m.group(0).rstrip(".,);:'\"").lower())
    for m in ARXIV_RE.finditer(text):
        out.add("arxiv:" + re.sub(r"\s+", "", m.group(0)).lower())
    for m in URL_RE.finditer(text):
        u = m.group(0).rstrip(".,);:'\"")
        if not DOI_RE.search(u):
            out.add("url:" + u.lower())
    for m in AUTHORYEAR_RE.finditer(text):
        out.add(f"ay:{normalize(m.group(1)).lower()}|{m.group(2)}")
    for m in EMARK_RE.finditer(text):
        out.add("mark:" + m.group(0))
    return out


def extract_symbols(rel, text):
    """Disa acik sembol envanteri: ad + parametre sayisi."""
    ext = os.path.splitext(rel)[1].lower()
    out = set()
    if ext == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return out
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                a = node.args
                n = len(a.posonlyargs) + len(a.args) + len(a.kwonlyargs)
                out.add(f"{node.name}/{n}")
            elif isinstance(node, ast.ClassDef):
                out.add(f"class:{node.name}")
        return out
    pairs = []
    if ext in {".js", ".jsx", ".ts", ".tsx"}:
        pairs = [JS_FUNC_RE, JS_ARROW_RE]
        for m in JS_CLASS_RE.finditer(text):
            out.add(f"class:{m.group(1)}")
    elif ext == ".go":
        pairs = [GO_FUNC_RE]
    elif ext == ".rs":
        pairs = [RS_FUNC_RE]
    elif ext in {".java", ".kt", ".cs"}:
        pairs = [JAVA_METH_RE]
    elif ext == ".sh":
        for m in SH_FUNC_RE.finditer(text):
            out.add(f"{m.group(1)}/0")
        return out
    for rx in pairs:
        for m in rx.finditer(text):
            name = m.group(1)
            params = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
            n = len([p for p in params.split(",") if p.strip()])
            out.add(f"{name}/{n}")
    return out


def extract_tests(rel, text):
    out = set()
    ext = os.path.splitext(rel)[1].lower()
    if ext == ".py":
        for m in PY_TEST_RE.finditer(text):
            out.add(m.group(1))
    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
        for m in JS_TEST_RE.finditer(text):
            out.add(normalize(m.group(1))[:80])
    return out


def extract_config_keys(rel, text):
    out = set()
    base = os.path.basename(rel).lower()
    ext = os.path.splitext(rel)[1].lower()
    if base.startswith(".env") or ext in {".env", ".ini", ".cfg"}:
        for m in ENVKEY_RE.finditer(text):
            out.add(m.group(1))
    elif ext == ".json":
        try:
            obj = json.loads(text)
        except Exception:
            return out
        if isinstance(obj, dict):
            for k in obj:
                out.add(str(k))
    return out


def extract_dependencies(rel, text):
    """{ad: surum} — ad kaybi P0, surum degisimi P1."""
    out = {}
    base = os.path.basename(rel).lower()
    if base == "package.json":
        try:
            obj = json.loads(text)
        except Exception:
            return out
        for sec in ("dependencies", "devDependencies", "peerDependencies"):
            d = obj.get(sec) or {}
            if isinstance(d, dict):
                for k, v in d.items():
                    out[str(k)] = str(v)
    elif base in {"requirements.txt", "requirements-dev.txt"}:
        for line in text.splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith("-"):
                continue
            m = re.match(r"^([A-Za-z0-9._-]+)\s*([<>=!~].*)?$", line)
            if m:
                out[m.group(1).lower()] = (m.group(2) or "").strip()
    elif base == "pyproject.toml":
        for m in re.finditer(r'^\s*"([A-Za-z0-9._-]+)\s*([<>=!~][^"]*)?"\s*,?\s*$',
                             text, re.M):
            out[m.group(1).lower()] = (m.group(2) or "").strip()
    return out


def extract_all(files, scope_numbers=True, variants=False):
    """Tum birimleri cikar. Donen: kind -> {key: locator}

    `variants=True` yalniz KARSILASTIRILAN (sonra) taraf icin kullanilir:
    belirsiz sayi bicimlerinin her iki yorumunu da tasir, boylece salt
    bicim degisimi kayip sayilmaz.
    """
    units = {k: {} for k in
             ("SECTION", "CITATION", "NUMBER", "SYMBOL", "TEST", "CONFIG_KEY")}
    deps = {}
    sections_meta = {}
    for rel, text in sorted(files.items()):
        if text is None:
            continue
        ext = os.path.splitext(rel)[1].lower()
        for key, body in split_sections(rel, text):
            if not normalize(body):
                continue
            units["SECTION"][key] = rel
            sections_meta[key] = {
                "fp": fingerprint(body),
                "chars": count_chars(body),
                "sentences": count_sentences(body),
                "tokens": token_set(body),
                "text": body,
                "file": rel,
            }
        for c in extract_citations(text):
            units["CITATION"].setdefault(c, rel)
        if scope_numbers:
            for n in extract_numbers(text, variants=variants):
                units["NUMBER"].setdefault(n, rel)
        if ext in CODE_EXT:
            for s in extract_symbols(rel, text):
                units["SYMBOL"].setdefault(s, rel)
            for t in extract_tests(rel, text):
                units["TEST"].setdefault(t, rel)
        if ext in DATA_EXT or os.path.basename(rel).startswith(".env"):
            for k in extract_config_keys(rel, text):
                units["CONFIG_KEY"].setdefault(k, rel)
        for k, v in extract_dependencies(rel, text).items():
            deps[k] = v
    return units, deps, sections_meta


# --------------------------------------------------------------------------
# Kayip siniflandirma
# --------------------------------------------------------------------------
def is_template(key):
    tail = key.split("::")[-1].split(" > ")[-1].strip().lower()
    return any(re.match(p, tail) for p in TEMPLATE_PATTERNS)


def _signed_intent_for(key, intent):
    """Bu konumu kapsayan IMZALI bir niyet kaydi var mi? (gerekce, imza) dondur."""
    for rec in intent or []:
        if not isinstance(rec, dict):
            continue
        loc = str(rec.get("konum", ""))
        imza = str(rec.get("imza", "")).strip()
        if loc and imza and rec.get("gerekce") and (loc in key or key in loc):
            return str(rec.get("gerekce")), imza
    return None


def classify_loss(kind, key, before_meta, after_meta, intent, fix_locations):
    """Ilk eslesen kazanir. Donen: (sinif, aciklama)"""
    if kind == "SECTION":
        bm = before_meta.get(key)
        if bm and is_template(key):
            return "SABLON", "otomatik uretilen icerik"
        # BIRLESTIRILDI: kaybolan bolumun icerigi korunan bir bolumun icinde mi?
        # Olcu KAPSAMA'dir (containment), Jaccard degil: kucuk bir bolum buyuk
        # bir bolume tasindiginda Jaccard dusuk cikar ve gercek birlesme kacar.
        # Ayrica cok kisa bolumlerde kapsama tesadufen saglanabilecegi icin
        # asgari icerik kelimesi sarti konur.
        if bm and len(bm["tokens"]) >= 8:
            for ak, am in after_meta.items():
                inter = len(bm["tokens"] & am["tokens"])
                containment = inter / len(bm["tokens"])
                if containment >= 0.90:
                    return "BIRLESTIRILDI", (
                        f"icerigin %{containment*100:.0f}'i '{ak}' icinde bulundu")
    for rec in intent:
        loc = str(rec.get("konum", ""))
        if loc and (loc in key or key in loc):
            # Imza SART: `onay: true` tek basina yetmez, cunku o alani modelin
            # kendisi yazabilir. Beyan edilmis silme bir INSAN kaydidir.
            imza = str(rec.get("imza", "")).strip()
            if rec.get("gerekce") and imza:
                if kind in PROTECTED_KINDS:
                    return "BEYAN_EDILDI_KORUMALI", (
                        f"imzali beyan var ama '{kind}' korumali tur - "
                        f"otomatik kapatilamaz, insan onayi gerekir")
                return "BEYAN_EDILDI", f"{str(rec.get('gerekce'))[:100]} [imza: {imza[:40]}]"
            if rec.get("gerekce") and rec.get("onay") and not imza:
                return "BEYANSIZ", (
                    "UNSIGNED_WAIVER: niyet kaydinda `imza` alani yok; "
                    "`onay: true` tek basina gecerli degildir")
            return "BEYANSIZ", "niyet kaydinda gerekce veya imza eksik"
    for loc in fix_locations:
        if loc and (loc in key or key in loc):
            return "BULGUYA_BAGLI", f"FIX konumu ile ortusuyor: {loc}"
    return "BEYANSIZ", "hicbir mesru kayip sinifina girmiyor"


# --------------------------------------------------------------------------
# Ana
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="ALI KOMUT TOOLKIT v4 - koruma kapisi (veri kaybi olcumu)")
    ap.add_argument("once", help="orijinal girdi (dosya veya klasor)")
    ap.add_argument("sonra", help="uretilen cikti (dosya veya klasor)")
    ap.add_argument("--tip", choices=list(REQUIRED_KINDS), default=None,
                    help="profil; zorunlu birim turlerini belirler")
    ap.add_argument("--niyet", help="beyan edilen silmeler (JSON liste)")
    ap.add_argument("--bulgular", help="bulgu listesi (JSON) - FIX konumlari icin")
    ap.add_argument("--out", help="raporu bu dosyaya da yaz")
    ap.add_argument("--sessiz", action="store_true")
    args = ap.parse_args(argv)

    before = collect(args.once)
    after = collect(args.sonra)
    if before is None:
        fail_closed(f"ONCE yolu okunamadi: {args.once}", args.out)
    if after is None:
        fail_closed(f"SONRA yolu okunamadi: {args.sonra}", args.out)
    if not before:
        fail_closed("ONCE tarafinda okunabilir dosya yok - EMPTY_TARGET", args.out)
    if not after:
        fail_closed("SONRA tarafinda okunabilir dosya yok - EMPTY_TARGET", args.out)

    intent = []
    if args.niyet:
        try:
            with open(args.niyet, encoding="utf-8") as f:
                intent = json.load(f)
            if not isinstance(intent, list):
                raise ValueError("niyet dosyasi liste olmali")
        except Exception as e:
            fail_closed(f"niyet dosyasi okunamadi: {e}", args.out)

    fix_locations = []
    if args.bulgular:
        try:
            with open(args.bulgular, encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("findings", data) if isinstance(data, dict) else data
            for it in items or []:
                if isinstance(it, dict) and it.get("severity") in ("P0", "P1"):
                    fix_locations.append(str(it.get("location", "")))
        except Exception as e:
            fail_closed(f"bulgu dosyasi okunamadi: {e}", args.out)

    bu, bdeps, bmeta = extract_all(before)
    au, adeps, ameta = extract_all(after, variants=True)

    findings = []
    n = [0]

    def add(code, sev, loc, ev, fix):
        n[0] += 1
        findings.append(finding(f"KOR-{n[0]:03d}", code, sev, loc, ev, fix))

    # --- 0. Olculemezlik: zorunlu tur bos mu? -----------------------------
    required = REQUIRED_KINDS.get(args.tip, []) if args.tip else []
    indeterminate = []
    for kind in required:
        if not bu.get(kind):
            indeterminate.append(kind)
            add("SCHEMA_INVALID", "P0", f"olcum:{kind}",
                f"'{args.tip}' profilinde zorunlu olan '{kind}' turunden girdide 0 birim cikti",
                "cikarici bu formati desteklemiyor olabilir; INDETERMINATE = engel, 'temiz' degil")

    # --- 1. Bolum karsilastirmasi ----------------------------------------
    kept = changed = lost = 0
    losses = []
    for key, meta in bmeta.items():
        am = ameta.get(key)
        if am is None:
            # ayni dosya icinde tasinmis/yeniden adlandirilmis olabilir
            best = None
            for ak, cand in ameta.items():
                j = jaccard(meta["tokens"], cand["tokens"])
                if j >= 0.85 and (best is None or j > best[1]):
                    best = (ak, j, cand)
            if best:
                am = best[2]
                if am["fp"] == meta["fp"]:
                    kept += 1
                    continue
        if am is None:
            cls, why = classify_loss("SECTION", key, bmeta, ameta, intent, fix_locations)
            losses.append({"kind": "SECTION", "key": key, "sinif": cls, "aciklama": why})
            if cls in ("BEYANSIZ", "BEYAN_EDILDI_KORUMALI"):
                lost += 1
                add("DATA_LOSS", "P0", key,
                    f"bolum ciktida yok ({meta['chars']} karakter, {meta['sentences']} cumle); sinif={cls}: {why}",
                    "bolumu geri getir veya SILME_NIYETI kaydina gerekce+onay ekle")
            continue
        if am["fp"] == meta["fp"]:
            kept += 1
            continue
        cr = am["chars"] / meta["chars"] if meta["chars"] else 1.0
        sr = am["sentences"] / meta["sentences"] if meta["sentences"] else 1.0
        # Sessiz deger degisimi kaybin ustundedir: bolum yerinde duruyor ama
        # icindeki bir sayi baska bir degere donmusse bu HER ZAMAN P0'dir.
        # (Silmek gorulur; degistirmek gorulmez.)
        bnums = extract_numbers(meta["text"])
        anums = extract_numbers(am["text"], variants=True)
        mutated = sorted(bnums - anums)[:8]
        if mutated:
            imzali = _signed_intent_for(key, intent)
            if imzali:
                # Beyan edilmis degisim P1'e iner ama RAPORDAN SILINMEZ:
                # "sessiz" olmaktan cikar, cunku imza ve gerekce goruntulenir.
                add("STYLE_FAILURE", "P1", key,
                    f"beyan edilmis deger degisimi: {', '.join(mutated)} "
                    f"[gerekce: {imzali[0][:70]} | imza: {imzali[1][:40]}]",
                    "beyan kayitli; degisimin kaynagini final raporda goster")
            else:
                add("FACTUAL_ERROR", "P0", key,
                    f"sessiz deger degisimi: {', '.join(mutated)} bu bolumde artik yok "
                    f"(bolum yerinde duruyor, deger degismis)",
                    "degeri geri getir veya IMZALI niyet kaydiyla beyan et "
                    "(imzasiz beyan gecerli degildir)")
        # HACIM ANLAM DEGILDIR. Bir bolum ayni uzunlukta kalip icerigi
        # dolguyla degistirilebilir; olculmus saldiri: "Sinirliliklar" bolumu
        # ayni hacimde ovgu metniyle degistirildiginde salt oran testi P1 verir.
        # Bu yuzden icerik kelimesi TUTMA orani ayrica olculur.
        inter = len(meta["tokens"] & am["tokens"])
        retention = inter / len(meta["tokens"]) if meta["tokens"] else 1.0
        if retention < TOKEN_RETENTION_MIN and len(meta["tokens"]) >= 8:
            lost += 1
            losses.append({"kind": "SECTION", "key": key, "sinif": "ANLAM_KAYBI",
                           "aciklama": f"icerik kelimesi tutma orani %{retention*100:.0f}"})
            add("DATA_LOSS", "P0", key,
                f"hacim korundu ama ICERIK degisti: anlamli kelimelerin yalniz "
                f"%{retention*100:.0f}'i kaldi (esik %{TOKEN_RETENTION_MIN*100:.0f}); "
                f"karakter %{cr*100:.0f}, cumle %{sr*100:.0f}",
                "silinen icerigi geri getir; dolgu metniyle yer doldurma kayip sayilir")
        elif cr >= 0.95 and sr >= 0.95:
            changed += 1
            add("STYLE_FAILURE", "P1", key,
                f"icerik degisti ama hacim korundu (karakter %{cr*100:.0f}, "
                f"cumle %{sr*100:.0f}, icerik kelimesi %{retention*100:.0f})",
                "degisikligin bir bulguya bagli oldugunu FIX kaydiyla goster")
        else:
            lost += 1
            losses.append({"kind": "SECTION", "key": key, "sinif": "KUCULDU",
                           "aciklama": f"karakter %{cr*100:.0f}, cumle %{sr*100:.0f}"})
            add("DATA_LOSS", "P0", key,
                f"bolum kuculdu: karakter %{cr*100:.0f} (esik %95), cumle %{sr*100:.0f} (esik %95)",
                "silinen kismi geri getir veya gerekce+onay ile beyan et")

    # --- 2. Atom birimler (atif/sayi/sembol/test/config) -------------------
    for kind in ("CITATION", "NUMBER", "SYMBOL", "TEST", "CONFIG_KEY"):
        missing = [k for k in bu[kind] if k not in au[kind]]
        for k in missing:
            cls, why = classify_loss(kind, bu[kind][k], bmeta, ameta, intent, fix_locations)
            losses.append({"kind": kind, "key": k, "sinif": cls, "aciklama": why})
            if cls in ("BEYANSIZ", "BEYAN_EDILDI_KORUMALI"):
                sev = "P0" if kind in P0_KINDS else "P1"
                add("DATA_LOSS", sev, f"{kind}:{bu[kind][k]}",
                    f"'{k}' girdide vardi, ciktida yok; sinif={cls}: {why}",
                    f"{kind} birimini geri getir veya gerekce+onay ile beyan et")

    # --- 3. Bagimlilik: ad kaybi P0, surum degisimi P1 --------------------
    for name, ver in bdeps.items():
        if name not in adeps:
            add("DATA_LOSS", "P0", f"DEPENDENCY:{name}",
                f"bagimlilik '{name}' ({ver}) kaldirilmis",
                "bagimliligi geri getir veya kaldirma gerekcesini yaz")
        elif adeps[name] != ver:
            add("STYLE_FAILURE", "P1", f"DEPENDENCY:{name}",
                f"surum degisti: {ver} -> {adeps[name]}",
                "surum degisiminin gerekcesini ve test kanitini yaz")

    # --- 4. Kaynaksiz ekleme (anti-halusinasyon) --------------------------
    new_cit = [k for k in au["CITATION"] if k not in bu["CITATION"]]
    for k in new_cit[:20]:
        add("CLAIM_UNSUPPORTED", "P1", f"CITATION:{au['CITATION'][k]}",
            f"ciktida girdide olmayan yeni atif: {k}",
            "KAYNAKSIZ_EKLEME - kaynagini goster veya atfi kaldir")

    # --- 5. Karar ---------------------------------------------------------
    p0, p1, p2 = recount(findings)
    verdict = verdict_from(p0, p1)
    total_sections = len(bmeta)
    report = {
        "arac": "ALI_KOMUT_TOOLKIT_v4",
        "kapi": "KORUMA",
        "once": os.path.abspath(args.once),
        "sonra": os.path.abspath(args.sonra),
        "tip": args.tip,
        "verdict": "ENGEL_VAR" if indeterminate else verdict,
        "indeterminate": indeterminate,
        "keep": {
            "toplam": total_sections,
            "korundu": kept,
            "degisti": changed,
            "kayip": lost,
            "kapsama": f"{kept + changed}/{total_sections}" if total_sections else "0/0",
        },
        "birimler": {k: {"once": len(bu[k]), "sonra": len(au[k])} for k in bu},
        "bagimlilik": {"once": len(bdeps), "sonra": len(adeps)},
        "kayiplar": losses[:200],
        "counts": {"P0": p0, "P1": p1, "P2": p2},
        "findings": findings,
    }
    emit(report, args.out, args.sessiz)
    return EXIT_BLOCK if (p0 > 0 or indeterminate) else EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # fail-closed: traceback degil, gecerli rapor
        fail_closed(f"beklenmeyen hata: {type(exc).__name__}: {exc}")
        sys.exit(EXIT_USAGE)
