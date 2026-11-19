#!/usr/bin/env python3
"""Yonlendirme Profili Uygulayici — TEK KAYNAK (O7-07, WP4 kapandi)

TEK KAYNAK: master `ORTAK/scripts/apply_routing.py`; KOD_SABLONLAR ve
ATLAS_SABLONLAR altindaki nushalar BAYT BIREBIR kopyadir (budget_guard O7-06
deseni; wrapper/symlink OLCUM-02 K1 dersi nedeniyle bilincli reddedildi).
HAT-BAGIMSIZLIK: tum yollar betigin KENDI konumunden cozulur; FAZ maliyet
tablosu her agacin KENDI routing.profiles.json'undaki `faz_maliyet` bloktan
okunur (O7-07: ATLAS'in gomulu tablosu kendi JSON'una tasindi) ve kapı
bagimsizlik kontrolu ONEK-NOTR'dur — kapı ajanlari `*-gate-2a`, `*-gate-2b`,
`*-gate-2c(-*)` kalibiyla bulunur; tek dosya iki hatta da hizmet eder.
`bedava` profili su an yalniz KOD hattindadir (O7-03, P2 kapsam disi).

NEDEN VAR:
opencode'un yapilandirma semasinda YEDEK MODEL ZINCIRI YOKTUR (`Config.Agent`
yalnizca tek bir `model` dizesi kabul eder; `fallback`/`retry` anahtari yok ve
sema `additionalProperties: false`). Bir saglayici duserse ya da butce
degisirse, 12 ajan dosyasindaki `model:` satirlarini ELLE degistirmek gerekir.
Bu betik onu tek komuta indirir ve degistirmeden ONCE kataloga dogrular.

Kullanim:
  python3 scripts/apply_routing.py                 # mevcut durumu goster
  python3 scripts/apply_routing.py denge --kuru    # ne degisecek (yazmadan)
  python3 scripts/apply_routing.py denge           # uygula
  python3 scripts/apply_routing.py --maliyet       # profilleri karsilastir
"""
import json, os, pathlib, re, sys

KOK = pathlib.Path(__file__).resolve().parent.parent
PROFIL = KOK / "routing.profiles.json"
AJAN = KOK / ".opencode" / "agent"
# OLCUM-P0-4 (31.08.2026): katalog yolu KULLANICI HESABINA baglidir; oz-test
# RT-1/RT-2 bu yuzden ortama gore sonuc veriyordu. Varsayilan DEGISMEDI —
# yalniz enjekte edilebilir yapildi ki test kendi fikstirini kullanabilsin.
KAT = pathlib.Path(os.environ.get("ATLAS_MODEL_KATALOG")
                   or os.path.expanduser("~/.cache/opencode/models.json"))

# Faz basina beklenen KUMULATIF girdi / cikti tokeni (20K kelimelik makale, tek tur).
# Kaynak: ajanli dongude her adimda tum baglam yeniden gonderilir.
# FAZ tablosu betigin bulundugu agacin routing.profiles.json'undaki
# `faz_maliyet` bloktan okunur; rol listesi boylece her hatta tek kaynakta durur.
def _faz_yukle():
    import json as _j
    d = _j.loads(PROFIL.read_text())
    fm = d.get("faz_maliyet") or {}
    return {k: tuple(v) for k, v in fm.items()}
FAZ = _faz_yukle()
CACHE_ORANI = 0.90   # olculen gercek oran %97; muhafazakar davraniliyor


def kat_yukle():
    if not KAT.exists():
        print(f"FAIL: model katalogu yok ({KAT})"); sys.exit(1)
    return json.loads(KAT.read_text())


def fiyat(kat, tam):
    prov, _, mid = tam.partition("/")
    v = kat.get(prov, {}).get("models", {}).get(mid)
    if not v:
        return None
    c = v.get("cost") or {}
    return (c.get("input") or 0, c.get("output") or 0,
            c.get("cache_read") if c.get("cache_read") is not None else (c.get("input") or 0),
            c.get("cache_write") or 0)


def kosu_maliyeti(kat, esleme):
    top = 0.0
    satir = []
    for ajan, (ad, gin, gout) in FAZ.items():
        model = esleme.get(ajan)
        f = fiyat(kat, model) if model else None
        if not f:
            satir.append((ad, model or "(yok)", None)); continue
        p_in, p_out, p_cr, p_cw = f
        taze = gin * (1 - CACHE_ORANI)
        onbellek = gin * CACHE_ORANI
        m = (taze * p_in + onbellek * p_cr + gout * p_out + onbellek * 0.02 * p_cw) / 1_000_000
        top += m
        satir.append((ad, model, m))
    return top, satir


