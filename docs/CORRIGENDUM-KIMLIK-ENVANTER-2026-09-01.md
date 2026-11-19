# CORRIGENDUM — Kayıt kimliği ve açık envanter ayrımı

Tarih: 1 Eylül 2026

## AMAÇ

Bu not tarihsel kayıtları yeniden adlandırmaz veya silmez. Aynı kısa kimliğin farklı
belgelerde farklı mekanizmalar için kullanılmasından doğan karışıklığı I6 uyarınca
üstten bir düzeltme kaydıyla ayırır.

Bu notta:

- `TT-*`, yalnız `docs/DENETIM-2026-08-31-TAM-TARAMA.md` içindeki kimliğe yapılan
  nitelikli referanstır; eski satırın geriye dönük adı değildir.
- Başka tarihlerde kullanılan çakışan kimlikler, kısa etiketle değil mekanizma adı ve
  commit kimliğiyle anılır.
- Commit varlığı ve dosya kapsamı Git kaydında doğrulanabilir. Çalışma zamanı kapanış
  sonuçları bu belge turunda yeniden çalıştırılmadı; önceki DEVIR/SURUM/DERSLER
  kayıtlarından aktarıldığında `RAPORLANMIŞ KANIT`tır.

## BAĞLAYICI REFERANS KURALI

Yeni kayıtlarda belirsiz `B-9`, `D-1`, `D-2`, `D-3`, `D-4` veya `P1-5` tek başına
kullanılmaz. En az şu üç parçadan ikisi birlikte yazılır:

1. kaynak belge/ad alanı (`TT`, tarihsel SURUM, P1 paketi gibi),
2. mekanizma adı,
3. varsa commit kimliği.

Örnek: `TT-D-2 — budget_guard CWD/proje-adı filtresi`; yalnız `D-2` yazılmaz.

## KAYITLI ON BİR MEKANİZMA KAPANIŞI

Aşağıdaki on bir satır seçili post-tarama commit dizisindeki ayrı mekanizma
kayıtlarıdır. Bu sayı tam açık/kapalı backlog sayısı değildir.

| # | Kanonik mekanizma açıklaması | Tarihsel kısa etiket | Commit |
|---|---|---|---|
| 1 | Etik kimliğinin P0 şiddeti aklamasının engellenmesi | TT-B-1 | `b11ed8f` |
| 2 | `manifest_reconciliation` alanında liste tipinin zorunlu olması | TT-B-2 | `019b7c3` |
| 3 | `null` Gate-2B kökünün REC-05'i atlamasının engellenmesi | TT-B-3 | `ee6c660` |
| 4 | Teslim hash yanlış tipinin temiz TSL-01 ile kapanması | Tam-tarama ek bulgusu | `067af4e` |
| 5 | Etik bekleyişi muafiyetinin yalnız tanınan P1/P2 şiddetlerine açılması | Sonraki kayıttaki `D-1` | `5dbe9bf` |
| 6 | KOD bütçe/katalog ortam-yolu enjeksiyonlarının ikizlere yayılması | Sonraki kayıttaki `D-3` | `119dea5` |
| 7 | İkili/okunamayan imza anahtarı okumasının kontrollü kapanması | Sonraki kayıttaki `D-4` | `0d8327c` |
| 8 | Olumlu KOD fikstürlerinde açık `findings: []` sözleşmesi | `D2-FINDINGS` | `768f099` |
| 9 | K3-1/BG-2 testlerinin canlı bütçe hesabından yalıtılması | K3-1/BG-2 | `b6d097b` |
| 10 | Normalize özdeş Gate-2A/2B girdilerinin FINAL'de fail-closed kapanması | TT-B-7 | `67202b7` |
| 11 | GM-16'nın commitli öz-test envanter pinine alınması | GM-16 pin | `c777160` |

Bu on bir kayıt çalışma zamanı kapanışlarının bu turda yeniden ölçüldüğü anlamına
gelmez. İlgili TDD, I9, selftest, attest ve regresyon sonuçları önceki kayıtlardan
aktarılan `RAPORLANMIŞ KANIT`tır.

## SONRAKİ DÖRT AYRI MEKANİZMA KAYDI

On birli diziden sonra dört ayrı tam-tarama mekanizması daha kayıt altına alınmıştır:

| Nitelikli kimlik | Mekanizma | Commit |
|---|---|---|
| TT-B-4 | CHK-02 durum alanında kapalı küme/tam eşleşme | `35eafea` |
| TT-B-5 | CHK-02 tablo keşfinin PROVENANCE bölümüyle sınırlandırılması | `da0cbd5` |
| TT-C-5 | TR-01 sistem adlarında token-sınır eşleşmesi | `9363a36` |
| TT-B-6 | CHK-01 başlık kimliğinde ayrı başlık/tam kimlik eşleşmesi | `a3bbd63` |

Dolayısıyla `11 kapalı` ifadesi nihai envanter değildir. Seçilen dizide toplam on beş
ayrı mekanizma kaydı vardır; bu da labın bütün backlogunun on beş olduğu anlamına gelmez.

