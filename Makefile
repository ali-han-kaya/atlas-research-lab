PY ?= python3
# pip-audit yalniz gelistirme aracidir; varsa yerel sanal ortam kullanilir.
PY_AUDIT ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo $(PY))

.PHONY: dogrula dogrula-ci bagimlilik-kontrol kanit kanit-yaz proof dokuman-sozlesmesi kanit-dogrula kanit-paket-dogrula kanit-paket-selftest makbuz-dogrula kanit-negatif olgu-negatif durum-yaz durum-kontrol durum-selftest mutasyon mutasyon-anlatim mutasyon-anlatim-selftest mutasyon-kisa sir-mutasyon oztest-mutasyon oztest-mutasyon-yaz oztest demo demo-selftest temiz-teslim taze-klon fresh-clone kapsam kapsam-yaz kapsam-selftest kapi-sozlesme-test model-kimlik kamu-lint kamu-selftest kamu-arama kamu-arama-selftest yayin-kapisi katalog-kontrol bedava-kontrol katalog-selftest ci-katalog-denetim katalog-kayit-dogrula katalog-kayit-selftest iddia iddia-hizli iddia-ag iddia-yaz iddia-selftest guvenlik kur yayinla yardim

yardim:
	@echo "make dogrula   tek giris: bagimlilik on kontrolu + temiz teslim on kontrolu + hijyen + sozdizimi + sir taramasi + kapi oz-testi + uc oz-test (ATLAS_LAB varsa parite)"
	@echo "make bagimlilik-kontrol  gerekli Python modullerini denetle; eksikse kurulum komutlari ve rc=2"
	@echo "make dogrula-ci  runner kipi: olculebilen kalemler hukme girer, oz-testler rapor"
	@echo "make kanit     commit + sha256 kanitini ignored yola ve dogrulama paketini yaz (kanit-cikti/ + kanit-paketi/; tracked attestation'a dokunmaz)"
	@echo "make kanit-yaz  tracked attestation.json'i acikca yenile (commit oncesi)"
	@echo "make proof  PROOF.md'yi attestation, canli komutlar ve CI durumundan uret"
	@echo "make kanit-dogrula  attestation.json'i gercek commit/agac ile dogrula"
	@echo "make kanit-negatif  KANIT-00..06 kodlarinin her birini gercek bozulmayla sinar"
	@echo "make kanit-paket-dogrula  kanit-paketi/ icindeki sema, attestation, manifest ve ham kayitlari dogrula"
	@echo "make kanit-paket-selftest  paket semasi ve bulgu kimliklerinin sessizce gevşemediğini gecici paketle sinar"
	@echo "make makbuz-dogrula  kanit-paketi/makbuz.json icindeki komut/rc/ham satir bagini commit/agac kanitina karsi denetle"
	@echo "make olgu-negatif  OLG-1 negatif kontrol: eksik/bozuk attestation ve 145/146 sinamasi"
	@echo "make durum-yaz  tek uretilmis DURUM sayfasini yenile (docs/DURUM.md)"
	@echo "make durum-kontrol  DURUM sayfasi kaynaklara gore bayat mi (CI)"
	@echo "make durum-selftest  DURUM bayatlik kapisinin negatif testleri (gecici kok)"
	@echo "make mutasyon  kapi sozlesmeleri: temiz taban + ihlal; hata rc!=0, beklenen-bulgu isaretli"
	@echo "make mutasyon-anlatim  katalogdan 109/91/18 ve guncel sayilari turet; README/docs/iddia ile karsilastir"
	@echo "make mutasyon-anlatim-selftest  anlatim kapisinin pozitif + negatif vakalari"
	@echo "make mutasyon-kisa  6 vakalik hizli duman seti (HATA/TERMINAL/BEKLENEN_BULGU)"
	@echo "make sir-mutasyon  dort sir kapisi kenarinin FAIL->PASS mutasyon kanitini dogrula"
	@echo "make oztest-mutasyon  hedef kapi bozulunca ilgili oz-testin PASS->FAIL oldugunu olc; bos govdeli testleri tara"
	@echo "make demo      ince sarmalayici: ./demo (kod ayrimi icin ./demo; make her hatada 2 doner)"
	@echo "make demo-selftest  demo 0/1/2 sozlesmesini gecici fiksturlerle sinar"
	@echo "make temiz-teslim  sentetik temiz teslimi ve 5 kenar fiksturunu uctan uca sinar"
	@echo "make taze-klon  temiz klonda venv kur; dogrula, kanit-dogrula, demo ve agsiz iddia kabul testini kos"
	@echo "make fresh-clone  taze-klon icin Ingilizce alias"
	@echo "make kapsam    mutasyon kapsam tablosu guncel mi (docs/MUTASYON_KAPSAM.md)"
	@echo "make kapsam-yaz  kapsam tablosunu yeniden uret"
	@echo "make kapsam-selftest  kapsam ratchet'inin gecici kopyada kirmizi/yesil testleri"
	@echo "make kapi-sozlesme-test  ATLAS-KAPI-CIKTI/v1 sema ve sozlesme testleri"
	@echo "make model-kimlik  emekli model kimligi: kor noktasiz tarama + acik onay listesi"
	@echo "make kamu-lint  ozel yol/eski alan/sahte hash geri sizma taramasi"
	@echo "make kamu-selftest  kamu lint negatif fiksturleri"
	@echo "make kamu-arama  repo kapsamli GitHub kod aramasi; yalniz incomplete_results=false 0'lari kanit"
	@echo "make kamu-arama-selftest  kod arama sozlesmesini agsiz sina"
	@echo "make yayin-kapisi  yayin manifesti + makale/sir/ozel yol kapisi (dogrula on kosulu)"
	@echo "make katalog-kontrol  canli models.dev kapisi: allowlist + bedava profili + append-only kanit (KAYIT_ARGS ile yol)"
	@echo "make bedava-kontrol  yalniz bedava profili: 10 rol + canli models.dev; elle, CI'ya baglanmaz"
	@echo "make katalog-selftest  katalog kapisi, uretici ve kayit-dogrulayici oz-testleri (ag yok; dogrula on kosulu)"
	@echo "make ci-katalog-denetim  CI workflowlarinda canli katalog/models.dev adimi yok; offline katalog selftesti dogrula-ci icinde"
	@echo "make katalog-kayit-dogrula  JSONL kanit kaydi: sema + sira + commit/tree/hash + append-only"
	@echo "make iddia    README/docs sayisal iddialarini ureten komutla yeniden olc (ag haric)"
	@echo "make iddia-hizli  dogrula/mutasyon gibi pahali satirlari atla; atlananlar PASS degil"
	@echo "make iddia-ag  ag gerektiren iddialari da olc"
	@echo "make iddia-yaz  ham kanit anlik goruntusunu yenile (tools/iddia_olcum.json)"
	@echo "make dokuman-sozlesmesi  README/docs make hedefleri ve CI job adlari gercek Makefile/workflow ile uyusuyor mu"
	@echo "make iddia-selftest  hizli kip ve atlama sozlesmesinin negatif testleri"
	@echo "make guvenlik  pip-audit: bilinen CVE taramasi (requirements-dev.txt)"
	@echo "make kur       commit/push korumasini bu klonda etkinlestir"
	@echo "make oztest    yalniz oz-test paketleri"
	@echo "make yayinla   dis labdan aktarim (ATLAS_LAB=<yol>; kuru kosu; drift varsa hata)"
	@echo "make yayinla UYGULA=1  aktarimi yaz"

