#!/usr/bin/env python3
"""ALI KOMUT TOOLKIT v4 — PAKET ICI TUTARLILIK KAPISI

    python3 v4_consistency.py <paket_koku> [--out rapor.json] [--sessiz]

Neden var: `000_ONCE_BUNU_YAPISTIR.md` tek basina calisabilmek zorunda oldugu
icin cekirdek dosyalarla kacinilmaz olarak ortusur. Elle tutulan iki kopya
KAYAR. Kayma teorik degil, olculmus bir hatadir: bir onceki nesilde ayni bulgu
nesnesi bir dosyada `priority`, digerinde `severity` diye yazilmisti ve
birlestirici yalniz `priority` okudugu icin `severity` etiketli bir P0 bulgusu
SIFIR sayiliyordu — fail-closed kapi sessizce fail-open oluyordu.

Bu betik o kaymayi mekanik olarak yakalar.

Cikis: 0 = tutarli, 1 = celiski var, 2 = kullanim hatasi.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v4_common import (  # noqa: E402
    CHECK_STATUSES, CODES, EXIT_BLOCK, EXIT_OK, EXIT_USAGE, SEVERITIES,
    TERMINAL_STATES, TYPES, emit, fail_closed, finding, recount, verdict_from,
)

ANA = "000_ONCE_BUNU_YAPISTIR.md"
CEKIRDEK = "ARACLAR/cekirdek"
SOZLESME_DOSYASI = "ARACLAR/cekirdek/C1_SOZLESME.md"
ORNEK_RAPOR = "ARACLAR/ORNEKLER/ORNEK_RAPOR.md"

ARASTIRMA_DOSYALARI = {"ALLAHAŞKI.md"}
ARASTIRMA_DIZINLERI = {
    "yahudikaynaklar", "moschiach", "sebatay", "sebatay-sevi-kaynaklari",
}

# Iki dosyada birden yazilmasi yasak olan sayilar: tek yerde tanimli olmali,
# ama pratikte ANA dosya tek basina calismak zorunda oldugu icin tekrar eder.
# Bu yuzden kural: tekrar edebilir, AMA AYNI olmak zorunda.
ILK_EKRAN_SATIR = 32
ILK_EKRAN_KARAKTER = 1800

PINNED = {
    "durus_butcesi": (r"en fazla[^.\n]{0,24}3[^.\n]{0,24}soru", 2),
    "ilk_ekran_satir": (r"[≤<]=?\s*32\s*satır", 2),
    "ilk_ekran_karakter": (r"[≤<]=?\s*1800\s*karakter", 2),
    "koruma_esigi": (r"%95", 2),
    "faz_sayisi": (r"F0\b[\s\S]{0,400}?F6\b|[Yy]edi faz|YEDİ FAZ", 2),
}

# Kosu sirasinda URETILEN dosyalar: pakette bulunmalari BEKLENMEZ.
RUNTIME_GENERATED = {"SONRAKI_SEFER.md", "niyet.json", "muafiyet.json",
                     "bulgular.json", "rapor.json", "answers.json"}

BANNED_TOKENS = [
    (r"\bpriority\b", "bulgu nesnesinde `priority` degil `severity` kullanilir"),
    (r"KEEP'l", "Ingilizce simgeye Turkce cekim eki yasak (sozluk kurali 2)"),
    (r"PASS'l", "Ingilizce simgeye Turkce cekim eki yasak (sozluk kurali 2)"),
    (r"gate'[a-zçğıöşü]", "Ingilizce simgeye Turkce cekim eki yasak; 'kapi' kullan"),
    (r"\bDEPRECATED\b", "kullanilmayacak dosya silinir, pakette birakilmaz"),
    (r"disable:\s*true", "devre disi sarmalayici dosya pakette bulunmaz"),
]

# Makine anahtarlarinda Turkce karakter yasak (I/i buyuk-kucuk tuzagi).
KEYLIKE_RE = re.compile(r'"([^"]{1,40})"\s*:')
# DIKKAT: ASCII 'I' (U+0049) buraya GIRMEZ. Yalniz Turkceye ozgu kod
# noktalari: 'İ' (U+0130) ve 'ı' (U+0131) ile s/g/u/o/c cedilla-breve cifti.
TURKISH = set("İıŞşĞğÜüÖöÇç")


def _is_quoted_example(text, pos):
    """Yasak simge, kuralin KENDISINDE veya bir kanit alintisinda geciyorsa
    bu bir kullanim degil, bir ornektir.

    Iki kosul BIRLIKTE saglanmali (tek kosul kandirilabilir olurdu):
      1) simge ters tirnak icinde (`...`) — yani kod/ornek olarak isaretli,
      2) satir ya bir alinti blogu (`>`) ya da 'yasak' kelimesini iceriyor.
    """
    ls = text.rfind("\n", 0, pos) + 1
    le = text.find("\n", pos)
    if le == -1:
        le = len(text)
    line = text[ls:le]
    col = pos - ls
    if line[:col].count("`") % 2 == 0:
        return False  # ters tirnak icinde degil
    return line.lstrip().startswith(">") or "yasak" in line.lower()


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def kapsam_turu(rel, dizin=False):
    """Birinci seviye paket yolunu normatif, arastirma veya tanimsiz ayir."""
    rel = unicodedata.normalize("NFC", rel.replace(os.sep, "/").strip("/"))
    top = rel.split("/", 1)[0]
    if top == "ARACLAR" and (dizin or "/" in rel):
        return "normatif"
    if top in ARASTIRMA_DIZINLERI and (dizin or "/" in rel):
        return "arastirma"
    if not dizin and "/" not in rel:
        if rel in ARASTIRMA_DOSYALARI:
            return "arastirma"
        if fnmatch.fnmatchcase(rel, "000_*.md") or fnmatch.fnmatchcase(rel, "001_*.md"):
            return "normatif"
    return "tanimlanmamis"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="ALI KOMUT TOOLKIT v4 - paket ici tutarlilik kapisi")
    ap.add_argument("kok", nargs="?", default=".")
    ap.add_argument("--out")
    ap.add_argument("--sessiz", action="store_true")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.kok)
    if not os.path.isdir(root):
        fail_closed(f"paket koku yok: {root}", args.out)

    findings, n = [], [0]

    def add(code, sev, loc, ev, fix):
        n[0] += 1
        findings.append(finding(f"TUT-{n[0]:03d}", code, sev, loc, ev, fix))

    md_files, all_paths = {}, set()
    kapsam = {"normatif": [], "arastirma": [], "tanimlanmamis": []}
    for dp, dn, fns in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in {".git", "__pycache__"})
        rel_dp = os.path.relpath(dp, root).replace(os.sep, "/")
        if rel_dp == ".":
            for dirname in list(dn):
                tur = kapsam_turu(dirname, dizin=True)
                if tur == "tanimlanmamis":
                    kapsam[tur].append(dirname + "/")
                    add("SCOPE_VIOLATION", "P0", dirname + "/",
                        "paket kokunde tanimlanmamis dizin",
                        "yolu normatif/arastirma politikasinda siniflandir")
                    dn.remove(dirname)
        for fn in sorted(fns):
            rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/")
            tur = kapsam_turu(rel)
            kapsam[tur].append(rel)
            if tur == "tanimlanmamis":
                add("SCOPE_VIOLATION", "P0", rel,
                    "paket kokunde tanimlanmamis dosya",
                    "yolu normatif/arastirma politikasinda siniflandir")
                continue
            if tur == "arastirma":
                continue
            all_paths.add(rel)
            all_paths.add(os.path.basename(rel))
            if fn.endswith((".md", ".py")):
                txt = read(os.path.join(dp, fn))
                if txt is not None:
                    md_files[rel] = txt

    if ANA not in md_files:
        add("SCHEMA_INVALID", "P0", ANA, "ana komut dosyasi bulunamadi",
            f"{ANA} paket kokunde olmali")
        p0, p1, p2 = recount(findings)
        emit({"arac": "ALI_KOMUT_TOOLKIT_v4", "kapi": "TUTARLILIK",
              "verdict": "ENGEL_VAR", "counts": {"P0": p0, "P1": p1, "P2": p2},
              "kapsam": kapsam, "findings": findings}, args.out, args.sessiz)
        return EXIT_BLOCK

    ana = md_files[ANA]
    cekirdek_txt = "\n".join(v for k, v in md_files.items() if k.startswith(CEKIRDEK))
    # NORMATIF KAYNAK: kapali listeler C1'in KENDISINDE aranir.
    # Birlestirilmis cekirdek metnine bakmak fail-open uretir: bir deger C1'den
    # tamamen silinse bile baska bir cekirdek dosyasinda gectigi icin kapi
    # sessizce geciyordu (olculmus kusur, bu satir onun duzeltmesidir).
    c1 = md_files.get(SOZLESME_DOSYASI)
    if c1 is None:
        add("SCHEMA_INVALID", "P0", SOZLESME_DOSYASI,
            "normatif sozlesme dosyasi bulunamadi",
            f"{SOZLESME_DOSYASI} pakette olmali")
        c1 = ""

    # --- 1. Kapali listeler her iki tarafta da tam gecmeli ---------------
    for label, values in (("siddet", SEVERITIES), ("tur kodu", CODES),
                          ("kontrol durumu", CHECK_STATUSES),
                          ("terminal durum", TERMINAL_STATES), ("tip", TYPES)):
        for v in values:
            if v not in ana:
                add("SCHEMA_INVALID", "P0", ANA,
                    f"{label} degeri '{v}' ana komutta gecmiyor",
                    "ana komut tek basina calismak zorunda; kapali listeyi tam yaz")
            if v not in c1:
                add("SCHEMA_INVALID", "P0", SOZLESME_DOSYASI,
                    f"{label} degeri '{v}' NORMATIF KAYNAKTA gecmiyor",
                    "C1 tek dogruluk kaynagidir; degeri ekle veya betikteki "
                    "kapali listeden cikar")

    # --- 2. Cekirdekte olup ana komutta olmayan kapali liste degeri -------
    extra = re.findall(r"\b[A-Z][A-Z0-9_]{4,}\b", cekirdek_txt)
    known = set(SEVERITIES) | set(CODES) | set(CHECK_STATUSES) | set(TERMINAL_STATES) | set(TYPES)
    for tok in set(extra):
        if tok in known:
            continue
        # Kod gibi gorunen ama listede olmayan token cekirdekte tanimliysa
        # ve ana komutta hic gecmiyorsa, bu bir kayma adayidir.
        if tok.endswith("_ERROR") or tok.endswith("_INVALID") or tok.endswith("_MISSING"):
            if tok not in ana:
                add("SCHEMA_INVALID", "P1", CEKIRDEK,
                    f"kod benzeri '{tok}' cekirdekte var, ana komutta yok",
                    "ya kapali listeye ekle ya cekirdekten cikar")

    # --- 3. Yasak simgeler ------------------------------------------------
    for rel, txt in md_files.items():
        if rel.startswith("ARACLAR/betikler/") and rel.endswith(".py"):
            continue  # betiklerde ingilizce degisken adi normaldir
        for pat, why in BANNED_TOKENS:
            for m in re.finditer(pat, txt):
                lineno = txt[: m.start()].count("\n") + 1
                if _is_quoted_example(txt, m.start()):
                    continue  # kuralin kendisi / kanit alintisi, kullanim degil
                add("STYLE_FAILURE", "P1", f"{rel}:{lineno}",
                    f"yasak simge {m.group(0)!r}: {why}", "sozluk kuralina uy")

    # --- 4. Makine anahtarlarinda Turkce karakter -------------------------
    for rel, txt in md_files.items():
        for m in KEYLIKE_RE.finditer(txt):
            key = m.group(1)
            if any(ch in TURKISH for ch in key):
                line = txt[: m.start()].count("\n") + 1
                add("SCHEMA_INVALID", "P0", f"{rel}:{line}",
                    f"makine anahtarinda Turkce karakter: {key!r}",
                    "anahtarlar ASCII olmali (Turkce yerelde 'I'.lower()=='i' degil)")

    # --- 5. Sabitlenmis sayilar (tekrar edebilir ama AYNI olmali) --------
    for name, (pat, min_hits) in PINNED.items():
        hits = sum(1 for t in (ana, cekirdek_txt) if re.search(pat, t, re.I | re.S))
        if hits < min_hits:
            add("SCHEMA_INVALID", "P1", "paket",
                f"sabit '{name}' ana komut ve cekirdekte ayni bicimde gecmiyor "
                f"({hits}/{min_hits})",
                "iki tarafta da ayni degeri yaz; kayma fail-open uretir")

    # --- 6. Kirik dosya referansi ----------------------------------------
    ref_re = re.compile(r"`([A-Za-z0-9_./-]+\.(?:md|py|json|txt))`")
    for rel, txt in md_files.items():
        for m in ref_re.finditer(txt):
            target = m.group(1).lstrip("./")
            if target in all_paths or os.path.basename(target) in all_paths:
                continue
            if os.path.basename(target) in RUNTIME_GENERATED:
                continue  # kosu sirasinda uretilir, pakette olmasi beklenmez
            if target.endswith((".json", ".txt")):
                continue  # kullanicinin uretecegi dosyalar
            line = txt[: m.start()].count("\n") + 1
            add("CITATION_MISSING", "P1", f"{rel}:{line}",
                f"pakette olmayan dosyaya referans: {target}",
                "referansi duzelt veya dosyayi ekle")

    # --- 7. Her cekirdek/profil dosyasi geri isaret etmeli ----------------
    for rel, txt in md_files.items():
        if rel == ANA or not rel.endswith(".md"):
            continue
        if rel in ("001_SORUN_CIKARSA_OKU.md",
                   "ARACLAR/BAGIMSIZ_DENETIM_YENI_SOHBETE_YAPISTIR.md"):
            continue
        first = txt.splitlines()[0] if txt.splitlines() else ""
        if not first.startswith(">"):
            add("STYLE_FAILURE", "P1", rel,
                "ilk satir geri isaret eden yonlendirme notu degil",
                f"ilk satira '> Bu dosya tek basina calistirilmaz...' ekle")

    # --- 8. Ornek rapor kendi ilk-ekran butcesine uyuyor mu? --------------
    ornek = md_files.get(ORNEK_RAPOR)
    if ornek:
        m = re.search(r"## İLK EKRAN.*?\n```\n(.*?)\n```", ornek, re.S)
        if not m:
            add("SCHEMA_INVALID", "P1", ORNEK_RAPOR,
                "ILK EKRAN blogu bulunamadi", "ornek raporda ILK EKRAN blogu olmali")
        else:
            blok = m.group(1)
            nl, nc = len(blok.splitlines()), len(blok)
            if nl > ILK_EKRAN_SATIR or nc > ILK_EKRAN_KARAKTER:
                add("STYLE_FAILURE", "P1", ORNEK_RAPOR,
                    f"ornek ilk ekran {nl} satir / {nc} karakter; "
                    f"sinir {ILK_EKRAN_SATIR} / {ILK_EKRAN_KARAKTER}",
                    "ornegi kisalt ya da sozlesmedeki siniri gercekci yap - "
                    "kendi kuralini ihlal eden ornek, kurali gecersiz kilar")

    p0, p1, p2 = recount(findings)
    report = {
        "arac": "ALI_KOMUT_TOOLKIT_v4",
        "kapi": "TUTARLILIK",
        "kok": root,
        "verdict": verdict_from(p0, p1),
        "incelenen_dosya": len(md_files),
        "kapsam": kapsam,
        "counts": {"P0": p0, "P1": p1, "P2": p2},
        "findings": findings,
    }
    emit(report, args.out, args.sessiz)
    return EXIT_BLOCK if (p0 or p1) else EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        fail_closed(f"beklenmeyen hata: {type(exc).__name__}: {exc}")
        sys.exit(EXIT_USAGE)
