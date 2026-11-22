#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kamu_lint.py — kamu agacinda ozel-lab sizintisini fail-closed tarar.

NEDEN VAR: OLG-1'in kaniti kamu agacindaki attestation.json'dir. Bir gun
koda, belgeye veya OLGULAR makine bloguna ozel bir mutlak yol, kaldirilmis
tarihsel commit alani ya da uydurma/elle yazilmis commit hash'i geri girerse
bu kontrol kirmizi olur. Kontrol `make dogrula` on kosuludur; negatif
fiksturleri de ayni komutta kosar.

Kurallar:
  KAMU-01  ozel mutlak yol / lab dizini adi
  KAMU-02  kaldirilmis eski makine alanlari
  KAMU-03  "dış-lab" bagimlilik ifadesi
  KAMU-04  OLGULAR makine blogunda commit-benzeri hash veya eski alan
  KAMU-05  olgu_lint'te attestation disi fallback izi
  KAMU-06  attestation.json gercek commit/agacla dogrulanamiyor

Kullanim:
  python3 tools/kamu_lint.py --kontrol   # depoyu tara
  python3 tools/kamu_lint.py --oztest    # negatif fiksturler
CIKIS: 0 = temiz · 1 = bulgu · 2 = kullanim/arac hatasi
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
OLGULAR = "docs/OLGULAR.md"
OLGU_LINT = "ATLAS_SABLONLAR/scripts/olgu_lint.py"
KANIT_ARACI = "tools/kanit_dogrula.py"

# Parcali yazim: bu betigin kendisi taranirken kendi desenini yakalamaz.
OZEL_YOL = re.compile(
    "|".join([
        "/" + "Users/",
        "Desktop[\\\\/]" + "MTRX",
        "AI_" + "ARASTIRMA_LABI",
        "MTRX[\\\\/]" + "AI_",
    ]),
    re.IGNORECASE,
)
ESKI_ALAN = re.compile(
    r"\b(?:" + "|".join([
        "baseline_" + "commit",
        "mekanizma_" + "sayisi",
        "mekanizma_" + "kayitlari",
    ]) + r")\b"
)
OZEL_IFADE = re.compile(
    "|".join([
        "\u00f6zel" + r"\s*" + "a\u011fa\u00e7",
        "ozel" + r"\s*" + "agac",
        "\u00f6zel" + "-" + "a\u011fa\u00e7",
        "private" + r"\s+" + "tree",
    ]),
    re.IGNORECASE,
)
HEX_HASH = re.compile(r"^[0-9a-fA-F]{7,40}$")
KANIT_CAGRI = "kanit_" + "dogrula.py"
FALLBACK_IZLERI = (
    "merge" + "-base",
    "cat" + "-file",
    "COMMIT_" + "ATA_DEGIL",
)


def bulgu(kod, yol, satir, ayrinti):
    return "%s %s:%s %s" % (kod, yol, satir, ayrinti)


def tara_metin(metin, yol):
    """Tek dosya metnini tarar; (bulgular) dondurur."""
    bulgular = []
    for no, satir in enumerate(metin.splitlines(), 1):
        if OZEL_YOL.search(satir):
            bulgular.append(bulgu("KAMU-01", yol, no, "ozel mutlak yol/lab adi"))
        if ESKI_ALAN.search(satir):
            bulgular.append(bulgu("KAMU-02", yol, no, "kaldirilmis makine alani"))
        if OZEL_IFADE.search(satir):
            bulgular.append(bulgu("KAMU-03", yol, no, "dış-lab bagimlilik ifadesi"))

    if yol == OLGULAR:
        bulgular.extend(_makine_blok(metin, yol))
    if yol == OLGU_LINT:
        for iz in FALLBACK_IZLERI:
            if iz in metin:
                bulgular.append(bulgu("KAMU-05", yol, 1,
                                      "attestation disi fallback izi: %s" % iz))
        if KANIT_CAGRI not in metin:
            bulgular.append(bulgu("KAMU-05", yol, 1,
                                  "kanit_dogrula cagrisi yok"))
    return bulgular


def _json_yurun(veri, yol, iz):
    if isinstance(veri, dict):
        for anahtar, deger in veri.items():
            if isinstance(anahtar, str) and HEX_HASH.fullmatch(anahtar):
                return bulgu("KAMU-04", yol, 1,
                             "makine blogunda hash-benzeri anahtar: %s" % anahtar)
            sonuc = _json_yurun(deger, yol, iz)
            if sonuc:
                return sonuc
    elif isinstance(veri, list):
        for deger in veri:
            sonuc = _json_yurun(deger, yol, iz)
            if sonuc:
                return sonuc
    elif isinstance(veri, str) and HEX_HASH.fullmatch(veri):
        return bulgu("KAMU-04", yol, 1,
                     "makine blogunda commit-benzeri deger: %s" % veri)
    return None


def _makine_blok(metin, yol):
    """OLGULAR makine blogunu sema ve hash sizintisi icin denetler."""
    eslesme = re.search(
        r"<!-- OLGULAR_JSON_BASLA -->\s*```json\s*(\{.*?\})\s*```\s*"
        r"<!-- OLGULAR_JSON_BITIR -->",
        metin,
        re.DOTALL,
    )
    if not eslesme:
        return [bulgu("KAMU-04", yol, 1, "makine blogu bulunamadi")]
    try:
        veri = json.loads(eslesme.group(1))
    except (TypeError, ValueError):
        return [bulgu("KAMU-04", yol, 1, "makine blogu gecersiz JSON")]
    if not isinstance(veri, dict):
        return [bulgu("KAMU-04", yol, 1, "makine blogu sozluk degil")]
    if veri.get("schema") != "OLGULAR/v2":
        return [bulgu("KAMU-04", yol, 1, "schema OLGULAR/v2 degil")]
    if veri.get("kamu_kaniti") != "attestation.json":
        return [bulgu("KAMU-04", yol, 1, "kamu_kaniti attestation.json degil")]
    sizinti = _json_yurun(veri, yol, "")
    return [sizinti] if sizinti else []


