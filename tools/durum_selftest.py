#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DURUM NEGATIF TEST — bayatlik kapisinin gercekten reddettigini kanitla.

Testler gercek depoyu degistirmez. Her vaka icin gecici bir kok kurulur:
  * `--kontrol` once sayfayi kanonik kayitlarla karsilastirir,
  * sayfa guncelse ATLAS/KOD oz-testlerini alt surec olarak kosar,
  * sayfa, pin veya canli sonuc saptiginda rc!=0; sayfa tek sayiyla
    bozuldugunda ise tam olarak rc=1 doner.

Boylece `--kontrol` yalnizca dosya karsilastirmasi yapan bir kisayola
indirgenirse veya canli testler devre disi kalirsa bu testler kirmizi olur.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ARAC = Path(__file__).resolve().with_name("durum.py")


def _yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")


def _json_yaz(yol, veri):
    _yaz(yol, json.dumps(veri, ensure_ascii=False, indent=2) + "\n")


def _calistir(kok, *argumanlar):
    komut = [sys.executable, str(ARAC), "--kok", str(kok)] + list(argumanlar)
    return subprocess.run(komut, cwd=str(kok), capture_output=True, text=True,
                          timeout=60)


def _cikti(r):
    return (r.stdout or "") + (r.stderr or "")


def _hazirla(kok):
    """Kucuk, gercek dosya semasina uyan bir depo kok'u kur."""
    taban = {
        "sayi": 145,
        "kimlikler": ["T-%03d" % i for i in range(1, 146)],
        "kimlik_hash": "sha256:" + "0" * 64,
    }
    _json_yaz(kok / "ATLAS_SABLONLAR" / "scripts" / "OZTEST-TABAN.json", taban)

    olgular = {
        "schema": "OLGULAR/v2",
        "lab_surum": "v0-test",
        "kamu_kaniti": "attestation.json",
        "atlas_envanter_sayisi": 145,
        "atlas_son_gecen": 145,
        "kod_son_gecen": 174,
        "attest_canli": 145,
        "attest_taban": 145,
        "attest_p0": 0,
        "attest_p1": 0,
    }
    _yaz(kok / "docs" / "OLGULAR.md",
         "<!-- OLGULAR_JSON_BASLA -->\n```json\n"
         + json.dumps(olgular, ensure_ascii=False, indent=2)
         + "\n```\n<!-- OLGULAR_JSON_BITIR -->\n")

    _yaz(kok / "SURUM.md",
         "Surum: v0-test\n"
         "<!-- C15f:basla -->\n"
         "skill_lint_kontrol: 95\n"
         "skill_kapi_sayisi: 95\n"
         "SKILL_md_satir: 500\n"
         "kapi_taban_kimlik: 90\n"
         "atlas_envanter: 145\n"
         "<!-- C15f:bitti -->\n")

    _yaz(kok / "ATLAS_SABLONLAR" / "scripts" / "atlas_selftest.py",
         "from pathlib import Path\n"
         "Path(__file__).with_name('atlas.marker').write_text('calisti')\n"
         "print('OZ-TEST: 145/145 gecti')\n")
    _yaz(kok / "KOD_SABLONLAR" / "scripts" / "kod_selftest.py",
         "from pathlib import Path\n"
         "Path(__file__).with_name('kod.marker').write_text('calisti')\n"
         "print('KOD OZ-TEST: 174/174 gecti')\n")

    r = _calistir(kok, "--yaz")
    if r.returncode != 0:
        raise RuntimeError("gecici kok uretilemedi:\n" + _cikti(r))


