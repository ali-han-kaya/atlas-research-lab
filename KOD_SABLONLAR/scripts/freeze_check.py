#!/usr/bin/env python3
"""freeze_check — dondurulmus bolgeler ve kapi altyapisi bozulmamis mi

NEDEN VAR:
TASARIM-KOD-HATTI.md "en buyuk 3 risk" §1: `kod_profil.json` ele gecirilirse
(`"test_komutu": "true"`) butun kapilar sahte yesil olur. Hicbir kapi bunu
goremez, cunku hepsi o profile bakar. Tek savunma, profilin ve kapi
betiklerinin SHA256'sini KFAZ0'da dondurup her faz sinirinda karsilastirmaktir.

`GATE_TAMPERED` TERMINAL bir P0'dir: hat durur, dongu sayaci artmaz, insan
karari olmadan devam edilmez. Sebep: kapiyi degistiren bir kosunun kendi
kapisina verdigi karar anlamsizdir.

KURALLAR
  FRZ-01  `kod_profil.json` SHA256 tabandan farkli            [GATE_TAMPERED P0 TERMINAL]
  FRZ-02  Kapi betigi (scripts/*.py|sh) SHA256 farkli         [GATE_TAMPERED P0 TERMINAL]
  FRZ-03  KFAZ1'de dondurulan dosya degismis                                     [P0]
  FRZ-04  Tabanda kayitli dosya artik yok                                        [P0]
  FRZ-05  BASELINE.json yok / okunamiyor        [CALISTIRILMADI P1 + OLCULMEYEN]
  FRZ-06  BASELINE.json SEMASI eksik            [CALISTIRILMADI P0 — FAIL-CLOSED]
  FRZ-07  Taban KIRLI agacta olculmus (`temiz_agac`: false)
                                               [POISONED_BASELINE P0]

FRZ-06 NICIN EKLENDI (OLCUM-02, 24.08.2026):
Ilk canli kosuda KFAZ0 ajani tabani `{"sha256": {"kod_profil.json": "..."}}`
bicimiyle yazdi; bu betik ise UST DUZEY `kod_profil_sha256` arar. Sonuc: hicbir
hash karsilastirilmadi ama cikti `PASS` ve **exit=0** oldu. Kurcalanmis bir
profille bile ayni sonuc alindi (olculdu). Yani tasarimin 1 numarali riskine
karsi yazilan birincil savunma SESSIZCE etkisizdi.

Artik: taban DOSYASI var ama dondurma alanlari yoksa bu bir PASS degil,
CALISTIRILAMAMIS bir kontroldur ve P0'dir. "Sessiz temiz" yoktur; exit kodu
da bunu soyler.

Kullanim: python3 scripts/freeze_check.py [--taban _KOSU/gate/BASELINE.json] [--json]
"""
import hashlib, json, pathlib, re, sys

JSON_CIK = "--json" in sys.argv
taban_yol = pathlib.Path("_KOSU/gate/BASELINE.json")
if "--taban" in sys.argv:
    i = sys.argv.index("--taban")
    if i + 1 < len(sys.argv):
        taban_yol = pathlib.Path(sys.argv[i + 1])


def sha(p):
    h = hashlib.sha256()
    h.update(pathlib.Path(p).read_bytes())
    return h.hexdigest()


