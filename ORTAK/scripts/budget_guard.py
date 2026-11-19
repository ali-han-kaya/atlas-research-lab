#!/usr/bin/env python3
"""Atlas v5.5.4 Budget Guard — GERCEK harcamayi okur, tahmin etmez

TEK KAYNAK (O7-06, WP4 kapandi): bu dosya `ORTAK/scripts/budget_guard.py`
master'dir. `KOD_SABLONLAR/scripts/` ve `ATLAS_SABLONLAR/scripts/` altindaki
nusmalar BAYT BIREBIR kopyadir; sapma olursa `kod_selftest` BG-1 kirmizi verir.
Wrapper/symlink BILINCLI SECILMEDI: OLCUM-02 K1'de symlink sablon hedefe
kopyalaninca kiriliyordu (canli olculdu) ve ATLAS hattinin kurulum
mekanizmasi yoktur; ozdes-kopya + hash-sinari deseni kurulum yollarini
dokunmadan birakir.

NEDEN YENIDEN YAZILDI (bagimsiz denetim, 23.08.2026):
Onceki surum uc cikti dosyasinin BAYT boyutunu 4'e bolup makale basina SABIT
$0.80 / $1.15 varsayiyordu. Olculen gercek: `~/.local/share/opencode/opencode.db`
icinde 6.736 asistan mesaji, TOPLAM $180.07 harcanmis; `.atlas_budget.json`
hic olusmamis. Yani koruma faturanin %0'ini goruyordu ve 9-20x sapiyordu.

Dort yapisal kusur duzeltildi:
  1. YANLIS EKSEN: maliyet surucusu kumulatif GIRDI'dir (ajanli dongude her
     adimda tum baglam yeniden gonderilir), uretilen artefaktin boyutu degil.
  2. MODEL KORLUGU: opus-5 ile deepseek-v4-flash arasinda 102x fiyat farki var;
     eski surum ikisini ayni sayiyordu.
  3. CACHE KORLUGU: olculen faturada cache okuma kalemi %77'ye kadar cikiyor
     (opencode-go/glm-5.3: $48.87'nin $37.65'i). Modelde hic yoktu.
  4. FAIL-OPEN: butce dosyasi `sys.exit(1)`'den ONCE yaziliyordu; asim tespit
     edildiginde para zaten harcanmisti. Ayrica esik `>` idi, tam limitte geciyordu.

KULLANIM:
  python3 scripts/budget_guard.py --report          # salt okunur durum
  python3 scripts/budget_guard.py --preflight FAZ3  # faz ONCESI fail-closed kapi
  python3 scripts/budget_guard.py --kaydet          # kosuyu deftere isle
"""
import json, os, pathlib, sqlite3, sys, uuid as uuidlib
from datetime import datetime, timezone

# OLCUM-P0-4 (31.08.2026): bu iki yol KULLANICI HESABINA baglidir. Oz-test
# kendi ilkesine ("tum fikstirler gecici klasorde kurulur") ragmen bu ortam
# durumuna bagimliydi; opencode.db bulunmayan bir makinede BG-4 daima
# KALDI verirdi. Varsayilan DEGISMEDI — yalniz enjekte edilebilir yapildi.
DB = pathlib.Path(os.environ.get("ATLAS_OPENCODE_DB")
                  or os.path.expanduser("~/.local/share/opencode/opencode.db"))
KAT = pathlib.Path(os.environ.get("ATLAS_MODEL_KATALOG")
                   or os.path.expanduser("~/.cache/opencode/models.json"))
BUTCE = pathlib.Path(".atlas_budget.json")
LIMIT = float(os.environ.get("ATLAS_BUDGET_LIMIT", "30.0"))
# KOD hatti KFAZ0..KFAZ5 kullanir; akademik hat FAZ0..FAZ4. Ikisi de burada.
# OLCUM-02 K3: bu dosya ATLAS surumune symlink'ti ve yalniz FAZ* taniyordu;
# `/kod-faz0` adim 2 (`--preflight KFAZ0`) exit=1 aliyordu ve komutun kendi
# kurali geregi hat ILK MAKINE KOMUTUNDA duruyordu (canli olculdu).
FAZ_LIMIT = {"FAZ0": 0.30, "FAZ1": 0.60, "FAZ2": 1.00, "FAZ3": 1.60, "FAZ4": 0.60,
             "KFAZ0": 0.30, "KFAZ1": 0.60, "KFAZ2": 1.00, "KFAZ3": 0.60,
             "KFAZ4": 0.60, "KFAZ5": 0.30}

FILES = [
    "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md",
    "01-FAZ-1-LENS-ANALYSIS.json",
    "02-FAZ-2-FIX-MANIFEST.md",
    "03-FAZ-3-MASTER-v5.5.md",
    "04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md",
]


