#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""oztest_mutasyon.py — oz-testlerin ikinci katman mutasyon kaniti.

NEDEN VAR
  Bir oz-testin PASS vermesi, testin gercekten kostugunu gostermez. Bir kapi
  bozuldugunda ilgili testin KIRMIZI olmasi gerekir. Birinci katman
  (`mutasyon_bataryasi.py`) kapinin ihlali yakaladigini olcer; bu ikinci
  katman testin kapi regresyonunu yakaladigini olcer.

  Her vaka hedef kapiyi GECICI kopyada bozar, test paketini kosar ve hedef test
  kimliginin PASS -> FAIL gectigini arar. Bos govdeli testler de AST ile
  yakalanir: kosulsuz `True` gecen `kontrol/sina` cagrilari ve yalniz
  `pass`/`...`/docstring/`assert True` tasiyan test fonksiyonlari.

  Fikstur koku tamamen gecicidir; gercek agaca yazilmaz. Atlas paketi git
  gerektiren OLG-1 icin `.git` de kopyalanir; bu yuzden mutasyonlu kosuda
  YAYIN-1/OLG-1 ek kirmizi verebilir. Hedef testler yine de kendi kimlikleriyle
  FAIL etmelidir; arac bunu ayri ayri dogrular.

KULLANIM
  python3 tools/oztest_mutasyon.py --kontrol   # yeniden olc ve kaydi dogrula
  python3 tools/oztest_mutasyon.py --yaz       # kaydi yenile

CIKIS: 0 = hedef testler PASS->FAIL ve bos-govde taramasi temiz ·
       1 = mutasyon gorulmedi, test bos gorundu veya kayit bayat
