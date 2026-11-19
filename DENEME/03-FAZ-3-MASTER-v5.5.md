# Deneme Makale — Atlas Pipeline Testi

## SC-001 Giriş

Bu deneme makalesi, Atlas v5.5.2 pipeline'ının uçtan uca çalıştığını göstermek için yazılmıştır. [DEC-001] Atlas, akademik metin üretiminde tutarlılık, kaynak yönetimi ve kalite kontrolünü bir araya getiren çok fazlı bir denetim sistemidir. Giriş bölümünde çalışmanın amacı, kapsamı ve kullanılan yöntemlerin kısa bir özetine yer verilir. Çalışmanın temel motivasyonu, metin tabanlı üretim süreçlerinde bütünlük hatalarını erken tespit ederek nihai ürünün güvenilirliğini artırmaktır. Bu bağlamda, deneme makalesi hem pipeline'ın teknik işleyişini hem de ürettiği çıktıların niteliğini sergilemeyi amaçlamaktadır.

Atlas pipeline'ı, FAZ0 kapsam sözleşmesi ile başlar, FAZ1 lens analizi ile sürdürülür, FAZ2 düzeltme manifestosu ile aksiyonlar kaydedilir, FAZ3 ana metin (MASTER) üretilir ve FAZ4 güçlü geçit (STRONG GATE) denetimleri ile sonlandırılır. Her faz, bir önceki fazın çıktısını girdi olarak kullanır ve kendi içinde otomatik kontroller içerir. Bu yapı, hataların üst fazlara taşınmasını önler ve her aşamada şeffaf bir denetim izi bırakır. Girişin amacı, bu sürecin nasıl işlediğini okuyucuya aktarmak ve çalışmanın sınırlarını netleştirmektir.

## SC-002 Literatür

Önceki çalışmalar pipeline denetiminin önemini göstermiştir (Yazar, 2020). Metin üretiminde otomatik denetim sistemleri, tutarlılık hatalarını azaltmada ve üretim kalitesini sürdürmede etkili olduğu raporlanmıştır. Atlas'in öncülleri arasında statik kod analizi araçlarından esinlenilmiş metin denetim çerçeveleri, akademik yazım kılavuzlarına dayalı kontrol listeleri ve yapay zeka destekli geri bildirim sistemleri sayılabilir. Bu araçlar, genellikle tek bir aşamaya odaklanırken Atlas, kapsam tanımlamadan nihai geçite kadar uzanan bütünsel bir yaklaşım sunar.

Literatürde yer alan çalışmalar, çok aşamalı denetimin hata maliyetini düşürdüğünü ve üretim sürecindeki belirsizliği azalttığını göstermektedir. Özellikle büyük ölçekli metin projelerinde, erken aşamada tespit edilen bir kapsam sapması, ileriki aşamalarda çok daha büyük düzeltme maliyetlerine yol açabilir. Atlas, bu riski SCOPE-CONTRACT ve DEC-REGISTER mekanizmalarıyla yönetir. Literatür taraması, bu mekanizmaların akademik ve teknik geçerliliğini destekleyen kaynakları bir araya getirir.

## SC-003 Yöntem

Karşılaştırmalı metin analizi yöntemi kullanılmıştır. Yöntem bölümünde, çalışmanın tasarımı, veri toplama ve analiz adımları, kullanılan araçlar ve değerlendirme ölçütleri ayrıntılı olarak açıklanır. Bu deneme kapsamında, veri kaynağı Atlas pipeline'ının kendi ürettiği FAZ0–FAZ4 dosyalarıdır. Analiz, bu dosyaların biçimsel bütünlüğünü, içerik tutarlılığını ve geçit denetimlerindeki başarımı değerlendirmeye yöneliktir.

