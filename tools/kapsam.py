#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kapsam — yayimlanan ATLAS/KOD kapı kurallarinin TAM envanteri ve kapsami.

NEDEN VAR
  "5/5 kural atesledi" cumlesi, kac kuralin hic test edilmedigini soylemez.
  Bu betik her kurali tek tek listeler; mutasyon vakasi olmayan her kural icin
  ya OLCULMUS bir kapsam-disi gerekcesi ya da "BOSLUK" yazar. Gerekce uydurulmaz:
  siniflandirma betiklerin gercek bagimliliklarina dayanir (asagidaki tablo).
  Cikti docs/MUTASYON_KAPSAM.md'ye yazilir.

KULLANIM
  python3 tools/kapsam.py            # markdown'i ekrana bas
  python3 tools/kapsam.py --yaz     # docs/MUTASYON_KAPSAM.md'yi yaz
  python3 tools/kapsam.py --kontrol # dosya guncel mi (CI; farkliysa rc=1)
"""
import importlib.util
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
HEDEF = KOK / 'docs' / 'MUTASYON_KAPSAM.md'
DIZINLER = ('ATLAS_SABLONLAR/scripts', 'KOD_SABLONLAR/scripts')

KURAL = re.compile(r'^\s{0,8}([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})\b')
# OLCUM-* bir kapi kurali degil, olcum kaydinin referansidir.
YOKSAY_PREFIX = {'OLCUM'}

# Kapsam disi gerekceleri BETIKLERIN GERCEK BAGIMLILIKLARINA dayanir:
#   api_surface  : _KOSU/gate/BASELINE.json (KFAZ0 imza envanteri) yoksa CALISTIRILMADI
#   dep_audit    : `git diff --name-only HEAD` ile degisen dosyalari okur
#   olgu_lint    : SURUM.md makine blogunu HEAD/commit hashleriyle karsilastirir
#   oztest_attest: butun agacin selftest hash tabanini + ham kosu ciktisini ister
#   teslim_imza  : HMAC anahtari (LAB_IMZA_ANAHTARI veya ~/.config/lab_imza.key)
#   verify_doi   : requests ile api.crossref.org'a cikar (ag)
KAPSAM_DISI = {
    'ATLAS_SABLONLAR/scripts/verify_doi.py':
        ('ag', 'requests ile api.crossref.org sorgusu; batarya agsiz kosar'),
    'ATLAS_SABLONLAR/scripts/teslim_imza.py':
        ('gizli-anahtar', 'HMAC anahtari ister (LAB_IMZA_ANAHTARI / '
                          '~/.config/lab_imza.key); anahtar depoya konmaz'),
    'ATLAS_SABLONLAR/scripts/olgu_lint.py':
        ('tarihce', 'SURUM.md makine blogunu HEAD/commit hashleriyle karsilastirir'),
    'ATLAS_SABLONLAR/scripts/oztest_attest.py':
        ('kosu-durumu', 'butun agacin selftest hash tabanini ve ham kosu '
                        'ciktisini ister'),
    'KOD_SABLONLAR/scripts/api_surface.py':
        ('kosu-durumu', 'KFAZ0 _KOSU/gate/BASELINE.json imza envanterini ister; '
                        'envanter yoksa CALISTIRILMADI'),
    'KOD_SABLONLAR/scripts/dep_audit.py':
        ('depo-durumu', '`git diff --name-only HEAD` ile degisen dosyalari okur'),
}


def kapi_betikleri():
    for d in DIZINLER:
        for p in sorted((KOK / d).glob('*.py')):
            if not p.name.endswith('_selftest.py'):
                yield p


def envanter():
    """{betik_goreli: [kural, ...]} — yalniz basliktaki bildirimler."""
    sonuc = {}
    for p in kapi_betikleri():
        kimlikler = set()
        for satir in p.read_text(encoding='utf-8').splitlines()[:100]:
            m = KURAL.match(satir)
            if m and m.group(1).split('-')[0] not in YOKSAY_PREFIX:
                kimlikler.add(m.group(1))
        if kimlikler:
            sonuc[str(p.relative_to(KOK))] = sorted(kimlikler)
    return sonuc


def batarya():
    yol = KOK / 'tools' / 'mutasyon_bataryasi.py'
    spec = importlib.util.spec_from_file_location('mb', str(yol))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.vakalar()


def normalize(kimlik):
    for onek in ('KOD-', 'ATLAS-'):
        if kimlik.startswith(onek):
            return kimlik[len(onek):]
    return kimlik


def oz_testler():
    metin = ''
    for d in DIZINLER:
        for p in sorted((KOK / d).glob('*_selftest.py')):
            metin += p.read_text(encoding='utf-8')
    return metin


def olc():
    """[(betik, kural, vaka|None, durum, gerekce)] + ozet sayilari."""
    envan = envanter()
    testler = {}
    for kimlik, _katman, _kural, betik, *_ in batarya():
        testler.setdefault(betik, {})[normalize(kimlik)] = kimlik
    oz = oz_testler()

    satirlar = []
    test = disi = bosluk = oz_anilan = 0
    for betik, kurallar in envan.items():
        for k in kurallar:
            vaka = testler.get(betik, {}).get(k)
            if vaka:
                test += 1
                satirlar.append((betik, k, vaka, 'TEST EDILDI',
                                 'mutasyon vakasi: %s' % vaka))
            elif betik in KAPSAM_DISI:
                disi += 1
                sinif, gerekce = KAPSAM_DISI[betik]
                satirlar.append((betik, k, None, 'KAPSAM DISI',
                                 '%s: %s' % (sinif, gerekce)))
            else:
                bosluk += 1
                if k in oz:
                    oz_anilan += 1
                    gerekce = 'BOSLUK — yalniz oz-testte aniliyor, mutasyon vakasi yok'
                else:
                    gerekce = 'BOSLUK — hicbir testte gecmiyor'
                satirlar.append((betik, k, None, 'BOSLUK', gerekce))
    return satirlar, envan, (test, disi, bosluk, oz_anilan)


def sinif_tablosu(satirlar):
    siniflar = {}
    for betik, k, _v, durum, gerekce in satirlar:
        if durum != 'KAPSAM DISI':
            continue
        sinif = gerekce.split(':', 1)[0]
        siniflar.setdefault(sinif, {'gerekce': gerekce.split(': ', 1)[1],
                                    'betik': set(), 'kural': 0})
        siniflar[sinif]['betik'].add(betik.split('/')[-1])
        siniflar[sinif]['kural'] += 1
    out = ['| Sinif | Gerekce (betikte olculen bagimlilik) | Betik | Kural |',
           '|---|---|---|---|']
    for sinif in sorted(siniflar):
        v = siniflar[sinif]
        out.append('| %s | %s | %s | %d |' % (
            sinif, v['gerekce'], ', '.join(sorted(v['betik'])), v['kural']))
    return out


def markdown():
    satirlar, envan, (test, disi, bosluk, oz_anilan) = olc()
    out = ['# Mutasyon kapsami — tam kural envanteri', '',
           'Kaynak: `tools/kapsam.py` (uretilmis dosya; elle duzenlenmez).',
           'Envanter, ATLAS ve KOD kapi betiklerinin basliklarinda bildirdigi',
           'kural kimlikleridir; `*_selftest.py` ve `OLCUM-*` referanslari sayilmaz.',
           '',
           'Her kural icin tek soru sorulur: **mutasyon bataryasinda onu ateslettiren',
           'bir vaka var mi?** Yoksa iki durumdan biri yazilir: gerekcesi olculmus',
           '**KAPSAM DISI** ya da **BOSLUK**. Bosluk gizlenmez.', '',
           '## Ozet', '',
           '| Olcum | Deger |', '|---|---|',
           '| Kapi betigi | %d |' % len(envan),
           '| Bildirilen kural | %d |' % len(satirlar),
           '| Mutasyon vakasi olan (TEST EDILDI) | %d |' % test,
           '| Gerekceli kapsam disi | %d |' % disi,
           '| Bosluk (gerekce yok) | %d |' % bosluk,
           '| — bunlardan yalniz oz-testte anilan | %d |' % oz_anilan,
           '| — hicbir testte gecmeyen | %d |' % (bosluk - oz_anilan),
           '',
           '## Kapsam disi siniflari', '',
           'Gerekceler tahmin degil; her satir betigin kodundaki bagimliliga dayanir',
           '(asagida betik adiyla birlikte yazili).', '']
    out += sinif_tablosu(satirlar)
    out += ['', '## Tam envanter', '',
            '| Betik | Kural | Mutasyon vakasi | Durum | Gerekce |',
            '|---|---|---|---|---|']
    for betik, k, vaka, durum, gerekce in satirlar:
        out.append('| `%s` | %s | %s | %s | %s |' % (
            betik.split('/')[-1], k, vaka or '—', durum, gerekce))
    out.append('')
    return '\n'.join(out)


def main(argv):
    metin = markdown()
    if '--kontrol' in argv:
        if not HEDEF.is_file():
            print('KAPSAM: %s yok — `make kapsam-yaz` kosun' % HEDEF.name)
            return 1
        if HEDEF.read_text(encoding='utf-8') != metin:
            print('KAPSAM: docs/MUTASYON_KAPSAM.md guncel degil — `make kapsam-yaz`')
            return 1
        print('KAPSAM: guncel (%d satir)' % len(metin.splitlines()))
        return 0
    if '--yaz' in argv:
        HEDEF.parent.mkdir(parents=True, exist_ok=True)
        HEDEF.write_text(metin, encoding='utf-8')
        print('KAPSAM: yazildi · %s' % HEDEF.relative_to(KOK))
        return 0
    print(metin)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
