#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""katalog_kayit_dogrula.py — bedava katalog kanit kaydini fail-closed denetle.

NEDEN VAR
  `docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl` canli models.dev olcumlerinin
  append-only kanitidir. Kayit yazan `tools/katalog_kontrol.py` satiri kendi
  commit/tree/tanim hash'leriyle uretir; ancak yazilan dosya sonradan elle
  duzenlenirse bu alanlar tek basina degismeden kalabilir. Bu betik dosyayi
  dort katmanda yeniden olcer:

    1. sema: satir basina tam bir JSON nesnesi, zorunlu alanlar, tipler ve
       bilinen sonuc/kaynak degerleri,
    2. sira: zaman damgalari ve commit atalari ileri yonlu; satirlar geri
       siralanamaz, araya sokulamaz,
    3. agac: commit cozulur, tree ve tree_sha256 yeniden hesaplanir,
    4. tanim: uc yapilandirma dosyasinin SHA-256'si o commit'ten yeniden
       hesaplanir,
    5. append-only: dosyanin Git gecmisindeki her surum oncekinin bayt
       onekidir; mevcut calisma agaci HEAD ile birebir ayni olmalidir.

  Boylece yalnizca semaya uyan bir satir yetmez; iddia ettigi olcumun
  commit/tree/tanim kaniti de tutmali ve satir gecmiste degismemis olmalidir.

KULLANIM
  python3 tools/katalog_kayit_dogrula.py
  python3 tools/katalog_kayit_dogrula.py --kayit docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl
  python3 tools/katalog_kayit_dogrula.py --kok <git-koku> --kayit <yol>

CIKIS
  0 = butun satirlar sema + sira + agac + tanim + append-only denetiminden gecti
  1 = en az bir satir/gecmis kurali ihlal edildi
  2 = kullanim veya okunamayan git/dosya hatasi
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
VARSAYILAN_KAYIT = KOK / 'docs' / 'KOD_BEDAVA_KATALOG_KAYDI.jsonl'
TANIM_DOSYALARI = (
    'tools/model_katalog.json',
    'KOD_SABLONLAR/routing.profiles.json',
    'KOD_SABLONLAR/opencode.json',
)
ZORUNLU_ALANLAR = frozenset({
    'agac_kirli', 'asgari_limit', 'canli', 'commit', 'github_run_id', 'ham',
    'kaynak', 'model', 'profil', 'roller', 'sebep', 'sonuc', 'surum',
    'tanim_sha256', 'tree', 'tree_sha256', 'zaman',
})
OPSIYONEL_ALANLAR = frozenset({'aile_politikasi'})
CANLI_ALANLARI = frozenset({
    'id', 'name', 'family', 'status', 'reasoning', 'tool_call', 'cost', 'limit',
})
AILE_ALANLARI = frozenset({'aile', 'ad_oneki', 'saglayici'})
ZAMAN_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
HASH_RE = re.compile(r'^[0-9a-f]{64}$')
COMMIT_RE = re.compile(r'^[0-9a-f]{40}$')


class Hata(Exception):
    """Dogrulama altyapisi (git/dosya) calisamadi."""


def _git(kok, *args, **kwargs):
    try:
        r = subprocess.run(
            ['git', '-C', str(kok)] + list(args),
            capture_output=True, **kwargs)
    except OSError as e:
        raise Hata('git baslatilamadi: %s' % e)
    if r.returncode != 0:
        stderr = (r.stderr or b'')
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', 'replace')
        raise Hata('git %s: %s' % (
            ' '.join(args), str(stderr).strip()[:220]))
    return r.stdout


def _git_rc(kok, *args):
    """Sifir/ bir hata kodu ayrimi gereken git sorgusu."""
    try:
        r = subprocess.run(
            ['git', '-C', str(kok)] + list(args),
            capture_output=True)
    except OSError as e:
        raise Hata('git baslatilamadi: %s' % e)
    return r.returncode


def _metin(ham):
    return ham.decode('utf-8', 'replace')


def _sayi(deger):
    return isinstance(deger, int) and not isinstance(deger, bool)


def _hash(deger):
    return isinstance(deger, str) and bool(HASH_RE.match(deger))


