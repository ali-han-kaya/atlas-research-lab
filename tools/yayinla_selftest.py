#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yayinla_selftest.py — yayinla.py'nin fikstur muafiyeti ve public katmani.

NEDEN VAR
  `tools/yayinla.py` iki guvenlik sinirini tasir:
    * fikstur muafiyeti yalniz (dosya, TAM satir SHA-256) ciftini susturur;
      satir baska bir dosyaya tasinirsa bulgu kalmalidir,
    * `KORUNAN` public katmani ve `KORUNAN_KOKLER`, aktarim disinda kalan
      dosyalarin `SILINECEK` sayilmasini engeller.

  Bu iki sinir bugune kadar yalniz gercek aktarim ciktisindan gozleniyordu.
  Negatif fiksturu olmayan bir koruma test edilmemis sayilir.

NASIL
  Gecici bir hedef agac (yayinla.py + minimal yayin manifesti) ve gecici bir
  kaynak lab kurulur; gercek `yayinla.py` alt surecte kosar. Ana agaca YAZILMAZ.
  Bozuk manifest, izinsiz kayit, tasinan fikstur satiri ve korunan belgeler
  ayri vakalarda olculur. `SILINECEK` listesi ciktidan okunur; korunan bir
  dosyanin adi orada gorunurse vaka kirmizidir.

KULLANIM
  python3 tools/yayinla_selftest.py

CIKIS: 0 = butun vakalar gecti · 1 = en az bir vaka kirmizi
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ARAC = KOK / "tools" / "yayinla.py"
sys.path.insert(0, str(KOK / "tools"))
import yayinla  # noqa: E402

# Muafiyetin izin verdigi iki gercek dosya. Ayni satir A'dan B'ye tasininca
# kayit (dosya, hash) anahtarindan dolayi B'de eslesmemelidir.
IZINLI_A = "docs/OLCUM-02-CANLI-KOSU.md"
IZINLI_B = "KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_selftest.py"
# Desene uyan ama yer tutucu ipucu tasimayan sentetik deger. Ikiye bolunur:
# butun halde yazilsaydi bu test dosyasi yayin kapisinda sir olarak yakalanirdi.
SAHTE = "AKIA" + "2E1F4B7C9D0E3F9A"

SONUCLAR = []


def kontrol(ad, gecti, ayrinti=""):
    SONUCLAR.append((ad, bool(gecti)))
    print("  %-5s %s%s" % ("PASS" if gecti else "FAIL", ad,
                           "" if gecti else " :: %s" % ayrinti))


def satir_hash(satir):
    return hashlib.sha256(satir.encode("utf-8")).hexdigest()


def kayit(dosya, satir):
    return {
        "dosya": dosya,
        "satir": 1,
        "satir_sha256": satir_hash(satir),
        "gerekce": "yayinla regresyon fiksturu; gercek sir degil",
        "kanit": "yayinla_selftest",
    }


def _yaz(yol, icerik):
    yol.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(icerik, bytes):
        yol.write_bytes(icerik)
    else:
        yol.write_text(icerik, encoding="utf-8")


def _json_yaz(yol, veri):
    _yaz(yol, json.dumps(veri, ensure_ascii=False, indent=2) + "\n")


def hedef(tmp, satirlar=None, kayitlar=None, manifest=None, dosyalar=None):
    """Gecici hedef depo ve kaynak lab kur; (hedef, lab) dondur."""
    kok = Path(tmp) / "public"
    lab = Path(tmp) / "lab"
    (kok / "tools").mkdir(parents=True)
    shutil.copy2(ARAC, kok / "tools" / "yayinla.py")
    _json_yaz(kok / "tools" / "yayin_manifest.json", {
        "schema": "ATLAS-YAYIN/v1",
        "yasak_yollar": ["yasak/"],
        "yasak_uzantilar": [".pdf"],
    })

    if manifest is None:
        manifest = {"schema": "SECRET-SCAN-FIKSTUR/v1",
                    "fiksturler": kayitlar or []}
    if isinstance(manifest, str):
        _yaz(kok / "tools" / "secret_fixtures.json", manifest)
    else:
        _json_yaz(kok / "tools" / "secret_fixtures.json", manifest)

    for rel, icerik in (dosyalar or {}).items():
        _yaz(kok / rel, icerik)

    for rel in yayinla.KOKLER + yayinla.TOOLKIT_KOKLER:
        (lab / rel).mkdir(parents=True, exist_ok=True)
    for rel, satir_listesi in (satirlar or {}).items():
        _yaz(lab / rel, "\n".join(satir_listesi) + "\n")
    return kok, lab


def kos(kok, lab):
    return subprocess.run(
        [sys.executable, str(kok / "tools" / "yayinla.py"),
         "--lab", str(lab)],
        cwd=str(kok), capture_output=True, text=True, timeout=60)


def cikti(r):
    return (r.stdout or "") + (r.stderr or "")


