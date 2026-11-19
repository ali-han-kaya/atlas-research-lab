#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bagimsizlik kaniti — `BAGIMSIZLIK: VAR` beyanini artefakta baglar (D17).

NEDEN (10/18 model, 8 Kasim 2026): kural "esigi acan olcum BAGIMSIZLIK: VAR
tasimali" diyordu; ama o alani YAZAN ajanin kendisiydi. Yani beyan esigi aciyordu
— 2. turdaki "beyan esik acmaz" kusurunun manifest katmanindaki aynasi.

Bu betik beyani olculebilir hale getirir: VAR dediysen bir HAM YANIT DOSYASI ve
onun sha256'si olmak zorunda. Dosya yoksa, sha tutmazsa ya da aile "oz" ise rc=1.

Kullanim:
  bagimsizlik_dogrula.py --kanit "farkli model ailesi" ham_yanit.md <sha256>

YAPISAL SINIR (yazili, gizlenmez): ayni ajan kendi dosyasini yazip sha'sini
hesaplayabilir. Bu betik onu TESPIT ETMEZ; yaptigi sey "beyan"i "artefakt"a
baglamaktir — denetlenebilir iz birakir, imkansizi iddia etmez.
"""
import hashlib
import sys

OZ_ADLAR = {'oz', 'self', 'kendim', 'ayni', 'lab', '-', ''}


def sha256(yol):
    h = hashlib.sha256()
    with open(yol, 'rb') as f:
        for parca in iter(lambda: f.read(65536), b''):
            h.update(parca)
    return h.hexdigest()


def dogrula(aile, dosya, beklenen):
    a = (aile or '').strip().lower()
    if a in OZ_ADLAR:
        return False, 'aile "%s" bagimsiz sayilmaz (oz/ayni model)' % aile
    try:
        gercek = sha256(dosya)
    except OSError as e:
        return False, 'ham yanit dosyasi yok: %s' % e
    if not beklenen or len(beklenen) != 64:
        return False, 'sha256 bicimi gecersiz (64 hex beklenir)'
    if gercek != beklenen.lower():
        return False, 'SHA TUTMADI: dosya %s != beyan %s' % (gercek[:12], beklenen[:12])
    return True, 'KANIT GECERLI: aile=%s · dosya=%s · sha=%s' % (aile, dosya, gercek[:12])


def main(argv):
    if len(argv) != 5 or argv[1] != '--kanit':
        print('KULLANIM: bagimsizlik_dogrula.py --kanit "<aile>" <dosya> <sha256>')
        return 2
    ok, mesaj = dogrula(argv[2], argv[3], argv[4])
    print(('GECERLI: ' if ok else 'GECERSIZ: ') + mesaj)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
