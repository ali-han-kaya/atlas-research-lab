#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""model_katalog_uret.py — models.dev anlik goruntusunden allowlist uretir.

`tools/model_katalog.json` yalniz aktif hatlarda gecen model kimliklerini
tasir. Bu arac canli kayittan yetenek bayraklarini okur ve dosyayi yeniden
uretir; elle JSON yazilmaz.

KULLANIM
  python3 tools/model_katalog_uret.py \
    --api-dosya /tmp/models.dev-api.json \
    --kimlik-dosya /tmp/atlas-model-ids.txt \
    --cikti /tmp/model_katalog.json

CIKIS
  0 = yazildi
  1 = kimlik gecersiz, eksik veya deprecated (cikti yazilmaz)
  2 = girdi okunamadi veya yazilamadi (cikti yazilmaz)
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

YETENEKLER = ('reasoning', 'tool_call')
ACIKLAMA = (
    'Sabit model katalogu (allowlist anlik goruntusu). MOD-1/MOD-2 kapilari '
    'ajanlarin BU listedeki modelleri kullandigini denetler; boylece sayi her '
    'klonda ayni cikar. Canli katalogla denetim icin ATLAS_MODEL_KATALOG=<yol> '
    "verin. Tazelik icin: make katalog-kontrol (ag gerekir; CI'da kosmaz).")
KAYNAK = 'models.dev semasi; yalniz depoda gecen model kimlikleri, %s'


class GirdiHatasi(Exception):
    """Girdi okunamadi; sonuc OLCULMEDI'dir."""


class UretimHatasi(Exception):
    """Canli kayit allowlist'i karsilamiyor; cikti yazilmaz."""


def katalog_uret(api, kimlikler, tarih):
    """Kimlikleri canli kayitla dogrular ve katalog sozlugunu dondurur."""
    if not kimlikler:
        raise UretimHatasi('aktif model kimligi bulunamadi')
    saglayicilar = {}
    for tam in sorted(set(kimlikler)):
        saglayici, ayrac, model = tam.partition('/')
        if not ayrac or not saglayici or not model:
            raise UretimHatasi('gecersiz kimlik: %s' % tam)
        govde = api.get(saglayici)
        if not isinstance(govde, dict):
            raise UretimHatasi('canli katalogda saglayici yok: %s' % saglayici)
        modeller = govde.get('models')
        if not isinstance(modeller, dict):
            raise UretimHatasi('canli katalogda models yok: %s' % saglayici)
        kayit = modeller.get(model)
        if not isinstance(kayit, dict):
            raise UretimHatasi('canli katalogda yok: %s' % tam)
        if kayit.get('status') == 'deprecated':
            raise UretimHatasi('canli katalogda deprecated: %s' % tam)
        for alan in YETENEKLER:
            if not isinstance(kayit.get(alan), bool):
                raise UretimHatasi('%s boolean degil: %s' % (alan, tam))
        saglayicilar.setdefault(saglayici, {})[model] = {
            alan: kayit[alan] for alan in YETENEKLER}
    veri = {'_aciklama': ACIKLAMA, '_kaynak': KAYNAK % tarih.isoformat()}
    for saglayici in sorted(saglayicilar):
        veri[saglayici] = {'models': saglayicilar[saglayici]}
    return veri


def metin_uret(veri):
    """Depodaki kanonik bicimi (tek satirlik model kayitlari) dondurur."""
    satirlar = ['{']
    for alan in ('_aciklama', '_kaynak'):
        satirlar.append(' %s: %s,' % (
            json.dumps(alan), json.dumps(veri[alan], ensure_ascii=False)))
    saglayicilar = sorted(k for k in veri if not k.startswith('_'))
    for i, saglayici in enumerate(saglayicilar):
        modeller = sorted(veri[saglayici]['models'].items())
        satirlar += [' %s: {' % json.dumps(saglayici), '  "models": {']
        for j, (model, kayit) in enumerate(modeller):
            satirlar.append('   %s: %s%s' % (
                json.dumps(model), json.dumps(kayit, ensure_ascii=False),
                ',' if j < len(modeller) - 1 else ''))
        satirlar += ['  }', ' }' + (',' if i < len(saglayicilar) - 1 else '')]
    satirlar.append('}')
    return '\n'.join(satirlar) + '\n'


def _girdi_oku(api_yolu, kimlik_yolu):
    try:
        api = json.loads(Path(api_yolu).read_text(encoding='utf-8'))
        satirlar = Path(kimlik_yolu).read_text(encoding='utf-8').splitlines()
    except (OSError, ValueError) as hata:
        raise GirdiHatasi('girdi okunamadi: %s' % hata)
    if not isinstance(api, dict):
        raise GirdiHatasi('api kok nesne degil')
    return api, [s.strip() for s in satirlar if s.strip()]


def main(argv=None):
    ayrac = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ayrac.add_argument('--api-dosya', default='/tmp/models.dev-api.json')
    ayrac.add_argument('--kimlik-dosya', default='/tmp/atlas-model-ids.txt')
    ayrac.add_argument('--cikti', default='/tmp/model_katalog.json')
    ayrac.add_argument('--tarih', type=datetime.date.fromisoformat,
                       help='_kaynak tarihi (varsayilan: bugun)')
    secim = ayrac.parse_args(argv)
    try:
        api, kimlikler = _girdi_oku(secim.api_dosya, secim.kimlik_dosya)
        veri = katalog_uret(api, kimlikler,
                            secim.tarih or datetime.date.today())
    except GirdiHatasi as hata:
        print('OLCULMEDI: %s' % hata, file=sys.stderr)
        return 2
    except UretimHatasi as hata:
        print('HATA: %s' % hata, file=sys.stderr)
        return 1
    try:
        Path(secim.cikti).write_text(metin_uret(veri), encoding='utf-8')
    except OSError as hata:
        print('OLCULMEDI: cikti yazilamadi: %s' % hata, file=sys.stderr)
        return 2
    adet = sum(len(g['models']) for k, g in veri.items()
               if not k.startswith('_'))
    print('yazildi: %s (%d model)' % (secim.cikti, adet))
    return 0


if __name__ == '__main__':
    sys.exit(main())
