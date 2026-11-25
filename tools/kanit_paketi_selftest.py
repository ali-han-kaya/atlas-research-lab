#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kanit_paketi_selftest.py — paket semasi ve bulgu kimlikleri sessizce gevşemesin.

Geçici bir paket üretir, `kanit_paketi_dogrula.py` ile temel PASS'i görür ve
sonra yalnız geçici kopyalarda:
  * `sonuc.json` şemasını bozar       -> PAKET-01
  * komutun `finding_ids` kümesini bozar -> PAKET-05
  * üst düzey `findings` kümesini bozar  -> PAKET-06
beklentisini sınar. Ana ağaç ve kök attestation değişmemelidir.

Kullanım: python3 tools/kanit_paketi_selftest.py
CIKIS: 0 = bütün kontroller beklendiği gibi · 1 = sapma/kurulum hatası
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KANIT = KOK / "tools" / "kanit.py"
DOGRULA = KOK / "tools" / "kanit_paketi_dogrula.py"
ATTESTATION = "attestation.json"


def kos(komut, timeout=180):
    try:
        return subprocess.run(
            komut, cwd=str(KOK), capture_output=True, text=True, timeout=timeout
        ), None
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def cikti(sonuc):
    if sonuc is None:
        return ""
    return (sonuc.stdout or "") + (sonuc.stderr or "")


def sha256(yol):
    try:
        return hashlib.sha256(yol.read_bytes()).hexdigest()
    except OSError:
        return None


def dogrula(paket):
    return kos([sys.executable, str(DOGRULA), "--paket", str(paket),
                "--makbuz"])


def mutasyon(kaynak, hedef, degistir):
    shutil.copytree(kaynak, hedef)
    yol = hedef / "sonuc.json"
    veri = json.loads(yol.read_text(encoding="utf-8"))
    degistir(veri)
    yol.write_text(
        json.dumps(veri, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main():
    hatalar = []
    toplam = 0

    def bekle(ad, gecti, ayrinti=""):
        nonlocal toplam
        toplam += 1
        if gecti:
            print("PASS " + ad)
            return
        print("KALDI " + ad)
        if ayrinti:
            for satir in str(ayrinti).strip().splitlines()[-10:]:
                print("  | " + satir)
        hatalar.append(ad)

    att_yolu = KOK / ATTESTATION
    att_once = sha256(att_yolu)
    durum_once, durum_hatasi = kos(
        ["git", "-C", str(KOK), "status", "--porcelain", "--untracked-files=all"]
    )
    durum_once = None if durum_once is None else durum_once.stdout
    if durum_once is None:
        print("KALDI kurulum: ana agac durumu okunamadi")
        print("\nKANIT PAKET OZ-TEST: FAIL — 0/0")
        return 1

    try:
        with tempfile.TemporaryDirectory(prefix="kanit-paket-oztest-") as gecici:
            kok = Path(gecici)
            paket = kok / "paket"
            ozel_att = kok / "attestation.json"
            komut = (
                'python3 -c "'
                "print('FAIL TST-01 P1 sentetik'); "
                "print('SONUC PASS')"
                '"'
            )
            uretim, uretim_hatasi = kos([
                sys.executable, str(KANIT),
                "--cikti", str(ozel_att),
                "--paket", str(paket),
                "--komut", komut,
            ])
            uretim_ok = (
                uretim is not None and uretim.returncode == 0
                and paket.is_dir()
            )
            bekle(
                "gecici paket uretildi",
                uretim_ok,
                uretim_hatasi or cikti(uretim),
            )

            if uretim_ok:
                temel, temel_hatasi = dogrula(paket)
                bekle(
                    "temel paket semasi ve bulgu kimlikleri",
                    temel is not None and temel.returncode == 0
                    and "PASS PAKET" in cikti(temel),
                    temel_hatasi or cikti(temel),
                )

                sema_paket = kok / "bozuk-sema"
                mutasyon(
                    paket, sema_paket,
                    lambda v: v.__setitem__("schema", "ATLAS-DOGRULAMA/v0"),
                )
                sema, sema_hatasi = dogrula(sema_paket)
                sema_metin = cikti(sema)
                bekle(
                    "bozuk sonuc semasi PAKET-01",
                    sema is not None and sema.returncode == 1
                    and "FAIL PAKET-01" in sema_metin,
                    sema_hatasi or sema_metin,
                )

                bulgu_paket = kok / "bozuk-bulgu"
                mutasyon(
                    paket, bulgu_paket,
                    lambda v: v["commands"][0].__setitem__(
                        "finding_ids", ["UYDURMA-01"]
                    ),
                )
                bulgu, bulgu_hatasi = dogrula(bulgu_paket)
                bulgu_metin = cikti(bulgu)
                bekle(
                    "bozuk komut bulgu kimligi PAKET-05",
                    bulgu is not None and bulgu.returncode == 1
                    and "FAIL PAKET-05" in bulgu_metin,
                    bulgu_hatasi or bulgu_metin,
                )

                ust_paket = kok / "bozuk-ust-bulgu"
                mutasyon(
                    paket, ust_paket,
                    lambda v: v.__setitem__("findings", []),
                )
                ust, ust_hatasi = dogrula(ust_paket)
                ust_metin = cikti(ust)
                bekle(
                    "bozuk ust bulgu kimligi PAKET-06",
                    ust is not None and ust.returncode == 1
                    and "FAIL PAKET-06" in ust_metin,
                    ust_hatasi or ust_metin,
                )
    finally:
        att_sonra = sha256(att_yolu)
        durum_sonra, _ = kos(
            ["git", "-C", str(KOK), "status", "--porcelain",
             "--untracked-files=all"]
        )
        durum_sonra = None if durum_sonra is None else durum_sonra.stdout
        bekle(
            "ana agac ve attestation degismedi",
            att_sonra == att_once and durum_sonra == durum_once,
            "attestation %r -> %r\nstatus %r -> %r" % (
                att_once, att_sonra, durum_once, durum_sonra),
        )

    if hatalar:
        print("\nKANIT PAKET OZ-TEST: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nKANIT PAKET OZ-TEST: PASS — %d/%d" % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
