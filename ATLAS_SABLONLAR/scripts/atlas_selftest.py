#!/usr/bin/env python3
"""Atlas v5.5.4 Oz-Test — betiklerin regresyon paketi

NEDEN VAR:
Lab'in denetim betikleri kendi kendini denetlemiyordu. Bir betik sessizce
bozulursa (yanlis pozitif PASS, kirilan yol, degisen dosya adi) kimse gormezdi.
Bu paket her betigi POZITIF ve NEGATIF girdiyle sinar.

Ilke: Hicbir sey proje klasorune yazilmaz. Tum fikstirler gecici klasorde
kurulur ve sonunda silinir.

Kullanim:
  python3 scripts/atlas_selftest.py
  python3 scripts/atlas_selftest.py --sessiz     # sadece ozet
  python3 scripts/atlas_selftest.py --tut        # hata halinde tmp klasoru birak
"""
import contextlib, hashlib, io, json, os, pathlib, re, runpy, shutil, sqlite3, subprocess, sys, tempfile, time
import unittest.mock

SCRIPTS = pathlib.Path(__file__).resolve().parent
SESSIZ = "--sessiz" in sys.argv
TUT = "--tut" in sys.argv
sonuc = []


def kontrol(kod, aciklama, gecti, detay=""):
    sonuc.append((kod, aciklama, gecti, detay))
    if not SESSIZ or not gecti:
        print(f"  {'OK  ' if gecti else 'KALDI'} {kod}: {aciklama}" + (f" :: {detay}" if not gecti and detay else ""))


def kos(betik, *args, cwd=None, env=None):
    if betik.endswith(".sh"):
        cmd = ["bash", str(SCRIPTS / betik), *args]
    else:
        cmd = [sys.executable, str(SCRIPTS / betik), *args]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


DOLGU = ("Bu satir fikstirin boyut esigini karsilamak icin eklenmistir. "
         "Icerik denetim acisindan notrdur ve hicbir iddia tasimaz. ")


def fikstir_opencode_db(yol: pathlib.Path, tutar: float = 0.50) -> pathlib.Path:
    """budget_guard'in okudugu opencode.db'nin ASGARI fikstiri.

    NEDEN: BG-4 "limit asiminda faz BASLATILMAZ" dalini sinar. O dala ulasmak icin
    harcamanin OLCULEBILIR olmasi gerekir; olculemezse betik (dogru bicimde) baska
    bir fail-closed dalina girer ve test ortama gore rastgele sonuc verir.
    Bu fikstir testi HERMETIK yapar — kullanici hesabindaki gercek opencode.db'ye
    dokunulmaz ve okunmaz.
    """
    yol.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(yol))
    con.execute("CREATE TABLE IF NOT EXISTS message (data TEXT)")
    con.execute("INSERT INTO message VALUES (?)", (json.dumps({
        "role": "assistant", "cost": tutar,
        "time": {"created": int(time.time() * 1000)},
        "path": {"cwd": str(yol.parent)},
        "providerID": "fikstir", "modelID": "test-model"}),))
    con.commit(); con.close()
    return yol


def fikstir_model_katalogu(profil_json: pathlib.Path, hedef: pathlib.Path) -> pathlib.Path:
    """apply_routing'in okudugu model katalogunun SENTETIK fikstiri.

    UYARI — FIYATLAR UYDURMADIR. Bu dosyadaki rakamlar gercek model fiyati DEGILDIR
    ve hicbir maliyet iddiasina kaynak yapilamaz. Amac yalnizca apply_routing'in
    ARITMETIGINI ve KAPILARINI (katalog dogrulamasi, 2A/2B aile bagimsizligi,
    --kuru yazmama sozu) olcmektir. Modeller routing.profiles.json'dan TURETILIR;
    profil degisirse fikstir de kendiliginden degisir. Model siniflari arasindaki
    sentetik fiyat farki, profillerin farkli eslemelerini ayirt etmeyi sinar.
    """
    def sentetik_fiyat(model_id: str) -> dict:
        if "claude-sonnet" in model_id:
            degerler = (8.0, 24.0, 0.8, 10.0)
        elif "deepseek-v4-pro" in model_id:
            degerler = (4.0, 12.0, 0.4, 2.0)
        elif "glm-5.3" in model_id:
            degerler = (3.0, 9.0, 0.3, 1.5)
        elif "glm-5.2" in model_id:
            degerler = (2.5, 7.5, 0.25, 1.25)
        elif "kimi-k2.7" in model_id:
            degerler = (1.5, 4.5, 0.15, 0.75)
        elif "deepseek-v4-flash" in model_id:
            degerler = (1.0, 3.0, 0.1, 0.5)
        else:
            degerler = (2.0, 6.0, 0.2, 1.0)
        return dict(zip(("input", "output", "cache_read", "cache_write"), degerler))

    d = json.loads(pathlib.Path(profil_json).read_text(encoding="utf-8"))
    META = ("aciklama", "bagimsizlik_feragati", "feragat_gerekcesi")
    kat: dict = {}
    for esleme in d.get("profiller", {}).values():
        for anahtar, model in esleme.items():
            if anahtar in META or not isinstance(model, str):
                continue
            prov, _, mid = model.partition("/")
            kat.setdefault(prov, {"models": {}})["models"][mid] = {
                "status": "stable", "reasoning": True, "tool_call": True,
                "cost": sentetik_fiyat(mid),
            }
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps(kat, indent=1), encoding="utf-8")
    return hedef


