#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tur4_paket_uret.py — 4. tur dis denetim paketini uretir.

NEDEN VAR: 3. turun kok surec kusuru, denetciye OLCULECEK DOSYANIN
verilmemesiydi. Sonuc: 113 `OLCULMEDI`. Bu betik paketi dosyayla birlikte
uretir; elle kopyalama yok, sha256 otomatik yazilir.

KULLANIM
    python3 scripts/tur4_paket_uret.py            # IKI PARCA yazar (varsayilan)
    python3 scripts/tur4_paket_uret.py --tek      # tek dosya (eski davranis)
    python3 scripts/tur4_paket_uret.py --kontrol  # yalniz sha256 + boyut basilir
"""

import hashlib
import os
import re
import subprocess
import sys

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(BURASI)

DOSYALAR = [
    ("A", "SKILL.md", "denetlenen eser"),
    # 11 Kasim 2026: "74 kontrol" SABIT yaziliydi, canli 86. Sayi etikete gomulmez.
    ("B", "scripts/skill_lint.py", "kapilarin kaynagi"),
    ("C", "scripts/d_dis_sayac.py", "denetim cevabi sayaci"),
]


def sha(yol):
    with open(yol, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def oku(yol):
    with open(yol, encoding="utf-8") as f:
        return f.read()


def surum():
    """Sürümü SURUM.md'den okur — elle yazılan sürüm D10 sınıfı hatadır."""
    with open(os.path.join(KOK, "SURUM.md"), encoding="utf-8") as f:
        for satir in f:
            if satir.startswith("Sürüm:"):
                return satir.split(":")[1].strip().split()[0]
    return "BILINMIYOR"


def eser_surum():
    """DENETLENEN ESERIN surumu: `SKILL.md` icindeki `metadata.version`.

    NEDEN AYRI (11 Kasim 2026, olculdu): bu betik bir sure `surum()`u (SURUM.md =
    LAB surumu) "Denetlenen surum: SKILL.md ..." diye yaziyordu. Bugun o deger
    `v1.7.302`, eserin gercek surumu ise `1.4.77`. Denetciye eserin surumu
    hakkinda YANLIS bilgi vermek, hic vermemekten kotudur. Iki surum AYRI yazilir.
    """
    metin = oku(os.path.join(KOK, "SKILL.md"))
    m = re.search(r'^\s+version:\s*"([^"]+)"', metin, re.M)
    if not m:
        return "BILINMIYOR"
    ham = m.group(1).strip()
    return ham if ham.startswith("v") else "v" + ham


def kaynak_tarihi():
    """Paketlenen dosyalarin SON commit gunu (`YYYY-AA-GG`).

    NEDEN (15 Kasim 2026, Z45b — OLCULDU): baslik `datetime.date.today()`
    tasiyordu. Gece devrinde ayni icerik farkli BAYT uretiyor, `C14y` de
    "BAYAT" diyordu. Olcum: `difflib` ile tek fark `**Tarih:** 2026-11-14` ->
    `2026-11-15`; P1 78848 B = 78848 B, sha baska. Yani kapinin gordugu sey
    "eser degisti" degil, TAKVIMIN DONMESIYDI. Yanlis-kirmizi.

    Artik yazilan gun, DENETLENEN SURUMUN gunudur: paketlenen dosyalar
    degismedikce cikti BIT BAZINDA aynidir (`C14y` karsilastirmasi guvenli).

    Fail-closed (I7): git yoksa `SOURCE_DATE_EPOCH` (UTC gun) kullanilir; o da
    yoksa `RuntimeError`. Duvar saatine SESSIZCE donmek ayni kusuru geri getirir —
    ve bu kez kimse fark etmez, cunku hata degil "normal" gorunur.
    """
    yollar = [y for _, y, _ in DOSYALAR]
    try:
        r = subprocess.run(['git', '-C', KOK, 'log', '-1', '--format=%cs', '--']
                           + yollar, capture_output=True, text=True, timeout=60)
        gun = (r.stdout or '').strip()
        if r.returncode == 0 and re.fullmatch(r'\d{4}-\d{2}-\d{2}', gun):
            return gun
    except Exception:
        pass
    sde = os.environ.get('SOURCE_DATE_EPOCH', '').strip()
    if sde.isdigit():
        import datetime as _dts
        # `utcfromtimestamp` 3.12'de DEPRECATED (OLCULDU: testte DeprecationWarning
        # basildi). Davranis ayni: UTC gunu. Zaman dilimi ACIKCA verilir — yerel
        # saate kayan bir hesap, "gun" alanini makineye bagimli yapardi.
        return _dts.datetime.fromtimestamp(
            int(sde), _dts.timezone.utc).date().isoformat()
    raise RuntimeError('kaynak tarihi okunamadi: git basarisiz ve SOURCE_DATE_EPOCH '
                       'tanimsiz — duvar saatine DONULMEZ (C14y yanlis-kirmizi verirdi)')


def ek_satir(yol):
    """Bir EK dosyasinin GERCEK satir sayisi — sablon metnine elle yazilmaz.

    11 Kasim 2026: sablonda "EK A 500 satirdir" / "EK B 1300+ satirdir" yaziyordu.
    Ikincisi canli degerin (2876) cok altindaydi; 8 Kasim'da yazilmis, o gunden
    beri kimse olcmedi. D10 sinifi: gomulu sayac yazildigi gun eskimeye baslar.
    """
    try:
        with open(os.path.join(KOK, yol), encoding="utf-8") as f:
            return str(sum(1 for _ in f))
    except Exception:
        return "BILINMIYOR"


def lint_surum():
    """`scripts/skill_lint.py` içindeki `SURUM:` satırı (ör. `2.32` → `v2.32`)."""
    for satir in oku(os.path.join(KOK, "scripts", "skill_lint.py")).splitlines():
        if satir.startswith("SURUM:"):
            ham = satir.split(":")[1].strip().split()[0]
            return ham if ham.startswith("v") else "v" + ham
    return "BILINMIYOR"


# --- DELTA (tam) — tur 11 -> tur 12 ------------------------------------------
# 17 Kasim 2026. Bu demet ELLE YAZILMADI: `git log` ciktisindan uretildi.
#   git log 857050f..5245423 --reverse --format='%h|%ad|%s' --date=short -- <KAPI_YOLLARI>
# ve `kayit:` ile baslayan satirlar ayiklandi (kayit commit'i mekanizma degistirmez).
# Kanit: `python3 -c "import scripts.tur4_paket_uret as T; print(len(T.DELTA_MADDELER))"`
# Ayni araligi bagimsiz olarak denetci de olcebilir:
#   git rev-list --count 857050f..5245423          -> DELTA_SAYILAR["toplam"]
#   git show --stat <sha>                          -> her satirin kaniti
# YENI TUR -> yeni demet. Bu demet DEGISTIRILMEZ (tarihsel kayit).
DELTA_BASLANGIC = "857050f"
DELTA_BITIS = "5245423"

