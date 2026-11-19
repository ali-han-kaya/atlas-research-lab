#!/usr/bin/env python3
"""teslim_imza — ATLAS teslim manifestinin BUTUNLUGU ve HMAC imzasi (CHK-TESLIM, P1-4)

NEDEN VAR:
P0 kosusunun kapanmamis OLCULMEYEN #1'i: `git tag -s v1.7.75` -> `gpg failed to
sign the data`, exit 128. Imza anahtari yapilandirilmamisti, dolayisiyla iki tag
de IMZASIZ atildi. Sonuc: "su surumde sunu teslim ettim" iddiasinin makine
tarafindan dogrulanabilir bir karsiligi YOKTU.

KOD hattinda bu cozulmus: `imzala.py` BASELINE.json'u HMAC-SHA256 ile imzalar,
`freeze_check` dogrular. Bu betik ayni mekanizmayi ATLAS'a tasir.

IKI KATMAN, BIRBIRINDEN BAGIMSIZ:
  1) BUTUNLUK (anahtarsiz calisir) — teslim artefaktlarinin sha256'lari
     manifeste yazilir ve commit'lenir. Bir artefakt sonradan degistirilirse
     hash tutmaz. Bu katman HER MAKINEDE calisir, anahtar gerektirmez.
  2) IMZA (anahtar varsa) — manifestin kendisi HMAC ile imzalanir. Boylece
     "artefakti degistirip hash'i de guncelleyen" saldirgan yakalanir.

Katman 1 tek basina da degerlidir: imzasiz bir tag'den daha guclu kanit verir,
cunku hash'ler git tarihine islenir.

ANAHTAR ASLA KENDILIGINDEN URETILMEZ (KOD hattindan bilincli SAPMA):
`imzala.py` anahtar yoksa olusturur. Burada olusturmuyoruz. Sebep olculdu:
imzalayan makine ile dogrulayan makine farkli olabilir (bulut VM'i ile Ali'nin
Mac'i). Bir tarafta kendiliginden anahtar uretilirse obur tarafta imza GECERSIZ
gorunur ve YANLIS ALARM uretir. Anahtar yoksa manifest imzasiz yazilir, dogrulama
TSL-05 ile DUSUK_GUVEN (P1) der ve kapiyi KAPATMAZ — mevcut teslimler kirilmaz.
Anahtar uretmek Ali'nin acik karari olmali:  openssl rand -hex 32 > ~/.config/lab_imza.key

KURALLAR (CHK-TESLIM)
  TSL-01  manifest yok / bozuk           -> kapi ACILMAZ (fail-closed)      [P0]
  TSL-02  manifestte listelenen dosya diskte YOK                           [P0]
  TSL-03  dosya sha256'si manifesttekiyle tutmuyor -> TAHRIFAT             [P0]
  TSL-04  imza var ama GECERSIZ -> manifest tahrif edilmis / baska anahtar  [P0]
  TSL-05  imza YOK -> DUSUK_GUVEN, kapi kapanmaz                           [P1]
  TSL-06  ZORUNLU teslim artefakti manifestte hic yok -> kapsam eksigi      [P0]

TSL-06 NICIN VAR:
TSL-02/03 olmadan bir kisi tek dosyalik bir manifest yazip imzalayabilir ve
"teslim dogrulandi" diyebilirdi. Kapsam kontrolu olmayan butunluk kontrolu
vacuous'tur: neyin butun oldugunu soyler, NEYIN EKSIK oldugunu soylemez.

KALAN RISK (acikca yazilir, kapatilmaz):
Anahtara erisebilen biri artefakti degistirip manifesti yeniden imzalayabilir.
HMAC simetriktir: imzalayan ile dogrulayan ayni anahtari bilir, dolayisiyla bu
mekanizma DIS bir tarafa kanit sunmaz — yalniz sonradan-degistirmeyi yakalar.
Tek kisilik labda kabul edilen sinir budur (bkz. P1-4 sartnamesi: "Ed25519/ZIP-215
dogrulayici YAZMA"). Ayrica manifest neyin teslim edildigini olcer, teslim edilenin
DOGRU oldugunu olcmez.

NEDEN --full ZINCIRINDE DEGIL:
Ali'nin 31.08 karari (--mutabakat icin verildi, ayni gerekce burada da gecerli):
teslim asamasina gelmemis bir projede --full kirilirdi. --teslim ayri kosulur.

Kullanim:
  python3 scripts/teslim_imza.py --uret        # hash'leri hesapla, manifesti yaz
  python3 scripts/teslim_imza.py --dogrula     # butunluk + imza dogrula
  bash    scripts/check_integrity.sh --teslim  # ayni dogrulama, kapi olarak
"""
import hashlib
import hmac
import json
import re
import os
import pathlib
import sys

