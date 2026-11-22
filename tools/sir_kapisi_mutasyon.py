#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sir_kapisi_mutasyon.py — dort sır kapısı kenarının mutasyon kanıtı.

NEDEN VAR
  Bir düzeltmenin gerçekten bir hatayı kapattığını göstermek için düzeltme
  geçici bir kopyada geri alınır. İlgili selftest vakası FAIL vermeli, düzeltme
  geri konunca aynı vaka PASS vermelidir. Bu betik o ölçümü yapar, sonucu
  `tools/sir_kapisi_mutasyon_kaniti.json` içine yazar ve DEVIR'deki insan-okur
  bölümü aynı kayıttan üretir.

  Kayıt süs değildir: `--kontrol` her koşuda dört mutasyonu yeniden uygular,
  baseline 17/17 ile her vakanın 16/17 FAIL çıktısını birebir arar, kaynak/test
  SHA-256'larını ve sürümü denetler. CI'da `make sir-mutasyon` ile koşar.

HERMETİK ORTAM
  Geçici HOME ve `GIT_CONFIG_GLOBAL` kullanılır; global config'te
  `user.useConfigOnly=true` vardır. Böylece Git, kullanıcı/makine adından
  otomatik kimlik üretemez. `_kimlik(depo)` çağrısı kaldırılan shallow clone
  vakası CI'daki gibi `Author identity unknown` ile FAIL verir; çağrı varken
  PASS verir.

KULLANIM
  python3 tools/sir_kapisi_mutasyon.py --kontrol   # kaydı yeniden ölç ve doğrula
  python3 tools/sir_kapisi_mutasyon.py --yaz       # kaydı ve DEVIR bölümünü yenile

CIKIS: 0 = dört vaka FAIL->PASS ve kayıt güncel · 1 = kanıt/kayıt uyuşmuyor
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KANIT = KOK / 'tools' / 'sir_kapisi_mutasyon_kaniti.json'
DEVIR = KOK / 'docs' / 'DEVIR-2026-11-22-1923.md'
SURUM = KOK / 'SURUM.md'
KAPI = 'tools/sir_kapisi.py'
SELFTEST = 'tools/sir_kapisi_selftest.py'
SEMA = 'ATLAS-SIR-MUTASYON/v1'
BASLANGIC = '<!-- SIR_MUTASYON_KANITI:BASLA -->'
BITIS = '<!-- SIR_MUTASYON_KANITI:BITISI -->'
BEKLENEN_TEST = 17
BEKLENEN_BASARISIZ = 16
BASLIK = 'SIR KAPISI OZ-TEST:'

# Her vaka: (id, kenar, düzeltme, test adı, mutasyon açıklaması, dosya, eski, yeni)
# `eski` ve `yeni` gerçek kaynak metnidir; biri dosyada tam olarak bir kez
# bulunmazsa betik fail-closed durur. Test adı da selftest kaynağında aranır.
VAKALAR = [
    {
        'id': 'H5-MUT-01',
        'kenar': 'merge',
        'duzeltme': 'git show --first-parent',
        'test': 'merge commit canliyi yakalar',
        'mutasyon': "git show komutundan --first-parent kaldirildi",
        'dosya': KAPI,
        'eski': "['git', 'show', '--first-parent', '--format='",
        'yeni': "['git', 'show', '--format='",
    },
    {
        'id': 'H5-MUT-02',
        'kenar': 'rename',
        'duzeltme': 'staged --diff-filter=ACMR -M',
        'test': 'rename staged canliyi yakalar',
        'mutasyon': "staged filtresi ACMR -M yerine ACM yapildi",
        'dosya': KAPI,
        'eski': "'--diff-filter=ACMR', '-M'",
        'yeni': "'--diff-filter=ACM'",
    },
    {
        'id': 'H5-MUT-03',
        'kenar': '++ icerik satiri',
        'duzeltme': "+++ yalniz hunk basligi sayilir",
        'test': '++ icerik satiri canliyi yakalar',
        'mutasyon': "+++ ile baslayan eklenmis icerik satiri atlandi",
        'dosya': KAPI,
        'eski': "            if not satir.startswith('+'):\n                continue\n",
        'yeni': ("            if not satir.startswith('+') or "
                 "satir.startswith('+++'):\n                continue\n"),
    },
    {
        'id': 'H5-MUT-04',
        'kenar': 'shallow clone / hermetik git kimligi',
        'duzeltme': 'klonda _kimlik(depo)',
        'test': 'shallow clone yeni siri yakalar',
        'mutasyon': "klonun _kimlik(depo) cagrisi kaldirildi",
        'dosya': SELFTEST,
        'eski': "        _kimlik(depo)\n        _yaz(depo / 'new.md', CANLI + '\\n')",
        'yeni': "        _yaz(depo / 'new.md', CANLI + '\\n')",
    },
]


