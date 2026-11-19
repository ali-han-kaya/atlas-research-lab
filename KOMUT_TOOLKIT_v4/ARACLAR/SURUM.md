> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# SÜRÜM v4.1 — ne değişti, ne ölçüldü, ne ölçülmedi

> v4.0 teslim edildi, ardından paket kendi F0→F6 disiplininden geçirildi ve
> yedi kusur düzeltildi (§5). Bu, o denetimden geçmiş sürümdür.

---

## 1. v3'ten v4'e: on iki değişiklik

| # | v3'te | v4'te | Neden |
|---|---|---|---|
| 1 | Otomatik iş-tipi tespiti vaat ediliyor, karar tablosu yok | Sıralı ilk-eşleşen sınıflandırıcı, 5 tip, beyan edilen sinyal | Kullanıcı ne istediğini anlatmak zorunda kalmasın |
| 2 | 13 satırlık faz tablosu, 9 çıktısı rapora hiç girmiyor | 7 faz; her fazın rapora giren adlandırılmış çıktısı var | Rapora girmeyen faz uygulanmaz, görünmez |
| 3 | Yalnız şiddet ekseni (`P0/P1/P2`) | Şiddet **+** kapalı tür kodu listesi | Tür kodu yeniden deneme hedefini seçer |
| 4 | "Döngü BLOCKER=0 olana dek sürer" — hedef belirtilmemiş | Hedefli onarım + dondurulmuş bölgeler | Global yeniden yazım = veri kaybı |
| 5 | Denetçi güvenilmezse çıkış yolu yok | `GRADER_MISCALIBRATED` → `BUTUNLUK_ASKISI`, yeniden deneme yasak | Güvenilmez denetçiyi yeniden çağırmak ikinci güvenilmez karar üretir |
| 6 | **Veri kaybı ölçülmüyor** | Koruma sözleşmesi + `v4_preserve.py` | Kullanıcının birinci kısıtı |
| 7 | Her fazda insan onayı (13 tur) | Otomatik varsayılan, ilan edilmiş 3 duruş bütçesi | "Her şey otomatik olsun" isteği |
| 8 | Betiklerde proje sabitleri (test sayısı, proje adı) | Sıfır proje sabiti; taban çizgisi + oran kuralı | Yeni bir işte yanlış engel üretmesin |
| 9 | Ahlak katmanı yok | 5 negatif kural, her biri bir artefakta bağlı | Bağlanmamış ahlak cümlesi davranış değiştirmez |
| 10 | Enjeksiyon savunması yok | Veri sınırı + `INJECTION_ATTEMPT` bulgusu | Kullanıcı bir *metin* yapıştırıyor |
| 11 | Araç yeteneği sorulmuyor | `MODE-A` / `MODE-B`; MODE-B'de olumlu karar **yok** | Araçsız modelden hash/betik çıktısı istemek uydurmaya davettir |
| 12 | Tek kelimelik `PASS` damgası | Üçlü karar: `KAPSAM` + `OLCULEN` + `OLCULMEYEN` | Kapsamsız damga, korumaya çalıştığının tersini üretir |

## 2. Kapatılan ölçülmüş açıklar

Her satır şimdi `v4_selftest.py` içinde bir regresyon fikstürüdür. **Köken**
sütunu, o saldırının nerede gerçekten çalıştırıldığını söyler — hepsi aynı
kaynaktan gelmez ve bunu birbirine karıştırmak kendi 3. kuralımızı
("ölçmediğini iddia etme") çiğnerdi:

- `v3-ÖLÇÜLDÜ` — bir önceki neslin **gerçek kodu** üzerinde çalıştırıldı ve
  orada sahte olumlu karar üretti.
- `v4-TASLAK` — bu paketin **kendi ilk taslağını** kırdı; düzeltildi.
- `ÖNLEM` — v3'te böyle bir kontrol hiç yoktu; v4'te yeni eklendi, karşılaştırma
  yapılacak bir v3 davranışı yok.

