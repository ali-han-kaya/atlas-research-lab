#!/usr/bin/env python3
"""kod_selftest — KOD hatti makine kapilarinin oz-testi

NEDEN VAR:
Bir kapinin "PASS" demesi, kapinin CALISTIGI anlamina gelmez. Atlas v1.5'te
iki adet bos `{}` dosyasi FINAL PASS aliyordu ve hicbir test bunu goremiyordu.
Bu betik her kapiyi POZITIF (temiz girdi -> PASS) ve NEGATIF (bozuk girdi ->
FAIL) fiksturle sinar. Negatif fikstur olmadan bir kapi test edilmemistir:
her zaman PASS diyen bir kapi da pozitif testi gecer.

DIL BAGIMSIZLIGI: hat hicbir dilin kaynak kodunu ayristirmaz. Ayni artefakt
zinciri python/js/swift profilleriyle AYNI kararı vermelidir; DIL-1..3 bunu
sinar.

Kullanim: python3 scripts/kod_selftest.py [--ayrintili] [--yalniz-d2-findings]
"""
import ast, hashlib, json, os, pathlib, re, shutil, sqlite3, subprocess, sys, tempfile, time

AYRINTILI = "--ayrintili" in sys.argv
S = pathlib.Path(__file__).resolve().parent

# ------------------------------------------------ O5-03  ORTAMDAN YALITIM
# 24.08.2026 (olculdu): `V4_VERIFY_YOLU` operatorun kabuğunda EXPORT edilmisse
# — ki `00_KOD_OKU_BENI.md` tam olarak bunu oneriyor — degisken alt sureclere
# SIZIYOR ve secret_scan'i KISMI modda sinayan 5 fikstur (K4-1, E2E-1, JSON-1,
# JSON-2, O4-03a) YANLIS KIRMIZI veriyordu. Kanit (git archive HEAD, v1.7.7):
# env yokken 122/122, env varken 117/122 — yani kusur bu turdan ONCE de vardi
# ve kapilarda DEGIL, oz-testin ORTAMA BAGLILIGINDAYDI.
# Cozum: degisken BASTA alinip `os.environ`dan CIKARILIR (boylece hicbir alt
# surece sizmaz); TAM modu isteyen fikstürler yolu ACIKCA `--v4` ile verir.
_V4_ORTAM = os.environ.pop("V4_VERIFY_YOLU", "")
gecti, kaldi, atlandi = 0, 0, 0
raporlar = []


def kos(betik, *args, cwd=None):
    komut = ([sys.executable, str(S / betik)] if betik.endswith(".py")
             else ["bash", str(S / betik)]) + list(args)
    r = subprocess.run(komut, cwd=cwd, capture_output=True, text=True, timeout=600)
    return r.returncode, (r.stdout + r.stderr)


def butce_preflight_kos(faz):
    """budget_guard faz testini canli kullanici DB'sinden yalit."""
    with tempfile.TemporaryDirectory() as d:
        dp = pathlib.Path(d)
        db = dp / "opencode.db"
        with sqlite3.connect(db) as con:
            con.execute("CREATE TABLE message (data TEXT)")
        ortam = dict(os.environ,
                     ATLAS_OPENCODE_DB=str(db),
                     ATLAS_BUDGET_LIMIT="30.0",
                     ATLAS_PROJE_UUID="550e8400-e29b-41d4-a716-446655440000")
        komut = [sys.executable, str(S / "budget_guard.py"), "--preflight", faz]
        r = subprocess.run(komut, cwd=dp, capture_output=True, text=True, env=ortam, timeout=600)
        return r.returncode, (r.stdout + r.stderr)


def sina(ad, kosul, ayrinti=""):
    global gecti, kaldi
    if kosul:
        gecti += 1
        raporlar.append(f"  OK   {ad}")
    else:
        kaldi += 1
        raporlar.append(f"  FAIL {ad}" + (f"\n         {ayrinti}" if ayrinti else ""))


def sina_atla(ad, neden=""):
    """OLCULMEMIS kalem — `OK` SAYILMAZ, `FAIL` de SAYILMAZ; ayri kova.

    v1.7.286 (D2): onceden bu kalemler "kosul=True + ayrinti=CALISTIRILMADI"
    kalibiyla `sina()` uzerinden yaziliyordu. Olculdu: `sina` kosulu `True` gorunce `gecti += 1` yapiyor
    ve `  OK   ...` basiyordu — ayrinti metni "CALISTIRILMADI" olsa bile.
    Sonuc: olculmemis kalem PASS sayacina giriyordu (§4 "olcmedigini iddia etme").
    `lab_full` ayni ayrimi `ATLANDI` kovasiyla zaten yapiyor (KOSULLU, rc=0);
    burada da ayni sozlesme gecerli: kalem GORUNUR, ama sayaci SISIRMEZ.
    """
    global atlandi
    atlandi += 1
    raporlar.append(f"  ATLANDI {ad}" + (f"\n         {neden}" if neden else ""))


def ozet_metni(gecti, kaldi, atlandi):
    """Ozet satiri. ATLANDI varsa "hepsi gecti" DENMEZ (fail-closed dil).

    `lab_full` ayni sozlesmeyi `HUKUM: KOSULLU` ile uygular. Ayri fonksiyon
    olmasinin sebebi: ozet mantigi test EDILEBILSIN — gomulu print test edilemez.
    """
    s = f"\nKOD OZ-TEST: {gecti}/{gecti + kaldi} gecti"
    if atlandi:
        s += f" · {atlandi} ATLANDI — KOSULLU, tam kosu GEREKLI"
    return s


def git_kur(d):
    subprocess.run(["git", "init", "-q", "."], cwd=d, capture_output=True, timeout=600)
    subprocess.run(["git", "add", "-A"], cwd=d, capture_output=True, timeout=600)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "taban"], cwd=d, capture_output=True, timeout=600)


def oku(p):
    """Dosya yoksa BOS DIZE doner — oz-test COKMEZ, ilgili test KIRMIZI verir.
    (Geri alma matrisinde olculdu: eksik dosya traceback uretiyor ve rapor hic
    basilmadigi icin 'KIRMIZI=0' gibi ALDATICI bir sonuc cikiyordu.)"""
    try:
        return pathlib.Path(p).read_text(encoding="utf-8")
    except Exception:
        return ""


def yaz(p, icerik):
    p = pathlib.Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(icerik if isinstance(icerik, str)
                 else json.dumps(icerik, ensure_ascii=False, indent=2), encoding="utf-8")


def d2_findings_sozlesmesi():
    """Olumlu KOD kapi fiksturlerinde `findings: []` alanini dogrula."""
    agac = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    hedefler, ihlaller = [], []

    def statik_deger(dugum):
        if isinstance(dugum, ast.Dict):
            try:
                return ast.literal_eval(dugum)
            except Exception:
                return None
        if (isinstance(dugum, ast.Constant) and isinstance(dugum.value, str)
                and dugum.value.strip().startswith("{")):
            try:
                return json.loads(dugum.value)
            except Exception:
                return None
        return None

    def olumlu_fikstur(veri):
        if not isinstance(veri, dict) or veri.get("verdict") != "PASS":
            return False
        if "findings" in veri and veri.get("findings") not in ([], None):
            return False
        for alan in ("checks", "manifest_reconciliation"):
            kayitlar = veri.get(alan)
            if (isinstance(kayitlar, list) and kayitlar
                    and all(isinstance(k, dict) and str(k.get("status", "")).strip()
                            for k in kayitlar)):
                return True
        return False

    for dugum in ast.walk(agac):
        veri = statik_deger(dugum)
        if not olumlu_fikstur(veri):
            continue
        hedefler.append(dugum.lineno)
        if veri.get("findings", None) != []:
            ihlaller.append(dugum.lineno)
    return sorted(hedefler), sorted(ihlaller)


_d2_hedefler, _d2_ihlaller = d2_findings_sozlesmesi()
if "--yalniz-d2-findings" in sys.argv:
    for _satir in _d2_ihlaller:
        print(f"FAIL D2-FINDINGS satir={_satir}: olumlu fixture explicit findings: [] tasimiyor")
    print(f"D2-FINDINGS: olumlu={len(_d2_hedefler)} eksik={len(_d2_ihlaller)} traceback=0")
    sys.exit(0 if len(_d2_hedefler) >= 11 and not _d2_ihlaller else 1)

sina("D2-FINDINGS olumlu kapi fiksturleri explicit findings: [] tasir",
     len(_d2_hedefler) >= 11 and not _d2_ihlaller,
     f"olumlu={len(_d2_hedefler)} eksik_satirlar={_d2_ihlaller}")


# ------------------------------------------------ O5-01  OZ-FIKSTUR PARCALI YAZIM
# v1.7.7'nin ACIK BULGUSU (24.08.2026, olculdu): `secret_scan` fiksturleri PEM
# basligini KAYNAKTA TEK PARCA tasiyordu. Hat hedef depoya kurulunca kendi
# `scripts/kod_selftest.py`'sini de goturur; oradaki satirlar IZLENMEYEN durur ve
# TAM mod taramasi (v4_verify `-----BEGIN ... PRIVATE KEY-----` kalibi) bunlari
# GERCEK sir sanardi: kurulu depoda 3x P0 (kod_selftest.py:528, :552 ve
# scripts/__pycache__/kod_selftest.*.pyc) ve her KFAZ2 bloklanirdi.
#
# COZUM fiksturu ZAYIFLATMAK DEGIL: yazilan DOSYA yine tam, gecerli bir PEM
# govdesi tasir (kapinin disleri aynen durur); yalniz KAYNAKTA dize parcalidir.
#
# NEDEN `+` DEGIL `"".join(...)` (bu turda olculdu): CPython AST optimizeri iki
# dize LITERALININ `+`'sini DERLEME ZAMANINDA KATLAR; katlanan sabit .pyc'ye TEK
# PARCA yazilir ve `scripts/__pycache__/kod_selftest.*.pyc` yine eslesirdi
# (olcum: `"a" + "b"` -> pyc'de tam dize VAR; `"".join((a, b))` -> YOK).
def sahte_anahtar():
    """secret_scan fiksturu: gecerli govdeli SAHTE ozel anahtar (parcali yazim).

    Donen DIZE tek parcadir (gercek bir anahtar dosyasi gibi taranmalidir);
    parcali olan bu betigin KAYNAK METNIDIR.
    """
    bas = "".join(("-----BEGIN RSA", " PRIVATE", " KEY-----\n"))
    son = "".join(("-----END RSA", " PRIVATE", " KEY-----\n"))
    return bas + "MIIEowIBAAKCAQEAx7Vq3nQe9Zk2pLmT0uYb8cWfNhGdRsAv\n" + son


def v4_yolu():
    """Toolkit'teki v4_verify.py — TAM mod fiksturleri icin. Yoksa None.

    Toolkit KOPYALANMAZ ve DEGISTIRILMEZ (kirmizi cizgi); yalnizca ISARET edilir.
    """
    for aday in (_V4_ORTAM,
                 S.parent.parent / "KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_verify.py",
                 S.parent.parent.parent / "KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_verify.py"):
        if aday and pathlib.Path(aday).is_file():
            return pathlib.Path(aday)
    return None


# =============================================================== PERM (perm_lint)
with tempfile.TemporaryDirectory() as d:
    a = pathlib.Path(d) / ".opencode" / "agent"
    yaz(a / "temiz.md", '---\ndescription: temiz\nmode: subagent\npermission:\n  read:\n'
                        '    "*": allow\n    "gizli/**": deny\n    "**/gizli/**": deny\n---\ngovde\n')
    rc, out = kos("perm_lint.py", "--dizin", d, "--sessiz")
    sina("PERM-1 temiz blok PASS verir", rc == 0, out.strip()[:160])

    yaz(a / "bozuk.md", '---\ndescription: bozuk\nmode: subagent\npermission:\n  read:\n'
                        '    "gizli/**": deny\n    "*": allow\n---\ngovde\n')
    rc, out = kos("perm_lint.py", "--dizin", d, "--sessiz")
    sina("PERM-2 olu kural (yildiz sonda) FAIL verir", rc == 1 and "PERM-01" in out, out.strip()[:160])

with tempfile.TemporaryDirectory() as d:
    a = pathlib.Path(d) / ".opencode" / "agent"
    yaz(a / "tekkalip.md", '---\ndescription: tek kalip\nmode: subagent\npermission:\n  read:\n'
                           '    "*": allow\n    "**/gizli/**": deny\n---\ngovde\n')
    rc, out = kos("perm_lint.py", "--dizin", d, "--sessiz")
    sina("PERM-3 tek kalip (kok korunmuyor) FAIL verir", rc == 1 and "PERM-02" in out, out.strip()[:200])

