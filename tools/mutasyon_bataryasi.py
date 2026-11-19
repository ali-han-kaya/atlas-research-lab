#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mutasyon_bataryasi — yayimlanan kapilarin GERCEKTEN atesledigini olcer.

NEDEN VAR
  Bir kapi "PASS" diyorsa, o kapinin bir ihlali yakalayabildigi ayri bir olcumle
  gosterilmelidir. Aksi halde yesil, kapinin degil girdinin ozelligidir. Bu betik
  her vaka icin once TEMIZ TABAN alir, sonra ayni kopyada tek bir ihlal uretir ve
  kapinin kirmiziya dondugunu olcer. Ikisi birlikte olmadan vaka GECMEZ.

NE OLCMEZ
  Model cagirmaz, ag kullanmaz, gercek makale uretmez. Olctugu sey kapi
  betiginin kendi kararidir; kapsam disi olan sey raporda yazilidir.

KULLANIM
  python3 tools/mutasyon_bataryasi.py [--ayrintili]

CIKIS
  0  : butun vakalar atesledi (taban temiz + mutasyon kirmizi)
  1  : en az bir vaka ateslemedi / taban kirlendi / mutasyon uygulanamadi
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
AYRINTILI = '--ayrintili' in sys.argv
ATLA = shutil.ignore_patterns('.git', '__pycache__', 'node_modules', '.pytest_cache',
                              '.ruff_cache', '.DS_Store')

# Anahtar PARCALI yazilir: bu dosya depoda durur ve sir tarayicisi (H4) bitisik
# deseni yakalar. Parcali literal tarayiciyi yaniltmak icin degil, gercek bir
# anahtarin depoya sizmasini onlemek icin boyle: fikstur oldugu gorunur.
SAHTE_ANAHTAR = 'AKIA' + 'Z7Q2M4XK9PLR3TWV'

DEC_BASLIKLAR = ['Etik Kurul', 'Cikar Catismasi', 'Finansman', 'credit',
                 'Veri Erisilebilirligi', 'Yapay Zeka']


def kos(komut, cwd=None):
    r = subprocess.run([str(k) for k in komut], cwd=str(cwd or KOK),
                       capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def yaz(yol, metin):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding='utf-8')


def ekle(kok, rel, metin):
    """Mutasyon: dosyanin sonuna ekle. Hedef yoksa HATA dondurur."""
    yol = kok / rel
    if not yol.is_file():
        return 'HATA: hedef yok: %s' % rel
    with yol.open('a', encoding='utf-8') as f:
        f.write(metin)
    return None


def degistir(kok, rel, eski, yeni):
    """Mutasyon: TAM bir metin parcasini degistir (tek eslesme sarti)."""
    yol = kok / rel
    if not yol.is_file():
        return 'HATA: hedef yok: %s' % rel
    metin = yol.read_text(encoding='utf-8')
    adet = metin.count(eski)
    if adet != 1:
        return 'HATA: %s icinde desen %d kez gecti (1 bekleniyordu)' % (rel, adet)
    yol.write_text(metin.replace(eski, yeni, 1), encoding='utf-8')
    return None


def dec_govde(basliklar):
    return '# Makale\n\n' + '\n\n'.join('## %s\n\nBeyan metni.' % b for b in basliklar) + '\n'


def qr_govde(uzun_mu):
    # 40+ kelime ESIGI gercek sayimla gecilir; sayi uydurulmaz (ATLAS kapisi da
    # kelime sayar). Uzunluk calisirken olculur, yorumda iddia edilmez.
    if uzun_mu:
        alinti = ('Bu paragraf kirk kelimelik esigi asan bir alintinin nasil '
                  'gorundugunu olcmek icin yazilmistir ve gercekten uzun bir '
                  'alintidir; boylece kapi uzun alinti uclusunu denetlemek zorunda '
                  'kalir ve sayfa numarasi verilmedigi icin kirmizi yanmasi '
                  'gerekir, cunku ucuncu unsur eksiktir ve bu eksiklik sessiz '
                  'gecilmemelidir.')
        atif = '(Kaya, 2020).'
    else:
        alinti = 'Kisa bir alinti.'
        atif = '(Kaya, 2020, s. 12).'
    return ('# Makale\n\nGovde metni burada baslar.\n\n'
            '"%s" %s\n\n## Kaynakca\n\nKaya, A. (2020). Deneme.\n' % (alinti, atif))