__test__ = False

MANIFEST = "TESLIM-MANIFEST.json"
SEMA = "ATLAS-TESLIM/v1"

# check_integrity.sh'in fazlarda ZORUNLU tuttugu teslim artefaktlari.
ZORUNLU = [
    "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md",
    "01-FAZ-1-LENS-ANALYSIS.json",
    "02-FAZ-2-FIX-MANIFEST.md",
    "03-FAZ-3-MASTER-v5.5.md",
    "04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md",
    "gate/STRONG-gate-2a-v5.5.json",
    "gate/STRONG-gate-2b-v5.5.json",
    "gate/FINAL-GATE-v5.5.json",
]


def sha256(yol: pathlib.Path) -> str:
    h = hashlib.sha256()
    with yol.open("rb") as f:
        for parca in iter(lambda: f.read(65536), b""):
            h.update(parca)
    return "sha256:" + h.hexdigest()


ANAHTAR_BICIM = re.compile(r"^[0-9a-fA-F]{32,}$")


def _gecerli_anahtar(ham):
    """En az 32 hex hane (16 bayt). Gecersizse None — utf-8'e DUSMEZ.

    Eski surumde `hmac_hex` `bytes.fromhex` basarisiz olunca sessizce
    `anahtar.encode("utf-8")` yapiyordu: 1 karakterlik bir anahtar dosyasi
    8 BITLIK bir HMAC uretip "imzalandi" diye raporlaniyordu (olculdu).
    Dogrulama tek yerde toplandi; iki yol (ortam ve dosya) ayni suzgecten gecer.
    """
    ham = (ham or "").strip()
    return ham if ANAHTAR_BICIM.match(ham) else None


def anahtar_bul():
    """Once ORTAM, sonra dosya. ASLA URETMEZ. Gecersiz anahtar KABUL EDILMEZ."""
    env = _gecerli_anahtar(os.environ.get("LAB_IMZA_ANAHTARI", ""))
    if env:
        return env, "env:LAB_IMZA_ANAHTARI"
    for aday in (pathlib.Path.home() / ".config" / "lab_imza.key",
                 pathlib.Path(".lab_imza.key")):
        if aday.is_file():
            try:
                ham = aday.read_text(encoding="utf-8").strip()
            except (UnicodeDecodeError, OSError):
                return None, f"GECERSIZ:{aday}"
            iyi = _gecerli_anahtar(ham)
            if iyi:
                return iyi, str(aday)
            return None, f"GECERSIZ:{aday}"
    return None, None


def _tekil_cift(ciftler):
    gorulen = set()
    for k, _ in ciftler:
        if k in gorulen:
            raise ValueError(f"yinelenen JSON anahtari: {k}")
        gorulen.add(k)
    return dict(ciftler)


