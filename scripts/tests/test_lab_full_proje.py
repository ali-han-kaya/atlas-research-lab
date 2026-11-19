#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lab_full_proje — `scripts/lab_full.py` proje sınıflandırması.

NEDEN VAR (15 Kasım 2026): `lab_full`, `projeler/*/` altındaki işleri **yalnız
dönüş koduyla** sınıflandırıyordu. Ölçüldü: `silat-makale`nin kendi kapısı
`PASS-PENDING-ETHICS` hükmü veriyor (`DEC-035/036` OPEN) ve projenin kaydı bunu
"istenen davranış, hata değildir" diye yazıyor. Devir belgesi yazıldığı anda rc=0
olur ve proje **YEŞİL** görünürdü — kapının kendi hükmü "insan onayı bekliyor"
iken. Panoda yanlış yeşil, ölçülen bir yalandır.

Test edilen iki saf fonksiyon:
  proje_hukmu(dizin)  -> FINAL-GATE*.json içindeki `verdict`
  durum_belirle(rc, hukum) -> YESIL / KIRMIZI / INSAN_BEKLIYOR

Kullanım:
    python3 -m unittest scripts/tests/test_lab_full_proje.py -v
"""

import importlib.util
import json
import os
import tempfile
import unittest

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(os.path.dirname(BURASI))
BETIK = os.path.join(KOK, "scripts", "lab_full.py")


def _modul():
    spec = importlib.util.spec_from_file_location("_lab_full_test", BETIK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


LF = _modul()


class TestDurumBelirle(unittest.TestCase):
    def test_rc_sifir_hukum_pass_yesil(self):
        self.assertEqual(LF.durum_belirle(0, "PASS"), "YESIL")

    def test_pending_ethics_yesil_sayilmaz(self):
        """ASIL KUSUR: bu satır olmadan proje sahte yeşil yanıyordu."""
        self.assertEqual(LF.durum_belirle(0, "PASS-PENDING-ETHICS"),
                         "INSAN_BEKLIYOR")

    def test_blocked_insan_bekliyor(self):
        self.assertEqual(LF.durum_belirle(0, "BLOCKED"), "INSAN_BEKLIYOR")

    def test_rc_basarisiz_kirmizi_kazanir(self):
        """rc!=0 ise hüküm ne olursa olsun KIRMIZI (sıra: önce kapı)."""
        self.assertEqual(LF.durum_belirle(1, "PASS"), "KIRMIZI")
        self.assertEqual(LF.durum_belirle(1, "PASS-PENDING-ETHICS"), "KIRMIZI")

    def test_hukum_yoksa_eski_davranis(self):
        """Hüküm okunamazsa rc geçerlidir — ama 'hüküm yok' != 'hüküm YEŞİL'."""
        self.assertEqual(LF.durum_belirle(0, ""), "YESIL")

    def test_kucuk_harf_hukum_de_okunur(self):
        self.assertEqual(LF.durum_belirle(0, "pass-pending-ethics"),
                         "INSAN_BEKLIYOR")


class TestProjeHukmu(unittest.TestCase):
    def _proje(self, verdict=None, gecersiz=False):
        d = tempfile.mkdtemp(prefix="proje_hukmu_")
        os.makedirs(os.path.join(d, "gate"))
        if gecersiz:
            with open(os.path.join(d, "gate", "FINAL-GATE-v5.5.json"), "w",
                      encoding="utf-8") as f:
                f.write("{bozuk json")
        elif verdict is not None:
            with open(os.path.join(d, "gate", "FINAL-GATE-v5.5.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"verdict": verdict, "gate_type": "FINAL-2-of-2"}, f)
        return d

    def test_hukum_okunur(self):
        self.assertEqual(LF.proje_hukmu(self._proje("PASS-PENDING-ETHICS")),
                         "PASS-PENDING-ETHICS")

    def test_gate_yoksa_bos(self):
        self.assertEqual(LF.proje_hukmu(self._proje()), "")

    def test_bozuk_json_sessizce_bos(self):
        """Fail-open değil: hüküm okunamazsa boş döner, uydurmaz."""
        self.assertEqual(LF.proje_hukmu(self._proje(gecersiz=True)), "")

    def test_gate_dizini_yoksa_bos(self):
        d = tempfile.mkdtemp(prefix="proje_hukmu_")
        self.assertEqual(LF.proje_hukmu(d), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
