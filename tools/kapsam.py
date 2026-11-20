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
# Dosyanin herhangi bir yerindeki bolum basligi: `# --- FRZ-08 ...`.
# Bu, ust KURALLAR listesine yazilmamis ama kodda hukum ureten kurali yakalar.
BOLUM = re.compile(r'^\s*#+\s*-{2,}\s*([A-Z]{2,8}(?:-[A-Z0-9]{1,8}){0,2}-\d{2,3})\b')
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
    # OLCULDU (19.11.2026): SEC-04 baslikta bildirilir ama secret_scan'in
    # hicbir dalinda bu kimlikle bulgu BASILMAZ; atlanan dosyalar yalniz sayilir.
    # Kural kimligi olu oldugu icin mutasyonla ateslenemez; gercek bulgu uretmez.
    'KOD_SABLONLAR/scripts/secret_scan.py':
        ('olu-kimlik', 'SEC-04 yalniz baslikta bildirilir; hicbir kod dali bu '
                       'kimligi basmiyor (atlanan dosyalar yalniz sayilir)'),
}


# Risk sirasi — 19.11.2026'daki 51 mutation-kapsamsiz kuralin tamami.
# Siralama ilkesi: once sahte yesil/tamper (P0), sonra tedarik/teslim/yuzey,
# sonra test envanteri/olcum/provenance; bilgi seviyesindeki olu kimlik sonda.
# Liste sabittir: vakalar eklense de siralama degismez, durum sutunu guncellenir.
RISK_GRUPLARI = {
    'KANIT': 'Kanit/yesil butunlugu — P0',
    'KAPSAM': 'Kapsam/degisiklik butunlugu — P0',
    'TEDARIK': 'Tedarik, teslim ve disa acik yuzey — P0/P1',
    'ENVANTER': 'Test envanteri, olcum ve provenance — P0/P1',
    'BILGI': 'Bilgi seviyesi / olu kimlik — P1',
}
RISK_SIRASI = [
    ('TST-08', 'KANIT'), ('RECK-06', 'KAPSAM'), ('DEP-05', 'TEDARIK'),
    ('FRZ-08', 'KAPSAM'), ('RECK-01', 'KAPSAM'), ('RECK-02', 'KAPSAM'),
    ('RECK-08', 'KAPSAM'), ('RECK-09', 'KAPSAM'), ('RECK-04', 'KAPSAM'),
    ('RECK-05', 'KAPSAM'), ('RECK-07', 'KAPSAM'), ('TST-07', 'KANIT'),
    ('TST-10', 'KANIT'), ('TST-11', 'KANIT'), ('TST-12', 'KANIT'),
    ('TST-09', 'KANIT'), ('TST-01', 'KANIT'), ('TST-02', 'KANIT'),
    ('TST-03', 'KANIT'), ('TST-05', 'KANIT'), ('TST-06', 'KANIT'),
    ('DEP-01', 'TEDARIK'), ('DEP-02', 'TEDARIK'), ('DEP-06', 'TEDARIK'),
    ('DEP-03', 'TEDARIK'), ('DEP-04', 'TEDARIK'), ('TSL-03', 'TEDARIK'),
    ('TSL-04', 'TEDARIK'), ('TSL-06', 'TEDARIK'), ('TSL-01', 'TEDARIK'),
    ('TSL-02', 'TEDARIK'), ('TSL-05', 'TEDARIK'), ('API-02', 'TEDARIK'),
    ('API-03', 'TEDARIK'), ('API-01', 'TEDARIK'), ('API-05', 'TEDARIK'),
    ('API-04', 'TEDARIK'), ('OZT-01', 'ENVANTER'), ('OZT-02', 'ENVANTER'),
    ('OZT-03', 'ENVANTER'), ('OZT-04', 'ENVANTER'), ('OZT-05', 'ENVANTER'),
    ('OZT-06', 'ENVANTER'), ('OLGU-04', 'ENVANTER'), ('OLGU-05', 'ENVANTER'),
    ('OLGU-06', 'ENVANTER'), ('CHK-01', 'ENVANTER'), ('CHK-02', 'ENVANTER'),
    ('CHK-05', 'ENVANTER'), ('DEC-027', 'ENVANTER'), ('SEC-04', 'BILGI'),
]
RISK_EKLENEN = {'TST-08', 'RECK-06', 'DEP-05',
               'RECK-01', 'RECK-02', 'RECK-04',
               'RECK-05', 'TST-07', 'TST-09',
               'TST-01', 'TST-02', 'TST-03'}
