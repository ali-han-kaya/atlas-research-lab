#!/usr/bin/env python3
"""Atlas v5.5.4 Gate Merge — 2-of-2 Voting (guvenlik-sikilastirilmis)

Kullanim: python3 scripts/gate_merge.py gate/STRONG-gate-2a-v5.5.json gate/STRONG-gate-2b-v5.5.json

GUVENLIK ILKESI (P0-01 duzeltmesi):
Bu script agent'in kendi beyan ettigi `verdict` veya `metadata.p0_count/p1_count`
alanlarina GUVENMEZ. P0/P1 sayilari HER ZAMAN ham `findings`, `checks` ve
`manifest_reconciliation` dizilerinden yeniden hesaplanir. Agent beyani ile
yeniden hesaplanan deger celisirse bu celiskinin kendisi FAIL nedenidir
(metadata_mismatch).

v5.5.4 — UC EK KAPI (bagimsiz denetimde kanitlandi, bkz. atlas_selftest GM-5..GM-10):

1. KAPALI LISTE (schema_invalid): Siddet etiketi kapali listede olmalidir.
   ONCE: `priority: "CRITICAL"` hicbir dala dusmuyor ve SESSIZCE sayilmiyordu.
   Kanit: 3 bulgulu ("SQL enjeksiyonu"/CRITICAL, "kimlik dogrulama"/SEV0) bir
   2A dosyasi FINAL PASS veriyordu. Artik taninmayan etiket P0'dir.
   Ayni kural `checks[].status` ve `manifest_reconciliation[].status` icin de gecerli.

2. NO_INSPECTION_EVIDENCE: Bir kapi hicbir denetim izi tasimiyorsa (checks,
   findings, manifest_reconciliation UCU de bos/yok) o kapi PASS veremez.
   ONCE: iki adet `{}` dosyasi FINAL PASS veriyordu.
   "Hicbir sey olcmemek, temiz cikmakla ayni sey degildir." (C1_SOZLESME §4)

3. IDENTICAL_GATE_INPUTS: 2A ve 2B'nin icerigi (zaman damgasi ve etiket haric)
   birebir ayniysa bagimsizlik yoktur; bu P0'dir. (C5_KAPILAR §2 kural 5)

4. B-7 (lab v1.7.27): "0 bulgu" ile "0 UYGULANABILIR kontrol" ayrt edilir.
   Her kapi icin checks toplam/calisan/kosmadi sayilari hesaplanir; FINAL
   JSON'un counts alanina ve raporuna yazilir. Kosmadi kontroller zaten
   P1 sayildigi icin verdict etkilenmez — bu ekleme GORUNURLUK icindir:
   raporu okuyan, kacin kontrolun fiilen kostugunu gorur.

NOT (P1-9): SOLO profil mantigi routing seviyesinde final-release-only çalışır.
Gate davranışı bu adımda değiştirilmedi; sadece karar ve not dokümantasyonu
sürdürülmektedir.
"""
import copy, json, sys, pathlib
from datetime import datetime, timezone

# --- KAPALI LISTELER (C1_SOZLESME) --------------------------------------------
# C3 (TUR-7, WP4): kapi ilkeleri TEK kaynaktan — ORTAK/scripts/ortak_gate.py
# Akademik ve kod hatti ayni tablolari kullanir; birinde duzeltme otekinde de gecerli olur.
# Onceki surum bu tablolari burada KOPYALIYORDU; kopya riski acikti (iki dosya arasinda sapma).
_BURASI = pathlib.Path(__file__).resolve().parent
for _aday in (_BURASI.parent.parent / "ORTAK" / "scripts", _BURASI.parent / "ORTAK" / "scripts"):
    if (_aday / "ortak_gate.py").exists():
        sys.path.insert(0, str(_aday))
        break
else:
    print("FAIL: ORTAK/scripts/ortak_gate.py bulunamadi — kapi ilkeleri tek kaynaktan gelir")
    sys.exit(1)