def _agac_dosyalari(kok, rev):
    """kanit.py ile ayni agac listesi: attestation.json haric blob'lar."""
    ham = _git(kok, 'ls-tree', '-r', '-z', '--full-tree', rev)
    sonuc = []
    for kayit in ham.split(b'\0'):
        if not kayit:
            continue
        meta, ayrac, ham_yol = kayit.partition(b'\t')
        if not ayrac:
            raise Hata('git ls-tree bicimi bozuk: %s' % _metin(kayit)[:120])
        try:
            mode, tur, obj = meta.decode('ascii').split()
            yol = ham_yol.decode('utf-8')
        except (UnicodeDecodeError, ValueError) as e:
            raise Hata('git ls-tree alani okunamadi: %s' % e)
        if yol == 'attestation.json':
            continue
        if tur != 'blob':
            raise Hata('blob olmayan agac kaydi: %s (%s)' % (yol, tur))
        icerik = _git(kok, 'cat-file', 'blob', obj)
        sonuc.append({
            'path': yol,
            'mode': mode,
            'size': len(icerik),
            'sha256': hashlib.sha256(icerik).hexdigest(),
        })
    sonuc.sort(key=lambda x: x['path'])
    return sonuc


def _agac_ozeti(dosyalar):
    h = hashlib.sha256()
    for f in dosyalar:
        h.update(f['path'].encode('utf-8'))
        h.update(b'\0')
        h.update(f['mode'].encode('ascii'))
        h.update(b'\0')
        h.update(f['sha256'].encode('ascii'))
        h.update(b'\0')
        h.update(str(f['size']).encode('ascii'))
        h.update(b'\n')
    return h.hexdigest()


def _zaman_oku(deger, yer, hatalar):
    if not isinstance(deger, str) or not ZAMAN_RE.match(deger):
        hatalar.append('%s: zaman YYYY-MM-DDTHH:MM:SSZ degil: %r'
                       % (yer, deger))
        return None
    try:
        return datetime.strptime(deger, '%Y-%m-%dT%H:%M:%SZ').replace(
            tzinfo=timezone.utc)
    except ValueError:
        hatalar.append('%s: gecersiz zaman: %r' % (yer, deger))
        return None


def _canli_denetle(deger, yer, hatalar, zorunlu):
    if deger is None:
        if zorunlu:
            hatalar.append('%s: PASS satirinda canli kaydi yok' % yer)
        return
    if not isinstance(deger, dict):
        hatalar.append('%s: canli nesne degil' % yer)
        return
    eksik = sorted(CANLI_ALANLARI - set(deger))
    fazla = sorted(set(deger) - CANLI_ALANLARI)
    if eksik:
        hatalar.append('%s: canli alanlari eksik: %s'
                       % (yer, ', '.join(eksik)))
    if fazla:
        hatalar.append('%s: canli bilinmeyen alan: %s'
                       % (yer, ', '.join(fazla)))
    for alan in ('id', 'name', 'family'):
        if not isinstance(deger.get(alan), str) or not deger[alan].strip():
            hatalar.append('%s: canli.%s metin degil/bos' % (yer, alan))
    if deger.get('status') is not None and not isinstance(
            deger.get('status'), str):
        hatalar.append('%s: canli.status metin veya null degil' % yer)
    for alan in ('reasoning', 'tool_call'):
        if not isinstance(deger.get(alan), bool):
            hatalar.append('%s: canli.%s boolean degil' % (yer, alan))
    maliyet = deger.get('cost')
    if not isinstance(maliyet, dict) or not maliyet:
        hatalar.append('%s: canli.cost nesnesi yok/bos' % yer)
    else:
        for alan, fiyat in maliyet.items():
            if not isinstance(alan, str) or not _sayi(fiyat) or fiyat < 0:
                hatalar.append('%s: canli.cost.%s negatif olmayan sayi degil'
                               % (yer, alan))
    limit = deger.get('limit')
    if not isinstance(limit, dict) or set(limit) != {'context', 'output'}:
        hatalar.append('%s: canli.limit context/output alanlarini tasimali'
                       % yer)
    else:
        for alan in ('context', 'output'):
            if not _sayi(limit[alan]) or limit[alan] <= 0:
                hatalar.append('%s: canli.limit.%s pozitif tamsayi degil'
                               % (yer, alan))