def taban_ve_mutasyon(kok, kapi, argumanlar, mutasyon, iz, taban_rc=0):
    """(durum, ayrinti) dondurur. taban_rc: temiz kopyada beklenen cikis kodu."""
    betik = kok / kapi
    if not betik.is_file():
        return 'EKSIK', 'kapi betigi yok: %s' % kapi

    komut = [sys.executable, betik] + argumanlar(kok)

    rc0, o0 = kos(komut, cwd=kok)
    if rc0 != taban_rc:
        return 'TABAN_KIRIK', 'taban rc=%d (beklenen %d) · %s' % (
            rc0, taban_rc, o0.strip().splitlines()[-1] if o0.strip() else '')

    hata = mutasyon(kok)
    if hata:
        return 'MUTASYON_UYGULANMADI', hata

    rc1, o1 = kos(komut, cwd=kok)
    if rc1 == 0:
        return 'ATESLEMEDI', 'mutasyon sonrasi rc=0 (kapi kirmiziya donmedi)'
    if iz not in o1:
        return 'ATESLEMEDI', 'rc=%d ama beklenen iz (%s) ciktida yok' % (rc1, iz)
    return 'GECTI', 'taban rc=0 · mutasyon rc=%d · iz=%s' % (rc1, iz)


def vakalar():
    """Her vaka: (kimlik, katman, kural, kapi, argumanlar, mutasyon, iz)."""
    return [
        ('KOD-SEC-02', 'KOD', 'gercek sir kalibi P0', 'KOD_SABLONLAR/scripts/secret_scan.py',
         lambda k: ['--tum', '--dizin', str(k / 'sandbox')],
         lambda k: ekle(k, 'sandbox/notlar.md', '\nanahtar = "%s"\n' % SAHTE_ANAHTAR),
         'SEC-'),
        ('KOD-PERM-01', 'KOD', 'olu kural yok (findLast sirasi)', 'KOD_SABLONLAR/scripts/perm_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: degistir(
             k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-gate-2a.md',
             '  bash:\n    "*": allow\n    "git commit*": deny\n',
             '  bash:\n    "git commit*": deny\n    "*": allow\n'),
         'PERM-01'),
        ('ATLAS-PL-10', 'ATLAS', 'vacuous PASS muafiyeti yok', 'ATLAS_SABLONLAR/scripts/prompt_lint.py',
         lambda k: ['--dizin', str(k)],
         lambda k: ekle(k, 'ATLAS_SABLONLAR/.opencode/agent/atlas-scoper.md',
                        '\nKanit GEREKMEZ.\n'),
         'PL-10'),
        ('ATLAS-DEC-03', 'ATLAS', 'beyan basligi zorunlu', 'ATLAS_SABLONLAR/scripts/declaration_check.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'MASTER.md')],
         lambda k: yaz(k / 'sandbox' / 'MASTER.md',
                       dec_govde([b for b in DEC_BASLIKLAR if b != 'Finansman'])),
         'DEC-03'),
        ('ATLAS-QR-02', 'ATLAS', '40+ kelimelik alintida uclu', 'ATLAS_SABLONLAR/scripts/quote_ratio.py',
         lambda k: ['--dosya', str(k / 'sandbox' / 'makale.md')],
         lambda k: yaz(k / 'sandbox' / 'makale.md', qr_govde(uzun_mu=True)),
         'QR-02'),
    ]


def hazirla(kok):
    """Temiz kopya + vakalarin temiz taban fiksturleri."""
    yaz(kok / 'sandbox' / 'notlar.md', '# Notlar\n\nBu dosyada sir yok.\n')
    yaz(kok / 'sandbox' / 'MASTER.md', dec_govde(DEC_BASLIKLAR))
    yaz(kok / 'sandbox' / 'makale.md', qr_govde(uzun_mu=False))


def main():
    print('MUTASYON BATARYASI — ATLAS + KOD kapi kurallari')
    print('kaynak: %s' % KOK.name)
    print('kural: once TEMIZ TABAN (rc=0), sonra tek ihlal, sonra KIRMIZI (rc!=0 + iz).')
    print()

    gecen = 0
    satirlar = []
    for kimlik, katman, kural, kapi, argumanlar, mutasyon, iz in vakalar():
        tmp = Path(tempfile.mkdtemp(prefix='atlas_mut_'))
        try:
            hedef = tmp / 'depo'
            shutil.copytree(KOK, hedef, symlinks=True, ignore=ATLA)
            hazirla(hedef)
            durum, ayrinti = taban_ve_mutasyon(hedef, kapi, argumanlar, mutasyon, iz)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        if durum == 'GECTI':
            gecen += 1
        satirlar.append((kimlik, katman, kural, durum, ayrinti))
        print('  [%d/%d] %-13s %-6s %-34s %s' % (
            len(satirlar), len(vakalar()), kimlik, katman, durum, kural))
        print('         %s' % ayrinti)

    print()
    print('SONUC: %d/%d kural atesledi · taban temiz olmayan=%d' % (
        gecen, len(vakalar()),
        sum(1 for s in satirlar if s[3] == 'TABAN_KIRIK')))

    kirik = [s for s in satirlar if s[3] != 'GECTI']
    if kirik:
        print('HUKUM: FAIL — ateslemeyen vaka var; kapi kaniti eksik.')
        return 1
    print('HUKUM: PASS — her kural temiz tabanda sessiz, ihlalde kirmizi.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
