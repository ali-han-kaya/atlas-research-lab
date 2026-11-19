#!/usr/bin/env python3
"""kod_gate_merge — KFAZ4 kapi birlestirici (2-of-2 / 3-of-3)

Kapi ilkeleri BU DOSYADA DEGIL, `ORTAK/scripts/ortak_gate.py` icindedir.
Buradan kopyalanmaz, import edilir: bir ilke duzeldiginde iki hat birden duzelir.

Kullanim:
  python3 scripts/kod_gate_merge.py _KOSU/gate/KOD-gate-2a.json _KOSU/gate/KOD-gate-2b.json
  python3 scripts/kod_gate_merge.py 2a.json 2b.json 2c.json      # guvenlik oyu dahil
Cikti: _KOSU/gate/FINAL-KOD-GATE.json  ·  exit 0 = PASS/PASS-PENDING-ETHICS, 1 = FAIL
"""
import hashlib, json, os, pathlib, sys
from datetime import datetime, timezone

_BURASI = pathlib.Path(__file__).resolve().parent
for _aday in (_BURASI.parent.parent / "ORTAK" / "scripts", _BURASI.parent / "ORTAK" / "scripts"):
    if (_aday / "ortak_gate.py").exists():
        sys.path.insert(0, str(_aday))
        break
else:
    print("FAIL: ORTAK/scripts/ortak_gate.py bulunamadi — kapi ilkeleri tek kaynaktan gelir, "
          "kopyalanmaz. Hat eksik kurulmus.")
    sys.exit(1)

# ORTAK/ agacina .pyc YAZMA: import suresince bytecode yazimi kapatilir ve
# eski haline dondurulur (secret_scan.py'deki kalibin aynisi). Aksi halde her
# kosu `ORTAK/scripts/__pycache__/` uretir; silinse de geri gelir.
_onceki_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    import ortak_gate as og  # noqa: E402
finally:
    sys.dont_write_bytecode = _onceki_bytecode

yollar = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(yollar) not in (2, 3):
    print("Kullanim: kod_gate_merge.py <2a.json> <2b.json> [2c.json]")
    sys.exit(1)

etiketler = ["2A", "2B", "2C"][:len(yollar)]
kapilar, sonuclar, imzalar, okuma_hatalari = [], [], [], []

for yol, et in zip(yollar, etiketler):
    d, hata = og.yukle(yol)
    if hata:
        okuma_hatalari.append(f"{et} ({yol}): {hata}")
        continue
    kapilar.append(d)
    sonuclar.append(og.degerlendir(d, et))
    imzalar.append(og.imza(d))

if okuma_hatalari:
    print("FAIL: kapi dosyasi okunamadi -> " + " | ".join(okuma_hatalari))
    sys.exit(1)

verdict, notlar = og.birlestir(sonuclar, imzalar)

# --- kod hattina ozgu ek kural: 2C yalniz KOSULLU cagirilir, ama cagirildiysa oyu tam sayilir
mod = f"{len(yollar)}-of-{len(yollar)}"

ozet = " ".join(f"{s['etiket']}={s['gercek_verdict']}(P0:{s['p0']},P1:{s['p1']})" for s in sonuclar)
gerekce = f"{mod} {ozet} -> {verdict}"

cikti = {
    "sema": "FINAL-KOD-GATE/v1",
    "mod": mod,
    "verdict": verdict,
    "gerekce": gerekce,
    "kapilar": sonuclar,
    "ihlaller": notlar,
    "olusturuldu": datetime.now(timezone.utc).isoformat(),
    "girdi_dosyalari": yollar,
    # Tazelik denetimi mtime'a birakilmaz: ayni saniye icinde yeniden yazilan bir
    # kapi dosyasi mtime karsilastirmasindan kacar. check_code_integrity.sh bu
    # ozetleri yeniden hesaplayip karsilastirir.
    "girdi_sha256": {y: hashlib.sha256(pathlib.Path(y).read_bytes()).hexdigest() for y in yollar},
}

hedef = pathlib.Path("_KOSU/gate/FINAL-KOD-GATE.json")
hedef.parent.mkdir(parents=True, exist_ok=True)
hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=2), encoding="utf-8")

for n in notlar:
    print(f"IHLAL {n}")
print(gerekce)
# v1.7.282 (KOD GM-9): gerekceli red P0/P1 sayilmaz ama GORUNUR kalir.
_red = [r for s in sonuclar for r in (s.get("reddedilen") or [])]
if _red:
    print(f"REDDEDILEN_GEREKCELI: {len(_red)} "
          + " ".join(f"{r['fix_id']}={r['status']}"
                     + ("!GEREKCE-YOK" if r['gerekce'] == "(gerekce yok)" else "")
                     for r in _red))
print(f"yazildi: {hedef}")
sys.exit(0 if verdict in ("PASS", "PASS-PENDING-ETHICS") else 1)