#: aralik sayilari — TURETILMIS, ve `_delta_tutarlilik()` her cagrida dogrular:
#: toplam == mekanizma + kayit + kapsam_disi ve mekanizma == len(DELTA_MADDELER).
DELTA_SAYILAR = {"toplam": 115, "mekanizma": 68, "kayit": 25, "kapsam_disi": 22,
                 "skill_dokunma": 8, "lint_dokunma": 41}

DELTA_MADDELER = (
    ("C19", "997ebf8", "2026-11-12", "parantez dengesi + _ vurgusu — D1 kapandi (kapi 89->90)"),
    ("C17", "fa89899", "2026-11-12", "§7 Paket sayimi manifestoya bagli — kapisiz sayac kapandi (#1)"),
    ("C16 S10", "f60298b", "2026-11-12", "42 eslesmeyen acilis beyan edildi — gorunur kilindi (#2)"),
    ("Y0+Y1", "da267a6", "2026-11-12", "parantez sayaci duzeltildi (42 -> 25) + bayat kapsam kaydi"),
    ("Y2", "2a17a4a", "2026-11-12", "kod blogu metin degil + kapanmamis backtick fail-closed"),
    ("Y3", "0d3d170", "2026-11-12", "\"25\" de yanlisti — numara ayiklama kalibi kalkti, yigin farkinda kural geldi"),
    ("Y4", "d932139", "2026-11-12", "gercek borc kapandi (SKILL.md satir 323) — ve kapatirken baska kapi yandi"),
    ("Y5", "ab0240f", "2026-11-12", "dil bilgisi turu — satir 323-324 dort cumleye bolundu (kapi korumuyor, olculdu)"),
    ("Z2", "89d0873", "2026-11-12", "token_olcum.py \"P1+P2 birlikte\" satiri hic basmiyordu"),
    ("Z1", "03fbf0e", "2026-11-12", "ag'li kapi sahte kapidir — C14p cevrimdisi + fail-open kapatildi"),
    ("Z4", "88dbaad", "2026-11-12", "ayni sinif kusur ikinci yerde — C14q/C14r hala canliydi"),
    ("Z5", "280024f", "2026-11-12", "taban yazmak onaylamaktir — kapi_farki --yaz korkulugu"),
    ("Z6", "ea7065c", "2026-11-12", "\"aga bagimlilik kalmadi\" iddiasi olculdu — TAM kosu AG KAPALI"),
    ("Z7", "106bc82", "2026-11-12", "snapshot tarihi 3 dosya icin YALAN soyluyordu — dosya bazli tarih"),
    ("Z8", "55fa18d", "2026-11-12", "durum dosyasi yarim kalabiliyordu — atomik yazma"),
    ("Z9", "dedb33f", "2026-11-13", "\"6/6\" elle yazilmisti; duzeltince kapi FAIL-OPEN cikti"),
    ("Z10", "01f357c", "2026-11-13", "ayni kusur sinifi iki betikte daha — yol argumani yok sayiliyordu"),
    ("Z11+Z12", "db5629c", "2026-11-13", "orneklem 6 -> 12 ayet; plato daraldi ve konum yalani kalkti"),
    ("Z13", "36bf9f3", "2026-11-13", "--kabul joker korkulugu artik OLCULUYOR (sira 7)"),
    ("Z14", "7c66ccd", "2026-11-13", "subprocess sinifi — ucuncu parti yok, iki ciplak cagri vardi (sira 8)"),
    ("Z15", "aaae412", "2026-11-13", "sayiyi tutmak ADI tutmak degildir — C15g ad denetimi kazandi (sira 3)"),
    ("Z16a", "af99e21", "2026-11-13", "bos kume = OLCUM YAPILAMADI (kalem 1/3)"),
    ("Z16b", "a4c0aa7", "2026-11-13", "timeout'un varligi degil DEGERI denetlenir (kalem 2/3)"),
    ("Z16c", "7d3eb77", "2026-11-13", "meal_farki olcumu KAPI oldu — C15k (kalem 3/3)"),
    ("Z17a", "f378c15", "2026-11-13", "C15k snapshot ICERIGINI de denetler (kalem #4)"),
    ("Z17", "b7de6e5", "2026-11-13", "olculmeyen B kalemleri #4-#10 (5 mekanizma, 2 zaten kapali)"),
    ("Z18a", "0f7d1db", "2026-11-13", "sablon timeout borcu KAPANDI — C15j artik sablonlari da zorunlu sayar (B-#4)"),
    ("Z18b", "e3a65cd", "2026-11-13", "plato gecici dizin sizintisi KAPANDI — C15l tmp-sizinti==0 ister (B-#5)"),
    ("Z18c", "5acfdb8", "2026-11-13", "_sad3 harf denegi — iki yonlu spesifikasyon (B-#6)"),
    ("Z18d", "fec389d", "2026-11-13", "C15l \"agsiz\" iddiasi YANLISTI — duzeltildi, lint 507s -> 20s (B-#7)"),
    ("Z18e", "4176e67", "2026-11-13", "n>12 VERI SINIRI — sentetik dolgu reddedilir, ust sinir olculur (B-#8)"),
    ("Z19", "75d0bf3", "2026-11-14", "C15l sure esigi MARJ ile gerekcelendi (B-#3)"),
    ("Z20a", "2b2bf33", "2026-11-14", "orneklem n=12 -> 16 ayet (B-#2 karari: \"3\")"),
    ("Z20b", "bd71338", "2026-11-14", "C15m — uc ayet listesi ayrismaz (yeni kapi, 94.)"),
    ("Z21a", "10f5aad", "2026-11-14", "bozuk/eksik snapshot SESSIZCE gecmesin (C-#4)"),
    ("Z21b", "8b025a7", "2026-11-14", "main() her dali korumali, cokme rc=2 (C-#5)"),
    ("Z21c", "f67b600", "2026-11-14", "ayet listesi TEK KAYNAK — scripts/ayetler.py (C-#2)"),
    ("Z22", "76a8ce0", "2026-11-14", "C14m cevrimdisi olcer + kaynagini soyler (ag bagimliligi kapandi)"),
    ("Z23", "6c91af2", "2026-11-14", "kapi_farki parmak izi kapanisa kadar (derin guclendirme gorunur) — C-#3"),
    ("Z24", "8e60899", "2026-11-14", "C15l sure esigi cakili degil, OLCULU (bant ortasi + bayatlama) — C-#10"),
    ("Z25", "222ef6e", "2026-11-14", "ozet iddiasi OLCULEN sinirla sinirli + kapi C15n — C-#6"),
    ("Z26", "4444c2e", "2026-11-14", "ters-probe NO-OP idi — probe gercekten olumsuzluyor (C-#6 duzeltme)"),
    ("Z27", "dd546e1", "2026-11-14", "olumsuzlama probe'u ANLAMI degil SEYRELMEYI olcuyordu (C-#6, 2. bulgu)"),
    ("Z28", "afbd639", "2026-11-14", "C15n inkar penceresi YANLIS-GECIR veriyordu (C-#6 kalan, kullanici \"1\")"),
    ("Z29", "1fb22ea", "2026-11-14", "kapi_farki KOR — kapinin TOLERANS+BEKCI kosullari parmak izinde yoktu"),
    ("Z30", "7629be4", "2026-11-14", "SENTETIK probe yerine GERCEK Turkce olumsuz ozet — 3/4 GECIYOR"),
    ("Z31a", "1b00952", "2026-11-14", "defter en yeni kaniti degil ALFABETIK ILK kaynagi gosteriyordu"),
    ("Z31b", "ff6c5c4", "2026-11-14", "\"kanit sayaci\" gercekte ANMA sayaciydi — SERT kanit ratchet'i eklendi"),
    ("Z32a", "0f38ff5", "2026-11-14", "SERT kanit tanimi exit gecisini de kapsiyor — 36 -> 47 (yikama REDDEDILDI)"),
    ("Z33", "9451c95", "2026-11-14", "mutasyon KOSUCUSU — kanit satirini artik kosum uretiyor"),
    ("Z33b", "486d466", "2026-11-14", "harness timeout'u LITERAL olmali — C15j statik taramasi buldu"),
    ("Z33c", "536d111", "2026-11-14", "ilk mutasyon kosumu — 5 kapi GERCEK kosumla SERT, SERT 47 -> 52"),
    ("Z34a", "7e74a75", "2026-11-14", "capa mutasyon URETECI — kalan 43 kapinin capasi kaynaktan cikarildi"),
    ("Z34b", "69c2343", "2026-11-14", "mutasyon kaydi BIRIKIMLI — --md artik onceki partiyi silmiyor"),
    ("Z34c", "0630e36", "2026-11-14", "parti 2 — 12 mutasyon, 2 kanit (C13u, C15d); SERT 52 -> 54"),
    ("Z34d", "e804a4a", "2026-11-14", "capa penceresi GIRDI SINIRINA daraltildi (isabet 2/12 olculmustu)"),
    ("Z34e", "0bdfd6b", "2026-11-14", "parti 3 — 5 mutasyon, 1 kanit (C13n); SERT 54 -> 55"),
    ("Z38a", "e48aa69", "2026-11-14", "TOKEN mutasyon ureteci — `_gerek` demetleri AST ile okunuyor"),
    ("Z38b", "8e8dab3", "2026-11-14", "`re.I` duzeltmesi — token deseni BUYUK harfi kaciriyordu"),
    ("Z38c", "88e19e7", "2026-11-14", "kosum 7 kaydi — token yontemi 3/3 (C13e, C13r, C13s)"),
    ("Z38d", "dff2765", "2026-11-14", "kosum 8 kaydi — token yontemi 4/4 (C13k, C13l, C13m, C13o)"),
    ("Z39a", "0fa3063", "2026-11-14", "span genisletme — C11c ve C13i artik aday uretiyor"),
    ("Z43a", "b70ec20", "2026-11-14", "kosucuya `yeni_dosya` bicimi — FAIL yolu yeni DOSYA isteyen kapilar icin"),
    ("Z44", "c49a779", "2026-11-14", "C17 katman (2) sentetik fixture ile sinanir — arsiv yokken katman olculmuyordu"),
    ("Z45b", "91ab661", "2026-11-15", "paket tarihi duvar saatinden degil KAYNAKTAN gelir — C14y gece devri yanlis-kirmizisi"),
    ("Z45d", "8a1f068", "2026-11-15", "C17 \"dogrulanan dosya\" sayisi BEKLENEN sayiydi — beyan/olcum celiskisi"),
    ("Z45c", "6d8bd57", "2026-11-15", "SOURCE_DATE_EPOCH ve RuntimeError dallari CALISTIRILDI (EK 116 OLCULMEYEN)"),
    ("C15i", "5245423", "2026-11-15", "kapi KORLESTIRILMEDI — siniflandirma sozlesmesi projenin kendi hukmune baglandi"),
)


