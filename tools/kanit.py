#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kanit.py — bu agacin commit/agac kaniti ve tasinabilir dogrulama paketi.

NEDEN VAR: OLG-1'in kaniti bu kamu agacinin kendi HEAD commit'i ve izlenen
dosyalarin sha256'sidir. Bu betik yalniz bu depodaki GERCEK HEAD commit'ini ve
izlenen dosyalarin sha256'sini yazar; dis bir agaci OKUMAZ. Attestation kendi
dosyasini kapsamaz; boylece commit/hash dongusu olusmaz.

`make kanit` ayrica makine-okur bir dogrulama paketi uretir:
  kanit-paketi/sonuc.json       ATLAS-DOGRULAMA/v1
  kanit-paketi/attestation.json  agac kanitinin kopyasi
  kanit-paketi/manifest.sha256  paket dosyalarinin SHA-256 manifesti
  kanit-paketi/makbuz.json      ATLAS-MAKBUZ/v1: komut/rc/ham satir baglantisi
  kanit-paketi/komutlar/        komut stdout/stderr kayitlari

Paket, attestation yazildiktan SONRA dogrulama komutlarini kosar. Boylece T1
yeni agac kanitini kullanir; yalniz attestation.json degistigi icin
`kanit_dogrula`nin agac temizligi kurali bunu dislar. Paket git'e eklenmez
(`.gitignore`); tasimak icin dizini kopyalamak yeterlidir.

Var olan bir `--paket` hedefi yalniz sonuc/makbuz/attestation semalari ve
manifest hash'leri bu araç tarafindan uretilmis paketle tutarliysa temizlenir.
Yabanci, bos, dosya, sembolik baglanti, depo koku/ustu ve `.git` altindaki
yollar reddedilir; hicbiri silinmez.

Kullanim:
  python3 tools/kanit.py                    # attestation + kanit-paketi
  python3 tools/kanit.py --cikti <yol>      # attestation'i baska yola yaz
  python3 tools/kanit.py --paket <dizin>    # paket konumunu degistir; mevcut
                                             # yabanci dizinleri silmez
  python3 tools/kanit.py --komut "make kapsam"  # varsayilan komutlari degistir
  python3 tools/kanit.py --paketsiz         # yalniz attestation (eski davranis)

CIKIS: 0 = attestation ve paket yazildi, butun komutlar PASS
       1 = kirli agac/git hatasi veya dogrulama komutu FAIL
       2 = kullanim/paket yazma hatasi
