#!/usr/bin/env python3
"""ALI KOMUT TOOLKIT v4 — ARSIV / HIJYEN / SIR KAPISI

    python3 v4_verify.py <klasor|arsiv.zip> [--manifest SHA256SUMS.txt]
                         [--kanit-dizin RAPORLAR] [--muafiyet muafiyet.json]
                         [--fikstur fikstur.json] [--out rapor.json] [--sessiz]

TEK YETKILI TAM TARAMA (paket): `cd KOMUT_TOOLKIT_v4 && python3
ARACLAR/betikler/v4_verify.py . --kanit-dizin ARACLAR/KANIT` — kendi
`ARACLAR/FIKSTUR.json`'unu otomatik uygular (raporda `fikstur_otomatik`).
Depo geneli sir taramasi ise `KOD_SABLONLAR/scripts/secret_scan.py --tum`.
Bagimlilik/onbellek dizinlerinin (`.venv`, `node_modules`, ...) ICINE
girilmez; dizin tek bir P1 hijyen notu olarak gorunur.

Kapatilan somut delikler (hepsi gercek kod uzerinde olculdu):
  D1  Bos klasore dogrultuldugunda olumlu karar veriyordu (files=0, PASS).
      -> EMPTY_TARGET = P0.
  D2  Sir taramasi dosya+desen basina ILK eslesmede duruyordu; 1. satirda yer
      tutucu, 500. satirda gercek anahtar olan dosyada gercek anahtar hic
      gorulmuyordu.  -> Tum eslesmeler taranir.
  D3  "Yer tutucu ipucu" listesi eslesmeyi otomatik P2'ye indiriyordu; `xxx`,
      `test-`, `...` iceren GERCEK formatli OpenAI/AWS/uretim-parolasi
      anahtarlari nota dusuyor ve kapi olumlu karar veriyordu.
      -> Ipucu artik yalniz NOT dusurur; indirgeme IMZALI MUAFIYET ister.
  D4  Arsiv acmak bir guven siniri olarak ele alinmiyordu.
      -> Yol gecisi, sembolik link, sikistirma orani, __MACOSX/._* kontrolu.
  D5  Kanit loglari hijyen kuralina takiliyordu (kanit uretme zorunlulugu ile
      celisiyordu). -> --kanit-dizin hijyenden muaf, sir taramasindan DEGIL.

Cikis: 0 = engel yok, 1 = engel var, 2 = kullanim hatasi.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v4_common import (  # noqa: E402
    EXIT_BLOCK, EXIT_OK, EXIT_USAGE, emit, fail_closed, finding, recount,
    sha256_file, verdict_from,
)

HERE = os.path.dirname(os.path.abspath(__file__))
PAKET_KOKU = os.path.abspath(os.path.join(HERE, "..", ".."))
KENDI_FIKSTUR = os.path.abspath(os.path.join(HERE, "..", "FIKSTUR.json"))
# Depo kopyasinda ikinci birinci-taraf manifest vardir (secret_scan ile ayni).
# Yalniz KOK tam olarak depo koku ise uygulanir; hedefin getirdigi manifest asla.
REPO_KOKU = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REPO_FIKSTUR = os.path.join(REPO_KOKU, "tools", "secret_fixtures.json")

HYGIENE_PATTERNS = [
    (r"(^|/)(node_modules|\.next|__pycache__|\.pytest_cache|\.mypy_cache|\.venv|venv|\.tox)(/|$)",
     "bagimlilik/onbellek klasoru"),
    (r"(^|/)(__MACOSX)(/|$)", "macOS arsiv artigi"),
    (r"(^|/)\._[^/]+$", "macOS AppleDouble ikizi"),
    (r"(^|/)\.DS_Store$", "macOS klasor meta dosyasi"),
    (r"\.(pyc|pyo|class|so|o|obj)$", "derleme ciktisi"),
    (r"(^|/)\.env$", "GERCEK .env dosyasi"),
    (r"(^|/)\.env\.(local|development|production|test|staging|prod|dev)[^/]*$",
     "GERCEK .env varyanti"),
]

SECRET_PATTERNS = [
    (r"sk-(?:ant-)?[A-Za-z0-9_-]{20,}", "OpenAI/Anthropic bicimli anahtar"),
    (r"AKIA[0-9A-Z]{16}", "AWS erisim anahtari"),
    (r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}", "GitHub jetonu"),
    (r"github_pat_[A-Za-z0-9_]{22,}", "GitHub ince jeton"),
    (r"AIza[0-9A-Za-z_-]{35}", "Google API anahtari"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "Slack jetonu"),
    (r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----", "ozel anahtar"),
    (r"(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@/]+:[^\s:@/]+@",
     "kimlik bilgili baglanti dizesi"),
    (r"(?i)\b(?:api[_-]?key|secret|token|passwd|password)\b\s*[:=]\s*[\"']?([A-Za-z0-9+/_@.\\-]{16,})",
     "anahtar/parola atamasi"),
]

# Bu ipuclari SADECE not dusurur. Otomatik indirgeme YAPMAZ.
PLACEHOLDER_HINTS = [
    "example", "changeme", "placeholder", "dummy", "fake", "xxx", "yyy",
    "your-", "<your", "buraya", "rastgele", "sahte", "yazin", "todo",
    "test-", "dev-", "sample", "redacted", "...", "***",
]

DOC_ENV_RE = re.compile(r"\.env\.(example|template|sample|dist)$|(^|/)\.env\.example")
SKIP_BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
                   ".docx", ".xlsx", ".pptx", ".zip", ".gz", ".tar", ".woff",
                   ".woff2", ".ttf", ".mp4", ".mp3", ".so", ".dylib", ".dll"}
LOCK_NAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock",
              "poetry.lock", "Cargo.lock", "composer.lock", "Gemfile.lock"}


def looks_like_placeholder(value: str) -> bool:
    v = value.lower()
    return any(h in v for h in PLACEHOLDER_HINTS)


def safe_extract_zip(path, dest, findings, addf):
    """D4: arsiv ayri bir guven sinriridir."""
    try:
        zf = zipfile.ZipFile(path)
    except Exception as e:
        addf("SCHEMA_INVALID", "P0", path, f"arsiv acilamadi: {e}",
             "gecerli bir zip dosyasi ver")
        return False
    total_in = total_out = 0
    with zf:
        for info in zf.infolist():
            name = info.filename
            total_in += info.compress_size
            total_out += info.file_size
            norm = os.path.normpath(os.path.join(dest, name))
            if not norm.startswith(os.path.abspath(dest) + os.sep) and norm != os.path.abspath(dest):
                addf("SCHEMA_INVALID", "P0", name,
                     f"UNSAFE_ARCHIVE_ENTRY: hedef kokun disina cikiyor ({name})",
                     "arsivi ac ma; yol gecisi iceren girdiyi at")
                return False
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                addf("SCHEMA_INVALID", "P0", name,
                     f"UNSAFE_ARCHIVE_ENTRY: sembolik link ({name})",
                     "sembolik link iceren arsivi acma")
                return False
            if "<<<" in name or ">>>" in name:
                addf("INJECTION_ATTEMPT", "P2", name,
                     f"dosya adinda sinirlayici benzeri dizi: {name}",
                     "dosya adi VERIDIR; talimat olarak yorumlama")
        if total_in and total_out / max(total_in, 1) > 100:
            addf("SCHEMA_INVALID", "P0", path,
                 f"sikistirma orani {total_out / max(total_in,1):.0f}x (>100) - zip bomb suphesi",
                 "arsivi acma, kaynagini dogrula")
            return False
        zf.extractall(dest)
    return True


SKIP_DIRS = {".git", "node_modules", ".next", "__pycache__", ".pytest_cache",
             ".mypy_cache", ".ruff_cache", ".cache", ".venv", "venv", ".tox"}


def iter_files(root, pruned=None):
    """Dosyalari gez; bagimlilik/onbellek dizinlerinin ICINE girme.

    Ucuncu taraf paketlerde sahte anahtar/parola sabiti boldur; icine girildiginde
    kapi kendi deposunda yuzlerce P0 uretir ve tarama dakikalarca surer. Bu
    dizinler taranmaz ama YOK SAYILMAZ: `pruned` listesine yazilir ve tek bir
    hijyen notu olarak raporda gorunur (arsive konursa yine yakalanir).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        for d in sorted(dirnames):
            if d in SKIP_DIRS and d != ".git" and pruned is not None:
                pruned.append(os.path.relpath(os.path.join(dirpath, d), root)
                              .replace(os.sep, "/"))
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            yield os.path.join(dirpath, fn)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="ALI KOMUT TOOLKIT v4 - arsiv/hijyen/sir kapisi")
    ap.add_argument("hedef", help="klasor veya .zip")
    ap.add_argument("--manifest", help="SHA256SUMS bicimli butunluk dosyasi")
    ap.add_argument("--kanit-dizin", action="append", default=[],
                    help="hijyenden muaf kanit/rapor dizini (birden fazla verilebilir)")
    ap.add_argument("--muafiyet", help="imzali muafiyet kayitlari (JSON liste)")
    ap.add_argument("--fikstur",
                    help="satir SHA-256'li fikstur manifesti (JSON); verilmezse "
                         "arac KENDI ARACLAR/FIKSTUR.json'unu yalniz kendi "
                         "paketini tararken uygular; hedefin manifesti okunmaz")
    ap.add_argument("--out")
    ap.add_argument("--sessiz", action="store_true")
    args = ap.parse_args(argv)

    findings, n = [], [0]

    def addf(code, sev, loc, ev, fix):
        n[0] += 1
        findings.append(finding(f"ARS-{n[0]:03d}", code, sev, loc, ev, fix))

    waivers = []
    if args.muafiyet:
        try:
            with open(args.muafiyet, encoding="utf-8") as f:
                waivers = json.load(f)
            if not isinstance(waivers, list):
                raise ValueError("muafiyet dosyasi liste olmali")
        except Exception as e:
            fail_closed(f"muafiyet dosyasi okunamadi: {e}", args.out)
    signed = set()

    def is_signed(loc, rel):
        """Muafiyet konumu tam satir (`dosya:12`) veya dosya yolu olabilir.
        Desen eslesmesi KABUL EDILMEZ — yalniz acik kimlik/yol."""
        return loc in signed or rel in signed

    for w in waivers:
        if isinstance(w, dict) and w.get("imza") and w.get("gerekce") and w.get("konum"):
            signed.add(str(w["konum"]))
        elif isinstance(w, dict):
            addf("SCHEMA_INVALID", "P0", str(w.get("konum", "?")),
                 "UNSIGNED_WAIVER: muafiyet kaydinda imza veya gerekce yok",
                 "muafiyet insan imzasi ister; imza+gerekce+konum zorunlu")

    # Fikstur muafiyeti DESEN/DOSYA degil, TAM (dosya, satir SHA-256) ciftidir.
    # KAYNAK HER ZAMAN ARACIN KENDI PAKETIDIR: hedef agacta bulunan bir manifest
    # asla okunmaz; boylece hedef depo kendini muaf tutamaz (SP-13). `--fikstur`
    # acikca verilirse o kullanilir. Verilmezse arac kendi ARACLAR/FIKSTUR.json'
    # unu YALNIZ kendi paketini (ya da onu iceren bir ust dizini) tararken
    # uygular: `v4_verify.py .` tek basina da kendi test fiksturlerini susturur,
    # depo kokunde ise deponun kendi `tools/secret_fixtures.json`'u (secret_scan
    # ile ayni kayitlar) devreye girer; yabanci hedefte kayit yollari tutmadigi
    # icin hicbir sey susturulmaz.
    def _fikstur_oku(yol):
        try:
            with open(yol, encoding="utf-8") as f:
                fd = json.load(f)
        except Exception as e:
            fail_closed(f"fikstur manifesti okunamadi: {e}", args.out)
        if not isinstance(fd, dict) or not isinstance(fd.get("fiksturler"), list):
            fail_closed("fikstur manifesti semasi gecersiz: {\"fiksturler\": []} bekleniyor",
                        args.out)
        kayitlar = []
        for k in fd["fiksturler"]:
            if not isinstance(k, dict):
                fail_closed("fikstur kaydi nesne degil", args.out)
            rel = str(k.get("dosya", "")).replace("\\", "/")
            h = str(k.get("satir_sha256", ""))
            if (not rel or rel.startswith("/") or ".." in rel.split("/") or
                    not re.fullmatch(r"[0-9a-f]{64}", h) or
                    not str(k.get("gerekce", "")).strip() or
                    not str(k.get("kanit", "")).strip()):
                fail_closed(f"fikstur kaydi gecersiz: {rel!r}", args.out)
            kayitlar.append((rel, h))
        return kayitlar

    hedef_kok = os.path.abspath(args.hedef)
    fikstur_kaynagi = None
    fikstur_otomatik = False
    kayitlar = []
    if args.fikstur:
        fikstur_kaynagi = os.path.abspath(args.fikstur)
        kayitlar = _fikstur_oku(fikstur_kaynagi)
    elif os.path.isdir(hedef_kok):
        if hedef_kok == PAKET_KOKU and os.path.isfile(KENDI_FIKSTUR):
            fikstur_kaynagi = KENDI_FIKSTUR
        elif hedef_kok == REPO_KOKU and os.path.isfile(REPO_FIKSTUR):
            fikstur_kaynagi = REPO_FIKSTUR
        if fikstur_kaynagi:
            fikstur_otomatik = True
            kayitlar = _fikstur_oku(fikstur_kaynagi)
    # Paket manifesti PAKET-GORELI yollar tasir; hedef paketin ust dizini ise
    # onek eklenir. Depo manifesti ise zaten depo-goreli yazilmistir.
    onek = ""
    if (fikstur_otomatik and fikstur_kaynagi == KENDI_FIKSTUR
            and hedef_kok != PAKET_KOKU):
        onek = os.path.relpath(PAKET_KOKU, hedef_kok).replace(os.sep, "/")
    fixtures = set()
    for rel, h in kayitlar:
        goreli = (rel if not onek else
                  os.path.normpath(os.path.join(onek, rel)).replace(os.sep, "/"))
        if (goreli, h) in fixtures:
            fail_closed(f"yinelenen fikstur kaydi: {goreli}", args.out)
        fixtures.add((goreli, h))

    tmp = None
    root = os.path.abspath(args.hedef)
    if os.path.isfile(root) and root.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp(prefix="v4verify_")
        if not safe_extract_zip(root, tmp, findings, addf):
            p0, p1, p2 = recount(findings)
            emit({"arac": "ALI_KOMUT_TOOLKIT_v4", "kapi": "ARSIV",
                  "hedef": root, "verdict": "ENGEL_VAR",
                  "counts": {"P0": p0, "P1": p1, "P2": p2},
                  "findings": findings}, args.out, args.sessiz)
            return EXIT_BLOCK
        root = tmp
    elif not os.path.isdir(root):
        fail_closed(f"hedef klasor/arsiv yok: {root}", args.out)

    pruned = []
    files = [p for p in iter_files(root, pruned) if os.path.isfile(p)]

    # D1: bos hedef olumlu karar veremez
    if not files:
        addf("SCHEMA_INVALID", "P0", root,
             "EMPTY_TARGET: denetlenecek dosya bulunamadi (0 dosya)",
             "dogru yolu ver; bos hedef 'temiz' degildir")

    evidence_dirs = [d.strip("/") for d in (args.kanit_dizin or [])]

    def in_evidence(rel):
        return any(rel == d or rel.startswith(d + "/") for d in evidence_dirs)

    total_bytes = 0
    hygiene = []
    for p in files:
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        try:
            total_bytes += os.path.getsize(p)
        except OSError:
            pass
        if in_evidence(rel):
            continue  # D5: kanit dizini hijyenden muaf
        for pat, why in HYGIENE_PATTERNS:
            if re.search(pat, rel):
                hygiene.append((rel, why))
                break
    # Bagimlilik dizinleri icerigiyle taranmadi; kendisi tek P1 notu olarak kalir.
    for rel in pruned:
        hygiene.append((rel + "/", "bagimlilik/onbellek klasoru (taranmadi)"))
    for rel, why in hygiene[:40]:
        sev = "P0" if ".env" in rel.split("/")[-1] and "example" not in rel else "P1"
        addf("STYLE_FAILURE" if sev == "P1" else "DATA_LOSS", sev, rel,
             f"hijyen ihlali: {why}", "bu dosyayi paketten cikar")

    # --- sir taramasi: TUM eslesmeler, otomatik indirgeme YOK -------------
    real_secrets, noted = [], []
    for p in files:
        rel = os.path.relpath(p, root).replace(os.sep, "/")
        base = os.path.basename(rel)
        if os.path.splitext(rel)[1].lower() in SKIP_BINARY_EXT or base in LOCK_NAMES:
            continue
        try:
            if os.path.getsize(p) > 4_000_000:
                continue
            with open(p, encoding="utf-8", errors="ignore") as f:
                txt = f.read()
        except OSError:
            continue
        is_doc_env = bool(DOC_ENV_RE.search(rel))
        satirlar = txt.splitlines()
        for pat, why in SECRET_PATTERNS:
            for m in re.finditer(pat, txt):  # D2: ilk eslesmede DURMA
                snippet = m.group(0)[:48]
                line = txt[: m.start()].count("\n") + 1
                loc = f"{rel}:{line}"
                _h = (hashlib.sha256(satirlar[line - 1].encode("utf-8")).hexdigest()
                      if 0 < line <= len(satirlar) else "")
                if (rel, _h) in fixtures:
                    noted.append({"konum": loc, "tur": why,
                                  "not": "fikstur satir SHA-256"})
                    continue
                hint = looks_like_placeholder(m.group(0))
                if is_signed(loc, rel):
                    noted.append({"konum": loc, "tur": why, "not": "imzali muafiyet"})
                    continue
                if is_doc_env:
                    # dokumantasyon dosyasi: P2 baslar ama gorunur kalir
                    noted.append({"konum": loc, "tur": why,
                                  "not": "dokumantasyon .env ornegi"})
                    addf("STYLE_FAILURE", "P2", loc,
                         f"{why} (ornek dosya): {snippet}",
                         "dokumantasyon; yine de gercek deger olmadigini dogrula")
                    continue
                # D3: ipucu varsa bile OTOMATIK indirgeme YOK
                note = " [OLASI_YER_TUTUCU]" if hint else ""
                real_secrets.append({"konum": loc, "tur": why, "ipucu": hint})
                addf("DATA_LOSS", "P0", loc,
                     f"{why}: {snippet}{note}",
                     "anahtari kaldir; yer tutucu ise imzali muafiyet kaydi ekle "
                     "(otomatik indirgeme yasak)")

    # --- manifest ---------------------------------------------------------
    manifest_report = None
    if args.manifest:
        mp = os.path.abspath(args.manifest)
        if not os.path.isfile(mp):
            addf("SCHEMA_INVALID", "P0", mp, "manifest dosyasi bulunamadi",
                 "dogru manifest yolunu ver")
        else:
            expected = {}
            with open(mp, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and re.fullmatch(r"[0-9a-f]{64}", parts[0]):
                        expected[parts[1].lstrip("*./")] = parts[0]
            ok = miss = bad = 0
            miss_list, bad_list = [], []
            for rel, want in expected.items():
                fp = os.path.join(root, rel)
                if not os.path.isfile(fp):
                    miss += 1
                    miss_list.append(rel)
                    continue
                if sha256_file(fp) == want:
                    ok += 1
                else:
                    bad += 1
                    bad_list.append(rel)
            manifest_report = {"toplam": len(expected), "eslesen": ok,
                               "eksik": miss, "bozuk": bad}
            if not expected:
                addf("SCHEMA_INVALID", "P0", mp,
                     "manifest bos veya bicimi taninmadi",
                     "sha256sum bicimi bekleniyor")
            if miss:
                addf("DATA_LOSS", "P0", "manifest",
                     f"{miss} dosya eksik: {miss_list[:5]}", "eksik dosyalari geri getir")
            if bad:
                addf("DATA_LOSS", "P0", "manifest",
                     f"{bad} dosya ozeti tutmadi: {bad_list[:5]}",
                     "degisen dosyalari incele veya manifesti yeniden uret")

    p0, p1, p2 = recount(findings)
    report = {
        "arac": "ALI_KOMUT_TOOLKIT_v4",
        "kapi": "ARSIV",
        "hedef": os.path.abspath(args.hedef),
        "verdict": verdict_from(p0, p1),
        "dosya_sayisi": len(files),
        "toplam_bayt": total_bytes,
        "hijyen_ihlali": len(hygiene),
        "sir_bulgusu": len(real_secrets),
        "fikstur_muafiyeti": sum(1 for n in noted
                                if n.get("not") == "fikstur satir SHA-256"),
        "fikstur_manifesti": fikstur_kaynagi,
        "fikstur_otomatik": fikstur_otomatik,
        "taranmayan_dizin": pruned,
        "sir_notu": noted[:20],
        "manifest": manifest_report,
        "counts": {"P0": p0, "P1": p1, "P2": p2},
        "findings": findings,
    }
    emit(report, args.out, args.sessiz)
    if tmp:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    return EXIT_BLOCK if p0 else EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        fail_closed(f"beklenmeyen hata: {type(exc).__name__}: {exc}")
        sys.exit(EXIT_USAGE)