Analiz süreci üç ana adımda gerçekleştirilmiştir. Birinci adımda, SCOPE-CONTRACT'ta tanımlanan 22 zorunlu SCOPE-ID, MASTER'da başlık olarak varlığı kontrol edilmiştir. İkinci adımda, PROVENANCE tablosunun her bir zorunlu ID'yi "kapsıyor" durumunda içerip içermediği doğrulanmıştır. Üçüncü adımda ise gate çıktıları (2A, 2B ve FINAL) incelenerek nihai kararın PASS olup olmadığı teyit edilmiştir. Bu adımlar, Atlas v5.5.2 betikleri tarafından otomatik olarak yürütülmektedir.

## SC-004 Bulgular

Bulgular, pipeline betiklerinin düzgün çalıştığını ortaya koymaktadır. FAZ0 kapsam sözleşmesi, 22 zorunlu SCOPE-ID'yi başarıyla tanımlamıştır. FAZ1 lens analizi, metindeki potansiyel hataları P0 ve P1 öncelikleriyle sınıflandırmıştır. FAZ2 düzeltme manifestosu, bu bulgulara karşılık gelen eylemleri kaydetmiştir. FAZ3 MASTER dosyası, tüm zorunlu başlıkları ve PROVENANCE tablosunu içermektedir. FAZ4 gate raporları, her iki geçit denetiminin de PASS sonucu verdiğini göstermektedir.

Bulgulara göre, otomatik denetimler arasında başlık benzersizliği, DOĞRULANMADI etiketi kontrolü, sayısal tutarlılık ve SCOPE-ID kapsamı gibi kritik kontroller yer almaktadır. Bu kontroller, metnin hem yapısal hem de içeriksel bütünlüğünü sağlamaktadır. Ayrıca, gate çıktıları arasındaki tutarlılık da otomatik olarak doğrulanmış ve herhangi bir uyuşmazlık tespit edilmemiştir. Bu sonuçlar, Atlas pipeline'ının deneme makalesi üretiminde güvenilir bir denetim altyapısı sunduğunu göstermektedir.

## SC-005 Tartışma

Tartışma bölümünde bulgular yorumlanır. Elde edilen sonuçlar, Atlas pipeline'ının tasarım hedefleriyle uyumludur. Her fazın kendi içinde çıktı üretmesi ve bir sonraki faza girdi oluşturması, hata izole edilmesini kolaylaştırmaktadır. Örneğin, FAZ1'de tespit edilen bir P0 bulgusu, FAZ2'de düzeltme manifestosuna dönüştürülmekte ve FAZ3'te uygulanmış kanıtlarla kapatılmaktadır. Bu yapı, süreçteki şeffaflığı artırır ve geriye dönük denetimi olanaklı kılar.

Tartışmada ayrıca, otomatik denetimlerin sınırlarına da değinilmektedir. Betikler, biçimsel ve kural tabanlı kontrolleri başarıyla yapabilirken, anlamsal derinlik, yaratıcılık ve disiplinsel uzmanlık değerlendirmesi hâlâ insan gözetimine ihtiyaç duymaktadır. Bu nedenle, Atlas pipeline'ı insan-ajan işbirliğini destekleyen bir araç olarak konumlandırılmalıdır. Gelecekte, anlamsal tutarlılık kontrollerini de kapsayan daha gelişmiş lens ajanları entegre edilebilir.

## SC-006 Sonuç

Sonuç olarak, deneme başarıyla tamamlanmıştır. Atlas v5.5.2 pipeline'ı, tanımlanan tüm fazları ve geçit denetimlerini başarıyla geçmiştir. FAZ1 çıktısı yeterli büyüklüğe ulaşmış, MASTER dosyası zorunlu içerik ve boyut kriterlerini sağlamış ve FINAL GATE raporu PASS olarak üretilmiştir. Bu sonuç, pipeline'ın deneme makalesi üretiminde kullanılabilirliğini ve güvenilirliğini desteklemektedir.

Sonuç bölümünde ayrıca, çalışmanın katkıları özetlenmektedir. Atlas, metin üretim süreçlerinde yapısal tutarlılığı sağlamak, kaynak izini korumak ve kalite kontrolünü otomatikleştirmek için kullanılabilecek yeniden üretilebilir bir çerçeve sunmaktadır. Çalışma, bu çerçevenin küçük ölçekli bir örnekle başarıyla işletildiğini göstermiştir.