def kanonik(d: dict) -> bytes:
    kopya = {k: v for k, v in d.items() if k != "imza"}
    return json.dumps(kopya, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def hmac_hex(anahtar: str, veri: bytes) -> str:
    # Gecersiz anahtar buraya HIC ULASMAZ (_gecerli_anahtar suzer). Yine de
    # savunma amacli sert davran: sessizce zayif anahtara DUSME.
    key = bytes.fromhex(anahtar)
    if len(key) < 16:
        raise ValueError("anahtar 16 bayttan kisa")
    return hmac.new(key, veri, hashlib.sha256).hexdigest()


def _main():
    uret = "--uret" in sys.argv
    json_cik = "--json" in sys.argv
    man = pathlib.Path(MANIFEST)
    anahtar, kaynak = anahtar_bul()

    if uret:
        # DOWNGRADE KORUMASI: daha once imzalanmis bir manifest, anahtar yokken
        # yeniden uretilemez. Aksi halde saldirgan artefakti degistirip tek
        # komutla butun hash'leri tazeler ve imzayi dusurur (olculdu).
        if man.is_file() and not anahtar:
            try:
                _eski = json.loads(man.read_text(encoding="utf-8"))
            except Exception:
                _eski = None
            if isinstance(_eski, dict) and _eski.get("imza"):
                print("FAIL: mevcut manifest IMZALI ama anahtar yok — imzasiz "
                      "yeniden uretim REDDEDILDI (downgrade korumasi)")
                return 1
        dosyalar = {}
        eksik_diskte = []
        for ad in ZORUNLU:
            p = pathlib.Path(ad)
            if p.is_file():
                dosyalar[ad] = sha256(p)
            else:
                eksik_diskte.append(ad)
        d = {"sema": SEMA, "dosyalar": dosyalar}
        if anahtar:
            d["imza"] = hmac_hex(anahtar, kanonik(d))
        man.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        if anahtar:
            durum = f"imzalandi (kaynak {kaynak})"
        elif kaynak and str(kaynak).startswith("GECERSIZ:"):
            # Sessiz zayiflama YERINE acik ret. Eski surumde 1 baytlik bir anahtar
            # dosyasi "imzalandi" diye raporlanip 8 BITLIK HMAC uretiyordu (olculdu).
            durum = (f"IMZASIZ — anahtar dosyasi GECERSIZ ({kaynak[9:]}): "
                     "en az 32 hex hane gerekli, zayif anahtarla imzalanmadi")
        else:
            durum = ("IMZASIZ — anahtar yok; uretilmedi. Olusturmak icin: "
                     "openssl rand -hex 32 > ~/.config/lab_imza.key")
        print(f"OK {MANIFEST} yazildi — {len(dosyalar)} dosya, {durum}")
        if eksik_diskte:
            print("FAIL diskte olmayan zorunlu artefakt: " + ", ".join(eksik_diskte))
            return 1
        return 0

    bulgular = []

    def ekle(kural, siddet, aciklama):
        bulgular.append({"kural": kural, "siddet": siddet, "aciklama": aciklama})

    # Manifest okuma. TEK KURAL: sozluk DEGILSE kapi ACILMAZ.
    # Eski surumde `d = json.loads(...)` sonrasi `if d is not None:` vardi;
    # `null` gecerli JSON'dur ve None'a cozulur, dolayisiyla TUM kapilar
    # atlaniyordu — kapi fail-OPEN idi (olculdu: `TESLIM PASS`, exit 0).
    d = None
    if not man.is_file():
        ekle("TSL-01", "P0", f"{MANIFEST} yok — teslim OLCULEMEDI, kapi ACILMAZ")
    else:
        try:
            ham = json.loads(man.read_text(encoding="utf-8"),
                             object_pairs_hook=_tekil_cift)
        except Exception as e:
            ekle("TSL-01", "P0", f"{MANIFEST} JSON gecersiz: {e} — kapi ACILMAZ")
        else:
            if isinstance(ham, dict):
                d = ham
            else:
                ekle("TSL-01", "P0", f"{MANIFEST} sozluk degil "
                                     f"({type(ham).__name__}) — kapi ACILMAZ")

    if isinstance(d, dict) and d.get("sema") != SEMA:
        ekle("TSL-01", "P0", f"{MANIFEST} semasi beklenen {SEMA} degil: {d.get('sema')!r}")

    if isinstance(d, dict):
        dosyalar = d.get("dosyalar")
        if not isinstance(dosyalar, dict):
            ekle("TSL-01", "P0", f"{MANIFEST} icinde `dosyalar` sozlugu yok — kapi ACILMAZ")
            dosyalar = {}

        kapsam_disi = [a for a in ZORUNLU if a not in dosyalar]
        if kapsam_disi:
            ekle("TSL-06", "P0", "ZORUNLU artefakt manifestte yok: " + ", ".join(kapsam_disi))

        for ad, beklenen in sorted(dosyalar.items()):
            if not (isinstance(beklenen, str)
                    and re.fullmatch(r"sha256:[0-9a-fA-F]{64}", beklenen)):
                ekle("TSL-01", "P0", f"{ad} icin hash bicimi gecersiz "
                     f"({beklenen!r}) — sha256:<64 hex> gerekli")
                continue
            p = pathlib.Path(ad)
            if not p.is_file():
                ekle("TSL-02", "P0", f"manifestte listelenen dosya diskte YOK: {ad}")
                continue
            gercek = sha256(p)
            if gercek != beklenen:
                ekle("TSL-03", "P0",
                     f"TAHRIFAT: {ad} hash tutmuyor "
                     f"(manifest {beklenen[:22]}..., disk {gercek[:22]}...)")

        # VARLIK ile GECERLILIK ayrilir. Eski surumde `if not imza:` yuzunden
        # imza alanini null/""/0/[] yapmak imzayi SIYIRIP kapiyi aciyordu (P1).
        # Artik: alan HIC YOKSA P1 (eski imzasiz teslimler kirilmasin),
        # alan VAR ama gecersizse P0.
        imza_var = "imza" in d
        imza = d.get("imza")
        gecerli_bicim = isinstance(imza, str) and re.fullmatch(r"[0-9a-fA-F]{64}", imza.strip())
        if not imza_var:
            ekle("TSL-05", "P1", "manifest IMZASIZ (alan hic yok) — DUSUK_GUVEN. Butunluk "
                                 "hash'leri gecerli ama manifestin kendisi korumasiz")
        elif not gecerli_bicim:
            ekle("TSL-04", "P0", f"`imza` alani VAR ama gecerli 64-hane hex DEGIL ({imza!r}) — "
                                 "imza siyirma girisimi veya bozuk manifest")
        elif kaynak and str(kaynak).startswith("GECERSIZ:"):
            ekle("TSL-04", "P0", f"imza dogrulanamadi: anahtar dosyasi gecersiz ({kaynak[9:]})")
        elif not anahtar:
            ekle("TSL-05", "P1", "manifest imzali ama anahtar bu makinede YOK — imza "
                                 "DOGRULANMADI (DUSUK_GUVEN), yanlis alarm uretilmedi")
        elif not hmac.compare_digest(imza.strip().lower(),
                                     hmac_hex(anahtar, kanonik(d)).lower()):
            ekle("TSL-04", "P0", "imza GECERSIZ — manifest tahrif edilmis veya baska "
                                 f"anahtarla imzalanmis (kaynak {kaynak})")

    p0 = sum(1 for b in bulgular if b["siddet"] == "P0")
    p1 = sum(1 for b in bulgular if b["siddet"] == "P1")
    if json_cik:
        print(json.dumps({"sema": "TESLIM-ATTEST/v1", "p0": p0, "p1": p1,
                          "bulgular": bulgular}, ensure_ascii=False, indent=2))
    else:
        for b in bulgular:
            print(f"{b['siddet']} {b['kural']} {b['aciklama']}")
        print(f"TESLIM {'FAIL' if p0 else 'PASS'} — P0={p0} P1={p1}")
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(_main())
