# Seen CLI (PlutoFF)

Professionaalne, minimalistlik ja ülikiire macOS CLI seenevaatluste sisestamiseks otse terminalist PlutoF / eElurikkuse andmebaasi.

---

## Omadused

- **Apple Photos otsetugi:** Fotosid saab kopeerida otse macOS Photos rakendusest ja kleepida terminali. Teegi sisefailid (`*.photoslibrary`) säilitatakse alati 100% puutumatuna.
- **Natiivne HEIC teisendus:** Teisendab macOS natiivse `sips` utiliidi abil Apple `.HEIC` fotod automaatselt JPEG-formaati, säilitades täieliku EXIF ajatempli ja GPS koordinaadid.
- **Zsh `noglob` integratsioon:** Väldib metamärkide (`?`, `*`, `[200~`) tõlgendamist failimustrina.
- **Kolmetasemeline deduplikatsioon:** Hoiab ära topeltvaatlused failiräsi (SHA-256), failinime ja EXIF kuupäeva/GPS ristkontrolli abil.
- **Automaatne pilvesünkroon:** Iga lisatud vaatlus uuendab SQLite andmebaasi ja juurutab reaalajas veebiarhiivi aadressile [https://fungib.web.app](https://fungib.web.app).

---

## Paigaldus ja Kasutamine

```bash
# Vaatluse lisamine eesti tavanimega ja fotoga
seen männi-kuldpoorik [LOHISTA_FOTO_VÕI_KLEEBI]

# Lisaparameetritega
seen "kollane tarrik" /tee/pildini.HEIC substraat:kuusk tüüp:lamapuu ohtrus:üksikud märkus:"leitud samblaselt tüvelt"
```
