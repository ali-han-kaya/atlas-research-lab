> **BU BİR ÖRNEKTİR — senin verinden üretilmedi.** Çıktının nasıl görüneceğini
> görmek için buradadır. Sayılar uydurmadır ve hiçbir gerçek çalışmaya ait değildir.

# Örnek çıktı — bir akademik makale koşusu

## Yapay zekânın ilk cevabı (çalışmayı yapıştırmadan önce)

```
ARAC_ENVANTERI: dosya_okuma=EVET kod_calistirma=HAYIR ag_erisimi=HAYIR
MOD=B

HAZIR - calismani yapistir
```

## Koşu sırasında gördüklerin

```
Bu kosu sana en fazla 3 kez soru sorar. Tahmin: 6-12 dk (tampon dahil).
Uzatan tek sey: bolum sayisi > 200.

TIP=AKADEMIK | SINYAL=kural-2 (kaynakca + 14 DOI) | GUVEN=YUKSEK

[F0/F6 ALIM]      47/47 dosya okundu · KEEP 128 kilitli · sirada: F1 SOZLESME
[F1/F6 SOZLESME]  6 zorunlu kontrol secildi · kalan durus: 3 · sirada: F2 DENETIM
[F2/F6 DENETIM]   KEEP 128 kilitli · 40 bulgu · kalan durus: 3 · sirada: F3 ONARIM

DUR-1/3 · SILME ONAYI
KEEP-014 dusecek: "Orneklem tek merkezlidir ... nedensellik cikarimina" (§4)
Neden: ayni cumle §6'da birebir tekrar ediyor.
  1) SIL (tekrar oldugu icin)
  2) KORU   <- varsayilan
Cevap gelmezse KORU uygulanir, raporda "onaysiz" isaretlenir.

[F3/F6 ONARIM]    6 FIX uygulandi · 34 bulgu acik · sirada: F4 KORUMA
[F4/F6 KORUMA]    KEEP 128/128 korundu · 0 beyansiz kayip · sirada: F5 KAPI
[F5/F6 KAPI]      P0=0 P1=6 P2=31 · DENETIM_TIPI=OZ_DENETIM · sirada: F6 TESLIM
```

---

## İLK EKRAN (≤32 satır / ≤1800 karakter)

```
KARAR
  KAPSAM      : 47 dosya, 128 bolum, 14 DOI, 96 sayisal iddia
  OLCULEN     : 6 zorunlu kontrolun 5'i kosuldu (kanit: bulgu listesi §7) -> KOSULLU
  OLCULMEYEN  : DOI erisim dogrulamasi (MOD=B, ag yok) - 14 DOI UNVERIFIED_SOURCE
  DENETIM_TIPI: OZ_DENETIM

KORUMA
  KEEP 128/128 korundu · 1 silme onayin bekliyor (KEEP-014, tekrar)

SIMDI 3 SEY
  1. §5 Sonuc: "tum Almanya'da uygulanabilir" ifadesi n=12 tek merkezli
     orneklemle desteklenmiyor -> kapsami "bu merkezde" olarak daralt.
  2. Kaynakca: metindeki 3 atif kaynakcada yok (Yilmaz 2021, Demir 2019,
     Kaya 2020) -> ekle veya atiflari kaldir.
  3. §3 Bulgular: guven araligi sifiri iceriyor ama "p<0.05" yaziyor
     -> ikisinden biri yanlis; ham veriden yeniden hesapla.

GERI KALANI
  37 bulgu daha: 3 P1, 34 P2 -> §7 tam liste

NE DEGISTI
  FIX-001 §2 Yontem: orneklem buyuklugu gerekcesi eklendi
  FIX-002 §4 Sinirliliklar: kesitsel tasarim uyarisi netlestirildi
  FIX-003 §1 Giris: terim birligi (YZ -> yapay zeka, 9 yerde)
  FIX-004 §3 Bulgular: tablo-metin sayi uyusmazligi giderildi (13.23 -> 13.232)
  FIX-005/006 §6 Kaynakca: 2 yil bilgisi eslendi · §2 eksik veri stratejisi yazildi

OLCULMEYEN
  - DOI erisim kontrolu: MOD=B, ag yok -> 14 DOI UNVERIFIED_SOURCE
  - Etik kurul onay numarasi dogrulanmadi: dis kaynak gerekir
  - Istatistik yeniden hesabi: ham veri saglanmadi -> INDETERMINATE degil,
    NOT_AVAILABLE (bulgu 3 bu yuzden "yeniden hesapla" diyor)
```

