> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# C1 — SÖZLEŞME (normatif kaynak)

Bu dosya **tek doğruluk kaynağıdır**. Paketteki hiçbir dosya buradaki bir sözcüğü,
kodu, şiddet etiketini veya şemayı farklı yazamaz. `v4_consistency.py` bunu
mekanik olarak denetler; çelişki bulursa paket yayınlanmaz.

---

## 1. ŞİDDET EKSENİ (kapalı liste — üç değer, başka yok)

| Değer | Anlamı | Sonucu |
|---|---|---|
| `P0` | Teslimi engelleyen kusur | Karar `ENGEL_VAR` olur |
| `P1` | Düzeltilmeli, teslimi engellemez | Karar en iyi ihtimalle `KOSULLU` |
| `P2` | Not / kozmetik / bilgilendirici | Karar etkilenmez, kayda geçer |

**Kapalılık kuralı:** `P0` / `P1` / `P2` dışındaki her değer — `CRITICAL`,
`BLOCKER`, `high`, `SEV0`, boşluklu `"P0 "`, boş dize, eksik alan — `SCHEMA_INVALID`
üretir ve **`P0` sayılır**. "Tanımadım, saymadım" davranışı yasaktır.

> Gerekçe (ölçülmüş): önceki neslin karar birleştiricisi tanımadığı şiddet
> etiketini sessizce yok sayıyordu. `priority: "CRITICAL"` etiketli dört kritik
> bulgu içeren bir denetim çıktısı olumlu karar alıyordu. Kapalı liste bu deliği kapatır.

## 2. TÜR EKSENİ (kapalı liste — makine tarafı)

Tür kodu **kullanıcıya gösterilmez**; yeniden deneme hedefini ve profil kontrolünü seçer.

| Kod | Ne demek | Yeniden deneme hedefi |
|---|---|---|
| `FACTUAL_ERROR` | Olgu yanlış | yalnız iddianın geçtiği bölüm |
| `CLAIM_UNSUPPORTED` | İddia var, kanıtı yok | yalnız iddia + kaynak bölümü |
| `CITATION_MISSING` | Kaynak/atıf eksik veya kırık | yalnız kaynakça + atıf noktası |
| `LOGICAL_ERROR` | Çelişki, non sequitur, kategori hatası | yalnız çelişen iki konum |
| `STYLE_FAILURE` | Biçim/dil/şablon ihlali | yalnız ilgili paragraf |
| `DATA_LOSS` | Koruma sözleşmesi ihlali | **yeniden deneme yok** → geri al |
| `SCOPE_VIOLATION` | Hedef dışı bölüm değişmiş | **yeniden deneme yok** → geri al |
| `INJECTION_ATTEMPT` | Veri içinde talimat kalıbı | yeniden deneme yok → kaydet |
| `GRADER_MISCALIBRATED` | **Denetçinin kendisi güvenilmez** | **yeniden deneme YASAK** → `BUTUNLUK_ASKISI` |
| `SCHEMA_INVALID` | Sözleşme dışı çıktı | yeniden deneme yok → düzelt ve yeniden üret |

**`GRADER_MISCALIBRATED` kuralı:** Güvenilmez bir denetçiyi yeniden çağırmak
yalnızca ikinci bir güvenilmez karar üretir. Bu koda sahip bir bulgu **asla**
yeniden denenmez; koşu `BUTUNLUK_ASKISI` terminal durumuna geçer ve insana döner.

**Kapalılık kuralı:** Bu listede olmayan bir kod uydurmak yeni kategori açmak
değil, hatadır → `SCHEMA_INVALID` → `P0`.

## 3. BULGU NESNESİ (tek şema)

```json
{
  "id": "F-001",
  "code": "CLAIM_UNSUPPORTED",
  "severity": "P1",
  "location": "dosya.md §3.2 / satir 142",
  "evidence": "girdiden BIREBIR alinti, <=200 karakter",
  "fix": "uygulanabilir tek cumlelik duzeltme"
}
```

Kurallar:

- **Anahtarlar ASCII İngilizce, değerler Türkçe.** Anahtar adı `[A-Z0-9_a-z-]+`
  desenine uyar; Türkçe karakter (İ, ı, ş, ğ, ü, ö, ç) **anahtarda yasaktır**.
  (Türkçe yerelde `"I".lower() == "ı"` olduğu için büyük/küçük harf duyarsız
  eşleşme ve `grep` bozulur.)
- `evidence` **birebir alıntıdır**, özet değildir. Denetlenen dosyada literal
  alt-dize olarak bulunamayan `evidence` → bulgu `FINDING_UNVERIFIABLE` sayılır.
- `fix` boş bırakılamaz. "Gözden geçirilmeli" bir düzeltme değildir.
- Aynı `fix` metnini paylaşan bulgular **tek eyleme** birleştirilir (kullanıcıya
  bulgu sayısı değil, eylem sayısı gösterilir).