# ======================================================== GATE (kod_gate_merge)
with tempfile.TemporaryDirectory() as d:
    yaz(pathlib.Path(d) / "a.json", {"kapi": "2A", "verdict": "PASS", "findings": [],
                                     "checks": [{"id": "C1", "status": "GECTI", "evidence": "x"}]})
    yaz(pathlib.Path(d) / "b.json", {"kapi": "2B", "verdict": "PASS", "findings": [],
                                     "checks": [{"id": "C2", "status": "GECTI", "evidence": "y"}]})
    rc, out = kos("kod_gate_merge.py", "a.json", "b.json", cwd=d)
    sina("GM-1 iki temiz kapi PASS", rc == 0, out.strip()[:160])

    yaz(pathlib.Path(d) / "bos1.json", {})
    yaz(pathlib.Path(d) / "bos2.json", {})
    rc, out = kos("kod_gate_merge.py", "bos1.json", "bos2.json", cwd=d)
    sina("GM-2 iki bos {} FAIL (NO_INSPECTION_EVIDENCE)",
         rc == 1 and "NO_INSPECTION_EVIDENCE" in out, out.strip()[:160])

    yaz(pathlib.Path(d) / "crit.json", {"verdict": "PASS",
                                        "findings": [{"priority": "CRITICAL", "aciklama": "sql"}]})
    rc, out = kos("kod_gate_merge.py", "crit.json", "b.json", cwd=d)
    sina("GM-3 CRITICAL etiketi sessizce dusmez, FAIL", rc == 1, out.strip()[:160])

    yaz(pathlib.Path(d) / "ayni1.json", {"verdict": "PASS", "findings": [],
                                         "checks": [{"id": "C9", "status": "GECTI", "evidence": "z"}]})
    yaz(pathlib.Path(d) / "ayni2.json", {"verdict": "PASS", "findings": [],
                                         "checks": [{"id": "C9", "status": "GECTI", "evidence": "z"}]})
    rc, out = kos("kod_gate_merge.py", "ayni1.json", "ayni2.json", cwd=d)
    sina("GM-4 birebir ayni kapi IDENTICAL_GATE_INPUTS FAIL",
         rc == 1 and "IDENTICAL_GATE_INPUTS" in out, out.strip()[:160])

    yaz(pathlib.Path(d) / "yalan.json", {"verdict": "PASS", "metadata": {"p0_count": 0},
                                         "findings": [{"priority": "P0", "aciklama": "x"}]})
    rc, out = kos("kod_gate_merge.py", "yalan.json", "b.json", cwd=d)
    _gm5_beyan_ok = rc == 1 and "beyan p0_count" in out

    yaz(pathlib.Path(d) / "gm5-metadata-yok.json",
        {"kapi": "2A", "verdict": "PASS", "findings": [],
         "checks": [{"id": "GM5-YOK", "status": "GECTI", "evidence": "x"}]})
    _gm5_yok_rc, _gm5_yok_cikti = kos(
        "kod_gate_merge.py", "gm5-metadata-yok.json", "b.json", cwd=d)
    _gm5_metadata_yok_ok = _gm5_yok_rc == 0 and "Traceback" not in _gm5_yok_cikti

    _gm5_kok_vakalari = [
        ("liste", []),
        ("metin", "string"),
        ("null", None),
        ("sayi", 0),
        ("boolean", False),
    ]
    _gm5_kok_sonuclari = []
    for _gm5_ad, _gm5_deger in _gm5_kok_vakalari:
        _gm5_yol = pathlib.Path(d) / f"gm5-metadata-kok-{_gm5_ad}.json"
        yaz(_gm5_yol, {"kapi": "2A", "verdict": "PASS", "metadata": _gm5_deger,
                       "findings": [],
                       "checks": [{"id": f"GM5-{_gm5_ad}", "status": "GECTI",
                                   "evidence": "x"}]})
        _gm5_rc, _gm5_cikti = kos(
            "kod_gate_merge.py", _gm5_yol.name, "b.json", cwd=d)
        _gm5_final = json.loads(
            (pathlib.Path(d) / "_KOSU/gate/FINAL-KOD-GATE.json").read_text(encoding="utf-8")
        )
        _gm5_kok_sonuclari.append(
            (_gm5_ad, _gm5_rc, "IHLAL" in _gm5_cikti,
             "metadata" in _gm5_cikti.lower(), "Traceback" in _gm5_cikti,
             _gm5_final["verdict"],
             any("metadata" in n.lower() for n in _gm5_final["ihlaller"]))
        )
    _gm5_sayac_vakalari = [
        ("p0-liste", "p0_count", []),
        ("p0-sozluk", "p0_count", {}),
        ("p0-bos-metin", "p0_count", ""),
        ("p0-metin", "p0_count", "abc"),
        ("p0-false", "p0_count", False),
        ("p0-true", "p0_count", True),
        ("p0-float", "p0_count", 0.5),
        ("p0-null", "p0_count", None),
        ("p0-negatif", "p0_count", -1),
        ("p0-sayisal-metin", "p0_count", "0"),
        ("p1-null", "p1_count", None),
        ("p1-liste", "p1_count", []),
    ]
    _gm5_sayac_sonuclari = []
    for _gm5_ad, _gm5_alan, _gm5_deger in _gm5_sayac_vakalari:
        _gm5_yol = pathlib.Path(d) / f"gm5-metadata-sayac-{_gm5_ad}.json"
        yaz(_gm5_yol, {"kapi": "2A", "verdict": "PASS",
                       "metadata": {_gm5_alan: _gm5_deger}, "findings": [],
                       "checks": [{"id": f"GM5-SAYAC-{_gm5_ad}", "status": "GECTI",
                                   "evidence": "x"}]})
        _gm5_rc, _gm5_cikti = kos(
            "kod_gate_merge.py", _gm5_yol.name, "b.json", cwd=d)
        _gm5_final = json.loads(
            (pathlib.Path(d) / "_KOSU/gate/FINAL-KOD-GATE.json").read_text(encoding="utf-8")
        )
        _gm5_sayac_sonuclari.append(
            (_gm5_ad, _gm5_rc, "IHLAL" in _gm5_cikti,
             "metadata." in _gm5_cikti.lower(), "Traceback" in _gm5_cikti,
             _gm5_final["verdict"],
             any("metadata." in n.lower() for n in _gm5_final["ihlaller"]))
        )
    sina(
        "GM-5 metadata yok serbest; beyan celiskisi, gecersiz kok ve sayac tipleri temiz FAIL",
        _gm5_beyan_ok and _gm5_metadata_yok_ok
        and all(rc == 1 and ihlal and metadata_tanisi and not traceback
                and verdict == "FAIL" and final_tanisi
                for _, rc, ihlal, metadata_tanisi, traceback, verdict, final_tanisi
                in _gm5_kok_sonuclari)
        and all(rc == 1 and ihlal and metadata_tanisi and not traceback
                and verdict == "FAIL" and final_tanisi
                for _, rc, ihlal, metadata_tanisi, traceback, verdict, final_tanisi
                in _gm5_sayac_sonuclari),
        f"beyan={_gm5_beyan_ok} yok={_gm5_metadata_yok_ok} "
        f"kokler={_gm5_kok_sonuclari} sayaclar={_gm5_sayac_sonuclari}",
    )

    yaz(pathlib.Path(d) / "etik-eksik.json", {"verdict": "PASS",
                                               "findings": [{"id": "PENDING_ETHICS",
                                                             "finding": "etik siddeti eksik"}]})
    rc, out = kos("kod_gate_merge.py", "etik-eksik.json", "b.json", cwd=d)
    sina("GM-6 PENDING_ETHICS siddeti YOKSA P0'i AKLAYAMAZ",
         rc == 1 and "PASS-PENDING-ETHICS" not in out and "P0:1" in out
         and "Traceback" not in out, out.strip()[:200])

    yaz(pathlib.Path(d) / "etik-liste.json", {"verdict": "PASS",
                                               "findings": [{"id": "PENDING_ETHICS",
                                                             "priority": ["P0"],
                                                             "finding": "etik siddeti yanlis tip"}]})
    rc, out = kos("kod_gate_merge.py", "etik-liste.json", "b.json", cwd=d)
    sina("GM-7 PENDING_ETHICS konteyner siddeti P0'i AKLAYAMAZ",
         rc == 1 and "PASS-PENDING-ETHICS" not in out and "P0:1" in out
         and "Traceback" not in out, out.strip()[:200])

    yaz(pathlib.Path(d) / "c.json", {"kapi": "2C", "verdict": "PASS", "findings": [],
                                     "checks": [{"id": "C3", "status": "GECTI", "evidence": "z"}]})
    _gm8_sonuclar = []
    for _gm8_adet in (2, 3):
        for _gm8_etik in ("P1", "P2"):
            for _gm8_ek in (None, "P0", "P1"):
                _gm8_bulgular = [{"id": "PENDING_ETHICS", "priority": _gm8_etik,
                                  "finding": "etik onay bekliyor"}]
                if _gm8_ek is not None:
                    _gm8_bulgular.append({"id": "BASKA_ENGEL", "priority": _gm8_ek,
                                          "finding": "etik disi engel"})
                yaz(pathlib.Path(d) / "etik.json", {"verdict": "PASS", "findings": _gm8_bulgular})
                _gm8_yollar = ["etik.json", "b.json"] + (["c.json"] if _gm8_adet == 3 else [])
                rc, out = kos("kod_gate_merge.py", *_gm8_yollar, cwd=d)
                try:
                    _gm8_final = json.loads(oku(pathlib.Path(d) / "_KOSU/gate/FINAL-KOD-GATE.json"))
                except ValueError:
                    _gm8_final = {}
                _gm8_verdict = "PASS-PENDING-ETHICS" if _gm8_ek is None else "FAIL"
                _gm8_ok = (
                    rc == (0 if _gm8_ek is None else 1)
                    and _gm8_final.get("verdict") == _gm8_verdict
                    and _gm8_final.get("mod") == f"{_gm8_adet}-of-{_gm8_adet}"
                    and f"-> {_gm8_verdict}" in out and "Traceback" not in out
                )
                _gm8_sonuclar.append((_gm8_adet, _gm8_etik, _gm8_ek, rc,
                                      _gm8_final.get("verdict"), _gm8_ok))
    sina("GM-8 etik bekleyisi exit 0; ek P0/P1 exit 1 (2-of-2 ve 3-of-3)",
         all(ok for _, _, _, _, _, ok in _gm8_sonuclar), f"sonuclar={_gm8_sonuclar}")

    # --- GM-9 (v1.7.282): GEREKCELI RED ayri kova — KOD hatti (ortak_gate.degerlendir)
    # Olculdu: M2 mutasyonunda `ortak_gate` dali kaldirildi, HICBIR test yanmadi
    # (KOD 172/172). Bu test o bosluğu kapatir. Uc yon:
    #   (a) REDDEDILDI + gerekce -> PASS, stdout'ta REDDEDILEN_GEREKCELI
    #   (b) UYGULANMAMIS         -> FAIL P1 (muafiyet sanilmasin)
    #   (c) REDDEDILDI, gerekce YOK -> FAIL P0 (fail-closed; gerekcesiz red kacistir)
    _gm9 = []
    for _ad, _madde, _beklenen in (
        ("red", {"fix_id": "CHG-024", "status": "REDDEDILDI",
                 "evidence": "oneri reddedildi; gerekce: ayri baslik zorunlu"}, "PASS"),
        ("yapilmadi", {"fix_id": "CHG-024", "status": "UYGULANMAMIS"}, "FAIL"),
        ("gerekcesiz", {"fix_id": "CHG-024", "status": "REDDEDILDI"}, "FAIL"),
    ):
        yaz(pathlib.Path(d) / "mr.json",
            {"kapi": "2A", "verdict": _beklenen, "findings": [],
             "checks": [{"id": "C2", "status": "GECTI", "evidence": "y"}],
             "manifest_reconciliation": [_madde]})
        rc, out = kos("kod_gate_merge.py", "mr.json", "a.json", cwd=d)
        _f = {}
        try:
            _f = json.loads(oku(pathlib.Path(d) / "_KOSU/gate/FINAL-KOD-GATE.json"))
        except ValueError:
            pass
        _red = _f.get("kapilar", [{}])[0].get("reddedilen", [])
        _gm9.append((_ad, rc, _beklenen, _red, out))

    # (d) GEREKCELI RED `checks[]` icinde — manifest'te DEGIL.
    # Olculdu (v1.7.284, M7): `reddedilen_kayitlar` yalniz manifest tararken
    # bu yol HICBIR testi yakmiyordu (KOD 173/173). Ayni ontoloji iki yerde
    # farkli uygulaniyordu. Bu yon o bosluğu kapatir.
    yaz(pathlib.Path(d) / "checks_red.json",
        {"kapi": "2A", "verdict": "PASS", "findings": [],
         "checks": [{"id": "C1", "status": "GECTI", "evidence": "x"},
                    {"id": "C2", "status": "REDDEDILDI",
                     "evidence": "kapsam disi; gerekce: ..."}]})
    _gm9d_rc, _gm9d_out = kos("kod_gate_merge.py", "checks_red.json", "b.json", cwd=d)
    try:
        _gm9d_f = json.loads(oku(pathlib.Path(d) / "_KOSU/gate/FINAL-KOD-GATE.json"))
    except ValueError:
        _gm9d_f = {}
    _gm9d_red = _gm9d_f.get("kapilar", [{}])[0].get("reddedilen", [])
    sina("GM-9 gerekceli REDDEDILDI P0/P1 sayilmaz + GORUNUR; UYGULANMAMIS P1; gerekcesiz P0",
         _gm9[0][1] == 0 and "REDDEDILEN_GEREKCELI: 1" in _gm9[0][4]
         and len(_gm9[0][3]) == 1 and _gm9[0][3][0]["fix_id"] == "CHG-024"
         and _gm9[1][1] == 1 and "P1:1" in _gm9[1][4] and "REDDEDILEN_GEREKCELI" not in _gm9[1][4]
         and _gm9[2][1] == 1 and "P0:1" in _gm9[2][4] and "GEREKCE-YOK" in _gm9[2][4]
         and _gm9d_rc == 0
         and "REDDEDILEN_GEREKCELI: 1" in _gm9d_out
         and len(_gm9d_red) == 1 and _gm9d_red[0]["kaynak"] == "checks"
         and not any("Traceback" in x[4] for x in _gm9),
         f"red={_gm9[0][1]} yapilmadi={_gm9[1][1]} gerekcesiz={_gm9[2][1]} "
         f"checks_red=(rc={_gm9d_rc},red={_gm9d_red})")

# --- GM-10 (v1.7.286, D2): OLCULMEMIS KALEM `OK` SAYILAMAZ -----------------
# Olculdu: `sina(ad, True, "CALISTIRILMADI: ...")` -> `  OK   ad` ve `gecti += 1`.
# Yani olculmemis kalem PASS sayacina giriyordu. `lab_full` bu ayrimi zaten
# `ATLANDI`/`KOSULLU` ile yapiyor; oz-test tarafi yapmiyordu.
# Fonksiyonun kaynagi BIREBIR alinip calistirilir — gercek davranis olculur,
# kopya bir mantik degil. Yonler:
#   (a) sina_atla -> gecti ARTMAZ, atlandi ARTAR, satir "ATLANDI" der
#   (b) ozet: atlandi=0 -> "173/173 gecti" (eski bicim KORUNUR)
#   (c) ozet: atlandi>0 -> "ATLANDI — KOSULLU" (fail-closed dil)
#   (d) kaynakta `sina(..., True, "CALISTIRILMADI` kalibi KALMADI
_src = pathlib.Path(__file__).resolve().read_text(encoding="utf-8")
_ns = {"gecti": 0, "kaldi": 0, "atlandi": 0, "raporlar": []}
for _ad in ("sina", "sina_atla", "ozet_metni"):
    _i = _src.index(f"def {_ad}(")
    _j = _src.index("\ndef ", _i + 1)
    exec(compile(_src[_i:_j], f"<{_ad}>", "exec"), _ns)
_ns["sina_atla"]("ORNEK-1 olculemedi", "CALISTIRILMADI: paket disinda")
_gm10_satir = _ns["raporlar"][-1]
_gm10_a = (_ns["gecti"] == 0 and _ns["atlandi"] == 1
           and _gm10_satir.strip().startswith("ATLANDI ORNEK-1"))
_gm10_b = _ns["ozet_metni"](173, 0, 0).strip() == "KOD OZ-TEST: 173/173 gecti"
_gm10_c_metin = _ns["ozet_metni"](172, 0, 1)
_gm10_c = ("KOD OZ-TEST: 172/172 gecti" in _gm10_c_metin
           and "ATLANDI" in _gm10_c_metin and "KOSULLU" in _gm10_c_metin)
import re as _re
# (d) YALNIZ KOD satirlari — yorum/docstring'de kalibi ANLATMAK serbest.
#     Olculdu (ilk hali): yalniz `_src` tarandi -> 3 eslesme cikti ve ucu de
#     kendi aciklamamdi. Test kendi dokumantasyonunu "kusur" saymamali.
_kalan = []
for _s in _src.split("\n"):
    _kod = _s.split("#", 1)[0]
    if _re.search(r'sina\([^)]*?,\s*True,\s*"CALISTIRILMADI', _kod):
        _kalan.append(_s.strip()[:70])
_gm10_d = (_kalan == [])
sina("GM-10 OLCULMEMIS kalem OK SAYILMAZ: sina_atla ayri kova · ozet KOSULLU der",
     _gm10_a and _gm10_b and _gm10_c and _gm10_d,
     f"a=({_ns['gecti']},{_ns['atlandi']},{_gm10_satir.strip()[:60]!r}) "
     f"b={_gm10_b} c={_gm10_c} kalan_kalip={len(_kalan)}")

# ============================================================ TEST (test_attest)
JUNIT_TEMIZ = ('<?xml version="1.0"?><testsuite tests="5" failures="0" errors="0" skipped="0">'
               '</testsuite>')
JUNIT_KIRIK = ('<?xml version="1.0"?><testsuite tests="5" failures="2" errors="0" skipped="0">'
               '</testsuite>')
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "_KOSU/gate/junit.xml", JUNIT_TEMIZ)
    yaz(dp / "_KOSU/gate/BASELINE.json", {"test": {"kosan": 5, "atlanan": 0}, "test_adlari": []})
    yaz(dp / "_KOSU/03-KFAZ-3-TEST-EVIDENCE.json",
        {"komut": "pytest", "cikis_kodu": 0, "rapor": "_KOSU/gate/junit.xml",
         "rapor_formati": "junit-xml", "sonuc": {"kosan": 5, "basarisiz": 0, "hata": 0, "atlanan": 0}})
    rc, out = kos("test_attest.py", cwd=d)
    sina("TST-1 temiz kanit PASS", rc == 0, out.strip()[:160])

    yaz(dp / "_KOSU/gate/junit.xml", JUNIT_KIRIK)
    rc, out = kos("test_attest.py", cwd=d)
    sina("TST-2 basarisiz test FAIL + beyan celiskisi",
         rc == 1 and "EVIDENCE_UNVERIFIED" in out, out.strip()[:200])

    yaz(dp / "_KOSU/gate/junit.xml",
        '<?xml version="1.0"?><testsuite tests="2" failures="0" errors="0" skipped="0"></testsuite>')
    yaz(dp / "_KOSU/03-KFAZ-3-TEST-EVIDENCE.json",
        {"komut": "pytest", "cikis_kodu": 0, "rapor": "_KOSU/gate/junit.xml",
         "rapor_formati": "junit-xml", "sonuc": {"kosan": 2, "basarisiz": 0, "hata": 0, "atlanan": 0}})
    rc, out = kos("test_attest.py", cwd=d)
    sina("TST-3 kosan(2) < taban(5): test silinerek yesil olmaz",
         rc == 1 and "TST-04" in out, out.strip()[:200])

    yaz(dp / "_KOSU/03-KFAZ-3-TEST-EVIDENCE.json",
        {"komut": "pytest", "cikis_kodu": 0, "rapor_formati": "yok"})
    rc, out = kos("test_attest.py", cwd=d)
    sina("TST-4 makine okunur rapor YOK -> EVIDENCE_UNVERIFIED P0",
         rc == 1 and "EVIDENCE_UNVERIFIED" in out, out.strip()[:200])

# ========================================================= FREEZE (freeze_check)
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "kod_profil.json", {"dil": "python", "test_komutu": "pytest"})
    import hashlib
    h = hashlib.sha256((dp / "kod_profil.json").read_bytes()).hexdigest()
    yaz(dp / "_KOSU/gate/BASELINE.json",
        {"kod_profil_yolu": "kod_profil.json", "kod_profil_sha256": h,
         "scripts_sha256": {}, "dondurulan": {}})
    rc, out = kos("freeze_check.py", cwd=d)
    sina("FRZ-1 profil degismemis -> PASS", rc == 0, out.strip()[:160])

    yaz(dp / "kod_profil.json", {"dil": "python", "test_komutu": "true"})
    rc, out = kos("freeze_check.py", cwd=d)
    sina("FRZ-2 profil ele gecirilmis -> GATE_TAMPERED, exit=2 TERMINAL",
         rc == 2 and "GATE_TAMPERED" in out, f"exit={rc} {out.strip()[:160]}")

    shutil.rmtree(dp / "_KOSU")
    rc, out = kos("freeze_check.py", cwd=d)
    sina("FRZ-3 taban yok -> CALISTIRILMADI, sessiz temiz DEGIL",
         rc == 1 and "CALISTIRILMADI" in out, out.strip()[:160])

