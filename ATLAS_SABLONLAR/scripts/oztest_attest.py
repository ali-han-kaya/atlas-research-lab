#!/usr/bin/env python3
"""oztest_attest — ATLAS oz-test ENVANTERININ pinlenmesi (CHK-OZTEST, P1-3)

NEDEN VAR:
`atlas_selftest.py` labin davranisini sertifikalandiran tek artefakttir. Ama
"68/68 gecti" satiri, KAC testin var oldugunu degil kacinin gectigini soyler.
Bir test SESSIZCE SILINIRSE sayi duser ve kimse gormez; daha kotusu, silinen
test kirmiziysa sayi ARTAR ve silme "iyilesme" gibi gorunur.

KOD hattindaki `test_attest.py` ayni sorunu JUnit XML uzerinden cozer (TST-04:
"kosan >= taban.kosan — test SILINEREK yesil yapilamaz"). Bu betik ayni ilkeyi
ATLAS'a tasir, ama TEK BIR FARKLA:

  **Gecen sayi degil, ENVANTER pinlenir.**

Cunku gecen sayi ortama baglidir: MOD-1/MOD-2 opencode veri dosyalari olmayan
bir makinede DAIMA duser (bkz. atlas_selftest basligi). Gecen sayiyi pinlemek,
kusursuz bir labi baska bir makinede kirmizi yakardi. Test KIMLIKLERI ise
ortamdan bagimsizdir: AA-1 makinede gecmese de VARDIR. Silinirse yoktur.

Sayilar HER ZAMAN ham kosu ciktisindan YENIDEN hesaplanir; taban dosyasi
yalnizca karsilastirma icin okunur. Beyan ile hesap celisirse celiski P0'dir.

KURALLAR (CHK-OZTEST)
  OZT-01  taban dosyasi yok / bozuk       -> kapi ACILMAZ (fail-closed)     [P0]
  OZT-02  tabandaki kimlik bu kosuda YOK  -> test SILINMIS                  [P0]
  OZT-03  kosuda hicbir test yok          -> sifir test "temiz" degildir    [P0]
  OZT-05  tabanda olmayan YENI kimlik var -> taban guncellenmeli            [P1]
  OZT-06  taban kimlik_hash'i kendi listesiyle tutmuyor -> taban kurcalanmis[P0]

OZT-05 NICIN P0 DEGIL:
Test EKLEMEK istenen davranistir. Kapiyi kapatirsa herkes tabani "duzeltmek"
icin refleksle gunceller ve pin anlamini yitirir. P1 uyari verir, insan gorur.

OZT-04 NICIN YOK:
Ilk tasarimda "kimlik sayisi taban sayisindan dusuk" diye ayri bir P0 kurali vardi.
Mutasyon testi onu KAPATTI ve HICBIR oz-test kirmizi yanmadi — yani kural kapisizdi.
Incelendiginde mantiksal olarak da gereksiz oldugu gorüldü: kimlikler benzersiz
oldugu icin sayi ancak bir kimlik eksildiginde duser, o da zaten OZT-02'dir. Tek
basina yanabilecegi durum yalnizca taban dosyasindaki `sayi` alaninin elle
sisirilmesidir ki bu yanlis-pozitif uretir. Kaldirildi: yanmayan kural, olcum degil
susleme olur ve sahte guven verir.

OZT-06 NICIN VAR:
OZT-02'yi atlatmanin kolay yolu tabandaki kimligi de silmektir. Hash, elle
dusurulmus tabani yakalar: saldirganin ayrica hash'i yeniden hesaplamasi gerekir
ve bu, commit diff'inde iki ayri kasitli degisiklik olarak gorunur.

KALAN RISK (acikca yazilir, kapatilmaz):
Bu betik testin YOKLUGUNU olcer, BOSLUGUNU olcmez. Govdesi bosaltilmis ama
kimligi duran bir test butun kontrolleri gecer. Ayrica `--uret` ile tabani
yeniden ureten biri her ihlali silebilir; pin sahteciligi ZORLASTIRIR,
IMKANSIZ KILMAZ. Karsi tedbir sosyal degil yapisaldir: taban dosyasi commit'lenir,
degisikligi denetleyen taraf gorur.

NEDEN --full ZINCIRINDE DEGIL:
`atlas_selftest.py` kendi icinde `check_integrity.sh --full` cagirir. Bu betigi
--full'e baglamak sonsuz ozyineleme uretirdi. Devir/nobet kontrol listesinde
elle kosulur.

Kullanim:
  python3 scripts/oztest_attest.py                      # canli kosu + varsayilan taban
  python3 scripts/oztest_attest.py --uret               # tabani bu kosudan URET
  python3 scripts/oztest_attest.py --cikti <dosya> --taban <dosya> [--json]
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

__test__ = False

SEMA = "OZTEST-TABAN/v1"
BETIKLER = pathlib.Path(__file__).resolve().parent
VARSAYILAN_TABAN = BETIKLER / "OZTEST-TABAN.json"
# "  OK   AA-1: ..." / "  KALDI CC-3: ... :: rc=1" -> AA-1, CC-3
# Once GENIS yakala, sonra bicimi DOGRULA. Eski surumde tek dar regex vardi ve
# `TS-4a`, `CI-18b`, `FIX_RECONCILE-1`, `OZ-1` gibi mesru kimlikleri KACIRIYORDU;
# kacan kimlik tabana hic girmedigi icin SESSIZCE SILINEBILIRDI (olculdu).
SATIR = re.compile(r"^\s*(?:OK|KALDI)\s+([^\s:]+)\s*:")
# YAZILI SOZLESME — kabul edilen kimlik bicimi:
#   <bolum>(-<bolum>)*-<rakam>[<tek kucuk harf>]
#   bolum: harf/rakam/alt cizgi/nokta (unicode; Turkce harf dahil)
# Ornek gecerli : AA-1, TS-4a, CI-18b, FIX_RECONCILE-1, OZ-1
# Ornek gecersiz: OZ-TEST-CRASH (rakamla bitmiyor) — kimlik DEGIL, tanidir.
KIMLIK_BICIM = re.compile(r"^[\w.]+(?:-[\w.]+)*-\d+[a-z]?$", re.UNICODE)


def kimlikleri_cikar(metin):
    """Ham kosu ciktisindan test kimliklerini YENIDEN hesaplar."""
    bulunan = set()
    for satir in metin.splitlines():
        m = SATIR.match(satir)
        if m and KIMLIK_BICIM.match(m.group(1)):
            bulunan.add(m.group(1))
    return sorted(bulunan)


def kimlik_hash(kimlikler):
    ham = "\n".join(sorted(kimlikler)).encode("utf-8")
    return "sha256:" + hashlib.sha256(ham).hexdigest()


def _arg(bayrak, varsayilan=None):
    if bayrak in sys.argv:
        i = sys.argv.index(bayrak)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return varsayilan


def _main():
    json_cik = "--json" in sys.argv
    uret = "--uret" in sys.argv
    taban_yol = pathlib.Path(_arg("--taban", str(VARSAYILAN_TABAN)))
    cikti_yol = _arg("--cikti")

    if cikti_yol:
        cy = pathlib.Path(cikti_yol)
        if not cy.is_file():
            print(f"P0 OZT-01 --cikti dosyasi yok: {cy} — envanter OLCULEMEDI, kapi ACILMAZ")
            print("OZTEST-ATTEST FAIL — P0=1 P1=0")
            sys.exit(1)
        # utf-8-sig: BOM'lu dosyada ilk kimlik yutulup asilsiz OZT-02 uretiliyordu.
        ham = cy.read_text(encoding="utf-8-sig")
    else:
        try:
            r = subprocess.run([sys.executable, "-B", str(BETIKLER / "atlas_selftest.py")],
                               capture_output=True, text=True, timeout=900)
        except subprocess.TimeoutExpired:
            print("P0 OZT-03 oz-test 900s icinde bitmedi — envanter OLCULEMEDI, kapi ACILMAZ")
            print("OZTEST-ATTEST FAIL — P0=1 P1=0")
            sys.exit(1)
        ham = (r.stdout or "") + (r.stderr or "")

    canli = kimlikleri_cikar(ham)
    bulgular = []

    def ekle(kural, siddet, aciklama):
        bulgular.append({"kural": kural, "siddet": siddet, "aciklama": aciklama})

    if uret:
        taban_yol.parent.mkdir(parents=True, exist_ok=True)
        taban_yol.write_text(json.dumps(
            {"sema": SEMA, "sayi": len(canli), "kimlikler": canli,
             "kimlik_hash": kimlik_hash(canli)},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # TEK KURAL: taban sozluk DEGILSE ya da BOS ise kapi ACILMAZ.
    # Eski surumde `taban = json.loads(...)` sonrasi `if taban is not None:` vardi;
    # `null` gecerli JSON'dur ve None'a cozulur -> TUM kontroller atlaniyordu,
    # kapi fail-OPEN idi (olculdu: PASS, exit 0). Ayrica bicimsel olarak kusursuz
    # ama BOS bir taban (kimlikler=[] + dogru hash) yalniz P1 uretiyordu.
    taban = None
    if not taban_yol.is_file():
        ekle("OZT-01", "P0", f"{taban_yol} yok — envanter tabani OLCULEMEDI, kapi ACILMAZ")
    else:
        try:
            _ham = json.loads(taban_yol.read_text(encoding="utf-8"))
        except Exception as e:
            ekle("OZT-01", "P0", f"{taban_yol} JSON gecersiz: {e} — kapi ACILMAZ")
        else:
            if not isinstance(_ham, dict):
                ekle("OZT-01", "P0", f"{taban_yol} sozluk degil "
                                     f"({type(_ham).__name__}) — kapi ACILMAZ")
            else:
                taban = _ham

    if not canli:
        ekle("OZT-03", "P0", "kosu ciktisinda hicbir test kimligi yok — "
                             "sifir test 'temiz' degildir")

    if taban is not None:
        pinli = taban.get("kimlikler")
        if not isinstance(pinli, list) or not all(isinstance(k, str) for k in pinli):
            ekle("OZT-01", "P0", f"{taban_yol} icinde gecerli `kimlikler` listesi yok "
                                 f"(hepsi metin olmali) — kapi ACILMAZ")
        elif not pinli:
            ekle("OZT-01", "P0", f"{taban_yol} kimlik listesi BOS — bos taban hicbir testi "
                                 f"korumaz, kapi ACILMAZ")
        elif taban.get("sema") != SEMA:
            ekle("OZT-01", "P0", f"{taban_yol} semasi beklenen {SEMA} degil: "
                                 f"{taban.get('sema')!r} — kapi ACILMAZ")
        else:
            if taban.get("sayi") != len(pinli):
                ekle("OZT-01", "P0", f"{taban_yol} `sayi` alani ({taban.get('sayi')}) kimlik "
                                     f"sayisiyla ({len(pinli)}) tutmuyor — taban elle degistirilmis")
            beklenen = taban.get("kimlik_hash")
            gercek = kimlik_hash(pinli)
            if beklenen != gercek:
                ekle("OZT-06", "P0",
                     f"taban kimlik_hash'i listesiyle tutmuyor "
                     f"(kayitli {beklenen}, hesaplanan {gercek}) — taban elle degistirilmis")

            eksik = sorted(set(pinli) - set(canli))
            if eksik:
                ekle("OZT-02", "P0", "tabanda olup bu kosuda OLMAYAN test: " + ", ".join(eksik))

            yeni = sorted(set(canli) - set(pinli))
            if yeni:
                ekle("OZT-05", "P1", "tabanda olmayan YENI test: " + ", ".join(yeni)
                                     + " — `--uret` ile taban guncellenmeli")

    p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
    p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
    rapor = {"sema": "OZTEST-ATTEST/v1", "canli_sayi": len(canli), "canli": canli,
             "taban_sayi": (taban or {}).get("sayi"), "p0": p0, "p1": p1,
             "bulgular": bulgular,
             "kalan_risk": "Testin YOKLUGUNU olcer, BOSLUGUNU olcmez; "
                           "--uret ile taban yeniden uretilerek ihlal silinebilir."}
    if json_cik:
        print(json.dumps(rapor, ensure_ascii=False, indent=2))
    else:
        for b in bulgular:
            print(f"{b['siddet']} {b['kural']} {b['aciklama']}")
        print(f"envanter: canli={len(canli)} taban={(taban or {}).get('sayi')}")
        print(f"OZTEST-ATTEST {'FAIL' if p0 else 'PASS'} — P0={p0} P1={p1}")
    sys.exit(1 if p0 else 0)


if __name__ == "__main__":
    _main()
