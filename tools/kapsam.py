#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kapsam — mutasyon bataryasinin hangi kapi kuralini gercekten atesledigini olcer.

NEDEN VAR
  "5/5 kural atesledi" cumlesi, kac kuralin HIC test edilmedigini soylemez.
  Bu betik kapi betiklerinin kendi basliklarinda bildirdigi kural kimliklerini
  tarar, mutasyon bataryasindaki vakalarla ve oz-testlerdeki anmalarla esler;
  cikti docs/MUTASYON_KAPSAM.md'ye yazilir. Sayilar kosarken olculur, elle
  yazilmaz.

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
DIZINLER = ('ATLAS_SABLONLAR/scripts', 'KOD_SABLONLAR/scripts', 'ORTAK/scripts')

KURAL = re.compile(r'^\s{0,8}([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})\b')
# OLCUM-* bir kapi kurali degil, olcum kaydinin referansidir.
YOKSAY_PREFIX = {'OLCUM'}


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
    envan = envanter()
    testler = {}
    for kimlik, _katman, _kural, betik, *_ in batarya():
        testler.setdefault(betik, set()).add(normalize(kimlik))
    oz = oz_testler()

    satirlar = []
    toplam = 0
    mutasyon = 0
    yalniz_oz = 0
    hic = 0
    for betik, kurallar in envan.items():
        m = testler.get(betik, set())
        s_mut, s_oz, s_yok = [], [], []
        for k in kurallar:
            toplam += 1
            if k in m:
                mutasyon += 1
                s_mut.append(k)
            elif k in oz:
                yalniz_oz += 1
                s_oz.append(k)
            else:
                hic += 1
                s_yok.append(k)
        satirlar.append((betik, kurallar, s_mut, s_oz, s_yok))

    tamper = []
    for betik in envan:
        metin = (KOK / betik).read_text(encoding='utf-8')
        if 'GATE_TAMPERED' not in metin:
            continue
        # Yalniz GATE_TAMPERED'i URETEN satirlar: ayni satirda gecen kural ID'si.
        ureten = set()
        for satir in metin.splitlines():
            if 'GATE_TAMPERED' not in satir:
                continue
            for k in envan[betik]:
                if k in satir:
                    ureten.add(k)
        m = testler.get(betik, set())
        for k in sorted(ureten):
            durum = ('mutasyon' if k in m else
                     ('yalniz oz-test' if k in oz else 'HIC TEST YOK'))
            tamper.append((betik, k, durum))
    return satirlar, (toplam, mutasyon, yalniz_oz, hic), tamper


def markdown():
    satirlar, (toplam, mutasyon, yalniz_oz, hic), tamper = olc()
    out = []
    out.append('# Mutasyon kapsami — olculmus')
    out.append('')
    out.append('Kaynak: `tools/kapsam.py` (uretilmis dosya; elle duzenlenmez).')
    out.append('Envanter, kapi betiklerinin basliklarinda bildirdigi kural')
    out.append('kimlikleridir; `*_selftest.py` ve `OLCUM-*` referanslari sayilmaz.')
    out.append('')
    out.append('## Ozet')
    out.append('')
    out.append('| Olcum | Deger |')
    out.append('|---|---|')
    out.append('| Kapi betigi | %d |' % len(satirlar))
    out.append('| Bildirilen kural | %d |' % toplam)
    out.append('| Mutasyonla ateslenen | %d |' % mutasyon)
    out.append('| Yalniz oz-testte gecen | %d |' % yalniz_oz)
    out.append('| Hicbir testte gecmeyen | %d |' % hic)
    out.append('')
    out.append('**Okuma:** "mutasyonla ateslenen", bataryanin temiz taban + tek')
    out.append('ihlal + kirmizi huküm ucluyle o kurali gercekten kosturdugu')
    out.append('anlamina gelir. "Yalniz oz-testte gecen" kural, bir testte')
    out.append('anilir ama ihlalde atesledigi ayri bir mutasyonla kanitlanmamis')
    out.append('demektir; "hicbir testte gecmeyen" ise hicbir kaniti olmayan')
    out.append('kuraldir.')
    out.append('')
    out.append('## GATE_TAMPERED — kritik kural')
    out.append('')
    if tamper:
        out.append('| Betik | Kural | Durum |')
        out.append('|---|---|---|')
        for betik, k, durum in tamper:
            out.append('| `%s` | %s | %s |' % (betik.split('/')[-1], k, durum))
        out.append('')
        out.append('`GATE_TAMPERED` bir kural degil bir koddur; onu ureten')
        out.append('kurallar yukaridadir. Mutasyon bataryasinda bu betik icin')
        out.append('vaka yoktur; KOD oz-testi bu davranisi ayri fiksturlerle')
        out.append('kilitler. Fark kapatilmadikca tablo bunu gizlemez.')
    else:
        out.append('Bu depoda `GATE_TAMPERED` ureten betik bulunamadi.')
    out.append('')
    out.append('## Betik bazinda')
    out.append('')
    out.append('| Kapi betigi | Kural | Mutasyon | Yalniz oz-test | Hic test yok |')
    out.append('|---|---|---|---|---|')
    for betik, kurallar, s_mut, s_oz, s_yok in satirlar:
        out.append('| `%s` | %d | %s | %s | %s |' % (
            betik.split('/')[-1], len(kurallar),
            ', '.join(s_mut) or '—', ', '.join(s_oz) or '—', ', '.join(s_yok) or '—'))
    out.append('')
    return '\n'.join(out)


def main(argv):
    metin = markdown()
    if '--kontrol' in argv:
        if not HEDEF.is_file():
            print('KAPSAM: %s yok — `make kapsam-yaz` kosun' % HEDEF.name)
            return 1
        mevcut = HEDEF.read_text(encoding='utf-8')
        if mevcut != metin:
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
