"""ORTAK kapi cekirdegi — iki hattin da import ettigi TEK kaynak.

NEDEN VAR:
Akademik hattaki `gate_merge.py` ve kod hattindaki `kod_gate_merge.py` ayni
kapi ilkelerini uygulamak zorundadir. Ilkeleri iki dosyaya KOPYALAMAK, birinde
duzeltilen bir kusurun otekinde yasamaya devam etmesi demektir. Bu modul o
ilkelerin tek kaynagidir.

ILKELER (Atlas v5.5.4'te kanitlanmis uc kusurdan tureme):
  1. KAPALI LISTE — taninmayan siddet/durum etiketi SESSIZCE dusmez, P0 sayilir.
     Kanit: `priority: "CRITICAL"` hicbir dala dusmuyordu; 3 bulgulu bir 2A
     dosyasi FINAL PASS veriyordu.
  2. NO_INSPECTION_EVIDENCE — hicbir denetim izi tasimayan kapi PASS veremez.
     Kanit: iki adet `{}` dosyasi FINAL PASS veriyordu.
     "Hicbir sey olcmemek, temiz cikmakla ayni sey degildir." (C1_SOZLESME §4)
  3. IDENTICAL_GATE_INPUTS — iki kapinin icerigi (zaman damgasi/etiket haric)
     birebir ayniysa bagimsizlik yoktur, P0. (C5_KAPILAR §2 kural 5)
  4. Kapi kendi `verdict`/`p0_count` beyanina GUVENILMEZ; sayilar her zaman ham
     dizilerden yeniden hesaplanir. Beyan ile hesap celisirse celiskinin
     KENDISI FAIL nedenidir.

BILINEN BORC: `ATLAS_SABLONLAR/scripts/gate_merge.py` bu modulu HENUZ import
etmiyor (mantigi kendi icinde tasiyor, 53 oz-test ona bagli). Bu modul o
dosyadan BIREBIR port edildi. Akademik hattin buraya tasinmasi WP4 isidir ve
YAPILMADI — iki kopya arasinda sapma riski acik durmaktadir.
"""
import copy, json

_TR = str.maketrans("İIŞĞÜÖÇı", "IISGUOCI")


def norm(x):
    """Siddet/durum etiketini karsilastirilabilir hale getir (TR karakter dahil)."""
    return str(x or "").strip().upper().translate(_TR).replace("-", "_").replace(" ", "_")


P0_ETIKET = {"P0", "CRITICAL", "KRITIK", "BLOCKER", "ENGELLEYICI", "SEV0", "S0", "FATAL"}
P1_ETIKET = {"P1", "HIGH", "YUKSEK", "MAJOR", "ONEMLI", "SEV1", "S1"}
P2_ETIKET = {"P2", "P3", "MEDIUM", "ORTA", "MINOR", "LOW", "DUSUK", "SEV2", "S2",
             "INFO", "BILGI", "NIT", "NOTE", "NOT"}

CHECK_GECER = {"GECTI", "GECER", "PASS", "PASSED", "OK", "TAMAM"}
CHECK_KALDI = {"KALDI", "FAIL", "FAILED", "HATA", "RED"}
CHECK_KOSMADI = {"CALISTIRILMADI", "NOT_RUN", "NOTRUN", "SKIPPED", "ATLANDI", "N/A", "NA"}

MR_KANITLI = {"UYGULANMIS_KANITLI", "KANITLI", "UYGULANMIS", "APPLIED_VERIFIED", "VERIFIED"}
MR_KANITSIZ = {"KANITSIZ", "UNVERIFIED", "NO_EVIDENCE"}
MR_UYGULANMAMIS = {"UYGULANMAMIS", "NOT_APPLIED", "PENDING", "BEKLIYOR"}
# v1.7.282 (ATLAS GM-17 · KOD GM-9) — GEREKCELI RED, "YAPILMADI" ILE AYNI KOVA DEGILDIR.
#   ONCE: kapali listede REDDEDILDI durumu YOKTU. Manifestte "reddedildi; degisiklik
#   yok" diye kaydedilen bir FIX, MR_UYGULANMAMIS'a dusuyor ve P1 sayiliyordu.
#   Olculdu (silat-makale, 10 Kasim 2026): FIX-024 (P2, reddedildi, gerekce
#   "ayri baslik GATE SCRIPTI ICIN zorunlu") yuzunden FINAL FAIL; yalniz o satirin
#   status'u degistirilince FINAL PASS-PENDING-ETHICS (rc=0). Yani gate KENDI
#   ihtiyaci icin verilmis gerekceli reddi engel sayiyordu.
#   SIMDI: gerekceli red ayri kovada SAYILIR: P0/P1 DEGIL, ama SESSIZ de degil —
#   rapor ve stdout'ta "REDDEDILEN_GEREKCELI" olarak gorunur.
#   Gerekcesiz/bos reddetme burada YOK: yalniz acik etiketler sayilir; taninmayan
#   etiket yine P0 (fail-closed korunur).
MR_REDDEDILDI = {"REDDEDILDI", "REDDEDILMIS", "GEREKCELI_RED", "REJECTED", "WONTFIX", "RED_DEGERLENDIRILDI"}