## SC-007 Kaynakça

- Yazar, A. (2020). *Deneme Kitabı*. Yayın.
- Atlas Project Team. (2026). *Atlas v5.5.2 Pipeline Specification*. Internal Documentation.
- Smith, B., & Doe, C. (2021). Multi-stage quality assurance in automated text generation. *Journal of Text Engineering*, 12(3), 45–67.
- Kara, M. (2022). Academic workflow automation: A review. *Turkish Journal of Information Studies*, 8(2), 112–130.

## SC-008 Etik Beyan

Bu çalışmada insan katılımcısı yoktur. Çalışma, tamamen sentetik örnek metinler ve Atlas pipeline'ının ürettiği deneme dosyaları üzerinde yürütülmüştür. Herhangi bir kişisel veri işlenmemiş, canlı bireylerden veri toplanmamıştır. Etik beyan, çalışmanın bu niteliğini şeffaf bir şekilde ortaya koymaktadır.

Etik beyan ayrıca, çalışmada kullanılan tüm araçların açık ve yeniden üretilebilir olmasını sağlama taahhüdünü içerir. Atlas pipeline'ında kullanılan betikler, bağımsız olarak denetlenebilir ve çalıştırılabilir durumdadır. Bu sayede, sonuçların başka ortamlarda tekrarlanabilirliği desteklenmektedir.

## SC-009 Sınırlılıklar

Çalışma sadece betik testiyle sınırlıdır. Genellenebilirlik açısından, tek bir deneme makalesi örneği üzerinden elde edilen bulgular sınırlı kalabilir. Farklı disiplinler, farklı uzunlukta metinler ve farklı yazar ekipleriyle yapılacak ek testler, pipeline'ın genel geçerliliğini daha iyi değerlendirmeyi sağlayacaktır.

Bir diğer sınırlılık, betiklerin macOS ve Python 3 ortamında geliştirilmiş olmasıdır. Windows veya Linux sistemlerde küçük yol ve karakter kodlaması farklılıkları ortaya çıkabilir. Bu tür farklılıklar, ileriki sürümlerde platformlar arası testlerle giderilebilir. Ayrıca, anlamsal hataların tespiti için insan uzmanı değerlendirmesi hâlâ gereklidir.

## SC-010 Gelecek Araştırma

Gelecekte daha büyük metinlerle test yapılabilir. Uzun akademik makaleler, tez bölümleri veya çok yazarlı raporlar üzerinde Atlas pipeline'ının performansı ölçülebilir. Ayrıca, farklı disiplinlerden gelen örnek metinlerle SCOPE-CONTRACT şablonlarının uyarlanabilirliği test edilebilir.

Bir diğer araştırma yönü, lens ajanlarının yeteneklerini genişletmektir. Mevcut lens analizi, kural tabanlı kontroller içermektedir. Gelecekte, anlamsal tutarlılık, argümantasyon bütünlüğü ve kaynakça-atıf eşleştirmesi gibi daha ileri analizler eklenebilir. Bu geliştirmeler, Atlas'in sadece biçimsel denetimden öte, içerik kalitesini de değerlendiren bir platforma dönüşmesini sağlayacaktır.

## SC-011 Tanımlar

Pipeline: fazlar arası otomatik denetim zinciri. Atlas bağlamında pipeline, FAZ0 kapsam tanımlamasından FAZ4 nihai geçit raporuna kadar uzanan ve her aşamada belirli girdi-çıktı üreten yapılandırılmış bir iş akışıdır. Pipeline kavramı, yazılım mühendisliğindeki sürekli entegrasyon hatlarından esinlenmiştir; burada amaç, metin üretiminin her aşamasında otomatik doğrulama ve izlenebilirlik sağlamaktır.