def _tanim_denetle(deger, yer, hatalar):
    if not isinstance(deger, dict):
        hatalar.append('%s: tanim_sha256 nesne degil' % yer)
        return
    eksik = [p for p in TANIM_DOSYALARI if p not in deger]
    fazla = sorted(set(deger) - set(TANIM_DOSYALARI))
    if eksik:
        hatalar.append('%s: tanim_sha256 eksik: %s'
                       % (yer, ', '.join(eksik)))
    if fazla:
        hatalar.append('%s: tanim_sha256 bilinmeyen yol: %s'
                       % (yer, ', '.join(fazla)))
    for yol in TANIM_DOSYALARI:
        if yol in deger and not _hash(deger[yol]):
            hatalar.append('%s: tanim_sha256.%s 64 hex degil'
                           % (yer, yol))


def _satir_semasi(satir, yer, hatalar):
    if not isinstance(satir, dict):
        hatalar.append('%s: satir JSON nesnesi degil' % yer)
        return None
    eksik = sorted(ZORUNLU_ALANLAR - set(satir))
    fazla = sorted(set(satir) - ZORUNLU_ALANLAR - OPSIYONEL_ALANLAR)
    if eksik:
        hatalar.append('%s: zorunlu alanlar eksik: %s'
                       % (yer, ', '.join(eksik)))
    if fazla:
        hatalar.append('%s: bilinmeyen alan: %s'
                       % (yer, ', '.join(fazla)))
    if 'surum' not in satir:
        hatalar.append('%s: surum yok' % yer)
    else:
        if not _sayi(satir['surum']) or satir['surum'] not in (1, 2):
            hatalar.append('%s: surum 1 veya 2 olmali' % yer)
        if satir.get('surum') == 2 and 'aile_politikasi' not in satir:
            hatalar.append('%s: surum=2 icin aile_politikasi zorunlu' % yer)
    zaman = _zaman_oku(satir.get('zaman'), yer, hatalar)
    if satir.get('kaynak') not in ('ci', 'yerel'):
        hatalar.append('%s: kaynak ci/yerel degil: %r'
                       % (yer, satir.get('kaynak')))
    run_id = satir.get('github_run_id')
    if run_id is not None and not (
            isinstance(run_id, str) and run_id.isdigit()):
        hatalar.append('%s: github_run_id null veya rakam dizisi degil' % yer)
    if satir.get('profil') != 'bedava':
        hatalar.append('%s: profil bedava degil' % yer)
    if not _sayi(satir.get('roller')) or not 0 <= satir['roller'] <= 100:
        hatalar.append('%s: roller 0..100 tamsayi degil' % yer)
    if satir.get('sonuc') not in ('PASS', 'FAIL', 'OLCULMEDI'):
        hatalar.append('%s: sonuc PASS/FAIL/OLCULMEDI degil' % yer)
    if not isinstance(satir.get('sebep'), str):
        hatalar.append('%s: sebep metin degil' % yer)
    if satir.get('agac_kirli') is not False:
        hatalar.append('%s: agac_kirli false olmali' % yer)
    ham = satir.get('ham')
    if not isinstance(ham, list) or not ham or not all(
            isinstance(x, str) for x in ham):
        hatalar.append('%s: ham dolu metin listesi degil' % yer)
    model = satir.get('model')
    if model is not None and not (isinstance(model, str) and model.strip()):
        hatalar.append('%s: model null veya bos metin degil' % yer)
    if satir.get('sonuc') == 'PASS':
        if model is None:
            hatalar.append('%s: PASS satirinda model yok' % yer)
        if satir.get('sebep') != '':
            hatalar.append('%s: PASS satirinda sebep bos degil' % yer)
        if satir.get('roller') != 10:
            hatalar.append('%s: PASS satirinda roller 10 degil' % yer)
    elif isinstance(satir.get('sebep'), str) and not satir['sebep'].strip():
        hatalar.append('%s: PASS olmayan satirda sebep bos' % yer)

    asgari = satir.get('asgari_limit')
    if satir.get('sonuc') == 'PASS' and not isinstance(asgari, dict):
        hatalar.append('%s: PASS satirinda asgari_limit yok' % yer)
    elif asgari is not None:
        if not isinstance(asgari, dict) or set(asgari) != {'context', 'output'}:
            hatalar.append('%s: asgari_limit context/output alanlarini tasimali'
                           % yer)
        else:
            for alan in ('context', 'output'):
                if not _sayi(asgari[alan]) or asgari[alan] <= 0:
                    hatalar.append('%s: asgari_limit.%s pozitif tamsayi degil'
                                   % (yer, alan))

    _canli_denetle(satir.get('canli'), yer, hatalar,
                   satir.get('sonuc') == 'PASS')
    _tanim_denetle(satir.get('tanim_sha256'), yer, hatalar)

    if 'aile_politikasi' in satir:
        aile = satir['aile_politikasi']
        if not isinstance(aile, dict) or set(aile) != AILE_ALANLARI:
            hatalar.append('%s: aile_politikasi aile/ad_oneki/saglayici '
                           'alanlarini tasimali' % yer)
        else:
            for alan in AILE_ALANLARI:
                if not isinstance(aile[alan], str) or not aile[alan].strip():
                    hatalar.append('%s: aile_politikasi.%s bos/metin degil'
                                   % (yer, alan))
    return zaman


