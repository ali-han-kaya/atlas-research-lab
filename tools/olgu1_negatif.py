#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OLG-1 NEGATIF KONTROL — bozuk kanitin kapida yandigini ana agaci kirletmeden olc.

Her kosu ana agacin HEAD'inden gecici bir git klonu uretir ve dort sozlesmeyi
siralar:

  1. temiz taban: `olgu_lint` rc=0 ve `OLGU-LINT PASS` — kapi gercekten acik,
  2. `attestation.json` commit alani var olmayan bir SHA'ya bozulur; `olgu_lint`
     rc=1 ve `FAIL OLGU-04 KANIT_GECERSIZ ... COMMIT_YOK` basar,
  3. `atlas_selftest --sessiz` rc=1, `OZ-TEST: 144/145 gecti` ve kalan tek
     kimlik `OLG-1` olur,
  4. ana agacin git durumu, HEAD'i ve attestation hash'i degismez.

Klonda `atlas_selftest`in butun kalemleri kosar; boylece kontrol yalniz
`olgu_lint`in kirmizisini degil, genis paketin 144/145 verdigini de olcer.
Temiz taban kiriksa negatif kontrole gecilmez: bozuk kopyada alinan kirmizi
kanit sayilmaz.

Kullanim: python3 tools/olgu1_negatif.py
CIKIS: 0 = dort sozlesme de tuttu · 1 = sapma veya kurulum hatasi
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ATTESTATION = "attestation.json"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
OZET_RE = re.compile(r"^OZ-TEST:\s*(\d+)/(\d+)\s+gecti\s*$", re.MULTILINE)
KALDI_RE = re.compile(r"^\s*KALDI\s+([^\s:]+)\s*:", re.MULTILINE)


def kos(komut, cwd, timeout, env=None):
    """Alt sureci kos; (sonuc, hata_metni) dondur."""
    try:
        return subprocess.run(komut, cwd=str(cwd), capture_output=True,
                              text=True, timeout=timeout, env=env), None
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def cikti(sonuc):
    if sonuc is None:
        return ""
    return (sonuc.stdout or "") + (sonuc.stderr or "")


def git(kok, *args, timeout=120):
    return kos(["git", "-C", str(kok), *args], KOK, timeout)


def rev(kok, *args):
    sonuc, _ = git(kok, *args)
    if sonuc is None or sonuc.returncode != 0:
        return None
    return sonuc.stdout.strip()


def sha256(yol):
    try:
        return hashlib.sha256(yol.read_bytes()).hexdigest()
    except OSError:
        return None


def durum(kok):
    return rev(kok, "status", "--porcelain", "--untracked-files=all")


def bozuk_commit(klon, eski):
    """Var olmayan, bicimce gecerli bir commit SHA'si uret; yoksa None."""
    for ilk in "0123456789abcdef":
        aday = ilk + eski[1:]
        if aday == eski:
            continue
        sonuc, _ = git(klon, "cat-file", "-e", aday + "^{commit}", timeout=60)
        if sonuc is None or sonuc.returncode != 0:
            return aday
    return None