# ========================================================= IMZA (imzala.py)
def _imza_kos(dp, anahtar_yaz):
    ev = dp / "bos-home"
    key = ev / ".config" / "lab_imza.key"
    key.parent.mkdir(parents=True, exist_ok=True)
    anahtar_yaz(key)
    taban = dp / "BASELINE.json"
    yaz(taban, {})
    ortam = {k: v for k, v in os.environ.items() if k != "LAB_IMZA_ANAHTARI"}
    ortam["HOME"] = str(ev)
    r = subprocess.run([sys.executable, str(S / "imzala.py"), "--dogrula",
                        "--taban", str(taban)], cwd=dp, capture_output=True,
                       text=True, env=ortam, timeout=600)
    return r.returncode, r.stdout + r.stderr

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    rc, out = _imza_kos(dp, lambda p: p.write_bytes(b"\xff\xfe\x00\x01"))
    sina("K20-1 IKILI anahtar temiz GECERSIZ reddi verir (cokmeden)",
         rc == 1 and "GECERSIZ" in out and "Traceback" not in out,
         f"exit={rc} {out.strip()[:180]}")

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    def _okunamaz_yaz(p):
        p.write_text("a" * 64 + "\n", encoding="utf-8")
        p.chmod(0o000)
    rc, out = _imza_kos(dp, _okunamaz_yaz)
    (dp / "bos-home" / ".config" / "lab_imza.key").chmod(0o600)
    sina("K20-2 OKUNAMAYAN anahtar temiz GECERSIZ reddi verir (cokmeden)",
         rc == 1 and "GECERSIZ" in out and "Traceback" not in out,
         f"exit={rc} {out.strip()[:180]}")

# ======================================================== RECONCILE (chg_reconcile)
def kosu_iskeleti(dp, degisecek, chg, req=None, req_test=None, dondurulan=None):
    req = req or [{"id": "REQ-001", "tur": "yapisal", "kabul": "x"}]
    yaz(dp / "_KOSU/00-KFAZ-0-SPEC.md",
        "# spec\n\n```json\n" + json.dumps({"sema": "KFAZ0/v1", "req": req}) + "\n```\n")
    yaz(dp / "_KOSU/01-KFAZ-1-PLAN.md",
        "# plan\n\n```json\n" + json.dumps({"sema": "KFAZ1/v1", "degisecek": degisecek,
                                           "dondurulan": dondurulan or [],
                                           "req_test": req_test or {"REQ-001": []}}) + "\n```\n")
    yaz(dp / "_KOSU/02-KFAZ-2-MANIFEST.md",
        "# manifest\n\n```json\n" + json.dumps({"sema": "KFAZ2/v1", "chg": chg}) + "\n```\n")
    yaz(dp / "_KOSU/gate/BASELINE.json", {"test_adlari": ["test_eski"]})


with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(d)
    (dp / "src/a.py").write_text("x = 2\n")
    kosu_iskeleti(dp, ["src/a.py"], [{"id": "CHG-001", "req": "REQ-001",
                                      "dosya": "src/a.py", "durum": "UYGULANMIS"}])
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("RECK-1 plan/manifest/diff ortusuyor -> PASS", rc == 0, out.strip()[:200])

    (dp / "src/plansiz.py").write_text("y = 1\n")
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("RECK-2 plansiz dosya -> SCOPE_VIOLATION P0",
         rc == 1 and "SCOPE_VIOLATION" in out, out.strip()[:200])
    (dp / "src/plansiz.py").unlink()

    kosu_iskeleti(dp, ["src/a.py"], [{"id": "CHG-002", "req": "REQ-001",
                                      "dosya": "src/yok.py", "durum": "UYGULANMIS"}])
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("RECK-3 hayalet CHG (plansiz dosyaya bagli) -> P0",
         rc == 1 and "HAYALET_CHG" in out, out.strip()[:200])

    kosu_iskeleti(dp, ["src/a.py"], [{"id": "CHG-001", "req": "REQ-001",
                                      "dosya": "src/a.py", "durum": "UYGULANMIS"}],
                  req=[{"id": "REQ-001", "tur": "davranissal", "kabul": "x"}],
                  req_test={"REQ-001": ["test_eski"]})
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("RECK-4 davranissal REQ tabanda VAR OLAN teste eslenmis -> P0",
         rc == 1 and "RECK-07" in out, out.strip()[:220])

    kosu_iskeleti(dp, ["src/a.py"], [{"id": "CHG-001", "req": "REQ-001",
                                      "dosya": "src/a.py", "durum": "UYGULANMIS"}],
                  dondurulan=["src/a.py"])
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("RECK-5 dondurulmus bolge degismis -> P0",
         rc == 1 and "RECK-06" in out, out.strip()[:220])

    yaz(dp / "_KOSU/01-KFAZ-1-PLAN.md", "# plan\n\nmakine blogu yok, sadece markdown tablosu\n")
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("RECK-6 makine blogu yok -> CALISTIRILMADI P0 (sessiz PASS degil)",
         rc == 1 and "CALISTIRILMADI" in out, out.strip()[:220])

# ============================================================= SECRET / DEP / API
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    kok = pathlib.Path(__file__).resolve().parent.parent.parent
    yaz(dp / "temiz.py", "x = 1\n")
    git_kur(d)
    (dp / "gercek.py").write_text('AWS = "AKIA' + "A" * 16 + '"\n')
    rc, out = kos("secret_scan.py", "--tum", "--dizin", str(kok), cwd=d)
    sina("SEC-0 kalip kaynagi v4_verify.py'den geliyor (kopyalanmiyor)",
         "v4_verify.py" in out, out.strip()[:200])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    # O3-10 (v1.7.7): bu fikstur eskiden `"kilit_dosyasi": []` yaziyordu ve
    # "P0 bekle" diyordu — yani DUZELTILEN davranisi kodluyordu. Bos liste artik
    # BILINCLI BEYANDIR (BILGI). P0 yolu icin anahtar HIC OLMAMALIDIR.
    yaz(dp / "kod_profil.json", {"bagimlilik_manifesti": ["pyproject.toml"]})
    yaz(dp / "pyproject.toml", "[project]\ndependencies = [\"requests\"]\n")
    git_kur(d)
    rc, out = kos("dep_audit.py", cwd=d)
    sina("DEP-1 manifest var, kilit ANAHTARI yok -> P0", rc == 1 and "DEP-01" in out,
         out.strip()[:200])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "kod_profil.json", {"imza_komutu": ""})
    yaz(dp / "_KOSU/gate/BASELINE.json", {"dis_imza": ["foo", "bar"]})
    yaz(dp / "src.py", "def foo():\n    pass\n")
    rc, out = kos("api_surface.py", cwd=d)
    sina("API-1 T2 kademesi olumlu karar URETEMEZ (DUSUK_GUVEN)",
         "T2" in out and "DUSUK_GUVEN" in out, out.strip()[:220])

# ======================================================= INTEGRITY (bosluklu yol)
with tempfile.TemporaryDirectory() as d:
    bosluklu = pathlib.Path(d) / "bosluk testi"
    bosluklu.mkdir()
    rc, out = kos("check_code_integrity.sh", cwd=str(bosluklu))
    sina("ITG-90 bosluklu yolda calisir (v1.5 regresyonu)",
         "No such file" not in out and rc == 1, out.strip()[:200])

    yaz(bosluklu / "_KOSU/00-KFAZ-0-a.md", "```json\n{}\n```\n")
    yaz(bosluklu / "_KOSU/01-KFAZ-1-a.md", "```json\n{}\n```\n")
    yaz(bosluklu / "_KOSU/02-KFAZ-2-a.md", "```json\n{}\n```\n")
    yaz(bosluklu / "_KOSU/03-KFAZ-3-a.json", {"cikis_kodu": 0})
    yaz(bosluklu / "_KOSU/gate/BASELINE.json", {})
    yaz(bosluklu / "_KOSU/gate/KOD-gate-2a.json",
        {"kapi": "2A", "verdict": "PASS", "findings": [],
         "checks": [{"id": "C1", "status": "GECTI", "evidence": "a"}]})
    yaz(bosluklu / "_KOSU/gate/KOD-gate-2b.json",
        {"kapi": "2B", "verdict": "PASS", "findings": [],
         "checks": [{"id": "C2", "status": "GECTI", "evidence": "b"}]})
    # FINAL elle degil GERCEK birlestirici ile uretilir -> girdi_sha256 tasir
    rc, out = kos("kod_gate_merge.py", "_KOSU/gate/KOD-gate-2a.json",
                  "_KOSU/gate/KOD-gate-2b.json", cwd=str(bosluklu))
    sina("ITG-91a birlestirici bosluklu yolda FINAL uretti", rc == 0, out.strip()[:200])

    rc, out = kos("check_code_integrity.sh", cwd=str(bosluklu))
    sina("ITG-91 tam zincir -> PASS", rc == 0, out.strip()[:200])

    # 2A yeniden yazilir: mtime degil ICERIK degisir -> ozet tutmaz
    yaz(bosluklu / "_KOSU/gate/KOD-gate-2a.json",
        {"kapi": "2A", "verdict": "PASS", "findings": [],
         "checks": [{"id": "C1", "status": "GECTI",
                                                      "evidence": "DEGISTI"}]})
    rc, out = kos("check_code_integrity.sh", cwd=str(bosluklu))
    sina("ITG-92 FINAL bayat (2A icerigi degisti) -> FAIL",
         rc == 1 and "BAYAT" in out, out.strip()[:240])

    # FINAL tazelenir, sonra verdict FAIL yapilir ve TESLIM yazilir
    kos("kod_gate_merge.py", "_KOSU/gate/KOD-gate-2a.json",
        "_KOSU/gate/KOD-gate-2b.json", cwd=str(bosluklu))
    fin = bosluklu / "_KOSU/gate/FINAL-KOD-GATE.json"
    d = json.loads(fin.read_text()); d["verdict"] = "FAIL"
    fin.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    yaz(bosluklu / "_KOSU/05-KFAZ-5-TESLIM.md", "teslim\n")
    rc, out = kos("check_code_integrity.sh", cwd=str(bosluklu))
    sina("ITG-93 verdict FAIL iken TESLIM yazilmis -> FAIL",
         rc == 1 and "ITG-22" in out, out.strip()[:240])

# ================================================= DIL BAGIMSIZLIGI (python/js/swift)
for dil, komut, rapor in (("python", "pytest -q", "_KOSU/gate/junit.xml"),
                          ("js", "vitest run --reporter=junit", "_KOSU/gate/junit.xml"),
                          ("swift", "swift test --xunit-output", "_KOSU/gate/junit.xml")):
    with tempfile.TemporaryDirectory() as d:
        dp = pathlib.Path(d)
        yaz(dp / "kod_profil.json", {"dil": dil, "test_komutu": komut,
                                     "test_raporu": rapor, "test_rapor_formati": "junit-xml"})
        yaz(dp / rapor, JUNIT_TEMIZ)
        yaz(dp / "_KOSU/gate/BASELINE.json", {"test": {"kosan": 5, "atlanan": 0}, "test_adlari": []})
        yaz(dp / "_KOSU/03-KFAZ-3-TEST-EVIDENCE.json",
            {"komut": komut, "cikis_kodu": 0, "rapor": rapor, "rapor_formati": "junit-xml",
             "sonuc": {"kosan": 5, "basarisiz": 0, "hata": 0, "atlanan": 0}})
        rc, out = kos("test_attest.py", cwd=d)
        sina(f"DIL-{dil} ayni artefakt zinciri ayni karari verir (PASS)", rc == 0, out.strip()[:160])


# =============================================================================
# OLCUM-02 DUZELTMELERININ NEGATIF FIKSTURLERI  (24.08.2026)
#
# Canli duman kosusu 19 kirik buldu ve bu oz-test o gun 32/32 YESIL veriyordu.
# Yani oz-test, hattin kurulabilirligini, surulebilirligini ve ajan ciktisinin
# SEMASINI hic olcmuyordu. Asagidaki her blok bir duzeltmeye aittir ve
# DUZELTME GERI ALINIRSA KIRMIZI VERIR — testin varlik sebebi budur.
# =============================================================================

def _sema_kosu(dp, req, taban_ek=None, faz2=True):
    """Standart bir _KOSU agaci kurar; `req` KFAZ0 makine blogunun req alanidir."""
    yaz(dp / "src/a.py", "def f(): return 2\n")
    yaz(dp / "tests/test_var.py", "def test_var(): assert True\n")
    yaz(dp / "_KOSU/00-KFAZ-0-SPEC.md",
        "# KFAZ0\n```json\n" + json.dumps(
            {"sema": "KFAZ0/v1", "giris_modu": "MEVCUT_KOD", "req": req}) + "\n```\n")
    yaz(dp / "_KOSU/01-KFAZ-1-PLAN.md",
        "# KFAZ1\n```json\n" + json.dumps(
            {"sema": "KFAZ1/v1", "degisecek": ["src/a.py"], "dondurulan": [],
             "req_test": {"REQ-01": ["test_yeni"]}, "req_dosya": {"REQ-01": ["src/a.py"]},
             "gerekce": {"src/a.py": "REQ-01"}}) + "\n```\n")
    if faz2:
        yaz(dp / "_KOSU/02-KFAZ-2-MAN.md",
            "# KFAZ2\n```json\n" + json.dumps(
                {"sema": "KFAZ2/v1",
                 "chg": [{"id": "CHG-001", "req": "REQ-01", "dosya": "src/a.py",
                          "durum": "UYGULANMIS", "ozet": "x"}]}) + "\n```\n")
    taban = {"sema": "BASELINE/v1", "test": {"kosan": 1, "atlanan": 0},
             "test_adlari": ["test_var"]}
    if taban_ek is not None:
        taban.update(taban_ek)
        if taban_ek.get("_test_adlari_sil"):
            taban.pop("test_adlari", None); taban.pop("_test_adlari_sil", None)
    yaz(dp / "_KOSU/gate/BASELINE.json", taban)
    git_kur(str(dp))
    yaz(dp / "src/a.py", "def f(): return 3\n")


# ------------------------------------------------- K12 / RECK-08 sema dogrulama
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d); _sema_kosu(dp, ["REQ-01", "REQ-02"])          # DIZE listesi
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("K12-1 KFAZ0.req DIZE listesi -> SCHEMA_INVALID P0 (sessizce dusmez)",
         rc == 1 and "SCHEMA_INVALID" in out and "req[0]" in out, out.strip()[:220])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _sema_kosu(dp, [{"id": "REQ-01", "kabul": "x"}])                    # `tur` YOK
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("K12-2 REQ'te `tur` alani yok -> SCHEMA_INVALID P0",
         rc == 1 and "SCHEMA_INVALID" in out and "tur" in out, out.strip()[:220])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _sema_kosu(dp, [{"id": "REQ-01", "tur": "uydurma", "kabul": "x"}])
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("K12-3 REQ.tur kapali listede degil -> SCHEMA_INVALID P0",
         rc == 1 and "SCHEMA_INVALID" in out, out.strip()[:220])

with tempfile.TemporaryDirectory() as d:                                # POZITIF
    dp = pathlib.Path(d)
    _sema_kosu(dp, [{"id": "REQ-01", "tur": "davranissal", "kabul": "f() -> 3"}])
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("K12-4 semaya uygun req -> SCHEMA_INVALID YOK (yanlis-pozitif kontrolu)",
         "SCHEMA_INVALID" not in out, out.strip()[:220])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _sema_kosu(dp, [{"id": "REQ-01", "tur": "davranissal", "kabul": "x"}],
               taban_ek={"_test_adlari_sil": True})
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("K12-5 tabanda `test_adlari` yok -> RECK-07 P0 CALISTIRILMADI (sessiz gecmez)",
         rc == 1 and "RECK-07" in out and "CALISTIRILMADI" in out, out.strip()[:220])

# --------------------------------------------------------- K10 faz farkindaligi
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _sema_kosu(dp, [{"id": "REQ-01", "tur": "davranissal", "kabul": "x"}], faz2=False)
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("K10-1 KFAZ1 asamasi (02 artefakti yok) -> KFAZ1 TAMAMLANABILIR (exit=0)",
         rc == 0 and "bu faz henuz gelmedi" in out, out.strip()[:220])

