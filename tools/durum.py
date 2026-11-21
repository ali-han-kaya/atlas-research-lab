#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""durum.py — docs/DURUM.md'yi tek kaynaktan uret ve bayatligi denetle.

NEDEN VAR: Oz-test ve envanter sayilari AGENTS.md, SURUM.md, README.md ve
docs/README.md arasinda elle tekrarlaniyordu; biri guncellenince digerleri
bayatliyordu. Bu betik tek bir `docs/DURUM.md` uretir. Sayfa:

  * ATLAS ve KOD oz-testlerini CANLI kosar (sayiyi tahmin etmez),
  * pinli ATLAS envanterini `OZTEST-TABAN.json`dan okur,
  * kapı envanterini `SURUM.md` C15f makine blogundan okur,
  * `docs/OLGULAR.md` kayitlariyla capraz kontrol eder.

Sayfa elle duzenlenmez. `--kontrol` (CI) ayni kaynaklari yeniden olcup
committed sayfayla karsilastirir; fark varsa rc=1 verir. Boylece sayi
degisip sayfa guncellenmezse CI kirmizi olur.

KULLANIM
  python3 tools/durum.py --yaz        # kanonik kayitlardan docs/DURUM.md'yi yenile
  python3 tools/durum.py --kontrol    # canli testlerle bayat mi? (varsayilan)
  python3 tools/durum.py --stdout     # yazmadan uretilen sayfayi bas

`--yaz` hizli yoldur: sayiyi OLGULAR/OZTEST/SURUM kayitlarindan alir. `--kontrol`
ise ATLAS ve KOD oz-testlerini yeniden kosar; canli sayi kanonik kayitla veya
sayfayla uyusmazsa rc=1 verir. CI bu ikinci kipi kullanir.

CIKIS
  0  sayfa guncel / basariyla yazildi
  1  sayfa bayat, test basarisiz veya kaynak uyusmuyor
  2  kullanim hatasi
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SAYFA = KOK / "docs" / "DURUM.md"
TABAN = KOK / "ATLAS_SABLONLAR" / "scripts" / "OZTEST-TABAN.json"
OLGULAR = KOK / "docs" / "OLGULAR.md"
SURUM = KOK / "SURUM.md"
KATALOG = KOK / "tools" / "model_katalog.json"


class DurumHatasi(Exception):
    pass


def oku(yol):
    try:
        return yol.read_text(encoding="utf-8")
    except OSError as exc:
        raise DurumHatasi("%s okunamadi: %s" % (yol.relative_to(KOK), exc))


def json_blok(metin, bas, bit, ad):
    desen = (re.escape(bas) + r"\s*```json\s*(\{.*?\})\s*```\s*"
             + re.escape(bit))
    eslesme = re.search(desen, metin, re.DOTALL)
    if not eslesme:
        raise DurumHatasi("%s: tek JSON blogu bulunamadi" % ad)
    try:
        return json.loads(eslesme.group(1))
    except ValueError as exc:
        raise DurumHatasi("%s: JSON bozuk: %s" % (ad, exc))


def c15f_bloku(metin):
    eslesme = re.search(
        r"<!-- C15f:basla -->\s*(.*?)\s*<!-- C15f:bitti -->", metin, re.DOTALL)
    if not eslesme:
        raise DurumHatasi("SURUM.md: C15f blogu bulunamadi")
    veri = {}
    for satir in eslesme.group(1).splitlines():
        if not satir.strip():
            continue
        if ":" not in satir:
            raise DurumHatasi("SURUM.md C15f: gecersiz satir: %r" % satir)
        anahtar, deger = satir.split(":", 1)
        anahtar, deger = anahtar.strip(), deger.strip()
        try:
            veri[anahtar] = int(deger)
        except ValueError:
            raise DurumHatasi("SURUM.md C15f: %s tamsayi degil" % anahtar)
    return veri


def python_dosya_sayisi():
    """H2'nin saydigi python dosyalari; dogrula.py ile ayni atlama kumesi."""
    atla = {".git", "__pycache__", "node_modules", ".pytest_cache",
            ".ruff_cache", ".venv", ".venv-token"}
    sayi = 0
    for kok, dizinler, dosyalar in os.walk(KOK):
        dizinler[:] = [d for d in dizinler if d not in atla]
        sayi += sum(1 for ad in dosyalar if ad.endswith(".py"))
    return sayi


def _kuyruk(cikti, n=8):
    satirlar = [s for s in (cikti or "").splitlines() if s.strip()]
    return "\n".join(satirlar[-n:])[:1200] or "(bos cikti)"


