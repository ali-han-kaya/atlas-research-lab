# OPERATÖR — KURULUM ve HATTI SÜRME

> **BU DOSYA AJANLARIN BAĞLAMINA YÜKLENMEZ.** `opencode.json` `instructions`
> listesinde **yoktur** ve olmamalıdır. İçeriği hattı **dışarıdan** süren insana
> (ya da insanın kabuğuna) yöneliktir.
>
> Gerekçe — ÖLÇÜM-03 O3-02 (24 Ağustos 2026): bu iki bölüm daha önce
> `00_KOD_OKU_BENI.md` içindeydi ve o dosya `instructions`'tadır. Ajanlar
> operatöre yazılmış "hattı şöyle sür" talimatını **kendi görevleri** sandı ve
> `scripts/kos_faz.sh`'i özyinelemeli çağırdı. Tek koşuda `kod-architect`
> **44** kez `kos_faz.sh`, **6** kez `opencode run --agent` çalıştırdı; açılan
> oturum sayısı `build=78`, `kod-architect=74` oldu ve ücretsiz modelin günlük
> kotası tükendi. Düzeltme buradaki ayrımdır.

## KURULUM — atlanamaz  (ÖLÇÜM-02 K1/K2)

`KOD_SABLONLAR/` **kendi kendine yeten bir paket değildir**: `scripts/` bir
symlink taşıyordu ve `kod_gate_merge.py` `ORTAK/` çekirdeğini arar. Elle
kopyalama iki kırıkla sonuçlanıyordu. Kurulum tek komuttur:

```
bash KOD_SABLONLAR/scripts/kur.sh <hedef-depo>            # kur + doğrula
bash KOD_SABLONLAR/scripts/kur.sh <hedef-depo> --kuru     # ne yapacağını göster
bash KOD_SABLONLAR/scripts/kur.sh <hedef-depo> --dogrula  # MEVCUT kurulumu denetle
```

`--dogrula` **kopyalamaz**; ORTAK çekirdeğinin labla birebir olduğunu, asılı
symlink kalmadığını ve kapıların gerçekten koştuğunu sınar. Kurulum modunda bu
sapma kontrolü anlamsızdır (taze kopya bozulmayı ezer), bu yüzden ayrı moddur.

## HATTI SÜRME — `--agent` KULLANMAYIN  (ÖLÇÜM-02 K5/K6/K17)

**Önce temiz ağaç (v1.7.22, O3-04):** `kos_faz.sh --komut kod-faz0` yalnız
**temiz** git ağacında başlar. Kurulumun kendi kalıntılarını (`.gitignore`,
`kod_profil.json`, `scripts/` …) kod-faz0'dan ÖNCE commit'leyin; aksi hâlde
kapı hatı durdurur. Neden: kirli ağaçta ölçülen taban yeni testleri içine
alır ve RECK-07 zehirlenir. `_KOSU/` kirilik sayılmaz.

Üç ölçülmüş tuzak vardır:

1. **`opencode run --agent <alt-ajan>` sessizce düşer.** On ajandan dokuzu
   `mode: subagent`'tır. `--agent` ile çağrıldıklarında opencode stderr'e
   "Falling back to default agent" yazar, **exit=0 döner** ve ajanın istem
   metni de izin bloğu da HİÇ uygulanmaz. Doğru yol `--command <komut>`'tur.
2. **`-m` bayrağı komut yolunda yok sayılır.** Ajanın frontmatter `model:`
   satırı kazanır. Model değiştirmek için `scripts/apply_routing.py <profil>`
   kullanın, `-m` değil.
3. **Onay isteyen fazlar başsız koşuda 0 artefaktla exit=0 döner** (fail-OPEN).

Üçü birden `scripts/kos_faz.sh` ile kapatılır — ajan banner'ını doğrular,
zaman aşımı/yeniden deneme sarmalını uygular, artefaktın GERÇEKTEN oluştuğunu
sınar:

```
bash scripts/kos_faz.sh --komut kod-faz0 --ajan kod-scoper \
     --artefakt '_KOSU/00-KFAZ-0-*.md' --artefakt '_KOSU/gate/BASELINE.json' \
     -- "Ne inşa edilecek: ... Giriş modu: MEVCUT_KOD"
```

Çıkış kodları: `2` ajan düştü · `3` bütün denemeler asıldı · `4` artefakt yok.