def _delta_tutarlilik():
    """Gomulu sayilar KENDI KENDINI denetler (D10 sinifi: elle sayi bayatlar).

    (1) `mekanizma` demetin uzunlugu olmali — ayri yazilmis sayi tutmazsa hata.
    (2) `toplam` == mekanizma + kayit + kapsam_disi — eksik sinif kalmasin.
    Hata varsa `uret()` coker: sessiz yanlis paket gitmesindense cokme iyidir.
    """
    n = len(DELTA_MADDELER)
    s = DELTA_SAYILAR
    if s["mekanizma"] != n:
        raise RuntimeError("DELTA_SAYILAR['mekanizma']=%d ama demet %d eleman"
                           % (s["mekanizma"], n))
    if s["toplam"] != s["mekanizma"] + s["kayit"] + s["kapsam_disi"]:
        raise RuntimeError("DELTA_SAYILAR toplami tutmuyor: %d != %d+%d+%d"
                           % (s["toplam"], s["mekanizma"], s["kayit"], s["kapsam_disi"]))
    return s


def delta_tablo():
    """Tam delta tablosu — her mekanizma commit'i tek satir + kanit komutu."""
    satir = ["| # | Etiket | Ne değişti (commit konusu) | Kanıt |",
             "|---|---|---|---|"]
    for i, (et, h, _d, k) in enumerate(DELTA_MADDELER, 1):
        satir.append("| %d | `%s` | %s | `git show --stat %s` |" % (i, et, k, h))
    return "\n".join(satir)