def senaryo(gecici, head, bekle):
    klon = gecici / "agac"
    sonuc, hata = kos(
        ["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout",
         str(KOK), str(klon)], gecici, 300)
    if sonuc is None or sonuc.returncode != 0:
        raise RuntimeError("gecici klon olusturulamadi: "
                           + (cikti(sonuc) or hata or "rc yok"))
    sonuc, hata = kos(["git", "-C", str(klon), "checkout", "--quiet",
                       "--detach", head], gecici, 120)
    if sonuc is None or sonuc.returncode != 0:
        raise RuntimeError("klonda HEAD checkout edilemedi: "
                           + (cikti(sonuc) or hata or "rc yok"))
    bekle(
        "gecici klon ana HEAD'de temiz",
        rev(klon, "rev-parse", "HEAD") == head and durum(klon) == "",
        "HEAD=%r durum=%r" % (rev(klon, "rev-parse", "HEAD"), durum(klon)),
    )

    lint = klon / "ATLAS_SABLONLAR" / "scripts" / "olgu_lint.py"
    selftest = klon / "ATLAS_SABLONLAR" / "scripts" / "atlas_selftest.py"
    katalog = klon / "tools" / "model_katalog.json"
    for yol in (lint, selftest, katalog):
        if not yol.is_file():
            raise RuntimeError("klonda arac/katalog yok: %s" % yol)
    # `make dogrula` T1 de ayni sabit katalogu enjekte eder. Enjekte edilmezse
    # runner'da ~/.cache/opencode/models.json yok diye MOD-1/MOD-2 de duser ve
    # 144/145 yerine 142/145 olur; bu, OLG-1 negatif kontrolunu bozar.
    ortam = dict(os.environ, ATLAS_MODEL_KATALOG=str(katalog))

    sonuc, hata = kos([sys.executable, str(lint)], klon, 180)
    temiz_cikti = cikti(sonuc)
    bekle(
        "temiz taban: olgu_lint rc=0 · OLGU-LINT PASS",
        sonuc is not None and sonuc.returncode == 0
        and "OLGU-LINT PASS" in temiz_cikti,
        hata or temiz_cikti,
    )
    if sonuc is None or sonuc.returncode != 0:
        raise RuntimeError("temiz taban kirik; negatif kontrol anlamsiz")

    attest = klon / ATTESTATION
    try:
        veri = json.loads(attest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("klonda attestation okunamadi: %s"
                           % type(exc).__name__)
    eski = veri.get("commit") if isinstance(veri, dict) else None
    if not isinstance(eski, str) or not COMMIT_RE.fullmatch(eski):
        raise RuntimeError("attestation commit bicimi gecersiz: %r" % eski)
    yeni = bozuk_commit(klon, eski)
    if yeni is None:
        raise RuntimeError("var olmayan commit adayi uretilemedi")
    veri["commit"] = yeni
    attest.write_text(
        json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  bilgi: attestation commit %s -> %s" % (eski, yeni))

    sonuc, hata = kos([sys.executable, str(lint)], klon, 180)
    bozuk_cikti = cikti(sonuc)
    bekle(
        "bozuk commit: olgu_lint rc=1 · KANIT_GECERSIZ · COMMIT_YOK",
        sonuc is not None and sonuc.returncode == 1
        and "FAIL OLGU-04 KANIT_GECERSIZ" in bozuk_cikti
        and "COMMIT_YOK" in bozuk_cikti,
        hata or bozuk_cikti,
    )

    sonuc, hata = kos([sys.executable, str(selftest), "--sessiz"], klon, 900,
                      env=ortam)
    atlas_cikti = cikti(sonuc)
    ozetler = OZET_RE.findall(atlas_cikti)
    ozet = (int(ozetler[-1][0]), int(ozetler[-1][1])) if ozetler else None
    kalan = sorted(set(KALDI_RE.findall(atlas_cikti)))
    bekle(
        "atlas_selftest rc=1 · OZ-TEST: 144/145 gecti · kalan yalniz OLG-1",
        sonuc is not None and sonuc.returncode == 1
        and ozet == (144, 145) and kalan == ["OLG-1"],
        "%s\nrc=%s ozet=%s kalan=%s\n%s" % (
            hata or "", None if sonuc is None else sonuc.returncode,
            ozet, kalan, atlas_cikti,
        ),
    )


def main():
    hatalar = []
    toplam = 0

    def bekle(ad, gecti, ayrinti=""):
        nonlocal toplam
        toplam += 1
        if gecti:
            print("PASS " + ad)
            return
        print("KALDI " + ad)
        if ayrinti:
            for satir in str(ayrinti).strip().splitlines()[-14:]:
                print("  | " + satir)
        hatalar.append(ad)

    attest_yolu = KOK / ATTESTATION
    head_once = rev(KOK, "rev-parse", "HEAD")
    durum_once = durum(KOK)
    attest_once = sha256(attest_yolu) if attest_yolu.is_file() else None
    if head_once is None or durum_once is None or attest_once is None:
        print("KALDI kurulum: ana agac/attestation okunamadi")
        print("\nOLG-1 NEGATIF KONTROL: FAIL — 0/0")
        return 1

    try:
        with tempfile.TemporaryDirectory(prefix="olgu1-negatif-") as gecici:
            try:
                senaryo(Path(gecici), head_once, bekle)
            except RuntimeError as exc:
                bekle("senaryo tamamlandi", False, str(exc))
    finally:
        head_sonra = rev(KOK, "rev-parse", "HEAD")
        durum_sonra = durum(KOK)
        attest_sonra = sha256(attest_yolu) if attest_yolu.is_file() else None
        bekle(
            "ana agac degismedi (HEAD/status/attestation)",
            head_sonra == head_once and durum_sonra == durum_once
            and attest_sonra == attest_once,
            "HEAD %r -> %r\nstatus %r -> %r\nattestation %r -> %r" % (
                head_once, head_sonra, durum_once, durum_sonra,
                attest_once, attest_sonra,
            ),
        )

    if hatalar:
        print("\nOLG-1 NEGATIF KONTROL: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nOLG-1 NEGATIF KONTROL: PASS — %d/%d · ana agac degismedi"
          % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