"""
import argparse
import ast
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

KOK = pathlib.Path(__file__).resolve().parents[1]
KANIT = KOK / "tools" / "oztest_mutasyon_kaniti.json"
SEMA = "OZTEST-MUTASYON/v1"
ATLAS_SELFTEST = "ATLAS_SABLONLAR/scripts/atlas_selftest.py"
KOD_SELFTEST = "KOD_SABLONLAR/scripts/kod_selftest.py"
V4_SELFTEST = "KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_selftest.py"

# Her vaka: hedef kapi, hedef test kimligi ve kaynakta TEK kez gecen mutasyon.
# `eski`/`yeni` gercek kaynak metnidir; biri bir kez bulunmazsa arac durur.
VAKALAR = [
    {
        "id": "OZM-01",
        "paket": "ATLAS",
        "kapi": "ATLAS_SABLONLAR/scripts/check_models.py",
        "test": "MOD-2",
        "test_adi": "check_models: katalogda olmayan model FAIL",
        "mutasyon": "MOD-03 katalog-yok bulgusu kaldirildi",
        "eski": ('    if bilgi is None:\n'
                 '        hata.append(f"MOD-03 {ad}: katalogda YOK: {tam}")\n'
                 '        continue\n'),
        "yeni": ('    if bilgi is None:\n'
                 '        continue\n'),
    },
    {
        "id": "OZM-02",
        "paket": "ATLAS",
        "kapi": "ATLAS_SABLONLAR/scripts/budget_guard.py",
        "test": "BG-3",
        "test_adi": "budget_guard: bilinmeyen faz preflight FAIL",
        "mutasyon": "bilinmeyen faz dali rc=1 yerine rc=0 donduruyor",
        "eski": ('    if tahmin is None:\n'
                 '        print(f"FAIL: bilinmeyen faz \'{pref}\' (beklenen: {list(FAZ_LIMIT)})")\n'
                 '        sys.exit(1)\n'),
        "yeni": ('    if tahmin is None:\n'
                 '        print(f"FAIL: bilinmeyen faz \'{pref}\' (beklenen: {list(FAZ_LIMIT)})")\n'
                 '        sys.exit(0)\n'),
    },
    {
        "id": "OZM-03",
        "paket": "ATLAS",
        "kapi": "ATLAS_SABLONLAR/scripts/prompt_lint.py",
        "test": "PL-3",
        "test_adi": "prompt_lint: 'kanit GEREKMEZ' vacuous-PASS deligi yakalanir",
        "mutasyon": "PL-10 vacuous-PASS kontrolu devre disi",
        "eski": ('    if VACUOUS.search(t):\n'
                 '        hatalar.append(f"PL-10'),
        "yeni": ('    if False and VACUOUS.search(t):\n'
                 '        hatalar.append(f"PL-10'),
    },
    {
        "id": "OZM-04",
        "paket": "KOD",
        "kapi": "KOD_SABLONLAR/scripts/dep_audit.py",
        "test": "DEP-1",
        "test_adi": "DEP-1 manifest var, kilit ANAHTARI yok -> P0",
        "mutasyon": "kilit anahtari yok bulgusu P0 yerine P1",
        "eski": ('        else:\n'
                 '            bulgular.append({"kural": "DEP-01", "siddet": "P0", "konum": m,\n'),
        "yeni": ('        else:\n'
                 '            bulgular.append({"kural": "DEP-01", "siddet": "P1", "konum": m,\n'),
    },
    {
        "id": "OZM-05",
        "paket": "KOD",
        "kapi": "KOD_SABLONLAR/scripts/freeze_check.py",
        "test": "FRZ-2",
        "test_adi": "FRZ-2 profil ele gecirilmis -> GATE_TAMPERED, exit=2 TERMINAL",
        "mutasyon": "profil SHA256 degisim dali atlandi",
        "eski": ('    elif sha(profil) != beklenen:\n'
                 '        bulgular.append({"kural": "FRZ-01"'),
        "yeni": ('    elif False and sha(profil) != beklenen:\n'
                 '        bulgular.append({"kural": "FRZ-01"'),
    },
    {
        "id": "OZM-06",
        "paket": "KOD",
        "kapi": "KOD_SABLONLAR/scripts/test_attest.py",
        "test": "TST-1",
        "test_adi": "TST-1 temiz kanit PASS",
        "mutasyon": "temiz kanitta da rc=1 donduren cikis",
        "eski": '    sys.exit(1 if p0 else 0)\n',
        "yeni": '    sys.exit(1)\n',
    },
]

TEST_CAGRI = {"kontrol": (0, 2, 3), "sina": (0, 1, 2), "check": (0, 2, 3)}
ATLAMA_IZI = ("atlandi", "atlanmis", "calistirilmadi", "skip")
TEST_DOSYA = re.compile(r"(?:selftest|_test)\.py$", re.I)


def _oku(yol):
    return pathlib.Path(yol).read_text(encoding="utf-8")


def _sha(yol):
    return hashlib.sha256(pathlib.Path(yol).read_bytes()).hexdigest()


def _sabit_deger(dugum):
    if isinstance(dugum, ast.Constant):
        return True, dugum.value
    return False, None


def _arg(dugum, sira, ad):
    if len(dugum.args) > sira:
        return dugum.args[sira]
    for kw in dugum.keywords:
        if kw.arg == ad:
            return kw.value
    return None


def _bos_govde(govde):
    """Docstring/pass/.../return/assert True disinda bir sey var mi?"""
    anlamli = []
    for dugum in govde:
        if isinstance(dugum, ast.Expr) and isinstance(dugum.value, ast.Constant):
            if isinstance(dugum.value.value, str):
                continue
        if isinstance(dugum, ast.Pass):
            continue
        if isinstance(dugum, ast.Expr) and isinstance(dugum.value, ast.Constant) and dugum.value.value is Ellipsis:
            continue
        if isinstance(dugum, ast.Return) and dugum.value is None:
            continue
        if isinstance(dugum, ast.Assert):
            sabit, deger = _sabit_deger(dugum.test)
            if sabit and bool(deger):
                continue
        if (isinstance(dugum, ast.Expr) and isinstance(dugum.value, ast.Call)
                and isinstance(dugum.value.func, ast.Attribute)
                and dugum.value.func.attr in ("assertTrue", "assertIs", "assertEqual")
                and len(dugum.value.args) >= 1):
            sabitler = [_sabit_deger(x)[0] for x in dugum.value.args]
            if all(sabitler) and len({repr(_sabit_deger(x)[1]) for x in dugum.value.args}) == 1:
                continue
        anlamli.append(dugum)
    return not anlamli


def bos_govde_tara(metin, ad="<bellek>"):
    """Test kayitlarindaki kosulsuz PASS'lari ve bos test gövdelerini bulur."""
    bulgular = []
    try:
        agac = ast.parse(metin)
    except SyntaxError as exc:
        return [{"dosya": ad, "satir": exc.lineno or 0,
                 "tip": "PARSE", "ayrinti": str(exc)}]

    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Call) and isinstance(dugum.func, ast.Name):
            adi = dugum.func.id
            if adi not in TEST_CAGRI:
                continue
            id_sira, kosul_sira, detay_sira = TEST_CAGRI[adi]
            kimlik = _arg(dugum, id_sira,
                          {"kontrol": "kod", "sina": "ad", "check": "tid"}[adi])
            kosul = _arg(dugum, kosul_sira,
                         {"kontrol": "gecti", "sina": "kosul", "check": "ok"}[adi])
            detay = _arg(dugum, detay_sira,
                         {"kontrol": "detay", "sina": "ayrinti", "check": "detail"}[adi])
            sabit, deger = _sabit_deger(kosul)
            if not sabit or not bool(deger):
                continue
            metin_detay = deger if isinstance(deger, str) else ""
            if isinstance(detay, ast.Constant) and isinstance(detay.value, str):
                metin_detay = detay.value
            if any(iz in metin_detay.lower() for iz in ATLAMA_IZI):
                continue  # acik "atlandi" dali test degildir; gorunur kalir
            kimlik_metni = kimlik.value if isinstance(kimlik, ast.Constant) else "?"
            bulgular.append({
                "dosya": ad,
                "satir": dugum.lineno,
                "tip": "KOSULSUZ_TRUE",
                "ayrinti": f"{adi}({kimlik_metni!r}) kosulu sabit True",
            })

        if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef)):
            adi = dugum.name.lower()
            if not (adi.startswith("test") or adi.endswith("_test")):
                continue
            if _bos_govde(dugum.body):
                bulgular.append({
                    "dosya": ad,
                    "satir": dugum.lineno,
                    "tip": "BOS_GOVDE",
                    "ayrinti": f"{dugum.name} yalniz pass/docstring/return tasiyor",
                })
    return bulgular


