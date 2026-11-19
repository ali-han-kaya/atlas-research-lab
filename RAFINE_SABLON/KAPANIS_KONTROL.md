# KAPANIŞ KONTROL — teslim öncesi

Her madde ya `[x]` ya da `[ ] + gerekçe`. Boş bırakılan madde teslimi durdurur.

## A. Koruma
- [ ] KEEP listesindeki madde sayısı = çıktıdaki eşleşme sayısı (sayıyı yaz: __/__)
- [ ] Kilitli blokların SHA256'sı bazla aynı
- [ ] İlan edilmiş sınırlar korundu, hiçbiri sessizce kapatılmadı

## B. İçerik
- [ ] Yeni iddia eklenmedi (eklendiyse listele)
- [ ] Her değişiklik FIX-MANIFEST'te kanıtlı
- [ ] "Doğrulanamadı" etiketleri yerinde

## C. Makine denetimi (çıktıyı yapıştır)
- [ ] `cite_match.py` → PASS · çıktı: ______
- [ ] `check_integrity.sh --faz3` → PASS · çıktı: ______
- [ ] `fix_reconcile.py` → PASS · çıktı: ______

## D. Ölçüm
- [ ] Kelime sayısı yeniden ölçüldü: ______ (önceki: ______)
- [ ] Sayfa/bölüm sayısı yeniden ölçüldü: ______

## E. Rapor
- [ ] BEYAN ve DOĞRULAMA ayrı başlıklarda
- [ ] "Doğrulanamadı" listesi raporda var
- [ ] Koşu kimliği her artefaktta aynı