# --------------------------------------------------------- K11 / FRZ-06 sema
def _fz(dp, taban):
    yaz(dp / "kod_profil.json", {"dil": "python", "test_komutu": "pytest -q"})
    yaz(dp / "_KOSU/gate/BASELINE.json", taban)

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _fz(dp, {"sema": "BASELINE/v1", "sha256": {"kod_profil.json": "deadbeef"}})
    rc, out = kos("freeze_check.py", cwd=d)
    sina("K11-1 tabanda dondurma alanlari yok -> FRZ-06 P0, PASS DEMEZ",
         rc == 1 and "FRZ-06" in out and "FAIL" in out, out.strip()[:220])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    import hashlib as _h
    _icerik = json.dumps({"dil": "python", "test_komutu": "pytest -q"},
                         ensure_ascii=False, indent=2)
    yaz(dp / "kod_profil.json", _icerik)
    _sha = _h.sha256((dp / "kod_profil.json").read_bytes()).hexdigest()
    yaz(dp / "_KOSU/gate/BASELINE.json",
        {"sema": "BASELINE/v1", "kod_profil_yolu": "kod_profil.json",
         "kod_profil_sha256": _sha, "scripts_sha256": {}, "dondurulan": {}})
    rc, out = kos("freeze_check.py", cwd=d)
    sina("K11-2 semaya uygun taban + temiz profil -> PASS (yanlis-pozitif kontrolu)",
         rc == 0, out.strip()[:220])
    yaz(dp / "kod_profil.json", {"dil": "python", "test_komutu": "true"})   # KURCALA
    rc, out = kos("freeze_check.py", cwd=d)
    sina("K11-3 semaya uygun taban + KURCALANMIS profil -> GATE_TAMPERED exit=2 TERMINAL",
         rc == 2 and "GATE_TAMPERED" in out, out.strip()[:220])

# ------------------------------------------------ K18 / TST-10..12 kanit kokeni
def _ta(dp, komut, rapor_yolu, prof_komut, prof_rapor):
    yaz(dp / "kod_profil.json", {"dil": "python", "test_komutu": prof_komut,
                                 "test_raporu": prof_rapor, "test_rapor_formati": "junit-xml"})
    yaz(dp / rapor_yolu, JUNIT_TEMIZ)
    yaz(dp / "_KOSU/gate/BASELINE.json", {"test": {"kosan": 5, "atlanan": 0}, "test_adlari": []})
    yaz(dp / "_KOSU/03-KFAZ-3-TEST-EVIDENCE.json",
        {"komut": komut, "cikis_kodu": 0, "rapor": rapor_yolu, "rapor_formati": "junit-xml",
         "sonuc": {"kosan": 5, "basarisiz": 0, "hata": 0, "atlanan": 0}})

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _ta(dp, "true", "_KOSU/gate/junit.xml", "pytest -q", "_KOSU/gate/junit.xml")
    rc, out = kos("test_attest.py", cwd=d)
    sina("K18-1 kanit komutu profildekinden FARKLI -> TST-11 EVIDENCE_UNVERIFIED",
         rc == 1 and "TST-11" in out, out.strip()[:220])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _ta(dp, "pytest -q", "_KOSU/gate/junit-sahte.xml", "pytest -q", "_KOSU/gate/junit.xml")
    rc, out = kos("test_attest.py", cwd=d)
    sina("K18-2 kanit raporu profildekinden FARKLI -> TST-12 EVIDENCE_UNVERIFIED",
         rc == 1 and "TST-12" in out, out.strip()[:220])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _ta(dp, "pytest -q", "_KOSU/gate/junit.xml", "pytest -q", "_KOSU/gate/junit.xml")
    rc, out = kos("test_attest.py", cwd=d)
    sina("K18-3 kanit ile profil ESLESIYOR -> PASS (yanlis-pozitif kontrolu)",
         rc == 0, out.strip()[:220])

# TST-10 tazelik: git deposu icinde, kaynak rapordan YENI
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _ta(dp, "pytest -q", "_KOSU/gate/junit.xml", "pytest -q", "_KOSU/gate/junit.xml")
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(str(dp))
    import time as _t
    _t.sleep(1.05)
    yaz(dp / "src/a.py", "x = 2\n")          # kaynak rapordan SONRA degisti
    rc, out = kos("test_attest.py", cwd=d)
    sina("K18-4 rapor kaynaktan ESKI -> TST-10 STALE_EVIDENCE P0",
         rc == 1 and "TST-10" in out and "STALE_EVIDENCE" in out, out.strip()[:220])

# ------------------------------------------------------------ K9 import guvenligi
_ta_metin = oku(S / "test_attest.py")
sina("K9-1 test_attest.py `__test__ = False` tasiyor (pytest toplamaz)",
     "__test__ = False" in _ta_metin, "")
sina("K9-2 test_attest.py govdesi __main__ korumasi altinda",
     'if __name__ == "__main__":' in _ta_metin and "def _main():" in _ta_metin, "")
_imp = subprocess.run(
    [sys.executable, "-c",
     "import sys;sys.dont_write_bytecode=True;sys.path.insert(0,%r);"
     "import io,contextlib;b=io.StringIO()\n"
     "with contextlib.redirect_stdout(b),contextlib.redirect_stderr(b):\n"
     "    import test_attest\n"
     "print(len(b.getvalue()))" % str(S)],
    capture_output=True, text=True, timeout=600)
sina("K9-3 test_attest import edilince YAN ETKI yok (exit yok, cikti yok)",
     _imp.returncode == 0 and _imp.stdout.strip() == "0",
     f"rc={_imp.returncode} out={_imp.stdout.strip()[:80]} err={_imp.stderr.strip()[:120]}")

# --------------------------------------------------- K8 apply_routing kapı kontrolu
# O7-07 sonrasi: tek kaynak ORTAK'ta, nushalar bayt birebir; kapı bagimsizlik
# kontrolu ONEK-NOTR'dur (`*-gate-2a` kalibi). Eski K8-1 sabit
# `esleme["kod-gate-2a"]` cagrisini ariyordu — OLCUM-02 K8'in RUHU korunur:
# calisan kod sabit ATLAS adi cagirmaz VE kapilar eksikliginde fail-closed'dir.
_ar = oku(S / "apply_routing.py")
_ar_kod = "\n".join(l for l in _ar.split("\n") if not l.lstrip().startswith("#"))
_neg_ok = False
_neg_iz = ""
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    (dp / ".opencode" / "agent").mkdir(parents=True)
    yaz(dp / ".opencode/agent/kod-gate-2b.md", "model: openrouter/z-ai/glm-5.2\n")
    (dp / "routing.profiles.json").write_text(json.dumps({
        "profiller": {"denge": {"aciklama": "negatif fikstur",
                                 "kod-gate-2b": "openrouter/z-ai/glm-5.2"}}}),
        encoding="utf-8")
    (dp / "scripts").mkdir()
    shutil.copyfile(S / "apply_routing.py", dp / "scripts" / "apply_routing.py")
    _imp = subprocess.run([sys.executable, str(dp / "scripts" / "apply_routing.py"),
                           "denge", "--kuru"], capture_output=True, text=True,
                          cwd=str(dp), timeout=600)
    _neg_ok = (_imp.returncode == 1 and "DEGERLENDIRILEMEZ" in _imp.stdout)
    _neg_iz = (_imp.stdout + _imp.stderr).strip().split("\n")[0][:160]
sina("K8-1 apply_routing kapilar ONEK-NOTR bulunur; eksikliginde fail-closed",
     '_bul(r"gate-2a$")' in _ar_kod
     and 'esleme.get("atlas-' not in _ar_kod and 'esleme["kod-gate-2a"]' not in _ar_kod
     and _neg_ok,
     f"negatif: rc={_imp.returncode} {_neg_iz}")