BASLIK = """# BEŞİNCİ TUR (dış tur **12**) DIŞ DENETİM PAKETİ — `SKILL.md`

> **Adlandırma (kayıtlı çelişki, `docs/TUR_HARITASI.md` §5):** lab bu turu
> "beşinci" diye adlandırdı; haritada **dış tur 12**'dir. Dosya adı
> `TUR5`'tir. Önceki paket `TUR4` idi (dış tur 11) — o dosya **silinmedi**,
> `docs/DIS_DENETIM_TUR4_P1.md` olarak duruyor.

**Tarih:** {TARIH} (paketlenen dosyaların son commit günü) · **Paket hazırlayan:** lab
**Denetlenen sürüm:** `SKILL.md` **{ESER_SURUM}** (kendi `metadata.version`'i) · `scripts/skill_lint.py` **{LINT_SURUM}**
**Lab kaydı:** `SURUM.md` **{SURUM}** — bu ESERİN sürümü değildir, labın sürümüdür
**Önceki tur:** dördüncü / dış tur 11 — paket `docs/DIS_DENETIM_TUR4_P1.md` + `_P2.md`.
Gönderim 12 Kasım 2026'da yapıldı; dosyalar 17 Kasım'da **yalnız sürüm satırı** için yeniden
üretildi (`9622518`) — yani `TUR4` paketindeki metin 12 Kasım'ın metnidir, delta bölümü dahil.

## Kimlik (paketi aldığını doğrula)

| Ek | Dosya | sha256 | Boyut |
|---|---|---|---|
{KIMLIK}

**Bu sha'lar senin elindeki metinle tutmuyorsa `OLCULMEDI` yaz ve dur** — yanlış sürümü
denetlemek, hiç denetlememekten kötüdür.

> **Not (ölçüldü):** EK blokları kaynaktan **birebir** kopyadır. Kaynak dosya newline'sız
> bitiyorsa (`scripts/skill_lint.py` öyle) blok sonuna markdown çiti için **1 bayt `\n`**
> eklenmiştir. Yani EK B'nin metni kaynaktan **+1 bayt** uzundur; tablodaki sha **kaynak
> dosyanın** sha'sıdır. EK A ve EK C birebir (0 bayt fark).

---

## §0 — BU TUR NEDEN VAR

Üçüncü turda **286 hücrenin 113'ü `OLCULMEDI`** çıktı. Sebep denetçilerin isteksizliği
değildi; **labın süreç kusuruydu**: paket, maddeleri ve *beklenen ölçüm komutlarını*
verdi ama **eserin kendisini vermedi**. Denetçiler dosyayı açamadı, dürüstçe
`OLCULMEDI` yazdı. Bir denetçi bunu açıkça kaydetti:

```
"SKILL.md v1.4.75 ve skill_lint.py v2.31 bu turda verilmedi, hicbir komut
 tarafimdan calistirilmadi, tum olcum alanlari OLCULMEDI"
```

**Bu paket dosyayı TAŞIYOR.** EK A / EK B / EK C tam metindir.

**Sonuç:** bu turda `"dosya verilmedi"` **geçerli cevap değildir.** Dosya elinde.
Bir maddeyi yine ölçemiyorsan **gerekçesini yaz** (`"EK A'da bu bilgi yok"` gibi) —
sadece `OLCULMEDI` yazıp bırakmak bu turda kabul edilmez.

---

## §1 — DENETÇİYE ÜÇ UYARI

1. **Lab kendini denetleyemez.** Bu paketteki her "ölçüldü" satırı **labın iddiasıdır**,
   kanıt değil. EK A/B/C'yi kendin oku, kendin hüküm ver.
2. **Lab bu turda KENDİ sayılarının yanlış olduğunu buldu** (§2). "Hepsi kapandı" demiyor.
3. **Rakam verme.** "N kontrol geçti" gibi cümleler **kapının çıktısıdır**, senin ölçümün değil.

---

## §2 — TUR 11'DEN BU YANA NE DEĞİŞTİ (tam delta)

**Aralık:** `{DELTA_BAS}..{DELTA_SON}` · **{DELTA_TOPLAM} commit**.
Dağılım: **{DELTA_MEK} mekanizma** (aşağıdaki tablo — her satır bir commit) ·
**{DELTA_KAYIT} kayıt** (DERSLER/SURUM/EK satırı; mekanizma değiştirmez) ·
**{DELTA_DISI} kapsam dışı** (midéo / silat / ATLAS hatları — bu paketin konusu değil).

**Bu tablo elle yazılmadı.** `git log <aralık> -- <kapı yolları>` çıktısından üretildi ve
`scripts/tur4_paket_uret.py` içinde `DELTA_MADDELER` demeti olarak duruyor. Her satırın
kanıtı yazılı: `git show --stat <sha>` → o commit'in hangi dosyaya dokunduğu.
Sayılar `DELTA_SAYILAR`'da; `_delta_tutarlilik()` her üretimde tutarlılığı **çökerterek**
denetler (mekanizma = demet uzunluğu; toplam = mekanizma + kayıt + kapsam dışı).

**Aralık neden burada bitiyor:** bitiş `{DELTA_SON}` = kapı hattındaki **son mekanizma**
commit'i. Bu tarihten sonra atılan kayıt commit'leri (DERSLER numarası, `SURUM.md` satırı, EK)
delta'yı **değiştirmez**; kapı/eser davranışını değiştirmedikleri için. Böylece paket,
kayıt commit'i atıldıkça bayatlamaz.

> **Kendi kendini doğrulama (denetçi için).** Şu iki komut tablonun aralığını sınar:
> `git rev-list --count {DELTA_BAS}..{DELTA_SON}` → **{DELTA_TOPLAM}** olmalı.
> Sayı tutmuyorsa tabloyu da sayıyı da çöpe at; paket sana **yanlış aralık** anlatıyor.

### Tam delta — {DELTA_MEK} mekanizma commit'i

{DELTA_TABLO}

### Değişmeyenler de bilgidir

- `scripts/d_dis_sayac.py` bu aralıkta **hiç değişmedi**: `git log -1 --format='%h %ad' --date=short -- scripts/d_dis_sayac.py` → `eae3741 2026-11-08`. Yani **EK C, tur 11'de denetlenen metnin aynısıdır** — onu yeniden denetlemek yeni bir şey ölçmez; yine de taşınıyor, çünkü paket eseri eksiksiz taşır.
- `SKILL.md` bu aralıkta **{DELTA_SKILL} kez** değişti (`git rev-list --count {DELTA_BAS}..{DELTA_SON} -- SKILL.md`); `scripts/skill_lint.py` **{DELTA_LINT} kez** (`-- scripts/skill_lint.py`). İki sayı toplanmaz: bir commit iki dosyaya birden dokunabilir.

### Bu bölümün önceki hâli nerede

Tur 11 paketindeki **8 Kasım deltası silinmedi**:
`git show 9622518:docs/DIS_DENETIM_TUR4_P1.md` → §2. Bu bölüm onun **yerine** geçer,
onu düzeltmez: o metin 11 Kasım paketine aitti, bu metin 12. tura aittir.

---

## §3 — SANA NE SORULUYOR (üç bölüm, üçü de zorunlu)

### A · 9 madde — tek karar

`D1 D2 D4 D7 D10 D11 D13 D17 D21`

**Sorulmayan 7 madde — neden yok:** `D3 D5 D14 D15 D18 D19 D22` üçüncü turda
**itirazsız** kapandı (>=8 `KAPANDI`, 0 `KAPANMADI`) ve eser o günden sonra bu
maddelere **değmedi** (`git log -S`, son değişiklik 2026-11-07). Kayıt:
`docs/MADDE_KAPANIS.json`. Kural: `SKILL.md` **§7.5** — kapanmış madde yeniden
sorulmaz; yeniden açmak için gerekçe şart (`C15a` kilitler).

**Bunlardan birini yeniden açmak istiyorsan** gerekçeyi yaz: hangi commit ya da
hangi yeni kanıt. Yoksa `KAPANDI (tur 3)` sayılır ve cevap beklenmez.

**Not:** `D6 D9 D12 D16 D20` diye madde **yoktur**. Üçüncü turda bir denetçi var olmayan
`D8`'e hüküm verdi ve üç gerçek maddeyi atladı. **Uydurma maddeye hüküm verme.**

| Karar | Ne zaman |
|---|---|
| `KAPANDI` | EK A/B'de kusur yok **veya** ölçümle kapandı |
| `KAPANMADI` | Kusur güncel sürümde duruyor |
| `YENI_KUSUR` | Düzeltme yeni bir boşluk açtı |

### A2 · §8'deki 6 BULGU — tur 11'in açık kalemleri

`N1 N2 N3 N4 N5 N6` — §8'de her biri için **labın ölçümü ve ham çıktısı** yazılı.
Her biri için tek kelime ver: `KATILIYORUM` · `KATILMIYORUM` · `OLCULMEDI`.
Katılmıyorsan **hangi cümleye** katılmadığını ve **hangi kanıtla** yaz.
`N6` bilerek `TARTIŞMALI` bırakıldı — labın gerekçesini oku, kendi hükmünü ver.

### B · 6 LAB İDDİASI — çürütmeye çalış

Bunlar labın **kendi beyanları**. Görevin **doğrulamak değil, çürütmeye çalışmak**.
Çürütemezsen `TUTTU` yaz; çürütürsen **hangı satır/kanıtla** olduğunu yaz.

| # | Labın iddiası | Nerede ara |
|---|---|---|
| L1 | **Kapı sayısı ve `C14t-a` ayırt etme gücü labın iddiasıdır** — sayıyı EK B'den **kendin say** | EK B, `k('C1..'` satırları; `_G14TA_YAK` / `_G14TA_MESRU` |
| L2 | `C14x` manifest dışı dosyayı **3 sınıfa** ayırır, KANITSIZ'da FAIL | EK B, `C14x` bloğu |
| L3 | `C14t` **bilinen yazım kümesini** yakalar, anlatılan biçimlerle — kaç tanesini kaçırdığını EK B'deki `bilinen-kacak` satırından **kendin** oku | EK B, `_SAYAC*` — biçimleri **kendin** dene |
| L4 | `SKILL.md` **500 satır** ve `C6` bunu kilitler | EK A sonu · EK B `k('C6'` |
| L5 |**41 açık hücre**nin düştüğü D kümesi, kapatılan 10 grupla aynı (`KAPSANMAYAN: YOK`) | **DİKKAT — bu iddia EK A'da YOK.** `SKILL.md` §13 = *ÖZ TEST (12 soru)*; içinde `KAPSANMAYAN` dizesi **geçmiyor** (ölçüldü, 11 Kasım). Dize yalnız **eski tur belgelerinde** (`docs/DEVIR-…`, `docs/DIS_DENETIM_TUR3_SONUC_…`) duruyor, EK'lerde değil. Yani bu iddia **EK'lerden doğrulanamaz** — yalnız *"desteklenmiyor"* diyebilirsin. Bunu bir **bulgu** say: labın paketi kendi iddiasına işaret edemiyor |
| L6 | `D17` **tam kapanmadı** (lab bunu kabul ediyor) | EK A §7.1 `BAGIMSIZLIK` · EK B `C14v` |

**L5 özellikle önemli:** lab "kapsanmayan yok" diyor. EK A'da **karşılığı olmayan** bir
D maddesi bulursan bu iddia çürür.

---

## §4 — 9 MADDENİN GÜNCEL DURUMU (labın iddiası — doğrula)

> **Bu bölüm 11 Kasım'da yazıldı ve o günün hâlini anlatır.** §2'deki delta, bu tablodan
> sonra eklenen kapıları listeliyor. En az bir madde bu arada **hareket etti**: `D1` için
> `C19` eklendi (12 Kasım, `997ebf8`) — aşağıda `D1`'in "Lab:" cümlesi `C13v`+`C14s` diyor,
> `C19`'u **anmıyor**. Yani D1 hükmünü verirken EK B'de `C19` bloğunu da ara; aşağıdaki
> cümle eksiktir ve bu, düzeltilmiş değil **kaydedilmiş** bir eksikliktir.

Her maddede: **labın iddiası** · **EK A/B'de nerede** · **sana sorulan**.
Satır numarası **verilmiyor** — sürüm değişince kayar. Metinden ara.

### D1 — vurgu/parantez dengesi sınıfı
**Lab:** `C13v` tek bir diziyi (`)*)`) arar. **`C14s` (8 Kasım 2026) sınıfı kapatmak için
eklendi** — markdown ayristiricisiyla *çözülmemiş vurgu işareti* (metin düğümünde literal
`*`) arar.
**Nerede:** EK B `k('C13v'` **ve** `C14s` bloğu (`k('C14s'`).
**Neden bu satır değişti (11 Kasım 2026, ölçüldü):** bu bölüm 8 Kasım'da yazıldı ve
*"tek kalıp mı, sınıfın tamamı mı?"* diye soruyordu. **O soru 3. turda iki model
tarafından cevaplandı ve cevabı uygulandı** (`skill_lint.py` `C14s` başlığındaki not).
Paket cevaplanmış soruyu soruyordu; denetçi "KAPANMADI" yazsaydı bulgu **yanlış**
olurdu. Soru artık şu: **`C14s` sınıfı gerçekten kapatıyor mu, yoksa hâlâ kaçak var mı?**
**Sana sorulan:** `C14s`'in ölçtüğü sınıf tam mı? Kaçan bir vurgu/parantez biçimi var mı?

### D2 — hadis ölçümünde §12 kanıt bloğu
**Lab:** §12 alanları (iddia/komut/çıktı/kod) mevcut.
**Nerede:** EK A §12.
**Sana sorulan:** alan **var** ama **içerik** yeterli mi? Alanın varlığı ölçüm sayılır mı?

### D4 — `curl`/`urllib` 403 ↔ 200 çelişkisi
**Lab:** çelişen üç iddia **silinmedi**, `OLCULMEDI` etiketiyle duruyor (I6).
**Nerede:** EK A `urllib`.
**Sana sorulan:** etiketlemek yeterli mi, yoksa çelişen iddiaların **tek yerde** toplanması
mı gerekir? `OLCULMEDI` etiketi çelişkiyi **görünür** kılıyor mu, gizliyor mu?

### D7 — `DURULAN` / `DURDURULAN`
**Lab:** terim **değiştirilmedi**; tartışma `ACIK_SORU` olarak kayıtlı. Bu bir **insan kararıdır**.
**Nerede:** EK A `DURULAN` · `ACIK_SORU`.
**Sana sorulan:** model bunu kapatabilir mi, yoksa `ACIK_SORU` kalması **doğru** mu?

### D10 — gömülü sayaç (**11 Kasım 2026'da KAPANDI — dördüncü tekrarda**; §2'deki
5. TUR NOTU'na bak. Aşağısı 8 Kasım'daki **üçüncü** tekrarın kaydıdır.)
**Lab:** `C13x` (rakam) + `C14t` (sözcük) + `C14t-a` (öz-sınama).
**Nerede:** EK A `C14t` · EK B `_SAYAC1..7` · `_G14TA_*`.
**Sana sorulan:** düzeltme **kök sebebi** mi kapatıyor? EK B'deki 7 desenin **dışında**
kalan bir yazım biçimi var mı? (Lab: "tanımlanmamış biçim kaçabilir" diyor — bu sınır yeterli mi?)

### D11 — betik `sha256` kimlik listesi
**Lab:** `kod=H` ise `sha256` hesaplanamaz; MOD-B istisnası yazılı. Her yeni kapı `KIMLIK_DEGISTI` üretir.
**Nerede:** EK A §8.2/1 · EK B `C14u`.
**Sana sorulan:** `ARAC_DEGISTI` / `KIMLIK_DEGISTI` ayrımı bunu çözüyor mu, yoksa
"her yeni kapı tabanı değiştirir" sorunu **tanım gereği** kalıyor mu?

### D13 — `Şura` ASCII sayıldı
**Lab:** eski cümle **silinmedi**, tarihli düzeltme notu eklendi.
**Nerede:** EK A `Şura`.
**Sana sorulan:** 9 hücre **aynı** kusuru mu anlatıyordu, yoksa alt-kusur var mı?

### D17 — K6 öz-denetim, bağımsız onay yok
**Lab:** **TAM KAPANMADI.** `BAGIMSIZLIK: VAR` yazıldıysa `BAGIMSIZLIK_KANIT` zorunlu ve
`bagimsizlik_dogrula.py` rc=0 vermeli. Ama **aynı ajan** kendi kanıt dosyasını üretebilir.
**Nerede:** EK A §7.1 · EK B `C14v`.
**Sana sorulan:** bu **yapısal** bir sınır mı (kapatılamaz), yoksa ölçülebilir bir kapı var mı?
Lab "kapanmadı" diyor — bu **doğru** mu, yoksa lab gereğinden fazla mı temkinli?

### D21 — `urllib` iddiaları kayıtsız
**Lab:** `python3 scripts/http_olcum.py` komutu dosyada var; iddia `OLCULMEDI`.
**Nerede:** EK A `urllib`.
**Sana sorulan:** etiketleme yeterli mi? Komut **var ama çalıştırılmamış** — bu kayıt mı, boşluk mu?

---

## §5 — ÖLÇÜLMEDİĞİNİ LABIN KABUL ETTİĞİ ŞEYLER

Bunlar `KAPANDI` diye **sunulmuyor**:

1. **113 `OLCULMEDI`** — bu paketin varlık sebebi; bu turda cevaplanacak.
2. **Canlı ağ kapıları** (`C14l/m/n/r`): 90 s'de timeout; bu paket `SNAPSHOT_ONLY` yolunu
   tarif eder. Snapshot sha256 ile sabit — **ağ yolunun kendisi ölçülmedi**.
3. **`C13` yapısal sınırı:** çapalar cümlenin **varlığını** ölçer, **doğruluğunu** ölçmez.
4. **`C14t` sınırı:** **bilinen** yazım kümesini yakalar; tanımlanmamış biçim (ör. Roma rakamı) kaçabilir. Kümenin ne kadarını yakaladığı EK B'deki `regresyon` / `bilinen-kacak` alanlarında **canlı** yazar.
5. **`C14x` "okunuyor" ölçütü:** dosya adının kodda **tırnaklı** geçmesine bakar; değişkenle
   kurulan dolaylı okuma bu ölçütü atlatır.
6. **`1.00` kapsam yorumu** — metin kaynağın kendisiyse zorunlu. "Alıntı kaymadı" der;
   **"çeviri doğru" demez.**
7. **Eşik değerleri** (0.50 ×3) ve **`ESKI_GUN=90`** — insan kararı, ölçülmedi.
8. **Mimo v2.6'nın 12 maddelik "kalan → KAPANDI" beyanı** — sayı olarak sayıldı (12),
   **tek tek doğrulanmadı** (hangi 12 D olduğu metinde adlandırılmamış).
9. **6 "yetim" snapshot dosyası** — silinmedi; 6'sı da manifest içi bir dosyanın **byte kopyası**.

---

## §6 — NASIL CEVAP VER

### A bölümü — her madde **tek satır**

```
D<n> : KAPANDI | KAPANMADI | YENI_KUSUR — <gerekçe> — ölçüm: <EK A/B'de hangi satır> → <ne gördün>
```

### B bölümü — her iddia **tek satır**

```
L<n> : TUTTU | CURUDU — <gerekçe> — kanıt: <EK A/B'de hangi satır>
```

### Sonda üç şey

- **YENI_KUSUR saydıkların:** (liste)
- **FARK EDİLMEYEN SINIR:** labın **kendi göremediği** kör nokta — varsa
- **GENEL HÜKÜM:** bir cümle

**Ölçmediğin hüküm için `OLCULMEDI` yaz** — ama **gerekçesiyle**. Bu turda "dosya verilmedi"
geçerli değil; dosya aşağıda.

---

## §7 — SINIRLARI BİL

- **EK A {EK_A_SATIR} satırdır.** Uzun ama tamamdır; kısaltılmadı, özetlenmedi.
- **EK B {EK_B_SATIR} satırdır.** Kapıların kaynağı. Okumak zorunda değilsin; **hüküm verdiğin
  maddenin** kapısını oku. Bu iki sayı **canlı** hesaplanır — 8 Kasım'da burada
  `500` ve `1300+` yazıyordu; ikincisi elle yazıldığı gün eskimeye başladı.
- **Sen metni okuyorsun, çalıştırmıyorsun.** Bu yüzden "komutu çalıştırdım" **deme** —
  `OLCULMEDI` yaz ve **hangi komutun** çalıştırılması gerektiğini söyle. Bu, lab için
  bir sonraki turun iş listesidir.

---

## §8 — TUR 11'İN AÇIK BULGULARI (6 madde — lab ÖLÇTÜ, hüküm senin)

Dış tur 11'in cevabı geldi (`v1.4.77.md`, 17 model). Orada **yeni kusur** diye işaretlenen
şeylerin bir kısmı lab tarafından ölçüldü. Aşağıdaki tablo **labın ölçümüdür, hükmü değil**.
Her satırda yapılan ölçümün komutu ve ham çıktısı var; **sen bağımsız hüküm ver**.

| # | Bulgu (tur 11'de kim söyledi) | Labın ölçümü (komut → ham çıktı) | Labın sınıfı |
|---|---|---|---|
| **N1** | `SKILL.md` "Bilinen kacak **3**" yazıyor (Fugu · DeepSeek v4.1 flash · Mistral) | `grep -cF "kacak 3" SKILL.md` → **1** · `python3 scripts/skill_lint.py` satırı → `C14t-a ... bilinen-kacak=5` | **AÇIK** — bayat gömülü sayı (D10 altıncı tekrar) |
| **N2** | Kapının kaçak listesi ile bastığı liste tutmuyor (DeepSeek v4.1 flash) | `C14t-a` çıktısı → `bilinen-kacak=5 ['IIII kontrol', 'IC kapi', 'VV kontrol']` — **5 diyor, 3 yazıyor**; kaynakta `_G14TA_BILINEN_KACAK[:3]` | **AÇIK** — `'86 madde'` ve `'adet: 67'` çıktıda **hiç görünmüyor** |
| **N3** | `KOSUL_DEGISTI` eserde tanımsız (Glm 5.3 flash · Fugu) | `grep -cF KOSUL_DEGISTI SKILL.md` → **0** · `scripts/kapi_farki.py` → **6** · `scripts/skill_lint.py` → **3** | **AÇIK** — kapı üretiyor, sözlükte adı yok |
| **N4** | `MADDE_KAPANIS` eşiği `YENI_KUSUR` hücresini göremiyor | `python3 -c` şema taraması → 7 kaydın **hiçbirinde** `yeni_kusur` alanı yok; `D18` = `kapandi=9 kapanmadi=0` → `ITIRAZ_YOK`. Oysa 3. tur cevabında (`sha 49358d28…`) `D18 : YENI_KUSUR` **var** | **AÇIK** — şema körlüğü (bulgunun kendisi düzelmiş olsa da hücre kaydedilemiyor) |
| **N5** | `C13w` `[GECERSIZ]` jetini aramıyor (Meta AI) | `SKILL.md`'den **iki** `[GECERSIZ]` jeti silindi; `C13w` çapası hâlâ `1/1 · 1/1 · 1/1` → **PASS** | **AÇIK** — işaret silinse kapı yine yeşil |
| **N6** | `http_olcum.py` 403'te `rc=0` dönüyor (DeepSeek v4.1 flash) | `scripts/http_olcum.py:41` → `return 0` (403 dalında da) | **TARTIŞMALI** — ölçüm *yapıldı* (403 ölçüldü), rc=0 bunu anlatıyor olabilir. **Lab kendi lehine karar vermedi**; gerekçeyi I4 gereği yazdı, hüküm sende |

### Tur 11'de "yeni kusur" denen ama **kapanmış** çıkanlar

Bunları **tekrar açma** — ölçüldü, düzeldi. Yine de bağımsız doğrula:

- **Bayat parametre beşlisi** (`35 bilinen · 1680 · %98.1 · 0/19`): `grep -cF` her biri için `SKILL.md`'de **0**. `C18` (12 Kasım, `857050f`) kaldırdı. *(Fugu, DeepSeek v4.1 flash ve Mistral bunu tur 11'de görmüştü — o gün doğruydu, bugün değil.)*
- **`25 bilinen yazimi` etiketi**: `scripts/skill_lint.py`'de **2** geçiş var ama ikisi de **tarihsel kayıt** (l.220 düzeltme notu, l.1836 yorum) — canlı etiket değil.
- **`C14s` parantezi ölçmüyor** (DeepSeek v4.1 flash · Grok 4.7): `C19` (12 Kasım, `997ebf8`) parantez dengesini **ayrı kapı** olarak ekledi. EK B'de `k('C19'` bloğunu ara.
- **Paket §2'deki "canlı 86"**: **artık pakette gömülü kapı sayısı yok** (§2'de tablo var, sayı yok). Bu paketteki her sayı ya `git`'ten ya `grep`'ten gelir; **kapı sayısı ise hiç yazılmaz** — tek kaynak EK B'deki `C15e` / `SONUC:` satırı (D10 dersi: gömülü sayaç bayatlar).

### Labın ÖLÇEMEDİĞİ, senin ölçebileceğin iki iddia

Bunlar tur 11'de söylendi, lab **doğrulamadı** — burada `OLCULMEDI` olarak duruyor:

1. **"EK B kendi kendine yetmiyor"** (Fugu — kendi sayısını veriyor, lab **doğrulamadı**): kapıların bir kısmı `scripts/` altındaki kardeş betiklere, `docs/`'a, `scripts/tests/*.json` tabanlarına bağlı ve bunlar pakette yok. Lab bu sayıyı **ölçmedi** (`OLCULMEDI`). Ölçmek istersen: EK B'de `_BURASI` yol birleştirmelerini say, `DOSYALAR` demetindeki üç dosyada **olmayan** hedefleri ayır.
2. **"`C1e` taban dosyaları elle güncelleniyor"** (Gemini 2.5): `scripts/tests/skill_surum_taban.json` + `lint_surum_taban.json` pakette **yok**, taban `--surum-taban-yaz` ile elle yazılıyor. Lab bunu kusur **saymadı** (I4: gerekçe `skill_lint.py:460`'ta yazılı — *"`--surum-taban-yaz` çalıştırılınca betik ... adlı bir DOSYA"* tuzağı). Gerekçeyi oku, kabul etmiyorsan **gerekçeyle** yaz.

---

"""


