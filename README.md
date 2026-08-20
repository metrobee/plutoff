# PlutoFF (Seen & Taim CLI)

Professionaalne, minimalistlik ja ülikiire macOS CLI seene- ja taimevaatluste sisestamiseks otse terminalist PlutoF / eElurikkuse andmebaasi.

---

## Tööriistad

1. **`seen` (Mükoloogia):** Seenevaatlused koos puiduliigi, substraadi, ohtruse ja EXIF/GPS metaandmetega.
2. **`taim` (Botaanika):** Taimevaatlused koos elupaiga (*mets, niit, park, rannik*), fenoloogia (*õitseb, viljub, pungad*) ja EXIF/GPS metaandmetega.

---

## Omadused

- **Apple Photos otsetugi:** Fotosid saab kopeerida otse macOS Photos rakendusest ja kleepida terminali. Teegi sisefailid (`*.photoslibrary`) säilitatakse alati 100% puutumatuna.
- **Natiivne HEIC teisendus:** Teisendab macOS natiivse `sips` utiliidi abil Apple `.HEIC` fotod automaatselt JPEG-formaati, säilitades täieliku EXIF ajatempli ja GPS koordinaadid.
- **Zsh `noglob` integratsioon:** Väldib metamärkide (`?`, `*`, `[200~`) tõlgendamist failimustrina.
- **PlutoF Automaatne Taksonituvastus:** Toetab eesti tavanimesid ja ladinakeelseid nimesid.
- **Automaatne pilvesünkroon:** Iga lisatud vaatlus uuendab SQLite andmebaasi ja juurutab reaalajas veebiarhiivi aadressile [https://fungib.web.app](https://fungib.web.app).

---

## Kasutamine

```bash
# Taimevaatlus (Harilik jugapuu)
taim harilik jugapuu [LOHISTA_FOTO_VÕI_KLEEBI]

# Lisaparameetritega
taim "harilik jugapuu" [FOTO] elupaik:park ohtrus:üksikud olek:viljub märkus:"Kärdla keskväljak"

# Seenevaatlus
seen "harilik kuuseriisikas" [FOTO] substraat:kuusk tüüp:kõdu ohtrus:massiliselt
```