def mevcut():
    d = {}
    for p in sorted(AJAN.glob("*.md")):
        m = re.search(r"^model:\s*(\S+)\s*$", p.read_text(encoding="utf-8"), re.M)
        d[p.stem] = m.group(1) if m else None
    return d


prof = json.loads(PROFIL.read_text(encoding="utf-8"))
kat = kat_yukle()
args = [a for a in sys.argv[1:] if not a.startswith("--")]
kuru = "--kuru" in sys.argv

if "--maliyet" in sys.argv or (not args and "--kuru" not in sys.argv):
    simdi = mevcut()
    t, _ = kosu_maliyeti(kat, simdi)
    print(f"=== MEVCUT DURUM ===  tahmini kosu: ${t:.2f}")
    for a in sorted(simdi):
        print(f"  {a:26s} {simdi[a] or '(model satiri yok -> global varsayilan)'}")
    print("\n=== PROFILLER ===")
    for ad, e in prof["profiller"].items():
        tt, _ = kosu_maliyeti(kat, e)
        print(f"  {ad:10s} ${tt:5.2f}/kosu · ${30/tt:5.1f} makale/ay ($30 limit) · {e['aciklama']}")
    print("\nUygulamak icin: python3 scripts/apply_routing.py <profil>")
    sys.exit(0)

if not args:
    print("Kullanim: apply_routing.py <profil> [--kuru] | --maliyet"); sys.exit(1)
ad = args[0]
if ad not in prof["profiller"]:
    print(f"FAIL: '{ad}' profili yok. Mevcut: {list(prof['profiller'])}"); sys.exit(1)
# META anahtarlar ajan eslemesi DEGILDIR; disarida birakilmazsa `apply_routing`
# onlari ajan sanip `.opencode/agent/bagimsizlik_feragati.md` arar (O3-09).
PROFIL_META = ("aciklama", "bagimsizlik_feragati", "feragat_gerekcesi")
profil_tanim = prof["profiller"][ad]
esleme = {k: v for k, v in profil_tanim.items() if k not in PROFIL_META}

# --- uygulamadan ONCE dogrula (fail-closed) ---
bozuk = []
for ajan, model in esleme.items():
    prov, _, mid = model.partition("/")
    v = kat.get(prov, {}).get("models", {}).get(mid)
    if v is None:
        bozuk.append(f"{ajan}: katalogda yok -> {model}")
    elif str(v.get("status", "")).lower() == "deprecated":
        bozuk.append(f"{ajan}: DEPRECATED -> {model}")
    elif not (v.get("reasoning") and v.get("tool_call")):
        bozuk.append(f"{ajan}: reasoning/tool_call yok -> {model}")
if bozuk:
    print(f"FAIL: '{ad}' profili uygulanamaz, {len(bozuk)} gecersiz model:")
    for b in bozuk:
        print(f"  {b}")
    sys.exit(1)

# --- gate bagimsizligi: 2A, 2B (ve varsa 2C) ayni aile olamaz ---
# OLCUM-02 K8 tarihce: kontrol once ATLAS ajan adlarini (`atlas-gate-2a/2b`)
# sabit ariyordu; KOD hattinda o anahtarlar YOKTUR ve koruma hic
# degerlendirilmiyordu (sabit-True ariza). O7-07'de kontrol ONEK-NOTR yapildi:
# kapı ajanlari profil icinde `*-gate-2a`, `*-gate-2b`, `*-gate-2c(-*)`
# kalibiyla bulunur; koruma artik iki hatta da gercektir.
def _aile(model):
    """`saglayici/aile/model` -> `aile`. Bilinmeyen bicimde tam dize doner."""
    parcalar = str(model or "").split("/")
    return parcalar[1] if len(parcalar) >= 2 else (parcalar[0] if parcalar else "")


def _bul(kalip):
    t = [k for k in esleme if re.search(kalip, k)]
    return t[0] if len(t) == 1 else None


_k2a = _bul(r"gate-2a$")
_k2b = _bul(r"gate-2b$")
_k2c = _bul(r"gate-2c($|-)")
_eksik = [k for k in (_k2a, _k2b) if not k]
if _eksik:
    print(f"FAIL: '{ad}' profilinde zorunlu kapi ajani(lari) tanimsiz "
          f"(*-gate-2a / *-gate-2b kalibinda): {_eksik} — "
          f"bagimsizlik DEGERLENDIRILEMEZ (fail-closed)")
    sys.exit(1)
