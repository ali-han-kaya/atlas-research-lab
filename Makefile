PY ?= python3
# pip-audit yalniz gelistirme aracidir; varsa yerel sanal ortam kullanilir.
PY_AUDIT ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo $(PY))

.PHONY: dogrula dogrula-ci mutasyon oztest demo kapsam kapsam-yaz katalog-kontrol guvenlik kur yayinla yardim

yardim:
	@echo "make dogrula   tek giris: hijyen + sozdizimi + sir taramasi + kapi oz-testi + uc oz-test"
	@echo "make dogrula-ci  runner kipi: olculebilen kalemler hukme girer, oz-testler rapor"
	@echo "make mutasyon  kapi kurallari gercekten atesliyor mu (temiz taban + ihlal)"
	@echo "make demo      ince sarmalayici: ./demo (kod ayrimi icin ./demo; make her hatada 2 doner)"
	@echo "make kapsam    mutasyon kapsam tablosu guncel mi (docs/MUTASYON_KAPSAM.md)"
	@echo "make kapsam-yaz  kapsam tablosunu yeniden uret"
	@echo "make katalog-kontrol  istege bagli ag kontrolu: sabit katalog models.dev'de guncel mi (CI'da yok)"
	@echo "make guvenlik  pip-audit: bilinen CVE taramasi (requirements-dev.txt)"
	@echo "make kur       commit/push korumasini bu klonda etkinlestir"
	@echo "make oztest    yalniz oz-test paketleri"
	@echo "make yayinla   ozel agactan aktarim (ATLAS_LAB=<yol>; kuru kosu)"
	@echo "make yayinla UYGULA=1  aktarimi yaz"

dogrula:
	@$(PY) tools/dogrula.py

dogrula-ci:
	@$(PY) tools/dogrula.py --ci

mutasyon:
	@$(PY) tools/mutasyon_bataryasi.py

demo:
	@./demo

kapsam:
	@$(PY) tools/kapsam.py --kontrol

kapsam-yaz:
	@$(PY) tools/kapsam.py --yaz

katalog-kontrol:
	@$(PY) tools/katalog_kontrol.py

guvenlik:
	@$(PY_AUDIT) tools/guvenlik.py

kur:
	@sh scripts/kur_hooks.sh

oztest:
	@$(PY) ATLAS_SABLONLAR/scripts/atlas_selftest.py --sessiz
	@$(PY) KOD_SABLONLAR/scripts/kod_selftest.py
	@cd KOMUT_TOOLKIT_v4/ARACLAR/betikler && $(PY) v4_selftest.py >/dev/null && echo "TOOLKIT OZ-TEST: gecti"

yayinla:
	@$(PY) tools/yayinla.py --lab "$${ATLAS_LAB:?ATLAS_LAB degiskeni gerekli}" $(if $(UYGULA),--uygula,)