# PARCALAMA (8 Kasim 2026): 154 KB'lik tek paket icin "denetci baglamina
# sigar mi" sorusu OLCULEMEDI (tiktoken/transformers yok). Cozum olcmek degil,
# soruyu ORTADAN KALDIRMAK: paket iki parcaya bolunur, her parca ~20k token.
# P1 = hukum vermek icin gereken her sey (mandat + 9 madde + 6 iddia) + EK A.
# P2 = kapilarin kaynagi (EK B + EK C). Denetci P1'i okur, P2'ye BAKAR.
P1_ETIKET = ("A",)
P2_ETIKET = ("B", "C")

P2_BASLIK = """# BEŞİNCİ TUR (dış tur **12**) DIŞ DENETİM PAKETİ — **PARÇA 2/2** (ESER)

**Tarih:** {TARIH} (paketlenen dosyaların son commit günü) · **Paket hazırlayan:** lab
**Denetlenen sürüm:** `SKILL.md` **{ESER_SURUM}** (kendi `metadata.version`'i) · `scripts/skill_lint.py` **{LINT_SURUM}**
**Lab kaydı:** `SURUM.md` **{SURUM}** — bu ESERİN sürümü değildir, labın sürümüdür

> **Bu dosya tek başına okunmaz.** Hüküm vermek için **PARÇA 1/2**
> (`{P1_AD}`) gerekir: 9 madde, 6 lab iddiası ve cevap biçimi oradadır.
> Bu parça yalnızca **kaynağı** taşır. İki dosya birlikte tek pakettir;
> ayrı ayrı denetlenmez.

## Kimlik (paketi aldığını doğrula)

| Ek | Dosya | sha256 | Boyut |
|---|---|---|---|
{KIMLIK}

**Bu sha'lar senin elindeki metinle tutmuyorsa `OLCULMEDI` yaz ve dur.**

"""


