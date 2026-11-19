#!/usr/bin/env python3
"""OLGULAR.md ile etkin lab kaynaklarini fail-closed karsilastirir.

OLGU-05, verilen ATLAS/attest/KOD ciktilarindaki sayilari kanonik kayitla
karsilastirir. OLGU-KANIT/v1 metadatasi HEAD, run_id, zaman damgasi ve timeout
bagini gorunur kilar; eksik, bayat veya uyusmayan bag WARN'dir ve sayisal
OLGU-05 sonucunu FAIL'e cevirmez. Metadata imzali koken kaniti degildir.

OLGU-06, son kanonik DEVIR'den sonraki mekanizma commit hash'lerinin bicimsel
olarak DERSLER satirlarinda bulunup Git commitlerine cozuldugunu denetler.
Dersin anlamsal dogrulugunu, olcumun gercekten kosuldugunu veya sonucun ilgili
committe uretildigini denetlemez.
"""

import datetime
import json
import pathlib
import re
import subprocess
import sys


SCRIPTS = pathlib.Path(__file__).resolve().parent
VARSAYILAN_KOK = SCRIPTS.parent.parent
JSON_BLOK = re.compile(
    r"<!-- OLGULAR_JSON_BASLA -->\s*```json\s*(\{.*?\})\s*```\s*"
    r"<!-- OLGULAR_JSON_BITIR -->",
    re.DOTALL,
)
COMMIT = re.compile(r"^[0-9a-f]{7,40}$")
ATLAS_OZET = re.compile(r"^OZ-TEST:\s*(\d+)/(\d+)\s+gecti\s*$", re.MULTILINE)
KOD_OZET = re.compile(r"^KOD OZ-TEST:\s*(\d+)/(\d+)\s+gecti\s*$", re.MULTILINE)
KANIT_BASLIK = re.compile(
    r"^OLGU-KANIT/v1 HEAD=(?P<head>[0-9a-f]{40}) "
    r"run_id=(?P<run_id>[A-Za-z0-9._:-]{1,128}) "
    r"timestamp=(?P<timestamp>\S+) timeout=(?P<timeout>[1-9][0-9]{0,4})$"
)
KANIT_TIMEOUT_EN_COK = 86400
KANIT_SECENEKLERI = {
    "--atlas-cikti": "atlas",
    "--attest-cikti": "attest",
    "--kod-cikti": "kod",
}
SAYISAL_ALANLAR = (
    "atlas_envanter_sayisi",
    "atlas_son_gecen",
    "kod_son_gecen",
    "attest_canli",
    "attest_taban",
    "attest_p0",
    "attest_p1",
    "mekanizma_sayisi",
)


def fail(kod, aciklama, *, beklenen=None, bulunan=None):
    satir = f"FAIL {kod} {aciklama}"
    if beklenen is not None:
        satir += f" beklenen={beklenen}"
    if bulunan is not None:
        satir += f" bulunan={bulunan}"
    print(satir)


def warn(kod, aciklama, *, beklenen=None, bulunan=None):
    satir = f"WARN {kod} {aciklama}"
    if beklenen is not None:
        satir += f" beklenen={beklenen}"
    if bulunan is not None:
        satir += f" bulunan={bulunan}"
    print(satir)


def argumanlar(argv):
    kok = VARSAYILAN_KOK
    git_kok = None
    yalniz_dersler = False
    kanitlar = {"atlas": None, "attest": None, "kod": None}
    i = 0
    while i < len(argv):
        if argv[i] == "--dersler":
            yalniz_dersler = True
            i += 1
            continue
        if argv[i] not in {"--kok", "--git-kok", *KANIT_SECENEKLERI} or i + 1 >= len(argv):
            fail(
                "OLGU-02", "SEMA_GECERSIZ",
                beklenen="--dersler veya --kok/--git-kok/--atlas-cikti/--attest-cikti/--kod-cikti YOL",
                bulunan=" ".join(argv),
            )
            return None, None, None, False
        if argv[i] == "--kok":
            kok = pathlib.Path(argv[i + 1]).resolve()
        elif argv[i] == "--git-kok":
            git_kok = pathlib.Path(argv[i + 1]).resolve()
        else:
            kanitlar[KANIT_SECENEKLERI[argv[i]]] = pathlib.Path(argv[i + 1]).resolve()
        i += 2
    if yalniz_dersler and any(yol is not None for yol in kanitlar.values()):
        fail("OLGU-02", "--dersler canli kanit secenekleriyle birlestirilemez")
        return None, None, None, False
    return kok, git_kok or kok, kanitlar, yalniz_dersler


