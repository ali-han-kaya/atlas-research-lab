#!/usr/bin/env python3
"""imzala — BASELINE.json icin HMAC-SHA256 imzasi (C4, WP4)

NEDEN VAR:
  Risk#2 kalintisi: yakalama ortamini ele geciren saldirgan `temiz_agac: true`
  yazarak zehirlenmis tabani temiz gibi gosterebilir. FRZ-07 bunu P0 ile yakalar
  ama yalniz `temiz_agac` alaninin ICERIGINE bakar; alanin KENDISININ
  sahte yazildigini ayiramaz. Cozum: tabanin kanonik JSON'u HMAC ile imzalanir;
  anahtar dosya sistemi disinda (veya env'de) tutulur.

  Bu betik C4'un minimal kademesidir (TUR-8):
    - anahtar yoksa olusturur (`~/.config/lab_imza.key` veya `LAB_IMZA_ANAHTARI`)
    - BASELINE.json'u kanonik hale getirir (temiz_agac_imzasi alani HARIC,
      anahtarlar sirali, bosluklar atilmis) ve HMAC-SHA256 uretir
    - imzayi `temiz_agac_imzasi` alanina yazar (ayni dosyada)
  Dogrulama `freeze_check.py` tarafindan yapilir: imza varsa ve gecerli ise
  guven yuksek; imza yoksa DUSUK_GUVEN P1 (mevcut tabanlar kirilmaz);
  imza var ama gecersiz ise P0.

Kullanim:
  python3 scripts/imzala.py                          # _KOSU/gate/BASELINE.json imzalar
  python3 scripts/imzala.py --taban yol/BASELINE.json
  python3 scripts/imzala.py --dogrula               # sadece dogrula, yazma
  python3 scripts/imzala.py --anahtar-yaz            # anahtari goster/olustur
"""
import hashlib, hmac, json, os, pathlib, sys

TABAN_VARSAYILAN = pathlib.Path("_KOSU/gate/BASELINE.json")
ANAHTAR_ADAYLARI = [
    pathlib.Path(os.environ.get("LAB_IMZA_ANAHTARI", "")) if os.environ.get("LAB_IMZA_ANAHTARI", "").strip() and len(os.environ.get("LAB_IMZA_ANAHTARI","")) < 256 and pathlib.Path(os.environ.get("LAB_IMZA_ANAHTARI","")).exists() else None,
    pathlib.Path.home() / ".config" / "lab_imza.key",
    pathlib.Path("KOD_SABLONLAR") / ".lab_imza.key",
    pathlib.Path(".lab_imza.key"),
]

def anahtar_yolu_bul():
    # Env icerigi dogrudan anahtar ise (64 hex), onu dosya yolu olarak degil icerik olarak kullan
    env_val = os.environ.get("LAB_IMZA_ANAHTARI", "").strip()
    if env_val and len(env_val) >= 32 and all(c in "0123456789abcdefABCDEF" for c in env_val.replace("-", "").replace("_","")):
        return None, env_val  # icerik
    for p in ANAHTAR_ADAYLARI:
        if p and p.exists() and p.is_file():
            return p, None
    return None, None

def anahtar_oku_veya_olustur():
    p, icerik = anahtar_yolu_bul()
    if icerik:
        return icerik.strip(), f"env:LAB_IMZA_ANAHTARI"
    if p:
        try:
            return p.read_text(encoding="utf-8").strip(), str(p)
        except (UnicodeDecodeError, OSError):
            # Var olan ama okunamayan anahtarin ustune yenisini URETME.
            # Bu yol temiz ret vermeli; aksi halde traceback ya da sessiz anahtar
            # degisimi imza zincirini guvenilmez hale getirir.
            return None, f"GECERSIZ:{p}"
    # olustur
    import secrets
    yeni = secrets.token_hex(32)
    hedef = pathlib.Path.home() / ".config" / "lab_imza.key"
    try:
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(yeni + "\n")
        # sadece sahibi okusun
        try: hedef.chmod(0o600)
        except: pass
        return yeni, str(hedef) + " (yeni olusturuldu)"
    except Exception as e:
        # fallback: KOD_SABLONLAR icine yaz (repo disi degil ama .gitignore'da olmali)
        fallback = pathlib.Path("KOD_SABLONLAR/.lab_imza.key")
        fallback.write_text(yeni + "\n")
        return yeni, str(fallback) + " (yedek konum)"

def kanonik_json(taban: dict) -> bytes:
    # imzayi kendisi HARIC tut, anahtarlar sirali, bosluk yok
    kopya = {k: v for k, v in taban.items() if k != "temiz_agac_imzasi"}
    return json.dumps(kopya, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def hmac_hex(anahtar_hex: str, veri: bytes) -> str:
    # anahtar hex ise bytes'a cevir, degilse utf-8
    try:
        key = bytes.fromhex(anahtar_hex.strip())
        if len(key) < 16:
            raise ValueError()
    except:
        key = anahtar_hex.encode("utf-8")
    return hmac.new(key, veri, hashlib.sha256).hexdigest()

def main():
    taban_yol = TABAN_VARSAYILAN
    if "--taban" in sys.argv:
        i = sys.argv.index("--taban")
        if i+1 < len(sys.argv):
            taban_yol = pathlib.Path(sys.argv[i+1])
    dogrula_sadece = "--dogrula" in sys.argv
    anahtar_goster = "--anahtar-yaz" in sys.argv

    if anahtar_goster:
        ana, kaynak = anahtar_oku_veya_olustur()
        if ana is None:
            print(f"FAIL: anahtar dosyasi GECERSIZ ({kaynak})")
            return 1
        print(f"ANAHTAR_KAYNAGI: {kaynak}")
        print(f"ANAHTAR_HEX: {ana[:12]}...{ana[-4:]} (uzunluk {len(ana)})")
        return 0

    if not taban_yol.exists():
        print(f"FAIL: {taban_yol} yok")
        return 1
    taban = json.loads(taban_yol.read_text())

    ana, kaynak = anahtar_oku_veya_olustur()
    if ana is None:
        print(f"FAIL: anahtar dosyasi GECERSIZ ({kaynak})")
        return 1
    kanonik = kanonik_json(taban)
    beklenen = hmac_hex(ana, kanonik)
    mevcut = taban.get("temiz_agac_imzasi")

    if dogrula_sadece:
        if not mevcut:
            print(f"INFO: {taban_yol} imzasiz — temiz_agac={taban.get('temiz_agac')} (DUSUK_GUVEN, eski taban olabilir)")
            return 0
        if hmac.compare_digest(str(mevcut).strip(), beklenen):
            print(f"PASS: imza gecerli — {taban_yol} (kaynak {kaynak})")
            return 0
        else:
            print(f"FAIL: imza GECERSIZ — beklenen {beklenen[:16]}... != mevcut {str(mevcut)[:16]}...")
            print(f"  Bu taban baska anahtarla imzalanmis veya tahrif edilmis olabilir.")
            return 1
    else:
        # yaz
        taban["temiz_agac_imzasi"] = beklenen
        # 2 bosluklu pretty print (BASELINE.ORNEK ile uyumlu)
        taban_yol.write_text(json.dumps(taban, ensure_ascii=False, indent=2) + "\n")
        print(f"OK: {taban_yol} imzalandi — temiz_agac={taban.get('temiz_agac')} HMAC={beklenen[:16]}... (kaynak {kaynak})")
        # dogrulamayi da goster
        return 0

if __name__ == "__main__":
    sys.exit(main())
