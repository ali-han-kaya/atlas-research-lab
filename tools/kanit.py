#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kanit.py — bu agacin kendi commit/agac kanitini uretir.

NEDEN VAR: OLG-1'in canli kaniti ozel agacin tarihcesine bagli; public agacta
CALISTIRILMADI. Bu betik ozel agaci OKUMAZ; yalniz bu depodaki GERCEK HEAD
commit'ini ve izlenen dosyalarin sha256'sini yazar. Attestation kendi dosyasini
kapsamaz; boylece commit/hash dongusu olusmaz.

Kullanim:
  python3 tools/kanit.py                 # attestation.json yaz
  python3 tools/kanit.py --cikti <yol>   # baska dosyaya yaz

CIKIS: 0 = yazildi · 1 = kirli agac/git hatasi · 2 = kullanim hatasi
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
SEMA = "ATLAS-KANIT/v1"
ATTESTATION = "attestation.json"


def git(*args, text=False):
    return subprocess.run(["git", "-C", str(KOK), *args],
                          capture_output=True, text=text)


def git_metin(*args):
    r = git(*args, text=True)
    if r.returncode != 0:
        raise RuntimeError("git %s: %s" % (
            " ".join(args), (r.stderr or "").strip()[:200]))
    return r.stdout


def kirli_dosyalar():
    """Izlenen dosyalarda commit edilmemis degisiklik var mi.

    attestation.json'in kendisi disarida tutulur: uretimden once eski surum
    izleniyor olabilir; onu yeniden yazmak bu betigin isidir.
    """
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


def agac_dosyalari(rev):
    """Git agacindaki blob'lari path/mode/size/sha256 olarak dondurur."""
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
    """Dosya listesinin deterministik sha256 ozeti."""
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


def arac_surumu(komut):
    try:
        r = subprocess.run(komut, capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            satirlar = (r.stdout or r.stderr).splitlines()
            return satirlar[0] if satirlar else "YOK"
    except (OSError, subprocess.SubprocessError):
        pass
    return "YOK"


def main():
    ap = argparse.ArgumentParser(description="ATLAS agac kaniti uret")
    ap.add_argument("--cikti", default=str(KOK / ATTESTATION),
                    help="yazilacak JSON yolu (varsayilan: attestation.json)")
    a = ap.parse_args()

    try:
        kirli = kirli_dosyalar()
        if kirli:
            print("FAIL KANIT-01 KIRLI_AGAC — once commit veya geri al:")
            for satir in kirli[:10]:
                print("  " + satir)
            return 1
        commit = git_metin("rev-parse", "HEAD").strip()
        tree = git_metin("rev-parse", "HEAD^{tree}").strip()
        dosyalar = agac_dosyalari("HEAD")
        veri = {
            "schema": SEMA,
            "generated_at": datetime.now(timezone.utc).isoformat(
                timespec="seconds").replace("+00:00", "Z"),
            "commit": commit,
            "tree": tree,
            "file_count": len(dosyalar),
            "files": dosyalar,
            "tree_sha256": agac_ozeti(dosyalar),
            "tool_versions": {
                "python": platform.python_version(),
                "git": arac_surumu(["git", "--version"]),
                "make": arac_surumu(["make", "--version"]),
                "platform": platform.platform(),
            },
            "scope": {
                "source": "git ls-tree -r --full-tree HEAD",
                "excludes": [ATTESTATION],
                "note": "Butun izlenen dosyalar; attestation.json kendini kapsamaz.",
            },
        }
        yol = Path(a.cikti)
        yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2,
                                  sort_keys=True) + "\n", encoding="utf-8")
        print("KANIT: YAZILDI %s" % yol)
        print("  commit=%s tree=%s dosya=%d tree_sha256=%s"
              % (commit, tree, len(dosyalar), veri["tree_sha256"]))
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as e:
        print("FAIL KANIT-01 URETILEMEDI — %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
