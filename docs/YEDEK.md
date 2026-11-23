# Yerel yedek — `git bundle`

Tek dosyalık, çevrimdışı, tam geçmiş yedeği. Uzak depo (GitHub) erişilemez,
arşivlenmiş veya silinmiş olsa da bu dosyadan depo birebir geri kurulabilir.

## Komut (tekrar edilebilir)

```bash
scripts/yedek_al.sh . "$HOME/atlas-yedek"
```

Betik sırayla:

1. `git bundle create <hedef>/atlas-<tarih>.bundle --all` — tüm dallar, etiketler
   ve işaretçiler tek dosyada.
2. `git bundle verify` — dosyanın eksiksiz olduğunu ve gereken nesneleri
   taşıdığını doğrular.
3. Geçici klasöre klonlar, `HEAD` sha'sının kaynakla aynı olduğunu ve
   `git fsck --full` temiz geçtiğini ölçer.
4. `YEDEK PASS — ...` satırını basar; herhangi bir adım tutmazsa `rc=1`.

Betik depoya, `HEAD`'e veya geçmişe yazmaz; yalnız hedef klasöre yeni bir dosya
bırakır (varsa eski bundle'lara dokunmaz).

## Haftalık otomatik yedek (launchd)

Şablon: `scripts/com.alikaya.atlas-yedek.plist` · kurulu kopya:
`~/Library/LaunchAgents/com.alikaya.atlas-yedek.plist` · zaman: **her Pazar 03:00**.
İş, macOS Desktop izni için `scripts/yedek_al_otomatik.command` üzerinden Terminal'de çalışır.

```bash
cp scripts/com.alikaya.atlas-yedek.plist "$HOME/Library/LaunchAgents/"
launchctl bootout gui/$(id -u) "$HOME/Library/LaunchAgents/com.alikaya.atlas-yedek.plist" 2>/dev/null || true
launchctl bootstrap gui/$(id -u) "$HOME/Library/LaunchAgents/com.alikaya.atlas-yedek.plist"
launchctl enable gui/$(id -u)/com.alikaya.atlas-yedek
```

Durum ve elle test:

```bash
launchctl print gui/$(id -u)/com.alikaya.atlas-yedek | head
launchctl kickstart -k gui/$(id -u)/com.alikaya.atlas-yedek
tail -20 "$HOME/Library/Logs/atlas-yedek.out.log"
```

Betik yalnız yeni `atlas-<tarih>.bundle` üretir; eski bundle'ları silmez.

## Geri yükleme

```bash
git clone ATLAS_YEDEK/atlas-<tarih>.bundle geri-yuklenen
cd geri-yuklenen
git log --oneline -1          # beklenen: yedek anındaki HEAD
```

## Kapsam

| Kapsar | Kapsamaz |
|---|---|
| Tüm commit'ler ve dallar | Commit edilmemiş çalışma ağacı |
| Etiketler ve işaretçiler | `.gitignore`'daki dosyalar, `docs/_ARSIV-*`, `projeler/` |
| Tam geçmiş (933 commit) | `~/.ssh`, kimlik bilgileri, uzak depo ayarları |

Yedek "depo geçmişi" içindir; kirli dosyalar için ayrıca commit veya kopya gerekir.

## Ölçüm — 20 Kasım 2026

```
$ scripts/yedek_al.sh . "$HOME/atlas-yedek"
YEDEK PASS — $HOME/atlas-yedek/atlas-20261120-075956.bundle
  HEAD=7d6ea2d37aa4a61e7a948a10c5ed2d4d87a5afbd · commit=933 · bayt=10038419
```

`git bundle verify` çıktısı: **"The bundle records a complete history."**
Kopya klonda `git fsck --full` temiz (rc=0), kaynak ve kopya `HEAD`/commit sayısı
aynı.

### Bilinen sınır (ölçüldü)

macOS'un büyük/küçük harf duyarsız dosya sisteminde iki yol çakışıyor
(`ALLAHAŞKI.md` / `ALLAHAŞKI.md` ve iki `Şekina…` dosyası). `git bundle create`
bu yüzden bir uyarı basar; **commit nesneleri eksiksizdir**, yalnız geri yüklemede
çakışan gruptan biri çalışma ağacına açılır. Veri kaybı değil, checkout sınırıdır.

## Uzak yedek durumu — 20 Kasım 2026

`origin` = `git@github.com:ali-han-kaya/ATLAS_Research_Lab_backup.git` (private).
`git ls-remote origin` → `8354e35…` (HEAD ve `refs/heads/master`), `ls-remote rc=0`.
API: `visibility=private`, `isArchived=false` (boş), `default_branch=master`,
`pushed_at=2026-11-20T06:47:51Z`. Yani uzak yedek bu tarihte **çalışıyor**;
bundle ondan bağımsız ikinci kopyadır.