# Eksik Python modulu kapilardan once, tek ve net bir kurulum hukmune
dogrula: bagimlilik-kontrol katalog-selftest ci-katalog-denetim
	@$(PY) tools/dogrula.py

dogrula-ci: bagimlilik-kontrol katalog-selftest ci-katalog-denetim dokuman-sozlesmesi
	@$(PY) tools/dogrula.py --ci

# Katalog oz-testlerinden de once kosar; eksik modul varsa kapilar baslamaz.
bagimlilik-kontrol:
	@$(PY) tools/dogrula.py --bagimlilik-kontrol

KANIT_CIKTI ?= kanit-cikti/attestation.json

kanit:
	@$(PY) tools/kanit.py --cikti "$(KANIT_CIKTI)" $(KANIT_ARGS)

kanit-yaz:
	@$(PY) tools/kanit.py --cikti attestation.json $(KANIT_ARGS)

proof:
	@$(PY) tools/kanit.py --proof

kanit-dogrula:
	@$(PY) tools/kanit_dogrula.py

kanit-paket-dogrula:
	@$(PY) tools/kanit_paketi_dogrula.py

kanit-paket-selftest:
	@$(PY) tools/kanit_paketi_selftest.py

makbuz-dogrula:
	@$(PY) tools/kanit_paketi_dogrula.py --makbuz