RISK_NOT = {
    'TST-08': 'Ham test raporu yok/okunamiyor — kanitsiz PASS P0; kapinin kanit temeli.',
    'RECK-06': 'Dondurulmus bolge diff\'te — dogrudan tamper sinyali, P0.',
    'DEP-05': 'Izinli lisans listesi disinda bagimlilik — tedarik/uyum P0.',
    'RECK-01': 'KFAZ0 sozlesmesindeki her REQ plan/eslesmede karsilik bulmali; '
               'aksi halde kapsamsiz sozlesme sessizce yesil kalir.',
    'RECK-02': '"UYGULANMIS" denilen her CHG\'nin dosyasi git diff\'te olmali; '
               'beyan ile gercek degisiklik carpraz denetlenir.',
    'RECK-04': '2B kapisinin "KANITLI" dedigi her CHG diff\'te olmali; ikinci '
               'gozun iddiasi manifest ve diff ile dogrulanir.',
    'FRZ-08': 'Temiz agac iddiasi imzayla baglanmali; imzasiz veya yanlis '
               'anahtarli taban tamper ya da dusuk guven sayilir.',
    'RECK-05': 'Hayalet CHG yok: olmayan REQ veya plansiz dosyaya baglanan '
               'degisiklik P0; manifest-diff bagini korur.',
    'RECK-07': 'Davranissal her REQ tabanda olmayan YENI bir test adina '
               'eslenmeli; eski testi gostermek bedava yesildir.',
    'RECK-08': 'Makine bloklarinin alan bicimi semaya uymali; sessizce dusen '
               'girdi RECK-01/07\'yi devre disi birakir.',
    'RECK-09': 'Plan yokken urun kodu degismemeli; KFAZ0 oncesi degisiklik '
               'kapsamsiz ve denetimsiz kalir.',
    'TST-01': 'Basarisiz test sayisi sifir olmali; kirmizi testle PASS verilemez.',
    'TST-02': 'Hatali test sayisi sifir olmali; altyapi hatasi yesil sayilmaz.',
    'TST-03': 'En az bir test kosmali; sifir test temiz degildir.',
    'TST-05': 'Atlanan test tabandan fazla olamaz; test atlayarak yesil olunmaz.',
    'TST-06': 'Kapsam tabanin bir altina kadar korunmali; sessiz kapsam kaybi P1.',
    'TST-07': 'Kanit beyani ham JUnit ile celisemez; kapi kendi beyanina guvenmez.',
    'TST-09': 'Test komutunun cikis kodu kayitli olmali; kosup kosmadigi '
               'bilinmeyen test yesil sayilmaz.',
    'TST-10': 'Rapor kaynaktan eski olamaz; bayat kanit mevcut kodu olcmemis olabilir.',
    'TST-11': 'Kanittaki komut kod_profil ile ayni olmali; baska komutun kaniti '
               'sayilmaz.',
    'TST-12': 'Kanittaki rapor yolu kod_profil ile ayni olmali; baska rapor '
               'gosterilemez.',
    'CHK-01': 'Her zorunlu SCOPE-ID MASTER icinde markdown basligi olarak '
               'bulunmali; metinde gecmesi yetmez.',
    'CHK-02': 'Her zorunlu ID PROVENANCE tablosunda kapsiyor durumunda olmali.',
    'CHK-05': 'Basliklar benzersiz olmali; tekrar eden baslik izlenebilirligi bozar.',
}

