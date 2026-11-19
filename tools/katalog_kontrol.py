#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""katalog_kontrol.py — sabit model katalogu models.dev'de hala gecerli mi?

NEDEN VAR
  `tools/model_katalog.json` bir ALLOWLIST anlik goruntusudur. `make dogrula`
  hermetik kalsin diye canli kataloga bakmaz; bu yuzden allowlist sessizce
  bayatlayabilir. Bu betik ISTEGE BAGLIDIR, AG GEREKTIRIR ve CI'da KOSMAZ.
  Yalnizca yerel model kimliklerinin models.dev'de hala bulundugunu ve yerel
  `reasoning` / `tool_call` degerlerinin canli kaynakla celismedigini olcer.

KULLANIM
  python3 tools/katalog_kontrol.py
  python3 tools/katalog_kontrol.py --katalog tools/model_katalog.json
  python3 tools/katalog_kontrol.py --api-dosya /tmp/models.dev-api.json
  python3 tools/katalog_kontrol.py --timeout 30

CIKIS
  0 = tum yerel modeller canli katalogda ve yetenekler uyumlu
  1 = en az bir bayat/eksik/celiskili kayit var (adlariyla)
  2 = olculemedi (ag, JSON, kullanim)
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
VARSAYILAN_KATALOG = KOK / 'tools' / 'model_katalog.json'
VARSAYILAN_API = 'https://models.dev/api.json'
YETENEKLER = ('reasoning', 'tool_call')


class Hata(Exception):
    """Kontrolun olcum uretemedigi durum; PASS'a cevrilmez."""


