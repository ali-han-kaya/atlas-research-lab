#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kanit_dogrula.py — attestation.json'i gercek commit ve agacla dogrular.

Fail-closed kurallar:
  KANIT-00  attestation.json yok/okunamadi       -> kapi ACILMAZ
  KANIT-01  sema/alan/tip/hash bicimi gecersiz    -> FAIL
  KANIT-02  commit yok, HEAD'in atası degil, tree uyusmuyor -> FAIL
  KANIT-03  kayitli dosya hash'leri commit agaciyla uyusmuyor -> FAIL
  KANIT-04  tree_sha256 yeniden hesapla tutmuyor   -> FAIL
  KANIT-05  guncel HEAD agaci kayitli agactan farkli -> FAIL
  KANIT-06  izlenen agac kirli (attestation disinda) -> FAIL

Neyi KANITLAMAZ: imza/koken/degistirilemezlik, testlerin gectigini, icerigin
dogru oldugunu veya zamani. Ayrintili sinirlar docs/README.md'dedir.

Kullanim: python3 tools/kanit_dogrula.py [--kanit attestation.json]
CIKIS: 0 = temiz · 1 = FAIL · 2 = dosya yok/okunamadi
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
SEMA = "ATLAS-KANIT/v1"
ATTESTATION = "attestation.json"
UST_ALANLAR = {"schema", "generated_at", "commit", "tree", "file_count",
               "files", "tree_sha256", "tool_versions", "scope"}
DOSYA_ALANLARI = {"path", "mode", "size", "sha256"}
ARAC_ALANLARI = {"python", "git", "make", "platform"}
KAPSAM_ALANLARI = {"source", "excludes", "note"}
MODLAR = {"100644", "100755", "120000"}


def git(*args, text=False):
    return subprocess.run(["git", "-C", str(KOK), *args],
                          capture_output=True, text=text)


def git_metin(*args):
    r = git(*args, text=True)
    if r.returncode != 0:
        raise RuntimeError("git %s: %s" % (
            " ".join(args), (r.stderr or "").strip()[:200]))
    return r.stdout


def hata(kod, mesaj):
    print("FAIL %s %s" % (kod, mesaj))


def agac_dosyalari(rev):
    r = git("ls-tree", "-r", "-z", "--full-tree", rev)
    if r.returncode != 0:
        raise RuntimeError("git ls-tree %s: %s" % (
            rev, (r.stderr or b"").decode("utf-8", "replace").strip()[:200]))
    sonuc = []
    for kayit in r.stdout.split(b"\0"):
        if not kayit:
            continue
        meta, ayrac, ham_yol = kayit.partition(b"\t")
        if not ayrac:
            raise RuntimeError("git ls-tree bicimi bozuk")
        try:
            mode, typ, obj = meta.decode("ascii").split()
            yol = ham_yol.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as e:
            raise RuntimeError("git ls-tree alani okunamadi: %s" % e)
        if yol == ATTESTATION:
            continue
        if typ != "blob":
            raise RuntimeError("blob olmayan agac kaydi: %s (%s)" % (yol, typ))
        icerik = git("cat-file", "blob", obj)
        if icerik.returncode != 0:
            raise RuntimeError("git cat-file %s: %s" % (
                obj, (icerik.stderr or b"").decode("utf-8", "replace").strip()[:200]))
        sonuc.append({
            "path": yol,
            "mode": mode,
            "size": len(icerik.stdout),
            "sha256": hashlib.sha256(icerik.stdout).hexdigest(),
        })
    sonuc.sort(key=lambda x: x["path"])
    return sonuc


