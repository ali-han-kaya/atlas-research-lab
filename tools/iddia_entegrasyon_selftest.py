#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDDIA ENTEGRASYON TESTI — gercek public dokumanlarin gecici kopyasinda
sozluk disi bir sayisal iddiayi `make iddia` ile kirmizi yakala.

Her vaka gercek README.md, README.en.md, docs/README.md ve
docs/EN/QUICKSTART.md dosyalarindan gecici bir kok kurar; defterin tum
alintilarini dogrulayabilmesi icin diger public README'ler de kopyalanir. Hedef dosyanin sonuna eski
`OLCUM_SOZCUK` listesinde bulunmayan bir sayisal iddia eklenir ve gecici kokte
GERCEK `make iddia` hedefi kosulur.

Beklenen: rc=2, `KAPSAM FAIL — 1 sayisal iddia`, `dosya:satir` ve `'jeton'`.
Ayrica gercek public dosyalarin baytlari test oncesi/sonrasi ayni kalmalidir.

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
PUBLIC = (
    "README.md",
    "README.tr.md",
    "README.en.md",
    "docs/README.md",
    "docs/EN/QUICKSTART.md",
)
DESTEK = (
    "Makefile",
    "tools/iddia.py",
    "tools/kapi_cikti.py",
    "tools/iddia_defteri.json",
    "schemas/atlas-kapi-cikti.schema.json",
    "docs/IDDIA-OZET.md",
)
# Sozlukte olmayan olcum adlari: eski OLCUM_SOZCUK bunlari tanimiyordu.
VAKALAR = (
    ("README.md", "SISTEM 12 agents"),
    ("README.en.md", "SISTEM 12 agents"),
    ("docs/README.md", "AKIS 5 phases"),
    ("docs/EN/QUICKSTART.md", "SISTEM 13 artifacts"),
)
ZAMAN_ASIMI = 120


def _kopyala(kok):
    kaynaklar = set(PUBLIC)
    defter = json.loads((KOK / "tools" / "iddia_defteri.json").read_text(
        encoding="utf-8"))
    # Ham kanit yolu defterdeki alandan gelir; DESTEK'te sabitlenmez.
    kaynaklar.add(defter["olcum_dosyasi"])
    for kayit in defter["iddialar"]:
        for kaynak in kayit.get("kaynaklar", []):
            if kaynak.get("dosya"):
                kaynaklar.add(kaynak["dosya"])
    for rel in sorted(kaynaklar) + list(DESTEK):
        hedef = kok / rel
        hedef.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(KOK / rel, hedef)


def _sha(yol):
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def _satir_ekle(metin, eklenti):
    """Dosya sonuna tek satir ekle; eklenecek satirin 1-tabanli numarasini ver."""
    if metin and not metin.endswith("\n"):
        metin += "\n"
    return metin + eklenti + "\n", metin.count("\n") + 1


def _make_iddia(kok):
    env = os.environ.copy()
    env["PY"] = sys.executable
    return subprocess.run(
        ["make", "iddia"], cwd=str(kok), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=ZAMAN_ASIMI)


def main():
    hatalar = []
    toplam = 0

    def bekle(ad, kosul, ayrinti=""):
        nonlocal toplam
        toplam += 1
        if kosul:
            print("PASS  " + ad)
        else:
            print("FAIL  " + ad)
            if ayrinti:
                print("      " + ayrinti.replace("\n", "\n      ")[-1800:])
            hatalar.append(ad)

    gercek = {rel: (KOK / rel).read_bytes() for rel in PUBLIC}
    with tempfile.TemporaryDirectory(prefix="iddia-entegrasyon-") as gecici:
        for sira, (rel, eklenti) in enumerate(VAKALAR, 1):
            kok = Path(gecici) / ("vaka-%d" % sira)
            _kopyala(kok)
            bekle("%s: gecici kopya gercek dosyayla ayni" % rel,
                  (kok / rel).read_bytes() == gercek[rel],
                  "kopya hash=%s kaynak hash=%s"
                  % (_sha(kok / rel), hashlib.sha256(gercek[rel]).hexdigest()))
            metin = gercek[rel].decode("utf-8")
            bekle("%s: iddia gercek dosyada yok" % rel,
                  eklenti not in metin, "gercek dosyada zaten var: %s" % eklenti)

            yeni, satir_no = _satir_ekle(
                (kok / rel).read_text(encoding="utf-8"), eklenti)
            (kok / rel).write_text(yeni, encoding="utf-8")
            jeton = re.search(r"\d+", eklenti).group(0)

            try:
                r = _make_iddia(kok)
            except (OSError, subprocess.SubprocessError) as exc:
                bekle("%s: make iddia kosuldu" % rel, False, str(exc))
                continue
            cikti = (r.stdout or "") + (r.stderr or "")
            bekle("%s: make iddia rc=2" % rel, r.returncode == 2, cikti)
            bekle("%s: tek kapsam ihlali" % rel,
                  "KAPSAM FAIL — 1 sayisal iddia" in cikti, cikti)
            bekle("%s:%d dosya:satir ile adlandirildi" % (rel, satir_no),
                  "%s:%d" % (rel, satir_no) in cikti, cikti)
            bekle("%s: '%s' jetonuyla adlandirildi" % (rel, jeton),
                  "'%s'" % jeton in cikti, cikti)
            bekle("%s: HUKUM KAPSAM BOZUK" % rel,
                  "HUKUM: KAPSAM BOZUK" in cikti, cikti)

        for rel, once in gercek.items():
            bekle("%s: gercek dosya degismedi" % rel,
                  (KOK / rel).read_bytes() == once,
                  "once=%s sonra=%s" % (
                      hashlib.sha256(once).hexdigest(), _sha(KOK / rel)))

    if hatalar:
        print("\nIDDIA ENTEGRASYON: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nIDDIA ENTEGRASYON: PASS — %d/%d" % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())