def _oku_json(yol):
    try:
        with open(yol, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise Hata('JSON okunamadi: %s (%s)' % (yol, e))


def _api_oku(adres, timeout):
    istek = urllib.request.Request(
        adres,
        headers={'User-Agent': 'atlas-katalog-kontrol/1.0',
                 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(istek, timeout=timeout) as cevap:
            ham = cevap.read()
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise Hata('models.dev okunamadi: %s' % e)
    try:
        return json.loads(ham.decode('utf-8'))
    except (UnicodeDecodeError, ValueError) as e:
        raise Hata('models.dev JSON degil: %s' % e)


def _katalog(veri):
    """Yerel katalogu {saglayici: {model: {...}}} olarak dogrula."""
    if not isinstance(veri, dict):
        raise Hata('yerel katalog kok nesnesi degil')
    saglayicilar = {}
    for ad, saglayici in veri.items():
        if ad.startswith('_'):
            continue
        if not isinstance(saglayici, dict):
            raise Hata('yerel saglayici nesnesi degil: %s' % ad)
        modeller = saglayici.get('models')
        if not isinstance(modeller, dict) or not modeller:
            raise Hata('yerel saglayici models alani bos/bozuk: %s' % ad)
        for kimlik, model in modeller.items():
            if not isinstance(model, dict):
                raise Hata('yerel model kaydi nesnesi degil: %s/%s' % (ad, kimlik))
        saglayicilar[ad] = modeller
    if not saglayicilar:
        raise Hata('yerel katalogda saglayici yok')
    return saglayicilar


def _canli(veri):
    if not isinstance(veri, dict):
        raise Hata('models.dev kok nesnesi degil')
    return veri


def karsilastir(yerel, canli):
    """[(tur, tam_ad, ayrinti)], toplam_model, gecerli_model dondur."""
    bulgular = []
    etkilenen = set()

    for saglayici in sorted(yerel):
        canli_saglayici = canli.get(saglayici)
        if not isinstance(canli_saglayici, dict):
            bulgular.append(('SAGLAYICI_YOK', saglayici,
                             'models.dev saglayicisi yok'))
            etkilenen.update('%s/%s' % (saglayici, m) for m in yerel[saglayici])
            continue
        canli_modeller = canli_saglayici.get('models')
        if not isinstance(canli_modeller, dict):
            bulgular.append(('SAGLAYICI_BOZUK', saglayici,
                             'models.dev models alani yok/bozuk'))
            etkilenen.update('%s/%s' % (saglayici, m) for m in yerel[saglayici])
            continue

        for kimlik in sorted(yerel[saglayici]):
            tam = '%s/%s' % (saglayici, kimlik)
            model = canli_modeller.get(kimlik)
            if not isinstance(model, dict):
                bulgular.append(('MODEL_YOK', tam,
                                 'models.dev %s.models icinde yok' % saglayici))
                etkilenen.add(tam)
                continue

            for alan in YETENEKLER:
                if alan not in yerel[saglayici][kimlik]:
                    continue
                yerel_deger = yerel[saglayici][kimlik][alan]
                canli_deger = model.get(alan)
                if not isinstance(yerel_deger, bool):
                    bulgular.append(('KATALOG_BOZUK', tam,
                                     '%s yerel kayitta boolean degil' % alan))
                    etkilenen.add(tam)
                elif not isinstance(canli_deger, bool):
                    bulgular.append(('ALAN_YOK', tam,
                                     'models.dev kaydinda %s boolean degil' % alan))
                    etkilenen.add(tam)
                elif yerel_deger != canli_deger:
                    bulgular.append(('YETENEK_FARKLI', tam,
                                     '%s %s -> %s' % (alan, yerel_deger, canli_deger)))
                    etkilenen.add(tam)

            if model.get('status') == 'deprecated':
                bulgular.append(('DURUM', tam, 'models.dev durumu deprecated'))
                etkilenen.add(tam)

    toplam = sum(len(modeller) for modeller in yerel.values())
    return bulgular, toplam, toplam - len(etkilenen)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Sabit model katalogunu models.dev canli kataloguyla karsilastirir.')
    ap.add_argument('--katalog', default=str(VARSAYILAN_KATALOG),
                    help='yerel allowlist JSON yolu (varsayilan: tools/model_katalog.json)')
    kaynak = ap.add_mutually_exclusive_group()
    kaynak.add_argument('--api-dosya',
                        help='ag yerine yerel models.dev api.json kopyasi kullan')
    kaynak.add_argument('--api-url', default=VARSAYILAN_API,
                        help='models.dev API adresi (varsayilan: %s)' % VARSAYILAN_API)
    ap.add_argument('--timeout', type=int, default=20,
                    help='ag zaman asimi, saniye (varsayilan: 20)')
    args = ap.parse_args(argv)

    if args.timeout <= 0:
        print('KATALOG KONTROL: OLCULEMEDI — timeout pozitif olmali')
        return 2

    try:
        yerel = _katalog(_oku_json(Path(args.katalog)))
        if args.api_dosya:
            canli = _canli(_oku_json(Path(args.api_dosya)))
            api_etiketi = args.api_dosya
        else:
            canli = _canli(_api_oku(args.api_url, args.timeout))
            api_etiketi = args.api_url
    except Hata as e:
        print('KATALOG KONTROL: OLCULEMEDI — %s' % e)
        return 2

    bulgular, toplam, gecerli = karsilastir(yerel, canli)
    print('KATALOG KONTROL — models.dev canli karsilastirma (istege bagli, ag)')
    print('katalog: %s' % args.katalog)
    print('canli: %s' % api_etiketi)
    print('saglayici=%d · model=%d' % (len(yerel), toplam))
    print()
    for tur, ad, ayrinti in bulgular:
        print('  %-14s %s — %s' % (tur, ad, ayrinti))
    if bulgular:
        print()
    print('SONUC: %d/%d gecerli · %d bulgu' % (gecerli, toplam, len(bulgular)))
    if bulgular:
        print('HUKUM: BAYAT — allowlist models.dev ile uyusmuyor; adlar yukarida.')
        return 1
    print('HUKUM: GUNCEL — tum yerel kimlikler canli katalogda.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