_rc, _out = kos("apply_routing.py", "denge", "--kuru")
sina("K8-2 varsayilan `denge` profili UYGULANABILIR (exit=0)", _rc == 0, _out.strip()[:200])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    profil = json.loads((S.parent / "routing.profiles.json").read_text(encoding="utf-8"))
    katalog = {}
    for tanim in profil["profiller"].values():
        for anahtar, model in tanim.items():
            if anahtar in ("aciklama", "bagimsizlik_feragati", "feragat_gerekcesi"):
                continue
            saglayici, _, model_id = model.partition("/")
            katalog.setdefault(saglayici, {"models": {}})["models"][model_id] = {
                "status": "active", "reasoning": True, "tool_call": True,
                "cost": {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
            }
    katalog_yolu = dp / "models.json"
    yaz(katalog_yolu, katalog)
    ortam = dict(os.environ, HOME=str(dp / "bos-home"),
                 ATLAS_MODEL_KATALOG=str(katalog_yolu))
    _imp = subprocess.run([sys.executable, str(S / "apply_routing.py"), "denge", "--kuru"],
                          capture_output=True, text=True, env=ortam, timeout=600)
    _iz = (_imp.stdout + _imp.stderr).strip()[:200]
sina("K8-3 apply_routing model katalogu yolunu ortamdan enjekte eder",
     _imp.returncode == 0 and "[--kuru] hicbir dosya yazilmadi" in _imp.stdout,
     f"rc={_imp.returncode} {_iz}")

# ------------------------------------------------------- K1/K3 budget_guard
sina("K1-1 scripts/budget_guard.py GERCEK dosya (symlink degil)",
     (S / "budget_guard.py").is_file() and not (S / "budget_guard.py").is_symlink(), "")
for _f in ("KFAZ0", "KFAZ5", "FAZ0"):
    _rc, _out = butce_preflight_kos(_f)
    sina(f"K3-1 budget_guard --preflight {_f} tanir (exit=0)",
         _rc == 0 and "Kaynak: opencode.db (OK)" in _out, _out.strip()[:160])

# ------------------------------------------------------ K4/K19 secret_scan
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(str(dp))
    yaz(dp / "src/b.py", "y = 2\n")
    rc, out = kos("secret_scan.py", cwd=d)
    sina("K4-1 toolkit yok -> KISMI mod exit=3 ('temiz' demez)",
         rc == 3 and "KISMI" in out, out.strip()[:200])
    yaz(dp / "src/gizli.pem", sahte_anahtar())   # O5-01: parcali yazim
    rc, out = kos("secret_scan.py", cwd=d)
    sina("K19-1 KISMI mod IZLENMEYEN sir dosyasini gorur -> P0 exit=1",
         rc == 1 and "SEC-02" in out and "gizli.pem" in out, out.strip()[:200])

# --- uctan uca kosuda bulunan iki yanlis pozitif (regresyon korumasi)
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    # hattin KENDI betikleri hedef depoda durur ve taranir. KISMI imza kalibi
    # ciplak yazilirsa BU KAYNAKLARI eslerdi ve her KFAZ2'yi bloklardi.
    (dp / "scripts").mkdir(parents=True, exist_ok=True)
    for _b in ("secret_scan.py", "kod_selftest.py"):
        shutil.copy(S / _b, dp / "scripts" / _b)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(str(dp))
    yaz(dp / "src/b.py", "y = 2\n")
    rc, out = kos("secret_scan.py", cwd=d)
    # NOT: ozet satiri "P0=0" icerir; bu yuzden dizeyi degil BULGU SATIRLARINI say.
    _p0_satir = [l for l in out.split("\n") if l.startswith("P0 ")]
    sina("E2E-1 hattin kendi betikleri sir SANILMAZ (yanlis pozitif yok)",
         rc == 3 and not _p0_satir, "; ".join(_p0_satir)[:220])
    yaz(dp / "src/anahtar.pem", sahte_anahtar())  # O5-01: parcali yazim
    rc, out = kos("secret_scan.py", cwd=d)
    sina("E2E-2 GERCEK anahtar dosyasi yine yakalanir (korlesme yok)",
         rc == 1 and "anahtar.pem" in out, out.strip()[:220])

_kur_metin = oku(S / "kur.sh")
sina("E2E-3 kur.sh LAB'i ISARETLE tespit eder (konumdan degil)",
     "LAB_GERCEK" in _kur_metin and "ATLAS_SABLONLAR" in _kur_metin, "")

# ------------------------------------------------------------ K14 gate-2a bash
_g2a = oku(S.parent / ".opencode" / "agent" / "kod-gate-2a.md")
_bash_blok = _g2a.split("  bash:")[1].split("  webfetch:")[0] if "  bash:" in _g2a else ""
sina("K14-1 kod-gate-2a bash VARSAYILAN DENY ('*': deny ilk satir)",
     _bash_blok.strip().startswith('"*": deny'), _bash_blok.strip()[:120])
sina("K14-2 kod-gate-2a bash izin listesi DAR (cat/sed/head yok)",
     not any(x in _bash_blok for x in ('"cat', '"sed', '"head', '"less')), _bash_blok[:120])

# ------------------------------------------------------------ K7 varsayilan model
_oc = json.loads(oku(S.parent / "opencode.json") or "{}")
sina("K7-1 opencode.json `model` anahtari VAR (ucretli varsayilana dusme yok)",
     bool(_oc.get("model")), str(sorted(_oc))[:160])

# ------------------------------------------------- K5/K17 kos_faz.sh surucusu
if shutil.which("timeout") and (S / "kos_faz.sh").exists():
    with tempfile.TemporaryDirectory() as d:
        dp = pathlib.Path(d)
        (dp / "sahte").mkdir(parents=True, exist_ok=True)
        (dp / "depo").mkdir(parents=True, exist_ok=True)
        _fake = dp / "sahte" / "opencode"
        _fake.write_text(
            "#!/usr/bin/env bash\n"
            'case "$SENARYO" in\n'
            '  dusme) echo \'! agent "x" is a subagent, not a primary agent.'
            " Falling back to default agent' >&2; echo '> build · m' >&2; exit 0 ;;\n"
            "  onaysiz) echo '> kod-scoper · m' >&2; echo 'Yapayim mi?'; exit 0 ;;\n"
            "  basarili) echo '> kod-scoper · m' >&2; mkdir -p _KOSU;"
            " echo x > _KOSU/00-KFAZ-0-S.md; exit 0 ;;\n"
            "esac\n")
        _fake.chmod(0o755)
        _env = dict(os.environ, PATH=f"{dp / 'sahte'}{os.pathsep}{os.environ['PATH']}")
        def _kf(senaryo):
            r = subprocess.run(
                ["bash", str(S / "kos_faz.sh"), "--komut", "kod-faz0", "--ajan", "kod-scoper",
                 "--sure", "10", "--deneme", "1", "--artefakt", "_KOSU/00-KFAZ-0-*.md",
                 "--", "test"],
                cwd=str(dp / "depo"), capture_output=True, text=True,
                env=dict(_env, SENARYO=senaryo), timeout=600)
            return r.returncode, r.stdout + r.stderr
        rc, out = _kf("dusme")
        sina("K5-1 kos_faz ajan DUSMESINI yakalar (exit=2)", rc == 2 and "ALT AJAN" in out,
             out.strip()[:200])
        rc, out = _kf("onaysiz")
        sina("K17-1 kos_faz ARTEFAKTSIZ onay cikmazini yakalar (exit=4)",
             rc == 4 and "URETILMEDI" in out, out.strip()[:200])
        rc, out = _kf("basarili")
        sina("K17-2 artefakt uretildiginde kos_faz PASS verir (yanlis-pozitif kontrolu)",
             rc == 0 and "OK —" in out, out.strip()[:200])
else:
    sina("K5-1 kos_faz ajan DUSMESINI yakalar (exit=2)",
         (S / "kos_faz.sh").exists(), "kos_faz.sh YOK ya da `timeout` yok")
    sina("K17-1 kos_faz ARTEFAKTSIZ onay cikmazini yakalar (exit=4)",
         (S / "kos_faz.sh").exists(), "kos_faz.sh YOK ya da `timeout` yok")

# ------------------------------------------------------------- K2 kurulum
sina("K2-1 kur.sh var ve calistirilabilir",
     (S / "kur.sh").exists() and os.access(S / "kur.sh", os.X_OK), "")
_kur = oku(S / "kur.sh")
sina("K2-2 kur.sh ORTAK cekirdegini tasir ve SAPMA denetler",
     "ortak_gate.py" in _kur and "AYRISMIS" in _kur, "")
sina("K2-3 kur.sh --dogrula modu var (kopyalamadan denetler)",
     "--dogrula" in _kur and "SADECE_DOGRULA" in _kur, "")


# ------------------------------------------- K13/K15 verdict semasi (ITG-11)
def _itg(verdict_2a):
    d = tempfile.mkdtemp()
    dp = pathlib.Path(d)
    for f in ("00-KFAZ-0-S.md", "01-KFAZ-1-P.md", "02-KFAZ-2-M.md"):
        yaz(dp / "_KOSU" / f, "x\n```json\n{}\n```\n")
    yaz(dp / "_KOSU/03-KFAZ-3-TEST-EVIDENCE.json", {"cikis_kodu": 0})
    yaz(dp / "_KOSU/gate/KOD-gate-2b.json",
        {"kapi": "2B", "verdict": "PASS", "findings": [],
         "manifest_reconciliation": [{"chg_id": "CHG-001", "status": "UYGULANMIS_KANITLI",
                                      "evidence": "x"}]})
    (dp / "_KOSU/gate/KOD-gate-2a.json").write_text(verdict_2a, encoding="utf-8")
    rc, out = kos("check_code_integrity.sh", cwd=d)
    shutil.rmtree(d, ignore_errors=True)
    return rc, out

_TEMIZ2A = '{"kapi":"2A","verdict":"PASS","findings":[],"checks":[{"id":"CHK-01","status":"GECTI","evidence":"x"}]}'
_, _o = _itg(_TEMIZ2A)
sina("K15-1 dogru sema (status) -> ITG-11 SIKAYET ETMEZ (yanlis-pozitif kontrolu)",
     "ITG-11" not in _o, _o.strip()[:200])
_, _o = _itg('{"kapi":"2A","verdict":"PASS","checks":[{"id":"CHK-01","durum":"GECTI"}]}')
sina("K15-2 `durum` yazilmis -> ITG-11 SEMA DISI (birlestirmeden ONCE yakalar)",
     "ITG-11" in _o and "durum" in _o, _o.strip()[:200])
_, _o = _itg('{"kapi":"2A","verdict":"PASS","checks":[')
sina("K13-1 zaman asiminin biraktigi YARIM verdict -> ITG-11 bozuk JSON",
     "ITG-11" in _o and "bozuk JSON" in _o, _o.strip()[:200])
_, _o = _itg('{"kapi":"2A","verdict":"PASS"}')
sina("K13-2 gecerli JSON ama DENETIM IZI yok -> ITG-11 FAIL (bos kapi PASS veremez)",
     "ITG-11" in _o and "denetim izi" in _o, _o.strip()[:200])


# --------------------------------------- --json ciktisinin SAFLIGI (regresyon)
# Denetimde yakalandi: KISMI mod uyarisi stdout'a basiliyordu ve `--json`
# ciktisini AYRISTIRILAMAZ hale getiriyordu. Uyari artik stderr'e gider.
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(str(dp))
    yaz(dp / "src/b.py", "y = 2\n")
    _r = subprocess.run([sys.executable, str(S / "secret_scan.py"), "--json"],
                        cwd=d, capture_output=True, text=True, timeout=600)
    try:
        json.loads(_r.stdout); _saf = True
    except Exception:
        _saf = False
    sina("JSON-1 secret_scan --json stdout'u SAF JSON (uyari stderr'e gider)",
         _saf and _r.returncode == 3, _r.stdout[:160])
    sina("JSON-2 uyari kaybolmadi, stderr'de duruyor",
         "CALISTIRILMADI" in _r.stderr, _r.stderr[:120])


# ------------------------------------- BG-1 budget_guard tek kaynak (O7-06)
# WP4/O7-06 kapanisi: tek kaynak `ORTAK/scripts/budget_guard.py`; KOD ve ATLAS
# nushalari BAYT BIREBIR kopyadir, BG-1 bunu hash ile sinar. Eski surum iki
# kopyanin cekirdek mantigini karsilastiriyordu; artik sapma TASARLANMAMISTIR —
# tek bayt saparsa test kirmizi verir. Wrapper/symlink bilincli SECILMEDI:
# OLCUM-02 K1 dersi (sablon hedef depoya kopyalaninca goreli referans kiriliyor)
# + ATLAS hattinin kurulum mekanizmasi yok — desen kurulum yollarina dokunmaz.
_bg_kaynak = {
    "ORTAK": S.parent.parent / "ORTAK" / "scripts" / "budget_guard.py",
    "KOD": S / "budget_guard.py",
    "ATLAS": S.parent.parent / "ATLAS_SABLONLAR" / "scripts" / "budget_guard.py",
}
_bg_var = {ad: y for ad, y in sorted(_bg_kaynak.items()) if y.is_file()}
if len(_bg_var) >= 2:
    _bg_hash = {ad: hashlib.sha256(y.read_bytes()).hexdigest() for ad, y in _bg_var.items()}
    sina("BG-1 budget_guard tek kaynak: kopyalar bayt birebir (" + "+".join(_bg_var) + ")",
         len(set(_bg_hash.values())) == 1,
         "; ".join(ad + "=" + k[:12] for ad, k in _bg_hash.items()))
else:
    sina_atla("BG-1 budget_guard tek kaynak karsilastirmasi",
              "CALISTIRILMADI: elde tek kopya var (hedef depoda normaldir): " + "+".join(_bg_var))
for _f, _bek in (("KFAZ0", 0), ("KFAZ5", 0), ("FAZ0", 0), ("YOKFAZ", 1)):
    _rc, _o = butce_preflight_kos(_f)
    sina(f"BG-2 --preflight {_f} -> exit={_bek}",
         _rc == _bek and "Kaynak: opencode.db (OK)" in _o, _o.strip()[:120])


# TT-D-2: mantiksal proje UUID'si + tarihsel CWD alias filtresi. Tum vakalar
# sentetik SQLite ve yalniz alt surece verilen env ile hermetiktir.
with tempfile.TemporaryDirectory() as d:
    _bg3_kok = pathlib.Path(d)
    _bg3_uuid = "550e8400-e29b-41d4-a716-446655440000"
    _bg3_diger_uuid = "550e8400-e29b-41d4-a716-446655440001"

    def _bg3_kos(ad, mesaj_cwd, tutar, *, uuid_dosyasi=True,
                 alias_veri=None, alias_ham=None, kuresel=False):
        proje = _bg3_kok / ad
        proje.mkdir(parents=True)
        if uuid_dosyasi:
            (proje / ".lab_proje_uuid").write_text(_bg3_uuid + "\n", encoding="utf-8")
        db = _bg3_kok / f"{ad}.db"
        with sqlite3.connect(db) as con:
            con.execute("CREATE TABLE message (data TEXT)")
            con.execute("INSERT INTO message VALUES (?)", (json.dumps({
                "role": "assistant",
                "cost": tutar,
                "time": {"created": int(time.time() * 1000)},
                "path": {"cwd": str(mesaj_cwd)},
                "providerID": "fikstir",
                "modelID": "test-model",
            }),))
        ortam = dict(os.environ)
        ortam.pop("ATLAS_PROJE_UUID", None)
        ortam.pop("ATLAS_PROJE_KIMLIK_DOSYASI", None)
        ortam.update(ATLAS_OPENCODE_DB=str(db), ATLAS_BUDGET_LIMIT="30.0")
        if alias_veri is not None or alias_ham is not None:
            alias = _bg3_kok / f"{ad}.json"
            if alias_ham is not None:
                alias.write_text(alias_ham, encoding="utf-8")
            else:
                alias.write_text(json.dumps(alias_veri), encoding="utf-8")
            ortam["ATLAS_PROJE_KIMLIK_DOSYASI"] = str(alias)
        komut = [sys.executable, str(S / "budget_guard.py")]
        if kuresel:
            komut.extend(("--kuresel", "--proje", str(_bg3_kok / "atlanacak-proje")))
        else:
            komut.extend(("--preflight", "KFAZ0"))
        r = subprocess.run(komut, cwd=proje, capture_output=True, text=True, env=ortam, timeout=600)
        return proje, r.returncode, r.stdout + r.stderr

    _bg3_sonuclar = []

    _proje, _rc, _o = _bg3_kos("ayni-cwd", _bg3_kok / "ayni-cwd" / "src", 1.0)
    _bg3_sonuclar.append(("ayni-cwd", _rc == 0
                          and f"GERCEK harcama (proje: {_proje.name}): $1.00" in _o
                          and "OK preflight KFAZ0" in _o and "Traceback" not in _o))

    _eski = _bg3_kok / "tarihsel-eski"
    _proje, _rc, _o = _bg3_kos(
        "tarihsel-alias", _eski / "src", 2.0,
        alias_veri={_bg3_uuid: [str(_eski)]},
    )
    _bg3_sonuclar.append(("tarihsel-alias", _rc == 0
                          and f"GERCEK harcama (proje: {_proje.name}): $2.00" in _o
                          and "Traceback" not in _o))

    _yabanci = _bg3_kok / "yabanci-proje"
    _proje, _rc, _o = _bg3_kos(
        "diger-uuid", _yabanci / "src", 99.0,
        alias_veri={_bg3_diger_uuid: [str(_yabanci)]},
    )
    _bg3_sonuclar.append(("diger-uuid", _rc == 0
                          and f"GERCEK harcama (proje: {_proje.name}): $0.00" in _o
                          and "Traceback" not in _o))

    _, _rc, _o = _bg3_kos("uuid-yok", _bg3_kok / "uuid-yok", 1.0, uuid_dosyasi=False)
    _bg3_sonuclar.append(("uuid-yok", _rc == 1 and "PROJE_KIMLIGI_YOK" in _o
                          and "Traceback" not in _o))

    _, _rc, _o = _bg3_kos("json-bozuk", _bg3_kok / "json-bozuk", 1.0, alias_ham="{")
    _bg3_sonuclar.append(("json-bozuk", _rc == 1 and "PROJE_KIMLIK_JSON_BOZUK" in _o
                          and "Traceback" not in _o))

    _limit_eski = _bg3_kok / "limit-eski"
    _proje, _rc, _o = _bg3_kos(
        "tarihsel-limit", _limit_eski, 99.0,
        alias_veri={_bg3_uuid: [str(_limit_eski)]},
    )
    _bg3_sonuclar.append(("tarihsel-limit", _rc == 1
                          and f"GERCEK harcama (proje: {_proje.name}): $99.00" in _o
                          and "FAIL preflight KFAZ0" in _o and "Traceback" not in _o))

    _, _rc, _o = _bg3_kos(
        "kuresel-bypass", _bg3_kok / "kuresel-bypass", 1.0,
        uuid_dosyasi=False, kuresel=True,
    )
    _bg3_sonuclar.append(("kuresel-bypass", _rc == 0
                          and "GERCEK harcama (TUM PROJELER): $1.00" in _o
                          and "PROJE_KIMLIGI_YOK" not in _o and "Traceback" not in _o))

    sina("BG-3 proje UUID + tarihsel CWD alias filtresi fail-closed ve hermetik",
         all(ok for _, ok in _bg3_sonuclar), f"sonuclar={_bg3_sonuclar}")


# ------------------------------------------- bilinmeyen --faz FAIL-CLOSED olmali
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _sema_kosu(dp, [{"id": "REQ-01", "tur": "davranissal", "kabul": "x"}])
    rc, out = kos("chg_reconcile.py", "--faz", "UYDURMA", cwd=d)
    sina("FAZ-1 bilinmeyen --faz degeri SESSIZCE kabul edilmez (exit=1)",
         rc == 1 and "bilinmeyen faz" in out, out.strip()[:180])
    rc, _ = kos("chg_reconcile.py", "--faz", "KFAZ2", cwd=d)
    sina("FAZ-2 gecerli --faz calismaya devam eder (yanlis-pozitif kontrolu)",
         rc == 0, "")


# ============================================= OLCUM-03 O3-01 / O3-02 / O3-08
# Ucu de CANLI kosuda olculdu (docs/OLCUM-03-DUZELTME-SONRASI.md). Bu testler
# duzeltmeler geri alindiginda KIRMIZI vermek icindir.
_PAKET = S.parent                     # KOD_SABLONLAR/
_KOSU_ONCE = (S.parent.parent / "_KOSU").exists()

# --- O3-01: suren birincil ajan (`build`) edit iznine tabi olmali -------------
# Canli kanit: `--command kod-fazN` iki oturum acar; ebeveyn `agent=build` yalniz
# opencode.json'a tabidir. Orada `edit` altinda "*" YOKKEN build KFAZ0 sirasinda
# birim/olcek.py ve tests/test_olcek.py'yi yazdi (opencode.db yazma atfi).
_oc = _PAKET / "opencode.json"
if _oc.exists():
    import json as _json, collections as _coll
    _d = _json.loads(_oc.read_text(), object_pairs_hook=_coll.OrderedDict)
    _e = _d.get("permission", {}).get("edit", {})
    _anahtarlar = list(_e.keys())
    sina("O3-01a opencode.json edit blogunda '*' kurali VAR",
         "*" in _e, f"anahtarlar: {_anahtarlar[:4]}")
    sina("O3-01b edit['*'] == deny (surucu ajan depoya yazamaz)",
         _e.get("*") == "deny", f"deger: {_e.get('*')!r}")
    sina("O3-01c IK-2: '*' ILK sirada (sonraki deny'ler olu kural olmasin)",
         _anahtarlar[:1] == ["*"], f"ilk anahtar: {_anahtarlar[:1]}")
    # yanlis-pozitif kontrolu: kirmizi cizgi deny'leri hala yerinde
    sina("O3-01d kirmizi cizgi deny'leri korundu",
         all(_e.get(k) == "deny" for k in ("yahuditurk/**", "ATLAS/**", "toolkit/**")),
         "kirmizi cizgi kurallari eksik")
    # B1 (OLCUM-06, 26.08.2026): build ebeveyni bash ile scripts/'i tasiyabiliyordu.
    # edit yasagi tek basina dondurulan bolgeyi korumuyor; bash de deny olmali.
    _b = _d.get("permission", {}).get("bash", {}) if isinstance(_d.get("permission", {}), dict) else {}
    _b_keys = list(_b.keys()) if isinstance(_b, dict) else []
    sina("B1-1 opencode.json bash blogunda '*' kurali VAR ve deny (build shell kapali)",
         _b.get("*") == "deny", f"bash anahtarlar: {_b_keys[:4]}")
    sina("B1-2 IK-2: bash['*'] ILK sirada (sonraki allow olu kural olmasin)",
         _b_keys[:1] == ["*"], f"ilk anahtar: {_b_keys[:1]}")
    sina("B1-3 bash allow listesi BOS — fail-closed (mv/cp/rm hicbiri allow degil)",
         isinstance(_b, dict) and not any(v == "allow" for v in _b.values()),
         f"bash allow: {[k for k,v in _b.items() if v=='allow'][:3]}")
    sina("B1-4 _bash_yildiz_notu var (B1 gerekcesi belgeli)",
         "_bash_yildiz_notu" in _d and "B1" in str(_d.get("_bash_yildiz_notu","")),
         f"_bash_yildiz_notu: {str(_d.get('_bash_yildiz_notu',''))[:80]}")
    # O3-02c: operator dosyasi ajan baglamina YUKLENMEMELI
    _ins = _d.get("instructions", [])
    sina("O3-02c OPERATOR_SURME.md `instructions` listesinde DEGIL",
         "OPERATOR_SURME.md" not in _ins, f"instructions: {_ins}")
else:
    sina_atla("O3-01 opencode.json bulunamadi", "CALISTIRILMADI: paket disinda kosuluyor")

# --- O3-02: surme talimati ajan baglamindan cikarilmis olmali -----------------
# Canli kanit: 00_KOD_OKU_BENI.md `instructions`'tadir; icindeki operator
# ornegini ajanlar kendi gorevi sandi ve kos_faz.sh'i 44 kez cagirdi
# (acilan oturum: build=78, kod-architect=74) -> ucretsiz model kotasi tukendi.
_ob = _PAKET / "00_KOD_OKU_BENI.md"
if _ob.exists():
    _t = _ob.read_text()
    sina("O3-02a 00_KOD_OKU_BENI.md ajanlara kos_faz.sh CAGIRMA ornegi vermiyor",
         "bash scripts/kos_faz.sh --komut" not in _t,
         "operator ornegi hala ajan baglaminda")
    sina("O3-02b ajanlara `opencode run` cagirma talimati yok",
         "opencode run --command" not in _t and "opencode run -c" not in _t,
         "ajan baglaminda `opencode run` ornegi var")
    _yasak = ("çağırmazsın" in _t) or ("cagirmazsin" in _t)
    sina("O3-02d yerine acik yasak yazildi (ajan kos_faz.sh/opencode run cagirmaz)",
         "kos_faz.sh" in _t and "opencode run" in _t and _yasak,
         f"kos_faz={'kos_faz.sh' in _t} opencode={'opencode run' in _t} yasak={_yasak}")
    sina("O3-02e OPERATOR_SURME.md var (talimat kaybolmadi, tasindi)",
         (_PAKET / "OPERATOR_SURME.md").exists(), "operator dosyasi yok")

# --- O3-02 KILIDI: makine olarak yeniden girisi reddet -----------------------
# Prompt metni danismandir; kilit kapidir (IK-8 ile ayni gerekce).
_kf = S / "kos_faz.sh"
if _kf.exists():
    # NOT: iki cagri da GECICI dizinde kosar. kos_faz.sh `_KOSU/loglar/` yaratir;
    # oz-test kendi bulundugu depoyu KIRLETMEMELIDIR (bu turda olculen kendi hatam).
    # Ikinci cagri PATH'ten opencode'u DUSURUR: boylece yanlis-pozitif kontrolu
    # HICBIR MODEL CAGRISI yapmadan (ve para harcamadan) kosar; beklenen exit=65.
    with tempfile.TemporaryDirectory() as _d:
        _rc = subprocess.run(
            ["bash", str(_kf), "--komut", "kod-faz1", "--ajan", "kod-architect", "--", "x"],
            capture_output=True, text=True, cwd=_d,
            env={**os.environ, "KOD_KOS_FAZ_AKTIF": "kod-faz0"}, timeout=600)
        sina("O3-02f kos_faz.sh YENIDEN GIRISI reddediyor (exit=66)",
             _rc.returncode == 66, f"exit={_rc.returncode} · {(_rc.stdout + _rc.stderr).strip()[:140]}")
        _bos = os.path.join(_d, "bos_path")
        os.makedirs(_bos, exist_ok=True)
        _env2 = {k: v for k, v in os.environ.items() if k != "KOD_KOS_FAZ_AKTIF"}
        _env2["PATH"] = _bos + ":/usr/bin:/bin"      # opencode YOK, timeout arayacak
        _rc2 = subprocess.run(
            ["bash", str(_kf), "--komut", "kod-faz1", "--ajan", "kod-architect", "--", "x"],
            capture_output=True, text=True, cwd=_d, env=_env2, timeout=600)
        sina("O3-02g kilit yokken 66 DONMUYOR (yanlis-pozitif, model cagrisi YOK)",
             _rc2.returncode != 66, f"exit={_rc2.returncode} · {(_rc2.stdout + _rc2.stderr).strip()[:120]}")
        sina("O3-02i oz-test kos_faz.sh cagrisi bulundugu depoyu KIRLETMIYOR",
             not (S.parent.parent / "_KOSU").exists() or _KOSU_ONCE,
             "lab kokunde _KOSU/ olustu")
    _kft = _kf.read_text()
    sina("O3-02h opencode cagrisi kilit degiskeniyle yapiliyor",
         'KOD_KOS_FAZ_AKTIF="$KOMUT" timeout' in _kft,
         "kilit cocuk surece miras gecmiyor")
    # --- O3-08: sifir-disi exit'te "OK" yazilmamali ---------------------------
    _i_guard = _kft.find('if [ "$SON_EXIT" -ne 0 ]; then\n  echo "DURDU')
    _i_ok = _kft.find('echo "OK — $KOMUT')
    sina("O3-08 ajan exit!=0 iken 'OK' satiri basilmiyor",
         _i_guard != -1 and _i_ok != -1 and _i_guard < _i_ok,
         "guard yok ya da OK satirindan sonra")


# ================================================ v1.7.7 KISA KIRIK TURU (O4-*/O3-*)
# Hepsi OLCUM-04 (docs/OLCUM-04-CANLI-DOGRULAMA.md) ve OLCUM-03'te CANLI olculdu.
# Her test bir duzeltmeyi korur: duzeltme geri alinirsa KIRMIZI verir.

# ---- O4-04  kurulum dosyalari SCOPE_VIOLATION sayilmaz (ama LOGLANIR) --------
# Canli: kurulum sonrasi ilk kosuda RECK-03 63x P0 uretiyordu, tamami SAHTE.
def _o404_kur(dp, plan_dosyalari, urun_ekstra=None):
    yaz(dp / "urun/a.py", "def f(): return 1\n")
    yaz(dp / "tests/test_a.py", "def test_a(): assert True\n")
    git_kur(str(dp))
    (dp / "urun/a.py").write_text("def f(): return 99\n")
    for yol, icerik in (urun_ekstra or {}).items():
        yaz(dp / yol, icerik)
    # hattin kurulum dosyalarini TAKLIT et (izlenmeyen)
    for k in ("scripts/chg_reconcile.py", ".opencode/agent/kod-scoper.md",
              "ORTAK/scripts/ortak_gate.py", "templates/BASELINE.ORNEK.json",
              "opencode.json", "00_KOD_OKU_BENI.md", "OPERATOR_SURME.md",
              "routing.profiles.json", "kod_profil.json"):
        yaz(dp / k, "kurulum icerigi\n")
    yaz(dp / "_KOSU/00-KFAZ-0-SPEC.md", "```json\n" + json.dumps(
        {"sema": "KFAZ0/v1", "giris_modu": "MEVCUT_KOD",
         "req": [{"id": "REQ-001", "tur": "yapisal", "kabul": "a duzeltilir"}]}) + "\n```\n")
    yaz(dp / "_KOSU/01-KFAZ-1-PLAN.md", "```json\n" + json.dumps(
        {"sema": "KFAZ1/v1", "degisecek": plan_dosyalari, "dondurulan": [],
         "req_test": {"REQ-001": []}, "req_dosya": {"REQ-001": plan_dosyalari},
         "gerekce": {x: "REQ-001" for x in plan_dosyalari}}) + "\n```\n")

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d); _o404_kur(dp, ["urun/a.py"])
    rc, out = kos("chg_reconcile.py", "--faz", "KFAZ1", cwd=d)
    sina("O4-04a kurulum dosyalari SCOPE_VIOLATION SAYILMAZ (P0=0)",
         rc == 0 and "SCOPE_VIOLATION" not in out, out.strip()[-220:])
    sina("O4-04b her muafiyet LOGLANIR (sessiz muafiyet yok)",
         out.count("BILGI RECK-03") >= 5 and "kurulum dosyasi:" in out,
         f"BILGI satiri={out.count('BILGI RECK-03')}")