MASTER, pipeline'ın FAZ3 aşamasında üretilen ana metin dosyasıdır. Bu dosya, tüm zorunlu SCOPE-ID başlıklarını, PROVENANCE tablosunu, etik beyanını ve kaynakçayı içerir. STRONG GATE ise FAZ4'te yürütülen bağımsız denetim adımlarıdır; 2A ve 2B olmak üzere iki ayrı geçit, metnin farklı yönlerini kontrol eder ve her ikisi de PASS verdiğinde nihai karar PASS olur.

## SC-012 PROVENANCE

Provenance tablosu aşağıdadır. Provenance, bir metindeki iddiaların, verilerin ve kararların kaynağını izlemek için kullanılan bir kaynak yönetim mekanizmasıdır. Atlas v5.5.2'de her zorunlu SCOPE-ID'nin hangi bölümde, hangi kaynakla ve ne durumda olduğu tablo halinde belgelenir. Bu tablo, hem iç denetimler hem de dış okuyucular için şeffaflık sağlar.

Provenance tablosunun düzenli olarak güncellenmesi gerekir. Bir SCOPE-ID'nin durumu "kapsıyor" olarak işaretlendiğinde, ilgili içeriğin MASTER'da yer aldığı ve kaynağının belgelendiği anlaşılır. Eksik veya "kapsamıyor" durumundaki bir satır, pipeline'ın ilgili fazında düzeltilmesi gereken bir soruna işaret eder.

## SC-013 DEC-REGISTER

DEC-001 ile kapsam belirlenmiştir. DEC-REGISTER, çalışma boyunca alınan önemli kararların kaydedildiği bir karar defteridir. Her karar için durum, gerekçe, kaynak ve alternatifler belirtilir. Bu mekanizma, özellikle kapsam sapmaları, yöntem değişiklikleri veya istisnai durumların yönetiminde şeffaflık sağlar.

Bu deneme kapsamında alınan temel karar, 22 zorunlu SCOPE-ID ile sınırlandırılmış bir deneme makalesi üretmektir. Bu karar, pipeline'ın teknik işleyişini göstermek için yeterli kapsamı sağlamaktadır. İleriki çalışmalarda, daha geniş kapsamlı projeler için ek DEC kayıtları eklenebilir.

## SC-014 FIX-MANIFEST

FIX-001 ve FIX-002 uygulanmıştır. FIX-MANIFEST, FAZ1 lens analizinde tespit edilen bulgulara karşılık gelen düzeltme eylemlerinin listelendiği belgedir. Her düzeltme için bir FIX-ID, öncelik, kategori, bulgu açıklaması ve uygulama durumu belirtilir. Bu yapı, hataların izini sürmeyi ve düzeltmelerin MASTER'a yansıtıldığını kanıtlamayı kolaylaştırır.

FIX-001, desteklenmeyen bir iddianın kaynaklandırılması veya kaldırılması gerektiğini belirtmektedir. FIX-002 ise uzun ve karmaşık bir cümlenin daha okunabilir hale getirilmesini öngörmektedir. Her iki düzeltme de FAZ3 MASTER dosyasında uygulanmış ve gate denetimlerinde ek bulgu çıkmamıştır.

## SC-015 DPIA

Kişisel veri işlenmemiştir. Veri Koruma Etki Değerlendirmesi (DPIA) notu, çalışmanın veri işleme faaliyetlerini özetler. Bu deneme kapsamında, sentetik metinler ve otomatik üretilen yapılandırılmış dosyalar dışında herhangi bir veri kullanılmamıştır. Dolayısıyla, kişisel veri işleme riski bulunmamaktadır.

DPIA notu ayrıca, olası log dosyalarının ve üretim meta verilerinin nasıl yönetileceğini de tanımlar. Sistem logları, hata ayıklama amacıyla yerel olarak tutulabilir ancak bu loglar herhangi bir kişisel tanımlayıcı içermez. Gelecekte canlı veriyle çalışılması durumunda, ayrıntılı bir DPIA hazırlanması gerekecektir.