# Bu dilimde kapatilamayan, hala hicbir testte gorunmeyen 8 kuralin risk
# sirasindaki ilk ucu. Bunlar silinmez; bir sonraki dilimin acik kaydidir.
SONRAKI_DILIM = ['TST-05', 'TST-06']
SONRAKI_NOT = {
    'TST-05': 'Atlanan test tabandan fazla olamaz; test atlayarak yesil olunmaz.',
    'TST-06': 'Kapsam tabanin bir altina kadar korunmali; sessiz kapsam '
              'kaybi P1.',
}


def risk_tablosu(satirlar):
    durum = {k: d for _b, k, _v, d, _g in satirlar}
    betik = {k: b.split('/')[-1] for b, k, _v, _d, _g in satirlar}
    if len(RISK_SIRASI) != 51 or len({r for r, _g in RISK_SIRASI}) != 51:
        raise SystemExit('RISK_SIRASI 51 tekil kural icermeli')
    eksik = [r for r, _g in RISK_SIRASI if r not in durum]
    if eksik:
        raise SystemExit('RISK_SIRASI envanterde yok: %s' % ', '.join(eksik))
    out = ['| # | Kural | Betik | Grup | Durum | Gerekce |', '|---|---|---|---|---|---|']
    for i, (kural, grup) in enumerate(RISK_SIRASI, 1):
        _durum = durum[kural]
        if _durum == 'TEST EDILDI' and kural in RISK_EKLENEN:
            _durum = 'TEST EDILDI (bu tur)'
        elif _durum == 'BOSLUK':
            # Gizli sayi dusumu yok: kalan her bosluk acikca bir sonraki
            # dilimin kaydidir; kapsam disi gibi etiketlenmez.
            _durum = 'BOSLUK (sonraki dilim)'
        gerekce = RISK_NOT.get(kural, RISK_GRUPLARI[grup])
        out.append('| %d | %s | `%s` | %s | %s | %s |' % (
            i, kural, betik[kural], RISK_GRUPLARI[grup], _durum, gerekce))
    return out


def kapi_betikleri():
    for d in DIZINLER:
        for p in sorted((KOK / d).glob('*.py')):
            if not p.name.endswith('_selftest.py'):
                yield p


def _kimlikler(p):
    """(satir basi bildirimleri, bolum basligi kimlikleri) — TUM dosya.

    Eski surum yalniz ilk 100 satiri okuyordu; FRZ-08 114. satirdaki bolum
    basliginda kaldigi icin envanterde hic gorunmuyordu. Artik sinir yok.
    """
    baslik, bolum = set(), set()
    for satir in p.read_text(encoding='utf-8').splitlines():
        m = KURAL.match(satir)
        if m and m.group(1).split('-')[0] not in YOKSAY_PREFIX:
            baslik.add(m.group(1))
        m = BOLUM.match(satir)
        if m and m.group(1).split('-')[0] not in YOKSAY_PREFIX:
            bolum.add(m.group(1))
    return baslik, bolum


def envanter():
    """{betik_goreli: [kural, ...]} — tum bildirimler + bolum basliklari."""
    sonuc = {}
    for p in kapi_betikleri():
        baslik, bolum = _kimlikler(p)
        kimlikler = baslik | bolum
        if kimlikler:
            sonuc[str(p.relative_to(KOK))] = sorted(kimlikler)
    return sonuc


def tarama():
    """Her kapinin baslik/bolum kimlik kumeleri; sayim kaniti icin."""
    sonuc = []
    for p in kapi_betikleri():
        baslik, bolum = _kimlikler(p)
        if baslik or bolum:
            sonuc.append((str(p.relative_to(KOK)), sorted(baslik), sorted(bolum),
                          sorted(baslik | bolum)))
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