def _selftest_dosyalari():
    yollar = [KOK / ATLAS_SELFTEST, KOK / KOD_SELFTEST, KOK / V4_SELFTEST]
    yollar += sorted((KOK / "tools").glob("*selftest*.py"))
    return [p for p in yollar if p.is_file()]


def bos_govde_denetimi():
    bulgular = []
    kayit = 0
    for yol in _selftest_dosyalari():
        metin = _oku(yol)
        try:
            agac = ast.parse(metin)
        except SyntaxError as exc:
            bulgular.append({"dosya": str(yol.relative_to(KOK)), "satir": exc.lineno or 0,
                             "tip": "PARSE", "ayrinti": str(exc)})
            continue
        for dugum in ast.walk(agac):
            if (isinstance(dugum, ast.Call) and isinstance(dugum.func, ast.Name)
                    and dugum.func.id in TEST_CAGRI):
                kayit += 1
        bulgular += bos_govde_tara(metin, str(yol.relative_to(KOK)))
    return {"taranan_dosya": len(_selftest_dosyalari()), "test_kaydi": kayit,
            "ihlal": len(bulgular), "bulgular": bulgular}


def bos_govde_oztest():
    """Aracin bos govdeyi GERCEKTEN yakaladigini sentetik kaynakla sinar."""
    fikstur = (
        "def kontrol(*a):\n    pass\n"
        "kontrol('BOS-1', 'kosulsuz', True)\n"
        "def test_bos():\n    pass\n"
        "class T:\n    def test_bos2(self):\n        ...\n"
    )
    bulgular = bos_govde_tara(fikstur, "<fikstir>")
    return len(bulgular), bulgular


def _git(*args):
    return subprocess.run(["git", "-C", str(KOK)] + list(args),
                          capture_output=True, text=True)


def _temiz_kaynak():
    """Test edilen dosyalar HEAD ile ayni mi? Taban kirliligi YAYIN-1'i yakardi."""
    yollar = [ATLAS_SELFTEST, KOD_SELFTEST, V4_SELFTEST] + sorted({v["kapi"] for v in VAKALAR})
    r = _git("status", "--porcelain", "--", *yollar)
    if r.returncode != 0:
        raise RuntimeError("git status: %s" % (r.stderr or r.stdout).strip()[:200])
    if r.stdout.strip():
        raise RuntimeError("test edilen kaynak temiz degil; once commit et: %s"
                           % r.stdout.strip())


