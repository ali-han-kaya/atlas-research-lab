#!/usr/bin/env python3
"""test_attest — KFAZ3 test kanitinin makine dogrulamasi (CHK-TEST)

NEDEN VAR:
Kod hattinda kapilar DIFF'i denetler, DAVRANISI denetlemez. Davranisi
sertifikalandiran tek artefakt test kanitidir. Ama ajanin "testler gecti"
beyanina guvenmek, gate_merge'un ogrettigi hatanin aynisidir: sayilar HER ZAMAN
ham rapordan (JUnit XML) YENIDEN hesaplanir; ajan beyani yalnizca karsilastirma
icin okunur. Beyan ile hesap celisirse celiskinin KENDISI P0'dir.

KURALLAR (CHK-TEST)
  TST-01  basarisiz = 0                                                       [P0]
  TST-02  hata = 0                                                            [P0]
  TST-03  kosan >= 1  (sifir test "temiz" degildir)                           [P0]
  TST-04  kosan >= taban.kosan  (test SILINEREK yesil yapilamaz)              [P0]
  TST-05  atlanan <= taban.atlanan  (test ATLANARAK yesil yapilamaz)          [P0]
  TST-06  kapsam >= taban.kapsam - 1                                          [P1]
  TST-07  TEST-EVIDENCE.json beyani ham raporla celisiyor  [EVIDENCE_UNVERIFIED P0]
  TST-08  rapor dosyasi yok / bos / ayristirilamiyor       [EVIDENCE_UNVERIFIED P0]
  TST-09  test komutunun cikis kodu kayitli degil                             [P0]
  TST-10  rapor KAYNAKTAN ESKI (bayat kanit)               [STALE_EVIDENCE P0]
  TST-11  kanittaki `komut` kod_profil.test_komutu ile ayni degil [EVIDENCE_UNVERIFIED P0]
  TST-12  kanittaki `rapor` kod_profil.test_raporu ile ayni degil [EVIDENCE_UNVERIFIED P0]

TST-10..12 NICIN EKLENDI (OLCUM-02 K18, 24.08.2026):
Elle uydurulmus bir JUnit XML — icinde depoda hic var olmamis bir test adi
(`test_ASLA_KOSMADI`) — bu betigi `PASS · exit=0` ile geciyordu. Betik beyan ile
raporu karsilastiriyordu, ama raporun GERCEKTEN KOSMUS bir testten geldigini
hic sormuyordu: tazelik yok, koken yok. Uc kontrol bunu daraltir:
  - TST-10 rapor, en yeni kaynak/test dosyasindan ESKI olamaz (bayat kanit).
  - TST-11/12 kanit, `kod_profil.json`'daki komut ve rapor yoluyla ESLESMELI;
    boylece sahtecilik profili de degistirmeyi gerektirir ve o da
    `freeze_check` FRZ-01 GATE_TAMPERED'a takilir (katmanli savunma).

KALAN RISK (acikca yazilir, kapatilmaz):
Bos govdeli, her zaman gecen bir test bu kontrollerin HEPSINI gecer. Bu betik
testin YOKLUGUNU olcer, BOSLUGUNU olcmez. RECK-07 (chg_reconcile) davranissal
her REQ'i tabanda OLMAYAN bir test adina baglayarak riski daraltir, sifirlamaz.
TST-10..12 de sahteciligi ZORLASTIRIR, imkansiz kilmaz: raporu dokunup profili
de tutarli yazan bir saldirgan gecebilir — ama artik freeze_check'e yakalanir.

Kullanim: python3 scripts/test_attest.py [--kanit _KOSU/03-KFAZ-3-TEST-EVIDENCE.json]
                                         [--taban _KOSU/gate/BASELINE.json]
                                         [--profil kod_profil.json] [--kosu _KOSU] [--json]
  --profil : TST-11/12 kaynagi (kanittaki komut ve rapor yolu bununla eslesmeli)
  --kosu   : kosu dizini; TST-10 tazelik taramasinda bu onek DISLANIR
"""
import json, pathlib, sys, xml.etree.ElementTree as ET


# ---------------------------------------------------------------- K9 (OLCUM-02)
# Bu dosyanin adi pytest'in varsayilan kesif kalibina (`test_*.py`) GIRER ve
# hedef deponun kokunde `pytest` calistirildiginda pytest onu bir test modulu
# sanip IMPORT eder. Govde eskiden modul duzeyindeydi ve sonunda sys.exit(1)
# cagiriyordu; import aninda SystemExit -> pytest INTERNALERROR, exit=3, SIFIR
# test kostu. Yani hattin test kanidi kapisi, denetledigi projenin test
# kosusunu YOK EDIYORDU (olculdu).
# Cozum: govde _main() icine alindi ve `__test__ = False` ile pytest'e bu
# modulun toplanmamasi bildirildi. Import artik YAN ETKISIZDIR.
__test__ = False


