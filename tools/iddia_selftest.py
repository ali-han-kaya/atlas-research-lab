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
KOK = Path(__file__).resolve().parents[1]
KAPI_MODUL = KOK / "tools" / "kapi_cikti.py"
KAPI_SEMA = KOK / "schemas" / "atlas-kapi-cikti.schema.json"
OZET = ("<!-- IDDIA-OZET:BASLA -->\n"
        "olculdu=3 · ag=0 · beyan=0 · olculmedi=0\n"
        "<!-- IDDIA-OZET:BITIR -->\n")
HIZLI_KOMUT = ["{py}", "-c", "print('HIZLI 7/7')"]
AGIR_DOGRULA = ["{py}", "tools/dogrula.py"]
AGIR_MUTASYON = ["{py}", "tools/mutasyon_bataryasi.py"]


def _yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")


def _json_yaz(yol, veri):
    _yaz(yol, json.dumps(veri, ensure_ascii=False, indent=2) + "\n")


def _defter_oku(kok):
    return json.loads((kok / "tools" / "iddia_defteri.json").read_text(
        encoding="utf-8"))


def _kanit_yolu(kok, defter=None):
    """Ham kanit yolunu defterdeki tek alandan coz."""
    defter = defter or _defter_oku(kok)
    return kok / defter["olcum_dosyasi"]


def _ozet_yaz(kok, icerik=OZET):
    _yaz(kok / "docs" / "IDDIA-OZET.md", icerik)


def _kapi_modulu(kok):
    """Gerçek kökteki sözleşme modülünü ve şemasını fikstüre taşı.

    `iddia.py` kapı satırları için `kapi_cikti`yi içe aktarır; fikstür bu
    modülü taşımazsa hızlı kip hiç çalışmaz ve test gerçek davranışı değil
    kendi eksikliğini ölçer.
    """
    shutil.copy2(KAPI_MODUL, kok / "tools" / KAPI_MODUL.name)
    (kok / "schemas").mkdir(parents=True, exist_ok=True)
    shutil.copy2(KAPI_SEMA, kok / "schemas" / KAPI_SEMA.name)


