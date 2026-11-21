#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kanit_paketi_dogrula.py — tasinabilir kanit paketini fail-closed dogrular.

Paket `make kanit` tarafindan uretilir. Bu betik paketi tek basina degil,
icindeki kanitlari birbirine baglayarak dogrular:

  PAKET-00  paket/dizin/sema/arac yok; kapi acilmaz
  PAKET-01  sonuc.json JSON Schema'ya uymuyor
  PAKET-02  zorunlu dosya/komut kaydi eksik veya fazla
  PAKET-03  manifest.sha256 bicimi, kapsami veya hash'i tutmuyor
  PAKET-04  attestation.json gecersiz veya commit/agacla uyusmuyor
  PAKET-05  komut log hash'i, cikis kodu veya bulgu kimligi tutmuyor
  PAKET-06  sonuc.json ic tutarliligi (commit/tree/manifest/findings) bozuk

Kullanim:
  python3 tools/kanit_paketi_dogrula.py
  python3 tools/kanit_paketi_dogrula.py --paket kanit-paketi
  python3 tools/kanit_paketi_dogrula.py --paket /tmp/atlas-kanit-paketi

CIKIS: 0 = paket temiz · 1 = paket FAIL · 2 = paket/arac yok veya okunamadi
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath

KOK = Path(__file__).resolve().parent.parent
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover - CI kurulumu bunu saglar
    Draft202012Validator = None
    FormatChecker = None

from tools.kanit import bulgu_kimlikleri  # noqa: E402

SEMA_DOSYASI = KOK / "schemas" / "atlas-dogrulama-sonuc.schema.json"
SEMA_SONUC = "ATLAS-DOGRULAMA/v1"
SONUC = "sonuc.json"
ATTESTATION = "attestation.json"
MANIFEST = "manifest.sha256"
LOG_DIZINI = "komutlar"
SHA = re.compile(r"^[0-9a-f]{64}$")


def hata(kod, mesaj):
    print("FAIL %s %s" % (kod, mesaj))


def oku_json(yol):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        hata("PAKET-00", "OKUNAMADI — %s: %s" % (yol, type(e).__name__))
        return None


def guvenli_yol(p):
    if not isinstance(p, str) or not p or "\\" in p:
        return False
    pp = PurePosixPath(p)
    return not pp.is_absolute() and ".." not in pp.parts


def sha256(yol):
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def manifest_oku(yol):
    """Manifest satirlarini {yol: sha256} olarak dondur; bicim hatasi None."""
    try:
        metin = yol.read_text(encoding="utf-8")
    except OSError as e:
        hata("PAKET-03", "MANIFEST_OKUNAMADI — %s" % e)
        return None
    kayitlar = {}
    for no, satir in enumerate(metin.splitlines(), 1):
        if not satir.strip():
            continue
        m = re.fullmatch(r"([0-9a-f]{64})  (.+)", satir)
        if not m:
            hata("PAKET-03", "MANIFEST_BICIM — satir=%d" % no)
            return None
        h, p = m.group(1), m.group(2)
        if not guvenli_yol(p) or p == MANIFEST:
            hata("PAKET-03", "MANIFEST_YOL — %r" % p)
            return None
        if p in kayitlar:
            hata("PAKET-03", "MANIFEST_YINELENEN — %s" % p)
            return None
        kayitlar[p] = h
    if not kayitlar:
        hata("PAKET-03", "MANIFEST_BOS")
        return None
    return kayitlar


