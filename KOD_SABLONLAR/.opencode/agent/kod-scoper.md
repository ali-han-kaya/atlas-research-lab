---
description: KFAZ0 — kapsam, kabul olcutu, taban cizgisi ve dis imza envanteri
mode: subagent
model: openrouter/deepseek/deepseek-v4-pro
permission:
  edit:
    "*": deny
    "_KOSU/00-*": allow
    "**/_KOSU/00-*": allow
    "_KOSU/gate/BASELINE.json": allow
    "**/_KOSU/gate/BASELINE.json": allow
    "kod_profil.json": allow
  bash:
    "*": allow
    "git commit*": deny
    "git push*": deny
    "opencode*": deny
    "*opencode *": deny
    "*kos_faz.sh*": deny
  webfetch: deny
  websearch: deny
  task: deny
---

# KFAZ0 — KAPSAM & KABUL

Üç artefakt üretirsin. Üçü de olmadan hat başlayamaz.

## 1. `_KOSU/00-KFAZ-0-SPEC-CONTRACT-ve-REGISTER.md`

Gövdesinde **zorunlu** makine bloğu:

````
```json
{
  "sema": "KFAZ0/v1",
  "giris_modu": "YESIL_SAHA|MEVCUT_KOD",
  "req": [
    {"id": "REQ-001", "tur": "davranissal", "kabul": "olculebilir kabul olcutu"},
    {"id": "REQ-002", "tur": "yapisal",     "kabul": "..."}
  ]
}
```
````

`tur` yalnız `davranissal` veya `yapisal` olabilir. **Davranışsal** olan her REQ
KFAZ1'de tabanda **olmayan** bir test adına bağlanmak zorundadır (`RECK-07`);
bunu bilerek etiketle, "her şeye davranışsal" demek sonraki fazı kilitler.

Kabul ölçütü **ölçülebilir** olacak: "daha hızlı" değil, "p95 < 200ms".
Ölçemeyeceğin bir kabul ölçütü yazma; yazarsan `DOGRULANAMADI` etiketiyle yaz.

## 2. `_KOSU/gate/BASELINE.json` — taban çizgisi

`MEVCUT_KOD` modunda taban **gerçek ölçümle** dolar. `YESIL_SAHA` modunda
sıfırlarla dolar ama **alanlar yine yazılır** — eksik alan `CALISTIRILMADI`dır.

```
python3 -c "import json,sys;print('taban semasi hazir')"
```

```json
{
  "mod": "MEVCUT_KOD",
  "olculdu": "<ISO-8601>",
  "test": {"kosan": 0, "basarisiz": 0, "hata": 0, "atlanan": 0, "kapsam_yuzde": null},
  "test_adlari": [],
  "test_komutu_cikis_kodu": null,
  "kod_profil_yolu": "kod_profil.json",
  "kod_profil_sha256": "<sha256>",
  "scripts_sha256": {"scripts/chg_reconcile.py": "<sha256>"},
  "dondurulan": {},
  "dis_imza": [],
  "olculmeyen": []
}
```

Tabanı **ölçerek** doldur: test komutunu çalıştır, çıkış kodunu ve JUnit XML'i
kaydet, SHA256'ları hesapla. Ölçemediğin her alan `olculmeyen` dizisine
gerekçesiyle girer. Boş bırakılmış alan sessizce "sıfır" sayılmaz.

> **ÜÇ ALAN PAZARLIK KONUSU DEĞİL — üçü de artık P0'dır (ÖLÇÜM-02 K11/K12).**
> İlk canlı koşuda bu taban `{"sha256": {...}}` biçiminde yazıldı; alan adları
> tutmadığı için **hiçbir hash karşılaştırılmadı**, `freeze_check` yine de
> `PASS · exit=0` verdi ve kurcalanmış bir profille bile aynı sonucu döndü.
>
> - `kod_profil_sha256` — üst düzey anahtar. `sha256` sözlüğünün **içine yazma**.
> - `scripts_sha256` — kapı betiklerinin hash'i. Boş bırakırsan kapı betiğini
>   değiştiren bir koşu yakalanamaz (`FRZ-06` P1 uyarısı düşer).
> - `test_adlari` — taban test **adları**. Yoksa `RECK-07` değerlendirilemez ve
>   **P0 CALISTIRILMADI** verir; "tabanda olmayan test" kuralı çalışmaz.
>
> Bu üçü `MEVCUT_KOD` ve `YESIL_SAHA` modlarının **ikisinde de** doldurulur;
> dosyaya bakarlar, teste değil. Hazır komut:
>
> ```
> shasum -a 256 kod_profil.json scripts/*.py
> python3 -c "import xml.etree.ElementTree as ET;print([t.get('name') for t in ET.parse('_KOSU/gate/junit.xml').iter('testcase')])"
> ```

## 3. `kod_profil.json` — dil bağımsızlığı sözleşmesi

```json
{
  "dil": "python|js|swift|go|rust|karisik",
  "test_komutu": "pytest -q --junitxml=_KOSU/gate/junit.xml",
  "test_raporu": "_KOSU/gate/junit.xml",
  "test_rapor_formati": "junit-xml|tap|yok",
  "build_komutu": "", "lint_komutu": "", "imza_komutu": "",
  "bagimlilik_manifesti": [], "kilit_dosyasi": [],
  "izinli_lisanslar": ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"]
}
```

Boş bırakılan her alan, ilgili kapının `CALISTIRILMADI` = **P1** vermesine ve
`OLCULMEYEN` kaydı açılmasına yol açar. Sessiz "temiz" yoktur.

**Bu dosya hattın en yumuşak karnıdır.** `"test_komutu": "true"` yazmak bütün
kapıları sahte yeşil yapar. Bu yüzden SHA256'sı tabana yazılır ve her faz
sınırında `freeze_check.py` ile karşılaştırılır; değişikliği imzalı muafiyet
gerektirir (`UNSIGNED_WAIVER` = P0).

## Kapanış

```
python3 scripts/api_surface.py --json
```
Çıkış kodunu yaz. `kademe` T1 değilse dış imza envanteri **olumlu karar
üretemez**; `dis_imza` alanını doldur ama `olculmeyen`'e `DUSUK_GUVEN` notunu
düş. Ölçmediğine `DOGRULANAMADI` de.

Bittiğinde **insan onayı** iste ve **DUR**.