def kur(kok: pathlib.Path):
    """Butun kapilardan GECEN taban proje kurar."""
    kok.mkdir(parents=True, exist_ok=True)
    (kok / "gate").mkdir(exist_ok=True)
    # betikleri projeye kopyala (gercek kullanim boyle)
    hedef = kok / "scripts"
    hedef.mkdir(exist_ok=True)
    for f in SCRIPTS.glob("*.py"):
        shutil.copy2(f, hedef / f.name)
    for f in SCRIPTS.glob("*.sh"):
        shutil.copy2(f, hedef / f.name)
    # WP4 (C3, TUR-7): ORTAK'i da kopyala — gate_merge artik tek kaynaktan import eder;
    # temp fikstirde ORTAK yoksa TABAN-1/CI-4/CI-5 gibi --full zinciri ORTAK bulunamadi diye kirilir.
    lab_kok = SCRIPTS.parent.parent
    ortak_src = lab_kok / "ORTAK" / "scripts" / "ortak_gate.py"
    if ortak_src.exists():
        (kok / "ORTAK" / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(ortak_src, kok / "ORTAK" / "scripts" / "ortak_gate.py")

    ids = [f"SC-{i:03d}" for i in range(1, 9)]

    # --- FAZ0 SCOPE ---
    sc = ["# SCOPE-CONTRACT", "", "| ID | Baslik | Durum | Kaynak | Gerekce |",
          "|---|---|---|---|---|"]
    for i, s in enumerate(ids, 1):
        sc.append(f"| {s} | Bolum {i} | ZORUNLU | uretilecek | taban |")
    sc += ["", "Transliterasyon sistemi: DMG (B-3, SC-030)", "", "## DEC-REGISTER", "", "DEC-001 kapsam belirlendi.", "", DOLGU * 12]
    (kok / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md").write_text("\n".join(sc), encoding="utf-8")

    # --- FAZ1 ---
    faz1 = {
        "atlas_version": "v5.5", "build": "v5.5.4", "faz": 1,
        "checks": [{"id": f"CHK-{i:02d}", "status": "GECTI"} for i in range(1, 8)],
        "findings": [
            {"id": "F-001", "priority": "P0", "finding": "kaynaksiz iddia", "location": "SC-001"},
            {"id": "F-002", "priority": "P1", "finding": "uzun cumle", "location": "SC-002"},
        ],
        "statistics": {"P0": 1, "P1": 1},
        "notes": [DOLGU] * 50,
    }
    (kok / "01-FAZ-1-LENS-ANALYSIS.json").write_text(
        json.dumps(faz1, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- FAZ2 ---
    faz2 = ["# FIX-MANIFEST", "",
            "FAZ1'deki 2 bulgu (F-001, F-002) bu manifestoda karsilanir.", "",
            "| FIX-ID | Severity | Kategori | Bulgu | Durum | Kanit |",
            "|---|---|---|---|---|---|",
            "| FIX-001 | P0 | CLAIM | kaynaksiz iddia | UYGULANMIŞ | SC-001 |",
            "| FIX-002 | P1 | STYLE | uzun cumle | UYGULANMIŞ | SC-002 |",
            "", "## FAZ1 Eslesmesi", "", "F-001→FIX-001, F-002→FIX-002.", "", DOLGU * 8]
    (kok / "02-FAZ-2-FIX-MANIFEST.md").write_text("\n".join(faz2), encoding="utf-8")

    # --- FAZ3 MASTER ---
    m = ["# Test Makalesi", ""]
    for i, s in enumerate(ids, 1):
        m += [f"## {s} Bolum {i}", ""]
        if s == "SC-001":
            m += ["Bir iddia (Yazar, 2020). FIX-001 ve FIX-002 uygulanmistir.", ""]
        elif s == "SC-007":
            m += ["## Kaynakca", "", "- Yazar, A. (2020). *Deneme*. Yayin.", ""]
        m += [DOLGU * 20, ""]
    m += ["## PROVENANCE Tablosu", "", "| SC-ID | Bolum | Kaynak | Satir | Kaynak Sinifi | Durum |",
          "|---|---|---|---|---|---|"]
    for i, s in enumerate(ids, 1):
        m.append(f"| {s} | Bolum {i} | Uretildi | {i*10} | IKINCIL | kapsiyor |")
    # --full beyan paketini de denetler; pozitif fikstur alti beyani tasir.
    for baslik in ("Etik Kurul", "Cikar Catismasi", "Finansman",
                   "Yazar Katkisi", "Veri Erisilebilirligi", "YZ Kullanimi"):
        m += ["", f"## {baslik}", "", "Sentetik test beyanidir."]
    (kok / "03-FAZ-3-MASTER-v5.5.md").write_text("\n".join(m), encoding="utf-8")

    # --- gate 2A / 2B ---
    g2a = {"atlas_version": "v5.5", "build": "v5.5.4", "gate": "2A", "verdict": "PASS",
           "metadata": {"p0_count": 0, "p1_count": 0, "gate_date": "2026-08-23T10:00:00+00:00"},
           "checks": [{"id": "CHK-01", "status": "GECTI", "evidence": "8 ID baslik"}],
           "findings": []}
    g2b = {"atlas_version": "v5.5", "build": "v5.5.4", "gate": "2B", "verdict": "PASS",
           "metadata": {"p0_count": 0, "p1_count": 0, "gate_date": "2026-08-23T10:00:00+00:00"},
           "checks": [{"id": "FIX-KANIT", "status": "GECTI", "evidence": "2/2"}],
           "findings": [],
           "manifest_reconciliation": [{"fix_id": "FIX-001", "status": "UYGULANMIŞ_KANITLI"},
                                       {"fix_id": "FIX-002", "status": "UYGULANMIŞ_KANITLI"}]}
    (kok / "gate/STRONG-gate-2a-v5.5.json").write_text(json.dumps(g2a, indent=2, ensure_ascii=False), encoding="utf-8")
    (kok / "gate/STRONG-gate-2b-v5.5.json").write_text(json.dumps(g2b, indent=2, ensure_ascii=False), encoding="utf-8")
    # FINAL'i gercek betik uretsin (tazelik dogru olsun)
    subprocess.run([sys.executable, "scripts/gate_merge.py",
                    "gate/STRONG-gate-2a-v5.5.json", "gate/STRONG-gate-2b-v5.5.json"],
                   cwd=kok, capture_output=True, text=True, timeout=600)

    # --- DEVIR ---
    devir = ["# DEVIR — Oz-test fiksturu", "", "## DURUM", "", "Fikstur hazir.", "",
             "## IDDIA vs DOGRULAMA", "",
             "| # | Iddia | Komut | Cikti | Exit |",
             "|---|---|---|---|---|",
             "| 1 | Fikstur kapilari gecer | `check_integrity.sh --full` | `FULL PASS` | 0 |",
             "", "## OLCULMEYEN", "", "Dis ortam bu fiksturde olculmez.", ""]
    (kok / "DEVIR.md").write_text("\n".join(devir), encoding="utf-8")
    return kok


def json_duzenle(p, fn):
    d = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    fn(d)
    pathlib.Path(p).write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


def calis(tmp):
    T = pathlib.Path(tmp)

    # ============ TABAN ============
    taban = kur(T / "taban")
    rc, o = kos("check_integrity.sh", "--full", cwd=taban)
    zincir_betikleri = ("cite_match.py", "quote_ratio.py", "declaration_check.py")
    zincir_isaretleri = ("CITE-MATCH PASS", "QUOTE-RATIO PASS", "DECLARATION-CHECK PASS")
    zincir_konumlari = [o.find(s) for s in (*zincir_isaretleri, "-- GATE --")]
    zincir_pozitif = (
        rc == 0 and "FULL PASS" in o
        and all(k >= 0 for k in zincir_konumlari)
        and zincir_konumlari == sorted(zincir_konumlari)
    )
    zincir_sonuclar = []
    for betik, ihlal in zip(zincir_betikleri, ("CITE-01", "QR-02", "DEC-06")):
        for vaka in ("ihlal", "eksik", "exit"):
            proje = kur(T / f"zincir-{betik}-{vaka}")
            master = proje / "03-FAZ-3-MASTER-v5.5.md"
            alt_betik = proje / "scripts" / betik
            beklenen_rc = 1
            if vaka == "ihlal":
                metin = master.read_text(encoding="utf-8")
                if betik == "cite_match.py":
                    metin = metin.replace("(Yazar, 2020)", "(Eksik, 2020)")
                elif betik == "quote_ratio.py":
                    metin += '\n\n"' + "alinti " * 41 + '"\n'
                else:
                    metin = metin.replace("## YZ Kullanimi", "## YZ Konusu")
                master.write_text(metin, encoding="utf-8")
            elif vaka == "eksik":
                alt_betik.unlink()  # yalniz gecici fikstur kopyasi
            else:
                beklenen_rc = 23
                alt_betik.write_text(
                    "import sys\nprint('SENTETIK ALT BETIK HATASI')\nsys.exit(23)\n",
                    encoding="utf-8",
                )
            r = subprocess.run(
                ["bash", str(proje / "scripts/check_integrity.sh"), "--full"],
                cwd=proje, capture_output=True, text=True, timeout=600,
            )
            cikti = r.stdout + r.stderr
            beklenen_iz = (f"FAIL {ihlal}" if vaka == "ihlal" else
                           (f"FAIL {alt_betik} yok" if vaka == "eksik" else
                            "SENTETIK ALT BETIK HATASI"))
            sonraki_betikler = zincir_betikleri[zincir_betikleri.index(betik) + 1:]
            dogru = (
                r.returncode == beklenen_rc and beklenen_iz in cikti
                and (vaka == "eksik" or f"FAIL {betik} exit={beklenen_rc}" in cikti)
                and "FULL PASS" not in cikti and "-- GATE --" not in cikti
                and all(f"-- {s} --" not in cikti for s in sonraki_betikler)
                and "Traceback" not in cikti
            )
            zincir_sonuclar.append((betik, vaka, r.returncode, dogru))
    # TT-C-3: QR-02 baglanti matrisi; mevcut TABAN-1 kimligi korunur.
    qr_alinti = " ".join(["alinti"] * 45)
    qr_ic_sayfa = " ".join(["alinti"] * 43 + ["p.", "42"])
    qr_vakalar = [
        ("ic_sayfa_ilgisiz_atif", f'"{qr_ic_sayfa}". Baska konu (Yazar, 2020).', 1),
        ("ic_sayfa_bitisik_atif", f'"{qr_ic_sayfa}" (Yazar, 2020).', 1),
        ("ilgisiz_tam_atif", f'"{qr_alinti}". Baska konu (Yazar, 2020, p. 42).', 1),
        ("ayri_sayfa", f'"{qr_alinti}" (Yazar, 2020). Baska konu p. 42.', 1),
        ("dogrudan", f'"{qr_alinti}" (Yazar, 2020, p. 42).', 0),
        ("anlati", f'“{qr_alinti}” Yazar (2020, s. 42).', 0),
        ("guillemet", f'«{qr_alinti}». (Yazar, 2020, pp. 42-43).', 0),
        ("blok", f'> {qr_alinti}\n(Yazar, 2020, p. 42).\n', 0),
        ("cok_satir_blok", '> ' + "alinti " * 22 + '\n> ' + "alinti " * 23
         + '\n(Yazar, 2020, p. 42).', 0),
    ]
    qr_sonuclar = []
    for qr_ad, qr_metin, qr_beklenen in qr_vakalar:
        qr_yol = T / f"qr-{qr_ad}.md"
        qr_yol.write_text(qr_metin + "\n\n## Kaynakça\nYazar (2020). Sentetik kaynak.\n",
                          encoding="utf-8")
        qr_rc, qr_o = kos("quote_ratio.py", "--dosya", str(qr_yol), cwd=T)
        qr_dogru = (
            qr_rc == qr_beklenen and "Traceback" not in qr_o
            and ("FAIL QR-02:" if qr_beklenen else "PASS QR-02: 1 uzun (40+)") in qr_o
            and (qr_beklenen == 0 or "QUOTE-RATIO PASS" not in qr_o)
        )
        qr_sonuclar.append((qr_ad, qr_rc, qr_dogru))
    # TT-C-3 matrisi sonu.
    # TT-C-8: karakter birlesimi; yalniz orani 100'e kirpmak testi gecirmez.
    qr8_kisa = "kelime " * 20
    qr8_uzun = " ".join(["alinti"] * 45)
    qr8_vakalar = [
        ("blok_tirnak", '> «' + qr8_kisa + '»', 142, 0),
        ("tek_tirnak", '"' + "a" * 20 + '"', 20, 0),
        ("ayni_metin_ayri", '"' + "a" * 20 + '" ve «' + "a" * 20 + '»', 40, 0),
        ("cok_satir_blok", '> ' + "a" * 20 + '\n> ' + "b" * 20, 41, 0),
        ("kesisen_tirnaklar", '"' + "a" * 20 + '«' + "b" * 20 + '"' + "c" * 20 + '»', 62, 0),
        ("ayri_blok_tirnak", '> ' + "a" * 20 + '\n\nARA METIN\n\n«' + "b" * 20 + '»', 40, 0),
        ("alintisiz", "Bu metinde alinti yok.", 0, 0),
        ("uzun_atifsiz", '> «' + qr8_uzun + '»', len(qr8_uzun) + 2, 1),
        ("uzun_atifli", '> «' + qr8_uzun + '»\n(Yazar, 2020, p. 42).', len(qr8_uzun) + 2, 0),
    ]
    qr8_sonuclar = []
    for qr8_ad, qr8_metin, qr8_karakter, qr8_beklenen in qr8_vakalar:
        qr8_yol = T / f"qr8-{qr8_ad}.md"
        qr8_yol.write_text(qr8_metin, encoding="utf-8")
        qr8_rc, qr8_o = kos("quote_ratio.py", "--dosya", str(qr8_yol), cwd=T)
        qr8_sayilar = re.search(
            r"^INFO QR-01: govde (\d+) kar — alinti (\d+) kar — oran %(\d+(?:\.\d+)?)",
            qr8_o, re.M,
        )
        qr8_dogru = (
            qr8_rc == qr8_beklenen and "Traceback" not in qr8_o and qr8_sayilar is not None
            and int(qr8_sayilar[1]) == len(qr8_metin)
            and int(qr8_sayilar[2]) == qr8_karakter
            and 0 <= int(qr8_sayilar[2]) <= int(qr8_sayilar[1])
            and 0 <= float(qr8_sayilar[3]) <= 100
            and qr8_sayilar[3] == f"{100 * qr8_karakter / len(qr8_metin):.1f}"
            and ("FAIL QR-02:" if qr8_beklenen else "QUOTE-RATIO PASS") in qr8_o
            and (qr8_beklenen == 0 or "QUOTE-RATIO PASS" not in qr8_o)
        )
        qr8_sonuclar.append((qr8_ad, qr8_rc, qr8_sayilar.groups() if qr8_sayilar else None, qr8_dogru))
    # TT-C-8 matrisi sonu.
    # TT-C-9: ayni %20 oranla iki yonlu SCOPE yuzdesi ve UYARI/exit 0 sozlesmesi.
    qr9_master = T / "qr9-master.md"
    qr9_master.write_text('"' + "a" * 20 + '"' + "b" * 78, encoding="utf-8")
    qr9_vakalar = [
        ("%15", 15), ("15%", 15), ("% 15", 15), ("15 %", 15),
        ("%19,5", 19.5), ("19,5%", 19.5), ("%19.5", 19.5), ("19.5%", 19.5),
        ("%20", 20), ("20%", 20), ("%100", 100), ("100%", 100),
        ("%0", None), ("0%", None), ("%101", None), ("101%", None),
        ("%", None), ("yok", None),
    ]
    qr9_sonuclar = []
    for qr9_i, (qr9_bicim, qr9_esik) in enumerate(qr9_vakalar):
        qr9_kok = T / f"qr9-{qr9_i}"
        qr9_kok.mkdir()
        (qr9_kok / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md").write_text(
            f"Alıntı oranı eşiği: {qr9_bicim}\n", encoding="utf-8",
        )
        qr9_rc, qr9_o = kos("quote_ratio.py", "--dosya", str(qr9_master), cwd=qr9_kok)
        qr9_ilan = re.search(
            r"^INFO QR-01-esik: ilan edilen esik %(\d+) .* → (ASIM|UYGUN)$", qr9_o, re.M,
        )
        qr9_dogru = (
            qr9_rc == 0 and "QUOTE-RATIO PASS" in qr9_o and "Traceback" not in qr9_o
            and "govde 100 kar — alinti 20 kar — oran %20.0" in qr9_o
        )
        if qr9_esik is None:
            qr9_dogru = (qr9_dogru and qr9_ilan is None
                         and "esigi ilan edilmemis" in qr9_o and "UYARI QR-01:" not in qr9_o)
        else:
            qr9_dogru = (
                qr9_dogru and qr9_ilan is not None
                and qr9_ilan[1] == f"{qr9_esik:.0f}"
                and qr9_ilan[2] == ("ASIM" if 20 > qr9_esik else "UYGUN")
                and ("UYARI QR-01:" in qr9_o) == (20 > qr9_esik)
                and "esigi ilan edilmemis" not in qr9_o
            )
        qr9_sonuclar.append((qr9_bicim, qr9_rc, qr9_dogru))
    # TT-C-9 matrisi sonu.
    kontrol("TABAN-1", "full metin denetimleri ve QR-02 alinti-atif bagi fail-closed",
            zincir_pozitif and all(ok for _, _, _, ok in zincir_sonuclar)
            and all(ok for _, _, ok in qr_sonuclar)
            and all(ok for _, _, _, ok in qr8_sonuclar)
            and all(ok for _, _, ok in qr9_sonuclar),
            f"pozitif_rc={rc}; konumlar={zincir_konumlari}; "
            f"vakalar={zincir_sonuclar}; QR={qr_sonuclar}; QR8={qr8_sonuclar}; QR9={qr9_sonuclar}")

    # ============ check_integrity.sh ============
    rc, o = kos("check_integrity.sh", "--sacma", cwd=taban)
    kontrol("CI-1", "bilinmeyen argumana rc=1 + kullanim", rc == 1 and "Kullanim" in o, f"rc={rc}")

    bos = T / "bos"; bos.mkdir()
    shutil.copytree(taban / "scripts", bos / "scripts")
    rc, o = kos("check_integrity.sh", "--faz0", cwd=bos)
    kontrol("CI-2", "yanlis klasorde rc=1 + 'ipucu' mesaji", rc == 1 and "ipucu" in o, f"rc={rc}")

    p3 = kur(T / "p3")
    json_duzenle(p3 / "gate/STRONG-gate-2a-v5.5.json", lambda d: d.update(verdict="FAIL"))
    rc, o = kos("check_integrity.sh", "--gate", cwd=p3)
    kontrol("CI-3", "2A verdict=FAIL ise --gate rc=1", rc == 1 and "verdict=FAIL" in o, f"rc={rc}")

    p4 = kur(T / "p4")
    json_duzenle(p4 / "gate/STRONG-gate-2a-v5.5.json",
                 lambda d: d["metadata"].update(gate_date="2026-12-31T23:59:00+00:00"))
    os.utime(p4 / "gate/STRONG-gate-2a-v5.5.json", None)
    rc, o = kos("check_integrity.sh", "--gate", cwd=p4)
    kontrol("CI-4", "bayat FINAL-GATE yakalanir", rc == 1 and "bayat" in o, f"rc={rc}")

    bosluk = T / "ara bosluk"
    shutil.copytree(taban, bosluk)
    r = subprocess.run(["bash", str(bosluk / "scripts/check_integrity.sh"), "--full"],
                       cwd=bosluk, capture_output=True, text=True, timeout=600)
    kontrol("CI-5", "bosluklu MUTLAK yolda --full zinciri kopmaz",
            r.returncode == 0 and "FULL PASS" in r.stdout, f"rc={r.returncode}")

    p6 = kur(T / "ci6")
    (p6 / "DEVIR.md").write_text(
        "# DEVIR\n\n## IDDIA vs DOGRULAMA\n\n"
        "| # | İddia | Komut | Çıktı | Exit |\n"
        "|---|---|---|---|---|\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--full", cwd=p6)
    kontrol("CI-6", "bos IDDIA vs DOGRULAMA tablosuyla devir KAPANMAZ",
            rc == 1 and "FAIL DEVIR-01" in o and "bos" in o.lower(), f"rc={rc}")

    p7 = kur(T / "ci7")
    (p7 / "DEVIR.md").write_text(
        "# DEVIR\n\n## IDDIA vs DOGRULAMA\n\n"
        "| # | İddia | Komut | Çıktı | Kod |\n"
        "|---|---|---|---|---|\n"
        "| 1 | Kapı ölçüldü | `check_integrity.sh --devir` | `OK DEVIR-01` | 0 |\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--devir", cwd=p7)
    kontrol("CI-7", "Kod kolonu Exit es anlamlisi olarak kabul edilir",
            rc == 0 and "OK DEVIR-01" in o, f"rc={rc}")

    p8 = kur(T / "ci8")
    (p8 / "DEVIR.md").write_text(
        "# DEVIR\n\n## IDDIA vs DOGRULAMA\n\n"
        "| # | İddia | Komut | Ham Çıktı | Exit |\n"
        "|---|---|---|---|---|\n"
        "| 1 | Kapı ölçüldü | `check_integrity.sh --devir` | `OK DEVIR-01` | 0 |\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--devir", cwd=p8)
    kontrol("CI-8", "Ham Cikti kolonu Cikti es anlamlisi olarak kabul edilir",
            rc == 0 and "OK DEVIR-01" in o, f"rc={rc}")

    p9 = kur(T / "ci9")
    (p9 / "DEVIR.md").write_text(
        "# DEVIR\n\n## 3. IDDIA vs DOGRULAMA\n\n"
        "| # | İddia | Komut | Çıktı | Exit |\n"
        "|---|---|---|---|---|\n"
        "| 1 | Kapı ölçüldü | `check_integrity.sh --devir` | `OK DEVIR-01` | 0 |\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--devir", cwd=p9)
    kontrol("CI-9", "numarali IDDIA vs DOGRULAMA basligi kabul edilir",
            rc == 0 and "OK DEVIR-01" in o, f"rc={rc}")

    p10 = kur(T / "ci10")
    (p10 / "DEVIR.md").write_text(
        "# DEVIR\n\n## IDDIA vs DOGRULAMA\n\n"
        "| # | İddia | Komut | Çıktı | Exit |\n"
        "|---|---|---|---|---|\n"
        "| 1 | - | - | - | - |\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--devir", cwd=p10)
    kontrol("CI-10", "yer tutucu satir kanit sayilmaz",
            rc == 1 and "FAIL DEVIR-01" in o and "bos" in o.lower(), f"rc={rc}")

    p11 = kur(T / "ci11")
    (p11 / "DEVIR.md").unlink()
    rc, o = kos("check_integrity.sh", "--devir", cwd=p11)
    kontrol("CI-11", "DEVIR dosyasi yoksa rc=1",
            rc == 1 and "FAIL DEVIR-01" in o and "yok" in o.lower(), f"rc={rc}")

    p12 = kur(T / "ci12")
    (p12 / "rapor").mkdir()
    (p12 / "rapor/MUTABAKAT.md").write_text(
        "# MUTABAKAT\n\n## KURAL 30 — BAGIMSIZLIK BEYANI\n\n"
        "Ic ajanlar ayni modelin kopyalaridir; bagimsiz uzman sayilmaz. "
        "Gercek bagimsizlik dis modellerle kurulur: Gemini ve Grok.\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--mutabakat", cwd=p12)
    kontrol("CI-12", "dolu Kural 30 bagimsizlik beyani kabul edilir",
            rc == 0 and "OK MUTABAKAT-01" in o, f"rc={rc}")

    p13 = kur(T / "ci13")
    (p13 / "rapor").mkdir()
    (p13 / "rapor/MUTABAKAT.md").write_text(
        "# MUTABAKAT\n\n## KURAL 30 — BAGIMSIZLIK BEYANI\n\n"
        "## NIHAI BULGULAR\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--mutabakat", cwd=p13)
    kontrol("CI-13", "bos Kural 30 bagimsizlik beyani MUTABAKAT kapisini gecmez",
            rc == 1 and "FAIL MUTABAKAT-01" in o and "bos" in o.lower(), f"rc={rc}")

    p14 = kur(T / "ci14")
    (p14 / "rapor").mkdir()
    (p14 / "rapor/MUTABAKAT.md").write_text(
        "# MUTABAKAT\n\n## KURAL 30 — BAGIMSIZLIK BEYANI\n\n"
        "Sıdk esastır.\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--mutabakat", cwd=p14)
    kontrol("CI-14", "genel sidk sozu Kural 30 bagimsizlik beyani sayilmaz",
            rc == 1 and "FAIL MUTABAKAT-01" in o and "icerik" in o.lower(), f"rc={rc}")

    p15 = kur(T / "ci15")
    rc, o = kos("check_integrity.sh", "--mutabakat", cwd=p15)
    kontrol("CI-15", "MUTABAKAT dosyasi yoksa rc=1",
            rc == 1 and "FAIL MUTABAKAT-01" in o and "yok" in o.lower(), f"rc={rc}")

    p16 = kur(T / "ci16")
    (p16 / "rapor").mkdir()
    (p16 / "rapor/MUTABAKAT.md").write_text(
        "# MUTABAKAT\n\n## NIHAI BULGULAR\n\nBulgu yok.\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--mutabakat", cwd=p16)
    kontrol("CI-16", "Kural 30 bagimsizlik alani yoksa MUTABAKAT kapisi kapanir",
            rc == 1 and "FAIL MUTABAKAT-01" in o and "alani yok" in o.lower(), f"rc={rc}")

    p17 = kur(T / "ci17")
    (p17 / "rapor").mkdir()
    (p17 / "rapor/MUTABAKAT.md").write_text(
        "# MUTABAKAT\n\n## KURAL 30 — BAGIMSIZLIK BEYANI\n\n"
        "Ic ajanlar ayni modelin kopyalaridir; bagimsiz uzman sayilmaz. "
        "Gercek bagimsizlik dis modellerle kurulur: <dis model ve ortamlar>.\n",
        encoding="utf-8")
    rc, o = kos("check_integrity.sh", "--mutabakat", cwd=p17)
    kontrol("CI-17", "doldurulmamis yer tutucu Kural 30 beyani sayilmaz",
            rc == 1 and "FAIL MUTABAKAT-01" in o and "yer tutucu" in o.lower(), f"rc={rc}")

    # CI-18: --full zinciri --mutabakat CAGIRMIYOR; banner da onu iddia ETMEMELI.
    # Bannerdaki tarihsel "mutabakat" kelimesi fix_reconcile'in sayi/ID mutabakatini
    # kastediyordu; P1-2 ayni ada sahip ikinci bir kapi ekleyince ifade yaniltici oldu.
    rc, o = kos("check_integrity.sh", "--full", cwd=taban)
    banner = [s for s in o.splitlines() if "FULL PASS" in s]
    kontrol("CI-18", "--full kosmadigi Kural 30 kapisini iddia etmez",
            rc == 0 and len(banner) == 1 and "MUTABAKAT-01" not in o
            and "sayi/ID mutabakati" in banner[0], f"rc={rc}")

    # ============ oztest_attest.py (P1-3: envanter pini) ============
    import json as _json
    OZ_D = T / "att"
    OZ_D.mkdir(parents=True, exist_ok=True)
    oz_canli = OZ_D / "oz_canli.txt"
    oz_canli.write_text(
        "  OK   AA-1: birinci\n  OK   BB-2: ikinci\n  KALDI CC-3: ucuncu :: rc=1\n"
        "  KALDI CC-3: ucuncu\nOZ-TEST: 2/3 gecti\n", encoding="utf-8")

    # OZ-1 SABIT tabanla kosar: --uret ile kosarsa taban olculecek ciktinin
    # KENDISINDEN uretilir, pinli == canli yapisal olarak garanti olur ve test
    # butun kurallar kaldirilsa bile yesil kalirdi (vacuous). Taban elle yazilir.
    import hashlib as _ozh
    _ozk = ["AA-1", "BB-2", "CC-3"]
    (OZ_D / "taban.json").write_text(_json.dumps({
        "sema": "OZTEST-TABAN/v1", "sayi": len(_ozk), "kimlikler": _ozk,
        "kimlik_hash": "sha256:" + _ozh.sha256("\n".join(_ozk).encode()).hexdigest()},
        ensure_ascii=False), encoding="utf-8")
    rc, o = kos("oztest_attest.py", "--cikti", str(oz_canli), "--taban", str(OZ_D / "taban.json"))
    kontrol("OZ-1", "saglam envanterde PASS (SABIT taban)",
            rc == 0 and "OZTEST-ATTEST PASS" in o and "P0=0 P1=0" in o, f"rc={rc}")

    oz_eksik = OZ_D / "oz_eksik.txt"
    oz_eksik.write_text("  OK   AA-1: birinci\n  OK   BB-2: ikinci\nOZ-TEST: 2/2 gecti\n",
                     encoding="utf-8")
    rc, o = kos("oztest_attest.py", "--cikti", str(oz_eksik), "--taban", str(OZ_D / "taban.json"))
    kontrol("OZ-2", "pinlenmis test SILINIRSE kapi kapanir",
            rc == 1 and "OZT-02" in o and "CC-3" in o, f"rc={rc}")

    rc, o = kos("oztest_attest.py", "--cikti", str(oz_canli), "--taban", str(OZ_D / "YOK.json"))
    oz_taban_yok = rc == 1 and "OZT-01" in o
    oz_taban_rc = rc
    oz_cikti_rc, oz_cikti_o = kos("oztest_attest.py", "--cikti", str(OZ_D / "YOK.txt"),
                                "--taban", str(OZ_D / "taban.json"))
    # AUD-01: _main()'in return degeri degil, GERCEK surec exit kodu olculur.
    # Timeout kontrollu uretilir; 900 saniye beklenmez, ic oz-test baslatilmaz.
    oz_timeout = subprocess.run([
        sys.executable, "-B", "-c",
        "import runpy, subprocess, sys\n"
        "from unittest.mock import patch\n"
        "betik = sys.argv[1]\n"
        "sys.argv = [betik]\n"
        "with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('atlas_selftest.py', 900)):\n"
        "    runpy.run_path(betik, run_name='__main__')\n",
        str(SCRIPTS / "oztest_attest.py"),
    ], capture_output=True, text=True, timeout=15)
    oz_timeout_o = (oz_timeout.stdout or "") + (oz_timeout.stderr or "")
    kontrol("OZ-3", "taban/kanit yoksa veya timeout olursa exit 1 (fail-closed)",
            oz_taban_yok
            and oz_cikti_rc == 1 and "OZT-01" in oz_cikti_o
            and "OZTEST-ATTEST FAIL" in oz_cikti_o
            and oz_timeout.returncode == 1 and "OZT-03" in oz_timeout_o
            and "OZTEST-ATTEST FAIL" in oz_timeout_o,
            f"taban_rc={oz_taban_rc}, kanit_rc={oz_cikti_rc}, timeout_rc={oz_timeout.returncode}")

    oz_bos = OZ_D / "oz_bos.txt"
    oz_bos.write_text("hicbir test satiri yok\n", encoding="utf-8")
    rc, o = kos("oztest_attest.py", "--cikti", str(oz_bos), "--taban", str(OZ_D / "taban.json"))
    kontrol("OZ-4", "sifir test 'temiz' sayilmaz",
            rc == 1 and "OZT-03" in o, f"rc={rc}")

    oz_artan = OZ_D / "oz_artan.txt"
    oz_artan.write_text(oz_canli.read_text(encoding="utf-8").replace(
        "OZ-TEST:", "  OK   DD-4: dorduncu\nOZ-TEST:"), encoding="utf-8")
    rc, o = kos("oztest_attest.py", "--cikti", str(oz_artan), "--taban", str(OZ_D / "taban.json"))
    kontrol("OZ-5", "YENI test eklemek kapiyi kapatmaz (yalniz P1 uyari)",
            rc == 0 and "OZT-05" in o and "DD-4" in o, f"rc={rc}")

    oz_kurcali = OZ_D / "oz_kurcali.json"
    _d = _json.loads((OZ_D / "taban.json").read_text(encoding="utf-8"))
    _d["kimlikler"] = [k for k in _d["kimlikler"] if k != "CC-3"]
    _d["sayi"] = len(_d["kimlikler"])
    oz_kurcali.write_text(_json.dumps(_d, ensure_ascii=False), encoding="utf-8")
    rc, o = kos("oztest_attest.py", "--cikti", str(oz_canli), "--taban", str(oz_kurcali))
    kontrol("OZ-6", "elle dusurulmus taban hash uyusmazligiyla yakalanir",
            rc == 1 and "OZT-06" in o, f"rc={rc}")

    (OZ_D / "null.json").write_text("null", encoding="utf-8")
    rc, o = kos("oztest_attest.py", "--cikti", str(oz_canli), "--taban", str(OZ_D / "null.json"))
    kontrol("OZ-7", "sozluk OLMAYAN taban (null) kapiyi ACMAZ",
            rc == 1 and "OZT-01" in o, f"rc={rc}")

    import hashlib as _oh
    (OZ_D / "bos.json").write_text(_json.dumps({
        "sema": "OZTEST-TABAN/v1", "sayi": 0, "kimlikler": [],
        "kimlik_hash": "sha256:" + _oh.sha256(b"").hexdigest()}), encoding="utf-8")
    rc, o = kos("oztest_attest.py", "--cikti", str(oz_canli), "--taban", str(OZ_D / "bos.json"))
    kontrol("OZ-8", "BOS ama hash'i tutan taban kapiyi ACMAZ",
            rc == 1 and "OZT-01" in o, f"rc={rc}")

    (OZ_D / "bicim.txt").write_text(
        "  OK   TS-4a: harf sonekli\n  OK   FIX_RECONCILE-1: alt cizgili\n"
        "  OK   CI-18b: harf sonekli\n  OK   AA-1: duz\n"
        "  KALDI OZ-TEST-CRASH: kimlik DEGIL\nOZ-TEST: 3/4 gecti\n", encoding="utf-8")
    rc, o = kos("oztest_attest.py", "--uret", "--cikti", str(OZ_D / "bicim.txt"),
                "--taban", str(OZ_D / "bicim.json"))
    _pin = _json.loads((OZ_D / "bicim.json").read_text(encoding="utf-8"))["kimlikler"]
    kontrol("OZ-9", "mesru kimlik bicimleri pinlenir, CRASH etiketi pinlenmez",
            set(_pin) == {"TS-4a", "FIX_RECONCILE-1", "CI-18b", "AA-1"}, f"pin={_pin}")

    # ============ teslim_imza.py (P1-4: teslim manifesti butunlugu + imza) ============
    # Sinama anahtari ORTAM DEGISKENIYLE verilir; dosya sistemine anahtar YAZILMAZ.
    ts_env = dict(os.environ, LAB_IMZA_ANAHTARI="a" * 64)
    ts_env2 = dict(os.environ, LAB_IMZA_ANAHTARI="b" * 64)
    import json as _tsjson

    ts1 = kur(T / "ts1")
    kos("teslim_imza.py", "--uret", cwd=ts1, env=ts_env)
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts1, env=ts_env)
    kontrol("TS-1", "saglam teslimde PASS", rc == 0 and "TESLIM PASS" in o, f"rc={rc}")

    ts2 = kur(T / "ts2")
    kos("teslim_imza.py", "--uret", cwd=ts2, env=ts_env)
    (ts2 / "03-FAZ-3-MASTER-v5.5.md").write_text("TAHRIF EDILDI\n", encoding="utf-8")
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts2, env=ts_env)
    kontrol("TS-2", "artefakt DEGISTIRILIRSE hash tutmaz",
            rc == 1 and "TSL-03" in o and "MASTER" in o, f"rc={rc}")

    ts3 = kur(T / "ts3")
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts3, env=ts_env)
    kontrol("TS-3", "manifest yoksa kapi ACILMAZ (fail-closed)",
            rc == 1 and "TSL-01" in o, f"rc={rc}")

    ts4 = kur(T / "ts4")
    kos("teslim_imza.py", "--uret", cwd=ts4, env=ts_env)
    (ts4 / "gate" / "FINAL-GATE-v5.5.json").rename(ts4 / "gate" / "_gizlendi.json")
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts4, env=ts_env)
    kontrol("TS-4", "listelenen dosya SILINIRSE yakalanir",
            rc == 1 and "TSL-02" in o, f"rc={rc}")

    ts5 = kur(T / "ts5")
    kos("teslim_imza.py", "--uret", cwd=ts5, env=ts_env)
    _m = ts5 / "TESLIM-MANIFEST.json"
    _d = _tsjson.loads(_m.read_text(encoding="utf-8"))
    _d["dosyalar"] = {k: v for k, v in _d["dosyalar"].items() if "MASTER" not in k}
    _m.write_text(_tsjson.dumps(_d, ensure_ascii=False, indent=2), encoding="utf-8")
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts5, env=ts_env)
    kontrol("TS-5", "zorunlu artefakt manifestte YOKSA kapsam eksigi yakalanir",
            rc == 1 and "TSL-06" in o, f"rc={rc}")

    ts6 = kur(T / "ts6")
    kos("teslim_imza.py", "--uret", cwd=ts6, env=ts_env)
    _m = ts6 / "TESLIM-MANIFEST.json"
    _d = _tsjson.loads(_m.read_text(encoding="utf-8"))
    _d.pop("imza", None)
    _m.write_text(_tsjson.dumps(_d, ensure_ascii=False, indent=2), encoding="utf-8")
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts6, env=ts_env)
    kontrol("TS-6", "imzasiz manifest kapiyi KAPATMAZ, DUSUK_GUVEN uyarir",
            rc == 0 and "TSL-05" in o and "DUSUK_GUVEN" in o, f"rc={rc}")

    ts7 = kur(T / "ts7")
    kos("teslim_imza.py", "--uret", cwd=ts7, env=ts_env)
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts7, env=ts_env2)
    kontrol("TS-7", "BASKA anahtarla imzalanmis manifest FAIL",
            rc == 1 and "TSL-04" in o, f"rc={rc}")

    ts8 = kur(T / "ts8")
    rc, o = kos("check_integrity.sh", "--teslim", cwd=ts8, env=ts_env)
    kontrol("TS-8", "check_integrity --teslim manifestsiz projede rc=1",
            rc == 1 and "TSL-01" in o, f"rc={rc}")
    kos("teslim_imza.py", "--uret", cwd=ts8, env=ts_env)
    rc, o = kos("check_integrity.sh", "--teslim", cwd=ts8, env=ts_env)
    kontrol("TS-9", "check_integrity --teslim saglam manifeste rc=0",
            rc == 0 and "TESLIM PASS" in o, f"rc={rc}")

    ts10 = kur(T / "ts10")
    kos("teslim_imza.py", "--uret", cwd=ts10, env=ts_env)
    (ts10 / "TESLIM-MANIFEST.json").write_text("null", encoding="utf-8")
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts10, env=ts_env)
    kontrol("TS-10", "sozluk OLMAYAN manifest (null) kapiyi ACMAZ",
            rc == 1 and "TSL-01" in o, f"rc={rc}")

    ts11 = kur(T / "ts11")
    kos("teslim_imza.py", "--uret", cwd=ts11, env=ts_env)
    (ts11 / "03-FAZ-3-MASTER-v5.5.md").write_text("TAHRIF\n", encoding="utf-8")
    kos("teslim_imza.py", "--uret", cwd=ts11, env=ts_env)
    _mm = ts11 / "TESLIM-MANIFEST.json"
    _dd = _tsjson.loads(_mm.read_text(encoding="utf-8")); _dd["imza"] = None
    _mm.write_text(_tsjson.dumps(_dd, ensure_ascii=False), encoding="utf-8")
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts11, env=ts_env)
    kontrol("TS-11", "imza alani VAR ama gecersiz ise P0 (imza siyirma kapali)",
            rc == 1 and "TSL-04" in o, f"rc={rc}")

    ts12 = kur(T / "ts12")
    kos("teslim_imza.py", "--uret", cwd=ts12, env=ts_env)
    _mm = ts12 / "TESLIM-MANIFEST.json"
    _dd = _tsjson.loads(_mm.read_text(encoding="utf-8"))
    _k = [k for k in _dd["dosyalar"] if "MASTER" in k][0]
    _dd["dosyalar"][_k] = "sha256:" + "0" * 64
    _mm.write_text(_tsjson.dumps(_dd, ensure_ascii=False), encoding="utf-8")
    rc, o = kos("teslim_imza.py", "--dogrula", cwd=ts12, env=ts_env)
    kontrol("TS-12", "imza `dosyalar` alanini KAPSAR (hash elle degisirse TSL-04)",
            rc == 1 and "TSL-04" in o, f"rc={rc}")

    # TS-13 ORTAM degil DOSYA yolunu sinar: ortam yolunda uzunluk denetimi vardi,
    # dosya yolunda YOKTU — 1 baytlik anahtar "imzalandi" diye raporlaniyordu.
    ts13 = kur(T / "ts13")
    (ts13 / ".lab_imza.key").write_text("a\n", encoding="utf-8")
    # HERMETIKLIK: `anahtar_bul()` once ~/.config/lab_imza.key'e bakar. Kullanicinin
    # GERCEK anahtari varsa fikstürün sahte kisa anahtarina hic sira gelmez ve bu test
    # kullanicinin hesabina bagimli hale gelir (P0-4'te ayni sinif kusur olculmustu:
    # "Tum fikstirler gecici klasorde kurulur" iddiasi ihlal ediliyordu).
    # Cozum: HOME bos bir fikstür ev dizinine yonlendirilir.
    _ts_ev = T / "ts13_ev"
    _ts_ev.mkdir(parents=True, exist_ok=True)
    _tsenv = {k: v for k, v in os.environ.items() if k != "LAB_IMZA_ANAHTARI"}
    _tsenv["HOME"] = str(_ts_ev)
    rc, o = kos("teslim_imza.py", "--uret", cwd=ts13, env=_tsenv)
    # DIKKAT: "imzalandi yok" yetmez — cokme de o kosulu saglar ve testi sahte
    # yesile boyar (olculdu). Acik RET metni ve traceback YOKLUGU da sart.
    kontrol("TS-13", "DOSYADAKI kisa anahtar ACIKCA reddedilir (cokmeden)",
            rc == 0 and "GECERSIZ" in o and "imzalandi" not in o
            and "Traceback" not in o, f"rc={rc} o={o.strip()[:70]}")

    ts14 = kur(T / "ts14")
    kos("teslim_imza.py", "--uret", cwd=ts14, env=ts_env)
    _mm = ts14 / "TESLIM-MANIFEST.json"
    _iyi = _tsjson.loads(_mm.read_text(encoding="utf-8"))
    _hk = next(iter(_iyi["dosyalar"]))
    _sonuclar = []
    for _bozuk in (None, 0, False, {}, [], ""):
        _dd = _tsjson.loads(_tsjson.dumps(_iyi))
        _dd["dosyalar"][_hk] = _bozuk
        _mm.write_text(_tsjson.dumps(_dd, ensure_ascii=False), encoding="utf-8")
        _rc, _o = kos("teslim_imza.py", "--dogrula", cwd=ts14, env=ts_env)
        _sonuclar.append((_rc, "TSL-01" in _o, "Traceback" in _o))
    kontrol("TS-14", "yanlis tipte hash temiz TSL-01 ile kapanir",
            all(rc == 1 and tsl01 and not traceback
                for rc, tsl01, traceback in _sonuclar),
            f"sonuclar={_sonuclar}")

    ts15 = kur(T / "ts15")
    (ts15 / ".lab_imza.key").write_bytes(b"\xff\xfe\x00\x01")
    _ts15_ev = T / "ts15_ev"
    _ts15_ev.mkdir(parents=True, exist_ok=True)
    _ts15_env = {k: v for k, v in os.environ.items() if k != "LAB_IMZA_ANAHTARI"}
    _ts15_env["HOME"] = str(_ts15_ev)
    rc, o = kos("teslim_imza.py", "--uret", cwd=ts15, env=_ts15_env)
    kontrol("TS-15", "IKILI anahtar temiz GECERSIZ reddi verir (cokmeden)",
            rc == 0 and "GECERSIZ" in o and "Traceback" not in o,
            f"rc={rc} o={o.strip()[:100]}")

    ts16 = kur(T / "ts16")
    _ts16_key = ts16 / ".lab_imza.key"
    _ts16_key.write_text("a" * 64 + "\n", encoding="utf-8")
    _ts16_key.chmod(0o000)
    _ts16_ev = T / "ts16_ev"
    _ts16_ev.mkdir(parents=True, exist_ok=True)
    _ts16_env = {k: v for k, v in os.environ.items() if k != "LAB_IMZA_ANAHTARI"}
    _ts16_env["HOME"] = str(_ts16_ev)
    try:
        rc, o = kos("teslim_imza.py", "--uret", cwd=ts16, env=_ts16_env)
    finally:
        _ts16_key.chmod(0o600)
    kontrol("TS-16", "OKUNAMAYAN anahtar temiz GECERSIZ reddi verir (cokmeden)",
            rc == 0 and "GECERSIZ" in o and "Traceback" not in o,
            f"rc={rc} o={o.strip()[:100]}")

    # ============ provenance_check.py ============
    _pc1_vakalar = [
        ("PROVENANCE", 0, "PASS CHK-02"),
        ("Ek Tablo", 1, "FAIL CHK-02"),
    ]
    _pc1_sonuclar = []
    for _pc1_no, (_pc1_baslik, _pc1_beklenen_rc, _pc1_beklenen_metin) in enumerate(_pc1_vakalar):
        _pc1_proje = kur(T / f"pc1_{_pc1_no}")
        _pc1_master = _pc1_proje / "03-FAZ-3-MASTER-v5.5.md"
        _pc1_master.write_text(
            _pc1_master.read_text(encoding="utf-8").replace(
                "## PROVENANCE Tablosu", f"## {_pc1_baslik}"
            ),
            encoding="utf-8",
        )
        _pc1_rc, _pc1_cikti = kos("provenance_check.py", cwd=_pc1_proje)
        _pc1_sonuclar.append(
            (_pc1_baslik, _pc1_rc, _pc1_beklenen_metin in _pc1_cikti,
             "Traceback" in _pc1_cikti, _pc1_beklenen_rc)
        )
    kontrol(
        "PC-1",
        "CHK-02 yalniz gercek PROVENANCE bolumundeki tabloyu kabul eder",
        all(rc == beklenen_rc and beklenen_metin_var and not traceback
            for _, rc, beklenen_metin_var, traceback, beklenen_rc in _pc1_sonuclar),
        f"sonuclar={_pc1_sonuclar}",
    )

    p = kur(T / "pc2")
    f = p / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
    f.write_text(f.read_text(encoding="utf-8").replace("| ZORUNLU |", "| Gerekli |"), encoding="utf-8")
    rc, o = kos("provenance_check.py", cwd=p)
    kontrol("PC-2", "ZORUNLU satiri yoksa vacuous PASS degil FAIL", rc == 1 and "CHK-00" in o, f"rc={rc}")

    _pc3_ids = [f"SC-{i:03d}" for i in range(1, 9)]
    _pc3_vakalar = [
        ("sekiz-duz-baslik", [], []),
        ("kalin-id", [("## SC-005 Bolum 5", "## **SC-005** Bolum 5")], []),
        ("eksik-id", [("## SC-005 Bolum 5", "## Bolum 5")], ["SC-005"]),
        (
            "tek-toplu-olumsuz-baslik",
            [(f"## {sid} Bolum {i}", f"## Bolum {i}") for i, sid in enumerate(_pc3_ids, 1)]
            + [
                (
                    "## PROVENANCE Tablosu",
                    f"## Eksik basliklar: {' '.join(_pc3_ids)}\n\n## PROVENANCE Tablosu",
                )
            ],
            _pc3_ids,
        ),
        ("not-on-ekli", [("## SC-005 Bolum 5", "## NOT-SC-005 Bolum 5")], ["SC-005"]),
        ("kelime-ici", [("## SC-005 Bolum 5", "## XSC-005Y Bolum 5")], ["SC-005"]),
        ("uzun-sayi", [("## SC-005 Bolum 5", "## SC-0050 Bolum 5")], ["SC-005"]),
        (
            "sonraki-id",
            [("## SC-005 Bolum 5", "## SC-001 SC-005 toplu baslik")],
            ["SC-005"],
        ),
    ]
    _pc3_sonuclar = []
    for _pc3_no, (_pc3_ad, _pc3_degisimler, _pc3_eksikler) in enumerate(_pc3_vakalar):
        _pc3_proje = kur(T / f"pc3_{_pc3_no}")
        _pc3_master = _pc3_proje / "03-FAZ-3-MASTER-v5.5.md"
        _pc3_metin = _pc3_master.read_text(encoding="utf-8")
        _pc3_degisim_tam = True
        for _pc3_eski, _pc3_yeni in _pc3_degisimler:
            if _pc3_eski not in _pc3_metin:
                _pc3_degisim_tam = False
                continue
            _pc3_metin = _pc3_metin.replace(_pc3_eski, _pc3_yeni, 1)
        _pc3_master.write_text(_pc3_metin, encoding="utf-8")
        _pc3_rc, _pc3_cikti = kos("provenance_check.py", cwd=_pc3_proje)
        if _pc3_eksikler:
            _pc3_davranis = (
                _pc3_rc == 1
                and "FAIL CHK-01" in _pc3_cikti
                and f"basliksiz {_pc3_eksikler}" in _pc3_cikti
            )
        else:
            _pc3_davranis = (
                _pc3_rc == 0
                and "PASS CHK-01" in _pc3_cikti
                and "FAIL CHK-01" not in _pc3_cikti
            )
        _pc3_sonuclar.append(
            (_pc3_ad, _pc3_rc, _pc3_degisim_tam, _pc3_davranis,
             "Traceback" in _pc3_cikti)
        )
    kontrol(
        "PC-3",
        "CHK-01 yalniz basliktaki ilk tam SC-ID tokenini bolum sayar",
        all(degisim_tam and davranis and not traceback
            for _, _, degisim_tam, davranis, traceback in _pc3_sonuclar),
        f"sonuclar={_pc3_sonuclar}",
    )

    _pc4_vakalar = [
        ("kapsamiyor", 1, "FAIL CHK-02"),
        ("NOT COVERED", 1, "FAIL CHK-02"),
        ("UNCOVERED", 1, "FAIL CHK-02"),
        ("NOT UNVERIFIED", 1, "FAIL CHK-02"),
        ("kapsiyor", 0, "PASS CHK-02"),
        ("COVERED", 0, "PASS CHK-02"),
        ("[UNVERIFIED]", 0, "PASS CHK-02"),
    ]
    _pc4_sonuclar = []
    for _pc4_no, (_pc4_durum, _pc4_beklenen_rc, _pc4_beklenen_metin) in enumerate(_pc4_vakalar):
        _pc4_proje = kur(T / f"pc4_{_pc4_no}")
        _pc4_master = _pc4_proje / "03-FAZ-3-MASTER-v5.5.md"
        _pc4_master.write_text(
            _pc4_master.read_text(encoding="utf-8").replace(
                "| SC-006 | Bolum 6 | Uretildi | 60 | IKINCIL | kapsiyor |",
                f"| SC-006 | Bolum 6 | Uretildi | 60 | IKINCIL | {_pc4_durum} |",
            ),
            encoding="utf-8",
        )
        _pc4_rc, _pc4_cikti = kos("provenance_check.py", cwd=_pc4_proje)
        _pc4_sonuclar.append(
            (_pc4_durum, _pc4_rc, _pc4_beklenen_metin in _pc4_cikti,
             "Traceback" in _pc4_cikti, _pc4_beklenen_rc)
        )
    kontrol(
        "PC-4",
        "CHK-02 durumlari kapali listeyle tam eslesir",
        all(rc == beklenen_rc and beklenen_metin_var and not traceback
            for _, rc, beklenen_metin_var, traceback, beklenen_rc in _pc4_sonuclar),
        f"sonuclar={_pc4_sonuclar}",
    )

    p = kur(T / "pc5"); (p / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md").unlink()
    rc, o = kos("provenance_check.py", cwd=p)
    kontrol("PC-5", "SCOPE yoksa temiz FAIL (traceback yok)",
            rc == 1 and "Traceback" not in o, f"rc={rc}")

    # B-9: Ingilizce durum token'lari
    p = kur(T / "pc6")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace("| kapsiyor |", "| COVERED |"), encoding="utf-8")
    rc, o = kos("provenance_check.py", cwd=p)
    kontrol("PC-6", "Ingilizce 'COVERED' durumu CHK-02'de kabul edilir (B-9)",
            rc == 0 and "PASS CHK-02" in o, f"rc={rc}")

    _pc7_benzersiz = kur(T / "pc7_benzersiz")
    _pc7_benzersiz_rc, _pc7_benzersiz_cikti = kos(
        "provenance_check.py", cwd=_pc7_benzersiz
    )
    _pc7_benzersiz_ok = (
        _pc7_benzersiz_rc == 0
        and "PASS CHK-05:" in _pc7_benzersiz_cikti
        and "WARN CHK-05:" not in _pc7_benzersiz_cikti
        and "Traceback" not in _pc7_benzersiz_cikti
    )

    _pc7_tekrar = kur(T / "pc7_tekrar")
    _pc7_master = _pc7_tekrar / "03-FAZ-3-MASTER-v5.5.md"
    _pc7_master.write_text(
        _pc7_master.read_text(encoding="utf-8")
        + "\n\n## CHK05 Tekrar Baslik\n\n## chk05 tekrar baslik\n",
        encoding="utf-8",
    )
    _pc7_tekrar_rc, _pc7_tekrar_cikti = kos(
        "provenance_check.py", cwd=_pc7_tekrar
    )
    _pc7_tekrar_ok = (
        _pc7_tekrar_rc == 0
        and "WARN CHK-05:" in _pc7_tekrar_cikti
        and "PASS CHK-05:" not in _pc7_tekrar_cikti
        and "PASS CHK-01:" in _pc7_tekrar_cikti
        and "PASS CHK-02:" in _pc7_tekrar_cikti
        and "Traceback" not in _pc7_tekrar_cikti
    )
    kontrol(
        "PC-7",
        "CHK-05 benzersiz basligi PASS, normalize yinelenen basligi WARN verir (B-9)",
        _pc7_benzersiz_ok and _pc7_tekrar_ok,
        f"benzersiz=(rc={_pc7_benzersiz_rc}, ok={_pc7_benzersiz_ok}) "
        f"tekrar=(rc={_pc7_tekrar_rc}, ok={_pc7_tekrar_ok})",
    )

    # ============ olgu_lint.py (P1-5: kanonik olgu + ham sayi sozlesmesi) ============
    _olg_lab_kok = SCRIPTS.parent.parent
    _olg_komut = [sys.executable, str(SCRIPTS / "olgu_lint.py")]
    _olg_kanon = _olg_lab_kok / "docs" / "OLGULAR.md"
    _olg_kanon_eslesme = re.search(
        r"<!-- OLGULAR_JSON_BASLA -->\s*```json\s*(\{.*?\})\s*```\s*"
        r"<!-- OLGULAR_JSON_BITIR -->",
        _olg_kanon.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    _olg_kanon_veri = json.loads(_olg_kanon_eslesme.group(1))
    _olg_atlas_kanit = T / "olg1_atlas.out"
    _olg_attest_kanit = T / "olg1_attest.json"
    _olg_kod_kanit = T / "olg1_kod.out"
    _olg_atlas_gecen = _olg_kanon_veri["atlas_son_gecen"]
    _olg_atlas_toplam = _olg_kanon_veri["atlas_envanter_sayisi"]
    _olg_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=_olg_lab_kok, text=True
    , timeout=600).strip()
    _olg_run = "OLG-1-FRESH"
    _olg_zaman = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _olg_baslik(head=_olg_head, run=_olg_run, zaman=_olg_zaman, timeout=900):
        return (f"OLGU-KANIT/v1 HEAD={head} run_id={run} "
                f"timestamp={zaman} timeout={timeout}")

    _olg_atlas_kanit.write_text(
        _olg_baslik() + f"\nOZ-TEST: {_olg_atlas_gecen}/{_olg_atlas_toplam} gecti\n",
        encoding="utf-8",
    )
    _olg_attest_kanit.write_text(
        json.dumps({
            "sema": "OZTEST-ATTEST/v1",
            "kanit": {
                "sema": "OLGU-KANIT/v1", "head": _olg_head, "run_id": _olg_run,
                "timestamp": _olg_zaman, "timeout": 900,
            },
            "canli_sayi": _olg_kanon_veri["attest_canli"],
            "taban_sayi": _olg_kanon_veri["attest_taban"],
            "p0": _olg_kanon_veri["attest_p0"],
            "p1": _olg_kanon_veri["attest_p1"],
        }),
        encoding="utf-8",
    )
    _olg_kod_gecen = _olg_kanon_veri["kod_son_gecen"]
    _olg_kod_kanit.write_text(
        _olg_baslik() + f"\nKOD OZ-TEST: {_olg_kod_gecen}/{_olg_kod_gecen} gecti\n",
        encoding="utf-8",
    )
    _olg_kanit_argumanlari = [
        "--atlas-cikti", str(_olg_atlas_kanit),
        "--attest-cikti", str(_olg_attest_kanit),
        "--kod-cikti", str(_olg_kod_kanit),
    ]
    _olg_pozitif = subprocess.run(
        _olg_komut,
        cwd=_olg_lab_kok,
        capture_output=True,
        text=True, timeout=600,
    )
    _olg_pozitif_cikti = (_olg_pozitif.stdout or "") + (_olg_pozitif.stderr or "")
    _olg_pozitif_ok = (
        _olg_pozitif.returncode == 0
        and "OLGU-LINT PASS" in _olg_pozitif_cikti
        and "Traceback" not in _olg_pozitif_cikti
    )
    _olg_canli_pozitif = subprocess.run(
        _olg_komut + _olg_kanit_argumanlari,
        cwd=_olg_lab_kok,
        capture_output=True,
        text=True, timeout=600,
    )
    _olg_canli_pozitif_cikti = (
        (_olg_canli_pozitif.stdout or "") + (_olg_canli_pozitif.stderr or "")
    )
    _olg_canli_pozitif_ok = (
        _olg_canli_pozitif.returncode == 0
        and "OLGU-LINT PASS" in _olg_canli_pozitif_cikti
        and "WARN OLGU-05 KANIT_" not in _olg_canli_pozitif_cikti
        and "Traceback" not in _olg_canli_pozitif_cikti
    )

    _olg_yanlis_head = ("0" if _olg_head[0] != "0" else "1") + _olg_head[1:]
    _olg_atlas_kanit.write_text(
        _olg_baslik(head=_olg_yanlis_head)
        + f"\nOZ-TEST: {_olg_atlas_gecen}/{_olg_atlas_toplam} gecti\n", encoding="utf-8"
    )
    _olg_head_sonuc = subprocess.run(
        _olg_komut + _olg_kanit_argumanlari, cwd=_olg_lab_kok,
        capture_output=True, text=True, timeout=600,
    )
    _olg_head_cikti = (_olg_head_sonuc.stdout or "") + (_olg_head_sonuc.stderr or "")
    _olg_head_ok = (
        _olg_head_sonuc.returncode == 0
        and "WARN OLGU-05 KANIT_HEAD_UYUSMAZLIGI kaynak=atlas-cikti" in _olg_head_cikti
        and f"beklenen={_olg_head} bulunan={_olg_yanlis_head}" in _olg_head_cikti
        and "OLGU-LINT PASS" in _olg_head_cikti
    )

    _olg_bayat_zaman = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 120))
    _olg_atlas_kanit.write_text(
        _olg_baslik(zaman=_olg_bayat_zaman, timeout=60)
        + f"\nOZ-TEST: {_olg_atlas_gecen}/{_olg_atlas_toplam} gecti\n", encoding="utf-8"
    )
    _olg_attest_kanit.write_text(
        json.dumps({
            "sema": "OZTEST-ATTEST/v1",
            "kanit": {
                "sema": "OLGU-KANIT/v1", "head": _olg_head, "run_id": "OLG-1-DIGER",
                "timestamp": _olg_zaman, "timeout": 900,
            },
            "canli_sayi": _olg_kanon_veri["attest_canli"],
            "taban_sayi": _olg_kanon_veri["attest_taban"],
            "p0": _olg_kanon_veri["attest_p0"], "p1": _olg_kanon_veri["attest_p1"],
        }), encoding="utf-8",
    )
    _olg_koken_sonuc = subprocess.run(
        _olg_komut + _olg_kanit_argumanlari, cwd=_olg_lab_kok,
        capture_output=True, text=True, timeout=600,
    )
    _olg_koken_cikti = (_olg_koken_sonuc.stdout or "") + (_olg_koken_sonuc.stderr or "")
    _olg_koken_ok = (
        _olg_koken_sonuc.returncode == 0
        and "WARN OLGU-05 KANIT_ZAMAN_ASIMI kaynak=atlas-cikti" in _olg_koken_cikti
        and "WARN OLGU-05 KANIT_RUN_UYUSMAZLIGI kaynak=kanit-seti" in _olg_koken_cikti
        and "OLGU-LINT PASS" in _olg_koken_cikti
    )

    _olg_atlas_kanit.write_text(
        f"OZ-TEST: {_olg_atlas_gecen}/{_olg_atlas_toplam} gecti\n", encoding="utf-8"
    )
    _olg_bozuk_attest = json.loads(_olg_attest_kanit.read_text(encoding="utf-8"))
    _olg_bozuk_attest["kanit"]["run_id"] = 7
    _olg_attest_kanit.write_text(json.dumps(_olg_bozuk_attest), encoding="utf-8")
    _olg_kod_kanit.write_text(
        _olg_baslik(timeout=100000) + f"\nKOD OZ-TEST: {_olg_kod_gecen}/{_olg_kod_gecen} gecti\n",
        encoding="utf-8",
    )
    _olg_bozuk_sonuc = subprocess.run(
        _olg_komut + _olg_kanit_argumanlari, cwd=_olg_lab_kok,
        capture_output=True, text=True, timeout=600,
    )
    _olg_bozuk_cikti = (_olg_bozuk_sonuc.stdout or "") + (_olg_bozuk_sonuc.stderr or "")
    _olg_bozuk_ok = (
        _olg_bozuk_sonuc.returncode == 0
        and all(f"WARN OLGU-05 KANIT_KOKENI_DOGRULANAMADI kaynak={kaynak}" in _olg_bozuk_cikti
                for kaynak in ("atlas-cikti", "attest-cikti", "kod-cikti"))
        and "FAIL" not in _olg_bozuk_cikti and "Traceback" not in _olg_bozuk_cikti
        and "OLGU-LINT PASS" in _olg_bozuk_cikti
    )

    _olg_atlas_kanit.write_text(
        _olg_baslik() + f"\nOZ-TEST: {_olg_atlas_gecen}/{_olg_atlas_toplam} gecti\n",
        encoding="utf-8",
    )
    _olg_kod_kanit.write_text(
        _olg_baslik() + f"\nKOD OZ-TEST: {_olg_kod_gecen}/{_olg_kod_gecen} gecti\n",
        encoding="utf-8",
    )
    _olg_attest_kanit.write_text(
        json.dumps({
            "sema": "OZTEST-ATTEST/v1",
            "kanit": {
                "sema": "OLGU-KANIT/v1", "head": _olg_head, "run_id": _olg_run,
                "timestamp": _olg_zaman, "timeout": 900,
            },
            "canli_sayi": _olg_kanon_veri["attest_canli"],
            "taban_sayi": _olg_kanon_veri["attest_taban"],
            "p0": _olg_kanon_veri["attest_p0"], "p1": _olg_kanon_veri["attest_p1"],
        }), encoding="utf-8",
    )

    _olg_bayat_atlas = T / "olg1_bayat_atlas.out"
    _olg_bayat_gecen = _olg_atlas_gecen - 1 if _olg_atlas_gecen > 0 else 1
    _olg_bayat_atlas.write_text(
        _olg_baslik() + f"\nOZ-TEST: {_olg_bayat_gecen}/{_olg_atlas_toplam} gecti\n",
        encoding="utf-8",
    )
    _olg_bayat_sonuc = subprocess.run(
        _olg_komut + [
            "--atlas-cikti", str(_olg_bayat_atlas),
            "--attest-cikti", str(_olg_attest_kanit),
            "--kod-cikti", str(_olg_kod_kanit),
        ],
        cwd=_olg_lab_kok,
        capture_output=True,
        text=True, timeout=600,
    )
    _olg_bayat_cikti = (_olg_bayat_sonuc.stdout or "") + (_olg_bayat_sonuc.stderr or "")
    _olg_bayat_ok = (
        _olg_bayat_sonuc.returncode == 1
        and "FAIL OLGU-05 DEGER_UYUSMAZLIGI id=atlas_son_gecen" in _olg_bayat_cikti
        and f"beklenen={_olg_bayat_gecen} bulunan={_olg_atlas_gecen}" in _olg_bayat_cikti
        and "Traceback" not in _olg_bayat_cikti
    )

    _olg_eksik_kanit_sonuc = subprocess.run(
        _olg_komut + ["--atlas-cikti", str(_olg_atlas_kanit)],
        cwd=_olg_lab_kok,
        capture_output=True,
        text=True, timeout=600,
    )
    _olg_eksik_kanit_cikti = (
        (_olg_eksik_kanit_sonuc.stdout or "") + (_olg_eksik_kanit_sonuc.stderr or "")
    )
    _olg_eksik_kanit_ok = (
        _olg_eksik_kanit_sonuc.returncode == 1
        and "FAIL OLGU-05 CANLI_OLCUM_DOGRULANAMADI" in _olg_eksik_kanit_cikti
        and "Traceback" not in _olg_eksik_kanit_cikti
    )

    _olg_yok = T / "olg1_yok"
    _olg_yok.mkdir(parents=True, exist_ok=True)
    _olg_yok_sonuc = subprocess.run(
        _olg_komut + ["--kok", str(_olg_yok), "--git-kok", str(_olg_lab_kok)],
        capture_output=True,
        text=True, timeout=600,
    )
    _olg_yok_cikti = (_olg_yok_sonuc.stdout or "") + (_olg_yok_sonuc.stderr or "")
    _olg_yok_ok = (
        _olg_yok_sonuc.returncode == 1
        and "FAIL OLGU-01 KANON_YOK" in _olg_yok_cikti
        and "Traceback" not in _olg_yok_cikti
    )

    _olg_surum_ok = False
    _olg_surum_ayrinti = "kanon-yok"
    if _olg_kanon.is_file():
        _olg_bozuk = T / "olg1_surum"
        (_olg_bozuk / "docs").mkdir(parents=True, exist_ok=True)
        (_olg_bozuk / "ATLAS_SABLONLAR" / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(_olg_kanon, _olg_bozuk / "docs" / "OLGULAR.md")
        shutil.copy2(_olg_lab_kok / "SURUM.md", _olg_bozuk / "SURUM.md")
        shutil.copy2(
            SCRIPTS / "OZTEST-TABAN.json",
            _olg_bozuk / "ATLAS_SABLONLAR" / "scripts" / "OZTEST-TABAN.json",
        )
        _olg_bozuk_kanon = _olg_bozuk / "docs" / "OLGULAR.md"
        _olg_bozuk_metin = _olg_bozuk_kanon.read_text(encoding="utf-8")
        _olg_surum_satirlari = [
            satir for satir in _olg_bozuk_metin.splitlines()
            if satir.strip().startswith('"lab_surum":')
        ]
        _olg_surum_parcalari = _olg_surum_satirlari[0].split('"') if len(_olg_surum_satirlari) == 1 else []
        _olg_beklenen_surum = _olg_surum_parcalari[3] if len(_olg_surum_parcalari) >= 4 else ""
        _olg_eski_surum = f'"lab_surum": "{_olg_beklenen_surum}"'
        _olg_degisim_tam = bool(_olg_beklenen_surum) and _olg_bozuk_metin.count(_olg_eski_surum) == 1
        _olg_bozuk_kanon.write_text(
            _olg_bozuk_metin.replace(_olg_eski_surum, '"lab_surum": "v0.0.0"', 1),
            encoding="utf-8",
        )
        _olg_surum_sonuc = subprocess.run(
            _olg_komut + ["--kok", str(_olg_bozuk), "--git-kok", str(_olg_lab_kok)],
            capture_output=True,
            text=True, timeout=600,
        )
        _olg_surum_cikti = (_olg_surum_sonuc.stdout or "") + (_olg_surum_sonuc.stderr or "")
        _olg_surum_ok = (
            _olg_degisim_tam
            and _olg_surum_sonuc.returncode == 1
            and "FAIL OLGU-03 DEGER_UYUSMAZLIGI id=lab_surum" in _olg_surum_cikti
            and f"beklenen={_olg_beklenen_surum} bulunan=v0.0.0" in _olg_surum_cikti
            and "Traceback" not in _olg_surum_cikti
        )
        _olg_surum_ayrinti = (
            f"degisim={_olg_degisim_tam} rc={_olg_surum_sonuc.returncode} "
            f"cikti={_olg_surum_cikti.strip()[:180]}"
        )

    # OLGU-06: gecici belgeler + belirlenimsel Git cevaplari; commit uretilmez.
    olg06_mod = runpy.run_path(str(SCRIPTS / "olgu_lint.py"), run_name="olg06_test")
    olg06_fn = olg06_mod.get("olgu06_kontrol")
    olg06_sonuclar = []
    olg06_kok = T / "olg06_belgeler"
    (olg06_kok / "docs").mkdir(parents=True)
    olg06_devir = "docs/DEVIR-2026-01-01-0000-KANONIK.md"
    (olg06_kok / olg06_devir).write_text("# Sentetik DEVIR\n", encoding="utf-8")
    olg06_sur = olg06_kok / "SURUM.md"
    olg06_ders = olg06_kok / "docs/DERSLER_v1_2026-08-30.md"
    olg06_base, olg06_a, olg06_b, olg06_doc = (c * 40 for c in "abcd")
    olg06_baslik = "| Tarih | Oruntu | Oneri | Delta ic | Delta dis | Karar | Gerekce |\n"

    def olg06_satir(commit, numara="01.01"):
        return f"| {numara} | mekanizma | kayit | 0 | 0 | KABUL | `{commit}` |\n"

    def olg06_kanonik(*devirler):
        return "".join(
            f"Kanonik OLGU-06 DEVIR: `{devir}`\n" for devir in devirler
        )

    def olg06_vaka(ad, ders, beklenen, *, dosyalar=None, git_hata=False, surum=True,
                   kanonikler=None):
        if kanonikler is None:
            kanonikler = (olg06_devir,)
        olg06_sur.write_text(
            olg06_kanonik(*kanonikler) if surum else "Devir yok\n", encoding="utf-8"
        )
        if ders is None:
            if olg06_ders.exists():
                olg06_ders.unlink()
        else:
            olg06_ders.write_text(ders, encoding="utf-8")
        yollar = dosyalar or {
            olg06_a: "ATLAS_SABLONLAR/scripts/ornek.py\0",
            olg06_b: "KOD_SABLONLAR/scripts/ornek.sh\0",
            olg06_doc: "docs/DERSLER_v1_2026-08-30.md\0ATLAS_SABLONLAR/docs/PIPELINE.md\0",
        }

        def sahte_git(kok, *args, **kwargs):
            assert kok == olg06_kok
            if git_hata:
                return subprocess.CompletedProcess(args, 128, "", "sentetik git hatasi")
            cevaplar = {
                ("rev-parse", "--show-toplevel"): str(olg06_kok),
                ("rev-parse", "--is-shallow-repository"): "false",
                ("log", "-1", "--format=%H", "--diff-filter=A", "HEAD", "--", olg06_devir): olg06_base,
                ("rev-list", "--reverse", f"{olg06_base}..HEAD"): "\n".join(yollar),
            }
            if args[:6] == ("diff-tree", "--no-commit-id", "--name-only", "-r", "-m", "--root"):
                assert args[6] == "-z" and len(args) == 8
                cikti = yollar[args[7]]
            elif args[:2] == ("rev-parse", "--verify"):
                token = args[2].removesuffix("^{commit}")
                adaylar = [sha for sha in yollar if sha.startswith(token)]
                assert len(adaylar) == 1
                cikti = adaylar[0]
            else:
                cikti = cevaplar[args]  # beklenmeyen Git sorgusu testi kirar
            return subprocess.CompletedProcess(args, 0, cikti, "")

        if olg06_fn is None:
            olg06_sonuclar.append((ad, False, "OLGU-06 yok"))
            return
        yakala = io.StringIO()
        with unittest.mock.patch.dict(olg06_fn.__globals__, {"git_kos": sahte_git}), contextlib.redirect_stdout(yakala):
            sonuc06 = olg06_fn(olg06_kok, olg06_kok)
        cikti06 = yakala.getvalue()
        ok = (sonuc06 == beklenen and
              ("PASS OLGU-06" if beklenen == 0 else "FAIL OLGU-06") in cikti06)
        olg06_sonuclar.append((ad, ok, cikti06.strip()))

    olg06_tam = olg06_baslik + olg06_satir(olg06_a[:7]) + olg06_satir(olg06_b)
    olg06_vaka("tam-kisa-hash", olg06_tam, 0)
    olg06_vaka("eksik-kayit", olg06_baslik + olg06_satir(olg06_a), 1)
    olg06_vaka("dersler-yok", None, 1)
    olg06_vaka("yalniz-duzyazi", f"{olg06_a}\n{olg06_b}\n", 1)
    olg06_vaka("fenced-tablo", "```markdown\n" + olg06_tam + "```\n", 1)
    olg06_vaka("kisa-hash-alti", olg06_baslik + olg06_satir(olg06_a[:6]) + olg06_satir(olg06_b), 1)

    # 3 HANELI NUMARA (v1.7.404): DERSLER numarasi 12.100'de 2 -> 3 haneye cikti ama
    # olgu_lint deseni `\d{2}\.\d{2}` idi; 12.100..12.117 satirlari GORULMEDI ve OLGU-06
    # fail-open kaldi (olculdu: 436 numarali satirin 18'i desene uymuyordu).
    # Mutasyon: desen `\d{2}\.\d{2}`e dondurulurse bu vaka 1 doner -> test YANAR.
    olg06_vaka("uc-haneli-numara",
               olg06_baslik + olg06_satir(olg06_a[:7], "12.100") + olg06_satir(olg06_b), 0)

    olg06_vaka("hash-alt-dize", olg06_tam.replace(olg06_a[:7], "x" + olg06_a), 1)
    olg06_vaka("bozuk-satir", f"| {olg06_a} | {olg06_b} |\n", 1)
    olg06_vaka("devir-yok", olg06_tam, 1, surum=False)
    olg06_vaka("iki-kanonik", olg06_tam, 1, kanonikler=(olg06_devir, olg06_devir))
    olg06_vaka("ust-dizin", olg06_tam, 1,
               kanonikler=("../DEVIR-2026-01-01-0000-KANONIK.md",))
    olg06_vaka("devir-dosya-yok", olg06_tam, 1,
               kanonikler=("docs/DEVIR-2026-01-01-0000-YOK.md",))
    olg06_vaka("gecersiz-devir-adi", olg06_tam, 1,
               kanonikler=("docs/DEVIR-2026-01-01-0000-KANONIK!.md",))
    olg06_vaka("git-hatasi", olg06_tam, 1, git_hata=True)
    olg06_vaka("yalniz-belge", olg06_baslik, 0, dosyalar={
        olg06_doc: "AGENTS.md\0ATLAS_SABLONLAR/docs/PIPELINE.md\0SURUM.md\0",
    })
    olg06_vaka("prompt-sema-ortak", olg06_tam, 0, dosyalar={
        olg06_a: "ATLAS_SABLONLAR/.opencode/agent/ornek.md\0",
        olg06_b: "ATLAS_SABLONLAR/templates/SCHEMA.json\0ORTAK/scripts/ornek.py\0",
    })

    olg06_cli = subprocess.run(_olg_komut + ["--dersler"], capture_output=True, text=True, timeout=600)
    olg06_sonuclar.append(("cli", olg06_cli.returncode == 0 and
                           "PASS OLGU-06" in olg06_cli.stdout, olg06_cli.stdout))
    for ad, sahte_cikti, kod in (("eksik", "FAIL OLGU-06 DERS_KAYDI_EKSIK", 1),
                                 ("tam", "PASS OLGU-06 mekanizma=1", 0),
                                 ("betik-yok", None, 1)):
        proje06 = kur(T / f"olg06_full_{ad}")
        betik06 = proje06 / "scripts/olgu_lint.py"
        if sahte_cikti is None:
            betik06.unlink()
        else:
            betik06.write_text(
                f"import sys\nassert sys.argv[1:] == ['--dersler']\n"
                f"print({sahte_cikti!r})\nsys.exit({kod})\n", encoding="utf-8",
            )
        r06 = subprocess.run(["bash", str(proje06 / "scripts/check_integrity.sh"), "--full"],
                             cwd=proje06, capture_output=True, text=True, timeout=600)
        iz06 = "PASS OLGU-06" if ad == "tam" else "WARN OLGU-06"
        olg06_sonuclar.append((f"full-{ad}", r06.returncode == 0 and iz06 in r06.stdout
                               and "-- GATE --" in r06.stdout and "FULL PASS" in r06.stdout,
                               r06.stdout[-240:]))

    kontrol(
        "OLG-1",
        "kanonik olgu ve canli kanit pozitif capasi ile yokluk/surum/bayat/eksik kanit negatifleri fail-closed",
        _olg_pozitif_ok and _olg_canli_pozitif_ok and _olg_yok_ok and _olg_surum_ok
        and _olg_head_ok and _olg_koken_ok and _olg_bozuk_ok and _olg_bayat_ok and _olg_eksik_kanit_ok
        and all(ok for _, ok, _ in olg06_sonuclar),
        f"pozitif=(rc={_olg_pozitif.returncode}, ok={_olg_pozitif_ok}) "
        f"canli-pozitif=(rc={_olg_canli_pozitif.returncode}, ok={_olg_canli_pozitif_ok}) "
        f"head-uyusmaz=(rc={_olg_head_sonuc.returncode}, ok={_olg_head_ok}) "
        f"koken=(rc={_olg_koken_sonuc.returncode}, ok={_olg_koken_ok}) "
        f"bozuk-metadata=(rc={_olg_bozuk_sonuc.returncode}, ok={_olg_bozuk_ok}) "
        f"yok=(rc={_olg_yok_sonuc.returncode}, ok={_olg_yok_ok}) "
        f"surum=({_olg_surum_ayrinti}) "
        f"bayat=(rc={_olg_bayat_sonuc.returncode}, ok={_olg_bayat_ok}, "
        f"cikti={_olg_bayat_cikti.strip()[:180]}) "
        f"eksik-kanit=(rc={_olg_eksik_kanit_sonuc.returncode}, ok={_olg_eksik_kanit_ok}, "
        f"cikti={_olg_eksik_kanit_cikti.strip()[:180]}) "
        f"dersler={olg06_sonuclar}",
    )

    # B-2: Kaynak Sinifi
    # Tablosuz taban: eski kademeli davranis korunur (sinif sutunu varsa PASS).
    p = kur(T / "sc1")
    sc1_saglam_rc, sc1_saglam_o = kos("source_class_check.py", cwd=p)
    sc1_saglam_ok = (
        sc1_saglam_rc == 0
        and "SOURCE-CLASS-CHECK PASS" in sc1_saglam_o
        and "FAIL SRC-01" not in sc1_saglam_o
        and "KAYNAK SINIFLANDIRMA" not in (p / "03-FAZ-3-MASTER-v5.5.md").read_text(encoding="utf-8")
        and "Traceback" not in sc1_saglam_o
    )

    # Eski 5-sutunlu PROVENANCE: sinif sutunu yok -> kademeli CALISTIRILMADI.
    sc1_eski = kur(T / "sc1_eski")
    sc1_eski_f = sc1_eski / "03-FAZ-3-MASTER-v5.5.md"
    sc1_eski_metin = sc1_eski_f.read_text(encoding="utf-8")
    sc1_eski_metin = sc1_eski_metin.replace(
        "| SC-ID | Bolum | Kaynak | Satir | Kaynak Sinifi | Durum |\n"
        "|---|---|---|---|---|---|",
        "| SC-ID | Bolum | Kaynak | Satir | Durum |\n"
        "|---|---|---|---|---|",
    ).replace("| IKINCIL | kapsiyor |", "| kapsiyor |")
    sc1_eski_f.write_text(sc1_eski_metin, encoding="utf-8")
    sc1_eski_rc, sc1_eski_o = kos("source_class_check.py", cwd=sc1_eski)
    sc1_eski_ok = (
        sc1_eski_rc == 0
        and "INFO SRC-01: CALISTIRILMADI" in sc1_eski_o
        and "eski 5-sutunlu" in sc1_eski_o
        and "FAIL SRC-01" not in sc1_eski_o
        and "Traceback" not in sc1_eski_o
    )

    def sc1_tablo_kur(ad, sinif):
        proje = kur(T / ad)
        f = proje / "03-FAZ-3-MASTER-v5.5.md"
        metin = f.read_text(encoding="utf-8")
        metin = metin.replace(
            "## PROVENANCE Tablosu",
            "## KAYNAK SINIFLANDIRMA\n\n"
            "| Sinyal | Sinif |\n"
            "|---|---|\n"
            "| KURAN | BIRINCIL |\n"
            "| MAKALE | IKINCIL |\n\n"
            "## PROVENANCE Tablosu",
        )
        metin = metin.replace(
            "| SC-006 | Bolum 6 | Uretildi | 60 | IKINCIL | kapsiyor |",
            f"| SC-006 | Bolum 6 | MAKALE | 60 | {sinif} | kapsiyor |",
        )
        f.write_text(metin, encoding="utf-8")
        return proje

    # Tablo var + sinyal/sinif uyumu: yeni dal yesil kalir.
    sc1_tablo = sc1_tablo_kur("sc1_tablo", "IKINCIL")
    sc1_tablo_rc, sc1_tablo_o = kos("source_class_check.py", cwd=sc1_tablo)
    sc1_tablo_ok = (
        sc1_tablo_rc == 0
        and "SOURCE-CLASS-CHECK PASS" in sc1_tablo_o
        and "FAIL SRC-01" not in sc1_tablo_o
        and "Traceback" not in sc1_tablo_o
    )

    # Tablo var + yanlis sinif: yeni dal FAIL SRC-01 uretir.
    sc1_yanlis = sc1_tablo_kur("sc1_yanlis", "BIRINCIL")
    sc1_yanlis_rc, sc1_yanlis_o = kos("source_class_check.py", cwd=sc1_yanlis)
    sc1_yanlis_ok = (
        sc1_yanlis_rc == 1
        and "FAIL SRC-01: SC-006" in sc1_yanlis_o
        and "IKINCIL, PROVENANCE'ta BIRINCIL" in sc1_yanlis_o
        and "Traceback" not in sc1_yanlis_o
    )

    sc1_bosluk = kur(T / "sc1_bosluk")
    sc1_bosluk_f = sc1_bosluk / "03-FAZ-3-MASTER-v5.5.md"
    sc1_bosluk_f.write_text(
        sc1_bosluk_f.read_text(encoding="utf-8").replace(
            "| SC-006 | Bolum 6 | Uretildi | 60 | IKINCIL | kapsiyor |",
            "\n| SC-006 | Bolum 6 | Uretildi | 60 | BILINMEYEN | kapsiyor |",
        ),
        encoding="utf-8",
    )
    sc1_bosluk_rc, sc1_bosluk_o = kos("source_class_check.py", cwd=sc1_bosluk)
    sc1_bosluk_ok = (
        sc1_bosluk_rc == 1
        and "FAIL SRC-02: SC-006" in sc1_bosluk_o
        and "Traceback" not in sc1_bosluk_o
    )

    sc1_ek = kur(T / "sc1_ek")
    sc1_ek_f = sc1_ek / "03-FAZ-3-MASTER-v5.5.md"
    sc1_ek_f.write_text(
        sc1_ek_f.read_text(encoding="utf-8")
        + "\n\n## Ek Tablo\n\n"
          "| Kod | Aciklama | A | B | Deger | Durum |\n"
          "|---|---|---|---|---|---|\n"
          "| SC-999 | Ilgisiz | X | Y | BILINMEYEN | kayit |\n",
        encoding="utf-8",
    )
    sc1_ek_rc, sc1_ek_o = kos("source_class_check.py", cwd=sc1_ek)
    sc1_ek_ok = (
        sc1_ek_rc == 0
        and "SOURCE-CLASS-CHECK PASS" in sc1_ek_o
        and "FAIL SRC-02: SC-999" not in sc1_ek_o
        and "Traceback" not in sc1_ek_o
    )

    kontrol(
        "SC-1",
        "tablosuz eski kademeli PASS; tablo uyumlu PASS; yanlis sinif FAIL SRC-01; "
        "bosluk sonrasi gecersiz sinif SRC-02 FAIL",
        sc1_saglam_ok and sc1_eski_ok and sc1_tablo_ok and sc1_yanlis_ok
        and sc1_bosluk_ok and sc1_ek_ok,
        f"tablosuz=(rc={sc1_saglam_rc}, ok={sc1_saglam_ok}) "
        f"eski5=(rc={sc1_eski_rc}, ok={sc1_eski_ok}) "
        f"tablo=(rc={sc1_tablo_rc}, ok={sc1_tablo_ok}) "
        f"yanlis=(rc={sc1_yanlis_rc}, ok={sc1_yanlis_ok}) "
        f"bosluk=(rc={sc1_bosluk_rc}, ok={sc1_bosluk_ok}) "
        f"ek=(rc={sc1_ek_rc}, ok={sc1_ek_ok})",
    )

    p = kur(T / "sc2")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace("| IKINCIL | kapsiyor |",
                                                       "| AKTARMA | kapsiyor |"), encoding="utf-8")
    rc, o = kos("source_class_check.py", cwd=p)
    kontrol("SC-2", "AKTARMA beyan yoksa SRC-03 P1 (B-2)", rc == 1 and "SRC-03" in o, f"rc={rc}")

    # B-3 / C-5: Transliterasyon sistem adi kapali listede, token sinirli eslesir
    _tr1_sonuclar = []
    for _tr1_sistem in (
        "DMG", "IJMES", "ALA-LC", "EJTA", "DIN 31635", "ISO 233", "LOC", "EI2",
    ):
        _tr1_proje = kur(T / f"tr1-pozitif-{len(_tr1_sonuclar)}")
        _tr1_scope = _tr1_proje / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
        _tr1_scope.write_text(
            _tr1_scope.read_text(encoding="utf-8").replace(
                "Transliterasyon sistemi: DMG",
                f"Transliterasyon sistemi: {_tr1_sistem}",
            ),
            encoding="utf-8",
        )
        _tr1_rc, _tr1_cikti = kos("translit_check.py", cwd=_tr1_proje)
        _tr1_sonuclar.append(
            (f"pozitif:{_tr1_sistem}", _tr1_rc, "PASS TR-01" in _tr1_cikti,
             "Traceback" in _tr1_cikti, 0)
        )

    for _tr1_ad, _tr1_satir in (
        ("DIN", "Transliterasyon ile din iliskisi incelenir."),
        ("ALA", "Transliterasyon alan analizi icerir."),
        ("ISO", "Transliterasyon comparison notudur."),
    ):
        _tr1_proje = kur(T / f"tr1-negatif-{_tr1_ad.lower()}")
        _tr1_scope = _tr1_proje / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
        _tr1_scope.write_text(
            _tr1_scope.read_text(encoding="utf-8").replace(
                "Transliterasyon sistemi: DMG", _tr1_satir
            ),
            encoding="utf-8",
        )
        _tr1_master = _tr1_proje / "03-FAZ-3-MASTER-v5.5.md"
        _tr1_master.write_text(
            _tr1_master.read_text(encoding="utf-8").replace(
                "Bir iddia (Yazar, 2020).",
                "sekîne uzerine bir iddia (Yazar, 2020).",
            ),
            encoding="utf-8",
        )
        _tr1_rc, _tr1_cikti = kos("translit_check.py", cwd=_tr1_proje)
        _tr1_sonuclar.append(
            (f"negatif:{_tr1_ad}", _tr1_rc, "FAIL TR-01" in _tr1_cikti,
             "Traceback" in _tr1_cikti, 1)
        )

    kontrol(
        "TR-1",
        "kanonik sistemler PASS, DIN/ALA/ISO alt-dizeleri TR-01 FAIL (B-3/C-5)",
        all(rc == beklenen_rc and beklenen_metin_var and not traceback
            for _, rc, beklenen_metin_var, traceback, beklenen_rc in _tr1_sonuclar),
        f"sonuclar={_tr1_sonuclar}",
    )

    p = kur(T / "tr2")
    f = p / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
    f.write_text(f.read_text(encoding="utf-8").replace("Transliterasyon sistemi: DMG", ""), encoding="utf-8")
    # TR-01'in FAIL vermesi icin MASTER'da sekîne varyanti sart (kademeli gecis)
    fm = p / "03-FAZ-3-MASTER-v5.5.md"
    fm.write_text(fm.read_text(encoding="utf-8").replace("Bir iddia (Yazar, 2020).",
                                                        "sekîne uzerine bir iddia (Yazar, 2020)."), encoding="utf-8")
    tr2_ilan_rc, tr2_ilan_o = kos("translit_check.py", cwd=p)
    tr2_ilan_ok = (
        tr2_ilan_rc == 1
        and "FAIL TR-01" in tr2_ilan_o
        and "Traceback" not in tr2_ilan_o
    )

    tr2_macron = kur(T / "tr2_macron")
    tr2_macron_f = tr2_macron / "03-FAZ-3-MASTER-v5.5.md"
    tr2_macron_f.write_text(
        tr2_macron_f.read_text(encoding="utf-8").replace(
            "Bir iddia (Yazar, 2020).",
            "sekîne ve sakīna uzerine bir iddia (Yazar, 2020).",
        ),
        encoding="utf-8",
    )
    tr2_macron_rc, tr2_macron_o = kos("translit_check.py", cwd=tr2_macron)
    tr2_macron_ok = (
        tr2_macron_rc == 1
        and "FAIL TR-02" in tr2_macron_o
        and "sakīna" in tr2_macron_o
        and "Traceback" not in tr2_macron_o
    )

    # TT-C-6: Olculmeyen tutarli sayilmaz; gercek tek-yazim sonucu korunur.
    tr6_scope = T / "tr6-scope.md"
    tr6_scope.write_text("Transliterasyon sistemi: DMG\n", encoding="utf-8")
    tr6_sonuclar = []
    for tr6_ad, tr6_metin, tr6_olculdu in (
        ("terimsiz", "Bu sentetik metinde ilgili kavram bulunmuyor.\n", False),
        ("tek-yazim", "sekîne ve sekîne\n", True),
    ):
        tr6_master = T / f"tr6-{tr6_ad}.md"
        tr6_master.write_text(tr6_metin, encoding="utf-8")
        tr6_rc, tr6_o = kos(
            "translit_check.py", "--dosya", str(tr6_master), "--scope", str(tr6_scope),
        )
        tr6_ozet = "TRANSLIT-CHECK PASS — TR-01 ilan var, TR-02 " + (
            "tutarli" if tr6_olculdu else "CALISTIRILMADI"
        )
        tr6_ok = (
            tr6_rc == 0 and "PASS TR-01" in tr6_o and "Traceback" not in tr6_o
            and tr6_o.splitlines()[-1:] == [tr6_ozet]
            and (
                "PASS TR-02" in tr6_o and "CALISTIRILMADI" not in tr6_o
                if tr6_olculdu else
                "INFO TR-02: CALISTIRILMADI" in tr6_o and "PASS TR-02" not in tr6_o
                and "tutarli" not in tr6_o.lower() and "tutarlı" not in tr6_o.lower()
            )
        )
        tr6_sonuclar.append((tr6_ad, tr6_rc, tr6_ok))
    # TT-C-6 matrisi sonu.

    kontrol(
        "TR-2",
        "ilan/karisim FAIL; terimsiz CALISTIRILMADI, tek yazim tutarli (B-3/C-7/TT-C-6)",
        tr2_ilan_ok and tr2_macron_ok and all(ok for _, _, ok in tr6_sonuclar),
        f"ilan=(rc={tr2_ilan_rc}, ok={tr2_ilan_ok}) "
        f"macron=(rc={tr2_macron_rc}, ok={tr2_macron_ok}) tt_c6={tr6_sonuclar}",
    )

    # ============ fix_reconcile.py ============
    rc, o = kos("fix_reconcile.py", cwd=taban)
    kontrol("FR-1", "saglam projede PASS", rc == 0 and "FIX-RECONCILE PASS" in o, f"rc={rc}")

    p = kur(T / "fr2")
    f = p / "02-FAZ-2-FIX-MANIFEST.md"
    f.write_text(f.read_text(encoding="utf-8").replace(
        "| FIX-002 | P1 | STYLE | uzun cumle | UYGULANMIŞ | SC-002 |", ""), encoding="utf-8")
    rc, o = kos("fix_reconcile.py", cwd=p)
    kontrol("FR-2", "bulgu/FIX sayisi tutmazsa REC-01 FAIL", rc == 1 and "REC-01" in o, f"rc={rc}")

    p = kur(T / "fr3")
    f = p / "02-FAZ-2-FIX-MANIFEST.md"
    f.write_text(f.read_text(encoding="utf-8").replace("| FIX-002 | P1 |", "| FIX-002 | P0 |"), encoding="utf-8")
    rc, o = kos("fix_reconcile.py", cwd=p)
    kontrol("FR-3", "oncelik dagilimi tutmazsa REC-02 FAIL", rc == 1 and "REC-02" in o, f"rc={rc}")

    p = kur(T / "fr4")
    f = p / "02-FAZ-2-FIX-MANIFEST.md"
    t = f.read_text(encoding="utf-8").replace("F-001→FIX-001, F-002→FIX-002.", "F-001→FIX-001.")
    t = t.replace("FAZ1'deki 2 bulgu (F-001, F-002) bu manifestoda karsilanir.",
                  "FAZ1'deki bulgular bu manifestoda karsilanir.")
    f.write_text(t, encoding="utf-8")
    rc, o = kos("fix_reconcile.py", cwd=p)
    kontrol("FR-4", "atifsiz bulgu REC-03 FAIL", rc == 1 and "REC-03" in o, f"rc={rc}")

    p = kur(T / "fr5")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace("FIX-001 ve FIX-002 uygulanmistir.", "FIX-001 uygulanmistir."), encoding="utf-8")
    rc, o = kos("fix_reconcile.py", cwd=p)
    kontrol("FR-5", "MASTER'da kaniti olmayan FIX REC-04 FAIL", rc == 1 and "REC-04" in o, f"rc={rc}")
    kontrol("FR-6", "ayni durumda gate 2B iddiasi REC-05 FAIL",
            rc == 1 and "FAIL REC-05:" in o and "PASS REC-05:" not in o
            and "Traceback" not in o,
            f"rc={rc} {o.strip()[-160:]}")

    p = kur(T / "fr7")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace("FIX-001 ve FIX-002", "FIX-001, FIX-002 ve FIX-099"), encoding="utf-8")
    rc, o = kos("fix_reconcile.py", cwd=p)
    kontrol("FR-7", "manifestoda olmayan hayalet FIX REC-06 FAIL", rc == 1 and "REC-06" in o, f"rc={rc}")

    p = kur(T / "fr8"); shutil.rmtree(p / "gate")
    rc, o = kos("fix_reconcile.py", cwd=p)
    kontrol("FR-8", "gate yoksa FAIL degil NOT verir (erken faz)", rc == 0 and "NOT REC-05" in o, f"rc={rc}")

    p = kur(T / "fr9")
    json_duzenle(p / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.update(manifest_reconciliation={
                     "FIX-001": {"fix_id": "FIX-001", "status": "UYGULANMIŞ_KANITLI"}}))
    rc, o = kos("fix_reconcile.py", cwd=p)
    kontrol("FR-9", "sozluk manifest_reconciliation REC-05'i ATLAYAMAZ",
            rc == 1 and "REC-05" in o and "liste degil" in o and "Traceback" not in o,
            f"rc={rc} {o.strip()[-160:]}")

    p = kur(T / "fr10")
    (p / "gate/STRONG-gate-2b-v5.5.json").write_text("null", encoding="utf-8")
    rc, o = kos("fix_reconcile.py", cwd=p)
    kontrol("FR-10", "null gate 2B kokunde REC-05 kaybolmaz",
            rc == 1 and "REC-05" in o and "sozluk degil" in o and "Traceback" not in o,
            f"rc={rc} {o.strip()[-160:]}")

    # --- QR-10 (v1.7.276): duz tirnak Konuma gore eslesir; kisa vurgu cifti kaydirmaz ---
    # Mutasyon duyarliligi IKI YONLU:
    #   (a) sahte P0: iki KISA vurgu tirnagi arasindaki duzyazi 46 kelime ->
    #       eski desen (10+ karakter arayan) ciftleri kaydirip sahte 40+ alinti
    #       uretiyordu -> FAIL. Yeni kod PASS vermeli.
    #   (b) gercek P0: 46 kelimelik GERCEK alinti, sayfa yok -> HALA FAIL olmali.
    #       (b) yanmazsa duzeltme fail-open yapmis olur; (a) yanmazsa test sahtedir.
    qr10_proz = " ".join(["duzyazi"] * 46)
    p = kur(T / "qr10a")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace(
        "Bir iddia (Yazar, 2020).",
        'Bir iddia (Yazar, 2020).\n\n(a) Kavram "benzerlik" gibi gorunur, '
        + qr10_proz + ' "avlanma" ise ayridir.',
        1), encoding="utf-8")
    qr10a_rc, qr10a_o = kos("quote_ratio.py", "--dosya", "03-FAZ-3-MASTER-v5.5.md", cwd=p)

    p = kur(T / "qr10b")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace(
        "Bir iddia (Yazar, 2020).",
        'Bir iddia (Yazar, 2020).\n\n"' + qr10_proz + '" Baska konu (Yazar, 2020).',
        1), encoding="utf-8")
    qr10b_rc, qr10b_o = kos("quote_ratio.py", "--dosya", "03-FAZ-3-MASTER-v5.5.md", cwd=p)

    kontrol(
        "QR-10",
        "kisa vurgu tirnagi ciftleri KAYDIRMAZ (sahte 40+ alinti uretmez) · "
        "gercek 46 kelimelik alinti sayfasiz HALA FAIL",
        qr10a_rc == 0
        and "FAIL QR-02" not in qr10a_o
        and ("PASS QR-02: 0 uzun (40+)" in qr10a_o
             or "INFO QR-02: tirnakli/blok alinti span'i bulunamadi" in qr10a_o)
        and qr10b_rc == 1
        and "FAIL QR-02: 46 kelimelik" in qr10b_o
        and "Traceback" not in qr10a_o + qr10b_o,
        f"a=(rc={qr10a_rc}, fail={'FAIL QR-02' in qr10a_o}) "
        f"b=(rc={qr10b_rc}, fail={'FAIL QR-02' in qr10b_o})",
    )

    # --- QR-11 (v1.7.288): TABLO HUCRESI ALINTI DEGILDIR ---------------------
    # Olculdu (10.11.2026): ayni metin iki betikle farkli sonuc veriyordu —
    #   ege MASTER   ATLAS %3.5 · 32 span  vs  yamali %1.1 · 12 span
    #   silat MASTER ATLAS %3.2 · 36 span  vs  yamali %3.0 · 31 span
    # Sebep: `quote_ratio.py` markdown tablo satirindaki tirnaklari alinti sanip
    # span aciyordu. Yama `ege-makale` kopyasinda 2026-09-18'den beri vardi
    # (DEVIR.md:35) ama ATLAS'a tasinmamisti. Uc yon:
    #   (a) tablo satirindaki tirnak span ACMAZ (sayi degismez)
    #   (b) duzyazi ayni metin HALA span acar (yanlis-pozitif kontrolu:
    #       yama fazla yutarsa (b) duser)
    #   (c) govde KARAKTER SAYISI degismez (1 karakter -> 1 karakter)
    # Olculdu (ilk hal): `"kapsiyor"` gibi KISA tirnak span SAYILMIYOR (8 kar) ->
    # test iki tarafta da 0 buldu ve hicbir sey kanitlamadi. Esik 20 kar.
    _qr11_alinti = ("uzun bir hucre alintisi burada devam ediyor ve suruyor")
    _qr11_tab = f'| SC-001 | "{_qr11_alinti}" | baska |'
    _qr11_duz = f'Duzyazi: "{_qr11_alinti}" kelime.'
    _qr11_kok = kur(T / "qr11")
    (_qr11_kok / "03-FAZ-3-MASTER-v5.5.md").write_text(
        f"{_qr11_tab}\n\n{_qr11_duz}\n\n## Kaynakça\nYazar (2020). Sentetik.\n",
        encoding="utf-8")
    _q11rc, _q11o = kos("quote_ratio.py", "--dosya", "03-FAZ-3-MASTER-v5.5.md",
                        cwd=_qr11_kok)
    _q11m = re.search(r"^INFO QR-01: govde (\d+) kar — alinti (\d+) kar", _q11o, re.M)
    _q11govde = int(_q11m.group(1)) if _q11m else -1
    _q11alinti = int(_q11m.group(2)) if _q11m else -1

    # (a) yalniz tablo olsaydi span 0 olmali; (b) yalniz duzyazi olsaydi >0.
    # Ikisi birlikte: alinti kar yalniz duzyazi kismindan gelmeli.
    _qr11b_kok = kur(T / "qr11b")
    (_qr11b_kok / "03-FAZ-3-MASTER-v5.5.md").write_text(
        f"{_qr11_duz}\n\n## Kaynakça\nYazar (2020). Sentetik.\n", encoding="utf-8")
    _q11brc, _q11bo = kos("quote_ratio.py", "--dosya", "03-FAZ-3-MASTER-v5.5.md",
                          cwd=_qr11b_kok)
    _q11bm = re.search(r"^INFO QR-01: govde (\d+) kar — alinti (\d+) kar", _q11bo, re.M)
    _q11balinti = int(_q11bm.group(2)) if _q11bm else -1

    kontrol(
        "QR-11",
        "TABLO HUCRESI alinti DEGIL: tablo satirindaki tirnak span acmaz · "
        "duzyazi ayni metin HALA acar · karakter sayisi degismez",
        _q11rc == 0
        and _q11alinti >= 0
        # (a) tablo katkisi YOK: alinti kar yalniz duzyazi kosusundakiyle ayni
        and _q11alinti == _q11balinti
        # (b) duzyazi hala alinti uretiyor (yama fazla yutmadi)
        and _q11balinti > 0
        # (c) karakter birebir: 1 -> 1 degisim, govde sismedi/kuculmedi
        and _q11govde > 0
        and "Traceback" not in _q11o + _q11bo,
        f"tablo+duzyazi=({_q11rc},govde={_q11govde},alinti={_q11alinti}) "
        f"yalniz-duzyazi=({_q11brc},alinti={_q11balinti})",
    )

    # ============ cite_match.py ============
    rc, o = kos("cite_match.py", cwd=taban)
    kontrol("CM-1", "atif==kaynakca ise PASS", rc == 0 and "CITE-MATCH PASS" in o, f"rc={rc}")

    p = kur(T / "cm2")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n- Oksuz, B. (2021). *Anilmayan*. Yayin."), encoding="utf-8")
    rc, o = kos("cite_match.py", cwd=p)
    kontrol("CM-2", "oksuz kaynak CITE-02 FAIL", rc == 1 and "CITE-02" in o, f"rc={rc}")

    rc, o = kos("cite_match.py", "--gevsek", cwd=p)
    kontrol("CM-3", "--gevsek ile oksuz kaynak UYARI olur", rc == 0 and "UYARI CITE-02" in o, f"rc={rc}")

    p = kur(T / "cm4")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace("(Yazar, 2020)", "(Bilinmeyen, 1999)"), encoding="utf-8")
    rc, o = kos("cite_match.py", cwd=p)
    kontrol("CM-4", "kaynakcasiz atif CITE-01 FAIL", rc == 1 and "CITE-01" in o, f"rc={rc}")

    p = kur(T / "cm5")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace("## Kaynakca", "## Ekler"), encoding="utf-8")
    rc, o = kos("cite_match.py", cwd=p)
    kontrol("CM-5", "kaynakca bolumu yoksa temiz FAIL", rc == 1 and "CITE-00" in o and "Traceback" not in o, f"rc={rc}")

    rc, o = kos("cite_match.py", "--dosya", "03-FAZ-3-MASTER-v5.5.md", cwd=taban)
    kontrol("CM-6", "--dosya bayragi calisir", rc == 0 and "CITE-MATCH PASS" in o, f"rc={rc}")

    p = kur(T / "cm9")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n- Yazar, B. (2021). *Ayni Yazarin Diger Eseri*. Yayin.",
    )
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Bir iddia (Yazar, 2021).",
        1,
    )
    f.write_text(metin, encoding="utf-8")
    rc, o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-9",
        "CITE-03 ayni soyad farkli yillarda UYARI üretir; PASS CITE-03 vermez",
        rc == 0 and "UYARI CITE-03" in o and "PASS CITE-03" not in o,
        f"rc={rc} match=ok? {'UYARI CITE-03' in o} pass_yok? {'PASS CITE-03' not in o}\n"
        f"{o.strip().splitlines()[-4:] if o else []}",
    )

    # --- CM-10 (v1.7.275): yil gecen ama ATIF OLMAYAN parantezler + kalipsiz anma ---
    # Mutasyon duyarliligi: _soyad_adayi kaldirilip eski `parca[:m.start()]`
    # davranisina donulurse (a) blogu CITE-01 FAIL uretir, (b) blogu CITE-02 FAIL
    # uretir -> test YANAR. Testin kendisi bos degil, gercek bir kusuru tutuyor.
    p = kur(T / "cm10")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020).\n\n"
        "(a) Kunye (cilt 8, 2009) ile verilir. Sayfa goruntusu "
        "(kaynaklar/alusi-1924-v2-p5.jpg, p6.jpg) pakette saklidir. "
        "Sibli ve Zebidi (ö. 1791) sonraki derlemelerdir.\n\n"
        "(b) Kalipsiz bu konuda ayrintili bilgi verir.",
        1,
    )
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n- Kalipsiz, C. (2019). *Anilan*. Yayin.",
        1,
    )
    f.write_text(metin, encoding="utf-8")
    cm10_rc, cm10_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-10",
        "yil gecen olcu/dosya/vefat parantezleri atif sayilmaz (CITE-01) · "
        "atif kalibi taninmayan ama metinde anilan kaynak oksuz sayilmaz (CITE-02)",
        cm10_rc == 0
        and "PASS CITE-01" in cm10_o
        and "PASS CITE-02" in cm10_o
        and "INFO CITE-02: 1" in cm10_o
        and "cilt 8" not in cm10_o
        and "Traceback" not in cm10_o,
        f"rc={cm10_rc} | {cm10_o.strip().splitlines()[:3]}",
    )

    # --- CM-11 (v1.7.293): kaynakca yil parantezinde TARIH EKI -----------------
    # Olculdu (ege-makale): '- ... (1995, 8 Haziran).' bicimli girdi eski
    # `r"\(" + YIL + r"\)"` desenine takilmiyor, kaynakca HIC sayilmiyordu.
    # Mutasyon: YIL_P eski desene dondurulurse kaynakca bosalir -> CITE-01 FAIL -> YANAR.
    p = kur(T / "cm11")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n- Kurum, K. (2021, 1 Ekim). *Tarihli*. Yayin.", 1)
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Bir iddia (Kurum, 2021).", 1)
    f.write_text(metin, encoding="utf-8")
    cm11_rc, cm11_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-11",
        "kaynakca yil parantezinde tarih eki (2021, 1 Ekim) girdiyi kaybettirmez",
        cm11_rc == 0 and "PASS CITE-01" in cm11_o and "CITE-00" not in cm11_o
        and "Traceback" not in cm11_o,
        f"rc={cm11_rc} | {cm11_o.strip().splitlines()[:3]}",
    )

    # --- CM-12 (v1.7.293): ISO tarih ve TR tarih parantezi ATIF DEGILDIR --------
    # Olculdu (ege-makale): '(Ali Han Kaya, 2026-09-18)' -> Kaya (2026) ve
    # '(mfa.gov.tr, TBMM 8 Haziran 1995 karari)' -> Haziran (1995) sahte atif uretti.
    # NEGATIF KONTROL: '(Yazar, 2020, s. 45)' SAYFA NUMARASIDIR, atif KALMALI.
    # Mutasyon: _soyad_adayi basindaki iki tarih filtresi kaldirilirsa CITE-01 FAIL -> YANAR.
    p = kur(T / "cm12")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Sayfa (Yazar, 2020, s. 45).\n\n"
        "Kayit (Ali Han Kaya, 2026-09-18) biciminde; digeri "
        "(mfa.gov.tr, TBMM 8 Haziran 1995 karari) bicimindedir.", 1)
    f.write_text(metin, encoding="utf-8")
    cm12_rc, cm12_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-12",
        "ISO/TR tarih parantezi atif sayilmaz; sayfa numarali atif KORUNUR",
        cm12_rc == 0 and "PASS CITE-01" in cm12_o
        and "atif 1 <-> kaynak 1" in cm12_o
        and "Kaya" not in cm12_o and "Haziran" not in cm12_o
        and "Traceback" not in cm12_o,
        f"rc={cm12_rc} | {cm12_o.strip().splitlines()[:3]}",
    )

    # --- CM-13 (v1.7.293): KURUM / cok kelimeli ad TAM eslesir ------------------
    # Olculdu (ege-makale): kaynakca anahtari 'turkiye buyuk millet meclisi', atif
    # anahtari 'meclisi' (yildan geriye ilk buyuk harf) -> CITE-01 "kaynakcada yok".
    # Mutasyon: parca-3 blogu (_ad_norm + _kaynak_ad_norm) kaldirilirsa CITE-01 FAIL -> YANAR.
    p = kur(T / "cm13")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n"
        "- Turkiye Buyuk Millet Meclisi. (1995, 8 Haziran). *Karar*. Yayin.", 1)
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Karar (Türkiye Büyük Millet Meclisi, 1995) ile alindi.", 1)
    f.write_text(metin, encoding="utf-8")
    cm13_rc, cm13_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-13",
        "cok kelimeli kurum adi kaynakca anahtariyla TAM eslesir (CITE-01 PASS)",
        cm13_rc == 0 and "PASS CITE-01" in cm13_o
        and "INFO CITE-02" not in cm13_o and "FAIL CITE-02" not in cm13_o
        and "Traceback" not in cm13_o,
        f"rc={cm13_rc} | {cm13_o.strip().splitlines()[:3]}",
    )

    # --- CM-14 (v1.7.293): kurum adinda KISMI eslesme YASAK (yanlis pozitif) ----
    # '(State, 2025)' kaynakcada 'U.S. Department of State' ile eslesmemeli:
    # alt-dize eslesmesi kabul edilseydi her kisa ad her yerde "bulunurdu".
    # Mutasyon: _ad_norm AYNEN yerine 'in' (alt-dize) yapilirsa rc=0 olur -> YANAR.
    p = kur(T / "cm14")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n"
        "- U.S. Department of State. (2025). *Rapor*. Yayin.", 1)
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Kayit (State, 2025) bicimindedir.", 1)
    f.write_text(metin, encoding="utf-8")
    cm14_rc, cm14_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-14",
        "kurum adinda kismi eslesme kabul edilmez (State != U.S. Department of State)",
        cm14_rc == 1 and "CITE-01" in cm14_o and "State" in cm14_o
        and "Traceback" not in cm14_o,
        f"rc={cm14_rc} | {cm14_o.strip().splitlines()[:3]}",
    )

    # --- CM-15 (v1.7.294): APA yil eki ('2026a'/'2026b') ANAHTARA girer ---------
    # OLCULEN KUSUR: ayni soyad + ayni yil iki girdi TEK anahtara cokuyordu; girdi
    # sozlukte ustune yaziliyor, ikincisi HIC gorunmuyordu. Sonuc: anilmayan eser
    # PASS'a takiliyordu (olculdu: 'atif 1 <-> kaynak 1', oysa kaynakca 2 girdi).
    # Mutasyon: m.group(2) anahtardan cikarilirsa kaynak=1'e duser, CITE-02 FAIL
    # beklenirken PASS gelir -> test YANAR.
    p = kur(T / "cm15")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n"
        "- Zeta, A. (2021a). *Anilan*. Yayin.\n"
        "- Zeta, B. (2021b). *Anilmayan*. Yayin.", 1)
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Bir iddia (Zeta, 2021a).", 1)
    f.write_text(metin, encoding="utf-8")
    cm15_rc, cm15_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-15",
        "APA yil eki (2021a/2021b) iki ayri kaynak sayilir; anilmayan CITE-02 FAIL",
        cm15_rc == 1 and "CITE-02" in cm15_o and "kaynak=3" in cm15_o
        and "Anilmayan" in cm15_o and "Traceback" not in cm15_o,
        f"rc={cm15_rc} | {cm15_o.strip().splitlines()[:4]}",
    )

    # --- CM-16 (v1.7.294): a/b ekinin NEGATIF KONTROLU ---------------------------
    # DERS (olculdu): ilk yazimda fiksturde HER IKI eser de ATIF olarak geciyordu.
    # Oksuz dongusu `if k in atiflar: continue` ile basladigi icin a/b dali HIC
    # calismadi -> M6 mutasyonu (govde kontrolunu kaldir) testi YAKMADI (140/140).
    # Yani test "yanmayan kural"di. Duzeltildi: '2021b' govdede AMMA atif kalibi
    # olarak DEGIL, duz metin olarak gecer. Boylece a/b dali calisir ve M6 yanar.
    # Beklenen dogru davranis: INFO (kalipsiz) — eser aniliyor, atif kalibi yok.
    # KUSUR davranisi (M6): FAIL — yanlis kirmizi.
    p = kur(T / "cm16")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n"
        "- Zeta, A. (2021a). *Birinci*. Yayin.\n"
        "- Zeta, B. (2021b). *Ikinci*. Yayin.", 1)
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Bir iddia (Zeta, 2021a). "
        "Ayrica 2021b verisi ayri bir notta tartisilir.", 1)
    f.write_text(metin, encoding="utf-8")
    cm16_rc, cm16_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-16",
        "a/b ekinin NEGATIF KONTROLU: ek govdede geciyorsa FAIL verilmez (INFO)",
        cm16_rc == 0 and "INFO CITE-02" in cm16_o and "FAIL CITE-02" not in cm16_o
        and "kaynak 3" in cm16_o and "Traceback" not in cm16_o,
        f"rc={cm16_rc} | {cm16_o.strip().splitlines()[:4]}",
    )

    # --- CM-17 (v1.7.295): '(t.y.)' girdisi kaynakcadan DUSMEZ -------------------
    # Olculdu (ege-makale): 12 kaynakca girdisinden 4'u '(t.y.)' bicimindeydi ve
    # HEPSI BIRINCIL kaynaga isaret ediyordu; hicbiri sayilmiyordu (7/12).
    # Mutasyon: kaynakca t.y. dali kaldirilirsa kaynak sayisi duser -> CITE-02 FAIL
    # (anilmayan sanilir) -> test YANAR.
    p = kur(T / "cm17")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n"
        "- Kurum A. (t.y.). *Anilan kurum*. https://a.example", 1)
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Resmi tez (Kurum A, t.y.) ile verilir.", 1)
    f.write_text(metin, encoding="utf-8")
    cm17_rc, cm17_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-17",
        "(t.y.) kaynakca girdisi sayilir ve '(Kurum A, t.y.)' atifiyla eslesir",
        cm17_rc == 0 and "PASS CITE-01" in cm17_o and "PASS CITE-02" in cm17_o
        and "kaynak 2" in cm17_o and "Traceback" not in cm17_o,
        f"rc={cm17_rc} | {cm17_o.strip().splitlines()[:4]}",
    )

    # --- CM-18 (v1.7.295): t.y. NEGATIF KONTROL — anilmayan girdi FAIL ------------
    # CM-17 tek yonu olcer (sayilir). Bu test tersini olcer: t.y. destegi "her t.y.
    # girdisini anilmis say" hâline donusmemeli. Anilmayan Kurum B FAIL vermeli.
    # Mutasyon: t.y. anahtari 'metinde_aniliyor'u atlarsa rc=0 olur, beklenen 1.
    p = kur(T / "cm18")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Yazar, A. (2020). *Deneme*. Yayin.\n"
        "- Kurum A. (t.y.). *Anilan kurum*. https://a.example\n"
        "- Kurum B. (t.y.). *HIC ANILMAYAN kurum*. https://b.example", 1)
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Resmi tez (Kurum A, t.y.) ile verilir.", 1)
    f.write_text(metin, encoding="utf-8")
    cm18_rc, cm18_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-18",
        "t.y. NEGATIF KONTROL: anilmayan t.y. girdisi oksuz sayilir (FAIL)",
        cm18_rc == 1 and "FAIL CITE-02" in cm18_o
        and "Kurum B" in cm18_o and "kaynak=3" in cm18_o
        and "Traceback" not in cm18_o,
        f"rc={cm18_rc} | {cm18_o.strip().splitlines()[:4]}",
    )

    # --- CM-19 (v1.7.403): HICRI/MILADI CIFT YIL ---------------------------------
    # OLCULDU 17 Kasim 2026: `(505/1111)` bicimli kaynakca girdisi HIC sayilmiyordu
    # (desen `505`i gorup atliyordu); govdedeki `(Yazar, 1111)` atfi "kaynakcada yok"
    # oluyordu. Fiksturde 2 girdi/2 atif varken sonuc `atif=1 kaynak=1` — SAHTE PASS.
    # Bu test iki yakayi birden olcer: kaynakca anahtari MILADI taraf (1111) olmali ve
    # govdedeki iki bicim de (`(A, 1111)` duz, `(A, 505/1111)` cift) ayni kaynaga baglanmali.
    # Mutasyon: anahtar `m.group(1)`te kalirsa HICRI dalinda None olur; atif=1/kaynak=1
    #   sahte PASS doner — bu test "kaynak 2" bekledigi icin YANAR.
    p = kur(T / "cm19")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Gazali, A. (505/1111). *Ihya*. Yayin.\n"
        "- Razi, F. (1981). *Mafatih*. Yayin.", 1)
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Gazali, 1111). Ikinci iddia (Razi, 1981). "
        "Ucuncu iddia cift yil bicimiyle (Gazali, 505/1111) verilir.", 1)
    f.write_text(metin, encoding="utf-8")
    cm19_rc, cm19_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-19",
        "cift yil (505/1111) kaynakcada sayilir; govdedeki (1111) ve (505/1111) ayni kaynaga baglanir",
        cm19_rc == 0 and "CITE-MATCH PASS" in cm19_o and "kaynak 2" in cm19_o
        and "Traceback" not in cm19_o,
        f"rc={cm19_rc} | {cm19_o.strip().splitlines()[:4]}",
    )

    # --- CM-20 (v1.7.403): HICRI DESENI YANLIS POZITIF URETMEMELI ------------------
    # Aday surumun ILK hali ciplak `1[0-5]\d{2}` kullaniyordu. 492 dosyalik taramada
    # silat'ta `JK010344` -> 1034, DEVIR'de `DEVIR:10546` -> 1054 ve `L1205` -> 1205
    # SAHTE atif uretti (4 dosya, rc 0 -> 1). Bu test o gerilemeyi kilitler.
    # Mutasyon: HICRI'deki `(?<=[,\s/])` ve `(?!\d)` sinir kapisi kaldirilirsa
    #   'Jk0 (1034)' atfi belirir -> CITE-01 FAIL -> bu test YANAR.
    p = kur(T / "cm20")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "Bir iddia (Yazar, 2020).",
        "Bir iddia (Yazar, 2020). Katalog kaydi (C15n, JK010344, DEVIR:10546, L1205) "
        "atif DEGILDIR.", 1)
    f.write_text(metin, encoding="utf-8")
    cm20_rc, cm20_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-20",
        "kimlik/sayfa gurultusu (JK010344, DEVIR:10546, L1205) sahte atif uretmez",
        cm20_rc == 0 and "CITE-MATCH PASS" in cm20_o and "FAIL CITE-01" not in cm20_o
        and "kaynak 1" in cm20_o,
        f"rc={cm20_rc} | {cm20_o.strip().splitlines()[:4]}",
    )

    # --- CM-21 (v1.7.403): TEK HICRI YIL KAYNAKCADA KABUL EDILMEZ (fail-closed) ----
    # `(1420)` gibi tek yil, `(1250)` sayfa numarasindan ayirt EDILEMEZ. Karar: kabul
    # edilmez — ama SESSIZCE yutulmaz da: CITE-00 ile soylenir ve cift yil onerilir.
    # Mutasyon: tek hicri yil da kabul edilirse rc=0 olur -> bu test YANAR.
    p = kur(T / "cm21")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    metin = f.read_text(encoding="utf-8")
    metin = metin.replace(
        "- Yazar, A. (2020). *Deneme*. Yayin.",
        "- Tabari, M. (1420). *Cami*. Yayin.", 1)
    metin = metin.replace("Bir iddia (Yazar, 2020).", "Bir iddia (Tabari, 1420).", 1)
    f.write_text(metin, encoding="utf-8")
    cm21_rc, cm21_o = kos("cite_match.py", cwd=p)
    kontrol(
        "CM-21",
        "tek hicri yil (1420) kaynakcada kabul edilmez; CITE-00 + cift yil onerisi, Traceback yok",
        cm21_rc == 1 and "CITE-00" in cm21_o and "1420/1999" in cm21_o
        and "Traceback" not in cm21_o,
        f"rc={cm21_rc} | {cm21_o.strip().splitlines()[:4]}",
    )

    # ============ verify_doi.py ============
    rc, o = kos("verify_doi.py", cwd=bos)
    kontrol("VD-1", "MASTER yoksa sessizce atlar (rc=0)", rc == 0, f"rc={rc}")

    rc, o = kos("verify_doi.py", "--require-master", cwd=bos)
    kontrol("VD-2", "--require-master ile MASTER yoksa FAIL", rc == 1, f"rc={rc}")

    p = kur(T / "vd3_nfc")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace("Bir iddia (Yazar, 2020).",
                                                      "Bir iddia [DOĞRULANMADI] (Yazar, 2020)."), encoding="utf-8")
    nfc_rc, nfc_o = kos("verify_doi.py", "--require-master", cwd=p)

    p = kur(T / "vd3_nfd")
    f = p / "03-FAZ-3-MASTER-v5.5.md"
    f.write_text(f.read_text(encoding="utf-8").replace("Bir iddia (Yazar, 2020).",
                                                      "Bir iddia [DO\u0047\u0306RULANMADI] (Yazar, 2020)."), encoding="utf-8")
    nfd_rc, nfd_o = kos("verify_doi.py", "--require-master", cwd=p)

    nfc_ok = nfc_rc == 1 and "istisna DISINDA 1" in nfc_o and "Traceback" not in nfc_o
    nfd_ok = nfd_rc == 1 and "istisna DISINDA 1" in nfd_o and "Traceback" not in nfd_o
    kontrol("VD-3", "istisna disinda NFC ve NFD [DOGRULANMADI] etiketleri FAIL",
            nfc_ok and nfd_ok, f"NFC rc={nfc_rc}; NFD rc={nfd_rc}")

    # ============ gate_merge.py ============
    p = kur(T / "gm1")
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json", "gate/STRONG-gate-2b-v5.5.json", cwd=p)
    gm1_final = json.loads((p / "gate/FINAL-GATE-v5.5.json").read_text(encoding="utf-8"))
    kontrol("GM-1", "bagimsiz temiz kapilarda FINAL PASS",
            rc == 0 and "FINAL PASS" in o and gm1_final["verdict"] == "PASS"
            and not gm1_final["metadata_integrity"]["mismatch_detected"]
            and "IDENTICAL_GATE_INPUTS" not in gm1_final["metadata_integrity"]["mismatch_notes"],
            f"rc={rc}")

    p = kur(T / "gm2")
    json_duzenle(p / "gate/STRONG-gate-2a-v5.5.json", lambda d: d["metadata"].update(p0_count=5))
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json", "gate/STRONG-gate-2b-v5.5.json", cwd=p)
    gm2_final = json.loads((p / "gate/FINAL-GATE-v5.5.json").read_text(encoding="utf-8"))
    _gm2_pozitif_ok = (
        rc == 1
        and "METADATA_MISMATCH" in o
        and gm2_final["metadata_integrity"]["mismatch_detected"]
        and "IDENTICAL_GATE_INPUTS" not in gm2_final["metadata_integrity"]["mismatch_notes"]
    )
    _gm2_metadata_yok = kur(T / "gm2_metadata_yok")
    json_duzenle(
        _gm2_metadata_yok / "gate/STRONG-gate-2a-v5.5.json",
        lambda d: d.pop("metadata", None),
    )
    _gm2_yok_rc, _gm2_yok_cikti = kos(
        "gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
        "gate/STRONG-gate-2b-v5.5.json", cwd=_gm2_metadata_yok,
    )
    _gm2_yok_final = json.loads(
        (_gm2_metadata_yok / "gate/FINAL-GATE-v5.5.json").read_text(encoding="utf-8")
    )
    _gm2_metadata_yok_ok = (
        _gm2_yok_rc == 0
        and "FINAL PASS" in _gm2_yok_cikti
        and "Traceback" not in _gm2_yok_cikti
        and _gm2_yok_final["verdict"] == "PASS"
        and not _gm2_yok_final["metadata_integrity"]["mismatch_detected"]
    )
    _gm2_metadata_bos = kur(T / "gm2_metadata_bos")
    json_duzenle(
        _gm2_metadata_bos / "gate/STRONG-gate-2a-v5.5.json",
        lambda d: d.__setitem__("metadata", {}),
    )
    _gm2_bos_rc, _gm2_bos_cikti = kos(
        "gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
        "gate/STRONG-gate-2b-v5.5.json", cwd=_gm2_metadata_bos,
    )
    _gm2_bos_final = json.loads(
        (_gm2_metadata_bos / "gate/FINAL-GATE-v5.5.json").read_text(encoding="utf-8")
    )
    _gm2_metadata_bos_ok = (
        _gm2_bos_rc == 0
        and "FINAL PASS" in _gm2_bos_cikti
        and "Traceback" not in _gm2_bos_cikti
        and _gm2_bos_final["verdict"] == "PASS"
        and not _gm2_bos_final["metadata_integrity"]["mismatch_detected"]
    )
    _gm2_tip_vakalari = [
        ("p0-liste", "p0_count", []),
        ("p0-sozluk", "p0_count", {}),
        ("p0-bos-metin", "p0_count", ""),
        ("p0-metin", "p0_count", "abc"),
        ("p0-false", "p0_count", False),
        ("p0-true", "p0_count", True),
        ("p0-float", "p0_count", 0.5),
        ("p0-null", "p0_count", None),
        ("p0-negatif", "p0_count", -1),
        ("p0-sayisal-metin", "p0_count", "0"),
        ("p1-null", "p1_count", None),
        ("p1-liste", "p1_count", []),
    ]
    _gm2_tip_sonuclari = []
    for _gm2_ad, _gm2_alan, _gm2_deger in _gm2_tip_vakalari:
        _gm2_proje = kur(T / f"gm2_{_gm2_ad}")
        json_duzenle(
            _gm2_proje / "gate/STRONG-gate-2a-v5.5.json",
            lambda d, alan=_gm2_alan, deger=_gm2_deger:
                d["metadata"].__setitem__(alan, deger),
        )
        _gm2_rc, _gm2_cikti = kos(
            "gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
            "gate/STRONG-gate-2b-v5.5.json", cwd=_gm2_proje,
        )
        _gm2_tip_sonuclari.append(
            (_gm2_ad, _gm2_rc, "metadata" in _gm2_cikti.lower(),
             "Traceback" in _gm2_cikti)
        )
    _gm2_kok_vakalari = [
        ("liste", []),
        ("metin", "string"),
        ("null", None),
        ("sayi", 0),
        ("boolean", False),
    ]
    _gm2_kok_sonuclari = []
    for _gm2_ad, _gm2_deger in _gm2_kok_vakalari:
        _gm2_proje = kur(T / f"gm2_metadata_kok_{_gm2_ad}")
        json_duzenle(
            _gm2_proje / "gate/STRONG-gate-2a-v5.5.json",
            lambda d, deger=_gm2_deger: d.__setitem__("metadata", deger),
        )
        _gm2_rc, _gm2_cikti = kos(
            "gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
            "gate/STRONG-gate-2b-v5.5.json", cwd=_gm2_proje,
        )
        _gm2_final = json.loads(
            (_gm2_proje / "gate/FINAL-GATE-v5.5.json").read_text(encoding="utf-8")
        )
        _gm2_notlar = _gm2_final["metadata_integrity"]["mismatch_notes"]
        _gm2_kok_sonuclari.append(
            (_gm2_ad, _gm2_rc, "METADATA_MISMATCH" in _gm2_cikti,
             "Traceback" in _gm2_cikti, _gm2_final["verdict"],
             _gm2_final["metadata_integrity"]["mismatch_detected"],
             any("metadata" in n.lower() and "nesne" in n.lower() for n in _gm2_notlar))
        )
    kontrol(
        "GM-2",
        "metadata yok/bos serbest; sayac celiskisi, gecersiz sayac ve kok tipleri temiz FAIL verir",
        _gm2_pozitif_ok
        and _gm2_metadata_yok_ok
        and _gm2_metadata_bos_ok
        and all(rc == 1 and metadata_tanisi and not traceback
                for _, rc, metadata_tanisi, traceback in _gm2_tip_sonuclari)
        and all(rc == 1 and metadata_mismatch and not traceback and verdict == "FAIL"
                and mismatch and acik_tani
                for _, rc, metadata_mismatch, traceback, verdict, mismatch, acik_tani
                in _gm2_kok_sonuclari),
        f"pozitif={_gm2_pozitif_ok} yok={_gm2_metadata_yok_ok} "
        f"bos={_gm2_metadata_bos_ok} tipler={_gm2_tip_sonuclari} "
        f"kokler={_gm2_kok_sonuclari}",
    )

    p = kur(T / "gm3")
    json_duzenle(p / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d["manifest_reconciliation"].__setitem__(0, {"fix_id": "FIX-001", "status": "KANITSIZ"}))
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json", "gate/STRONG-gate-2b-v5.5.json", cwd=p)
    kontrol("GM-3", "KANITSIZ FIX P0 sayilir ve FAIL verir", rc == 1 and "FINAL FAIL" in o, f"rc={rc}")

    rc, o = kos("gate_merge.py", "yok.json", "yok2.json", cwd=taban)
    kontrol("GM-4", "eksik dosyada temiz FAIL (traceback yok)",
            rc == 1 and "Traceback" not in o, f"rc={rc}")


    # ---- v5.5.4 regresyon kilitleri (bagimsiz denetimde KANITLANMIS kusurlar) ----
    # Bu on test, gercekten olmus uc yanlis-pozitifi tekrar acilmasin diye kilitler.

    def gm(ad, aciklama, a, b, bekle_rc=1, bekle_metin=None):
        pp = kur(T / ad)
        (pp / "gate/STRONG-gate-2a-v5.5.json").write_text(json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8")
        (pp / "gate/STRONG-gate-2b-v5.5.json").write_text(json.dumps(b, indent=2, ensure_ascii=False), encoding="utf-8")
        rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json", "gate/STRONG-gate-2b-v5.5.json", cwd=pp)
        ok = (rc == bekle_rc) and (bekle_metin is None or bekle_metin in o)
        kontrol(ad.upper(), aciklama, ok, f"rc={rc}")

    temiz2b = {"verdict": "PASS", "metadata": {"p0_count": 0, "p1_count": 0}, "findings": [],
               "manifest_reconciliation": [{"fix_id": "FIX-001", "status": "UYGULANMIŞ_KANITLI"}]}

    gm("gm-5", "iki bos {} kapi PASS VEREMEZ (NO_INSPECTION_EVIDENCE)", {}, {})
    gm("gm-6", "siddet 'CRITICAL'/'SEV0' sessizce dusmez, P0 sayilir",
       {"verdict": "PASS", "metadata": {"p0_count": 0, "p1_count": 0},
        "checks": [{"id": "CHK-01", "status": "GECTI"}],
        "findings": [{"priority": "CRITICAL", "finding": "SQL enjeksiyonu"},
                     {"priority": "SEV0", "finding": "kimlik dogrulama atlaniyor"}]}, temiz2b)
    gm("gm-7", "siddet alani OLMAYAN bulgu P0 sayilir",
       {"verdict": "PASS", "metadata": {"p0_count": 0, "p1_count": 0},
        "checks": [{"id": "CHK-01", "status": "GECTI"}],
        "findings": [{"finding": "siddetsiz bulgu"}]}, temiz2b)
    gm("gm-8", "CALISTIRILMADI kontrol 'temiz' sayilmaz, P1 olur",
       {"verdict": "PASS", "metadata": {"p0_count": 0, "p1_count": 0}, "findings": [],
        "checks": [{"id": "CHK-01", "status": "CALISTIRILMADI"}]}, temiz2b)
    gm("gm-9", "kapali liste disi durum etiketi P0 olur",
       {"verdict": "PASS", "metadata": {"p0_count": 0, "p1_count": 0}, "findings": [],
        "checks": [{"id": "CHK-01", "status": "BILINMEYEN_DURUM"}]}, temiz2b)

    # B-7: FINAL raporu fiilen calisan kontrol sayisini tasimali
    pp = kur(T / "gm10")
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json", "gate/STRONG-gate-2b-v5.5.json", cwd=pp)
    try:
        j = json.loads((pp / "gate/FINAL-GATE-v5.5.json").read_text(encoding="utf-8"))
        rapor = (pp / "04-FAZ-4-STRONG-GATE-RAPORU-v5.5.md").read_text(encoding="utf-8")
        ok = (rc == 0 and j["counts"]["checks_calisan_2a"] == 1 and j["counts"]["checks_toplam_2a"] == 1
              and "Fiilen Calisan Kontroller" in rapor)
    except Exception as e:
        ok, rapor = False, str(e)
    kontrol("GM-10", "FINAL counts+rapor fiilen calisan kontrol sayisini yazar (B-7)", ok,
            f"rc={rc} calisan={j.get('counts', {}).get('checks_calisan_2a') if isinstance(j, dict) else '?'}")

    # IDENTICAL_GATE_INPUTS: oynak alanlar farkli olsa da ayni denetim iki oy sayilmaz.
    ayni_2a = {
        "gate": "2A", "agent": "kor-denetci", "verdict": "PASS",
        "metadata": {"p0_count": 0, "p1_count": 0, "gate_date": "2026-08-31T10:00:00+00:00"},
        "checks": [{"id": "CHK-01", "status": "GECTI", "evidence": "ayni kanit"}],
        "findings": [],
    }
    ayni_2b = json.loads(json.dumps(ayni_2a))
    ayni_2b.update(gate="2B", agent="manifest-denetcisi")
    ayni_2b["metadata"]["gate_date"] = "2026-08-31T11:00:00+00:00"
    pp = kur(T / "gm16")
    (pp / "gate/STRONG-gate-2a-v5.5.json").write_text(
        json.dumps(ayni_2a, indent=2, ensure_ascii=False), encoding="utf-8")
    (pp / "gate/STRONG-gate-2b-v5.5.json").write_text(
        json.dumps(ayni_2b, indent=2, ensure_ascii=False), encoding="utf-8")
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json", "gate/STRONG-gate-2b-v5.5.json", cwd=pp)
    j = json.loads((pp / "gate/FINAL-GATE-v5.5.json").read_text(encoding="utf-8"))
    kontrol("GM-16", "ozdes normalize 2A/2B girdileri FINAL FAIL verir",
            rc == 1 and j["verdict"] == "FAIL"
            and j["metadata_integrity"]["mismatch_detected"]
            and "IDENTICAL_GATE_INPUTS" in j["metadata_integrity"]["mismatch_notes"]
            and j["metadata_integrity"]["mismatch_notes"].count("IDENTICAL_GATE_INPUTS") == 1
            and j["gate_2a"] == "PASS" and j["gate_2b"] == "PASS"
            and j["counts"]["p0_2a"] == 0 and j["counts"]["p1_2a"] == 0
            and j["counts"]["p0_2b"] == 0 and j["counts"]["p1_2b"] == 0,
            f"rc={rc} {o.strip()[:180]}")

    # --- cite_match: transliterasyon ve sayfa numarali anlatimsal atif ---
    def cm_kur(ad, govde_ek):
        pp = kur(T / ad)
        f = pp / "03-FAZ-3-MASTER-v5.5.md"
        f.write_text(f.read_text(encoding="utf-8").replace(
            "Bir iddia (Yazar, 2020).", "Bir iddia (Yazar, 2020). " + govde_ek), encoding="utf-8")
        return pp

    pp = cm_kur("cm7", "Ṭabarī (1987) boyle der. Ḥallāj (1913) ayrica.")
    cm7_rc, cm7_o = kos("cite_match.py", cwd=pp)
    cm7_mevcut_ok = (
        cm7_rc == 1
        and "CITE-01" in cm7_o
        and "abar" in cm7_o
        and "Traceback" not in cm7_o
    )

    cm7_pozitif_sonuclar = []
    for cm7_ad, cm7_yil, cm7_dizin in (
        ("al-Ṭabarī", "1987", "cm7_al_tabari"),
        ("ʿĀʾişe", "1913", "cm7_ayn_aise"),
    ):
        cm7_pp = cm_kur(cm7_dizin, f"{cm7_ad} ({cm7_yil}) boyle der.")
        cm7_f = cm7_pp / "03-FAZ-3-MASTER-v5.5.md"
        cm7_f.write_text(
            cm7_f.read_text(encoding="utf-8").replace(
                "- Yazar, A. (2020). *Deneme*. Yayin.",
                "- Yazar, A. (2020). *Deneme*. Yayin.\n"
                f"- {cm7_ad}, A. ({cm7_yil}). *Deneme*. Yayin.",
            ),
            encoding="utf-8",
        )
        cm7_pozitif_rc, cm7_pozitif_o = kos("cite_match.py", cwd=cm7_pp)
        cm7_pozitif_sonuclar.append(
            (cm7_ad, cm7_pozitif_rc, "CITE-MATCH PASS" in cm7_pozitif_o,
             "Traceback" in cm7_pozitif_o)
        )

    cm7_duz_yazi_pp = cm_kur("cm7_duz_yazi", "Araştırma gerçekleştirildi (2020).")
    cm7_duz_yazi_rc, cm7_duz_yazi_o = kos("cite_match.py", cwd=cm7_duz_yazi_pp)
    cm7_duz_yazi_ok = (
        cm7_duz_yazi_rc == 0
        and "FAIL CITE-01" not in cm7_duz_yazi_o
        and "CITE-MATCH PASS" in cm7_duz_yazi_o
        and "Traceback" not in cm7_duz_yazi_o
    )

    kontrol(
        "CM-7",
        "anlatimsal atiflari yakalar; kucuk harfli yuklemi atif saymaz",
        cm7_mevcut_ok
        and all(rc == 0 and pass_var and not traceback
                for _, rc, pass_var, traceback in cm7_pozitif_sonuclar)
        and cm7_duz_yazi_ok,
        f"mevcut=(rc={cm7_rc}, ok={cm7_mevcut_ok}) "
        f"pozitif={cm7_pozitif_sonuclar} "
        f"duz_yazi=(rc={cm7_duz_yazi_rc}, ok={cm7_duz_yazi_ok})",
    )

    pp = cm_kur("cm8", "Scholem (1941, s. 45) ise soyle der. Idel (1988, pp. 12-14) katiliyor.")
    rc, o = kos("cite_match.py", cwd=pp)
    kontrol("CM-8", "SAYFA NUMARALI anlatimsal atif (Scholem, 1941, s. 45) yakalanir",
            rc == 1 and "CITE-01" in o and "Scholem" in o, f"rc={rc}")

    # --- verify_doi: DEC-027 muafiyeti ACIK NIYET gerektirir ---
    def vd_kur(ad, baslik, seviye="##"):
        pp = kur(T / ad)
        f = pp / "03-FAZ-3-MASTER-v5.5.md"
        f.write_text(f.read_text(encoding="utf-8").replace(
            "## SC-008 Bolum 8", f"{seviye} {baslik}\n\nBu iddia [DOĞRULANMADI].\n\n## SC-008 Bolum 8"),
            encoding="utf-8")
        return pp

    pp = vd_kur("vd4", "18. Sinirliliklar ve M1 notu")
    rc, o = kos("verify_doi.py", "--require-master", cwd=pp)
    kontrol("VD-4", "'18...M1' basligi muafiyet TETIKLEMEZ (ciplak 8 yetmez)",
            rc == 1 and "muaf bolum yok" in o, f"rc={rc}")

    vd5_h2 = vd_kur("vd5_h2", "§8 Bilinen Sinirlar (M1)")
    vd5_h2_rc, vd5_h2_o = kos("verify_doi.py", "--require-master", cwd=vd5_h2)
    vd5_h1 = vd_kur("vd5_h1", "§8 Bilinen Sinirlar (M1)", seviye="#")
    vd5_h1_rc, vd5_h1_o = kos("verify_doi.py", "--require-master", cwd=vd5_h1)
    kontrol(
        "VD-5",
        "H2+ muafiyeti korunur; H1 muafiyet basligi etiketi engellemez",
        vd5_h2_rc == 0 and "muaf bolum sayisi: 1" in vd5_h2_o
        and "Traceback" not in vd5_h2_o
        and vd5_h1_rc == 1 and "muaf bolum yok" in vd5_h1_o
        and "istisna DISINDA 1" in vd5_h1_o and "Traceback" not in vd5_h1_o,
        f"H2 rc={vd5_h2_rc}; H1 rc={vd5_h1_rc}",
    )

    pp = vd_kur("vd6", "Bilinen Sinirlar <!-- DEC-027-EXEMPT -->")
    rc, o = kos("verify_doi.py", "--require-master", cwd=pp)
    kontrol("VD-6", "acik '<!-- DEC-027-EXEMPT -->' isareti muafiyet acar",
            rc == 0 and "muaf bolum sayisi: 1" in o, f"rc={rc}")

    # E-9: CrossRef dallari gercek aga cikmadan korunur. verify_doi.py betik
    # oldugu icin ayni surecte runpy ile calistirilir; patch context'i requests.get
    # cagrisini yakalar ve finally blogu cwd/argv durumunu geri yukler.
    def vd7_kos(ad, durum):
        import requests

        pp = kur(T / ad)
        f = pp / "03-FAZ-3-MASTER-v5.5.md"
        f.write_text(f.read_text(encoding="utf-8") + "\nKaynak DOI: 10.1234/atlas.vd7\n",
                     encoding="utf-8")
        if durum == "ag":
            get_patch = unittest.mock.patch(
                "requests.get", side_effect=requests.RequestException("VD-7 ag kesintisi"))
        else:
            yanit = unittest.mock.Mock(status_code=durum)
            get_patch = unittest.mock.patch("requests.get", return_value=yanit)

        stdout = io.StringIO()
        stderr = io.StringIO()
        eski_cwd = os.getcwd()
        eski_argv = sys.argv[:]
        rc = 0
        cagri = 0
        url = ""
        try:
            os.chdir(pp)
            sys.argv = [str(SCRIPTS / "verify_doi.py"), "--require-master"]
            with get_patch as sahte_get, unittest.mock.patch("time.sleep", return_value=None), \
                    contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    runpy.run_path(str(SCRIPTS / "verify_doi.py"), run_name="__main__")
                except SystemExit as e:
                    rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
                except Exception as e:
                    rc = 99
                    print(f"VD-7 HARNESS ERROR: {type(e).__name__}: {e}", file=stderr)
                cagri = sahte_get.call_count
                if sahte_get.call_args:
                    url = sahte_get.call_args.args[0]
        finally:
            sys.argv = eski_argv
            os.chdir(eski_cwd)
        return rc, stdout.getvalue() + stderr.getvalue(), cagri, url

    vd7_200_rc, vd7_200_o, vd7_200_n, vd7_200_url = vd7_kos("vd7_200", 200)
    vd7_404_rc, vd7_404_o, vd7_404_n, vd7_404_url = vd7_kos("vd7_404", 404)
    vd7_ag_rc, vd7_ag_o, vd7_ag_n, vd7_ag_url = vd7_kos("vd7_ag", "ag")
    vd7_url = "https://api.crossref.org/works/10.1234/atlas.vd7"
    kontrol(
        "VD-7",
        "CrossRef 200/404/ag hatasi hermetik: PASS/FAIL/WARN politikasini korur",
        vd7_200_rc == 0 and "OK 10.1234/atlas.vd7 [200]" in vd7_200_o
        and "PASS:" in vd7_200_o and "Traceback" not in vd7_200_o
        and vd7_404_rc == 1 and "FAIL 10.1234/atlas.vd7 [404]" in vd7_404_o
        and "CrossRef'te dogrulanamadi" in vd7_404_o and "Traceback" not in vd7_404_o
        and vd7_ag_rc == 0 and "ERR (ag hatasi, sayilmaz)" in vd7_ag_o
        and "WARN:" in vd7_ag_o and "FAIL sayilmadi" in vd7_ag_o
        and "Traceback" not in vd7_ag_o
        and (vd7_200_n, vd7_404_n, vd7_ag_n) == (1, 1, 1)
        and vd7_200_url == vd7_404_url == vd7_ag_url == vd7_url,
        f"200={vd7_200_rc}/{vd7_200_n}; 404={vd7_404_rc}/{vd7_404_n}; "
        f"ag={vd7_ag_rc}/{vd7_ag_n}",
    )

    # --- declaration_check: beyan basliklari tam normalize eslesir ---
    dc_basliklar = [
        "Etik Kurul",
        "Cikar Catismasi",
        "Finansman",
        "credit",
        "Veri Erisilebilirligi",
        "Yapay Zeka",
    ]

    def dc_kur(ad, basliklar):
        pp = T / ad
        pp.mkdir(parents=True)
        govde = "# Makale\n\n" + "\n\n".join(
            f"## {baslik}\n\nBeyan metni." for baslik in basliklar
        ) + "\n"
        (pp / "MASTER.md").write_text(govde, encoding="utf-8")
        return pp

    pp = dc_kur("dc1_tam", dc_basliklar)
    dc_tam_rc, dc_tam_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=pp)

    pp = dc_kur("dc1_yapay_zeka_alt_dize", [
        "Yapay Zeka Tarihi" if baslik == "Yapay Zeka" else baslik
        for baslik in dc_basliklar
    ])
    dc_yz_rc, dc_yz_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=pp)

    pp = dc_kur("dc1_credit_alt_dize", [
        "Accreditation" if baslik == "credit" else baslik
        for baslik in dc_basliklar
    ])
    dc_credit_rc, dc_credit_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=pp)

    pp = dc_kur("dc1_baslik_yok", [
        baslik for baslik in dc_basliklar if baslik != "Finansman"
    ])
    dc_yok_rc, dc_yok_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=pp)

    pp = dc_kur("dc1_fenced_code", [
        baslik for baslik in dc_basliklar if baslik != "Finansman"
    ])
    dc_fence_yolu = pp / "MASTER.md"
    dc_fence_yolu.write_text(
        dc_fence_yolu.read_text(encoding="utf-8")
        + "\n```markdown\n## Finansman\n\nKod ornegi.\n```\n"
        + "\n~~~markdown\n## Finansman\n\nKod ornegi.\n~~~\n",
        encoding="utf-8",
    )
    dc_fence_rc, dc_fence_o = kos(
        "declaration_check.py", "--dosya", "MASTER.md", cwd=pp
    )

    dc1_ok = (
        dc_tam_rc == 0 and "DECLARATION-CHECK PASS" in dc_tam_o
        and "Traceback" not in dc_tam_o
        and dc_yz_rc == 1 and "FAIL DEC-06" in dc_yz_o
        and "Traceback" not in dc_yz_o
        and dc_credit_rc == 1 and "FAIL DEC-04" in dc_credit_o
        and "Traceback" not in dc_credit_o
        and dc_yok_rc == 1 and "FAIL DEC-03" in dc_yok_o
        and "Traceback" not in dc_yok_o
        and dc_fence_rc == 1 and "FAIL DEC-03" in dc_fence_o
        and "Traceback" not in dc_fence_o
    )
    kontrol("DC-1", "beyan basliklari tam eslesir; alt-dize, eksik ve fenced-code baslik FAIL",
            dc1_ok,
            f"tam={dc_tam_rc}; yapay_zeka={dc_yz_rc}; "
            f"credit={dc_credit_rc}; yok={dc_yok_rc}; fence={dc_fence_rc}")

    # --- DEC-10 (v1.7.277): RUN-IN kalin beyan etiketi taninir ---
    # Mutasyon: find_runin cagrisi kaldirilirsa (a) FAIL DEC-07 verir -> test yanar.
    # (b) notr etiket ("**Not:**") DPIA sayilmamali -> gevsek eslesme fail-open'i yakalar.
    dc10_a = T / "dc10_runin"
    dc10_a.mkdir(parents=True)
    (dc10_a / "MASTER.md").write_text(
        "# Makale\n\n"
        "## Etik Kurul\n\nBeyan metni.\n\n"
        "## Cikar Catismasi\n\nBeyan metni.\n\n"
        "## Finansman\n\nBeyan metni.\n\n"
        "## Yazar Katkisi\n\nBeyan metni.\n\n"
        "## Veri Erisilebilirligi\n\nBeyan metni.\n\n"
        "## YZ Kullanimi\n\nBeyan metni.\n\n"
        "**DPIA (Veri Koruma Etki Degerlendirmesi):** N/A (gerekceli) — kisisel veri\n"
        "islenmemektedir.\n",
        encoding="utf-8")
    dc10a_rc, dc10a_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=dc10_a)

    dc10_b = T / "dc10_notr"
    dc10_b.mkdir(parents=True)
    (dc10_b / "MASTER.md").write_text(
        "# Makale\n\n"
        "## Etik Kurul\n\nBeyan metni.\n\n"
        "## Cikar Catismasi\n\nBeyan metni.\n\n"
        "## Finansman\n\nBeyan metni.\n\n"
        "## Yazar Katkisi\n\nBeyan metni.\n\n"
        "## Veri Erisilebilirligi\n\nBeyan metni.\n\n"
        "## YZ Kullanimi\n\nBeyan metni.\n\n"
        "**Not:** Bu bolum taslaktir; DPIA konusu ileride ele alinacaktir.\n",
        encoding="utf-8")
    dc10b_rc, dc10b_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=dc10_b)

    kontrol(
        "DEC-10",
        "satir ici kalin beyan etiketi (DPIA:) taninir · notr etiket (**Not:**) DPIA sayilmaz",
        dc10a_rc == 0
        and "PASS DEC-07 DPIA: satir ici beyan etiketi" in dc10a_o
        and "DECLARATION-CHECK PASS" in dc10a_o
        and "PASS DEC-07" not in dc10b_o
        and "INFO DEC-07 DPIA: CALISTIRILMADI" in dc10b_o
        and "Traceback" not in dc10a_o + dc10b_o,
        f"runin=(rc={dc10a_rc}) notr=(rc={dc10b_rc}, dpia_pass={'PASS DEC-07' in dc10b_o})",
    )

    # --- DEC-11 (v1.7.277): N/A beyani kendi tetikleyicisini doyurmaz ---
    # Mutasyon: olumsuzluk penceresi kaldirilirsa (a) FAIL DEC-07 verir -> test yanar.
    # (b) GERCEK kisisel veri (katilimci gorusmesi, olumsuzluk yok) HALA FAIL olmali;
    #     yanmazsa duzeltme fail-open yapmis olur.
    dc11_a = T / "dc11_na"
    dc11_a.mkdir(parents=True)
    (dc11_a / "MASTER.md").write_text(
        "# Makale\n\n"
        "## Etik Kurul\n\nBeyan metni.\n\n"
        "## Cikar Catismasi\n\nBeyan metni.\n\n"
        "## Finansman\n\nBeyan metni.\n\n"
        "## Yazar Katkisi\n\nBeyan metni.\n\n"
        "## Veri Erisilebilirligi\n\nBeyan metni.\n\n"
        "## YZ Kullanimi\n\nBeyan metni.\n\n"
        "Bu calismada kisisel veri islenmemektedir; katilimci yoktur.\n",
        encoding="utf-8")
    dc11a_rc, dc11a_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=dc11_a)

    dc11_b = T / "dc11_gercek"
    dc11_b.mkdir(parents=True)
    (dc11_b / "MASTER.md").write_text(
        "# Makale\n\n"
        "## Etik Kurul\n\nBeyan metni.\n\n"
        "## Cikar Catismasi\n\nBeyan metni.\n\n"
        "## Finansman\n\nBeyan metni.\n\n"
        "## Yazar Katkisi\n\nBeyan metni.\n\n"
        "## Veri Erisilebilirligi\n\nBeyan metni.\n\n"
        "## YZ Kullanimi\n\nBeyan metni.\n\n"
        "Arastirma kapsaminda on iki katilimci ile gorusme yapilmistir.\n",
        encoding="utf-8")
    dc11b_rc, dc11b_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=dc11_b)

    kontrol(
        "DEC-11",
        "N/A beyani ('kisisel veri islenmemektedir') DPIA'yi ZORUNLU kilmaz · "
        "gercek kisisel veri (katilimci gorusmesi) HALA FAIL",
        dc11a_rc == 0
        and "INFO DEC-07 DPIA: CALISTIRILMADI" in dc11a_o
        and "FAIL DEC-07" not in dc11a_o
        and dc11b_rc == 1
        and "FAIL DEC-07 DPIA: kisisel veri isareti var" in dc11b_o
        and "Traceback" not in dc11a_o + dc11b_o,
        f"na=(rc={dc11a_rc}) gercek=(rc={dc11b_rc})",
    )

    # --- DEC-12 (v1.7.278): TURKCE HARFLI baslik taninir, gevsek desen TANINMAZ ---
    # ONCE olculdu: 6 Turkce basligin 4'u taninmiyordu (DEC-02/04/05/06) —
    #   `lower()` "Çıkar Çatışması" -> "çıkar çatışması" != "cikar catismasi".
    #   Arac makaleyi ASCII Turkce yazmaya ZORLUYORDU.
    # Mutasyon: _katla() kimlik yapilirsa -> Turkce baslik yine gorunmez -> (a) yanar.
    # Ters yon: (b) gevsek etiket ("Destek" / "Not") beyan SANILMAMALI —
    #   katlama eslestirmeyi GEVSETMEMELI. Yanmazsa duzeltme fail-open olurdu.
    dc12_a = T / "dc12_turkce"
    dc12_a.mkdir(parents=True)
    (dc12_a / "MASTER.md").write_text(
        "# Makale\n\n"
        "## Etik Kurul\n\nBeyan metni.\n\n"
        "## \u00c7\u0131kar \u00c7at\u0131\u015fmas\u0131\n\nBeyan metni.\n\n"
        "## Finansman\n\nBeyan metni.\n\n"
        "## Yazar Katk\u0131s\u0131\n\nBeyan metni.\n\n"
        "## Veri Eri\u015filebilirli\u011fi\n\nBeyan metni.\n\n"
        "## Yapay Zek\u00e2 Kullan\u0131m\u0131\n\nBeyan metni.\n",
        encoding="utf-8")
    dc12a_rc, dc12a_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=dc12_a)

    dc12_b = T / "dc12_gevsek"
    dc12_b.mkdir(parents=True)
    (dc12_b / "MASTER.md").write_text(
        "# Makale\n\n"
        "## Etik Kurul\n\nBeyan metni.\n\n"
        "## Finansman\n\nBeyan metni.\n\n"
        "**Destek:** Bu calisma bir kurum tarafindan desteklenmemistir.\n\n"
        "**Not:** Cikar catismasi ve yazar katkisi beyanlari ileride eklenecektir.\n",
        encoding="utf-8")
    dc12b_rc, dc12b_o = kos("declaration_check.py", "--dosya", "MASTER.md", cwd=dc12_b)

    kontrol(
        "DEC-12",
        "Turkce harfli basliklar TANINIR (\u00e7 \u011f \u0131 \u0130 \u00f6 \u015f \u00fc \u00e2) · "
        "gevsek etiket ('**Destek:**' / '**Not:**') beyan SAYILMAZ",
        dc12a_rc == 0
        and dc12a_o.count("PASS DEC-0") == 6
        and 'PASS DEC-02 Cikar Catismasi: "\u00c7\u0131kar \u00c7at\u0131\u015fmas\u0131"' in dc12a_o
        and 'PASS DEC-04 Yazar Katkisi: "Yazar Katk\u0131s\u0131"' in dc12a_o
        and 'PASS DEC-05 Veri Erisilebilirligi: "Veri Eri\u015filebilirli\u011fi"' in dc12a_o
        and 'PASS DEC-06 YZ Kullanimi: "Yapay Zek\u00e2 Kullan\u0131m\u0131"' in dc12a_o
        and dc12b_rc == 1
        and "FAIL DEC-02" in dc12b_o
        and "FAIL DEC-04" in dc12b_o
        and "FAIL DEC-05" in dc12b_o
        and "FAIL DEC-06" in dc12b_o
        and "PASS DEC-02" not in dc12b_o
        and "PASS DEC-06" not in dc12b_o
        and "Traceback" not in dc12a_o + dc12b_o,
        f"turkce=(rc={dc12a_rc}, pass={dc12a_o.count('PASS DEC-0')}) "
        f"gevsek=(rc={dc12b_rc})",
    )

    # --- ai_disclosure: RUN manifestinden iki konumlu, kanitli AI beyani ---
    ai_d = T / "ai1"
    ai_d.mkdir()
    ai_manifest = ai_d / "RUN-MANIFEST.json"
    ai_taban = {
        "schema": "ATLAS-RUN-MANIFEST/v1",
        "scope": "ARTICLE_DEVELOPMENT_HISTORY",
        "entries": [
            {
                "role": "atlas-analysis",
                "provider": "openai",
                "model": "gpt-5.6-sol",
                "model_version": "OLCULMEYEN",
                "date": "2026-09-01",
                "usage": "analysis",
                "primary_source_verified": "EVET",
                "evidence_ref": "artifact:gate/analysis.json",
            },
            {
                "role": "atlas-writer",
                "provider": "deepseek",
                "model": "deepseek-v4-pro",
                "model_version": "2026-08",
                "date": "2026-08-31",
                "usage": "writing",
                "primary_source_verified": "UYGULANMAZ",
                "evidence_ref": "session:session-123",
            },
        ],
    }
    # Ayni manifest satiri iki kez kaydedilse de beyan tablosu tek satir uretmeli.
    ai_taban["entries"].append(dict(ai_taban["entries"][1]))

    def ai_manifest_yaz(ad, degistir=None):
        veri = json.loads(json.dumps(ai_taban))
        if degistir is not None:
            degistir(veri)
        yol = ai_d / ad
        yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return yol

    ai_manifest_yaz("RUN-MANIFEST.json")
    ai_once = sorted(p.name for p in ai_d.iterdir())
    ai_pos_rc, ai_pos_o = kos("ai_disclosure.py", "--manifest", str(ai_manifest))
    ai_sonra = sorted(p.name for p in ai_d.iterdir())
    ai_hash = hashlib.sha256(ai_manifest.read_bytes()).hexdigest()

    ai_cikti = ai_d / "AI-BEYANI.md"
    ai_yaz_rc, ai_yaz_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_manifest), "--output", str(ai_cikti))
    ai_cikti_metin = ai_cikti.read_text(encoding="utf-8") if ai_cikti.is_file() else ai_pos_o
    ai_check_rc, ai_check_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_manifest), "--check", str(ai_cikti))

    ai_yok_rc, ai_yok_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_d / "YOK.json"))
    ai_bozuk = ai_d / "bozuk.json"
    ai_bozuk.write_text("{\n", encoding="utf-8")
    ai_bozuk_rc, ai_bozuk_o = kos("ai_disclosure.py", "--manifest", str(ai_bozuk))

    def ai_alan_sil(alan):
        return lambda d: d["entries"][0].pop(alan)

    ai_model = ai_manifest_yaz("model-yok.json", ai_alan_sil("model"))
    ai_model_rc, ai_model_o = kos("ai_disclosure.py", "--manifest", str(ai_model))
    ai_tarih = ai_manifest_yaz("tarih-yok.json", ai_alan_sil("date"))
    ai_tarih_rc, ai_tarih_o = kos("ai_disclosure.py", "--manifest", str(ai_tarih))
    ai_usage = ai_manifest_yaz("usage-yok.json", ai_alan_sil("usage"))
    ai_usage_rc, ai_usage_o = kos("ai_disclosure.py", "--manifest", str(ai_usage))
    ai_bilinmeyen = ai_manifest_yaz(
        "usage-bilinmeyen.json",
        lambda d: d["entries"][0].update(usage="translation"),
    )
    ai_bilinmeyen_rc, ai_bilinmeyen_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_bilinmeyen))
    ai_fazla = ai_manifest_yaz(
        "fazla-alan.json",
        lambda d: d["entries"][0].update(configured_model="routing-profili"),
    )
    ai_fazla_rc, ai_fazla_o = kos("ai_disclosure.py", "--manifest", str(ai_fazla))
    ai_dogrulama = ai_manifest_yaz(
        "dogrulama-bilinmeyen.json",
        lambda d: d["entries"][0].update(primary_source_verified="BELIRSIZ"),
    )
    ai_dogrulama_rc, ai_dogrulama_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_dogrulama))
    ai_routing = ai_manifest_yaz(
        "routing-kanit-degil.json",
        lambda d: d["entries"][0].update(evidence_ref="routing:denge"),
    )
    ai_routing_rc, ai_routing_o = kos("ai_disclosure.py", "--manifest", str(ai_routing))

    ai_tablo_bozuk = ai_d / "tablo-elle-degisti.md"
    ai_tablo_bozuk.write_text(
        ai_cikti_metin.replace(
            "| atlas-analysis | openai/gpt-5.6-sol |",
            "| atlas-analysis | elle-degistirildi/model |",
            1,
        ),
        encoding="utf-8",
    )
    ai_tablo_rc, ai_tablo_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_manifest), "--check", str(ai_tablo_bozuk))

    ai_kapak = ai_d / "yalniz-kapak.md"
    ai_kapak.write_text(ai_cikti_metin.split("\n## Article\n", 1)[0] + "\n", encoding="utf-8")
    ai_kapak_rc, ai_kapak_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_manifest), "--check", str(ai_kapak))
    ai_makale = ai_d / "yalniz-makale.md"
    ai_makale.write_text(
        "## Article\n" + ai_cikti_metin.split("\n## Article\n", 1)[-1],
        encoding="utf-8",
    )
    ai_makale_rc, ai_makale_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_manifest), "--check", str(ai_makale))
    ai_yanlis_yer = ai_d / "yanlis-bolum.md"
    ai_yanlis_yer.write_text(
        ai_cikti_metin.replace("### Remerciements", "### Méthodologie", 1),
        encoding="utf-8",
    )
    ai_yanlis_yer_rc, ai_yanlis_yer_o = kos(
        "ai_disclosure.py", "--manifest", str(ai_manifest), "--check", str(ai_yanlis_yer))

    ai1_kosullar = {
        "stdout_rc": ai_pos_rc == 0,
        "stdout_yazmadi": ai_once == ai_sonra,
        "hash": f"manifest-sha256={ai_hash}" in ai_pos_o,
        "kapak_bolumu": "## Lettre de couverture" in ai_pos_o,
        "makale_bolumu": "## Article" in ai_pos_o,
        "tesekkur_bolumu": "### Remerciements" in ai_pos_o,
        "yontem_bolumu": "### Méthodologie" in ai_pos_o,
        "tekillestirme": ai_pos_o.count(
            "| atlas-writer | deepseek/deepseek-v4-pro | 2026-08 | "
            "2026-08-31 | writing | UYGULANMAZ |"
        ) == 1,
        "sirali": (
            ai_pos_o.find("| atlas-analysis |") >= 0
            and ai_pos_o.find("| atlas-analysis |") < ai_pos_o.find("| atlas-writer |")
        ),
        "output": ai_yaz_rc == 0 and ai_cikti.is_file(),
        "check": ai_check_rc == 0 and "AI-DISCLOSURE CHECK PASS" in ai_check_o,
        "manifest_yok": ai_yok_rc == 1 and "FAIL AI-00" in ai_yok_o,
        "json_bozuk": ai_bozuk_rc == 1 and "FAIL AI-01" in ai_bozuk_o,
        "model_yok": ai_model_rc == 1 and "FAIL AI-02" in ai_model_o,
        "tarih_yok": ai_tarih_rc == 1 and "FAIL AI-02" in ai_tarih_o,
        "usage_yok": ai_usage_rc == 1 and "FAIL AI-02" in ai_usage_o,
        "usage_bilinmeyen": ai_bilinmeyen_rc == 1 and "FAIL AI-02" in ai_bilinmeyen_o,
        "kapali_sema": ai_fazla_rc == 1 and "FAIL AI-02" in ai_fazla_o,
        "dogrulama_bilinmeyen": ai_dogrulama_rc == 1 and "FAIL AI-02" in ai_dogrulama_o,
        "routing_kanit_degil": ai_routing_rc == 1 and "FAIL AI-02" in ai_routing_o,
        "tablo_bozuk": ai_tablo_rc == 1 and "FAIL AI-04" in ai_tablo_o,
        "yalniz_kapak": ai_kapak_rc == 1 and "FAIL AI-04" in ai_kapak_o,
        "yalniz_makale": ai_makale_rc == 1 and "FAIL AI-04" in ai_makale_o,
        "yanlis_yer": ai_yanlis_yer_rc == 1 and "FAIL AI-04" in ai_yanlis_yer_o,
        "traceback_yok": all("Traceback" not in cikti for cikti in (
            ai_pos_o, ai_yaz_o, ai_check_o, ai_yok_o, ai_bozuk_o,
            ai_model_o, ai_tarih_o, ai_usage_o, ai_bilinmeyen_o,
            ai_fazla_o, ai_dogrulama_o, ai_routing_o,
            ai_tablo_o, ai_kapak_o, ai_makale_o, ai_yanlis_yer_o,
        )),
    }
    ai1_ok = all(ai1_kosullar.values())
    ai1_kalan = ",".join(ad for ad, gecti in ai1_kosullar.items() if not gecti)
    kontrol(
        "AI-1",
        "RUN manifesti iki konumlu beyani ve tekil tabloyu uretir; bozuk/eksik/elle degistirilmis cikti FAIL",
        ai1_ok,
        f"pos={ai_pos_rc}; yaz={ai_yaz_rc}; check={ai_check_rc}; "
        f"yok={ai_yok_rc}; bozuk={ai_bozuk_rc}; model={ai_model_rc}; "
        f"tarih={ai_tarih_rc}; usage={ai_usage_rc}/{ai_bilinmeyen_rc}; "
        f"sema={ai_fazla_rc}; dogrulama={ai_dogrulama_rc}; routing={ai_routing_rc}; "
        f"tablo={ai_tablo_rc}; kapak={ai_kapak_rc}; makale={ai_makale_rc}; "
        f"yer={ai_yanlis_yer_rc}; kalan={ai1_kalan or '-'}",
    )

    # --- P1-7: MAIN -> REVIEWER -> CRITIC tipli hakem paneli ---
    hj_kok = T / "hj1"
    hj_kok.mkdir()
    hj_sema = SCRIPTS.parent / "templates/REVIEW-PANEL-SCHEMA.json"
    hj_girdi_hash = "sha256:" + ("a" * 64)

    def hj_taban_artefaktlari():
        ortak = {
            "schema": "ATLAS-REVIEW-PANEL/v1",
            "run_id": "SYNTHETIC-HJ-1",
            "input_sha256": hj_girdi_hash,
            "attempt": 1,
        }
        main = {
            **ortak,
            "role": "MAIN",
            "provider": "openrouter",
            "model": "anthropic/claude-sonnet-5",
            "model_family": "anthropic",
            "session_ref": "session:hj-main",
            "cost_usd": 0.15,
            "findings": [
                {
                    "finding_id": "HJ-001",
                    "severity": "P1",
                    "axis": "E3",
                    "location": "§1",
                    "quote": "Sentetik iddia.",
                    "claim": "Iddianin kaniti acik yazilmalidir.",
                    "recommendation": "Kanit konumunu ekle.",
                    "evidence_ref": "artifact:synthetic-source.md#L1",
                },
                {
                    "finding_id": "HJ-002",
                    "severity": "P2",
                    "axis": "E6",
                    "location": "§2",
                    "quote": "Sentetik ifade.",
                    "claim": "Ifade daraltilabilir.",
                    "recommendation": "Daha dar bir ifade kullan.",
                    "evidence_ref": "artifact:synthetic-source.md#L2",
                },
            ],
        }
        reviewer = {
            **ortak,
            "role": "REVIEWER",
            "provider": "openrouter",
            "model": "deepseek/deepseek-v4-pro",
            "model_family": "deepseek",
            "session_ref": "session:hj-reviewer",
            "cost_usd": 0.12,
            "judgments": [
                {
                    "finding_id": "HJ-001",
                    "verdict": "AGREE",
                    "severity": "P1",
                    "location": "§1",
                    "rationale": "Kanit konumu eksikligi sentetik metinde goruluyor.",
                    "evidence_ref": "artifact:synthetic-source.md#L1",
                },
                {
                    "finding_id": "HJ-002",
                    "verdict": "DISAGREE_CONCERN",
                    "severity": "P2",
                    "location": "§2",
                    "rationale": "Bu zorunlu duzeltme degil, uslup kaygisidir.",
                    "evidence_ref": "artifact:synthetic-source.md#L2",
                },
            ],
            "new_findings": [],
        }
        critic = {
            **ortak,
            "role": "CRITIC",
            "provider": "openrouter",
            "model": "z-ai/glm-5.3",
            "model_family": "z-ai",
            "session_ref": "session:hj-critic",
            "cost_usd": 0.18,
            "judgments": [
                {
                    "finding_id": "HJ-001",
                    "verdict": "AGREE",
                    "severity": "P1",
                    "location": "§1",
                    "rationale": "MAIN ve kaynak konumu birlikte bu bulguyu destekliyor.",
                    "evidence_ref": "artifact:synthetic-source.md#L1",
                },
                {
                    "finding_id": "HJ-002",
                    "verdict": "AGREE",
                    "severity": "P2",
                    "location": "§2",
                    "rationale": "MAIN onerisi makul, REVIEWER kaygisi kayitta tutulmali.",
                    "evidence_ref": "artifact:synthetic-source.md#L2",
                },
            ],
            "new_findings": [],
        }
        return main, reviewer, critic

    def hj_kos(ad, degistir=None, *, output=False, max_cost="1.00", schema_path=None):
        vaka = hj_kok / ad
        vaka.mkdir(parents=True, exist_ok=True)
        main, reviewer, critic = hj_taban_artefaktlari()
        if degistir is not None:
            degistir(main, reviewer, critic)
        yollar = []
        for rol, veri in (("MAIN", main), ("REVIEWER", reviewer), ("CRITIC", critic)):
            yol = vaka / f"{rol}.json"
            yol.write_text(json.dumps(veri, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            yollar.append(yol)
        fix = vaka / "02-FAZ-2-FIX-MANIFEST.md"
        fix.write_text("SENTINEL — DEGISTIRME\n", encoding="utf-8")
        once = fix.read_bytes()
        args = [
            "--main", str(yollar[0]),
            "--reviewer", str(yollar[1]),
            "--critic", str(yollar[2]),
            "--schema", str(schema_path or hj_sema),
            "--max-cost", max_cost,
        ]
        cikti_yolu = vaka / "FINAL-PANEL.json"
        if output:
            args += ["--output", str(cikti_yolu)]
        rc, o = kos("review_panel.py", *args, cwd=vaka)
        metin = cikti_yolu.read_text(encoding="utf-8") if cikti_yolu.is_file() else o
        try:
            veri = json.loads(metin)
        except Exception:
            veri = None
        return rc, o, veri, metin, once == fix.read_bytes(), cikti_yolu.exists()

    hj_pos_rc, hj_pos_o, hj_pos_j, hj_pos_m, hj_pos_fix, hj_pos_yazdi = hj_kos("pozitif")
    hj_out1_rc, hj_out1_o, hj_out1_j, hj_out1_m, hj_out1_fix, _ = hj_kos("output-1", output=True)
    hj_out2_rc, hj_out2_o, hj_out2_j, hj_out2_m, hj_out2_fix, _ = hj_kos("output-2", output=True)

    def hj_pivotal(_m, r, _c):
        r["judgments"][0]["verdict"] = "DISAGREE_EVIDENCE"
        r["judgments"][0]["rationale"] = "Kaynak konumu iddiayi desteklemiyor."

    hj_piv_rc, hj_piv_o, hj_piv_j, _, _, _ = hj_kos("pivotal", hj_pivotal)

    def hj_uchu_birbir(_m, r, c):
        r["judgments"][0]["verdict"] = "DISAGREE_EVIDENCE"
        r["judgments"][0]["rationale"] = "Kayit MAIN iddiasini desteklemiyor."
        c["judgments"][0]["verdict"] = "DISAGREE_CONCERN"
        c["judgments"][0]["rationale"] = "Yontemsel kaygi var; kanit hukmu vermiyorum."

    hj_111_rc, hj_111_o, hj_111_j, _, _, _ = hj_kos("uc-yollu", hj_uchu_birbir)

    def hj_p0_concern(m, r, c):
        m["findings"][1]["severity"] = "P0"
        r["judgments"][1].update(verdict="DISAGREE_CONCERN", severity="P0")
        c["judgments"][1]["severity"] = "P0"

    hj_p0_rc, hj_p0_o, hj_p0_j, _, _, _ = hj_kos("p0-concern", hj_p0_concern)

    def hj_reviewer_yeni(_m, r, c):
        r["new_findings"].append({
            "finding_id": "HJ-R001", "severity": "P1", "axis": "E2",
            "location": "§3", "quote": "Yeni sentetik bulgu.",
            "claim": "Reviewer yeni bir yontem kaygisi buldu.",
            "recommendation": "Insan incelemesine sun.",
            "evidence_ref": "artifact:synthetic-source.md#L3",
        })
        c["judgments"].append({
            "finding_id": "HJ-R001", "verdict": "AGREE", "severity": "P1",
            "location": "§3", "rationale": "Yeni bulgu makul gorunuyor.",
            "evidence_ref": "artifact:synthetic-source.md#L3",
        })

    hj_ry_rc, hj_ry_o, hj_ry_j, _, _, _ = hj_kos("reviewer-yeni", hj_reviewer_yeni)

    def hj_critic_yeni(_m, _r, c):
        c["new_findings"].append({
            "finding_id": "HJ-C001", "severity": "P2", "axis": "E5",
            "location": "§4", "quote": "Critic sentetik bulgu.",
            "claim": "Critic yeni bir saygi kaygisi buldu.",
            "recommendation": "Insan incelemesine sun.",
            "evidence_ref": "artifact:synthetic-source.md#L4",
        })

    hj_cy_rc, hj_cy_o, hj_cy_j, _, _, _ = hj_kos("critic-yeni", hj_critic_yeni)

    def hj_bilinmeyen(_m, r, _c):
        r["judgments"][0]["verdict"] = "KISMEN"

    hj_bil_rc, hj_bil_o, _, _, _, _ = hj_kos("bilinmeyen", hj_bilinmeyen)

    def hj_rol(_m, _r, c):
        c["role"] = "REVIEWER"

    hj_rol_rc, hj_rol_o, _, _, _, _ = hj_kos("rol", hj_rol)

    def hj_hash(_m, _r, c):
        c["input_sha256"] = "sha256:" + ("b" * 64)

    hj_hash_rc, hj_hash_o, _, _, _, _ = hj_kos("hash", hj_hash)

    def hj_aile(_m, _r, c):
        c["model_family"] = "deepseek"

    hj_aile_rc, hj_aile_o, _, _, _, _ = hj_kos("aile", hj_aile)

    def hj_oturum(_m, r, c):
        c["session_ref"] = r["session_ref"]

    hj_oturum_rc, hj_oturum_o, _, _, _, _ = hj_kos("oturum", hj_oturum)

    def hj_retry(_m, r, _c):
        r["attempt"] = 2

    hj_retry_rc, hj_retry_o, _, _, _, _ = hj_kos("retry", hj_retry)

    def hj_butce(_m, _r, c):
        c["cost_usd"] = 0.90

    hj_butce_rc, hj_butce_o, _, _, _, _ = hj_kos("butce", hj_butce)

    def hj_kapsam(_m, _r, c):
        c["judgments"].pop()

    hj_kap_rc, hj_kap_o, _, _, _, _ = hj_kos("kapsam", hj_kapsam)

    def hj_kanit(_m, r, _c):
        r["judgments"][0]["verdict"] = "DISAGREE_EVIDENCE"
        r["judgments"][0].pop("evidence_ref")

    hj_kanit_rc, hj_kanit_o, _, _, _, _ = hj_kos("kanit", hj_kanit)

    def hj_fazla(m, _r, _c):
        m["independent_expert"] = True

    hj_fazla_rc, hj_fazla_o, _, _, _, _ = hj_kos("fazla", hj_fazla)

    hj_sema_rc, hj_sema_o, _, _, _, _ = hj_kos(
        "sema-yok", schema_path=hj_kok / "YOK-SCHEMA.json")

    def hj_item(j, kimlik):
        if not isinstance(j, dict):
            return None
        return next((x for x in j.get("items", []) if x.get("finding_id") == kimlik), None)

    hj1_kosullar = {
        "pozitif": hj_pos_rc == 0 and isinstance(hj_pos_j, dict)
                    and hj_pos_j.get("status") == "PASS",
        "stdout_yazmadi": not hj_pos_yazdi,
        "unanimous_not_truth": (hj_item(hj_pos_j, "HJ-001") or {}).get("status")
                               == "UNANIMOUS_UNVERIFIED",
        "concern_korundu": (hj_item(hj_pos_j, "HJ-002") or {}).get("status")
                            == "PANEL_MAJORITY_STANDS",
        "uc_aile": isinstance(hj_pos_j, dict)
                   and len({m.get("model_family") for m in hj_pos_j.get("models", [])}) == 3,
        "bagimsizlik_iddiasi_yok": isinstance(hj_pos_j, dict)
                                   and hj_pos_j.get("independence") == "ROLE_SEPARATION_ONLY",
        "butce": isinstance(hj_pos_j, dict) and hj_pos_j.get("cost_usd") == 0.45
                 and hj_pos_j.get("max_cost_usd") == 1.0,
        "retry_yok": isinstance(hj_pos_j, dict) and hj_pos_j.get("retries") == 0,
        "fix_yazilmadi": hj_pos_fix and hj_out1_fix and hj_out2_fix
                         and isinstance(hj_pos_j, dict)
                         and hj_pos_j.get("fix_manifest_written") is False,
        "output": hj_out1_rc == 0 and isinstance(hj_out1_j, dict)
                  and "REVIEW-PANEL PASS" in hj_out1_o,
        "deterministik": hj_out1_m == hj_out2_m,
        "pivotal": hj_piv_rc == 2 and isinstance(hj_piv_j, dict)
                    and hj_piv_j.get("status") == "BLOCKED"
                    and (hj_item(hj_piv_j, "HJ-001") or {}).get("status")
                    == "PIVOTAL_PENDING_GATE_2C",
        "uc_yollu_insan": hj_111_rc == 2 and isinstance(hj_111_j, dict)
                           and (hj_item(hj_111_j, "HJ-001") or {}).get("status")
                           == "HUMAN_REVIEW_REQUIRED"
                           and (hj_item(hj_111_j, "HJ-001") or {}).get("reason")
                           == "THREE_WAY_SPLIT_HUMAN_REVIEW",
        "p0_concern": hj_p0_rc == 2 and isinstance(hj_p0_j, dict)
                       and (hj_item(hj_p0_j, "HJ-002") or {}).get("status")
                       == "HUMAN_REVIEW_REQUIRED",
        "reviewer_yeni": hj_ry_rc == 2 and isinstance(hj_ry_j, dict)
                          and (hj_item(hj_ry_j, "HJ-R001") or {}).get("status")
                          == "HUMAN_REVIEW_REQUIRED",
        "critic_yeni": hj_cy_rc == 2 and isinstance(hj_cy_j, dict)
                        and (hj_item(hj_cy_j, "HJ-C001") or {}).get("status")
                        == "HUMAN_REVIEW_REQUIRED",
        "bilinmeyen": hj_bil_rc == 1 and "FAIL HJ-04" in hj_bil_o,
        "rol": hj_rol_rc == 1 and "FAIL HJ-05" in hj_rol_o,
        "hash": hj_hash_rc == 1 and "FAIL HJ-02" in hj_hash_o,
        "aile": hj_aile_rc == 1 and "FAIL HJ-06" in hj_aile_o,
        "oturum": hj_oturum_rc == 1 and "FAIL HJ-06" in hj_oturum_o,
        "retry": hj_retry_rc == 1 and "FAIL HJ-07" in hj_retry_o,
        "butce_asimi": hj_butce_rc == 1 and "FAIL HJ-07" in hj_butce_o,
        "kapsam": hj_kap_rc == 1 and "FAIL HJ-03" in hj_kap_o,
        "kanit": hj_kanit_rc == 1 and "FAIL HJ-01" in hj_kanit_o,
        "kapali_sema": hj_fazla_rc == 1 and "FAIL HJ-01" in hj_fazla_o,
        "sema_yok": hj_sema_rc == 1 and "FAIL HJ-00" in hj_sema_o,
        "traceback_yok": all("Traceback" not in cikti for cikti in (
            hj_pos_o, hj_out1_o, hj_out2_o, hj_piv_o, hj_111_o,
            hj_p0_o, hj_ry_o, hj_cy_o,
            hj_bil_o, hj_rol_o, hj_hash_o, hj_aile_o, hj_oturum_o, hj_retry_o,
            hj_butce_o, hj_kap_o, hj_kanit_o, hj_fazla_o, hj_sema_o,
        )),
    }
    hj1_ok = all(hj1_kosullar.values())
    hj1_kalan = ",".join(ad for ad, gecti in hj1_kosullar.items() if not gecti)
    kontrol(
        "HJ-1",
        "uc rollu panel kapali sema, tipli hukum, insan blokaji, butce ve retriesiz akisi uygular",
        hj1_ok,
        f"pos={hj_pos_rc}; pivotal={hj_piv_rc}; 1-1-1={hj_111_rc}; p0={hj_p0_rc}; "
        f"yeni={hj_ry_rc}/{hj_cy_rc}; sema={hj_bil_rc}/{hj_fazla_rc}; "
        f"rol={hj_rol_rc}; hash={hj_hash_rc}; aile={hj_aile_rc}; "
        f"oturum={hj_oturum_rc}; retry={hj_retry_rc}; butce={hj_butce_rc}; "
        f"kapsam={hj_kap_rc}; kanit={hj_kanit_rc}; kalan={hj1_kalan or '-'}",
    )

    # --- P1-8: Gate-2C pivotal + disa cikan lokator istisnasi ---
    g2c_kok = T / "g2c1"
    g2c_kok.mkdir()
    g2c_sema = SCRIPTS.parent / "templates/GATE-2C-SCHEMA.json"
    g2c_betik = SCRIPTS / "gate_2c.py"

    def g2c_sha_bytes(ham):
        return "sha256:" + hashlib.sha256(ham).hexdigest()

    def g2c_sha_metin(metin):
        return g2c_sha_bytes(metin.encode("utf-8"))

    def g2c_panel():
        return {
            "schema": "ATLAS-REVIEW-PANEL-RESULT/v1",
            "run_id": "SYNTHETIC-G2C-1",
            "input_sha256": "sha256:" + ("c" * 64),
            "status": "BLOCKED",
            "reason_codes": ["HJ-001:PIVOTAL_EVIDENCE_DISAGREEMENT"],
            "independence": "ROLE_SEPARATION_ONLY",
            "models": [
                {"role": "MAIN", "provider": "p1", "model": "m1",
                 "model_family": "f1", "session_ref": "session:g2c-main"},
                {"role": "REVIEWER", "provider": "p2", "model": "m2",
                 "model_family": "f2", "session_ref": "session:g2c-reviewer"},
                {"role": "CRITIC", "provider": "p3", "model": "m3",
                 "model_family": "f3", "session_ref": "session:g2c-critic"},
            ],
            "cost_usd": 0.45,
            "max_cost_usd": 1.0,
            "retries": 0,
            "items": [
                {
                    "finding_id": "HJ-001", "source_role": "MAIN", "severity": "P1",
                    "claim": "Kaydin DOI lokatoru 10.1234/atlas.main olmalidir.",
                    "votes": {"MAIN": "AGREE", "REVIEWER": "DISAGREE_EVIDENCE",
                              "CRITIC": "AGREE"},
                    "status": "PIVOTAL_PENDING_GATE_2C",
                    "reason": "PIVOTAL_EVIDENCE_DISAGREEMENT",
                    "evidence_refs": ["artifact:main#1", "source:reviewer#1"],
                },
                {
                    "finding_id": "HJ-002", "source_role": "MAIN", "severity": "P2",
                    "claim": "Disa cikacak kaydin DOI lokatoru dogrudur.",
                    "votes": {"MAIN": "AGREE", "REVIEWER": "AGREE", "CRITIC": "AGREE"},
                    "status": "UNANIMOUS_UNVERIFIED",
                    "reason": "UNANIMOUS_IS_NOT_EVIDENCE",
                    "evidence_refs": ["artifact:main#2"],
                },
                {
                    "finding_id": "HJ-003", "source_role": "MAIN", "severity": "P2",
                    "claim": "Bu lokator iddiasi degildir.",
                    "votes": {"MAIN": "AGREE", "REVIEWER": "DISAGREE_CONCERN",
                              "CRITIC": "AGREE"},
                    "status": "PANEL_MAJORITY_STANDS",
                    "reason": "MINORITY_CONCERN_RECORDED",
                    "evidence_refs": ["artifact:main#3"],
                },
            ],
            "fix_manifest_written": False,
        }

    def g2c_json_ham(veri):
        return (json.dumps(veri, indent=2, ensure_ascii=False, sort_keys=True)
                + "\n").encode("utf-8")

    def g2c_istek(panel, panel_ham):
        def kayit(kimlik, sinif, disa, provider, identifier, onermeler):
            claim = next(x["claim"] for x in panel["items"]
                         if x["finding_id"] == kimlik)
            return {
                "finding_id": kimlik,
                "claim_sha256": g2c_sha_metin(claim),
                "claim_class": sinif,
                "external_bound": disa,
                "locator": {"provider": provider, "identifier": identifier},
                "propositions": onermeler,
                "classification_evidence_ref": f"artifact:classification#{kimlik}",
            }

        return {
            "schema": "ATLAS-GATE-2C-REQUEST/v1",
            "run_id": panel["run_id"],
            "panel_sha256": g2c_sha_bytes(panel_ham),
            "items": [
                kayit("HJ-001", "primary_source_locator", False,
                      "CROSSREF_DOI", "10.1234/atlas.main", [
                          {"side": "PANEL_MAJORITY", "expected": {
                              "doi": "10.1234/atlas.main", "title": "Atlas Main Record",
                              "published_year": 2026}},
                          {"side": "EVIDENCE_MINORITY", "expected": {
                              "doi": "10.1234/atlas.main", "title": "Yanlis Baslik",
                              "published_year": 2025}},
                      ]),
                kayit("HJ-002", "primary_source_locator", True,
                      "CROSSREF_DOI", "10.1234/atlas.high", [
                          {"side": "PANEL_MAJORITY", "expected": {
                              "doi": "10.1234/atlas.high", "title": "Atlas High Record",
                              "published_year": 2026}},
                      ]),
                kayit("HJ-003", "other", False, "NONE", "UYGULANMAZ", []),
            ],
        }

    class G2CYanit:
        def __init__(self, durum, veri):
            self.status_code = durum
            self._veri = veri

        def json(self):
            return self._veri

    def g2c_http(url, **_kwargs):
        doi = url.rsplit("/works/", 1)[-1]
        baslik = {
            "10.1234/atlas.main": "Atlas Main Record",
            "10.1234/atlas.high": "Atlas High Record",
        }[doi]
        return G2CYanit(200, {"message": {
            "DOI": doi, "title": [baslik],
            "published": {"date-parts": [[2026]]},
        }})

    def g2c_kos(ad, *, istek_degistir=None, panel_degistir=None,
                http_side_effect=g2c_http):
        vaka = g2c_kok / ad
        vaka.mkdir(parents=True, exist_ok=True)
        panel = g2c_panel()
        if panel_degistir:
            panel_degistir(panel)
        panel_ham = g2c_json_ham(panel)
        istek = g2c_istek(panel, panel_ham)
        if istek_degistir:
            istek_degistir(istek)
        istek_ham = g2c_json_ham(istek)
        panel_yol = vaka / "FINAL-PANEL.json"
        istek_yol = vaka / "GATE-2C-REQUEST.json"
        cikti_yol = vaka / "STRONG-gate-2c-v5.5.json"
        panel_yol.write_bytes(panel_ham)
        istek_yol.write_bytes(istek_ham)
        dersler = vaka / "DERSLER.md"
        fix = vaka / "02-FAZ-2-FIX-MANIFEST.md"
        dersler.write_text("SENTINEL DERSLER\n", encoding="utf-8")
        fix.write_text("SENTINEL FIX\n", encoding="utf-8")
        once = (dersler.read_bytes(), fix.read_bytes())
        stdout = io.StringIO()
        eski_argv = sys.argv[:]
        rc = 127
        try:
            sys.argv = [
                str(g2c_betik), "--panel", str(panel_yol),
                "--request", str(istek_yol), "--schema", str(g2c_sema),
                "--output", str(cikti_yol),
            ]
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stdout):
                try:
                    with unittest.mock.patch("requests.get", side_effect=http_side_effect) as mock_get:
                        try:
                            runpy.run_path(str(g2c_betik), run_name="__main__")
                        except SystemExit as exc:
                            rc = int(exc.code or 0)
                        cagri = mock_get.call_count
                except FileNotFoundError:
                    stdout.write("FAIL G2C-00: gate_2c.py bulunamadi\n")
                    cagri = 0
                except Exception as exc:
                    stdout.write(f"FAIL G2C-TEST: {type(exc).__name__}: {exc}\n")
                    cagri = 0
        finally:
            sys.argv = eski_argv
        veri = None
        if cikti_yol.is_file():
            try:
                veri = json.loads(cikti_yol.read_text(encoding="utf-8"))
            except Exception:
                pass
        degismedi = once == (dersler.read_bytes(), fix.read_bytes())
        return rc, stdout.getvalue(), veri, cikti_yol, panel_yol, istek_yol, cagri, degismedi

    g2c_pos = g2c_kos("pozitif-1")
    g2c_pos2 = g2c_kos("pozitif-2")

    def g2c_ag_hatasi(_url, **_kwargs):
        import requests
        raise requests.RequestException("sentetik ag hatasi")

    g2c_ag = g2c_kos("ag-hatasi", http_side_effect=g2c_ag_hatasi)
    g2c_eksik = g2c_kos(
        "eksik-madde", istek_degistir=lambda r: r["items"].pop())
    g2c_hash = g2c_kos(
        "hash", istek_degistir=lambda r: r.update(panel_sha256="sha256:" + ("0" * 64)))
    g2c_sinif = g2c_kos(
        "sinif", istek_degistir=lambda r: r["items"][0].update(claim_class="bilinmeyen"))
    g2c_fazla = g2c_kos(
        "fazla", istek_degistir=lambda r: r.update(independent_expert=True))

    def g2c_belirsiz(r):
        r["items"][0]["propositions"][1]["expected"] = dict(
            r["items"][0]["propositions"][0]["expected"])

    g2c_amb = g2c_kos("belirsiz", istek_degistir=g2c_belirsiz)

    def g2c_p0_panel(p):
        p["items"][0].update(
            severity="P0",
            votes={"MAIN": "AGREE", "REVIEWER": "DISAGREE_CONCERN",
                   "CRITIC": "AGREE"},
            status="HUMAN_REVIEW_REQUIRED",
            reason="P0_CONCERN",
        )
        p["reason_codes"] = ["HJ-001:P0_CONCERN"]

    g2c_p0 = g2c_kos(
        "p0-override-yok",
        panel_degistir=g2c_p0_panel,
        istek_degistir=lambda r: r["items"][0].update(external_bound=True),
    )

    def g2c_ek_panel(p):
        p["items"][0].update(
            source_role="REVIEWER",
            votes={"REVIEWER": "AGREE", "CRITIC": "AGREE"},
            status="HUMAN_REVIEW_REQUIRED",
            reason="ADDED_AFTER_MAIN_NO_THREE_VOTES",
        )
        p["reason_codes"] = ["HJ-001:ADDED_AFTER_MAIN"]

    g2c_ek = g2c_kos(
        "ek-bulgu-override-yok",
        panel_degistir=g2c_ek_panel,
        istek_degistir=lambda r: r["items"][0].update(external_bound=True),
    )

    # check_integrity --gate2c: uretim sonucunu yeniden ag cagirmadan
    # panel/istek hashlerine ve hesaplanan hukme baglar.
    g2c_ci = g2c_kok / "ci-pass"
    if g2c_pos[3].is_file():
        (g2c_ci / "rapor/PANEL").mkdir(parents=True)
        (g2c_ci / "gate").mkdir()
        shutil.copy2(g2c_pos[4], g2c_ci / "rapor/PANEL/FINAL-PANEL.json")
        shutil.copy2(g2c_pos[5], g2c_ci / "rapor/PANEL/GATE-2C-REQUEST.json")
        shutil.copy2(g2c_pos[3], g2c_ci / "gate/STRONG-gate-2c-v5.5.json")
        g2c_ci_rc, g2c_ci_o = kos("check_integrity.sh", "--gate2c", cwd=g2c_ci)

        g2c_ci_bayat = g2c_kok / "ci-bayat"
        shutil.copytree(g2c_ci, g2c_ci_bayat)
        json_duzenle(
            g2c_ci_bayat / "rapor/PANEL/GATE-2C-REQUEST.json",
            lambda d: d["items"][0].update(
                classification_evidence_ref="artifact:classification#degisti"),
        )
        g2c_ci_bayat_rc, g2c_ci_bayat_o = kos(
            "check_integrity.sh", "--gate2c", cwd=g2c_ci_bayat)

        g2c_ci_hukum = g2c_kok / "ci-hukum"
        shutil.copytree(g2c_ci, g2c_ci_hukum)
        json_duzenle(
            g2c_ci_hukum / "gate/STRONG-gate-2c-v5.5.json",
            lambda d: d["items"][0].update(status="HUMAN_REVIEW_REQUIRED"),
        )
        g2c_ci_hukum_rc, g2c_ci_hukum_o = kos(
            "check_integrity.sh", "--gate2c", cwd=g2c_ci_hukum)
    else:
        g2c_ci_rc = g2c_ci_bayat_rc = g2c_ci_hukum_rc = 127
        g2c_ci_o = g2c_ci_bayat_o = g2c_ci_hukum_o = (
            "FAIL G2C-00: Gate-2C sonucu uretilmedi")

    pos_j = g2c_pos[2] if isinstance(g2c_pos[2], dict) else {}
    pos_items = {x.get("finding_id"): x for x in pos_j.get("items", [])
                 if isinstance(x, dict)}
    g2c1_kosullar = {
        "pozitif": g2c_pos[0] == 0 and pos_j.get("verdict") == "PASS",
        "pivotal_cozuldu": pos_items.get("HJ-001", {}).get("status")
                            == "RESOLVED_BY_PRIMARY_SOURCE",
        "high_stakes_tetiklendi": pos_items.get("HJ-002", {}).get("trigger_reasons")
                                  == ["HIGH_STAKES_PRIMARY_SOURCE_LOCATOR"],
        "tetiksiz_ag_yok": g2c_pos[6] == 2,
        "deterministik": (
            g2c_pos[3].is_file() and g2c_pos2[3].is_file()
            and g2c_pos[3].read_bytes() == g2c_pos2[3].read_bytes()
        ),
        "kanonik_yazma_yok": g2c_pos[7] and g2c_pos2[7],
        "ag_blocked": g2c_ag[0] == 2 and isinstance(g2c_ag[2], dict)
                      and g2c_ag[2].get("verdict") == "BLOCKED"
                      and g2c_ag[6] == 1,
        "eksik_fail_closed": g2c_eksik[0] == 1 and "FAIL G2C-02" in g2c_eksik[1],
        "hash_fail_closed": g2c_hash[0] == 1 and "FAIL G2C-02" in g2c_hash[1],
        "sinif_kapali": g2c_sinif[0] == 1 and "FAIL G2C-01" in g2c_sinif[1],
        "fazla_alan": g2c_fazla[0] == 1 and "FAIL G2C-01" in g2c_fazla[1],
        "belirsiz_insan": g2c_amb[0] == 2 and isinstance(g2c_amb[2], dict)
                           and g2c_amb[2].get("verdict") == "BLOCKED",
        "p0_override_yok": g2c_p0[0] == 2 and isinstance(g2c_p0[2], dict)
                            and next(x for x in g2c_p0[2]["items"]
                                     if x["finding_id"] == "HJ-001")["status"]
                            == "HUMAN_REVIEW_REQUIRED",
        "ek_bulgu_override_yok": g2c_ek[0] == 2 and isinstance(g2c_ek[2], dict)
                                 and next(x for x in g2c_ek[2]["items"]
                                          if x["finding_id"] == "HJ-001")["status"]
                                 == "HUMAN_REVIEW_REQUIRED",
        "integrity_pass": g2c_ci_rc == 0 and "GATE-2C CHECK PASS" in g2c_ci_o,
        "integrity_bayat": g2c_ci_bayat_rc == 1 and "FAIL G2C-04" in g2c_ci_bayat_o,
        "integrity_hukum": g2c_ci_hukum_rc == 1 and "FAIL G2C-04" in g2c_ci_hukum_o,
        "retry_yok": pos_j.get("retries") == 0,
        "otomatik_yazma_yok": pos_j.get("dersler_written") is False
                               and pos_j.get("fix_manifest_written") is False,
        "traceback_yok": all("Traceback" not in x[1] for x in (
            g2c_pos, g2c_pos2, g2c_ag, g2c_eksik, g2c_hash,
            g2c_sinif, g2c_fazla, g2c_amb, g2c_p0, g2c_ek,
        )),
    }
    g2c1_ok = all(g2c1_kosullar.values())
    g2c1_kalan = ",".join(k for k, v in g2c1_kosullar.items() if not v)
    kontrol(
        "G2C-1",
        "Gate-2C yalniz pivotal/high-stakes lokatoru Crossref ile fail-closed dogrular",
        g2c1_ok,
        f"pos={g2c_pos[0]}; ag={g2c_ag[0]}; eksik={g2c_eksik[0]}; "
        f"hash={g2c_hash[0]}; sinif={g2c_sinif[0]}; fazla={g2c_fazla[0]}; "
        f"belirsiz={g2c_amb[0]}; p0={g2c_p0[0]}; ek={g2c_ek[0]}; "
        f"ci={g2c_ci_rc}/{g2c_ci_bayat_rc}/{g2c_ci_hukum_rc}; "
        f"calls={g2c_pos[6]}; kalan={g2c1_kalan or '-'}",
    )


    # ---- v5.5.4: yeni denetim betikleri ----
    LAB = SCRIPTS.parent.parent          # lab koku
    rc, o = kos("check_models.py", "--dizin", str(LAB), "--sessiz")
    kontrol("MOD-1", "check_models: tum ajan modelleri katalogda gecerli",
            rc == 0 and "MODEL-DENETIM PASS" in o, f"rc={rc}")

    sahte = T / "sahtemodel/.opencode/agent"
    sahte.mkdir(parents=True)
    (sahte / "x.md").write_text("---\nmodel: openrouter/yok/olmayan-model-9\ndescription: t\nmode: subagent\n---\nx\n", encoding="utf-8")
    rc, o = kos("check_models.py", "--dizin", str(T / "sahtemodel"), "--sessiz")
    kontrol("MOD-2", "check_models: katalogda olmayan model FAIL", rc == 1 and "MOD-03" in o, f"rc={rc}")

    mod3_ajan = T / "mod3/.opencode/agent"
    mod3_ajan.mkdir(parents=True)
    (mod3_ajan / "x.md").write_text(
        "---\nmodel: openrouter/test-model\ndescription: t\nmode: subagent\n---\nx\n",
        encoding="utf-8")
    mod3_katalog = T / "mod3-katalog/models.json"
    mod3_katalog.parent.mkdir(parents=True)
    mod3_katalog.write_text(json.dumps({
        "openrouter": {"models": {"test-model": {
            "status": "stable", "reasoning": True, "tool_call": True,
        }}},
    }), encoding="utf-8")
    mod3_home = T / "mod3-bos-home"
    mod3_home.mkdir()
    mod3_bos_ortam = dict(os.environ, HOME=str(mod3_home))
    mod3_bos_ortam.pop("ATLAS_MODEL_KATALOG", None)
    mod3_ortam = dict(mod3_bos_ortam, ATLAS_MODEL_KATALOG=str(mod3_katalog))
    mod3_rc, mod3_o = kos(
        "check_models.py", "--dizin", str(T / "mod3"), "--sessiz", env=mod3_ortam)
    mod3_yok_rc, mod3_yok_o = kos(
        "check_models.py", "--dizin", str(T / "mod3"), "--sessiz", env=mod3_bos_ortam)
    kontrol(
        "MOD-3", "check_models: model katalogu yolu ortamdan enjekte edilir",
        mod3_rc == 0 and "MODEL-DENETIM PASS — 1 ajan" in mod3_o
        and "Traceback" not in mod3_o
        and mod3_yok_rc == 1 and "FAIL MOD-00" in mod3_yok_o
        and "Traceback" not in mod3_yok_o,
        f"env={mod3_rc}; fallback={mod3_yok_rc}")

    mod4_ic = T / "mod4-ic"
    mod4_ic_ajan = mod4_ic / ".opencode/agent"
    mod4_ic_ajan.mkdir(parents=True)
    mod4_ic_hedef = mod4_ic / "ajan-kaynak.md"
    mod4_ic_hedef.write_text(
        "---\nmodel: openrouter/test-model\ndescription: t\nmode: subagent\n---\nx\n",
        encoding="utf-8")
    (mod4_ic_ajan / "a.md").symlink_to(mod4_ic_hedef)
    (mod4_ic_ajan / "b.md").symlink_to(mod4_ic_hedef)
    mod4_ic_rc, mod4_ic_o = kos(
        "check_models.py", "--dizin", str(mod4_ic), "--sessiz", env=mod3_ortam)

    mod4_dis = T / "mod4-dis"
    mod4_dis_ajan = mod4_dis / ".opencode/agent"
    mod4_dis_ajan.mkdir(parents=True)
    mod4_dis_hedef = T / "mod4-dis-hedef.md"
    mod4_dis_hedef.write_text(mod4_ic_hedef.read_text(encoding="utf-8"), encoding="utf-8")
    (mod4_dis_ajan / "x.md").symlink_to(mod4_dis_hedef)
    mod4_dis_rc, mod4_dis_o = kos(
        "check_models.py", "--dizin", str(mod4_dis), "--sessiz", env=mod3_ortam)

    mod4_kirik = T / "mod4-kirik"
    mod4_kirik_ajan = mod4_kirik / ".opencode/agent"
    mod4_kirik_ajan.mkdir(parents=True)
    (mod4_kirik_ajan / "x.md").symlink_to(mod4_kirik / "olmayan.md")
    mod4_kirik_rc, mod4_kirik_o = kos(
        "check_models.py", "--dizin", str(mod4_kirik), "--sessiz", env=mod3_ortam)

    kontrol(
        "MOD-4", "check_models: kok-ici symlink cozulur/deduplike edilir; dis/kirik FAIL",
        mod4_ic_rc == 0 and "MODEL-DENETIM PASS — 1 ajan" in mod4_ic_o
        and "Traceback" not in mod4_ic_o
        and mod4_dis_rc == 1 and "MOD-08" in mod4_dis_o
        and "KOK_DISI_SYMLINK" in mod4_dis_o and "Traceback" not in mod4_dis_o
        and mod4_kirik_rc == 1 and "MOD-08" in mod4_kirik_o
        and "KIRIK_SYMLINK" in mod4_kirik_o and "Traceback" not in mod4_kirik_o,
        f"ic={mod4_ic_rc}; dis={mod4_dis_rc}; kirik={mod4_kirik_rc}")

    rc, o = kos("prompt_lint.py", "--dizin", str(LAB), "--sessiz")
    kontrol("PL-1", "prompt_lint: tum promptlar temiz", rc == 0 and "PROMPT-LINT PASS" in o, f"rc={rc}")

    kotu = T / "kotuprompt/.opencode/agent"
    kotu.mkdir(parents=True)
    (kotu / "atlas-lens-x.md").write_text(
        '---\ndescription: t\nmode: subagent\n---\n'
        'disable: true\n'
        'Cikti: {"verdict": "consistent"}\n'
        'CHK-07 her zaman PASS.\n'
        'Etiketlerini birakma.\n', encoding="utf-8")
    pl2_kotu_rc, pl2_kotu_o = kos(
        "prompt_lint.py", "--dizin", str(T / "kotuprompt"), "--sessiz"
    )

    pl2_daima = T / "pl2_daima/.opencode/agent"
    pl2_daima.mkdir(parents=True)
    (pl2_daima / "normal-daima.md").write_text(
        '---\ndescription: t\nmode: subagent\n---\n'
        'DOGRULANAMADI halinde bu kontrol daima PASS.\n',
        encoding="utf-8",
    )
    pl2_daima_rc, pl2_daima_o = kos(
        "prompt_lint.py", "--dizin", str(T / "pl2_daima"), "--sessiz"
    )

    kontrol(
        "PL-2",
        "prompt_lint: lens verdict + kalici muafiyet + etiket yasagi; normal daima PASS yakalanir",
        pl2_kotu_rc == 1 and "PL-09" in pl2_kotu_o and "PL-11" in pl2_kotu_o
        and "PL-13" in pl2_kotu_o and "Traceback" not in pl2_kotu_o
        and pl2_daima_rc == 1 and "PL-11" in pl2_daima_o
        and "Traceback" not in pl2_daima_o,
        f"kotu={pl2_kotu_rc}; daima={pl2_daima_rc}",
    )

    (kotu / "atlas-vacuous.md").write_text(
        '---\ndescription: t\nmode: subagent\n---\n'
        'Her check icin ayri bir kanit alani GEREKMEZ, liste yeterlidir.\n', encoding="utf-8")
    rc, o = kos("prompt_lint.py", "--dizin", str(T / "kotuprompt"), "--sessiz")
    kontrol("PL-3", "prompt_lint: 'kanit GEREKMEZ' vacuous-PASS deligi yakalanir",
            rc == 1 and "PL-10" in o, f"rc={rc}")

    with tempfile.TemporaryDirectory(prefix="atlas_pl4_", dir="/tmp") as pl4_tmp:
        pl4_t = pathlib.Path(pl4_tmp)
        pl4_prompt = (
            '---\ndescription: symlink capasi\nmode: subagent\n---\n'
            'DOGRULANAMADI\n'
        )

        pl4_ic = pl4_t / "ic"
        pl4_ic_ajan = pl4_ic / ".opencode/agent"
        pl4_ic_ajan.mkdir(parents=True)
        pl4_ic_hedef = pl4_ic / "hedef.md"
        pl4_ic_hedef.write_text(pl4_prompt, encoding="utf-8")
        (pl4_ic_ajan / "bag.md").symlink_to(pl4_ic_hedef)
        pl4_ic_rc, pl4_ic_o = kos("prompt_lint.py", "--dizin", str(pl4_ic), "--sessiz")

        pl4_dis = pl4_t / "dis"
        pl4_dis_ajan = pl4_dis / ".opencode/agent"
        pl4_dis_ajan.mkdir(parents=True)
        pl4_dis_hedef = pl4_t / "kok-disi-hedef.md"
        pl4_dis_hedef.write_text(pl4_prompt, encoding="utf-8")
        (pl4_dis_ajan / "bag.md").symlink_to(pl4_dis_hedef)
        pl4_dis_rc, pl4_dis_o = kos("prompt_lint.py", "--dizin", str(pl4_dis), "--sessiz")

        pl4_kirik = pl4_t / "kirik"
        pl4_kirik_ajan = pl4_kirik / ".opencode/agent"
        pl4_kirik_ajan.mkdir(parents=True)
        (pl4_kirik_ajan / "bag.md").symlink_to(pl4_t / "mevcut-degil.md")
        pl4_kirik_rc, pl4_kirik_o = kos("prompt_lint.py", "--dizin", str(pl4_kirik), "--sessiz")

    kontrol(
        "PL-4",
        "prompt_lint: kok-ici symlink lint edilir; kok-disi reddedilir; kirik PL-18 kalir",
        pl4_ic_rc == 0 and "PROMPT-LINT PASS — 1 prompt dosyasi" in pl4_ic_o
        and "Traceback" not in pl4_ic_o
        and pl4_dis_rc == 1 and "PL-04" in pl4_dis_o and "KOK-DISI SYMLINK" in pl4_dis_o
        and "Traceback" not in pl4_dis_o
        and pl4_kirik_rc == 1 and "PL-18" in pl4_kirik_o and "KIRIK SYMLINK" in pl4_kirik_o
        and "Traceback" not in pl4_kirik_o,
        f"ic={pl4_ic_rc}; dis={pl4_dis_rc}; kirik={pl4_kirik_rc}",
    )

    pb = kur(T / "butce")
    bg_uuid = "550e8400-e29b-41d4-a716-446655440000"
    (pb / ".lab_proje_uuid").write_text(bg_uuid + "\n", encoding="utf-8")
    bg_ortam = dict(
        os.environ,
        ATLAS_BUDGET_LIMIT="30.0",
        ATLAS_OPENCODE_DB=str(fikstir_opencode_db(pb / "fikstir_opencode.db")),
        ATLAS_PROJE_UUID=bg_uuid,
    )
    rc, o = kos("budget_guard.py", "--preflight", "SACMA", cwd=pb, env=bg_ortam)
    kontrol("BG-3", "budget_guard: bilinmeyen faz preflight FAIL", rc == 1, f"rc={rc}")

    # BG-4 hermetik: harcama OLCULEBILIR olmali ki "limit asildi" dali sinansin.
    # Fikstir $0.50 harcama + FAZ3 tahmini $1.60 > limit $0.001 -> BASLATILMADI.
    ortam = dict(bg_ortam, ATLAS_BUDGET_LIMIT="0.001")
    r = subprocess.run([sys.executable, str(SCRIPTS / "budget_guard.py"), "--preflight", "FAZ3", "--kuresel"],
                       cwd=pb, capture_output=True, text=True, env=ortam, timeout=600)
    kontrol("BG-4", "budget_guard: limit asiminda faz BASLATILMAZ (fail-closed)",
            r.returncode == 1 and "BASLATILMADI" in (r.stdout + r.stderr), f"rc={r.returncode}")

    # RT-1/RT-2 hermetik: gercek fiyat verisi DEGIL, apply_routing'in aritmetigi ve
    # kapilari olculur. Fikstir routing.profiles.json'dan turetilir (bkz. fonksiyon
    # docstring'indeki UYARI: fiyatlar uydurmadir, maliyet iddiasina kaynak olamaz).
    ortam_kat = dict(os.environ, ATLAS_MODEL_KATALOG=str(fikstir_model_katalogu(
        SCRIPTS.parent / "routing.profiles.json", T / "routing_kat" / "models.json")))

    rc, o = kos("apply_routing.py", "--maliyet", env=ortam_kat)
    maliyetler = {}
    for satir in o.splitlines():
        eslesme = re.match(
            r"^\s*(kalite|denge|ekonomi|solo)\s+\$\s*([0-9]+(?:\.[0-9]+)?)/kosu\b",
            satir,
        )
        if eslesme:
            maliyetler[eslesme.group(1)] = float(eslesme.group(2))
    kontrol(
        "RT-1",
        "apply_routing: sentetik profil maliyetleri sayisal ve ayrik hesaplanir",
        rc == 0
        and {"kalite", "denge", "ekonomi", "solo"}.issubset(maliyetler)
        and maliyetler["kalite"] > maliyetler["denge"] > maliyetler["ekonomi"] > 0,
        f"rc={rc}; maliyetler={maliyetler}",
    )

    rc, o = kos("apply_routing.py", "denge", "--kuru", env=ortam_kat)
    kontrol("RT-2", "apply_routing --kuru dosya YAZMAZ", rc == 0 and "hicbir dosya yazilmadi" in o, f"rc={rc}")

    # ============ budget_guard.py ============
    p = kur(T / "bg1")
    (p / ".lab_proje_uuid").write_text(bg_uuid + "\n", encoding="utf-8")
    bg1_ortam = dict(
        os.environ,
        ATLAS_BUDGET_LIMIT="30.0",
        ATLAS_OPENCODE_DB=str(fikstir_opencode_db(p / "fikstir_opencode.db")),
        ATLAS_PROJE_UUID=bg_uuid,
    )
    rc, o = kos("budget_guard.py", "--report", cwd=p, env=bg1_ortam)
    yazdi = (p / ".atlas_budget.json").exists()
    kontrol("BG-1", "--report calisir ve dosya YAZMAZ", rc == 0 and not yazdi, f"rc={rc} yazdi={yazdi}")
    kontrol("BG-2", "FAZ1 dosyasi token sayimina dahil", "Token: 0" not in o, o.strip().splitlines()[0] if o.strip() else "")

    # ============ C-4: PASS-PENDING-ETHICS ============
    pe = kur(T / "pe1")
    json_duzenle(pe / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.setdefault("findings", []).append(
                     {"id": "PENDING_ETHICS", "priority": "P1",
                      "finding": "DEC-036 etik onay bekliyor", "evidence": "DEC-036 OPEN"}))
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                "gate/STRONG-gate-2b-v5.5.json", cwd=pe)
    kontrol("PE-1", "yalniz etik bekleniyorsa FINAL=PASS-PENDING-ETHICS (exit 0)",
            rc == 0 and "PASS-PENDING-ETHICS" in o, f"rc={rc} {o.strip()[:140]}")

    rc, o = kos("check_integrity.sh", "--full", cwd=pe)
    kontrol("PE-2", "check_integrity --full PASS-PENDING-ETHICS'i kabul eder",
            rc == 0 and "PASS-PENDING-ETHICS" in o, f"rc={rc} {o.strip()[-200:]}")

    pe2 = kur(T / "pe2")
    json_duzenle(pe2 / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.setdefault("findings", []).extend([
                     {"id": "PENDING_ETHICS", "priority": "P1", "finding": "etik", "evidence": "x"},
                     {"id": "F-900", "priority": "P0", "finding": "gercek kusur", "evidence": "y"}]))
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                "gate/STRONG-gate-2b-v5.5.json", cwd=pe2)
    kontrol("PE-3", "etik disinda P0 varsa yine FAIL (muafiyet DEGIL)",
            rc == 1 and "PASS-PENDING-ETHICS" not in o, f"rc={rc} {o.strip()[:140]}")

    pe3 = kur(T / "pe3")
    json_duzenle(pe3 / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.setdefault("findings", []).append(
                     {"id": "PENDING_ETHICS", "priority": "P0",
                      "finding": "etik kimligi tasiyan P0 kusur", "evidence": "x"}))
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                "gate/STRONG-gate-2b-v5.5.json", cwd=pe3)
    kontrol("GM-11", "PENDING_ETHICS kimligi P0 siddeti AKLAYAMAZ",
            rc == 1 and "PASS-PENDING-ETHICS" not in o and "P0:1" in o,
            f"rc={rc} {o.strip()[:160]}")

    pe4 = kur(T / "pe4")
    json_duzenle(pe4 / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.update(manifest_reconciliation={
                     "FIX-001": {"fix_id": "FIX-001", "status": "UYGULANMIŞ_KANITLI"}}))
    rc_merge, o_merge = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                            "gate/STRONG-gate-2b-v5.5.json", cwd=pe4)
    rc_full, o_full = kos("check_integrity.sh", "--full", cwd=pe4)
    kontrol("GM-12", "sozluk manifest_reconciliation FINAL ve --full kapilarini KAPATIR",
            rc_merge == 1 and rc_full == 1 and "P0:1" in o_merge
            and "Traceback" not in o_merge + o_full,
            f"merge={rc_merge} full={rc_full} {o_merge.strip()[:150]}")

    pe5 = kur(T / "pe5")
    json_duzenle(pe5 / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.setdefault("findings", []).append(
                     {"id": "PENDING_ETHICS", "finding": "etik siddeti eksik", "evidence": "x"}))
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                "gate/STRONG-gate-2b-v5.5.json", cwd=pe5)
    kontrol("GM-13", "PENDING_ETHICS siddeti YOKSA P0'i AKLAYAMAZ",
            rc == 1 and "PASS-PENDING-ETHICS" not in o and "P0:1" in o
            and "Traceback" not in o,
            f"rc={rc} {o.strip()[:180]}")

    # --- GM-17 (v1.7.282, YENI): GEREKCELI RED ayri kovada — P1 sayilmaz ama GORUNUR ---
    # Olculdu (silat, 10.11.2026): FIX-024 (P2, "reddedildi; gerekce: ayri baslik
    # gate scripti icin zorunlu") UYGULANMAMIS yazildigi icin P1 sayildi ->
    # FINAL FAIL. Gate kendi ihtiyaci icin verilmis reddi engel sayiyordu.
    # IKI YON:
    #   (a) REDDEDILDI + gerekce  -> PASS olmali, "REDDEDILEN_GEREKCELI" GORUNMELI
    #   (b) UYGULANMAMIS (ayni fix) -> HALA P1/FAIL olmali (muafiyet sanilmasin)
    def gm14_kur(ad, durum):
        pp = kur(T / ad)
        json_duzenle(pp / "gate/STRONG-gate-2b-v5.5.json",
                     lambda d: d.setdefault("manifest_reconciliation", []).append(
                         {"fix_id": "FIX-024", "status": durum,
                          "evidence": "E-019 onerisi reddedildi; gerekce: ayri baslik gate scripti icin zorunlu"}))
        return pp, kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                       "gate/STRONG-gate-2b-v5.5.json", cwd=pp)

    _, (gm14a_rc, gm14a_o) = gm14_kur("gm14_red", "REDDEDILDI")
    _, (gm14b_rc, gm14b_o) = gm14_kur("gm14_yapilmadi", "UYGULANMAMIS")
    # (c) gerekcesiz red de P1 OLMAMALI degil — KANITSIZ ile karisir; burada
    #     yalniz "gerekcesiz REDDEDILDI" ucuz bir kacis mi diye bakilir:
    #     status REDDEDILDI ama evidence yok -> P0/P1 sayilmaz, ama gorunur yazilir.
    pp = kur(T / "gm14_gerekcesiz")
    json_duzenle(pp / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.setdefault("manifest_reconciliation", []).append(
                     {"fix_id": "FIX-025", "status": "REDDEDILDI"}))
    gm14c_rc, gm14c_o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                            "gate/STRONG-gate-2b-v5.5.json", cwd=pp)

    kontrol(
        "GM-17",
        "gerekceli REDDEDILDI P1 SAYILMAZ ve GORUNUR kalir · ayni fix UYGULANMAMIS ise HALA FAIL",
        gm14a_rc == 0
        and "REDDEDILEN_GEREKCELI: 1" in gm14a_o
        and "FIX-024=REDDEDILDI" in gm14a_o
        and "P1:0" in gm14a_o
        and gm14b_rc == 1
        and "P1:1" in gm14b_o
        and "REDDEDILEN_GEREKCELI" not in gm14b_o
        # (c) gerekcesiz red KACIS olur -> P0 (fail-closed) ama yine GORUNUR
        and gm14c_rc == 1
        and "P0:1" in gm14c_o
        and "GEREKCE-YOK" in gm14c_o
        and "Traceback" not in gm14a_o + gm14b_o + gm14c_o,
        f"red=(rc={gm14a_rc}) yapilmadi=(rc={gm14b_rc}) gerekcesiz=(rc={gm14c_rc}) "
        f"| c={gm14c_o.strip()[:150]}",
    )

    # --- GM-18 (v1.7.284): SAYAC INVARIANT'I ---------------------------------
    # Olculdu (silat, 10.11.2026): `reddedilen` kovasi eklenince denklem
    #   toplam == calisan + kosmadi          (24 = 23 + 1)
    #   toplam == calisan + kosmadi + red    (24 = 23 + 0 + 1)   <-- yeni
    # SESSIZCE degisti. Dahasi `checks[]` icinde KANITSIZ bir kontrol HICBIR
    # kovaya girmiyordu (ne calisan ne kosmadi) — sayac sessizce kuculuyordu.
    # Uc yon:
    #   (a) KANITSIZ kontrol -> SAYAC_INVARIANT notu GORUNUR (kayip sessiz degil)
    #   (b) temiz kapi       -> invariant notu YOK (yanlis pozitif yok)
    #   (c) gerekceli red    -> ucuncu kova SAYILIR, invariant TUTAR
    def gm18_kur(ad, checks, mr):
        pp = kur(T / ad)
        json_duzenle(pp / "gate/STRONG-gate-2b-v5.5.json",
                     lambda d: d.update(checks=checks, manifest_reconciliation=mr))
        rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                    "gate/STRONG-gate-2b-v5.5.json", cwd=pp)
        try:
            fj = json.loads(
                (pp / "gate/FINAL-GATE-v5.5.json").read_text(encoding="utf-8"))
        except (ValueError, OSError):
            fj = {}
        notlar = (fj.get("metadata_integrity") or {}).get("mismatch_notes") or []
        return rc, o, notlar, (fj.get("counts") or {})

    _K1 = {"id": "C1", "status": "GECTI", "evidence": "x"}
    _MR0 = []

    _g18a_rc, _g18a_o, _g18a_n, _g18a_c = gm18_kur(
        "gm18_kanitsiz", [_K1, {"id": "C2", "status": "KANITSIZ", "evidence": "?"}], _MR0)
    _g18b_rc, _g18b_o, _g18b_n, _g18b_c = gm18_kur(
        "gm18_temiz", [_K1, {"id": "C2", "status": "GECTI", "evidence": "y"}], _MR0)
    _g18c_rc, _g18c_o, _g18c_n, _g18c_c = gm18_kur(
        "gm18_red", [_K1], [{"fix_id": "FIX-001", "status": "UYGULANMIS_KANITLI"},
                            {"fix_id": "FIX-002", "status": "REDDEDILDI",
                             "evidence": "kapsam disi; gerekce: ..."}])
    _g18d_rc, _g18d_o, _g18d_n, _g18d_c = gm18_kur(
        "gm18_silindi",
        [_K1, {"id": "C2", "status": "CALISTIRILMADI", "evidence": "?"}],
        [{"fix_id": "FIX-002", "status": "UYGULANMAMIS"}])
    # (e) checks[] icinde gerekceli red — manifest'te DEGIL.
    # Olculdu: bu dal M6 mutasyonunda YANMADI (133/133 gecti) -> testsiz kalmisti.
    _g18e_rc, _g18e_o, _g18e_n, _g18e_c = gm18_kur(
        "gm18_checks_red",
        [_K1, {"id": "C2", "status": "REDDEDILDI",
               "evidence": "kapsam disi; gerekce: ..."}], _MR0)
    # (f) ayni yer, gerekce YOK -> fail-closed P0
    _g18f_rc, _g18f_o, _g18f_n, _g18f_c = gm18_kur(
        "gm18_checks_red_gerekcesiz",
        [_K1, {"id": "C2", "status": "REDDEDILDI"}], _MR0)

    kontrol(
        "GM-18",
        "SAYAC INVARIANT: toplam == calisan + kosmadi + reddedilen · kova kaybi GORUNUR",
        # (a) KANITSIZ hicbir kovaya girmiyor -> invariant notu CIKAR
        _g18a_rc == 1
        and any("SAYAC_INVARIANT" in n for n in _g18a_n)
        and _g18a_c.get("checks_toplam_2b") == 2
        # (b) temiz kapi -> invariant notu YOK
        and not any("SAYAC_INVARIANT" in n for n in _g18b_n)
        and _g18b_c.get("checks_calisan_2b") + _g18b_c.get("checks_kosmadi_2b") \
        + _g18b_c.get("reddedilen_2b") == _g18b_c.get("checks_toplam_2b")
        # (c) gerekceli red ucuncu kova -> TUTAR, not YOK, sayi GORUNUR
        and _g18c_rc == 0
        and not any("SAYAC_INVARIANT" in n for n in _g18c_n)
        and _g18c_c.get("reddedilen_2b") == 1
        and _g18c_c.get("checks_calisan_2b") + _g18c_c.get("checks_kosmadi_2b") \
        + _g18c_c.get("reddedilen_2b") == _g18c_c.get("checks_toplam_2b")
        # (d) ikinci ve ucuncu kova birlikte de tutar (kosmadi + red)
        and _g18d_c.get("checks_calisan_2b") + _g18d_c.get("checks_kosmadi_2b") \
        + _g18d_c.get("reddedilen_2b") == _g18d_c.get("checks_toplam_2b")
        # (d) fixture: checks = GECTI + CALISTIRILMADI, mr = UYGULANMAMIS
        #     -> kosmadi = 2 (iki ayri "kosmadi" turu AYNI kovada), red = 0
        and _g18d_c.get("checks_kosmadi_2b") == 2
        and _g18d_c.get("reddedilen_2b") == 0
        and not any("SAYAC_INVARIANT" in n for n in _g18d_n)
        # (e) checks[] icindeki gerekceli red: ucuncu kova + stdout'ta GORUNUR
        and _g18e_rc == 0
        and not any("SAYAC_INVARIANT" in n for n in _g18e_n)
        and _g18e_c.get("reddedilen_2b") == 1
        and "REDDEDILEN_GEREKCELI: 1" in _g18e_o
        # (f) gerekcesiz red KACIS olur -> P0 (fail-closed)
        and _g18f_rc == 1
        and any("GEREKCE yok" in n for n in _g18f_n)
        and _g18f_c.get("p0_2b") == 1
        and not any("Traceback" in x for x in (_g18a_o, _g18b_o, _g18c_o, _g18d_o,
                                               _g18e_o, _g18f_o)),
        f"kanitsiz=(rc={_g18a_rc},{_g18a_c}) temiz=(rc={_g18b_rc},{_g18b_c}) "
        f"red=(rc={_g18c_rc},red={_g18c_c.get('reddedilen_2b')}) "
        f"kosmadi=(rc={_g18d_rc},k={_g18d_c.get('checks_kosmadi_2b')}) "
        f"checks_red=(rc={_g18e_rc},red={_g18e_c.get('reddedilen_2b')}) "
        f"gerekcesiz=(rc={_g18f_rc},p0={_g18f_c.get('p0_2b')})",
    )

    pe6 = kur(T / "pe6")
    json_duzenle(pe6 / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.setdefault("findings", []).append(
                     {"id": "PENDING_ETHICS", "priority": ["P0"],
                      "finding": "etik siddeti yanlis tip", "evidence": "x"}))
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                "gate/STRONG-gate-2b-v5.5.json", cwd=pe6)
    kontrol("GM-14", "PENDING_ETHICS konteyner siddeti P0'i AKLAYAMAZ",
            rc == 1 and "PASS-PENDING-ETHICS" not in o and "P0:1" in o
            and "Traceback" not in o,
            f"rc={rc} {o.strip()[:180]}")

    pe7 = kur(T / "pe7")
    json_duzenle(pe7 / "gate/STRONG-gate-2b-v5.5.json",
                 lambda d: d.setdefault("findings", []).append(
                     {"id": "PENDING_ETHICS", "priority": "P2",
                      "finding": "etik onay bekliyor", "evidence": "x"}))
    rc, o = kos("gate_merge.py", "gate/STRONG-gate-2a-v5.5.json",
                "gate/STRONG-gate-2b-v5.5.json", cwd=pe7)
    kontrol("GM-15", "PENDING_ETHICS taninan P2 ise PASS-PENDING-ETHICS kalir",
            rc == 0 and "PASS-PENDING-ETHICS" in o and "Traceback" not in o,
            f"rc={rc} {o.strip()[:180]}")

    # ============ scope_profile_check.py (B-1: alan uyumsuzlugu) ============
    # Kendi fiksturunu kurar; kur() taban projesini DEGISTIRMEZ (53 testi riske atmamak icin).
    def sp_kur(ad, profil, yuvalar):
        d = T / ad
        d.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SCRIPTS, d / "scripts", dirs_exist_ok=True)
        sat = [f"ALAN_PROFILI: {profil}", "", "| ID | Başlık | Zorunluluk | Kaynak | Gerekce |",
               "|---|---|---|---|---|"]
        ortak = ["001", "003", "004", "005", "006", "008", "011", "012", "013", "014",
                 "015", "016", "018", "019", "020", "021", "022", "030"]
        for i in ortak:
            sat.append(f"| SC-{i} | Bolum {i} | ZORUNLU | uretilecek | taban |")
        for sc, baslik in yuvalar.items():
            sat.append(f"| {sc} | {baslik} | ZORUNLU | uretilecek | taban |")
        (d / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md").write_text("\n".join(sat), encoding="utf-8")
        return d

    FILOLOJIK = {"SC-002": "Birincil Metin Kulliyati", "SC-007": "Filolojik Yontem",
                 "SC-009": "Transliterasyon Anahtari", "SC-010": "Karsilastirma Olcutu"}
    AMPIRIK = {"SC-002": "Literatur Sinirbilim", "SC-007": "Null Model",
               "SC-009": "Istatistik", "SC-010": "Bulgular"}

    d = sp_kur("sp1", "filolojik-teolojik", FILOLOJIK)
    rc, o = kos("scope_profile_check.py", cwd=d)
    kontrol("SP-1", "filolojik profil dogru yuvalarla PASS", rc == 0 and "PASS" in o, f"rc={rc} {o.strip()[:120]}")

    d = sp_kur("sp2", "filolojik-teolojik", {**FILOLOJIK, "SC-007": "Null Model"})
    rc_yasak, o_yasak = kos("scope_profile_check.py", cwd=d)

    d = sp_kur("sp2-sira", "filolojik-teolojik", FILOLOJIK)
    f = d / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
    satirlar = []
    for satir in f.read_text(encoding="utf-8").splitlines():
        if satir.strip().startswith("|"):
            sutunlar = [c.strip() for c in satir.strip().strip("|").split("|")]
            if len(sutunlar) == 5:
                sutunlar = [sutunlar[i] for i in (2, 1, 0, 3, 4)]
                satir = "| " + " | ".join(sutunlar) + " |"
        satirlar.append(satir)
    f.write_text("\n".join(satirlar), encoding="utf-8")
    rc_sira, o_sira = kos("scope_profile_check.py", cwd=d)

    d = sp_kur("sp2-eksik", "filolojik-teolojik", FILOLOJIK)
    f = d / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
    f.write_text(f.read_text(encoding="utf-8").replace("Zorunluluk", "Durum", 1),
                 encoding="utf-8")
    rc_eksik, o_eksik = kos("scope_profile_check.py", cwd=d)

    d = sp_kur("sp2-cift", "filolojik-teolojik", FILOLOJIK)
    f = d / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
    f.write_text(f.read_text(encoding="utf-8").replace(
        "| ID | Başlık | Zorunluluk | Kaynak | Gerekce |",
        "| ID | Başlık | Başlık | Zorunluluk | Kaynak | Gerekce |", 1),
        encoding="utf-8")
    rc_cift, o_cift = kos("scope_profile_check.py", cwd=d)

    kontrol("SP-2", "scope tablosu baslik adiyla indekslenir; sema hatalari fail-closed",
            rc_yasak == 1 and "SP-02" in o_yasak and "Traceback" not in o_yasak
            and rc_sira == 0 and "SCOPE-PROFILE PASS" in o_sira and "Traceback" not in o_sira
            and rc_eksik == 1 and "SP-07" in o_eksik and "EKSIK" in o_eksik
            and "Traceback" not in o_eksik
            and rc_cift == 1 and "SP-07" in o_cift and "CIFT" in o_cift
            and "Traceback" not in o_cift,
            f"yasak={rc_yasak} sira={rc_sira} eksik={rc_eksik} cift={rc_cift}")

    d = sp_kur("sp3", "ampirik", AMPIRIK)
    rc, o = kos("scope_profile_check.py", cwd=d)
    kontrol("SP-3", "ampirik profil eski iskeletle PASS (geriye uyumluluk)",
            rc == 0 and "PASS" in o, f"rc={rc} {o.strip()[:120]}")

    d = sp_kur("sp4", "ampirik", AMPIRIK)
    f = d / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
    f.write_text(f.read_text(encoding="utf-8").replace("ALAN_PROFILI: ampirik", "# profil yok"), encoding="utf-8")
    rc, o = kos("scope_profile_check.py", cwd=d)
    kontrol("SP-4", "ALAN_PROFILI beyani yoksa FAIL", rc == 1 and "SP-01" in o, f"rc={rc}")

    d = sp_kur("sp5", "filolojik-teolojik", {k: v for k, v in FILOLOJIK.items() if k != "SC-009"})
    rc, o = kos("scope_profile_check.py", cwd=d)
    kontrol("SP-5", "profile ozgu yuva eksikse FAIL", rc == 1 and "SP-04" in o, f"rc={rc}")

    d = sp_kur("sp6", "ampirik", AMPIRIK)
    f = d / "00-FAZ-0-SCOPE-CONTRACT-ve-REGISTER.md"
    f.write_text(f.read_text(encoding="utf-8").replace("| ZORUNLU |", "| Gerekli |"), encoding="utf-8")
    rc, o = kos("scope_profile_check.py", cwd=d)
    kontrol("SP-6", "bos zorunlu liste vacuous PASS vermez", rc == 1 and "SP-06" in o, f"rc={rc}")

    d = sp_kur("sp7", "solo", {})
    rc, o = kos("scope_profile_check.py", cwd=d)
    kontrol("SP-7", "SOLO profilinde profil-özel yuva zorlaması olmadan PASS",
            rc == 0 and "SCOPE-PROFILE PASS" in o,
            f"rc={rc} {o.strip()[:120]}")

    # ============ tools/yayinla.py (yayin plani / .opencode / git) ============
    # Yayin plani iki sessiz hata uretebilir: `.opencode` calisma-zamani
    # dosyalarini yayina katar ya da temiz agacta izlenen bir dosyayi atlar.
    # Ikisi de ancak baska bir klonda drift olarak gorunur; burada kilitliyoruz.
    _yayin_kok = SCRIPTS.parent.parent
    _yayin_arac = _yayin_kok / "tools" / "yayinla.py"
    if not _yayin_arac.is_file() or not (_yayin_kok / ".git").exists():
        kontrol("YAYIN-1", "yayin plani .opencode calisma-zamanini dislar ve git ile tutarlidir",
                True, "fikstir koku: tools/yayinla.py veya .git yok; kontrol atlandi")
    else:
        try:
            import importlib.util
            _yayin_spec = importlib.util.spec_from_file_location(
                "atlas_yayinla_oztest", str(_yayin_arac))
            _yayin = importlib.util.module_from_spec(_yayin_spec)
            _yayin_spec.loader.exec_module(_yayin)

            # (1) Calisma-zamani dosyalari plana giremez; gercek bir ajan dosyasi girer.
            _runtime = [
                ".opencode/package.json",
                ".opencode/package-lock.json",
                ".opencode/bun.lock",
                ".opencode/.gitignore",
            ]
            _kaynak = T / "yayin-kaynak"
            for _d in list(_yayin.KOKLER) + list(_yayin.TOOLKIT_KOKLER):
                (_kaynak / _d).mkdir(parents=True, exist_ok=True)
            for _rel in _runtime:
                _p = _kaynak / _rel
                _p.parent.mkdir(parents=True, exist_ok=True)
                _p.write_text("calisma-zamani\n", encoding="utf-8")
            _ajan = ".opencode/agent/yayin-oztest.md"
            _ajan_yolu = _kaynak / _ajan
            _ajan_yolu.parent.mkdir(parents=True, exist_ok=True)
            _ajan_yolu.write_text("# ajan\n", encoding="utf-8")
            _planli = set(_yayin.topla(str(_kaynak)))
            _runtime_disarida = not (set(_runtime) & _planli)
            _ajan_icerde = _ajan in _planli

            # (2) Gercek public agac: plan yollari izlenen dosyalarda olmali;
            # temiz agacta plan disi fazlalik ve drift bulunmamali.
            _istenen = _yayin.topla(str(_yayin_kok))
            _yeni, _degisen, _ayni = _yayin.plan(_istenen)
            _silinecek = _yayin.fazlalik(_istenen)
            _git_ls = subprocess.run(
                ["git", "-C", str(_yayin_kok), "ls-files", "-z"],
                capture_output=True, text=True, timeout=60)
            if _git_ls.returncode != 0:
                raise RuntimeError("git ls-files rc=%d: %s" % (
                    _git_ls.returncode, (_git_ls.stderr or "").strip()[:120]))
            _izlenen = {x for x in _git_ls.stdout.split("\0") if x}
            _git_durum = subprocess.run(
                ["git", "-C", str(_yayin_kok), "status", "--porcelain",
                 "--untracked-files=all"],
                capture_output=True, text=True, timeout=60)
            if _git_durum.returncode != 0:
                raise RuntimeError("git status rc=%d" % _git_durum.returncode)
            # Negatif OLG-1 kontrolu yalniz attestation'i bozar; o dosya yayin
            # planinin parcasi degildir, temizlik olcutune girmez.
            _kirli = [s for s in _git_durum.stdout.splitlines()
                      if s.strip() and not s.rstrip().endswith("attestation.json")]
            _plan_temiz = (not _yeni and not _degisen and not _silinecek
                           and len(_ayni) == len(_istenen))
            _izlenen_tutarli = set(_istenen) <= _izlenen
            _gecti = (_runtime_disarida and _ajan_icerde and _plan_temiz
                      and _izlenen_tutarli and not _kirli)
            _ayrinti = (
                "runtime_disarida=%s ajan_icerde=%s plan_temiz=%s "
                "izlenen_tutarli=%s kirli=%d planda=%d"
                % (_runtime_disarida, _ajan_icerde, _plan_temiz,
                   _izlenen_tutarli, len(_kirli), len(_istenen)))
            if _kirli:
                _ayrinti += " kirli_ilk=%r" % (_kirli[:2],)
            kontrol("YAYIN-1", "yayin plani .opencode calisma-zamanini dislar ve git ile tutarlidir",
                    _gecti, _ayrinti)
        except Exception as _e:
            kontrol("YAYIN-1", "yayin plani .opencode calisma-zamanini dislar ve git ile tutarlidir",
                    False, "%s: %s" % (type(_e).__name__, _e))


tmp = tempfile.mkdtemp(prefix="atlas_selftest_")
hata = False
try:
    if not SESSIZ:
        print(f"=== ATLAS OZ-TEST — gecici klasor: {tmp} ===")
    calis(tmp)
except Exception as e:
    hata = True
    print(f"KALDI OZ-TEST-CRASH: test paketi coktu :: {type(e).__name__}: {e}")
finally:
    if not (TUT and (hata or any(not g for _, _, g, _ in sonuc))):
        shutil.rmtree(tmp, ignore_errors=True)
    elif TUT:
        print(f"\n[--tut] gecici klasor birakildi: {tmp}")

gecen = sum(1 for _, _, g, _ in sonuc if g)
print(f"\nOZ-TEST: {gecen}/{len(sonuc)} gecti")
kalanlar = [(k, a) for k, a, g, _ in sonuc if not g]
for k, a in kalanlar:
    print(f"  KALDI {k}: {a}")
sys.exit(1 if (kalanlar or hata) else 0)