def oku(yol):
    return yol.read_text(encoding='utf-8')


def yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding='utf-8')


def sha256(yol):
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(['git', '-C', str(KOK)] + list(args),
                          capture_output=True, text=True)


def git_metin(*args):
    r = git(*args)
    if r.returncode != 0:
        raise RuntimeError('git %s: %s' % (' '.join(args),
                                          (r.stderr or r.stdout).strip()[:200]))
    return r.stdout.strip()


def surum_oku():
    m = re.search(r'^Sürüm:\s*(v\d+\.\d+\.\d+)', oku(SURUM), re.MULTILINE)
    if not m:
        raise RuntimeError('SURUM.md icinde sürüm satiri bulunamadi')
    return m.group(1)


def temiz_kaynak():
    """Test edilen iki dosya commit'li mi? Değilse kayıt yanlış commit'e bağlanır."""
    r = git('status', '--porcelain', '--', KAPI, SELFTEST)
    if r.returncode != 0:
        raise RuntimeError('git status: %s' % (r.stderr or r.stdout).strip()[:200])
    if r.stdout.strip():
        raise RuntimeError('kaynak/test temiz degil; once commit et: %s'
                          % r.stdout.strip())


def _satir(cikti, ad):
    """Belirli test adını taşıyan PASS/FAIL satırını döndürür."""
    for satir in cikti.splitlines():
        if ad in satir and re.search(r'\s(PASS|FAIL)\s', satir):
            return satir.strip()
    return ''


def _ozet(cikti):
    for satir in cikti.splitlines():
        if satir.strip().startswith(BASLIK):
            return satir.strip()
    return ''


def _test_sayisi(satir):
    m = re.search(r'(\d+/\d+)', satir)
    return m.group(1) if m else ''


def _satirlari_ayikla(cikti):
    satirlar = []
    for satir in cikti.splitlines():
        if re.search(r'^\s{2}.+\s+(PASS|FAIL)\s', satir):
            satirlar.append(satir.strip())
    return satirlar


def _kopya(tmp):
    """Yalniz gerekli dosyalari kopyalar; gerçek agaca dokunmaz."""
    (tmp / 'tools').mkdir(parents=True)
    (tmp / '.githooks').mkdir(parents=True)
    (tmp / 'home').mkdir()
    shutil.copy2(KOK / KAPI, tmp / KAPI)
    shutil.copy2(KOK / SELFTEST, tmp / SELFTEST)
    for ad in ('pre-commit', 'pre-push'):
        shutil.copy2(KOK / '.githooks' / ad, tmp / '.githooks' / ad)
    cfg = tmp / 'home' / '.gitconfig'
    yaz(cfg, '[user]\n\tuseConfigOnly = true\n')
    return dict(os.environ,
                HOME=str(tmp / 'home'),
                GIT_CONFIG_NOSYSTEM='1',
                GIT_CONFIG_GLOBAL=str(cfg))


def _kos(tmp, env):
    r = subprocess.run([sys.executable, str(tmp / SELFTEST)],
                       cwd=str(tmp), env=env, capture_output=True,
                       text=True, timeout=180)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def _mutasyon_uygula(tmp, vaka):
    yol = tmp / vaka['dosya']
    metin = oku(yol)
    adet = metin.count(vaka['eski'])
    if adet != 1:
        raise RuntimeError('%s: mutasyon deseni %d kez gecti (1 bekleniyordu)'
                           % (vaka['dosya'], adet))
    yaz(yol, metin.replace(vaka['eski'], vaka['yeni'], 1))