## ÇAKIŞAN D KİMLİKLERİ

| Belirsiz etiket | Sonraki kayıttaki mekanizma | Tam-tarama mekanizması |
|---|---|---|
| `D-1` | Etik şiddet/muafiyet kapalı kümesi (`5dbe9bf`) | TT-D-1: bozuk DB'nin `KISMI:` sonucu ile bütçe kapısını açması |
| `D-3` | KOD ortam-yolu enjeksiyonu (`119dea5`) | TT-D-3: aynı modelin farklı yol biçimleriyle bağımsız sayılması |
| `D-4` | İmza anahtarı okuması (`0d8327c`) | TT-D-4: fiyat bloğu olmayan modelin sıfır fiyatlanması |

`D2-FINDINGS`, olumlu KOD test fikstürlerindeki açık boş bulgu listesi sözleşmesidir.
TT-D-2 ise `budget_guard` CWD alt-dizesi/proje yeniden adlandırması filtresidir.
Birbirlerinin devamı veya kapanışı değildir.

## B-9 VE P1-5 ANLAM AYRIMI

- `SURUM v1.7.27 / B-9`, çok dillilik kırıklarıdır.
- `TT-B-9`, CHK-05 için regresyon testi bulunmamasıdır.
- `AUDIT-v5.5.2 / P1-05`, DOI HTTP hatası ve deterministik DOI seçimidir.
- Eski inşa kaydındaki `P1-5`, `cite_match` kapısına verilen etikettir.
- `P1-PAKET / P1-5`, kanonik `OLGULAR.md` ve ham sayı lint'i önerisidir.

Bu anlamlardan biri diğerini kapatmış sayılmaz.

## GERÇEK AÇIK ENVANTER YAPISI

`docs/DEVIR-2026-09-01-2213.md` dokuz ayrıntılı grup kaydeder:

1. `cite_match`, `quote_ratio`, `declaration_check` zincir bağlantısı; önce
   TT-C-1/TT-C-3 ve TT-E-1/TT-E-2 sertleşmesi.
2. `PIPELINE.md` belge-disk sapması.
3. TT-E-1 beyan alt-dize kaçağı.
4. TT-B-8, TT-B-9 ve TT-B-10 karar katmanı.
5. TT-C-1/3/4/6/7/8/9/11 akademik kapıları; reddedilen TT-C-2/10 yeniden açılmaz.
6. TT-D-2 bütçe/CWD-proje-adı filtresi.
7. TT-D-5/6/7 model ve maliyet denetimi.
8. TT-E-1..7, TT-E-9 ve TT-E-10'un doğrulanan PL-11 yarısı.
9. P1-PAKET/P1-5 kanonik OLGULAR ve ham sayı lint'i; yetkili kapsam kaydı gerekir.

Gruplar bağımsız sayaç değildir: TT-E-1, 1/3/8'in; TT-E-2, 1/8'in;
TT-C-1 ve TT-C-3 ise 1/5'in kesişimindedir.

## BEŞLİ ADAY SEÇİM HAVUZU

`Beş açık` ifadesi diskte doğrudan bir backlog satırı olarak bulunmadı. Aktarılan
bağlam ile son DEVIR'in kesişiminden aşağıdaki dar seçim havuzu çıkarılmıştır:

1. TT-B-8 — FR-6 vacuous `REC-05` yüklemi,
2. TT-B-9 — CHK-05 regresyon testi yokluğu,
3. TT-B-10 — metadata sayaç tiplerinin temiz kapanmaması,
4. TT-D-2 — bütçe CWD/proje-adı filtresi,
5. P1-PAKET/P1-5 — kanonik OLGULAR + ham sayı lint'i.

Bu bölüm `ÇIKARIM`dır; dokuz ayrıntılı grup yerine geçen tam backlog değildir.

## KARAR BEKLEYENLER

- `PASS-PENDING-ETHICS` çıkış kodu ve tüketici politikası.
- Genel etik/N-A şeması: yetkili, kanıt standardı ve PASS bağlantısı.
- P1-PAKET/P1-5 için yetkili kapsam kaydı.

## BU CORRIGENDUMUN DEĞİŞTİRMEDİĞİ ŞEYLER

- Eski DEVIR, DENETIM, SURUM ve DERSLER satırları geriye dönük değiştirilmez.
- Kod, test, `OZTEST-TABAN.json` ve kapı davranışları değişmez.
- Kapalı mekanizmalar yeniden açılmaz.
- TT-B-8 bu belge işine karıştırılmaz; ayrı test işi olarak kalır.

## OLCULMEYEN

- Bu belge turunda ATLAS selftest, attest, KOD selftest, I9 ve regresyon deltası
  yeniden çalıştırılmadı.
- On beş mekanizmanın çalışma zamanı kapanışları yeniden ölçülmedi.
- Beşli seçim havuzunun birebir yazılı birincil satırı bulunmadı; eşleme `ÇIKARIM`dır.
- Canlı DB/HOME/bütçe/CWD, gerçek teslim/MASTER, ikinci model ve ikinci fiziksel makine
  ölçülmedi.
