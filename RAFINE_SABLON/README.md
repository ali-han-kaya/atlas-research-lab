# RAFINE_SABLON — zincirin 3. halkası

Sürüm: v1 · Tarih: 23 Ağustos 2026

## Bu klasör ne işe yarar

Zincir üç halkadır:

1. **ATLAS_SABLONLAR/** — sıfırdan üretim (FAZ0→FAZ4, çok ajanlı).
2. **KOMUT_TOOLKIT_v4/** — tek komutla oturum disiplini (F0–F6, C1–C6).
3. **RAFINE_SABLON/** — *elde zaten bir metin varken* onu bir sürüm ileri
   taşımak: asgari müdahale, KEEP koruması, teslim paketi.

3. halka daha önce lab'da yoktu; `isimlendir/` çalışma tezgâhında tek seferlik
komutlar olarak yaşıyordu. Bu klasör o yöntemin **projeden bağımsız** hâlidir.

## Kaynak ve fark

Yöntem `mtrx/isimlendir/OPTIMIZE_KOMUT_V5.9.md` ve `CLAUDE_OPUS5_KOMUT.md`
koşularından çıkarıldı. **Orijinaller dokunulmazdır ve kopyalanmamıştır** —
buradaki dosya, o koşuların proje adlarından arındırılmış şablonudur.

Somut farklar:

- Sabit yollar `{{...}}` yer tutucularına çevrildi.
- Kapanış kontrolüne lab'ın makine denetimleri bağlandı (`check_integrity.sh`,
  `cite_match.py`, `fix_reconcile.py`).
- KEEP listesi ayrı bir şablona ayrıldı; sayı elle değil dosyadan gelir.

## Nasıl kullanılır

1. `KEEP-LISTESI-TEMPLATE.md`'yi projenin çalışma klasörüne kopyala, doldur.
2. `RAFINE_KOMUT_SABLONU.md`'deki `{{...}}` alanlarını doldur.
3. Kod bloğunu ajana yapıştır.
4. Bitişte `KAPANIS_KONTROL.md`'yi sırayla işaretle.

## Sınır

Bu şablon **yeni iddia üretmez**. Yeni bölüm/iddia gerekiyorsa iş 3. halka
değildir; `ATLAS_SABLONLAR/` FAZ0'dan başlanır.