kanit-negatif:
	@$(PY) tools/kanit_negatif.py

olgu-negatif:
	@$(PY) tools/olgu1_negatif.py

durum-yaz:
	@$(PY) tools/durum.py --yaz

# DURUM_KOK: durum_selftest'in gecici fikstur kokunu gercek hedefe baglar.
durum-kontrol:
	@$(PY) tools/durum.py --kontrol $(if $(DURUM_KOK),--kok "$(DURUM_KOK)",)

durum-selftest:
	@$(PY) tools/durum_selftest.py

mutasyon:
	@$(PY) tools/mutasyon_bataryasi.py

mutasyon-anlatim:
	@$(PY) tools/mutasyon_anlatim_kapisi.py --kontrol

mutasyon-anlatim-selftest:
	@$(PY) tools/mutasyon_anlatim_kapisi_selftest.py

katalog-tutarlilik:
	@$(PY) tools/mutasyon_bataryasi.py --katalog-tutarlilik

katalog-tutarlilik-test:
	@$(PY) tools/mutasyon_bataryasi.py --katalog-tutarlilik-oztest

mutasyon-kisa:
	@$(PY) tools/mutasyon_bataryasi.py --kisa

sir-mutasyon:
	@$(PY) tools/sir_kapisi_mutasyon.py --kontrol

oztest-mutasyon:
	@$(PY) tools/mutasyon_bataryasi.py --katalog-tutarlilik-oztest
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

kapsam-selftest:
	@$(PY) tools/kapsam_selftest.py

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

# Canli models.dev ister; bu yuzden bilerek CI'ya baglanmaz. Yalniz profil
# sozlesmesini (10 rol, tek kimlik, cost 0, reasoning/tool_call true) olcer.
bedava-kontrol:
	@$(PY) tools/katalog_kontrol.py --profil-only

katalog-selftest:
	@$(PY) tools/katalog_kontrol_selftest.py
	@$(PY) tools/model_katalog_uret_selftest.py
	@$(PY) tools/katalog_kayit_dogrula_selftest.py

ci-katalog-denetim:
	@$(PY) tools/katalog_kontrol_selftest.py --ci-denetim

katalog-kayit-selftest:
	@$(PY) tools/katalog_kayit_dogrula_selftest.py

# Kayit dosyasi yalniz eklenir; dogrulayici mevcut agacta HEAD'i ve tam git
# gecmisini ister. CI checkout'u fetch-depth: 0 ile calisir.
katalog-kayit-dogrula:
	@$(PY) tools/katalog_kayit_dogrula.py

iddia:
	@$(PY) tools/iddia.py

dokuman-sozlesmesi:
	@$(PY) tools/iddia.py --dokuman

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
