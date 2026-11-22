# ACIMASIZ HAKEM — 2 TURLU KOMUT v2
**Düzeltilen:** v1'de tek komut vardı ve "dosyayı oku" diyordu. Web'deki modeller (ChatGPT, Gemini, Claude.ai)
senin diskindeki dosyayı **okuyamaz**. Ayrıca token sınırı yoktu → Opus 191k'da çöktü.
v2'de iki mod var ve okuma bütçesi sınırlı.

---

## HANGİ MODU KULLANACAĞIM?

| Model nerede? | Mod | Ne yapacaksın |
|---|---|---|
| `opencode` / Cursor / Claude Code (terminal) | **MOD A** | Komutu yapıştır, model dosyaları kendi okur |
| ChatGPT, Gemini, Claude.ai, Grok (tarayıcı) | **MOD B** | Komut + **metni de** yapıştır |
| OpenRouter API (dosya erişimi yok) | **MOD B** | Aynı |

---

# MOD A — DOSYA OKUYAN MODELLER (terminal)

Çalışma klasörü: `<CALISMA_TEZGAHI>`

```
SEN: Hakemli bir derginin en acımasız hakemisin. Alanın: İslam Araştırmaları + Karşılaştırmalı Semitik Filoloji. Ahlâk-ı Muhammedî (sıdk, emanet, edep, hilm) ile denetliyorsun. Övgü yok. Sadece kanıtlı eleştiri.

⚠️ OKUMA BÜTÇESİ (kesinlikle aşma — önceki koşu bellek taşmasından çöktü):
SADECE şu 4 dosyayı oku, başka hiçbir şeyi okuma:
1. CIKTI_ALLAHASKI/ALLAHAŞKI_v5.9_FINAL.md
2. CIKTI_ALLAHASKI/BILINEN_SINIRLAR_v5.9.md
3. CIKTI_ALLAHASKI/ILAHIYAT_SON_KONTROL_v5.9.md
4. CIKTI_ALLAHASKI/rapor/NIHAI_RAPOR_v5.9.md

YASAK: yahuditurk/ altındaki PDF'leri açma. portfolyo/ okuma. TRUTH_MAKALE*.md okuma. ATLAS/.opencode okuma. rapor/ klasörünün geri kalanını okuma.

GÖREV — 7 eksenden hakemle. Her eksende en az 1 bulgu ara:
E1 KATKI: Özgün katkı ne? Literatürde zaten var mı? "Asimetrik karşılıklı muhabbet" gerçekten yeni bir kavram mı, yoksa mahabbet literatürünün yeniden adlandırılması mı?
E2 YÖNTEM: Dört seviyeli çerçeve ve H1/H2 testi metodolojik olarak sağlam mı? Null model gerçekten test edildi mi, yoksa sadece beyan mı edildi?
E3 KANIT: Her iddianın kanıtı var mı? Kanıtı olmayan iddiaları satır numarasıyla listele.
E4 KÜNYE: Kaynakçadaki her künyeyi denetle. Şüpheli olanı işaretle. Yapabiliyorsan DOI/CrossRef ile doğrula.
E5 TEOLOJİK RİSK: Tevhid, tenzih, teşbih riski. Gayb konusunda kesin hüküm. Yahudi geleneğine karşı adaletsiz dil.
E6 BİÇİM: APA 7, IMRaD, dil, imlâ, terim tutarlılığı (sekîne/Şekina/sakīna/šəkhīnāh).
E7 DÜRÜSTLÜK DENETİMİ: BILINEN_SINIRLAR_v5.9'da "doğrulanamadı" yazan 13 madde GERÇEKTEN doğrulanamaz mı? Yoksa yazar tembellik mi etti? Kaç tanesini sen doğrulayabilirsin?

KURALLAR:
- Her bulgu: satır no + birebir alıntı + neden + öneri.
- Şiddet: P0 (yayını durdurur) / P1 (düzeltilmeli) / P2 (öneri).
- Kaynak UYDURMA. Emin olmadığında "doğrulayamadım" yaz.
- Hiçbir bulgu bulamadığın eksen varsa "E# temiz" yaz — uydurma bulgu ekleme.

ÇIKTIYI ŞU DOSYAYA YAZ: CIKTI_ALLAHASKI/rapor/TUR1/HAKEM_[MODEL_ADI]_TUR1.md

FORMAT:
# HAKEM RAPORU — [Model] — TUR 1
**Karar:** KABUL | KÜÇÜK REVİZYON | BÜYÜK REVİZYON | RET
**Okunan dosyalar:** (4 dosya)
## P0 Bulgular
| # | Eksen | Satır | Alıntı | Sorun | Öneri |
## P1 Bulgular
(aynı tablo)
## P2 Bulgular
(aynı tablo)
## E7 Dürüstlük Denetimi
13 maddenin her biri için: HAKLI (gerçekten doğrulanamaz) / TEMBELLİK (doğrulanabilirdi)
## En Kritik 3 Düzeltme
## Ahlâk Değerlendirmesi
sıdk / emanet / edep / hilm — her biri için 1 cümle
```