def donem():
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _uuid_duzelt(deger):
    """Yalniz kanonik, tek satirlik UUID degerlerini kabul et."""
    if not isinstance(deger, str):
        return None
    aday = deger.strip()
    try:
        duzeltilmis = str(uuidlib.UUID(aday))
    except (AttributeError, ValueError):
        return None
    return duzeltilmis if aday.lower() == duzeltilmis else None


def _cwd_duzelt(yol):
    """CWD/alias yollarini symlink ve macOS /var alias farkindan arindir."""
    if not isinstance(yol, str) or not yol.strip() or not os.path.isabs(yol):
        return None
    return os.path.realpath(os.path.abspath(os.path.expanduser(yol)))


def proje_uuid_bul(baslangic=None):
    """Env override veya CWD'den yukari .lab_proje_uuid tara."""
    if "ATLAS_PROJE_UUID" in os.environ:
        return _uuid_duzelt(os.environ.get("ATLAS_PROJE_UUID"))
    kok = pathlib.Path(baslangic or os.getcwd()).expanduser().resolve()
    for dizin in (kok, *kok.parents):
        kimlik = dizin / ".lab_proje_uuid"
        if not kimlik.is_file():
            continue
        try:
            satirlar = kimlik.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            return None
        return _uuid_duzelt(satirlar[0]) if len(satirlar) == 1 else None
    return None


def izinli_cwd_listesi(proje_uuid, mevcut_cwd=None):
    """Mevcut proje yolu ile UUID'ye bagli tarihsel alias yollarini dondur."""
    mevcut = _cwd_duzelt(str(mevcut_cwd or os.getcwd()))
    if mevcut is None:
        return [], "PROJE_KIMLIK_JSON_BOZUK: mevcut CWD mutlak yol degil"
    izinli = [mevcut]
    alias_yolu = os.environ.get("ATLAS_PROJE_KIMLIK_DOSYASI")
    if not alias_yolu:
        return izinli, None
    try:
        veri = json.loads(pathlib.Path(alias_yolu).read_text(encoding="utf-8"))
        if not isinstance(veri, dict):
            raise ValueError("kok JSON nesnesi degil")
        aliaslar = veri.get(proje_uuid, [])
        if not isinstance(aliaslar, list):
            raise ValueError("UUID alias degeri liste degil")
        for alias in aliaslar:
            duzeltilmis = _cwd_duzelt(alias)
            if duzeltilmis is None:
                raise ValueError("alias mutlak yol degil")
            if duzeltilmis not in izinli:
                izinli.append(duzeltilmis)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as e:
        return [], f"PROJE_KIMLIK_JSON_BOZUK: {type(e).__name__}: {e}"
    return izinli, None


def _cwd_izinli_mi(mesaj_cwd, izinli_yollar):
    mesaj = _cwd_duzelt(mesaj_cwd)
    if mesaj is None:
        return False
    for kok in izinli_yollar:
        try:
            if os.path.commonpath([kok, mesaj]) == kok:
                return True
        except ValueError:
            continue
    return False


def gercek_harcama(proje=None, donem_str=None):
    """opencode.db'den GERCEK faturayi oku. Tahmin degil — opencode'un kendi kaydi.

    Doner: (toplam, {model: tutar}, mesaj_sayisi, durum_notu)"""
    izinli_yollar = []
    if proje is not None:
        proje_uuid = proje_uuid_bul(proje)
        if proje_uuid is None:
            return 0.0, {}, 0, ("PROJE_KIMLIGI_YOK: ATLAS_PROJE_UUID veya "
                                  ".lab_proje_uuid icinde gecerli UUID bulunamadi")
        izinli_yollar, kimlik_hatasi = izinli_cwd_listesi(proje_uuid, proje)
        if kimlik_hatasi:
            return 0.0, {}, 0, kimlik_hatasi
    if not DB.exists():
        return 0.0, {}, 0, f"OLCULMEDI: opencode.db yok ({DB})"
    try:
        con = sqlite3.connect(f"file:{DB}?immutable=1", uri=True)
    except Exception as e:
        return 0.0, {}, 0, f"OLCULMEDI: veritabani acilamadi ({e})"
    top, per, n = 0.0, {}, 0
    try:
        for (d,) in con.execute("SELECT data FROM message"):
            try:
                m = json.loads(d)
            except Exception:
                continue
            if m.get("role") != "assistant":
                continue
            c = m.get("cost")
            if not isinstance(c, (int, float)):
                continue
            if donem_str:
                ts = ((m.get("time") or {}).get("created") or 0) / 1000
                if not ts or datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m") != donem_str:
                    continue
            if proje is not None:
                cwd = ((m.get("path") or {}).get("cwd") or "")
                if not _cwd_izinli_mi(cwd, izinli_yollar):
                    continue
            k = f"{m.get('providerID','?')}/{m.get('modelID','?')}"
            per[k] = per.get(k, 0.0) + c
            top += c
            n += 1
    except Exception as e:
        return top, per, n, f"KISMI: okuma yarida kesildi ({e})"
    finally:
        con.close()
    return top, per, n, "OK"


