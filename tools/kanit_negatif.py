#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KANIT-00..06 negatif bataryasi — kanit kapisi sessizce gevşemesin.

Her vaka ana agactan uretilen gecici bir klonda gercek bir bozulma yapar ve
`tools/kanit_dogrula.py`'nin beklenen `FAIL KANIT-xx` satirini ve cikis kodunu
vermesini ister. Ana agacin HEAD'i, durumu ve attestation hash'i degismez.

Kapsanan kodlar:
  KANIT-00  attestation yok / JSON okunamadi
  KANIT-01  sema gecersiz
  KANIT-02  commit yok / HEAD'in atasi degil / tree uyusmuyor
  KANIT-03  kayitli dosya hash'i commit agaciyla uyusmuyor
  KANIT-04  file_count veya tree_sha256 uyusmuyor
  KANIT-05  guncel HEAD agaci kayitli agactan farkli
  KANIT-06  izlenen agac kirli

Ayrica `kanit.py`'nin paket hedefi korumasini sinar: var olan yabanci bir
dizin reddedilmeli, icindeki dosyalar silinmemelidir; yeni yol kabul edilir.

Kullanim: python3 tools/kanit_negatif.py
CIKIS: 0 = butun vakalar beklendigi gibi kirmizi · 1 = sapma/kurulum hatasi
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ARAC = "tools/kanit_dogrula.py"
ATTESTATION = "attestation.json"


def kos(komut, cwd, timeout=120):
    try:
        return subprocess.run(komut, cwd=str(cwd), capture_output=True,
                              text=True, timeout=timeout), None
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "%s: %s" % (type(exc).__name__, exc)


def cikti(sonuc):
    if sonuc is None:
        return ""
    return (sonuc.stdout or "") + (sonuc.stderr or "")


def git(kok, *args):
    sonuc, hata = kos(["git", "-C", str(kok), *args], KOK, timeout=120)
    if sonuc is None or sonuc.returncode != 0:
        raise RuntimeError("git %s: %s" % (
            " ".join(args), cikti(sonuc) or hata or "rc yok"))
    return sonuc.stdout.strip()


def sha256(yol):
    try:
        return hashlib.sha256(yol.read_bytes()).hexdigest()
    except OSError:
        return None


def durum(kok):
    sonuc, _ = kos(["git", "-C", str(kok), "status", "--porcelain",
                    "--untracked-files=all"], KOK, timeout=60)
    return None if sonuc is None else sonuc.stdout


