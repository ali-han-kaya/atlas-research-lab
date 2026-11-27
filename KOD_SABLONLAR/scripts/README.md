# scripts/ — tek kaynak haritasi

Bu dizindeki betiklerin menseleri (O7-04, SURUM v1.7.19):

| Betik        | Mensei                                                                 |
|--------------|------------------------------------------------------------------------|
| budget_guard.py   | `ORTAK/scripts/budget_guard.py` master'inin BAYT BIREBIR nusnasi (O7-06); sapmayi `kod_selftest` BG-1 hash testi yakalar |
| apply_routing.py  | `ORTAK/scripts/apply_routing.py` master'inin BAYT BIREBIR nusnasi (O7-07); kapı bagimsizlik kontrolü önek-notrdur |
| kod_gate_merge.py | kapı ilkelerini `ORTAK/scripts/ortak_gate.py`'den IMPORT eder |
| katalog_kontrol.py | **TEK KAYNAK** — canlı models.dev kapısı. Labda `tools/katalog_kontrol.py` ince uyumluluk girişidir; hedef projeye `kur.sh` bu dosyayı `scripts/` altına, allowlist'i `model_katalog.json` olarak ve CI workflow'unu `.github/workflows/` altına kurar |
| check_models.py   | **BU AGACTA YOK** — tek kaynak `ATLAS_SABLONLAR/scripts/check_models.py` |

check_models icin wrapper/symlink BILINÇLI YOKTUR: `kur.sh` yalniz bu agaci
hedef depoya tasir; `../ATLAS_SABLONLAR` referansi hedefte KIRILIR
(OLCUM-02 K1 ile ayni ariza sinifi). Lab'dan koşmak:

    python3 ATLAS_SABLONLAR/scripts/check_models.py

Bu dosya kurulumla hedef depoya da tasinir; hedefte yalnizca bilgi amaçlidir.

## Canli katalog kapisi

Kurulumdan sonra hedef projede iki komut vardir:

```bash
# yalniz bedava profili (on rol + canli models.dev)
python3 scripts/katalog_kontrol.py --profil-only

# allowlist + bedava profili; CI workflow'u bu komutu kosar
python3 scripts/katalog_kontrol.py \
  --katalog model_katalog.json \
  --profil-dosya routing.profiles.json
```

`rc=0` yalniz butun kosullar saglandiginda; `rc=1` adlandirilmis ihlal; `rc=2`
`OLCULMEDI` (ag/JSON/okuma). `rc=2` PASS sayilmaz. `kur.sh` hedefte ayni
workflow yolu varsa dokunmaz; proje kendi workflow'unu korur.
