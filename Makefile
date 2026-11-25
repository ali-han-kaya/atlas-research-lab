PY ?= python3
# pip-audit yalniz gelistirme aracidir; varsa yerel sanal ortam kullanilir.
PY_AUDIT ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo $(PY))

.PHONY: dogrula dogrula-ci kanit kanit-dogrula kanit-paket-dogrula makbuz-dogrula kanit-negatif olgu-negatif durum-yaz durum-kontrol durum-selftest mutasyon mutasyon-kisa sir-mutasyon oztest-mutasyon oztest-mutasyon-yaz oztest demo demo-selftest temiz-teslim taze-klon fresh-clone kapsam kapsam-yaz kapi-sozlesme-test model-kimlik kamu-lint kamu-selftest kamu-arama kamu-arama-selftest yayin-kapisi katalog-kontrol katalog-selftest iddia iddia-hizli iddia-ag iddia-yaz iddia-selftest guvenlik kur yayinla yardim

yardim:
	@echo "make dogrula   tek giris: hijyen + sozdizimi + sir taramasi + kapi oz-testi + uc oz-test (ATLAS_LAB varsa parite)"
	@echo "make dogrula-ci  runner kipi: olculebilen kalemler hukme girer, oz-testler rapor"
	@echo "make kanit     commit + sha256 kanitini ve dogrulama paketini yaz (attestation.json + kanit-paketi/)"
	@echo "make kanit-dogrula  attestation.json'i gercek commit/agac ile dogrula"
	@echo "make kanit-negatif  KANIT-00..06 kodlarinin her birini gercek bozulmayla sinar"
	@echo "make kanit-paket-dogrula  kanit-paketi/ icindeki sema, attestation, manifest ve ham kayitlari dogrula"
	@echo "make makbuz-dogrula  kanit-paketi/makbuz.json icindeki komut/rc/ham satir bagini commit/agac kanitina karsi denetle"
	@echo "make olgu-negatif  OLG-1 negatif kontrol: eksik/bozuk attestation ve 145/146 sinamasi"
	@echo "make durum-yaz  tek uretilmis DURUM sayfasini yenile (docs/DURUM.md)"
	@echo "make durum-kontrol  DURUM sayfasi kaynaklara gore bayat mi (CI)"
	@echo "make durum-selftest  DURUM bayatlik kapisinin negatif testleri (gecici kok)"
	@echo "make mutasyon  kapi sozlesmeleri: temiz taban + ihlal; hata rc!=0, beklenen-bulgu isaretli"
	@echo "make mutasyon-kisa  6 vakalik hizli duman seti (HATA/TERMINAL/BEKLENEN_BULGU)"
	@echo "make sir-mutasyon  dort sir kapisi kenarinin FAIL->PASS mutasyon kanitini dogrula"
	@echo "make oztest-mutasyon  hedef kapi bozulunca ilgili oz-testin PASS->FAIL oldugunu olc; bos govdeli testleri tara"
	@echo "make demo      ince sarmalayici: ./demo (kod ayrimi icin ./demo; make her hatada 2 doner)"
	@echo "make demo-selftest  demo 0/1/2 sozlesmesini gecici fiksturlerle sinar"
	@echo "make temiz-teslim  sentetik temiz teslimi ve 5 kenar fiksturunu uctan uca sinar"
	@echo "make taze-klon  temiz klonda venv kur; demo, dogrula ve kisa mutasyon setini kos"
	@echo "make fresh-clone  taze-klon icin Ingilizce alias"
	@echo "make kapsam    mutasyon kapsam tablosu guncel mi (docs/MUTASYON_KAPSAM.md)"
	@echo "make kapsam-yaz  kapsam tablosunu yeniden uret"
	@echo "make kapi-sozlesme-test  ATLAS-KAPI-CIKTI/v1 sema ve sozlesme testleri"
	@echo "make model-kimlik  emekli model kimligi: kor noktasiz tarama + acik onay listesi"
	@echo "make kamu-lint  ozel yol/eski alan/sahte hash geri sizma taramasi"
	@echo "make kamu-selftest  kamu lint negatif fiksturleri"
	@echo "make kamu-arama  repo kapsamli GitHub kod aramasi; yalniz incomplete_results=false 0'lari kanit"
	@echo "make kamu-arama-selftest  kod arama sozlesmesini agsiz sina"
	@echo "make yayin-kapisi  yayin manifesti + makale/sir/ozel yol kapisi (dogrula on kosulu)"
	@echo "make katalog-kontrol  canli models.dev kapisi: allowlist + bedava profili + append-only kanit (KAYIT_ARGS ile yol)"
	@echo "make katalog-selftest  katalog kapisi ve uretici oz-testleri (ag yok; dogrula on kosulu)"
	@echo "make iddia    README/docs sayisal iddialarini ureten komutla yeniden olc (ag haric)"
	@echo "make iddia-hizli  dogrula/mutasyon gibi pahali satirlari atla; atlananlar PASS degil"
	@echo "make iddia-ag  ag gerektiren iddialari da olc"
	@echo "make iddia-yaz  ham kanit anlik goruntusunu yenile (tools/iddia_olcum.json)"
	@echo "make iddia-selftest  hizli kip ve atlama sozlesmesinin negatif testleri"
	@echo "make guvenlik  pip-audit: bilinen CVE taramasi (requirements-dev.txt)"
	@echo "make kur       commit/push korumasini bu klonda etkinlestir"
	@echo "make oztest    yalniz oz-test paketleri"
	@echo "make yayinla   dis labdan aktarim (ATLAS_LAB=<yol>; kuru kosu; drift varsa hata)"
	@echo "make yayinla UYGULA=1  aktarimi yaz"