def oztest(betik, argumanlar, desen, ad):
    """Bir oz-testi canli kosar ve (gecen, toplam) dondurur."""
    ortam = dict(os.environ)
    ortam.pop("ATLAS_LAB", None)
    if KATALOG.is_file():
        ortam["ATLAS_MODEL_KATALOG"] = str(KATALOG)
    komut = [sys.executable, str(KOK / betik)] + list(argumanlar)
    try:
        r = subprocess.run(komut, cwd=str(KOK), env=ortam, capture_output=True,
                           text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DurumHatasi("%s kosulamadi: %s" % (ad, exc))
    cikti = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise DurumHatasi("%s rc=%d\n%s" % (ad, r.returncode, _kuyruk(cikti)))
    eslesme = re.search(desen, cikti, re.MULTILINE)
    if not eslesme:
        raise DurumHatasi("%s: ozet satiri yok\n%s" % (ad, _kuyruk(cikti)))
    return int(eslesme.group(1)), int(eslesme.group(2))


def olculeri_topla(canli=False):
    try:
        taban = json.loads(oku(TABAN))
    except ValueError as exc:
        raise DurumHatasi("OZTEST-TABAN.json: JSON bozuk: %s" % exc)
    if not isinstance(taban, dict):
        raise DurumHatasi("OZTEST-TABAN.json: nesne degil")
    sayi = taban.get("sayi")
    kimlikler = taban.get("kimlikler")
    kimlik_hash = taban.get("kimlik_hash")
    if type(sayi) is not int or sayi <= 0:
        raise DurumHatasi("OZTEST-TABAN.json: sayi pozitif tamsayi degil")
    if not isinstance(kimlikler, list) or len(kimlikler) != sayi:
        raise DurumHatasi("OZTEST-TABAN.json: kimlikler sayisi sayi ile uyusmuyor")
    if not isinstance(kimlik_hash, str) or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", kimlik_hash):
        raise DurumHatasi("OZTEST-TABAN.json: kimlik_hash gecersiz")

    olgular = json_blok(oku(OLGULAR), "<!-- OLGULAR_JSON_BASLA -->",
                        "<!-- OLGULAR_JSON_BITIR -->", "OLGULAR.md")
    for alan in ("atlas_envanter_sayisi", "atlas_son_gecen", "kod_son_gecen"):
        if type(olgular.get(alan)) is not int:
            raise DurumHatasi("OLGULAR.md: %s tamsayi degil" % alan)

    surum = c15f_bloku(oku(SURUM))
    for alan in ("skill_lint_kontrol", "skill_kapi_sayisi",
                 "SKILL_md_satir", "kapi_taban_kimlik", "atlas_envanter"):
        if alan not in surum:
            raise DurumHatasi("SURUM.md C15f: %s alani yok" % alan)

    if canli:
        atlas_gecen, atlas_toplam = oztest(
            "ATLAS_SABLONLAR/scripts/atlas_selftest.py", ["--sessiz"],
            r"^OZ-TEST:\s*(\d+)/(\d+)\s+gecti", "ATLAS oz-testi")
        kod_gecen, kod_toplam = oztest(
            "KOD_SABLONLAR/scripts/kod_selftest.py", [],
            r"^KOD OZ-TEST:\s*(\d+)/(\d+)\s+gecti", "KOD oz-testi")
    else:
        # Hizli uretim: son kayitli canli olcum. CI `--kontrol` ile bunu
        # yeniden kosar; kayit ile canli ayrisirsa kirmizi olur.
        atlas_gecen = olgular["atlas_son_gecen"]
        atlas_toplam = olgular["atlas_envanter_sayisi"]
        kod_gecen = kod_toplam = olgular["kod_son_gecen"]

    # Fail-closed capraz kontroller: sayfa, kaynaklardan biriyle celisemez.
    if atlas_gecen != atlas_toplam:
        raise DurumHatasi("ATLAS oz-testi eksik: %d/%d" % (atlas_gecen, atlas_toplam))
    if kod_gecen != kod_toplam:
        raise DurumHatasi("KOD oz-testi eksik: %d/%d" % (kod_gecen, kod_toplam))
    if atlas_toplam != sayi:
        raise DurumHatasi(
            "ATLAS canli toplam=%d, pinli envanter=%d" % (atlas_toplam, sayi))
    if olgular["atlas_envanter_sayisi"] != sayi:
        raise DurumHatasi(
            "OLGULAR atlas_envanter_sayisi=%d, pin=%d"
            % (olgular["atlas_envanter_sayisi"], sayi))
    if olgular["atlas_son_gecen"] != atlas_gecen:
        raise DurumHatasi(
            "OLGULAR atlas_son_gecen=%d, %s=%d"
            % (olgular["atlas_son_gecen"],
               "canli" if canli else "sayfa", atlas_gecen))
    if olgular["kod_son_gecen"] != kod_gecen:
        raise DurumHatasi(
            "OLGULAR kod_son_gecen=%d, %s=%d"
            % (olgular["kod_son_gecen"],
               "canli" if canli else "sayfa", kod_gecen))
    if surum["atlas_envanter"] != sayi:
        raise DurumHatasi(
            "SURUM atlas_envanter=%d, pin=%d" % (surum["atlas_envanter"], sayi))
    if surum["skill_kapi_sayisi"] != surum["skill_lint_kontrol"]:
        raise DurumHatasi(
            "SURUM skill_kapi_sayisi=%d, skill_lint_kontrol=%d"
            % (surum["skill_kapi_sayisi"], surum["skill_lint_kontrol"]))

    return {
        "atlas_gecen": atlas_gecen,
        "atlas_toplam": atlas_toplam,
        "kod_gecen": kod_gecen,
        "kod_toplam": kod_toplam,
        "sayi": sayi,
        "kimlik_hash": kimlik_hash,
        "surum": surum,
        "python_dosya": python_dosya_sayisi(),
    }


def uret(canli=False):
    o = olculeri_topla(canli)
    s = o["surum"]
    satirlar = [
        "# DURUM — ÜRETİLMİŞ GÜNCEL SAYILAR",
        "",
        "> **Bu dosya üretilmiştir; elle düzenlenmez.** Kaynak: kanonik öz-test kayıtları,",
        "> `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` ve `SURUM.md` C15f makine bloğu;",
        "> CI canlı koşuyla doğrular.",
        "> Yenile: `make durum-yaz` · Bayatlık denetimi: `make durum-kontrol` (CI).",
        "",
        "## Öz-testler (son kayıtlı canlı ölçüm; CI yeniden koşar)",
        "",
        "| Kalem | Sonuç | Komut |",
        "|---|---|---|",
        "| ATLAS öz-testi | %d/%d | `python3 ATLAS_SABLONLAR/scripts/atlas_selftest.py --sessiz` |"
        % (o["atlas_gecen"], o["atlas_toplam"]),
        "| KOD öz-testi | %d/%d | `python3 KOD_SABLONLAR/scripts/kod_selftest.py` |"
        % (o["kod_gecen"], o["kod_toplam"]),
        "",
        "## Envanter",
        "",
        "| Kalem | Değer | Kaynak |",
        "|---|---|---|",
        "| ATLAS pinli test envanteri | %d | `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` (`sayi`) |"
        % o["sayi"],
        "| ATLAS envanter kimlik hash'i | `%s` | `ATLAS_SABLONLAR/scripts/OZTEST-TABAN.json` (`kimlik_hash`) |"
        % o["kimlik_hash"],
        "| Python dosya sayısı (H2) | %d | `make dogrula` H2 taraması |"
        % o["python_dosya"],
        "| Kapı lint kontrolü | %d | `SURUM.md` C15f (`skill_lint_kontrol`) |"
        % s["skill_lint_kontrol"],
        "| Kapı envanteri | %d | `SURUM.md` C15f (`skill_kapi_sayisi`) |"
        % s["skill_kapi_sayisi"],
        "| Kapı taban kimlik | %d | `SURUM.md` C15f (`kapi_taban_kimlik`) |"
        % s["kapi_taban_kimlik"],
        "| `SKILL.md` satır | %d | `SURUM.md` C15f (`SKILL_md_satir`) |"
        % s["SKILL_md_satir"],
        "",
        "## Çapraz kontrol",
        "",
        "- ATLAS: canlı %d/%d = pinli envanter %d = OLGULAR %d = SURUM %d"
        % (o["atlas_gecen"], o["atlas_toplam"], o["sayi"],
           o["sayi"], s["atlas_envanter"]),
        "- KOD: canlı %d/%d = OLGULAR %d"
        % (o["kod_gecen"], o["kod_toplam"], o["kod_gecen"]),
        "",
        "Bu üç eşitlikten biri bozulursa `make durum-kontrol` kırmızı olur;",
        "sayılar belgeye elle yazılmaz.",
        "",
    ]
    return "\n".join(satirlar)


def main(argv=None):
    ap = argparse.ArgumentParser(description="DURUM sayfasini uret/denetle")
    grup = ap.add_mutually_exclusive_group()
    grup.add_argument("--yaz", action="store_true", help="docs/DURUM.md'yi yenile")
    grup.add_argument("--kontrol", action="store_true", help="bayat mi denetle (varsayilan)")
    grup.add_argument("--stdout", action="store_true", help="yazmadan bas")
    args = ap.parse_args(argv)

    try:
        icerik = uret(canli=args.kontrol)
        if args.stdout:
            sys.stdout.write(icerik)
            return 0
        if args.yaz:
            SAYFA.parent.mkdir(parents=True, exist_ok=True)
            onceki = SAYFA.read_text(encoding="utf-8") if SAYFA.is_file() else None
            SAYFA.write_text(icerik, encoding="utf-8")
            if onceki == icerik:
                print("DURUM: YAZILDI (degisiklik yok) %s" % SAYFA)
            else:
                print("DURUM: YAZILDI %s" % SAYFA)
            return 0
        if not SAYFA.is_file():
            print("DURUM: FAIL — %s yok; once `make durum-yaz`" % SAYFA)
            return 1
        mevcut = SAYFA.read_text(encoding="utf-8")
        if mevcut == icerik:
            print("DURUM: GUNCEL — %s" % SAYFA)
            return 0
        print("DURUM: BAYAT — %s" % SAYFA)
        fark = difflib.unified_diff(
            mevcut.splitlines(), icerik.splitlines(),
            fromfile="committed", tofile="uretilen", lineterm="")
        for i, satir in enumerate(fark):
            if i >= 80:
                print("... (fark kirpildi; `make durum-yaz` ile yenile)")
                break
            print(satir)
        return 1
    except DurumHatasi as exc:
        print("DURUM: FAIL — %s" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