def _izlenen_dosyalar():
    r = subprocess.run(
        ["git", "-C", str(KOK), "ls-files", "-z"],
        capture_output=True,
    )
    if r.returncode != 0:
        raise RuntimeError("git ls-files rc=%d" % r.returncode)
    return [x.decode("utf-8") for x in r.stdout.split(b"\0") if x]


def tara_agac():
    bulgular = []
    sayi = 0
    for rel in _izlenen_dosyalar():
        yol = KOK / rel
        try:
            ham = yol.read_bytes()
        except OSError as exc:
            bulgular.append(bulgu("KAMU-01", rel, 1,
                                  "okunamadi: %s" % type(exc).__name__))
            continue
        sayi += 1
        metin = ham.decode("utf-8", "replace")
        bulgular.extend(tara_metin(metin, rel))
    return sayi, bulgular


def kanit_kontrol():
    arac = KOK / KANIT_ARACI
    if not arac.is_file():
        return [bulgu("KAMU-06", KANIT_ARACI, 1, "kanit araci yok")]
    r = subprocess.run(
        [sys.executable, str(arac)],
        cwd=str(KOK), capture_output=True, text=True,
    )
    if r.returncode != 0:
        son = ((r.stdout or "") + (r.stderr or "")).strip().splitlines()
        return [bulgu("KAMU-06", "attestation.json", 1,
                      son[-1][:180] if son else "kanit rc=%d" % r.returncode)]
    return []


def oztest():
    vakalar = [
        ("ozel yol", "x = '/" + "Users/" + "ali/lab'\n", "KAMU-01"),
        ("eski alan", "baseline_" + "commit: 1234567\n", "KAMU-02"),
        ("ozel ifade", "bu " + "\u00f6zel" + " " + "a\u011fa\u00e7" + " bagimlidir\n", "KAMU-03"),
        ("temiz", "kamu agaci yalniz attestation.json kullanir\n", None),
    ]
    hatalar = []
    for ad, metin, beklenen in vakalar:
        bulgular = tara_metin(metin, "README.md")
        kodlar = [b.split()[0] for b in bulgular]
        if beklenen is None:
            if bulgular:
                hatalar.append("%s: beklenmeyen bulgu %r" % (ad, bulgular))
        elif beklenen not in kodlar:
            hatalar.append("%s: %s bekleniyor, bulunan %r" % (ad, beklenen, kodlar))

    # Makine blogu: uydurma hash ve eski alan ayri ayri yakalanmali.
    sahte = ('<!-- OLGULAR_JSON_BASLA -->\n```json\n'
             '{"schema":"OLGULAR/v2","kamu_kaniti":"attestation.json",'
             '"lab_surum":"v1","x":"deadbeef"}\n```\n'
             '<!-- OLGULAR_JSON_BITIR -->\n')
    bulgular = tara_metin(sahte, OLGULAR)
    if not any(b.startswith("KAMU-04") for b in bulgular):
        hatalar.append("makine blogu: sahte hash yakalanmadi")

    # olgu_lint'te fallback izi ve kanit cagrisi denetimi.
    fallback = "def x():\n    git('merge" + "-base', '--is-ancestor')\n"
    bulgular = tara_metin(fallback, OLGU_LINT)
    if not any(b.startswith("KAMU-05") for b in bulgular):
        hatalar.append("olgu_lint: fallback izi yakalanmadi")
    bulgular = tara_metin("print('x')\n", OLGU_LINT)
    if not any("kanit_dogrula cagrisi yok" in b for b in bulgular):
        hatalar.append("olgu_lint: kanit cagrisi yoklugu yakalanmadi")

    if hatalar:
        for hata in hatalar:
            print("FAIL KAMU-LINT OZTEST " + hata)
        print("KAMU-LINT OZ-TEST: FAIL — %d/%d" % (len(vakalar) + 3 - len(hatalar),
                                                   len(vakalar) + 3))
        return 1
    print("KAMU-LINT OZ-TEST: PASS — 7/7")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Kamu agaci sizinti kontrolu")
    ap.add_argument("--kontrol", action="store_true", help="izlenen agaci tara")
    ap.add_argument("--oztest", action="store_true", help="negatif fiksturleri kos")
    a = ap.parse_args()
    if a.oztest and not a.kontrol:
        return oztest()
    if not a.kontrol and not a.oztest:
        ap.error("--kontrol veya --oztest gerekli")
    if a.oztest:
        rc = oztest()
        if rc != 0:
            return rc
    try:
        sayi, bulgular = tara_agac()
    except RuntimeError as exc:
        print("FAIL KAMU-LINT ARAC — %s" % exc)
        return 2
    bulgular.extend(kanit_kontrol())
    if bulgular:
        for satir in bulgular[:40]:
            print("FAIL " + satir)
        print("KAMU-LINT: FAIL — %d bulgu" % len(bulgular))
        return 1
    print("KAMU-LINT: PASS — 0 bulgu · %d dosya" % sayi)
    return 0


if __name__ == "__main__":
    sys.exit(main())
