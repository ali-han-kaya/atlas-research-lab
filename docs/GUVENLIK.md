# Bagimlilik guvenligi — `pip-audit`

Kaynak: `tools/guvenlik.py` · olcum: 2026-11-19 · hedef: `requirements-dev.txt`

| Olcum | Deger |
|---|---|
| Toplam bulgu | 12 |
| Kabul edilmis (duzeltme yayimlanmamis) | 12 |
| Kabul edilmemis (yeni) | 0 |

| Paket | Surum | ID | Duzeltme | Durum |
|---|---|---|---|---|
| filelock | 3.19.1 | GHSA-69hj-f68j-2879 | 4.2.1 | kabul: duzeltme 4.2.1 PyPI da yayimlanmamis (pip-audit bagimliligi) |
| filelock | 3.19.1 | GHSA-8mx5-7m5m-r77g | 4.2.1 | kabul: duzeltme 4.2.1 PyPI da yayimlanmamis (pip-audit bagimliligi) |
| filelock | 3.19.1 | PYSEC-2026-1374 | 3.20.3 | kabul: duzeltme 3.20.3 PyPI da yayimlanmamis (pip-audit bagimliligi) |
| filelock | 3.19.1 | PYSEC-2026-1375 | 3.20.1 | kabul: duzeltme 3.20.1 PyPI da yayimlanmamis (pip-audit bagimliligi) |
| msgpack | 1.1.2 | GHSA-j586-36cw-2gc2 | 1.2.3 | kabul: duzeltme 1.2.3 PyPI da yayimlanmamis (pip-audit bagimliligi) |
| msgpack | 1.1.2 | PYSEC-2026-3625 | 1.2.1 | kabul: duzeltme 1.2.1 PyPI da yayimlanmamis (pip-audit bagimliligi) |
| requests | 2.32.5 | PYSEC-2026-2275 | 2.33.0 | kabul: duzeltme 2.33.0 PyPI da yayimlanmamis (pip download ile olculdu) |
| urllib3 | 2.6.3 | PYSEC-2026-141 | 2.7.0 | kabul: duzeltme 2.7.0 PyPI da yayimlanmamis |
| urllib3 | 2.6.3 | PYSEC-2026-142 | 2.7.0 | kabul: duzeltme 2.7.0 PyPI da yayimlanmamis (pip download ile olculdu) |
| urllib3 | 2.6.3 | PYSEC-2026-4175 | 2.8.0 | kabul: duzeltme 2.8.0 PyPI da yayimlanmamis |
| urllib3 | 2.6.3 | PYSEC-2026-4176 | 2.8.0 | kabul: duzeltme 2.8.0 PyPI da yayimlanmamis |
| urllib3 | 2.6.3 | PYSEC-2026-4177 | 2.8.0 | kabul: duzeltme 2.8.0 PyPI da yayimlanmamis |

## Neden muafiyet var

Her satirin duzeltme surumu PyPI da aranmis ve BULUNAMAMISTIR;
bu yuzden sabitlemek mumkun degildi. Muafiyet sessiz degil:
listede olmayan bir bulgu cikarsa `make guvenlik` kirmizi doner.
Duzeltme yayimlandiginda satir silinir ve surum sabitlenir.