| Kod | Saldırı | Köken | v3'te sonuç | v4'te sonuç |
|---|---|---|---|---|
| SP-1 | Boş JSON (`{}`) iki kapı olarak verildi | v3-ÖLÇÜLDÜ | olumlu karar | `NO_INSPECTION_EVIDENCE` → engel |
| SP-2 | Kapalı liste dışı şiddet etiketi (`CRITICAL`, `BLOCKER`, `SEV0`, boşluklu) taşıyan 4 kritik bulgu | v3-ÖLÇÜLDÜ | olumlu karar | kapalı liste dışı → her biri `P0` |
| SP-3 | Aynı dosya iki kapı olarak verildi | v3-ÖLÇÜLDÜ | "2 kapı geçti" | `IDENTICAL_GATE_INPUTS` → engel |
| SP-4 | Boş klasör denetlendi | v3-ÖLÇÜLDÜ | `files=0`, olumlu karar | `EMPTY_TARGET` → engel |
| SP-5 | Beyan `p0_count: 0`, gerçekte `P0` var | v3-ÖLÇÜLDÜ | olumlu karar | `METADATA_MISMATCH` → engel |
| SP-6 | `xxx`/`test-`/`...` içeren **gerçek formatlı** anahtarlar | v3-ÖLÇÜLDÜ | nota indirildi, olumlu karar | otomatik indirgeme yok → engel |
| SP-7 | Aracın kendi klasörü denetlendi | v3-ÖLÇÜLDÜ | engel (kendi kanıtına takılıyor) | geçiyor (kanıt dizini hijyenden muaf, sır taramasında) |
| VK-1 | Bölümün ilk 200 karakteri korunup gerisi silindi | v3-ÖLÇÜLDÜ | koruma geçti (%84 kayıp) | `CONTENT_LOST` → engel |
| VK-2 | Zorunlu birim türünden 0 birim çıktı | ÖNLEM | kontrol yok | `INDETERMINATE` → engel |
| VK-4 | Yalnız tipografik normalizasyon farkı | v3-ÖLÇÜLDÜ | yanlış `P0` | 0 bulgu |
| KT-A | Bölüm aynı hacimde tutulup **anlamı** dolguyla değiştirildi | v4-TASLAK | (v4'ün ilk taslağını da kırdı: `P1`) | içerik kelimesi < %70 → `P0` |
| KT-B | `onay: true` yazılmış imzasız silme kaydı | v4-TASLAK | (v4'ün ilk taslağını da kırdı: meşru sayıldı) | `UNSIGNED_WAIVER` → engel |
| PI-2 | Dosya adında sınırlayıcı taklidi | ÖNLEM | görülmüyor | `INJECTION_ATTEMPT` bulgusu |
| KT-11 | Arşivde yol geçişi / aşırı sıkıştırma oranı | ÖNLEM | kontrol yok | `UNSAFE_ARCHIVE_ENTRY` → engel |
| GZ-1 | İmzasız muafiyet kaydı | ÖNLEM | kontrol yok | `UNSIGNED_WAIVER` → engel |

**KT-A ve KT-B, bu paketin kendi ilk taslağını kırdı.** İkisi de düzeltildi ve
regresyon fikstürü olarak eklendi. Bu satır burada duruyor çünkü "gizli kusur
yok" kuralı kendi geçmişimiz için de geçerlidir.

## 3. Bu sürümde gerçekten ölçülenler

`ARACLAR/KANIT/` altındaki JSON dosyaları bu koşunun ham çıktılarıdır.

| # | Ne ölçüldü | Sonuç | Kanıt |
|---|---|---|---|
| 1 | 36 saldırı/regresyon fikstürü | 36/36 geçti | `KANIT/01_oztest.json` |
| 2 | Paket içi tutarlılık (kapalı listeler, sözlük, kırık referans) | engel yok | `KANIT/02_tutarlilik.json` |
| 3 | Paketin kendi arşiv/hijyen/sır kapısından geçmesi | engel yok | `KANIT/03_arsiv.json` |
| 4 | Koruma kapısı yanlış pozitif oranı — 404 bölümlük gerçek depo, girdi=çıktı | 404/404 korundu, 0 bulgu | `KANIT/04_koruma_kimlik.json` |
| 5 | Koruma kapısı duyarlılığı — aynı depodan 1 bağımlılık + 2 test + içerik silindi | hepsi `P0`, doğru konumla | `KANIT/05_koruma_mutasyon.json` |

Kendin doğrulamak istersen:

```bash
python3 ARACLAR/betikler/v4_selftest.py        # 36/36 gecmeli, rc=0
python3 ARACLAR/betikler/v4_consistency.py .   # rc=0
python3 ARACLAR/betikler/v4_verify.py . --kanit-dizin ARACLAR/KANIT --muafiyet ARACLAR/MUAFIYET.json
sha256sum -c ARACLAR/SHA256SUMS.txt
```

## 4. BILINEN_SINIRLAR — ölçülmeyenler

```
- ne_olculmedi        : Komut metninin farkli model ailelerinde (GPT, Gemini,
                        Llama, yerel modeller) gercekten ayni davranisi uretip
                        uretmedigi
  hangi_karari_etkiler : "Hangi yapay zekaya yapistirayim" karari
  eksik_kanit         : Cok modelli A/B kosusu yapilmadi; yalniz tek bir model
                        ailesinde tasarlandi ve gozden gecirildi
  siddet              : P1

- ne_olculmedi        : Siniflandiricinin dogruluk orani
  hangi_karari_etkiler : "Tipi elle duzeltmem gerekir mi" karari
  eksik_kanit         : Sabit bir 10 vakalik fikstur seti kosulmadi; karar
                        tablosu tasarim gerekcesiyle savunuluyor, olcumle degil
  siddet              : P1

- ne_olculmedi        : MODE-B'de (yalniz sohbet penceresi) koruma sozlesmesinin
                        hash olmadan ne kadar guvenilir oldugu
  hangi_karari_etkiler : "Betik calistiramadigim ortamda bu araca ne kadar
                        guvenebilirim" karari
  eksik_kanit         : MODE-B davranisi bir modelin talimat takibine baglidir;
                        betikle olculemez. Bu yuzden MODE-B'de nihai durum
                        `OLCULMEDI`dir ve olumlu karar uretilmez
  siddet              : P1

- ne_olculmedi        : Enjeksiyon savunmasinin gercek etkinligi
  hangi_karari_etkiler : "Guvenilmeyen bir metni bu araca verebilir miyim" karari
  eksik_kanit         : Veri siniri bir kalkan degil kayit cihazidir; kalip
                        tabanli dedektorlerin 10 varyanttan 9'unu kacirdigi
                        olculdu. v4 engelleme iddiasinda BULUNMAZ
  siddet              : P1

- ne_olculmedi        : Cok buyuk girdide (200+ sayfa) bagimsiz kor denetimin
                        pratikte kosulup kosulmadigi
  hangi_karari_etkiler : "DENETIM_TIPI: BAGIMSIZ alabilir miyim" karari
  eksik_kanit         : Bagimsiz denetim ikinci bir sohbet gerektirir; kullanici
                        bunu atlarsa rapor OZ_DENETIM olarak kalir - bu bir
                        eksiklik degil, dogru etiketlemedir
  siddet              : P2
```

## 5. İkinci denetim turu (v4.1) — paket kendi disiplininden geçirildi

Teslimden sonra paket, kendi F0→F6 sırasıyla baştan sona denetlendi. **Yedi kusur
bulundu, yedisi de düzeltildi.** İkisi `P0`'dı ve ikisini de paketin *kendi*
kapıları yakaladı — biri kapının kendisindeydi.

| FIX | Şiddet | Kusur | Nasıl bulundu | Düzeltme |
|---|---|---|---|---|
| FIX-001 | `P0` | **Tutarlılık kapısı fail-open.** Kapalı liste değerleri birleştirilmiş çekirdek metninde aranıyordu; bir değer normatif kaynaktan (C1) tamamen silinse bile başka bir çekirdek dosyasında geçtiği için kapı geçiyordu. | Planlı bozma testi: `GRADER_MISCALIBRATED` C1'den silindi, kapı `rc=0` verdi | Kapalı listeler artık **C1'in kendisinde** aranıyor. Regresyon fikstürü: `TUT-2` |
| FIX-006 | `P0` | **C1 kendi iddiasını karşılamıyordu.** "Tek doğruluk kaynağı" diyor ama iş tipi listesi (`KOD`/`GIRISIM`/`BELGE`) içinde yoktu. | FIX-001 sonrası güçlenmiş kapı yakaladı | C1'e §4b "İŞ TİPİ" bölümü eklendi |
| FIX-002 | `P1` | **İlk ekran bütçesi iç çelişkiliydi.** ≤25 satır deniyordu ama bölüm tahsislerinin toplamı zaten 25'i aşıyordu; örnek rapor 33 satırdı. Kendi örneğini ihlal eden kural, kuraldır sayılmaz. | Örnek rapor mekanik olarak ölçüldü | Bütçe ≤32 satır / ≤1800 karakter (tahsis toplamıyla uyumlu); örnek 32 satıra indirildi; kapı artık bunu mekanik denetliyor. Fikstür: `TUT-3` |
| FIX-003 | `P1` | **Aşırı iddia.** §2'nin başlığı "hepsi bir önceki neslin gerçek kodunda çalıştırıldı ve başarılı oldu" diyordu; oysa bazıları v4'ün kendi taslağını kırmıştı, bazılarının v3'te karşılığı yoktu. Kendi 3. kuralımızın ihlali. | İddia-kanıt eşlemesi | **Köken** sütunu eklendi: `v3-ÖLÇÜLDÜ` / `v4-TASLAK` / `ÖNLEM` |
| FIX-005 | `P1` | Öz-testin belge başlığı aynı aşırı iddiayı tekrarlıyordu | Aynı eşleme | Aynı dürüst çerçeveyle değiştirildi |
| FIX-004 | `P1` | **Ölçülmemiş üç iddia.** "Python 3.9+ yeterli" (yalnız 3.11'de koşuldu), "her betik `--help` destekler" (`v4_common` bir kütüphane), çıkış kodu sözleşmesi gerçek davranışla uyuşmuyordu. | Betikler tek tek çalıştırıldı | Üçü de ölçülen gerçeğe göre yazıldı |
| FIX-007 | `P1` | **Gürültülü kapı riski.** Sessiz değer değişimi imzalı beyanla bile `P0` kalıyordu; meşru bir düzeltmede bile engel üretiyordu. Gürültülü kapı bypass edilir. | Paketin kendi düzenlemeleri koruma kapısından geçirildi | İmzalı niyet kaydı şiddeti `P1`'e indiriyor ama bulgu **rapordan silinmiyor** — gerekçe ve imza görünür. Fikstür: `MUT-5` |

**İkinci turda ölçülenler:**

| Ne | Sonuç |
|---|---|
| Öz-test fikstür sayısı | 36 → **39**, hepsi geçiyor |
| Python 3.9 sözdizimi + 3.9 dışı çalışma zamanı API'si | temiz / yok |
| Beş komut betiğinde `--help`, çıkış kodu, başka dizinden çalışma | çalışıyor |
| Bozuk JSON, tuhaf tip, `NaN`, ikili dosya, boş hedef | hepsinde biçimli fail-closed, **traceback yok** |
| 5 MB tek satır / 8000 bölüm | 2,2 sn / 0,6 sn |
| Kodlama, satır sonu, BOM | hepsi UTF-8, CRLF yok, BOM yok |
| Kapılar dekor mu? (kasten bozup öz-test koşuldu) | üçünde de ilgili test **KALDI** — kapılar gerçek |
| Uçtan uca prova: gerçek depo + dikkatsiz "optimizasyon" | sızan anahtar, silinen 9 bölüm, silinen test, kaldırılan bağımlılık — **hepsi yakalandı** |
| Paketin kendi düzenlemeleri koruma kapısından | 206/206 bölüm korundu, 0 kayıp |

## 6. Bu paketin en büyük tek zayıflığı

Betikler (`MODE-A`) ölçer; komut metni (`MODE-B`) yalnızca **talimat verir**.
MODE-B'de hiçbir mekanizma, modelin koruma sözleşmesini gerçekten uyguladığını
zorlamaz — yalnızca uygulamasını ister ve uygulamadığında bunu beyan etmesini
ister. Bu yüzden MODE-B çıktısının nihai durumu asla `TAMAMLANDI` olmaz,
`OLCULMEDI` olur. Bu bir kusur değil, kusurun **dürüst etiketlenmesidir**;
ama kullanıcının bilmesi gereken şey şudur: *ölçüm istiyorsan betikleri
çalıştırabilen bir ortamda çalış.*
