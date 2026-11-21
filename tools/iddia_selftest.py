#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IDDIA HIZLI KIP TESTI — atlanan satirin PASS sayilmadigini kanitla.

Gecici bir kok kurulur; iddia.py oraya kopyalanir ve sahte `dogrula.py` /
`mutasyon_bataryasi.py` betikleri yalnizca kostuklarinda bir marker yazar.
Boylece "hizli kip gercekten kosmadi" iddiasi cikti metninden degil, yan etkiden
okunur.

Vakalar:
  * --hizli: hizli satir olculur, agir satirlar ATLANDI basilir, marker yok.
  * --hizli: agir satirin ham kaniti eksik olsa da hizli kosu gecerlidir.
  * tam kosu: agir kanit eksikse fail-closed rc=2; kanit tamamsa kosar.
  * --yaz --hizli: kismi anlik goruntu yazmayi reddeder, dosya degismez.
  * --hizli --sadece <agir>: olculecek satir yoksa rc=2, komut kosmaz.

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ARAC = Path(__file__).resolve().with_name("iddia.py")
HIZLI_KOMUT = ["{py}", "-c", "print('HIZLI 7/7')"]
AGIR_DOGRULA = ["{py}", "tools/dogrula.py"]
AGIR_MUTASYON = ["{py}", "tools/mutasyon_bataryasi.py"]


def _yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")


def _json_yaz(yol, veri):
    _yaz(yol, json.dumps(veri, ensure_ascii=False, indent=2) + "\n")


def _defter(kok):
    return {
        "iddialar": [
            {
                "id": "IDD-01",
                "iddia": "hizli satir",
                "kaynaklar": [{"dosya": "README.md", "alinti": "HIZLI 7/7"}],
                "durum": "OLCULDU",
                "komut": HIZLI_KOMUT,
                "ayikla": "HIZLI (\\d+/\\d+)",
                "beklenen": "7/7",
            },
            {
                "id": "IDD-02",
                "iddia": "agir dogrula",
                "kaynaklar": [{"dosya": "README.md", "alinti": "AGIR 3/3"}],
                "durum": "OLCULDU",
                "komut": AGIR_DOGRULA,
                "ayikla": "AGIR (\\d+/\\d+)",
                "beklenen": "3/3",
            },
            {
                "id": "IDD-03",
                "iddia": "agir mutasyon",
                "kaynaklar": [{"dosya": "README.md", "alinti": "AGIR 3/3"}],
                "durum": "OLCULDU",
                "komut": AGIR_MUTASYON,
                "ayikla": "AGIR (\\d+/\\d+)",
                "beklenen": "3/3",
            },
        ]
    }


def _hizli_kanit():
    return {
        "olcumler": {
            "IDD-01": {
                "komut": HIZLI_KOMUT,
                "rc": 0,
                "ham": "HIZLI 7/7",
                "deger": "7/7",
            }
        }
    }


def _tam_kanit():
    kanit = _hizli_kanit()
    for eid, komut in (("IDD-02", AGIR_DOGRULA),
                       ("IDD-03", AGIR_MUTASYON)):
        kanit["olcumler"][eid] = {
            "komut": komut,
            "rc": 0,
            "ham": "AGIR 3/3",
            "deger": "3/3",
        }
    return kanit


def _sahte_agir(kok, ad):
    _yaz(kok / "tools" / (ad + ".py"),
         "from pathlib import Path\n"
         "Path(__file__).with_name('%s.marker').write_text('x')\n"
         "print('AGIR 3/3')\n" % ad)


def _hazirla(kok):
    (kok / "tools").mkdir(parents=True)
    shutil.copy2(ARAC, kok / "tools" / "iddia.py")
    _yaz(kok / "README.md", "HIZLI 7/7\nAGIR 3/3\n")
    _json_yaz(kok / "tools" / "iddia_defteri.json", _defter(kok))
    _json_yaz(kok / "tools" / "iddia_olcum.json", _hizli_kanit())
    _sahte_agir(kok, "dogrula")
    _sahte_agir(kok, "mutasyon_bataryasi")