def _ek_blogu(etiket, yol, ne):
    tam = os.path.join(KOK, yol)
    s = sha(tam)
    b = os.path.getsize(tam)
    icerik = oku(tam)
    # KAPATMA CITI KENDI SATIRINDA OLMALI: dosya sonu newline'siz bitiyorsa
    # ```` onceki satira yapisir ve blok render edilmez (olculdu: EK B).
    if not icerik.endswith("\n"):
        icerik += "\n"
    # dis cit: 4 backtick — icerikte ``` varsa bozulmasin
    return ("\n---\n\n## EK %s — `%s` (%s)\n\n"
            "sha256 `%s` · %d B\n\n````text\n%s````\n"
            % (etiket, yol, ne, s, b, icerik))


def _kimlik(secim):
    satir = []
    for etiket, yol, ne in DOSYALAR:
        tam = os.path.join(KOK, yol)
        satir.append("| %s | `%s` | `%s` | %d B |"
                     % (etiket, yol, sha(tam), os.path.getsize(tam)))
    if secim is not None and len(secim) < len(DOSYALAR):
        var = set(secim)
        yok = [e for e, _, _ in DOSYALAR if e not in var]
        satir.append("")
        satir.append("Bu parçada taşınmayan ek(ler): **%s** — diğer parçada."
                     % ", ".join("EK " + e for e in yok))
    return "\n".join(satir)


