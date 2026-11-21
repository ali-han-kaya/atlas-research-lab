PY ?= python3
# pip-audit yalniz gelistirme aracidir; varsa yerel sanal ortam kullanilir.
PY_AUDIT ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo $(PY))

.PHONY: dogrula dogrula-ci kanit kanit-dogrula kanit-paket-dogrula durum-yaz durum-kontrol durum-selftest mutasyon oztest demo demo-selftest kapsam kapsam-yaz katalog-kontrol iddia iddia-ag iddia-yaz guvenlik kur yayinla yardim

yardim:
	@echo "make dogrula   tek giris: hijyen + sozdizimi + sir taramasi + kapi oz-testi + uc oz-test (ATLAS_LAB varsa parite)"
	@echo "make dogrula-ci  runner kipi: olculebilen kalemler hukme girer, oz-testler rapor"
	@echo "make kanit     commit + sha256 kanitini ve dogrulama paketini yaz (attestation.json + kanit-paketi/)"
	@echo "make kanit-dogrula  attestation.json'i gercek commit/agac ile dogrula"
	@echo "make kanit-paket-dogrula  kanit-paketi/ icindeki sema, attestation, manifest ve ham kayitlari dogrula"
	@echo "make durum-yaz  tek uretilmis DURUM sayfasini yenile (docs/DURUM.md)"
	@echo "make durum-kontrol  DURUM sayfasi kaynaklara gore bayat mi (CI)"
	@echo "make durum-selftest  DURUM bayatlik kapisinin negatif testleri (gecici kok)"
	@echo "make mutasyon  kapi sozlesmeleri: temiz taban + ihlal; hata rc!=0, beklenen-bulgu isaretli"
	@echo "make demo      ince sarmalayici: ./demo (kod ayrimi icin ./demo; make her hatada 2 doner)"
	@echo "make demo-selftest  demo 0/2 sozlesmesini gecici fiksturlerle sinar"
	@echo "make kapsam    mutasyon kapsam tablosu guncel mi (docs/MUTASYON_KAPSAM.md)"
	@echo "make kapsam-yaz  kapsam tablosunu yeniden uret"
	@echo "make katalog-kontrol  istege bagli ag kontrolu: sabit katalog models.dev'de guncel mi (CI'da yok)"
	@echo "make iddia    README/docs sayisal iddialarini ureten komutla yeniden olc (ag haric)"
	@echo "make iddia-ag  ag gerektiren iddialari da olc"
	@echo "make iddia-yaz  ham kanit anlik goruntusunu yenile (tools/iddia_olcum.json)"
	@echo "make guvenlik  pip-audit: bilinen CVE taramasi (requirements-dev.txt)"
	@echo "make kur       commit/push korumasini bu klonda etkinlestir"
	@echo "make oztest    yalniz oz-test paketleri"
	@echo "make yayinla   ozel agactan aktarim (ATLAS_LAB=<yol>; kuru kosu; drift varsa hata)"
	@echo "make yayinla UYGULA=1  aktarimi yaz"

dogrula:
	@$(PY) tools/dogrula.py

dogrula-ci:
	@$(PY) tools/dogrula.py --ci

kanit:
	@$(PY) tools/kanit.py $(KANIT_ARGS)

kanit-dogrula:
	@$(PY) tools/kanit_dogrula.py

kanit-paket-dogrula:
	@$(PY) tools/kanit_paketi_dogrula.py

durum-yaz:
	@$(PY) tools/durum.py --yaz

durum-kontrol:
	@$(PY) tools/durum.py --kontrol

durum-selftest:
	@$(PY) tools/durum_selftest.py

mutasyon:
	@$(PY) tools/mutasyon_bataryasi.py

demo:
	@./demo

demo-selftest:
	@$(PY) tools/demo_selftest.py

kapsam:
	@$(PY) tools/kapsam.py --kontrol

kapsam-yaz:
	@$(PY) tools/kapsam.py --yaz

katalog-kontrol:
	@$(PY) tools/katalog_kontrol.py

iddia:
	@$(PY) tools/iddia.py

iddia-ag:
	@$(PY) tools/iddia.py --ag

iddia-yaz:
	@$(PY) tools/iddia.py --yaz

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
