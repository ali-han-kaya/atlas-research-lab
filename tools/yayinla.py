#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yayinla.py — ozel laboratuvar agacindan bu depoya MEKANIK aktarim.

NEDEN VAR: yayin agaci elle kopyalanirsa iki sey sessizce bozulur —
(a) mekanizma guncellenir, depo eskir; (b) bir dosya yanlislikla makale veya
proje ciktisiyla birlikte kopyalanir. Bu arac yalniz asagidaki ACIK listedeki
yollari tasir; liste disina cikmaz ve hedefte liste disi dosya birakmaz.

Kullanim:
    python3 tools/yayinla.py --lab ~/Desktop/MTRX/AI_ARASTIRMA_LABI            # kuru kosu
    python3 tools/yayinla.py --lab ~/Desktop/MTRX/AI_ARASTIRMA_LABI --uygula

CIKIS: 0 = plan yazildi/temiz · 1 = sir bulgusu (HICBIR SEY yazilmadi) · 2 = kullanim hatasi
"""
import argparse
import hashlib
import os
import re
import shutil
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- DAHIL LISTESI (tek kaynak; yeni yol buraya yazilmadan yayimlanmaz) ------
KOKLER = ['ATLAS_SABLONLAR', 'KOD_SABLONLAR', 'ORTAK', 'RAFINE_SABLON',
          'HAKEM_HEYETI', 'DENEME', 'scripts', '.opencode']
DOSYALAR = ['AGENTS.md', 'AI_CALISMA_SISTEMI_v1.md', 'ISARETCILER.md',
            'opencode.json']
TOOLKIT_DOSYALARI = ['KOMUT_TOOLKIT_v4/000_ONCE_BUNU_YAPISTIR.md',
                     'KOMUT_TOOLKIT_v4/001_SORUN_CIKARSA_OKU.md']
TOOLKIT_KOKLER = ['KOMUT_TOOLKIT_v4/ARACLAR']
DOCS_DOSYALARI = [
    'DERSLER_v1_2026-08-30.md',
    'OLGULAR.md',
    'OLCUM-01-IZIN-GLOB.md', 'OLCUM-02-CANLI-KOSU.md',
    'OLCUM-03-DUZELTME-SONRASI.md', 'OLCUM-04-CANLI-DOGRULAMA.md',
    'OLCUM-05-ADIM1-TAZE-KURULUM-TARAMASI.md', 'OLCUM-05-CANLI-TAM-KOSU.md',
    'OLCUM-06-CANLI-TAM-KOSU.md', 'OLCUM-07-CANLI-DENGE-TAM-KOSU.md',
    'DENETIM-2026-08-31-TAM-TARAMA.md',
    'DENETIM_RAPORU_2026-08-30_v3_SIFIR_GOZLE.md',
    'MUTASYON_KOSUM.md', 'CORRIGENDUM-KIMLIK-ENVANTER-2026-09-01.md',
]

# --- HARIC -------------------------------------------------------------------
ATLA_AD = {'.DS_Store', '__pycache__', 'node_modules', '.pytest_cache',
           '.ruff_cache', '.git', '.venv', '.venv-token'}
ATLA_UZANTI = {'.pyc', '.pyo'}

# --- BU DEPONUN KENDI KATMANI (aktarimla silinmez/uzerine yazilmaz) ----------
KORUNAN = {'README.md', 'LICENSE', 'Makefile', '.gitignore', 'docs/README.md'}
KORUNAN_KOKLER = ('.github', 'tools')

SIR_KALIPLARI = [
    ('postgres-dsn', re.compile(r'postgres(?:ql)?://[^\s:/]+:[^\s@]+@')),
    ('neon', re.compile(r'npg_[A-Za-z0-9]{8,}')),
    ('openai', re.compile(r'sk-(?:proj-)?[A-Za-z0-9]{24,}')),
    ('github', re.compile(r'ghp_[A-Za-z0-9]{30,}')),
    ('aws', re.compile(r'AKIA[0-9A-Z]{16}')),
    ('slack', re.compile(r'xox[bap]-[A-Za-z0-9-]{10,}')),
    ('google', re.compile(r'AIza[0-9A-Za-z_-]{35}')),
]
FIKSTUR = ('AKIAXXX', 'AKIA1234567890')
ANAHTAR = re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----\r?\n[A-Za-z0-9+/=]{64,}')


def atilabilir(ad):
    return ad in ATLA_AD or os.path.splitext(ad)[1] in ATLA_UZANTI


def topla(lab):
    """(rel -> kaynak yol) haritasi. Eksik zorunlu yol = kullanim hatasi."""
    istenen = {}

    def ekle_dir(kok_rel):
        taban = os.path.join(lab, kok_rel)
        if not os.path.isdir(taban):
            raise SystemExit('HATA: kaynak klasor yok: %s' % taban)
        for dirpath, dizinler, dosyalar in os.walk(taban):
            dizinler[:] = sorted(d for d in dizinler if d not in ATLA_AD)
            for ad in sorted(dosyalar):
                if atilabilir(ad):
                    continue
                tam = os.path.join(dirpath, ad)
                istenen[os.path.relpath(tam, lab)] = tam

    for kok in KOKLER + TOOLKIT_KOKLER:
        ekle_dir(kok)
    for rel in DOSYALAR + TOOLKIT_DOSYALARI + ['docs/' + d for d in DOCS_DOSYALARI]:
        tam = os.path.join(lab, rel)
        if os.path.exists(tam):
            istenen[rel] = tam
    return istenen


def ozet_oku(tam):
    if os.path.islink(tam):
        return ('link', os.readlink(tam))
    try:
        with open(tam, 'rb') as f:
            return ('sha', hashlib.sha256(f.read()).hexdigest())
    except OSError:
        return ('yok', '')


def plan(istenen):
    yeni, degisen, ayni = [], [], []
    for rel, kaynak in sorted(istenen.items()):
        hedef = os.path.join(KOK, rel)
        if not os.path.exists(hedef):
            yeni.append(rel)
        elif ozet_oku(kaynak) != ozet_oku(hedef):
            degisen.append(rel)
        else:
            ayni.append(rel)
    return yeni, degisen, ayni


def fazlalik(istenen):
    """Hedefte olup planda olmayan, bu deponun kendi katmani disindaki dosyalar."""
    silinecek = []
    tabanlar = KOKLER + TOOLKIT_KOKLER + ['KOMUT_TOOLKIT_v4', 'docs']
    for taban in tabanlar:
        dizin = os.path.join(KOK, taban)
        if not os.path.isdir(dizin):
            continue
        for dirpath, dizinler, dosyalar in os.walk(dizin):
            dizinler[:] = [d for d in dizinler if d not in ATLA_AD]
            for ad in dosyalar:
                tam = os.path.join(dirpath, ad)
                rel = os.path.relpath(tam, KOK)
                if rel in istenen or rel in KORUNAN:
                    continue
                if any(rel == k or rel.startswith(k + '/') for k in KORUNAN_KOKLER):
                    continue
                silinecek.append(rel)
    return sorted(silinecek)


def sir_tara(istenen):
    bulgular = []
    for rel, tam in sorted(istenen.items()):
        if os.path.islink(tam) or os.path.getsize(tam) > 2 * 1024 * 1024:
            continue
        try:
            with open(tam, encoding='utf-8') as f:
                metin = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        for no, satir in enumerate(metin.splitlines(), 1):
            if any(f in satir for f in FIKSTUR):
                continue
            for ad, kalip in SIR_KALIPLARI:
                if kalip.search(satir):
                    bulgular.append((rel, no, ad))
        for m in ANAHTAR.finditer(metin):
            bulgular.append((rel, metin[:m.start()].count('\n') + 1, 'private-key'))
    return bulgular


def yaz(istenen, silinecek):
    for rel, kaynak in sorted(istenen.items()):
        hedef = os.path.join(KOK, rel)
        os.makedirs(os.path.dirname(hedef), exist_ok=True)
        if os.path.islink(kaynak):
            if os.path.lexists(hedef):
                os.remove(hedef)
            os.symlink(os.readlink(kaynak), hedef)
        else:
            shutil.copy2(kaynak, hedef)
    for rel in silinecek:
        os.remove(os.path.join(KOK, rel))
    return len(istenen), len(silinecek)


def main():
    ap = argparse.ArgumentParser(description='Ozel lab agacindan bu depoya aktarim.')
    ap.add_argument('--lab', default=os.environ.get('ATLAS_LAB'),
                    help='ozel laboratuvar agacinin koku (veya ATLAS_LAB)')
    ap.add_argument('--uygula', action='store_true',
                    help='plani YAZ (verilmezse yalniz gosterir)')
    ap.add_argument('--liste', type=int, default=20,
                    help='ekranda gosterilecek degisiklik sayisi (varsayilan 20)')
    a = ap.parse_args()

    if not a.lab:
        print('HATA: --lab <yol> gerekli (veya ATLAS_LAB degiskeni).', file=sys.stderr)
        return 2
    lab = os.path.abspath(os.path.expanduser(a.lab))
    if not os.path.isdir(lab):
        print('HATA: kaynak dizin yok: %s' % lab, file=sys.stderr)
        return 2

    istenen = topla(lab)
    yeni, degisen, ayni = plan(istenen)
    silinecek = fazlalik(istenen)
    bulgular = sir_tara(istenen)

    print('YAYIN PLANI · kaynak: %s' % lab)
    print('  planda=%d · yeni=%d · degisen=%d · ayni=%d · silinecek=%d'
          % (len(istenen), len(yeni), len(degisen), len(ayni), len(silinecek)))
    for baslik, liste in (('YENI', yeni), ('DEGISEN', degisen),
                          ('SILINECEK', silinecek)):
        for rel in liste[:a.liste]:
            print('    %-9s %s' % (baslik, rel))
        if len(liste) > a.liste:
            print('    %-9s ... +%d' % (baslik, len(liste) - a.liste))

    if bulgular:
        print()
        print('SIR TARAMASI: %d bulgu — HICBIR SEY YAZILMADI' % len(bulgular))
        for rel, no, ad in bulgular[:20]:
            print('    %s:%d (%s)' % (rel, no, ad))
        return 1
    print()
    print('SIR TARAMASI: temiz (0 bulgu)')

    if not a.uygula:
        print()
        print('KURU KOSU — yazmak icin: --uygula')
        return 0

    n, s = yaz(istenen, silinecek)
    print()
    print('YAZILDI: %d dosya · silinen: %d' % (n, s))
    print('Sonraki adim: make dogrula && git add -A && git commit')
    return 0


if __name__ == '__main__':
    sys.exit(main())
