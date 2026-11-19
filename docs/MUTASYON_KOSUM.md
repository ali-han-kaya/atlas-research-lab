# MUTASYON KOŞUM KAYDI (üretilmiş)

Bu dosya **elle yazılmaz**. Üreten: `scripts/mutasyon_kos.py`. Her satır gerçek bir mutasyon koşumundan gelir; `once | **sonra**` hücreleri lint çıkış kodudur. Çıktı hücresinde **başka** kapı kimlikleri `<baska-kapi>` diye maskelenir: satır tek bir kapının kanıtıdır, başka kapıya kredi yazılmasın diye.

| kapı | mutasyon | once | sonra | çıktı |
|---|---|---|---|---|
| `C11b` | §7.4 geri donus P1 -> K2 | 0 | **1** | rc=1 · FAIL eksik: ['p1 → k2'] |
| `C11d` | §10 I6 kimligi (kaynagi AGENTS.md, I1-I9) | 0 | **1** | rc=1 · FAIL eksik: ['i1-i9'] |
| `C11e` | §7.1 BLOK_GECERSIZ <-> ACIK_SORU ayrimi | 0 | **1** | rc=1 · FAIL eksik: ['iki durum karismaz'] |
| `C14e` | [sir] isaretleyen insan + veri verilmisse dur (D14) | 0 | **1** | rc=1 · FAIL sapan: ['Isaretleyen **insandir**: 0/1'] |
| `C18` | kapi parametreleri gomulu yazilmaz (D10 5. tekrar) | 0 | **1** | rc=1 · FAIL sapan: ['H:tek kaynak `<baska-kapi>` cikt: 0/1'] |
| `C13u` | capa bozuldu: gocte veri degistirilmez | 0 | **1** | rc=1 · FAIL sapan: ['Gocte **veri degistirilmez: 0/1'] |
| `C15d` | capa bozuldu: sessizlik riza degildir | 0 | **1** | rc=1 · FAIL madde=7 · cevapsiz>0 olan=7 · hepsi ITIRAZ_YOK=True · |
| `C13n` | capa bozuldu: her sentez satiri kaynakli · iskelet/malzeme | 0 | **1** | rc=1 · FAIL sapan: ['her sentez satiri kaynakli: 0/1'] |
| `C14o` | durum.json anahtari semadan kaydi (kalem 3) | 0 | **1** | rc=1 · FAIL sema=18 gercek=18 eksik=['asama'] fazla=['asama_x'] |
| `C14k` | injection_sayac uyum sarti TERS cevrildi | 0 | **1** | rc=1 · FAIL uyum rc=1 "DURUM : injection=1 kayit" · uyumsuz rc=0  |
| `C14l` | karsilastirici ESIT demiyor (birebir aynilik olcumu) | 0 | **1** | rc=1 · FAIL SONUC: ES1T — alinti #0 (blok #3 ile) [SIKI] |
| `C14t` | SKILL.md'ye gomulu sayac sokuldu (D10b) | 0 | **1** | rc=1 · FAIL bulunan: ['sayaç: 7'] · alinti: 0 |
| `C11a` | capa bozuldu: kullanilan= | 0 | **1** | rc=1 · FAIL eksik: ['kullanilan='] |
| `C13a` | capa bozuldu: 2026-11-07 yeniden olcum | 0 | **1** | rc=1 · FAIL sapan: ['2026-11-07 yeniden olcum: 0/1'] |
| `C13b` | capa bozuldu: govde indirilmedi | 0 | **1** | rc=1 · FAIL sapan: ['govde indirilmedi: 0/1'] |
| `C13c` | capa bozuldu: gecersiz dis blok kaydi | 0 | **1** | rc=1 · FAIL sapan: ['gecersiz dis blok kaydi: 0/1'] |
| `C13d` | capa bozuldu: butce_disi | 0 | **1** | rc=1 · FAIL sapan: ['butce_disi: 0/1'] |
| `C13f` | capa bozuldu: 8.2/6 bunu zorunlu kilar | 0 | **1** | rc=1 · FAIL sapan: ['8.2/6 bunu zorunlu kilar: 0/1'] |
| `C13g` | capa bozuldu: okuma yok + yazma yok: sonuc sohbette | 0 | **1** | rc=1 · FAIL sapan: ['okuma yok + yazma yok: son: 0/1'] |
| `C13h` | capa bozuldu: esik sekle degil riske baglidir | 0 | **1** | rc=1 · FAIL sapan: ['esik sekle degil riske bag: 0/1'] |
| `C13j` | capa bozuldu: ust hemze u+0654 | 0 | **1** | rc=1 · FAIL sapan: ['ust hemze U+0654: 0/1'] |
| `C13p` | capa bozuldu: kez bilgi sorusu sorar | 0 | **1** | rc=1 · FAIL sapan: ['kez bilgi sorusu sorar: 0/1'] |
| `C13q` | capa bozuldu: veya §8.2/6 zorunlu taramasi yapilmadi | 0 | **1** | rc=1 · FAIL sapan: ['veya §8.2/6 zorunlu tarama: 0/1'] |
| `C12a` | capa: §99 diye bir bolum yok (capraz atif cozulmez) | 0 | **1** | rc=1 · FAIL cozulmeyen: ['99'] |
| `C12b` | capa: §3.3/99 maddesi yok (madde numarasi uydurma) | 0 | **1** | rc=1 · FAIL yok: ['3.3/99'] |
| `C13e` | token bozuldu: karsiligi el ile yapilir" hukmu uyarinca | 0 | **1** | rc=1 · FAIL sapan: ['karsiligi el ile yapilir" : 0/1'] |
| `C13r` | token bozuldu: Âl-i İmrân 3:159 | 0 | **1** | rc=1 · FAIL sapan: ['H:Âl-i İmrân 3:159: 0/1'] |
| `C13s` | token bozuldu: إن الصدق يهدي إلى البر وإن البر يهدي إلى الج | 0 | **1** | rc=1 · FAIL sapan: ['H:إن الصدق يهدي إلى البر و: 0/1'] |
| `C13k` | token bozuldu: eklenen olarak kaydedilir | 0 | **1** | rc=1 · FAIL sapan: ['eklenen olarak kaydedilir: 0/1'] |
| `C13l` | token bozuldu: her p0 ve p1 iddia | 0 | **1** | rc=1 · FAIL sapan: ['her p0 ve p1 iddia: 0/1'] |
| `C13m` | token bozuldu: aracla_bulunmadi = arama araci yoktu | 0 | **1** | rc=1 · FAIL sapan: ['aracla_bulunmadi = arama a: 0/1'] |
| `C13o` | token bozuldu: "mod":"<a/b/c>" | 0 | **1** | rc=1 · FAIL sapan: ['"mod":"<a/b/c>": 0/1'] |
| `C14s` | SKILL.md'de literal yildiz (vurgu butunlugu bozuldu) | 0 | **1** | rc=1 · FAIL literal *: 1 — Ag* yoksa kaynak |
| `C15b` | tur haritasi sayisi diskle celisiyor (bos iskelet) | 0 | **1** | rc=1 · FAIL paket=19 · harita=6/2 yer · cevapsiz=6 (cevap blogu 0 |
| `C11c` | token bozuldu: §3.3/3 | 0 | **1** | rc=1 · FAIL eksik: ['§3.3/3'] |
| `C13i` | token bozuldu: kucuk is (§0.6) | 0 | **1** | rc=1 · FAIL sapan: ['kucuk is (§0.6): 2/3'] |
| `C14i` | goc veriyi degistiriyor (VERI_DEGISMEDI: HAYIR) | 0 | **1** | rc=1 · FAIL VERI_DEGISMEDI: HAYIR — GERI AL |
| `C14j` | tip hatasi kontrolu ters cevrildi (fail-closed yok) | 0 | **1** | rc=1 · FAIL <bos> |
| `C14za` | tiktoken yokken rc=0 (OLCULMEDI sozu tutulmuyor) | 0 | **1** | rc=1 · FAIL tiktoken YOK -> OLCULMEDI+rc2 · HATA: tiktoken yokken |
| `C14w` | compatibility betik kumesini ilan etmiyor (scripts/ yok) | 0 | **1** | rc=1 · FAIL betik=12 · eksik=- · compatibility=YOK |
| `C15a` | kapanmis madde P1'de yeniden soruluyor (D22 -> D13) | 0 | **1** | rc=1 · FAIL kayit=7 madde · itirazsiz+degmedi=7 · P1 sorulan=9 ·  |
| `C14z` | surum() SURUM.md ile ayni degil — kendi testi kirilir | 0 | **1** | rc=1 · FAIL rc=1 · Ran 10 tests in 0.073s / FAILED (failures=1) |
| `C14v` | oz-beyan artik bagimsiz sayiliyor (OZ_ADLAR'dan 'oz' cikti) | 0 | **1** | rc=1 · FAIL gecerli=0 · oz=0 · bozuk-sha=1 |
| `C15c` | gomulu eser govdesi bozuldu (kunye sha tutmuyor) | 0 | **1** | rc=1 · FAIL paket=26 · ayni=20 · farkli=1 · gomdesiz=3 · kunyesiz |
| `C17` | TUR_HARITASI §3 dosya sayisi manifestle celisiyor (16 -> 17) | 0 | **1** | rc=1 · FAIL §3=17 dosya·1865272 B·119 MODEL: · §7=esleme=3/16 · P |
| `C14t-a` | sayac kuralindan 'kalem' anahtari cikti — bilinen yazim kacar | 0 | **1** | rc=1 · FAIL regresyon=55/58 kacan=['9 kalem', 'on iki kalem', 'to |
| `C15l` | plato taramasi 3'ten baslamiyor (alt=99) — n<3 | 0 | **1** | rc=1 · FAIL n=0 · tmp-sizinti=0 · - · HATA: rc=2 / TARAMA satiri  |
| `C14x` | manifest disi yetim dosya olusturuldu (KANITSIZ) | 0 | **1** | rc=1 · FAIL manifest=150 · ikiz=6 · ham-iz=2 · KANITSIZ=Q_yetim.t |
| `C17` | fixture (iii) sha vakasi etkisizlesti — sha256 katmani sinanmiyor | 0 | **1** | rc=1 · FAIL §3=16 dosya·1865272 B·119 MODEL: · §7=esleme=3/16 · P |
| `C14y` | kaynak tarihi yerine duvar saati (date.today) — gece devri yanlis-kirm | 0 | **1** | rc=1 · FAIL EK=3 · eser=v1.4.81 · lint=2.65 · tam=350766 B · P1=7 |
| `C17` | dogrulanan dosya sayisi bozuk dosyayi DUSMEZ (beyan/olcum celiskisi ge | 0 | **1** | rc=1 · FAIL §3=16 dosya·1865272 B·119 MODEL: · §7=esleme=3/16 · P |

## Koşum 2026-11-15 08:46 · 2 kanıt

| `C15i` | siniflandirma durum_belirle() uzerinden GECMIYOR (rc deseni geri geldi | 0 | **1** | rc=1 · FAIL projeler_tara=var · gorunurluk=var · zorunlu=var · js |
| `C15i` | bekleyen hukum oneki (PASS-PENDING) dustu — PASS-PENDING-ETHICS yine Y | 0 | **1** | rc=1 · FAIL projeler_tara=var · gorunurluk=var · zorunlu=var · js |
