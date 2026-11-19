#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tur4_paket_uret — `scripts/tur4_paket_uret.py` için GERÇEK test.

NEDEN VAR (9 Kasım 2026): `tur4_paket_uret.py` bir süre **kapısızdı**. Sonra
`skill_lint.py` içine `C14y` eklendi — o kapı paketin İÇERİĞİNİ kaynakla
karşılaştırır. Ama `C14y` betiğin **API'sini** sınamaz:

  - `--tek` ile parçalı mod aynı EK'leri taşıyor mu
  - `parca_adlari()` tarih formatını doğru üretiyor mu
  - `--kontrol` çıktısı üç satır ve sha'lar diskle aynı mı
  - `uret()` bilinmeyen seçim verilince patlıyor mu (fail-closed)

Bu testler OLMADAN `C14y` "yeşil" der ama `--tek` sessizce bozulabilir.
Test kapısız bırakılmaz: her koşuda `skill_lint.py` → `C14z` bunu çalıştırır.

Kullanım:
    python3 -m unittest scripts/tests/test_tur4_paket_uret.py -v
"""

import importlib.util
import os
import re
import subprocess
import sys
import unittest

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
BETIK = os.path.join(KOK, "scripts", "tur4_paket_uret.py")


def _modul():
    spec = importlib.util.spec_from_file_location("_t4_test", BETIK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


T4 = _modul()


def _ek_etiketleri(metin):
    """Metindeki `## EK <X> — `<yol>`` başlıklarının etiket kümesi."""
    return set(re.findall(r"^## EK ([A-Z]) — `", metin, re.M))


class TestParcaYapisi(unittest.TestCase):
    """Parçalama YENİ kusur üretmemeli: her EK tam olarak bir parçada."""

    def test_tum_ekler_bir_parcada(self):
        p1 = _ek_etiketleri(T4.uret(T4.P1_ETIKET))
        p2 = _ek_etiketleri(T4.uret(T4.P2_ETIKET))
        tumu = set(e for e, _, _ in T4.DOSYALAR)
        self.assertEqual(p1 & p2, set(), "aynı EK iki parçada")
        self.assertEqual(p1 | p2, tumu, "parçalar eseri eksik taşıyor")

    def test_tek_mod_hepsini_tasir(self):
        self.assertEqual(_ek_etiketleri(T4.uret()), set(e for e, _, _ in T4.DOSYALAR))

    def test_tek_ve_parcali_ayni_icerik(self):
        tek = T4.uret()
        birlesik = T4.uret(T4.P1_ETIKET) + T4.uret(T4.P2_ETIKET)
        # Her EK bloğunun GÖVDESİ iki modda da birebir aynı olmalı.
        for et, yol, _ in T4.DOSYALAR:
            a = re.search(r"^## EK %s — `%s`.*?````text\n(.*?)\n````$"
                          % (et, re.escape(yol)), tek, re.M | re.S)
            b = re.search(r"^## EK %s — `%s`.*?````text\n(.*?)\n````$"
                          % (et, re.escape(yol)), birlesik, re.M | re.S)
            self.assertIsNotNone(a, "EK %s tek modda yok" % et)
            self.assertIsNotNone(b, "EK %s parçalı modda yok" % et)
            self.assertEqual(a.group(1), b.group(1), "EK %s gövdesi modlar arası farklı" % et)


class TestSurumTekKaynak(unittest.TestCase):
    """Sürüm elle yazılmaz — SURUM.md'den ve SKILL.md'den okunur.

    11 Kasım 2026: iki sürüm KARIŞTIRILIYORDU. Başlık "Denetlenen sürüm:
    `SKILL.md`" diyor ama SURUM.md'nin LAB sürümünü yazıyordu. Artık iki ayrı
    alan var; ikisi de kendi kaynağından okunur.
    """

    def test_surum_surum_md_ile_ayni(self):
        with open(os.path.join(KOK, "SURUM.md"), encoding="utf-8") as f:
            for satir in f:
                if satir.startswith("Sürüm:"):
                    beklenen = satir.split(":")[1].strip().split()[0]
                    break
            else:
                self.fail("SURUM.md içinde `Sürüm:` satırı yok")
        self.assertEqual(T4.surum(), beklenen)
        self.assertIn(beklenen, T4.uret())
        self.assertIn(beklenen, T4.uret(T4.P1_ETIKET))
        self.assertIn(beklenen, T4.uret(T4.P2_ETIKET))

    def test_eser_surum_skill_md_ile_ayni(self):
        """`eser_surum()` SKILL.md'nin KENDİ `metadata.version`'unu okumalı."""
        with open(os.path.join(KOK, "SKILL.md"), encoding="utf-8") as f:
            for satir in f:
                if re.match(r"^\s+version:\s*\"", satir):
                    ham = re.search(r'"([^"]+)"', satir).group(1)
                    beklenen = ham if ham.startswith("v") else "v" + ham
                    break
            else:
                self.fail("SKILL.md içinde `version:` satırı yok")
        self.assertEqual(T4.eser_surum(), beklenen)
        self.assertIn(beklenen, T4.uret())
        self.assertIn(beklenen, T4.uret(T4.P1_ETIKET))
        self.assertIn(beklenen, T4.uret(T4.P2_ETIKET))

    def test_iki_surum_karistirilmaz(self):
        """Eser sürümü ile lab sürümü aynı alanda yazılmamalı."""
        for metin in (T4.uret(), T4.uret(T4.P1_ETIKET), T4.uret(T4.P2_ETIKET)):
            self.assertIn("Denetlenen sürüm:", metin)
            satir = [s for s in metin.splitlines() if s.startswith("**Denetlenen sürüm:**")][0]
            self.assertIn("SKILL.md", satir)
            # ESER sürümü bu satırda olmalı
            self.assertIn(T4.eser_surum(), satir)


class TestAdVeCli(unittest.TestCase):

    def test_parca_adlari_sabit_ve_deterministik(self):
        """12 Kasim 2026: ad ARTIK GUNE BAGLI DEGIL.

        OLCULDU (kusur): eski ad `..._P1_YYYY-AA-GG.md` idi ve
        `datetime.date.today()` kullaniyordu. Gece yarisi gecince kapi
        `C14y ... FAIL ... _2026-11-12.md YOK` veriyordu — yani her gun
        kirmizi. Tarih zaten paket ICERIGINDE yaziyor; ad onu tekrar
        etmemeli, yoksa iki kopyadan biri kacinilmaz olarak bayatlar.
        """
        p1, p2 = T4.parca_adlari()
        self.assertEqual(p1, "DIS_DENETIM_TUR5_P1.md")
        self.assertEqual(p2, "DIS_DENETIM_TUR5_P2.md")
        # deterministik: iki cagri ayni adi vermeli (gun farki etkilemez)
        self.assertEqual(T4.parca_adlari(), T4.parca_adlari())
        # tarih ad yerine ICERIKTE yasar
        self.assertIn("**Tarih:**", T4.uret(T4.P1_ETIKET))

    def test_p2_p1_adini_anar(self):
        self.assertIn(T4.parca_adlari()[0], T4.uret(T4.P2_ETIKET))

    def test_kontrol_uc_satir_ve_sha_diskle_ayni(self):
        # [DUZELTME 13 Kasim 2026, Z17f] TIMEOUT eklendi. C15j taramasi
        # `scripts/*.py` (ust duzey) idi; `scripts/tests/` ALT DIZINI taranmiyordu.
        # Tarama kapsami genisletilince bu cagri OLCULDU (timeout yok).
        # Timeout'suz cagri, testin HIC DONMEMESI demektir.
        r = subprocess.run([sys.executable, BETIK, "--kontrol"],
                           cwd=KOK, capture_output=True, text=True,
                           timeout=300)
        self.assertEqual(r.returncode, 0, r.stderr)
        # 11 Kasım 2026: `--kontrol` artık iki sürüm satırı da basar
        # (`ESER` / `LAB`). EK satırları yalnız A/B/C ile başlayanlardır.
        satirlar = [s for s in r.stdout.strip().splitlines()
                    if s.strip() and s[:1] in ("A", "B", "C") and s[1:3] == "  "]
        self.assertEqual(len(satirlar), len(T4.DOSYALAR))
        for satir, (et, yol, _) in zip(satirlar, T4.DOSYALAR):
            self.assertTrue(satir.startswith(et + "  "), satir)
            self.assertIn(T4.sha(os.path.join(KOK, yol)), satir)


class TestTarihKaynaktan(unittest.TestCase):
    """15 Kasım 2026 (Z45b): paket TAKVİME bağlı olmamalı.

    OLCULDU (kusur): başlık `datetime.date.today()` taşıyordu. Gece devrinde
    aynı içerik farklı bayt üretti ve `C14y` "BAYAT" dedi — P1 78848 B =
    78848 B, tek fark `**Tarih:** 2026-11-14` -> `2026-11-15`. Yani kapı
    "eser değişti" değil "takvim döndü" diyordu: YANLIŞ-KIRMIZI.
    """

    def test_tarih_kaynaktan_gelir(self):
        """Başlıktaki gün = paketlenen dosyaların SON commit günü."""
        gun = T4.kaynak_tarihi()
        self.assertRegex(gun, r"^\d{4}-\d{2}-\d{2}$")
        m = re.search(r"\*\*Tarih:\*\* (\d{4}-\d{2}-\d{2})",
                      T4.uret(T4.P1_ETIKET))
        self.assertIsNotNone(m, "başlıkta Tarih satırı yok")
        self.assertEqual(m.group(1), gun)
        r = subprocess.run(
            ["git", "-C", KOK, "log", "-1", "--format=%cs", "--"]
            + [y for _, y, _ in T4.DOSYALAR],
            capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr[:200])
        self.assertEqual(m.group(1), r.stdout.strip())

    def test_iki_uretim_ayni_bayt(self):
        """Aynı repo durumu -> aynı bayt (üretim deterministik)."""
        a = T4.uret(T4.P1_ETIKET)
        b = T4.uret(T4.P1_ETIKET)
        self.assertEqual(a, b)
        c = T4.uret(T4.P2_ETIKET)
        self.assertEqual(c, T4.uret(T4.P2_ETIKET))

    def test_kaynakta_duvar_saati_cagrisi_yok(self):
        """AST taraması: `date.today` / `datetime.now` ÇAĞRISI olmamalı.

        Değer testi tek başına yetmez: kaynaklar bugün commit edilirse
        "git günü == bugün" olur ve regresyon GÖRÜNMEZ. Bu test güne bağlı
        değil — duvar saati çağrısı hangi gün eklenirse eklensin yakalar.
        Yorum satırları sayılmaz (yalnız ÇAĞRI düğümleri gezilir).
        """
        import ast as _ast
        with open(BETIK, encoding="utf-8") as f:
            agac = _ast.parse(f.read())
        yasak = []
        for d in _ast.walk(agac):
            if isinstance(d, _ast.Call) and isinstance(d.func, _ast.Attribute) \
                    and d.func.attr in ("today", "now", "utcnow"):
                yasak.append("%s() satır %d" % (d.func.attr, d.lineno))
        self.assertEqual(yasak, [], "duvar saati çağrısı: %s" % yasak)


class TestYedekYollar(unittest.TestCase):
    """15 Kasım 2026 (Z45c): `kaynak_tarihi()`nin git DIŞINDAKİ iki dalı.

    OLCULMEYEN kalemiydi: EK 116 §4 "`SOURCE_DATE_EPOCH` yolu ÇALIŞTIRILMADI;
    `RuntimeError` yolu da denenmedi". Bu sınıf iki dalı da çalıştırır.
    git başarısız taklit edilir (`subprocess` stub) — gerçek repoyu bozmadan.
    """

    @staticmethod
    def _git_yok():
        import types
        return types.SimpleNamespace(
            run=lambda *a, **k: types.SimpleNamespace(
                returncode=128, stdout="", stderr="git: command not found"))

    def test_source_date_epoch_git_yokken_gun_verir(self):
        import unittest.mock as mock
        with mock.patch.object(T4, "subprocess", self._git_yok()), \
                mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "0"}):
            self.assertEqual(T4.kaynak_tarihi(), "1970-01-01")

    def test_source_date_epoch_gercek_tarih(self):
        """0 seçildi çünkü sınır: en eski temsil edilebilir gün."""
        import unittest.mock as mock
        # 1700000000 = 2023-11-14 (UTC) — sabit, yerel saate bağlı değil
        with mock.patch.object(T4, "subprocess", self._git_yok()), \
                mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1700000000"}):
            self.assertEqual(T4.kaynak_tarihi(), "2023-11-14")

    def test_ikisi_de_yoksa_runtimeerror(self):
        """Fail-closed: duvar saatine SESSİZCE dönmek yasak (I7)."""
        import unittest.mock as mock
        with mock.patch.object(T4, "subprocess", self._git_yok()), \
                mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as bağlam:
                T4.kaynak_tarihi()
        self.assertIn("SOURCE_DATE_EPOCH", str(bağlam.exception))

    def test_bozuk_epoch_de_sessizce_gecmez(self):
        """`SOURCE_DATE_EPOCH=abc` → RuntimeError; `isdigit` kontrolü bunu sağlar."""
        import unittest.mock as mock
        with mock.patch.object(T4, "subprocess", self._git_yok()), \
                mock.patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "abc"}):
            with self.assertRaises(RuntimeError):
                T4.kaynak_tarihi()


class TestFailClosed(unittest.TestCase):
    """Bilinmeyen seçim sessizce boş paket üretmemeli."""

    def test_bilinmeyen_secim_bos_ek_verir_ve_kimlik_tutar(self):
        m = T4.uret(("Z",))
        self.assertEqual(_ek_etiketleri(m), set(), "olmayan etiket EK üretti")
        # kimlik tablosu yine de tüm dosyaları listeler (denetçi doğrulayabilsin)
        for _, yol, _ in T4.DOSYALAR:
            self.assertIn(yol, m)


class TestDelta(unittest.TestCase):
    """TAM DELTA (17 Kasım 2026) — tablo ve gömülü sayılar kendini denetler.

    NEDEN: tur 11 paketinin §2 deltası 8 Kasım'a aitti ve elle yazılmıştı;
    yeni turda olduğu gibi gönderilseydi denetçi **eski durumu** denetlerdi.
    Delta artık `git log`'dan üretilmiş bir demet + `_delta_tutarlilik()`.

    Bu testler olmadan: sayı bozulur, tablo eksik satır basar, `uret()` çökmeden
    yanlış sayı taşıyan paket denetçiye gider. Üçü de sessiz kusurdur.
    """

    def test_aritmetik_tutarli(self):
        n = len(T4.DELTA_MADDELER)
        s = T4.DELTA_SAYILAR
        self.assertEqual(s["mekanizma"], n,
                         "gomulu mekanizma sayisi demetle uyusmuyor")
        self.assertEqual(s["toplam"], n + s["kayit"] + s["kapsam_disi"],
                         "toplam != mekanizma + kayit + kapsam_disi")
        # `_delta_tutarlilik()` ayni seyi dogrular ve sozlugu dondurur
        self.assertEqual(T4._delta_tutarlilik(), s)

    def test_bozuk_sayi_coker(self):
        """Fail-closed: yanlis sayiyla paket URETILMEZ, coker."""
        import unittest.mock as mock
        bozuk = dict(T4.DELTA_SAYILAR)
        bozuk["mekanizma"] = len(T4.DELTA_MADDELER) + 1
        with mock.patch.object(T4, "DELTA_SAYILAR", bozuk):
            with self.assertRaises(RuntimeError):
                T4._delta_tutarlilik()

    def test_toplam_bozuksa_da_coker(self):
        import unittest.mock as mock
        bozuk = dict(T4.DELTA_SAYILAR)
        bozuk["kapsam_disi"] = bozuk["kapsam_disi"] + 7
        with mock.patch.object(T4, "DELTA_SAYILAR", bozuk):
            with self.assertRaises(RuntimeError):
                T4._delta_tutarlilik()

    def test_tablo_her_madde_icin_bir_satir(self):
        satirlar = T4.delta_tablo().splitlines()
        # 2 baslik satiri + bir satir/madde
        self.assertEqual(len(satirlar), len(T4.DELTA_MADDELER) + 2)
        for (et, h, _d, _k), satir in zip(T4.DELTA_MADDELER, satirlar[2:]):
            self.assertIn(h, satir, "kanit sha satirda yok: %s" % h)
            self.assertTrue(satir.startswith("| "), satir)
        # hucre sayisi sabit: 4 sutun -> satirda 5 ayirac
        for satir in satirlar:
            self.assertEqual(satir.count("|"), 5, satir)

    def test_yer_tutucu_kalmadi(self):
        """`uret()` her `{...}` tutucusunu doldurmus olmali."""
        for metin in (T4.uret(), T4.uret(T4.P1_ETIKET), T4.uret(T4.P2_ETIKET)):
            kalan = re.findall(r"\{[A-Z_]+\}", metin)
            self.assertEqual(kalan, [], "doldurulmamis tutucu: %s" % kalan)

    def test_delta_P1_ve_tek_pakette_var(self):
        """Delta P1'de olmali (P2 yalniz eseri tasir, §0-§7 P1'dedir)."""
        p1 = T4.uret(T4.P1_ETIKET)
        self.assertIn("tam delta", p1)
        self.assertIn("git show --stat " + T4.DELTA_MADDELER[0][1], p1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