def _calistir(kok, *argumanlar):
    return subprocess.run(
        [sys.executable, str(kok / "tools" / "iddia.py")] + list(argumanlar),
        cwd=str(kok), capture_output=True, text=True, timeout=60)


def _cikti(r):
    return (r.stdout or "") + (r.stderr or "")


def _satir(cikti, eid):
    return next((s for s in cikti.splitlines() if eid in s), "")


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

    with tempfile.TemporaryDirectory(prefix="iddia-hizli-") as gecici:
        kok = Path(gecici) / "kok"
        _hazirla(kok)

        r = _calistir(kok, "--hizli")
        cikti = _cikti(r)
        bekle("hizli kosu rc=0", r.returncode == 0, cikti)
        bekle("hizli satir olculdu",
              _satir(cikti, "IDD-01").lstrip().startswith("PASS"), cikti)
        bekle("agir dogrula satiri ATLANDI",
              _satir(cikti, "IDD-02").lstrip().startswith("ATLANDI"), cikti)
        bekle("agir mutasyon satiri ATLANDI",
              _satir(cikti, "IDD-03").lstrip().startswith("ATLANDI"), cikti)
        bekle("hizli kosu agir dogrula komutunu kosmadi",
              not (kok / "tools" / "dogrula.marker").exists(), cikti)
        bekle("hizli kosu agir mutasyon komutunu kosmadi",
              not (kok / "tools" / "mutasyon_bataryasi.marker").exists(), cikti)
        bekle("ozet atlananlari ayri saydi",
              "atlandi=2" in cikti and "HIZLI — 1/1" in cikti, cikti)

        # Tam kosu hala fail-closed: agir kanit eksikse rc=2, komut kosmaz.
        r = _calistir(kok)
        cikti = _cikti(r)
        bekle("tam kosu eksik agir kanitta rc=2", r.returncode == 2, cikti)
        bekle("tam kosu eksik kaniti adlandirdi",
              "ham kanit yok" in cikti and "IDD-02" in cikti
              and "IDD-03" in cikti, cikti)

        # Kanit tamamsa varsayilan kosu iki agir komutu da kosar.
        _json_yaz(kok / "tools" / "iddia_olcum.json", _tam_kanit())
        r = _calistir(kok)
        cikti = _cikti(r)
        bekle("tam kosu tam kanitta rc=0", r.returncode == 0, cikti)
        bekle("tam kosu agir komutlari kostu",
              (kok / "tools" / "dogrula.marker").exists()
              and (kok / "tools" / "mutasyon_bataryasi.marker").exists(),
              cikti)

        # Kismi anlik goruntu tam kaniti silmemeli.
        kanit_yolu = kok / "tools" / "iddia_olcum.json"
        once = kanit_yolu.read_bytes()
        r = _calistir(kok, "--yaz", "--hizli")
        bekle("--yaz --hizli rc=2", r.returncode == 2, _cikti(r))
        bekle("--yaz --hizli kanit dosyasini degistirmedi",
              kanit_yolu.read_bytes() == once, _cikti(r))

        # Yalniz agir satir secilirse hizli kipte olculecek sey yoktur.
        for marker in ("dogrula.marker", "mutasyon_bataryasi.marker"):
            (kok / "tools" / marker).unlink(missing_ok=True)
        r = _calistir(kok, "--hizli", "--sadece", "IDD-02")
        cikti = _cikti(r)
        bekle("yalniz agir secimde rc=2", r.returncode == 2, cikti)
        bekle("yalniz agir secimde OLCULMEDI",
              "HUKUM: OLCULMEDI" in cikti, cikti)
        bekle("yalniz agir secimde komut kosmadi",
              not (kok / "tools" / "dogrula.marker").exists(), cikti)

    if hatalar:
        print("\nIDDIA OZ-TEST: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nIDDIA OZ-TEST: PASS — %d/%d" % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
