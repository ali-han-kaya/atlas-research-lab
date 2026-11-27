# İddia defteri — makine denetimli özet

Bu sayfa `tools/iddia_defteri.json` içindeki durum dağılımının belgelenmiş
özetidir. `make iddia` her koşuda önce bu satırı defterden yeniden hesaplar ve
birebir karşılaştırır; ikisi ayrışırsa `rc=2` ile kırmızı olur. Satır otomatik
yazılmaz: defter bilinçli değiştiğinde burada da bilinçli olarak güncellenir,
aksi halde kapı sessiz kaymaya izin vermez.

<!-- IDDIA-OZET:BASLA -->
olculdu=42 · ag=1 · beyan=11 · olculmedi=1
<!-- IDDIA-OZET:BITIR -->

- `OLCULDU` — komutu koşan, ham kanıt satırı defterdeki komutla ve beyanla
  birebir tutan satır.
- `AG_GEREKLI` — ağ isteyen satır; varsayılan koşuda atlanır, PASS sayılmaz.
- `BEYAN` — tarihli veya makineye bağlı kayıt; yeniden koşulmaz, gerekçesi
  satırda yazılıdır.
- `OLCULMEDI` — bu ağaçta yeniden üretilemeyen satır; gerekçesi satırda
  yazılıdır.

Ham kanıt dosyası defterin üst düzeyindeki `olcum_dosyasi` alanındadır
(`tools/iddia_olcum.json`); `tools/iddia.py` bu yolun tam olarak o dosya
olduğunu doğrular. Tek bir satırın defter → komut → ham kanıt → hüküm izi kök
`README.tr.md` içindeki **Tek bir iddiayı izlemek** bölümündedir.