def fiyatlar():
    if not KAT.exists():
        return {}
    try:
        return json.loads(KAT.read_text())
    except Exception:
        return {}


def faz_tahmini(faz):
    return FAZ_LIMIT.get(str(faz).upper())


def token_ozeti():
    t = 0
    for f in FILES:
        try:
            t += pathlib.Path(f).stat().st_size // 4
        except Exception:
            pass
    return t


# ------------------------------------------------------------------ CLI
arg = sys.argv[1:]
rapor = "--report" in arg
kaydet = "--kaydet" in arg
pref = None
if "--preflight" in arg:
    i = arg.index("--preflight")
    pref = arg[i + 1] if i + 1 < len(arg) else "?"

d = donem()
# Limit PROJE basinadir ($30/ay/proje). Varsayilan filtre: calisma dizini.
# --kuresel, --proje de verilse tum proje kimligi/CWD filtrelerini bypass eder.
proje = os.getcwd()
if "--proje" in arg:
    i = arg.index("--proje")
    proje = arg[i + 1] if i + 1 < len(arg) else proje
if "--kuresel" in arg:
    proje = None
toplam, per_model, n, durum = gercek_harcama(proje=proje, donem_str=d)
kur_top, _, kur_n, _ = gercek_harcama(donem_str=d)
tok = token_ozeti()
kimlik_hatasi = durum.startswith(("PROJE_KIMLIGI_YOK", "PROJE_KIMLIK_JSON_BOZUK"))

kapsam = "TUM PROJELER" if proje is None else f"proje: {os.path.basename(str(proje)) or proje}"
print(f"Token: {tok} | Donem: {d} | Kaynak: opencode.db ({durum})")
print(f"GERCEK harcama ({kapsam}): ${toplam:.2f} / ${LIMIT:.2f}  ({n} asistan mesaji)")
if proje is not None:
    print(f"  bilgi — bu donem TUM projeler: ${kur_top:.2f} ({kur_n} mesaj)")
if per_model:
    for k, v in sorted(per_model.items(), key=lambda x: -x[1])[:5]:
        print(f"    ${v:7.2f}  {k}")
if durum.startswith("OLCULMEDI"):
    print("UYARI: gercek harcama OLCULEMEDI — bu bir 'temiz' sonuc DEGILDIR.")
if kimlik_hatasi:
    print(f"UYARI: {durum}")

# --- preflight: faz BASLAMADAN fail-closed ---
if pref:
    tahmin = faz_tahmini(pref)
    if tahmin is None:
        print(f"FAIL: bilinmeyen faz '{pref}' (beklenen: {list(FAZ_LIMIT)})")
        sys.exit(1)
    if kimlik_hatasi:
        print(f"FAIL preflight {pref}: {durum}")
        sys.exit(1)
    if durum.startswith("OLCULMEDI"):
        print(f"FAIL preflight {pref}: harcama olculemedigi icin kapi ACILMAZ (fail-closed).")
        sys.exit(1)
    print(f"Preflight {pref}: mevcut ${toplam:.2f} + faz tahmini ${tahmin:.2f} = ${toplam + tahmin:.2f}")
    if toplam + tahmin >= LIMIT:
        print(f"FAIL preflight {pref}: limit asilacak (${toplam + tahmin:.2f} >= ${LIMIT:.2f}). Faz BASLATILMADI.")
        sys.exit(1)
    print(f"OK preflight {pref}: butce yeterli.")
    sys.exit(0)

# --- kaydet: SIRA ONEMLI — once kontrol, sonra yazma ---
if kaydet and not rapor:
    if kimlik_hatasi:
        print(f"FAIL: {durum} — defter YAZILMADI.")
        sys.exit(1)
    if toplam >= LIMIT:
        print(f"FAIL: butce asildi (${toplam:.2f} >= ${LIMIT:.2f}) — defter YAZILMADI, kosu durduruldu.")
        sys.exit(1)
    try:
        veri = json.loads(BUTCE.read_text()) if BUTCE.exists() else {}
    except Exception:
        veri = {}
    if veri.get("period") != d:
        veri = {"period": d, "history": []}
    veri["spent_real"] = round(toplam, 4)
    veri["by_model"] = {k: round(v, 4) for k, v in per_model.items()}
    veri.setdefault("history", []).append({
        "date": datetime.now(timezone.utc).isoformat(),
        "spent_real": round(toplam, 4), "tokens_artifact": tok,
    })
    veri["history"] = veri["history"][-100:]
    BUTCE.write_text(json.dumps(veri, indent=2, ensure_ascii=False))
    print(f"Defter guncellendi: {BUTCE}")

if kimlik_hatasi:
    print(f"FAIL: {durum}")
    sys.exit(1)
if toplam >= LIMIT:
    print(f"FAIL: butce asildi ${toplam:.2f} >= ${LIMIT:.2f}")
    sys.exit(1)
print("OK: budget icinde")
sys.exit(0)
