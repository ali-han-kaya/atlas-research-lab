# RAFİNE KOMUT ŞABLONU — sürüm yükseltme (asgari müdahale)

Yer tutucuları doldur, aşağıdaki kod bloğunu ajana yapıştır.

| Yer tutucu | Açıklama | Örnek |
|---|---|---|
| `{{PROJE_KOK}}` | çalışma klasörünün tam yolu | `/Users/.../CIKTI_X` |
| `{{GIRDI}}` | yükseltilecek dosya | `MAKALE.md` |
| `{{GIRDI_SURUM}}` | girdi sürümü + kelime sayısı | `v5.8, 5635 kelime` |
| `{{CIKTI}}` | üretilecek dosya | `MAKALE_v5.9_FINAL.md` |
| `{{HEDEF}}` | teslim hedefi | `Hakemli dergi, İMRaD, APA7` |
| `{{KEEP_DOSYA}}` | KEEP listesi dosyası | `KEEP-LISTESI.md` |
| `{{SINIR_DOSYA}}` | bilinen sınırlar dosyası | `BILINEN_SINIRLAR.md` |
| `{{KOSU_KIMLIGI}}` | koşu kimliği | `PROJE-2026-08-23-v5.9` |
| `{{DOGRULANAMAYAN}}` | "doğrulanamadı" kalacak kaynaklar | `D4: Beydavi, Taberi` |

---

```
GÖREV: {{GIRDI}} dosyasını teslim sürümüne yükselt.
AHLAK: Ahlâk-ı Muhammedî — sıdk, emanet, edep, hilm. Yaptığını gizleme,
yapmadığını yaptım deme.

KONUM: {{PROJE_KOK}}/{{GIRDI}} ({{GIRDI_SURUM}})
HEDEF: {{HEDEF}}

FAZ 0 — OKU (silme yok, yazma yok, sadece oku):
1. {{PROJE_KOK}}/{{GIRDI}} (tamamı)
2. {{PROJE_KOK}}/{{KEEP_DOSYA}} — korunacak parçaların listesi
3. {{PROJE_KOK}}/{{SINIR_DOSYA}} — ilan edilmiş sınırlar
4. Varsa önceki denetim raporları (rapor/, gate/)
5. AI_ARASTIRMA_LABI/ATLAS_SABLONLAR/AGENTS.md — üretim disiplini
FAZ 0 çıktısı: okuduklarının 10 satırlık özeti. Okumadığını okudum deme.

FAZ 1 — PLAN (tek satır bile yazmadan önce planı yaz):
- Ne KORUNACAK: {{KEEP_DOSYA}}'daki her madde tek tek işaretlenir.
- Ne DEĞİŞECEK: madde madde, gerekçesiyle.
- Ne ÖLÇÜLMEDİ: açıkça yaz; tahmini ölçüm diye sunma.
- {{DOGRULANAMAYAN}} nasıl "doğrulanamadı" kalacak?
- Kullanıcı onayı olmadan FAZ 2'ye geçme.

FAZ 2 — İNŞA (asgari müdahale ilkesi):
- Yalnız dil, akış, noktalama, tutarlılık. YENİ İDDİA EKLEME.
- Yeni bölüm, yeni tablo, yeni kaynak ekleme — istenmedikçe.
- İlan edilmiş sınırları {{SINIR_DOSYA}}'da KORU; kapatma.
- Kaynakça biçimi tek olsun; atıf-kaynakça %100 eşleşsin.
- Her değişikliği FIX-MANIFEST ve PROVENANCE'a yaz; kanıtsız değişiklik yok.

FAZ 3 — KONTROL (makineyle, beyanla değil):
- KAPANIS_KONTROL.md'deki maddeleri sırayla [x] yap.
- Şu betikleri çalıştır ve ÇIKTILARINI RAPORA YAPIŞTIR:
    python3 scripts/cite_match.py --dosya {{CIKTI}}
    bash scripts/check_integrity.sh --faz3      (Atlas düzeni varsa)
    python3 ../KOMUT_TOOLKIT_v4/ARACLAR/betikler/v4_preserve.py {{PROJE_KOK}}/{{GIRDI}} {{PROJE_KOK}}/{{CIKTI}} --sessiz
- KEEP sayısı: {{KEEP_DOSYA}}'daki madde sayısı ile çıktıdaki eşleşme sayısını
  KARŞILAŞTIR; eşit değilse teslim etme.
- Kelime/sayfa sayısını yeniden ÖLÇ; önceki sayıyı kopyalama.

TESLİM:
- Dosya: {{PROJE_KOK}}/{{CIKTI}}
- Rapor: {{PROJE_KOK}}/rapor/NIHAI_RAPOR_{{KOSU_KIMLIGI}}.md
- Koşu Kimliği: {{KOSU_KIMLIGI}}
- Raporda BEYAN ile DOĞRULAMA ayrı başlık altında yazılır.

YASAKLAR:
- Halüsinasyon yok. Uydurma sayfa, uydurma atıf, uydurma DOI yok.
- "Doğrulanamadı"yı "doğrulandı" yapma.
- Üstünlük dili yok; saygılı karşılaştırma.
- Orijinal/kilitli dosyaları değiştirme; yalnız {{CIKTI}} üretilir.

ARAÇLAR: dosya_okuma=EVET, kod_calistirma=EVET, ag_erisimi=EVET (DOI doğrulama)
```
