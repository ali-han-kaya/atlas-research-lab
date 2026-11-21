#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""katalog_kontrol.py — sabit katalog ve KOD `bedava` profili models.dev'de gecerli mi?

NEDEN VAR
  `tools/model_katalog.json` bir ALLOWLIST anlik goruntusudur. `make dogrula`
  hermetik kalsin diye canli kataloga bakmaz; bu yuzden allowlist sessizce
  bayatlayabilir. Bu betik models.dev'i okur, allowlist'teki her kimligi ve
  `KOD_SABLONLAR/routing.profiles.json` -> `profiller.bedava` altindaki on rolu
  canli kayitla karsilastirir. Normal CI yolunda `.github/workflows/dogrula.yml`
  icindeki `bedava canli katalog` isi olarak her push/PR'da, haftalik cron'da ve
  elle tetiklemede kosar; artik istege bagli bir yerel kontrol degildir.

  KOSULLAR (bedava profili, politika: docs/KOD_BEDAVA_MODEL_POLITIKASI.md)
    - on rolun tamami ayni kimlige bakar (tek kimlik),
    - kimlik canli kayitta vardir, `status` deprecated degildir,
    - `cost.input` ve `cost.output` (varsa diger sayisal cost alanlari) 0'dir,
    - `reasoning` ve `tool_call` canlida true, yerel allowlist'te de true'dur,
    - `limit.context` / `limit.output`, `bedava_politika.asgari_limit` altina
      dusmez.

  KAYIT
    Her olcum, commit/tree/tree_sha256 ve tanim dosyalarinin SHA-256'lariyla
    birlikte append-only JSONL kaydina yazilir. `--kayit` verilmezse yazilmaz.
    Izlenen kayit yolu icin agac temiz olmalidir; degilse kayit OLCULMEDI olur.

KULLANIM
  python3 tools/katalog_kontrol.py
  python3 tools/katalog_kontrol.py --kayit docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl
  python3 tools/katalog_kontrol.py --api-dosya /tmp/models.dev-api.json
  python3 tools/katalog_kontrol.py --timeout 30

CIKIS
  0 = allowlist canli katalogda ve bedava profili butun kosullari sagliyor
  1 = en az bir bayat/eksik/celiskili kayit veya bedava kosulu ihlali (adlariyla)
  2 = olculemedi (ag, JSON, kayit, kullanim); PASS'a cevrilmez
"""
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
VARSAYILAN_KATALOG = KOK / 'tools' / 'model_katalog.json'
VARSAYILAN_PROFIL = KOK / 'KOD_SABLONLAR' / 'routing.profiles.json'
VARSAYILAN_API = 'https://models.dev/api.json'
YETENEKLER = ('reasoning', 'tool_call')
PROFIL_ADI = 'bedava'
BEKLENEN_ROL = 10
TANIM_DOSYALARI = (
    'tools/model_katalog.json',
    'KOD_SABLONLAR/routing.profiles.json',
    'KOD_SABLONLAR/opencode.json',
)


class Hata(Exception):
    """Kontrolun olcum uretemedigi durum; PASS'a cevrilmez."""


class ProfilHatasi(Exception):
    """Bedava profili sozlesmesi bozuk; bu bir yapilandirma ihlalidir."""


