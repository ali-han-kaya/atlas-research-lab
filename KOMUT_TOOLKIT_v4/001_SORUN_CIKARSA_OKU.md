> Bu dosyayı yalnızca bir şey ters gittiyse aç. Normal akışta gerekmez.

# SORUN ÇIKARSA

## 1. Yapay zekâ `HAZIR - calismani yapistir` demedi

**En sık neden:** dosyanın tamamı kopyalanmadı.

Yap: `000_ONCE_BUNU_YAPISTIR.md` dosyasını aç, `Ctrl+A` / `Cmd+A` ile **tamamını**
seç, yeniden yapıştır. Dosya `> BU DOSYAYI SOHBETE YAPIŞTIR` satırıyla başlar ve
`...o iddia raporda yer almaz.` satırıyla biter. İkisi de yapıştırdığın metinde
varsa tam kopyalanmıştır.

**İkinci neden:** model konuşmaya başladı, rolü almadı. Tek satır yaz:

```
Rolu al. Sadece su satiri yaz: HAZIR - calismani yapistir
```

## 2. Çalışmam çok büyük, sohbete sığmıyor

Sırayla:

1. Önce `000_ONCE_BUNU_YAPISTIR.md`'yi yapıştır, `HAZIR` cevabını al.
2. Çalışmanı **dosya olarak ekle** (metne yapıştırma). Çoğu arayüz dosyayı
   yapıştırılan metinden daha verimli işler.
3. Hâlâ sığmıyorsa bölümlere ayır ve şunu yaz:

```
Calisma 3 parca halinde gelecek. Her parcadan sonra sadece
"PARCA n/3 ALINDI - KEEP <sayi>" yaz, baska bir sey yazma.
Uc parca da gelince F0'dan basla.
```

Koruma sözleşmesi parça parça da çalışır: her parçanın `KEEP` listesi ayrı üretilir,
sonunda birleştirilir.

## 3. Rapor çok uzun / panik yaptım

İlk ekran 32 satırı / 1800 karakteri geçmemeliydi. Geçtiyse şunu yaz:

```
Raporu §9 ilk ekran sozlesmesine gore yeniden yaz: en fazla 32 satir,
en fazla 3 eylem. Gerisi ek bolumlerde kalsin.
```

## 4. Yanlış tipte sınıflandırdı

Tek kelime yaz — düzeltmek ucuzdur, yalnız profil kuyruğu yeniden koşar:

```
AKADEMIK
```

(veya `KOD`, `VERI`, `GIRISIM`, `BELGE`)

## 5. İçeriğimi sildiğini düşünüyorum

Şunu yaz:

```
KORUMA raporunu ac: hangi KEEP kayitlari degisti, hangi sinifta,
kaybin gerekcesi ne? Beyansiz kayip varsa geri al.
```

Beyansız kayıp `P0`'dır ve teslimi engellemeliydi. Engellemediyse bu aracın
kendi hatasıdır — raporun `BILINEN_SINIRLAR` bölümünde görünmesi gerekir.

## 6. "Ölçtüm" dedi ama ölçemezdi

`MOD=B` iken hash, betik çıktısı, DOI erişim onayı veya dolar maliyeti üretmek
yasaktır. Gördüysen yaz:

```
MOD=B idi. §2'ye gore hash/betik/DOI/maliyet uretmen yasakti.
Bu satirlari NOT_EXECUTED olarak degistir ve durumu OLCULMEDI yap.
```

## 7. Koşu yarıda kaldı, sohbet öldü

Yeni bir sohbet aç:

1. `000_ONCE_BUNU_YAPISTIR.md`'yi yapıştır.
2. `HAZIR` cevabından sonra şunu yaz:

```
DEVAM: <KOSU_KIMLIGI>
```

3. Elinde varsa `KEEP` listesini ve çalışmayı da yapıştır.

Kimliği kaybettiysen sorun değil — baştan koş. Araç raporda "devam kaydı
bulunamadı, baştan başlandı" yazar.

## 8. Gerçek bağımsız denetim istiyorum

Tek sohbette gerçek körlük yoktur; model kendi düzeltmelerini zaten görmüştür.
Bunun için:

1. **Yeni bir sohbet** aç (aynı sohbet olmaz).
2. `ARACLAR/BAGIMSIZ_DENETIM_YENI_SOHBETE_YAPISTIR.md` dosyasını yapıştır.
3. **Yalnız final çıktıyı** ver — düzeltme kayıtlarını, bulgu listesini, önceki
   raporu **verme**.

O sohbetin raporunda `DENETIM_TIPI: BAGIMSIZ` yazabilir.

## 9. Betikleri çalıştırmak istiyorum (MODE-A)

```bash
python3 ARACLAR/betikler/v4_selftest.py            # araci kendi kapisindan gecir
python3 ARACLAR/betikler/v4_verify.py <klasor>     # arsiv/hijyen/sir taramasi
python3 ARACLAR/betikler/v4_preserve.py <once> <sonra>   # koruma kapisi
python3 ARACLAR/betikler/v4_gate.py <a.json> <b.json>    # karar birlestirici
python3 ARACLAR/betikler/v4_consistency.py .       # paket ici celiski taramasi
```

Harici paket gerekmez — yalnız Python standart kütüphanesi.

**Sürüm:** Sözdizimi Python 3.9 hedefiyle doğrulandı ve 3.9 dışı hiçbir çalışma
zamanı API'si kullanılmıyor; **çalışma zamanı testleri 3.11 üzerinde koştu.**
3.9/3.10'da bizzat çalıştırılmadı — bu bir tahmin değil, ölçülmemiş bir alan.

**`--help`:** yukarıdaki beş komut betiği destekler. `v4_common.py` bir
kütüphanedir, doğrudan çalıştırılmaz.

**Çıkış kodları:**

| Kod | Anlamı | Ne zaman |
|---|---|---|
| `0` | engel yok | denetim koştu, `P0` bulunmadı |
| `1` | engel var **veya** girdi denetlenemedi | `P0` bulundu; ya da hedef okunamadı/eksik/yetersiz — **okunamayan hedef "temiz" değildir** |
| `2` | argüman hatası | bilinmeyen bayrak, eksik zorunlu argüman (argparse) |

## 10. Hiçbiri işe yaramadı

Aracın kendisi kusurlu olabilir. Yapay zekâya şunu yaz:

```
Bu paketin kendisinde bir kusur oldugunu dusunuyorum: <ne oldu>.
Paketi denetle, bulguyu C1 sema formatinda yaz, duzeltme oner.
Kendini savunma.
```