_onceki_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    from ortak_gate import (
        P0_ETIKET as _P0, P1_ETIKET as _P1, P2_ETIKET as _P2,
        CHECK_GECER, CHECK_KALDI, CHECK_KOSMADI,
        MR_KANITLI, MR_KANITSIZ, MR_UYGULANMAMIS, MR_REDDEDILDI,
        reddedilen_kayitlar,
        ETIK_BEKLIYOR, KOD_EK_P0, norm,
    )
    # KOD'a ozgu ek P0'lari da P0 say (ATLAS'ta gorulurse gene P0 olmali)
    P0_ETIKET = _P0 | KOD_EK_P0
    P1_ETIKET = _P1
    P2_ETIKET = _P2
except ImportError as e:
    print(f"FAIL: ortak_gate import hatasi: {e}")
    sys.exit(1)
finally:
    sys.dont_write_bytecode = _onceki_bytecode

# Not: ETIK_BEKLIYOR (PENDING_ETHICS) C-4 geregi ayri sayilir — PASS-PENDING-ETHICS
# yalniz etik bekleniyorsa verilir, baska P0/P1 yine FAIL (muafiyet degil).


def load(p):
    try:
        raw = pathlib.Path(p).read_text()
    except Exception as e:
        return None, f"okunamadi: {e}"
    try:
        data = json.loads(raw)
    except Exception as e:
        return None, f"JSON gecersiz: {e}"
    if not isinstance(data, dict):
        return None, "JSON kok nesnesi dict degil"
    return data, None


def recompute_counts(gate, label="?"):
    """P0/P1 sayilarini SADECE ham dizilerden hesapla. Metadata'ya bakma.

    Kapali liste disindaki her etiket SCHEMA_INVALID'dir ve P0 sayilir:
    sessizce dusen bulgu olmaz (fail-closed)."""
    p0 = 0
    p1 = 0
    etik = 0
    ihlaller = []

    def dizi(ad):
        nonlocal p0
        if ad not in gate:
            return []
        v = gate.get(ad)
        if not isinstance(v, list):
            ihlaller.append(f"{label}: {ad} liste degil ({type(v).__name__}) -> P0")
            p0 += 1
            return []
        return v

    # --- findings ---
    for i, f in enumerate(dizi("findings")):
        if not isinstance(f, dict):
            ihlaller.append(f"{label}: findings[{i}] nesne degil"); p0 += 1; continue
        ham = f.get("priority", f.get("severity", None))
        pr = norm(ham)
        etik_kimligi = (norm(f.get("id")) in ETIK_BEKLIYOR
                        or norm(f.get("kod")) in ETIK_BEKLIYOR)
        # Etik bekleyisi yalniz TANINAN P1/P2 bulguyu ayri verdict'e tasir.
        # Eksik/falsy/konteyner siddet degeri muaf tutulmaz; asagidaki kapali
        # liste dali onu P0 sayar.
        if etik_kimligi and (pr in P1_ETIKET or pr in P2_ETIKET):
            etik += 1
            continue
        if pr in P0_ETIKET:
            p0 += 1
        elif pr in P1_ETIKET:
            p1 += 1
        elif pr in P2_ETIKET:
            pass  # bloklamaz ama dusmez: raporda gorunur
        elif not pr:
            ihlaller.append(f"{label}: findings[{i}] siddet alani YOK -> P0 sayildi"); p0 += 1
        else:
            ihlaller.append(f"{label}: findings[{i}] siddet '{ham}' kapali listede yok -> P0 sayildi"); p0 += 1

    # --- checks ---
    for i, c in enumerate(dizi("checks")):
        if not isinstance(c, dict):
            ihlaller.append(f"{label}: checks[{i}] nesne degil"); p0 += 1; continue
        st = norm(c.get("status"))
        if st in CHECK_GECER:
            pass
        elif st in CHECK_KALDI:
            p1 += 1
        elif st in CHECK_KOSMADI:
            # "olculmedi" temiz demek degildir (C1 §4)
            ihlaller.append(f"{label}: checks[{i}] ({c.get('id','?')}) CALISTIRILMADI -> P1"); p1 += 1
        elif st in MR_REDDEDILDI:
            # v1.7.284 (GM-18): ayni ontoloji `checks[]` icin de gecerli.
            # Gerekceli red ayri kovadir: P0/P1 DEGIL, ama sayacta GORUNUR.
            # Gerekcesiz red KACIS olur -> KANITSIZ ile ayni (P0).
            if not (c.get("evidence") or c.get("kanit") or c.get("reason") or c.get("gerekce")):
                ihlaller.append(f"{label}: checks[{i}] ({c.get('id','?')}) REDDEDILDI ama GEREKCE yok -> P0")
                p0 += 1
        elif not st:
            ihlaller.append(f"{label}: checks[{i}] durum alani YOK -> P0"); p0 += 1
        else:
            ihlaller.append(f"{label}: checks[{i}] durum '{c.get('status')}' kapali listede yok -> P0"); p0 += 1

    # --- manifest_reconciliation ---
    for i, m in enumerate(dizi("manifest_reconciliation")):
        if not isinstance(m, dict):
            ihlaller.append(f"{label}: manifest_reconciliation[{i}] nesne degil"); p0 += 1; continue
        st = norm(m.get("status"))
        if st in MR_KANITLI:
            pass
        elif st in MR_KANITSIZ:
            p0 += 1
        elif st in MR_UYGULANMAMIS:
            p1 += 1
        elif st in MR_REDDEDILDI:
            # v1.7.282 (GM-17): GEREKCELI RED ayri kovada. P0/P1 DEGIL.
            # Olculdu (silat, 10.11.2026): FIX-024 P2 + reddedildi -> P1 sanildi,
            # FINAL FAIL idi; yalniz bu satir degisince PASS-PENDING-ETHICS oldu.
            # Sessiz dusmez: evaluate() -> "reddedilen" + rapor + stdout.
            # Gerekcesiz red KACIS olur: evidence bos ise P0 (ortak_gate ile ayni kural).
            if not (m.get("evidence") or m.get("reason") or m.get("gerekce")):
                ihlaller.append(f"{label}: manifest_reconciliation[{i}] REDDEDILDI ama GEREKCE yok -> P0")
                p0 += 1
        elif not st:
            ihlaller.append(f"{label}: manifest_reconciliation[{i}] durum YOK -> P0"); p0 += 1
        else:
            ihlaller.append(f"{label}: manifest_reconciliation[{i}] durum '{m.get('status')}' kapali listede yok -> P0"); p0 += 1

    return p0, p1, etik, ihlaller


