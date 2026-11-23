# ATLAS'ı kısa turda anla

Bu tur, depoyu ilk kez açan birinin üç sorusunu yanıtlar:

1. **Bu lab ne yapar?**
2. **Kime yarar?**
3. **İddiasını nasıl kanıtlar?**

ATLAS bir makale arşivi değildir. Akademik metin ve yazılım üretimini, modelin
"tamamlandı" beyanına değil teslimin kendi baytları üzerinde koşan kapılara
bağlayan bir **üretim mekanizmasıdır**.

## 1. Ne yapar?

İki hat ve bir oturum disiplini vardır:

| Katman | Görev | Çıktı |
|---|---|---|
| **ATLAS** | Kapsam → üç paralel inceleme merceği → hedefli düzeltme → MASTER → 2-of-2 kabul | Denetlenmiş akademik metin |
| **KOD** | KFAZ0–5: kapsam, tasarım, uygulama, kanıt, 2A/2B/2C kapıları | Kanıtı olan yazılım teslimi |
| **Toolkit** | Model-agnostik oturum sözleşmesi: C1–C6 + çalıştırılabilir denetimler | Tekrarlanabilir çalışma disiplini |

Makaleler, PDF'ler, konu korpusları ve ham araştırma çıktıları bu depoda
**yoktur**. Depo ürünü değil, ürünü üreten ve denetleyen mekanizmayı taşır.

## 2. Kime yarar?

- **Araştırmacıya:** "Kaynak var mı, iddia nerede, düzeltme gerçekten uygulandı mı?"
  sorularını metnin kendisine sormayı öğretir.
- **Yazılım ekibine:** KFAZ0–5 ve 2A/2B/2C kapılarıyla teslimi beyandan ayırır.
- **Denetçiye / işe alım ekibine:** Yalnız sonucu değil, sonucun nasıl ölçüldüğünü
  gösterir; her sayı bir komuta bağlanır.
- **Yeni öğrenene:** Fail-closed, kanıt seviyesi, KEEP parmak izi ve mutasyon
  testi gibi kavramları çalışan örneklerle öğretir.

## 3. İddiasını nasıl kanıtlar?

### Tek komutlar

| Komut | Neyi ölçer |
|---|---|
| `make dogrula` | Depo hijyeni, sözdizimi, sır taraması, kapı öz-testleri ve üç öz-test paketi |
| `make iddia` | README ve kamu belgelerindeki sayısal iddiaları, onları üreten komutla yeniden ölçer |
| `make mutasyon` | Kapı kurallarının gerçekten ateşlediğini: temiz taban + tek ihlal + kırmızı hüküm |
| `make kanit-dogrula` | `attestation.json` içindeki commit, ağaç ve dosya hash'lerini |
| `make yayin-kapisi` | Yayın manifesti, listelenmemiş dosya, makale izi, sır ve kişisel mutlak yol |
| `./demo` | Bilerek kusurlu `DENEME/` koşusunda beklenen kırmızı hükmü |

`make dogrula` sekiz kalemi sayar; yayın kapısı bunun **ön koşuludur**, sayılan
sekiz kaleme eklenmez. Böylece mevcut 8/8 sözleşmesi değişmez.

### Kanıt zinciri

```text
brief / kaynak
      │
      ├── ATLAS hattı ──┐
      └── KOD hattı ────┤
                        ▼
                 kapılar (fail-closed)
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
     attestation.json          CI / iddia defteri
     (commit + tree + hash)    (sayı → komut → ham çıktı)
            │
            ▼
     yayın manifesti → public ağaç
```

Kanıtın üç parçası ayrılmaz:

1. **Koşan komut** — gerçekten çalıştırılmış olmalı.
2. **Ham çıktı** — komutun ürettiği satır; özet etiket değil.
3. **Birincil kayıt** — commit, ağaç veya dosya hash'i.

Bu üçü yoksa cümle bir **iddiadır**; `OLCULMEYEN` alanına yazılır. Ölçülemeyen
şey "geçti" sayılmaz.

## 4. İlk turda ne yapmalı?

```bash
git clone https://github.com/ali-han-kaya/atlas-research-lab.git
cd atlas-research-lab
python3 -m pip install -r requirements-dev.txt
make kur
make dogrula
make yayin-kapisi
./demo            # beklenen: rc=1 — kırmızı, çünkü iddia > kanıt
make iddia        # README sayılarını yeniden ölçer
```

`./demo` kırmızı döner; bu bir arıza değil, laboratuvarın bilerek sakladığı
kusurlu koşuyu bugünkü kapının reddettiğini gösterir. `make demo` kullanılmaz:
GNU make tarif hatasını 2'ye çevirdiği için 1/2 ayrımını taşımaz.

## 5. Nerede okumalı?

- Giriş ve hızlı başlangıç: [`../README.md`](../README.md)
- Ölçüm ve öğrenim kayıtları: [`README.md`](README.md)
- Yayın sınırı ve manifest: [`YAYIN-SOZLESMESI.md`](YAYIN-SOZLESMESI.md)
- Güncel sayılar (üretilmiş): [`DURUM.md`](DURUM.md)
- İngilizce hızlı başlangıç: [`EN/QUICKSTART.md`](EN/QUICKSTART.md)

## Sınır

Bu tur labın **mekanizmasını** anlatır. Akademik bir makalenin içerik
doğruluğunu, kaynakların gerçekliğini veya public yayının dış denetimini
kanıtlamaz. Depoda makale metni, PDF veya ham araştırma çıktısı yoktur; bu bir
eksik değil, yayın sözleşmesinin bilinçli sınırıdır.