def vaka_temiz(tmp):
    """Ayni satir kayitli dosyada susmali; once sirsiz taban P0 vermeli."""
    on_kok, on_lab = hedef(
        Path(tmp) / "on", {IZINLI_A: [SAHTE]},
        dosyalar={IZINLI_A: SAHTE + "\n"})
    on = kos(on_kok, on_lab)
    on_cikti = cikti(on)
    kontrol("on kosul: fikstur satiri gercekten sir sayiliyor",
            on.returncode == 1 and "SIR TARAMASI: 1 bulgu" in on_cikti,
            "rc=%d · %s" % (on.returncode, on_cikti.strip()[-180:]))
    if not (on.returncode == 1 and "SIR TARAMASI: 1 bulgu" in on_cikti):
        return

    kok, lab = hedef(
        Path(tmp) / "son", {IZINLI_A: [SAHTE]},
        [kayit(IZINLI_A, SAHTE)],
        dosyalar={IZINLI_A: SAHTE + "\n"})
    r = kos(kok, lab)
    metin = cikti(r)
    kontrol("bilinen fikstur satiri sessiz",
            r.returncode == 0 and "SIR TARAMASI: temiz" in metin,
            "rc=%d · %s" % (r.returncode, metin.strip()[-180:]))


def vaka_tasindi(tmp):
    """Kayitli satir izinli baska dosyaya tasininca bulgu kalmalidir."""
    kok, lab = hedef(
        Path(tmp), {IZINLI_B: [SAHTE]}, [kayit(IZINLI_A, SAHTE)])
    r = kos(kok, lab)
    metin = cikti(r)
    kontrol("fikstur satiri baska dosyaya tasininca bulgu",
            r.returncode == 1 and "SIR TARAMASI: 1 bulgu" in metin
            and IZINLI_B in metin,
            "rc=%d · %s" % (r.returncode, metin.strip()[-220:]))


def vaka_bozuk_manifest(tmp):
    """Bozuk manifest 'temiz' dememeli; surec fail-closed kapanmali."""
    kok, lab = hedef(
        Path(tmp), manifest='{ "fiksturler": [ olsun ')
    r = kos(kok, lab)
    metin = cikti(r)
    kontrol("bozuk manifest fail-closed",
            r.returncode == 1
            and "HATA: fikstur manifesti" in metin
            and "SIR TARAMASI: temiz" not in metin,
            "rc=%d · %s" % (r.returncode, metin.strip()[-220:]))


def vaka_gecersiz_kayit(tmp):
    """Izinli dosya listesi disindaki kayit manifesti kabul edilmemeli."""
    kayitlar = [kayit("docs/IZINSIZ.md", SAHTE)]
    kok, lab = hedef(Path(tmp), kayitlar=kayitlar)
    r = kos(kok, lab)
    metin = cikti(r)
    kontrol("izinsiz fikstur kaydi fail-closed",
            r.returncode == 1
            and "fikstur kaydi gecersiz/izinli dosya disinda" in metin
            and "SIR TARAMASI: temiz" not in metin,
            "rc=%d · %s" % (r.returncode, metin.strip()[-220:]))


def vaka_korunan(tmp):
    """Korunan public belgeleri SILINECEK saymamali; siradan dosyayi saymali."""
    korunan = sorted(rel for rel in yayinla.KORUNAN if rel.startswith("docs/"))
    dosyalar = {rel: "public katman belgesi\n" for rel in korunan}
    dosyalar["docs/serbest.md"] = "aktarim disi dosya\n"
    kok, lab = hedef(Path(tmp), dosyalar=dosyalar)
    r = kos(kok, lab)
    metin = cikti(r)
    silinecek = [
        satir.strip()[len("SILINECEK"):].strip()
        for satir in metin.splitlines()
        if satir.strip().startswith("SILINECEK ")
    ]
    kontrol("korunan belgeler silinecek sayilmadi",
            set(silinecek) == {"docs/serbest.md"},
            "silinecek=%r · %s" % (silinecek, metin.strip()[-220:]))
    kontrol("korunmayan dosya silinecek sayildi",
            "silinecek=1" in metin and "docs/serbest.md" in silinecek,
            "rc=%d · %s" % (r.returncode, metin.strip()[-220:]))


def main():
    print("YAYINLA OZ-TESTI — fikstur muafiyeti ve public katman siniri")
    print("kaynak: %s" % KOK.name)
    print()
    tmp = tempfile.mkdtemp(prefix="yayinla_selftest_")
    try:
        vaka_temiz(Path(tmp) / "a")
        vaka_tasindi(Path(tmp) / "b")
        vaka_bozuk_manifest(Path(tmp) / "c")
        vaka_gecersiz_kayit(Path(tmp) / "d")
        vaka_korunan(Path(tmp) / "e")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    kirik = [ad for ad, gecti in SONUCLAR if not gecti]
    print()
    print("  vaka=%d · gecen=%d · kalan=%d"
          % (len(SONUCLAR), len(SONUCLAR) - len(kirik), len(kirik)))
    if kirik:
        print("HUKUM: FAIL — yayinla korumasi zayifladi: %s"
              % ", ".join(kirik))
        return 1
    print("HUKUM: PASS — fikstur yalniz tam satir hash'inde susuyor; "
          "tasima ve bozuk manifest bulgu, korunan public katmani silinmiyor.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
