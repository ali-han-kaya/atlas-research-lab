# scripts/ — tek kaynak haritasi

Bu dizindeki betiklerin menseleri (O7-04, SURUM v1.7.19):

| Betik        | Mensei                                                                 |
|--------------|------------------------------------------------------------------------|
| budget_guard.py   | `ORTAK/scripts/budget_guard.py` master'inin BAYT BIREBIR nusnasi (O7-06); sapmayi `kod_selftest` BG-1 hash testi yakalar |
| apply_routing.py  | `ORTAK/scripts/apply_routing.py` master'inin BAYT BIREBIR nusnasi (O7-07); kapı bagimsizlik kontrolü önek-notrdur |
| kod_gate_merge.py | kapı ilkelerini `ORTAK/scripts/ortak_gate.py`'den IMPORT eder |
| check_models.py   | **BU AGACTA YOK** — tek kaynak `ATLAS_SABLONLAR/scripts/check_models.py` |

check_models icin wrapper/symlink BILINÇLI YOKTUR: `kur.sh` yalniz bu agaci
hedef depoya tasir; `../ATLAS_SABLONLAR` referansi hedefte KIRILIR
(OLCUM-02 K1 ile ayni ariza sinifi). Lab'dan koşmak:

    python3 ATLAS_SABLONLAR/scripts/check_models.py

Bu dosya kurulumla hedef depoya da tasinir; hedefte yalnizca bilgi amaçlidir.
