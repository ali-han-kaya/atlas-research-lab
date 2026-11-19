# PROVENANCE-TEMPLATE — Atlas v5.5

> MASTER (`03-FAZ-3-MASTER-v5.5.md`) sonuna eklenen PROVENANCE tablosu bu iskeleti
> temel alır (CHK-02). Tüm ZORUNLU SCOPE-ID'ler (≥22) tabloda en az bir kez
> "kapsıyor" durumuyla yer almalıdır. `provenance_check.py` bu tabloyu denetler.

## PROVENANCE

| SCOPE-ID | Bölüm | Kaynak | Satır Referansı | Kaynak Sınıfı | Durum |
|----------|-------|--------|-----------------|--------------|-------|
| SC-001 | §1 Giriş | A paketi / <kaynak> | MASTER L<n> / §X.Y | BIRINCIL | kapsıyor |
| SC-002 | §2 Literatür | A paketi | MASTER L<n> | IKINCIL | kapsıyor |
| SC-XXX | §X | <kaynak> | MASTER L<n> | BIRINCIL\|IKINCIL\|UCUNCUL\|AKTARMA | kapsıyor\|eksik |

**Kaynak Sınıfı (B-2, v1.7.28):** `BIRINCIL` = kutsal metin / birincil kaynak (Kur'an, Zohar,
Talmud, Taberî'nin kendisi); `IKINCIL` = ikincil akademik okuma (Scholem, Idel);
`UCUNCUL` = üçüncül derleme/ansiklopedi; `AKTARMA` = asıl kaynak görülmeden
aktarılan ikincil okuma — her `AKTARMA` satırında tabloda veya hemen yakında
"asıl kaynak görülmedi" beyanı zorunludur (yoksa P1). `source_class_check.py` denetler.

**Kurallar:**
- "MASTER line X" referansları gerçekten o satıra denk gelmelidir.
- "§Y.Z" referansları doğru bölüme işaret etmelidir (yanlış = P1).
- Doğrulanmamış kaynak (DEC-027 §8 M1) satırlarında durum `[UNVERIFIED]` olarak
  işaretlenir; bu kasıtlıdır.