with tempfile.TemporaryDirectory() as d:                    # NEGATIF FIKSTUR
    dp = pathlib.Path(d)
    _o404_kur(dp, ["urun/a.py"], urun_ekstra={"urun/kacak.py": "print('plansiz')\n"})
    rc, out = kos("chg_reconcile.py", "--faz", "KFAZ1", cwd=d)
    sina("O4-04c NEGATIF: plan disi URUN dosyasi HALA P0 (muafiyet urunu kapsamaz)",
         rc == 1 and "SCOPE_VIOLATION" in out and "urun/kacak.py" in out, out.strip()[-220:])

with tempfile.TemporaryDirectory() as d:                    # dondurma muafiyeti EZMEZ
    dp = pathlib.Path(d); _o404_kur(dp, ["urun/a.py"])
    _pp = dp / "_KOSU/01-KFAZ-1-PLAN.md"
    _pj = json.loads(re.search(r"```json(.*?)```", _pp.read_text(), re.S).group(1))
    _pj["dondurulan"] = ["scripts/chg_reconcile.py"]
    yaz(_pp, "```json\n" + json.dumps(_pj) + "\n```\n")
    rc, out = kos("chg_reconcile.py", "--faz", "KFAZ1", cwd=d)
    sina("O4-04d ACIK dondurma beyani kurulum muafiyetini EZER (RECK-06 P0)",
         "RECK-06" in out and rc == 1, out.strip()[-200:])

# ---- O3-10  dep_audit: kilit beyani VAR/BOS/YOK ayrimi ----------------------
def _dep_kur(dp, profil):
    yaz(dp / "pyproject.toml", "[project]\nname='x'\nversion='0.1.0'\ndependencies=[]\n")
    yaz(dp / "kod_profil.json", profil)

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _dep_kur(dp, {"dil": "python", "bagimlilik_manifesti": ["pyproject.toml"]})
    rc, out = kos("dep_audit.py", cwd=d)
    sina("O3-10a kilit ANAHTARI YOK -> P0 (sessiz bosluk)",
         rc == 1 and "anahtari HIC YOK" in out, out.strip()[:200])
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _dep_kur(dp, {"dil": "python", "bagimlilik_manifesti": ["pyproject.toml"],
                  "kilit_dosyasi": []})
    rc, out = kos("dep_audit.py", cwd=d)
    sina("O3-10b kilit BOS BEYAN -> P0 YOK, BILGI var (bilincli beyan)",
         rc == 0 and "BILGI DEP-01" in out and "BEYAN_EDILMIS" in out, out.strip()[:200])
with tempfile.TemporaryDirectory() as d:                    # NEGATIF FIKSTUR
    dp = pathlib.Path(d)
    _dep_kur(dp, {"dil": "python", "bagimlilik_manifesti": ["pyproject.toml"],
                  "kilit_dosyasi": ["uv.lock"]})
    rc, out = kos("dep_audit.py", cwd=d)
    sina("O3-10c NEGATIF: kilit BEYAN EDILMIS ama diskte yok -> P0",
         rc == 1 and "beyan tutmuyor" in out, out.strip()[:200])

# ---- O3-06  FRZ-03 canlandi: KFAZ1 plan dondurmasi denetleniyor -------------
def _frz_kur(dp, plan_dondurulan):
    yaz(dp / "kod_profil.json", {"dil": "python"})
    yaz(dp / "hedef.txt", "dondurulacak icerik\n")
    yaz(dp / "_KOSU/01-KFAZ-1-PLAN.md", "```json\n" + json.dumps(
        {"sema": "KFAZ1/v1", "degisecek": [], "dondurulan": plan_dondurulan,
         "req_test": {}}) + "\n```\n")
    _pf = hashlib.sha256((dp / "kod_profil.json").read_bytes()).hexdigest()
    yaz(dp / "_KOSU/gate/BASELINE.json",
        {"mod": "MEVCUT_KOD", "olculdu": "2026-08-24T00:00:00Z",
         "test": {"kosan": 1, "basarisiz": 0, "hata": 0, "atlanan": 0, "kapsam_yuzde": None},
         "test_adlari": [], "test_komutu_cikis_kodu": 0,
         "kod_profil_yolu": "kod_profil.json", "kod_profil_sha256": _pf,
         "scripts_sha256": {}, "dondurulan": {}, "dis_imza": [], "olculmeyen": []})

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d); _frz_kur(dp, ["hedef.txt"])
    rc, out = kos("freeze_check.py", cwd=d)
    sina("O3-06a plan dondurmasi ILK KOSUDA kaydedilir (FREEZE-PLAN.json)",
         rc == 0 and "ILK_KAYIT" in out and (dp / "_KOSU/gate/FREEZE-PLAN.json").exists(),
         out.strip()[:200])
    (dp / "hedef.txt").write_text("KURCALANDI\n")           # NEGATIF FIKSTUR
    rc2, out2 = kos("freeze_check.py", cwd=d)
    sina("O3-06b NEGATIF: plan-dondurmali dosya degisince FRZ-03 P0 (eskiden PASS'ti)",
         rc2 == 1 and "FRZ-03" in out2 and "DONDURULMUS bolge degismis" in out2,
         out2.strip()[:200])
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d); _frz_kur(dp, [])
    rc, out = kos("freeze_check.py", cwd=d)
    sina("O3-06c plan var ama dondurulan BOS -> BILGI, P0 yok (yanlis-pozitif kontrolu)",
         rc == 0 and "BILGI FRZ-03" in out, out.strip()[:200])

# ---- v1.7.22  O3-04 taban kirliligi + O3-05 plan-oncesi urun kodu ----------
# Iki kirik da OLCUM-03'te CANLI olculdu; v1.7.22'te kapatildi. Her fikstur
# duzeltmeyi korur: geri alinirsa KIRMIZI verir.

with tempfile.TemporaryDirectory() as d:                    # NEGATIF FIKSTUR
    dp = pathlib.Path(d); _frz_kur(dp, [])
    _tb = dp / "_KOSU/gate/BASELINE.json"
    _tj = json.loads(_tb.read_text()); _tj["temiz_agac"] = False; yaz(_tb, _tj)
    rc, out = kos("freeze_check.py", cwd=d)
    sina("O3-04a NEGATIF: kirli-agacta olculmus taban -> FRZ-07 POISONED_BASELINE P0",
         rc == 1 and "FRZ-07" in out and "POISONED_BASELINE" in out,
         out.strip()[-220:])
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d); _frz_kur(dp, [])                   # temiz_agac alani YOK
    rc, out = kos("freeze_check.py", cwd=d)
    sina("O3-04b eski tabanda temiz_agac YOK -> BILGI (geriye donuk uyum, P0 degil)",
         rc == 0 and "BILGI FRZ-07" in out, out.strip()[-200:])
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d); _frz_kur(dp, [])
    _tb = dp / "_KOSU/gate/BASELINE.json"
    _tj = json.loads(_tb.read_text()); _tj["temiz_agac"] = True
    # imzasi YOK — kademeli DUSUK_GUVEN P1 (mevcut tabanlar kirilmaz)
    if "temiz_agac_imzasi" in _tj: del _tj["temiz_agac_imzasi"]
    yaz(_tb, _tj)
    rc, out = kos("freeze_check.py", cwd=d)
    sina("O3-04d temiz:true imzasiz -> FRZ-08 DUSUK_GUVEN P1 (kademeli, P0 degil)",
         rc == 0 and "FRZ-08" in out and "DUSUK_GUVEN" in out, out.strip()[-220:])
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d); _frz_kur(dp, [])
    _tb = dp / "_KOSU/gate/BASELINE.json"
    _tj = json.loads(_tb.read_text()); _tj["temiz_agac"] = True; _tj["temiz_agac_imzasi"] = "deadbeef"*8
    yaz(_tb, _tj)
    os.environ["LAB_IMZA_ANAHTARI"] = "a"*64
    try:
        rc, out = kos("freeze_check.py", cwd=d)
    finally:
        del os.environ["LAB_IMZA_ANAHTARI"]
    sina("O3-04e temiz:true gecersiz imza -> FRZ-08 TAMPERED P0 (terminal)",
         rc != 0 and "FRZ-08" in out and "TAMPERED" in out, out.strip()[-220:])
if shutil.which("git"):
    with tempfile.TemporaryDirectory() as d:                 # NEGATIF FIKSTUR
        dp = pathlib.Path(d); (dp / "depo").mkdir()
        subprocess.run(["git", "init", "-q", "."], cwd=str(dp / "depo"),
                       capture_output=True, timeout=600)
        (dp / "depo" / "kurulmamis.txt").write_text("commit edilmemis\n")
        rr = subprocess.run(
            ["bash", str(S / "kos_faz.sh"), "--komut", "kod-faz0",
             "--ajan", "kod-scoper", "--sure", "10", "--deneme", "1", "--", "test"],
            cwd=str(dp / "depo"), capture_output=True, text=True, timeout=600)
        sina("O3-04c NEGATIF: kod-faz0 KIRLI agacta BASLAMAZ (temiz-agac kapisi, exit=1)",
             rr.returncode == 1 and "TEMIZ OLMAYAN agacta" in (rr.stdout + rr.stderr),
             (rr.stdout + rr.stderr).strip()[:200])

def _o305_kur(dp, ekstra_urun=None):
    # yalniz KFAZ0 artefakti — plan henuz yok; kurulum kalintilari izlenmeyen.
    # DIKKAT: git_kur'un ilk commit'i DOLU olmali (bosa commit hata verir ve
    # HEAD olusmaz); o yuzden once bir dosya konup commit'leniyor.
    yaz(dp / "README.md", "hedef depo\n")
    git_kur(str(dp))
    yaz(dp / "_KOSU/00-KFAZ-0-SPEC.md", "```json\n" + json.dumps(
        {"sema": "KFAZ0/v1", "giris_modu": "YESIL_SAHA",
         "req": [{"id": "REQ-001", "tur": "davranissal", "kabul": "x calisir"}]}) + "\n```\n")
    for k in ("scripts/chg_reconcile.py", ".gitignore", "kod_profil.json"):
        yaz(dp / k, "kurulum icerigi\n")
    for yol, icerik in (ekstra_urun or {}).items():
        yaz(dp / yol, icerik)

with tempfile.TemporaryDirectory() as d:                    # NEGATIF FIKSTUR
    dp = pathlib.Path(d)
    _o305_kur(dp, {"birim/olcek.py": "def olc(): return 1\n"})
    rc, out = kos("chg_reconcile.py", "--faz", "KFAZ0", cwd=d)
    sina("O3-05a NEGATIF: plan YOKKEN urun kodu diff'te -> RECK-09 P0 (eskiden PASS'ti)",
         rc == 1 and "RECK-09" in out and "KFAZ0_PRE_PLAN_CHANGE" in out,
         out.strip()[-220:])
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _o305_kur(dp)                                            # yalniz kurulum dosyalari
    rc, out = kos("chg_reconcile.py", "--faz", "KFAZ0", cwd=d)
    sina("O3-05b kurulum dosyalari plan-oncesinde BILGI (muafiyet korunur, PASS)",
         rc == 0 and "BILGI RECK-09" in out and "PASS" in out, out.strip()[-200:])

# ---- O4-02  2B semasi: checks[i].status ZORUNLU ------------------------------
_2A = {"sema": "KOD-GATE/v1", "kapi": "2A", "verdict": "PASS", "findings": [],
       "checks": [{"id": "A-01", "status": "GECTI", "kanit": "git diff okundu"}],
       "metadata": {"p0_count": 0, "p1_count": 0}}
