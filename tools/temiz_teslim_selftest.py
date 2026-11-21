#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""temiz_teslim_selftest.py — sentetik temiz teslim + 5 kenar fikstürü.

NEDEN VAR
  DENEME/ yalnız kırmızı yolu gösterir: 8 FIX iddiasının 2'si MASTER'a
  yansımışken dondurulmuş gate PASS demiştir. Bu betik, DENEME/'yi
  DEĞİŞTİRMEDEN, makale metni taşımayan sentetik bir proje kurar ve meşru
  teslimin uçtan uca rc=0 verdiğini gerçek komutlarla ölçer:

      demo.py --kok <temiz>          -> rc=0 (iddia == kanıt, mutabakat PASS)
      scripts/check_integrity.sh --full -> rc=0 (FAZ0..FAZ3 + gate)

  Ardından aynı temiz kökten beş kenar fikstürü türetir ve her birinin
  beklenen rc'sini ayrı ayrı sınar. Fikstürler tempfile altında üretilir;
  DENEME/ yalnızca betik kopyalamak için OKUNUR, hiçbir zaman yazılmaz.

  Sentetik MASTER, 22 zorunlu SCOPE-ID başlığını ve PROVENANCE satırlarını
  taşır; gövdesi "SENTETIK KAYIT" izlerinden oluşur. Makale paragrafı,
  kaynakça, DOI veya alıntı yoktur.

ÇIKIŞ
  0 = temiz fikstür rc=0 ve beş kenar fikstürü beklenen rc'yi verdi
  1 = en az bir sapma, eksik iz veya kurulum hatası
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DEMO = KOK / "tools" / "demo.py"
KAYNAK_BETIKLER = KOK / "DENEME" / "scripts"
SCOPE_IDLERI = ["SC-%03d" % i for i in range(1, 23)]
MANIFEST = "02-FAZ-2-FIX-MANIFEST.md"
MASTER = "03-FAZ-3-MASTER-v5.5.md"
GATE2B = Path("gate") / "STRONG-gate-2b-v5.5.json"
FINAL_GATE = Path("gate") / "FINAL-GATE-v5.5.json"


def yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")


def temiz_kur(kok):
    """Makale metni taşımayan, mekanizma odaklı sentetik teslimi kur."""
    shutil.copytree(KAYNAK_BETIKLER, kok / "scripts",
                    ignore=shutil.ignore_patterns("__pycache__"))

    scope_satirlari = "\n".join(
        "| %s | Sentetik kapsam %s | ZORUNLU | Sentetik | Sinama |"
        % (sid, sid) for sid in SCOPE_IDLERI)
    yaz(kok / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md",
        "# Sentetik kapsam sozlesmesi\n\n"
        "| ID | Baslik | Zorunluluk | Kaynak | Gerekce |\n"
        "|---|---|---|---|---|\n"
        + scope_satirlari
        + "\n\n| DEC-001 | DECIDED | Sentetik sinama | Sinama | - | - |\n\n"
        + "KAPSAM KAYDI. " * 80)

    findings = {
        "findings": [
            {"id": "F-001", "priority": "P0", "finding": "Sentetik bulgu"}
        ],
        "sentetik_kayit": ["CHK-001 P0 sentetik kayit."] * 200,
    }
    yaz(kok / "01-FAZ-1-LENS-ANALYSIS.json",
        json.dumps(findings, indent=2, ensure_ascii=False) + "\n")

    yaz(kok / MANIFEST,
        "# Sentetik FIX manifesti\n\n"
        "| FIX-ID | Severity | Kategori | Bulgu | Durum | Kanit |\n"
        "|---|---|---|---|---|---|\n"
        "| FIX-001 | P0 | SENTETIK | F-001 | UYGULANMIS | SC-001 |\n\n"
        + "F-001 sentetik kayit. " * 50)

    bolumler = []
    for i, sid in enumerate(SCOPE_IDLERI, 1):
        bolumler.append(
            "## %s Sentetik kapsam %02d\n\n"
            "SENTETIK KAYIT %s. Makale metni yoktur; yalniz mekanizma izi.\n"
            % (sid, i, sid))
    provenance = "\n".join(
        "| %s | Sentetik kapsam | Sentetik | kayit | kapsiyor |" % sid
        for sid in SCOPE_IDLERI)
    yaz(kok / MASTER,
        "# Sentetik teslim kaydi\n\n"
        + "\n".join(bolumler)
        + "\n## PROVENANCE\n\n"
        + "| SCOPE-ID | Bolum | Kaynak | Satir | Durum |\n"
        + "|---|---|---|---|---|\n"
        + provenance
        + "\n\nFIX-001 sentetik kanit.\n\n"
        + "SENTETIK DOGRULAMA KAYDI. " * 900)

    yaz(kok / "gate" / "STRONG-gate-2a-v5.5.json",
        json.dumps({"gate": "2a", "verdict": "PASS"}, indent=2) + "\n")
    yaz(kok / GATE2B,
        json.dumps({
            "gate": "2b",
            "verdict": "PASS",
            "manifest_reconciliation": [
                {"fix_id": "FIX-001", "status": "UYGULANMIS_KANITLI"}
            ],
        }, indent=2) + "\n")
    yaz(kok / FINAL_GATE, json.dumps({"verdict": "PASS"}, indent=2) + "\n")
    yaz(kok / "04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md",
        "# Sentetik gate raporu\n")


def kopya_kur(kaynak, hedef):
    shutil.copytree(kaynak, hedef)