def _kontrol(kok):
    return _calistir(kok, "--kontrol")


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

    with tempfile.TemporaryDirectory(prefix="durum-negatif-") as gecici:
        temel = Path(gecici) / "temel"
        _hazirla(temel)

        # 1) Pozitif: sayfa guncel; kapı hem sayfayi hem canli testleri kosar.
        r = _kontrol(temel)
        cikti = _cikti(r)
        marker_atlas = temel / "ATLAS_SABLONLAR" / "scripts" / "atlas.marker"
        marker_kod = temel / "KOD_SABLONLAR" / "scripts" / "kod.marker"
        bekle("pozitif kontrol GUNCEL", r.returncode == 0 and "GUNCEL" in cikti,
              cikti)
        bekle("canli ATLAS testi alt surec olarak kosuldu", marker_atlas.is_file(),
              "atlas.marker yok: " + cikti)
        bekle("canli KOD testi alt surec olarak kosuldu", marker_kod.is_file(),
              "kod.marker yok: " + cikti)

        # 2) Sayfadaki oz-test sayisi yanlis: BAYAT ve rc!=0.
        vaka = Path(gecici) / "sayfa"
        shutil.copytree(temel, vaka)
        sayfa = vaka / "docs" / "DURUM.md"
        eski = sayfa.read_text(encoding="utf-8")
        yeni = eski.replace("| ATLAS öz-testi | 145/145 |",
                            "| ATLAS öz-testi | 144/145 |")
        if yeni == eski:
            bekle("sayfa testi kurulabildi (ATLAS satiri bulundu)", False,
                  "ATLAS oz-test satiri bulunamadi")
        else:
            sayfa.write_text(yeni, encoding="utf-8")
            r = _kontrol(vaka)
            bekle("yanlis oz-test sayfasi rc=1", r.returncode == 1, _cikti(r))
            bekle("yanlis oz-test sayfasi BAYAT", "BAYAT" in _cikti(r), _cikti(r))

        # 3) Sayfadaki tek bir sayi: yalnizca SKILL.md satir degeri 500 -> 501.
        #    Kaynaklar ayni kalir; sayfa karsilastirmasi rc=1 vermeli. Canli
        #    DURUM sayfasi bu testten etkilenmemeli.
        canli_sayfa = Path(__file__).resolve().parents[1] / "docs" / "DURUM.md"
        canli_once = canli_sayfa.read_bytes()
        vaka = Path(gecici) / "tek-sayi"
        shutil.copytree(temel, vaka)
        sayfa = vaka / "docs" / "DURUM.md"
        eski = sayfa.read_text(encoding="utf-8")
        aranan = "| `SKILL.md` satır | 500 |"
        if eski.count(aranan) != 1:
            bekle("tek sayi testi kurulabildi (SKILL satiri tek)", False,
                  "SKILL satiri %d kez bulundu" % eski.count(aranan))
        else:
            yeni = eski.replace(aranan, "| `SKILL.md` satır | 501 |")
            sayfa.write_text(yeni, encoding="utf-8")
            r = _kontrol(vaka)
            cikti = _cikti(r)
            bekle("tek sayi degisikligi rc=1", r.returncode == 1, cikti)
            bekle("tek sayi degisikligi BAYAT", "BAYAT" in cikti, cikti)
        bekle("canli DURUM sayfasi degismedi",
              canli_sayfa.read_bytes() == canli_once,
              "canli docs/DURUM.md degisti")

        # 4) Pin/envanter sayisi yanlis: kaynak capraz kontrolu rc!=0.
        vaka = Path(gecici) / "pin"
        shutil.copytree(temel, vaka)
        taban_yolu = vaka / "ATLAS_SABLONLAR" / "scripts" / "OZTEST-TABAN.json"
        taban = json.loads(taban_yolu.read_text(encoding="utf-8"))
        taban["sayi"] = 144
        taban["kimlikler"] = taban["kimlikler"][:144]
        _json_yaz(taban_yolu, taban)
        r = _kontrol(vaka)
        bekle("yanlis pin/envanter rc!=0", r.returncode != 0, _cikti(r))

        # 5) Canli sonuc kanonik kayittan farkli: `--kontrol` canli testi
        #    kosmadan gecmemeli. Sahte ATLAS testi 144/144 bildirir; sayfa ve
        #    kanonik kayit 145 der. Yalnizca dosya karsilastiran bir kisayol
        #    bu vakada yanlislikla 0 dondurur ve test kirmizi olur.
        vaka = Path(gecici) / "canli"
        shutil.copytree(temel, vaka)
        _yaz(vaka / "ATLAS_SABLONLAR" / "scripts" / "atlas_selftest.py",
             "from pathlib import Path\n"
             "Path(__file__).with_name('atlas.marker').write_text('calisti')\n"
             "print('OZ-TEST: 144/144 gecti')\n")
        r = _kontrol(vaka)
        cikti = _cikti(r)
        marker = vaka / "ATLAS_SABLONLAR" / "scripts" / "atlas.marker"
        bekle("canli sonuc sapmasi rc!=0", r.returncode != 0, cikti)
        bekle("canli sonuc sapmasi FAIL", "DURUM: FAIL" in cikti, cikti)
        bekle("canli sapma icin test gercekten kosuldu", marker.is_file(),
              "atlas.marker yok: " + cikti)

    if hatalar:
        print("\nDURUM NEGATIF TEST: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nDURUM NEGATIF TEST: PASS — %d/%d" % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