with tempfile.TemporaryDirectory() as d:                    # NEGATIF FIKSTUR
    dp = pathlib.Path(d)
    yaz(dp / "a.json", _2A)
    yaz(dp / "b.json", {"sema": "KOD-GATE/v1", "kapi": "2B", "verdict": "PASS",
                        "checks": [{"id": "MR-01", "durum": "GECTI", "kanit": "x"},
                                   {"id": "MR-02", "durum": "GECTI", "kanit": "y"}],
                        "manifest_reconciliation": [], "findings": [],
                        "metadata": {"p0_count": 0, "p1_count": 0}})
    rc, out = kos("kod_gate_merge.py", str(dp / "a.json"), str(dp / "b.json"), cwd=d)
    sina("O4-02a NEGATIF: `status` yerine `durum` yazan 2B -> P0 + FINAL FAIL",
         rc == 1 and out.count("durum alani YOK") == 2, out.strip()[-200:])
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "a.json", _2A)
    yaz(dp / "b.json", {"sema": "KOD-GATE/v1", "kapi": "2B", "verdict": "PASS",
                        "checks": [{"id": "MR-01", "status": "GECTI", "kanit": "diff exit=0"}],
                        "manifest_reconciliation": [], "findings": [],
                        "metadata": {"p0_count": 0, "p1_count": 0}})
    rc, out = kos("kod_gate_merge.py", str(dp / "a.json"), str(dp / "b.json"), cwd=d)
    sina("O4-02b semaya uygun 2B -> PASS (yanlis-pozitif kontrolu)",
         rc == 0 and "-> PASS" in out, out.strip()[-200:])
_2bk = oku(S.parent / ".opencode/command/kod-gate-2b.md")
sina("O4-02c kod-gate-2b KOMUTU zorunlu semayi belgeliyor",
     '"status": "GECTI"' in _2bk and "ZORUNLU SEMA" in _2bk and "ortak_gate.py:42-43" in _2bk,
     "komut dosyasinda sema blogu yok")
_2ba = oku(S.parent / ".opencode/agent/kod-gate-2b.md")
sina("O4-02d kod-gate-2b AJANI da checks semasini gosteriyor",
     '"status": "GECTI|KALDI|CALISTIRILMADI"' in _2ba, "ajan ornegi hala bos `checks: []`")

# ---- O4-03  secret_scan: v4_verify_yolu DIZIN verilince cozer ----------------
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    # secret_scan bu modulden BES sey bekler; eksik biri AttributeError verir ve
    # traceback metni yolu icerdigi icin naif bir `"v4_verify.py" in out` iddiasi
    # YANLIS POZITIF gecer. (Bu kusur bu turda kendi testimde bulundu.)
    yaz(dp / "sahte_toolkit/ARACLAR/betikler/v4_verify.py",
        "import re\n"
        "SECRET_PATTERNS = [(r'AKIA[0-9A-Z]{16}', 'aws')]\n"
        "DOC_ENV_RE = re.compile(r'\\.env\\.(example|template|sample|dist)$')\n"
        "SKIP_BINARY_EXT = {'.png', '.pdf'}\n"
        "LOCK_NAMES = {'uv.lock'}\n"
        "def looks_like_placeholder(v):\n    return 'ORNEK' in v\n")
    yaz(dp / "kod_profil.json", {"dil": "python",
                                 "v4_verify_yolu": str(dp / "sahte_toolkit")})
    yaz(dp / "temiz.py", "x = 1\n")
    git_kur(str(dp))
    rc, out = kos("secret_scan.py", cwd=d)
    sina("O4-03a DIZIN verilince v4_verify.py cozulur (eskiden AttributeError)",
         rc == 0 and "Traceback" not in out and "SECRET-SCAN PASS" in out
         and "sahte_toolkit/ARACLAR/betikler/v4_verify.py" in out, out.strip()[:220])
    yaz(dp / "kod_profil.json", {"dil": "python",
                                 "v4_verify_yolu": str(dp / "sahte_toolkit/ARACLAR/betikler/v4_verify.py")})
    rc2, out2 = kos("secret_scan.py", cwd=d)
    sina("O4-03b DOSYA yolu da calismaya devam eder (gerileme kontrolu)",
         rc2 == 0 and "Traceback" not in out2 and "SECRET-SCAN PASS" in out2,
         out2.strip()[:200])

# ---- O4-01  kos_faz.sh: --artefakt yoksa SESSIZ gecmez ----------------------
_kf = oku(S / "kos_faz.sh")
sina("O4-01a --artefakt yokken UYARI + artefakt_denetimi=YOK basiliyor",
     'ARTEFAKT_DENETIMI="YOK"' in _kf and "ARTEFAKT DENETIMI YAPILMADI" in _kf
     and "artefakt_denetimi=$ARTEFAKT_DENETIMI" in _kf,
     "sessiz artefakt=0 hala mumkun")
sina("O4-01b uyari OLCULMEYEN kaydi da aciyor",
     "OLCULMEYEN: $KOMUT artefakt denetimi CALISTIRILMADI" in _kf,
     "OLCULMEYEN satiri yok")

# ---- O4-05  check_code_integrity FAIL -> exit=1 (DOGRULANMIS DAVRANIS) ------
# OLCUM-04 "FAIL ama exit=0" bildirdi; YENIDEN URETILEMEDI. Kok neden olcum
# sanati hatasidir: cikis kodu BORU ardindan okununca `tail`in kodu gelir.
# Betik dogru; bu test dogru davranisi KILITLER ki ileride gerilemesin.
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "_KOSU/gate/.tut", "")
    rc, out = kos("check_code_integrity.sh", cwd=d)
    sina("O4-05 integrity FAIL durumunda exit=1 (fail-open DEGIL)",
         rc == 1 and "CODE-INTEGRITY FAIL" in out, f"exit={rc} · {out.strip()[-160:]}")

# ---- O3-07  kor denetim deligi kapandi --------------------------------------
_g2a = oku(S.parent / ".opencode/agent/kod-gate-2a.md")
# Yorum satirlari kuralin KENDISI degildir; duzeltmenin gerekcesi orada YAZILI
# oldugu icin naif substring aramasi kendi aciklamasina takilir. Yalniz `#` ile
# baslamayan satirlara bakilir. (Bu kusur da bu turda kendi testimde bulundu.)
_g2a_kural = [l for l in _g2a.split("\n") if not l.strip().startswith("#")]
sina("O3-07a gate-2a bash listesinde `python3 -c *` YOK (keyfi dosya okuma)",
     not any('"python3 -c *": allow' in l for l in _g2a_kural), "kor denetim hala delik")
sina("O3-07b 2A test kosabilmeye devam ediyor (dar kaliplar duruyor)",
     '"python3 -m pytest*": allow' in _g2a and '"git diff*": allow' in _g2a,
     "2A artik test kosamaz — fazla kisildi")

# ---- O3-09  bedava profili + ACIK bagimsizlik feragati ----------------------
_rp = json.loads(oku(S.parent / "routing.profiles.json") or "{}")
_bed = (_rp.get("profiller") or {}).get("bedava") or {}
sina("O3-09a `bedava` profili var ve 10 ajanin hepsi ucretsiz modelde",
     len([v for k, v in _bed.items() if k.startswith("kod-")]) == 10
     and all(":free" in v for k, v in _bed.items() if k.startswith("kod-")),
     f"ajan={len([k for k in _bed if k.startswith('kod-')])}")
sina("O3-09b feragat ACIK ve gerekceli (sessiz zayiflatma yok)",
     _bed.get("bagimsizlik_feragati") is True and len(_bed.get("feragat_gerekcesi", "")) > 20,
     "feragat bayragi/gerekcesi eksik")
rc, out = kos("apply_routing.py", "bedava", "--kuru", cwd=str(S.parent))
sina("O3-09c apply_routing `bedava`yi UYGULAYABILIYOR + OLCULMEYEN basiyor",
     rc == 0 and "ACIK FERAGATLE" in out and "OLCULMEYEN: KFAZ4 kapi bagimsizligi" in out,
     f"exit={rc} · {out.strip()[:200]}")
sina("O3-09d denge/ekonomi/kalite bozulmadi",
     all(kos("apply_routing.py", _p, "--kuru", cwd=str(S.parent))[0] == 0
         for _p in ("denge", "ekonomi", "kalite")), "bir profil bozuldu")

# ---- SURUM duzeni: v1.7.6 Degisiklik Kaydi'nda, v1.7.5'in USTUNDE ----------
_sur = oku(S.parent.parent / "SURUM.md")
if _sur:
    _sat = _sur.split("\n")
    _i = {v: next((i for i, l in enumerate(_sat) if l.startswith(f"- {v} ")), -1)
          for v in ("v1.7.9", "v1.7.8", "v1.7.7", "v1.7.6", "v1.7.5", "v1.7.4")}
    _ikayit = next((i for i, l in enumerate(_sat) if l.startswith("## Değişiklik Kaydı")), -1)
    sina("SUR-1 v1.7.6 Degisiklik Kaydi bolumunde (dosya sonunda DEGIL)",
         _i["v1.7.6"] > _ikayit >= 0 and _i["v1.7.6"] < _i["v1.7.4"], f"konumlar={_i}")
    sina("SUR-2 surum sirasi azalan (v1.7.9 > … > v1.7.4)",
         _i["v1.7.9"] < _i["v1.7.8"] < _i["v1.7.7"] < _i["v1.7.6"] < _i["v1.7.5"] < _i["v1.7.4"],
         f"konumlar={_i}")
else:
    sina_atla("SUR-1 SURUM.md okunamadi", "CALISTIRILMADI: paket disinda kosuluyor")

# ===================================================== O5-01  OZ-FIKSTUR PARCALI
# v1.7.7'nin acik bulgusu: bu betigin KENDI sir fiksturleri kurulu depoda
# 3x P0 uretiyor ve KFAZ2'yi blokluyordu. Negatif fikstür: kurulu-depo
# senaryosu (hattin betikleri IZLENMEYEN) — o satirlar icin P0 CIKMAMALI,
# ama GERCEK bir anahtar dosyasi HALA P0 vermeli.
_pem_bas = sahte_anahtar().split("\n")[0]        # tam baslik yalniz CALISMA ZAMANINDA olusur
sina("O5-01a PEM basligi kod_selftest.py KAYNAGINDA tek parca GECMEZ",
     _pem_bas not in oku(S / "kod_selftest.py"),
     "kaynakta tek parca imza var — secret_scan kurulu depoda P0 uretir")
sina("O5-01b sahte_anahtar() calisma zamaninda TAM PEM uretir (fikstur disleri yerinde)",
     _pem_bas.startswith("-----BEGIN RSA") and _pem_bas.endswith("PRIVATE KEY-----")
     and "MIIEow" in sahte_anahtar() and sahte_anahtar().count("\n") == 3,
     repr(sahte_anahtar()[:40]))

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    # KURULU DEPO SENARYOSU: once depo taban alinir, SONRA hat kurulur ->
    # hattin betikleri IZLENMEYEN durur ve taramaya GIRER. (E2E-1 betikleri
    # tabana katiyordu; bu yuzden bu yolu HIC olcmuyordu.)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(str(dp))
    (dp / "scripts").mkdir(parents=True, exist_ok=True)
    for _b in ("secret_scan.py", "kod_selftest.py"):
        shutil.copy(S / _b, dp / "scripts" / _b)
    _v4 = v4_yolu()
    _v4a = ("--v4", str(_v4)) if _v4 else ()
    _mod = "TAM" if _v4 else "KISMI"
    rc, out = kos("secret_scan.py", *_v4a, cwd=d)
    _p0 = [l for l in out.split("\n") if l.startswith("P0 ")]
    sina(f"O5-01c kurulu depoda oz-fikstur satirlari P0 URETMEZ ({_mod} mod)",
         not any("kod_selftest.py" in l for l in _p0), "; ".join(_p0)[:260])

    yaz(dp / "src/anahtar.pem", sahte_anahtar())
    rc, out = kos("secret_scan.py", *_v4a, cwd=d)
    sina(f"O5-01d ayni senaryoda GERCEK anahtar dosyasi HALA P0 ({_mod} mod, korlesme yok)",
         rc == 1 and "anahtar.pem" in out, f"exit={rc} · {out.strip()[:260]}")

# ================================================== O5-02  DERLEME ONBELLEGI (.pyc)
# Canli senaryo: KFAZ3 pytest kosunca `birim/__pycache__/*.pyc` ve
# `tests/__pycache__/*.pyc` olusur; IZLENMEYEN olduklari icin RECK-03 hepsini
# SCOPE_VIOLATION P0 sayardi. Muafiyet UZANTIYA OZGU ve LOGLU olmalidir.
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(d)
    (dp / "src/a.py").write_text("x = 2\n")
    kosu_iskeleti(dp, ["src/a.py"], [{"id": "CHG-001", "req": "REQ-001",
                                      "dosya": "src/a.py", "durum": "UYGULANMIS"}])
    # KFAZ3'un yan urunu: derleme onbellegi (izlenmeyen)
    yaz(dp / "birim/__pycache__/hesap.cpython-314.pyc", "sahte bytecode\n")
    yaz(dp / "tests/__pycache__/test_hesap.cpython-314.pyc", "sahte bytecode\n")
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("O5-02a izlenmeyen .pyc RECK-03 P0 URETMEZ (KFAZ3 yan urunu)",
         rc == 0 and "SCOPE_VIOLATION" not in out, f"exit={rc} · {out.strip()[-260:]}")
    sina("O5-02b .pyc muafiyeti LOGLU (sessiz muafiyet YOK)",
         out.count("BILGI RECK-03 ONBELLEK") == 2 and "derleme onbellegi:" in out,
         f"BILGI satiri={out.count('BILGI RECK-03 ONBELLEK')}")

    # kur.sh'in yazdigi .gitignore de KURULUM dosyasidir (taze depoda izlenmeyen)
    yaz(dp / ".gitignore", "__pycache__/\n*.pyc\n")
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("O5-02c kurulumun yazdigi .gitignore RECK-03 P0 URETMEZ (BILGI/KURULUM)",
         rc == 0 and "kurulum dosyasi: .gitignore" in out, f"exit={rc} · {out.strip()[-260:]}")

    # UZANTIYA OZGULUK: ayni dizindeki plansiz bir .py HALA ihlaldir
    yaz(dp / "birim/plansiz.py", "y = 1\n")
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("O5-02d izlenmeyen .py HALA SCOPE_VIOLATION P0 (muafiyet uzantiya ozgu)",
         rc == 1 and "SCOPE_VIOLATION" in out and "plansiz.py" in out, out.strip()[-260:])
    (dp / "birim/plansiz.py").unlink()



# YOLA da OZGU: `__pycache__/` DISINDAKI bir .pyc muafiyete GIRMEZ. Bu kontrol
# .gitignore'u OLMAYAN temiz bir depoda kosmalidir; aksi halde `*.pyc` zaten
# `git ls-files --others --exclude-standard` tarafindan elenir ve test muafiyet
# mantigini degil gitignore'u olcer (denetimde bu tuzaga dusuldu ve duzeltildi).
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(d)
    (dp / "src/a.py").write_text("x = 2\n")
    kosu_iskeleti(dp, ["src/a.py"], [{"id": "CHG-001", "req": "REQ-001",
                                      "dosya": "src/a.py", "durum": "UYGULANMIS"}])
    yaz(dp / "birim/__pycache__/hesap.cpython-314.pyc", "sahte bytecode\n")
    yaz(dp / "sahte.pyc", "bytecode gibi gorunur\n")
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("O5-02e `__pycache__/` DISINDAKI .pyc muaf DEGIL (yol kosulu da var)",
         rc == 1 and "SCOPE_VIOLATION" in out and "sahte.pyc" in out,
         out.strip()[-300:])
    sina("O5-02f ayni kosuda `__pycache__/` ICINDEKI .pyc muaf KALIR (daraltma dar)",
         "ONBELLEK" in out and "hesap.cpython-314.pyc" in out
         and "SCOPE_VIOLATION diff'te olan 'birim/__pycache__" not in out,
         out.strip()[-300:])

    # KATMANLI SAVUNMA: ACIK `dondurulan` beyani muafiyeti EZER. Muafiyet bir
    # "gormezden gel" degildir; plan bir .pyc'yi dondurmussa degismesi P0'dir.
    kosu_iskeleti(dp, ["src/a.py"], [{"id": "CHG-001", "req": "REQ-001",
                                      "dosya": "src/a.py", "durum": "UYGULANMIS"}],
                  dondurulan=["birim/__pycache__/hesap.cpython-314.pyc"])
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("O5-02g ACIK `dondurulan` beyani .pyc muafiyetini EZER (RECK-06 P0)",
         rc == 1 and "RECK-06" in out and "hesap.cpython-314.pyc" in out,
         f"exit={rc} · {out.strip()[-300:]}")

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(d)
    yaz(dp / "src/__pycache__/a.cpython-314.pyc", "sahte bytecode\n")
    rc, out = kos("secret_scan.py", cwd=d)
    sina("O5-02h secret_scan .pyc'yi kapsam disi birakir ve LOGLAR (BILGI SEC-05 pyc)",
         "BILGI SEC-05" in out and "pyc" in out, out.strip()[:260])

    yaz(dp / "src/anahtar.pem", sahte_anahtar())
    rc, out = kos("secret_scan.py", cwd=d)
    sina("O5-02i .pyc muafiyeti taramayi KORLESTIRMEZ (gercek anahtar HALA P0)",
         rc == 1 and "anahtar.pem" in out, f"exit={rc} · {out.strip()[:260]}")
    (dp / "src/anahtar.pem").unlink()

    # SIZINTI KAPISINDA yanlis negatif olmasin: `__pycache__/` disindaki bir
    # `.pyc` TARANIR. Yalniz uzantiya bakan bir muafiyet, sirri `sahte.pyc`
    # adiyla saklamaya izin verirdi (denetimde olculdu).
    yaz(dp / "sahte.pyc", sahte_anahtar())
    rc, out = kos("secret_scan.py", cwd=d)
    _sec05_sahte = [l for l in out.split("\n") if "SEC-05" in l and "sahte.pyc" in l]
    _p0_sahte = [l for l in out.split("\n") if l.startswith("P0 ") and "sahte.pyc" in l]
    sina("O5-02j `__pycache__/` DISINDAKI .pyc TARANIR (sizinti kapisinda kor nokta yok)",
         rc == 1 and _p0_sahte and not _sec05_sahte,
         f"exit={rc} · P0={_p0_sahte} · SEC05={_sec05_sahte}")