# Kod hattina ozgu ek durumlar (KFAZ3 kanit zinciri)
KOD_EK_P0 = {"EVIDENCE_UNVERIFIED", "SCOPE_VIOLATION", "GATE_TAMPERED", "UNSIGNED_WAIVER"}

# C-4: tasarim geregi acik kalan onay bekleyisi ayri sayilir. Baska engel yoksa
# verdict PASS-PENDING-ETHICS olur; muafiyet DEGILDIR, raporda gorunur kalir.
ETIK_BEKLIYOR = {"PENDING_ETHICS", "DEC_036_OPEN", "DEC-036-OPEN"}


def yukle(yol):
    import pathlib
    try:
        ham = pathlib.Path(yol).read_text()
    except Exception as e:
        return None, f"okunamadi: {e}"
    try:
        d = json.loads(ham)
    except Exception as e:
        return None, f"JSON gecersiz: {e}"
    if not isinstance(d, dict):
        return None, "JSON kok nesnesi dict degil"
    return d, None


def yeniden_say(kapi, etiket="?"):
    """P0/P1 sayilarini SADECE ham dizilerden hesapla. Metadata'ya bakma."""
    p0 = p1 = etik = 0
    ihlaller = []

    def dizi(ad):
        nonlocal p0
        if ad not in kapi:
            return []
        v = kapi.get(ad)
        if not isinstance(v, list):
            ihlaller.append(f"{etiket}: {ad} liste degil ({type(v).__name__}) -> P0")
            p0 += 1
            return []
        return v

    for i, f in enumerate(dizi("findings")):
        if not isinstance(f, dict):
            ihlaller.append(f"{etiket}: findings[{i}] nesne degil"); p0 += 1; continue
        ham = f.get("priority", f.get("severity", None))
        pr = norm(ham)
        etik_kimligi = (norm(f.get("id")) in ETIK_BEKLIYOR
                        or norm(f.get("kod")) in ETIK_BEKLIYOR)
        # Etik bekleyisi yalniz TANINAN P1/P2 bulguyu ayirir. Eksik/falsy/
        # konteyner siddet kapali liste dalinda P0 kalir.
        if etik_kimligi and (pr in P1_ETIKET or pr in P2_ETIKET):
            etik += 1
            continue
        if pr in P0_ETIKET or pr in KOD_EK_P0:
            p0 += 1
        elif pr in P1_ETIKET:
            p1 += 1
        elif pr in P2_ETIKET:
            pass
        elif not pr:
            ihlaller.append(f"{etiket}: findings[{i}] siddet alani YOK -> P0 sayildi"); p0 += 1
        else:
            ihlaller.append(f"{etiket}: findings[{i}] siddet '{ham}' kapali listede yok -> P0 sayildi"); p0 += 1

    for i, c in enumerate(dizi("checks")):
        if not isinstance(c, dict):
            ihlaller.append(f"{etiket}: checks[{i}] nesne degil"); p0 += 1; continue
        st = norm(c.get("status"))
        if st in CHECK_GECER:
            pass
        elif st in CHECK_KALDI:
            p1 += 1
        elif st in CHECK_KOSMADI:
            ihlaller.append(f"{etiket}: checks[{i}] ({c.get('id','?')}) CALISTIRILMADI -> P1"); p1 += 1
        elif st in MR_REDDEDILDI:
            # v1.7.284 (GM-18): ATLAS `gate_merge` ile AYNI ontoloji.
            # Gerekceli red ayri kovadir: P0/P1 DEGIL, sayacta ve raporda GORUNUR.
            # Gerekcesiz red KACIS olur -> P0 (fail-closed).
            if not (c.get("evidence") or c.get("kanit")
                    or c.get("reason") or c.get("gerekce")):
                ihlaller.append(f"{etiket}: checks[{i}] ({c.get('id','?')}) REDDEDILDI ama GEREKCE yok -> P0")
                p0 += 1
        elif not st:
            ihlaller.append(f"{etiket}: checks[{i}] durum alani YOK -> P0"); p0 += 1
        else:
            ihlaller.append(f"{etiket}: checks[{i}] durum '{c.get('status')}' kapali listede yok -> P0"); p0 += 1

    for i, m in enumerate(dizi("manifest_reconciliation")):
        if not isinstance(m, dict):
            ihlaller.append(f"{etiket}: manifest_reconciliation[{i}] nesne degil"); p0 += 1; continue
        st = norm(m.get("status"))
        if st in MR_KANITLI:
            pass
        elif st in MR_KANITSIZ:
            p0 += 1
        elif st in MR_UYGULANMAMIS:
            p1 += 1
        elif st in MR_REDDEDILDI:
            # v1.7.282 (ATLAS GM-17 · KOD GM-9): gerekceli red P0/P1 DEGIL — ayri kova.
            # Gerekcesiz red KACIS olur: evidence bos ise KANITSIZ sayilir (P0).
            if not (m.get("evidence") or m.get("reason") or m.get("gerekce")):
                ihlaller.append(f"{etiket}: manifest_reconciliation[{i}] REDDEDILDI ama GEREKCE yok -> P0")
                p0 += 1
        elif not st:
            ihlaller.append(f"{etiket}: manifest_reconciliation[{i}] durum YOK -> P0"); p0 += 1
        else:
            ihlaller.append(f"{etiket}: manifest_reconciliation[{i}] durum '{m.get('status')}' kapali listede yok -> P0"); p0 += 1

    return p0, p1, etik, ihlaller