def _commit_agac_denetle(satir, yer, kok, hatalar):
    commit = satir.get('commit')
    tree = satir.get('tree')
    tree_sha = satir.get('tree_sha256')
    if not isinstance(commit, str) or not COMMIT_RE.match(commit):
        hatalar.append('%s: commit 40 hex degil' % yer)
        return None
    if not isinstance(tree, str) or not COMMIT_RE.match(tree):
        hatalar.append('%s: tree 40 hex degil' % yer)
        return None
    if not _hash(tree_sha):
        hatalar.append('%s: tree_sha256 64 hex degil' % yer)
        return None
    if _git_rc(kok, 'cat-file', '-e', commit + '^{commit}') != 0:
        hatalar.append('%s: commit git gecmisinde yok: %s' % (yer, commit))
        return None
    gercek_tree = _metin(_git(kok, 'rev-parse', commit + '^{tree}')).strip()
    if gercek_tree != tree:
        hatalar.append('%s: tree commit ile uyusmuyor: kayit=%s gercek=%s'
                       % (yer, tree, gercek_tree))
    try:
        gercek_sha = _agac_ozeti(_agac_dosyalari(kok, commit))
    except Hata as e:
        hatalar.append('%s: agac ozeti hesaplanamadi: %s' % (yer, e))
        return commit
    if gercek_sha != tree_sha:
        hatalar.append('%s: tree_sha256 yeniden hesapla uyusmuyor: '
                       'kayit=%s gercek=%s' % (yer, tree_sha, gercek_sha))
    return commit


def _tanim_hash_denetle(satir, yer, kok, hatalar):
    commit = satir.get('commit')
    tanim = satir.get('tanim_sha256')
    if not isinstance(commit, str) or not isinstance(tanim, dict):
        return
    for yol in TANIM_DOSYALARI:
        beklenen = tanim.get(yol)
        if not _hash(beklenen):
            continue
        try:
            icerik = _git(kok, 'show', '%s:%s' % (commit, yol))
        except Hata as e:
            hatalar.append('%s: tanim dosyasi committe okunamadi (%s): %s'
                           % (yer, yol, e))
            continue
        gercek = hashlib.sha256(icerik).hexdigest()
        if gercek != beklenen:
            hatalar.append('%s: tanim_sha256.%s uyusmuyor: kayit=%s gercek=%s'
                           % (yer, yol, beklenen, gercek))


def _sira_denetle(satirlar, zamanlar, commitler, kok, hatalar):
    for i in range(1, len(satirlar)):
        onceki = zamanlar[i - 1]
        simdiki = zamanlar[i]
        if onceki is not None and simdiki is not None and simdiki < onceki:
            hatalar.append('satir %d: zaman sirasi geriye gidiyor (%s -> %s)'
                           % (i + 1, onceki.isoformat(), simdiki.isoformat()))
        a = commitler[i - 1]
        b = commitler[i]
        if not a or not b or a == b:
            continue
        rc = _git_rc(kok, 'merge-base', '--is-ancestor', a, b)
        if rc != 0:
            hatalar.append('satir %d: commit sirasi ileri degil (%s -> %s)'
                           % (i + 1, a[:12], b[:12]))