def denetim_kaniti_var(gate):
    """Kapi gercekten bir sey denetlemis mi? Ucu de bossa denetim yoktur."""
    for ad in ("checks", "findings", "manifest_reconciliation"):
        v = gate.get(ad)
        if isinstance(v, list) and len(v) > 0:
            return True
    return False


def imza(gate):
    """Iki kapiyi karsilastirmak icin oynak alanlardan arindirilmis imza."""
    d = copy.deepcopy(gate) if isinstance(gate, dict) else {}
    md = d.get("metadata")
    if isinstance(md, dict):
        md.pop("gate_date", None)
    for k in ("gate", "agent"):
        d.pop(k, None)
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def declared_counts(gate, label="?"):
    """Agent'in kendi beyan ettigi sayilar (sadece karsilastirma/seffaflik icin)."""
    meta = gate.get("metadata")
    if "metadata" not in gate:
        return None, None, []
    if not isinstance(meta, dict):
        return None, None, [
            f"{label}: metadata gecersiz kok tip "
            f"({meta!r}, tip={type(meta).__name__}); JSON nesnesi olmali"
        ]

    ihlaller = []

    def sayac(ad):
        if ad not in meta:
            return None
        deger = meta[ad]
        if type(deger) is not int or deger < 0:
            ihlaller.append(
                f"{label}: metadata.{ad} gecersiz sayac "
                f"({deger!r}, tip={type(deger).__name__}); "
                "negatif olmayan tam sayi olmali"
            )
            return None
        return deger

    return sayac("p0_count"), sayac("p1_count"), ihlaller


