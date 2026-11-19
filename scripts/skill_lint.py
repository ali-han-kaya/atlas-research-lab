#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SKILL.md makine kapisi — "her kural davranisi degistirmiyorsa kural degildir".

NEDEN VAR: 3 Kasim 2026 alt ajan denetimi (KANIT DENETCISI rolu) sunu olctu:
hicbir betik SKILL.md'yi okumuyordu, yani dosyanin butun kapilari birer
cumleydi; "bozdum, kirmizi yandi" demek yeterliydi. Bu betik o deligi kapatir.

KONTROLLER (her biri exit koduna baglanir)
  C1  frontmatter var mi, YAML alanlari spec'e uyuyor mu
  C2  zorunlu bolumler (§0 §1 §3 §7 §8) metinde gercekten var mi
  C3  ZORUNLU listesi ile govdedeki basliklar tutarli mi
  C4  yasak cumle blogu var ve dolu mu
  C5  yasak cumleler GOVDEDE gecmiyor mu (blok haric)
  C6  satir sayisi <= 500 (agentskills.io onerisi)
  C7  homoglif/zerewidth yok (elle yazim tuzagi; araliklar genisletildi)
  C8  §12 DOGRULAMA blogu ve exit kodu alani var mi
  C9  terminal durum listesi tam mi
  C10 altin cumleler DURUYOR mu (yer + inkar eki + birebir)
  C11a §8.1 manifestinde SORU_BUTCESI satiri ve 4 alani duruyor mu
  C11b §7.4 geri donus kurali P1 -> K2 olarak duruyor mu
  C11c §6.1 atif hedefleri (§8.1 alan tanimi + §3.3/3 kaynak yolu) duruyor mu
  C11d §10 I6 kimligi (kaynagi AGENTS.md, I1-I9) duruyor mu
  C11e §7.1 BLOK_GECERSIZ <-> ACIK_SORU ayrimi duruyor mu
  C12a her §A.B atfinin hedefi gercekten tanimli mi (bolum + alt bolum)
  C12b her §A.B/N madde numarasi gercekten var mi
  C13a-C13r v1.4.42 TUR 5 duzeltmelerinin capalari (18 kapi)
  C13s     sunnah.com hadis metinlerinin olculdugu kaydi (2026-11-07)
  C13t     INJECTION_ATTEMPT tasiyici + bitti sarti (2026-11-07)
  C13u     `sir` sema gocu — geriye uyum kurali (2026-11-07)
  C13v     fazladan kapanis parantezi yok (D1 sinifi, 2026-11-07)
  C13w     sure adi imla rejimi olculmus halde (D13, 2026-11-07)
  C13x     kontrol sayisi tek kaynak, GOMULU sayi yok (D10, 2026-11-07)
  C13y     3.3 MOD etiketi olcumden gelir (D22, 2026-11-07)
  C13z     hadis olcumu §12 alanli, C13z-a calistirmali (D2, 2026-11-07)
  C14a     HTTP 403 olcumu komutlu (D4/D21, 2026-11-07)
  C14b     kunye uc tarihi birlikte (D3, 2026-11-07)
  C14c     elle tarama §12 karsiligi (D18, 2026-11-07)
  C14d     MOD-B kimlik listesi istisnasi (D11, 2026-11-07)
  C14e     [sir] isaretleyen insan (D14, 2026-11-07)
  C14f     esik oz-denetimle acilmaz (D17, 2026-11-07)
  C14h     REDDEDILENLER iki alt turu ayri sayar (D19, 2026-11-07)
  C14i     durum.json gocu gercekten kosar (kalem 7, 2026-11-07)
  C14j     goc bozuk tipde fail-closed (kalem 7, 2026-11-07)
  C14k     INJECTION_ATTEMPT sarti calistirmali (kalem 8, 2026-11-07)
  C14l     sunnah.com birebir aynilik calistirmali (kalem 2, 2026-11-07)
  C14m     Turkce ayet ozetleri 9 MEAL ile olculdu (kalem 1, 2026-11-07)
  C14q     hadis TURKCE metni bagimsiz kaynakla olculdu (2026-11-07)
  C14r     hadis id eslesmesi ARAPCA + negatif kontrol (2026-11-07)
  C14n     cevrimdisi olcum + snapshot yasi bilinir (kalem 2/3, 2026-11-07)
  C14o     gercek durum.json semaya uyar (kalem 3, 2026-11-07)
  C14p     esik PLATO icinde + plato TANIMDAN bagimsiz (OLCULMEYEN 2/4, 2026-11-07)
  C14g     DURDURULAN anlami gloslu (D7, 2026-11-07)
  C14s     markdown vurgu butunlugu — literal * yok (D1 sinifi, 2026-11-08)
  C14t     gomulu sayac sozcukle de yazilsa yasak (D10b, 2026-11-08)
  C14u     ARAC_DEGISTI/KIMLIK_DEGISTI olcumu + taban (D11, 2026-11-08)
  C14v     BAGIMSIZLIK: VAR kanit ister (aile+dosya+sha) (D17, 2026-11-08)
  C14w     metindeki her betik diskte var + compatibility kumeyi ilan eder (D21, 2026-11-08)

Kullanim:  python3 scripts/skill_lint.py [SKILL.md]
           python3 scripts/skill_lint.py --metin <teslim-dosyasi>
Exit: 0 = temiz · 1 = ihlal · 2 = dosya okunamadi / olcum yapilamadi
NEDEN 2.46: `C14p` canli kosuyordu — `api.alquran.cloud`'a 12 HTTPS cagrisi.
OLCULDU: bir kosuda `FAIL ... timed out after 120 seconds` (betik tek basina
`real 127,80 s`, `user 0,86 s` = is yok, bekleme var), ayni gun sonraki kosuda
`PASS`. Yani kapinin hukmu ucuncu tarafin gecikmesine bagliydi — AG'LI KAPI
SAHTE KAPIDIR. Kardesleri `C14m`/`C14n` zaten `SNAPSHOT_ONLY=1` ile kosuyordu.
Artik `C14p` de: cikti 32 satir BIREBIR ayni, sure `127,80 s -> 0,06 s`.
FAIL-CLOSED kaniti (M77): snapshot silinince eski hal `PLATO ... 6/6 DEGISMIYOR`
diyor ve GECERDI (cunku `ceviri()` hatasi `continue` ile yutuluyordu);
`kapsam_matrisi` artik `MEAL_EKSIK` bildirir, kapi FAIL eder — olculdu.
IKINCI KUSUR (12.25): yeni blokta `_eksik` adi kullanilinca `_kosul_parmak`
modul duzeyi tanimlari topladigi icin KOMSU kapi `C14o`'nun parmak izi de
degisti (`79503494cd38 -> 1b5b41585545`). Ad `_eksik_meal` yapildi; olculdu:
yalniz `C14p` degisti, `C14o` ayni.

SURUM: 2.67 (15 Kasim 2026) — C15i sozlesmesi: siniflandirma projenin KENDI
  hukmunden gecer (`durum_belirle` + `proje_hukmu` bagI denetlenir);
  `PASS-PENDING*` artik YESIL sayilmaz.
  OLCULDU (15 Kasim 2026, Z46): `lab_full` projeyi yalniz rc ile sinifliyordu;
  `silat-makale` kendi kapisinda `PASS-PENDING-ETHICS` verirken devir
  belgesi yazilinca rc=0 oldu ve panoda YESIL yanacakti. C15i eski deseni
  (`'YESIL' if rc == 0 else 'KIRMIZI'`) aradigi icin hakli olarak FAIL etti;
  kapi KORLESTIRILMEDI, yeni sozlesmeye gore SIKILASTIRILDI: (a) iki fonksiyon
  var, (b) `PASS-PENDING` oneki duruyor, (c) `projeler_tara` ikisini de
  cagiriyor. Mutasyon M46/M47 ile yakildi. Eski `SURUM: 2.66` satiri silinmedi
  (I6) — asagida duruyor.
  OLCULDU (15 Kasim 2026, Z45d): gercek arsivin gecici kopyasinda 1 bayt
  bozuldu (bayt sayisi AYNI, sha baska). Kapı FAIL etti — dogru — ama ayrinti
  satiri kendi kendisiyle CELISTI: "arsiv=VAR·16 dosya dogrulandi ... HATA:
  arsivde BOZUK 1: V146 tur 2.md sha256". Sayi `len(manifest) - len(eksik)`
  idi, yani BEKLENEN dosya sayisi; bozuk dosya dusulmuyordu. Artik
  `len(manifest) - len(eksik) - len(bozuk)` ve etiket "N/M dosya dogrulandi".
  Ayni kosuda 15/16 yazar. Ikinci kusur ayni yerde: "VAR" etiketi ile
  "dogrulandi" sozu, dogrulanmamis dosya varken de basiliyordu.

SURUM: 2.65 (15 Kasim 2026) — Z44: C17 (2) katmani SENTETIK FIXTURE ile sinanir.
  DUZELTME (I6, silinmedi): asagidaki 2.63 satirindaki "marj 60x" ARTIK YANLIS.
  Olculdu (14 Kasim 2026): n=12 -> 16 yapilinca dogru hal 1,0 s -> 1,7 s oldu
  ve marj 60x -> 35,3x'e dustu; hicbir sey bunu soylemedi (sessiz erime).
  Artik: esik = sqrt(bekleme * bozuk_taban) = sqrt(1,7 * 457,2) = 27,9 s
  -> iki yonde 16,4x. Ayrica (a) MARJ YETERSIZ (bant < 100x),
  (b) REFERANS BAYAT (>3x: baska makine/kod buyumesi -> YENIDEN OLC),
  (c) esik bozuk tabana cok yakin -> uc kontrol. M129-M132 kanitladi.
  Esik ciktiya yazilir: `sure=1.7s·esik=27.9s·marj=16.4x`.
SURUM: 2.63 (14 Kasim 2026) — Z19: C15l sure esigi MARJ ile gerekcelendi.
  _PLT_SURE_ESIK=60.0 · gercek 1.0s (3 tekrar) -> marj 60x · M113 kanitladi.
  [BAYAT — 2.64'te duzeltildi: marj 35,3x'e erimisti; sabit kaldirildi.]
  Yavas makinede esik ASILIRSA: sil degil, gerekceli yukselt.
SURUM: 2.62 (13 Kasim 2026) — Z18e: n>12 VERI SINIRI (sentetik dolgu RED).
  TARAMA: n_max_veri= + monoton=; C15l ikisini de ister (M111/M112).
SURUM: 2.61 (13 Kasim 2026) — Z18d: C15l 'agsiz' iddiasi YANLISTI, duzeltildi.
  plato alt kosulari canliyi deniyordu (500s). SNAPSHOT_ONLY=1 -> 1.1s.
  C15l sure<=60s ister (M110: 457.2s -> FAIL). Lint 507s -> 20s.
SURUM: 2.60 (13 Kasim 2026) — Z18c: _sad3 harf denegi (iki yonlu).
  ESITLENMELI 5 cift + AYRI KALMALI 5 cift; ilk denemem totolojiydi, kendim yaktim.
SURUM: 2.59 (13 Kasim 2026) — Z18b: plato gecici dizin temizligi.
  --plato-tarama try/finally + rmtree; C15l tmp-sizinti==0 ister (M106/M107).
SURUM: 2.58 (13 Kasim 2026) — Z18a: sablonlar ARTIK ZORUNLU (C15j).
  41 cagrinin hepsine timeout eklendi; 142/142 + 174/174 KORUNDU (olculdu).
  sablon-ihlal 41 -> 0; >0 ise FAIL (M105 kanitladi).
SURUM: 2.57 (13 Kasim 2026) — Z17: olculmeyen B kalemleri (7 adet).
  #7  C15l: PLATO n=3..12 taramasi; secili esik plato ICINDE mi (M100).
  #8  C14u joker listesi 3 -> 11 dize (M102: 'all' jokerini eski liste KORDU).
  #9  C15g _sad3 ayirt ediciligi oz-test (M103: rakam silen normalizasyon KOR).
  #10 C15j kapsami scripts/tests/ alt dizini (M104); sablonlar OLCULUR+raporlanir.
  #4  C15k snapshot ICERIGI sha ile (M96b) — Z17a.
  #5 ve #6 KOD GEREKMEDI: C14x (M97) ve C15g hadis deseni (M98) zaten kapatiyor.
SURUM: 2.56 (13 Kasim 2026) — Z16c: C15k meal_farki olcumu KAPI oldu.
Olculdu (EK 81): olcum vardi ama her kosuda yapilmiyordu; aga bagimliydi.
Artik once canli, olmazsa sha'li snapshot; `--snapshot` agsiz + KAYNAK satiri.
M94 (snapshot dosyasi silindi) FAIL eksik=1; M95 (ayet eklendi, veri yok)
FAIL ayet 12/13. Kapı 91->92.
SURUM: 2.55 (13 Kasim 2026) — Z16b: C15j timeout VARLIGI degil DEGERI de denetler.
Olculdu (M93): `timeout=0.001` eski halde GECIYORDU (varlik vardi). Asgari
esik 10 s; oz-test uc ornekle (yok / iyi / kucuk) ayirt eder.
SURUM: 2.54 (13 Kasim 2026) — Z16a: C15g BOS KUME artik FAIL. Olculdu (M92a):
ARZ ayet tablosunun bicimi bozulunca desen BOS donuyordu ve kapi PASS
veriyordu (bos == bos). M92b ayni mutasyonu `AYET DESENI BULUNAMADI` ile
yakalar. Ayni sinif hadis desenine de uygulandi.
SURUM: 2.53 (13 Kasim 2026) — Z15: C15g AD denetimi. Olculdu (M89): JSON'da
`49:6`->`50:1` (sayi 11 kalir) C15g PASS veriyordu — sayi tutmak adi tutmak
degil. M90 ayni mutasyonu yakalar; M91 liste buyutmeyi sayi tarafindan yakalar.
SURUM: 2.52 (13 Kasim 2026) — Z14: subprocess sinifi tarandi (sira 8).
33 cagri, ucuncu parti YOK, shell=True YOK; 2 cagrida `timeout=` YOKTU
(kapatildi). Yeni kapi C15j: her `.run()` timeout tasir + oz-test ayirt
edici (M88). Kimlik C15g CAKISTI (ARZ blogu) -> C15j.
SURUM: 2.51 (13 Kasim 2026) — Z13: `--kabul` JOKER korkulugu artik OLCULUYOR.
C14u `*`/`ALL`/`...` joker'lerini dener: hepsi REDDEDILMELI ve taban DOSYASI
degismemeli (rc + sha). Olculdu: arac joker'i kabul eder hale getirilince
C14u FAIL (M87).
SURUM: 2.50 (13 Kasim 2026) — Z10: yol argumani sinamasi C14q/C14r'de;
iki hadis betigi bayrak-once sirasinda yolu yok sayiyordu (duzeltildi).
SURUM: 2.49 (13 Kasim 2026) — Z9: PLATO sayisi olcumden turetiliyor + n ilani;
C14p KENDI MUTANTINI goruyor (fail-OPEN yol argumani kusuru kapatildi).
SURUM: 2.48 (12 Kasim 2026) — Z7: snapshot DOSYA BAZLI tarih + YAS_DOSYA
+ MTIME_KAYMASI; C14n bunlari zorunlu tutar.
SURUM: 2.47 (12 Kasim 2026) — Z4: C14q/C14r CEVRIMDISI (ayni sinif: hadis kapilari hala canliya gidiyordu).
SURUM: 2.46 (12 Kasim 2026) — Z1: C14p CEVRIMDISI kostu (ag bagimliligi
kalkti) + MEAL_EKSIK fail-closed + komsu kapi parmak izi kirlenmesi
duzeltildi (_eksik -> _eksik_meal). SURUM 2.45 (12 Kasim 2026) — Y3: numara ayiklama KALIBI KALKTI, YIGIN
FARKINDA kural geldi (25 -> 1).
NEDEN: Y0'in duzelttigi kalip `(?<![\\w.(])\\d\\)` hala 26 MESRU kapanisi
yiyordu (`§2)`, `rc=0)`, `3/4)`, `Hucurat 49:6)`, `sayac 1→2)`, `(kod: 0)`);
32 eslesmenin yalniz 6'si gercek numaralandirmaydi. Sonuc: 24 SAHTE acik.
Kural: ')' YIGIN BOSKEN ve rakamin ardindan geliyorsa numaralandirma,
YIGIN DOLUYSA kapanis. Olculdu: HIC ayiklama (1, 8) · MEVCUT kalip (25) ·
YIGIN FARKINDA (1, 0). Kalan tek acik GERCEK borc: SKILL.md satir 323.
onceki 2.44 (12 Kasim 2026) — Y2: kod blogu metin degil + kapanmamis
backtick fail-closed.
NEDEN: `_parantez_tara` yalniz satir ici kod araligini siliyordu; ``` blogunun
ICINDEKI parantezler metin sayiliyordu. Olculdu (SKILL.md): 7 blogun hepsi
dengeli, sayi degismedi (25) — ama dengesiz bir ornek sayaci sessizce
kaydirirdi. Ikincisi daha agir: satir ici aralik KAPANMAZSA `[^`\\n]*`
kalibi metnin geri kalanini YUTAR ve parantez sayaci sessizce kayar. Bu,
Y0'in kardesidir (ayni sinif: mesru olmayan silme). Artik (a) fence bloklari
tamamen cikarilir, (b) kalan backtick sayilir; sifir degilse `C19` FAIL eder
ve `C16`nin `paren_acik` olcumu fail-closed davranir (beyanla karsilastirmaz).
onceki 2.43 (12 Kasim 2026) — Y0: parantez sayaci DUZELTILDI (42 -> 25).
NEDEN: `_parantez_tara` icindeki numara-ayiklama kalibi `(?<![\\w(])\\d\\)`
noktayi haric tutmuyordu; `§0.7)` dizisindeki `7)` 'numara' sanilip
KAPANIS PARANTEZI ile birlikte siliniyordu. Sonuc: sayi 42 cikiyordu,
dogrusu 25. Fark tam olarak `§X.Y)` sayisi kadar: 17. Yani `C19` ve yeni
`S10` bir gun boyunca YANLIS sayiyi dogruladi. Kalip `(?<![\\w.(])\\d\\)`
oldu: `§0.7)` korunur, `1) secenek` hala ayiklanir. M61 (dengeli
`(bkz §1.2, §3.4)` -> PASS) ve M62 (eski kalip geri -> FAIL 42) bunu
kanitlar. Ayrica `_kapsam_disi` madde 1 de bayatti (Y1): §3'u `C17`
EK 61'den beri olcuyor.
onceki 2.42 (12 Kasim 2026) — C16: S10 eslesmeyen ACILIS parantezi (#2).
NEDEN: `C19` bu sayiyi iki turdur RAPORLUYOR ama GATE ETMIYOR (kapali
kumeyi yanlis yakmamak icin). Raporlanan ama hukme girmeyen sayi
SESSIZCE oynayabilir — D10'un ayni sinifi. #2 onu `C16` beyani yapar:
sayi 42, sessiz degisim imkansiz. `C19` ile `C16` AYNI fonksiyonu
kullanir (`_parantez_tara`) — kopya kod ayrisirsa kapi yanlis seyi dogru
sayar. M57 kaniti: SKILL.md'ye kapanmamis '(' eklendi -> C19 PASS,
C16 FAIL (beyan 42, olculen 43). M58 negatif kontrol: dengeli parantez
-> C16 PASS.
onceki 2.41 (12 Kasim 2026) — C17: §7 esleme sayaclari manifestoya bagli (#1).
NEDEN: `TUR_HARITASI` §7'deki "esleme kaniti 3/16 · `Paket:` satiri 1/16 ·
`Hedef paket:` dahil 2/16" satiri IKI KEZ yanlis cikmisti (EK 59/60: "12/16"
yaziyordu) ve HIC KAPISI YOKTU — her tur elle olculdu. Ayni sinif D10'un
koku: kapisiz sayac bayatlar. Cozum: `ARSIV_MANIFESTOSU.json` zaten arsivi
okuyor; dosya basina `paket_adi` · `paket_satiri_bas` · `paket_her` alanlari
eklendi, `_olculdu` toplamlari DOSYA sayisidir. `C17` uc sayaci manifestla
karsilastirir. OLCUM TUZAGI: ayni sayilar §7'nin ALTINDAKI alinti blogunda da
geciyor; kapi once maddeyi bulur, sonra `>` ile baslayan ilk satirda KESER —
tum belgede arama yanlis yeri bulabilirdi.
onceki 2.40 (12 Kasim 2026) — C19: parantez dengesi + `_` vurgusu (D1).
NEDEN: DIS DENETIM TUR 11'de 6/17 model D1'i KAPANMADI saydi; lab olctu ve
hakli buldu. `C14s` yalniz `*` ariyor; `C13v` capasi literal `)*)` — ciplak
`))` ikisini de yakmiyor (olculdu). `C19` iki YOKLUK olcumu: eslesmeyen
kapanis parantezi = 0 · `_` vurgu = 0. Sinir: eslesmeyen acilis = 42
(cok satirli parantezler), gate edilmiyor, raporlaniyor.
onceki 2.39 (12 Kasim 2026) — C18: kapi parametreleri gomulu yazilmaz.
NEDEN: DIS DENETIM TUR 11 (17 model). 6 model `SKILL.md` §7.3'teki `C14t-a`
parametrelerinin bayat oldugunu soyledi; lab olctu ve HAKLI buldu — besi de
bayat (35->58 · 1680->2400 · %98.1->%98.7 · 0/19->0/40 · 3->5). D10'un
BESINCI tekrari. Onceki dort duzeltme SAYAC kapisi uretmisti; `C18` ilk kez
KAPININ KENDI PARAMETRESINI baglar. Ayrica `C14t-a` etiketi de bayat sayi
tasıyordu ('25 bilinen yazimi', canli 58) — kaldirildi.
onceki 2.38 (12 Kasim 2026) — C16'ya tur sayaclari (S6-S9).
NEDEN: `§0` "10 tamamlandi · 1 bekliyor" ve `§4` "10 tur + 1 bekleyen"
kapisizdi. Gerekce `DEVIR-2026-11-08-0931.md:5938`: "§4 tablosunda 10 + 1 ✓".
Ayni sayi IKI yerde yazili (S6/S7 §0 · S8/S9 §4 basligi) — C15b dersi:
ilk uyusma otekini golgelemesin, HER biri ayri beyan.
Olcum: §4 tablosu 11 satir -> 10 tamamlanan + 1 BEKLEYEN.
onceki 2.37 (12 Kasim 2026) — C17 ARSIV MANIFESTOSU eklendi; C16 tarama araligi genisledi.
NEDEN: `TUR_HARITASI` §3 sayaclari (16 dosya · 1 865 272 B · 119 `MODEL:`)
DEPO DISI kaynaga bagliydi ve hic kapisi yoktu. `docs/ARSIV_MANIFESTOSU.json`
(4.8 KB) depoya girdi; §3 sayilari manifestoyla, manifesto arsivle dogrulanir.
Arsiv yoksa FAIL degil CALISTIRILAMADI (AGENTS.md: her kosu BLOCKED yasak).
Ayrica §3 `^MODEL:` taniminin 2 girintili satiri atladigi kayda gecirildi
(119 vs 121; §3 sayisi degistirilmedi, tanimi yazili).
onceki 2.36 (12 Kasim 2026) — C16'ya `paket_serisi` olcum tipi + beyan S5.
NEDEN: `TUR_HARITASI` §0 "12 paket" sayaci KAPI DISINDAYDI (beyan edilmemis
gomulu sayac — D10 sinifi). Aralik tanimi (v1.3.3..v1.4.27) `C16` icinde
kodlanir: diskteki 14 surumlu dosyadan 3'u (v1441/v1443/v1444) aralik
DISINDA; 11 + surumsuz `k1_denetim_paket.md` = 12. Gerekce
`DEVIR-2026-11-08-0931.md:5955` (aralik=12 · dosya toplami=15) — I4:
kusur ilan etmeden once gerekce arandi, sayi DOGRU cikti; eksik olan kapıydı.
onceki 2.35 (12 Kasim 2026) — C16 BEYAN EDILMIS SAYAC eklendi.
NEDEN: C15b gomulu sayaclari denetlemiyor. `TUR_HARITASI`nin tamami
tarandi (§0 §1 §2.1-2.4 §3 §4 §5 §6 §7) ve dort turda bulunan gomulu
sayaclarin HICBIRINI kapi gormedi (§3 "128 MODEL:" -> 119 · §6 madde
sayisi · §7 "12/16" · §7 "tur 10 (18 madde)"). Hepsi ELLE cikti.
KAPSAM DAR: yalniz `docs/SAYAC_BEYANLARI.json` icinde BEYAN EDILEN
sayilar; "tum sayilar" denetlenemez (SURUM.md'de 14 612 ifade, cogu
tarihsel kayit — gerekce C15f'te ayni). Kalip 0 eslesme verirse FAIL:
sessiz kapi yasak. Kanit: M30/M31/M32 (EK 59).
onceki 2.34 (11 Kasim 2026) — C14y DISK UYUSMASI eklendi. Olculdu (R1): uretici
metni degistirilip paket yeniden URETILMEYINCE C14y PASS rc=0 veriyordu — cunku
yalniz CANLI URETIMI denetliyor, `docs/DIS_DENETIM_TUR4_P*.md` dosyalarini HIC
OKUMUYORDU. Denetciye bayat paket gidebilirdi. Sabahki yakalama TESADUFTU
(basliktaki lint surumu degismisti; govde degisse gorulmezdi).
onceki 2.33 (11 Kasim 2026) — SURUM DISIPLINI: C1e IKI DOSYAYA genisletildi
(SKILL.md + bu dosya). Olculdu: bu dosya 10 commit degisti (`d9ed7ac` …
`ac9abe6`), `SURUM:` 2.32 SABIT kaldi (8 Kasim) — ayni kusur, ikinci dosya.
Taban: scripts/tests/lint_surum_taban.json. Yeni kimlik ACILMADI (I5).
onceki 2.32 (8 Kasim 2026) — 3. tur: C14s (vurgu SINIFI), C14t (sozcukle sayac),
C14u (ARAC/KIMLIK olcumu + taban), C14v (bagimsizlik kaniti), C14w (betik kapsami).
onceki 2.31 (7 Kasim 2026) — C13x KURALA cevrildi: gomulu "N kontrol" sayisi
yasak (R: regex capasi). D10 ikinci kez tekrarlamisti (41 -> 46 -> 67).
onceki 2.30 (7 Kasim 2026) — C14r'ye NEGATIF KONTROL eklendi: esik 0.50 ust
kenarda (marj 0.03), asil kanit ayrIm (0.531 vs 0.000).
onceki 2.29 (7 Kasim 2026) — C14r: hadeethenc id eslesmesi ARAPCA obek
ortusmesiyle kanitlandi (67 kontrol; ilk olcut yanlisti — rivayet farki yakalandi).
onceki 2.28 (7 Kasim 2026) — C14q: hadis Turkce metni BAGIMSIZ kaynakla olculdu
(66 kontrol; ilk olcum Buhari 39'da 1/9 SAPMA buldu, metin resmi ceviriyle degistirildi).
onceki 2.27 (7 Kasim 2026) — C14p: esik PLATO icinde mi (65 kontrol; esikler insan
secimiydi, duyarlilik taramasi eklendi — OLCULMEYEN kalem 2).
onceki 2.26 (7 Kasim 2026) — C14o: gercek durum.json semaya uyar (64 kontrol;
goc yalniz test dosyasinda kosmustu, labta gercek durum.json YOKTU — kalem 3).
onceki 2.25 (7 Kasim 2026) — C14n: cevrimdisi olcum calisir (snapshot sha256 ile
sabit; 63 kontrol). onceki 2.24 (7 Kasim 2026) — C14m: Turkce ayet ozetleri Diyanet ile olculdu (62 kontrol;
"serbest ozet" hic olculmemisti — kalem 1).
onceki 2.23 (7 Kasim 2026) — C14l: sunnah.com birebir aynilik calistirmali, ag yoksa
FAIL (61 kontrol; iddia bir tur OLCULMEDI idi — kalem 2).
onceki 2.22 (7 Kasim 2026) — C14k: INJECTION_ATTEMPT sarti calistirmali (60 kontrol;
sart yaziliydi ama elle denetleniyordu — kalem 8).
onceki 2.21 (7 Kasim 2026) — C14i/C14j: `durum.json` gocu GERCEKTEN kosar ve
bozuk tipde fail-closed (59 kontrol; goc kurali yaziliydi ama hic calistirilmamisti).
onceki 2.20 (7 Kasim 2026) — C14h: REDDEDILENLER iki alt turu ayri sayar (D19).
onceki 2.19 (7 Kasim 2026) — C14f: esik oz-denetimle acilmaz (D17) · C14g: DURDURULAN glosu (D7).
onceki 2.18 (7 Kasim 2026) — C14c/d/e: D18 elle tarama §12 karsiligi · D11 MOD-B kimlik
istisnasi · D14 [sir] isaretleyen insan (54 kontrol).
onceki 2.17 (7 Kasim 2026) — C14b: kunye uc tarihi birlikte gosterir (51 kontrol).
onceki 2.16 (7 Kasim 2026) — D15: INJECTION_ATTEMPT tek sozdizimi (`=`), C13t 3->3 + ':' yokluk capasi (50 kontrol).
onceki 2.15 (7 Kasim 2026) — C14a: HTTP 403 olcumu komutlu (50 kontrol).
onceki 2.14 (7 Kasim 2026) — C13z: hadis olcumu hem §12 alanli hem CALISTIRMALI
(49 kontrol: C13z metin + C13z-a calistirmali; D2'nin "sayi var, komut yok"
kusuru; mutasyon 1/1).
onceki 2.13 (7 Kasim 2026) — C13y: 3.3 MOD etiketi olcumden gelir (47 kontrol).
onceki 2.12 (7 Kasim 2026) — C13x: kontrol sayisi tek kaynak, bayat sayi yok (46 kontrol).
onceki 2.11 (7 Kasim 2026) — C13w: sure adi imla rejimi olculmus halde (45 kontrol).
onceki 2.10 (7 Kasim 2026) — C13v: fazladan kapanis parantezi yokluk capasi
(44 kontrol; D1 gerilemesi `a588c46`'da geri gelmisti, 18/18 model kacirdi; mutasyon 1/1).
onceki 2.9 (7 Kasim 2026) — C13u: `sir` sema gocu kurali (43 kontrol; mutasyon 2/2).
onceki 2.8 (7 Kasim 2026) — C13t: `INJECTION_ATTEMPT` tasiyici + bitti sarti
(42 kontrol; mutasyon 2/2: sart silindi -> FAIL · manifest alani silindi -> FAIL).
onceki 2.7 (7 Kasim 2026) — ALINTI kurali: `--metin` artik ters tirnak icindeki ve
ayni satirda `IHLAL` jeti tasiyan gecisi kanit kaydi sayar (saymaz, ama YAZAR);
ters tirnak disinda ya da markersiz ayni cumle hala IHLAL (m1/m2/m4 olcumu).
onceki 2.6 (7 Kasim 2026) — C13s: sunnah.com hadis olcum capasi + C13a yeni metne cekildi (41 kontrol); onceki 2.5 (7 Kasim 2026) — C13a-C13r: v1.4.42 TUR 5 duzeltmelerine capa (mutasyon 0/18 dersi); onceki 2.4 (6 Kasim 2026) — C12a/C12b capraz atif cozunurlugu eklendi; onceki 2.3 (6 Kasim 2026) — C11c/C11d/C11e (kalan 3 capa, mutasyon 5/5); onceki 2.2 (6 Kasim 2026) — C11a/C11b yapisal capalar eklendi (mutasyon M-v1437..M-v1441 dersi); onceki 2.1 (4 Kasim 2026) — 4 Kasim 2026 denetim delikleri kapandi; asagida
her duzeltmenin kendi DUZELTME NOTU vardir (I6: eski notlar silinmez).
"""
import io
import json
import os
import hashlib
import re
import sys
import unicodedata as _ud

# ==========================================================================
# Ortak metin normalizasyonu — Turkce karakterleri katlar.
# DUZELTME NOTU (4 Kasim 2026, M18): onceki surum yalnizca NFC + lower yapiyordu;
# "her sey hazir" kalibi "her şey hazır" metninde KACIYORDU (olcum: rc=0).
# Artik İ/I/ı→i · Ş/ş→s · Ğ/ğ→g · Ü/ü→u · Ö/ö→o · Ç/ç→c katlanir + NFKC.
# ==========================================================================
_TR = {'İ': 'i', 'I': 'i', 'ı': 'i', 'Ş': 's', 'ş': 's', 'Ğ': 'g', 'ğ': 'g',
       'Ü': 'u', 'ü': 'u', 'Ö': 'o', 'ö': 'o', 'Ç': 'c', 'ç': 'c', 'Â': 'a', 'â': 'a'}


def _katla(s):
    # DUZELTME (5 Kasim 2026, F6-P1#4): gorunmez karakterler NFKC'den SONRA da
    # kalabildigi icin (ZWSP, soft hyphen, word joiner, BOM) once BOSLUKLA
    # degistirilir (SILINMEZ — silinirse "her\u200Bse\u200Bey hazir" tek kelime
    # "hersey hazir" olur ve C5'in kelime eslesmesi KACAR; olcum: bypass).
    for _gor in ('\u200b', '\u200c', '\u200d', '\u2060', '\ufeff', '\u00ad', '\u2024'):
        s = s.replace(_gor, ' ')
    for a, b in _TR.items():
        s = s.replace(a, b)
    s = s.replace('**', '').replace('`', '').replace('*', '')
    s = s.replace('\u2019', "'").replace('\u2018', "'")
    s = _ud.normalize('NFKC', s)
    return ' '.join(s.split()).lower()


def _bolumler(metin):
    """`## N.` basliklarini ve govde metinlerini dondurur: {no: katli govde}."""
    parcalar = re.split(r'^(## \d+\..*)$', metin, flags=re.M)
    sonuc = {}
    suanki = None
    for p in parcalar:
        m = re.match(r'^## (\d+)\.', p)
        if m:
            suanki = m.group(1)
            sonuc.setdefault(suanki, '')
        elif suanki:
            sonuc[suanki] += p
    return {k: _katla(v) for k, v in sonuc.items()}


# ==========================================================================
# --metin modu
# DUZELTME NOTU (4 Kasim 2026): (a) kalip listesi artik DONMUS'tur — SKILL.md
# blogundan bir kalip silinirse kapi ZAYIFLAMAZ (eski surum kendi kalibini
# sildigi icin C4 >=5 esigini kandiriyordu, olcum: rc=0 kalmisti);
# (b) Turkce karakter katlamasi (M18); (c) rc=2 sozlesmesi: dosya okunamiyorsa
# traceback/rc=1 DEGIL, duz mesaj + rc=2 (eski surum FileNotFoundError ile
# rc=1 uretiyordu — sozlesme ihlali).
# ==========================================================================
# DONMUS KALIP LISTESI — SKILL.md blogunun asgari icerigi. Buraya eklenen
# kalip SKILL.md'den silinse bile taranmaya devam eder.
DONMUS_KALIP = [
    'her sey hazir',
    'teslime hazir',
    'sorunsuz calisiyor',
    'tamamen tamamlandi',
    'muhtemelen calisir',
    'buyuk ihtimalle dogru',
    'sorun gorunmuyor',
    'gerekli tum kontroller yapildi',
]

if len(sys.argv) > 2 and sys.argv[1] == '--metin':
    hedef = sys.argv[2]
    if not os.path.isfile(hedef):
        print('SONUC: OLCULEMEDI — dosya yok: %s' % hedef)
        sys.exit(2)
    try:
        T = io.open(hedef, encoding='utf-8').read()
    except Exception as e:
        print('SONUC: OLCULEMEDI — okunamadi: %s (%s)' % (hedef, e))
        sys.exit(2)
    kaynak_yolu = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SKILL.md')
    blok_kaliplar = []
    try:
        kaynak = io.open(kaynak_yolu, encoding='utf-8').read()
        bb = re.search(r'<!-- YASAK_BASLANGIC -->(.*?)<!-- YASAK_BITIS -->', kaynak, re.S)
        blok_kaliplar = [s.strip() for s in bb.group(1).split('\n') if s.strip()] if bb else []
    except Exception:
        blok_kaliplar = []   # SKILL.md yoksa donmus liste yine calisir
    # donmus + blok birlesimi; bloktan silinmis kalip donmus listede kalir
    silinen = [k for k in DONMUS_KALIP if k not in [b.lower() for b in blok_kaliplar]]
    kaliplar = sorted(set([k.lower() for k in DONMUS_KALIP] + [b.lower() for b in blok_kaliplar]))
    print('METIN    :', hedef)
    print('KALIP    : %d (donmus %d + blok %d)' % (len(kaliplar), len(DONMUS_KALIP), len(blok_kaliplar)))
    if silinen:
        print('  UYARI  SKILL.md blogundan silinmis kalip (donmus liste koruyor): %s' % silinen)
    # DUZELTME (5 Kasim 2026, F6-P1#2): SKILL.md'nin KENDI yasak-liste blogu
    # taranmamali (§11: "Kapsam: teslim metni (bu bolum haric)"). Eski surum
    # kendi blogunu da tarayip SKILL.md'ye karsi rc=1 uretiyordu — yani kapinin
    # kendi kendine yaptigi tarama yanlisti. Artik blok metinden CIKARILIR.
    T = re.sub(r'<!-- YASAK_BASLANGIC -->.*?<!-- YASAK_BITIS -->', '', T, flags=re.S)
    # Ters tirnak, `_katla` tarafindan SILINIYOR; span sinirlarini kaybetmemek icin
    # once gorunmez isaretle isaretlenir (asagidaki ALINTI kurali bunu kullanir).
    nT = _katla(T.replace('`', '\u0001'))
    hit = []
    # DUZELTME (4 Kasim 2026, M18b): --metin de artik C5 ile AYNI olcumu yapar —
    # kelime siniri + inkar istisnasi. Eski surum `k in nT` alt-dize ariyordu;
    # "her sey hazirlanmadi" masum cumlesi IHLAL uretiyordu (olcum: rc=1).
    _INKAR_M = re.compile(r'\s*(?:degil\w*|lanmadi|olmadi|yoktur|kalinmaz|yazilmaz)\b')
    # DUZELTME NOTU (7 Kasim 2026, TUR 6 OLCULMEYEN #5): kapi, kendi ciktisini
    # ALINTILAYAN kaydi da ihlal sayiyordu — `SURUM.md` icinde
    # `` `IHLAL: "teslime hazir"` `` gecen tarihsel bir olcum satiri rc=1 uretiyordu.
    # §4 "ham cikti" ister, §11 yasak cumleyi yasaklar: ikisi carpisinca kanit
    # yazilamaz hale geliyordu. Kural: **ters tirnak icindeki span = alinti**,
    # iddia degil → ALINTI olarak YAZILIR, sayilmaz. Ters tirnak disinda ayni
    # cumle hala IHLAL (mutasyonla olculdu: `M-ALINTI`).
    _SPAN = []
    _pos = [i for i, ch in enumerate(nT) if ch == '\u0001']
    for a, b in zip(_pos[0::2], _pos[1::2]):
        _SPAN.append((a, b))
    _SATIR_BAS = [0] + [m.end() for m in re.finditer(r'\n', nT)]
    def _satir_no(i):
        import bisect
        return bisect.bisect_right(_SATIR_BAS, i) - 1
    _satirlar = nT.split('\n')
    def _span_ici(a, b):
        # a,b = eslesmenin (start,end); s,e = ters tirnak span'i
        if not any(s < a and e >= b for s, e in _SPAN):
            return False
        # DARALTMA: span icinde olmasi tek basina yetmez — ayni SATIRDA `ihlal`
        # jeti de olmali (yani satir, kapinin kendi ciktisini KAYDEDIYOR).
        # Aksi halde yasak cumleyi ters tirnakla gizlemek yol olurdu (m2 olcumu).
        return 'ihlal' in _satirlar[_satir_no(a)]
    alinti = []
    for k in kaliplar:
        for mm in re.finditer(r'(?<![a-z0-9])' + re.escape(k) + r'(?![a-z0-9])', nT):
            if _INKAR_M.match(nT[mm.end():mm.end() + 24]):
                continue
            if _span_ici(mm.start(), mm.end()):
                alinti.append(k)
                break
            hit.append(k)
            break
    for k in alinti:
        print('  ALINTI  "%s" (ters tirnak icinde — kanit kaydi, sayilmadi)' % k)
    for k in hit:
        print('  IHLAL: "%s"' % k)
    print()
    if hit:
        print('SONUC: IHLAL VAR (%d yasak cumle)' % len(hit))
        sys.exit(1)
    print('SONUC: TEMIZ — yasak cumle yok')
    sys.exit(0)

# 11 Kasim 2026: BAYRAKLAR YOL SAYILMAZ. Olculdu: `skill_lint.py
# --surum-taban-yaz` calistirilinca betik "--surum-taban-yaz" adli bir DOSYA
# aradi ve `OLCULEMEDI — dosya yok` verdi (rc=2). Bayrak argv[1]'de durunca
# YOL olarak yorumlaniyordu.
def _bayrak(_x):
    return _x.startswith('--')


YOL = (sys.argv[1] if (len(sys.argv) > 1 and not _bayrak(sys.argv[1]))
       else os.path.join(
           os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SKILL.md'))

if not os.path.isfile(YOL):
    print('SONUC: OLCULEMEDI — dosya yok: %s' % YOL)
    sys.exit(2)

try:
    C = io.open(YOL, encoding='utf-8').read()
except Exception as e:
    print('SONUC: OLCULEMEDI — okunamadi: %s (%s)' % (YOL, e))
    sys.exit(2)

satir = C.count('\n') + (0 if C.endswith('\n') else 1)

hata = []
uyari = []
sayac = {'kontrol': 0}
# [EK 2026-11-09] Kapi kimlikleri TEK noktadan toplanir. C15e (mutasyon sayaci)
# bu listeyi kullanir; `mutasyon_tara.py`yi subprocess ile cagirip lint'i
# YENIDEN kosturmaz — o yol OLCULDU ve SONSUZ OZYINELEME verdi
# (lint -> C15e -> mutasyon_tara -> lint -> ...). 900 s'te zaman asimi.
KAPI_KIMLIKLERI = []


def k(no, ad, ok, ayrinti=''):
    sayac['kontrol'] += 1
    if no not in KAPI_KIMLIKLERI:
        KAPI_KIMLIKLERI.append(no)
    durum = 'PASS' if ok else 'FAIL'
    print('  %-3s %-46s %s %s' % (no, ad, durum, ayrinti))
    if not ok:
        hata.append('%s %s%s' % (no, ad, (' — ' + ayrinti) if ayrinti else ''))


print('SKILL.md :', YOL)
print('satir    :', satir)
print('bayt     :', len(C.encode('utf-8')))
print()

# --- C1 frontmatter -------------------------------------------------------
m = re.match(r'^---\n(.*?)\n---\n', C, re.S)
if not m:
    k('C1', 'frontmatter var', False, 'dosya --- ile baslamali')
    fm = ''
else:
    fm = m.group(1)
    k('C1', 'frontmatter var', True)


def alan(ad):
    mm = re.search(r'^%s:\s*(.*)$' % ad, fm, re.M)
    if not mm:
        return None
    return mm.group(1).strip().strip('"').strip("'")


name = alan('name') or ''
desc = alan('description') or ''
comp = alan('compatibility') or ''
k('C1a', 'name deseni (a-z0-9, tek tire, <=64)', bool(re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name)) and len(name) <= 64, name)
k('C1b', 'description 1-1024 karakter', 1 <= len(desc) <= 1024, '%d kr' % len(desc))
# DUZELTME (4 Kasim 2026): eski surum `(not comp) or len<=500` — BOS compatibility
# PASS oluyordu (M-mutant: C1c false-green). Artik DOLU olmak zorunda.
k('C1c', 'compatibility DOLU ve <=500 karakter', bool(comp) and len(comp) <= 500,
  ('bos!' if not comp else '%d kr' % len(comp)))
k('C1d', 'license alani var', bool(alan('license')))
# --- C1e: SURUM DISIPLINI — IKI DOSYA (11 Kasim 2026) ----------------------
# OLCULDU: "version satiri var mi" kontrolu YETMIYORDU (vacuous kapi — yesil
# ama kor). Iki dosyada AYNI kusur olculdu:
#   1) `SKILL.md` son 3 commit'te degisti (`f20ac00` · `c352335` · `3854859`)
#      ve `metadata.version` `1.4.76` SABIT kaldi.
#   2) BU DOSYA son 10 commit'te degisti (`d9ed7ac` … `ac9abe6`) ve `SURUM:`
#      `2.32` SABIT kaldi (8 Kasim).
# Kusur birinci dosyada kapatildi, ikincisinde ACIK kaldi — cunku kapi tek
# dosyaya bakiyordu. Kismi duzeltme, duzeltme degildir.
# Her iki dosya da kendi kuralini yaziyor ("surum her degisiklikte artar");
# kural YAZILI, UYGULANMAMIS. Varlik kontrolu bunu GORMEZ.
#
# OLCUT — taban dosyalari, her biri elle tazelenir:
#   scripts/tests/skill_surum_taban.json  -> SKILL.md
#   scripts/tests/lint_surum_taban.json   -> bu dosya (scripts/skill_lint.py)
#   * dosya sha256'si tabanla AYNI  -> surum sarti yok (dosya degismedi)
#   * sha DEGISTI                   -> surum tabandan BUYUK olmali
# Taban guncellemesi: `python3 scripts/skill_lint.py --surum-taban-yaz`
# Otomatik tazeleme kapiyi KOR EDER (her kosuda taban yazilirsa surum sarti
# hic sinanmaz); bu bir TASARIM KARARIDIR, olcum degil.
_vm = re.search(r'^\s+version:\s*"?([^"\n]+)"?', fm, re.M)
_eser_ver = _vm.group(1).strip() if _vm else ''
_lint_ver = ''
try:
    with open(os.path.abspath(__file__), encoding='utf-8') as _lf:
        for _ll in _lf:
            if _ll.startswith('SURUM:'):
                _lint_ver = _ll.split(':', 1)[1].strip().split()[0]
                break
except Exception:
    _lint_ver = ''


def _sd_ad(_s):
    """'1.4.77' / '2.33' -> (1, 4, 77) / (2, 33) — karsilastirilabilir demet."""
    _p = [int(x) for x in re.findall(r'\d+', _s or '')]
    return tuple(_p) if _p else (0,)


def _sd_denetle(_yol, _taban_yol, _surum, _ad):
    """(ok, metin). Dosya DEGISTIYSE surum tabandan BUYUK olmali."""
    if not _surum:
        return False, '%s: surum satiri YOK' % _ad
    if not os.path.exists(_yol):
        return False, '%s: dosya yok' % _ad
    _sha = hashlib.sha256(open(_yol, 'rb').read()).hexdigest()
    if '--surum-taban-yaz' in sys.argv:
        _esk = {}
        if os.path.exists(_taban_yol):
            try:
                with open(_taban_yol, encoding='utf-8') as _f:
                    _esk = json.load(_f)
            except Exception:
                _esk = {}
        _esk.update({'_aciklama': '%s surum tabani. Kapi: C1e. '
                                  'sha degistiyse surum ARTMIŞ olmali.' % _ad,
                     'sha256': _sha, 'version': _surum})
        # ATOMIK YAZ (Z8): surum tabani da durum dosyasidir; yarim kalirsa
        # `C1e` bir daha calismaz.
        from atomik_yaz import yaz_json as _yazj
        _yazj(_taban_yol, _esk, indent=2, sort_keys=False)
        return True, 'YAZILDI: %s (sha=%s… · version=%s)' % (
            os.path.basename(_taban_yol), _sha[:12], _surum)
    if not os.path.exists(_taban_yol):
        return False, '%s: taban yok (uret: --surum-taban-yaz)' % _ad
    try:
        with open(_taban_yol, encoding='utf-8') as _f:
            _tb = json.load(_f)
    except Exception as _e:
        return False, '%s: taban okunamadi (%s)' % (_ad, _e)
    _b_sha, _b_ver = _tb.get('sha256'), _tb.get('version')
    if _sha == _b_sha:
        return True, '%s taban=%s · degismedi' % (_ad, _b_ver)
    if _sd_ad(_surum) <= _sd_ad(_b_ver):
        return False, ('%s HATA: dosya DEGISTI ama surum ARTMIYOR '
                       '(taban=%s -> simdi=%s)' % (_ad, _b_ver, _surum))
    return True, '%s taban=%s -> simdi=%s (artti)' % (_ad, _b_ver, _surum)


# `_BURASI` bu satirdan SONRA (L~1412) tanimli — C1e ondan once kosar.
# Ilk yazimda `_BURASI` kullanildi ve kapi "CALISTIRILAMADI" verdi (olculdu).
_sd_bu = os.path.dirname(os.path.abspath(__file__))
_sd_ciftler = [
    (os.path.join(_sd_bu, os.pardir, 'SKILL.md'),
     os.path.join(_sd_bu, 'tests', 'skill_surum_taban.json'),
     _eser_ver, 'SKILL.md'),
    (os.path.abspath(__file__),
     os.path.join(_sd_bu, 'tests', 'lint_surum_taban.json'),
     _lint_ver, 'skill_lint.py'),
]
_g1e_ok = True
_g1e_parca = []
for _yol, _tb, _sv, _ad in _sd_ciftler:
    _ok, _m = _sd_denetle(_yol, _tb, _sv, _ad)
    _g1e_ok = _g1e_ok and _ok
    _g1e_parca.append(_m)
if '--surum-taban-yaz' in sys.argv:
    for _m in _g1e_parca:
        print(_m)
    sys.exit(0)
k('C1e', 'metadata.version/SURUM var ve dosya degistiyse ARTAR', _g1e_ok,
  ' · '.join(_g1e_parca))

# --- C2 zorunlu bolumler --------------------------------------------------
# DUZELTME NOTU (3 Kasim 2026, mutasyon M1): onceki surum yalniz "'## 7.' metinde
# var mi" diye bakiyordu. Mutasyon testinde basligi "## 7. (bozuldu)" yapinca
# kapi YESIL kaldi — yani kapi vacuous'tu. Artik basligin ADI ve bolumun
# ICERIGI de denetlenir: numara + anahtar kelime + govde isareti.
# DUZELTME (n4 mutasyonu): onceki surum baslikta alt-dize ariyordu, bu yuzden
# "## 7. K6 — DENETIM BOZULDU" YESIL kaldi (alt-dize eslesmesi kapıyı kandirir).
# Artik baslik TAM desenle eslesir: numara + K<faz> + tam baslik (+ opsiyonel "· ...").
# DUZELTME (4 Kasim 2026, M2): (a) sonek serbest degil — yalniz "· **GIRDI:** ...
# · **CIKTI:** ..." bicimi kabul edilir ("· ESKI SURUM" gibi sonekler artik FAIL);
# (b) isaret ARTIK BOLUM GOVDESINDE aranir (eski surum tum dosyada ariyordu;
# isaret baska bolume tasinsa YESIL kaliyordu).
ZORUNLU = [
    ('0', r'^## 0\. SOZLESME(?: · \*\*GIRDI:\*\* .+ · \*\*CIKTI:\*\* .+)?$', 'Soru butcesi'),
    ('1', r'^## 1\. K0 — KUSANMA(?: · \*\*GIRDI:\*\* .+ · \*\*CIKTI:\*\* .+)?$', 'ARAC_ENVANTERI'),
    ('3', r'^## 3\. K2 — KANIT(?: · \*\*GIRDI:\*\* .+ · \*\*CIKTI:\*\* .+)?$', 'KAYNAKTA_BULUNAMADI'),
    ('7', r'^## 7\. K6 — DENETIM(?: · \*\*GIRDI:\*\* .+ · \*\*CIKTI:\*\* .+)?$', 'OZ_DENETIM'),
    ('8', r'^## 8\. K7 — TESLIM(?: · \*\*GIRDI:\*\* .+ · \*\*CIKTI:\*\* .+)?$', 'OLCULMEYEN'),
    # DUZELTME NOTU (7 Kasim 2026, TUR 6 D9): `§13` "Her teslimden sonra 12 soru"
    # diyor ama ZORUNLU listesinde ve bu kontrolde yoktu; D9 ile listeye eklendi,
    # kapi da basligin varligini olcer. Mutasyon: basligi sil -> C3 FAIL.
    ('13', r'^## 13\. OZ TEST(?: .*)?$', 'OZ_DENETIM'),
]
govdeler = _bolumler(C)
eksik = []
for num, desen, isaret in ZORUNLU:
    mh = re.search(desen, C, re.M)
    if not mh:
        # baslik var mi, adi yanlis mi? ayirt et ki teshis dogru olsun
        var = re.search(r'^## %s\.[^\n]*$' % num, C, re.M)
        eksik.append('§%s basligi TAM eslesmiyor: %s' % (num, var.group(0)[:46] if var else 'yok'))
        continue
    if _katla(isaret) not in govdeler.get(num, ''):
        eksik.append('§%s govdesinde "%s" yok' % (num, isaret))
k('C2', 'zorunlu bolumler (baslik+sonEK+govde)', not eksik, ('; '.join(eksik)) if eksik else '5 bolum')

# --- C3 ZORUNLU listesi tutarli -------------------------------------------
# DUZELTME NOTU (3 Kasim 2026): onceki surumde bu kontrol `(.*?)\.` ile
# cumleyi ILK NOKTADA kesiyordu; "§3.2" icindeki nokta yuzunden liste
# ['0','1','3'] cikip YANLIS FAIL uretiyordu (dosya dogruydu, betik yanlisti).
# Ders: denetcinin kendi olcum hatasi. Artik cumlenin tamami alinir ve
# "§3.2" gibi alt bolum numaralari da ana numaraya indirgenir.
zl = re.search(r'\*\*ZORUNLU bolumler[^\n]*\*\*(.*?)(?:\n\n|\n#)', C, re.S)
if zl:
    gecen = {n.split('.')[0] for n in re.findall(r'§(\d+(?:\.\d+)*)', zl.group(1))}
    beklenen = {z[0] for z in ZORUNLU}          # artik tuple: (numara, baslik, isaret)
    k('C3', 'ZORUNLU listesi govdeyle tutarli', gecen == beklenen,
      'liste=%s govde=%s' % (sorted(gecen), sorted(beklenen)))
else:
    k('C3', 'ZORUNLU listesi var', False, 'cumle bulunamadi')

# --- C4/C5 yasak cumleler -------------------------------------------------
blok = re.search(r'<!-- YASAK_BASLANGIC -->(.*?)<!-- YASAK_BITIS -->', C, re.S)
if not blok:
    k('C4', 'yasak cumle blogu var', False)
    yasaklar = []
else:
    yasaklar = [s.strip().lower() for s in blok.group(1).split('\n') if s.strip()]
    # DUZELTME (4 Kasim 2026): donmus liste kontrolu — bloktan kalip silinirse
    # kapi zayiflamaz; C4 artik hem doluluk hem donmus asgariyi denetler.
    silinen = [x for x in DONMUS_KALIP if x not in yasaklar]
    k('C4', 'yasak cumle blogu dolu (>=5) + donmus liste tam',
      len(yasaklar) >= 5 and not silinen,
      '%d kalip%s' % (len(yasaklar), (' · blogtan silinmis: %s' % silinen) if silinen else ''))

# DUZELTME (B-12): onceki surumde yorum "frontmatter taranmaz" diyordu ama kod
# frontmatter'i cikarmiyordu. Artik gercekten cikariliyor: taranan = govde.
govde = (C[m.end():] if m else C)
govde = govde.replace(blok.group(0), '') if blok else govde
nGovde = _katla(govde)
bulunan = []
# DUZELTME (4 Kasim 2026, M5): eski surum `y in govde.lower()` alt-dize ariyordu;
# "her sey hazirlanmadi" icin FALSE-RED veriyordu (olcum: rc=1).
# Artik (a) kelime siniri: \b ile; (b) inkar istisnasi: kalibi hemen takip eden
# "degil/degildir/lanmadi/olmadi" varsa bu bir OLUMSUZ cumledir, ihlal degildir.
INKAR = re.compile(r'\s*(?:degil\w*|lanmadi|olmadi|yoktur|kalinmaz|yazilmaz)\b')
for y in yasaklar:
    if not y:
        continue
    for mm in re.finditer(r'(?<![a-z0-9])' + re.escape(y) + r'(?![a-z0-9])', nGovde):
        sonrasi = nGovde[mm.end():mm.end() + 24]
        if INKAR.match(sonrasi):
            continue   # olumsuz kullanim: "her sey hazir degil" gibi
        bulunan.append(y)
        break
k('C5', 'yasak cumle govdede gecmiyor (sinir+inkar)', not bulunan,
  ('gecen: %s' % bulunan) if bulunan else '')

# --- C6 satir -------------------------------------------------------------
k('C6', 'satir <= 500 (spec onerisi)', satir <= 500, '%d satir' % satir)

# --- C7 homoglif ----------------------------------------------------------
# DUZELTME (4 Kasim 2026, M15/M21): eski surum yalniz U+0400-04FF ve U+0370-03FF
# bakiyordu; U+0269 (ɩ) ve U+2024 (․) KACIYORDU (olcum: rc=0).
# Aralik genisletildi: IPA ek (0250-02AF) · tek-nokta (2024) · zero-width
# (200C/200D) · tam-genişlik (FF01-FF5E).
def _homoglif(metin):
    kotu = []
    for i, ch in enumerate(metin):
        o = ord(ch)
        if (0x0400 <= o <= 0x04FF or 0x0370 <= o <= 0x03FF or
                0x0250 <= o <= 0x02AF or 0xFF01 <= o <= 0xFF5E or
                # DUZELTME (5 Kasim 2026, F6-P1#3): gorunmezler de tasinir —
                # ZWSP/ZWNJ/ZWJ/soft-hyphen/word-joiner/BOM/one-dot-point.
                o in (0x2024, 0x200B, 0x200C, 0x200D, 0x2060, 0x00AD, 0xFEFF)):
            kotu.append((metin.count('\n', 0, i) + 1, 'U+%04X' % o))
    return kotu


homo = _homoglif(C)
k('C7', 'homoglif/zerewidth yok (genis aralik)', not homo,
  ('%d adet, ilk: satir %s %s' % (len(homo), homo[0][0], homo[0][1])) if homo else '')

# --- C8 beyan blogu -------------------------------------------------------
# DUZELTME (5 Kasim 2026, F6-P1#5): eski surum tum dosyada ariyordu; DOGRULAMA
# blogu §12 disina tasilinca YESIL kaliyordu. Artik §12 GOVDESINDE aranir.
_g12 = govdeler.get('12', '')
# NOT: govdeler _katla'dan gecmis — coklu bosluk TEK bosluga iner ("kod   :" -> "kod :").
k('C8', '§12 DOGRULAMA blogu (cikti+kod alanli)',
  ('dogrulama' in _g12) and ('cikti :' in _g12) and ('kod :' in _g12))

# --- C10 ALTIN CUMLELER (B-5, v2) ----------------------------------------
# NEDEN: bagimsiz denetci (3 Kasim 2026) yuk tasiyan kurallari KOPYADA ters
# cevirdi ("sayilmaz"->"sayilir", "devir yazmaz"->"Devir yazilir",
# "TASINAMAZ"->"TASINABILIR") ve 14/14 TEMIZ aldi. Yapisal kontrol bunu
# gormuyordu. Bu kapi, kuralin ANLAMINI tasiyan cumleyi birebir arar.
#
# DUZELTME (4 Kasim 2026, M11/M12/M16):
#   (a) YER: her altin cumle kendi BOLUNDE bulunmak zorunda (M16: cumle baska
#       bolume tasindiginda eski surum YESIL kaliyordu);
#   (b) INKAR EKI: cumleyi hemen takip eden "degildir/yanlistir/gecersiz"
#       gibi ek, kurali TERSINE cevirir (M11: boylece yesil kaliyordu);
#   (c) katlama Turkce karakterleri de kapsar (M18 false-red).
ALTIN = [
    ("P0/P1 OLCULMEYEN'e tasinamaz", 'olculmeyene tasinamaz', '7'),
    ("dur/mola devir yazmaz", 'dur/mola devir yazmaz', '8'),
    ("ayni modelin kopyasi bagimsiz sayilmaz", 'ayni modelin ikinci kopyasi bagimsiz sayilmaz', '7'),
    ("onaysiz TAMAMLANDI gecersiz", 'onay yoksa tamamlandi gecersizdir', '8'),
    ("her sayisal iddia kaynakli", 'her sayisal iddia kaynagini tasir', '6'),
    ("denemeyen MOD dusuremez", 'denemeyen ajan mod dusuremez', '1'),
    ("ENGEL_VAR cikisi tanimli", 'engel_var cikisi (tanimsiz kalamaz)', '7'),
    ("alinti arac ile bulunur", 'alintiyi aracla bul', '3'),
    ("yanmayan test = sus", 'yanmayan test = sus payi', '10'),
]
INKAR_EKI = re.compile(r'^\s*(?:\W*)(?:degil\b|degildir|yanlistir|gecersiz(?:dir)?|olmaz|tasinabilir|sayilir|yazilir)\b')
ng = _katla(C)
kayip = []
for ad, hedef, bol in ALTIN:
    konum = ng.find(hedef)
    if konum < 0:
        kayip.append('%s (yok)' % ad)
        continue
    if _katla(hedef) not in govdeler.get(bol, ''):
        kayip.append('%s (bolum §%s degil)' % (ad, bol))
        continue
    if INKAR_EKI.match(ng[konum + len(hedef):konum + len(hedef) + 30]):
        kayip.append('%s (sonuna inkar eki)' % ad)
k('C10', 'altin cumleler (%d) yer+inkar+birebir' % len(ALTIN), not kayip,
  ('sorunlu: %s' % kayip) if kayip else '%d/%d' % (len(ALTIN), len(ALTIN)))

# --- C9 terminal ----------------------------------------------------------
# DUZELTME (5 Kasim 2026, F6-P1#6): eski surum tum dosyada ariyordu; liste
# §8.5'ten tasilinca YESIL kaliyordu. Artik §8 GOVDESINDE aranir.
GEREKLI = ['TAMAMLANDI', 'KOSULLU', 'ENGEL_VAR', 'INSAN_BEKLIYOR', 'OLCULMEDI']
_g8 = govdeler.get('8', '')
yok = [t_ for t_ in GEREKLI if _katla(t_) not in _g8]
k('C9', 'terminal durum listesi §8 govdesinde tam', not yok, 'eksik: %s' % yok if yok else '')

# --- C12 capraz atif cozunurlugu ------------------------------------------
# DUZELTME NOTU (6 Kasim 2026, K17): C11a-C11e capalari bir cumlenin VAR OLUP
# OLMADIGINA bakar, DOGRU OLUP OLMADIGINA bakmaz. Bir yazar `§8.1` yazsa ama
# §8.1 diye bir bolum olmasa, C11c yine PASS verir (capa metni gecti). Bu kapi
# o deligi kapatir: metindeki HER `§A.B` atfinin hedefi gercekten tanimli mi?
#   - bolum   -> `^## A.`
#   - alt bol -> `**A.B ` veya `### A.B ` (iki bicim de kullaniliyor: §1.2 `###`)
#   - madde   -> `§A.B/N` icin A.B govdesinde `N.` veya `N)` ile baslayan satir
ATIF = re.compile(r'§(\d+)(?:\.(\d+))?(?:/(\d+))?')
_ham = C
_bolum = set(re.findall(r'^## (\d+)\.', _ham, re.M))
_alt = set(re.findall(r'^\*\*(\d+\.\d+)[ .]', _ham, re.M)) | \
    set(re.findall(r'^### (\d+\.\d+)', _ham, re.M))

# alt bolum govdeleri (madde sayimi icin)
_alt_govde = {}
_parca = re.split(r'^(?:\*\*|### )(\d+\.\d+)[ .].*$', _ham, flags=re.M)
for _i in range(1, len(_parca), 2):
    _alt_govde.setdefault(_parca[_i], '')
    _alt_govde[_parca[_i]] += _parca[_i + 1]

_cozulmeyen = []
_madde_yok = []
_gorulen = set()
for _a, _b, _d in ATIF.findall(_ham):
    _ref = _a + ('.' + _b if _b else '') + ('/' + _d if _d else '')
    if _ref in _gorulen:
        continue
    _gorulen.add(_ref)
    if _b:
        if _a + '.' + _b not in _alt:
            _cozulmeyen.append(_ref)
            continue
        if _d:
            _g = _alt_govde.get(_a + '.' + _b, '')
            if not re.search(r'^\s*%s[.)]' % re.escape(_d), _g, re.M):
                _madde_yok.append(_ref)
    else:
        if _a not in _bolum:
            _cozulmeyen.append(_ref)

k('C12a', 'her §A.B atfinin hedefi tanimli', not _cozulmeyen,
  ('cozulmeyen: %s' % _cozulmeyen) if _cozulmeyen else '%d benzersiz atif' % len(_gorulen))
k('C12b', 'her §A.B/N madde numarasi gercek', not _madde_yok,
  ('yok: %s' % _madde_yok) if _madde_yok else '')

# --- C11 yapisal capalar --------------------------------------------------
# DUZELTME NOTU (6 Kasim 2026, mutasyon M-v1437..M-v1441): v1.4.37-41'in BES
# duzeltmesi mutasyonda YANMADI (5/5 KORUNMASIZ, olculdu: her mutant tek tek
# uygulandi, lint rc=0 kaldi). Sebep: C1-C10 metin KALIBINA bakar; o bes
# duzeltme ICERIK cumlesidir. Bu iki kapi en azindan ikisini korur:
#   C11a -> §8.1 manifestinde SORU_BUTCESI satiri (v1.4.41)
#   C11b -> §7.4 geri donus kurali P1 -> K2 (v1.4.40)
# Kalan uc duzeltme (v1.4.37 atif hedefi, v1.4.38 I6 kimligi, v1.4.39
# BLOK_GECERSIZ ayrimi) HALA KORUNMASIZ — bu bilincli, kapi yazmak icin
# olculebilir bir capa gerekir; ucunun de capasi yok. Teslimde OLCULMEYEN yazilir.
CAPA = [
    ('C11a', '§8.1 manifestinde SORU_BUTCESI (4 alan)', '8',
     ['soru_butcesi', 'ilan=', 'kullanilan=', 'kalan=', 'butce disi=']),
    ('C11b', '§7.4 geri donus P1 -> K2', '7', ['p1 → k2']),
    # DUZELTME NOTU (6 Kasim 2026, K16b): kalan uc korumasiz duzeltmeye de
    # olculebilir capa bulundu — her capa KENDI bolumunde TEK kez geciyor
    # (olculdu: gecis=1). Artik 5/5 mutant yaniyor.
    ('C11c', '§6.1 atif hedefleri (§8.1 alan + §3.3/3)', '6', ['§8.1', '§3.3/3']),
    ('C11d', '§10 I6 kimligi (kaynagi AGENTS.md, I1-I9)', '10',
     ['agents.md', 'i1-i9']),
    ('C11e', '§7.1 BLOK_GECERSIZ <-> ACIK_SORU ayrimi', '7',
     ['iki durum karismaz', 'reddedilenler altina']),
]
for _no, _ad, _bol, _gerek in CAPA:
    _gov = govdeler.get(_bol, '')
    _eksik = [g for g in _gerek if _katla(g) not in _gov]
    k(_no, _ad, not _eksik, ('eksik: %s' % _eksik) if _eksik else '%d capa' % len(_gerek))

# --- C13 v1.4.42 capalari (TUR 5) -----------------------------------------
# DUZELTME NOTU (7 Kasim 2026, TUR 5): v1.4.42'nin ON SEKIZ duzeltmesi
# mutasyonda YANMADI (olculdu: 0/18; $TMPDIR/mut_t5.py her duzeltmeyi tek tek
# geri bozdu, lint her seferinde "TEMIZ — 22 kontrol gecti"). Yani "22/22"
# bu duzeltmeler icin KANIT DEGILDI. Asagidaki 18 kapi her duzeltmenin
# DEGISTIRILMIS cumlesini capa olarak tutar.
#
# Yontem: her capa KATLA'DAN gecmis metinde aranir, BEKLENEN gecis sayisi
# yazilidir. Mutant metni eski haline dondurdugunde capa KAYBOLUR (sayi 0) ->
# FAIL. Beklenen sayi 1'den buyukse (F9 uc bolume ayni gerekceyi yazdi) sayi
# yine tutmalidir: biri silinirse kapi yanar.
#
# NOT: capa metni DEGISIKLIGIN KENDISIDIR, kuralin dogrulugu degil. Kapi
# "cumle duruyor mu" olcer; "cumle dogru mu" olcmez — bu OLCULMEYEN kalir.
C13 = [
    ('C13a', 'F1 ayet dongusu exit kodu olculdu (2026-11-07)',
     # DUZELTME (7 Kasim 2026): TUR 5'te bu satir `kod = OLCULMEDI` idi; ayni
     # gun dongu yeniden kosuldu (rc=0, 200 x7) ve satir olcume cevrildi.
     # Capa yeni metne gore yazildi; eski metin artik YANLIS olurdu.
     [('2026-11-07 yeniden olcum', 1),
      ("asagida\" diye bir kayit yoktu", 1)]),
    ('C13b', 'F2 govde indirilmedi -> metin OLCULMEDI',
     [('govde indirilmedi', 1)]),
    ('C13c', 'F3 REDDEDILENLER dis blok kolunu da kapsar',
     [('gecersiz dis blok kaydi', 1), ("sayim'da ikisi ayri sayilir", 1)]),
    ('C13d', 'F4 soru_butcesi 4 alan',
     [('kullanilan":0', 1), ('butce_disi', 1)]),
    ('C13e', 'F5 satir no atfi yerine compatibility hukmu',
     [('karsiligi el ile yapilir" hukmu uyarinca', 1)]),
    ('C13f', 'F6 lint taramasi zorunlu',
     [('8.2/6 bunu zorunlu kilar', 1)]),
    ('C13g', 'F7 MOD tablosunda devralma hucresi acik',
     [('okuma yok + yazma yok: sonuc sohbette', 1)]),
    ('C13h', 'F8 kucuk is esigi risk tabanli',
     [('esik sekle degil riske baglidir', 1)]),
    ('C13i', 'F9 kucuk is gerekcesi 3 yerde taniniyor',
     [('kucuk is (§0.6)', 3)]),
    ('C13j', 'F10 Unicode adlari olculmus',
     [('ust hemze U+0654', 1), ('kucuk vav U+06E5', 1)]),
    ('C13k', 'F11 kimlik listesi korunum + EKLENEN',
     # DUZELTME NOTU (7 Kasim 2026, TUR 6 D11): kimlik listesi tanimina betik
     # sha256'si eklendi; kimlik degisimi jetoni metinde artik 2 kez geciyor.
     # 7 Kasim 2026 (dis denetim D11, ikinci tur): MOD-B istisnasi + "yeni kapi =
     # EKLENEN" cumlesi eklendi -> jeton 2 -> 4. Sayac DUSURULMEDI; gerekce bu.
     [('eklenen olarak kaydedilir', 1), ('kimlik_degisti', 4)]),
    ('C13l', 'F12 K2->K3 kapisi P1i de denetler',
     [('her p0 ve p1 iddia', 1)]),
    ('C13m', 'F14 ARACLA_BULUNMADI tanimli',
     [('aracla_bulunmadi = arama araci yoktu', 1)]),
    ('C13n', 'F15 cikti tablosunda iskelet/malzeme (derleme + kitapcik)',
     [('her sentez satiri kaynakli · iskelet/malzeme', 1),
      # DUZELTME (7 Kasim 2026): F15 basta yarim uygulanmisti — yalniz derleme
      # satiri. Kitapcik satiri da ayni §16 sinirina tabidir; capa eklendi.
      ('sayfa/olcu hedefi tutuyor · iskelet/malzeme', 1)]),
    ('C13o', 'F16 durum.json mod sablonu yer tutucu',
     [('"mod":"<a|b|c>"', 1)]),
    ('C13p', 'F17 soru butcesi bilgi sorusuna nitelendi',
     [('kez bilgi sorusu sorar', 1)]),
    ('C13q', 'F18 ENGEL_VAR taniminda tarama tetikleyicisi',
     [('veya §8.2/6 zorunlu taramasi yapilmadi', 1)]),
    ('C13r', 'F19 Al-i Imran Turkce imla',
     # DUZELTME (7 Kasim 2026): katla() diyakritigi siler -> "Âl-i İmrân" ve
     # "Al-i Imran" KATLA'DA AYNI olur, mutant yanmadi (olculdu 17/18). Bu capa
     # HAM metinde aranir: "H:" oneki ham arama demektir.
     [('H:Âl-i İmrân 3:159', 1)]),
    ('C13s', 'sunnah.com hadis metinleri olculdu (2026-11-07)',
     # YENI KAPI (7 Kasim 2026): iki hadis kunyesi (`bukhari:39`, `bukhari:6094`)
     # `DOGRULANAMADI` idi. 2026-11-07'de `webfetch` ile HTTP 200 alindi.
     # Capa, olcumun YAZILDIGINI tutar — metnin dogrulugunu degil (o OLCULMEYEN kalir).
     # DUZELTME NOTU (7 Kasim 2026, TUR 6 D2): onceki capa `metin okundu — parafraz
     # uygun` hukmunu sabitliyordu; o hüküm kanitsizdi (URL/komut/stdout §12 blogu yok)
     # ve D2 ile `OLCULMEDI`ye cekildi. Capa yeni metne tasindi.
     # DUZELTME NOTU (7 Kasim 2026, OLCULMEYEN #5 kapandi): capa artik YAZILI olan
     # BIRINCIL METNI tutar. Once "hukum" sabitlenmisti (yanlis), sonra "olculmedi"
     # (dogru ama zayif); simdi olculmus metnin kendisi. Mutasyon: alintiyi sil -> FAIL.
     # DUZELTME NOTU (7 Kasim 2026, Arapca olcumu): kapsam da capaya girdi —
     # Turkce satir hadisin TAMAMINI degil %16 / %29'unu veriyor; bu artik yazili.
     [('Truthfulness leads to righteousness, and righteousness leads to Paradise.', 1),
      ('Religion is very easy and whoever overburdens himself in his religion', 1),
      ('Arapca olcumu', 2),
      # YENI (7 Kasim 2026, "tamami yazilmali" karari): kisa satir hadisin
      # %29 / %16'sini veriyordu. Tam metin yazildi; capa artik TAM Arapcayi
      # tutar — biri kesilirse FAIL. Metin harakeli oldugu icin `H:` (ham) capa.
      ('H:إن الصدق يهدي إلى البر وإن البر يهدي إلى الجنة وإن الرجل ليصدق حتى يكون صديقا وإن الكذب يهدي إلى الفجور وإن الفجور يهدي إلى النار وإن الرجل ليكذب حتى يكتب عند الله كذابا', 1),
      ('H:إن الدين يسر ولن يشاد الدين أحد إلا غلبه فسددوا وقاربوا وأبشروا واستعينوا بالغدوة والروحة وشىء من الدلجة', 1)]),
    # YENI KAPI (7 Kasim 2026): `sir` alani eklendi ama GOC kurali yoktu —
    # eski durum.json dosyalarinda anahtar bulunmayacak. Kural uc noktayi tutar:
    # okuyucu eksik anahtari bos sayar, yazici ekler, goc veriyi degistirmez.
    ('C13u', 'sir sema gocu (geriye uyum) tanimli',
     [('`sir` gocu (geriye uyum)', 1),
      ('okuyucu eksik anahtari `[]` sayar', 1),
      ('Gocte **veri degistirilmez**', 1)]),
    # YENI KAPI (7 Kasim 2026, dis denetim D1 GERILEMESI): D1 fazladan kapanis
    # parantezini kapatmisti (`36ae4de`), ama `a588c46` (tam hadis metni) ayni
    # hatayi GERI GETIRDI — 18/18 dis model D1'e "KAPATTI" dedi, hicbiri
    # yakalamadi (I3: anlasma dogruluk degildir). 43 kontrolun hicbiri
    # sozdizimini olcmuyordu. Bu capa YOKLUK capasidir: `)*` + `)` dizisi 0 olmali.
    # Olculdu: `a588c46`=2 · `HEAD`=2 · duzeltilmis=0. Mutasyon: geri koy -> FAIL.
    ('C13v', 'fazladan kapanis parantezi yok (D1 sinifi)',
     # `H:` (ham metin) SART: `_katla()` `*` karakterini siliyor, capa `))`e
     # donusuyor ve her cift parantezi sayiyordu — capa kendini olduruyordu.
     [('H:)*)', 0)]),
    # YENI KAPI (7 Kasim 2026, dis denetim D13): `Şura`nin ASCII sayildigi cumle
    # 9/9 modele gore YENI KUSURDU. "diger sure adlari ASCII" ifadesi geri
    # gelmemeli; yerine OLCULMUS hali durmali. Olculdu: `Ş`=U+015E, ASCII degil.
    ('C13w', 'sure adi imla rejimi olculmus halde (D13)',
     [('iki ad** Turkce', 1),
      ('U+015E,', 1),
      ('diger sure adlari ASCII', 1)]),
    # YENI KAPI (7 Kasim 2026, dis denetim D10): §7.3 tablosuna `(41 kontrol)`
    # yazilmisti; betik 45 kontrol olctu -> ayni dosyada iki celisen sayi
    # (6/18 model YENI_KUSUR dedi). Kapinin kendisi de kopya sayi tasimaz.
    # DUZELTME (7 Kasim 2026, D10 IkINCI tekrar): eski capa yalniz '41 kontrol'
    # dizesini ariyordu; sayac 46 olunca korlesti. Artik KURAL: SKILL.md'de
    # `N kontrol` gibi gomulu sayi HIC olmamali (tek kaynak: betigin SURUM:).
    ('C13x', 'kontrol sayisi tek kaynak, GOMULU sayi yok (D10)',
     [('tek kaynak betigin `SURUM:` satiri', 1),
      ('R:' + r'\d+\s*kontrol', 0)]),
    # YENI KAPI (7 Kasim 2026, dis denetim D22): "yazma yoksa NOT_EXECUTED: MOD-C"
    # §1 tablosuyla CELISIYORDU (`E|H|E` = MOD-B). 4 model YENI_KUSUR saydi.
    ('C13y', '3.3 MOD etiketi olcumden gelir (D22)',
     [('`E|H|E` = **MOD-B**', 1),
      ('olcumden** gelir', 1),
      ('yazma yoksa `NOT_EXECUTED: MOD-C`', 0)]),
    # YENI KAPI (7 Kasim 2026): `INJECTION_ATTEMPT` kurali iki turdur yaziliydi ama
    # TASIYICISI ve DENETIM SARTI yoktu — "kuralim var" yanilsamasi (D19'un
    # `REDDEDILENLER` icin yakaladigi hatanin aynisi). Bu capa uc noktayi birlikte
    # tutar: manifest alani (2 kez: sema + §8.2/6), sayac karsilastirma sarti,
    # ve `durum.json` alan tanimi. Mutasyon: sarti sil -> FAIL.
    # YENI KAPI (7 Kasim 2026, dis denetim D2): hadis satirlarinda "34/18 kelime"
    # iddiasi vardi ama KOMUT/HAM CIKTI/EXIT yoktu (5/18 model KAPATMADI saydi).
    # §12 alanlari artik satirda; asil olcum C13z calistirmali kapisinda.
    ('C13z', 'hadis olcumu §12 alanli (D2)',
     [('python3 scripts/hadis_olcum.py SKILL.md --bekle 34 18', 1),
      ('ham_kelime=34', 1),
      ('ham_kelime=18', 1),
      # DUZELTME (7 Kasim 2026, kalem 2): iddia once 'GERI ALINDI' idi (yanit
      # dosyada yoktu). Artik OLCULDU — betik sayfayi cekip karsilastiriyor.
      ('sunnah.com ile birebir aynilik OLCULDU', 1),
      # 8 Kasim 2026 (D4): istemci matrisi AYNI YERDE kuruldu — betik adi
      # ikinci kez geciyor (kanit olarak). Capa 1 -> 2; gevsetme degil, metin buyudu.
      ('sunnah_karsilastir.py', 2)]),
    # YENI KAPI (7 Kasim 2026, dis denetim D4/D21): "curl/urllib ayni gun 403"
    # cumlesi vardi, o gunun ciktisi YOKTU. Artik komut + ham cikti satirda.
    # Yokluk capasi `H:` ile: katlama ters tirnak/yildizi siliyor, aksi halde
    # yeni cumle de eski desene benziyor (olculdu).
    ('C14a', 'HTTP 403 olcumu komutlu (D4/D21)',
     [('for u in 39 6094; do curl', 1),
      ('http_olcum.py https://sunnah.com/bukhari:39', 1),
      ('2026-11-07 09:47', 1),
      ('H:`curl`/`urllib` ayni gun', 0)]),
    # YENI KAPI (7 Kasim 2026, dis denetim D3): kunye satirinda UC tarih geciyordu,
    # kunye ikisini gosteriyordu. Uculuk birlikte aranir; biri dusunce FAIL.
    # YENI KAPILAR (7 Kasim 2026, dis denetim ikinci tur)
    ('C14h', 'REDDEDILENLER iki alt turu ayri sayar (D19)',
     [('(i) kendi iddian', 1),
      ('(ii) §7.1 geregi gecersiz dis blok', 1),
      ('`BLOK_GECERSIZ` kalemi (ii) altindadir', 1)]),
    ('C14f', 'esik oz-denetimle acilmaz (D17 dongusu kirildi)',
     [('`OZ_DENETIM` ise esik ACILMAZ', 1),
      ('`BAGIMSIZLIK: VAR` tasimali', 1)]),
    ('C14g', 'DURDURULAN anlami gloslu, tartisma ACIK_SORU (D7)',
     [('isi BIZ durdururuz', 1),
      ('dil tartismasi **ACIK_SORU** olarak kaydedildi', 1)]),
    ('C14c', 'elle tarama §12 karsiligi var, ENGEL_VAR uretmez (D18)',
     [('elle tarama — <ne tarandi>', 1),
      ('NOT_APPLICABLE (elle)', 1),
      ('tek basina `ENGEL_VAR` uretmez', 1)]),
    ('C14d', 'MOD-B kimlik listesi + ARAC/KIMLIK ayrimi (D11)',
     [('NOT_EXECUTED (MOD-B)`', 1),
      ('ARAC_DEGISTI', 1),
      ('kapi_farki.py --taban', 1)]),
    ('C14e', '[sir] isaretleyen insan + veri verilmisse dur (D14)',
     [('Insaretleyen', 0),
      ('Isaretleyen **insandir**', 1),
      ('HUMAN_REVIEW_REQUIRED`, anahtar yenileme', 1)]),
    ('C14b', 'kunye uc tarihi birlikte gosterir (D3)',
     [('hadis metni 2026-11-07; **quran.com API olcumu 2026-11-05**', 1),
      ('erisim 2026-11-06', 1)]),
    # YENI KAPI (12 Kasim 2026, DIS DENETIM TUR 11 — D10'un BESINCI tekrari):
    # `SKILL.md` §7.3 `C14t-a`'nin BES parametresini gomulu yaziyordu ve BESI DE
    # bayatti: bilinen yazim 35 (canli 58) · bicim uzayi 1680 (canli 2400) ·
    # %98.1 (canli 98.7) · yanlis pozitif 0/19 (canli 0/40) · kacak 3 (canli 5).
    # D10'un onceki dort tekrari SAYAC kapilarini uretmisti (C13x, C14t, C14t-a);
    # hicbiri KAPININ KENDI PARAMETRESINI kapsamiyordu — sozlukte "bilinen
    # yazim"/"bicimlik uzay"/"yanlis pozitif"/"bilinen-kacak" yok.
    # KURAL: parametre yazilmaz; tek kaynak `C14t-a` ciktisi. Bes bicim de yasak.
    # Ayni sinif paket metninde de vardi (statik 47 · canli 86 -> canli 50 · 88);
    # `scripts/tur4_paket_uret.py` ayni gun duzeltildi.
    ('C18', 'kapi parametreleri gomulu yazilmaz (D10 5. tekrar)',
     [('R:' + r'\d+\s+bilinen yazim', 0),
      ('R:' + r'\d+\s+bicimlik uzay', 0),
      ('R:' + r'olculen\s+\*{0,2}%\d', 0),
      ('R:' + r'yanlis pozitif\s+\*{0,2}\d', 0),
      ('R:' + r'bilinen-kacak\s+\*{0,2}\d', 0),
      ('H:tek kaynak `C14t-a` ciktisi', 1)]),
    ('C13t', 'INJECTION_ATTEMPT tasiyici + bitti sarti',
     [('INJECTION_ATTEMPT=<n>', 3),          # 7 Kasim 2026 (D15): 3 -> 3.3/§0.9 da `=` oldu
      ('n == len(durum.json.injection)', 1),
      ('len(injection)` bitti sartidir', 1),
      ('H:`INJECTION_ATTEMPT: <n>`', 0)]),    # iki sozdizimi geri gelmesin (D15)
]
_T = _katla(C)
for _no, _ad, _bek in C13:
    _sap = []
    for _cap, _n in _bek:
        if _cap.startswith('R:'):
            # REGEX capasi (7 Kasim 2026, D10'un IKINCI tekrari). Sebep: eski capa
            # '41 kontrol' DIZESINI yasakliyordu. Sayac 41 -> 46 olunca kapi
            # KORLESTI ("46 kontrol" != "41 kontrol") ve bayat sayi dosyaya
            # geri girdi (olculdu: SKILL.md 'v2.12, 46 kontrol', gercek 2.30/67).
            # Kapi ESKI HATANIN METNINI degil KURALI yasaklamali: "N kontrol" gibi
            # HERHANGI bir gomulu sayi yasak.
            _ger = len(__import__('re').findall(_cap[2:], C))
        elif _cap.startswith('H:'):
            _ger = C.count(_cap[2:])
        else:
            _ger = _T.count(_katla(_cap))
        if _ger != _n:
            _sap.append('%s: %d/%d' % (_cap[:26], _ger, _n))
    k(_no, _ad, not _sap, ('sapan: %s' % _sap) if _sap else '%d capa' % len(_bek))

# --- C14p CALISTIRMALI: esik PLATO icinde mi (OLCULMEYEN kalem 2) ---------
# NEDEN (7 Kasim 2026): kapsam/meal esikleri (0.50/0.50) INSAN secimi, olculmemisti.
# Esik "hukum veren" bir sayidir; platonun DISINDA secilmisse keyfi olur.
# Bu kapi duyarlilik taramasini kosturur ve 0.50'nin plato icinde oldugunu arar.
# Fail-closed: plato bulunamazsa FAIL (esik keyfi demektir).
_pl = ''
_pl_ok = False
try:
    # [DUZELTME 2026-11-12, Z1] AG BAGIMLILIGI KALDIRILDI. Bu kapi `ceviri()`yi
    # CANLI kosturuyordu: `api.alquran.cloud`'a 12 HTTPS cagrisi. OLCULDU — bir
    # kosuda betik tek basina `real 127,80 s` (user 0,86 s = is yok, BEKLEME var)
    # surdu ve 120 s zaman asimina carpti: `C14p FAIL ... timed out`; ayni gun
    # sonraki kosuda `PASS`. Yani AYNI KOD bazen yesil bazen kirmizi — kapinin
    # hukmu ucuncu tarafin gecikmesine bagliydi. Kardesleri `C14m`/`C14n` zaten
    # `SNAPSHOT_ONLY=1` ile cevrimdisi kosuyordu; `C14p` atlanmisti. Artik o da
    # snapshot'tan kosar: OLCULDU — cikti 32 satir **birebir ayni**, sure
    # `127,80 s -> 0,06 s`. Fail-closed: snapshot eksikse `ceviri()` duser,
    # `kapsam_matrisi` bunu artik `MEAL_EKSIK` diye bildirir (sessiz kapsam kaybi
    # yok) ve kapi FAIL eder.
    _d6 = os.path.dirname(os.path.abspath(__file__))
    _env9 = dict(os.environ)
    _env9['SNAPSHOT_ONLY'] = '1'
    _r9 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d6, 'ayet_ozet_kontrol.py'), '--duyarlilik', YOL],
        capture_output=True, text=True, timeout=120, env=_env9)
    _satirlar = _r9.stdout.strip().splitlines()
    _eksik_meal = [x for x in _satirlar if 'MEAL_EKSIK' in x]
    _pl = ' | '.join(x for x in _satirlar
                     if x.startswith(('PLATO:', 'COZUNURLUK:', 'SONUC_TANIM:')))[:250]
    _pl = 'cevrimdisi (snapshot, ag YOK) · ' + _pl
    if _eksik_meal:
        _pl = ('MEAL_EKSIK %d: %s | ' % (len(_eksik_meal), _eksik_meal[0][:70])) + _pl
    # TANIM DAYANIKLILIGI (7 Kasim 2026, OLCULMEYEN kalem 4): plato kaba
    # izgaranin (3-6 kelime) eseri olabilir. Olcut TANIMI degistirilerek
    # (kelime esigi + tekrar sayimi) platonun saglam kalip kalmadigi olculur.
    # Fail-closed: 4/4 tanimda 0.50 plato icinde degilse FAIL.
    # --- KENDI MUTANTINI GORUYOR MU (13 Kasim 2026, Z9) --------------------
    # NEDEN (olculdu): bu kapinin cagrisi `--duyarlilik <yol>` SIRASIYLA
    # yapiliyordu; `ayet_ozet_kontrol.py` ise yolu `argv[1]`den okuyordu ve
    # `--duyarlilik` ONCE gelince argv[1] bir BAYRAK oluyordu -> yol sessizce
    # `SKILL.md`ye dusuyordu. Ayni mutant iki sirada olculdu:
    #     --duyarlilik <mutant> -> "sonuc 6/6 ... n=6 ayet"   (mutant YOK SAYILDI)
    #     <mutant> --duyarlilik -> "sonuc 5/5 ... n=5 ayet"   (dogru)
    # Yani kapi kendi mutasyonunu HIC gormedi: FAIL-OPEN. Metin "6/6" sabit
    # yazildigi surece de iki hal AYNI gorunuyordu.
    # Cozum iki katmanli: (1) arac siradan bagimsiz yol okur; (2) bu kapi KENDI
    # mutantini uretir ve `n=` sayisinin DUSTUGUNU gorur. Ikinci katman olmadan
    # ayni hata yeni bir kilikla geri gelebilir.
    _mut9 = None
    _n9_yol = _n9_mut = None
    try:
        import re as _re9
        import tempfile as _tf9
        with open(YOL, encoding='utf-8') as _f9:
            _metin9 = _f9.read()
        # Bir ayet ozetini 10 karakterin ALTINA dusur -> `ozet_cumlesi` onu
        # bulamaz -> olculebilen ayet sayisi BIR azalir. Baska hicbir sey degismez.
        _m9 = _re9.search(r'\b(\d{1,3}:\d{1,3})\s*:\s*"[^"]{10,300}"', _metin9)
        if _m9 is None:
            _pl = 'MUTANT9: ayet ozeti bulunamadi (desen degisti) | ' + _pl
        else:
            _d9 = _tf9.mkdtemp()
            _mut9 = os.path.join(_d9, 'm9.md')
            with open(_mut9, 'w', encoding='utf-8') as _f9:
                _f9.write(_metin9.replace(_m9.group(0),
                                          '%s: "kisa"' % _m9.group(1), 1))
            _r9b = __import__('subprocess').run(
                [sys.executable, os.path.join(_d6, 'ayet_ozet_kontrol.py'),
                 '--duyarlilik', _mut9],
                capture_output=True, text=True, timeout=120, env=_env9)

            def _n9(stdout):
                for _x in stdout.splitlines():
                    if _x.startswith('PLATO:') and '· n=' in _x:
                        return _x.split('· n=')[1].split(' ')[0]
                return None
            _n9_yol = _n9(_r9.stdout)
            _n9_mut = _n9(_r9b.stdout)
            _pl = 'mutant n=%s (yol n=%s)' % (_n9_mut, _n9_yol) + ' | ' + _pl
    except Exception as _e9:
        _n9_yol = _n9_mut = None
        _pl = 'MUTANT9 CALISTIRILAMADI: %s | ' % _e9 + _pl

    # Fail-closed: plato YOK, tanim 4/4 degil, ya da KENDI MUTANTINI GORMUYOR.
    _pl_ok = ((not _eksik_meal) and _r9.returncode == 0 and any(
        x.startswith('PLATO:') and 'DEGISMIYOR' in x for x in _satirlar)
        and any(x.startswith('SONUC_TANIM: 4/4') for x in _satirlar)
        and _n9_yol is not None and _n9_mut is not None
        and _n9_mut != _n9_yol)
except Exception as _e:
    _pl = 'CALISTIRILAMADI: %s' % _e
k('C14p', 'esik plato icinde + plato TANIMDAN bagimsiz (OLCULMEYEN 2/4)', _pl_ok, _pl)

# --- C14o CALISTIRMALI: GERCEK durum.json semaya uyar (kalem 3) -----------
# NEDEN (7 Kasim 2026, OLCULMEYEN kalem 3): `durum_goc.py` yalniz TEST dosyasinda
# kosmustu; labta GERCEK `durum.json` yoktu (0 adet). Bu kapi gercek dosyayi
# SKILL.md'deki §1.1 json bloguyla karsilastirir: anahtar kumesi AYNI olmali.
# Eksik fazla anahtar -> FAIL (sema kaymasi sessizce gecmesin).
_dj = ''
_dj_ok = False
try:
    _d5 = os.path.dirname(os.path.abspath(__file__))
    _kok = os.path.dirname(_d5)
    _dj_yol = os.path.join(_kok, 'docs', 'skill_denetim', 'durum.json')
    with open(YOL, encoding='utf-8') as _f:
        _skill = _f.read()
    _blk = _skill.split('`durum.json` (makine okur')[1].split('```json', 1)[1].split('```', 1)[0]
    _sema = sorted(__import__('json').loads(_blk).keys())
    with open(_dj_yol, encoding='utf-8') as _f:
        _ger = sorted(__import__('json').load(_f).keys())
    _eksik = [a for a in _sema if a not in _ger]
    _fazla = [a for a in _ger if a not in _sema]
    _dj = 'sema=%d gercek=%d eksik=%s fazla=%s' % (
        len(_sema), len(_ger), _eksik or '-', _fazla or '-')
    _dj_ok = (not _eksik and not _fazla)
except Exception as _e:
    _dj = 'CALISTIRILAMADI: %s' % _e
k('C14o', 'gercek durum.json semaya uyar (kalem 3)', _dj_ok, _dj)

# --- C14n CALISTIRMALI: CEVRIMDISI olcum (snapshot sha) -------------------
# NEDEN (7 Kasim 2026, OLCULMEYEN kalem 2): `C14l`/`C14m` ag bagimliydi; ag yoksa
# lint FAIL donuyordu, yani cevrimdisi ortamda lab HIC yesil olamiyordu.
# Cozum: dis kaynak bir kez indirilip `tests/snapshot/` altina sha256 ile sabitlendi.
# Bu kapi once snapshot'in KENDISINI dogrular, sonra iki olcumu SNAPSHOT_ONLY=1 ile
# (ag yokmus gibi) kosturur. Ikisi de rc=0 olmali.
# FAIL-CLOSED: snapshot bozulursa (sha tutmazsa) rc=1 -> PASS degil.
_cd = ''
_cd_ok = False
try:
    _d4 = os.path.dirname(os.path.abspath(__file__))
    _env = dict(os.environ)
    _env['SNAPSHOT_ONLY'] = '1'
    _r6 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d4, 'snapshot_yenile.py'), '--dogrula'],
        capture_output=True, text=True, timeout=60)
    _r7 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d4, 'sunnah_karsilastir.py'), YOL, '6094'],
        capture_output=True, text=True, timeout=60, env=_env)
    _r8 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d4, 'ayet_ozet_kontrol.py'), YOL],
        capture_output=True, text=True, timeout=90, env=_env)
    _yas = [x for x in _r6.stdout.splitlines() if x.startswith('YAS:')]
    # [DUZELTME 2026-11-12, Z7] DOSYA BAZLI YAS + MTIME KAYMASI gorunur olsun.
    # NEDEN (olculdu): manifestte TEK global tarih vardi; mutasyon testlerinde
    # 3 snapshot dosyasi geri yazilinca mtime bugune kaydi ama global tarih
    # bunu gostermedi. Artik `--dogrula` bunlari AYRI satirlarda yaziyor.
    _yasd = [x for x in _r6.stdout.splitlines() if x.startswith('YAS_DOSYA:')]
    _mtime = [x for x in _r6.stdout.splitlines() if x.startswith('MTIME_KAYMASI:')]
    _cd = 'snapshot rc=%d "%s" · %s · %s · %s · sunnah rc=%d · ayet rc=%d "%s"' % (
        _r6.returncode,
        (_r6.stdout.strip().splitlines() or ['<bos>'])[-1][:60],
        (_yas or ['YAS: BILINMIYOR'])[0][:40],
        (_yasd or ['YAS_DOSYA: BILINMIYOR'])[0][:90],
        (_mtime or ['MTIME_KAYMASI: BILINMIYOR'])[0][:60],
        _r7.returncode, _r8.returncode,
        (_r8.stdout.strip().splitlines() or ['<bos>'])[-1][:40])
    # YAS DAMGASI (7 Kasim 2026, OLCULMEYEN kalem 3): snapshot eskir; tarih YOKSA
    # da FAIL — tarihsiz snapshot "ne zamanki dunya" sorusunu cevaplayamaz.
    # Z7: dosya bazli yas satiri DA zorunlu — global tarih tek basina yetmez.
    _cd_ok = (_r6.returncode == 0 and _r7.returncode == 0
              and _r8.returncode == 0
              and bool(_yas) and 'BILINMIYOR' not in _yas[0]
              and bool(_yasd) and 'BILINMIYOR' not in _yasd[0]
              and 'snapshot (sha dogrulandi)' in _r7.stdout)
except Exception as _e:
    _cd = 'CALISTIRILAMADI: %s' % _e
k('C14n', 'cevrimdisi olcum calisir + snapshot YASI bilinir (kalem 2/3)', _cd_ok, _cd)

# --- C14m CALISTIRMALI: Turkce ayet ozetleri (kalem 1) --------------------
# NEDEN: L456 "Turkce satirlar serbest ozet" diyordu ama HIC OLCULMEMISTI.
# Olcut: ozetin anahtar kavramlari `tr.diyanet` cevrisinde geciyor mu?
# Bu "birebir ceviri" olcumu DEGILDIR; "ozet uydurma degil" olcumudur.
# FAIL-CLOSED: ag yoksa PASS degil FAIL (ag olmadan iddia dogrulanamaz).
_ay = ''
_ay_ok = False
try:
    _d3 = os.path.dirname(os.path.abspath(__file__))
    # CEVRIMDISI (14 Kasim 2026, Z22 / C14m) --------------------------------
    # NEDEN (olculdu): burasi env GECMIYORDU -> `ceviri()` once CANLIya
    # gidiyordu. Olcum: ayni komut **canli 16,14 s** vs **SNAPSHOT_ONLY=1
    # 0,11 s** = **146,9x**, ve her lint kosusunda **144 HTTP istegi**
    # (16 ayet x 9 meal). Daha kotusu: ag ACIKKEN bu kapi snapshot'i
    # GORMUYORDU — bozuk meal mutasyonunda (M117) FAIL listesi
    # [C14p, C14n, C15k] idi, C14m **yoktu**; agsiz kosuda ise
    # [C14p, C14n, C14m, C15k]. Yani ag acikken kapi KORDU (fail-OPEN).
    # Kardesleri `C14n`/`C15l`/`C15k` bu env'i Z18d'de zaten veriyordu.
    # AYRICA `kaynak=snapshot` aranir: olcumun NEREDEN geldigi iddianin
    # parcasi olsun (once `SONUC` satiri kaynagi hic soylemiyordu).
    _env5 = dict(os.environ)
    _env5['SNAPSHOT_ONLY'] = '1'
    _r5 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d3, 'ayet_ozet_kontrol.py'), YOL],
        capture_output=True, text=True, timeout=90, env=_env5)
    _ay = (_r5.stdout.strip().splitlines() or ['<bos>'])[-1]
    if _r5.returncode != 0:
        _ay += ' | ' + ((_r5.stderr.strip().splitlines() or ['<bos>'])[0])
    # MEAL_HATA (14 Kasim 2026, Z21 / C-#4) ---------------------------------
    # NEDEN (olculdu): bozuk bir snapshot dosyasi (sha TUTUYOR ama `data.text`
    # yok) `ayet_ozet_kontrol`de "HATA" yaziliyor, meal `gecen`e GIRMIYOR,
    # pay 8/9 = 0.89 cikiyor ve `MEAL_ESIK=0.5` bunu AFFEDIYORDU -> ayet TAM
    # -> rc=0 -> bu kapi YESIL. Yani bir meali kaybetmek olcumu gecirirdi.
    # Betik artik rc=1 doner; burada AYRICA `meal_hata=0` aranir: iki
    # bagimsiz isaret, tek sessiz gecis yolu kalmasin.
    if 'meal_hata=0' not in _ay:
        _ay_ok = False
        _ay += ' | HATA: meal_hata=0 YOK (okunamayan meal var ya da alan ' \
               'kaldirildi)'
    elif 'kaynak=snapshot' not in _ay:
        # Ag acikken kapi canliya kacarsa kaynak=canli olur -> KOR olur.
        _ay_ok = False
        _ay += ' | HATA: kaynak=snapshot YOK (olcum canliya gitmis ya da ' \
               'kaynak alani kaldirilmis)'
    else:
        _ay_ok = (_r5.returncode == 0)
except Exception as _e:
    _ay = 'CALISTIRILAMADI (ag?): %s' % _e
k('C14m', 'Turkce ayet ozetleri 9 meal ile olculdu (kalem 1)', _ay_ok, _ay)

# --- C14l CALISTIRMALI: sunnah.com birebir aynilik (kalem 2) --------------
# NEDEN: iddia bir tur "GERI ALINDI" (OLCULMEDI) idi cunku `webfetch` yaniti
# dosyada yoktu. Artik her kosuda YENIDEN olculur: sayfa cekilir, alinti
# sayfadaki Arapca bloklarla normalize karsilastirilir.
# FAIL-CLOSED: ag yoksa PASS DE GIL, sessiz atlama da YOK -> FAIL.
# Gerekce: "sayfada birebir var" iddiasi ancak agla dogrulanir; ag yoksa
# o iddia OLCULMEMIS olur ve yesil gosterilemez.
_sn = ''
_sn_ok = False
try:
    _d2 = os.path.dirname(os.path.abspath(__file__))
    _r4 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d2, 'sunnah_karsilastir.py'), YOL, '6094'],
        capture_output=True, text=True, timeout=60)
    _sn = (_r4.stdout.strip().splitlines() or ['<bos>'])[-1]
    if _r4.returncode != 0:
        _sn += ' | ' + ((_r4.stderr.strip().splitlines() or ['<bos>'])[0])
    _sn_ok = (_r4.returncode == 0 and 'ESIT' in _r4.stdout)
except Exception as _e:
    _sn = 'CALISTIRILAMADI (ag?): %s' % _e
k('C14l', 'sunnah.com ile birebir aynilik calistirmali (kalem 2)', _sn_ok, _sn)

# --- C14q CALISTIRMALI: hadis TURKCE metni bagimsiz kaynakla olculdu ------
# NEDEN (7 Kasim 2026, `OLCULMEYEN` hadis Turkce cevirisi): Arapca sunnah.com
# ile sabitlenmisti ama Turkce ceviri "bu dosyanin metnidir, bagimsiz
# dogrulanmadi" idi. Ilk olcum KUSUR BULDU: Buhari 39 cevirisi bagimsiz
# kaynakla **1/9 (0.11) SAPMA** veriyordu; metin resmi ceviriyle degistirildi.
# Bu kapi o duzeltmenin geri kaymasini engeller.
# Kaynak: hadeethenc.com (muttefekun/sahih kunyesiyle). Ag yoksa script
# SHA'SI TUTAN snapshot'a duser; sha tutmazsa rc!=0 -> FAIL (fail-closed).
_ht = ''
_ht_ok = False
try:
    _d7 = os.path.dirname(os.path.abspath(__file__))
    # [DUZELTME 2026-11-12, Z4] AG BAGIMLILIGI KALDIRILDI. Bu kapi
    # `hadis_tr_karsilastir.py`yi ENV GECMEDEN cagiriyordu; betik
    # `SNAPSHOT_ONLY != "1"` gorunce CANLI gidiyordu. OLCULDU: ciktida
    # `HTTP 200`, `user 0,04 s`. `C14p`de kapatilan sinifin AYNISI burada
    # acik kalmisti: yavas agda 90 s timeout -> kapi kirmizi. Artik snapshot.
    _env7 = dict(os.environ)
    _env7['SNAPSHOT_ONLY'] = '1'
    _r10 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d7, 'hadis_tr_karsilastir.py'), YOL],
        capture_output=True, text=True, timeout=90, env=_env7)
    _sat = _r10.stdout.strip().splitlines()
    _ht = (_sat or ['<bos>'])[-1][:120]
    _ht_ok = (_r10.returncode == 0 and 'TAM' in _ht
              and _ht.startswith('SONUC: 2/2 '))
    _ht = 'cevrimdisi (snapshot, ag YOK) · ' + _ht

    # --- YOLU YOK SAYIYOR MU (13 Kasim 2026, Z10) -------------------------
    # NEDEN (olculdu): `yol = argv[1] if not argv[1].startswith('--')` deseni
    # bayrak ONCE gelince yolu SESSIZCE `SKILL.md`ye dusuruyordu. Ayrım edici
    # test OLMAYAN bir yoldur: dogru arac rc=2 vermeli. Olculdu (once):
    #   `hadis_tr_karsilastir.py --kunye /yok/boyle.md` -> rc=0
    #     "SONUC: 2/2 hadis TAM"      <-- yolu YOK SAYDI, gercek SKILL'i okudu
    #   `/yok/boyle.md --kunye`                          -> rc=2 "HATA: okunamadi"
    # Bu sinif `ayet_ozet_kontrol.py`de de vardi (Z9/EK 79). Bir kapi kendi
    # mutasyonunu gormuyorsa fail-OPEN'dir; bu sinama onu her kosuda olcer.
    _yok7 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d7, 'hadis_tr_karsilastir.py'),
         '--kunye', os.path.join(_d7, 'BOYLE_BIR_DOSYA_YOK.md')],
        capture_output=True, text=True, timeout=60, env=_env7)
    _yolok7 = (_yok7.returncode != 0)
    _ht_ok = _ht_ok and _yolok7
    _ht = ('yol_sinama rc=%d %s · ' % (_yok7.returncode,
                                       'OK' if _yolok7 else 'YOL_YOK_SAYILDI')) + _ht
except Exception as _e:
    _ht = 'CALISTIRILAMADI: %s' % _e
k('C14q', 'hadis TURKCE metni bagimsiz kaynakla olculdu (hadeethenc) + yol siranmaz', _ht_ok, _ht)

# --- C14r CALISTIRMALI: hadeethenc ID eslesmesi ARAPCA ile kanitlandi -----
# NEDEN (7 Kasim 2026, OLCULMEYEN kalem 2): `C14q` id eslesmesine DAYANIYOR,
# ama o eslesme elle (Turkce baslikla) yapilmisti. Eslesme yanlissa C14q
# yanlis hadisi olcer. Bu kapi eslesmeyi ARAPCA obek ortusmesiyle kanitlar.
# ILK OLCUT YANLISTI (olculdu): "birebir alt dizgi" Buhari 6094'te tutmadi —
# sebep yanlis id degil, FARKLI RIVAYET. Olcut obek ortusmesine cevrildi ve
# farkli lafizlar gizlenmeden yazdiriliyor.
_id = ''
_id_ok = False
try:
    _d8 = os.path.dirname(os.path.abspath(__file__))
    # [DUZELTME 2026-11-12, Z4] AG BAGIMLILIGI KALDIRILDI (C14q ile ayni sinif).
    # OLCULDU: bu betik de env gelmeyince canliya gidiyordu; snapshot yolu
    # `hadeeth_<no>__ar.json` + sha dogrulamasi ile AYNI sonucu veriyor
    # (NEGATIF KONTROL + AYIRT_EDIYOR satirlari birebir ayni).
    _env8 = dict(os.environ)
    _env8['SNAPSHOT_ONLY'] = '1'
    _r11 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d8, 'hadis_id_dogrula.py'), YOL],
        capture_output=True, text=True, timeout=90, env=_env8)
    _sat2 = _r11.stdout.strip().splitlines()
    # NEGATIF KONTROL (7 Kasim 2026, OLCULMEYEN kalem 5): esik 0.50'nin duyarliligi
    # OLCULDU — dogru eslesme 0.53-1.00, yanlis 0.00, esik ust KENARDA (marj 0.03).
    # Yani "0.50 gecti" tek basina zayif; asil kanit AYRIM'in varligidir.
    _neg = [x for x in _sat2 if x.startswith(('NEGATIF KONTROL:', 'ESIK:'))]
    _id = ((_sat2 or ['<bos>'])[-2][:70] + ' · ' +
           ((_sat2 or ['<bos>'])[-1][:25]) + ' · ' +
           ' · '.join(_neg))[:230]
    _id_ok = (_r11.returncode == 0 and any(x.startswith('SONUC: 2/2 ') for x in _sat2)
              and any('AYIRT_EDIYOR' in x for x in _sat2))
    _id = 'cevrimdisi (snapshot, ag YOK) · ' + _id

    # YOL SINAMASI (Z10, C14q ile ayni sinif): olmayan yol -> rc!=0 olmali.
    _yok8 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d8, 'hadis_id_dogrula.py'),
         '--kunye', os.path.join(_d8, 'BOYLE_BIR_DOSYA_YOK.md')],
        capture_output=True, text=True, timeout=60, env=_env8)
    _yolok8 = (_yok8.returncode != 0)
    _id_ok = _id_ok and _yolok8
    _id = ('yol_sinama rc=%d %s · ' % (_yok8.returncode,
                                       'OK' if _yolok8 else 'YOL_YOK_SAYILDI')) + _id
except Exception as _e:
    _id = 'CALISTIRILAMADI: %s' % _e
k('C14r', 'hadis id eslesmesi ARAPCA + NEGATIF KONTROL ayirt ediyor + yol siranmaz', _id_ok, _id)

# --- C14k CALISTIRMALI: INJECTION_ATTEMPT sarti GERCEKTEN denetlenir -------
# NEDEN (7 Kasim 2026, kalem 8): §8.2/6 sarti `n == len(durum.json.injection)`
# diyordu ama ELLE denetleniyordu; `C13t` yalniz metnin varligini olcuyordu.
# Bu kapi sarti kosar: uyum -> 0, uyumsuz -> 1, tip hatasi -> 1 (fail-closed).
_k1 = _k1o = _k2 = _k2o = 0
try:
    _d = os.path.dirname(os.path.abspath(__file__))
    _r = __import__('subprocess').run(
        [sys.executable, os.path.join(_d, 'injection_sayac.py'),
         os.path.join(_d, 'tests', 'manifest_inj_uyum.md'),
         os.path.join(_d, 'tests', 'durum_inj_uyum.json')],
        capture_output=True, text=True, timeout=30)
    _k1, _k1o = _r.returncode, (_r.stdout.strip().splitlines() or ['<bos>'])[-1]
    _r2 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d, 'injection_sayac.py'),
         os.path.join(_d, 'tests', 'manifest_inj_uyumsuz.md'),
         os.path.join(_d, 'tests', 'durum_inj_uyum.json')],
        capture_output=True, text=True, timeout=30)
    _k2, _k2o = _r2.returncode, (_r2.stderr.strip().splitlines() or ['<bos>'])[0]
except Exception as _e:
    _k1o = 'CALISTIRILAMADI: %s' % _e
k('C14k', 'INJECTION_ATTEMPT sarti calistirmali: uyum=0 / uyumsuz=1 (kalem 8)',
  (_k1 == 0 and _k2 == 1), 'uyum rc=%d "%s" · uyumsuz rc=%d "%s"'
  % (_k1, _k1o, _k2, _k2o))

# --- C14i CALISTIRMALI: `durum.json` gocu gercekten kosar -----------------
# NEDEN (7 Kasim 2026, kalem 7): `sir` gocu KURALI yaziliydi ama diskte
# `durum.json` 0 adet oldugu icin goc HIC CALISTIRILMAMISTI — "kural var,
# mekanizma yok" (D19 dersinin aynisi). Bu kapi gocu gercek bir ornek dosyada
# kosar: eksik anahtar eklenir, VERI DEGISMEZ, ikinci kosu "gerekmedi" der.
# Mutasyon: veri degistiren goc -> VERI_DEGISMEDI=HAYIR -> FAIL (olculdu).
_goc = ''
_goc_ok = False
try:
    _tmpd = __import__('tempfile').mkdtemp()
    _src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'tests', 'durum_eski_sema.json')
    _dst = os.path.join(_tmpd, 'durum.json')
    __import__('shutil').copyfile(_src, _dst)
    _r1 = __import__('subprocess').run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'durum_goc.py'), _dst],
        capture_output=True, text=True, timeout=30)
    _r2 = __import__('subprocess').run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'durum_goc.py'), _dst],
        capture_output=True, text=True, timeout=30)
    _l1 = _r1.stdout.strip().splitlines()
    _goc = _l1[-1] if _l1 else '<bos>'
    _goc_ok = (_r1.returncode == 0 and 'VERI_DEGISMEDI: evet' in _r1.stdout
               and 'EKLENEN: sir' in _r1.stdout
               and 'GOC_GEREKMEDI: evet' in _r2.stdout)
    __import__('shutil').rmtree(_tmpd, ignore_errors=True)
except Exception as _e:
    _goc = 'CALISTIRILAMADI: %s' % _e
k('C14i', 'durum.json gocu gercekten kosar (kalem 7)', _goc_ok, _goc)

# --- C14j CALISTIRMALI: goc bozuk veride FAIL-CLOSED ----------------------
# Mutasyon M3'te olculdu: `sir` anahtari VAR ama tipi `str` ise eski surum
# sessizce geciyordu ("goc edildi" damgasi alip bozuk kaliyordu).
_gj = ''
_gj_ok = False
try:
    _tmpd2 = __import__('tempfile').mkdtemp()
    _bad = os.path.join(_tmpd2, 'bozuk.json')
    with open(_bad, 'w', encoding='utf-8') as _f:
        _f.write('{"asama":"K0","sir":"x"}')
    _r3 = __import__('subprocess').run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'durum_goc.py'), _bad],
        capture_output=True, text=True, timeout=30)
    _gj = (_r3.stderr.strip().splitlines() or ['<bos>'])[0]
    _gj_ok = (_r3.returncode == 1 and 'tip hatasi' in _r3.stderr)
    __import__('shutil').rmtree(_tmpd2, ignore_errors=True)
except Exception as _e:
    _gj = 'CALISTIRILAMADI: %s' % _e
k('C14j', 'goc bozuk tipde fail-closed (kalem 7)', _gj_ok, _gj)

# --- C13z CALISTIRMALI: hadis kelime sayimi -------------------------------
# NEDEN CALISTIRMALI (7 Kasim 2026, D2): capa yalniz CUMLEYI olcer, DOGRULUGUNU
# olcmez — bu, C13 ailesinin bilinen yapisal siniridir. Bu kapi siniri bir
# noktada kapatir: `scripts/hadis_olcum.py` gercekten kosar ve 34/18 tutmazsa FAIL.
# Mutasyon: sayiyi 18->19 yap -> rc=1 -> FAIL (olculdu).
_g13z = ''
_g13z_ok = False
try:
    _r = __import__('subprocess').run(
        [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'hadis_olcum.py'), YOL, '--bekle', '34', '18'],
        capture_output=True, text=True, timeout=30)
    _g13z = (_r.stdout.strip().splitlines() or [''])[-1]
    _g13z_ok = (_r.returncode == 0)
    if not _g13z_ok:
        _g13z += ' | ' + (_r.stderr.strip().splitlines() or [''])[0]
except Exception as _e:                       # betik yoksa FAIL, sessiz gecme
    _g13z = 'CALISTIRILAMADI: %s' % _e
k('C13z-a', 'hadis kelime sayimi calistirmali (D2)', _g13z_ok, _g13z)


# --- C14s CALISTIRMALI: markdown vurgu butunlugu (D1 SINIFI, 8 Kasim 2026) ---
# NEDEN: `C13v` tek bir diziyi (`)*)`) ariyordu — SINIFI degil. 3. turda iki model
# "tek satir kontrolu sinifi kapatmaz" dedi; hakliydi. Sinif = COZULMEMIS vurgu
# isareti: ayristirici metin dugumunde literal `*` birakiyorsa vurgu kapanmamis.
# Bu kontrol dosyada GERCEK iki kusur buldu ve ikisi de duzeltildi (8 Kasim 2026):
# (a) `...kullanildi.) *(7 Kasim...` — italik `*` kapanmamis; (b) `**desteklemez**.)*`
# — sahipsiz `)*`. Mutasyon: vurgu bozuldugunda literal `*` sayisi 0'dan 3'e cikar.
_g14s = ''
_g14s_ok = False
try:
    from markdown_it import MarkdownIt as _MD

    def _yildiz(dugumler):
        for _t in dugumler:
            if _t.type == 'inline' and _t.children:
                for _c in _t.children:
                    if _c.type == 'text' and '*' in _c.content:
                        yield _c.content
            elif _t.children:
                yield from _yildiz(_t.children)

    _kalan = list(_yildiz(_MD('commonmark').parse(C)))
    _g14s = 'literal *: %d%s' % (
        len(_kalan), (' — ' + _kalan[0][:48].replace('\n', ' ')) if _kalan else '')
    _g14s_ok = (len(_kalan) == 0)
except ImportError:
    _g14s = 'CALISTIRILAMADI: markdown_it yok (elle: vurgu isaretlerini say)'
except Exception as _e:
    _g14s = 'CALISTIRILAMADI: %s' % _e
k('C14s', 'markdown vurgu butunlugu — literal * yok (D1 sinifi)', _g14s_ok, _g14s)

# --- C19 CALISTIRMALI: parantez dengesi + `_` vurgusu (D1 sinifi, tur 11) ----
# NEDEN (12 Kasim 2026, DIS DENETIM TUR 11): 6/17 model dedi ki `C14s` yalniz
# `*` ariyor; `_` vurgusu ve parantez dengesi OLCULMUYOR. Lab olctu ve HAKLI
# buldu: SKILL.md'ye ciplak `))` eklendi -> `C13v PASS` · `C14s PASS` (rc=1
# veren 4 FAIL kimlik/boyut kapilariydi). `C13v` capasi literal `)*)` dizesidir;
# ciplak `))` o dizeye GIRMEZ. Yani D1 sinifi kapanmamisti.
#
# COZUM: iki YOKLUK olcumu — donmus sayi yok.
#   (1) ESLESMEYEN KAPANIS parantezi = 0. Yigin taramasi; kod araliklari ve
#       `N)` numaralandirmasi MESRU oldugu icin cikarilir.
#   (2) `_` vurgu deseni = 0. Belge `_` vurgusu kullanmiyor (olculdu: 0).
# OLCULEN SINIR (gizlenmiyor): eslesmeyen ACILIS = 25 — cok satirli parantezler.
# [DUZELTME 2026-11-12, Y0] Burada 42 yaziyordu; olculdu ve YANLIS cikti.
# Sebep asagidaki numara-ayiklama kalibiydi: `§X.Y)` biciminde kapanis
# parantezini siliyordu (17 kez). Dogrusu 25.
# Bu sayi `C19`'da GATE EDILMIYOR, yalniz raporlanir. #2 (12 Kasim 2026) bu
# sayiyi `C16`'da BEYAN EDILEN sayac yapar (S10): gate etmek yerine, sessizce
# oynayamaz hâle getirir. Ayni sayiyi iki kapi olcerse algoritma TEK olmali.


def _parantez_tara(metin):
    """(eslesmeyen_kapanis, eslesmeyen_acilis, kapanmamis_backtick) — TEK TANIM.

    NEDEN fonksiyon (12 Kasim 2026, #2): `C19` sayiyi raporluyor, `C16` beyan
    olarak olcuyor. Iki yerde AYNI algoritma kosmali; kopya kod bir gun ayrisir
    ve kapi yanlis seyi dogru sayar. Kod araliklari ve `N)` numaralandirmasi
    MESRU oldugu icin cikarilir. Yigin PARAGRAF BASINA sifirlanir (M48 dersi:
    tek yigin bekleyen acilislari yutar ve kapi kor kalir; sayi 2026-11-12'de
    duzeltildi: 42 degil 25).
    """
    # [DUZELTME 2026-11-12, Y2] FENCE BLOKLARI once TAMAMEN cikarilir. Eskiden
    # yalniz satir ici kod araligi (`x`) siliniyordu; ``` blogunun ICINDEKI
    # parantezler "metin" sayiliyordu. Olculdu (SKILL.md, Y2): 7 blogun hepsi
    # dengeli -> sayi degismedi (25). Ama dengesiz bir ornek eklenirse sayaci
    # sessizce kaydirirdi; artik kod blogu metin degildir.
    _m = re.sub(r'(?ms)^[ \t]*```[^\n]*\n.*?^[ \t]*```[ \t]*$', '', metin)
    _m = re.sub(r'`[^`\n]*`', '', _m)
    # KAPANMAMIS BACKTICK = OLCUM GUVENILMEZ. Kapanmayan satir ici aralik,
    # kalibin metnin geri kalanini YUTMASINA yol acar; parantez sayaci sessizce
    # kayar. Bu Y0'in KARDESIDIR (ayni sinif: mesru olmayan silme). Artik
    # yutulan metin sayilir ve cagirana bildirilir; hüküm fail-closed verilir.
    _arti = _m.count('`')
    # [DUZELTME 2026-11-12, Y0] ESKI KALIP: `(?<![\w(])\d\)`. OLCULDU:
    # `§0.7)` dizisindeki `7)` 'numara' sanilip SILINIYORDU -> gercek
    # kapanis yok oluyor, acilis sahte kaliyordu. Fark tam olarak
    # `§X.Y)` sayisi kadar: 17. Yani sayi 42 degil 25'ti.
    # YENI: `.` da haric -> `§0.7)` korunur, `1) secenek` hala ayiklanir.
    #
    # [DUZELTME 2026-11-12, Y3] O KALIP DA EKSIKTI — KALIP TAMAMEN KALKTI.
    # Olculdu: kalip 32 yerde esliyor; bunlarin yalniz 6'si GERCEK
    # numaralandirma (`1) evet`), 26'si MESRU KAPANIS (`§2)`, `rc=0)`,
    # `3/4)`, `Hucurat 49:6)`, `sayac 1→2)`, `(kod: 0)`). Yani kalip 26 gercek
    # kapanisi yiyor, 24 SAHTE acik uretiyordu: 25 gosteriyordu, dogrusu 1.
    # KALIP YERINE KURAL: ')' YIGIN BOSKEN ve bir rakamin ardindan geliyorsa
    # NUMARALANDIRMADIR ( `1) evet` ); YIGIN DOLUYSA KAPANISTIR ( `(§2)` ).
    # Karar karaktere degil, o anki yigina bakar. Kalip yok, karar var.
    _kapali = _yig = 0
    for _p in re.split(r'\n\s*\n', _m):
        _y = 0
        _i = 0
        _n = len(_p)
        while _i < _n:
            _ch = _p[_i]
            if _ch == '(':
                _y += 1
            elif _ch == ')':
                if _y:
                    _y -= 1
                else:
                    _j = _i - 1
                    while _j >= 0 and _p[_j].isdigit():
                        _j -= 1
                    _num = ((_j < _i - 1) and
                            (_j < 0 or not (_p[_j].isalnum() or
                                            _p[_j] in '._')))
                    if not _num:
                        _kapali += 1
            _i += 1
        _yig += _y
    return _kapali, _yig, _arti


_g19 = ''
_g19_ok = False
try:
    # YIGIN PARAGRAF BASINA SIFIRLANIR. NEDEN (12 Kasim 2026, M48): belge
    # genelinde 25 ESLESMEYEN ACILIS var (cok satirli parantezler). Tek yigin
    # kullanilinca ciplak '))' bu aciklardan ikisini YUTUYOR ve kapi KOR kaliyor
    # (not: burada once 42 yaziyordu, Y0 ile duzeltildi)
    # (olculdu: M48 -> eslesmeyen kapanis=0, rc yalniz kimlik kapilarindan 1).
    # Paragraf basina sifirlayinca ayni mutasyon 2 eslesmeyen kapanis veriyor.
    _kapali, _yig, _arti_bt = _parantez_tara(C)
    _alt = re.findall(r'(?<![\w`])_[^\s_][^_\n]*[^\s_]_', C)
    _g19 = ('eslesmeyen kapanis=%d · _ vurgu=%d · eslesmeyen acilis=%d (beyan S10)'
            % (_kapali, len(_alt), _yig))
    if _arti_bt:
        _g19 += ' · KAPANMAMIS BACKTICK=%d (olcum guvenilmez)' % _arti_bt
    _g19_ok = (_kapali == 0 and not _alt and _arti_bt == 0)
except Exception as _e:
    _g19 = 'CALISTIRILAMADI: %s' % _e
k('C19', 'parantez dengesi + _ vurgusu (D1 sinifi, tur 11)', _g19_ok, _g19)

# --- C14t CALISTIRMALI: gomulu sayac iddiasi — RAKAM DEGIL (D10b) -----------
# TARIHCE: once `C13x` (rakam+kontrol), sonra 2 desen, sonra 7 desen.
# 8 Kasim 2026'da OLCULDU: 7 desen, anlamli bicim uzayinin (1190 yazim)
# yalniz **%32'sini** yakaliyordu. "Desen ekle" yaklasimi yanlisti — her
# ekleme bir sonraki bicimi kaciriyordu. DORDUNCU kez KURALA cevrildi:
#   (sayi) (ayirici<=6) (sayac-kelimesi)   ve   ters sira   ve   ozel bicimler
# Ayirici: bosluk, tire, iki nokta, esittir, parantez, em-dash.
# "7.1" icindeki rakam sayilmaz ((?<![\w.])) — labin gercek basligini yakmaz.
# `sayac 1 -> 2` yakilmaz: ok isareti SAYIM DEGIL, artis tarifidir.
_SOZ_ONEK = (r'(?:bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on|yirmi|otuz|'
             r'kırk|elli|altmış|yetmiş|seksen|doksan|yüz)')
_SOZ = r'(?:' + _SOZ_ONEK + r'|altmis|yetmis)'      # ASCII varyant
_RAKAM = r'(?<![\w.])\d+(?![\w.])'
# ROMA RAKAMI (8 Kasim 2026). Iki asama:
#   1) Ilk yazim ACIK LISTE (I..L) idi — "XLI kontrol" adli bicim kaciyordu.
#   2) Ikinci yazim yine ACIK LISTE. Bu, "sayac 50'yi gecmez" KABULUne
#      dayaniyordu — olcum degil. Ayni hastalik (numaralandirma) tekrar etmis.
#      [GECERSIZ] _ROMA_LISTE kaldirildi; yerine GRAMER kurali geldi.
# Kural: M*(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})
#   - uzunluk sinirsiz (LI, XLIX, MMXXVI de yakalanir)
#   - B-4 (9 Kasim 2026): once `M{0,4}` yazdim — bu da bir UST SINIR kabulu.
#     Olculdu: 5000 (MMMMM), 9999 ve 10000 KACIYORDU. `M*` yapildi.
#     264 lab belgesinde olculdu: `M*` FAZLA eslesme getirmedi (0 yeni).
#   - gecersiz dizileri reddeder (IIII, IC, IL, VV, VX — olculdu)
#   - lookahead `(?=[IVXLCDM])` bos eslesmeyi engeller
#   - `(?<![A-Za-z])`/`(?![A-Za-z])` kelime icinde eslesmeyi engeller
# Mesru kullanim yakilmaz: "II. Dunya Savasi", "Madde IV", "tip I hata" —
# cunku Roma TEK BASINA yetmez, SAYAC KELIMESI veya "kapi" gerekir.
_ROMA = (r'(?<![A-Za-z])(?=[IVXLCDM])'
         r'M*(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})'
         r'(?![A-Za-z])')
_NUM = r'(?:' + _RAKAM + r'|' + _SOZ + r'(?:[\s\-]+' + _SOZ + r')?|' + _ROMA + r')'
# D10 (11 Kasim 2026): `test` ve `capa` labin KENDI sayaclaridir
# (`atlas_selftest` test sayisi, `C13` capa sayisi) ama sozlukte yoktu —
# `86 test` / `86 capa` kaciyordu. Olculdu: SKILL.md'de ikisi de 0 eslesme
# (yani kapi bugun kirmizi yanmaz). `madde` (306 korpus), `kalem` (85) ve
# keywordsuz `adet: 67` (98, tanimlayici adlari) EKLENMEDI — gerekce DERSLER'de.
# D10 (11 Kasim 2026, ikinci adim): `kalem` de labin KENDI sayacidir
# (`lab_full` kac kalem kosturdu). EK 45'te "once okuyan kapi yaz" diye
# ertelendi; olcum o ertelemeyi curuttu — SKILL.md'de `kalem` iceren tek
# rakamli ifade `9 kalem` idi ve o zaten GOMULU SAYACTIR (D10'un yasakladigi
# sey). Onu "okuyan kapi" yazmak yanlis seyi dogrulamak olurdu. Sayi
# belgeden KALDIRILDI, sozluge `kalem` eklendi.
_KW = r'(?:kontroller|kontrol|gate|checks|check|test|capa|kalem)'
_KAPI = r'(?:kap[ıi]lar[ıi]?|kap[ıi])'
# D10-kalem (11 Kasim 2026): `kalem` kw-num yonunde YANLIS POZITIF uretiyor.
# Olculdu (SKILL.md L464-465): "OLCULMEYEN kalem 5" / "kalem 4" = KALEM
# NUMARASI, sayi iddiasi degil. Turkcede sayac SONRA ("9 kalem"), numara
# ONCE ("kalem 5") gelir; ayrim AYIRICIDA: "kalem: 9" sayactir.
# Bu yuzden `kw-num` deseni `kalem` DISINDA kosar; kalem icin ayri kural.
_KW_KSN = r'(?:kontroller|kontrol|gate|checks|check|test|capa)'
_AY = r'[\s\-:=\u2014\u2013()\[\]]{0,6}'
# D10 (11 Kasim 2026): sayi ile sayac kelimesi arasina bir BIRIM adi girebiliyor —
# "67 adet kontrol", "kontrol adedi: 67", "gate count: 67". `_AY` bunlari
# yakalayamaz cunku `adet` HARF tasir, ayirici degil. Bu bir SOZLUK genisletmesi
# degil, DILBILGISI duzeltmesidir: yalniz ZATEN sayac kelimesi olan bicimlere
# uygulanir, yani yeni bir kelime sinifi acmaz.
# "9 adet 404 dondu" gibi birim kullanan MESRU cumle yakilmaz: orada sayac
# kelimesi yok.
_BIRIM = r'(?:adet|tane|adedi|count)'
_AYB = _AY + r'(?:' + _BIRIM + _AY + r')?'
# SINIR (olculdu, gizlenmiyor): sozcuk sayi + TEK "kapi" ("iki kapi") yakilmaz.
# Sebep: labin kendi basligi ayni bicimde ("7.1 Iki kapi."). Bilesik sayi
# ("yetmis iki kapi"), rakam ("67 kapi"), ROMA ("XLI kapi"), iki nokta ve
# "toplam" bicimleri YAKILIR. Kalan acik: yalniz o tek bicim.
_SAYAC_KURAL = [
    ('num-kw',        _NUM + _AYB + _KW + r'\b'),
    ('kw-num',        r'\b' + _KW_KSN + _AYB + _NUM),
    ('kapi-rakam',    _RAKAM + _AYB + _KAPI + r'\b'),
    ('kapi-roma',     _ROMA + _AY + _KAPI + r'\b'),
    ('kapi-bilesik',  _SOZ + r'[\s\-]+' + _SOZ + _AY + _KAPI + r'\b'),
    ('kapi-nokta',    r'\b' + _KAPI + r'\s*[:=]\s*' + _NUM),
    ('kapi-toplam',   r'\btoplam\s+' + _NUM + _AYB + _KAPI + r'\b'),
    ('kapi-tire-soz', _SOZ + r'\-' + _KAPI + r'\b'),
    ('sayac',         r'\bsaya[cç][ıi]?\s*[:=]?\s*' + _NUM
                      + r'(?!\s*(?:\u2192|->|=>))'),
    ('sayisi',        r'\bsay[ıi]s[ıi]\s*[:=]?\s*' + _NUM),
    # D10 ikinci tekrar (11.11.2026): `madde` ve kelimesiz `adet:` -- EK 45'te
    # 'hepsi madde isareti' gerekcesiyle REDDEDILMISTI; YENIDEN OLCUM o gerekceyi
    # CURUTTU (311 eslesme: 3 isaret, 2 sira numarasi, ~305 gercek sayac).
    # num-madde: iki istisna OLCULDU -- '§10' bolum numarasi, '3-5' aralik.
    ('num-madde',    r'(?<![\u00a7\w.\-\u2013\u2014\d])\d+(?![\w.])' + _AY
                     + r'madde\b'),
    ('madde-nokta',  r'\bmadde\s*[:=]\s*' + _NUM),
    ('adet-nokta',   r'(?<![\w.])adet\s*[:=]\s*' + _NUM),
    # D10-kalem: `kalem` SAYAC olarak yalniz AYIRICILI yazilir ("kalem: 9").
    ('kalem-nokta',   r'\bkalem\s*[:=]\s*' + _NUM),
]
_SAYAC_DER = [(ad, re.compile(d, re.I)) for ad, d in _SAYAC_KURAL]


def _sayac_bul(metin):
    """[(kural_adi, eslesen_metin)] — yasak sayac iddialari."""
    return [(ad, m.group(0)) for ad, d in _SAYAC_DER for m in d.finditer(metin)]


# --- C14t ALINTI muafiyeti (11 Kasim 2026) ---------------------------------
# NEDEN: `test` ve `kalem` sozluge girdikten sonra KOTU bir sayinin
# ALINTILANMASI SKILL.md'de yazilamaz hale geldi (`"34 test" diyordu, gercek
# 103`). I6 "eski yanlis sayiyi kaydet" der, D10 "gomulu sayac yazma" der:
# ikisi carpisinca kayit yazilamiyor. `--metin` modunda bu 7 Kasim 2026'da
# cozulmustu; `C14t`'ye TASINMAMISTI (gizli kirilganlik, bugun eslesme 0).
# KURAL DAR: ters tirnak ICINDE **ve** AYNI SATIRDA kayit jetonu.
# Ters tirnak disinda -> IHLAL. Icinde ama jetonsuz -> IHLAL (gizleme kapali).
# Jeton = "bu alinti bir KAYIT / DUZELTME kaydidir" isareti.
# P2-1 (11.11.2026) OLCUMU: ilk sozluk 13 makul kayit kalibinin 6'sini reddediyordu
# (tarihsellik isareti yoktu). Tarihsel isaretler eklendi -> 13/13.
#
# KALDIRILAN `gecer|geçer` (KENDI KUSURUM, olculdu): "geçerli" (valid) ile "geçer"
# (passes) ayni koku yakaliyor; `Gecerli `86 kontrol` degeri` ihlal=0 veriyordu,
# yani GUNCEL iddiayi ters tirnakla gizleme yolu acikti.
#
# ALINMAYAN `gecti` (olculdu): 4 gizleme yolu aciyor (`86 kontrol gecti` vb),
# hicbir kayit kalibini kazanmiyor. Gereksiz ve zararli.
_SAYAC_JET = re.compile(
    r'(?:ihlal|diyordu|gercek|ge\u00e7ek|yanlis|yanl\u0131\u015f'
    r'|olculdu|\u00f6l\u00e7\u00fcld\u00fc|olcum|\u00f6l\u00e7\u00fcm|beklenen|yerine'
    r'|eski|eskiden|onceki|\u00f6nceki|onceden|\u00f6nceden'
    r'|duzeltilen|d\u00fczeltilen|duzeltme|d\u00fczeltme'
    r'|seklinde|\u015feklinde|yazilmisti|yaz\u0131lm\u0131\u015ft\u0131'
    r'|tarihli'
    # NOT: bu ikilik (ASCII/aksanli) MUT-4'un fiksturuyle ORTAYA CIKTI: ilk
    # halde yalniz ASCII vardi, `Önceki` aksanli yazim kaciyordu.
    r'|kaldirildi|kald\u0131r\u0131ld\u0131|kaldirilmis|kald\u0131r\u0131lm\u0131\u015f'
    r'|revizyon|yaziyordu|yaz\u0131yordu)',
    re.I)


def _sayac_ayir(metin):
    """(ihlal, alinti) — ters tirnak + kayit jetonu olan eslesme alintidir."""
    # Yerel adlar `_al_` onekiyle BENZERSIZ: `_tanimlar` kapsam ayirt etmiyor
    # (D11 siniri), modul duzeyinde ayni adi kullanan bir kapinin parmak izini
    # degistirmemesi icin cakisma birakilmiyor. Olculdu: `_satirlar` 3 yerde.
    _al_span = [(m.start(), m.end()) for m in re.finditer(r'`[^`\n]*`', metin)]
    _al_bas = [0] + [m.end() for m in re.finditer(r'\n', metin)]
    import bisect as _al_bisect

    def _al_satir(i):
        return _al_bisect.bisect_right(_al_bas, i) - 1

    _al_satirlar = metin.split('\n')
    ihlal, alinti = [], []
    for ad, d in _SAYAC_DER:
        for m in d.finditer(metin):
            s, e = m.start(), m.end()
            _al_icinde = any(a < s and b >= e for a, b in _al_span)
            if _al_icinde and _SAYAC_JET.search(_al_satirlar[_al_satir(s)]):
                alinti.append(m.group(0))
            else:
                ihlal.append(m.group(0))
    return ihlal, alinti


_bulunan_sayac, _alinti_sayac = _sayac_ayir(C)
for _a in _alinti_sayac[:3]:
    print('  ALINTI  sayac "%s" (ters tirnak + kayit jetonu — kanit kaydi)' % _a)
k('C14t', 'gomulu sayac iddiasi yok — sozcukle yazim dahil (D10b, alintili)',
  not _bulunan_sayac,
  '%s · alinti: %d' % (
      ('bulunan: %s' % _bulunan_sayac[:4]) if _bulunan_sayac else '0 eslesme',
      len(_alinti_sayac)))

# --- C14t-a CALISTIRMALI: C14t'nin KENDI ayirt etme gucu (8 Kasim 2026) -----
# NEDEN: C14t ilk yazildiginda 23 yazimin 16'sini yakaliyordu ve bunu KIMSE
# olcmedi — "0 eslesme" ciktisi kapinin kor oldugunu gizliyordu.
# 8 Kasim 2026'da daha agir bir sey olculdu: 7 desen, anlamli bicim uzayinin
# (1190 yazim) yalniz %32'sini yakaliyordu. Secilmis 25 ornegin "25/25" demesi
# YETMIYOR — kapi kendi sinavini URETMELI. Iki katman:
#   1) REGRESYON: 25 bilinen yazim hala yakalaniyor mu (sabit liste)
#   2) UZAY: 1190 bicimlik uretilmis uzayda yakalama orani >= 0.95 ve
#      12 mesru cumlede 0 yanlis pozitif. Esik olculdu (gercek 0.973).
_G14TA_YAK = [
    '41 kontrol', '67 kontrol', '99 kontrol', '6 kontrol gecisi', 'alti kontrol',
    'altı kontrol', 'on iki kontrol', 'yetmis iki kapi', 'yetmiş iki kapı',
    '6 gate', '67 checks', 'kontroller: 67', 'kontrol sayisi: 70',
    'kapi sayisi: 67', 'toplam 67 kapi', '67 kapi', 'altı-kontrol',
    'tireli 67-kontrol', 'alti-kontrol', '17 kontrol', '72 kontrol',
    'toplam alti kapi', 'yetmiş-iki kapı', 'altmis yedi kapi', 'yetmis-iki kapi',
    # ROMA (8 Kasim 2026): 7 bicimde kaciyordu, olculdu ve kapatildi
    'XLI kontrol', 'XLI kapi', 'sayac XLI', 'kontroller: XLI',
    'toplam XL kapi', 'kontrol sayisi: XLI',
    # KURAL sinavi: 50'nin USTU (liste degil gramer — 8 Kasim 2026)
    'LI kontrol', 'sayac LI', 'XLIX kapi', 'MMXXVI kontrol',
    # B-4: 3999 USTU (9 Kasim 2026 olcumu — M{0,4} bunlari kaciriyordu)
    'MMMMM kontrol', 'sayac MMMMMMMMMM',
    # D10 (11 Kasim 2026): sozluk (test/capa) + BIRIM yuvasi (adet/count/adedi)
    # ile KAPANAN bes bicim. Bu liste REGRESYONdur: kural geri alinirsa yanar.
    '86 test', '86 capa', '67 adet kontrol', 'kontrol adedi: 67',
    'gate count: 67', 'toplam 67 adet kapi', 'sayac 86 test',
    '72 test', 'XLI test', 'on iki capa', '9 kalem', 'on iki kalem',
    # MUT-B (11.11.2026): `kalem: 9` regresyonda YOKTU — `kalem-nokta`
    # kurali silindiginde test gecmeye devam ediyordu (uzay orani 96.7%,
    # esigin ustunde). Yanmayan kural sahte guven verir (§9B.2).
    'kalem: 9', 'kalem = 12', 'toplam 9 kalem',
    # D10 ikinci tekrar (11.11.2026): `madde` + kelimesiz `adet:`
    '86 madde', '(4 madde)', '9 madde, hepsi cevaplanir',
    'adet: 67', 'madde: 7', 'madde = 12']
# OLCULMUS SINIR (gizlenmiyor): kural YALNIZ gecerli roma dizisini yakalar.
# Gecersiz dizi ("IIII", "IC", "VV") sayi DEGILDIR — kural onlari reddeder.
# Kimse sayac iddiasini gecersiz roma ile yazmaz; yazsa da kacardi. Kayit:
_G14TA_BILINEN_KACAK = ['IIII kontrol', 'IC kapi', 'VV kontrol',
                        # D10 (11 Kasim 2026) — OLCULDU, REDDEDILDI:
                        # `madde` sozluge eklenmedi (SKILL.md 3, korpus 306
                        # eslesme; hepsi madde-isareti). Keywordsuz `adet: 67`
                        # de eklenmedi (korpus 98; `p1_count=0` gibi tanimlayici
                        # adlari). Ikisi de BILINEN kacak olarak duruyor.
                        '86 madde', 'adet: 67']
_G14TA_MESRU = [
    '7.1 Iki kapi. Ic denetim', '**7.1 Iki kapi.**', 'Iki kapi.',
    'kapi kilitlenmez', 'bu bir kapi ID', 'C14t (sayi sozcukle)', 'sayac 1→2',
    'iki kapi acilir', 'tek kapi var', 'iki-uc kapi var', 'her kapi bir olcum',
    'kapi sayisi YAZILMAZ',
    'II. Dunya Savasi', 'Madde IV', 'tip I hata',
    # GRAMERIN GEREKCESI (8 Kasim 2026, labin KENDI 237 belgesinde olculdu):
    # Roma yerine serbest harf dizisi [IVXLCDM]+ kullanilirsa su 4 mesru
    # cumle YANLIS yakalanir. Gramer bunlari eler — faydasi budur.
    'LLM gate', 'bu im) — kapi kapanmaz', 'sinirli kontroller',
    'asagidaki (kapi acilir)',
    # D10 (11 Kasim 2026): BIRIM yuvasi yanlis-pozitif uretmemeli.
    '9 adet 404 dondu', '6 adet 404 ve 2 tane 410', '3-5 madde',
 '2 tane bulgu kaldi',
    'count: 12 satir',
    # D10-kalem (11 Kasim 2026): "OLCULMEYEN kalem 5" = KALEM NUMARASI,
    # sayac iddiasi degil. Ikisi SKILL.md'de GERCEKTEN var (L464-465).
    'OLCULMEYEN kalem 5 — onceki halim eksikti',
    # C14t ALINTI muafiyeti (11.11.2026): bu UC cumle ALINTI'dir (ters tirnak +
    # kayit jetonu). Kalan dordu IHLAL'dir — muafiyet gizleme yolu acmamali.
    'Kayit: `"34 test" diyordu, gercek 103`',
    # P2-1 (11.11.2026): bunlar ONCEDEN IHLAL sayiliyordu (6/13 kayip).
    # Tarihsel isaret jetonlari eklendikten sonra ALINTI olurlar.
    'Kayit: `"34 test"` (11.11.2026 tarihli eski satir)',
    'Eski surumde `"34 test"` vardi; simdi 103.',
    # DUZELTME (11.11.2026): ilk hali `"86 kontrol"` -> 52 kontrol idi ve KENDI
    # testime yanlis ornekti: `52 kontrol` tirnak DISINDA = CIPLAK sayac iddiasi,
    # yani C14t onu YAKALAMALI. Test dogru davrandi, ornek yanlisti.
    '`"86 kontrol"` idi, revizyonla duzeltildi',
    'Duzeltilen satir: `"86 kontrol"` / dogrusu 52',
    'Onceki kayit `"67 adet kontrol"`; guncel 52',
    'Not: `"9 kalem"` seklinde yazilmisti',
    # MUT-4 (11.11.2026): TURKCE AKSANLI yazim agirligi. Bu uc satir olmadan
    # aksanli jeton alternatifleri (duzeltilen/d\u00fczeltilen, kaldirildi/
    # kald\u0131r\u0131ld\u0131) SILINDIGINDE test gecmeye devam ediyordu -> kural
    # kendi sinavinda gorunmuyordu. YANMAYAN KURAL SAHTE GUVEN VERIR (§9B.2).
    'D\u00fczeltilen sat\u0131r: `"86 kontrol"`',
    '`"34 test"` kald\u0131r\u0131ld\u0131',
    '\u00d6nceki kay\u0131t `"67 adet kontrol"` idi',
    'OLCULMEYEN kalem 4 — ONCEKI CUMLE YANLISTI',
    'siddet etiketi tasiyan kalem 3 kaldi',
    # D10 ikinci tekrar (11.11.2026) ISTISNALARI — bunlar SAYAC degil:
    'bu dosyanin \u00a710 madde numarasi degildir',
    'Ne degisti (insan diliyle, 3-5 madde)',
    'madde isaretleri 3 tanedir']
_G14TA_KACAN = [t for t in _G14TA_YAK if not _sayac_bul(t)]
# C14t-a (11.11.2026): FP olcumu MUAFIYETLIDIR — yoksa alinti ornegi
# mesru listede dururken FP sayilir ve test mekanizmadan habersiz kalir.
_G14TA_FP = [t for t in _G14TA_MESRU if _sayac_ayir(t)[0]]
# GIZLEME SINAVI: ters tirnak ICINDE ama kayit jetonu YOK -> YANMALI.
# Yoksa "yasak sayiyi ters tirnakla gizle" yolu acilirdi. Muafiyetin bedeli budur.
_G14TA_GIZLE = [
    '`86 kontrol`', '`34 test`', '`9 kalem`',
    'Sonuc `86 kontrol` cikti',
    '``67 adet kontrol``',
    # P2-1 (11.11.2026): KENDI KUSURUMUN nobetcisi — "gecerli"/"guncel"
    # jetonu guncel iddiayi GIZLEYEMEZ. `gecer` bu yuzden sozlukten CIKARILDI.
    'Gecerli `86 kontrol` degeri',
    'Guncel `86 kontrol` sayisi',
    # `gecti` jetonu ALINMADI (4 gizleme yolu aciyordu): bunlar YANMALI.
    '`86 kontrol gecti`',
    'SONUC: `86 kontrol gecti`',
    '`34 test gecti`',
    # MUT-2 (11.11.2026): jeton VAR ama TERS TIRNAK YOK -> yine IHLAL olmali.
    # Bu uc satir olmadan "jeton tek basina yetsin" mutasyonu KAÇIYORDU
    # (yalniz C14u kosul izi yakaliyordu; davranis testi yoktu).
    'Sonuc 86 kontrol diyordu, gercek 52',
    '34 test olculdu, gercek 103',
    'eski kayit 9 kalem diyordu',
]
_G14TA_GIZLE_KACAN = [t for t in _G14TA_GIZLE if not _sayac_ayir(t)[0]]
# --- uretilmis uzay: 4 sayi ekseni x 7 anahtar x 7 baglac -------------------
_G14TA_SAYI = (('41', '67', '99', '6'),
               ('XLI', 'L', 'IV', 'XII', 'LI', 'XLIX', 'MMXXVI'),
               ('iki', 'alti', 'altı', 'yedi', 'on iki', 'yetmis', 'yetmiş'),
               ('yetmis iki', 'yetmiş iki', 'altmis yedi', 'altmış yedi'),
               ('yetmis', 'altmis'))
_G14TA_ANAHTAR = ('kontrol', 'kontroller', 'gate', 'check', 'checks',
                  'kapi', 'kapı',
                  # D10 (11 Kasim 2026): yeni sozluk UZAYA DA girer — yoksa
                  # kapsama orani yalniz ESKI kelimelerde olculur ve %98,1
                  # yaniltir (EK 43'un elestirdigi ayni hastalik).
                  'test', 'capa', 'kalem')
_G14TA_BAGLAC = ('{n} {k}', '{n}-{k}', '{k}: {n}', '{k} : {n}',
                 '{k} sayisi: {n}', '{k} sayısı: {n}', 'toplam {n} {k}',
                 'sayac {n}', 'sayac: {n}', '({n} {k})')
_G14TA_UZAY = [b.format(n=n, k=kk)
               for sl in _G14TA_SAYI for n in sl
               for kk in _G14TA_ANAHTAR for b in _G14TA_BAGLAC]
_G14TA_UZAY_KACAN = [t for t in _G14TA_UZAY if not _sayac_bul(t)]
_G14TA_ORAN = (len(_G14TA_UZAY) - len(_G14TA_UZAY_KACAN)) / len(_G14TA_UZAY)
k('C14t-a', 'C14t kurali bilinen yazimlari + uretilmis uzayin >=%95ini yakalar',
  (not _G14TA_KACAN) and (not _G14TA_FP) and _G14TA_ORAN >= 0.95
  and (not _G14TA_GIZLE_KACAN),
  'regresyon=%d/%d kacan=%s · uzay=%d/%d (%.1f%%) · yanlis-pozitif=%d/%d · '
  'bilinen-kacak=%d %s · gizleme-kacan=%d' % (
      len(_G14TA_YAK) - len(_G14TA_KACAN), len(_G14TA_YAK),
      (_G14TA_KACAN[:3] or '-'),
      len(_G14TA_UZAY) - len(_G14TA_UZAY_KACAN), len(_G14TA_UZAY),
      100 * _G14TA_ORAN, len(_G14TA_FP), len(_G14TA_MESRU),
      len(_G14TA_BILINEN_KACAK), (_G14TA_BILINEN_KACAK[:3] or '-'),
      len(_G14TA_GIZLE_KACAN)))

# --- C14u CALISTIRMALI: ARAC_DEGISTI / KIMLIK_DEGISTI ayrimi (D11) ----------
# NEDEN: kimlik listesi betik sha256'sini tasir; her YENI kapi sha'yi degistirir.
# Metin "yeni kapi = EKLENEN" diyordu ama bunu AYIRT EDEN OLCUM yoktu — kapilari
# ZAYIFLATAN degisiklik de "EKLENEN" diye beyan edilebilirdi. `kapi_farki.py`
# kapi kimlik kumesini ve capa beklentilerini karsilastirir:
#   KALDIRILAN / GEVSETILEN -> rc=1 (KIMLIK_DEGISTI) · yalniz ekleme -> ARAC_DEGISTI
# Taban dosyasi (`scripts/tests/kapi_taban.json`) her mesru degisiklikte AYNI
# commit'te guncellenir — yani degisiklik DIFF'te gorunur, sessiz kalamaz.
_BURASI = os.path.dirname(os.path.abspath(__file__))
_KAPI_FARKI = os.path.join(_BURASI, 'kapi_farki.py')
_KAPI_TABAN = os.path.join(_BURASI, 'tests', 'kapi_taban.json')
# [Z44, 15 Kasim 2026] KATMAN (2) `_arsiv_dogrula()` FONKSIYONUNA CIKARILDI ve
# SENTETIK FIXTURE eklendi. Yan etki OLCULDU: 26 kapinin kosul parmak izi
# degisti ama 26/26 kapinin KOSUL METNI birebir AYNIDIR (olculdu: ast.unparse
# ile HEAD ve calisma kopyasi karsilastirildi). Sebep BAGLASIM: `_h` defteri
# hub'dir; (2) blogunun `if _eksik:` / `if _fazla:` / `if _bozuk:` bekcileri
# `_h`nin TANIMI sayiliyordu (kapi_farki `_tanimlar` (c) BEKCI kurali). Blok
# fonksiyona cikinca bu uc bekci tanimi `_h`den dustu -> `_h`ye bagli 26 kapi
# ayni anda dondu (kapi basina -57 parca, +16 fixture parcasi).
# Taban bu yuzden ADIYLA kabul edildi; kabul gerekcesi EK 115'te kayitli.
_g14u = ''
_g14u_ok = False
try:
    _r = __import__('subprocess').run(
        [sys.executable, _KAPI_FARKI, '--taban', _KAPI_TABAN,
         '--guncel', os.path.abspath(__file__)],
        capture_output=True, text=True, timeout=60)
    _sat = [x for x in _r.stdout.strip().splitlines() if x.startswith('SONUC:')]
    _g14u = (_sat[-1] if _sat else '<SONUC yok>')[:90]
    _g14u_ok = (_r.returncode == 0 and _g14u.endswith('AYNI'))
except Exception as _e:
    _g14u = 'CALISTIRILAMADI: %s' % _e
# Aracin KENDISI mutasyona duyarli mi: gevsetilmis capa yakalanmali.
_g14u_mut = 'CALISTIRILAMADI'
try:
    import tempfile as _tf
    _d = _tf.mkdtemp()
    _kopya = os.path.join(_d, 'skill_lint_mut.py')
    _kaynak = open(os.path.abspath(__file__), encoding='utf-8').read()
    _mut = _kaynak.replace("('U+015E,', 1)", "('U+015E,', 0)", 1)
    if _mut == _kaynak:
        _g14u_mut = 'MUTASYON NOKTASI YOK'
    else:
        open(_kopya, 'w', encoding='utf-8').write(_mut)
        _r2 = __import__('subprocess').run(
            [sys.executable, _KAPI_FARKI, '--taban', _KAPI_TABAN, '--guncel', _kopya],
            capture_output=True, text=True, timeout=60)
        _g14u_mut = 'YAKALADI' if _r2.returncode == 1 else 'KACIRDI'
except Exception as _e:
    _g14u_mut = 'CALISTIRILAMADI: %s' % _e
# --- C14u-a KOSUL mutasyonu (D11, 11.11.2026) ------------------------------
# NEDEN: capa mutasyonu yakalaniyordu ama KOSUL mutasyonu yakalanmiyordu.
# `k('C14t', ..., not _bulunan_sayac, ...)` -> `True` yapildiginda kimlik dizesi
# ve C13 capasi AYNI kaldigi icin arac `SONUC: AYNI` / rc=0 diyordu. Yani
# KAPATILMIS bir kapi "ayni" gorunuyordu — denetimin en pahali kor noktasi.
_g14u_kos = 'CALISTIRILAMADI'
try:
    _kaynak = open(os.path.abspath(__file__), encoding='utf-8').read()
    _HEDEF_T = "  not " + "_bulunan_sayac,\n"
    _mut2 = _kaynak.replace(_HEDEF_T, "  True,\n", 1)
    if _kaynak.count(_HEDEF_T) != 1:
        _g14u_kos = 'COK_ESLESME %d' % _kaynak.count(_HEDEF_T)
    elif _mut2 == _kaynak:
        _g14u_kos = 'MUTASYON NOKTASI YOK'
    else:
        _kopya2 = os.path.join(_d, 'skill_lint_kosul.py')
        open(_kopya2, 'w', encoding='utf-8').write(_mut2)
        _r3 = __import__('subprocess').run(
            [sys.executable, _KAPI_FARKI, '--taban', _KAPI_TABAN,
             '--guncel', _kopya2],
            capture_output=True, text=True, timeout=60)
        _g14u_kos = ('YAKALADI' if (_r3.returncode == 1
                                    and 'KOSUL_DEGISTI' in _r3.stdout)
                     else 'KACIRDI rc=%d' % _r3.returncode)
    # NEGATIF KONTROL 1: yeni kapi EKLENEN'dir, kosul degisimi DEGIL.
    # Hedef CALISMA ANINDA birlestirilir: yoksa arama metni dosyada 2 kez gecer
    # (gercek cagri + bu satir) ve replace YANLIS yere vurur (olculdu: C14ZZ
    # test kodunun icine dustu, kopya bozuldu, test YANLIS-KIRMIZI yazdi).
    _HEDEF_U = "k('C14u', " + "'ARAC_DEGISTI/KIMLIK_DEGISTI/KOSUL_DEGISTI ayrimi + taban (D11)',"
    _HEDEF_B = "'gomulu sayac iddiasi yok — sozcukle yazim dahil " + "(D10b, alintili)'"
    _g14u_ek = 'CALISTIRILAMADI'
    _g14u_met = 'CALISTIRILAMADI'
    _say_u = _kaynak.count(_HEDEF_U)
    if _say_u != 1:
        _g14u_ek = _g14u_met = 'COK_ESLESME %d' % _say_u
    else:
        _mut3 = _kaynak.replace(
            _HEDEF_U,
            "k('C14ZZ', 'TEST — yalniz ekleme', True, 'deneme')\n" + _HEDEF_U, 1)
        _kopya3 = os.path.join(_d, 'skill_lint_ekle.py')
        open(_kopya3, 'w', encoding='utf-8').write(_mut3)
        _r4 = __import__('subprocess').run(
            [sys.executable, _KAPI_FARKI, '--taban', _KAPI_TABAN,
             '--guncel', _kopya3],
            capture_output=True, text=True, timeout=60)
        _g14u_ek = ('GECIRDI' if (_r4.returncode == 0
                                  and 'ARAC_DEGISTI' in _r4.stdout)
                    else 'YANLIS-KIRMIZI rc=%d' % _r4.returncode)
        # NEGATIF KONTROL 2: kosula ve kimlige dokunmayan duzenleme AYNI kalmali.
        if _kaynak.count(_HEDEF_B) != 1:
            _g14u_met = 'COK_ESLESME %d' % _kaynak.count(_HEDEF_B)
        else:
            _mut4 = _kaynak.replace(_HEDEF_B, _HEDEF_B[:-1] + ", deneme)'", 1)
            _kopya4 = os.path.join(_d, 'skill_lint_metin.py')
            open(_kopya4, 'w', encoding='utf-8').write(_mut4)
            _r5 = __import__('subprocess').run(
                [sys.executable, _KAPI_FARKI, '--taban', _KAPI_TABAN,
                 '--guncel', _kopya4],
                capture_output=True, text=True, timeout=60)
            _g14u_met = ('GECIRDI' if (_r5.returncode == 0
                                       and _r5.stdout.rstrip().endswith('AYNI'))
                         else 'YANLIS-KIRMIZI rc=%d' % _r5.returncode)
    # --- JOKER KORKULUGU (13.11.2026, Z13) -----------------------------
    # NEDEN: `--kabul` korkulugu "her degisikligi ADIYLA kabul et" diyor ama
    # bunu OLCEN bir kapı yoktu. Biri `--kabul '*'` joker'ini desteklerse
    # (veya `fazla` denetimini kaldirirsa) hicbir kapı yanmazdi — korkuluk
    # sessizce yok olurdu. Artik joker REDDEDILMELI ve taban DOSYASINA
    # dokunulmamali. Iki sey birden: rc=1 VE icerik degismedi.
    _g14u_joker = 'CALISTIRILAMADI'
    try:
        import hashlib as _hj
        _tjc = os.path.join(_d, 'taban_joker.json')
        _tjk = open(_KAPI_TABAN, encoding='utf-8').read()
        open(_tjc, 'w', encoding='utf-8').write(_tjk)
        _h_once = _hj.sha256(_tjk.encode('utf-8')).hexdigest()[:12]
        # [DUZELTME 13 Kasim 2026, Z17d] LISTE 3 DIZEDEN 11'E CIKARILDI.
        # NEDEN (EK 82 OLCULMEYEN): "Joker testi yalniz 3 dizeyi deniyor
        # (`*`, `ALL`, `...`). Baska bir joker desteklenirse gorulmez."
        # Test edilen joker, test edilmeyen jokerin kaniti degildir. Kucuk/buyuk
        # harf, KISALTMA (`C15*`), BOS dize ve BOS OGE (`C15l,`) eklendi.
        _jokerler = ['*', 'ALL', 'all', 'hepsi', '...', 'C15*', 'C1*',
                     'C15l*', '%', '', 'C15l,']
        _g14u_joker = 'CALISTIRILAMADI'
        for _j in _jokerler:
            _rj = __import__('subprocess').run(
                [sys.executable, _KAPI_FARKI, '--yaz', _tjc,
                 '--guncel', _kopya2, '--kabul', _j],
                capture_output=True, text=True, timeout=60)
            _h_sonra = _hj.sha256(
                open(_tjc, encoding='utf-8').read().encode('utf-8')).hexdigest()[:12]
            if _rj.returncode != 1 or 'RED' not in _rj.stdout:
                _g14u_joker = "JOKER GECTI rc=%d (%s)" % (_rj.returncode, _j)
                break
            if _h_sonra != _h_once:
                _g14u_joker = "TABAN DEGISTI sha %s->%s (%s)" % (
                    _h_once, _h_sonra, _j)
                break
            _g14u_joker = 'REDDETTI'
    except Exception as _ej:
        _g14u_joker = 'CALISTIRILAMADI: %s' % _ej
except Exception as _e:
    _g14u_kos = 'CALISTIRILAMADI: %s' % _e
    _g14u_ek = _g14u_met = _g14u_joker = 'CALISTIRILAMADI'
k('C14u', 'ARAC_DEGISTI/KIMLIK_DEGISTI/KOSUL_DEGISTI ayrimi + taban (D11)',
  _g14u_ok and _g14u_mut == 'YAKALADI' and _g14u_kos == 'YAKALADI'
  and _g14u_ek == 'GECIRDI' and _g14u_met == 'GECIRDI'
  and _g14u_joker == 'REDDETTI',
  '%s · capa-mut: %s · KOSUL-mut: %s · ekleme: %s · metin: %s · joker: %s'
  % (_g14u, _g14u_mut, _g14u_kos, _g14u_ek, _g14u_met, _g14u_joker))

# --- C14v CALISTIRMALI: BAGIMSIZLIK kanidi artefakta bagli (D17) ------------
# NEDEN: "BAGIMSIZLIK: VAR tasimali" kuralini YAZAN ajanin kendisiydi — yani
# beyan esigi aciyordu (2. turun "beyan esik acmaz" kusurunun manifest aynasi;
# 3. turda 10/18 model KAPANMADI dedi). Artik VAR dediysen HAM YANIT DOSYASI ve
# sha256'si var; `bagimsizlik_dogrula.py` bunu olcer.
# YAPISAL SINIR (gizlenmez): ayni ajan dosyayi kendisi uretebilir — betik bunu
# TESPIT ETMEZ; beyani artefakta baglar, imkansizi iddia etmez.
_BAG = os.path.join(_BURASI, 'bagimsizlik_dogrula.py')
_g14v = 'CALISTIRILAMADI'
_g14v_ok = False
try:
    import tempfile as _tf2
    _d2 = _tf2.mkdtemp()
    _f = os.path.join(_d2, 'ham.md')
    open(_f, 'w', encoding='utf-8').write('MODEL: dis\nYANIT: ...\n')
    _sha = __import__('hashlib').sha256(open(_f, 'rb').read()).hexdigest()
    _iyi = __import__('subprocess').run(
        [sys.executable, _BAG, '--kanit', 'farkli model ailesi', _f, _sha],
        capture_output=True, text=True, timeout=30)
    _oz = __import__('subprocess').run(
        [sys.executable, _BAG, '--kanit', 'oz', _f, _sha],
        capture_output=True, text=True, timeout=30)
    _bozuk = __import__('subprocess').run(
        [sys.executable, _BAG, '--kanit', 'insan', _f, '0' * 64],
        capture_output=True, text=True, timeout=30)
    _g14v = 'gecerli=%d · oz=%d · bozuk-sha=%d' % (
        _iyi.returncode, _oz.returncode, _bozuk.returncode)
    _g14v_ok = (_iyi.returncode == 0 and _oz.returncode == 1
                and _bozuk.returncode == 1)
except Exception as _e:
    _g14v = 'CALISTIRILAMADI: %s' % _e
k('C14v', 'BAGIMSIZLIK: VAR kanit ister (aile+dosya+sha) (D17)',
  _g14v_ok, _g14v)


# --- C14w CALISTIRMALI: SKILL.md'de gecen her betik diskte VAR + compatibility ---
# NEDEN (3. tur, D21: 1 KAPANMADI + 1 YENI_KUSUR): `compatibility` alani yalniz
# `scripts/skill_lint.py` diyordu; belge ise 11 betige atif yapiyor. Okuyucu
# hangi betigin kurulu oldugunu bilemiyor, "betik yok" durumu sessiz kaliyordu.
# Iki sey olculur: (a) metinde GECEN her betik diskte var mi (dangling atif yok);
# (b) compatibility betik KUMESINI ilan ediyor mu (`scripts/` gecmeli).
_BETIK = sorted(set(re.findall(r'scripts/[a-z0-9_]+\.py', C)))
_BETIK_EKSIK = [b for b in _BETIK
                if not os.path.exists(os.path.join(_BURASI, '..', b))]
_C_UYUM = [l for l in C.splitlines() if l.startswith('compatibility:')]
_C_UYUM_VAR = bool(_C_UYUM) and 'scripts/' in _C_UYUM[0]
k('C14w', 'metindeki her betik diskte var + compatibility kumeyi ilan eder (D21)',
  (not _BETIK_EKSIK) and _C_UYUM_VAR,
  'betik=%d · eksik=%s · compatibility=%s' % (
      len(_BETIK), (','.join(_BETIK_EKSIK) or '-'),
      'VAR' if _C_UYUM_VAR else 'YOK'))

# --- C14x CALISTIRMALI: manifest disi snapshot dosyasi KANIT SAYILAMAZ ------
# NEDEN (8 Kasim 2026): `scripts/tests/snapshot/` altinda manifestte OLMAYAN
# 6 dosya vardi (`ayet_<a>-<b>.json`). Bunlar "yetim" diye anildi ve `rm`
# onayi istendi. OLCULDU: altisi da `__tr.diyanet` ikizinin BYTE KOPYASI
# (sha256 birebir). Yani silmeye gerek yok — ama sessiz kalmalari da yanlis.
# UC SINIF (her biri olculur, gevsetme yok):
#   IKIZ    manifest icindeki bir dosyayla BYTE AYNI -> kanit (ayni icerik)
#   HAM IZ  `.html` gibi ham indirme; HICBIR betik adini anmiyor -> kanit DEGIL
#   KANITSIZ geri kalan her sey -> FAIL
# "HAM" sinifi bedava kabul degil: betikte adi geciyorsa (yani okunuyorsa)
# KANITSIZ sayilir, cunku sabitlenmemis veri olcume giriyor demektir.
_SNAP = os.path.join(_BURASI, 'tests', 'snapshot')
_MANIFEST = os.path.join(_SNAP, 'SNAPSHOT.sha256')
_g14x = ''
_g14x_ok = False
try:
    def _sha256(yol):
        import hashlib as _h
        with open(yol, 'rb') as _f:
            return _h.sha256(_f.read()).hexdigest()

    _BETIK_METNI = ''.join(
        open(os.path.join(_BURASI, x), encoding='utf-8', errors='replace').read()
        for x in os.listdir(_BURASI) if x.endswith('.py'))
    if not os.path.isdir(_SNAP):
        _g14x = 'CALISTIRILAMADI: snapshot dizini yok'
    else:
        _man = {}
        with open(_MANIFEST, encoding='utf-8') as _f:
            for _l in _f:
                _l = _l.strip()
                if not _l or _l.startswith('#'):
                    continue
                # Z7 (12 Kasim 2026): manifeste 3. sutun (dosya bazli tarih)
                # eklendi. `split(None, 1)` tarihi ADIN icine katiyordu ->
                # butun dosyalar "manifest disi" gorundu (C14x KANITSIZ dedi).
                # OLCULDU: duzeltme oncesi `manifest=60 · KANITSIZ=60 dosya`.
                _p = _l.split(None, 2)
                if len(_p) >= 2:
                    _man[_p[1]] = _p[0]
        _diskte = sorted(x for x in os.listdir(_SNAP)
                         if not x.startswith('.') and x != 'SNAPSHOT.sha256')
        _yetim = [x for x in _diskte if x not in _man]
        _man_sha = {}
        for _ad in _man:
            _yol = os.path.join(_SNAP, _ad)
            if os.path.exists(_yol):
                _man_sha.setdefault(_sha256(_yol), []).append(_ad)
        _ikiz, _ham, _kanitsiz = [], [], []
        for _y in _yetim:
            _s = _sha256(os.path.join(_SNAP, _y))
            if _s in _man_sha:
                _ikiz.append('%s=%s' % (_y, _man_sha[_s][0]))
            # "okunuyor" olcutu: dosya adi KOD icinde tirnakli gecmeli.
            # Serbest metin (docstring/yorum) okuma degildir — olculdu:
            # `snapshot_yenile.py:23` "YAZILDI: sunnah_6094.html ..." sadece
            # bir ORNEK yazisi; betik o dosyayi acmiyor. Tirnak sarti bunu ayirir.
            elif _y.endswith('.html') and not (
                    ("'%s'" % _y) in _BETIK_METNI or ('"%s"' % _y) in _BETIK_METNI):
                _ham.append(_y)          # ham iz: hicbir betik okumuyor
            else:
                _kanitsiz.append(_y)
        _g14x_ok = not _kanitsiz
        _g14x = ('manifest=%d · ikiz=%d · ham-iz=%d · KANITSIZ=%s' % (
            len(_man), len(_ikiz), len(_ham), (','.join(_kanitsiz) or '-')))
except Exception as _e:
    _g14x = 'CALISTIRILAMADI: %s' % _e
k('C14x', 'manifest disi snapshot dosyasi ikiz/ham-iz; KANITSIZ yok',
  _g14x_ok, _g14x)

# --- C14y CALISTIRMALI: denetim paketi ESERI birebir tasir (8 Kasim 2026) ---
# NEDEN: 3. turun kok surec kusuru, denetim paketinde ESERIN OLMAMASIYDI
# (denetciye yalniz maddeler + beklenen komutlar verildi -> 113 OLCULMEDI).
# `scripts/tur4_paket_uret.py` bunu cozer — ama paket BETIGIN NE YAPTIGINI
# olcmek zorunda: EK bloklari gercekten kaynakla ayni mi, yoksa cit kirilmis mi?
# Bu kapi, uretimi CALISTIRIR ve cikan metni KAYNAKLA karsilastirir.
# Olculen uc sey:
#   (1) kimlik tablosundaki sha, diskteki sha ile ayni
#   (2) EK blogunun icerigi kaynakla BIREBIR (veya newline'siz kaynakta +1 B)
#   (3) basliktaki surum SURUM.md + `SURUM:` satiriyla ayni (elle yazilmis degil)
_g14y = ''
_g14y_ok = False
try:
    import importlib.util as _ilu
    import hashlib as _hh
    _yp = os.path.join(_BURASI, 'tur4_paket_uret.py')
    if not os.path.exists(_yp):
        _g14y = 'CALISTIRILAMADI: tur4_paket_uret.py yok'
    else:
        _spec = _ilu.spec_from_file_location('_t4', _yp)
        _t4 = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_t4)
        # surum TEK KAYNAKTAN mi — KAPI KENDI okur, paketleyicinin fonksiyonunu
        # KULLANMAZ. Ilk yazim `_t4.surum()` ile karsilastiriyordu; bu TOTOLOJI:
        # paketleyici de ayni fonksiyonu cagiriyor, mutasyon (surumu elle yaz)
        # YANMADI -> kapi degildi. Olculdu, duzeltildi.
        _sm_yol = os.path.join(_BURASI, os.pardir, 'SURUM.md')
        _sm_surum = None
        with open(_sm_yol, encoding='utf-8') as _f:
            for _l in _f:
                if _l.startswith('Sürüm:'):
                    _sm_surum = _l.split(':')[1].strip().split()[0]
                    break
        _lint_surum = None
        with open(os.path.abspath(__file__), encoding='utf-8') as _f:
            for _l in _f:
                if _l.startswith('SURUM:'):
                    _lint_surum = _l.split(':')[1].strip().split()[0]
                    break
        # (0) ESER SURUMU — 11 Kasim 2026, OLCULDU: baslik bir sure
        # "Denetlenen surum: `SKILL.md` **v1.7.302**" yaziyordu; o SURUM.md'nin
        # LAB surumuydu, eserin kendi surumu `1.4.76` idi. Denetciye eserin
        # surumu hakkinda YANLIS bilgi vermek, hic vermemekten kotudur.
        # Bu satir eserin surumunu KENDI okur (paketleyicinin `eser_surum()`
        # fonksiyonunu CAGRMAZ — yoksa kapi totoloji olur ve mutasyonda YANMAZ).
        _eser_surum = None
        try:
            _sk_metin = open(os.path.join(_BURASI, os.pardir, 'SKILL.md'),
                             encoding='utf-8').read()
            _m_eser = re.search(r'^\s+version:\s*"([^"]+)"', _sk_metin, re.M)
            if _m_eser:
                _h_eser = _m_eser.group(1).strip()
                _eser_surum = _h_eser if _h_eser.startswith('v') else 'v' + _h_eser
        except Exception:
            _eser_surum = None

        def _paket_denetle(_metin, _secim):
            """Bir paketin (veya parcanin) tasidigi her EK'i kaynakla karsilastir."""
            _h = []
            for _et, _yol, _ne in _t4.DOSYALAR:
                if _et not in _secim:
                    continue
                _tam = os.path.join(_t4.KOK, _yol)
                _ham = open(_tam, 'rb').read()
                _bek = _hh.sha256(_ham).hexdigest()
                # (1) kimlik tablosu
                if ('`%s`' % _bek) not in _metin:
                    _h.append('%s: kimlik sha yok' % _et)
                # (2) EK blogu
                _i = _metin.find('\n## EK %s — `%s`' % (_et, _yol))
                if _i < 0:
                    _h.append('%s: EK blogu yok' % _et)
                    continue
                _bas2 = _metin.find('````text\n', _i) + len('````text\n')
                _son2 = _metin.find('\n````\n', _bas2)
                if _son2 < 0:
                    _h.append('%s: kapatma citi KENDI SATIRINDA degil' % _et)
                    continue
                # `_son2` icerigin SON newline'ini gosterir: +1 ile icerige dahil et.
                _icerik = _metin[_bas2:_son2 + 1].encode()
                if _icerik == _ham or _icerik == _ham + b'\n':
                    continue          # newline'siz kaynak: belgelenmis +1 B
                _h.append('%s: EK kaynakla ayni degil (%d vs %d B)'
                          % (_et, len(_icerik), len(_ham)))
            # (3) baslik surumu
            _bas3 = _metin.split('\n## §0')[0]
            if not _sm_surum:
                _h.append('SURUM.md surumu okunamadi')
            elif _sm_surum not in _bas3:
                _h.append('baslik SURUM.md (%s) tasimiyor' % _sm_surum)
            if not _lint_surum:
                _h.append('lint SURUM: satiri okunamadi')
            elif ('v' + _lint_surum.lstrip('v')) not in _bas3:
                _h.append('baslik lint surumu (%s) tasimiyor' % _lint_surum)
            # (3b) ESER SURUMU: SKILL.md'nin kendi metadata.version'u baslikta
            # OLMALI. `_sm_surum` (SURUM.md) bu sorunun cevabi DEGIL.
            if not _eser_surum:
                _h.append('SKILL.md metadata.version okunamadi')
            elif _eser_surum not in _bas3:
                _h.append('baslik ESER surumunu (%s) tasimiyor' % _eser_surum)
            return _h

        _tum = tuple(e for e, _, _ in _t4.DOSYALAR)
        _hata = _paket_denetle(_t4.uret(), _tum)          # tek dosya (eski davranis)
        _p1_ad, _p2_ad = _t4.parca_adlari()
        _m1 = _t4.uret(_t4.P1_ETIKET)
        _m2 = _t4.uret(_t4.P2_ETIKET)
        _hata += _paket_denetle(_m1, _t4.P1_ETIKET)       # PARCA 1
        _hata += _paket_denetle(_m2, _t4.P2_ETIKET)       # PARCA 2
        # (4) PARCA BUTUNLUGU — 8 Kasim 2026: tek paket 154 KB'ti ve "denetci
        # baglamina sigar mi" OLCULEMEDI. Cozum olcmek degil, soruyu kaldirmak:
        # iki parca. Ama parcalama YENI BIR KUSUR URETEBILIR — bir EK hicbir
        # parcada olmaz, ya da iki parcada birden olur. Ikisi de olculur.
        _e1 = set(e for e, _, _ in _t4.DOSYALAR
                  if ('\n## EK %s — `' % e) in _m1)
        _e2 = set(e for e, _, _ in _t4.DOSYALAR
                  if ('\n## EK %s — `' % e) in _m2)
        if _e1 & _e2:
            _hata.append('ayni EK iki parcada: %s' % sorted(_e1 & _e2))
        if (_e1 | _e2) != set(_tum):
            _hata.append('parcalar eseri EKSIK tasiyor: %s'
                         % sorted(set(_tum) - (_e1 | _e2)))
        if _p1_ad not in _m2:
            _hata.append('P2, P1 dosya adini anmiyor (%s)' % _p1_ad)
        # (5) DISK UYUSMASI — 11 Kasim 2026, OLCULDU (R1):
        # Buraya kadar her sey CANLI URETIM uzerinde olculuyordu. Diskteki
        # `docs/DIS_DENETIM_TUR4_P*.md` dosyalari HIC OKUNMUYORDU. Olcum:
        # ureticinin metni degistirildi, paket YENIDEN URETILMEDI -> C14y
        # PASS rc=0 verdi, P1=73428 B basti ama diskte 73423 B duruyordu.
        # Yani denetciye BAYAT paket gidebilirdi ve hicbir kapi gormezdi.
        # Sabah (11 Kasim) yakalamasi TESADUFTU: yalniz CA başlıktaki
        # `lint surumu` alani degismisti. Govde degisseydi gorulmezdi.
        _disk = []
        for _ad, _bekle in ((_p1_ad, _m1), (_p2_ad, _m2)):
            _yol = os.path.join(_BURASI, os.pardir, 'docs', _ad)
            if not os.path.exists(_yol):
                _disk.append('%s YOK (uret: tur4_paket_uret.py)' % _ad)
                continue
            with open(_yol, 'rb') as _f:
                _gercek = _f.read()
            if _gercek != _bekle.encode('utf-8'):
                _disk.append('%s BAYAT (disk=%d B, canli=%d B; yeniden uret)'
                             % (_ad, len(_gercek), len(_bekle.encode('utf-8'))))
        _hata += _disk
        _g14y_ok = not _hata
        _g14y = 'EK=%d · eser=%s · lint=%s · tam=%d B · P1=%d B · P2=%d B · %s' % (
            len(_t4.DOSYALAR), _eser_surum, _lint_surum,
            len(_t4.uret().encode()), len(_m1.encode()), len(_m2.encode()),
            ('HATA: ' + ' | '.join(_hata[:3])) if _hata
            else 'birebir + bolunmus + surum tek kaynak')
except Exception as _e:
    _g14y = 'CALISTIRILAMADI: %s' % _e
k('C14y', 'denetim paketi eseri birebir tasir; surum elle yazilmaz',
  _g14y_ok, _g14y)

# --- C14z CALISTIRMALI: tur4_paket_uret.py'nin KENDI testi (9 Kasim 2026) ----
# NEDEN: `C14y` paketin ICERIGINI kaynakla karsilastirir, ama betigin API'sini
# SINAMAZ: `--tek` sessizce EK birakabilir, `parca_adlari()` tarih formatini
# bozabilir, `--kontrol` sha'lari diskten farkli basilabilir. Bunlar `C14y`'de
# YESIL kalirdi. Ayrica KOD hatti oz-testi (`kod_selftest.py`) LAB betiklerini
# tanimaz — yani betik "kapisi var, testi yok" durumundaydi.
# `scripts/tests/test_tur4_paket_uret.py` 8 test tasir; bu kapi onu HER KOSUDA
# calistirir. Test kapisiz birakilmaz (olü test = test degil).
# Olculdu (4 mutasyon, 4'u de yandi):
#   T1 EK A iki parcada      -> FAILED (failures=1)
#   T2 --tek yalniz EK A     -> FAILED (failures=2)
#   T3 surum elle yazilmis   -> FAILED (failures=1)
#   T4 P2, P1'i anmiyor      -> FAILED (failures=1)
_g14z = ''
_g14z_ok = False
try:
    import subprocess as _sp
    _tp = os.path.join(_BURASI, 'tests', 'test_tur4_paket_uret.py')
    if not os.path.exists(_tp):
        _g14z = 'CALISTIRILAMADI: scripts/tests/test_tur4_paket_uret.py yok'
    else:
        _r = _sp.run([sys.executable, '-m', 'unittest',
                      'scripts.tests.test_tur4_paket_uret'],
                     cwd=os.path.join(_BURASI, os.pardir),
                     capture_output=True, text=True, timeout=120)
        _son = [l for l in (_r.stdout + _r.stderr).strip().splitlines() if l.strip()]
        _ozet = [l for l in _son if l.startswith('Ran ') or l.startswith('OK')
                 or l.startswith('FAILED')]
        _g14z_ok = _r.returncode == 0
        _ozet_metin = ' | '.join(_ozet[-2:]) if _ozet else (_son[-1] if _son else '-')
        _g14z = 'rc=%d · %s' % (_r.returncode, _ozet_metin)
except Exception as _e:
    _g14z = 'CALISTIRILAMADI: %s' % _e
# 11 Kasim 2026: etiketteki "8 test" BAYATTI — test sayisi 10'a cikti ama
# etiket sabit kaldi (D10 sinifi: gomulu sayac). Sayac etiketten CIKARILDI;
# gercek sayi rapora `Ran N tests` olarak zaten dusuyor.
k('C14z', 'tur4_paket_uret.py kendi testleriyle sinanir (sayi raporda)',
  _g14z_ok, _g14z)

# --- C14za CALISTIRMALI: token_olcum.py tahmin UYDURMAZ (9 Kasim 2026) -------
# NEDEN: bir tur boyunca "bayt/4" tahmini yazdim ve %33 yanlisti. Betik
# tiktoken YOKKEN de dogru davranmali: sayi UYDURMAMALI, OLCULMEDI demeli.
# ILK YAZIM YANMADI (T5): kapi CIKTI METNINE bakiyordu ("No module named"
# ariyordu). Uydurma sayi basan mutasyon o metni hic uretmedigi icin kapi
# ATLANDI ve PASS verdi -> totoloji. Duzeltildi: kapi artik ORTAMI olcer
# (`python -c "import tiktoken"`), ciktinin sozune guvenmez.
_g14za = ''
_g14za_ok = False
try:
    import subprocess as _sp2
    _tp2 = os.path.join(_BURASI, 'token_olcum.py')
    _kok2 = os.path.join(_BURASI, os.pardir)
    if not os.path.exists(_tp2):
        _g14za = 'CALISTIRILAMADI: token_olcum.py yok'
    else:
        _h = []
        _kaynak = open(_tp2, encoding='utf-8').read()
        # (0) kaynakta GERCEK tokenizer cagrisi var mi
        if 'get_encoding' not in _kaynak:
            _h.append('gercek tokenizer cagrisi yok')
        # (1) ORTAM: bu yorumlayicida tiktoken var mi?
        # timeout (13 Kasim 2026, Z14): timeout'suz birakildiginda bir venv
        # kilidi/askida kalma lint'i SONSUZA kadar bekletirdi — C15g olcer.
        _var = _sp2.run([sys.executable, '-c', 'import tiktoken'],
                        capture_output=True, text=True, timeout=60)
        if _var.returncode != 0:
            # (1a) YOKKEN: rc 2 ve OLCULMEDI olmali; sayi BASILMAMALI
            _r = _sp2.run([sys.executable, _tp2], cwd=_kok2,
                          capture_output=True, text=True, timeout=60)
            _cik = (_r.stdout + _r.stderr)
            if _r.returncode != 2:
                _h.append('tiktoken yokken rc=%d (2 beklenir)' % _r.returncode)
            if 'OLCULMEDI' not in _cik:
                _h.append('tiktoken yokken OLCULMEDI yazmiyor')
            # UYDURMA SAYI testi: "token:" + rakam dizisi ciktida olmamali
            if re.search(r'token\s*[:=]\s*\d', _cik):
                _h.append('tiktoken yokken SAYI basiyor (uydurma)')
            _rejim = 'tiktoken YOK -> OLCULMEDI+rc2'
        else:
            # (1b) VARKEN: gercek sayilar pozitif tamsayi olmali
            _r = _sp2.run([sys.executable, _tp2, '--json'], cwd=_kok2,
                          capture_output=True, text=True, timeout=120)
            if _r.returncode != 0:
                _h.append('tiktoken varken rc=%d' % _r.returncode)
            else:
                try:
                    _j = json.loads(_r.stdout)
                    _ok_sayi = [x for x in _j.get('olculen', [])
                                if x.get('durum') == 'OK']
                    if not _ok_sayi:
                        _h.append('--json hicbir dosya olcmedi')
                    for _x in _ok_sayi:
                        for _v in _x.get('token', {}).values():
                            if not isinstance(_v, int) or _v <= 0:
                                _h.append('%s: token degeri gecersiz' % _x.get('dosya'))
                                break
                except Exception as _ej:
                    _h.append('--json ayristirilamadi: %s' % _ej)
            _rejim = 'tiktoken VAR -> gercek sayi'
        _g14za_ok = not _h
        _g14za = '%s · %s' % (_rejim,
                              ('HATA: ' + ' | '.join(_h)) if _h else 'dogru davrandi')
except Exception as _e:
    _g14za = 'CALISTIRILAMADI: %s' % _e
k('C14za', 'token_olcum.py tahmin uydurmaz; tiktoken yokken OLCULMEDI der',
  _g14za_ok, _g14za)

# --- C15a: kapanmis madde yeniden sorulmaz (SKILL.md §7.5, 9 Kasim 2026) -----
# NEDEN: 3. turda 18 modelin 7 maddesi ITIRAZSIZ kapandi (>=8 KAPANDI, 0
# KAPANMADI) ama 4. tur paketi AYNI 16 maddeyi yeniden soruyordu. Tur sayisini
# sisiren sey yeni kusur degil, KAPANMIS maddenin yeniden acilmasidir.
# Kural SKILL.md §7.5; kayit `docs/MADDE_KAPANIS.json`.
# Kapi kaynagi DISKTEN degil URETICIDEN okur: paket dosyasi bayat olabilir,
# uretici metni her zaman gunceldir (C14y ile ayni gerekce).
_g15a = ''
_g15a_ok = False
try:
    _gp = os.path.join(_BURASI, os.pardir, 'docs', 'MADDE_KAPANIS.json')
    if not os.path.exists(_gp):
        _g15a = 'CALISTIRILAMADI: docs/MADDE_KAPANIS.json yok'
    else:
        _h = []
        with open(_gp, encoding='utf-8') as _f:
            _kayit = json.load(_f)
        _esik = _kayit.get('_esik', {})
        _min_k = int(_esik.get('itirazsiz_min_kapandi', 8))
        _max_n = int(_esik.get('itirazsiz_max_kapanmadi', 0))
        # (1) kayit kendi tanimina uyuyor mu — 'itirazsiz' etiketi esikle tutarli mi
        _kapali = []
        for _m in _kayit.get('maddeler', []):
            _a, _b = int(_m.get('kapandi', 0)), int(_m.get('kapanmadi', 0))
            if _a < _min_k or _b > _max_n:
                _h.append('%s kayitta ama esigi saglamiyor (%d/%d)'
                          % (_m.get('id'), _a, _b))
                continue
            if _m.get('eser_degisti') == 'HAYIR' and not _m.get('yeniden_acma_gerekcesi'):
                _kapali.append(_m['id'])
            elif _m.get('eser_degisti') not in ('EVET', 'HAYIR'):
                _h.append('%s eser_degisti gecersiz: %r'
                          % (_m.get('id'), _m.get('eser_degisti')))
        # (2) URETICININ P1 metninde bu maddeler var mi
        _t4y = os.path.join(_BURASI, 'tur4_paket_uret.py')
        if not os.path.exists(_t4y):
            _h.append('tur4_paket_uret.py yok — paket olculemedi')
            _sorulan = set()
        else:
            import importlib.util as _iu
            _sp = _iu.spec_from_file_location('_t4_c15a', _t4y)
            _mod = _iu.module_from_spec(_sp)
            _sp.loader.exec_module(_mod)
            _p1 = _mod.uret(_mod.P1_ETIKET)
            _sorulan = set(re.findall(r'^### (D\d+) —', _p1, re.M))
            if not _sorulan:
                _h.append('uretici P1 metninde madde basligi yok — olcum yapilamadi')
        _tekrar = sorted(set(_kapali) & _sorulan, key=lambda x: int(x[1:]))
        if _tekrar:
            _h.append('ITIRAZSIZ kapanmis ama YENIDEN sorulan: %s' % _tekrar)
        _g15a_ok = not _h
        _g15a = ('kayit=%d madde · itirazsiz+degmedi=%d · P1 sorulan=%d · tekrar=%d'
                 % (len(_kayit.get('maddeler', [])), len(_kapali), len(_sorulan),
                    len(_tekrar)))
        if _h:
            _g15a += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g15a = 'CALISTIRILAMADI: %s' % _e
k('C15a', 'kapanmis madde yeniden sorulmaz (§7.5, docs/MADDE_KAPANIS.json)',
  _g15a_ok, _g15a)

# --- C15b: tur haritasi diskle celismez (docs/TUR_HARITASI.md, 9 Kasim 2026) --
# NEDEN: D10 (gomulu sayac) UC KEZ tekrarladi — belgeye elle yazilan sayi bayatlar.
# `docs/TUR_HARITASI.md` tur sayisini, paket sayisini ve cevapsiz paket listesini
# tasiyor. Bunlar diskten OLCULUR; bayatlarsa kapi FAIL verir.
# Olculen 3 sey: (1) haritada adi gecen her paket diskte VAR mi, (2) haritanin
# "18 dosya" iddiasi diskteki paket sayisiyla ayni mi, (3) "cevap vermeyen (5)"
# listesi 2000 B altindaki bos iskeletlerle ayni mi.
# [DUZELTME 2026-11-09] (3) BOZULDU ve sebebi kapiydi: "bos" olcutu DOSYA BOYUTU
# (<2000 B) idi. Bos iskeletlere olcum blogu yazilinca dosyalar 2 650-3 113 B oldu
# ve kapi "diskte 0 bos iskelet" dedi — oysa 6 dosyada hala TEK cevap blogu yoktu.
# Boyut, "cevap var mi" sorusunun VEKILIDIR ve vekil yaniltir. Yeni olcut:
# `^MODEL:` satiri sayisi (cevap blogunun zorunlu ilk satiri — iskeletin kendi
# kurali). Olculdu: 8 dolu dosyada MODEL: 9-19; 6 bos dosyada 0.
_g15b = ''
_g15b_ok = False
try:
    _hp = os.path.join(_BURASI, os.pardir, 'docs', 'TUR_HARITASI.md')
    if not os.path.exists(_hp):
        _g15b = 'CALISTIRILAMADI: docs/TUR_HARITASI.md yok'
    else:
        _h = []
        _hd = open(_hp, encoding='utf-8').read()
        _dd = os.path.join(_BURASI, os.pardir, 'docs')
        # (1) haritada `k1_...` / `DIS_DENETIM_TUR...` olarak anilan dosyalar
        _anilan = set(re.findall(r'\| `((?:k1_|DIS_)[A-Za-z0-9_.-]+\.md)`', _hd))
        _yok = sorted(x for x in _anilan if not os.path.exists(os.path.join(_dd, x)))
        if _yok:
            _h.append('haritada anilan ama diskte OLMAYAN: %s' % _yok)
        # (2) diskteki paket sayisi (TUR4'un P1/P2 parcalari haric)
        _disk = sorted(f for f in os.listdir(_dd)
                       if (f.startswith('k1_denetim_paket') or
                           f.startswith('k1_dis_denetim_paketi') or
                           f.startswith('DIS_DENETIM_TUR3_2026') or
                           f.startswith('DIS_DENETIM_TUR4_2026')))
        _m = re.search(r'## 1\. ÜRETİLEN PAKETLER — (\d+) dosya', _hd)
        if not _m:
            _h.append('haritada "## 1. ÜRETİLEN PAKETLER — <n> dosya" basligi yok')
        elif int(_m.group(1)) != len(_disk):
            _h.append('harita "%s dosya" diyor, diskte %d paket' % (_m.group(1), len(_disk)))
        # (3) bos iskelet listesi
        # [DUZELTME 2026-11-09] eskiden: os.path.getsize(...) < 2000
        # yeni olcut: cevap blogu sayisi (^MODEL:). Boyut vekildi, vekil yaniltti.
        _bos = []
        _cevapblogu = {}
        for _f in sorted(os.listdir(_dd)):
            if not (_f.startswith('k1_cevaplar') and _f.endswith('.md')):
                continue
            _ft = open(os.path.join(_dd, _f), encoding='utf-8', errors='replace').read()
            _nb = len(re.findall(r'^MODEL:', _ft, re.M))
            _cevapblogu[_f] = _nb
            if _nb == 0:
                _bos.append(_f)
        # harita "bos iskelet = N" demeli; N diskteki 2000 B alti sayisiyla ayni olmali
        # metin Turkce yazimla duruyor ('dosyası', 'boş') — kalibi metne hizala,
        # tahmine degil: aksan-toleransli siniflar kullanilir.
        # [DUZELTME 2026-11-09] kalip 3 yazimi da tanimali:
        #   "6 cevap dosyasi bos iskelet" · "6'si **boş iskelet**" · "6 paket cevap dosyasi ..."
        # [DUZELTME 2026-11-09] Ilk uyusan kalibi almak YETMEDI: harita sayiyi IKI
        # ayri yerde yaziyor (§2 basligi ve "Olculen ... kopyalamadan SONRA" satiri).
        # Ilk uyusma oteki ifadeyi golgeliyordu -> M9 mutasyonu YANMADI (olculdu).
        # Simdi TUM uyusmalar toplanir ve HER BIRI diskteki sayiya esit olmali.
        # [DUZELTME 2026-11-09 #2] KALIN ISARETI KACAGI. Olculdu: 4 yazimdan 3'u
        # gorulmuyordu — `**6** cevap`, `**6**'si **bos iskelet**`, `**10** paket ...`.
        # Yani harita sayiyi kalin yazarsa kapi SESSIZ kalip PASS veriyordu.
        # Sessiz kapi, yanlis PASS'in en tehlikeli turudur.
        # COZUM: eslestirme KALIN ISARETI SILINMIS kopya uzerinde yapilir. `**`
        # silinmesi satir sonu silmez -> satir numaralari DEGISMEZ, rapor dogru kalir.
        _hd_n = _hd.replace('**', '').replace('__', '')
        # TARIHSEL SOZ: `>` ile baslayan blok alintilar GECMIS SES'tir, guncel iddia
        # degildir. I6 geregi eski/yanlis satir silinmez, alintiya alinir. Bu satirlar
        # eslestirmeden CIKARILIR (yoksa duzeltme notu kendi kendini yakalar —
        # bes kez tekrarlanan "kendi aciklamani kapiya yem etme" tuzagi).
        # [DUZELTME #3] Once "TUM blok alintilar muaf" yazdim; M13b ile OLCULDU ve
        # DELIK CIKTI: yanlis bir sayi `>` icine yazilinca kapi gormuyordu (rc=0).
        # Muafiyet artik ISARET SARTINA bagli: yalniz `[GECERSIZ]`/`[DUZELTME`/
        # `[ESKI` etiketi TASIYAN blok alintilar gecmis sozdur. Isaretsiz `>` satiri
        # normal iddia sayilir (kapi onu gorur).
        _MUAF = ('[GECERSIZ', '[DUZELTME', '[ESKI')
        _hd_n = '\n'.join(
            ('' if (_sl.lstrip().startswith('>') and any(_m in _sl for _m in _MUAF))
             else _sl)
            for _sl in _hd_n.split('\n'))
        _mb = None
        _iddialar = []
        for _rp in (r"(\d+)\s+cevap\s+dosyas[\u0131i]\s+bo[\u015fs]\s+iskelet",
                    r"(\d+)\s+paket\s+cevap\s+dosyas[\u0131i]\s+a[\u00e7c][\u0131i]ld[\u0131i]",
                    r"(\d+)['\u2019]s[\u0131i]\s+bo[\u015fs]\s+iskelet"):
            for _mm2 in re.finditer(_rp, _hd_n):
                _iddialar.append((int(_mm2.group(1)),
                                  _hd_n[:_mm2.start()].count(chr(10)) + 1))
        if _iddialar:
            _yanlis = [(n, l) for n, l in _iddialar if n != len(_bos)]
            if _yanlis:
                _h.append('haritada %d yerde "bos iskelet" sayisi var, diskte %d; '
                          'uymayanlar: %s'
                          % (len(_iddialar), len(_bos),
                             ', '.join('satir %d' % l for _, l in _yanlis)))
            _mb = True   # rapora yazilacak
        else:
            _h.append('haritada "<n> cevap dosyasi bos iskelet" satiri yok')
        _g15b_ok = not _h
        _g15b = ('paket=%d · harita=%s · cevapsiz=%d (cevap blogu 0) · anilan=%d · '
                 'cevap_blogu=%d/%d dosyada >0 · kalin_tolerans=ACIK' % (
                     len(_disk),
                     ('%s/%d yer' % (len(_bos), len(_iddialar)) if _iddialar else '-'),
                     len(_bos), len(_anilan),
                     sum(1 for x in _cevapblogu.values() if x > 0), len(_cevapblogu)))
        if _h:
            _g15b += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g15b = 'CALISTIRILAMADI: %s' % _e
k('C15b', 'tur haritasi diskle celismez (docs/TUR_HARITASI.md sayilari olculur)',
  _g15b_ok, _g15b)

# --- C15c: paket kunyesindeki sha, gomulu eserle ayni (9 Kasim 2026) ---------
# NEDEN: `k1_denetim_paket_v135.md` kunyesi aylarca v1.3.3'un sha'sini tasidi
# (v1.3.3 paketinden kopyalanmis, guncellenmemis). Denetciler yazdi, kapi gormedi.
#
# YONTEM — cit ESLESTIRME YOK. Denendi ve 3 kez yanlis cikardi (olculdu):
#   (i)  `## BOLUM D` sonrasi her sey        -> kuyruk metni sizdi
#   (ii) ilk ``` ... son ```                 -> SKILL.md'nin KENDI citlerini yedi
#   (iii) ilk ``` ... ilk ```                -> dosyada EK A/B/C varsa erken kesti
# Bunun yerine: dosyadaki TUM citli bloklar cikarilir, her birinin sha256'si
# 3 normalizasyonla (ham / +\n / strip+\n) hesaplanir. Kunye sha'sini TUTAN blok
# varsa AYNI. sha256 aramasi yanlis-pozitif uretemez.
# Kunye bicimi 3 turlu: `sha256: <64>` · `sha256 <64>` · `sha256 `<64>``
# Gomulu eser tasimayan paket FAIL degil; `gomdesiz` olarak raporlanir.
_g15c = ''
_g15c_ok = False
try:
    import hashlib as _hl
    _dd = os.path.join(_BURASI, os.pardir, 'docs')
    _paket = sorted(f for f in os.listdir(_dd)
                    if f.endswith('.md') and (
                        f.startswith('k1_denetim_paket') or
                        f.startswith('k1_dis_denetim_paketi') or
                        f.startswith('DIS_DENETIM_TUR')))
    _h = []
    _ayni, _farkli, _gomdesiz, _kunyesiz = [], [], [], []
    _RE_KUNYE = (r'^sha256:\s*`?([0-9a-f]{64})',
                 r'^`?sha256`?\s+`([0-9a-f]{64})`',
                 r'sha256\s+`([0-9a-f]{64})`')
    for _f in _paket:
        _t = open(os.path.join(_dd, _f), encoding='utf-8').read()
        _k = None
        for _rp in _RE_KUNYE:
            _mm = re.search(_rp, _t, re.M)
            if _mm:
                _k = _mm.group(1)
                break
        if _k is None:
            _kunyesiz.append(_f)
            continue
        # Bu paket eseri GOMUYOR mu? Uc bicimden biri yoksa gomdesiz sayilir.
        # (olculdu: DIS_DENETIM_TUR4_P2 yalniz EK B/EK C tasir; EK A = P1'de)
        _gomuyor = bool(re.search(r'===\s*SKILL\.md BA\u015eLANGI\u00c7 \(birebir\)|'
                                  r'^#{1,4}\s*(?:B\u00d6L\u00dcM|BOLUM)\s*D|'
                                  r'^#{1,4}\s*EK\s*A\s*\u2014\s*`SKILL\.md`',
                                  _t, re.M))
        # --- (0) MARKER bicimi: `=== SKILL.md BASLANGIC (birebir) ===` ... BITIS
        # Bu paketlerde cit YOK (olculdu: v1.3.x, v1.4.0-v1.4.6).
        _bulundu = None
        _mm = re.search(r'===\s*SKILL\.md BA\u015eLANGI\u00c7 \(birebir\)\s*===\n'
                        r'(.*?)\n===\s*SKILL\.md B\u0130T\u0130\u015e \(birebir\)\s*===',
                        _t, re.S)
        if _mm is not None:
            _mg = _mm.group(1)
            for _z in (_mg, _mg + '\n', _mg.strip() + '\n'):
                if _hl.sha256(_z.encode()).hexdigest() == _k:
                    _bulundu = _mg
                    break
        # cit konumlari: 4'luk once, 3'luk sonra (4'un icindeki 3 sayilmasin)
        _poz = [(x.start(), 4) for x in re.finditer(r'````', _t)]
        _pos3 = [(x.start(), 3) for x in re.finditer(r'(?<!`)```(?!`)', _t)]
        # 4'luk cit araligina dusen 3'lukleri at
        _dort = [(a, a + 4) for a, _ in _poz]
        _pos3 = [(a, n) for a, n in _pos3
                 if not any(a0 <= a < a1 for a0, a1 in _dort)]
        _cit = sorted(_poz + _pos3)
        for _i in (range(len(_cit)) if _bulundu is None else []):
            _a, _na = _cit[_i]
            for _j in range(_i + 1, len(_cit)):
                _b, _nb = _cit[_j]
                if _nb != _na:
                    continue
                _ic = _t[_a + _na:_b]
                _s0 = _ic.split('\n', 1)
                if len(_s0) == 2 and len(_s0[0]) <= 12 \
                        and re.fullmatch(r'[A-Za-z]*', _s0[0].strip()):
                    _ic = _s0[1]
                for _z in (_ic, _ic + '\n', _ic.strip() + '\n'):
                    if _hl.sha256(_z.encode()).hexdigest() == _k:
                        _bulundu = _ic
                        break
                if _bulundu is not None:
                    break
            if _bulundu is not None:
                break
        if _bulundu is not None:
            _ayni.append(_f)
        elif not _gomuyor:
            _gomdesiz.append(_f)
        else:
            # hicbir blok tutmadi -> gercek uyusmazlik adayi; en yakin adayi raporla
            _aday = _t[_cit[0][0] + _cit[0][1]:] if _cit else ''
            _acy = _hl.sha256(_aday.encode()).hexdigest()[:12] if _aday else '-'
            _farkli.append('%s (kunye %s, hicbir blok tutmadi; %d blok)'
                           % (_f, _k[:12], len(_cit) // 2))
    if _farkli:
        _h.append('KUNYE ile GOMULU GOVDE uyusmuyor: %s' % _farkli)
    _g15c_ok = not _h
    _g15c = ('paket=%d · ayni=%d · farkli=%d · gomdesiz=%d · kunyesiz=%d'
             % (len(_paket), len(_ayni), len(_farkli), len(_gomdesiz), len(_kunyesiz)))
    if _gomdesiz:
        _g15c += ' · gomdesiz: %s' % _gomdesiz
    if _kunyesiz:
        _g15c += ' · kunyesiz: %s' % _kunyesiz
    if _h:
        _g15c += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g15c = 'CALISTIRILAMADI: %s' % _e
k('C15c', 'paket kunye sha = gomulu eser sha (docs/*paket*.md)', _g15c_ok, _g15c)

# --- C15d: "cevapsiz" maddede KAPANDI etiketi yasak (9 Kasim 2026) -----------
# NEDEN: `MADDE_KAPANIS.json` 7 maddeyi "itirazsiz KAPANDI" diye kaydetti; ama
# ayni dosyanin `_olcum_notu` sunu soyluyor: "her maddeye en fazla 9-11 model
# cevap vermis ... Cevap vermeyen modelin maddeyi gorup gormedigi OLCULMEDI".
# Yani `cevapsiz` 9-10 iken "KAPANDI" yazmak SESSIZLIGI RIZA saymaktir.
# Kayit durusttu, ETIKET yanlisti. Bu kapi etiketi kilitler (SKILL.md §7.5).
_g15d = ''
_g15d_ok = False
try:
    _gp = os.path.join(_BURASI, os.pardir, 'docs', 'MADDE_KAPANIS.json')
    if not os.path.exists(_gp):
        _g15d = 'CALISTIRILAMADI: docs/MADDE_KAPANIS.json yok'
    else:
        _h = []
        with open(_gp, encoding='utf-8') as _f:
            _kay = json.load(_f)
        _esz = _kay.get('_esik', {})
        if _esz.get('cevapsiz_as_consent') is not False:
            _h.append('_esik.cevapsiz_as_consent False degil: %r'
                      % _esz.get('cevapsiz_as_consent'))
        _maddeler = _kay.get('maddeler', [])
        _cev = [m for m in _maddeler if int(m.get('cevapsiz', 0)) > 0]
        for _m in _maddeler:
            if str(_m.get('etiket', '')) == 'KAPANDI':
                _h.append('%s etiket=KAPANDI (cevapsiz=%s)'
                          % (_m.get('id'), _m.get('cevapsiz')))
        # SKILL.md §7.5 "cevapsiz sayilmaz" gibi IK-I-ANLAMLI ifade tasimamali
        _sk = open(os.path.join(_BURASI, os.pardir, 'SKILL.md'),
                   encoding='utf-8').read()
        if 'cevapsiz sayilmaz' in _sk:
            _h.append('SKILL.md hala "cevapsiz sayilmaz" diyor (iki anlamli: '
                      'riza mi, kapanis mi?)')
        if 'Sessizlik riza degildir' not in _sk:
            _h.append('SKILL.md §7.5 "Sessizlik riza degildir" cumlesini tasimiyor')
        _g15d_ok = not _h
        _g15d = ('madde=%d · cevapsiz>0 olan=%d · hepsi ITIRAZ_YOK=%s · '
                 'cevapsiz_as_consent=%s'
                 % (len(_maddeler), len(_cev),
                    all(str(m.get('etiket')) == 'ITIRAZ_YOK' for m in _cev),
                    _esz.get('cevapsiz_as_consent')))
        if _h:
            _g15d += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g15d = 'CALISTIRILAMADI: %s' % _e
k('C15d', 'cevapsiz maddede KAPANDI etiketi yasak (sessizlik riza degildir)',
  _g15d_ok, _g15d)


# --- C15j: her subprocess cagrisi TIMEOUT tasir (13 Kasim 2026, Z14) -------
# NEDEN (sira 8 taramasi): 3 betik · 33 cagri · UCUNCU PARTI IKILI YOK —
# hepsi `sys.executable`, `bash`, `git`. Ama OLCULDU ki iki cagrida `timeout=`
# YOKTU:
#   skill_lint.py:2360   `python3 -c 'import tiktoken'` (ortam yoklamasi)
#   mutasyon_tara.py:108 skill_lint cagrisi (60-120 s suren is)
# Timeout'suz cagri, kapinin HIC DONMEMESI demektir — CI'da "gecti" degil
# "asili kaldi". Bu, fail-OPEN'in sessiz bicimidir: FAIL yazmaz, BEKLER.
# Kapi UC sey ister: (a) hicbir cagri timeout'suz olmamali, (b) VARLIK YETMEZ —
# DEGER de denetlenir (asgari 10 s), (c) OLCUMUN KENDISI ayirt edici olmali:
# uc ornek (timeout YOK / 30 / 0.001) dogru siniflandirilmali.
#
# NEDEN (b) — OLCULDU (13 Kasim 2026, Z16b): eski hal yalniz `'timeout' in
# keywords` bakiyordu. `timeout=0.001` GECIYORDU: varlik var, deger anlamsiz.
# Oyle bir cagri pratikte HER ZAMAN zaman asimina ugrar — koruma kagittan.
#   M93  mutasyon_tara.py timeout=900 -> timeout=0.001
#        -> C15j FAIL "timeout-suz/kuccuk=1 (esik>10s) [mutasyon_tara.py:111]"
#        geri -> PASS; sha AYNI
# Literal OLMAYAN (degisken) timeout degeri BILINMIYOR sayilir ve FAIL eder:
# kanit yoksa "var" demeyiz.
#
# NEDEN (c) — ilk yazimda oz-test "iyi" ornegi `timeout=5` idi ve esik 10
# olunca YAKALANDI: oz-test yanlis-KIRMIZI verdi (olculdu). Ornek deger
# esigin USTUNDE olmali; testin kendisi de bu yuzden bir iddiadir.


def _tp_eksik(yol, asgari=None):
    """`<x>.run(...)` cagrilarindan `timeout` tasimayanlarin satir numaralari.

    [DUZELTME 13 Kasim 2026, Z16b] VARLIK YETMEZ — DEGER DE DENETLENIR.
    Eski hal yalniz `'timeout' in keywords` bakiyordu; `timeout=0.001` de
    geciyordu. Oyle bir cagri pratikte HER ZAMAN zaman asimina ugrar: kapi
    "suresiz bekleme yok" der ama komut hic bitmez — yani koruma kagittan.
    `asgari` verilirse DEGER de karsilastirilir (<= asgari -> kotu).
    Literal olmayan (degisken) deger olculur: deger BILINMIYORSA sayilir.
    """
    import ast as _ast_tp
    try:
        with open(yol, encoding='utf-8') as _f:
            _agac = _ast_tp.parse(_f.read())
    except Exception:
        return [0]
    _kotu = []
    for _d in _ast_tp.walk(_agac):
        if not isinstance(_d, _ast_tp.Call):
            continue
        _fn = _d.func
        if not (isinstance(_fn, _ast_tp.Attribute) and _fn.attr == 'run'):
            continue
        _anah = {}
        for _kk in _d.keywords:
            if _kk.arg:
                _anah[_kk.arg] = _kk.value
        if 'timeout' not in _anah:
            _kotu.append(_d.lineno)
            continue
        if asgari is None:
            continue
        _v = _anah['timeout']
        if isinstance(_v, _ast_tp.Constant) and isinstance(_v.value, (int, float)) \
                and not isinstance(_v.value, bool):
            if _v.value <= asgari:
                _kotu.append(_d.lineno)
        else:
            # literal degil: deger BILINMIYOR -> kanit yok, sayilir
            _kotu.append(_d.lineno)
    return sorted(_kotu)


_tp_kotu = []
_tp_taranan = 0
_tp_oz = 'CALISTIRILAMADI'
try:
    import glob as _gl_tp
    import tempfile as _tf_tp
    # [DUZELTME 13 Kasim 2026, Z17f / kalem #10] KAPSAM GENISLETILDI.
    # NEDEN (EK 82 OLCULMEYEN): "_tp_dosyalar" yalniz `scripts/*.py` (ust
    # duzey) idi; `scripts/tests/` ALT DIZINI taranmiyordu. Yani lab kendi
    # test betiklerinde timeout'suz cagri yapsa kapi gormezdi. OLCULDU:
    # genisletmeden once `scripts/*.py` = 21 dosya; ALT DIZINLE = 22 dosya ve
    # 1 IHLAL cikti (`scripts/tests/test_tur4_paket_uret.py:144` -> timeout eklendi).
    # [DUZELTME 13 Kasim 2026, Z18a / B-#4] SABLONLAR ARTIK ZORUNLU.
    # NEDEN (olculdu): Z17f'de sablon taramasi "OLCULUR ama FAIL ettirmez"
    # birakilmisti cunku 41 ihlal vardi (ATLAS 16 + KOD 25). Ali "kapat" dedi.
    # Talep uzerine 41 cagrinin HEPSINE timeout eklendi:
    #   atlas_selftest.py 17 cagri -> timeout=600
    #   kod_selftest.py   20 cagri -> timeout=600
    #   api_surface/chg_reconcile/dep_audit/secret_scan/test_attest 5 cagri -> 120
    # Ve sayilar KORUNDU (olculdu, kendi aday surumuyle degil):
    #   ATLAS OZ-TEST: 142/142 · KOD OZ-TEST: 174/174
    # Yani "41 cagriyi kapatmak oz-testi riske atar" korkusu OLCULDU ve
    # gerceklesmedi. Kapsam artik sessiz borc degil: `sablon-ihlal>0` -> FAIL.
    # OLCULDU (M105): sablonlardan bir timeout silindi -> FAIL.
    _tp_dosyalar = sorted(_gl_tp.glob(os.path.join(_BURASI, '*.py'))) + \
        sorted(_gl_tp.glob(os.path.join(_BURASI, 'tests', '*.py')))
    # Asgari esik: 10 s. Daha kisasi pratikte her zaman zaman asimi.
    _TP_ASGARI = 10
    for _tp_y in _tp_dosyalar:
        _tp_taranan += 1
        for _tp_satir in _tp_eksik(_tp_y, _TP_ASGARI):
            _tp_kotu.append('%s:%d' % (os.path.basename(_tp_y), _tp_satir))
    # Sablonlar: OLCUL + RAPOR (FAIL ettirmez) — kapsam karari insanda.
    _tp_sablon_ihlal = 0
    for _tp_kok in ('ATLAS_SABLONLAR', 'KOD_SABLONLAR'):
        _tp_dizin = os.path.join(os.path.dirname(_BURASI), _tp_kok)
        if not os.path.isdir(_tp_dizin):
            continue
        for _tp_y2 in sorted(_gl_tp.glob(os.path.join(_tp_dizin, '**', '*.py'),
                                         recursive=True)):
            _tp_sablon_ihlal += len(_tp_eksik(_tp_y2, _TP_ASGARI))
    if _tp_sablon_ihlal:
        _tp_kotu.append('SABLON:%d' % _tp_sablon_ihlal)
    _tp_d = _tf_tp.mkdtemp()
    _tp_kotu_ornek = os.path.join(_tp_d, 'kotu.py')
    with open(_tp_kotu_ornek, 'w', encoding='utf-8') as _f:
        _f.write("import subprocess\n"
                 "subprocess.run(['echo', 'x'], capture_output=True)\n")
    _tp_iyi_ornek = os.path.join(_tp_d, 'iyi.py')
    with open(_tp_iyi_ornek, 'w', encoding='utf-8') as _f:
        # Ornek DEGERI esigin USTUNDE olmali (esik 10): 5 yazilirsa "iyi"
        # ornek de yakalanir ve oz-test yanlis-KIRMIZI verir (olculdu).
        _f.write("import subprocess\n"
                 "subprocess.run(['echo', 'x'], capture_output=True, timeout=30)\n")
    # UCUNCU ORNEK (Z16b): timeout VAR ama DEGERI 0.001 -> yine kotu olmali.
    # Bu olmadan "varlik denetimi" degeri denetim sanilir.
    _tp_kucuk_ornek = os.path.join(_tp_d, 'kucuk.py')
    with open(_tp_kucuk_ornek, 'w', encoding='utf-8') as _f:
        _f.write("import subprocess\n"
                 "subprocess.run(['echo', 'x'], capture_output=True, timeout=0.001)\n")
    _tp_a = _tp_eksik(_tp_kotu_ornek, _TP_ASGARI)
    _tp_b = _tp_eksik(_tp_iyi_ornek, _TP_ASGARI)
    _tp_c = _tp_eksik(_tp_kucuk_ornek, _TP_ASGARI)
    if len(_tp_a) == 1 and not _tp_b and len(_tp_c) == 1:
        _tp_oz = 'AYIRT_ETTI'
    else:
        _tp_oz = 'KOR (yok=%d iyi=%d kucuk=%d)' % (
            len(_tp_a), len(_tp_b), len(_tp_c))
except Exception as _e_tp:
    _tp_oz = 'CALISTIRILAMADI: %s' % _e_tp

# --- C15l: PLATO'nun orneklem buyuklugune gore davranisi TARANIR (Z17c) ----
# NEDEN (EK 81 OLCULMEYEN): "Plato n'ye gore nasil davraniyor, taranmadi.
# Yalniz n=6 ve n=12 olculdu." Iki nokta egri degildir. Esik secimi ancak
# platonun ICINDE savunulabilir; plato n ile daraliyorsa "plato 0.30-0.60"
# cumlesi yalniz kucuk n icin dogrudur.
#
# OLCULDU (13 Kasim 2026): n=3..6 -> 0.30-0.60 (ORTA) · n>=7 -> 0.30-0.50
# (UST KENAR). Yani plato n ile DARALIYOR; ZAYIF uyarisi n<12'de cikiyor.
#
# KAPI UC SEY ISTER:
#   (1) tarama rc=0 ve HER n icin PLATO satiri ayristirilabilsin
#   (2) `sonuc_degisen=0` — hicbir n'de hukum esige duyarli OLMAMALI
#   (3) `plato(n>=10)` tek deger olmali (DEGISKEN degil) VE kucuk-orneklem
#       platosundan FARKLI olmali: fark, "n ile daralma" iddiasinin kanitidir.
#       Esitlenirse esik secimi iddiasi kanitsiz kalir -> FAIL (fail-closed).
try:
    import subprocess as _plt_sp
    _plt_kok = os.path.dirname(_BURASI)
    _plt_r = _plt_sp.run([sys.executable,
                          os.path.join(_BURASI, 'ayet_ozet_kontrol.py'),
                          '--plato-tarama'],
                         capture_output=True, text=True, timeout=900,
                         cwd=_plt_kok)
    _plt_sat = ''
    for _plt_l in _plt_r.stdout.splitlines():
        if _plt_l.startswith('TARAMA: '):
            _plt_sat = _plt_l.strip()
    _plt_h = []
    if _plt_r.returncode != 0:
        _plt_h.append('rc=%d' % _plt_r.returncode)
    if not _plt_sat:
        _plt_h.append('TARAMA satiri yok')
        _plt_oz = '-'
    else:
        import re as _plt_re
        _plt_m = _plt_re.search(
            r'plato\(kucuk orneklem\)=([\d.\-]+) · plato\(n>=(\d+)\)=([\w.\-]+)'
            r' · sonuc_degisen=(\d+) · zayif_uyari_n<(\d+)=(\w+)'
            r' · secili=([\d.]+) · plato_icinde=(\w+)'
            r' · n_max_veri=(\d+) · monoton=(\w+) · sure=([\d.]+)s',
            _plt_sat)
        if not _plt_m:
            _plt_h.append('TARAMA ayristirilamadi')
            _plt_oz = '-'
        else:
            (_kucuk, _esikN, _buyuk, _deg, _zN, _zay, _sec, _ic,
             _nveri, _mono, _sure) = _plt_m.groups()
            # VERI SINIRI (13 Kasim 2026, Z18e / B-#8) -----------------------
            # NEDEN (EK 88 OLCULMEYEN #8): "n>12 plato davranisi olculmedi
            # (SKILL.md'de 12 ayet var)." OLCULDU: snapshot'ta da AYNI 12 ayet
            # var -> n>12 icin VERI YOK. Sentetik doldurma YAPILMADI (tekrar
            # eden satir platonun n davranisi hakkinda kanit uretmez).
            # Kapi iki sey ister:
            #   (1) n_max_veri >= ORNEKLEM_ESIK(12): veri ZAYIF esiginin
            #       altina duserse "zayif uyari" olcutu dayanaksiz kalir.
            #   (2) monoton=evet: plato(n+1) ⊆ plato(n). Daralma beklenir
            #       (satir eklenince esigi gecen minimum kapsam ancak duser).
            #       Bu, olculemeyen n>12 icin UST SINIR verir: plato(n>12) ⊆
            #       plato(12)=0.30-0.50. Esik 0.50 ust kenarda; plato daralirsa
            #       `plato_icinde=hayir` cikar ve bu kapi yakalar.
            # ORNEKLEM_ESIK ayet_ozet_kontrol.py'de tanimli; burada YOK
            # (olculdu: NameError -> C15l CALISTIRILAMADI). Kendi sabitimizi
            # kullaniyoruz ve AYNI degeri tasidigini asagida olcuyoruz.
            _PLT_ORNEKLEM = 12
            if int(_nveri) < _PLT_ORNEKLEM:
                _plt_h.append('n_max_veri=%s < %d (veri azaldi — ZAYIF esigi '
                              'dayanaksiz)' % (_nveri, _PLT_ORNEKLEM))
            if _mono != 'evet':
                _plt_h.append('plato n ile IC ICE GECMIYOR (monoton=%s) — '
                              'ust sinir iddiasi gecersiz' % _mono)
            # SURE ESIGI (13 Kasim 2026, Z18d / B-#7; gerekce Z19 / B-#3) -----
            # NEDEN VAR (olculdu): kapi "agsiz" diyordu ama `ceviri()` once
            # CANLIYI deniyordu. Ayni makinede olculdu:
            #   --plato-tarama  ag acik : 512,53 / 546,79 / 489,15 s (3 tekrar)
            #   --plato-tarama  agsiz   :   1,10 s
            # Yani ag varken bu TEK kapi tum lint suresinin %98'iydi (lint
            # toplam 507,18 s). Alt kosulara SNAPSHOT_ONLY=1 verildi -> 1,08 s.
            #
            # ESIK NEDEN 60 s (insan secimi — EK 89 OLCULMEYEN #3):
            #   dogru hal 1,0 s (3 tekrar: 1,0 / 1,0 / 1,0 — sacilma yok)
            #   bozuk hal 457,2 / 512,53 / 546,79 / 489,15 s
            #   MARJ = 60x · iki rejim arasi ~60x-450x BOS BANT
            # Esik o bandin ALT ucunda: hem yanlis-KIRMIZI hem korluk riski dusuk.
            #
            # YAVAS MAKINEDE ESIK ASILIRSA: kapiyi SILME, esigi GEREKCELI
            # yukselt ve yeni marji buraya yaz. Silmek, B-#7'de duzeltilen
            # sessiz ag bagimliligini geri getirir.
            # ---- C-#10 (14 Kasim 2026): ESIK ARTIK CAKILI DEGIL, OLCULU ----
            # BULGU (olculdu): esik sabiti 60.0 idi ve ustundeki yorum
            # "MARJ 60x" diyordu. Orneklem n=12 -> 16 yapilinca dogru halin
            # suresi 1,0 s -> **1,7 s** oldu (3 tekrar: 1,7 / 1,7 / 1,7) ->
            # GERCEK marj **35,3x**. Yani yorumdaki 60x YANLIS hale geldi ve
            # bunu HICBIR sey soylemedi: marj sessizce eridi (n buyudukce
            # erimeye devam eder). Ayrica sabit SANIYE makineden makineye
            # tasinmaz: bu Mac'ten ~35x yavas bir makinede dogru hal esigi
            # asar ve kapi YANLIS-KIRMIZI verir.
            #
            # COZUM: sabit yerine (a) OLCULMUS referans, (b) ASGARI marj.
            #   esik = bekleme * MARJ_ASGARI   -> marj erirse burada FAIL.
            #   ayrica esik, BOZUK halin en kucuk olcumunun yarisini gecmez
            #   (bozuk hal 457,2 / 512,53 / 546,79 / 489,15 s -> taban 457,2).
            # Boylece iki yon de kapali: marj erimesi ve korluk.
            #
            # YAVAS MAKINE: esik asilirsa kapiyi SILME / sabiti buyutME.
            # Once `_PLT_SURE_BEKLEME`yi O MAKINEDE yeniden olc, tarihini ve
            # 3 tekrari yorumda guncelle, sonra marji yeniden hesapla.
            # Makine ~35x yavassa marj zaten 1x'e iner: o durumda asil soru
            # "bu makine bu kapiyi kosmali mi" — karar insanda (AGENTS §8).
            _PLT_SURE_BEKLEME = 1.7    # olculdu 2026-11-14, n=16, 3 tekrar
            _PLT_BOZUK_TABAN = 457.2   # olculdu, ag acik en kucuk (4 olcum)
            # ASGARI MARJ TURETILMIS, secilmis degil: bant genisligi
            # (bozuk/dogru) en az 100x olmali -> simetrik marj >= 10x.
            # Bugun bant = 457,2/1,7 = 269x -> marj 16,4x (>=10, gecer).
            # 100x'in alti: iki rejim ayrismiyor, kapi anlamsizlasir.
            _PLT_BANT_ASGARI = 100.0
            _PLT_MARJ_ASGARI = _PLT_BANT_ASGARI ** 0.5
            # ESIK = BANDIN GEOMETRIK ORTASI.
            # Iki olcum ayni makineden: dogru hal (bekleme) ve bozuk hal
            # (bozuk_taban). Geometrik orta, iki yonde ESIT carpan birakir:
            #   esik/bekleme == bozuk_taban/esik
            # Sayisal (bugun): sqrt(1.7 * 457.2) = 27.9 s
            #   yukari 16,4x  -> KORLUK payi (ag geri gelirse ~269x cikar)
            #   asagi  16,4x  -> ayni makinede olcum oynamasi icin pay
            # DIKKAT: "16,4x yavas makine toleransi" DEMEK DEGILDIR. Makine
            # tasindiginda tolerans `_PLT_BAYAT_CARPAN`(3x) kadardir; otesinde
            # kapi hukum vermez, YENIDEN OLC der (fail-closed).
            # Aritmetik orta (229 s) bozuk tarafa cok yakin olurdu; 60 sabiti
            # ise bandin ALT ucundaydi ve marji sessizce eriyordu (bulundu).
            _plt_esik = (_PLT_SURE_BEKLEME * _PLT_BOZUK_TABAN) ** 0.5
            # (1) MARJ: esik ile dogru hal arasinda en az MARJ_ASGARI kalsin.
            _plt_marj = _plt_esik / _PLT_SURE_BEKLEME
            if _plt_marj < _PLT_MARJ_ASGARI:
                _plt_h.append('MARJ YETERSIZ: esik %.1fs / dogru hal %.2fs = '
                              '%.1fx < asgari %.0fx'
                              % (_plt_esik, _PLT_SURE_BEKLEME, _plt_marj,
                                 _PLT_MARJ_ASGARI))
            # (2) KORLUK: esik bozuk tabana cok yaklasirsa yanlis-GECIRIR.
            if _plt_esik > _PLT_BOZUK_TABAN / 2.0:
                _plt_h.append('esik %.1fs bozuk tabana cok yakin (%.1fs) — '
                              'ag bagimliligini kacirabilir'
                              % (_plt_esik, _PLT_BOZUK_TABAN))
            # (3) BAYAT REFERANS: dogru hal referanstan buyuk olcude buyudu.
            # BUGUN OLDU: n=12 iken 1,0 s idi, n=16 ile 1,7 s. Kimse fark
            # etmedi cunku esik CAKILIYDI. Simdi referans bayatlarsa gorunur.
            # BAYATLIK ESIGI: 3x. NEDEN 3x (olculdu, M129-M132): bu kapi
            # MAKINEDEN BAGIMSIZ DEGIL ve bunu IDDIA ETMIYOR. Kayitli referans
            # bu makinede olculmustur; baska (yavas) bir makinede dogru hal
            # referanstan buyuk cikar. 3x icinde makine/kod oynamasi sayilir;
            # otesinde "bu olcum bu makine icin GECERLI DEGIL, yeniden olc"
            # denir. Fail-closed: sessizce eski referansla hukum vermez.
            # (M129: 25 s -> 14,7x -> FAIL "REFERANS BAYAT". Bu bir
            # "kirik" hukumu DEGIL, "yeniden kalibre et" cagrisidir.)
            _PLT_BAYAT_CARPAN = 3.0
            if float(_sure) > _PLT_SURE_BEKLEME * _PLT_BAYAT_CARPAN:
                _plt_h.append('REFERANS BAYAT: dogru hal %ss / referans %.2fs '
                              '= %.1fx — `_PLT_SURE_BEKLEME`yi olc ve tarihini '
                              'guncelle'
                              % (_sure, _PLT_SURE_BEKLEME,
                                 float(_sure) / _PLT_SURE_BEKLEME))
            # (4) ASIL SORU: olculen sure esigi asti mi?
            if float(_sure) > _plt_esik:
                _plt_h.append('sure %ss > esik %.1fs (marj %.1fx; ag '
                              'bagimliligi geri gelmis olabilir)'
                              % (_sure, _plt_esik,
                                 _plt_esik / float(_sure)))
            # SECILI ESIK PLATO ICINDE MI — olculdu (M100): bu kontrol yokken
            # `ESIK` 0.65 yapildi ve kapi PASS verdi; ESIK taranan degerleri
            # degil yalniz metni etkiliyor, yani kapi KORDU. Asil soru:
            # secilen esik platonun icinde mi? Disindaysa hukum duyarli.
            if _ic != 'evet':
                _plt_h.append('secili esik %s plato DISINDA (plato_icinde=%s)'
                              % (_sec, _ic))
            if _deg != '0':
                _plt_h.append('sonuc_degisen=%s (esige duyarli)' % _deg)
            if _buyuk == 'DEGISKEN':
                _plt_h.append('plato(n>=%s) DEGISKEN' % _esikN)
            if _kucuk == _buyuk:
                _plt_h.append('plato kucuk/buyuk orneklemde AYNI (%s) — '
                              'daralma iddiasi kanitsiz' % _kucuk)
            if _zay != 'var':
                _plt_h.append('ZAYIF uyari yok (n<%s)' % _zN)
            # Esik GORUNUR olmali: "sure=1.7s" tek basina anlamsiz — hangi
            # esige gore? Esik artik hesap ediliyor, o yuzden yazilir.
            _plt_oz = ('kucuk=%s · n>=%s=%s · sonuc_degisen=%s · zayif=%s · '
                       'secili=%s·icinde=%s · n_max_veri=%s·monoton=%s · '
                       'sure=%ss·esik=%.1fs·marj=%.1fx'
                       % (_kucuk, _esikN, _buyuk, _deg, _zay, _sec, _ic,
                          _nveri, _mono, _sure, _plt_esik, _plt_marj))
    # GECICI DIZIN SIZINTISI (13 Kasim 2026, Z18b / B-#5) -------------------
    # NEDEN (olculdu, EK 88 OLCULMEYEN #5 + M106): `--plato-tarama` her kosuda
    # `tempfile.mkdtemp()` aciyor ve hic silmiyordu; TMPDIR'de 4846 tmp dizini
    # birikmisti. `try/finally` + `rmtree` eklendi. Ama "temizlik var" demek
    # yetmez: OLCEN bir sey olmali. M106 mutasyonu: finally'daki rmtree
    # kaldirildi -> 1 dizin kaldi; duzeltmeyle 0. Kapi artik `plato_*` onekli
    # dizin sayisini kosturan SONRA sayar ve 0 ister.
    import glob as _plt_gl
    import tempfile as _plt_tf
    _plt_siz = len(_plt_gl.glob(os.path.join(_plt_tf.gettempdir(), 'plato_*')))
    _plt_n = len([x for x in _plt_r.stdout.splitlines()
                  if x[:3].strip().isdigit()])
    if _plt_n < 3:
        _plt_h.append('taranan n=%d (<3)' % _plt_n)
    if _plt_siz:
        _plt_h.append('gecici dizin sizintisi: %d adet plato_*' % _plt_siz)
    _plt_ok = not _plt_h
    _plt = 'n=%d · tmp-sizinti=%d · %s' % (_plt_n, _plt_siz, _plt_oz)
    if _plt_h:
        _plt += ' · HATA: ' + ' | '.join(_plt_h)
except Exception as _plt_e:
    _plt_ok = False
    _plt = 'CALISTIRILAMADI: %s' % _plt_e

k('C15l', 'PLATO orneklem buyuklugune gore taranir (n=3..N, snapshot-zorunlu)',
  _plt_ok, _plt)

# --- C15m: UC AYET LISTESI AYRISAMAZ (14 Kasim 2026, Z20) -------------------
# NEDEN (olculdu, Z20a): orneklem 12 -> 16 yapildi. `snapshot_yenile.py` ve
# `meal_farki.py` AYNI ayetleri AYRI listelerde tutuyor. `meal_farki.py`'yi
# guncellemeyi UNUTTUM; C15k "ayet=12/12" dedi ve yakaladi — yani 4 yeni ayet
# meal farki olcumune HIC girmiyordu. Ama o yakalama SANSA bagliydi: C15k
# kendi listesini dogruluyor, otekinden haberi yok. Bu kapi ayrismayi
# DOGRUDAN denetler, dolayli degil.
# KAPI UC SEY ISTER:
#   (1) snapshot_yenile.AYETLER == meal_farki.AYETLER (SIRALI) — sira ayrica
#       onemli: plato taramasi SKILL.md sirasini kullanir, eski onek korunmali.
#   (2) SKILL.md'de ozeti olan ayetler KUMESI == bu liste (ozetsiz ayet
#       olculemez; fazla ozet ise snapshot'siz kalir)
#   (3) liste BOS olamaz — bos==bos "ayrisma yok" demek olurdu (fail-closed).
try:
    import importlib.util as _drift_ilu

    def _drift_yukle(_drift_ad, _drift_yol):
        _drift_sp = _drift_ilu.spec_from_file_location(_drift_ad, _drift_yol)
        _drift_m = _drift_ilu.module_from_spec(_drift_sp)
        _drift_sp.loader.exec_module(_drift_m)
        return _drift_m

    _drift_h = []
    _drift_sy = _drift_yukle('_drift_sy', os.path.join(_BURASI, 'snapshot_yenile.py'))
    _drift_mf = _drift_yukle('_drift_mf', os.path.join(_BURASI, 'meal_farki.py'))
    _drift_aok = _drift_yukle('_drift_aok', os.path.join(_BURASI, 'ayet_ozet_kontrol.py'))
    _drift_a = _drift_sy.AYETLER
    _drift_b = _drift_mf.AYETLER
    with open(os.path.join(os.path.dirname(_BURASI), 'SKILL.md'),
              encoding='utf-8') as _drift_f:
        _drift_c = _drift_aok.ayetler(_drift_f.read())
    # TEK KAYNAK (14 Kasim 2026, Z21c / C-#2) --------------------------------
    # NEDEN: iki liste tek kaynaga tasindi (`scripts/ayetler.py`). O zaman
    # "esitlik" iddiasi TOTOLOJI olur — ayni nesneyi karsilastirmak bilgi
    # uretmez. Gizlemek yerine iddiayi degistiriyoruz: iki betikte `AYETLER`
    # ATAMASI OLMAMALI (yalniz import). Aksi halde biri yerel liste tanimlar
    # ve ayrisma SESSIZCE geri gelir.
    import ast as _drift_ast
    for _drift_ad, _drift_yol in (
            ('snapshot_yenile.py', os.path.join(_BURASI, 'snapshot_yenile.py')),
            ('meal_farki.py', os.path.join(_BURASI, 'meal_farki.py'))):
        with open(_drift_yol, encoding='utf-8') as _drift_f:
            _drift_agac = _drift_ast.parse(_drift_f.read())
        for _drift_n in _drift_ast.walk(_drift_agac):
            if isinstance(_drift_n, _drift_ast.Assign):
                for _drift_t in _drift_n.targets:
                    if isinstance(_drift_t, _drift_ast.Name) and \
                            _drift_t.id == 'AYETLER':
                        _drift_h.append('%s YEREL AYETLER atamasi tasiyor '
                                        '(tek kaynak bozuldu)' % _drift_ad)
    if not _drift_a:
        _drift_h.append('ayetler.AYETLER BOS')
    elif _drift_a is not _drift_b:
        _drift_h.append('ayetler.AYETLER AYNI NESNE DEGIL: %r vs %r'
                        % (id(_drift_a), id(_drift_b)))
    if set(_drift_a) != set(_drift_c):
        _drift_h.append('SKILL.md kumesi FARKLI: eksik=%s fazla=%s'
                        % (sorted(set(_drift_a) - set(_drift_c)),
                           sorted(set(_drift_c) - set(_drift_a))))
    _drift_ok = not _drift_h
    _drift = 'n=%d · ayni_nesne=%s · SKILL=%d · %s' % (
        len(_drift_a), 'evet' if _drift_a is _drift_b else 'HAYIR', len(_drift_c),
        'ayni' if _drift_ok else ' | '.join(_drift_h))
except Exception as _drift_e:
    _drift_ok = False
    _drift = 'CALISTIRILAMADI: %s' % _drift_e

k('C15m', 'Ayet listesi TEK KAYNAK (ayetler.py) + SKILL.md kumesi ayni',
  _drift_ok, _drift)

# --- C15k: meal_farki OLCUMU her kosuda yapilir (13 Kasim 2026, Z16c) ------
# NEDEN (EK 81 OLCULMEYEN): `meal_farki.py` bir OLCUM uretiyordu ama KAPI
# DEGILDI — yani "12 ayet x 9 meal farki olculdu" iddiasi her kosuda
# dogrulanmiyordu. Bir kez olcmek, her kosuda olcmek degildir; aradan gecen
# surede veri/snapshot/ayet listesi degisebilir.
#
# KAPIYA BAGLAMADAN ONCEKI ENGEL (olculdu): betik AGA CIKIYORDU. Ag kapaliyken
# `OLCULEMEDI (meal sayisi 0)` verip **rc=1** donuyordu; yani kapi her agsiz
# kosuda KIRMIZI olurdu. (NOT: ilk olcumumde `| tail` sonrasi `$?` okumus ve
# rc=0 sanmistim — tail'in kodu. Dogru olcum ayri satirda: rc=1.)
#
# DUZELTME: `meal_farki.py` once CANLI dener, olmazsa `scripts/tests/snapshot/`
# altindaki **sha ile sabitlenmis** snapshot'i okur; `--snapshot` ile aga HIC
# cikmaz. Hangi kaynagi kullandigini `KAYNAK:` satirinda SOYLER (sessiz dusme
# yok).
#
# KAPI UC SEY ISTER:
#   (1) `--snapshot` kosar ve rc=0 · ayet sayisi kodda yazandan (AYETLER) farkli
#       olamaz — "bazi ayetler olculdu" yeterli degil
#   (2) AYETLER x EDITIONLAR dosyalarinin HEPSI snapshot'ta var — eksik dosya
#       sessizce "olculmedi" demek olurdu
#   (3) OLCUMUN KENDISI ayirt edici: var olmayan ayet (`99:99`) rc!=0 vermeli.
#       Bu olmadan kosucu her ciktida rc=0 gorebilir.
#   (4) [Z17a, kalem #4] Dosya VAR olmasi YETMEZ — ICERIK de dogru olmali:
#       `snapshot_yenile.py --dogrula` (SNAPSHOT.sha256 manifesti) rc=0.
#       OLCULDU (M96): icerik degistirildi, dosya sayisi ayni kaldi ->
#       eski C15k PASS ("eksik=0"), --dogrula rc=1. Yani kordu.
try:
    import ast as _ast3
    import subprocess as _sp3
    _kok3 = os.path.dirname(_BURASI)
    _mf3 = os.path.join(_BURASI, 'meal_farki.py')
    # AYETLER artik `scripts/ayetler.py`de (14 Kasim 2026, Z21c / C-#2).
    # Eskiden `meal_farki.py` icindeki ATAMA okunuyordu; tek kaynaga tasininca
    # orada atama kalmadi ve bu kapi `ayet=16/0` verdi (olculdu). Simdi
    # AYETLER tek kaynaktan, EDITIONLAR meal_farki.py'den okunur.
    _ayet3 = []
    for _d3 in _ast3.walk(_ast3.parse(
            open(os.path.join(_BURASI, 'ayetler.py'), encoding='utf-8').read())):
        if isinstance(_d3, _ast3.Assign) and getattr(_d3.targets[0], 'id', '') \
                == 'AYETLER':
            _ayet3 = [x.value for x in _d3.value.elts
                      if isinstance(x, _ast3.Constant)]
    _ed3 = []
    for _d3 in _ast3.walk(_ast3.parse(open(_mf3, encoding='utf-8').read())):
        if isinstance(_d3, _ast3.Assign) and getattr(_d3.targets[0], 'id', '') \
                == 'EDITIONLAR':
            _ed3 = [x.value for x in _d3.value.elts
                    if isinstance(x, _ast3.Constant)]
    _bekle3 = len(_ayet3) * len(_ed3)

    def _mf_kos3(_ek):
        _mfk_arg = [sys.executable, _mf3, '--snapshot']
        if _ek:
            _mfk_arg.append(_ek)
        return _sp3.run(_mfk_arg, capture_output=True, text=True, timeout=300,
                        cwd=_kok3)

    _mfk_r1 = _mf_kos3(None)
    _mfk_m = re.search(r'SONUC: (\d+)/(\d+) ayet olculdu', _mfk_r1.stdout)
    _mfk_n = int(_mfk_m.group(1)) if _mfk_m else -1
    _mfk_d = int(_mfk_m.group(2)) if _mfk_m else -1
    _mfk_kay = 'KAYNAK: snapshot' in _mfk_r1.stdout
    _mfk_eksik = [('%s__%s' % (a.replace(':', '-'), e))
               for a in _ayet3 for e in _ed3
               if not os.path.exists(os.path.join(
                   _BURASI, 'tests', 'snapshot',
                   'ayet_%s__%s.json' % (a.replace(':', '-'), e)))]
    _mfk_r2 = _mf_kos3('99:99')
    _mfk_oz = 'AYIRT_ETTI' if _mfk_r2.returncode != 0 else 'KOR (olmayan ayet rc=0)'
    # --- ICERIK DENETIMI (13 Kasim 2026, Z17a / kalem #4) -------------------
    # NEDEN (olculdu, M96): yukaridaki `_mfk_eksik` yalniz dosyanin VARLIGINA
    # bakiyor. `ayet_4-58__tr.diyanet.json` ICERIGI degistirildi (dosya var,
    # sha bozuk):
    #     C15k PASS "eksik=0"        <-- KOR
    #     snapshot_yenile.py --dogrula rc=1
    # Yani "dosya var" ile "veri dogru" ayni sey degil — Z16a'nin (bos kume)
    # veri tarafindaki kardesi. Artik sha manifesti de denetleniyor.
    _mfk_dg = _sp3.run([sys.executable,
                        os.path.join(_BURASI, 'snapshot_yenile.py'),
                        '--dogrula'], capture_output=True, text=True,
                       timeout=300, cwd=_kok3)
    _mfk_sha_ok = _mfk_dg.returncode == 0
    _mfk_satir = ''
    for _mfk_l in _mfk_dg.stdout.splitlines():
        if _mfk_l.startswith('SONUC: '):
            _mfk_satir = _mfk_l.strip()
    _mfk_h = []
    if _mfk_r1.returncode != 0:
        _mfk_h.append('rc=%d' % _mfk_r1.returncode)
    if _mfk_n != len(_ayet3) or _mfk_d != len(_ayet3):
        _mfk_h.append('ayet %s/%s (kodda %d)' % (_mfk_n, _mfk_d, len(_ayet3)))
    if not _mfk_kay:
        _mfk_h.append('KAYNAK satiri yok')
    if _mfk_eksik:
        _mfk_h.append('eksik snapshot: %d [%s]'
                   % (len(_mfk_eksik), ', '.join(_mfk_eksik[:3])))
    if _mfk_oz != 'AYIRT_ETTI':
        _mfk_h.append(_mfk_oz)
    if not _mfk_sha_ok:
        _mfk_h.append('snapshot bozuk: rc=%d %s'
                      % (_mfk_dg.returncode, _mfk_satir[:90]))
    # --- DAL KORUMASI OZ-TESTI (14 Kasim 2026, Z21b / C-#5) -----------------
    # NEDEN (olculdu): `main()` icinde YALNIZ `yenile()` try icindeydi.
    # Manifest `chmod 000` yapildi -> `--dogrula` rc=1 ama stdout BOS ve
    # stderr `Traceback ... PermissionError`. Yani betik cokuyor, kullanici
    # tanidik "HATA:" satiri gormuyor; `rc` de "olcum basarisiz" ile "cokdu"
    # ayrimini tasimiyordu. Duzeltme: her dal korumali + rc=2.
    # Bu oz-test o duzeltmenin KALICI kanitidir: manifest geri yuklenir
    # (try/finally + sha), aga CIKMAZ, `yenile()` kosmaz (yan etkisi var).
    _mfk_dal = _sp3.run([sys.executable,
                         os.path.join(_BURASI, 'snapshot_yenile.py'),
                         '--oz-test'], capture_output=True, text=True,
                        timeout=300, cwd=_kok3)
    _mfk_dal_ok = (_mfk_dal.returncode == 0
                   and 'OZ-TEST: 2 dal korumali' in _mfk_dal.stdout)
    if not _mfk_dal_ok:
        _mfk_h.append('dal korumasi oz-testi BASARISIZ: rc=%d %s'
                      % (_mfk_dal.returncode,
                         (_mfk_dal.stdout + _mfk_dal.stderr).strip()[:90]))
    _c15k_ok = not _mfk_h
    _c15k = ('ayet=%s/%s · meal=%d · eksik=%d · sha=%s · '
             'kaynak=%s · oz-test: %s · dal=%s'
             % (_mfk_n, len(_ayet3), len(_ed3), len(_mfk_eksik),
                'DOGRU' if _mfk_sha_ok else 'BOZUK',
                'snapshot' if _mfk_kay else 'YOK', _mfk_oz,
                'korumali' if _mfk_dal_ok else 'BOZUK'))
    if _mfk_h:
        _c15k += ' · HATA: ' + ' | '.join(_mfk_h)
except Exception as _e3:
    _c15k_ok = False
    _c15k = 'CALISTIRILAMADI: %s' % _e3

k('C15k', 'meal_farki olcumu her kosuda yapilir (snapshot tabanli, agsiz)',
  _c15k_ok, _c15k)

k('C15j', 'her subprocess run() TIMEOUT tasir (asili kalma = sessiz fail-OPEN)',
  _tp_oz == 'AYIRT_ETTI' and not _tp_kotu and _tp_sablon_ihlal == 0,
  'betik=%d · timeout-suz/kuccuk=%d (esik>%ds)%s · sablon-ihlal=%d · '
  'oz-test: %s'
  % (_tp_taranan, len(_tp_kotu), _TP_ASGARI,
     (' [' + ', '.join(_tp_kotu[:4]) + ']') if _tp_kotu else '',
     _tp_sablon_ihlal, _tp_oz))

# --- C15e: "mutasyonu olmayan kapi, kapi degildir" sayaci (9 Kasim 2026) ----
# NEDEN: ilke SKILL.md'de var ama 81 kapinin KACINDA kanit oldugu HIC
# SAYILMADI. Olculmemis ilke, ilke degildir.
#
# ILK OLCUM (9 Kasim 2026): 81 kapi · 81 kanitli · 0 kanitsiz.
# Ama bu sonuca ancak SAYACIN KENDISI UC KEZ KOR CIKTIKTAN SONRA ulasildi:
#   (1) kimlik deseni `C14f/g`, `C13z-a`, `C14za` bicimlerini gormuyordu -> 78
#   (2) aralik yazimi `C13a-C13r` gorulmuyordu (18 kapi "kanitsiz" sanildi)
#   (3) tablo kaniti (`| 0 | **1** |`, `2/2`, `C14f/g`) gorulmuyordu -> 5 kapi
# Her uc korluk OLCULDU ve kapatildi. Sayac kendi kendine PASS veremez.
#
# SONSUZ OZYINELEME — OLCULDU VE KAPATILDI: ilk surum `mutasyon_tara.py`yi
# subprocess ile cagirip lint'i YENIDEN kosturdu -> lint -> C15e -> lint -> ...
# 900 s'te zaman asimi. Cozum: kimlik listesi `KAPI_KIMLIKLERI`den GELIR;
# `tara(KAPI_KIMLIKLERI)` subprocess acmaz.
#
# MUTASYON KANITI (bu kapi icin, 9 Kasim 2026 — HAM CIKTILAR):
#   M19  kanitsiz kapi C99 C15e'den ONCE eklendi: C15e FAIL rc=1 idi ama
#        KAPI_DEGIL'de C99 YOKTU -> sayac KONUM KORDU (olculdu, kusur bulundu)
#   M19b ayni mutant, C99 C15e'den SONRA: C15e FAIL rc=1
#        "kapi=83 · kanitli=81 · kanitsiz=2 · KAPI_DEGIL: C15e, C99"  <- yakalar
#   M20  C1c kaniti `**1**` -> `**0**`: C15e FAIL rc=1
#        "kanitli=80 · kanitsiz=2 · KAPI_DEGIL: C1c, C15e ·
#         defterde kanitli ama artik kanitsiz: C1c"
#   M22  defter silindi: C15e FAIL rc=1 "defter yok: ...mutasyon_defteri.json"
# Yani sayac UC FARKLI yoldan yanar; hicbiri "FAIL" tek basina degil,
# HANGI kapinin kanidinin eksildigini adiyla soyler.
_g15e = ''
_g15e_ok = False
try:
    import importlib.util as _ilu
    _mp = os.path.join(_BURASI, 'mutasyon_tara.py')
    if not os.path.exists(_mp):
        _g15e = 'CALISTIRILAMADI: scripts/mutasyon_tara.py yok'
    else:
        _spec = _ilu.spec_from_file_location('_mt', _mp)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        # [DUZELTME 2026-11-09] KONUM KORLUGU. Ilk surum yalniz
        # `KAPI_KIMLIKLERI`ni kullaniyordu; yani C15e'den SONRA eklenen bir
        # kapi listede yoktu. OLCULDU (M19): C99 C15e'den sonra eklendi ve
        # sayac onu GORMEDI (kapi=82 cikti, KAPI_DEGIL'de C99 yok) — yani
        # sayac yeni eklenen kanitsiz kapilari kaciriyordu.
        # COZUM: kimlikler HEM calisma-zamani listesinden HEM kaynak dosyanin
        # STATIK `k('<KIMLIK>'` cagrilarindan toplanir (satir konumu onemsiz).
        # Dinamik `k(_no, ...)` aileleri zaten KAPI_KIMLIKLERI'nde.
        _statik = re.findall(r"k\(\s*'([A-Z][0-9]{1,2}[a-z-]*)'",
                             open(os.path.abspath(__file__), encoding='utf-8').read())
        _hepsi = list(KAPI_KIMLIKLERI)
        for _s in _statik:
            if _s not in _hepsi:
                _hepsi.append(_s)
        if 'C15e' not in _hepsi:
            _hepsi.append('C15e')
        _ks, _aday = _mod.tara(_hepsi)
        _kanitsiz = [x for x in _ks if not _aday[x]]
        _sert_say = -1
        _h = []
        # [Z31b] `_h` PAYLASILAN bir toplayici: ona yeni `append` eklemek
        # 26 kapinin parmak izini birden degistirdi (OLCULDU: C12a, C12b,
        # C13z-a, C14o, ... C19 — tek kapinin isi 26 kapiyi kirdi). Bu yuzden
        # ratchet hatalari AYRI toplayiciya yazilir; `_h`ya hic dokunulmaz.
        _hz = []
        if _kanitsiz:
            _h.append('KAPI_DEGIL (mutasyon kaniti yok): %s'
                      % ', '.join(_kanitsiz))
        # Defter regresyonu: kanit SAYISI dusemez.
        _dp = os.path.join(_BURASI, 'tests', 'mutasyon_defteri.json')
        if not os.path.exists(_dp):
            _h.append('defter yok: scripts/tests/mutasyon_defteri.json '
                      '(uret: python3 scripts/mutasyon_tara.py --yaz)')
        else:
            with open(_dp, encoding='utf-8') as _f:
                _def = json.load(_f)
            _dk = set(_def.get('aday', {}))
            _kayip = sorted(_dk - set(x for x in _ks if _aday[x]))
            if _kayip:
                _h.append('defterde kanitli ama artik kanitsiz: %s'
                          % ', '.join(_kayip))
            if _def.get('toplam') != len(_ks):
                _h.append('defter bayat: defterde toplam=%s, canli=%d '
                          '(yenile: --yaz)'
                          % (_def.get('toplam'), len(_ks)))
            # [DUZELTME 2026-11-14, Z31b] SERT KANIT RATCHET.
            # NEDEN (olculdu): sayac "kanit var mi" diye bakiyordu; oysa
            # 95 kapinin 88'inin "kaniti" serbest duzyaziydi ('rc=1'
            # gecmesi). Yani sayac gercekte ANMA sayaciydi: mutasyonun
            # KOSULDUGUNU degil YAZILDIGINI gosteriyordu.
            # TOPTAN sertlestirme OLCULDU ve REDDEDILDI: SERT kume yalniz
            # 36/95 -> 59 kapi kanitsiz kalir, C15e kirilir.
            # Bu yuzden kural TABAN KORUMA: bugunku 36 kaybolamaz.
            # OLCULDU (M162 asagida).
            if 'sert_kimlikler' not in _def:
                _hz.append('defterde sert_kimlikler YOK '
                           '(uret: python3 scripts/mutasyon_tara.py --yaz)')
            else:
                _sert_def = set(_def.get('sert_kimlikler') or [])
                _sert_canli = set(_mod.sert_kimlikler(_ks, _aday))
                _sert_say = len(_sert_canli)
                _sert_kayip = sorted(_sert_def - _sert_canli)
                if _sert_kayip:
                    _hz.append('SERT kanit kayboldu (artik yalniz prose): %s'
                               % ', '.join(_sert_kayip))
        _g15e_ok = not _h and not _hz
        _g15e = ('kapi=%d · kanitli=%d · kanitsiz=%d · sert=%d/%d'
                 % (len(_ks), len(_ks) - len(_kanitsiz), len(_kanitsiz),
                    _sert_say, len(_ks)))
        if _h or _hz:
            _g15e += ' · HATA: ' + ' | '.join(_h + _hz)
except Exception as _e:
    _g15e = 'CALISTIRILAMADI: %s' % _e
k('C15e', 'mutasyonu olmayan kapi kapi degildir (kanit sayaci)',
  _g15e_ok, _g15e)

# --- C15f: kanitsiz iddia yasagi — SURUM.md guncel olcum blogu (9 Kasim 2026) --
# NEDEN: `SURUM.md` sayilarla dolu (14 612 sayi ifadesi) ama hicbiri makine
# tarafindan dogrulanmiyordu. "Kayit gercegin gerisinde kaliyor" labin EN PAHALI
# hatasiydi (AGENTS.md §4). Bu kapi, guncel durumu MAKINE OKUNUR tek bir bloga
# baglar ve canli olcumle karsilastirir.
#
# KAPSAM — DAR TUTULDU, ve nedeni:
#   * TUM sayilar dogrulanamaz: 14 612 ifade var; cogu TARIHSEL kayit (v1.3.2'de
#     41 kontrol vardi, bugun 82). Tarihsel kaydin eskimesi KUSUR DEGIL, kaydin
#     kendisidir. Hepsini "canli olcumle esit olmali" diye baglamak, tarihi
#     yalan soylemeye zorlamak olurdu.
#   * Bu yuzden kapsam: `<!-- C15f:basla --> ... <!-- C15f:bitti -->` blogu.
#     Blok YOKSA -> FAIL (kanitsiz iddia yasagi: guncel durum makine okunur
#     olmali). Blok VARSA -> her satir canli olcumle karsilastirilir.
#   * `atlas_envanter` OZTEST-TABAN.json'dan okunur; atlas_selftest KOSULMAZ
#     (88 s). Yani bu kapi "canli kosu gecti" DEMEZ — "envanter pinli" der.
#
# MUTASYON KANITI (9 Kasim 2026):
#   M23  skill_lint_kontrol: 82 -> 83   -> FAIL "skill_lint_kontrol: blok=83 canli=82"
#   M24  blok tamamen silindi            -> FAIL "C15f blogu yok"
#   M25  bilinmeyen anahtar eklendi      -> FAIL "bilinmeyen anahtar: foo_bar"
#   M26  SKILL_md_satir: 500 -> 499      -> FAIL "SKILL_md_satir: blok=499 canli=500"
_g15f = ''
_g15f_ok = False
try:
    _sp = os.path.join(_BURASI, os.pardir, 'SURUM.md')
    _h = []
    # Beklenen anahtarlar ve CANLI degerleri (hepsi ucuz olcum).
    # [DUZELTME 2026-11-09] KONUM KORLUGU — IKINCI KEZ AYNI HATA.
    # Ilk surum `sayac['kontrol'] + 1` kullaniyordu, yani KENDINDEN ONCE
    # calisan kapilari sayiyordu. OLCULDU (M27): C99 C15f'den SONRA eklendi ve
    # C15f PASS verdi (anahtar=5 · blok=5 · uyusan=5) — yani bayat blok
    # yakalanmadi. Sayac, blok ile gercek arasindaki farki GORMUYORDU.
    # COZUM: ayni yontem C15e'de de kullaniliyor — kimlikler HEM
    # KAPI_KIMLIKLERI'nden HEM kaynagin STATIK `k('<KIMLIK>'` cagrilarindan
    # toplanir. Satir konumu onemsizlesir.
    _statik_f = re.findall(r"k\(\s*'([A-Z][0-9]{1,2}[a-z-]*)'",
                           open(os.path.abspath(__file__), encoding='utf-8').read())
    _hepsi_f = list(KAPI_KIMLIKLERI)
    for _sf in _statik_f:
        if _sf not in _hepsi_f:
            _hepsi_f.append(_sf)
    if 'C15f' not in _hepsi_f:
        _hepsi_f.append('C15f')
    _bekle = {
        'skill_lint_kontrol': len(_hepsi_f),
        'skill_kapi_sayisi': len(_hepsi_f),
        'SKILL_md_satir': satir,
    }
    # kapi_taban_kimlik: taban dosyasindan (varsa)
    try:
        with open(os.path.join(_BURASI, 'tests', 'kapi_taban.json'),
                  encoding='utf-8') as _f:
            _bekle['kapi_taban_kimlik'] = len(json.load(_f)['kimlikler'])
    except Exception:
        pass
    # atlas_envanter: pinli envanter (selftest KOSULMAZ)
    try:
        with open(os.path.join(_BURASI, os.pardir, 'ATLAS_SABLONLAR', 'scripts',
                               'OZTEST-TABAN.json'), encoding='utf-8') as _f:
            _bekle['atlas_envanter'] = json.load(_f)['sayi']
    except Exception:
        _h.append('OZTEST-TABAN.json okunamadi')

    if not os.path.exists(_sp):
        _g15f = 'CALISTIRILAMADI: SURUM.md yok'
    else:
        _s = open(_sp, encoding='utf-8').read()
        _m = re.search(r'<!--\s*C15f:basla\s*-->(.*?)<!--\s*C15f:bitti\s*-->',
                       _s, re.S)
        if not _m:
            _h.append('C15f blogu yok (SURUM.md icinde '
                      '<!-- C15f:basla --> ... <!-- C15f:bitti -->)')
            _blok = {}
        else:
            _blok = {}
            for _ln in _m.group(1).splitlines():
                _ln = _ln.strip()
                if not _ln or _ln.startswith('#'):
                    continue
                if ':' not in _ln:
                    _h.append('bicimsiz satir: %r' % _ln)
                    continue
                _kk, _vv = _ln.split(':', 1)
                _kk, _vv = _kk.strip(), _vv.strip()
                if not re.fullmatch(r'\d+', _vv):
                    _h.append('%s degeri sayi degil: %r' % (_kk, _vv))
                    continue
                _blok[_kk] = int(_vv)
            for _kk in _blok:
                if _kk not in _bekle:
                    _h.append('bilinmeyen anahtar: %s' % _kk)
            for _kk, _canli in _bekle.items():
                if _kk not in _blok:
                    _h.append('eksik anahtar: %s (canli=%s)' % (_kk, _canli))
                elif _blok[_kk] != _canli:
                    _h.append('%s: blok=%s canli=%s'
                              % (_kk, _blok[_kk], _canli))
        _g15f_ok = not _h
        _g15f = ('anahtar=%d · blok=%d · uyusan=%d'
                 % (len(_bekle), len(_blok),
                    sum(1 for _kk, _vv in _bekle.items() if _blok.get(_kk) == _vv)))
        if _h:
            _g15f += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g15f = 'CALISTIRILAMADI: %s' % _e
k('C15f', 'kanitsiz iddia yasagi (SURUM.md guncel olcum blogu)',
  _g15f_ok, _g15f)

# --- C15g: ARZ olcum blogu — sayilar elden degil JSON'dan gelir (9 Kasim 2026) -
# NEDEN: `docs/ARZ-*.md` belgeleri sayilarla dolu ve sayilar DOGRUYDU — ama ELLE
# yazilmisti. Elle yazilan sayi kayar; kaydiginda kimse fark etmez. Labin en
# pahali hatasi buydu ("kayit gercegin gerisinde kaliyor"). Cozum: her ARZ
# belgesinde makine uretimi `<!-- ARZ_OLCUM:basla -->` blogu; degerler
# `MADDE_KAPANIS.json` + `KAYNAK_OLCUM.json`dan gelir.
#
# KAPSAM: `docs/ARZ-*.md` (varsa). Blok yoksa FAIL; deger uyusmazsa FAIL;
# bilinmeyen anahtar FAIL. `scripts/arz_uret.py <dosya>` blogu yeniler.
#
# OZYINELEME KORUMASI: bu kapi `skill_lint.py`yi CAGRMAZ; yalniz JSON okur.
#
# MUTASYON KANITI (9 Kasim 2026):
#   M28 madde_sayisi 7 -> 8        -> FAIL "madde_sayisi: blok=8 canli=7"
#   M29 blok silindi               -> FAIL "ARZ_OLCUM blogu yok"
#   M30 kaynak_acilan 11 -> 10     -> FAIL "kaynak_acilan: blok=10 canli=11"
#   M31 bilinmeyen anahtar         -> FAIL "bilinmeyen anahtar: uydurma"
#
# AD DENETIMI (13 Kasim 2026, Z15) — SAYI TUTMAK ADI TUTMAK DEGILDIR:
#   M89 (duzeltme ONCESI)  JSON'da `49:6` -> `50:1`, sayi 11 KALDI
#                          -> C15g PASS rc=0  <-- KOR
#        Yani ARZ belgesi `49:6` diyor, JSON `50:1` diyor, kapi "uyusuyor"
#        diyordu. Kanit ile iddia arasindaki bag kopunca geriye yalniz sayi kalir.
#   M90 (duzeltme SONRASI) ayni mutasyon -> C15g FAIL rc=1
#        "ad=UYUSMUYOR(1) · HATA: ARZ-...: AYET adlari uyusmuyor (blok=49:6,...)"
#        geri -> PASS "ad=UYDU"; KAYNAK_OLCUM.json sha AYNI
#   M91 JSON'a 3 giris EKLENDI (11 -> 14) -> C15g FAIL rc=1
#        "ARZ-...=9/11 · HATA: kaynak_toplam blok=11 canli=14"
#        (yani "listeyi buyutelim" yolu SAYI tarafindan zaten kapaliydi)
#
# BOS KUME (13 Kasim 2026, Z16a) — "kanit yok" ile "kanit uyusuyor" ayni sey degil:
#   M92a (duzeltme ONCESI) ARZ ayet tablosunun bicimi bozuldu (`| N | `a:b` |`
#        -> `| N | a:b |`), desen BOS dondu -> C15g PASS rc=0 "ad=UYDU"
#        Eski kosul `if _arz_ayet and ...` idi: bos kumede KISA DEVRE, kontrol
#        hic calismadi. Bos == bos -> "uyusuyor". Fail-OPEN'in en sessiz bicimi.
#   M92b (duzeltme SONRASI) ayni mutasyon -> C15g FAIL rc=1
#        "ad=UYUSMUYOR(1) · HATA: ARZ-...: AYET DESENI BULUNAMADI (tablo bicimi
#         degismis olabilir) — olcum YAPILAMADI"
#        geri -> PASS "ad=UYDU"; ARZ + skill_lint sha AYNI
_g15g = ''
_g15g_ok = False
try:
    _ad = os.path.join(_BURASI, 'arz_uret.py')
    if not os.path.exists(_ad):
        _g15g = 'CALISTIRILAMADI: scripts/arz_uret.py yok'
    else:
        import importlib.util as _ilu3
        _sp3 = _ilu3.spec_from_file_location('_arzu', _ad)
        _m3 = _ilu3.module_from_spec(_sp3)
        _sp3.loader.exec_module(_m3)
        _canli = _m3.degerler()
        _dizin = os.path.join(_BURASI, os.pardir, 'docs')
        _arzlar = sorted(x for x in os.listdir(_dizin)
                         if x.startswith('ARZ-') and x.endswith('.md'))
        _h = []
        if not _arzlar:
            _h.append('docs/ARZ-*.md yok')
        _satir = []
        for _x in _arzlar:
            _t = open(os.path.join(_dizin, _x), encoding='utf-8').read()
            _b = _m3.ayristir(_t)
            if _b is None:
                _h.append('%s: ARZ_OLCUM blogu yok (uret: '
                          'python3 scripts/arz_uret.py docs/%s)' % (_x, _x))
                continue
            _uy = 0
            for _k, _v in _canli.items():
                if _k not in _b:
                    _h.append('%s: eksik anahtar %s (canli=%s)'
                              % (_x, _k, _v))
                elif _b[_k] != _v:
                    _h.append('%s: %s blok=%s canli=%s'
                              % (_x, _k, _b[_k], _v))
                else:
                    _uy += 1
            for _k in _b:
                if _k not in _canli:
                    _h.append('%s: bilinmeyen anahtar: %s' % (_x, _k))
            _satir.append('%s=%d/%d' % (_x, _uy, len(_canli)))
        # --- AD DENETIMI (13 Kasim 2026, Z15) ---------------------------
        # NEDEN (olculdu, M89): C15g yalniz SAYIYI karsilastiriyordu. JSON'da
        # `49:6` -> `50:1` yapildi (sayi 11 KALDI): C15g PASS verdi (rc=0).
        # Yani ARZ belgesi `49:6` diyor, JSON `50:1` diyor, kapi "uyusuyor"
        # diyordu. Sayi tutmak ADI tutmak degildir; kanit ile iddia arasindaki
        # bagi koparinca geriye yalniz sayi kalir.
        _ad_h = []
        _j_yol = os.path.join(_dizin, os.pardir, 'docs', 'KAYNAK_OLCUM.json')
        if not os.path.exists(_j_yol):
            _ad_h.append('KAYNAK_OLCUM.json yok')
        else:
            import json as _js3
            _jl = _js3.load(open(_j_yol, encoding='utf-8')).get('kaynaklar') or []
            _j_ayet = [x.get('anahtar') for x in _jl
                       if x.get('tur') != 'hadis' and x.get('anahtar')]
            _j_hadis = [x.get('ad') for x in _jl if x.get('tur') == 'hadis']
            # Turkce aksan -> ASCII (ARZ tablosu `Tirmizî`, JSON `Tirmizi`)
            def _sad3(_t):
                for _a, _b in (('î', 'i'), ('Î', 'i'), ('û', 'u'), ('Û', 'u'),
                               ('â', 'a'), ('Â', 'a'), ('ş', 's'), ('Ş', 's'),
                               ('ğ', 'g'), ('Ğ', 'g'), ('ü', 'u'), ('Ü', 'u'),
                               ('ö', 'o'), ('Ö', 'o'), ('ç', 'c'), ('Ç', 'c'),
                               ('ı', 'i'), ('İ', 'i')):
                    _t = _t.replace(_a, _b)
                return ' '.join(_t.split()).lower()
            for _x in _arzlar:
                _t = open(os.path.join(_dizin, _x), encoding='utf-8').read()
                _arz_ayet = re.findall(r'^\|\s*\d+\s*\|\s*`(\d+:\d+)`', _t, re.M)
                _arz_hadis = re.findall(r'^\|\s*\d+\s*\|\s*\*\*([^*\n]+?)\*\*\s*\|',
                                        _t, re.M)
                # [DUZELTME 13 Kasim 2026, Z16] BOS KUME SESSIZ ATLAMA (M92):
                # eski hal `if _arz_ayet and ...` idi — yani ARZ tablosunun
                # bicimi degisirse `_arz_ayet` BOS doner, kosul kisa devre olur
                # ve kapi PASS verir. Bos == bos. Bu, "kanit yok" ile "kanit
                # uyusuyor"u ayni saymak demektir: fail-OPEN'in en sessiz bicimi.
                # Artik bos kume FAIL: desen bulunamadi = olcum yapilamadi.
                if not _arz_ayet:
                    _ad_h.append('%s: AYET DESENI BULUNAMADI (tablo bicimi '
                                 'degismis olabilir) — olcum YAPILAMADI' % _x)
                elif [_sad3(x) for x in _arz_ayet] != \
                        [_sad3(x or '') for x in _j_ayet]:
                    _ad_h.append('%s: AYET adlari uyusmuyor (blok=%s · json=%s)'
                                 % (_x, ','.join(_arz_ayet), ','.join(
                                     x or '?' for x in _j_ayet)))
                # ayni sinif: hadis deseni de sessizce bos kalabilir
                if not _arz_hadis:
                    _ad_h.append('%s: HADIS DESENI BULUNAMADI — olcum '
                                 'YAPILAMADI' % _x)
                elif sorted(_sad3(x) for x in _arz_hadis) != \
                        sorted(_sad3(x or '') for x in _j_hadis):
                    _ad_h.append('%s: HADIS adlari uyusmuyor (blok=%s · json=%s)'
                                 % (_x, ','.join(_arz_hadis), ','.join(
                                     x or '?' for x in _j_hadis)))
        # --- _sad3 AYIRT EDICI MI (13 Kasim 2026, Z17e / kalem #9) ----------
        # NEDEN (EK 84 OLCULMEYEN): "_sad3 agresif: Isa/Isa ayni sayilir;
        # yanlis eslesme riski olculmedi." Normallestirme, FARKI gizlerse
        # kapi kor olur: "Buhari 52" ile "Buhari 1" ayni sayilirsa ad denetimi
        # hicbir sey denetlemez. Bu oz-test, normalizasyonun AYIRT ETTIGINI
        # olcer: her gercek ad icin son hanesi degistirilmis varyant FARKLI
        # olmali. Rakam/noktalama silen bir normalizasyon bu testte duser.
        _ad_oz_h = []
        try:
            _ad_denek = list(_j_hadis) + list(_j_ayet)
            for _ad_x in _ad_denek:
                _ad_x = _ad_x or ''
                _deg = None
                for _i in range(len(_ad_x) - 1, -1, -1):
                    if _ad_x[_i].isdigit():
                        _deg = _ad_x[:_i] + ('0' if _ad_x[_i] != '0' else '1') \
                            + _ad_x[_i + 1:]
                        break
                if _deg is None:
                    continue          # rakam yok -> bu denek uygun degil
                if _sad3(_ad_x) == _sad3(_deg):
                    _ad_oz_h.append('%s ~ %s AYNI' % (_ad_x, _deg))
            # --- HARF DENEGI: IKI YONLU SPESIFIKASYON (Z18c / B-#6) ------
            # NEDEN (EK 88 OLCULMEYEN #6): "`_sad3` oz-testi YALNIZ rakam
            # farkini deniyor. Harf farki (or. `Salih` ~ `Salah`) icin ayirt
            # edicilik olculmedi." Bu gercek bir korluk: unlu SILEN bir
            # normallestirme rakam testini GECER (rakamlar yerinde durur) ama
            # `Salih` ile `Salah` ayni olur.
            #
            # [DUZELTME 13 Kasim 2026, Z18c] ILK DENEMEM KUSURLUYDU ve kendim
            # yakaladim: "harf degistir, _sad3 FARKLI olmali" diye yazmistim ama
            # dongude `if _sad3(_v) == _sade: continue` vardi — yani FARKIN
            # OLUSTUGU durumlari atliyor, sonra "fark var mi" diye soruyordum.
            # Totoloji: iddia hic ateslenemezdi (`harf-denek=44` yaziyor ama
            # hicbir sey denetlemiyordu). Ders: oz-testin kendisi de iddiadir.
            #
            # DOGRU OLCUM — iki yonlu, ILAN EDILMIS ciftlerle:
            #   ESITLENMELI (diyakritik/translit — TASARIM): 5 cift
            #   FARKLI KALMALI (gercek harf farki): 5 cift
            # Tek yon yetmez: unlu silen normallestirme FARKLI yarisini dusurur,
            # hicbir sey yapmayan (identity) normallestirme ESITLENMELI yarisini
            # dusurur. Iki yon birlikte normalizasyonu KISITLAR.
            _ad_esit = [('Buhârî', 'Buhari'), ('Müslim', 'Muslim'),
                        ('Şûrâ', 'Şura'), ('Tirmizî', 'Tirmizi'),
                        ('İsrâ', 'Isra')]
            _ad_fark = [('Salih', 'Salah'), ('Buhari', 'Buhara'),
                        ('Nesai', 'Nesae'), ('Tirmizi', 'Tirmizu'),
                        ('Darimi', 'Daremi')]
            _ad_harf = 0
            for _a, _b in _ad_esit:
                _ad_harf += 1
                if _sad3(_a) != _sad3(_b):
                    _ad_oz_h.append('ESITLENMELI: %s ~ %s FARKLI' % (_a, _b))
            for _a, _b in _ad_fark:
                _ad_harf += 1
                if _sad3(_a) == _sad3(_b):
                    _ad_oz_h.append('AYRI KALMALI: %s ~ %s AYNI' % (_a, _b))
            _ad_oz = 'AYIRT_ETTI' if not _ad_oz_h else \
                'KOR (%d)' % len(_ad_oz_h)
        except Exception as _e_adoz:
            _ad_oz = 'CALISTIRILAMADI: %s' % _e_adoz
            _ad_oz_h = [_ad_oz]
        if _ad_oz_h:
            _h.extend(_ad_oz_h[:3])
        _h.extend(_ad_h)
        _g15g_ok = not _h
        _g15g = ('arz=%d · %s · anahtar=%d · ad=%s · ad-oz-test: %s · '
                 'harf-denek=%d'
                 % (len(_arzlar), ' '.join(_satir), len(_canli),
                    'UYDU' if not _ad_h else 'UYUSMUYOR(%d)' % len(_ad_h),
                    _ad_oz, _ad_harf))
        if _h:
            _g15g += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g15g = 'CALISTIRILAMADI: %s' % _e
k('C15g', 'ARZ olcum blogu JSON kaynagiyla uyusur (elle sayi yok)',
  _g15g_ok, _g15g)

# --- C15h: lab_full tek giris + fail-closed semantigi bozulmadi (10 Kasim 2026) -
# NEDEN: `lab_full.py` kapanis protokolunun TEK GIRISI oldu. Ama tek giris
# olmasi yetmez: fail-OPEN bir giris, hic giris olmamasindan KOTUDUR (yesil
# yanar, kimse bakmaz). Bu kapi uc seyi kilitler:
#   (1) 9 kalem duruyor ve kimlikleri K1..K9 — kalem SESSIZCE silinemez
#   (2) K7 (git status --porcelain) BOS_OLMALI listesinde — kirli agac FAIL
#   (3) atlanan kalem varsa `KOSULLU`; kodda `PASS` fail-open yolu yok
#   (4) SKILL.md bu otomasyona SAHIP (lab_full.py referansi duruyor)
#
# OZYINELEME KORUMASI: bu kapi `lab_full.py`yi SUBPROCESS ILE CAGRMAZ.
# Cagirsa: lint -> C15h -> lab_full -> K1 -> lint -> ... 900 s timeout (olculdu
# deseni `C15e`de yasandi). Bu yuzden AST ile STATIK okunur, kosulmaz.
#
# MUTASYON KANITI (10 Kasim 2026):
#   M36 KALEMLER'den K5 silindi      -> FAIL "kalem=8 (beklenen 9)"
#   M37 BOS_OLMALI'dan K7 cikarildi  -> FAIL "K7 BOS_OLMALI'da degil"
#   M38 'KOSULLU' -> 'PASS' (fail-open) -> FAIL "fail-open: atlanan kalem varken PASS"
#   M39 SKILL.md'den lab_full referansi silindi -> FAIL "SKILL.md lab_full'a sahip degil"
_g15h = ''
_g15h_ok = False
try:
    import ast as _ast
    _p = os.path.join(_BURASI, 'lab_full.py')
    _h = []
    _say = []
    if not os.path.exists(_p):
        _h.append('scripts/lab_full.py yok')
    else:
        _kaynak = open(_p, encoding='utf-8').read()
        _agac = _ast.parse(_kaynak)

        def _dizi(ad):
            """Modul duzeyinde `ad = [...]` listesinin elemanlarini dondurur."""
            for _n in _agac.body:
                if isinstance(_n, _ast.Assign):
                    for _t in _n.targets:
                        if isinstance(_t, _ast.Name) and _t.id == ad:
                            try:
                                return _ast.literal_eval(_n.value)
                            except Exception:
                                return None
            return None

        # KALEMLER literal_eval ILE OKUNAMAZ: elemanlarinda `sys.executable`
        # var (ast.Name). OLCULDU: literal_eval -> ValueError -> kapi
        # "statik okunamadi" dedi (dogru davranis: fail-closed). Cozum: Liste
        # dugumunu AST uzerinden yuru, her elemanin ILK alanini (kimlik
        # sabiti) ve alan sayisini oku; komut icerigini cozumlemeye calisma.
        _kal = None
        for _n in _agac.body:
            if isinstance(_n, _ast.Assign):
                for _t in _n.targets:
                    if isinstance(_t, _ast.Name) and _t.id == 'KALEMLER':
                        _kal = _n.value
        _bos = _dizi('BOS_OLMALI')
        if not isinstance(_kal, (_ast.List, _ast.Tuple)):
            _h.append('KALEMLER listesi statik okunamadi')
        else:
            _kim = []
            for _e in _kal.elts:
                if not isinstance(_e, (_ast.Tuple, _ast.List)):
                    _h.append('kalem dugumu tuple degil: %s'
                              % type(_e).__name__)
                    break
                if len(_e.elts) != 4:
                    _h.append('kalem %d alanli (beklenen 4)'
                              % len(_e.elts))
                    break
                _ilk = _e.elts[0]
                if not (isinstance(_ilk, _ast.Constant)
                        and isinstance(_ilk.value, str)):
                    _h.append('kalem kimligi sabit string degil')
                    break
                _kim.append(_ilk.value)
            _say.append('kalem=%d' % len(_kim))
            if len(_kim) != 9:
                _h.append('kalem=%d (beklenen 9)' % len(_kim))
            _bek = ['K%d' % _i for _i in range(1, 10)]
            if sorted(_kim) != _bek:
                _h.append('kimlikler beklenenden farkli: %s' % (_kim,))
        if _bos is None:
            _h.append('BOS_OLMALI kumesi statik okunamadi')
        else:
            _say.append('bos_olmali=%d' % len(_bos))
            if 'K7' not in _bos:
                _h.append("K7 BOS_OLMALI'da degil (kirli agac FAIL etmez)")
        # fail-closed: 'KOSULLU' yolu duruyor mu, fail-open 'PASS' yolu var mi
        if 'KOSULLU' not in _kaynak:
            _h.append('fail-open: KOSULLU yolu yok (atlanan kalem PASS sayilir)')
        if "'--hizli'" not in _kaynak and '"--hizli"' not in _kaynak:
            _h.append('--hizli secenegi yok')
        # FAIL-OPEN DENETIMI: `elif atlanan:` dalinin govdesinde
        # `hukum = 'KOSULLU'` ATAMASI olmali.
        # OLCULDU (M38, 10 Kasim 2026): ilk surum yalniz `'KOSULLU' in metin`
        # ariyordu. `hukum = 'PASS'` yapildiginda dosyada `print('...KOSULLU...')`
        # satiri KALDIGI icin kapi PASS dedi — mutasyon YANMADI. Yani metinde
        # string aramak fail-open'i yakalamiyor; ATAMA denetlenir.
        _fa = [n for n in _ast.walk(_agac)
               if isinstance(n, _ast.If) and isinstance(n.test, _ast.Name)
               and n.test.id == 'atlanan']
        if not _fa:
            _h.append('"elif atlanan:" dali yok — fail-closed kirilmis')
        else:
            _atama = None
            _rc = None
            # DİKKAT: `_ast.walk(_fa[0])` YANLIS — orelse (else:) dalini da
            # gezer ve SON atamayi (`hukum = 'PASS'`) bulur; o zaman kapi her
            # zaman FAIL verir. OLCULDU: o haliyle C15h kendi kodunda FAIL dedi.
            # Yalniz `elif atlanan:` govdesi (body) gezilir.
            for _n in [x for _g in _fa[0].body for x in _ast.walk(_g)]:
                if isinstance(_n, _ast.Assign):
                    for _t in _n.targets:
                        if isinstance(_t, _ast.Name) and _t.id == 'hukum':
                            _atama = _n.value
                        if isinstance(_t, _ast.Name) and _t.id == 'rc':
                            _rc = _n.value
            if not (isinstance(_atama, _ast.Constant)
                    and _atama.value == 'KOSULLU'):
                _h.append("fail-open: 'elif atlanan:' dalinda "
                          "hukum = 'KOSULLU' atamasi yok")
            # CIKIS SOZLESMESI: docstring "0 = hepsi gecti · 1 = FAIL ·
            # 2 = kosulamadi" diyor. KOSULLU dalinda rc = 0 olmali; baska bir
            # deger sozlesmeyi bozar ve cagiran araci yaniltir.
            # OLCULDU (M38c, 10 Kasim 2026): `rc = 0` -> `rc = 3` mutasyonu
            # YANMADI; kapida rc denetimi yoktu.
            if not (isinstance(_rc, _ast.Constant) and _rc.value == 0):
                _h.append("fail-open: 'elif atlanan:' dalinda rc = 0 degil")
            if not _fa[0].test.id == 'atlanan':
                _h.append('atlanan dali bozuldu')

    # SKILL.md bu otomasyona sahip mi
    _kok = os.path.dirname(_BURASI)  # _BURASI = scripts/ ; kok = lab dizini
    _sk = os.path.join(_kok, 'SKILL.md')
    if os.path.exists(_sk):
        _s = open(_sk, encoding='utf-8').read()
        if 'scripts/lab_full.py' not in _s:
            _h.append("SKILL.md lab_full'a sahip degil (referans yok)")
        elif 'KOSULLU' not in _s:
            _h.append('SKILL.md lab_full KOSULLU semantigini yazmiyor')
    else:
        _h.append('SKILL.md yok')
    _g15h_ok = not _h
    _g15h = (' · '.join(_say) + ' · SKILL=%s'
             % ('var' if os.path.exists(_sk) else 'yok'))
    if _h:
        _g15h += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g15h = 'CALISTIRILAMADI: %s' % _e
k('C15h', 'tek giris lab_full fail-closed (9 kalem · K7 bos · KOSULLU yolu)',
  _g15h_ok, _g15h)

# --- C15i: K10 proje manzarasi — gorunurluk kalemi (10 Kasim 2026) -----------
# NEDEN: OLCULDU ki lab 6 makale projesi barindiriyor, 1'i YESIL, 2'si KIRMIZI,
# 3'u baslamamis — ve bu durum HICBIR kapanis ciktisinda gorunmuyordu. Yani
# yillar boyunca "lab temiz" denen rapor, icindeki iki kirmizi makaleyi
# gormeden yazilmis olabilir. Gorunmeyen durum, olmayan durum degildir; ama
# oyle sanilir. Bu kapi o sessizligi kilitler.
#
# KILITLEDIGI SEYLER:
#   (1) `projeler_tara` fonksiyonu duruyor (silinemez)
#   (2) siniflar korunuyor: BASLAMADI / YESIL / KIRMIZI (+Z46: INSAN_BEKLIYOR)
#   (3) siniflandirma DOGRU: faz0 yok -> BASLAMADI; rc!=0 -> KIRMIZI;
#       rc==0 + PASS-PENDING*/BLOCKED/HUMAN_REVIEW -> INSAN_BEKLIYOR; aksi YESIL
#       [DUZELTME 2026-11-15, Z46: eski (3) satiri "rc==0 -> YESIL" idi; olculdu
#        ki bu, kendi kapisi PASS-PENDING-ETHICS veren projeyi YESIL gosteriyor.
#        Eski satir silinmedi — I6.]
#   (4) GOVUNURLUK: proje manzarasi HER kosuda basilir (sessiz birakilamaz)
#   (5) HUKME GIRMEZ: `--proje-zorunlu` bayragi yoksa rc degismez
#   (6) `--proje-zorunlu` VARSA kirmizi -> FAIL (kullanici acikca isterse)
#   (7) `--json` ciktisinda `projeler` alani duruyor
#
# OZYINELEME KORUMASI: `lab_full.py` CAGRILMAZ; AST ile statik okunur.
# Cagirsa: lint -> C15i -> lab_full -> K1 -> lint -> ... (olculmus desen).
#
# MUTASYON KANITI (10 Kasim 2026):
#   M41 `projeler_tara` silindi          -> FAIL "K10 fonksiyonu yok"
#   M42 `--proje-zorunlu` silindi        -> FAIL "zorunlu kilma bayragi yok"
#   M43 `--json`dan `projeler` alani cikti -> FAIL "json'da projeler yok"
#   M44 gorunurluk basimi silindi        -> FAIL "proje manzarasi basilmiyor"
#   M45 KIRMIZI -> YESIL (rc!=0 dali)    -> FAIL "siniflandirma bozuk"
#
# SOZLESME DEGISTI (15 Kasim 2026, Z46) — OLCULDU:
#   `projeler_tara` bir projeyi YALNIZ `--full` donus koduna bakarak
#   sinifliyordu. `silat-makale`nin kendi kapisi `verdict=PASS-PENDING-ETHICS`
#   veriyor (DEC-035/036 OPEN) ve projenin kaydi bunu "istenen davranis, hata
#   degildir" diye yaziyor. Devir belgesi yazildigi ANDA rc=0 oldu -> proje
#   panoda YESIL yandi. Kendi kapisi "insan onayi bekliyor" derken yesil yanmak
#   SAHTE YESILDIR. Bu yuzden siniflandirma `durum_belirle()`ye tasindi ve
#   girdisi artik projenin KENDI hukmudur (`proje_hukmu` -> FINAL-GATE verdict).
#   M45 bu yuzden GECERSIZ: rc dali artik `durum_belirle()` icinde; yerine
#   M46/M47 yazildi (asagi). Eski satir silinmedi — tarih kaydi bozulmasin.
_g15i = ''
_g15i_ok = False
try:
    import ast as _ast
    _p = os.path.join(_BURASI, 'lab_full.py')
    _h = []
    _say = []
    if not os.path.exists(_p):
        _h.append('scripts/lab_full.py yok')
    else:
        _kaynak = open(_p, encoding='utf-8').read()
        _agac = _ast.parse(_kaynak)

        # (1) fonksiyon var mi
        _fonk = [n for n in _agac.body
                 if isinstance(n, _ast.FunctionDef) and n.name == 'projeler_tara']
        if not _fonk:
            _h.append('K10 fonksiyonu yok (projeler_tara)')
        else:
            _govde = _ast.dump(_fonk[0])
            # (2)+(3) siniflandirma
            for _sinif in ('BASLAMADI', 'YESIL', 'KIRMIZI'):
                if "'%s'" % _sinif not in _govde:
                    _h.append('sinif yok: %s' % _sinif)
            # faz0 -> BASLAMADI bagi
            if '00-FAZ-0-SCOPE-CONTRACT' not in _govde:
                _h.append('faz0 kontrolu yok -> baslamamis proje FAIL sayilir')
            # (3) SINIFLANDIRMA BAGI (Z46, 15 Kasim 2026). Eski desen
            # `'YESIL' if rc == 0 else 'KIRMIZI'` idi; rc tabanli bu desen
            # `PASS-PENDING*` hukmu veren projeyi YESIL gosteriyordu (SAHTE
            # YESIL). Yeni sozlesme UC parcali ve HER parca denetlenir:
            #   (a) `durum_belirle` ve `proje_hukmu` fonksiyonlari VAR,
            #   (b) `durum_belirle` bekleyen hukukleri AYRI sinifa atar
            #       (INSAN_BEKLIYOR + 'PASS-PENDING' oneki),
            #   (c) `projeler_tara` IKISINI DE CAGRIR — yani siniflandirma
            #       baypas edilemez, hüküm okunmadan sinif verilemez.
            _fonk_d = [n for n in _agac.body
                       if isinstance(n, _ast.FunctionDef)
                       and n.name == 'durum_belirle']
            _fonk_h = [n for n in _agac.body
                       if isinstance(n, _ast.FunctionDef)
                       and n.name == 'proje_hukmu']
            if not _fonk_d:
                _h.append('durum_belirle() yok — siniflandirma tek yerde degil')
            if not _fonk_h:
                _h.append('proje_hukmu() yok — projenin KENDI hukmu okunmuyor')
            if _fonk_d:
                _govde_d = _ast.dump(_fonk_d[0])
                for _s2 in ('INSAN_BEKLIYOR', 'KIRMIZI', 'YESIL'):
                    if "'%s'" % _s2 not in _govde_d:
                        _h.append('durum_belirle: sinif yok: %s' % _s2)
                if "'PASS-PENDING'" not in _govde_d:
                    _h.append('durum_belirle: bekleyen hukum oneki yok '
                              '(PASS-PENDING) — sahte yesil geri gelir')
            _cagri = set()
            for _n in _ast.walk(_fonk[0]):
                if isinstance(_n, _ast.Call) and isinstance(_n.func, _ast.Name):
                    _cagri.add(_n.func.id)
            for _gerek in ('durum_belirle', 'proje_hukmu'):
                if _gerek not in _cagri:
                    _h.append('projeler_tara %s() cagirmiyor — siniflandirma '
                              'baypas edilebilir' % _gerek)
            _say.append('projeler_tara=var')

        # (4) GORUNURLUK — `print(...)` CAGRISI olmali, YORUMDA gecmesi yetmez.
        # OLCULDU (M44, 10 Kasim 2026): ilk surum `'PROJE MANZARASI' in _kaynak`
        # ariyordu. Mutasyonda print satiri degistirildi ama YORUMDA ayni kelime
        # kaldigi icin kapi PASS dedi — yani KAPI YORUMU KODA TERCIH ETTI.
        # Cozum: AST'de `print(...)` cagrisinin argumanlarinda ayni metin aranir.
        # Yorumlar AST'ye hic girmez; boylece yorum kapıyı doyuremez.
        _basim = False
        for _n in _ast.walk(_agac):
            if not isinstance(_n, _ast.Call):
                continue
            _f = _n.func
            if not (isinstance(_f, _ast.Name) and _f.id == 'print'):
                continue
            _arg = ' '.join(
                x.value for x in _ast.walk(_n)
                if isinstance(x, _ast.Constant) and isinstance(x.value, str))
            if 'PROJE MANZARASI' in _arg:
                _basim = True
        if not _basim:
            _h.append('proje manzarasi print ile basilmiyor '
                      '(yorumda gecmesi sayilmaz)')
        else:
            _say.append('gorunurluk=var')

        # (5)+(6) zorunlu kilma bayragi
        if "'--proje-zorunlu'" not in _kaynak and '"--proje-zorunlu"' not in _kaynak:
            _h.append('zorunlu kilma bayragi yok (--proje-zorunlu)')
        else:
            # bayrak, kirmizi -> FAIL yapan dalin ICINDE kullanilmali
            _dal = [n for n in _ast.walk(_agac)
                    if isinstance(n, _ast.If)
                    and isinstance(n.test, _ast.BoolOp)]
            _zor = False
            for _n in _dal:
                _t = _ast.dump(_n.test)
                if '--proje-zorunlu' in _t:
                    _g = ' '.join(_ast.dump(x) for x in _n.body)
                    if 'FAIL' in _g:
                        _zor = True
            if not _zor:
                _h.append('--proje-zorunlu dali FAIL uretmiyor')
            else:
                _say.append('zorunlu=var')

        # (7) json alani
        if "'projeler': projeler" not in _kaynak:
            _h.append("json'da projeler alani yok (makine okunur degil)")
        else:
            _say.append('json=var')

    _g15i_ok = not _h
    _g15i = ' · '.join(_say)
    if _h:
        _g15i += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g15i = 'CALISTIRILAMADI: %s' % _e
k('C15i', 'K10 proje manzarasi: 4 sinif (INSAN_BEKLIYOR dahil) · kendi hukmu · gorunur · hukme girmez · zorunlu kilinabilir',
  _g15i_ok, _g15i)

# --- C15n: ozet iddiasi OLCULEN sinirla sinirli (C-#6) ----------------------
# NEDEN (olculdu, 14 Kasim 2026): `SKILL.md` "Turkce satirlar **serbest
# ozet**" diyordu. Bu cumle OLCULEBILIR BIR SINIR KOY MUYORDU, yani okuyan
# "anlam denetleniyor" sanabilirdi. Olculdu ki olcut ANLAMI OLCMUYOR:
#   iddia  : kapsam olcutu ozetin anlamini denetler
#   komut  : ayni kokleri koruyup anlami TERS ceviren sentetik ozet
#   cikti  : 4:58 icin kapsam=0.67 -> ESIK 0.50 -> **GECER**
#            ("emanetleri ehline vermeyin, adaletle hukmetmeyin" = meale TERS)
#   cikti  : ayni anlami BASKA kelimeyle veren ozet kapsam=0.25 -> **KALIR**
#   [DUZELTME 2026-11-14, Z26] Yukaridaki "16/16" sayilari OLCULMEMISTI:
#   koddaki ters probe `degil`i (5 harf) filtreye takip SESSIZCE dusuruyordu,
#   yani probe TABANLA AYNI seyi olcuyordu (M139). Kapi no-op probe'u 16/16
#   diye raporluyordu.
#   [DUZELTME 2026-11-14, Z27] Z26'nin duzeltmesi de YETMEDI: `yoktur`
#   hicbir mealde gecmedigi icin etkisi PAYDA BUYUMESIYDI. OLCULDU (M146):
#   ANLAMSIZ `zezeze` tokeni **16/16 AYNI hukumu** veriyor; 33:70'te (en kisa
#   ozet, N=2) taban 1.00 -> 0.33, yani 1/(N+1)=0.67 seyrelmesi. Yani
#   "olumsuzlanmis ozet geciyor" ifadesi olumsuzlamayi DEGIL seyrelmeyi
#   olcuyordu. Artik TERS ile NOTR KARSILASTIRILIR:
#     tes_hukum_fark > 0 -> olumsuzlama ayirt edilebiliyor (bugun 0)
#   Olculen: sira_farkli=0/16 · ters_hukum_fark=0/16 · ters_deger_fark=1/16
#            · en_kisa_ozet=2 · meal_hata=0
#   KANITLANABILIR iddia: kapsam bir KUME UYELIGI oranidir -> kelime SIRASINA
#   duyarsizdir (sira_farkli=0/16, matematiksel) ve olumsuzlama ile anlamsiz
#   token AYIRT EDILEMEZ (0/16). Yani olcut anlam boyutunu gormuyor.
# Yani olcut "ozet uydurma degil" olcumudur (kendi yorumu bunu soyluyordu) ama
# BELGEDEKI cumle bu siniri yazmiyordu. C-#6 tam olarak bu: iddia > olcum.
#
# IKINCI BULGU (olculdu, ayni gun): "olumsuzlamayi da yakalariz" DOGRU DEGIL.
# Turkce olumsuzlama deseni (`\b(degil|deyil|yok|asla|hic|hiç|olmaz|olamaz)\b`
# + `\w+(me|ma)[yzdn]\w*`) 16 ayette **8/16 UYUMSUZ** verdi
# (4:135, 49:11, 2:286, 42:38, 3:159, 33:70, 5:8, 24:22). Yani olumsuzlama
# eklemek sorunu KAPATMIYOR; bu yuzden o yol SECILMEDI (uydurma cozum olurdu).
#
# COZUM — iki parca, tek mekanizma: iddia = olcum.
#   (1) `ayet_ozet_kontrol.py --anlam-siniri` siniri OLCER (probe'lar yukarida).
#   (2) Bu kapi SKILL.md'deki iddiayi o olcumle KARSILASTIRIR:
#       - "anlami OLCMEZ" sinir ifadesi YOKSA FAIL (sinir yazilmali),
#       - "serbest ozet" / "birebir ceviri" gibi ANLAM iddiasi VARSA FAIL,
#       - belgedeki sayilar (`ters ozet A/B GECIYOR`, `farkli-kelime ozet A/B
#         KALIYOR`) canli olcumle AYNI DEGILSE FAIL (bayat sayi yasak).
# Yani ayet sayisi artarsa ve belge guncellenmezse kapi YANAR — sessiz bayatlama
# (C-#10'un ayni sinifi) burada da kapatilir.
_g15n = ''
_g15n_ok = False
try:
    _d15 = os.path.dirname(os.path.abspath(__file__))
    _env15 = dict(os.environ)
    _env15['SNAPSHOT_ONLY'] = '1'
    _r15 = __import__('subprocess').run(
        [sys.executable, os.path.join(_d15, 'ayet_ozet_kontrol.py'),
         YOL, '--anlam-siniri'],
        capture_output=True, text=True, timeout=90, env=_env15)
    _s15 = (_r15.stdout.strip().splitlines() or ['<bos>'])[-1]
    _h15 = []
    # [DUZELTME 2026-11-14, Z26] ALANLAR DEGISTI — eski probe NO-OP idi.
    # Olculdu (M139): `degil` 5 harf oldugu icin `icerik_kelimeleri` onu
    # SESSIZCE dusuruyordu; ters-probe kelime listesi tabanla BIREBIR AYNI
    # cikiyordu (16 ayetin 13'unde sonuc ayni, kalan 3'unde fark `kel[:5]`
    # kirpmasindan). Yani "ters ozet 16/16 GECIYOR" sayisi KANITSIZDI.
    # Artik probe'lar: (a) SIRA ters (kume uyeligi siradan bagimsiz -> ayni
    # oran beklenir), (b) TERS = listeye SAYILAN olumsuzlama tokeni eklenir.
    # [DUZELTME 2026-11-14, Z27] TERS probe'u ANLAMI olcmuyordu: `yoktur`
    # hicbir mealde gecmedigi icin etkisi payda buyumesidir. OLCULDU (M146):
    # ANLAMSIZ `zezeze` tokeni **16/16 AYNI hukumu** veriyor. Yani
    # "olumsuzlanmis ozet geciyor" ifadesi olumsuzlamayi degil 1/(N+1)
    # SEYRELMESINI olcer. Kapi artik TERS ile NOTR'u KARSILASTIRIR:
    #   ters_hukum_fark == 0  -> ayirt edilemiyor (bugunku durum)
    #   ters_hukum_fark  > 0  -> olumsuzlama ayirt edilebilir hale gelmis
    # [DUZELTME 2026-11-14, Z30] GERCEK Turkce olumsuz ozet probe'u eklendi.
    # Onceki probe'lar SENTETIKTI (token duzeyi); "gercek olumsuz cumle gecer mi"
    # OLCULMEMISTI. Fixture: 4 INSAN YAZIMI cumle (kokleri korur, anlami ters
    # cevirir). Olculen: gercek_gecen=3 · gercek_olculen=4.
    _m15 = re.search(r'ayet=(\d+) · olculen=(\d+) · sira_farkli=(\d+) · '
                     r'ters_gecen=(\d+) · ters_hukum_fark=(\d+) · '
                     r'ters_deger_fark=(\d+) · en_kisa_ozet=(\d+) · '
                     r'gercek_gecen=(\d+) · gercek_olculen=(\d+) · '
                     r'esik=([0-9.]+) · meal_hata=(\d+)',
                     _s15)
    if _r15.returncode != 0:
        _h15.append('betik rc=%d: %s'
                    % (_r15.returncode,
                       (_r15.stderr.strip().splitlines() or ['<bos>'])[0]))
    if not _m15:
        # [DUZELTME 2026-11-14, Z26 / M139] Bu dal TUM alanlari tanimlamali.
        # Olculdu: betik rc=2 ile coktugunde (self-check) `_n_sira` tanimsiz
        # kaliyordu -> NameError -> "CALISTIRILAMADI" cikiyor ve GERCEK SEBEP
        # (rc + stderr) mesajdan dusuyordu. Fail-closed yine saglaniyordu ama
        # teshis yanlisti; hata mesaji teshisi tasimali.
        _h15.append('SINIR satiri ayristirilamadi (alan adi degismis ya da '
                    'betik cikti vermeden oldu)')
        _n_ayet = _n_olc = _n_sira = _n_ters = 0
        _n_htar = _n_dtar = _n_kisa = 0
        _n_gc = _n_go = 0
        _n_hata = -1
    else:
        (_n_ayet, _n_olc, _n_sira, _n_ters, _n_htar, _n_dtar,
         _n_kisa, _n_gc, _n_go, _n_esik, _n_hata) = _m15.groups()
        _n_ayet = int(_n_ayet); _n_olc = int(_n_olc)
        _n_sira = int(_n_sira); _n_ters = int(_n_ters)
        _n_htar = int(_n_htar); _n_dtar = int(_n_dtar)
        _n_kisa = int(_n_kisa); _n_hata = int(_n_hata)
        _n_gc = int(_n_gc); _n_go = int(_n_go)
        if _n_hata != 0:
            _h15.append('meal_hata=%d (okunamayan meal var — olcum eksik)'
                        % _n_hata)
        if _n_olc != _n_ayet:
            _h15.append('olculen=%d / ayet=%d (bazi ayet olculemedi)'
                        % (_n_olc, _n_ayet))
        # (a) SIRA: kapsam bir KUME UYELIGI orani oldugu icin kelime sirasi
        # orani degistirmemeli. Degistiriyorsa olcut yapisal olarak degismis
        # ve belgedeki "SIRA-duyarsiz" siniri ARTIK YANLIS olur -> FAIL.
        if _n_sira != 0:
            _h15.append('sira_farkli=%d — olcut kelime SIRASINA duyarli hale '
                        'gelmis; belgedeki "sira-duyarsiz" siniri ARTIK '
                        'EKSIK, yeniden olc ve metni guncelle' % _n_sira)
        # (b) TERS vs NOTR: asil ayirt edicilik olcusu. Ikisi AYNI hukmu
        # veriyorsa olumsuzlama probe'u HICBIR SEY olcmuyor (seyrelme).
        # Bugun 0 -> belgedeki "olumsuzlama ayirt edilemez" siniri DOGRU.
        if _n_htar != 0:
            _h15.append('ters_hukum_fark=%d — olumsuzlama ARTIK ayirt '
                        'edilebiliyor; belgedeki "ayirt edilemez" siniri '
                        'ARTIK EKSIK, yeniden olc ve metni guncelle'
                        % _n_htar)
        if _n_ters > _n_olc:
            _h15.append('ters_gecen(%d) > olculen(%d) — sayac bozuk'
                        % (_n_ters, _n_olc))
        # SEYRELME: en kisa ozet 1 token eklenince ne kadar kirilgan?
        # N/(N+1) carpani. N<=2 -> 0.67, yani probe yapisal olarak kirilgan.
        if _n_kisa < 2:
            _h15.append('en_kisa_ozet=%d — olcum yapilamaz (icerik kelimesi '
                        'yok)' % _n_kisa)
        # GERCEK olumsuz ozet: 0 ise ya fixture bozuldu ya olcut anlami yakaliyor.
        if _n_go == 0:
            _h15.append('gercek_olculen=0 — gercek olumsuz fixture OLCULMEDI '
                        '(fixture silinmis ya da ayetler eslesmiyor)')
        elif _n_gc == 0:
            _h15.append('gercek_gecen=0 — GERCEK olumsuz ozet HIC gecmiyor; '
                        'olcut anlami yakaliyor olabilir, sinir metni '
                        'yeniden yazilmali')
    # BELGE TARAFI — iddia olcumle AYNI olmali.
    try:
        with open(YOL, encoding='utf-8') as _f15:
            _sk15 = _f15.read()
    except OSError as _e15:
        _sk15 = ''
        _h15.append('SKILL.md okunamadi: %s' % _e15)
    if 'anlami OLCMEZ' not in _sk15:
        _h15.append('sinir ifadesi YOK: "anlami OLCMEZ" (iddia sinirsiz '
                    'birakilamaz)')
    # YASAK IFADE — CUmLE DUZEYINDE. NEDEN (olculdu, kendi hatam): ilk yazim
    # duz `in` aramasiydi ve mesru bir INKARI yakaladi:
    #   "**Olculmeyen:** birebir ceviri — satirlar ... birebir iddia yok."
    # Bu cumle iddiayi REDDEDIYOR, kurmuyor. Duz arama bunu "ANLAM IDDIASI
    # geri gelmis" diye FAIL etti -> yanlis-KIRMIZI. Cozum: cumleye bol, bir
    # cumle YALNIZ (a) yasak ifadeyi icerip (b) inkari (yok/OLCMEZ/degil)
    # icermiyorsa iddia sayilir. Iki yon de olculur (M133/M134).
    # IKINCI DUZELTME (M135 kendi kapimi yakti, olculdu): "inkar cumlede
    # var mi" YETMIYOR. M135'te mesru cumle
    #   "**birebir ceviri** iddiasi YOK."
    # idi; eski desen `iddia yok` ariyordu ve "iddiasi YOK"u TANIMADI
    # (harf farki + buyuk harf) -> yanlis-KIRMIZI. Simdi:
    #   (a) inkar, YASAK IFADEYE YAKIN olmali (±60 karakter) — cumlenin
    #       baska yerindeki "yok" iddiayi affetmesin (kor nokta),
    #   (b) desen buyuk/kucuk harf DUYARSIZ ve "iddia*" gövdesini kapsar.
    # Ikisi de olculdu: M135 (mesru inkar -> PASS), M134 (iddia -> FAIL).
    # [DUZELTME 2026-11-14, Z28 / M151] YANLIS-GECIR KOR NOKTASI KAPATILDI.
    # ESKI HAL (olculdu): tek bir `_INKAR15` deseni ±60 karakter penceresinde
    # HERHANGI bir inkar ariyordu; `\bdegil\b`, `yoktur` ve `Olculmeyen`
    # desenin icindeydi. Sonuc: cumlede BASKA BIR SEYE ait bir "degil" yasak
    # ifadeyi affediyordu. Olculen yanlis-GECIR'ler:
    #   "satirlar **serbest ozet** kullanir; bu bir kisitlama degil."   -> GECIR
    #   "**serbest ozet** yaziyoruz. Olculmeyen: baska bir konu."       -> GECIR
    #   "**serbest ozet** yaziyoruz. Baska yerde yoktur ifadesi var."   -> GECIR
    # Yani kapi, kendi yasagi olan iddiayi geciriyordu — yanlis FAIL gurultudur,
    # yanlis PASS kapinin isini birakmasidir.
    #
    # YENI KURAL (iki eksen):
    #   (1) CUMLE SINIRI: inkar, yasak ifadeyle AYNI cumlede olmali
    #       ('.' ';' '!' '?' newline sinir). Cumlenin baska yerindeki inkar
    #       affetmez.
    #   (2) MESAFE, inkarin TURUNE gore:
    #         GUCLU  : `iddia* yok` · `OLCMEZ` · `Olculmeyen`  -> 60 karakter
    #                  (bunlar yazarin olcum-siniri beyanidir)
    #         ZAYIF  : `degil` · `yoktur`                      -> 25 karakter
    #                  (genel Turkce kelimeler; yasak ifadeye YAKIN olmali)
    # Olculen dogru siniflandirma:
    #   "**birebir ceviri** degil"                        -> GECIR (mesafe 1)
    #   "**birebir ceviri** … birebir iddia yok"          -> GECIR (mesafe ~20)
    #   "**serbest ozet** kullanir, bu kisitlama degil."  -> FAIL  (zayif, ~33)
    _INKAR15_GUCLU = re.compile(r'iddia\w*\s+yok|\bOLCMEZ\b|[OoÖö]l[çcC][üuU]lmeyen',
                                re.IGNORECASE)
    _INKAR15_ZAYIF = re.compile(r'\bdegil\b|yoktur', re.IGNORECASE)
    _INKAR15_MESAFE_GUCLU = 60
    _INKAR15_MESAFE_ZAYIF = 25
    _CUMLE15 = '. ; ! ? \n'.split()

    # NOT (Z28): yerel adlar `_z28*` onekiyle yazilir. NEDEN: `kapi_farki`
    # global tanim sozlugu uzerinden parmak izi uretir; `_bas`/`_son`/`_i`
    # gibi GENEL adlar baska kapilarin kosullarinda da geciyor ve bu
    # fonksiyonun govdesi ONLARIN parmak izine sizdi (olculdu: C14y/C15j/C19
    # parmak izi degisti, oysa kosullari degismemisti). Onek sizmayi keser.
    def _inkar15_var(_z28belge, _z28bas, _z28son):
        """Inkar, yasak ifadeyle AYNI cumlede ve MESAFE esigi icinde mi?"""
        _z28sol = max(0, _z28bas - _INKAR15_MESAFE_GUCLU)
        _z28sag = min(len(_z28belge), _z28son + _INKAR15_MESAFE_GUCLU)
        _z28i = _z28bas
        while _z28i > _z28sol and _z28belge[_z28i - 1] not in _CUMLE15:
            _z28i -= 1
        _z28sol = _z28i
        _z28j = _z28son
        while _z28j < _z28sag and _z28belge[_z28j] not in _CUMLE15:
            _z28j += 1
        _z28sag = _z28j
        if _INKAR15_GUCLU.search(_z28belge[_z28sol:_z28sag]):
            return True
        # ZAYIF inkar: yasak ifadeye 25 karakter MESAFEDE olmali (genel kelime).
        for _z28mz in _INKAR15_ZAYIF.finditer(
                _z28belge,
                max(0, _z28bas - _INKAR15_MESAFE_ZAYIF),
                min(len(_z28belge), _z28son + _INKAR15_MESAFE_ZAYIF)):
            return True
        return False

    # KOR NOKTASI (M138 ile OLCULDU): duz ifade listesi "anlami dogrulandi"
    # gibi bir iddiayi GORMUYORDU — yani kapi yalniz iki kelimeyi yasaklayip
    # asil iddia sinifini kaciriyordu. Liste DESENE cevrildi:
    #   (a) sinirsiz ifade  : "serbest ozet"
    #   (b) ceviri iddiasi  : "birebir ceviri"
    #   (c) ANLAM iddiasi   : "anlam(i)? dogrulandi / ispatlandi / denetlendi"
    # Hepsi inkar penceresiyle birlikte degerlendirilir.
    _YASAK15 = (r'serbest\s+ozet',
                r'birebir\s+[cç]eviri',
                r'anlam\w*\s+(?:do[gğ]ruland|ispatland|denetlend)\w*',
                # REGRESYON: kanitsiz sayilar geri gelirse yakala.
                # "ters ozet 16/16" YANLISTI (probe no-op, M139);
                # "ters ozet 12/16 GECIYOR" da YANLIS YONLENDIRICI cikti:
                # olumsuzlama, anlamsiz tokenla ayirt edilemiyor (M146).
                r'ters\s+ozet\s+\d+/\d+\s+GECIYOR')
    for _ya15 in _YASAK15:
        for _m15b in re.finditer(_ya15, _sk15, re.IGNORECASE):
            _bas15, _son15 = _m15b.start(), _m15b.end()
            _penc15 = _sk15[max(0, _bas15 - 60):_son15 + 60]
            if _inkar15_var(_sk15, _bas15, _son15):
                continue
            _h15.append('ANLAM IDDIASI geri gelmis: /%s/ (olcut anlami '
                        'olcmuyor) — baglam: %s'
                        % (_ya15, _penc15.replace('\n', ' ')[:90]))
    _d_sira = re.search(r'sira-duyarsiz (\d+)/(\d+) AYNI', _sk15)
    _d_notr = re.search(r'olumsuzlama ayirt edilemez (\d+)/(\d+)', _sk15)
    _d_grc = re.search(r'gercek olumsuz ozet (\d+)/(\d+) GECIYOR', _sk15)
    if not _d_sira:
        _h15.append('belgede "sira-duyarsiz A/B AYNI" sayisi YOK')
    elif _m15 and (int(_d_sira.group(2)) != _n_olc
                   or int(_d_sira.group(1)) != _n_olc - _n_sira):
        _h15.append('BAYAT SAYI: belge sira %s/%s, canli %d/%d (ayni/olculen)'
                    % (_d_sira.group(1), _d_sira.group(2),
                       _n_olc - _n_sira, _n_olc))
    # "olumsuzlama ayirt edilemez A/B": ayirt EDILEMEYEN sayisi = olculen - htar
    if not _d_notr:
        _h15.append('belgede "olumsuzlama ayirt edilemez A/B" sayisi YOK')
    elif _m15 and (int(_d_notr.group(1)) != _n_olc - _n_htar
                   or int(_d_notr.group(2)) != _n_olc):
        _h15.append('BAYAT SAYI: belge ayirt-edilemez %s/%s, canli %d/%d'
                    % (_d_notr.group(1), _d_notr.group(2),
                       _n_olc - _n_htar, _n_olc))
    if not _d_grc:
        _h15.append('belgede "gercek olumsuz ozet A/B GECIYOR" sayisi YOK')
    elif _m15 and (int(_d_grc.group(1)) != _n_gc
                   or int(_d_grc.group(2)) != _n_go):
        _h15.append('BAYAT SAYI: belge gercek olumsuz %s/%s, canli %d/%d'
                    % (_d_grc.group(1), _d_grc.group(2), _n_gc, _n_go))
    # NOT: `en_kisa_ozet` yalniz RAPORLANIR, hukme GIRMEZ. Seyrelme bu
    # olcutun bilinen siniridir; olcum yanlis degil, olcut anlami olcmuyor.
    _g15n_ok = not _h15
    _g15n = ('ayet=%d · olculen=%d · sira_farkli=%d · ters_gecen=%d · '
             'ters_hukum_fark=%d · ters_deger_fark=%d · en_kisa_ozet=%d · '
             'gercek_gecen=%d/%d · belge_sinir=%s'
             % (_n_ayet, _n_olc, _n_sira, _n_ters, _n_htar, _n_dtar,
                _n_kisa, _n_gc, _n_go,
                'var' if 'anlami OLCMEZ' in _sk15 else 'YOK'))
    if _h15:
        _g15n += ' · HATA: ' + ' | '.join(_h15)
except Exception as _e:
    _g15n = 'CALISTIRILAMADI: %s' % _e
k('C15n', 'ozet iddiasi OLCULEN sinirla sinirli (anlam iddiasi yok)',
  _g15n_ok, _g15n)

# --- C16: beyan edilmis sayaclar diskle celismez (docs/SAYAC_BEYANLARI.json) --
# NEDEN (12 Kasim 2026): C15b gomulu sayaclari DENETLEMIYOR. `TUR_HARITASI`nin
# tamami tarandi (§0 §1 §2.1-2.4 §3 §4 §5 §6 §7) ve dort turda bulunan gomulu
# sayaclarin HICBIRINI kapi gormedi: §3 "128 MODEL:" -> 119 · §6 madde sayisi ·
# §7 "12/16" · §7 "tur 10 (18 madde)". Hepsi ELLE olcumle cikti.
# D10 (gomulu sayac) dort kez tekrarladi; her seferinde "bir daha olmasin" yazildi
# ama KAPI YAZILMADI. Bu kapi o bosluga yazilir.
#
# KAPSAM — DAR VE KAPALI: "tum sayilar" denetlenemez. SURUM.md'de 14 612 sayi
# ifadesi var, cogu TARIHSEL kayit; tarihin eskimesi kusur degil, kaydin
# kendisidir (gerekce C15f'te de ayni). Bu yuzden kapsam
# `docs/SAYAC_BEYANLARI.json`: olcumu TANIMLI, beyan edilmis sayilar. Beyan
# eklenmedikce sayi denetlenmez — sahte guven uretmemek icin kapsam yazilir.
#
# SESSIZ KAPI YASAGI: bir kalip metinden kaybolursa (0 eslesme) FAIL. Aksi hâlde
# belge degisir, kalip tutmaz, kapi PASS verir ve kimse fark etmez — C15b'de
# M9/M13b ile OLCULEN tuzak.
#
# MUTASYON KANITI (12 Kasim 2026): bkz. docs/DEVIR-2026-11-08-0931.md EK 59
#   M30  "9 madde" -> "10 madde"        -> FAIL "C16 S1 ... olculen 9"  rc=1
#   M31  "TUR 6" -> "TUR 7"             -> FAIL "C16 S3 ... olculen 6"  rc=1
#   M32  S4 beyani metinden silindi     -> FAIL "C16 S4 kalip 0 eslesme" rc=1
# EK 66 (#2, S10):
#   M56  §7 beyan metni 42 -> 43         -> FAIL "S10 ... olculen 42"     rc=1
#   M57  SKILL.md'ye KAPANMAMIS '('      -> FAIL "S10 ... olculen 43"
#                                            (C19 hala PASS — tam kanit)
#   M58  NEGATIF KONTROL dengeli '('     -> PASS (sayi oynamadi)
# EK 67 (Y0, parantez kalibi duzeltmesi):
#   M59  §7 BEYAN metni 25 -> 26          -> FAIL "S10 ... olculen 25"
#   M60  SKILL.md'ye KAPANMAMIS '('       -> FAIL "S10 ... olculen 26"
#   M61  NEGATIF KONTROL dengeli
#        '(bkz §1.2, §3.4)'                -> PASS  (Y0'in kaniti: `4)` yenmiyor)
#   M62  REGRESYON: eski kalip geri       -> FAIL "S10 ... olculen 42"
#                                            (duzeltme geri alinirsa kapi yanar)
# EK 68 (Y2, kod blogu + kapanmamis backtick):
#   M63  SKILL.md'ye KAPANMAMIS backtick   -> C19 FAIL "KAPANMAMIS BACKTICK=1"
#                                            ve C16 FAIL "S10 olculemedi"
#                                            (fail-closed: olcum yoksa hüküm yok)
#   M64  NEGATIF KONTROL dengeli `x`       -> PASS (sayi 25 oynamadi)
#   M65  NEGATIF KONTROL fence icinde '('  -> PASS (kod blogu metin degil)
# EK 69 (Y3, yigin farkinda numara ayirma):
#   M66  KAPANMAMIS '(' eklendi            -> C16 FAIL "S10 ... olculen 2"
#   M67  NEGATIF '(bkz §9)'                -> PASS (mesru kapanis yenmiyor)
#   M68  NEGATIF '(rc=0)'                  -> PASS (eski kalibin yedigi dizi)
#   M69  NEGATIF '1) evet 2) hayir'        -> PASS (gercek numaralandirma)
#   M70  REGRESYON: Y2 surumu geri         -> C16 FAIL "olculen 25" (beyan 1)
_g16 = ''
_g16_ok = False
try:
    _beyant = os.path.join(_BURASI, os.pardir, 'docs', 'SAYAC_BEYANLARI.json')
    if not os.path.exists(_beyant):
        _g16 = 'CALISTIRILAMADI: docs/SAYAC_BEYANLARI.json yok'
    else:
        with open(_beyant, encoding='utf-8') as _f:
            _bey = json.load(_f)
        _h = []
        _olculen = {}

        def _olc(_b):
            """Beyanin BAGIMSIZ olcumu. Kaynak yoksa istisna — sessiz 0 degil."""
            _t = _b.get('olcum')
            if _t == 'regex_sayi':
                _y = os.path.join(_BURASI, os.pardir, _b['kaynak'])
                if not os.path.exists(_y):
                    raise IOError('kaynak yok: %s' % _b['kaynak'])
                return len(re.findall(_b['olcum_kalip'],
                                      open(_y, encoding='utf-8',
                                           errors='replace').read(), re.M))
            if _t == 'json_uzunluk':
                _y = os.path.join(_BURASI, os.pardir, _b['kaynak'])
                if not os.path.exists(_y):
                    raise IOError('kaynak yok: %s' % _b['kaynak'])
                with open(_y, encoding='utf-8') as _f2:
                    return len(json.load(_f2)[_b['anahtar']])
            if _t == 'max_tur':
                _y = os.path.join(_BURASI, os.pardir, _b['kaynak'])
                _en = 0
                for _ad in sorted(os.listdir(_y)):
                    if not _ad.startswith('k1_tur'):
                        continue
                    _m2 = re.match(r'k1_tur(\d+)', _ad)
                    if _m2:
                        _en = max(_en, int(_m2.group(1)))
                    _ic = open(os.path.join(_y, _ad), encoding='utf-8',
                               errors='replace').read()
                    for _mm in re.findall(r'TUR\s*(\d+)', _ic):
                        _en = max(_en, int(_mm))
                if _en == 0:
                    raise IOError('docs/k1_tur* bulunamadi')
                return _en
            if _t == 'uretici_madde':
                _t4 = os.path.join(_BURASI, 'tur4_paket_uret.py')
                if not os.path.exists(_t4):
                    raise IOError('tur4_paket_uret.py yok')
                import importlib.util as _iu
                _sp = _iu.spec_from_file_location('_t4_c16', _t4)
                _mod = _iu.module_from_spec(_sp)
                _sp.loader.exec_module(_mod)
                _p1 = _mod.uret(_mod.P1_ETIKET)
                return len(re.findall(r'^### (D\d+) \u2014', _p1, re.M))
            if _t in ('tablo_tamamlanan', 'tablo_bekleyen'):
                # §4 tablosundan sayilir. NEDEN §4: `§0` "10 tamamlandi · 1 bekliyor"
                # iddiasinin gerekcesi `DEVIR-2026-11-08-0931.md:5938`:
                # "§4 tablosunda 10 + 1 ✓". Yani kaynak tablonun KENDISI.
                # Satir bicimi: | **<n>** | ... |  ; BEKL.. iceren satir bekleyendir.
                _y = os.path.join(_BURASI, os.pardir, _b['kaynak'])
                if not os.path.exists(_y):
                    raise IOError('kaynak yok: %s' % _b['kaynak'])
                _ls4 = open(_y, encoding='utf-8', errors='replace').read().split('\n')
                _bas = None
                for _i4, _s4 in enumerate(_ls4):
                    if _s4.startswith('## 4.'):
                        _bas = _i4
                        break
                if _bas is None:
                    raise IOError('§4 bolumu bulunamadi')
                _son4 = len(_ls4)
                for _i4 in range(_bas + 1, len(_ls4)):
                    if _ls4[_i4].startswith('## '):
                        _son4 = _i4
                        break
                _tam = _bek = 0
                for _s4 in _ls4[_bas:_son4]:
                    if not re.match(r'^\|\s*\*\*\d+\*\*\s*\|', _s4):
                        continue
                    if 'BEKL' in _s4.upper():
                        _bek += 1
                    else:
                        _tam += 1
                if _tam + _bek == 0:
                    raise IOError('§4 tablosunda satir bulunamadi')
                return _tam if _t == 'tablo_tamamlanan' else _bek
            if _t == 'paket_serisi':
                # K1 denetim serisi: v1.3.3..v1.4.27 ARALIGI + surumsuz taban dosyasi.
                # NEDEN aralik: §0 satiri "12 paket" diyor ve tanimi "v1.3.3…v1.4.27"
                # (gerekce DEVIR-2026-11-08-0931.md:5955: aralik=12 · dosya=15).
                # Diskteki 14 surumlu dosyadan 3'u (v1441/v1443/v1444) aralik DISINDA;
                # 11 + surumsuz k1_denetim_paket.md = 12.
                _y = os.path.join(_BURASI, os.pardir, _b['kaynak'])
                _n = 0
                for _ad in sorted(os.listdir(_y)):
                    _mm = re.match(r'^k1_denetim_paket_v(\d+)\.md$', _ad)
                    if _mm:
                        _v = _mm.group(1)
                        if (int(_v[1]), int(_v[2:])) <= (4, 27):
                            _n += 1
                if os.path.exists(os.path.join(_y, 'k1_denetim_paket.md')):
                    _n += 1
                if _n == 0:
                    raise IOError('docs/k1_denetim_paket* bulunamadi')
                return _n
            if _t == 'paren_acik':
                # ESLESMEYEN ACILIS parantezi (#2, 12 Kasim 2026). `C19` bu
                # sayiyi her kosuda raporluyor ama GATE ETMIYOR; #2 onu BEYAN
                # edilen sayac yapar: sayi sessizce oynayamaz. Ayni fonksiyon
                # `_parantez_tara` kullanilir — iki tanim ayrisirsa kapi yanlis
                # seyi dogru sayar. Sayi 500 satir sinirinda degisirse BEYAN
                # guncellenmeli; yani degisim artik gorunur.
                _y = os.path.join(_BURASI, os.pardir, _b['kaynak'])
                if not os.path.exists(_y):
                    raise IOError('kaynak yok: %s' % _b['kaynak'])
                _k, _a, _bt = _parantez_tara(
                    open(_y, encoding='utf-8', errors='replace').read())
                if _bt:
                    # Fail-closed (I7): kapanmamis backtick varsa parantez sayaci
                    # guvenilmez. Beyanla karsilastirmak YANLIS hüküm verir;
                    # sessiz gecmek Y0'in tekraridir. Gurultu cikar.
                    raise IOError(
                        'kapanmamis backtick=%d — parantez sayaci guvenilmez '
                        '(Y2 sinifi); once onu duzelt' % _bt)
                return _a
            raise ValueError('bilinmeyen olcum tipi: %r' % _t)

        _MU = ('[GECERSIZ', '[DUZELTME', '[ESKI')
        for _b in _bey.get('beyanlar', []):
            _bid = _b.get('id', '?')
            try:
                _canli = _olc(_b)
            except Exception as _e2:
                _h.append('%s olculemedi: %s' % (_bid, _e2))
                continue
            _olculen[_bid] = _canli
            _yp = os.path.join(_BURASI, os.pardir, _b['belge'])
            if not os.path.exists(_yp):
                _h.append('%s belge yok: %s' % (_bid, _b['belge']))
                continue
            _bt = open(_yp, encoding='utf-8', errors='replace').read()
            # (a) kalin isareti SIL: sayi `**9**` yazilirsa da gorulmeli
            #     (C15b M13b dersi: kalin yazim kapiyi sessizlestiriyordu).
            _bn = _bt.replace('**', '').replace('__', '')
            # (b) ETIKETLI blok alinti GECMIS SOZ'dur; isaretsiz `>` normal
            #     iddia sayilir (C15b ile ayni kural — gecmisle iddiayi ayirir).
            _bn = '\n'.join(
                ('' if (_s.lstrip().startswith('>') and any(_m in _s for _m in _MU))
                 else _s) for _s in _bn.split('\n'))
            _bulunan = []
            for _mm in re.finditer(_b['kalip'], _bn):
                _bulunan.append((int(_mm.group(1)),
                                 _bn[:_mm.start()].count('\n') + 1))
            if not _bulunan:
                _h.append('%s kalip 0 eslesme (%r) — beyan metinden kayboldu; '
                          'kapi kor kalir' % (_bid, _b['kalip']))
                continue
            _kotu = [(n, l) for n, l in _bulunan if n != _canli]
            if _kotu:
                _h.append('%s: %d yerde beyan var, olculen %d; uymayanlar: %s'
                          % (_bid, len(_bulunan), _canli,
                             ', '.join('satir %d (beyan=%d)' % (l, n)
                                       for n, l in _kotu)))
        _g16_ok = bool(_olculen) and not _h
        _g16 = ('beyan=%d · olculen=%d · uyusan=%s'
                % (len(_bey.get('beyanlar', [])), len(_olculen),
                   ' '.join('%s=%d' % (_kk, _vv)
                            for _kk, _vv in sorted(_olculen.items()))))
        if not _olculen:
            _h.append('hicbir beyan olculemedi — kapi bos kume uzerinde PASS veremez')
        if _h:
            _g16 += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g16 = 'CALISTIRILAMADI: %s' % _e
k('C16', 'beyan edilmis sayaclar diskle celismez (docs/SAYAC_BEYANLARI.json)',
  _g16_ok, _g16)

def _arsiv_dogrula(ars_man, ars_yolu):
    """Arsiv katmani: `(hatalar, DOGRULANAN_dosya_sayisi)`.

    "DOGRULANAN" sozu OLCULEN seyi anlatir: bayti ve sha256'si tutan dosya.
    OLCULDU (15 Kasim 2026, Z45d — kusur): eski satir `len(ars_man) - len(eksik)`
    donuyordu, yani `bozuk` dusulmuyordu. Gercek arsivin kopyasinda 1 bayt
    bozulunca kapı su CELISKILI satiri basti:
        arsiv=VAR·16 dosya dogrulandi · ... · HATA: arsivde BOZUK 1: V146 tur 2.md sha256
    16 dosya "dogrulandi" denirken biri bozuktu. Fail-closed davranis DOGRUYDU
    (rc=1), ama BEYAN yanlisti; beyan ile olcum celisirse okuyan hangisine
    inanacagini bilemez.

    NEDEN AYRI FONKSIYON (15 Kasim 2026, Z44): katman (2) yalniz
    `~/Downloads` arsivi VARSA kosuyordu. Arsiv yokken katman HIC sinanmiyor,
    ama kapi yine PASS veriyordu — yani `C17`'nin kaniti yalniz (1) katmanini
    kapsiyordu. Fonksiyona cikarilinca AYNI kod hem gercek arsive hem de
    SENTETIK fixture'a uygulanabiliyor; katman artik arsiv olmadan da sinanir.

    Fail-closed: arsiv dizini yoksa `([], 0)` doner — cagiran taraf bunu
    "CALISTIRILAMADI" diye raporlar, "dogrulandi" diye DEGIL.
    """
    _arsdo_hl = __import__('hashlib')
    _arsdo_h, _arsdo_n = [], 0
    if not os.path.isdir(ars_yolu):
        return _arsdo_h, _arsdo_n
    _arsdo_diskte = set(os.listdir(ars_yolu))
    _arsdo_bek = set(_arsdo_d['ad'] for _arsdo_d in ars_man)
    _arsdo_eksik = sorted(_arsdo_bek - _arsdo_diskte)
    _arsdo_fazla = sorted(_arsdo_diskte - _arsdo_bek)
    _arsdo_bozuk = []
    for _arsdo_d in ars_man:
        _arsdo_p = os.path.join(ars_yolu, _arsdo_d['ad'])
        if not os.path.isfile(_arsdo_p):
            continue
        _arsdo_raw = open(_arsdo_p, 'rb').read()
        if len(_arsdo_raw) != int(_arsdo_d['bayt']):
            _arsdo_bozuk.append('%s bayt %d!=%d'
                                % (_arsdo_d['ad'][:28], len(_arsdo_raw),
                                   int(_arsdo_d['bayt'])))
        elif _arsdo_hl.sha256(_arsdo_raw).hexdigest() != _arsdo_d['sha256']:
            _arsdo_bozuk.append('%s sha256' % _arsdo_d['ad'][:28])
    if _arsdo_eksik:
        _arsdo_h.append('arsivde EKSIK %d dosya: %s'
                        % (len(_arsdo_eksik),
                           ', '.join(x[:24] for x in _arsdo_eksik[:3])))
    if _arsdo_fazla:
        _arsdo_h.append('arsivde FAZLA %d dosya: %s'
                        % (len(_arsdo_fazla),
                           ', '.join(x[:24] for x in _arsdo_fazla[:3])))
    if _arsdo_bozuk:
        _arsdo_h.append('arsivde BOZUK %d: %s'
                        % (len(_arsdo_bozuk), ' | '.join(_arsdo_bozuk[:3])))
    _arsdo_n = len(ars_man) - len(_arsdo_eksik) - len(_arsdo_bozuk)
    return _arsdo_h, _arsdo_n


# --- C17: §3 arsiv sayaclari manifestoya bagli (12 Kasim 2026) -----------------
# NEDEN: `TUR_HARITASI` §3 basligi "16 dosya · 1 865 272 B · 119 `MODEL:`" diyor.
# Bu sayaclar DEPO DISI bir kaynaga (~/Downloads arsivi) bagliydi ve HIC KAPISI
# YOKTU. Kapisiz sayac bayatlar — D10 alti kez tekrarladi. Arsivin kendisi depoya
# giremez (1.8 MB, kisisel arsiv); ama SAYILARI dogrulanabilir.
#
# COZUM: `docs/ARSIV_MANIFESTOSU.json` (4.8 KB) depoda kalir — 16 dosyanin adi,
# bayti, sha256'si ve `MODEL:` sayisi. Iki katman:
#   (1) DEPO ICI (her zaman): §3 basligindaki 3 sayi manifestoyla uyusmali.
#   (2) ARSIV VARSA: her dosya adi+bayt+sha256 birebir tutmali.
#       Arsiv YOKSA: FAIL DEGIL, "CALISTIRILAMADI". Kaynagi olmayan makinede her
#       kosu kirmizi olsaydi kapi degil gurultu olurdu (AGENTS.md §5).
#
# OLCUM TUZAGI (kayda geciyor): `^\s+MODEL:` kalibi YANILTIR — `\s` satir sonunu
# da yiyor, bos satir ardindan gelen GIRINTISIZ `MODEL:` de eslesiyor. Manifest
# yazilirken olculdu: kalip 12 dedi, dogrusu 2. Sayim SATIR SATIR yapildi.
#
# MUTASYON KANITI (12 Kasim 2026): bkz. docs/DEVIR-2026-11-08-0931.md EK 61
#   M36  §3 "16 dosya" -> "17 dosya"            -> FAIL rc=1
#   M37  manifest sha256 bir dosyada bozuldu    -> FAIL rc=1
#   M38  manifesto dosyasi silindi              -> FAIL rc=1
# EK 65 (§7 eklendikten sonra, #1):
#   M51  manifest paket_adi 3->2                -> FAIL (§7 esleme)
#   M52  manifest paket_satiri_bas 1->0         -> FAIL (§7 Paket:bas)
#   M53  manifest paket_her 2->1                -> FAIL (§7 paket:her)
#   M54  §7 CANLI iddia 3/16 -> 9/16            -> FAIL (§7 esleme)
#   M55  NEGATIF KONTROL: §7 ALINTI blogu bozuldu -> PASS (kesme calisiyor)
_g17 = ''
_g17_ok = False
try:
    _m17 = os.path.join(_BURASI, os.pardir, 'docs', 'ARSIV_MANIFESTOSU.json')
    if not os.path.exists(_m17):
        _g17 = 'CALISTIRILAMADI: docs/ARSIV_MANIFESTOSU.json yok'
    else:
        with open(_m17, encoding='utf-8') as _f:
            _man = json.load(_f)
        _ds = _man.get('dosyalar', [])
        _h = []
        if not _ds:
            _h.append('manifesto bos — beyan edilmis dosya yok')

        _n_dosya = len(_ds)
        _n_bayt = sum(int(d.get('bayt', 0)) for d in _ds)
        _n_model = sum(int(d.get('model_satiri', 0)) for d in _ds)
        # §7 uc esleme sayaci (12 Kasim 2026, #1). TANIM manifestte YAZILI
        # (`_paket_tanimi`); kapi yeniden yorumlamaz, ayni tanimi sayar.
        _n_pad = sum(1 for d in _ds if int(d.get('paket_adi', 0)))
        _n_pbas = sum(1 for d in _ds if int(d.get('paket_satiri_bas', 0)))
        _n_pher = sum(1 for d in _ds if int(d.get('paket_her', 0)))

        # ---- (1) DEPO ICI: §3 basligi manifestoyla uyusmali
        _hp = os.path.join(_BURASI, os.pardir, 'docs', 'TUR_HARITASI.md')
        _s3 = ''
        _s7t = ''
        if not os.path.exists(_hp):
            _h.append('TUR_HARITASI.md yok — §3 olculemedi')
        else:
            _ht = open(_hp, encoding='utf-8', errors='replace').read()
            _mm = re.search(
                r'##\s*3\.\s*AR[\u015eS][\u0130I]V\s*[\u2014\u2013-]\s*'
                r'(\d+)\s*dosya\s*\u00b7\s*([\d ]+)\s*B\s*\u00b7\s*'
                r'(\d+)\s*`MODEL:`', _ht)
            if not _mm:
                _h.append('§3 basligi bulunamadi — kalip bayatladi, kapi kor kalir')
            else:
                _b_dosya = int(_mm.group(1))
                _b_bayt = int(_mm.group(2).replace(' ', ''))
                _b_model = int(_mm.group(3))
                _s3 = '%d dosya·%d B·%d MODEL:' % (_b_dosya, _b_bayt, _b_model)
                if _b_dosya != _n_dosya:
                    _h.append('§3 dosya: beyan=%d · manifest=%d'
                              % (_b_dosya, _n_dosya))
                if _b_bayt != _n_bayt:
                    _h.append('§3 bayt: beyan=%d · manifest=%d'
                              % (_b_bayt, _n_bayt))
                if _b_model != _n_model:
                    _h.append('§3 MODEL:: beyan=%d · manifest=%d'
                              % (_b_model, _n_model))

            # ---- (1b) §7 CANLI iddia: uc esleme sayaci manifestoyla uyusmali
            # NEDEN (12 Kasim 2026, #1): §7'deki "esleme kaniti 3/16 · Paket:
            # satiri 1/16 · Hedef paket dahil 2/16" satiri IKI KEZ yanlis
            # cikmisti (EK 59/60) ve HIC KAPISI YOKTU — her tur elle olculdu.
            # OLCUM TUZAGI: ayni sayilar §7'nin ALTINDAKI alinti blogunda da
            # geciyor (`> **1/16** ...`). Tum belgede `re.search` yanlis yeri
            # bulabilir; bu yuzden ONCE madde bulunur, SONRA `>` ile baslayan
            # ilk satirda KESILIR — yalniz canli paragraf taranir.
            _m7 = re.search(r'Ar[\u015fs]ivdeki dosyalar[\u0131i]n hangi pakete '
                            r'ait oldu[\u011fg]u', _ht)
            if not _m7:
                _h.append('§7 esleme maddesi bulunamadi — kalip bayatladi, '
                          'kapi kor kalir')
            else:
                _canli = _ht[_m7.start():_m7.start() + 2000]
                _k7 = re.search(r'(?m)^\s*>', _canli)
                if _k7:
                    _canli = _canli[:_k7.start()]
                _p1 = re.search(r'e[\u015fs]leme kan[\u0131i]t[\u0131i]\s+\*\*'
                                r'(\d+)\s*/\s*(\d+)\*\*', _canli)
                _p2 = re.search(r'`Paket:`\s*sat[\u0131i]r[\u0131i]\s+\*\*'
                                r'(\d+)\s*/\s*(\d+)\*\*', _canli)
                _p3 = re.search(r'`Hedef paket:`\s*dahil\s+\*\*'
                                r'(\d+)\s*/\s*(\d+)\*\*', _canli)
                _s7 = []
                for _et, _mx, _n in (('esleme', _p1, _n_pad),
                                     ('Paket:bas', _p2, _n_pbas),
                                     ('paket:her', _p3, _n_pher)):
                    if not _mx:
                        _h.append('§7 %s kalibi bulunamadi — sessiz gecis yok'
                                  % _et)
                        continue
                    _b, _payda = int(_mx.group(1)), int(_mx.group(2))
                    _s7.append('%s=%d/%d' % (_et, _b, _payda))
                    if _payda != _n_dosya:
                        _h.append('§7 %s payda: beyan=%d · manifest dosya=%d'
                                  % (_et, _payda, _n_dosya))
                    if _b != _n:
                        _h.append('§7 %s: beyan=%d · manifest=%d'
                                  % (_et, _b, _n))
                if _s7:
                    _s7t = ' · '.join(_s7)

        # ---- (2) ARSIV VARSA sha256 dogrulamasi
        _ars = os.path.expanduser(os.path.join('~', 'Downloads',
                                               'DENET\u0130M TAWAKKUL', 'Ar\u015fiv'))
        _ars_durum = 'YOK'
        if os.path.isdir(_ars):
            _ars_h, _ars_n = _arsiv_dogrula(_ds, _ars)
            _h.extend(_ars_h)
            # N/M: M = manifestteki dosya, N = bayt+sha tutan. Tek sayi
            # yazmak, N'yi 'arsivdeki dosya' gibi okutuyordu (Z45d).
            _ars_durum = 'VAR·%d/%d dosya dogrulandi' % (_ars_n, len(_ds))
        else:
            _ars_durum = 'YOK (CALISTIRILAMADI — kapı degil, kaynak yok)'

        # ---- (3) KATMANIN KENDISI SINANIR (fixture) — ARSIV OLMADAN da
        # NEDEN (15 Kasim 2026, Z44): (2) katmani yalniz arsiv varsa kosuyordu
        # ve bu makinede arsiv YOK — yani katman hic sinanmadi, kapinin kaniti
        # yalniz (1) katmanini kapsiyordu. Sentetik arsiv kurulur ve AYNI
        # `_arsiv_dogrula` ona uygulanir. 5 vakanin 5'i de tutmali.
        # `~/Downloads` GEREKMEZ: fixture gecici dizinde kurulur ve silinir.
        # On ek `ars_fx_` (C15l `plato_*` sizintisini sayar, karismaz).
        _fx_ok = 0
        _fx_h = []
        _fx_d = __import__('tempfile').mkdtemp(prefix='ars_fx_')
        try:
            _fx_man = [
                {'ad': 'a.md', 'bayt': 3,
                 'sha256': __import__('hashlib').sha256(b'aaa').hexdigest()},
                {'ad': 'b.md', 'bayt': 3,
                 'sha256': __import__('hashlib').sha256(b'bbb').hexdigest()}]

            def _fx_yaz(_fx_ad, _fx_bayt):
                with open(os.path.join(_fx_d, _fx_ad), 'wb') as _fx_f:
                    _fx_f.write(_fx_bayt)

            _fx_yaz('a.md', b'aaa')
            _fx_yaz('b.md', b'bbb')
            # (i) saglam arsiv: hata YOK, 2 dosya dogrulandi
            _fx_e1, _fx_n1 = _arsiv_dogrula(_fx_man, _fx_d)
            if not _fx_e1 and _fx_n1 == 2:
                _fx_ok += 1
            else:
                _fx_h.append('(i) saglam arsivde hata: %s'
                             % ((_fx_e1 or ['n=%d' % _fx_n1])[0][:40]))
            # (ii) BAYT bozuk
            _fx_yaz('a.md', b'aa')
            _fx_e2, _fx_n2 = _arsiv_dogrula(_fx_man, _fx_d)
            # (ii) AYRICA SAYI: 1 dosya bozuk -> DOGRULANAN 1, haber verilen 2.
            # NEDEN (15 Kasim 2026, Z45d): eski kod `len(man) - len(eksik)`
            # donuyordu; bozuk dosya dusulmedigi icin kapi "16 dosya dogrulandi"
            # derken "BOZUK 1" diyordu. Sayi yalniz (i)'de sinaniyordu, yani
            # duzeltme YUK TASIMIYORDU (mutasyonla yanmazdi).
            if any('bayt' in _fx_x for _fx_x in _fx_e2) and _fx_n2 == 1:
                _fx_ok += 1
            else:
                _fx_h.append('(ii) bayt bozukligu yakalanmadi ya da n=%d (beklenen 1)'
                             % _fx_n2)
            # (iii) SHA bozuk — bayt AYNI, icerik farkli
            _fx_yaz('a.md', b'aab')
            _fx_e3, _fx_n3 = _arsiv_dogrula(_fx_man, _fx_d)
            if any('sha256' in _fx_x for _fx_x in _fx_e3) and _fx_n3 == 1:
                _fx_ok += 1
            else:
                _fx_h.append('(iii) sha uyusmazligi yakalanmadi ya da n=%d (beklenen 1)'
                             % _fx_n3)
            # (iv) EKSIK dosya
            _fx_yaz('a.md', b'aaa')
            os.unlink(os.path.join(_fx_d, 'b.md'))
            _fx_e4, _fx_n4 = _arsiv_dogrula(_fx_man, _fx_d)
            if any('EKSIK' in _fx_x for _fx_x in _fx_e4):
                _fx_ok += 1
            else:
                _fx_h.append('(iv) eksik dosya yakalanmadi')
            # (v) FAZLA dosya
            _fx_yaz('b.md', b'bbb')
            _fx_yaz('c.md', b'ccc')
            _fx_e5, _fx_n5 = _arsiv_dogrula(_fx_man, _fx_d)
            if any('FAZLA' in _fx_x for _fx_x in _fx_e5):
                _fx_ok += 1
            else:
                _fx_h.append('(v) fazla dosya yakalanmadi')
        finally:
            __import__('shutil').rmtree(_fx_d, ignore_errors=True)
        if _fx_ok != 5:
            _h.append('FIXTURE %d/5: %s' % (_fx_ok, ' | '.join(_fx_h)))

        _g17_ok = not _h
        _g17 = ('§3=%s · §7=%s · manifest=%d dosya·%d B·%d MODEL: · arsiv=%s'
                ' · fixture=%d/5'
                % (_s3 or '-', _s7t or '-', _n_dosya, _n_bayt, _n_model,
                   _ars_durum, _fx_ok))
        if _h:
            _g17 += ' · HATA: ' + ' | '.join(_h)
except Exception as _e:
    _g17 = 'CALISTIRILAMADI: %s' % _e
k('C17', 'arsiv §3 + §7 sayaclari manifestoya bagli (ARSIV_MANIFESTOSU.json)',
  _g17_ok, _g17)

# --- bilgi ----------------------------------------------------------------
print()
print('  BILGI  icerik ozeti: bolum=%d · tablo=%d · kod bloku=%d'
      % (len(re.findall(r'^## ', C, re.M)), C.count('\n|'), C.count('```')))
tok = round(len(C.encode('utf-8')) / 2.46)
print('  BILGI  token tahmini ~%d (bayt/2.46 gecmis oran; kesin tokenizer ile OLCULMEDI)' % tok)
if tok > 5000:
    print('  UYARI  spec "<5000 token onerir"; bu dosya ~%d. Bilincli sapma, teslimde OLCULMEYEN yazilir.' % tok)
    uyari.append('token')

print()
if hata:
    print('SONUC: IHLAL VAR (%d)' % len(hata))
    for h in hata:
        print('  - ' + h)
    sys.exit(1)
print('SONUC: TEMIZ — %d kontrol gecti (sayac)' % sayac['kontrol'])
sys.exit(0)