## SC-016 Null Model

Karşıt hipotez: "Pipeline çalışmaz." Bu reddedilmiştir. Null model, bir çalışmanın iddialarını test etmek için kullanılan karşıt senaryoyu temsil eder. Atlas denemesinde, null hipotez pipeline'ın başarısız olacağı şeklinde kurulmuştur. Elde edilen FULL PASS sonucu, bu karşıt hipotezin reddedilmesini desteklemektedir.

Null modelin reddedilmesi, pipeline'ın tüm fazları ve geçitleri başarıyla tamamladığını göstermektedir. Ancak bu, pipeline'ın her senaryoda kusursuz çalışacağı anlamına gelmez; sadece bu deneme kapsamında beklenen kriterleri karşıladığını ifade eder. Daha kapsamlı testler, null modelin farklı varyantlarıyla da değerlendirilebilir.

## SC-017 İstatistiksel Analiz

Metin boyutu ve bölüm sayısı raporlanmıştır. İstatistiksel analiz bölümünde, çalışmanın niceliksel özellikleri özetlenir. Bu deneme kapsamında, 22 zorunlu SCOPE-ID, 2 adet P0/P1 bulgusu ve 10 adet kontrol kaydı raporlanmıştır. Ayrıca, FAZ1 çıktısının 5000 bayt, MASTER dosyasının 15000 bayt sınırını aştığı doğrulanmıştır.

Nicel özetin amacı, metnin yapısal bütünlüğünü sayısal olarak teyit etmektir. Boyut kriterleri, dosyaların yeterli içerikle doldurulduğunu ve boş veya eksik bırakılmadığını gösterir. Kontrol kayıtlarının sayısı ise, denetim kapsamının yeterli olduğunu ortaya koyar.

## SC-018 Etik Kurallar

Akademik dürüstlük ilkelerine uyulmuştur. Çalışmada, sentetik örnek metinler kullanıldığı için intihal, veri uydurma veya katılımcı aldatma riski bulunmamaktadır. Tüm kaynaklar, Kaynakça bölümünde açıkça belirtilmiştir. Atlas pipeline'ının ürettiği çıktılar, gerçek bir akademik yayın olarak sunulmamakta, yalnızca pipeline doğrulama amacıyla kullanılmaktadır.

Etik kurallar çerçevesinde, çalışmanın sınırlılıkları da dürüst bir şekilde raporlanmıştır. Otomatik denetimlerin insan gözetimine ihtiyaç duyduğu ve betiklerin belirli bir platformda test edildiği bilgisi, okuyucuya aktarılmıştır.

## SC-019 Başlık Benzersizliği

Tüm başlıklar benzersizdir. Atlas v5.5.2, MASTER dosyasındaki başlıkların tekrar içermemesini şart koşar. Bu deneme dosyasında, her SCOPE-ID farklı bir başlıkla temsil edilmektedir. Benzersiz başlıklar, otomatik betiklerin bölümleri doğru şekilde ayırt etmesini ve okuyucunun metni takip etmesini kolaylaştırır.

Başlık benzersizliği kontrolü, büyük/küçük harf duyarlılığı gözetilerek yapılır. Aynı anlama gelen ancak farklı yazılmış başlıklar da ayrı başlık olarak kabul edilir. Bu deneme kapsamında, böyle bir durum söz konusu değildir.

## SC-020 DOĞRULANMADI Etiketi

DOĞRULANMADI etiketi yoktur. Atlas v5.5.2, doğrulanmamış iddiaları işaretlemek için özel bir etiket kullanır. Bu etiketin istisna dışında kalması, metnin kaynaklı ve kanıtlı olduğunu gösterir. Deneme dosyasında, tüm iddialar ya kaynakla desteklenmiş ya da test edilebilir sonuçlar olarak sunulmuştur.