def eksik_kanit(kok):
    yol = kok / MASTER
    metin = yol.read_text(encoding="utf-8")
    yaz(yol, metin.replace("FIX-001 sentetik kanit.", "Sentetik kanit kaldirildi."))


def hayalet_kanit(kok):
    yol = kok / MASTER
    with yol.open("a", encoding="utf-8") as f:
        f.write("\nFIX-999 sentetik hayalet kanit.\n")


def sahte_2b(kok):
    yol = kok / GATE2B
    veri = json.loads(yol.read_text(encoding="utf-8"))
    veri["manifest_reconciliation"].append(
        {"fix_id": "FIX-999", "status": "UYGULANMIS_KANITLI"})
    yaz(yol, json.dumps(veri, indent=2, ensure_ascii=False) + "\n")


def bozuk_final(kok):
    yaz(kok / FINAL_GATE, "{bozuk-json\n")


def eksik_kapsam(kok):
    yol = kok / MASTER
    metin = yol.read_text(encoding="utf-8")
    yaz(yol, re.sub(r"^## SC-022 .*$", "## Kimliksiz sentetik bolum",
                    metin, count=1, flags=re.M))


def kos(komut, cwd):
    try:
        r = subprocess.run(komut, cwd=str(cwd), capture_output=True, text=True,
                           timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, "komut kosulamadi: %s" % exc
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()


def demo(kok):
    return kos([sys.executable, str(DEMO), "--kok", str(kok)], kok)


def tam(kok):
    return kos(["bash", "scripts/check_integrity.sh", "--full"], kok)


def satir_ozeti(cikti, izler):
    for satir in reversed(cikti.splitlines()):
        if any(iz in satir for iz in izler):
            return satir.strip()[:160]
    return "(iz yok)"


def senaryo(ad, kok, beklenen, izler):
    sonuclar = []
    for etiket, fn, beklenen_rc, aranan in (
            ("demo", demo, beklenen["demo"], izler["demo"]),
            ("tam", tam, beklenen["tam"], izler["tam"])):
        rc, cikti = fn(kok)
        sorun = []
        if rc != beklenen_rc:
            sorun.append("rc=%r, beklenen=%d" % (rc, beklenen_rc))
        for iz in aranan:
            if iz not in cikti:
                sorun.append("cikti %r icermiyor" % iz)
        sonuclar.append((etiket, rc, cikti, sorun))

    if any(s[3] for s in sonuclar):
        print("KALDI %s" % ad)
        for etiket, rc, cikti, sorun in sonuclar:
            print("  %s rc=%r · %s" % (etiket, rc, "; ".join(sorun) or "ok"))
            for satir in cikti.splitlines()[-10:]:
                print("    | %s" % satir[:180])
        return False

    print("GECTI %-16s demo=%-2s tam=%-2s" % (
        ad, sonuclar[0][1], sonuclar[1][1]))
    return True


def main():
    if not KAYNAK_BETIKLER.is_dir():
        print("KALDI kurulum: %s yok" % KAYNAK_BETIKLER)
        return 1

    print("TEMIZ TESLIM — sentetik fikstur seti (makale metni yok)")
    with tempfile.TemporaryDirectory(prefix="atlas-temiz-teslim-") as tmp:
        gecici = Path(tmp)
        temiz = gecici / "temiz"
        temiz_kur(temiz)

        senaryolar = [
            ("temiz", temiz, {"demo": 0, "tam": 0}, {
                "demo": ("YESIL", "HUKUM: PASS"),
                "tam": ("FULL PASS v5.5.2",),
            }),
        ]

        kenarlar = [
            ("eksik-kanit", eksik_kanit, {"demo": 1, "tam": 0}, {
                "demo": ("BEKLENEN KIRMIZI", "FAIL REC-04"),
                "tam": ("FULL PASS v5.5.2",),
            }),
            ("hayalet-kanit", hayalet_kanit, {"demo": 2, "tam": 0}, {
                "demo": ("FIKSTUR DEGISTI", "REC-06"),
                "tam": ("FULL PASS v5.5.2",),
            }),
            ("sahte-2b", sahte_2b, {"demo": 2, "tam": 0}, {
                "demo": ("FIKSTUR DEGISTI", "REC-05"),
                "tam": ("FULL PASS v5.5.2",),
            }),
            ("bozuk-final", bozuk_final, {"demo": 2, "tam": 1}, {
                "demo": ("FIKSTUR DEGISTI",),
                "tam": ("FAIL JSON",),
            }),
            ("eksik-kapsam", eksik_kapsam, {"demo": 0, "tam": 1}, {
                "demo": ("YESIL",),
                "tam": ("FAIL CHK-01",),
            }),
        ]

        for ad, mutasyon, beklenen, izler in kenarlar:
            kok = gecici / ad
            kopya_kur(temiz, kok)
            mutasyon(kok)
            senaryolar.append((ad, kok, beklenen, izler))

        sonuclar = [senaryo(ad, kok, beklenen, izler)
                    for ad, kok, beklenen, izler in senaryolar]

    gecen = sum(1 for s in sonuclar if s)
    print("SONUC: %d/%d fikstur gecti (1 temiz + 5 kenar)" %
          (gecen, len(sonuclar)))
    if gecen == len(sonuclar):
        print("HUKUM: PASS — temiz teslim rc=0; bes kenar beklenen rc'yi verdi.")
        return 0
    print("HUKUM: FAIL — fikstur sozlesmesi beklenen sonucu vermedi.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