def oku_metin(yol):
    try:
        return yol.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen=f"okunabilir:{yol}", bulunan=type(exc).__name__)
        return None


def git_kos(git_kok, *args, kod="OLGU-04"):
    try:
        return subprocess.run(
            ["git", "-C", str(git_kok), *args],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        fail(kod, "COMMIT_DOGRULANAMADI", beklenen="git exit=0", bulunan=type(exc).__name__)
        return None


def mekanizma_yolu(yol):
    """ATLAS/KOD/ORTAK kod, test, prompt, sablon ve ayarlari; belge haric.

    Commit mesaji etiketine guvenilmez. Kok README/AGENTS/SURUM gibi metinler
    ve docs/ altindaki belgeler mekanizma degildir; .opencode/ ve templates/
    altindaki Markdown dosyalari ise calisan prompt/sozlesme olarak sayilir.
    """
    p = pathlib.PurePosixPath(yol)
    if len(p.parts) < 2 or p.parts[0] not in {"ATLAS_SABLONLAR", "KOD_SABLONLAR", "ORTAK"}:
        return False
    if p.parts[1] == "docs" or (len(p.parts) == 2 and p.suffix.lower() in {".md", ".txt", ".rst"}):
        return False
    return True


def olgu06_kontrol(kok, git_kok):
    """SURUM'un ilk DEVIR referansinin eklendigi commit'ten HEAD'e ders borcu.

    Baslangic dosya adina/tarihine gore siralanmaz. DEVIR'e sonradan yapilan
    bir belge duzeltmesi baslangici ileri tasiyip mekanizmalari gizleyemez.
    Yalniz tarihli, en az yedi dolu sutunlu DERSLER satirlarindaki Git'te
    cozumlenen hash'ler kayit sayilir. Dersin anlamsal dogrulugu olculmez.
    """
    def git_oku(*args):
        r = git_kos(git_kok, *args, kod="OLGU-06")
        if r is None or r.returncode != 0:
            raise ValueError("Git sorgusu dogrulanamadi: " + " ".join(args))
        return r.stdout.strip()

    try:
        if pathlib.Path(git_oku("rev-parse", "--show-toplevel")).resolve() != git_kok.resolve():
            raise ValueError("Git koku verilen dizinle ayni degil")
        if git_oku("rev-parse", "--is-shallow-repository") != "false":
            raise ValueError("Git gecmisi sig/eksik")
        surum = (kok / "SURUM.md").read_text(encoding="utf-8")
        kanonik_list = re.findall(
            r"^Kanonik OLGU-06 DEVIR:\s*`"
            r"(docs/DEVIR-\d{4}-\d{2}-\d{2}-\d{4}(?:-[A-Za-z0-9][A-Za-z0-9-]*)?\.md)"
            r"`\s*$",
            surum,
            re.MULTILINE,
        )
        if len(kanonik_list) != 1:
            raise ValueError(
                f"Kanonik OLGU-06 DEVIR: {len(kanonik_list)} eslesme (1 bekleniyor)"
            )
        devir = kanonik_list[0]
        devir_yolu = kok / devir
        devir_yolu.resolve().relative_to(kok.resolve())
        if not devir_yolu.is_file():
            raise ValueError("DEVIR dosyasi yok: " + devir)
        baslangic = git_oku("log", "-1", "--format=%H", "--diff-filter=A", "HEAD", "--", devir)
        if not re.fullmatch(r"[0-9a-f]{40}", baslangic):
            raise ValueError("DEVIR'in Git baslangici bulunamadi")

        dersler = (kok / "docs/DERSLER_v1_2026-08-30.md").read_text(encoding="utf-8")
        dersler = re.sub(r"<!--.*?-->", "", dersler, flags=re.DOTALL)
        hashler = set()
        fence = None
        for satir in dersler.splitlines():
            sinir = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", satir)
            if sinir:
                marker, son = sinir.groups()
                if fence is None:
                    fence = marker
                elif marker[0] == fence[0] and len(marker) >= len(fence) and not son.strip():
                    fence = None
                continue
            if fence or not re.match(r"^\|\s*\d{2}\.\d+(?:\.\d{4})?\s*\|", satir):
                continue
            sutunlar = [s.strip() for s in satir.strip().strip("|").split("|")]
            if len(sutunlar) < 7 or not all(sutunlar[:7]):
                continue
            hashler.update(h.lower() for h in re.findall(
                r"(?<![A-Za-z0-9_])[0-9a-fA-F]{7,40}(?![A-Za-z0-9_])", satir
            ))

        mekanizmalar = []
        for commit in git_oku("rev-list", "--reverse", f"{baslangic}..HEAD").splitlines():
            if not re.fullmatch(r"[0-9a-f]{40}", commit):
                raise ValueError("Git commit listesi bozuk")
            yollar = git_oku("diff-tree", "--no-commit-id", "--name-only", "-r", "-m", "--root", "-z", commit)
            if any(mekanizma_yolu(yol) for yol in yollar.split("\0") if yol):
                mekanizmalar.append(commit)
        eksik = []
        for commit in mekanizmalar:
            eslesen = [h for h in hashler if commit.startswith(h)]
            if not any(git_oku("rev-parse", "--verify", f"{h}^{{commit}}") == commit for h in eslesen):
                eksik.append(commit)
        for commit in eksik:
            fail("OLGU-06", f"DERS_KAYDI_EKSIK commit={commit}")
        if eksik:
            return 1
        print(f"PASS OLGU-06 devir={devir} baslangic={baslangic[:7]} mekanizma={len(mekanizmalar)}")
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        fail("OLGU-06", "DERS_KAYDI_DOGRULANAMADI", bulunan=str(exc))
        return 1


def kanit_oku(yol, kaynak):
    try:
        return yol.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(
            "OLGU-05", f"CANLI_OLCUM_DOGRULANAMADI kaynak={kaynak}",
            beklenen=f"okunabilir:{yol}", bulunan=type(exc).__name__,
        )
        return None


def ozet_ayristir(metin, desen, kaynak):
    eslesmeler = desen.findall(metin)
    if len(eslesmeler) != 1:
        fail(
            "OLGU-05", f"CANLI_OLCUM_DOGRULANAMADI kaynak={kaynak}",
            beklenen="tek ozet satiri", bulunan=len(eslesmeler),
        )
        return None
    gecen, toplam = (int(deger) for deger in eslesmeler[0])
    if gecen > toplam:
        fail(
            "OLGU-05", f"CANLI_OLCUM_DOGRULANAMADI kaynak={kaynak}",
            beklenen="gecen<=toplam", bulunan=f"{gecen}>{toplam}",
        )
        return None
    return gecen, toplam


def kanit_metadatasi(metin, kaynak, attest=None):
    """Metin basligini veya attest JSON kanit nesnesini kapali semayla ayristir."""
    if attest is None:
        ilk = metin.splitlines()[0] if metin.splitlines() else ""
        eslesme = KANIT_BASLIK.fullmatch(ilk)
        if eslesme is None:
            warn("OLGU-05", f"KANIT_KOKENI_DOGRULANAMADI kaynak={kaynak}",
                 beklenen="OLGU-KANIT/v1 basligi", bulunan="YOK_VEYA_GECERSIZ")
            return None
        meta = eslesme.groupdict()
        meta["timeout"] = int(meta["timeout"])
    else:
        meta = attest.get("kanit") if isinstance(attest, dict) else None
        alanlar = {"sema", "head", "run_id", "timestamp", "timeout"}
        if not isinstance(meta, dict) or set(meta) != alanlar or meta.get("sema") != "OLGU-KANIT/v1":
            warn("OLGU-05", f"KANIT_KOKENI_DOGRULANAMADI kaynak={kaynak}",
                 beklenen="kapali OLGU-KANIT/v1 nesnesi", bulunan="YOK_VEYA_GECERSIZ")
            return None
        meta = dict(meta)

    if not isinstance(meta.get("head"), str) or not re.fullmatch(r"[0-9a-f]{40}", meta["head"]):
        warn("OLGU-05", f"KANIT_KOKENI_DOGRULANAMADI kaynak={kaynak}",
             beklenen="head:40-kucuk-hex", bulunan=repr(meta.get("head")))
        return None
    if not isinstance(meta.get("run_id"), str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", meta["run_id"]):
        warn("OLGU-05", f"KANIT_KOKENI_DOGRULANAMADI kaynak={kaynak}",
             beklenen="run_id:kapali-token", bulunan=repr(meta.get("run_id")))
        return None
    timeout = meta.get("timeout")
    if type(timeout) is not int or not 1 <= timeout <= KANIT_TIMEOUT_EN_COK:
        warn("OLGU-05", f"KANIT_KOKENI_DOGRULANAMADI kaynak={kaynak}",
             beklenen=f"timeout:1..{KANIT_TIMEOUT_EN_COK}", bulunan=repr(timeout))
        return None
    try:
        zaman = datetime.datetime.fromisoformat(str(meta.get("timestamp", "")).replace("Z", "+00:00"))
        if zaman.tzinfo is None:
            raise ValueError("timezone yok")
        meta["zaman"] = zaman.astimezone(datetime.timezone.utc)
    except (OverflowError, TypeError, ValueError):
        warn("OLGU-05", f"KANIT_KOKENI_DOGRULANAMADI kaynak={kaynak}",
             beklenen="timezone-bagli ISO-8601 timestamp", bulunan=repr(meta.get("timestamp")))
        return None
    return meta


def kanit_koken_kontrol(atlas_metni, attest, kod_metni, git_kok):
    """Kaniti guncel HEAD/run/zamanla baglar; butun sonuclar yalniz WARN'dir."""
    metalar = {
        "atlas-cikti": kanit_metadatasi(atlas_metni, "atlas-cikti"),
        "attest-cikti": kanit_metadatasi("", "attest-cikti", attest=attest),
        "kod-cikti": kanit_metadatasi(kod_metni, "kod-cikti"),
    }
    try:
        git = subprocess.run(
            ["git", "-C", str(git_kok), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        git = None
    guncel_head = git.stdout.strip() if git is not None and git.returncode == 0 else None
    if not re.fullmatch(r"[0-9a-f]{40}", guncel_head or ""):
        warn("OLGU-05", "KANIT_HEAD_DOGRULANAMADI kaynak=git", beklenen="git HEAD", bulunan="YOK")
        guncel_head = None

    simdi = datetime.datetime.now(datetime.timezone.utc)
    for kaynak, meta in metalar.items():
        if meta is None:
            continue
        if guncel_head is not None and meta["head"] != guncel_head:
            warn("OLGU-05", f"KANIT_HEAD_UYUSMAZLIGI kaynak={kaynak}",
                 beklenen=guncel_head, bulunan=meta["head"])
        yas = (simdi - meta["zaman"]).total_seconds()
        if yas > meta["timeout"]:
            warn("OLGU-05", f"KANIT_ZAMAN_ASIMI kaynak={kaynak}",
                 beklenen=f"yas<={meta['timeout']}s", bulunan=f"yas={int(yas)}s")
        elif yas < -60:
            warn("OLGU-05", f"KANIT_ZAMANI_GELECEKTE kaynak={kaynak}",
                 beklenen="en-cok-60s-saat-farki", bulunan=f"fark={int(-yas)}s")

    runlar = {meta["run_id"] for meta in metalar.values() if meta is not None}
    if len(runlar) > 1:
        warn("OLGU-05", "KANIT_RUN_UYUSMAZLIGI kaynak=kanit-seti",
             beklenen="tek run_id", bulunan=",".join(sorted(runlar)))


def olgu05_kontrol(veri, kanitlar, git_kok):
    verilen = [ad for ad, yol in kanitlar.items() if yol is not None]
    if not verilen:
        return 0
    eksik = [ad for ad, yol in kanitlar.items() if yol is None]
    if eksik:
        fail(
            "OLGU-05", "CANLI_OLCUM_DOGRULANAMADI kaynak=kanit-seti",
            beklenen="atlas,attest,kod", bulunan=",".join(verilen) or "YOK",
        )
        return 1

    atlas_metni = kanit_oku(kanitlar["atlas"], "atlas-cikti")
    attest_metni = kanit_oku(kanitlar["attest"], "attest-cikti")
    kod_metni = kanit_oku(kanitlar["kod"], "kod-cikti")
    if None in (atlas_metni, attest_metni, kod_metni):
        return 1

    atlas_ozeti = ozet_ayristir(atlas_metni, ATLAS_OZET, "atlas-cikti")
    kod_ozeti = ozet_ayristir(kod_metni, KOD_OZET, "kod-cikti")
    try:
        attest = json.loads(attest_metni)
    except (json.JSONDecodeError, TypeError) as exc:
        fail(
            "OLGU-05", "CANLI_OLCUM_DOGRULANAMADI kaynak=attest-cikti",
            beklenen="gecerli JSON", bulunan=type(exc).__name__,
        )
        attest = None

    attest_alanlari = ("canli_sayi", "taban_sayi", "p0", "p1")
    if not isinstance(attest, dict) or attest.get("sema") != "OZTEST-ATTEST/v1":
        bulunan = attest.get("sema") if isinstance(attest, dict) else type(attest).__name__
        fail(
            "OLGU-05", "CANLI_OLCUM_DOGRULANAMADI kaynak=attest-cikti",
            beklenen="OZTEST-ATTEST/v1", bulunan=bulunan,
        )
        attest = None
    elif any(type(attest.get(alan)) is not int or attest[alan] < 0 for alan in attest_alanlari):
        fail(
            "OLGU-05", "CANLI_OLCUM_DOGRULANAMADI kaynak=attest-cikti",
            beklenen="canli_sayi/taban_sayi/p0/p1:negatif-olmayan-int", bulunan="SEMA_GECERSIZ",
        )
        attest = None

    kanit_koken_kontrol(atlas_metni, attest, kod_metni, git_kok)

    hatalar = int(atlas_ozeti is None or kod_ozeti is None or attest is None)
    olcumler = []
    if atlas_ozeti is not None:
        olcumler.extend((
            ("atlas_son_gecen", atlas_ozeti[0], "atlas-cikti"),
            ("atlas_envanter_sayisi", atlas_ozeti[1], "atlas-cikti"),
        ))
    if attest is not None:
        olcumler.extend((
            ("attest_canli", attest["canli_sayi"], "attest-cikti"),
            ("attest_taban", attest["taban_sayi"], "attest-cikti"),
            ("attest_p0", attest["p0"], "attest-cikti"),
            ("attest_p1", attest["p1"], "attest-cikti"),
        ))
    if kod_ozeti is not None:
        olcumler.append(("kod_son_gecen", kod_ozeti[0], "kod-cikti"))

    for alan, beklenen, kaynak in olcumler:
        if veri[alan] != beklenen:
            fail(
                "OLGU-05", f"DEGER_UYUSMAZLIGI id={alan} kaynak={kaynak}",
                beklenen=beklenen, bulunan=veri[alan],
            )
            hatalar += 1
    return hatalar


def main(argv=None):
    kok, git_kok, kanitlar, yalniz_dersler = argumanlar(list(sys.argv[1:] if argv is None else argv))
    if kok is None:
        return 1
    if yalniz_dersler:
        return olgu06_kontrol(kok, git_kok)

    kanon = kok / "docs" / "OLGULAR.md"
    if not kanon.is_file():
        fail("OLGU-01", "KANON_YOK", beklenen=kanon, bulunan="YOK")
        return 1

    metin = oku_metin(kanon)
    if metin is None:
        return 1
    eslesmeler = JSON_BLOK.findall(metin)
    if len(eslesmeler) != 1:
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen="tek JSON blok", bulunan=len(eslesmeler))
        return 1
    try:
        veri = json.loads(eslesmeler[0])
    except (json.JSONDecodeError, TypeError) as exc:
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen="gecerli JSON", bulunan=type(exc).__name__)
        return 1
    if not isinstance(veri, dict) or veri.get("schema") != "OLGULAR/v1":
        bulunan = veri.get("schema") if isinstance(veri, dict) else type(veri).__name__
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen="OLGULAR/v1", bulunan=bulunan)
        return 1

    hatalar = 0
    for alan in ("lab_surum", "baseline_commit", "mekanizma_kayitlari", *SAYISAL_ALANLAR):
        if alan not in veri:
            fail("OLGU-02", "SEMA_GECERSIZ", beklenen=f"alan:{alan}", bulunan="YOK")
            hatalar += 1
    if hatalar:
        return 1

    for alan in SAYISAL_ALANLAR:
        deger = veri[alan]
        if type(deger) is not int or deger < 0:
            fail("OLGU-02", "SEMA_GECERSIZ", beklenen=f"{alan}:negatif-olmayan-int", bulunan=repr(deger))
            hatalar += 1
    if not isinstance(veri["lab_surum"], str):
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen="lab_surum:string", bulunan=type(veri["lab_surum"]).__name__)
        hatalar += 1
    mekanizmalar = veri["mekanizma_kayitlari"]
    if not isinstance(mekanizmalar, list) or not all(isinstance(x, str) for x in mekanizmalar):
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen="mekanizma_kayitlari:string[]", bulunan=type(mekanizmalar).__name__)
        return 1
    if len(set(mekanizmalar)) != len(mekanizmalar):
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen="benzersiz commit dizisi", bulunan="YINELENEN")
        hatalar += 1
    if veri["mekanizma_sayisi"] != len(mekanizmalar):
        fail(
            "OLGU-03", "DEGER_UYUSMAZLIGI id=mekanizma_sayisi kaynak=mekanizma_kayitlari",
            beklenen=len(mekanizmalar), bulunan=veri["mekanizma_sayisi"],
        )
        hatalar += 1

    surum_yolu = kok / "SURUM.md"
    surum_metni = oku_metin(surum_yolu)
    if surum_metni is None:
        hatalar += 1
    else:
        surum_eslesme = re.search(r"^Sürüm:\s*(v[^\s]+)", surum_metni, re.MULTILINE)
        bulunan_surum = surum_eslesme.group(1) if surum_eslesme else "YOK"
        if bulunan_surum != veri["lab_surum"]:
            fail(
                "OLGU-03", "DEGER_UYUSMAZLIGI id=lab_surum kaynak=SURUM.md",
                beklenen=bulunan_surum, bulunan=veri["lab_surum"],
            )
            hatalar += 1

    taban_yolu = kok / "ATLAS_SABLONLAR" / "scripts" / "OZTEST-TABAN.json"
    try:
        taban = json.loads(taban_yolu.read_text(encoding="utf-8"))
        taban_sayi = taban.get("sayi") if isinstance(taban, dict) else None
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError) as exc:
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen=f"gecerli:{taban_yolu}", bulunan=type(exc).__name__)
        taban_sayi = None
        hatalar += 1
    if type(taban_sayi) is int and taban_sayi != veri["atlas_envanter_sayisi"]:
        fail(
            "OLGU-03", "DEGER_UYUSMAZLIGI id=atlas_envanter_sayisi kaynak=OZTEST-TABAN.json",
            beklenen=taban_sayi, bulunan=veri["atlas_envanter_sayisi"],
        )
        hatalar += 1
    elif taban_sayi is not None and type(taban_sayi) is not int:
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen="OZTEST sayi:int", bulunan=repr(taban_sayi))
        hatalar += 1

    hatalar += olgu05_kontrol(veri, kanitlar, git_kok)

    baseline = veri["baseline_commit"]
    commitler = [baseline, *mekanizmalar]
    for commit in commitler:
        if not isinstance(commit, str) or not COMMIT.fullmatch(commit):
            fail("OLGU-04", "COMMIT_DOGRULANAMADI", beklenen="7-40 kucuk-hex", bulunan=repr(commit))
            hatalar += 1
            continue
        varlik = git_kos(git_kok, "cat-file", "-e", f"{commit}^{{commit}}")
        if varlik is None or varlik.returncode != 0:
            bulunan = "git-yok" if varlik is None else (varlik.stderr.strip() or f"exit={varlik.returncode}")
            fail("OLGU-04", "COMMIT_DOGRULANAMADI", beklenen=f"commit:{commit}", bulunan=bulunan)
            hatalar += 1
            continue
        ata = git_kos(git_kok, "merge-base", "--is-ancestor", commit, "HEAD")
        if ata is None or ata.returncode != 0:
            bulunan = "git-yok" if ata is None else (ata.stderr.strip() or f"exit={ata.returncode}")
            fail("OLGU-04", "COMMIT_ATA_DEGIL", beklenen=f"{commit}<=HEAD", bulunan=bulunan)
            hatalar += 1

    hatalar += olgu06_kontrol(kok, git_kok)
    if hatalar:
        return 1
    print(f"OLGU-LINT PASS olgu={len(veri) - 1} kaynak={2 + len(commitler)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        fail("OLGU-02", "SEMA_GECERSIZ", beklenen="kontrollu sonuc", bulunan=type(exc).__name__)
        raise SystemExit(1)