# 2A vs 2B: 2-of-2 cekirdegi — PAZARLIK KONUSU DEGIL, FAIL.
_a, _b = _aile(esleme[_k2a]), _aile(esleme[_k2b])
# O3-09 (OLCUM-03): `$0` kosu icin `bedava` profili eklendi ve orada 2A=2B=2C
# ZORUNLU olarak ayni ailededir. Bu kural PAZARLIK KONUSU DEGILDIR, bu yuzden
# kaldirilmadi: profil ACIK bir `bagimsizlik_feragati` + `feragat_gerekcesi`
# tasimadikca hala FAIL'dir. Feragat varsa engel kalkar ama SESSIZ DEGILDIR —
# OLCULMEYEN kaydi basilir ve KFAZ4 sonuclari bagimsizlik acisindan gecersiz sayilir.
_feragat = bool(profil_tanim.get("bagimsizlik_feragati"))
_gerekce = profil_tanim.get("feragat_gerekcesi", "")
if _a == _b and not _feragat:
    print(f"FAIL: gate-2A ve gate-2B ayni model ailesinde '{_a}' "
          f"({esleme[_k2a]} / {esleme[_k2b]}) — 2-of-2 bagimsizligi kaybolur")
    print("      Bilincli istiyorsan profile `\"bagimsizlik_feragati\": true` ve "
          "`\"feragat_gerekcesi\": \"...\"` ekle (O3-09).")
    sys.exit(1)
if _a == _b and _feragat:
    print(f"UYARI: '{ad}' profilinde 2A ve 2B AYNI ailede ('{_a}') — bagimsizlik ACIK "
          f"FERAGATLE kaldirildi. Gerekce: {_gerekce or '(yazilmamis)'}")
    print("OLCULMEYEN: KFAZ4 kapi bagimsizligi · hangi_karari_etkiler: 2-of-2 oyunun "
          "bagimsiz sayilip sayilamayacagi · eksik_kanit: iki ayri aileyle kosu · siddet: P1")
# 2C kosulludur; carpismasi profilin ACIK bir tercihi olabilir (bkz. `ekonomi`
# profilinin kendi aciklamasi). Bu yuzden UYARI'dir, engel degil — ama sessiz
# de degildir: 3-of-3 iddiasi bu profilde gecersizdir.
_c = esleme.get(_k2c) if _k2c else None
if _c and _aile(_c) in (_a, _b):
    print(f"UYARI: gate-2C ({_c}) ailesi '{_aile(_c)}' 2A/2B ile ayni — bu profilde "
          f"3-of-3 bagimsizligi YOKTUR, guvenlik oyu bagimsiz sayilmaz")

simdi = mevcut()
degisen = [(a, simdi.get(a), m) for a, m in esleme.items() if simdi.get(a) != m]
eski_t, _ = kosu_maliyeti(kat, simdi)
yeni_t, satir = kosu_maliyeti(kat, esleme)

print(f"=== PROFIL: {ad} ===  {prof['profiller'][ad]['aciklama']}")
for a, e, y in degisen:
    print(f"  {a:26s} {e or '(yok)'}  ->  {y}")
if not degisen:
    print("  (degisiklik yok — zaten bu profildesin)")
print(f"\nTahmini kosu maliyeti: ${eski_t:.2f} -> ${yeni_t:.2f}"
      + (f"  ({(1-yeni_t/eski_t)*100:.0f}% dusus)" if eski_t > yeni_t > 0 else ""))
for fad, model, m in satir:
    print(f"    {fad:20s} {model:44s} ${m:.3f}" if m is not None else f"    {fad:20s} {model}")

if kuru:
    print("\n[--kuru] hicbir dosya yazilmadi.")
    sys.exit(0)
if not degisen:
    sys.exit(0)

n = 0
for a, _, y in degisen:
    p = AJAN / f"{a}.md"
    if not p.exists():
        print(f"UYARI: {p.name} yok, atlandi"); continue
    s = p.read_text(encoding="utf-8")
    s2 = re.sub(r"^model:\s*\S+\s*$", f"model: {y}", s, count=1, flags=re.M)
    if s2 == s:
        print(f"UYARI: {p.name} icinde 'model:' satiri bulunamadi, atlandi"); continue
    p.write_text(s2, encoding="utf-8"); n += 1
print(f"\n{n} ajan dosyasi guncellendi. SURUM.md'ye 1 satir yazmayi unutma.")
sys.exit(0)
