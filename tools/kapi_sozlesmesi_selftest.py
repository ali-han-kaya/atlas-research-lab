#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kapi_sozlesmesi_selftest.py — ATLAS-KAPI-CIKTI/v1 sözleşme testleri.

Vakalar:
  * şema dosyası geçerli Draft 2020-12 şemasıdır;
  * üretilen zarf şemayı geçer;
  * sürüm, zorunlu alan, kapalı nesne, yinelenen kimlik, sayaç ve hüküm
    çelişkileri fail-closed reddedilir;
  * `sec()` yalnız bildirilen kontrol kimliğini okur;
  * `kapsam.py --json` gerçek çıktısı sözleşmeyi geçer.
"""
import json
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))
if str(KOK / "tools") not in sys.path:
    sys.path.insert(0, str(KOK / "tools"))

import kapi_cikti  # noqa: E402


def _gecerli():
    return kapi_cikti.uret("test", [
        kapi_cikti.kontrol("K-1", "birinci kontrol", "PASS", deger="7/7",
                           ham="test K-1 PASS 7/7"),
        kapi_cikti.kontrol("K-2", "ikinci kontrol", "PASS", deger="3",
                           ham="test K-2 PASS 3"),
    ])


def _bekle(ad, kosul, ayrinti=""):
    if kosul:
        print("PASS  " + ad)
        return True
    print("FAIL  " + ad + ((" :: " + ayrinti) if ayrinti else ""))
    return False


def main():
    hatalar = []
    toplam = 0

    def kontrol(ad, kosul, ayrinti=""):
        nonlocal toplam
        toplam += 1
        if not _bekle(ad, kosul, ayrinti):
            hatalar.append(ad)

    from jsonschema import Draft202012Validator
    sema = json.loads(kapi_cikti.SEMA_YOLU.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(sema)
        gecerli_sema = True
    except Exception as e:
        gecerli_sema = False
        sema_hata = str(e)
    kontrol("sema gecerli Draft 2020-12", gecerli_sema,
            "" if gecerli_sema else sema_hata)

    v = _gecerli()
    try:
        kapi_cikti.dogrula(v)
        gecerli = True
    except Exception as e:
        gecerli = False
        hata = str(e)
    kontrol("uretilen zarf semayi gecer", gecerli, "" if gecerli else hata)

    def reddet(ad, mutasyon):
        """Bozuk zarf Sözleşme hatasıyla reddedilmeli; başka tip kabul değil."""
        x = _gecerli()
        mutasyon(x)
        reddedildi = False
        ayrinti = "bozuk zarf kabul edildi"
        try:
            kapi_cikti.dogrula(x)
        except kapi_cikti.SozlesmeHatasi:
            reddedildi = True
            ayrinti = ""
        except Exception as e:  # pragma: no cover - beklenmeyen tip
            ayrinti = "beklenmeyen tip %s: %s" % (type(e).__name__, e)
        kontrol(ad, reddedildi, ayrinti)

    reddet("surum uyusmazligi reddedilir", lambda x: x.update(surum="2.0.0"))
    reddet("zorunlu kontroller alani reddedilir", lambda x: x.pop("kontroller"))
    reddet("bilinmeyen kok alani reddedilir", lambda x: x.update(fazla=1))
    reddet("bilinmeyen kontrol alani reddedilir",
           lambda x: x["kontroller"][0].update(fazla=1))
    reddet("yinelenen kontrol kimligi reddedilir",
           lambda x: x["kontroller"][1].update(id="K-1"))
    reddet("sayaç celiskisi reddedilir",
           lambda x: x["sayilar"].update(gecti=1))
    reddet("PASS + rc=1 celiskisi reddedilir", lambda x: x.update(rc=1))
    reddet("FAIL + rc=0 celiskisi reddedilir",
           lambda x: x.update(hukum="FAIL"))

    try:
        deger = kapi_cikti.sec(v, "K-1")
        sec_ok = deger == "7/7"
    except Exception as e:
        sec_ok = False
        sec_hata = str(e)
    kontrol("sec() kontrol kimliginden deger okur", sec_ok,
            "" if sec_ok else globals().get("sec_hata", ""))

    try:
        kapi_cikti.sec(v, "YOK")
        yok_red = False
    except kapi_cikti.SozlesmeHatasi:
        yok_red = True
    kontrol("sec() bilinmeyen kimlikte fail-closed", yok_red)

    kapsam = subprocess.run(
        [sys.executable, str(KOK / "tools" / "kapsam.py"), "--json"],
        cwd=str(KOK), capture_output=True, text=True, timeout=120)
    try:
        k = kapi_cikti.oku(kapsam.stdout)
        kapsam_ok = (kapsam.returncode == 0 and k["kapi"] == "kapsam"
                     and kapi_cikti.sec(k, "KAPSAM.toplam_dogrulanan") == "117")
        kapsam_hata = "" if kapsam_ok else kapsam.stderr.strip()[:300]
    except Exception as e:
        kapsam_ok = False
        kapsam_hata = "%s: %s" % (type(e).__name__, e)
    kontrol("kapsam --json gercek cikti sozlesmeyi gecer", kapsam_ok,
            kapsam_hata)

    if hatalar:
        print("\nKAPI SOZLESME TEST: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nKAPI SOZLESME TEST: PASS — %d/%d" % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
