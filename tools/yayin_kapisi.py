#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yayin_kapisi.py — public agacin yayin sozlesmesini fail-closed uygular.

NE YAPAR
  `tools/yayin_manifest.json` icindeki ACIK izinli dosya listesini tek kaynak
  kabul eder; `git ls-files --cached --others --exclude-standard` ile yayina
  girebilecek dosyalari okur. Dort soru sorar:

    1. Dosya manifestte listeli mi? (listelenmemis dosya = FAIL)
    2. Yol/uzanti yasak mi? (makale, PDF, proje ciktisi vb.)
    3. Icerikte sir/token veya kisisel mutlak yol var mi?
    4. Icerik makale iskeleti tasiyor mu?

  Manifestte olup agacta bulunmayan yol da FAIL'dir; boylece iki yonlu parite
  korunur. Bulgu metni yalniz dosya, satir ve kural kimligi basar; sirlarin
  kendisini asla yazmaz.

NEDEN AYRI KAPI
  `kamu_lint` ve `sir_kapisi` mevcut riskleri tarar; bu kapi yayin kapsamini
  (izinli dosya listesi) ve makale/raw icerik sinirini tek yerde birlestirir.
  `tools/yayinla.py` kaynak labdan aktarim yapar; bu kapi hedef agacin kendisini
  denetler. Ikisi birbirinin yerine gecmez.

KULLANIM
  python3 tools/yayin_kapisi.py --kontrol
  python3 tools/yayin_kapisi.py --oztest
  python3 tools/yayin_kapisi.py --kontrol --oztest
  python3 tools/yayin_kapisi.py --kontrol --kok <baska-agac> \
      --manifest tools/yayin_manifest.json

CIKIS
  0 = temiz · 1 = yayin ihlali · 2 = manifest/arac hatasi (fail-closed)

KODLAR
  YAYIN-01  manifestte listelenmemis dosya
  YAYIN-02  yasak yol veya uzanti
  YAYIN-03  sir/token deseni
  YAYIN-04  okunamayan veya 5 MB ustu dosya
  YAYIN-05  kisisel mutlak yol
  YAYIN-06  makale iskeleti/isareti
  YAYIN-07  manifestte olup agacta olmayan yol
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
MANIFEST = "tools/yayin_manifest.json"
SEMA = "ATLAS-YAYIN/v1"
AZAMI_BAYT = 5 * 1024 * 1024

# Parcali yazim: kamu_lint bu betigi tararken kendi desenini yakalamaz.
OZEL_YOL = [
    re.compile("/" + "Users" + "/"),
    # `/HOME/bütçe` gibi düzyazı değil, gerçek Linux ev dizini. CI'nın
    # `/home/runner/...` yolu kişisel değildir ve bilerek dışarıdadır.
    re.compile(r"/home/(?!runner/)[A-Za-z0-9._-]+/"),
    re.compile("Desktop[\\\\/]" + "MTRX", re.IGNORECASE),
    re.compile("AI_" + "ARASTIRMA_" + "LABI", re.IGNORECASE),
    re.compile(r"[A-Za-z]:[\\/]" + "Users" + r"[\\/]", re.IGNORECASE),
]

