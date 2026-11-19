PY ?= python3

.PHONY: dogrula oztest yayinla yardim

yardim:
	@echo "make dogrula   tek giriş: hijyen + sözdizimi + sır taraması + üç öz-test"
	@echo "make dogrula-ci  runner kipi: ölçülebilen kalemler hükme girer, öz-testler rapor"
	@echo "make oztest    yalnız öz-test paketleri"
	@echo "make yayinla   özel ağaçtan aktarım (ATLAS_LAB=<yol>; kuru koşu)"
	@echo "make yayinla UYGULA=1  aktarımı yaz"

dogrula:
	@$(PY) tools/dogrula.py

dogrula-ci:
	@$(PY) tools/dogrula.py --ci

oztest:
	@$(PY) ATLAS_SABLONLAR/scripts/atlas_selftest.py --sessiz
	@$(PY) KOD_SABLONLAR/scripts/kod_selftest.py
	@cd KOMUT_TOOLKIT_v4/ARACLAR/betikler && $(PY) v4_selftest.py >/dev/null && echo "TOOLKIT OZ-TEST: gecti"

yayinla:
	@$(PY) tools/yayinla.py --lab "$${ATLAS_LAB:?ATLAS_LAB degiskeni gerekli}" $(if $(UYGULA),--uygula,)
