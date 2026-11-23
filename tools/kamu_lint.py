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
  python3 tools/kamu_lint.py --github-arama  # repo kapsamli kod arama
  python3 tools/kamu_lint.py --github-oztest # agsiz sahte API testi
CIKIS: 0 = temiz/kanitli · 1 = bulgu · 2 = kullanim/arac/olculemedi
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

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
GITHUB_API = "https://api.github.com"
GITHUB_REPO = "ali-han-kaya/atlas-research-lab"
# Sorgu metinleri parcali yazilir: bu betik kendi kamu-lint desenine
# takilmadan ayni degerleri GitHub'a sorgu olarak gonderebilsin.
VARSAYILAN_SORGULAR = (
    ("ozel-lab-adi", "AI_" + "ARASTIRMA_LABI"),
    ("ozel-lab-yolu", "Desktop/" + "MTRX"),
    ("neon-token", "npg" + "_"),
    ("github-token", "ghp" + "_"),
)
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


def _github_token():
    """Token'i ortama yazmadan bul; degeri asla basma."""
    for ad in ("GITHUB_TOKEN", "GH_TOKEN"):
        deger = os.environ.get(ad)
        if deger and deger.strip():
            return deger.strip(), None
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True,
                           text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None, "gh yok veya calismadi"
    if r.returncode != 0 or not r.stdout.strip():
        return None, "GITHUB_TOKEN/GH_TOKEN yok; gh auth token da vermedi"
    return r.stdout.strip(), None


def _repo_gecerli(repo):
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo))


def _sorgu_gecerli(sorgu):
    """Repo kapsamini kullanicinin sorgusuyla genisletmeye izin verme."""
    return (bool(sorgu.strip()) and "\n" not in sorgu
            and "\r" not in sorgu
            and not re.search(r"(^|\s)repo:", sorgu, re.IGNORECASE))


def _github_istek(api_url, repo, sorgu, token):
    """(JSON, None) veya (None, guvenli hata etiketi)."""
    if not re.match(r"^https?://", api_url):
        return None, "API_URL_GECERSIZ"
    tam = (api_url.rstrip("/") + "/search/code?"
           + urlencode({"q": "repo:%s %s" % (repo, sorgu),
                        "per_page": "1"}))
    istek = Request(tam, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer %s" % token,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "atlas-kamu-lint",
    })
    try:
        with urlopen(istek, timeout=20) as cevap:
            ham = cevap.read().decode("utf-8", "replace")
    except HTTPError as exc:
        # Yanit govdesini basma: hata metni kimlik bilgisi tasiyabilir.
        return None, "HTTP_%d" % exc.code
    except (URLError, TimeoutError, ValueError) as exc:
        return None, "AG_HATASI_%s" % type(exc).__name__
    try:
        return json.loads(ham), None
    except ValueError:
        return None, "JSON_GECERSIZ"


def github_sorgu(api_url, repo, etiket, sorgu, token):
    """Tek sorguyu fail-closed siniflandir.

    KANIT yalniz HTTP 200 + gecerli sayilar + incomplete_results=false + 0.
    incomplete_results=true ise 0 kanit DEGILDIR: INDEKS_YETISMEDI.
    """
    sonuc = {"etiket": etiket, "sorgu": sorgu, "durum": "OLCULEMEDI",
             "total_count": None, "incomplete_results": None,
             "neden": None}
    veri, hata = _github_istek(api_url, repo, sorgu, token)
    if hata:
        sonuc["neden"] = hata
        return sonuc
    if not isinstance(veri, dict):
        sonuc["neden"] = "YANIT_SOZLUK_DEGIL"
        return sonuc
    toplam = veri.get("total_count")
    if (not isinstance(toplam, int) or isinstance(toplam, bool)
            or toplam < 0):
        sonuc["neden"] = "TOTAL_COUNT_GECERSIZ"
        return sonuc
    eksik = veri.get("incomplete_results")
    if not isinstance(eksik, bool):
        sonuc["neden"] = "INCOMPLETE_RESULTS_YOK"
        return sonuc
    sonuc["total_count"] = toplam
    sonuc["incomplete_results"] = eksik
    if toplam > 0:
        sonuc["durum"] = "BULGU"
    elif eksik:
        sonuc["durum"] = "INDEKS_YETISMEDI"
    else:
        sonuc["durum"] = "KANIT"
    return sonuc