# Yalniz yuksek guvenilirlikli token/sir desenleri. Ornek cumlelerde gecen
# `sk-...` gibi kisa yer tutucular eslesmez; gercek uzunluk aranir.
SIR_DESENLERI = [
    ("postgres-dsn", re.compile(r"postgres(?:ql)?://[^\s:/]+:[^\s@]+@")),
    ("neon", re.compile(r"npg_[A-Za-z0-9]{8,}")),
    ("openai", re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{24,}")),
    ("github", re.compile(r"ghp_[A-Za-z0-9]{30,}")),
    ("aws", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("slack", re.compile(r"xox[bap]-[A-Za-z0-9-]{10,}")),
    ("google", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
]
OZEL_ANAHTAR = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----\r?\n[A-Za-z0-9+/=]{64,}"
)

# Makale iskeletinin guclu, yanlis-pozitifi dusuk izleri. `\section{` gibi
# genel komutlar bilerek yoktur: sablon belgeleri onu mesru kullanabilir.
MAKALE_ISARETLERI = [
    "\\" + "documentclass",
    "\\" + "begin" + "{" + "document" + "}",
    "\\" + "end" + "{" + "document" + "}",
    "\\" + "bibliography" + "{",
    "\\" + "begin" + "{" + "abstract" + "}",
    "\\" + "maketitle",
]


def _git(kok, *args):
    try:
        r = subprocess.run(["git", "-C", str(kok)] + list(args),
                           capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("git calistirilamadi: %s" % type(exc).__name__)
    if r.returncode != 0:
        hata = (r.stderr or b"").decode("utf-8", "replace").strip()[:180]
        raise RuntimeError("git rc=%d: %s" % (r.returncode, hata))
    return r.stdout


def _dosyalar(kok):
    """Yayina girebilecek izlenen + izlenmeyen (ignore disi) dosyalar."""
    ham = _git(kok, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    sonuc = []
    for parca in ham.split(b"\0"):
        if not parca:
            continue
        try:
            sonuc.append(parca.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise RuntimeError("dosya adi UTF-8 degil: %s" % exc)
    # Ayni yol iki kez gelirse (cached + others) tekillestir.
    return sorted(set(sonuc))


def _yol_norm(yol):
    norm = str(yol).replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    return norm


def _manifest_oku(kok, rel):
    yol = Path(rel)
    if not yol.is_absolute():
        yol = Path(kok) / yol
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise RuntimeError("manifest okunamadi: %s" % type(exc).__name__)
    if not isinstance(veri, dict) or veri.get("schema") != SEMA:
        raise RuntimeError("manifest semasi %s degil" % SEMA)
    izinli = veri.get("izinli")
    if not isinstance(izinli, list) or not izinli:
        raise RuntimeError("manifest.izinli bos veya liste degil")
    temiz = []
    gorulen = set()
    for ham in izinli:
        if not isinstance(ham, str) or not ham.strip():
            raise RuntimeError("manifest.izinli gecersiz kayit")
        norm = _yol_norm(ham)
        if (not norm or norm.startswith("/") or ".." in norm.split("/")
                or "\0" in norm):
            raise RuntimeError("manifest.izinli gecersiz yol: %r" % ham)
        if norm in gorulen:
            raise RuntimeError("manifest.izinli yinelenen yol: %s" % norm)
        gorulen.add(norm)
        temiz.append(norm)
    yasak_yollar = veri.get("yasak_yollar", [])
    yasak_uzantilar = veri.get("yasak_uzantilar", [])
    if not isinstance(yasak_yollar, list) or not isinstance(yasak_uzantilar, list):
        raise RuntimeError("manifest yasak listeleri gecersiz")
    return temiz, [str(x) for x in yasak_yollar], [str(x).lower() for x in yasak_uzantilar]


def _bulgu(kod, yol, satir, ayrinti):
    return "%s %s:%s %s" % (kod, yol, satir, ayrinti)


def _sir_fiksturleri(kok):
    """Yalniz dosya + TAM satir SHA-256'si ile belgelenmis sahte sirlar."""
    yol = Path(kok) / "tools" / "secret_fixtures.json"
    if not yol.is_file():
        return set()
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return set()
    kayitlar = set()
    for kayit in veri.get("fiksturler", []):
        if not isinstance(kayit, dict):
            continue
        dosya = str(kayit.get("dosya", "")).replace("\\", "/")
        h = str(kayit.get("satir_sha256", ""))
        if dosya and re.fullmatch(r"[0-9a-f]{64}", h):
            kayitlar.add((dosya, h))
    return kayitlar


def _icerik_bulgular(rel, metin, sir_fikstur):
    bulgular = []
    for no, satir in enumerate(metin.splitlines(), 1):
        h = hashlib.sha256(satir.encode("utf-8")).hexdigest()
        fikstur = (rel, h) in sir_fikstur
        for desen in OZEL_YOL:
            if desen.search(satir):
                bulgular.append(_bulgu("YAYIN-05", rel, no,
                                       "kisisel mutlak yol"))
                break
        if fikstur:
            continue
        for ad, desen in SIR_DESENLERI:
            if desen.search(satir):
                bulgular.append(_bulgu("YAYIN-03", rel, no,
                                       "sir/token deseni: %s" % ad))
                break
    for ad in MAKALE_ISARETLERI:
        if ad in metin:
            bulgular.append(_bulgu("YAYIN-06", rel, 1,
                                   "makale iskeleti: %s" % ad.replace("\\", "")))
    for eslesme in OZEL_ANAHTAR.finditer(metin):
        no = metin[:eslesme.start()].count("\n") + 1
        satirlar = metin.splitlines()
        satir = satirlar[no - 1] if no - 1 < len(satirlar) else ""
        h = hashlib.sha256(satir.encode("utf-8")).hexdigest()
        if (rel, h) not in sir_fikstur:
            bulgular.append(_bulgu("YAYIN-03", rel, no, "private-key blogu"))
    return bulgular


def _tara(kok, manifest_rel):
    izinli, yasak_yollar, yasak_uzantilar = _manifest_oku(kok, manifest_rel)
    izinli_kume = set(izinli)
    sir_fikstur = _sir_fiksturleri(kok)
    dosyalar = _dosyalar(kok)
    dosya_kume = set(dosyalar)
    bulgular = []

    for rel in dosyalar:
        norm = _yol_norm(rel)
        if norm not in izinli_kume:
            bulgular.append(_bulgu("YAYIN-01", rel, 1,
                                   "manifestte listelenmemis dosya"))
        for onek in yasak_yollar:
            if norm == onek or norm.startswith(onek.rstrip("/") + "/"):
                bulgular.append(_bulgu("YAYIN-02", rel, 1,
                                       "yasak yol: %s" % onek))
                break
        uzanti = os.path.splitext(norm)[1].lower()
        if uzanti in yasak_uzantilar:
            bulgular.append(_bulgu("YAYIN-02", rel, 1,
                                   "yasak uzanti: %s" % uzanti))

        tam = Path(kok) / rel
        if tam.is_symlink():
            hedef = os.readlink(tam)
            for desen in OZEL_YOL:
                if desen.search(hedef):
                    bulgular.append(_bulgu("YAYIN-05", rel, 1,
                                           "symlink hedefinde kisisel yol"))
                    break
            continue
        try:
            boy = tam.stat().st_size
            if boy > AZAMI_BAYT:
                bulgular.append(_bulgu("YAYIN-04", rel, 1,
                                       "5 MB ustu: %d bayt" % boy))
                continue
            veri = tam.read_bytes()
        except OSError as exc:
            bulgular.append(_bulgu("YAYIN-04", rel, 1,
                                   "okunamadi: %s" % type(exc).__name__))
            continue
        metin = veri.decode("utf-8", "replace")
        bulgular.extend(_icerik_bulgular(rel, metin, sir_fikstur))

    for rel in sorted(izinli_kume - dosya_kume):
        bulgular.append(_bulgu("YAYIN-07", rel, 1,
                               "manifestte var, agacta yok"))
    return len(dosyalar), len(izinli), bulgular


def _oztest():
    """Temiz + dort ayri ihlal vakasini gecici bir git deposunda olcer."""
    hatalar = []
    with tempfile.TemporaryDirectory(prefix="atlas-yayin-") as td:
        kok = Path(td)
        try:
            _git(kok, "init", "-q")
            (kok / "tools").mkdir()
            (kok / "temiz.txt").write_text("temiz kamu dosyasi\n", encoding="utf-8")
            manifest = {
                "schema": SEMA,
                "izinli": ["temiz.txt", "tools/yayin_manifest.json"],
                "yasak_yollar": ["projeler/"],
                "yasak_uzantilar": [".pdf", ".tex"],
            }
            (kok / "tools" / "yayin_manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
            _git(kok, "add", "-A")
            n, m, bulgular = _tara(kok, "tools/yayin_manifest.json")
            if bulgular or n != 2 or m != 2:
                hatalar.append("temiz taban beklenmedik: n=%d m=%d %r"
                               % (n, m, bulgular[:3]))

            (kok / ".test-gizli.txt").write_text(
                "postgres" + "://kullanici:parola@example.invalid/veritabani\n",
                encoding="utf-8")
            (kok / ".test-yol.txt").write_text(
                "/" + "Users/" + "ornek/kisisel/yol\n", encoding="utf-8")
            (kok / "projeler").mkdir()
            (kok / "projeler" / "ornek-makale.md").write_text(
                "\\" + "documentclass{article}\n"
                "\\" + "begin{document}\n" + "metin\n"
                "\\" + "end{document}\n", encoding="utf-8")
            (kok / "listesiz.txt").write_text("izinsiz\n", encoding="utf-8")
            _, _, bulgular = _tara(kok, "tools/yayin_manifest.json")
            kodlar = {b.split()[0] for b in bulgular}
            for kod in ("YAYIN-01", "YAYIN-02", "YAYIN-03", "YAYIN-05",
                        "YAYIN-06"):
                if kod not in kodlar:
                    hatalar.append("%s bekleniyor, bulunan %r"
                                   % (kod, sorted(kodlar)))
        except (OSError, RuntimeError, ValueError) as exc:
            hatalar.append("oztest kosulamadi: %s" % exc)

    if hatalar:
        for hata in hatalar:
            print("FAIL YAYIN-KAPISI OZTEST " + hata)
        print("YAYIN-KAPISI OZ-TEST: FAIL — %d hata" % len(hatalar))
        return 1
    print("YAYIN-KAPISI OZ-TEST: PASS — 5/5")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="ATLAS public yayin kapisi")
    ap.add_argument("--kontrol", action="store_true",
                    help="gercek agaci manifestle karsilastir")
    ap.add_argument("--oztest", action="store_true",
                    help="gecici depoda temiz + ihlal vakalarini kos")
    ap.add_argument("--kok", default=None, help="denetlenecek agac (varsayilan: bu depo)")
    ap.add_argument("--manifest", default=None,
                    help="manifest yolu (varsayilan: %s)" % MANIFEST)
    a = ap.parse_args(argv)
    if not a.kontrol and not a.oztest:
        ap.error("--kontrol veya --oztest gerekli")

    rc = 0
    if a.oztest:
        rc = _oztest()
        if rc != 0:
            return rc
    if a.kontrol:
        kok = Path(a.kok).resolve() if a.kok else KOK
        manifest = a.manifest or MANIFEST
        try:
            n, m, bulgular = _tara(kok, manifest)
        except (OSError, RuntimeError, ValueError) as exc:
            print("FAIL YAYIN-KAPISI ARAC — %s" % exc)
            return 2
        if bulgular:
            for satir in bulgular[:40]:
                print("FAIL " + satir)
            if len(bulgular) > 40:
                print("FAIL ... +%d bulgu" % (len(bulgular) - 40))
            print("YAYIN-KAPISI: FAIL — %d bulgu · agac=%d manifest=%d"
                  % (len(bulgular), n, m))
            return 1
        print("YAYIN-KAPISI: PASS — 0 bulgu · agac=%d manifest=%d · parite=0/0"
              % (n, m))
    return rc


if __name__ == "__main__":
    sys.exit(main())