dogrula: katalog-selftest
	@$(PY) tools/dogrula.py

dogrula-ci: katalog-selftest
	@$(PY) tools/dogrula.py --ci

kanit:
	@$(PY) tools/kanit.py $(KANIT_ARGS)

kanit-dogrula:
	@$(PY) tools/kanit_dogrula.py

kanit-paket-dogrula:
	@$(PY) tools/kanit_paketi_dogrula.py

makbuz-dogrula:
	@$(PY) tools/kanit_paketi_dogrula.py --makbuz

kanit-negatif:
	@$(PY) tools/kanit_negatif.py

olgu-negatif:
	@$(PY) tools/olgu1_negatif.py

durum-yaz:
	@$(PY) tools/durum.py --yaz

durum-kontrol:
	@$(PY) tools/durum.py --kontrol

durum-selftest:
	@$(PY) tools/durum_selftest.py

mutasyon:
	@$(PY) tools/mutasyon_bataryasi.py

mutasyon-kisa:
	@$(PY) tools/mutasyon_bataryasi.py --kisa

sir-mutasyon:
	@$(PY) tools/sir_kapisi_mutasyon.py --kontrol

oztest-mutasyon:
	@$(PY) tools/oztest_mutasyon.py --kontrol

oztest-mutasyon-yaz:
	@$(PY) tools/oztest_mutasyon.py --yaz

demo:
	@./demo

demo-selftest:
	@$(PY) tools/demo_selftest.py

temiz-teslim:
	@$(PY) tools/temiz_teslim_selftest.py

taze-klon:
	@$(PY) tools/taze_klon.py

fresh-clone: taze-klon

katalog-kurallar:
	@$(PY) tools/kural_katalogu.py --yaz

katalog-kurallar-kontrol:
	@$(PY) tools/kural_katalogu.py --kontrol

kapsam:
	@$(PY) tools/kapsam.py --kontrol

kapsam-yaz:
	@$(PY) tools/kapsam.py --yaz

kapi-sozlesme-test:
	@$(PY) tools/kapi_sozlesmesi_selftest.py

model-kimlik:
	@$(PY) tools/model_kimlik.py --kontrol

kamu-lint:
	@$(PY) tools/kamu_lint.py --kontrol

kamu-selftest:
	@$(PY) tools/kamu_lint.py --oztest

kamu-arama:
	@$(PY) tools/kamu_lint.py --github-arama

kamu-arama-selftest:
	@$(PY) tools/kamu_lint.py --github-oztest

yayin-kapisi:
	@$(PY) tools/yayin_kapisi.py --kontrol --oztest

KAYIT_ARGS ?= --kayit docs/KOD_BEDAVA_KATALOG_KAYDI.jsonl

katalog-kontrol:
	@$(PY) tools/katalog_kontrol.py $(KAYIT_ARGS)

katalog-selftest:
	@$(PY) tools/katalog_kontrol_selftest.py
	@$(PY) tools/model_katalog_uret_selftest.py

iddia:
	@$(PY) tools/iddia.py

iddia-hizli:
	@$(PY) tools/iddia.py --hizli

iddia-ag:
	@$(PY) tools/iddia.py --ag

iddia-yaz:
	@$(PY) tools/iddia.py --yaz

iddia-selftest:
	@$(PY) tools/iddia_selftest.py

# Sir fiksturu muafiyetinin regresyon testi: bilinen satir sessiz, satir/dosya
# degisimi P0, bozuk manifest fail-closed. `make dogrula` bunu on kosul olarak
# kosar; CI ayrica dogrudan cagrir.
fikstur-muafiyet-test:
	@$(PY) tools/fikstur_muafiyet_selftest.py

# Gecici kopyada IDD-04'u bozup gercek kapinin kirmizi yandigini olcer.
# Push/PR'da KOSMAZ; yalniz elle (ve workflow_dispatch ile) cagrilir.
iddia-bozma-selftest:
	@$(PY) tools/iddia_bozma_selftest.py

guvenlik:
	@$(PY_AUDIT) tools/guvenlik.py

kur:
	@sh scripts/kur_hooks.sh

oztest:
	@$(PY) ATLAS_SABLONLAR/scripts/atlas_selftest.py --sessiz
	@$(PY) KOD_SABLONLAR/scripts/kod_selftest.py
	@cd KOMUT_TOOLKIT_v4/ARACLAR/betikler && $(PY) v4_selftest.py >/dev/null && echo "TOOLKIT OZ-TEST: gecti"

yayinla:
	@if [ -z "$(ATLAS_LAB)" ]; then echo "ATLAS_LAB degiskeni gerekli" >&2; exit 2; fi
	@$(PY) tools/yayinla.py --lab "$(ATLAS_LAB)" $(if $(UYGULA),--uygula,)