def denetim_kaniti_var(kapi):
    """Kapi gercekten bir sey denetlemis mi? Ucu de bossa denetim yoktur."""
    for ad in ("checks", "findings", "manifest_reconciliation"):
        v = kapi.get(ad)
        if isinstance(v, list) and len(v) > 0:
            return True
    return False


def imza(kapi):
    """Iki kapiyi karsilastirmak icin oynak alanlardan arindirilmis imza."""
    d = copy.deepcopy(kapi) if isinstance(kapi, dict) else {}
    md = d.get("metadata")
    if isinstance(md, dict):
        md.pop("gate_date", None)
        md.pop("kapi_tarihi", None)
    for k in ("gate", "agent", "kapi", "ajan"):
        d.pop(k, None)
    return json.dumps(d, sort_keys=True, ensure_ascii=False)


def metadata_kok_ihlalleri(kapi, etiket="?"):
    if "metadata" not in kapi:
        return []
    meta = kapi.get("metadata")
    if isinstance(meta, dict):
        return []
    return [
        f"{etiket}: metadata gecersiz kok tip "
        f"({meta!r}, tip={type(meta).__name__}); JSON nesnesi olmali"
    ]


def metadata_sayac_ihlalleri(meta):
    if not isinstance(meta, dict):
        return []
    ihlaller = []
    for alan in ("p0_count", "p1_count"):
        if alan not in meta:
            continue
        deger = meta[alan]
        if type(deger) is not int or deger < 0:
            ihlaller.append(
                f"metadata.{alan} gecersiz sayac "
                f"({deger!r}, tip={type(deger).__name__}); "
                "negatif olmayan tam sayi olmali"
            )
    return ihlaller


def beyan_sayilari(kapi):
    meta = kapi.get("metadata", {})
    if not isinstance(meta, dict):
        return None, None
    return meta.get("p0_count"), meta.get("p1_count")