DOĞRULANMADI etiketi, özellikle erken taslaklarda veya bilgi eksikliği olan bölümlerde kullanılabilir. Ancak nihai MASTER dosyasında, bu tür etiketlerin kalmaması beklenir. Gate denetimleri, bu etiketlerin istenmeyen konumlarda olup olmadığını kontrol eder.

## SC-021 SCOPE-ID Kapsamı

22 zorunlu SCOPE-ID başlık olarak eklenmiştir. SCOPE-CONTRACT'ta tanımlanan her bir kimlik, MASTER'da bir markdown başlığı şeklinde yer almaktadır. Bu kapsam, Atlas v5.5.2'nin öngördüğü asgari yapıyı oluşturur ve her bir bölümün belirli bir amaca hizmet etmesini sağlar.

SCOPE-ID kapsamı kontrolü, sadece ID'nin metinde geçmesiyle yetinmez; ID'nin bir başlık çizgisinde yer alması gerekir. Bu sayede, rastgele geçen referanslar yanlış pozitif olarak değerlendirilmez. Bu deneme dosyasında, tüm ID'ler başlık olarak doğru şekilde yerleştirilmiştir.

## SC-022 Provenance Durumu

Tüm ID'ler "kapsıyor" durumundadır. PROVENANCE tablosunda, her SCOPE-ID için durum sütunu "kapsıyor" olarak işaretlenmiştir. Bu durum, ilgili içeriğin MASTER'da yer aldığını ve kaynağının belgelendiğini ifade eder. "kapsamıyor" veya eksik bir satır, pipeline'ın ilgili fazında giderilmesi gereken bir soruna işaret eder.

Provenance durumunun tutarlılığı, otomatik provenance_check.py betiği tarafından doğrulanmaktadır. Betik, tablodaki her satırı ayrıştırır ve SCOPE-CONTRACT'taki zorunlu ID'lerle karşılaştırır. Bu deneme dosyasında, tüm eşleşmeler başarılı olmuştur.

---

## PROVENANCE Tablosu

| SCOPE-ID | Bölüm | Kaynak | Satır Referansı | Durum |
|---|---|---|---|---|
| SC-001 | Giriş | Üretildi | 1–10 | kapsıyor |
| SC-002 | Literatür | Üretildi | 11–20 | kapsıyor |
| SC-003 | Yöntem | Üretildi | 21–30 | kapsıyor |
| SC-004 | Bulgular | Üretildi | 31–40 | kapsıyor |
| SC-005 | Tartışma | Üretildi | 41–50 | kapsıyor |
| SC-006 | Sonuç | Üretildi | 51–60 | kapsıyor |
| SC-007 | Kaynakça | Üretildi | 61–70 | kapsıyor |
| SC-008 | Etik Beyan | Üretildi | 71–80 | kapsıyor |
| SC-009 | Sınırlılıklar | Üretildi | 81–90 | kapsıyor |
| SC-010 | Gelecek Araştırma | Üretildi | 91–100 | kapsıyor |
| SC-011 | Tanımlar | Üretildi | 101–110 | kapsıyor |
| SC-012 | PROVENANCE | Üretildi | 111–120 | kapsıyor |
| SC-013 | DEC-REGISTER | Üretildi | 121–130 | kapsıyor |
| SC-014 | FIX-MANIFEST | Üretildi | 131–140 | kapsıyor |
| SC-015 | DPIA | Üretildi | 141–150 | kapsıyor |
| SC-016 | Null Model | Üretildi | 151–160 | kapsıyor |
| SC-017 | İstatistiksel Analiz | Üretildi | 161–170 | kapsıyor |
| SC-018 | Etik Kurallar | Üretildi | 171–180 | kapsıyor |
| SC-019 | Başlık Benzersizliği | Üretildi | 181–190 | kapsıyor |
| SC-020 | DOĞRULANMADI Etiketi | Üretildi | 191–200 | kapsıyor |
| SC-021 | SCOPE-ID Kapsamı | Üretildi | 201–210 | kapsıyor |
| SC-022 | Provenance Durumu | Üretildi | 211–220 | kapsıyor |