def check_stats(gate, label=""):
    """B-7: checks dizisinin fiili calisma istatistigi.
    2B kapisi icin manifest_reconciliation da sayilir (B-15 koruyucu)."""
    d = gate.get("checks", [])
    if not isinstance(d, list):
        d = []
    # 2B kapisi isini manifest_reconciliation'da yapiyor — o da sayilmalidir
    mr = gate.get("manifest_reconciliation", [])
    if not isinstance(mr, list):
        mr = []
    # Etiketlere gore kumele: 2B icin her ikisini birlestir
    items = d + (mr if label == "2B" else [])
    toplam = len(items)
    calisan = kosmadi = 0
    for c in items:
        st = norm(c.get("status")) if isinstance(c, dict) else ""
        if st in CHECK_GECER or st in CHECK_KALDI or st in MR_KANITLI:
            calisan += 1
        elif st in CHECK_KOSMADI or st in MR_UYGULANMAMIS:
            kosmadi += 1
    return {"toplam": toplam, "calisan": calisan, "kosmadi": kosmadi}


def evaluate(gate, label):
    """Bir gate JSON'u icin gercek verdict'i BAGIMSIZ hesapla."""
    p0, p1, etik, ihlaller = recompute_counts(gate, label)
    declared_verdict = norm(gate.get("verdict", ""))
    dp0, dp1, metadata_ihlalleri = declared_counts(gate, label)
    ck = check_stats(gate, label)
    _red = reddedilen_kayitlar(gate)

    # --- v1.7.284 (GM-18): SAYAC INVARIANT'I --------------------------------
    # Ontology uc kovalidir: her kontrol ya CALISTI, ya KOSMADI, ya GEREKCELI
    # REDDEDILDI. Bu yuzden:
    #     toplam == calisan + kosmadi + reddedilen
    # v1.7.282'de `reddedilen` kovasi eklendiginde bu denklem SESSIZCE degisti
    # (24 = 23 + 1 -> 24 = 23 + 0 + 1). Rapor okuyan kisi 23+0 != 24 gorup kayit
    # hatasi sanir. Fail-closed: invariant bozuksa kapi ACILMAZ.
    # Sayim `reddedilen_kayitlar()` ile AYNI kaynaktan gelir (checks + manifest),
    # ama `check_stats()`in SAYDIGI kaynaklarla SINIRLIDIR: 2A icin yalniz
    # `checks[]`, 2B icin `checks[]` + `manifest_reconciliation[]`.
    # Aksi halde 2A'da manifest'teki bir red sayilir ama toplamda olmadigi icin
    # invariant YANLIS yanar (fail-closed yanlis pozitif uretir).
    _sayilan_kaynaklar = {"checks"} | ({"manifest_reconciliation"} if label == "2B" else set())
    _red_say = sum(1 for r in _red if r.get("kaynak") in _sayilan_kaynaklar)
    _toplam_beklenen = ck["calisan"] + ck["kosmadi"] + _red_say
    if _toplam_beklenen != ck["toplam"]:
        ihlaller.append(
            f"{label}: SAYAC_INVARIANT — toplam={ck['toplam']} ama "
            f"calisan({ck['calisan']}) + kosmadi({ck['kosmadi']}) + reddedilen({_red_say}) "
            f"= {_toplam_beklenen}"
        )
        p0 += 1
    ck = dict(ck, reddedilen=_red_say)

    kanit_var = denetim_kaniti_var(gate)
    if not kanit_var:
        ihlaller.append(f"{label}: NO_INSPECTION_EVIDENCE — checks/findings/manifest_reconciliation UCU DE bos")

    # Gercek verdict SADECE yeniden hesaplanan sayilardan turetilir.
    # Denetim kaniti yoksa PASS verilemez.
    real_verdict = "PASS" if (p0 == 0 and p1 == 0 and kanit_var) else "FAIL"

    mismatch = False
    mismatch_notes = list(ihlaller) + metadata_ihlalleri
    if declared_verdict and declared_verdict != real_verdict:
        mismatch = True
        mismatch_notes.append(
            f"{label}: agent verdict='{declared_verdict}' ama yeniden hesaplanan='{real_verdict}'"
        )
    if ihlaller or metadata_ihlalleri:
        mismatch = True
    if dp0 is not None and dp0 != p0:
        mismatch = True
        mismatch_notes.append(f"{label}: agent p0_count={dp0} ama gercek={p0}")
    if dp1 is not None and dp1 != p1:
        mismatch = True
        mismatch_notes.append(f"{label}: agent p1_count={dp1} ama gercek={p1}")

    return {
        "label": label,
        "real_verdict": real_verdict,
        "declared_verdict": declared_verdict or None,
        "p0": p0,
        "p1": p1,
        "etik_bekleyen": etik,
        "reddedilen": reddedilen_kayitlar(gate),
        # GM-18: sayac invariant'inin UCUNCU kovasi (checks + manifest).
        "reddedilen_sayac": ck.get("reddedilen", 0),
        "declared_p0": dp0,
        "declared_p1": dp1,
        "mismatch": mismatch,
        "mismatch_notes": mismatch_notes,
        "kanit_var": kanit_var,
        "checks_toplam": ck["toplam"],
        "checks_calisan": ck["calisan"],
        "checks_kosmadi": ck["kosmadi"],
        "schema_ihlali": len(ihlaller) > 0,
        "findings": gate.get("findings", []) if isinstance(gate.get("findings", []), list) else [],
    }