if not taban_yol.exists():
    msg = (f"FRZ-05 {taban_yol} yok — dondurma kontrolu CALISTIRILMADI. "
           f"Bu 'temiz' demek DEGILDIR; OLCULMEYEN kaydi acilmalidir.")
    print(("P1 " + msg) if not JSON_CIK else json.dumps(
        {"sema": "FREEZE-CHECK/v1", "durum": "CALISTIRILMADI", "not": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)

taban = json.loads(taban_yol.read_text())
bulgular = []
terminal = False

# ------------------------------------------------ FRZ-06 SEMA (fail-closed)
# Bir alanin YOKLUGU ile BOS OLMASI ayni sey degildir:
#   yok  -> taban eksik yazilmis, kontrol CALISTIRILAMAZ  -> P0
#   bos  -> "donduracak sey yok" BEYANI vardir            -> P1 (kayda gecer)
_SEMA_P0 = ("kod_profil_sha256", "scripts_sha256")
for _alan in _SEMA_P0:
    if _alan not in taban:
        bulgular.append({"kural": "FRZ-06", "siddet": "P0", "kod": "CALISTIRILMADI",
                         "konum": str(taban_yol),
                         "aciklama": f"tabanda `{_alan}` anahtari YOK — dondurma kontrolu "
                                     f"CALISTIRILAMAZ. Bu 'temiz' DEGILDIR"})
if "dondurulan" not in taban:
    bulgular.append({"kural": "FRZ-06", "siddet": "P1", "kod": "CALISTIRILMADI",
                     "konum": str(taban_yol),
                     "aciklama": "tabanda `dondurulan` anahtari yok — KFAZ1 dondurma "
                                 "beyani izlenemiyor"})
if isinstance(taban.get("scripts_sha256"), dict) and not taban["scripts_sha256"]:
    bulgular.append({"kural": "FRZ-06", "siddet": "P1", "konum": str(taban_yol),
                     "aciklama": "`scripts_sha256` BOS — hicbir kapi betigi dondurulmamis; "
                                 "kapi betigini degistiren bir kosu yakalanamaz"})
for _alan in ("scripts_sha256", "dondurulan"):
    if _alan in taban and not isinstance(taban[_alan], dict):
        bulgular.append({"kural": "FRZ-06", "siddet": "P0", "kod": "CALISTIRILMADI",
                         "konum": str(taban_yol),
                         "aciklama": f"`{_alan}` sozluk degil ({type(taban[_alan]).__name__})"})

# ------------------------------------------- FRZ-07 TABAN KIRLILIGI (O3-04)
# OLCUM-03 O3-04 (24.08.2026): taban KIRLI agacta olculurse (once kod+test
# yazilmis, SONRA BASELINE kaydedilmis) yeni test adlari `test_adlari`na
# sizar; RECK-07'nin "tabanda OLMAYAN test" ayirt edicisi ile test_attest'in
# `kosan>=taban` kurali ayni anda etkisizlesir (olculdu: kosan=9 >= taban=9).
#
# FRZ-07: yakalama anindaki agac durumu tabana YAZILIR (`temiz_agac`).
#   false     -> taban zehirlidir: POISONED_BASELINE P0
#   alan yok  -> eski tabanlar icin BILGI (geriye donuk uyum); yeni tabanlarda
#                alanin dogru yazilmasi kos_faz.sh kod-faz0 temiz-agac kapisiyla
#                saglanir. Alanin BOS/None olmasi da "bilinmiyor" sayilir.
_ta = taban.get("temiz_agac", None)
if _ta is False:
    bulgular.append({"kural": "FRZ-07", "siddet": "P0", "kod": "POISONED_BASELINE",
                     "konum": str(taban_yol),
                     "aciklama": "taban KIRLI agacta olculmus (`temiz_agac`: false) — "
                                 "yeni testler tabana sismis olabilir; RECK-07 ve "
                                 "`kosan>=taban` ayirt edicileri zehirlenmistir. "
                                 "Tabani TEMIZ agacta yeniden olcun"})
elif _ta is None:
    bulgular.append({"kural": "FRZ-07", "siddet": "BILGI", "konum": str(taban_yol),
                     "aciklama": "tabanda `temiz_agac` alani YOK (eski taban) — "
                                 "yakalama anindaki agac durumu bilinmiyor"})

# ------------------------------------------- FRZ-08 IMZALI TABAN (C4, TUR-8 WP4)
# Kalinti risk: temiz_agac:true yazan sahte tabani yalniz imza ayirir.
#   imzali + gecerli  -> yuksek guven (BILGI)
#   imzali + gecersiz -> P0 TAMPERED
#   temiz:true + imzasiz -> P1 DUSUK_GUVEN (mevcut tabanlar kirilmaz, kademeli)
#   temiz:false/None  -> FRZ-07 zaten P0/BILGI, burada ek is yok
try:
    _imza = taban.get("temiz_agac_imzasi")
    if _ta is True:
        if not _imza:
            bulgular.append({"kural": "FRZ-08", "siddet": "P1", "kod": "DUSUK_GUVEN",
                             "konum": str(taban_yol),
                             "aciklama": "temiz_agac:true ama `temiz_agac_imzasi` YOK — "
                                         "DUSUK_GUVEN (eski/imzasiz taban; imzala.py ile imzala)"})
        else:
            # anahtar ara (olusturma YOK, yalniz ara)
            _ana = None; _kaynak = None
            import os as _os
            _env = _os.environ.get("LAB_IMZA_ANAHTARI", "").strip()
            if _env and len(_env) >= 32 and all(c in "0123456789abcdefABCDEF" for c in _env.replace("-", "").replace("_","")):
                _ana = _env
            else:
                for _cand in (pathlib.Path.home() / ".config" / "lab_imza.key",
                              pathlib.Path("KOD_SABLONLAR/.lab_imza.key"),
                              pathlib.Path(".lab_imza.key")):
                    if _cand.exists():
                        try: _ana = _cand.read_text().strip(); _kaynak = str(_cand); break
                        except: pass
            if not _ana:
                bulgular.append({"kural": "FRZ-08", "siddet": "P1", "kod": "DUSUK_GUVEN",
                                 "konum": str(taban_yol),
                                 "aciklama": "temiz_agac:true ve imzasi var ama anahtar bulunamadi — "
                                             "dogrulanamadi (anahtar ~/.config/lab_imza.key)"})
            else:
                import hmac as _hmac, hashlib as _hl, json as _js
                _kanonik = _js.dumps({k: v for k, v in taban.items() if k != "temiz_agac_imzasi"},
                                     sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                try: _key = bytes.fromhex(_ana.strip())
                except: _key = _ana.encode("utf-8")
                _bek = _hmac.new(_key, _kanonik, _hl.sha256).hexdigest()
                if _hmac.compare_digest(str(_imza).strip(), _bek):
                    bulgular.append({"kural": "FRZ-08", "siddet": "BILGI", "kod": "IMZALI",
                                     "konum": str(taban_yol),
                                     "aciklama": "temiz_agac:true ve imzasi GECERLI — yuksek guven"})
                else:
                    bulgular.append({"kural": "FRZ-08", "siddet": "P0", "kod": "TAMPERED",
                                     "konum": str(taban_yol),
                                     "aciklama": "temiz_agac:true ama imzasi GECERSIZ — "
                                                 "taban baska anahtarla imzalanmis veya tahrif edilmis"})
                    terminal = True
except Exception as _e:
    bulgular.append({"kural": "FRZ-08", "siddet": "P1", "kod": "CALISTIRILMADI",
                     "konum": str(taban_yol),
                     "aciklama": f"imza kontrolu CALISTIRILMADI: {_e}"})

# FRZ-01 kod_profil.json
beklenen = taban.get("kod_profil_sha256")
profil = pathlib.Path(taban.get("kod_profil_yolu", "kod_profil.json"))
if beklenen:
    if not profil.exists():
        bulgular.append({"kural": "FRZ-01", "siddet": "P0", "kod": "GATE_TAMPERED",
                         "konum": str(profil), "aciklama": "profil dosyasi KAYIP"}); terminal = True
    elif sha(profil) != beklenen:
        bulgular.append({"kural": "FRZ-01", "siddet": "P0", "kod": "GATE_TAMPERED", "konum": str(profil),
                         "aciklama": f"SHA256 degismis (taban {beklenen[:12]}… != simdi {sha(profil)[:12]}…) — "
                                     f"imzali muafiyet yoksa UNSIGNED_WAIVER"}); terminal = True
elif "kod_profil_sha256" in taban:
    # anahtar var ama BOS: acik bir "dondurmuyorum" beyani -> P0 degil ama sessiz de degil
    bulgular.append({"kural": "FRZ-01", "siddet": "P0", "kod": "CALISTIRILMADI",
                     "konum": str(profil),
                     "aciklama": "tabanda kod_profil_sha256 BOS — profil dondurulmamis"})
# anahtarin hic olmamasi durumu FRZ-06'da P0 olarak kaydedildi

# FRZ-02 kapi betikleri — B3 (26.08.2026, OLCUM-06)
# Canli kosuda ajan anahtari ciplak yazdi ("api_surface.py") ve dogru hash'e
# ragmen `pathlib.Path("api_surface.py").exists()` false oldugu icin 12×
# yanlis GATE_TAMPERED P0 terminal uretti. Veri dogru, bicim farkliydi.
# Anahtar bicimi goreceli yol ve "scripts/" onekli olmalidir; ciplak ad
# SCHEMA_INVALID P0 verir ve TERMINAL'e DUSMEZ — karar yanlis terminal degil,
# acik bicim hatasi olur.
for yol, beklenen_h in (taban.get("scripts_sha256") or {}).items():
    if not isinstance(yol, str) or "/" not in yol or not yol.startswith("scripts/") or ".." in yol:
        bulgular.append({"kural": "FRZ-02", "siddet": "P0", "kod": "SCHEMA_INVALID", "konum": str(yol),
                         "aciklama": f"BASELINE.scripts_sha256 anahtari '{yol}' bicim disidir — "
                                     f"beklenen 'scripts/*.py' goreceli yolu (or. 'scripts/chg_reconcile.py'); "
                                     f"ciplak dosya adi ile yazilan taban KAP KAYIP gibi gorunur ve "
                                     f"yanlis GATE_TAMPERED terminali uretirdi. Anahtari duzelt."})
        continue
    if not isinstance(beklenen_h, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", beklenen_h.strip() or ""):
        bulgular.append({"kural": "FRZ-02", "siddet": "P0", "kod": "SCHEMA_INVALID", "konum": str(yol),
                         "aciklama": f"BASELINE.scripts_sha256['{yol}'] hash degeri 64-hex degil: "
                                     f"{beklenen_h!r} — beklenen 64 karakterlik hex SHA256"})
        continue
    p = pathlib.Path(yol)
    if not p.exists():
        bulgular.append({"kural": "FRZ-02", "siddet": "P0", "kod": "GATE_TAMPERED", "konum": yol,
                         "aciklama": "kapi betigi KAYIP"}); terminal = True
    elif sha(p) != beklenen_h:
        bulgular.append({"kural": "FRZ-02", "siddet": "P0", "kod": "GATE_TAMPERED", "konum": yol,
                         "aciklama": "kapi betigi DEGISMIS — kendi kapisini degistiren kosunun "
                                     "kararı anlamsizdir"}); terminal = True

# ===================================================== O3-06  FRZ-03 CANLANDIRMA
# OLCUM-03 O3-06: FRZ-03 OLU KURALDI. `dondurulan` YALNIZ BASELINE.json'dan
# okunuyordu; taban KFAZ0'da, dondurma karari HENUZ YOKKEN yazilir ve hicbir
# betik `BASELINE.dondurulan`'i doldurmaz. Sonuc: KFAZ1 plani dosya dondursa
# bile freeze_check "0 dondurulan dosya · PASS" diyordu (OLCUM-04'te plan
# `['_KOSU/gate/BASELINE.json']` dondurmustu, kapi gormedi).
#
# Artik KFAZ1 planinin `dondurulan` LISTESI de okunur ve tabandakiyle
# BIRLESTIRILIR. Plan yalniz YOL verir, hash vermez; beklenen hash su sirayla
# cozulur:
#   1) taban["dondurulan"][yol]          (varsa — en guclu)
#   2) taban["kod_profil_sha256"]        (yol profil dosyasiysa)
#   3) taban["scripts_sha256"][yol]      (yol bir kapi betigiyse)
#   4) yan dosya _KOSU/gate/FREEZE-PLAN.json  (ilk gorusta yazilir)
#
# (4)'UN SINIRI ACIKCA YAZILIR: ilk freeze_check kosusundan ONCE degistirilmis
# bir dosya "dondurulmus hali" olarak kaydedilir. Bu yuzden (4) ile korunan her
# yol icin BILGI satiri basilir; (1)-(3) ile korunanlar tam guvencelidir.
_plan_dondurulan = []
_kosu_dizin = pathlib.Path("_KOSU")
if "--kosu" in sys.argv:
    _i = sys.argv.index("--kosu")
    if _i + 1 < len(sys.argv):
        _kosu_dizin = pathlib.Path(sys.argv[_i + 1])
_plan_adaylar = sorted(_kosu_dizin.glob("01-KFAZ-1-*.md"))
if _plan_adaylar:
    try:
        _m = re.search(r"```json(.*?)```", _plan_adaylar[0].read_text(errors="ignore"), re.S)
        if _m:
            _pj = json.loads(_m.group(1))
            _pl = _pj.get("dondurulan")
            if isinstance(_pl, list):
                _plan_dondurulan = [x for x in _pl if isinstance(x, str) and x.strip()]
                if not _plan_dondurulan:
                    bulgular.append({"kural": "FRZ-03", "siddet": "BILGI",
                                     "konum": _plan_adaylar[0].name,
                                     "aciklama": "KFAZ1 plani var ama `dondurulan` BOS — "
                                                 "donduracak bolge beyan edilmemis"})
    except Exception as _e:
        bulgular.append({"kural": "FRZ-03", "siddet": "P1", "kod": "CALISTIRILMADI",
                         "konum": _plan_adaylar[0].name,
                         "aciklama": f"KFAZ1 plani okunamadi: {_e} — plan dondurmasi DENETLENMEDI"})

_yan_yol = _kosu_dizin / "gate" / "FREEZE-PLAN.json"
_yan = {}
if _yan_yol.exists():
    try:
        _yan = json.loads(_yan_yol.read_text())
    except Exception:
        _yan = {}

_birlesik = dict(taban.get("dondurulan") or {})
_yan_degisti = False
for _yol in _plan_dondurulan:
    if _yol in _birlesik:
        continue
    _p = pathlib.Path(_yol)
    _bek = None
    if _yol == taban.get("kod_profil_yolu", "kod_profil.json"):
        _bek = taban.get("kod_profil_sha256") or None
    elif _yol in (taban.get("scripts_sha256") or {}):
        _bek = taban["scripts_sha256"][_yol]
    elif _yol in _yan:
        _bek = _yan[_yol]
    elif _p.is_file():
        _bek = sha(_p)
        _yan[_yol] = _bek
        _yan_degisti = True
        bulgular.append({"kural": "FRZ-03", "siddet": "BILGI", "kod": "ILK_KAYIT",
                         "konum": _yol,
                         "aciklama": "plan dondurmasi ILK KEZ kaydedildi (FREEZE-PLAN.json); "
                                     "bu kosudan ONCEKI degisiklikler yakalanamaz"})
    if _bek:
        _birlesik[_yol] = _bek
    elif not _p.exists():
        bulgular.append({"kural": "FRZ-04", "siddet": "P0", "konum": _yol,
                         "aciklama": "KFAZ1 plani bu dosyayi DONDURDU ama dosya YOK"})
if _yan_degisti:
    try:
        _yan_yol.parent.mkdir(parents=True, exist_ok=True)
        _yan_yol.write_text(json.dumps(_yan, ensure_ascii=False, indent=2))
    except Exception as _e:
        bulgular.append({"kural": "FRZ-03", "siddet": "P1", "kod": "CALISTIRILMADI",
                         "konum": str(_yan_yol),
                         "aciklama": f"FREEZE-PLAN.json yazilamadi: {_e}"})

# FRZ-03/04 dondurulan bolgeler
for yol, beklenen_h in _birlesik.items():
    p = pathlib.Path(yol)
    if not p.exists():
        bulgular.append({"kural": "FRZ-04", "siddet": "P0", "konum": yol,
                         "aciklama": "dondurulan dosya artik yok"})
    elif sha(p) != beklenen_h:
        bulgular.append({"kural": "FRZ-03", "siddet": "P0", "konum": yol,
                         "aciklama": "DONDURULMUS bolge degismis — KFAZ1 plani ihlal edildi"})

p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
rapor = {"sema": "FREEZE-CHECK/v1", "taban": str(taban_yol), "terminal": terminal,
         "p0": p0, "bulgular": bulgular,
         "kontrol_edilen": {"profil": 1 if beklenen else 0,
                            "betik": len(taban.get("scripts_sha256") or {}),
                            "dondurulan": len(_birlesik)}}
if JSON_CIK:
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
else:
    for b in bulgular:
        print(f"{b['siddet']} {b['kural']} {b.get('kod','')} {b['konum']}: {b['aciklama']}")
    if terminal:
        print("FREEZE-CHECK TERMINAL FAIL — GATE_TAMPERED. Hat DURUR, dongu sayaci artmaz, "
              "insan karari olmadan devam edilmez.")
    else:
        _kars = (1 if beklenen else 0) + len(taban.get('scripts_sha256') or {}) \
                + len(_birlesik)
        _ek = "" if _kars else "  [HICBIR HASH KARSILASTIRILMADI]"
        print(f"FREEZE-CHECK {'FAIL' if p0 else 'PASS'} — "
              f"profil+{len(taban.get('scripts_sha256') or {})} betik+"
              f"{len(_birlesik)} dondurulan dosya · P0={p0}{_ek}")
sys.exit(2 if terminal else (1 if p0 else 0))