---

# MOD B — TARAYICI MODELLERİ (dosya okuyamaz)

Bu modellere **metni sen vereceksin**. Sıra:

**1)** Aşağıdaki komutu yapıştır.
**2)** Sonra `ALLAHAŞKI_v5.9_FINAL.md` dosyasını aç → **tümünü kopyala** → yapıştır.
**3)** Sonra `BILINEN_SINIRLAR_v5.9.md` → kopyala → yapıştır.
**4)** Gönder.

(3 dosya ≈ 25 bin kelime. Her modern modelin bağlamına sığar.)

```
SEN: Hakemli bir derginin en acımasız hakemisin. Alanın: İslam Araştırmaları + Karşılaştırmalı Semitik Filoloji. Ahlâk-ı Muhammedî (sıdk, emanet, edep, hilm) ile denetliyorsun. Övgü yok. Sadece kanıtlı eleştiri.

Aşağıda bir makale ve sınırlılık belgesi vereceğim. Dosya sistemine erişimin yok — sadece yapıştırdığım metni değerlendir. Yapıştırılmayan bir şeye atıf yapma.

GÖREV — 7 eksenden hakemle:
E1 KATKI: Özgün katkı ne? "Asimetrik karşılıklı muhabbet" gerçekten yeni mi?
E2 YÖNTEM: Dört seviyeli çerçeve ve H1/H2 testi sağlam mı? Null model test edildi mi yoksa beyan mı?
E3 KANIT: Kanıtsız iddiaları bölüm numarasıyla listele.
E4 KÜNYE: Kaynakçadaki künyeleri denetle. Bildiğin hataları söyle. Bilmiyorsan "doğrulayamadım" yaz.
E5 TEOLOJİK RİSK: Tevhid, tenzih, teşbih. Gayb konusunda kesin hüküm. Yahudi geleneğine adaletsiz dil.
E6 BİÇİM: APA 7, IMRaD, dil, terim tutarlılığı.
E7 DÜRÜSTLÜK: "Doğrulanamadı" denen 13 madde gerçekten doğrulanamaz mı, yoksa tembellik mi?

KURALLAR:
- Her bulgu: bölüm/§ no + birebir alıntı + neden + öneri.
- Şiddet: P0 / P1 / P2.
- Kaynak UYDURMA. Emin değilsen "doğrulayamadım".
- Temiz eksen varsa "E# temiz" yaz. Uydurma bulgu ekleme.

FORMAT (markdown ver, ben kopyalayacağım):
# HAKEM RAPORU — [Model] — TUR 1
**Karar:** KABUL | KÜÇÜK REVİZYON | BÜYÜK REVİZYON | RET
## P0 / P1 / P2 Bulgular (tablo: # | Eksen | § | Alıntı | Sorun | Öneri)
## E7 Dürüstlük Denetimi (13 madde: HAKLI / TEMBELLİK)
## En Kritik 3 Düzeltme
## Ahlâk Değerlendirmesi (sıdk/emanet/edep/hilm)

--- MAKALE BAŞLIYOR ---
[BURAYA ALLAHAŞKI_v5.9_FINAL.md'nin TAMAMINI YAPIŞTIR]
--- MAKALE BİTTİ ---

--- SINIRLILIKLAR BAŞLIYOR ---
[BURAYA BILINEN_SINIRLAR_v5.9.md'yi YAPIŞTIR]
--- SINIRLILIKLAR BİTTİ ---
```