def reddedilen_kayitlar(kapi):
    """GEREKCELI REDDEDILMIS kayitlari dondur (gorunurluk icin).

    IKI KAYNAK: `checks[]` ve `manifest_reconciliation[]`. v1.7.284 (GM-18):
    onceden yalniz manifest taranirdi; `checks[]` icindeki gerekceli red
    sayacta gorunmez oluyordu (ayni ontoloji iki yerde farkli uygulaniyordu).
    But kayitlar P0/P1 SAYILMAZ ama SESSIZ de dusmez: cagiran taraf bunlari
    rapora ve stdout'a yazmakla yukumludur.
    """
    out = []
    for kaynak in ("checks", "manifest_reconciliation"):
        dizi = kapi.get(kaynak)
        if not isinstance(dizi, list):
            continue
        for i, m in enumerate(dizi):
            if not isinstance(m, dict):
                continue
            if norm(m.get("status")) in MR_REDDEDILDI:
                out.append({
                    "kaynak": kaynak,
                    "index": i,
                    "fix_id": (m.get("fix_id") or m.get("id")
                               or f"{kaynak}[{i}]"),
                    "status": m.get("status"),
                    "gerekce": (m.get("evidence") or m.get("reason")
                                or m.get("gerekce") or m.get("kanit")
                                or "(gerekce yok)"),
                })
    return out


def degerlendir(kapi, etiket):
    """Bir kapi JSON'u icin gercek verdict'i BAGIMSIZ hesapla."""
    p0, p1, etik, ihlaller = yeniden_say(kapi, etiket)
    beyan_verdict = norm(kapi.get("verdict", ""))
    metadata_ihlalleri = metadata_kok_ihlalleri(kapi, etiket)
    sayac_ihlalleri = metadata_sayac_ihlalleri(kapi.get("metadata"))
    dp0, dp1 = beyan_sayilari(kapi)

    kanit = denetim_kaniti_var(kapi)
    if not kanit:
        ihlaller.append(f"{etiket}: NO_INSPECTION_EVIDENCE — checks/findings/manifest_reconciliation UCU DE bos")

    gercek = "PASS" if (p0 == 0 and p1 == 0 and kanit) else "FAIL"

    celiski = bool(ihlaller or metadata_ihlalleri or sayac_ihlalleri)
    notlar = list(ihlaller) + metadata_ihlalleri + sayac_ihlalleri
    if beyan_verdict and beyan_verdict != gercek:
        celiski = True
        notlar.append(f"{etiket}: kapi verdict='{beyan_verdict}' ama yeniden hesaplanan='{gercek}'")
    if dp0 is not None and dp0 != p0:
        celiski = True; notlar.append(f"{etiket}: beyan p0_count={dp0} ama gercek={p0}")
    if dp1 is not None and dp1 != p1:
        celiski = True; notlar.append(f"{etiket}: beyan p1_count={dp1} ama gercek={p1}")

    return {"etiket": etiket, "gercek_verdict": gercek, "beyan_verdict": beyan_verdict or None,
            "p0": p0, "p1": p1, "etik_bekleyen": etik, "beyan_p0": dp0, "beyan_p1": dp1,
            # v1.7.282 (ATLAS GM-17): gerekceli red P0/P1 DEGIL ama SESSIZ de degil.
            # FINAL-KOD-GATE.json'da `kapilar[].reddedilen` altinda gorunur.
            "reddedilen": reddedilen_kayitlar(kapi),
            "celiski": celiski, "celiski_notlari": notlar, "kanit_var": kanit,
            "sema_ihlali": bool(ihlaller),
            "findings": kapi.get("findings", []) if isinstance(kapi.get("findings", []), list) else []}


def birlestir(sonuclar, imzalar):
    """N-of-N: hepsi PASS olmali, celiski olmamali, imzalar birbirinden farkli olmali."""
    notlar = []
    ayni = []
    for i in range(len(imzalar)):
        for j in range(i + 1, len(imzalar)):
            if imzalar[i] == imzalar[j]:
                ayni.append(f"IDENTICAL_GATE_INPUTS: {sonuclar[i]['etiket']} ve {sonuclar[j]['etiket']} "
                            f"icerigi birebir ayni — bagimsizlik yok (P0)")
    notlar.extend(ayni)
    for s in sonuclar:
        notlar.extend(s["celiski_notlari"])
    hepsi_pass = all(s["gercek_verdict"] == "PASS" for s in sonuclar)
    celiski_var = any(s["celiski"] for s in sonuclar)
    verdict = "PASS" if (hepsi_pass and not celiski_var and not ayni) else "FAIL"
    if verdict == "PASS" and sum(s.get("etik_bekleyen", 0) for s in sonuclar) > 0:
        verdict = "PASS-PENDING-ETHICS"
    return verdict, notlar