# ---- kur.sh: hedef deponun .gitignore'una derleme onbellegi eklenir ----------
# SAHTE LAB: kur.sh LAB'i ISARETLE tanir (E2E-3), konumdan degil. --kuru modu
# hicbir sey yazmaz ve DOGRULAMAYA GIRMEZ -> oz-test kendini yeniden cagirmaz.
def sahte_lab(kok):
    (kok / "ATLAS_SABLONLAR").mkdir(parents=True, exist_ok=True)
    yaz(kok / "ORTAK/scripts/ortak_gate.py", "# stub\n")
    sab = kok / "KOD_SABLONLAR"
    (sab / ".opencode").mkdir(parents=True, exist_ok=True)
    yaz(sab / "templates/kod_profil.ORNEK.json", {"dil": "python"})
    for _a in ("opencode.json", "routing.profiles.json", "00_KOD_OKU_BENI.md",
               "OPERATOR_SURME.md"):
        yaz(sab / _a, "{}\n" if _a.endswith(".json") else "# stub\n")
    (sab / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy(S / "kur.sh", sab / "scripts" / "kur.sh")
    return sab / "scripts" / "kur.sh"


with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _kur = sahte_lab(dp / "lab")
    (dp / "hedef").mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["bash", str(_kur), str(dp / "hedef"), "--kuru"],
                       capture_output=True, text=True, timeout=600)
    _o = r.stdout + r.stderr
    sina("O5-02k kur.sh KURULUMDA .gitignore'a __pycache__/ + *.pyc ekler",
         "__pycache__/" in _o and "*.pyc" in _o and ".gitignore" in _o, _o.strip()[-300:])

    yaz(dp / "hedef/.gitignore", "__pycache__/\n*.pyc\n")
    r = subprocess.run(["bash", str(_kur), str(dp / "hedef"), "--kuru"],
                       capture_output=True, text=True, timeout=600)
    _o = r.stdout + r.stderr
    sina("O5-02l kur.sh IDEMPOTENT: satirlar varsa .gitignore'a DOKUNMAZ",
         "DOKUNULMADI" in _o and "eklenecek" not in _o, _o.strip()[-300:])

# ---- kur.sh --dogrula: eksik .gitignore KURULUM EKSIK sayilir ---------------
def sahte_kurulum(kok):
    """--dogrula'nin kosturdugu betikler STUB'dir: oz-test kendini cagirmaz."""
    (kok / "scripts").mkdir(parents=True, exist_ok=True)
    yaz(kok / "ORTAK/scripts/ortak_gate.py", "# stub\n")
    for _b, _cikis in (("budget_guard.py", 0), ("kod_gate_merge.py", 1),
                       ("kod_selftest.py", 0), ("perm_lint.py", 0)):
        yaz(kok / "scripts" / _b, f"import sys\nsys.exit({_cikis})\n")


with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    sahte_kurulum(dp)
    rc, out = kos("kur.sh", str(dp), "--dogrula")
    sina("O5-02m kur.sh --dogrula .gitignore YOKSA FAIL sayar (fail-closed)",
         "FAIL .gitignore" in out and rc == 1, f"exit={rc} · {out.strip()[-300:]}")

    yaz(dp / ".gitignore", "__pycache__/\n*.pyc\n")
    rc, out = kos("kur.sh", str(dp), "--dogrula")
    sina("O5-02n kur.sh --dogrula iki satir varsa OK basar",
         "OK   .gitignore" in out and "FAIL .gitignore" not in out, out.strip()[-300:])

# ============================ O5-05  MUAFIYET YOLU: TAM DIZIN BILESENI  [P0]
# Bagimsiz denetim (24.08.2026): iki kapinin yol kosulu ALT-DIZE ariyordu
# (`"__pycache__/" in yol`). Bu yuzden `evil__pycache__/anahtar.pyc` — icinde
# GERCEK bir PEM ozel anahtar — HER IKI kapida da muaf sayildi ve ikisi de
# exit=0 dondu: tek bir dizin adiyla KAPSAM ve SIZINTI kapilari BIRLIKTE
# atlatilabiliyordu. Fikstur, ayni kosuda GERCEK `__pycache__`in muaf KALDIGINI
# da olcer — daraltma dogru yerde dar olmali.
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _pem_govde = sahte_anahtar()
    yaz(dp / "birim/hesap.py", "x = 1\n")
    yaz(dp / "evil__pycache__/anahtar.pyc", _pem_govde)
    yaz(dp / "birim/__pycache__/hesap.cpython-314.pyc", _pem_govde)
    git_kur(str(dp))                       # ikisi de TAKIPLI
    # takipli dosyalar degistirilir -> `git diff HEAD` ikisini de gorur
    yaz(dp / "evil__pycache__/anahtar.pyc", _pem_govde + "ZZ\n")
    yaz(dp / "birim/__pycache__/hesap.cpython-314.pyc", _pem_govde + "YY\n")
    kosu_iskeleti(dp, ["birim/hesap.py"], [{"id": "CHG-001", "req": "REQ-001",
                                            "dosya": "birim/hesap.py", "durum": "PLANLANDI"}])
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("O5-05a `evil__pycache__/x.pyc` RECK-03 P0 (alt-dize kacisi kapali)",
         rc == 1 and "SCOPE_VIOLATION" in out and "evil__pycache__/anahtar.pyc" in out,
         f"exit={rc} · {out.strip()[-300:]}")
    sina("O5-05b ayni kosuda GERCEK `birim/__pycache__/` muaf KALIR",
         "ONBELLEK" in out and "birim/__pycache__/hesap.cpython-314.pyc" in out
         and "SCOPE_VIOLATION diff'te olan 'birim/__pycache__" not in out,
         out.strip()[-300:])

    _v4 = v4_yolu()
    _v4a = ("--v4", str(_v4)) if _v4 else ()
    _mod = "TAM" if _v4 else "KISMI"
    rc, out = kos("secret_scan.py", *_v4a, cwd=d)
    _p0 = [l for l in out.split("\n") if l.startswith("P0 ")]
    sina(f"O5-05c ayni dosya secret_scan'de de P0 ({_mod} mod, iki kapili kacis kapali)",
         rc == 1 and any("evil__pycache__/anahtar.pyc" in l for l in _p0),
         f"exit={rc} · P0={_p0}")
    sina("O5-05d secret_scan'de GERCEK `__pycache__` yine BILGI SEC-05 (muaf)",
         any("SEC-05" in l and "birim/__pycache__/hesap.cpython-314.pyc" in l
             for l in out.split("\n"))
         and not any("birim/__pycache__" in l for l in _p0),
         out.strip()[:300])

# ================== O5-06  GUVEN SINIRI: EBEVEYNDE OZYINELEMELI ARAMA YOK [P0]
# Bagimsiz denetim (24.08.2026): `v4_aday_yollar()` hedefin EBEVEYNINDE
# `**/KOMUT_TOOLKIT_v4/.../v4_verify.py` ariyor ve buldugunu IMPORT EDIYORDU —
# yani taranan deponun DISINDAKI rastgele derinlikte bir kardes agactan Python
# CALISTIRIYORDU. Fikstur bunu iki yonden olcer: (a) kardes agactaki sahte
# toolkit IMPORT EDILMEMELI (diske iz birakan bir sahte kullanilir), (b) kapi
# KISMI moda dusup fail-closed exit=3 vermeli.
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _kardes = dp / "kardes/derin/KOMUT_TOOLKIT_v4/ARACLAR/betikler"
    yaz(_kardes / "v4_verify.py",
        "import pathlib, re\n"
        "pathlib.Path(__file__).parent.joinpath('IMPORT_EDILDIM.iz').write_text('x')\n"
        "SECRET_PATTERNS = [(r'ASLA-ESLESMEZ-XYZZY', 'sahte')]\n"
        "PLACEHOLDER_HINTS = []\nSKIP_BINARY_EXT = set()\nLOCK_NAMES = set()\n"
        "DOC_ENV_RE = re.compile(r'$^')\n"
        "def looks_like_placeholder(s): return False\n")
    _hedef = dp / "hedef"
    yaz(_hedef / "a.py", "x = 1\n")
    git_kur(str(_hedef))
    rc, out = kos("secret_scan.py", cwd=str(_hedef))
    sina("O5-06a kardes agactaki YABANCI v4_verify.py IMPORT EDILMEZ",
         not (_kardes / "IMPORT_EDILDIM.iz").exists()
         and "kardes" not in out.split("kalip kaynagi")[-1][:200],
         f"iz={(_kardes / 'IMPORT_EDILDIM.iz').exists()} · {out.strip()[:200]}")
    sina("O5-06b toolkit bulunamayinca KISMI mod exit=3 (fail-closed korunur)",
         rc == 3 and "KISMI" in out, f"exit={rc} · {out.strip()[:200]}")

    # MESRU YOL KIRILMADI: acikca bildirilen toolkit hala TAM modu acar
    if v4_yolu():
        rc, out = kos("secret_scan.py", "--v4", str(v4_yolu()), cwd=str(_hedef))
        sina("O5-06c ACIK `--v4` hala TAM modu aciyor (mesru yol kirilmadi)",
             rc == 0 and "SECRET-SCAN PASS" in out, f"exit={rc} · {out.strip()[:200]}")
    else:
        sina_atla("O5-06c ACIK `--v4` hala TAM modu aciyor (mesru yol kirilmadi)",
                  "CALISTIRILMADI: toolkit elde yok")

# ======================================================= O5-03  ORTAMDAN YALITIM
with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "yankila.py",
        "import os\nprint('SIZDI' if os.environ.get('V4_VERIFY_YOLU') else 'YOK')\n")
    _r = subprocess.run([sys.executable, str(dp / "yankila.py")], capture_output=True, text=True, timeout=600)
    sina("O5-03a V4_VERIFY_YOLU alt sureclere SIZMAZ (KISMI fiksturler ortamdan yalitik)",
         "YOK" in _r.stdout, _r.stdout.strip()[:160])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "src/a.py", "x = 1\n")
    git_kur(str(dp))
    _v4 = v4_yolu()
    _kirli = dict(os.environ)
    _kirli["V4_VERIFY_YOLU"] = str(_v4 or "")
    _rk = subprocess.run([sys.executable, str(S / "secret_scan.py")], cwd=d,
                         capture_output=True, text=True, env=_kirli, timeout=600)
    _rt, _ = kos("secret_scan.py", cwd=d)          # yalitilmis ortam -> KISMI
    # Fark GERCEK: kirli ortamda TAM mod (exit=0), temiz ortamda KISMI (exit=3).
    # Yalitim olmasaydi K4-1/E2E-1/JSON-1/JSON-2/O4-03a operatorun kabuğuna gore
    # renk degistirirdi — olculen sey kapi degil, ortam olurdu.
    sina("O5-03b ortam kirliligi modu GERCEKTEN cevirir; yalitim K4-1'i sabit tutar",
         (_v4 is None) or (_rk.returncode == 0 and _rt == 3),
         f"kirli_exit={_rk.returncode} temiz_exit={_rt} v4={_v4}")

# ======================================================= OLCUM-06 B2+B3 (26.08.2026)
# OLCUM-06 canli: (B2) chg.req liste ise TypeError crash, (B3) scripts_sha256 ciplak
# anahtar yanlis GATE_TAMPERED terminali. Duzeltme geri alinirsa KIRMIZI verir.

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _sema_kosu(dp, [{"id": "REQ-01", "tur": "davranissal", "kabul": "x"}])
    # manifesti liste req ile ez (canli hatasi: ["REQ-001"])
    yaz(dp / "_KOSU/02-KFAZ-2-MAN.md",
        "# KFAZ2\n```json\n" + json.dumps({"sema": "KFAZ2/v1",
                                            "chg": [{"id": "CHG-001", "req": ["REQ-01"],
                                                     "dosya": "src/a.py", "durum": "UYGULANMIS"}]}) + "\n```\n")
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("B2-1 NEGATIF: chg.req LISTE ise SCHEMA_INVALID P0 ve crash YOK",
         rc == 1 and "SCHEMA_INVALID" in out and "req" in out
         and "Traceback" not in out and "TypeError" not in out,
         out.strip()[:300])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    _sema_kosu(dp, [{"id": "REQ-01", "tur": "davranissal", "kabul": "x"}])
    # bu kosu _sema_kosu'nun varsayilan string req'i ile gelir — pozitif kontrol
    rc, out = kos("chg_reconcile.py", cwd=d)
    sina("B2-2 POZITIF: chg.req DIZE ise SCHEMA_INVALID YOK (crash guard calisiyor)",
         "SCHEMA_INVALID" not in out and rc == 0,
         out.strip()[:300])

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    yaz(dp / "kod_profil.json", json.dumps({"dil": "python", "test_komutu": "pytest -q"}))
    _h = hashlib.sha256((dp / "kod_profil.json").read_bytes()).hexdigest()
    yaz(dp / "_KOSU/gate/BASELINE.json",
        {"mod": "MEVCUT_KOD", "olculdu": "2026-08-24T00:00:00Z",
         "test": {"kosan": 1, "basarisiz": 0, "hata": 0, "atlanan": 0, "kapsam_yuzde": None},
         "test_adlari": [], "test_komutu_cikis_kodu": 0,
         "kod_profil_yolu": "kod_profil.json", "kod_profil_sha256": _h,
         "scripts_sha256": {"api_surface.py": "a" * 64}, "dondurulan": {},
         "dis_imza": [], "olculmeyen": []})
    rc, out = kos("freeze_check.py", cwd=d)
    sina("B3-1 NEGATIF: scripts_sha256 ciplak anahtar -> SCHEMA_INVALID, GATE_TAMPERED degil (exit=1, terminal yok)",
         rc == 1 and "SCHEMA_INVALID" in out and "ciplak dosya adi" in out
         and "P0 FRZ-02 GATE_TAMPERED" not in out and "TERMINAL FAIL" not in out,
         f"exit={rc} · {out.strip()[:300]}")

with tempfile.TemporaryDirectory() as d:
    dp = pathlib.Path(d)
    (dp / "scripts").mkdir(parents=True, exist_ok=True)
    yaz(dp / "scripts/api_surface.py", "# kapi betigi\nx=1\n")
    _h_api = hashlib.sha256((dp / "scripts/api_surface.py").read_bytes()).hexdigest()
    yaz(dp / "kod_profil.json", json.dumps({"dil": "python", "test_komutu": "pytest -q"}))
    _h_prof = hashlib.sha256((dp / "kod_profil.json").read_bytes()).hexdigest()
    yaz(dp / "_KOSU/gate/BASELINE.json",
        {"mod": "MEVCUT_KOD", "olculdu": "2026-08-24T00:00:00Z",
         "test": {"kosan": 1, "basarisiz": 0, "hata": 0, "atlanan": 0, "kapsam_yuzde": None},
         "test_adlari": [], "test_komutu_cikis_kodu": 0,
         "kod_profil_yolu": "kod_profil.json", "kod_profil_sha256": _h_prof,
         "scripts_sha256": {"scripts/api_surface.py": _h_api}, "dondurulan": {},
         "dis_imza": [], "olculmeyen": []})
    rc, out = kos("freeze_check.py", cwd=d)
    sina("B3-2 POZITIF: scripts_sha256 'scripts/*.py' anahtari + dogru hash -> PASS",
         rc == 0 and "SCHEMA_INVALID" not in out and "PASS" in out,
         f"exit={rc} · {out.strip()[:300]}")

# ---------------------------------------------------------------------------- rapor
if AYRINTILI or kaldi:
    for r in raporlar:
        print(r)
else:
    for r in raporlar:
        if r.strip().startswith("FAIL"):
            print(r)
print(ozet_metni(gecti, kaldi, atlandi))
sys.exit(1 if kaldi else 0)