if len(sys.argv) < 3:
    print("Kullanim: gate_merge.py 2a.json 2b.json")
    sys.exit(1)

a, err_a = load(sys.argv[1])
b, err_b = load(sys.argv[2])

if a is None or b is None:
    print(f"FAIL: JSON okunamadi. 2A: {err_a or 'ok'} | 2B: {err_b or 'ok'}")
    sys.exit(1)

res_a = evaluate(a, "2A")
res_b = evaluate(b, "2B")

identical_gate_inputs = imza(a) == imza(b)
mismatch_notes = res_a["mismatch_notes"] + res_b["mismatch_notes"]
if identical_gate_inputs:
    mismatch_notes.append("IDENTICAL_GATE_INPUTS")
any_mismatch = res_a["mismatch"] or res_b["mismatch"] or identical_gate_inputs
# 2-of-2: HER IKI gate'in GERCEK (yeniden hesaplanan) verdict'i PASS olmali.
# Metadata/agent-beyan celiskisi VARSA guven kirilmistir -> FAIL.
verdict = "PASS" if (res_a["real_verdict"] == "PASS" and res_b["real_verdict"] == "PASS" and not any_mismatch) else "FAIL"
_etik = res_a.get("etik_bekleyen", 0) + res_b.get("etik_bekleyen", 0)
if verdict == "PASS" and _etik > 0:
    verdict = "PASS-PENDING-ETHICS"

reason_parts = [
    f"2A={res_a['real_verdict']}(P0:{res_a['p0']},P1:{res_a['p1']})",
    f"2B={res_b['real_verdict']}(P0:{res_b['p0']},P1:{res_b['p1']})",
]
if any_mismatch:
    reason_parts.append("METADATA_MISMATCH")
# B-7: kosmayan kontrol varsa reason'da gorunur olsun
_kosmadi = res_a["checks_kosmadi"] + res_b["checks_kosmadi"]
if _kosmadi > 0:
    reason_parts.append(f"KOSMADI_KONTROL:{_kosmadi}")
reason = " ".join(reason_parts) + f" -> {verdict}"

all_findings = []
for res in (res_a, res_b):
    for f in res["findings"]:
        if isinstance(f, dict):
            entry = dict(f)
            entry["_source"] = res["label"]
            all_findings.append(entry)