def _tek_kosu(mutasyon=None):
    tmp = Path(tempfile.mkdtemp(prefix='sir_mut_kanit_'))
    try:
        env = _kopya(tmp)
        if mutasyon:
            _mutasyon_uygula(tmp, mutasyon)
        return _kos(tmp, env)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def olc():
    temiz_kaynak()
    for vaka in VAKALAR:
        if vaka['test'] not in oku(KOK / SELFTEST):
            raise RuntimeError('test adi selftest kaynaginda yok: %s'
                               % vaka['test'])

    rc0, cikti0 = _tek_kosu()
    ozet0 = _ozet(cikti0)
    if rc0 != 0 or _test_sayisi(ozet0) != '%d/%d' % (BEKLENEN_TEST, BEKLENEN_TEST):
        raise RuntimeError('baseline FAIL: rc=%d · %s' % (rc0, ozet0 or cikti0[-400:]))
    satirlar0 = _satirlari_ayikla(cikti0)
    if len(satirlar0) != BEKLENEN_TEST:
        raise RuntimeError('baseline test satiri %d (beklenen %d)'
                           % (len(satirlar0), BEKLENEN_TEST))

    vakalar = []
    for vaka in VAKALAR:
        pass_satiri = _satir(cikti0, vaka['test'])
        if not pass_satiri or ' PASS ' not in pass_satiri:
            raise RuntimeError('%s: baseline PASS satiri yok' % vaka['id'])
        rc1, cikti1 = _tek_kosu(vaka)
        ozet1 = _ozet(cikti1)
        fail_satiri = _satir(cikti1, vaka['test'])
        satirlar1 = _satirlari_ayikla(cikti1)
        fail_sayisi = sum(1 for s in satirlar1 if ' FAIL ' in s)
        if (rc1 != 1 or _test_sayisi(ozet1) != '%d/%d' % (BEKLENEN_BASARISIZ, BEKLENEN_TEST)
                or not fail_satiri or ' FAIL ' not in fail_satiri
                or fail_sayisi != 1):
            raise RuntimeError(
                '%s: mutasyon beklenen FAIL vermedi: rc=%d · fail=%s · %s'
                % (vaka['id'], rc1, fail_satiri or '-', ozet1 or cikti1[-400:]))
        vakalar.append({
            'id': vaka['id'],
            'kenar': vaka['kenar'],
            'duzeltme': vaka['duzeltme'],
            'test': vaka['test'],
            'mutasyon': vaka['mutasyon'],
            'fail_rc': rc1,
            'fail_test_sayisi': _test_sayisi(ozet1),
            'fail_satiri': fail_satiri,
            'pass_rc': rc0,
            'pass_test_sayisi': _test_sayisi(ozet0),
            'pass_satiri': pass_satiri,
        })

    return {
        'schema': SEMA,
        'surum': surum_oku(),
        'kod_commit': git_metin('rev-parse', 'HEAD'),
        'kaynak': KAPI,
        'kaynak_sha256': sha256(KOK / KAPI),
        'selftest': SELFTEST,
        'selftest_sha256': sha256(KOK / SELFTEST),
        'hermetik': {
            'HOME': 'gecici',
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': 'gecici; [user] useConfigOnly=true',
        },
        'komut': 'python3 tools/sir_kapisi_mutasyon.py --kontrol',
        'temel': {
            'komut': 'python3 tools/sir_kapisi_selftest.py',
            'rc': rc0,
            'test_sayisi': _test_sayisi(ozet0),
            'satir': ozet0,
        },
        'vakalar': vakalar,
    }


def _normalize(satir):
    """Geçici git commit hash'i kayıtla karşılaştırmada değişkenlik yaratmasın."""
    return re.sub(r'\b[0-9a-f]{40}\b', '<sha>', satir)


def _karsilastir(kayitli, yeni):
    alanlar = ('surum', 'kaynak', 'kaynak_sha256', 'selftest', 'selftest_sha256',
               'temel')
    for alan in alanlar:
        if kayitli.get(alan) != yeni.get(alan):
            raise RuntimeError('kayit alani farkli: %s' % alan)
    eski = {v['id']: v for v in kayitli.get('vakalar', [])}
    yeni_v = {v['id']: v for v in yeni.get('vakalar', [])}
    if set(eski) != set(yeni_v):
        raise RuntimeError('vaka kimlikleri farkli')
    for vid in sorted(yeni_v):
        for alan in ('kenar', 'duzeltme', 'test', 'mutasyon',
                     'fail_rc', 'fail_test_sayisi', 'pass_rc', 'pass_test_sayisi'):
            if eski[vid].get(alan) != yeni_v[vid].get(alan):
                raise RuntimeError('%s: %s farkli' % (vid, alan))
        if _normalize(eski[vid].get('fail_satiri', '')) != _normalize(
                yeni_v[vid].get('fail_satiri', '')):
            raise RuntimeError('%s: fail_satiri farkli' % vid)
        if eski[vid].get('pass_satiri') != yeni_v[vid].get('pass_satiri'):
            raise RuntimeError('%s: pass_satiri farkli' % vid)
    if kayitli.get('kod_commit') != git_metin('rev-parse', 'HEAD'):
        # Kayit commit'i, kaydin kendisini ekleyen commit'in ebeveynidir.
        if subprocess.run(['git', '-C', str(KOK), 'merge-base', '--is-ancestor',
                           str(kayitli.get('kod_commit')), 'HEAD']).returncode != 0:
            raise RuntimeError('kayitli kod_commit HEAD\'in atasi degil')


def _hucre(metin):
    return str(metin).replace('|', '\\|')


