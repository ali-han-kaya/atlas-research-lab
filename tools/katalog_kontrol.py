#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lab uyumluluk giris noktasi — katalog kapisinin tek kaynagi KOD sablonudur.

Gercek uygulama: `KOD_SABLONLAR/scripts/katalog_kontrol.py`.
Bu dosya yalniz eski `make katalog-kontrol`, CI ve belgelerdeki `tools/...`
yolunu korur; kod burada CATALLANMAZ. Hedef projeye `kur.sh` ayni KOD
betigini `scripts/katalog_kontrol.py` olarak kopyalar.
"""
import runpy
from pathlib import Path

KAYNAK = (Path(__file__).resolve().parents[1]
          / 'KOD_SABLONLAR' / 'scripts' / 'katalog_kontrol.py')


if __name__ == '__main__':
    runpy.run_path(str(KAYNAK), run_name='__main__')