def _main():
    JSON_CIK = "--json" in sys.argv


    def arg(bayrak, varsayilan):
        if bayrak in sys.argv:
            i = sys.argv.index(bayrak)
            if i + 1 < len(sys.argv):
                return sys.argv[i + 1]
        return varsayilan


    kanit_yol = pathlib.Path(arg("--kanit", "_KOSU/03-KFAZ-3-TEST-EVIDENCE.json"))
    taban_yol = pathlib.Path(arg("--taban", "_KOSU/gate/BASELINE.json"))
    bulgular = []


    def ekle(kural, siddet, aciklama, kod=None):
        b = {"kural": kural, "siddet": siddet, "aciklama": aciklama}
        if kod:
            b["kod"] = kod
        bulgular.append(b)


    if not kanit_yol.exists():
        ekle("TST-08", "P0", f"{kanit_yol} yok — KFAZ3 kaniti uretilmemis", "EVIDENCE_UNVERIFIED")
        kanit = {}
    else:
        try:
            kanit = json.loads(kanit_yol.read_text())
        except Exception as e:
            ekle("TST-08", "P0", f"{kanit_yol} JSON gecersiz: {e}", "EVIDENCE_UNVERIFIED")
            kanit = {}

    taban = {}
    if taban_yol.exists():
        try:
            taban = json.loads(taban_yol.read_text())
        except Exception as e:
            ekle("TST-08", "P0", f"{taban_yol} JSON gecersiz: {e}", "EVIDENCE_UNVERIFIED")
    else:
        ekle("TST-08", "P1", f"{taban_yol} yok — taban karsilastirmasi CALISTIRILMADI "
                             f"(OLCULMEYEN kaydi acilmali)", "CALISTIRILMADI")

    taban_test = (taban.get("test") or {})


    def junit_oku(yol):
        """JUnit XML'i BAGIMSIZ ayristir. Ajan beyanina bakma."""
        p = pathlib.Path(yol)
        if not p.exists():
            return None, f"rapor dosyasi yok: {yol}"
        try:
            kok = ET.parse(p).getroot()
        except Exception as e:
            return None, f"XML ayristirilamadi: {e}"
        suites = [kok] if kok.tag == "testsuite" else list(kok.iter("testsuite"))
        if not suites:
            return None, "XML icinde <testsuite> yok"
        t = f = e = s = 0
        for su in suites:
            t += int(su.get("tests", 0) or 0)
            f += int(su.get("failures", 0) or 0)
            e += int(su.get("errors", 0) or 0)
            s += int(su.get("skipped", 0) or 0)
        return {"toplam": t, "basarisiz": f, "hata": e, "atlanan": s, "kosan": t - s}, None


    rapor_yol = kanit.get("rapor")
    bicim = (kanit.get("rapor_formati") or "").lower()
    ham = None

    if not rapor_yol:
        ekle("TST-08", "P0", "TEST-EVIDENCE icinde `rapor` alani yok — ham kanit olmadan "
                             "beyan dogrulanamaz", "EVIDENCE_UNVERIFIED")
    elif bicim in ("", "yok", "none"):
        ekle("TST-08", "P0", f"`rapor_formati`='{bicim or 'bos'}' — makine okunur test raporu YOK. "
                             f"CALISTIRILMADI = P1 degil, kanitsiz PASS = P0", "EVIDENCE_UNVERIFIED")
    elif bicim != "junit-xml":
        ekle("TST-08", "P1", f"`rapor_formati`='{bicim}' bu surumde ayristirilamiyor — "
                             f"CALISTIRILMADI (yalniz junit-xml destekleniyor)", "CALISTIRILMADI")
    else:
        ham, hata = junit_oku(rapor_yol)
        if hata:
            ekle("TST-08", "P0", hata, "EVIDENCE_UNVERIFIED")

    # ---------------------------------------- TST-10/11/12 KOKEN ve TAZELIK
    PROFIL = pathlib.Path(arg("--profil", "kod_profil.json"))
    _profil = {}
    if PROFIL.exists():
        try:
            _profil = json.loads(PROFIL.read_text())
        except Exception as e:
            ekle("TST-11", "P1", f"{PROFIL} JSON gecersiz: {e} — koken karsilastirmasi "
                                 f"CALISTIRILMADI", "CALISTIRILMADI")
    else:
        ekle("TST-11", "P1", f"{PROFIL} yok — koken karsilastirmasi CALISTIRILMADI",
             "CALISTIRILMADI")

    if _profil:
        _bek_komut = str(_profil.get("test_komutu", "")).strip()
        _bek_rapor = str(_profil.get("test_raporu", "")).strip()
        _kanit_komut = str(kanit.get("komut", "")).strip()
        if _bek_komut and _kanit_komut and _kanit_komut != _bek_komut:
            ekle("TST-11", "P0", f"kanit komutu {_kanit_komut!r} != kod_profil.test_komutu "
                                 f"{_bek_komut!r} — beyan edilen komut kosulmamis olabilir",
                 "EVIDENCE_UNVERIFIED")
        if _bek_rapor and rapor_yol and str(rapor_yol).strip() != _bek_rapor:
            ekle("TST-12", "P0", f"kanit raporu {str(rapor_yol)!r} != kod_profil.test_raporu "
                                 f"{_bek_rapor!r} — baska bir dosya kanit diye sunulmus",
                 "EVIDENCE_UNVERIFIED")

    # TST-10 TAZELIK: rapor, en yeni kaynak/test dosyasindan eski olamaz.
    # Kaynak kumesi git'ten alinir; git yoksa kontrol CALISTIRILMADI'dir.
    if rapor_yol and pathlib.Path(rapor_yol).exists():
        import subprocess
        _r = subprocess.run(["git", "ls-files"], capture_output=True, text=True, timeout=120)
        if _r.returncode != 0:
            ekle("TST-10", "P1", "`git ls-files` calismadi — rapor tazeligi CALISTIRILMADI",
                 "CALISTIRILMADI")
        else:
            _kosu_onek = str(pathlib.Path(arg("--kosu", "_KOSU"))).rstrip("/") + "/"
            _rapor_mt = pathlib.Path(rapor_yol).stat().st_mtime
            _en_yeni, _ad = 0.0, ""
            for _f in _r.stdout.split("\n"):
                _f = _f.strip()
                if not _f or _f.startswith(_kosu_onek) or _f.startswith(".opencode/"):
                    continue
                _fp = pathlib.Path(_f)
                if not _fp.exists():
                    continue
                _m = _fp.stat().st_mtime
                if _m > _en_yeni:
                    _en_yeni, _ad = _m, _f
            if _ad and _rapor_mt < _en_yeni:
                ekle("TST-10", "P0", f"rapor {rapor_yol} kaynaktan ESKI ('{_ad}' daha yeni) — "
                                     f"bu rapor mevcut kodu olcmemis olabilir", "STALE_EVIDENCE")

    # TST-09 cikis kodu
    cikis = kanit.get("cikis_kodu")
    if cikis is None:
        ekle("TST-09", "P0", "`cikis_kodu` kayitli degil — test komutunun gercekten kostugu bilinmiyor")
    elif int(cikis) != 0 and ham and (ham["basarisiz"] == 0 and ham["hata"] == 0):
        ekle("TST-07", "P0", f"cikis_kodu={cikis} ama raporda 0 basarisiz/0 hata — celiski",
             "EVIDENCE_UNVERIFIED")

    if ham:
        # TST-07 beyan/hesap celiskisi
        beyan = kanit.get("sonuc") or {}
        for alan in ("kosan", "basarisiz", "hata", "atlanan"):
            if alan in beyan and str(beyan[alan]).lstrip("-").isdigit() and int(beyan[alan]) != ham[alan]:
                ekle("TST-07", "P0", f"beyan {alan}={beyan[alan]} ama ham raporda {ham[alan]} — "
                                     f"kapi kendi beyanina guvenmez", "EVIDENCE_UNVERIFIED")
        if ham["basarisiz"] > 0:
            ekle("TST-01", "P0", f"basarisiz test: {ham['basarisiz']}")
        if ham["hata"] > 0:
            ekle("TST-02", "P0", f"hatali test: {ham['hata']}")
        if ham["kosan"] < 1:
            ekle("TST-03", "P0", "hicbir test kosmadi — sifir test 'temiz' degildir")
        tk = taban_test.get("kosan")
        if isinstance(tk, int) and ham["kosan"] < tk:
            ekle("TST-04", "P0", f"kosan {ham['kosan']} < taban {tk} — test SILINEREK yesil yapilamaz")
        ta = taban_test.get("atlanan")
        if isinstance(ta, int) and ham["atlanan"] > ta:
            ekle("TST-05", "P0", f"atlanan {ham['atlanan']} > taban {ta} — test ATLANARAK yesil yapilamaz")
        tkap = taban_test.get("kapsam_yuzde")
        kap = (kanit.get("sonuc") or {}).get("kapsam_yuzde")
        if isinstance(tkap, (int, float)):
            if not isinstance(kap, (int, float)):
                ekle("TST-06", "P1", f"taban kapsami {tkap}% ama bu kosuda kapsam CALISTIRILMADI", "CALISTIRILMADI")
            elif kap < tkap - 1:
                ekle("TST-06", "P1", f"kapsam {kap}% < taban {tkap}% - 1")

    p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
    p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
    rapor = {"sema": "TEST-ATTEST/v1", "ham_rapor": ham, "taban": taban_test,
             "p0": p0, "p1": p1, "bulgular": bulgular,
             "kalan_risk": "Bos govdeli her zaman gecen test bu kontrolleri gecer; "
                           "bu betik testin YOKLUGUNU olcer, BOSLUGUNU olcmez."}
    if JSON_CIK:
        print(json.dumps(rapor, ensure_ascii=False, indent=2))
    else:
        for b in bulgular:
            print(f"{b['siddet']} {b['kural']} {b.get('kod','')} {b['aciklama']}")
        if ham:
            print(f"ham rapor: kosan={ham['kosan']} basarisiz={ham['basarisiz']} "
                  f"hata={ham['hata']} atlanan={ham['atlanan']}")
        print(f"TEST-ATTEST {'FAIL' if p0 else 'PASS'} — P0={p0} P1={p1}")
    sys.exit(1 if p0 else 0)



if __name__ == "__main__":
    _main()