def agac_ozeti(dosyalar):
    h = hashlib.sha256()
    for f in dosyalar:
        h.update(f["path"].encode("utf-8"))
        h.update(b"\0")
        h.update(f["mode"].encode("ascii"))
        h.update(b"\0")
        h.update(f["sha256"].encode("ascii"))
        h.update(b"\0")
        h.update(str(f["size"]).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def kirli_dosyalar():
    r = git("status", "--porcelain", "--untracked-files=no", text=True)
    if r.returncode != 0:
        raise RuntimeError("git status: %s" % (r.stderr or "").strip()[:200])
    kirli = []
    for satir in r.stdout.splitlines():
        if not satir.strip():
            continue
        yol = satir[3:]
        if " -> " in yol:
            yol = yol.split(" -> ", 1)[1]
        if yol == ATTESTATION:
            continue
        kirli.append(satir)
    return kirli


def ilk_fark(a, b):
    """Iki dosya listesinin ilk farkini okunabilir bicimde dondurur."""
    am = {x["path"]: x for x in a}
    bm = {x["path"]: x for x in b}
    for yol in sorted(set(am) | set(bm)):
        if yol not in am:
            return "yalniz ikincide: %s" % yol
        if yol not in bm:
            return "yalniz birincide: %s" % yol
        if am[yol] != bm[yol]:
            return "alan farki: %s" % yol
    return "bilinmeyen"


def main():
    ap = argparse.ArgumentParser(description="ATLAS agac kanitini dogrula")
    ap.add_argument("--kanit", default=str(KOK / ATTESTATION),
                    help="okunacak JSON yolu (varsayilan: attestation.json)")
    a = ap.parse_args()
    yol = Path(a.kanit)
    if not yol.is_file():
        hata("KANIT-00", "KANIT_YOK — %s; once `make kanit`" % yol)
        return 2
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        hata("KANIT-00", "OKUNAMADI — %s: %s" % (yol, type(e).__name__))
        return 2

    if not isinstance(veri, dict):
        hata("KANIT-01", "SEMA — ust seviye sozluk degil")
        return 1
    if set(veri) != UST_ALANLAR:
        hata("KANIT-01", "SEMA — alanlar: eksik=%s fazla=%s" % (
            sorted(UST_ALANLAR - set(veri)), sorted(set(veri) - UST_ALANLAR)))
        return 1
    if veri.get("schema") != SEMA:
        hata("KANIT-01", "SEMA — beklenen=%s bulunan=%r" % (SEMA, veri.get("schema")))
        return 1

    for alan in ("commit", "tree"):
        deger = veri.get(alan)
        if not isinstance(deger, str) or not re.fullmatch(r"[0-9a-f]{40}", deger) \
                or deger == "0" * 40:
            hata("KANIT-01", "SEMA — %s:40-kucuk-hex (sifir olamaz)" % alan)
            return 1
    if not isinstance(veri.get("generated_at"), str):
        hata("KANIT-01", "SEMA — generated_at:string")
        return 1
    try:
        zaman = datetime.fromisoformat(veri["generated_at"].replace("Z", "+00:00"))
        if zaman.tzinfo is None:
            raise ValueError("timezone yok")
    except (TypeError, ValueError):
        hata("KANIT-01", "SEMA — generated_at:ISO-8601-timezone")
        return 1

    sayi = veri.get("file_count")
    if type(sayi) is not int or sayi < 0:
        hata("KANIT-01", "SEMA — file_count:negatif-olmayan-int")
        return 1
    dosyalar = veri.get("files")
    if not isinstance(dosyalar, list):
        hata("KANIT-01", "SEMA — files:liste")
        return 1
    if sayi != len(dosyalar):
        hata("KANIT-04", "DOSYA_SAYISI — file_count=%d len(files)=%d"
             % (sayi, len(dosyalar)))
        return 1

    gorulen = set()
    onceki = None
    for i, f in enumerate(dosyalar):
        if not isinstance(f, dict) or set(f) != DOSYA_ALANLARI:
            hata("KANIT-01", "SEMA — files[%d] alanlari" % i)
            return 1
        p = f.get("path")
        if not isinstance(p, str) or not p or "\\" in p or p == ATTESTATION:
            hata("KANIT-01", "SEMA — files[%d].path gecersiz" % i)
            return 1
        pp = PurePosixPath(p)
        if pp.is_absolute() or ".." in pp.parts:
            hata("KANIT-01", "SEMA — files[%d].path mutlak/ust dizin" % i)
            return 1
        if onceki is not None and p <= onceki:
            hata("KANIT-01", "SEMA — files sirali/benzersiz degil: %s" % p)
            return 1
        onceki = p
        if p in gorulen:
            hata("KANIT-01", "SEMA — yinelenen path: %s" % p)
            return 1
        gorulen.add(p)
        if f.get("mode") not in MODLAR:
            hata("KANIT-01", "SEMA — files[%d].mode gecersiz" % i)
            return 1
        if type(f.get("size")) is not int or f["size"] < 0:
            hata("KANIT-01", "SEMA — files[%d].size gecersiz" % i)
            return 1
        if not isinstance(f.get("sha256"), str) or \
                not re.fullmatch(r"[0-9a-f]{64}", f["sha256"]):
            hata("KANIT-01", "SEMA — files[%d].sha256 gecersiz" % i)
            return 1

    if not isinstance(veri.get("tree_sha256"), str) or \
            not re.fullmatch(r"[0-9a-f]{64}", veri["tree_sha256"]):
        hata("KANIT-01", "SEMA — tree_sha256:64-kucuk-hex")
        return 1
    hesaplanan = agac_ozeti(dosyalar)
    if hesaplanan != veri["tree_sha256"]:
        hata("KANIT-04", "AGAC_OZETI — beklenen=%s bulunan=%s"
             % (hesaplanan, veri["tree_sha256"]))
        return 1

    araclar = veri.get("tool_versions")
    if not isinstance(araclar, dict) or set(araclar) != ARAC_ALANLARI:
        hata("KANIT-01", "SEMA — tool_versions alanlari")
        return 1
    for ad, deger in araclar.items():
        if not isinstance(deger, str) or not deger.strip():
            hata("KANIT-01", "SEMA — tool_versions.%s bos" % ad)
            return 1

    kapsam = veri.get("scope")
    if not isinstance(kapsam, dict) or set(kapsam) != KAPSAM_ALANLARI:
        hata("KANIT-01", "SEMA — scope alanlari")
        return 1
    if kapsam.get("source") != "git ls-tree -r --full-tree HEAD" or \
            kapsam.get("excludes") != [ATTESTATION] or \
            not isinstance(kapsam.get("note"), str) or not kapsam["note"].strip():
        hata("KANIT-01", "SEMA — scope degeri gecersiz")
        return 1

    try:
        varlik = git("cat-file", "-e", veri["commit"] + "^{commit}", text=True)
        if varlik.returncode != 0:
            hata("KANIT-02", "COMMIT_YOK — %s" % veri["commit"])
            return 1
        ata = git("merge-base", "--is-ancestor", veri["commit"], "HEAD", text=True)
        if ata.returncode != 0:
            hata("KANIT-02", "COMMIT_ATA_DEGIL — %s <= HEAD" % veri["commit"])
            return 1
        tree = git_metin("rev-parse", veri["commit"] + "^{tree}").strip()
        if tree != veri["tree"]:
            hata("KANIT-02", "TREE_UYUSMAZ — commit=%s kayit=%s"
                 % (tree, veri["tree"]))
            return 1
        kayitli = agac_dosyalari(veri["commit"])
        if kayitli != dosyalar:
            hata("KANIT-03", "DOSYA_HASH — %s" % ilk_fark(kayitli, dosyalar))
            return 1
        guncel = agac_dosyalari("HEAD")
        if guncel != kayitli:
            hata("KANIT-05", "AGAC_SURUKLENDI — %s" % ilk_fark(kayitli, guncel))
            return 1
    except (RuntimeError, subprocess.SubprocessError) as e:
        hata("KANIT-02", "GIT — %s" % e)
        return 1

    try:
        kirli = kirli_dosyalar()
        if kirli:
            hata("KANIT-06", "AGAC_KIRLI — %s" % kirli[0])
            return 1
    except RuntimeError as e:
        hata("KANIT-06", "GIT_STATUS — %s" % e)
        return 1

    print("PASS KANIT commit=%s tree=%s dosya=%d tree_sha256=%s"
          % (veri["commit"], veri["tree"], len(dosyalar), veri["tree_sha256"]))
    print("KANIT: TEMIZ — kayitli commit gercek, agac hash'leri tutuyor, "
          "guncel HEAD ayni agac (attestation disinda).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