## 4. KONTROL KAYDI (checks — "ölçüm yapıldı" kanıtı)

```json
{"id": "CHK-KAYNAK", "status": "GECTI", "evidence": "37 atifin 37'si kaynakcada var"}
```

`status` kapalı liste: `GECTI` | `KALDI` | `CALISTIRILMADI`.

- `KALDI` → `P1` sayılır (bulgu listesine ayrıca yazılmasa bile).
- `CALISTIRILMADI` → `P1` sayılır ve `OLCULMEYEN` bölümüne düşer. Sessizce
  atlanamaz.
- `evidence` boş olan bir `GECTI` **geçersizdir** → `SCHEMA_INVALID` → `P0`.

**Boş denetim kuralı:** `findings: []` **tek başına** olumlu karar üretemez.
Olumlu karar için en az bir `checks` kaydı ve her kaydında dolu `evidence`
gerekir. Aksi hâlde `NO_INSPECTION_EVIDENCE` → `P0`.

> Gerekçe (ölçülmüş): boş JSON (`{}`) iki gate dosyası olarak verildiğinde
> v3'ün miras aldığı birleştirici `FINAL PASS` üretiyordu. Hiçbir şey
> ölçmemek, temiz çıkmakla aynı şey değildir.

## 4b. İŞ TİPİ (kapalı liste)

`KOD` | `AKADEMIK` | `VERI` | `GIRISIM` | `BELGE`

Sınıflandırma kuralları ve her tipin zorunlu kontrolleri `C3_SINIFLANDIRICI.md`
içindedir; **listenin kendisi burada normatiftir.** Bu beşin dışında bir tip
üretilemez; gerekiyorsa önce bu liste genişletilir.

## 5. TERMİNAL DURUMLAR (kapalı liste)

Her koşu tam olarak birinde biter:

| Durum | Anlamı |
|---|---|
| `TAMAMLANDI` | Tüm fazlar koştu, kapılar karar verdi |
| `KOSULLU` | Koştu ama açık P1 veya cevaplanmamış soru var |
| `ENGEL_VAR` | P0 var, teslim edilemez |
| `BUTUNLUK_ASKISI` | Denetçi güvenilmez — otomatik çıkış yolu YOK |
| `INSAN_BEKLIYOR` | Üç duruş noktasından birinde durdu |
| `BUTCE_BITTI` | Özerklik bütçesi tükendi |
| `OLCULMEDI` | MODE-B: ölçüm yapılamadı (bkz. C5 §4) |

"Pes ettim ama tamamlandı" diyen bir durum yoktur.

## 6. SÖZLÜK (12 terim — kavram başına tek isim)

| Terim | Karşılığı | Kullanılmayacak eşanlamlı |
|---|---|---|
| kapı | karar veren mekanik kontrol | gate, geçit |
| koruma | veri kaybını ölçen kontrol | preservation, KEEP kontrolü |
| bulgu | tespit edilen kusur kaydı | finding, issue |
| kanıt | birebir alıntı veya çalıştırma çıktısı | evidence, delil |
| duruş | kullanıcıya soru sorulan nokta | kesinti, onay |
| koşu | tek bir baştan sona çalıştırma | run, oturum |
| faz | pipeline adımı (F0..F6) | aşama, adım |
| profil | iş tipine özel kontrol seti | mod, şablon |
| KEEP | korunacak bölüm kaydı | — |
| muafiyet | imzalı kural istisnası | waiver, bypass |
| taban | değiştirilemez asgari kural | floor, hard rule |
| oturum kimliği | koşuyu geri getiren anahtar | run id, token |

**Üç yasak:**

1. Tek düzyazı cümlesi içinde dil karıştırma. ("KEEP listesi validate edildi" → yasak.)
2. İngilizce simgeye Türkçe çekim eki. (`KEEP'leri`, `PASS'ladı`, `gate'ten` → yasak.)
3. Bir kavram için iki isim. (Yukarıdaki sağ sütun kullanılmaz.)

## 7. MİKRO ÖRNEKLER (şema hizalaması için — gerçek veri değildir)

Sınıflandırma çıktısı:
```
TIP=AKADEMIK | SINYAL=kural-2 (kaynakca + 14 DOI) | GUVEN=YUKSEK
```

Bulgu:
```json
{"id":"F-003","code":"CITATION_MISSING","severity":"P1",
 "location":"bolum-3.md satir 88",
 "evidence":"(Yilmaz, 2021) metinde geciyor",
 "fix":"Kaynakcaya Yilmaz 2021 kaydini ekle veya atfi kaldir"}
```

KEEP kaydı:
```
KEEP-014 | §3 Yontem | sha256:9f2a...c31 | 1247 karakter | 18 cumle
```