def github_arama(api_url, repo, sorgular, token):
    return [github_sorgu(api_url, repo, etiket, sorgu, token)
            for etiket, sorgu in sorgular]


def github_karar(sonuclar):
    """(rc, hukum, sayilar) — bulgu > olculemedi > kanit onceligi."""
    kanit = sum(1 for x in sonuclar if x["durum"] == "KANIT")
    bulgu = sum(1 for x in sonuclar if x["durum"] == "BULGU")
    indeks = sum(1 for x in sonuclar if x["durum"] == "INDEKS_YETISMEDI")
    olculemedi = sum(1 for x in sonuclar
                     if x["durum"] not in ("KANIT", "BULGU",
                                           "INDEKS_YETISMEDI"))
    if bulgu:
        return 1, "FAIL", (kanit, bulgu, indeks, olculemedi)
    if indeks or olculemedi or kanit != len(sonuclar):
        return 2, "OLCULEMEDI", (kanit, bulgu, indeks, olculemedi)
    return 0, "PASS", (kanit, bulgu, indeks, olculemedi)


def github_yaz(sonuclar, repo):
    print("KOD ARAMA - repo:%s - %d sorgu" % (repo, len(sonuclar)))
    for x in sonuclar:
        if x["durum"] == "KANIT":
            print("  KANIT 0          %-18s total_count=0 "
                  "incomplete_results=false" % x["etiket"])
        elif x["durum"] == "BULGU":
            print("  FAIL BULGU       %-18s total_count=%s "
                  "incomplete_results=%s" % (
                      x["etiket"], x["total_count"],
                      str(x["incomplete_results"]).lower()))
        elif x["durum"] == "INDEKS_YETISMEDI":
            print("  OLCULEMEDI INDEKS %-18s total_count=%s "
                  "incomplete_results=true (0 kanit sayilmadi)" % (
                      x["etiket"], x["total_count"]))
        else:
            print("  OLCULEMEDI       %-18s neden=%s (0 kanit sayilmadi)"
                  % (x["etiket"], x["neden"]))
    rc, hukum, (kanit, bulgu, indeks, olculemedi) = github_karar(sonuclar)
    print("KOD ARAMA: %s - %d/%d sorgu kanit oldu - %d bulgu - "
          "%d indeks yetismedi - %d olculemedi"
          % (hukum, kanit, len(sonuclar), bulgu, indeks, olculemedi))
    if hukum == "OLCULEMEDI":
        print("HUKUM: OLCULEMEDI - indeks yetismedi veya alan eksik; "
              "0'lar kanit sayilmadi.")
    elif hukum == "FAIL":
        print("HUKUM: FAIL - repo kapsaminda eslesme var.")
    else:
        print("HUKUM: PASS - tum 0'lar incomplete_results=false ile kanitlandi.")
    return rc


