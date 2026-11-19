> Bu dosya tek başına çalıştırılmaz. Önce `000_ONCE_BUNU_YAPISTIR.md` yapıştırılmış olmalı.

# PROFİL: KOD

Ortak çekirdeğe **ek** kontroller. Koşmayan kontrol `CALISTIRILMADI` = `P1`.

---

## CHK-SIR — sır taraması (fail-closed)

Aranan desen aileleri:

| Aile | Örnek biçim |
|---|---|
| Sağlayıcı anahtarı | `sk-` / `sk-ant-` öneki, `AKIA` + 16 büyük harf/rakam, `AIza` + 35 karakter |
| Kod deposu jetonu | `ghp_` / `gho_` / `github_pat_` önekleri |
| Mesajlaşma jetonu | `xox` + tek harf + tire |
| Özel anahtar | `BEGIN ... PRIVATE KEY` başlığı |
| Bağlantı dizesi | şema + kullanıcı + iki nokta + parola + `@` |
| Atama | anahtar/parola adı, ardından atama işareti ve 16+ karakterlik değer |

Tam düzenli ifadeler `ARACLAR/betikler/v4_verify.py` içindeki `SECRET_PATTERNS`
listesindedir; buraya birebir yazılmaz (belge metninin kendisi tarayıcıyı
tetiklemesin diye).

**Üç kural — hepsi zorunlu:**

1. **Dosya başına ilk eşleşmede durma.** Dosyanın 1. satırında yer tutucu,
   500. satırında gerçek anahtar olabilir. Tüm eşleşmeleri tara.
2. **Yer tutucu indirimi otomatik olamaz.** `xxx`, `test-`, `dev-`, `...`,
   `changeme` gibi ipuçları eşleşmeyi `P2`'ye **düşürmez**; yalnız bulguya
   `OLASI_YER_TUTUCU` notu ekler. İndirgeme **imzalı muafiyet** ister.
3. `.env.example` / `.env.template` / `.env.sample` dokümantasyondur; taranır
   ama bulguları `P2` başlar. Gerçek `.env`, `.env.local`, `.env.production`
   pakete girmişse bu ayrıca `P0`'dır.

> Bu üç kural ölçülmüş bir hatadan çıkarıldı: yer tutucu ipuçlarına dayanan
> otomatik indirgeme, `xxx`/`test-`/`...` içeren **gerçek formatlı** OpenAI, AWS
> ve üretim parolası anahtarlarını nota indiriyor ve kapı olumlu karar veriyordu.

## CHK-BAGIMLILIK — bağımlılık ve lisans

- Kilit dosyası (`*.lock`, `package-lock.json`, `uv.lock`) var mı ve manifestoyla
  tutarlı mı?
- Sabitlenmemiş sürüm (`*`, `latest`, `^` geniş aralık) → `P1`.
- Bilinen açık taraması: **MODE-A + ağ varsa** çalıştır ve çıktıyı kanıt olarak
  ekle; yoksa `NOT_EXECUTED` yaz, "temiz" **deme**.
- Lisans uyumu: proje lisansı ile bağımlılık lisansları çelişiyor mu?
  (GPL bağımlılık + MIT proje → `P0` hukuki bayrak, "hukuk görüşü gerekir")
- Çalışma zamanı bağımlılığı olması gerekmeyenler `devDependencies`'te mi?

## CHK-IMZA — dışa açık yüzey envanteri

Girdideki her dışa açık sembolü çıkar: fonksiyon/sınıf adı + parametre sayısı +
imza; `export` / `__all__` / `pub` işaretlileri; HTTP uç noktaları (metod + yol);
ortam değişkeni adları; yapılandırma anahtarları; veritabanı şema alanları.

Bu envanter **KEEP listesinin bir parçasıdır**. Çıktıda kaybolan veya imzası
değişen her dışa açık sembol `DATA_LOSS` `P0`'dır — geriye dönük uyumsuzluk
sessizce yapılamaz.

## CHK-TEST — test kanıtı (attestation zorunlu)

**Sabit sayı kullanma.** "313 test geçmeli" gibi bir beklenti kodlanmaz — o sayı
bir anlık görüntüdür ve ilk iyileşmede yanlış engel üretir.

Bunun yerine:

| Ölçüt | Kural |
|---|---|
| Başarısız test | `== 0`, aksi `P0` |
| Hata (error) | `== 0`, aksi `P0` |
| Koşan test sayısı | `>= 1`, aksi `P0` |
| Koşan test sayısı | `>=` önceki taban çizgisi, aksi `P0` |
| Atlanan (skipped) test | `<=` önceki taban çizgisi, aksi `P1` |
| Kapsam (coverage) | `>=` taban − 1 puan, aksi `P1` — **eşitlik kontrolü yapma** |
| Çıkış kodu | `== 0` **ve** başarısız `== 0` — çelişki tek başına `P0` |

**Kanıt kaydı zorunlu:** `{komut, cikis_kodu, baslangic, sure_ms, calisma_dizini,
rapor_ozeti}`. Eksik alan → `EVIDENCE_UNVERIFIED` `P0`.
Elle yazılmış bir metin logu kanıt değildir; 90 baytlık uydurma bir metin
`"76 passed"` yazarak kapıyı geçebilir.

**MODE-B'de test kanıtı yoktur.** `NOT_EXECUTED` yaz, durum `OLCULMEDI`.

## CHK-HATA — hata yolları

- Yakalanıp yutulan istisna (`except: pass`, boş `catch`) → `P1`.
- Kullanıcı girdisiyle oluşan yol/komut (`os.system`, `eval`, dizeyle SQL) → `P0`.
- Zaman aşımı olmayan ağ çağrısı → `P1`.
- Kaynak sızıntısı: açılıp kapatılmayan dosya/bağlantı → `P1`.
- Hata mesajında sır/iç yol sızıntısı → `P1`.
- Yarış koşulu adayları: paylaşılan durum + eşzamanlılık, kilitsiz → `P1` + not.

## CHK-README — belge ↔ gerçeklik

README'deki her somut iddia doğrulanır: kurulum komutu gerçekten var mı; anılan
dosya/klasör var mı; anılan ortam değişkeni kodda okunuyor mu; verilen sayı
(test, kapsam, performans) bir kanıt artefaktına dayanıyor mu.

**Kaynağı olmayan sayısal iddia → `CLAIM_UNSUPPORTED` `P1`.** Bir depoda
yayınlanan sayı, karşı tarafın aynı komutu çalıştırmasıyla sınanır; tutmazsa
bu teknik değil dürüstlük bulgusu olarak okunur.

## CHK-HIJYEN — paket temizliği

`node_modules`, `.next`, `__pycache__`, `.pytest_cache`, `.venv`, derleme
çıktıları, `.DS_Store`, `__MACOSX/`, `._*` → `P1`.
Gerçek `.env*` dosyası → `P0`.

**İstisna:** koşunun kendi kanıt/rapor klasörü hijyen taramasının **dışındadır**
(kanıt üretmek zorunluluğuyla çelişmemesi için), ama sır taramasının **içindedir**
ve kanıt logları sır redaksiyonundan geçirilerek yazılır.

## KORUMA — bu profilde korumalı türler

Dışa açık fonksiyon/sınıf imzaları · `export`/`__all__` girdileri · test adları ve
sayıları · yapılandırma anahtarları · ortam değişkeni adları · bağımlılık
adı+sürümü · veritabanı geçiş (migration) dosyaları · lisans başlıkları.

Bir testin "gereksiz" diye silinmesi, bu profildeki en ağır ihlaldir.