def _defter(kok):
    return {
        "olcum_dosyasi": "tools/iddia_olcum.json",
        "kapsam": {"dahil": ["README.md"], "sayisal_istisna": []},
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


def _kapsam_kok(gecici, ad, metin, istisna=None, dahil=None):
    kok = Path(gecici) / ad
    (kok / "tools").mkdir(parents=True)
    shutil.copy2(ARAC, kok / "tools" / "iddia.py")
    _kapi_modulu(kok)
    _yaz(kok / "README.md", metin)
    _ozet_yaz(kok)
    defter = _defter(kok)
    defter["kapsam"] = {"dahil": dahil or ["README.md"],
                        "sayisal_istisna": istisna or []}
    _json_yaz(kok / "tools" / "iddia_defteri.json", defter)
    _json_yaz(_kanit_yolu(kok, defter), _hizli_kanit())
    _sahte_agir(kok, "dogrula")
    _sahte_agir(kok, "mutasyon_bataryasi")
    return kok


def _hazirla(kok):
    (kok / "tools").mkdir(parents=True)
    shutil.copy2(ARAC, kok / "tools" / "iddia.py")
    _kapi_modulu(kok)
    _yaz(kok / "README.md", "HIZLI 7/7\nAGIR 3/3\n")
    _ozet_yaz(kok)
    defter = _defter(kok)
    _json_yaz(kok / "tools" / "iddia_defteri.json", defter)
    _json_yaz(_kanit_yolu(kok, defter), _hizli_kanit())
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

        temel = "HIZLI 7/7\nAGIR 3/3\n"

        # --iz: tek kayit izi; diger satirlarin eksik kaniti bu izi kilitlemez.
        r = _calistir(kok, "--iz", "IDD-01")
        cikti = _cikti(r)
        bekle("--iz tek kayit rc=0", r.returncode == 0, cikti)
        for etiket in ("ATLAS — IDDIA IZI", "defter    :", "kaynak    :",
                       "komut     :", "ham kanit :", "guncel    :",
                       "HUKUM: PASS"):
            bekle("--iz ciktisinda %s var" % etiket.strip(),
                  etiket in cikti, cikti)
        bekle("--iz kaynak satirini gosterdi", "README.md:1" in cikti, cikti)
        bekle("--iz yalniz secilen kaydi gosterdi", "IDD-02" not in cikti, cikti)
        bekle("--iz agir komutlari kosmadi",
              not (kok / "tools" / "dogrula.marker").exists()
              and not (kok / "tools" / "mutasyon_bataryasi.marker").exists(),
              cikti)

        r = _calistir(kok, "--iz=IDD-01")
        bekle("--iz= formu rc=0", r.returncode == 0, _cikti(r))

        r = _calistir(kok, "--iz", "IDD-99")
        cikti = _cikti(r)
        bekle("--iz bilinmeyen ID rc=2", r.returncode == 2, cikti)
        bekle("--iz bilinmeyen ID adlandirildi", "IDD-99" in cikti, cikti)

        kanit_yolu = _kanit_yolu(kok)
        once = kanit_yolu.read_bytes()
        r = _calistir(kok, "--iz", "IDD-01", "--yaz")
        bekle("--iz --yaz rc=2", r.returncode == 2, _cikti(r))
        bekle("--iz --yaz kaniti degistirmedi",
              kanit_yolu.read_bytes() == once, _cikti(r))

        # Bozuk ham kanit: komut guncel olsa da iz FAIL olmali.
        iz_bozuk = _kapsam_kok(gecici, "iz-bozuk", temel)
        bozuk_yolu = _kanit_yolu(iz_bozuk)
        bozuk = json.loads(bozuk_yolu.read_text(encoding="utf-8"))
        bozuk["olcumler"]["IDD-01"]["ham"] = "HIZLI 9/9"
        _json_yaz(bozuk_yolu, bozuk)
        r = _calistir(iz_bozuk, "--iz", "IDD-01")
        cikti = _cikti(r)
        bekle("--iz bozuk ham kanitta rc=1", r.returncode == 1, cikti)
        bekle("--iz bozuk ham kaniti adlandirdi",
              "HUKUM: FAIL" in cikti and "ham kanit" in cikti, cikti)

        # Ham kanit yoksa komut kosmadan fail-closed olmali.
        iz_yok = _kapsam_kok(gecici, "iz-yok", temel)
        yok_yolu = _kanit_yolu(iz_yok)
        yok = json.loads(yok_yolu.read_text(encoding="utf-8"))
        yok["olcumler"].pop("IDD-01")
        _json_yaz(yok_yolu, yok)
        r = _calistir(iz_yok, "--iz", "IDD-01")
        cikti = _cikti(r)
        bekle("--iz eksik ham kanitta rc=2", r.returncode == 2, cikti)
        bekle("--iz eksik ham kaniti adlandirdi",
              "ham kanit yok" in cikti, cikti)

        # Tam kosu hala fail-closed: agir kanit eksikse rc=2, komut kosmaz.
        r = _calistir(kok)
        cikti = _cikti(r)
        bekle("tam kosu eksik agir kanitta rc=2", r.returncode == 2, cikti)
        bekle("tam kosu eksik kaniti adlandirdi",
              "ham kanit yok" in cikti and "IDD-02" in cikti
              and "IDD-03" in cikti, cikti)

        # Kanit tamamsa varsayilan kosu iki agir komutu da kosar.
        _json_yaz(_kanit_yolu(kok), _tam_kanit())
        r = _calistir(kok)
        cikti = _cikti(r)
        bekle("tam kosu tam kanitta rc=0", r.returncode == 0, cikti)
        bekle("tam kosu agir komutlari kostu",
              (kok / "tools" / "dogrula.marker").exists()
              and (kok / "tools" / "mutasyon_bataryasi.marker").exists(),
              cikti)

        # Kismi anlik goruntu tam kaniti silmemeli.
        kanit_yolu = _kanit_yolu(kok)
        once = kanit_yolu.read_bytes()
        r = _calistir(kok, "--yaz", "--hizli")
        bekle("--yaz --hizli rc=2", r.returncode == 2, _cikti(r))
        bekle("--yaz --hizli kanit dosyasini degistirmedi",
              kanit_yolu.read_bytes() == once, _cikti(r))

        # Basarili --yaz, kaniti defterdeki olcum_dosyasi alanina yazar.
        r = _calistir(kok, "--yaz")
        cikti = _cikti(r)
        bekle("--yaz defterdeki kanit yolunu kullandi",
              r.returncode == 0
              and "HAM KANIT YAZILDI:" in cikti
              and str(kanit_yolu.relative_to(kok)) in cikti
              and kanit_yolu.is_file(), cikti)

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

        # --- OLCUM DOSYASI: defter ham kanit yolunu tek basina tasir.
        ozet_drift = _kapsam_kok(gecici, "ozet-drift", temel)
        _ozet_yaz(ozet_drift, OZET.replace("olculdu=3", "olculdu=2"))
        r = _calistir(ozet_drift, "--hizli")
        bekle("ozet drift rc=2", r.returncode == 2, _cikti(r))
        bekle("ozet drift adlandirilir", "ozet drift" in _cikti(r), _cikti(r))

        ozet_yok = _kapsam_kok(gecici, "ozet-yok", temel)
        (ozet_yok / "docs" / "IDDIA-OZET.md").unlink()
        r = _calistir(ozet_yok, "--hizli")
        bekle("ozet blogu yoksa rc=2", r.returncode == 2, _cikti(r))
        yanlis_yol = _kapsam_kok(gecici, "olcum-yolu-yanlis", temel)
        defter_yolu = yanlis_yol / "tools" / "iddia_defteri.json"
        d = json.loads(defter_yolu.read_text(encoding="utf-8"))
        d["olcum_dosyasi"] = "tools/baska.json"
        _json_yaz(defter_yolu, d)
        r = _calistir(yanlis_yol, "--hizli")
        bekle("yanlis olcum_dosyasi rc=2", r.returncode == 2, _cikti(r))
        bekle("yanlis olcum_dosyasi adlandirilir",
              "olcum_dosyasi" in _cikti(r), _cikti(r))

        eksik_yol = _kapsam_kok(gecici, "olcum-yolu-eksik", temel)
        defter_yolu = eksik_yol / "tools" / "iddia_defteri.json"
        d = json.loads(defter_yolu.read_text(encoding="utf-8"))
        d.pop("olcum_dosyasi")
        _json_yaz(defter_yolu, d)
        r = _calistir(eksik_yol, "--hizli")
        bekle("eksik olcum_dosyasi rc=2", r.returncode == 2, _cikti(r))

        # --- KAPSAM KAPISI: sayisal iddia defterde ya da gerekceli istisnada.
        kirli = _kapsam_kok(gecici, "kapsam-eksik",
                            temel + "YENI 42 vaka\n")
        r = _calistir(kirli, "--hizli")
        cikti = _cikti(r)
        bekle("kapsamsiz iddia rc=2", r.returncode == 2, cikti)
        bekle("kapsamsiz iddia dosya:satir ve jeton basar",
              "README.md:3" in cikti and "'42'" in cikti, cikti)
        bekle("kapsamsiz iddia HUKUM KAPSAM BOZUK",
              "HUKUM: KAPSAM BOZUK" in cikti, cikti)

        # Sozlukte olmayan olcum adlari da varsayilan-redde yakalanir:
        # "agents" / "phases" OLCUM_SOZCUK listesinde yok; yine de kirmizi.
        agents = _kapsam_kok(gecici, "kapsam-agents",
                             temel + "SISTEM 12 agents\n")
        r = _calistir(agents, "--hizli")
        cikti = _cikti(r)
        bekle("sozluk disi 12 agents rc=2", r.returncode == 2, cikti)
        bekle("12 agents jetonu ve satiri adlandirilir",
              "README.md:3" in cikti and "'12'" in cikti, cikti)
        bekle("12 agents HUKUM KAPSAM BOZUK",
              "HUKUM: KAPSAM BOZUK" in cikti, cikti)

        phases = _kapsam_kok(gecici, "kapsam-phases",
                             temel + "AKIS 5 phases\n")
        r = _calistir(phases, "--hizli")
        cikti = _cikti(r)
        bekle("sozluk disi 5 phases rc=2", r.returncode == 2, cikti)
        bekle("5 phases jetonu ve satiri adlandirilir",
              "README.md:3" in cikti and "'5'" in cikti, cikti)
        bekle("5 phases HUKUM KAPSAM BOZUK",
              "HUKUM: KAPSAM BOZUK" in cikti, cikti)

        istisnali = _kapsam_kok(
            gecici, "kapsam-istisna", temel + "YENI 42 vaka\n",
            [{"desen": "YENI 42 vaka", "neden": "test istisnasi"}])
        r = _calistir(istisnali, "--hizli")
        cikti = _cikti(r)
        bekle("gerekceli istisna rc=0", r.returncode == 0, cikti)
        bekle("istisna sayaci basildi", "istisnada=1" in cikti, cikti)

        olu = _kapsam_kok(gecici, "kapsam-olu", temel,
                          [{"desen": "YOK 99 vaka", "neden": "olu"}])
        r = _calistir(olu, "--hizli")
        bekle("olu istisna rc=2", r.returncode == 2, _cikti(r))
        bekle("olu istisna adlandirilir", "olu istisna" in _cikti(r), _cikti(r))

        gerekcesiz = _kapsam_kok(
            gecici, "kapsam-gerekcesiz", temel + "YENI 42 vaka\n",
            [{"desen": "YENI 42 vaka"}])
        r = _calistir(gerekcesiz, "--hizli")
        bekle("gerekcesiz istisna rc=2", r.returncode == 2, _cikti(r))

        genis = _kapsam_kok(
            gecici, "kapsam-genis", temel + "YENI 42 vaka\n",
            [{"desen": ".*", "neden": "her sey"}])
        r = _calistir(genis, "--hizli")
        bekle("genis istisna rc=2", r.returncode == 2, _cikti(r))
        bekle("genis istisna adlandirilir", "cok genis" in _cikti(r), _cikti(r))

        cok_satir = _kapsam_kok(
            gecici, "kapsam-cok-satir",
            temel + "A 1 vaka\nB 2 vaka\nC 3 vaka\nD 4 vaka\n",
            [{"desen": "vaka", "neden": "dort satir"}])
        r = _calistir(cok_satir, "--hizli")
        bekle("dort satiri kapsayan istisna rc=2",
              r.returncode == 2 and "cok genis" in _cikti(r), _cikti(r))

        eksik_dosya = _kapsam_kok(
            gecici, "kapsam-dosya", temel,
            dahil=["README.md", "docs/YOK.md"])
        r = _calistir(eksik_dosya, "--hizli")
        bekle("kapsam disi dosya yoksa rc=2", r.returncode == 2, _cikti(r))
        bekle("eksik kapsam dosyasi adlandirilir",
              "docs/YOK.md" in _cikti(r), _cikti(r))

    if hatalar:
        print("\nIDDIA OZ-TEST: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nIDDIA OZ-TEST: PASS — %d/%d" % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