def _hazirla(hedef):
    """Temiz HEAD arsivini ve .git'i kopyalar; fikstür tabani kirli olmaz."""
    r = subprocess.run(["git", "-C", str(KOK), "archive", "--format=tar", "HEAD"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("git archive: %s" % (r.stderr or b"")[:200])
    hedef.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(r.stdout), mode="r:") as arsiv:
        arsiv.extractall(str(hedef))
    shutil.copytree(str(KOK / ".git"), str(hedef / ".git"), symlinks=True)
    return hedef


def _mutasyon_uygula(repo, vakalar):
    for vaka in vakalar:
        yol = repo / vaka["kapi"]
        metin = _oku(yol)
        adet = metin.count(vaka["eski"])
        if adet != 1:
            raise RuntimeError(
                "%s: mutasyon deseni %d kez gecti (1 bekleniyordu)" %
                (vaka["kapi"], adet))
        yol.write_text(metin.replace(vaka["eski"], vaka["yeni"], 1), encoding="utf-8")


def _kos_selftest(repo, paket, timeout=1200):
    rel = ATLAS_SELFTEST if paket == "ATLAS" else KOD_SELFTEST
    komut = [sys.executable, str(repo / rel)]
    if paket == "ATLAS":
        komut.append("--sessiz")
    r = subprocess.run(komut, cwd=str(repo), capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _ozet(cikti):
    son = None
    for satir in cikti.splitlines():
        if "OZ-TEST:" in satir and "gecti" in satir:
            son = satir.strip()
    return son or ""


def _fail_idler(cikti):
    kimlikler = set()
    for satir in cikti.splitlines():
        m = re.match(r"^\s+(?:KALDI|FAIL)\s+([A-Za-z0-9][A-Za-z0-9-]*)\b", satir)
        if m:
            kimlikler.add(m.group(1))
    return kimlikler


def _satirlar(cikti, hedef):
    return [s.strip() for s in cikti.splitlines()
            if re.match(r"^\s+(?:KALDI|FAIL)\s+%s\b" % re.escape(hedef), s)]


def _paket_olc(paket, vakalar):
    koke = pathlib.Path(tempfile.mkdtemp(prefix="ozm_%s_" % paket.lower()))
    try:
        taban = _hazirla(koke / "taban")
        mutant = _hazirla(koke / "mutant")
        _mutasyon_uygula(mutant, vakalar)
        # Iki kosu bagimsiz; paralel calisir. Boylece ikinci katman, iki tam
        # Atlas kosusunun ard arda toplami kadar surmez.
        import concurrent.futures as cf
        with cf.ThreadPoolExecutor(max_workers=2) as havuz:
            f0 = havuz.submit(_kos_selftest, taban, paket)
            f1 = havuz.submit(_kos_selftest, mutant, paket)
            rc0, cikti0 = f0.result()
            rc1, cikti1 = f1.result()
        return rc0, cikti0, rc1, cikti1
    finally:
        shutil.rmtree(str(koke), ignore_errors=True)


def olc():
    _temiz_kaynak()
    bos = bos_govde_denetimi()
    fikstur_sayisi, fikstur_bulgular = bos_govde_oztest()
    if bos["ihlal"]:
        for b in bos["bulgular"][:20]:
            print("FAIL BOS-GOVDE %(dosya)s:%(satir)s %(tip)s :: %(ayrinti)s" % b)
        raise RuntimeError("bos govdeli/kosulsuz test: %d" % bos["ihlal"])
    if fikstur_sayisi < 3:
        raise RuntimeError(
            "bos-govde oz-testi fiksturu yakalanmadi: %d bulgu (en az 3 bekleniyordu)"
            % fikstur_sayisi)

    sonuclar = []
    for paket in ("ATLAS", "KOD"):
        vakalar = [v for v in VAKALAR if v["paket"] == paket]
        rc0, cikti0, rc1, cikti1 = _paket_olc(paket, vakalar)
        ozet0, ozet1 = _ozet(cikti0), _ozet(cikti1)
        fail0, fail1 = _fail_idler(cikti0), _fail_idler(cikti1)
        if rc0 != 0 or fail0:
            raise RuntimeError(
                "%s taban PASS degil: rc=%d · fail=%s · %s"
                % (paket, rc0, sorted(fail0) or "-", ozet0 or cikti0[-500:]))
        if rc1 != 1:
            raise RuntimeError(
                "%s mutasyon rc=1 vermedi: rc=%d · %s"
                % (paket, rc1, ozet1 or cikti1[-500:]))
        for vaka in vakalar:
            if vaka["test"] not in fail1:
                raise RuntimeError(
                    "%s: %s hedef testi mutasyonda FAIL etmedi · fail=%s · %s"
                    % (paket, vaka["test"], sorted(fail1), ozet1 or cikti1[-500:]))
            sonuclar.append({
                "id": vaka["id"],
                "paket": paket,
                "kapi": vaka["kapi"],
                "test": vaka["test"],
                "test_adi": vaka["test_adi"],
                "mutasyon": vaka["mutasyon"],
                "baseline": "PASS",
                "mutant": "FAIL",
                "fail_satiri": (_satirlar(cikti1, vaka["test"]) or ["-"])[0],
                "baseline_ozet": ozet0,
                "mutant_ozet": ozet1,
            })
        print("%s: taban %s · mutant %s · hedef %s" % (
            paket, ozet0 or "PASS", ozet1 or "rc=%d" % rc1,
            ", ".join(v["test"] for v in vakalar)))

    kaynak = {}
    for rel in [ATLAS_SELFTEST, KOD_SELFTEST, V4_SELFTEST] + sorted({v["kapi"] for v in VAKALAR}):
        kaynak[rel] = _sha(KOK / rel)
    return {
        "sema": SEMA,
        "kaynak": kaynak,
        "vakalar": sonuclar,
        "bos_govde": {
            "taranan_dosya": bos["taranan_dosya"],
            "test_kaydi": bos["test_kaydi"],
            "ihlal": bos["ihlal"],
            "bulgular": bos["bulgular"],
        },
        "oztest": {
            "fikstur_bulgu": fikstur_sayisi,
            "fikstur_tipleri": sorted({b["tip"] for b in fikstur_bulgular}),
        },
        "sayim": {
            "vaka": len(sonuclar),
            "gecen": len(sonuclar),
            "bos_govde_ihlal": bos["ihlal"],
        },
    }


def _kanit_ile_uyumlu(sonuc, kayit):
    if kayit.get("sema") != SEMA:
        return "sema"
    if kayit.get("kaynak") != sonuc["kaynak"]:
        return "kaynak sha256"
    eski = {v.get("id"): v for v in kayit.get("vakalar", [])}
    yeni = {v.get("id"): v for v in sonuc["vakalar"]}
    if set(eski) != set(yeni):
        return "vaka kimlikleri"
    for kimlik in yeni:
        for alan in ("paket", "kapi", "test", "test_adi", "mutasyon",
                     "baseline", "mutant", "fail_satiri"):
            if eski[kimlik].get(alan) != yeni[kimlik].get(alan):
                return "%s.%s" % (kimlik, alan)
    if kayit.get("bos_govde") != sonuc["bos_govde"]:
        return "bos_govde"
    if kayit.get("oztest") != sonuc["oztest"]:
        return "oztest"
    if kayit.get("sayim") != sonuc["sayim"]:
        return "sayim"
    return ""


def main():
    ap = argparse.ArgumentParser(description="Oz-test ikinci katman mutasyonu")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--kontrol", action="store_true", help="yeniden olc ve kaydi dogrula")
    g.add_argument("--yaz", action="store_true", help="kaydi yenile")
    args = ap.parse_args()
    if not args.yaz:
        args.kontrol = True

    try:
        sonuc = olc()
    except Exception as exc:
        print("FAIL OZTEST-MUTASYON: %s: %s" % (type(exc).__name__, exc))
        return 1

    if args.yaz:
        KANIT.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
        print("OZTEST-MUTASYON: YAZILDI %s" % KANIT)
        return 0

    if not KANIT.is_file():
        print("FAIL OZTEST-MUTASYON: kayit yok (%s); once --yaz" % KANIT)
        return 1
    try:
        kayit = json.loads(_oku(KANIT))
    except Exception as exc:
        print("FAIL OZTEST-MUTASYON: kayit okunamadi: %s" % exc)
        return 1
    fark = _kanit_ile_uyumlu(sonuc, kayit)
    if fark:
        print("FAIL OZTEST-MUTASYON: kayit bayat (%s); --yaz ile yenile" % fark)
        return 1
    print("OZTEST-MUTASYON PASS — %d/%d hedef test PASS->FAIL · bos govde=0 · kayit guncel"
          % (sonuc["sayim"]["gecen"], sonuc["sayim"]["vaka"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