def main():
    ap = argparse.ArgumentParser(description="ATLAS kanit paketini dogrula")
    ap.add_argument("--paket", default=str(KOK / "kanit-paketi"),
                    help="paket dizini")
    ap.add_argument("--sema", default=str(SEMA_DOSYASI),
                    help="ATLAS-DOGRULAMA/v1 JSON Schema yolu")
    a = ap.parse_args()

    if Draft202012Validator is None:
        hata("PAKET-00", "ARAC_YOK — jsonschema kurulu degil; "
                          "`python3 -m pip install -r requirements-dev.txt`")
        return 2

    paket = Path(a.paket)
    if not paket.is_absolute():
        paket = KOK / paket
    if not paket.is_dir():
        hata("PAKET-00", "DIZIN_YOK — %s" % paket)
        return 2
    for ad in (SONUC, ATTESTATION, MANIFEST):
        if not (paket / ad).is_file():
            hata("PAKET-02", "DOSYA_YOK — %s" % (paket / ad))
            return 1
    if not (paket / LOG_DIZINI).is_dir():
        hata("PAKET-02", "DIZIN_YOK — %s" % (paket / LOG_DIZINI))
        return 1

    sema_yolu = Path(a.sema)
    if not sema_yolu.is_absolute():
        sema_yolu = KOK / sema_yolu
    sema = oku_json(sema_yolu)
    if sema is None:
        return 2
    sonuc = oku_json(paket / SONUC)
    if sonuc is None:
        return 2
    at = oku_json(paket / ATTESTATION)
    if at is None:
        return 2

    try:
        Draft202012Validator.check_schema(sema)
        Draft202012Validator(sema, format_checker=FormatChecker()).validate(sonuc)
    except Exception as e:
        hata("PAKET-01", "SONUC_SEMA — %s" % str(e).splitlines()[0][:240])
        return 1
    if sonuc.get("schema") != SEMA_SONUC:
        hata("PAKET-01", "SONUC_SEMA — schema=%r" % sonuc.get("schema"))
        return 1
    try:
        zaman = datetime.fromisoformat(
            str(sonuc["generated_at"]).replace("Z", "+00:00"))
        if zaman.tzinfo is None:
            raise ValueError("timezone yok")
    except (KeyError, TypeError, ValueError):
        hata("PAKET-01", "SONUC_SEMA — generated_at ISO-8601/timezone degil")
        return 1

    # Attestation'i mevcut fail-closed agac kapisiyla dogrula. Bu, commit'in
    # gercek oldugunu, agac hash'lerini ve guncel HEAD ile uyumunu kapsar.
    r = subprocess.run(
        [sys.executable, str(KOK / "tools" / "kanit_dogrula.py"),
         "--kanit", str(paket / ATTESTATION)],
        cwd=str(KOK), capture_output=True, text=True)
    if r.returncode != 0:
        hata("PAKET-04", "ATTESTATION — kanit_dogrula rc=%d" % r.returncode)
        for satir in ((r.stdout or "") + (r.stderr or "")).splitlines()[-4:]:
            print("  | " + satir[:240])
        return 1
    if sonuc.get("commit") != at.get("commit") or \
            sonuc.get("tree") != at.get("tree"):
        hata("PAKET-04", "ATTESTATION — commit/tree sonuc ile uyusmuyor")
        return 1
    if sonuc.get("attestation_sha256") != sha256(paket / ATTESTATION):
        hata("PAKET-04", "ATTESTATION — sha256 tutmuyor")
        return 1
    if sonuc.get("manifest", {}).get("files") != at.get("files") or \
            sonuc.get("manifest", {}).get("root_sha256") != at.get("tree_sha256"):
        hata("PAKET-06", "MANIFEST — sonuc/attestation dosya listesi veya kok hash farki")
        return 1

    komutlar = sonuc.get("commands")
    if not isinstance(komutlar, list) or not komutlar:
        hata("PAKET-02", "KOMUTLAR — bos veya liste degil")
        return 1
    if sonuc.get("command_count") != len(komutlar):
        hata("PAKET-06", "KOMUT_SAYISI — command_count=%r len=%d"
             % (sonuc.get("command_count"), len(komutlar)))
        return 1

    beklenen_loglar = set()
    bulgu_komutlari = {}
    ilk_sifir_olmayan = 0
    for sira, c in enumerate(komutlar, 1):
        if not isinstance(c, dict):
            hata("PAKET-02", "KOMUT[%d] — nesne degil" % sira)
            return 1
        kid = c.get("id")
        if not isinstance(kid, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", kid):
            hata("PAKET-02", "KOMUT[%d].id gecersiz" % sira)
            return 1
        if not isinstance(c.get("argv"), list) or not c["argv"] or \
                not all(isinstance(x, str) for x in c["argv"]):
            hata("PAKET-02", "KOMUT[%d].argv gecersiz" % sira)
            return 1
        if type(c.get("exit_code")) is not int:
            hata("PAKET-05", "KOMUT[%d].exit_code int degil" % sira)
            return 1
        if c["exit_code"] == 0 and c.get("status") != "PASS":
            hata("PAKET-05", "KOMUT[%d] rc=0 ama status=%r" % (sira, c.get("status")))
            return 1
        if c["exit_code"] != 0:
            ilk_sifir_olmayan = ilk_sifir_olmayan or c["exit_code"]
            if c.get("status") not in ("FAIL", "ERROR"):
                hata("PAKET-05", "KOMUT[%d] rc=%d ama status=%r"
                     % (sira, c["exit_code"], c.get("status")))
                return 1
        temel = "%s/%02d-%s" % (LOG_DIZINI, sira, kid)
        for uzanti in ("stdout.txt", "stderr.txt"):
            rel = temel + "." + uzanti
            beklenen_loglar.add(rel)
            yol = paket / rel
            if not yol.is_file():
                hata("PAKET-02", "LOG_YOK — %s" % rel)
                return 1
            ham = yol.read_text(encoding="utf-8")
            if sha256(yol) != c.get(uzanti.replace(".txt", "") + "_sha256"):
                hata("PAKET-05", "LOG_HASH — %s" % rel)
                return 1
            if len(ham.encode("utf-8")) != c.get(uzanti.replace(".txt", "") + "_bytes"):
                hata("PAKET-05", "LOG_BYTES — %s" % rel)
                return 1
        birlesik = ((paket / (temel + ".stdout.txt")).read_text(encoding="utf-8")
                    + "\n" +
                    (paket / (temel + ".stderr.txt")).read_text(encoding="utf-8"))
        kimlikler = bulgu_kimlikleri(birlesik)
        if kimlikler != c.get("finding_ids"):
            hata("PAKET-05", "BULGU_KIMLIK — %s beklenen=%s bulunan=%s"
                 % (kid, c.get("finding_ids"), kimlikler))
            return 1
        for bid in kimlikler:
            bulgu_komutlari.setdefault(bid, []).append(kid)

    gercek_loglar = {p.relative_to(paket).as_posix()
                     for p in (paket / LOG_DIZINI).glob("*") if p.is_file()}
    if gercek_loglar != beklenen_loglar:
        hata("PAKET-02", "LOG_KUMESI — eksik=%s fazla=%s"
             % (sorted(beklenen_loglar - gercek_loglar),
                sorted(gercek_loglar - beklenen_loglar)))
        return 1

    if sonuc.get("exit_code") != ilk_sifir_olmayan:
        hata("PAKET-06", "EXIT_CODE — beklenen=%d bulunan=%r"
             % (ilk_sifir_olmayan, sonuc.get("exit_code")))
        return 1
    beklenen_hukum = "PASS" if all(c.get("status") == "PASS" for c in komutlar) \
        else "FAIL"
    if sonuc.get("verdict") != beklenen_hukum:
        hata("PAKET-06", "VERDICT — beklenen=%s bulunan=%r"
             % (beklenen_hukum, sonuc.get("verdict")))
        return 1

    bulgular = sonuc.get("findings")
    if not isinstance(bulgular, list):
        hata("PAKET-06", "BULGULAR — liste degil")
        return 1
    if {b.get("id") for b in bulgular} != set(bulgu_komutlari):
        hata("PAKET-06", "BULGULAR — kimlik kumesi komut kayitlariyla uyusmuyor")
        return 1
    for b in bulgular:
        if sorted(b.get("commands", [])) != sorted(bulgu_komutlari.get(b.get("id"), [])):
            hata("PAKET-06", "BULGULAR[%r] — komut iliskisi uyusmuyor" % b.get("id"))
            return 1

    manifest = manifest_oku(paket / MANIFEST)
    if manifest is None:
        return 1
    dosyalar = {p.relative_to(paket).as_posix()
                for p in paket.rglob("*") if p.is_file()}
    dosyalar.discard(MANIFEST)
    if set(manifest) != dosyalar:
        hata("PAKET-03", "MANIFEST_KAPSAM — eksik=%s fazla=%s"
             % (sorted(dosyalar - set(manifest)), sorted(set(manifest) - dosyalar)))
        return 1
    for rel, h in manifest.items():
        if not SHA.fullmatch(h) or sha256(paket / rel) != h:
            hata("PAKET-03", "MANIFEST_HASH — %s" % rel)
            return 1

    print("PASS PAKET commit=%s komut=%d dosya=%d"
          % (sonuc["commit"], len(komutlar), len(manifest)))
    print("PAKET: TEMIZ — sonuc semasi, attestation, manifest ve ham "
          "komut kayitlari tutuyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
