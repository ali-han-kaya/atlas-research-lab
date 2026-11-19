# KFAZ0 — KAPSAM SÖZLEŞMESİ ve KAYIT

Depo: `<yol>` · Giriş modu: `YESIL_SAHA|MEVCUT_KOD` · Tarih: `<ISO-8601>`

## 1. Ne inşa edilecek (2-3 cümle)

## 2. Kabul ölçütleri

Her ölçüt **ölçülebilir** olacak. "Daha hızlı" değil, "p95 < 200ms".
Ölçemeyeceğin bir ölçütü `DOGRULANAMADI` etiketiyle yaz, sessizce yazma.

```json
{
  "sema": "KFAZ0/v1",
  "giris_modu": "MEVCUT_KOD",
  "req": [
    {"id": "REQ-001", "tur": "davranissal", "kabul": "p95 < 200ms (yuk: 100 es zamanli istek)"},
    {"id": "REQ-002", "tur": "yapisal", "kabul": "config okuma tek modulde toplanir"}
  ]
}
```

`tur` yalnız `davranissal` | `yapisal`. **Davranışsal** her REQ, KFAZ1'de tabanda
**olmayan** bir test adına bağlanmak zorundadır (RECK-07).

## 3. Kapsam dışı (açıkça)

## 4. OLCULMEYEN

- **ne_olculmedi:** … **hangi_karari_etkiler:** … **eksik_kanit:** … **siddet:** P0|P1|P2
