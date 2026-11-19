#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atomik_yaz.py — durum dosyalarini YARIM BIRAKMADAN yaz.

NEDEN VAR (12 Kasim 2026, OLCULDU): lab'in durum dosyalari (`kapi_taban.json`,
`mutasyon_defteri.json`, surum tabanlari) soyle yaziliyordu:

    json.dump(veri, open(yol, 'w', encoding='utf-8'))

Iki kusur birden:
  1) `open(yol, 'w')` dosyayi ONCE KISALTIR. `json.dump` ortada hata verirse
     hedef YARIM JSON kalir. Olculdu: 44 baytlik dosya 9 bayta dustu ve icerik
     `{"veri": ` oldu — yani `taban` bozuldu, `C14u` bir daha calismaz.
  2) Dosya nesnesi `close()` EDILMIYOR; CPython'da GC'ye kalir. Uzun omurlu bir
     surecte yazma gecikebilir.

COZUM: ayni dizinde gecici dosyaya yaz -> `flush` + `os.fsync` -> `os.replace`
(atomik, ayni dosya sistemi icinde). Hata olursa gecici dosya silinir ve HEDEF
DOSYAYA DOKUNULMAMIS olur.
"""

import json
import os
import tempfile


def yaz_json(yol, veri, indent=1, sort_keys=True, son_satir=True):
    """`veri`yi JSON olarak `yol`a ATOMIK yaz.

    Hata durumunda hedef dosya **degismez**. Donus: yazilan bayt sayisi.
    """
    hedef = os.path.abspath(yol)
    dizin = os.path.dirname(hedef) or '.'
    os.makedirs(dizin, exist_ok=True)

    # Gecici dosya AYNI dizinde olmali: `os.replace` ancak ayni dosya sistemi
    # icinde atomiktir; /tmp'ye yazip tasimak atomik olmaz.
    fd, gecici = tempfile.mkstemp(dir=dizin, prefix='.atomik-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(veri, f, ensure_ascii=False, indent=indent,
                      sort_keys=sort_keys)
            if son_satir:
                f.write('\n')
            f.flush()
            os.fsync(f.fileno())   # diske indi mi — replace oncesi garanti
        n = os.path.getsize(gecici)
        os.replace(gecici, hedef)  # ATOMIK: ya eski ya yeni, yarim YOK
        return n
    except Exception:
        # Yarim gecici dosya BIRAKMA; hedefe hic dokunulmadi.
        try:
            os.unlink(gecici)
        except OSError:
            pass
        raise
