#!/usr/bin/env python3
"""RUN manifestinden belirlenimsel Fransizca AI beyan paketi uretir.

Manifest, makalenin butun gelistirme gecmisindeki fiili AI kullanimlarini
oturum veya artefakt referansiyla kaydeder. Statik routing kaydi tek basina
kanit degildir. Kapali sema `templates/RUN-MANIFEST-TEMPLATE.json` dosyasidir.

Kullanim:
  python3 scripts/ai_disclosure.py --manifest RUN-MANIFEST.json
  python3 scripts/ai_disclosure.py --manifest RUN-MANIFEST.json --output AI-BEYANI.md
  python3 scripts/ai_disclosure.py --manifest RUN-MANIFEST.json --check AI-BEYANI.md

Varsayilan cikti stdout'tur. Dosyaya yalniz `--output` ile yazilir. `--check`,
mevcut beyanin manifestten yeniden uretilen kanonik metinle birebir ayni
oldugunu denetler; elle degistirilmis tablo veya bolum fail-closed reddedilir.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys


SCRIPTS = pathlib.Path(__file__).resolve().parent
SEMA_YOLU = SCRIPTS.parent / "templates" / "RUN-MANIFEST-TEMPLATE.json"
YER_TUTUCU = re.compile(r"<[^>]*>|\bYYYY\b|\bYAZIN\b|\bORNEK\b", re.IGNORECASE)

TESEKKUR_KULLANIMLARI = {"writing", "language_editing"}
YONTEM_KULLANIMLARI = {
    "source_verification",
    "data_collection",
    "analysis",
    "figure_generation",
}
KULLANIM_FR = {
    "writing": "assistance rédactionnelle",
    "language_editing": "relecture linguistique",
    "source_verification": "vérification des sources",
    "data_collection": "collecte de données",
    "analysis": "analyse",
    "figure_generation": "production de figures",
}


class ManifestHatasi(Exception):
    """Kullaniciya temiz bir AI-* tanisi dondurulecek beklenen hata."""

    def __init__(self, kod, mesaj):
        super().__init__(mesaj)
        self.kod = kod
        self.mesaj = mesaj


class TekrarliAnahtar(ValueError):
    pass


def _tekil_sozluk(ciftler):
    sonuc = {}
    for anahtar, deger in ciftler:
        if anahtar in sonuc:
            raise TekrarliAnahtar(f"tekrarli JSON anahtari: {anahtar}")
        sonuc[anahtar] = deger
    return sonuc


def _json_oku(yol, *, kod):
    try:
        ham = yol.read_bytes()
    except OSError as exc:
        raise ManifestHatasi(kod, f"dosya okunamadi: {yol} ({type(exc).__name__})") from exc
    try:
        metin = ham.decode("utf-8")
        veri = json.loads(
            metin,
            object_pairs_hook=_tekil_sozluk,
            parse_constant=lambda deger: (_ for _ in ()).throw(
                ValueError(f"gecersiz JSON sabiti: {deger}")
            ),
        )
    except (UnicodeError, json.JSONDecodeError, TekrarliAnahtar, ValueError) as exc:
        raise ManifestHatasi(kod, f"JSON gecersiz: {yol} ({exc})") from exc
    return ham, veri


def _sema_oku():
    _, sema = _json_oku(SEMA_YOLU, kod="AI-00")
    try:
        kok_alanlari = set(sema["required"])
        ozellikler = sema["properties"]
        sema_surumu = ozellikler["schema"]["const"]
        kapsam = ozellikler["scope"]["const"]
        satir = ozellikler["entries"]["items"]
        satir_alanlari = set(satir["required"])
        satir_ozellikleri = satir["properties"]
        kullanimlar = set(satir_ozellikleri["usage"]["enum"])
        dogrulamalar = set(satir_ozellikleri["primary_source_verified"]["enum"])
        kanit_deseni = satir_ozellikleri["evidence_ref"]["pattern"]
    except (KeyError, TypeError) as exc:
        raise ManifestHatasi("AI-00", f"RUN manifest sema sablonu bozuk: {exc}") from exc
    if sema.get("additionalProperties") is not False or satir.get("additionalProperties") is not False:
        raise ManifestHatasi("AI-00", "RUN manifest semasi kapali degil")
    return {
        "kok_alanlari": kok_alanlari,
        "satir_alanlari": satir_alanlari,
        "sema_surumu": sema_surumu,
        "kapsam": kapsam,
        "kullanimlar": kullanimlar,
        "dogrulamalar": dogrulamalar,
        "kanit_deseni": kanit_deseni,
    }


def _alan_farki(bulunan, beklenen):
    eksik = sorted(beklenen - bulunan)
    fazla = sorted(bulunan - beklenen)
    parcalar = []
    if eksik:
        parcalar.append("eksik=" + ",".join(eksik))
    if fazla:
        parcalar.append("fazla=" + ",".join(fazla))
    return "; ".join(parcalar)


def _metin_al(satir, alan, sira):
    deger = satir.get(alan)
    if not isinstance(deger, str) or not deger.strip():
        raise ManifestHatasi("AI-02", f"entries[{sira}].{alan} bos veya metin degil")
    if deger != deger.strip():
        raise ManifestHatasi("AI-02", f"entries[{sira}].{alan} kenar bosluk iceriyor")
    if "\n" in deger or "\r" in deger or "|" in deger or "\x00" in deger:
        raise ManifestHatasi("AI-02", f"entries[{sira}].{alan} guvensiz ayirici iceriyor")
    if YER_TUTUCU.search(deger):
        raise ManifestHatasi("AI-02", f"entries[{sira}].{alan} doldurulmamis yer tutucu")
    return deger


def manifest_dogrula(yol):
    sema = _sema_oku()
    if not yol.is_file():
        raise ManifestHatasi("AI-00", f"manifest dosyasi yok: {yol}")
    ham, veri = _json_oku(yol, kod="AI-01")
    if not isinstance(veri, dict):
        raise ManifestHatasi("AI-01", "manifest kok nesnesi sozluk degil")
    bulunan = set(veri)
    if bulunan != sema["kok_alanlari"]:
        raise ManifestHatasi(
            "AI-01", "manifest kok alanlari kapali semayla uyusmuyor: "
            + _alan_farki(bulunan, sema["kok_alanlari"]),
        )
    if veri["schema"] != sema["sema_surumu"]:
        raise ManifestHatasi(
            "AI-01", f"schema beklenen {sema['sema_surumu']!r}, bulunan {veri['schema']!r}")
    if veri["scope"] != sema["kapsam"]:
        raise ManifestHatasi(
            "AI-01", f"scope beklenen {sema['kapsam']!r}, bulunan {veri['scope']!r}")
    if not isinstance(veri["entries"], list) or not veri["entries"]:
        raise ManifestHatasi("AI-01", "entries bos olmayan bir liste olmali")

    satirlar = []
    for sira, satir in enumerate(veri["entries"]):
        if not isinstance(satir, dict):
            raise ManifestHatasi("AI-02", f"entries[{sira}] sozluk degil")
        bulunan = set(satir)
        if bulunan != sema["satir_alanlari"]:
            raise ManifestHatasi(
                "AI-02", f"entries[{sira}] alanlari kapali semayla uyusmuyor: "
                + _alan_farki(bulunan, sema["satir_alanlari"]),
            )
        temiz = {alan: _metin_al(satir, alan, sira) for alan in sema["satir_alanlari"]}
        try:
            datetime.date.fromisoformat(temiz["date"])
        except ValueError as exc:
            raise ManifestHatasi(
                "AI-02", f"entries[{sira}].date YYYY-MM-DD biciminde gecerli tarih degil") from exc
        if temiz["usage"] not in sema["kullanimlar"]:
            raise ManifestHatasi(
                "AI-02", f"entries[{sira}].usage kapali listede degil: {temiz['usage']!r}")
        if temiz["primary_source_verified"] not in sema["dogrulamalar"]:
            raise ManifestHatasi(
                "AI-02", "entries[{}].primary_source_verified kapali listede degil: {!r}".format(
                    sira, temiz["primary_source_verified"]
                ),
            )
        if re.fullmatch(sema["kanit_deseni"], temiz["evidence_ref"]) is None:
            raise ManifestHatasi(
                "AI-02", f"entries[{sira}].evidence_ref session: veya artifact: kaniti degil")
        satirlar.append(temiz)
    return ham, satirlar, sema["sema_surumu"]


def _sirali_tekil(satirlar):
    alanlar = (
        "role",
        "provider",
        "model",
        "model_version",
        "date",
        "usage",
        "primary_source_verified",
    )
    tekil = {tuple(satir[a] for a in alanlar) for satir in satirlar}
    return sorted(tekil, key=lambda degerler: tuple(d.casefold() for d in degerler))


def _arac_listesi(satirlar):
    araclar = {
        f"{satir['provider']}/{satir['model']} "
        f"(version {satir['model_version']}, {satir['date']})"
        for satir in satirlar
    }
    return "; ".join(sorted(araclar, key=str.casefold))


def _kullanim_listesi(satirlar):
    kullanilan = {KULLANIM_FR[satir["usage"]] for satir in satirlar}
    return ", ".join(sorted(kullanilan, key=str.casefold))


def beyan_uret(manifest_ham, satirlar, sema_surumu):
    ozet = _sirali_tekil(satirlar)
    tesekkur = [s for s in satirlar if s["usage"] in TESEKKUR_KULLANIMLARI]
    yontem = [s for s in satirlar if s["usage"] in YONTEM_KULLANIMLARI]
    bolumler = []
    if tesekkur:
        bolumler.append("Remerciements")
    if yontem:
        bolumler.append("Méthodologie")
    if len(bolumler) == 1:
        konum = f"la section {bolumler[0]}"
    else:
        konum = f"les sections {bolumler[0]} et {bolumler[1]}"
    manifest_hash = hashlib.sha256(manifest_ham).hexdigest()

    satirlar_md = [
        f"<!-- ATLAS-AI-DISCLOSURE schema={sema_surumu} manifest-sha256={manifest_hash} -->",
        "# Déclaration relative à l'utilisation de l'intelligence artificielle",
        "",
        "## Lettre de couverture",
        "",
        "Les auteurs déclarent avoir eu recours à des outils d'intelligence artificielle "
        f"générative dans la préparation de cet article, comme détaillé dans {konum} "
        "de l'article. Aucun système d'IA n'est répertorié comme auteur ; les auteurs assument "
        "l'entière responsabilité de l'exactitude, de l'intégrité et de l'originalité du contenu.",
        "",
        "## Article",
        "",
    ]
    if tesekkur:
        satirlar_md += [
            "### Remerciements",
            "",
            f"L'auteur a eu recours à {_arac_listesi(tesekkur)} pour "
            f"{_kullanim_listesi(tesekkur)}. Les sorties générées ont été intégralement "
            "relues et vérifiées par l'auteur, qui assume l'entière responsabilité du contenu final.",
            "",
        ]
    if yontem:
        satirlar_md += [
            "### Méthodologie",
            "",
            f"Des outils d'intelligence artificielle ({_arac_listesi(yontem)}) ont été utilisés "
            f"pour {_kullanim_listesi(yontem)}. Toutes les sorties ont été contrôlées par "
            "l'auteur ; toute discordance a été tranchée en faveur de la source primaire.",
            "",
        ]
    satirlar_md += [
        "## Registre des rôles et modèles",
        "",
        "| Rôle | Modèle | Version | Date | Usage | Source primaire vérifiée ? |",
        "|---|---|---|---|---|---|",
    ]
    for rol, provider, model, version, tarih, kullanim, dogrulama in ozet:
        satirlar_md.append(
            f"| {rol} | {provider}/{model} | {version} | {tarih} | {kullanim} | {dogrulama} |"
        )
    return "\n".join(satirlar_md) + "\n"


def _argumanlar(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=pathlib.Path)
    grup = parser.add_mutually_exclusive_group()
    grup.add_argument("--output", type=pathlib.Path)
    grup.add_argument("--check", type=pathlib.Path)
    return parser.parse_args(argv)


def main(argv=None):
    args = _argumanlar(sys.argv[1:] if argv is None else argv)
    try:
        ham, satirlar, sema_surumu = manifest_dogrula(args.manifest)
        cikti = beyan_uret(ham, satirlar, sema_surumu)
        if args.check is not None:
            try:
                mevcut = args.check.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ManifestHatasi(
                    "AI-04", f"denetlenecek beyan okunamadi: {args.check} ({type(exc).__name__})"
                ) from exc
            if mevcut != cikti:
                raise ManifestHatasi(
                    "AI-04", "beyan manifestten uretilen kanonik metinle uyusmuyor"
                )
            print(f"AI-DISCLOSURE CHECK PASS — {len(_sirali_tekil(satirlar))} tekil rol/model satiri")
        elif args.output is not None:
            try:
                args.output.write_text(cikti, encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ManifestHatasi(
                    "AI-03", f"beyan yazilamadi: {args.output} ({type(exc).__name__})"
                ) from exc
            print(f"AI-DISCLOSURE WRITE PASS — {args.output}")
        else:
            sys.stdout.write(cikti)
    except ManifestHatasi as exc:
        print(f"FAIL {exc.kod}: {exc.mesaj}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
