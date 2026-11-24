#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kapi_cikti.py — ATLAS kapı çıktısının sürümlü JSON sözleşmesi.

NEDEN VAR: kapılar arasındaki bağ metin satırlarına ve düzenli ifadelere
dayanıyordu. Bir özet satırının sözcük düzeni değişince tüketici sessizce
değer bulamıyor, kimi zaman da yanlış satırı seçiyordu. Bu modül tek bir
sürümlü zarf tanımlar:

    ATLAS-KAPI-CIKTI/v1
    {schema, surum, kapi, hukum, rc, uretildi, kontroller, sayilar, hata}

Tüketiciler `sec()` ile kontrol kimliğine göre değer okur; serbest metin
ayıklamaz. `oku()` zarftaki sürümü ve şemayı doğrular; şema yoksa fail-closed
davranır (doğrulanmamış çıktıyı kabul etmez).
"""
import datetime
import json
from pathlib import Path

SEMA = "ATLAS-KAPI-CIKTI/v1"
SURUM = "1.0.0"
SEMA_YOLU = Path(__file__).resolve().parents[1] / "schemas" / "atlas-kapi-cikti.schema.json"
DURUMLAR = ("PASS", "FAIL", "OLCULMEDI", "ATLANDI")
HUKUMLER = ("PASS", "FAIL", "KOSULLU", "OLCULMEDI")


class SozlesmeHatasi(Exception):
    """Kapı çıktısı sözleşmeye uymuyor."""


def _tek_satir(metin, sinir=4000):
    """Ham kanıt tek satırdır; JSON'a gömülecek metni taşma yapmadan tut."""
    if metin is None:
        return None
    s = " ".join(str(metin).split())
    return s[:sinir]


def kontrol(kid, ad, durum, deger=None, ayrinti=None, ham=None,
            kaynak=None, beklenen=None):
    """Sözleşmedeki tek kontrol kaydını üretir."""
    if durum not in DURUMLAR:
        raise ValueError("gecersiz kontrol durumu: %r" % (durum,))
    return {
        "id": str(kid),
        "ad": str(ad),
        "durum": durum,
        "deger": None if deger is None else str(deger)[:200],
        "beklenen": None if beklenen is None else str(beklenen)[:200],
        "ayrinti": _tek_satir(ayrinti, 2000),
        "ham": _tek_satir(ham),
        "kaynak": None if kaynak is None else str(kaynak)[:500],
    }


def sayilar(kontroller):
    """Kontrollerden sayaçları türet; çağıran ayrı sayaç uydurmaz."""
    toplam = len(kontroller)
    gecti = sum(1 for k in kontroller if k.get("durum") == "PASS")
    kalan = sum(1 for k in kontroller if k.get("durum") == "FAIL")
    olculmedi = sum(1 for k in kontroller if k.get("durum") == "OLCULMEDI")
    atlandi = sum(1 for k in kontroller if k.get("durum") == "ATLANDI")
    return {
        "toplam": toplam,
        "gecti": gecti,
        "kalan": kalan,
        "olculmedi": olculmedi,
        "atlandi": atlandi,
    }


def uret(kapi, kontroller, rc=0, hukum=None, hata=None, zaman=None):
    """Geçerli zarfı kur. Hüküm verilmezse rc ve kontrol durumundan türetilir."""
    ks = list(kontroller)
    if hukum is None:
        if hata:
            hukum = "OLCULMEDI"
        elif any(k.get("durum") == "FAIL" for k in ks):
            hukum = "FAIL"
        elif any(k.get("durum") == "OLCULMEDI" for k in ks):
            hukum = "OLCULMEDI"
        elif rc != 0:
            hukum = "FAIL"
        else:
            hukum = "PASS"
    if hukum not in HUKUMLER:
        raise ValueError("gecersiz hukum: %r" % (hukum,))
    return {
        "schema": SEMA,
        "surum": SURUM,
        "kapi": str(kapi),
        "hukum": hukum,
        "rc": int(rc),
        "uretildi": zaman or datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kontroller": ks,
        "sayilar": sayilar(ks),
        "hata": _tek_satir(hata, 2000),
    }


def _sema():
    try:
        return json.loads(SEMA_YOLU.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SozlesmeHatasi("sema okunamadi: %s" % e)


def dogrula(veri):
    """Şemayı ve şema dışı değişmezleri doğrula; hata varsa yükselt.

    Şema doğrulaması jsonschema ile yapılır. Kütüphane yoksa çıktı geçerli
    sayılmaz: bu modülün varlık nedeni doğrulanmış sözleşmedir.
    """
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as e:  # pragma: no cover - kurulum hatası
        raise SozlesmeHatasi("jsonschema yok: %s" % e)
    sema = _sema()
    try:
        Draft202012Validator.check_schema(sema)
        Draft202012Validator(sema, format_checker=FormatChecker()).validate(veri)
    except Exception as e:
        raise SozlesmeHatasi("sema ihlali: %s" % str(e).splitlines()[0][:400])
    if veri.get("schema") != SEMA or veri.get("surum") != SURUM:
        raise SozlesmeHatasi("surum uyusmuyor: %r/%r"
                             % (veri.get("schema"), veri.get("surum")))
    kimlikler = [k.get("id") for k in veri.get("kontroller", [])]
    if len(kimlikler) != len(set(kimlikler)):
        raise SozlesmeHatasi("yinelenen kontrol kimligi")
    bekle = sayilar(veri.get("kontroller", []))
    if veri.get("sayilar") != bekle:
        raise SozlesmeHatasi("sayilar kontrollerle celisiyor: %r != %r"
                             % (veri.get("sayilar"), bekle))
    if veri.get("hukum") == "PASS" and (veri.get("rc") != 0 or bekle["kalan"]):
        raise SozlesmeHatasi("PASS hukumu rc/kalan ile celisiyor")
    if veri.get("hukum") == "FAIL" and veri.get("rc") == 0 and not bekle["kalan"]:
        raise SozlesmeHatasi("FAIL hukumu rc/kalan ile celisiyor")
    return veri


def oku(metin):
    """Metni JSON zarfı olarak oku ve doğrula."""
    try:
        veri = json.loads(metin)
    except (TypeError, ValueError) as e:
        raise SozlesmeHatasi("JSON okunamadi: %s" % e)
    if not isinstance(veri, dict):
        raise SozlesmeHatasi("kok nesne degil")
    return dogrula(veri)


def _alan(veri, yol):
    parca = str(yol).split(".")
    deger = veri
    for ad in parca:
        if isinstance(deger, dict) and ad in deger:
            deger = deger[ad]
        else:
            raise SozlesmeHatasi("alan yok: %s" % yol)
    return deger


def sec(veri, kid, alan="deger"):
    """Kontrol kimliğine göre değer seç; yoksa fail-closed."""
    for k in veri.get("kontroller", []):
        if k.get("id") == kid:
            return _alan(k, alan)
    raise SozlesmeHatasi("kontrol yok: %s" % kid)


def yaz(veri, yol=None):
    """Zarfı doğrula; istenirse dosyaya yaz ve metni döndür."""
    dogrula(veri)
    metin = json.dumps(veri, ensure_ascii=False, indent=2) + "\n"
    if yol:
        p = Path(yol)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(metin, encoding="utf-8")
    return metin
