# KFAZ2 — DEĞİŞİKLİK MANİFESTİ

```json
{
  "sema": "KFAZ2/v1",
  "chg": [
    {"id": "CHG-001", "req": "REQ-001", "dosya": "src/a.py",
     "durum": "UYGULANMIS", "ozet": "sicak yolda O(n^2) dongu kaldirildi"}
  ]
}
```

`durum` yalnız `UYGULANMIS` | `UYGULANMADI`.
**`UYGULANMIS` bir iddiadır ve denetlenir:** RECK-02, o dosyanın
`git diff`/`git ls-files --others` çıktısında bulunmasını şart koşar.

## Dokunulmayanlar ve nedenleri

## OLCULMEYEN
