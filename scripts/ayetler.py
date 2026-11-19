#!/usr/bin/env python3
"""ayetler.py — ORNEKLEMIN TEK KAYNAGI (14 Kasim 2026, Z21c / C-#2).

NEDEN VAR: Ayni ayet listesi IKI Python dosyasinda ayri ayri duruyordu:
`snapshot_yenile.py` ve `meal_farki.py`. Orneklem 12 -> 16 yapildiginda
`meal_farki.py`'yi guncellemeyi UNUTTUM ve 4 yeni ayet **meal farki olcumune
hic girmedi** (olculdu: `C15k "ayet=12/12"`). `C15m` ayrismayi yakaladi ama
yakalama SANSA bagliydi: iki liste esit oldugu surece kimse fark etmez.

COZUM: liste TEK yerde tanimlidir; iki betik de buradan OKUR. Boylece
"ayrisma" diye bir durum olusamaz — iddia yapisal hale gelir, denetime
bagli kalmaz. `C15m` artik ek olarak su iddiayi olcer: iki betikte `AYETLER`
ATAMASI OLMAMALI (yalniz import).

SIRA ONEMLI: `ayet_ozet_kontrol.py --plato-tarama` n=3..N icin `SKILL.md`deki
FIZIKSEL sirayi kullanir. Yeni ayetler listenin SONUNA eklenir ki eski onek
korunsun ve olcum onceki kosuyla KARSILASTIRILABILIR kalsin (olculdu, Z20a:
yeni ayetler basa konunca plato 0.30-0.60 -> 0.30-0.50 dustu ve `C15l`
"daralma iddiasi kanitsiz" diye FAIL etti).
"""

AYETLER = [
    # --- ilk 6 (n=6 idi) ------------------------------------------------------
    "4:58",      # emanet
    "4:135",     # adalet + kendi aleyhine sahitlik
    "49:11",     # utandirmama
    "2:286",     # guc yetmeyeni yuklememe
    "42:38",     # danisma
    "3:159",     # danisma + tevekkul
    # --- [13 Kasim 2026, Z11] 6 -> 12 -----------------------------------------
    # NEDEN (olculdu): PLATO "hepsi gecti" demektir; 6 ayette bu neredeyse
    # zorunluydu (`PLATO: ZAYIF — n=6 < 12`).
    # 83:3 ALINMADI: olculdu — tr.diyanet 83:1/83:2/83:3 icin AYNI metni
    # donuyor (ucu de 150 bayt, sha 84ff35faa9); ikisini almak n'yi KOPYAYLA
    # sisirmek olurdu.
    "17:36",     # olcmeden iddia yok
    "83:1",      # olcude eksiltme/abartma
    "49:6",      # haber teyidi
    "2:282",     # kayit
    "39:53",     # umit
    "33:70",     # durust soz
    # --- [14 Kasim 2026, Z20] 12 -> 16 ----------------------------------------
    # NEDEN: n>12 plato davranisi ancak ayet EKLENEREK olculur (EK 90:
    # "veri engel degil, KARAR engel"). Secim kurali: mevcut 12'nin
    # KAPSAMADIGI ilke.
    "16:90",     # ihsan + haddi asmama
    "24:22",     # affetme / hosgoru (hata kabulu ilkesi)
    "31:17",     # sabir (ihtiyat ilkesi)
    "5:8",       # OFKE karsisinda adalet. 4:135 ile kelime ortusmesi var
                 # ("adalet") ama OZNE farkli: 4:135 kendi/yakinlarinin
                 # aleyhine, 5:8 baskasina duyulan ofke. Ortusme BILINEREK
                 # alindi, gizlenmiyor.
    # 4:59 ALINMADI: SKILL.md'de "bilerek eklenmedi" yazili (itaat ayeti,
    # danisma degil).
]