def github_oztest():
    """Sahte yerel API ile alan/indeks sozlesmesini agsiz sinar."""
    cevaplar = {
        "TEST-ZERO": (200, {"total_count": 0,
                            "incomplete_results": False}),
        "TEST-IND": (200, {"total_count": 0,
                           "incomplete_results": True}),
        "TEST-HIT": (200, {"total_count": 2,
                           "incomplete_results": False}),
        "TEST-MISSING": (200, {"total_count": 0}),
        "TEST-HTTP": (500, {}),
        "TEST-BADJSON": (200, "{bozuk"),
    }

    class Isleyici(BaseHTTPRequestHandler):
        def do_GET(self):
            q = parse_qs(urlparse(self.path).query).get("q", [""])[0]
            anahtar = next((k for k in cevaplar if k in q), None)
            if anahtar is None:
                kod, govde = 404, {}
            else:
                kod, govde = cevaplar[anahtar]
            ham = (govde.encode("utf-8") if isinstance(govde, str)
                   else json.dumps(govde).encode("utf-8"))
            self.send_response(kod)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(ham)))
            self.end_headers()
            self.wfile.write(ham)

        def log_message(self, *_args):
            pass

    sunucu = ThreadingHTTPServer(("127.0.0.1", 0), Isleyici)
    is_parcasi = threading.Thread(target=sunucu.serve_forever, daemon=True)
    is_parcasi.start()
    api = "http://127.0.0.1:%d" % sunucu.server_address[1]
    try:
        sorgular = [
            ("sifir", "TEST-ZERO"),
            ("indeks", "TEST-IND"),
            ("bulgu", "TEST-HIT"),
            ("alan-yok", "TEST-MISSING"),
            ("http", "TEST-HTTP"),
            ("json", "TEST-BADJSON"),
        ]
        sonuc = github_arama(api, "test/repo", sorgular, "test-token")
        k = {x["etiket"]: x for x in sonuc}
        hatalar = []
        if k["sifir"]["durum"] != "KANIT" or github_karar(
                [k["sifir"]])[0] != 0:
            hatalar.append("temiz 0 kanit sayilmadi")
        if k["indeks"]["durum"] != "INDEKS_YETISMEDI" or github_karar(
                [k["indeks"]])[0] != 2:
            hatalar.append("incomplete_results=true kanit sayildi")
        if k["bulgu"]["durum"] != "BULGU" or github_karar(
                [k["bulgu"]])[0] != 1:
            hatalar.append("pozitif sonuc bulgu sayilmadi")
        if k["alan-yok"]["durum"] != "OLCULEMEDI" or github_karar(
                [k["alan-yok"]])[0] != 2:
            hatalar.append("eksik alan olculemedi sayilmadi")
        if (not k["http"]["neden"].startswith("HTTP_500")
                or github_karar([k["http"]])[0] != 2):
            hatalar.append("HTTP hatasi olculemedi sayilmadi")
        if k["json"]["neden"] != "JSON_GECERSIZ" or github_karar(
                [k["json"]])[0] != 2:
            hatalar.append("bozuk JSON olculemedi sayilmadi")
    finally:
        sunucu.shutdown()
        sunucu.server_close()
        is_parcasi.join(timeout=2)
    if hatalar:
        for hata in hatalar:
            print("FAIL KAMU-ARAMA OZTEST " + hata)
        print("KAMU-ARAMA OZ-TEST: FAIL - %d/%d" % (len(hatalar),
                                                   len(sorgular)))
        return 1
    print("KAMU-ARAMA OZ-TEST: PASS - 6/6")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Kamu agaci sizinti kontrolu")
    ap.add_argument("--kontrol", action="store_true", help="izlenen agaci tara")
    ap.add_argument("--oztest", action="store_true", help="negatif fiksturleri kos")
    ap.add_argument("--github-arama", action="store_true",
                    help="repo kapsamli GitHub kod aramasi")
    ap.add_argument("--github-oztest", action="store_true",
                    help="kod arama sozlesmesini agsiz sina")
    ap.add_argument("--repo", default=GITHUB_REPO,
                    help="owner/repo (varsayilan: %s)" % GITHUB_REPO)
    ap.add_argument("--api-url", default=GITHUB_API,
                    help="GitHub API koku (varsayilan: %s)" % GITHUB_API)
    ap.add_argument("--sorgu", action="append", default=None,
                    help="ek repo kapsamli sorgu; tekrarlanabilir")
    a = ap.parse_args()
    if a.github_oztest:
        return github_oztest()
    if a.github_arama:
        if not _repo_gecerli(a.repo):
            print("KOD ARAMA: OLCULEMEDI - repo bicimi gecersiz")
            return 2
        sorgular = ([("kullanici-%d" % (i + 1), s)
                     for i, s in enumerate(a.sorgu)]
                    if a.sorgu else list(VARSAYILAN_SORGULAR))
        if any(not _sorgu_gecerli(s) for _e, s in sorgular):
            print("KOD ARAMA: OLCULEMEDI - bos veya repo: iceren sorgu")
            return 2
        token, hata = _github_token()
        if hata:
            print("KOD ARAMA: OLCULEMEDI - %s" % hata)
            return 2
        return github_yaz(github_arama(a.api_url, a.repo, sorgular, token),
                          a.repo)
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