def blok(kayit):
    satirlar = [
        BASLANGIC,
        '## Kalıcı mutasyon kanıtı — %s' % kayit['surum'],
        '',
        'Bu bölüm **elle yazılmaz**. Üreten ve doğrulayan: `%s`. '
        'Makine kaydı: `tools/sir_kapisi_mutasyon_kaniti.json`. '
        'CI adımı: `make sir-mutasyon`.' % kayit['komut'],
        '',
        'Kod commit: `%s` · Kaynak SHA-256: `%s` · Selftest SHA-256: `%s`'
        % (kayit['kod_commit'], kayit['kaynak_sha256'][:16],
           kayit['selftest_sha256'][:16]),
        'Hermetik ortam: `HOME` geçici · `GIT_CONFIG_NOSYSTEM=1` · '
        '`GIT_CONFIG_GLOBAL` geçici · `[user] useConfigOnly=true`.',
        '',
        'Temel: `%s` → `rc=%d` · `%s`'
        % (kayit['temel']['komut'], kayit['temel']['rc'],
           kayit['temel']['satir']),
        '',
        '| # | Kenar | Düzeltme | Test | Mutasyon | FAIL (düzeltme geri alınınca) | PASS (düzeltme varken) |',
        '|---|---|---|---|---|---|---|',
    ]
    for v in kayit['vakalar']:
        satirlar.append(
            '| `%s` | %s | %s | `%s` | %s | `rc=%d · %s`<br>`%s` | `rc=%d · %s`<br>`%s` |'
            % (_hucre(v['id']), _hucre(v['kenar']), _hucre(v['duzeltme']),
               _hucre(v['test']), _hucre(v['mutasyon']),
               v['fail_rc'], _hucre(v['fail_test_sayisi']),
               _hucre(v['fail_satiri']), v['pass_rc'],
               _hucre(v['pass_test_sayisi']), _hucre(v['pass_satiri'])))
    satirlar += ['', BITIS]
    return '\n'.join(satirlar)


def devir_yaz(kayit):
    metin = oku(DEVIR)
    yeni = blok(kayit)
    if BASLANGIC in metin:
        if metin.count(BASLANGIC) != 1 or metin.count(BITIS) != 1:
            raise RuntimeError('DEVIR mutasyon kaniti isaretleri tekil degil')
        bas = metin.index(BASLANGIC)
        bit = metin.index(BITIS, bas) + len(BITIS)
        metin = metin[:bas] + yeni + metin[bit:]
    else:
        metin = metin.rstrip() + '\n\n' + yeni + '\n'
    yaz(DEVIR, metin)


def devir_kontrol(kayit):
    metin = oku(DEVIR)
    if metin.count(BASLANGIC) != 1 or metin.count(BITIS) != 1:
        raise RuntimeError('DEVIR mutasyon kaniti blogu tekil degil')
    bas = metin.index(BASLANGIC)
    bit = metin.index(BITIS, bas) + len(BITIS)
    if metin[bas:bit] != blok(kayit):
        raise RuntimeError('DEVIR mutasyon kaniti blogu kayittan farkli')


def main(argv=None):
    ap = argparse.ArgumentParser(description='Sir kapisi mutasyon kaniti')
    grup = ap.add_mutually_exclusive_group()
    grup.add_argument('--yaz', action='store_true', help='kaniti ve DEVIR blogunu yenile')
    grup.add_argument('--kontrol', action='store_true', help='kaydi yeniden olc (varsayilan)')
    args = ap.parse_args(argv)
    try:
        if args.yaz:
            kayit = olc()
            yaz(KANIT, json.dumps(kayit, ensure_ascii=False, indent=2) + '\n')
            devir_yaz(kayit)
            print('SIR MUTASYON: YAZILDI %s' % KANIT.relative_to(KOK))
            print('SIR MUTASYON: YAZILDI %s' % DEVIR.relative_to(KOK))
        else:
            if not KANIT.is_file():
                raise RuntimeError('%s yok; once --yaz' % KANIT.relative_to(KOK))
            kayitli = json.loads(oku(KANIT))
            if kayitli.get('schema') != SEMA:
                raise RuntimeError('kanit semasi gecersiz: %s' % kayitli.get('schema'))
            yeni = olc()
            _karsilastir(kayitli, yeni)
            devir_kontrol(kayitli)
            print('SIR MUTASYON: PASS — %d/%d vaka FAIL->PASS · kayit %s · surum %s'
                  % (len(kayitli['vakalar']), len(VAKALAR),
                     kayitli['kod_commit'][:8], kayitli['surum']))
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print('FAIL SIR-MUTASYON: %s' % exc)
        return 1


if __name__ == '__main__':
    sys.exit(main())