def yaz(klon, veri):
    (klon / ATTESTATION).write_text(
        json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def kopya(veri):
    return copy.deepcopy(veri)


def agac_ozeti(dosyalar):
    h = hashlib.sha256()
    for f in dosyalar:
        h.update(f["path"].encode("utf-8"))
        h.update(b"\0")
        h.update(f["mode"].encode("ascii"))
        h.update(b"\0")
        h.update(f["sha256"].encode("ascii"))
        h.update(b"\0")
        h.update(str(f["size"]).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def sifirla(klon, head):
    git(klon, "reset", "--hard", "--quiet", head)
    git(klon, "checkout", "--quiet", "--", ATTESTATION)


def yan_commit(klon, head):
    """HEAD'in atasi olmayan, gecerli bir commit ve tree dondurur."""
    git(klon, "checkout", "--quiet", "-b", "kanit-yan", head)
    yol = klon / "README.md"
    yol.write_text(yol.read_text(encoding="utf-8") + "\nYAN DAL TESTI\n",
                   encoding="utf-8")
    git(klon, "add", "README.md")
    git(klon, "-c", "user.name=kanit-test", "-c",
        "user.email=kanit-test@example.invalid",
        "commit", "--quiet", "-m", "kanit negatif yan dal")
    yan = git(klon, "rev-parse", "HEAD")
    yan_tree = git(klon, "rev-parse", "HEAD^{tree}")
    git(klon, "checkout", "--quiet", "--detach", head)
    git(klon, "reset", "--hard", "--quiet", head)
    return yan, yan_tree


def ileri_commit(klon):
    """Baseline'dan ileri, temiz bir commit uretir (KANIT-05)."""
    yol = klon / "README.md"
    yol.write_text(yol.read_text(encoding="utf-8") + "\nAGAC SURUKLENME TESTI\n",
                   encoding="utf-8")
    git(klon, "add", "README.md")
    git(klon, "-c", "user.name=kanit-test", "-c",
        "user.email=kanit-test@example.invalid",
        "commit", "--quiet", "-m", "kanit negatif agac suruklenmesi")


def senaryo(klon, head, bekle):
    att_yolu = klon / ATTESTATION
    try:
        temel = json.loads(att_yolu.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("klonda attestation okunamadi: %s"
                           % type(exc).__name__)
    orijinal = kopya(temel)

    def calistir(ad, rc_beklenen, kod, parca, hazirla):
        hazirla()
        sonuc, hata = kos([sys.executable, str(klon / ARAC)], klon, timeout=120)
        metin = cikti(sonuc)
        bekle(
            ad,
            sonuc is not None and sonuc.returncode == rc_beklenen
            and ("FAIL %s" % kod) in metin and parca in metin,
            "rc=%s beklenen=%s kod=%s parca=%r\n%s" % (
                None if sonuc is None else sonuc.returncode,
                rc_beklenen, kod, parca, hata or metin,
            ),
        )
        sifirla(klon, head)

    # KANIT-00: dosya yok ve bozuk JSON.
    calistir(
        "KANIT-00 attestation yok", 2, "KANIT-00", "KANIT_YOK",
        lambda: att_yolu.unlink(),
    )
    calistir(
        "KANIT-00 bozuk JSON", 2, "KANIT-00", "OKUNAMADI",
        lambda: att_yolu.write_text("{", encoding="utf-8"),
    )

    # KANIT-01: sema gecersiz.
    def sema_bozuk():
        veri = kopya(temel)
        veri["schema"] = "ATLAS-KANIT/v0"
        yaz(klon, veri)

    calistir("KANIT-01 sema", 1, "KANIT-01", "SEMA", sema_bozuk)

    # KANIT-02: var olmayan commit, ata olmayan commit, tree uyusmazligi.
    def commit_yok():
        veri = kopya(temel)
        veri["commit"] = "f" * 40
        yaz(klon, veri)

    calistir("KANIT-02 commit yok", 1, "KANIT-02", "COMMIT_YOK", commit_yok)

    def ata_degil():
        yan, yan_tree = yan_commit(klon, head)
        veri = kopya(temel)
        veri["commit"] = yan
        veri["tree"] = yan_tree
        yaz(klon, veri)

    calistir("KANIT-02 commit ata degil", 1, "KANIT-02",
             "COMMIT_ATA_DEGIL", ata_degil)

    def tree_uyusmaz():
        veri = kopya(temel)
        veri["tree"] = git(klon, "rev-parse", "HEAD^{tree}")
        yaz(klon, veri)

    calistir("KANIT-02 tree uyusmaz", 1, "KANIT-02",
             "TREE_UYUSMAZ", tree_uyusmaz)

    # KANIT-03: dosya hash'i commit agaciyla uyusmuyor.
    def dosya_hash_bozuk():
        veri = kopya(temel)
        veri["files"][0]["sha256"] = "0" * 64
        veri["tree_sha256"] = agac_ozeti(veri["files"])
        yaz(klon, veri)

    calistir("KANIT-03 dosya hash", 1, "KANIT-03",
             "DOSYA_HASH", dosya_hash_bozuk)

    # KANIT-04: dosya sayisi ve agac ozeti.
    def dosya_sayisi_bozuk():
        veri = kopya(temel)
        veri["file_count"] = max(0, veri["file_count"] - 1)
        yaz(klon, veri)

    calistir("KANIT-04 dosya sayisi", 1, "KANIT-04",
             "DOSYA_SAYISI", dosya_sayisi_bozuk)

    def agac_ozeti_bozuk():
        veri = kopya(temel)
        veri["tree_sha256"] = "0" * 64
        yaz(klon, veri)

    calistir("KANIT-04 agac ozeti", 1, "KANIT-04",
             "AGAC_OZETI", agac_ozeti_bozuk)

    # KANIT-05: temiz ama one gitmis HEAD agaci.
    calistir("KANIT-05 agac suruklendi", 1, "KANIT-05",
             "AGAC_SURUKLENDI", lambda: ileri_commit(klon))

    # KANIT-06: izlenen dosya commit edilmeden kirli.
    def kirli_agac():
        yol = klon / "README.md"
        yol.write_text(yol.read_text(encoding="utf-8") + "\nKIRLI AGAC TESTI\n",
                       encoding="utf-8")

    calistir("KANIT-06 agac kirli", 1, "KANIT-06",
             "AGAC_KIRLI", kirli_agac)

    # Temel PASS, butun negatiflerden sonra da temiz olmali.
    sifirla(klon, head)
    sonuc, hata = kos([sys.executable, str(klon / ARAC)], klon, timeout=120)
    bekle(
        "temel PASS",
        sonuc is not None and sonuc.returncode == 0
        and "PASS KANIT" in cikti(sonuc),
        hata or cikti(sonuc),
    )


def paket_guvenlik_testleri(bekle):
    """kanit.py --paket: yabanci dizini silmeden reddetmeyi olcer."""
    sys.path.insert(0, str(KOK / "tools"))
    try:
        import kanit
    finally:
        sys.path.pop(0)

    with tempfile.TemporaryDirectory(prefix="kanit-paket-guvenlik-") as gecici:
        kok = Path(gecici)
        yanlis = kok / "yanlis"
        yanlis.mkdir()
        korunacak = yanlis / "KORUNACAK"
        korunacak.write_text("dokunma\n", encoding="utf-8")
        try:
            kanit.paket_hedef_dogrula(yanlis)
        except ValueError as exc:
            bekle("yabanci paket dizini reddedildi",
                  "ATLAS kanit paketi degil" in str(exc), str(exc))
        else:
            bekle("yabanci paket dizini reddedildi", False,
                  "yabanci dizin kabul edildi")
        bekle("yabanci dizin silinmedi",
              korunacak.is_file() and korunacak.read_text(encoding="utf-8")
              == "dokunma\n", "KORUNACAK dosyasi kayboldu")

        yeni = kok / "yeni"
        try:
            coz = kanit.paket_hedef_dogrula(yeni)
        except ValueError as exc:
            bekle("yeni paket yolu kabul edildi", False, str(exc))
        else:
            bekle("yeni paket yolu kabul edildi", coz == yeni.resolve(),
                  "cozulen yol=%r" % coz)

        # Kendi urettigimiz gecerli paket kabul edilir ve yeniden yazilabilir.
        paket = kok / "gecti"
        att_metni = json.dumps({
            "schema": "ATLAS-KANIT/v1",
            "commit": "a" * 40,
            "tree": "b" * 40,
            "tree_sha256": "c" * 64,
            "files": [],
        }, ensure_ascii=False, indent=2) + "\n"
        att_verisi = {
            "commit": "a" * 40,
            "tree": "b" * 40,
            "tree_sha256": "c" * 64,
            "files": [],
        }
        komutlar = [("selftest", ["true"], 0, "PASS selftest\n", "", 1, None)]
        try:
            kanit.paket_yaz(paket, att_metni, att_verisi, komutlar)
            kanit.paket_hedef_dogrula(paket)
        except (OSError, ValueError) as exc:
            bekle("kendi paket hedefi kabul edildi", False, str(exc))
        else:
            bekle("kendi paket hedefi kabul edildi", True)

        # Paket icine sonradan eklenen yabanci dosya sahipligi bozar.
        ekstra = paket / "EKSTRA"
        ekstra.write_text("dokunma\n", encoding="utf-8")
        try:
            kanit.paket_hedef_dogrula(paket)
        except ValueError as exc:
            bekle("paket icindeki yabanci dosya reddedildi",
                  "manifest disi dosya" in str(exc), str(exc))
        else:
            bekle("paket icindeki yabanci dosya reddedildi", False,
                  "yabanci dosya kabul edildi")
        bekle("paket icindeki yabanci dosya silinmedi",
              ekstra.is_file() and ekstra.read_text(encoding="utf-8")
              == "dokunma\n", "EKSTRA dosyasi kayboldu")

        dosya = kok / "dosya"
        dosya.write_text("x", encoding="utf-8")
        try:
            kanit.paket_hedef_dogrula(dosya)
        except ValueError as exc:
            bekle("paket hedefi dosya reddedildi",
                  "dizin degil" in str(exc), str(exc))
        else:
            bekle("paket hedefi dosya reddedildi", False,
                  "dosya hedefi kabul edildi")

        for ad, yol in (("depo koku", KOK), (".git", KOK / ".git")):
            try:
                kanit.paket_hedef_dogrula(yol)
            except ValueError:
                bekle("%s reddedildi" % ad, True)
            else:
                bekle("%s reddedildi" % ad, False, str(yol))


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
            for satir in str(ayrinti).strip().splitlines()[-14:]:
                print("  | " + satir)
        hatalar.append(ad)

    paket_guvenlik_testleri(bekle)

    head_once = git(KOK, "rev-parse", "HEAD")
    durum_once = durum(KOK)
    att_yolu = KOK / ATTESTATION
    att_once = sha256(att_yolu) if att_yolu.is_file() else None
    if durum_once is None or att_once is None:
        print("KALDI kurulum: ana agac/attestation okunamadi")
        print("\nKANIT NEGATIF: FAIL — 0/0")
        return 1

    try:
        with tempfile.TemporaryDirectory(prefix="kanit-negatif-") as gecici:
            klon = Path(gecici) / "agac"
            sonuc, hata = kos(
                ["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout",
                 str(KOK), str(klon)], Path(gecici), timeout=300)
            if sonuc is None or sonuc.returncode != 0:
                raise RuntimeError("gecici klon olusturulamadi: "
                                   + (cikti(sonuc) or hata or "rc yok"))
            sonuc, hata = kos(
                ["git", "-C", str(klon), "checkout", "--quiet", "--detach",
                 head_once], Path(gecici), timeout=120)
            if sonuc is None or sonuc.returncode != 0:
                raise RuntimeError("klonda HEAD checkout edilemedi: "
                                   + (cikti(sonuc) or hata or "rc yok"))
            bekle(
                "gecici klon ana HEAD'de temiz",
                git(klon, "rev-parse", "HEAD") == head_once
                and durum(klon) == "",
                "HEAD=%r durum=%r" % (
                    git(klon, "rev-parse", "HEAD"), durum(klon)),
            )
            try:
                senaryo(klon, head_once, bekle)
            except RuntimeError as exc:
                bekle("senaryo tamamlandi", False, str(exc))
    except RuntimeError as exc:
        bekle("kurulum", False, str(exc))
    finally:
        head_sonra = git(KOK, "rev-parse", "HEAD")
        durum_sonra = durum(KOK)
        att_sonra = sha256(att_yolu) if att_yolu.is_file() else None
        bekle(
            "ana agac degismedi (HEAD/status/attestation)",
            head_sonra == head_once and durum_sonra == durum_once
            and att_sonra == att_once,
            "HEAD %r -> %r\nstatus %r -> %r\nattestation %r -> %r" % (
                head_once, head_sonra, durum_once, durum_sonra,
                att_once, att_sonra,
            ),
        )

    if hatalar:
        print("\nKANIT NEGATIF: FAIL — %d/%d" % (len(hatalar), toplam))
        return 1
    print("\nKANIT NEGATIF: PASS — %d/%d · ana agac degismedi"
          % (toplam, toplam))
    return 0


if __name__ == "__main__":
    sys.exit(main())