"""
import argparse
import hashlib
import json
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
SEMA = "ATLAS-KANIT/v1"
SEMA_SONUC = "ATLAS-DOGRULAMA/v1"
ATTESTATION = "attestation.json"
SONUC = "sonuc.json"
MANIFEST = "manifest.sha256"
MAKBUZ = "makbuz.json"
SEMA_MAKBUZ = "ATLAS-MAKBUZ/v1"
LOG_DIZINI = "komutlar"
VARSAYILAN_PAKET = "kanit-paketi"
VARSAYILAN_KOMUTLAR = [
    ("dogrula", ["make", "dogrula"]),
    ("kapsam", ["make", "kapsam"]),
    ("iddia", ["make", "iddia"]),
]
BULGU_SATIRI = re.compile(
    r"^\s*(?:FAIL|KALDI|BULGU|HATA)\s+([A-Za-z0-9_.-]+)")
SIDDET = re.compile(r"\bP([0-2])\b")


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


def sha256_metin(metin):
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


# Makbuzda komutun "ham cikti satiri" olarak hukum/ozet satiri saklanir;
# yoksa son anlamli satir kullanilir. Boylece satir keyfi degil, komutun
# gercek ciktisindan secilir.
VERDICT_SATIRI = re.compile(
    r"\b(?:HUKUM|KAPSAM|SONUC|PASS|FAIL|ERROR|ZAMAN ASIMI)\b")
ONCELIK_SATIRI = re.compile(r"\b(?:HUKUM|KAPSAM|SONUC)\b")


def ham_satir(out, err):
    """Komutun son hukum/ozet satirini, yoksa son dolu satirini dondur.

    Once HUKUM/KAPSAM/SONUC tasiyan satir aranir; boylece "PASS degil" gibi
    bir uyari satiri, gercek hukum satirinin onune gecmez.
    """
    for metin in (out, err):
        satirlar = [s.rstrip() for s in (metin or "").splitlines() if s.strip()]
        for kalip in (ONCELIK_SATIRI, VERDICT_SATIRI):
            for satir in reversed(satirlar):
                if kalip.search(satir):
                    return satir
        if satirlar:
            return satirlar[-1]
    return ""


def bulgu_kimlikleri(metin):
    """Yalniz satir basindaki FAIL/KALDI/BULGU/HATA kimliklerini toplar.

    "0 bulgu" gibi basari satirlarini veya serbest metindeki "FAIL"
    kelimesini bulgu saymamak icin satir basi ve ayri kimlik aranir.
    """
    kimlikler = set()
    for satir in (metin or "").splitlines():
        m = BULGU_SATIRI.match(satir)
        if m:
            kimlikler.add(m.group(1))
    return sorted(kimlikler)


def siddet_bul(metin, kimlik=None):
    for satir in (metin or "").splitlines():
        if kimlik and kimlik not in satir:
            continue
        m = SIDDET.search(satir)
        if m:
            return "P%s" % m.group(1)
    return "UNKNOWN"


def komut_id(argv, sira):
    if len(argv) >= 2 and argv[0] == "make":
        temiz = re.sub(r"[^A-Za-z0-9_.-]+", "-", argv[1]).strip("-")
        if temiz:
            return temiz
    return "komut-%02d" % sira


def komut_calistir(argv):
    baslangic = time.monotonic()
    try:
        r = subprocess.run(argv, cwd=str(KOK), capture_output=True, text=True,
                           timeout=1800)
        rc = r.returncode
        out = r.stdout or ""
        err = r.stderr or ""
        hata = None
    except subprocess.TimeoutExpired:
        rc, out, err, hata = 124, "", "ZAMAN ASIMI (1800 s)", "ZAMAN ASIMI"
    except OSError as e:
        rc, out, err, hata = 125, "", "KOSULAMADI: %s" % e, "KOSULAMADI"
    sure = int(round((time.monotonic() - baslangic) * 1000))
    return rc, out, err, sure, hata


def attestation_verisi(commit, tree, dosyalar):
    return {
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


def paket_hedef_dogrula(paket):
    """Paket hedefini coz ve yalniz kendi urettigimiz paketi kabul et.

    Var olan bir dizin ancak sonuc/makbuz/attestation semalari ve manifest
    hash'leri tutarliysa onceki paket sayilir. Bos, yabanci, dosya, sembolik
    baglanti, depo koku/ustu ve .git altindaki yollar reddedilir; hicbiri
    silinmez. Donen yol cozulmus (resolved) yoldur.
    """
    ham = Path(paket)
    if ham.is_symlink():
        raise ValueError("PAKET REDDEDILDI — sembolik baglanti: %s" % ham)
    coz = ham.resolve()
    kok = KOK.resolve()
    if coz == kok or coz in kok.parents:
        raise ValueError("PAKET REDDEDILDI — depo koku veya ustu: %s" % coz)
    if coz.parent == Path("/"):
        raise ValueError("PAKET REDDEDILDI — kok altindaki ust dizin: %s" % coz)
    if coz == Path.home().resolve():
        raise ValueError("PAKET REDDEDILDI — ev dizini: %s" % coz)
    if any(par.name == ".git" for par in (coz, *coz.parents)):
        raise ValueError("PAKET REDDEDILDI — .git icinde: %s" % coz)
    if not coz.exists():
        return coz
    if not coz.is_dir():
        raise ValueError(
            "PAKET REDDEDILDI — mevcut hedef dizin degil; silinmedi: %s" % coz)
    _paket_sahipligi_dogrula(coz)
    return coz


def _paket_sahipligi_dogrula(paket):
    """Var olan dizinin bu araç tarafından uretilmis paket oldugunu kanitla."""
    zorunlu = (SONUC, ATTESTATION, MANIFEST, MAKBUZ, LOG_DIZINI)
    eksik = [ad for ad in zorunlu if not (paket / ad).exists()]
    if eksik:
        raise ValueError(
            "PAKET REDDEDILDI — mevcut dizin ATLAS kanit paketi degil "
            "(eksik: %s); silinmedi" % ", ".join(eksik))
    if not (paket / LOG_DIZINI).is_dir():
        raise ValueError(
            "PAKET REDDEDILDI — komutlar dizini degil; silinmedi: %s" % paket)

    def _json(ad):
        try:
            return json.loads((paket / ad).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "PAKET REDDEDILDI — %s okunamadi (%s); silinmedi"
                % (ad, type(exc).__name__))

    sonuc = _json(SONUC)
    makbuz = _json(MAKBUZ)
    attestation = _json(ATTESTATION)
    if not isinstance(sonuc, dict) or sonuc.get("schema") != SEMA_SONUC:
        raise ValueError(
            "PAKET REDDEDILDI — sonuc.json semasi ATLAS-DOGRULAMA/v1 degil; "
            "silinmedi")
    if not isinstance(makbuz, dict) or makbuz.get("schema") != SEMA_MAKBUZ:
        raise ValueError(
            "PAKET REDDEDILDI — makbuz.json semasi ATLAS-MAKBUZ/v1 degil; "
            "silinmedi")
    if not isinstance(attestation, dict) or attestation.get("schema") != SEMA:
        raise ValueError(
            "PAKET REDDEDILDI — attestation.json semasi ATLAS-KANIT/v1 degil; "
            "silinmedi")
    paket_bilgi = sonuc.get("package")
    if not isinstance(paket_bilgi, dict) \
            or paket_bilgi.get("format") != "directory" \
            or paket_bilgi.get("manifest_file") != MANIFEST \
            or paket_bilgi.get("attestation_file") != ATTESTATION \
            or paket_bilgi.get("log_directory") != LOG_DIZINI:
        raise ValueError(
            "PAKET REDDEDILDI — sonuc.json paket imzasi eksik/bozuk; "
            "silinmedi")

    manifest_yolu = paket / MANIFEST
    try:
        manifest_metni = manifest_yolu.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(
            "PAKET REDDEDILDI — manifest okunamadi (%s); silinmedi"
            % type(exc).__name__)
    kayitli = {}
    for satir in manifest_metni.splitlines():
        if not satir.strip():
            continue
        parca = satir.split("  ", 1)
        if len(parca) != 2:
            raise ValueError(
                "PAKET REDDEDILDI — manifest satiri bozuk; silinmedi: %r"
                % satir[:120])
        sha, rel = parca
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError(
                "PAKET REDDEDILDI — manifest sha256 bicimi bozuk; silinmedi")
        rel_yolu = Path(rel)
        if not rel or rel_yolu.is_absolute() or ".." in rel_yolu.parts \
                or rel in kayitli:
            raise ValueError(
                "PAKET REDDEDILDI — manifest yolu guvenli/benzersiz degil; "
                "silinmedi: %s" % rel)
        kayitli[rel] = sha

    gercek = set()
    for yol in paket.rglob("*"):
        if yol.is_symlink():
            raise ValueError(
                "PAKET REDDEDILDI — paket icinde sembolik baglanti; silinmedi: %s"
                % yol.relative_to(paket).as_posix())
        if not yol.is_file() or yol == manifest_yolu:
            continue
        rel = yol.relative_to(paket).as_posix()
        if rel not in kayitli:
            raise ValueError(
                "PAKET REDDEDILDI — manifest disi dosya; silinmedi: %s" % rel)
        try:
            gercek_sha = hashlib.sha256(yol.read_bytes()).hexdigest()
        except OSError as exc:
            raise ValueError(
                "PAKET REDDEDILDI — paket dosyasi okunamadi (%s); silinmedi: %s"
                % (type(exc).__name__, rel))
        if gercek_sha != kayitli[rel]:
            raise ValueError(
                "PAKET REDDEDILDI — manifest hash'i tutmuyor; silinmedi: %s" % rel)
        gercek.add(rel)
    eksik_dosya = sorted(set(kayitli) - gercek)
    if eksik_dosya:
        raise ValueError(
            "PAKET REDDEDILDI — manifestte olup dizinde olmayan dosya; "
            "silinmedi: %s" % ", ".join(eksik_dosya))


def paket_yaz(paket, attestation_metni, attestation_verisi_, komutlar):
    """Paketi yaz; (sonuc, manifest_yolu) dondur."""
    paket = paket_hedef_dogrula(paket)
    if paket.exists():
        shutil.rmtree(paket)
    (paket / LOG_DIZINI).mkdir(parents=True)

    (paket / ATTESTATION).write_text(attestation_metni, encoding="utf-8")
    at_sha = sha256_metin(attestation_metni)

    kayitlar = []
    for sira, (kimlik, argv, rc, out, err, sure, hata) in enumerate(komutlar, 1):
        ad = "%s/%02d-%s" % (LOG_DIZINI, sira, kimlik)
        (paket / (ad + ".stdout.txt")).write_text(out, encoding="utf-8")
        (paket / (ad + ".stderr.txt")).write_text(err, encoding="utf-8")
        birlesik = out + "\n" + err
        kimlikler = bulgu_kimlikleri(birlesik)
        durum = "ERROR" if hata else ("PASS" if rc == 0 else "FAIL")
        kayitlar.append({
            "id": kimlik,
            "argv": argv,
            "exit_code": rc,
            "status": durum,
            "duration_ms": sure,
            "stdout_sha256": sha256_metin(out),
            "stderr_sha256": sha256_metin(err),
            "stdout_bytes": len(out.encode("utf-8")),
            "stderr_bytes": len(err.encode("utf-8")),
            "finding_ids": kimlikler,
        })

    birlesik_metin = "\n".join(
        (out + "\n" + err) for _k, _a, _rc, out, err, _s, _h in komutlar)
    kimlikler = bulgu_kimlikleri(birlesik_metin)
    bulgular = [{
        "id": k,
        "commands": [r["id"] for r in kayitlar if k in r["finding_ids"]],
        "severity": siddet_bul(birlesik_metin, k),
    } for k in kimlikler]

    sifir_olmayan = [r["exit_code"] for r in kayitlar if r["exit_code"] != 0]
    sonuc = {
        "schema": SEMA_SONUC,
        "generated_at": datetime.now(timezone.utc).isoformat(
            timespec="seconds").replace("+00:00", "Z"),
        "commit": attestation_verisi_["commit"],
        "tree": attestation_verisi_["tree"],
        "exit_code": sifir_olmayan[0] if sifir_olmayan else 0,
        "verdict": "PASS" if all(r["status"] == "PASS" for r in kayitlar)
                   else "FAIL",
        "command_count": len(kayitlar),
        "attestation_sha256": at_sha,
        "commands": kayitlar,
        "findings": bulgular,
        "manifest": {
            "algorithm": "sha256",
            "root_sha256": attestation_verisi_["tree_sha256"],
            "files": attestation_verisi_["files"],
        },
        "package": {
            "format": "directory",
            "manifest_file": MANIFEST,
            "attestation_file": ATTESTATION,
            "log_directory": "komutlar",
        },
    }
    sonuc_metni = json.dumps(sonuc, ensure_ascii=False, indent=2,
                             sort_keys=True) + "\n"
    (paket / SONUC).write_text(sonuc_metni, encoding="utf-8")

    makbuz_kalemleri = []
    for sira, ((kimlik, argv, rc, out, err, _sure, _hata), kayit) in enumerate(
            zip(komutlar, kayitlar), 1):
        satir = ham_satir(out, err)
        if not satir:
            raise ValueError("komut %s bos cikti verdi; makbuz satiri yok"
                             % kimlik)
        makbuz_kalemleri.append({
            "id": kimlik,
            "argv": argv,
            "exit_code": rc,
            "status": kayit["status"],
            "raw_line": satir,
            "raw_line_sha256": sha256_metin(satir),
            "stdout": "%s/%02d-%s.stdout.txt" % (LOG_DIZINI, sira, kimlik),
            "stderr": "%s/%02d-%s.stderr.txt" % (LOG_DIZINI, sira, kimlik),
            "stdout_sha256": kayit["stdout_sha256"],
            "stderr_sha256": kayit["stderr_sha256"],
        })
    makbuz = {
        "schema": SEMA_MAKBUZ,
        "generated_at": sonuc["generated_at"],
        "commit": sonuc["commit"],
        "tree": sonuc["tree"],
        "tree_sha256": sonuc["manifest"]["root_sha256"],
        "attestation_sha256": sonuc["attestation_sha256"],
        "command_count": len(makbuz_kalemleri),
        "items": makbuz_kalemleri,
    }
    (paket / MAKBUZ).write_text(
        json.dumps(makbuz, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")

    satirlar = []
    for yol in sorted(paket.rglob("*")):
        if not yol.is_file() or yol.name == MANIFEST:
            continue
        rel = yol.relative_to(paket).as_posix()
        satirlar.append("%s  %s" % (
            hashlib.sha256(yol.read_bytes()).hexdigest(), rel))
    manifest_yolu = paket / MANIFEST
    manifest_yolu.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return sonuc, manifest_yolu


def main():
    ap = argparse.ArgumentParser(description="ATLAS agac kaniti ve paketi uret")
    ap.add_argument("--cikti", default=str(KOK / ATTESTATION),
                    help="yazilacak attestation JSON yolu")
    ap.add_argument("--paket", default=str(KOK / VARSAYILAN_PAKET),
                    help="tasinabilir kanit paketi dizini; yalniz kendi "
                         "urettigimiz paket temizlenir")
    ap.add_argument("--komut", action="append", default=None,
                    help="varsayilan dogrulama komutunun yerine komut ekle")
    ap.add_argument("--paketsiz", action="store_true",
                    help="yalniz attestation yaz; paket ve komutlari atla")
    a = ap.parse_args()

    try:
        paket = Path(a.paket)
        if not paket.is_absolute():
            paket = KOK / paket
        if not a.paketsiz:
            # Yanlis --paket hedefini komutlardan/attestation yazimindan ONCE
            # reddet; mevcut yabanci bir dizin hicbir zaman silinmez.
            paket = paket_hedef_dogrula(paket)
        kirli = kirli_dosyalar()
        if kirli:
            print("FAIL KANIT-01 KIRLI_AGAC — once commit veya geri al:")
            for satir in kirli[:10]:
                print("  " + satir)
            return 1
        commit = git_metin("rev-parse", "HEAD").strip()
        tree = git_metin("rev-parse", "HEAD^{tree}").strip()
        dosyalar = agac_dosyalari("HEAD")
        veri = attestation_verisi(commit, tree, dosyalar)
        at_metni = json.dumps(veri, ensure_ascii=False, indent=2,
                              sort_keys=True) + "\n"
        yol = Path(a.cikti)
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text(at_metni, encoding="utf-8")
        print("KANIT: YAZILDI %s" % yol)
        print("  commit=%s tree=%s dosya=%d tree_sha256=%s"
              % (commit, tree, len(dosyalar), veri["tree_sha256"]))

        if a.paketsiz:
            return 0

        if a.komut:
            komutlar = []
            for sira, metin in enumerate(a.komut, 1):
                argv = shlex.split(metin)
                if not argv:
                    raise ValueError("bos --komut")
                komutlar.append((komut_id(argv, sira), argv))
        else:
            komutlar = list(VARSAYILAN_KOMUTLAR)

        sonuclar = []
        for kimlik, argv in komutlar:
            print("KANIT: KOMUT %s — %s" % (kimlik, " ".join(argv)))
            rc, out, err, sure, hata = komut_calistir(argv)
            sonuclar.append((kimlik, argv, rc, out, err, sure, hata))
            print("  rc=%d · %d ms · %s" % (
                rc, sure, "PASS" if hata is None and rc == 0
                else ("ERROR" if hata else "FAIL")))

        sonuc, manifest = paket_yaz(paket, at_metni, veri, sonuclar)
        print("KANIT: PAKET %s" % paket)
        print("  hüküm=%s · komut=%d · bulgu=%d · manifest=%s"
              % (sonuc["verdict"], sonuc["command_count"],
                 len(sonuc["findings"]), manifest))
        print("  makbuz=%s · kalem=%d"
              % (paket / MAKBUZ, sonuc["command_count"]))
        return 0 if sonuc["verdict"] == "PASS" else 1
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as e:
        print("FAIL KANIT-01 URETILEMEDI — %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