def parca_adlari():
    """Parca dosya adlari — TUR kimligine bagli, URETIM GUNUNE degil.

    12 Kasim 2026 (olculdu): ad `..._P1_2026-11-11.md` bicimindeydi ve
    `datetime.date.today()` kullaniyordu. Gece yarisi gecince `C14y`:
      FAIL `DIS_DENETIM_TUR4_P1_2026-11-12.md YOK (uret: tur4_paket_uret.py)`
    Yani her gecis kapiyi KIRMIZI yapiyordu; dunku paket "kayip" gorunuyordu.

    Ad, ICERIGIN kimligini tasir: bu TUR5'in paketidir (dis tur 12). Uretim gunu ise
    ZATEN icerikte yazar (`**Tarih:** {TARIH}` + kimlik tablosu). Gunu ada
    ikinci kez koymak, ayni bilgiyi iki yerde tutup birini eskimeye mahkum
    etmekti. Yeni tur -> `TUR5` adi. Ayni turda icerik degisirse ad DEGISMEZ.
    """
    return ("DIS_DENETIM_TUR5_P1.md", "DIS_DENETIM_TUR5_P2.md")


def uret(secim=None):
    """secim=None -> tek dosya (tam paket). ('A',) -> P1. ('B','C') -> P2."""
    secim = tuple(secim) if secim is not None else tuple(e for e, _, _ in DOSYALAR)
    ekler = "".join(_ek_blogu(*d) for d in DOSYALAR if d[0] in secim)
    if secim == P2_ETIKET:
        baslik = (P2_BASLIK.replace("{KIMLIK}", _kimlik(secim))
                  .replace("{P1_AD}", parca_adlari()[0]))
    else:
        baslik = BASLIK.replace("{KIMLIK}", _kimlik(secim))
    baslik = (baslik.replace("{TARIH}", kaynak_tarihi())
              .replace("{SURUM}", surum())
              .replace("{ESER_SURUM}", eser_surum())
              .replace("{LINT_SURUM}", lint_surum())
              .replace("{EK_A_SATIR}", ek_satir("SKILL.md"))
              .replace("{EK_B_SATIR}", ek_satir("scripts/skill_lint.py")))
    # DELTA — gomulu sayilar ONCE, tek yerden (cokme riski burada gorunur)
    _ds = _delta_tutarlilik()
    baslik = (baslik.replace("{DELTA_BAS}", DELTA_BASLANGIC)
              .replace("{DELTA_SON}", DELTA_BITIS)
              .replace("{DELTA_TOPLAM}", str(_ds["toplam"]))
              .replace("{DELTA_MEK}", str(_ds["mekanizma"]))
              .replace("{DELTA_KAYIT}", str(_ds["kayit"]))
              .replace("{DELTA_DISI}", str(_ds["kapsam_disi"]))
              .replace("{DELTA_SKILL}", str(_ds["skill_dokunma"]))
              .replace("{DELTA_LINT}", str(_ds["lint_dokunma"]))
              .replace("{DELTA_TABLO}", delta_tablo()))
    return baslik + ekler