*(İlk ekran burada biter. Aşağısı ek bölümlerdir.)*

---

## §7 TAM BULGU LİSTESİ

| ID | Şiddet | Kod | Konum | Kanıt | Düzeltme |
|---|---|---|---|---|---|
| F-001 | P1 | LOGICAL_ERROR | §5 satır 210 | "tum Almanya'da uygulanabilir oldugu" | kapsamı "bu merkezde" olarak daralt |
| F-002 | P1 | CITATION_MISSING | §2 satır 88 | "(Yilmaz, 2021)" | kaynakçaya ekle veya atfı kaldır |
| F-003 | P1 | LOGICAL_ERROR | §3 satır 141 | "p<0.05 (GA: -0.02, 0.31)" | ikisinden biri yanlış, yeniden hesapla |
| F-004 | P2 | STYLE_FAILURE | §1 satır 22 | "son derece onemli bir bulgu" | belirsiz zarfı kantitatif karşılıkla değiştir |
| … | | | | | |

## §8 TAM DEĞİŞİKLİK LİSTESİ

| FIX | Bulgu | Konum | Önce | Sonra |
|---|---|---|---|---|
| FIX-004 | F-011 | §3 Tablo 2 | `χ²=13.23` | `χ²=13.232` |
| … | | | | |

## BILINEN_SINIRLAR

```
- ne_olculmedi        : DOI'lerin gercekten erisilebilir oldugu
  hangi_karari_etkiler : "Bu makaleyi dergiye gonderebilir miyim" karari
  eksik_kanit         : MOD=B, ag erisimi yok; MOD=A'da CrossRef sorgusu yapilirdi
  siddet              : P1

- ne_olculmedi        : Istatistiksel testlerin ham veriden yeniden hesabi
  hangi_karari_etkiler : "Bulgular bolumundeki sayilara guvenebilir miyim" karari
  eksik_kanit         : Ham veri dosyasi saglanmadi
  siddet              : P1

- ne_olculmedi        : Etik kurul onay numarasinin gecerliligi
  hangi_karari_etkiler : "Etik beyani eksiksiz mi" karari
  eksik_kanit         : Kurum kaydina erisim gerekir - dis dogrulama
  siddet              : P2
```

## KAPANIS

```
KAPANIS
Durum: KOSULLU - 3 P1 bulgu acik, hicbiri seni bloklamiyor ama duzeltilmeli.
Simdi tek yapman gereken: yukaridaki 1. maddeyi duzelt (kapsam daraltma).
Bu kosuyu geri getirmek icin: KOSU_KIMLIGI 7f3a-2026-08-17
Bu sohbeti kapatabilirsin.
```

## SONRAKI_SEFER.md (ayrı dosya olarak üretilir)

```
# SONRAKI SEFER
tip           : AKADEMIK (GUVEN=YUKSEK, kural-2: kaynakca + 14 DOI)
keep_sayisi   : 128
kosu_kimligi  : 7f3a-2026-08-17
tarih         : 2026-08-17
mod           : B (arac yok)
ertelenen     : F-004, F-007, F-012 ... (34 adet P2)
acik_p1       : F-001, F-002, F-003
onaysiz_silme : KEEP-014 (tekrar oldugu icin onerilmisti, KORU uygulandi)
not           : Gecen sefer AKADEMIK sectin. Degistirmek istersen tek kelime yaz.
```