def _oku_json(yol):
    try:
        with open(yol, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise Hata('JSON okunamadi: %s (%s)' % (yol, e))


def _api_oku(adres, timeout):
    istek = urllib.request.Request(
        adres,
        headers={'User-Agent': 'atlas-katalog-kontrol/1.1',
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


def _bedava_profil(veri):
    """(roller, asgari_limit) dondur; sozlesme bozuksa ProfilHatasi."""
    if not isinstance(veri, dict):
        raise ProfilHatasi('profil dosyasi kok nesnesi degil')
    profiller = veri.get('profiller')
    if not isinstance(profiller, dict):
        raise ProfilHatasi('profiller nesnesi yok')
    bedava = profiller.get(PROFIL_ADI)
    if not isinstance(bedava, dict):
        raise ProfilHatasi('profiller.%s nesnesi yok' % PROFIL_ADI)
    roller = {k: v for k, v in bedava.items() if k.startswith('kod-')}
    if not roller:
        raise ProfilHatasi('profiller.%s icinde kod-* rolu yok' % PROFIL_ADI)
    if len(roller) != BEKLENEN_ROL:
        raise ProfilHatasi('profiller.%s rol sayisi %d, politika %d diyor'
                           % (PROFIL_ADI, len(roller), BEKLENEN_ROL))
    politika = veri.get('bedava_politika')
    if not isinstance(politika, dict):
        raise ProfilHatasi('bedava_politika nesnesi yok')
    asgari = politika.get('asgari_limit')
    if not isinstance(asgari, dict):
        raise ProfilHatasi('bedava_politika.asgari_limit nesnesi yok')
    for alan in ('context', 'output'):
        deger = asgari.get(alan)
        if not isinstance(deger, int) or isinstance(deger, bool) or deger <= 0:
            raise ProfilHatasi('bedava_politika.asgari_limit.%s pozitif tamsayi degil'
                               % alan)
    return roller, {'context': asgari['context'], 'output': asgari['output']}


def _model_id(deger):
    if not isinstance(deger, str):
        return None
    onek = 'openrouter/'
    if not deger.startswith(onek) or len(deger) == len(onek):
        return None
    return deger[len(onek):]


def _sayisal(deger):
    return isinstance(deger, (int, float)) and not isinstance(deger, bool)


def _canli_kayit(canli, mid):
    if not mid:
        return None
    saglayici = canli.get('openrouter')
    if not isinstance(saglayici, dict):
        return None
    modeller = saglayici.get('models')
    if not isinstance(modeller, dict):
        return None
    kayit = modeller.get(mid)
    return kayit if isinstance(kayit, dict) else None


def _bedava_denetle(roller, asgari, canli, yerel):
    """Bedava profilini olcer; (bulgular, model_id, canli_kayit, gecen, toplam)."""
    bulgular = []
    gruplar = {}
    for rol in sorted(roller):
        mid = _model_id(roller[rol])
        if mid is None:
            bulgular.append(('ROL_BOZUK', rol,
                             'deger openrouter/<model> biciminde degil: %r'
                             % (roller[rol],)))
            continue
        gruplar.setdefault(mid, []).append(rol)

    toplam = len(roller)
    gecen = 0
    if len(gruplar) > 1:
        bulgular.append(('TEK_KIMLIK_DEGIL', 'profiller.%s' % PROFIL_ADI,
                         '%d farkli kimlik: %s'
                         % (len(gruplar), ', '.join(sorted(gruplar)))))
    elif len(gruplar) == 1:
        mid = sorted(gruplar)[0]
        if len(gruplar[mid]) != toplam:
            bulgular.append(('ROL_SAYISI', 'profiller.%s' % PROFIL_ADI,
                             '%d rol kimliksiz kaldi' % (toplam - len(gruplar[mid]))))

    canli_model = None
    ana_mid = sorted(gruplar)[0] if gruplar else None
    for mid in sorted(gruplar):
        tam = 'openrouter/%s' % mid
        kayit = _canli_kayit(canli, mid)
        if not isinstance(kayit, dict):
            bulgular.append(('MODEL_YOK', tam,
                             'models.dev openrouter.models icinde yok'))
            continue
        if mid == ana_mid:
            canli_model = kayit

        ok = True

        maliyet = kayit.get('cost')
        if not isinstance(maliyet, dict):
            bulgular.append(('MALIYET_YOK', tam, 'cost nesnesi yok'))
            ok = False
        else:
            for alan in ('input', 'output'):
                deger = maliyet.get(alan)
                if not _sayisal(deger):
                    bulgular.append(('MALIYET_YOK', tam,
                                     'cost.%s sayisal degil: %r' % (alan, deger)))
                    ok = False
                elif deger != 0:
                    bulgular.append(('MALIYET', tam,
                                     'cost.%s=%s (0 olmali)' % (alan, deger)))
                    ok = False
            for alan in sorted(maliyet):
                if alan in ('input', 'output'):
                    continue
                deger = maliyet[alan]
                if _sayisal(deger) and deger != 0:
                    bulgular.append(('MALIYET', tam,
                                     'cost.%s=%s (0 olmali)' % (alan, deger)))
                    ok = False

        for alan in YETENEKLER:
            if kayit.get(alan) is not True:
                bulgular.append(('YETENEK_FARKLI', tam,
                                 'canli %s=%r (true olmali)'
                                 % (alan, kayit.get(alan))))
                ok = False

        if kayit.get('status') == 'deprecated':
            bulgular.append(('DURUM', tam, 'models.dev durumu deprecated'))
            ok = False

        limit = kayit.get('limit')
        if not isinstance(limit, dict):
            bulgular.append(('LIMIT_YOK', tam, 'limit nesnesi yok'))
            ok = False
        else:
            for alan in ('context', 'output'):
                deger = limit.get(alan)
                esik = asgari[alan]
                if not _sayisal(deger):
                    bulgular.append(('LIMIT_YOK', tam,
                                     'limit.%s sayisal degil: %r' % (alan, deger)))
                    ok = False
                elif deger < esik:
                    bulgular.append(('LIMIT_YETERSIZ', tam,
                                     'limit.%s=%s < politika %s'
                                     % (alan, deger, esik)))
                    ok = False

        yerel_model = yerel.get('openrouter', {}).get(mid)
        if not isinstance(yerel_model, dict):
            bulgular.append(('KATALOGDA_YOK', tam,
                             'tools/model_katalog.json allowlistinde yok'))
            ok = False
        else:
            for alan in YETENEKLER:
                if yerel_model.get(alan) is not True:
                    bulgular.append(('KATALOG_YETENEK', tam,
                                     'yerel allowlist %s=true degil' % alan))
                    ok = False

        if ok:
            gecen += len(gruplar[mid])

    return bulgular, ana_mid, canli_model, gecen, toplam


def _rol_satiri(rol, deger, canli_model, asgari):
    tam = deger if isinstance(deger, str) else '(bozuk)'
    if not isinstance(canli_model, dict):
        return '  ROL %-24s %s · canli=yok · cost=?/? · reasoning/tool_call=?/? · limit=?/?'
    cost = canli_model.get('cost') if isinstance(canli_model.get('cost'), dict) else {}
    limit = canli_model.get('limit') if isinstance(canli_model.get('limit'), dict) else {}
    return ('  ROL %-24s %s · canli=var · cost=%s/%s · reasoning/tool_call=%s/%s'
            ' · limit=%s/%s >= %s/%s'
            % (rol, tam, cost.get('input', '?'), cost.get('output', '?'),
               str(canli_model.get('reasoning')).lower(),
               str(canli_model.get('tool_call')).lower(),
               limit.get('context', '?'), limit.get('output', '?'),
               asgari['context'], asgari['output']))


def _git(*args):
    r = subprocess.run(['git', '-C', str(KOK)] + list(args),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise Hata('git %s: %s' % (
            ' '.join(args),
            (r.stderr or b'').decode('utf-8', 'replace').strip()[:200]))
    return r.stdout


def _metin(ham):
    return ham.decode('utf-8', 'replace').strip()


def _yol(yol):
    p = Path(yol)
    return p if p.is_absolute() else KOK / p


def _iceride(yol):
    try:
        _yol(yol).resolve().relative_to(KOK)
        return True
    except ValueError:
        return False


def _agac_kirli():
    return bool(_metin(_git('status', '--porcelain', '--untracked-files=no')))


def _tree_sha256(commit):
    spec = importlib.util.spec_from_file_location(
        'atlas_kanit', str(KOK / 'tools' / 'kanit.py'))
    if spec is None or spec.loader is None:
        raise Hata('kanit.py yuklenemedi')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.agac_ozeti(mod.agac_dosyalari(commit))


def _kayit_yaz(args, satirlar, sonuc, sebep, model, canli_kayit, asgari, rol_sayisi):
    """Olcumu append-only JSONL'e yaz; basariliysa True."""
    if not args.kayit:
        return True
    try:
        commit = _metin(_git('rev-parse', 'HEAD'))
        tree = _metin(_git('rev-parse', 'HEAD^{tree}'))
        kirli = _agac_kirli()
        if _iceride(args.kayit) and kirli:
            print('KAYIT: OLCULMEDI — agac kirli; kayit commit/tree ile eslesmez '
                  '(once degisiklikleri commit edin)')
            return False
        tanim = {}
        for rel in TANIM_DOSYALARI:
            tanim[rel] = hashlib.sha256(_git('show', 'HEAD:%s' % rel)).hexdigest()
        kayit = {
            'surum': 1,
            'zaman': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'kaynak': 'ci' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'yerel',
            'github_run_id': os.environ.get('GITHUB_RUN_ID') or None,
            'commit': commit,
            'tree': tree,
            'tree_sha256': _tree_sha256(commit),
            'tanim_sha256': tanim,
            'profil': PROFIL_ADI,
            'roller': rol_sayisi,
            'model': model,
            'asgari_limit': asgari,
            'canli': canli_kayit,
            'sonuc': sonuc,
            'sebep': sebep,
            'agac_kirli': kirli,
            'ham': satirlar,
        }
        yol = _yol(args.kayit)
        yol.parent.mkdir(parents=True, exist_ok=True)
        with open(yol, 'a', encoding='utf-8') as f:
            f.write(json.dumps(kayit, ensure_ascii=False, sort_keys=True) + '\n')
        print('KAYIT: YAZILDI %s · commit=%s · tree_sha256=%s'
              % (yol, commit[:12], kayit['tree_sha256'][:16]))
        return True
    except (Hata, OSError, ValueError) as e:
        print('KAYIT: OLCULMEDI — %s' % e)
        return False


def _kanit_ozeti(canli_model):
    if not isinstance(canli_model, dict):
        return None
    return {
        'id': canli_model.get('id'),
        'name': canli_model.get('name'),
        'family': canli_model.get('family'),
        'status': canli_model.get('status'),
        'reasoning': canli_model.get('reasoning'),
        'tool_call': canli_model.get('tool_call'),
        'cost': canli_model.get('cost'),
        'limit': canli_model.get('limit'),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Sabit katalogu ve KOD bedava profilini models.dev canli '
                    'kataloguyla karsilastirir.')
    ap.add_argument('--katalog', default=str(VARSAYILAN_KATALOG),
                    help='yerel allowlist JSON yolu (varsayilan: tools/model_katalog.json)')
    ap.add_argument('--profil-dosya', default=str(VARSAYILAN_PROFIL),
                    help='routing.profiles.json yolu (varsayilan: KOD_SABLONLAR)')
    ap.add_argument('--kayit',
                    help='olcum kaydini bu JSONL dosyasina ekle (append-only)')
    kaynak = ap.add_mutually_exclusive_group()
    kaynak.add_argument('--api-dosya',
                        help='ag yerine yerel models.dev api.json kopyasi kullan')
    kaynak.add_argument('--api-url', default=VARSAYILAN_API,
                        help='models.dev API adresi (varsayilan: %s)' % VARSAYILAN_API)
    ap.add_argument('--timeout', type=int, default=20,
                    help='ag zaman asimi, saniye (varsayilan: 20)')
    args = ap.parse_args(argv)

    satirlar = []

    def yaz(satir=''):
        satirlar.append(satir)
        print(satir)

    if args.timeout <= 0:
        yaz('KATALOG KONTROL: OLCULMEDI — timeout pozitif olmali')
        return 2

    try:
        yerel = _katalog(_oku_json(Path(args.katalog)))
    except Hata as e:
        yaz('KATALOG KONTROL: OLCULMEDI — %s' % e)
        _kayit_yaz(args, satirlar, 'OLCULMEDI', str(e), None, None, None, 0)
        return 2

    try:
        profil_veri = _oku_json(Path(args.profil_dosya))
        roller, asgari = _bedava_profil(profil_veri)
        profil_hata = None
    except Hata as e:
        roller, asgari, profil_hata = {}, None, 'profil dosyasi okunamadi: %s' % e
    except ProfilHatasi as e:
        roller, asgari, profil_hata = {}, None, str(e)

    try:
        if args.api_dosya:
            canli = _canli(_oku_json(Path(args.api_dosya)))
            api_etiketi = args.api_dosya
        else:
            canli = _canli(_api_oku(args.api_url, args.timeout))
            api_etiketi = args.api_url
    except Hata as e:
        yaz('KATALOG KONTROL: OLCULMEDI — %s' % e)
        yaz('BEDAVA: OLCULMEDI — canli katalog okunamadi; PASS sayilmaz.')
        if profil_hata:
            yaz('BEDAVA: FAIL — %s' % profil_hata)
        model = _model_id(next(iter(roller.values()))) if len(roller) == 1 else None
        _kayit_yaz(args, satirlar, 'OLCULMEDI', str(e), model, None, asgari,
                   len(roller))
        return 2

    bulgular, toplam, gecerli = karsilastir(yerel, canli)
    yaz('KATALOG KONTROL — models.dev canli karsilastirma (CI kapisi)')
    yaz('katalog: %s' % args.katalog)
    yaz('profil: %s -> %s' % (args.profil_dosya, PROFIL_ADI))
    yaz('canli: %s' % api_etiketi)
    yaz('saglayici=%d · model=%d' % (len(yerel), toplam))
    yaz()
    for tur, ad, ayrinti in bulgular:
        yaz('  %-14s %s — %s' % (tur, ad, ayrinti))
    if bulgular:
        yaz()
    yaz('SONUC: %d/%d gecerli · %d bulgu' % (gecerli, toplam, len(bulgular)))

    bedava_bulgular = []
    model_id = None
    canli_model = None
    gecen_rol = 0
    if profil_hata:
        yaz()
        yaz('BEDAVA: FAIL — %s' % profil_hata)
    else:
        bedava_bulgular, model_id, canli_model, gecen_rol, rol_toplam = _bedava_denetle(
            roller, asgari, canli, yerel)
        yaz()
        yaz('BEDAVA PROFIL — %s · profiller.%s · %d rol'
            % (args.profil_dosya, PROFIL_ADI, rol_toplam))
        for rol in sorted(roller):
            yaz(_rol_satiri(rol, roller[rol], _canli_kayit(canli, _model_id(roller[rol])),
                            asgari))
        yaz()
        for tur, ad, ayrinti in bedava_bulgular:
            yaz('  BEDAVA %-16s %s — %s' % (tur, ad, ayrinti))
        if bedava_bulgular:
            yaz()
            yaz('BEDAVA: FAIL — %d bulgu · %d/%d rol gecti'
                % (len(bedava_bulgular), gecen_rol, rol_toplam))
        else:
            yaz('BEDAVA: %d/%d rol · tek kimlik openrouter/%s · cost 0/0 · '
                'reasoning/tool_call true · limit %s/%s >= %s/%s'
                % (gecen_rol, rol_toplam, model_id,
                   (canli_model.get('limit') or {}).get('context'),
                   (canli_model.get('limit') or {}).get('output'),
                   asgari['context'], asgari['output']))

    if bulgular or bedava_bulgular or profil_hata:
        if bulgular:
            yaz('HUKUM: BAYAT — allowlist models.dev ile uyusmuyor; adlar yukarida.')
        else:
            yaz('HUKUM: BAYAT — bedava profili kosullari saglanmiyor; adlar yukarida.')
        sonuc = 'FAIL'
        sebep = 'allowlist/bedava kosulu ihlali'
        rc = 1
    else:
        yaz('HUKUM: GUNCEL — tum yerel kimlikler canli katalogda.')
        sonuc = 'PASS'
        sebep = ''
        rc = 0

    if not _kayit_yaz(args, satirlar, sonuc, sebep, model_id,
                      _kanit_ozeti(canli_model), asgari, len(roller)):
        if rc == 0:
            yaz('HUKUM: KAYIT YOK — olcum PASS ama kanit yazilamadi; PASS sayilmaz.')
            rc = 2
    return rc


if __name__ == '__main__':
    sys.exit(main())