def _gecmis_append_only(kok, kayit_yolu, hatalar):
    rel = kayit_yolu.resolve().relative_to(kok.resolve()).as_posix()
    try:
        mevcut = kayit_yolu.read_bytes()
    except OSError as e:
        raise Hata('kayit okunamadi: %s' % e)
    try:
        head = _git(kok, 'show', 'HEAD:%s' % rel)
    except Hata as e:
        raise Hata('kayit HEAD agacinda yok: %s' % e)
    if mevcut != head:
        hatalar.append('calisma agaci HEAD ile ayni degil; once kaydi commit '
                       'edin (elle duzenlenmis satir kanit sayilmaz)')
    ham = _metin(_git(kok, 'log', '--follow', '--format=%H', '--', rel))
    commitler = [x.strip() for x in ham.splitlines() if x.strip()]
    if not commitler:
        hatalar.append('kayit dosyasinin git gecmisi yok')
        return
    onceki = None
    for commit in reversed(commitler):
        try:
            icerik = _git(kok, 'show', '%s:%s' % (commit, rel))
        except Hata as e:
            hatalar.append('gecmis surumu okunamadi (%s): %s'
                           % (commit[:12], e))
            continue
        if onceki is not None and not icerik.startswith(onceki):
            hatalar.append('append-only ihlali: %s surumu onceki surumun '
                           'bayt oneki degil' % commit[:12])
        onceki = icerik


def dogrula(kok, kayit_yolu):
    """(ok, hatalar) dondur; hatalar kullaniciya gosterilebilir metinlerdir."""
    kok = Path(kok)
    kayit_yolu = Path(kayit_yolu)
    hatalar = []
    try:
        ham = kayit_yolu.read_bytes()
    except OSError as e:
        return False, ['kayit okunamadi: %s' % e]
    if not ham:
        return False, ['kayit bos']
    if not ham.endswith(b'\n'):
        hatalar.append('dosya sonunda yeni satir yok')
    satirlar = []
    for i, satir in enumerate(ham.decode('utf-8').splitlines(), 1):
        if not satir.strip():
            hatalar.append('satir %d: bos satir' % i)
            continue
        try:
            satirlar.append(json.loads(satir))
        except ValueError as e:
            hatalar.append('satir %d: gecersiz JSON: %s' % (i, e))
            satirlar.append(None)
    zamanlar = []
    commitler = []
    for i, satir in enumerate(satirlar, 1):
        yer = 'satir %d' % i
        if satir is None:
            zamanlar.append(None)
            commitler.append(None)
            continue
        zamanlar.append(_satir_semasi(satir, yer, hatalar))
        commitler.append(_commit_agac_denetle(satir, yer, kok, hatalar))
        _tanim_hash_denetle(satir, yer, kok, hatalar)
    if all(x is not None for x in satirlar):
        _sira_denetle(satirlar, zamanlar, commitler, kok, hatalar)
    _gecmis_append_only(kok, kayit_yolu, hatalar)
    return not hatalar, hatalar


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='KOD bedava katalog kaydini sema, sira, git agaci ve '
                    'append-only gecmis acisindan dogrular.')
    ap.add_argument('--kayit', default=str(VARSAYILAN_KAYIT),
                    help='JSONL kayit yolu (varsayilan: docs/...)')
    ap.add_argument('--kok', default=str(KOK),
                    help='git kok dizini (varsayilan: depo koku)')
    args = ap.parse_args(argv)
    try:
        ok, hatalar = dogrula(args.kok, Path(args.kayit))
    except Hata as e:
        print('KATALOG KAYIT DOGRULA: HATA — %s' % e)
        return 2
    except (OSError, UnicodeError, ValueError) as e:
        print('KATALOG KAYIT DOGRULA: HATA — %s' % e)
        return 2
    if not ok:
        print('KATALOG KAYIT DOGRULA: FAIL — %d hata' % len(hatalar))
        for hata in hatalar:
            print('  %s' % hata)
        return 1
    print('KATALOG KAYIT DOGRULA: PASS — sema+sira+agac+tanim+append-only')
    return 0


if __name__ == '__main__':
    sys.exit(main())