---

# TUR 2 — BÜTÜNCÜL İKİNCİ GÖRÜŞ

Tüm TUR 1 raporları toplandıktan sonra, **aynı modellerin her birine** ver:

```
SEN: Aynı acımasız hakemsin. TUR 1'de kendi raporunu yazdın. Şimdi diğer hakemlerin raporlarını da göreceksin ve ikinci görüş vereceksin.

GÖREV:
1. Her hakemin her bulgusunu değerlendir: KATILIYORUM / KATILMIYORUM / KISMEN + gerekçe.
2. Aynı hatayı 3+ hakem bulmuşsa → otomatik P0'a yükselt.
3. Sadece 1 hakem bulmuş ve diğerleri o bölümü temiz demişse → şişirilmiş olabilir, sorgula.
4. Çelişen bulguları çöz: hangi hakem haklı, neden?
5. Kendi TUR 1 kararını gözden geçir. Değiştiysen NEDEN değiştiğini yaz.

ÖNEMLİ: Diğer hakemlere nazik olmak için katılma. Yanlışsa yanlış de.

FORMAT:
# HAKEM RAPORU — [Model] — TUR 2 (BÜTÜNCÜL)
**TUR 1 kararım:** ...
**TUR 2 kararım:** ...  (değiştiyse neden)
## Katılım Tablosu
| Hakem | Bulgu | Şiddet | Görüşüm | Gerekçe |
## Uzlaşılan Bulgular (3+ hakem)
## Tartışmalı Bulgular
## Şişirilmiş Bulgular (elenmesi gerekenler)
## NİHAİ P0 / P1 / P2 LİSTESİ
## En Kritik 3 Düzeltme (öncelik sırası)

--- TUR 1 RAPORLARI BAŞLIYOR ---
[TÜM MODELLERİN TUR 1 MARKDOWN'LARINI ALT ALTA YAPIŞTIR]
--- TUR 1 RAPORLARI BİTTİ ---
```

---

## SENİN ADIMLARIN (en az efor)

**TUR 1**
1. `opencode` ile Opus 5 → **MOD A** komutunu yapıştır → rapor `rapor/TUR1/` içine yazılır
2. Tarayıcıdaki her model için → **MOD B** komutu + makale metni + sınırlılıklar → cevabı `.md` olarak kaydet
3. Tüm TUR 1 raporlarını `rapor/TUR1/` klasöründe topla

**TUR 2**
4. `rapor/TUR1/` içindeki tüm markdown'ları tek metinde birleştir
5. Her modele **TUR 2** komutu + birleşik metni ver
6. Cevapları `rapor/TUR2/` içine kaydet

**BANA GETİR**
7. `rapor/TUR1/` + `rapor/TUR2/` içeriğini bana ver → birleştirip düzeltme planı yapayım

> Az modelle başlamak istersen: 2 model yeter. Getir, ben TUR 2'yi ona göre optimize ederim.

---

## MODEL ÖNERİSİ (çeşitlilik önemli — aynı aileden 2 model benzer körlük yapar)

| Rol | Model | Neden |
|---|---|---|
| Derin analiz | Claude Opus 5 (MOD A) | Uzun bağlam, dosya erişimi, titiz |
| Filoloji/tarih | Gemini 2.5 Pro (MOD B) | Geniş bağlam, karşılaştırmalı literatür |
| Karşı-görüş | GPT-5 / o-serisi (MOD B) | Farklı eğitim → farklı körlük noktaları |
| Sertlik | Grok / DeepSeek R1 (MOD B) | Daha az kibar, daha çok eleştiri |

---

**Koruma:** Son dosya 3 yerde: çalışma kopyası + `BACKUP_v5.9_PROTECTED/` + `~/Documents/ALLAH AŞKI/TESLIM_v5.9/`
Ayrıca git commit `a1a8383` ve `SHA256SUMS.txt` var. Hakemler dosyayı bozamaz.
