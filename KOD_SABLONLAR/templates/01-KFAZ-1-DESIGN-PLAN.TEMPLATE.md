# KFAZ1 — TASARIM PLANI ve DONDURMA

## 1. Yaklaşım (2-3 cümle)

## 2. Makine bloğu

```json
{
  "sema": "KFAZ1/v1",
  "degisecek": ["src/a.py"],
  "dondurulan": ["src/kritik_protokol.py"],
  "req_test": {"REQ-001": ["test_p95_yuk_altinda"]},
  "req_dosya": {"REQ-001": ["src/a.py"]},
  "gerekce": {"src/a.py": "REQ-001 sicak yol burada"}
}
```

`degisecek` bir **izin listesidir**: diff'te olup burada olmayan her dosya
`SCOPE_VIOLATION` = P0. Bir dosya hem `degisecek` hem `dondurulan` olamaz.

## 3. Dondurulan bölgeler ve gerekçeleri

## 4. Reddedilen alternatifler (neden değil)

## 5. OLCULMEYEN