out = {
    "atlas_version": "v5.5",
    "build": "v5.5.4",
    "gate_type": "FINAL-2-of-2",
    "verdict": verdict,
    "reason": reason,
    "gate_2a": res_a["real_verdict"],
    "gate_2b": res_b["real_verdict"],
    "counts": {
        "p0_2a": res_a["p0"], "p1_2a": res_a["p1"],
        "p0_2b": res_b["p0"], "p1_2b": res_b["p1"],
        # v1.7.282 (GM-17): gerekceli red ayri SAYILIR — P0/P1 degil, ama gorunur.
        # v1.7.284 (GM-18): sayim SAYACLA ayni kaynaktan gelir (checks + manifest);
        # aksi halde `calisan + kosmadi + reddedilen = toplam` denklemi raporla
        # tutmaz ve invariant'i denetleyen kapi kendi cikardigi sayiyi yalanlar.
        "reddedilen_2a": res_a.get("reddedilen_sayac", 0),
        "reddedilen_2b": res_b.get("reddedilen_sayac", 0),
        # B-7: fiilen calisan kontrol sayimi ("0 bulgu" != "0 uygulanan kontrol")
        "checks_toplam_2a": res_a["checks_toplam"], "checks_calisan_2a": res_a["checks_calisan"],
        "checks_kosmadi_2a": res_a["checks_kosmadi"],
        "checks_toplam_2b": res_b["checks_toplam"], "checks_calisan_2b": res_b["checks_calisan"],
        "checks_kosmadi_2b": res_b["checks_kosmadi"],
    },
    "metadata_integrity": {
        "mismatch_detected": any_mismatch,
        "mismatch_notes": mismatch_notes,
    },
    "findings": all_findings,
    "metadata": {"gate_date": datetime.now(timezone.utc).isoformat(), "voting": "2-of-2"},
}

pathlib.Path("gate").mkdir(exist_ok=True)
pathlib.Path("gate/FINAL-GATE-v5.5.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))

findings_md = "\n".join(
    f"- [{f.get('_source','?')}] {f.get('priority','?')} — {f.get('finding') or f.get('evidence') or f.get('issue') or '(detay yok)'} "
    f"(konum: {f.get('location','?')})"
    for f in all_findings
) or "(bulgu yok)"

mismatch_md = "\n".join(f"- {n}" for n in out["metadata_integrity"]["mismatch_notes"]) or "(yok)"

_red_a = res_a.get("reddedilen") or []
_red_b = res_b.get("reddedilen") or []
_all_red = _red_a + _red_b
reddedilen_md = "\n".join(
    f"- [{lbl}] {r['fix_id']} — {r['status']} — {r['gerekce']}"
    for lbl, lst in (("2A", _red_a), ("2B", _red_b)) for r in lst
) or "(gerekceli red yok)"

report = f"""# FINAL GATE RAPORU — v5.5.4

## Verdict: {verdict}
{reason}

## Gate 2A (kor denetim)
- Gercek verdict (yeniden hesaplanan): {res_a['real_verdict']}
- Agent beyani: {res_a['declared_verdict']}
- P0: {res_a['p0']}, P1: {res_a['p1']}

## Gate 2B (manifest dogrulama)
- Gercek verdict (yeniden hesaplanan): {res_b['real_verdict']}
- Agent beyani: {res_b['declared_verdict']}
- P0: {res_b['p0']}, P1: {res_b['p1']}

## Metadata Butunluk Kontrolu
Mismatch tespit edildi mi: {any_mismatch}
{mismatch_md}

## Fiilen Calisan Kontroller (B-7)
- 2A: {res_a['checks_calisan']} calisan / {res_a['checks_toplam']} toplam ({res_a['checks_kosmadi']} kosmadi)
- 2B: {res_b['checks_calisan']} calisan / {res_b['checks_toplam']} toplam ({res_b['checks_kosmadi']} kosmadi)
Not: kosmadi kontrol "temiz" degildir; her biri ayrica P1 olarak sayildi.

## Bulgu Detaylari
{findings_md}

## Gerekceli Reddedilen FIX'ler (GM-17)
Sayi: {len(_all_red)} (P0/P1 SAYILMAZ; gorunur kalir)
{reddedilen_md}

Tarih: {datetime.now(timezone.utc).isoformat()}
"""

pathlib.Path("04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md").write_text(report)

print(f"FINAL {verdict} {reason}")
if _all_red:
    print(f"REDDEDILEN_GEREKCELI: {len(_all_red)} "
          + " ".join(f"{r['fix_id']}={r['status']}"
                     + ("!GEREKCE-YOK" if r['gerekce'] == "(gerekce yok)" else "")
                     for r in _all_red))
sys.exit(0 if verdict in ("PASS", "PASS-PENDING-ETHICS") else 1)