def main(argv):
    if "--kontrol" in argv:
        for etiket, yol, ne in DOSYALAR:
            tam = os.path.join(KOK, yol)
            print("%s  %s  %s  %d B" % (etiket, sha(tam), yol, os.path.getsize(tam)))
        print("ESER  %s  SKILL.md metadata.version" % eser_surum())
        print("LAB   %s  SURUM.md (eserin surumu DEGIL)" % surum())
        return 0
    if "--tek" in argv:
        # 12 Kasim 2026: burada da `datetime.date.today()` vardi — yani `--tek`
        # modu, `parca_adlari()` duzeltildikten SONRA bile gune bagli bir ad
        # yaziyordu. Ayni kusurun ikinci kopyasi; ad tur kimligine baglandi.
        isler = [(None, "DIS_DENETIM_TUR5.md")]
    else:
        p1, p2 = parca_adlari()
        isler = [(P1_ETIKET, p1), (P2_ETIKET, p2)]
    for secim, ad in isler:
        metin = uret(secim)
        yol = os.path.join(KOK, "docs", ad)
        with open(yol, "w", encoding="utf-8") as f:
            f.write(metin)
        print("YAZILDI: docs/%s" % ad)
        print("BOYUT  : %d B · satir %d" % (len(metin.encode()), metin.count("\n")))
        print("SHA256 : %s" % hashlib.sha256(metin.encode()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