def tarama_tablosu():
    out = ['| Betik | Baslikta | Bolum basligi | Yeni | Envanter |',
           '|---|---|---|---|---|']
    for betik, baslik, bolum, birlesik in tarama():
        yeni = len(set(bolum) - set(baslik))
        out.append('| `%s` | %d | %d | %d | %d |' % (
            betik.split('/')[-1], len(baslik), len(bolum), yeni, len(birlesik)))
    return out


def markdown():
    satirlar, envan, (test, disi, bosluk, oz_anilan) = olc()
    out = ['# Mutasyon kapsami — tam kural envanteri', '',
           'Kaynak: `tools/kapsam.py` (uretilmis dosya; elle duzenlenmez).',
           'Envanter, ATLAS ve KOD kapi betiklerinin satir basi kural bildirimlerinden',
           've dosyanin herhangi bir yerindeki `# --- KIMLIK` bolum basliklarindan gelir;',
           '`*_selftest.py` ve `OLCUM-*` referanslari sayilmaz.',
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
           '## Risk sirasi (51 kural)', '',
           '19.11.2026 itibariyla mutation kapsami olmayan 51 kural; siralama',
           'saglamlik/etki sirasina gore sabittir. Kapatilan her kural bu turda',
           'vaka aldi; durum sutunu guncel envanterden okunur.', '']
    out += risk_tablosu(satirlar)
    out += ['', '## Sonraki dilim', '',
            'Asagidaki kural(lar) bu turda kapatilmadi; hala hicbir testte',
            'gorunmeyen %d kuralin risk sirasindaki ilk %d tanesidir. Bir sonraki' % (
                bosluk - oz_anilan, len(SONRAKI_DILIM)),
            'dilimde gercek vakayla kapatilacak; sessizce sayidan dusulmedi.', '',
            '| Kural | Betik | Neden test edilemedi / neyi korur |',
            '|---|---|---|']
    _risk_durum = {k: d for _b, k, _v, d, _g in satirlar}
    _risk_betik = {k: b.split('/')[-1] for b, k, _v, _d, _g in satirlar}
    for _k in SONRAKI_DILIM:
        if _risk_durum.get(_k) != 'BOSLUK':
            raise SystemExit('SONRAKI_DILIM artik bosluk degil: %s' % _k)
        out.append('| %s | `%s` | %s |' % (_k, _risk_betik[_k], SONRAKI_NOT[_k]))
    out += ['',
           '## Kapsam disi siniflari', '',
           'Gerekceler tahmin degil; her satir betigin kodundaki bagimliliga dayanir',
           '(asagida betik adiyla birlikte yazili).', '']
    out += sinif_tablosu(satirlar)
    out += ['', '## Tarama kaniti', '',
            '`Baslikta` satir basindaki kural bildirimleridir. `Bolum basligi`',
            'dosyanin herhangi bir yerindeki `# --- KIMLIK` basliklaridir; ilk 100',
            'satir siniri YOKTUR. `Yeni`, yalniz bolum basliginda gorunen ve ust',
            'listeye yazilmamis kimliklerdir. Envanter, iki kumenin birlesimidir.', '',
            '`DEC-10/12` ve `GM-17/18` gibi degisiklik etiketleri kural kimligi',
            'degildir; yalnizca kural bildirimleri ve `# --- KIMLIK` basliklari',
            'taranir. `CHK-00` gibi bolum basligi olmayan ara kodlar da bu',
            'envanterin konusu degildir.', '']
    _tarama = tarama()
    out += tarama_tablosu()
    out += ['', 'Toplam: %d betik · %d tekil kural; her satirda Envanter = '
            'Baslikta ∪ Bolum basligi.' % (
                len(_tarama), sum(len(x[3]) for x in _tarama)), '']
    out += ['## Tam envanter', '',
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
