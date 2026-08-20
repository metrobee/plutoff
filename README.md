# PlutoFF (`seen`)

> **Professionaalne, ülikiire ja automatiseeritud CLI tööriist seenevaatluste edastamiseks PlutoF / eElurikkuse ametlikku andmebaasi.**  
> *(Nimi: **PlutoFF** – viimane **F** nagu **Fungi**)*

![PlutoFF Demo](docs/demo.gif)

Toetab **macOS**, **Linux** ja **Windows** operatsioonisüsteeme.

---

## Kiirpaigaldus Homebrew kaudu (macOS ja Linux)

Kõige kiirem ja mugavam viis tööriista paigaldamiseks on kasutada Homebrew'd:

```bash
brew tap metrobee/tap
brew install seen
```

*Valmis! Pärast seda on käsk `seen` koheselt sinu terminalis kasutatav koos täieliku Tab-täienduse toega.*

---

## Muud paigalduse viisid

### Git / Käsitsi paigaldus (macOS ja Linux)
```bash
git clone https://github.com/metrobee/plutoff.git
cd plutoff
./install.sh
```

### Windows (PowerShell / CMD)
```cmd
git clone https://github.com/metrobee/plutoff.git
cd plutoff
install.bat
```

*Windows PowerShellis Tab-täienduse aktiveerimiseks:*
```powershell
. .\completions\seen.ps1
```

---

## Seadistamine (`~/.plutof_env`)

1. **Loo PlutoF portaalis OAuth2 rakendus:**
   - Logi sisse aadressil [https://app.plutof.ut.ee](https://app.plutof.ut.ee)
   - Vali vasakult menüüst või profiili alt **OAuth2 Applications** (või otselink: `https://app.plutof.ut.ee/oauth/applications/`)
   - Kliki **New Application** / **Lisa rakendus**:
     - **Name:** `plutoff` (või suvaline nimi)
     - **Client type:** `Confidential`
     - **Authorization grant type:** `Resource owner password-based`
     - **Redirect uris:** jäta tühjaks või määra `https://localhost`

2. **KRIITILINE TÄHELEPANEK (Võtmete kopeerimine):**
   > **TÄHTIS:** Kopeeri **Client ID** ja **Client Secret** KOHE loomise hetkel!  
   > PlutoF süsteemi eripära tõttu kuvatakse `Client Secret` selgel kujul ainult loomisel. Kui hiljem rakenduse seadetes klikkida *Edit* või *Save*, kirjutab süsteem salavõtme üle ja eelmine võti lakkab töötamast.

3. **Salvesta andmed faili `~/.plutof_env`:**
   Loo oma kodukausta fail `~/.plutof_env` (Windowsis `%USERPROFILE%\.plutof_env`):

```env
PLUTOF_CLIENT_ID=sinu_kopeeritud_client_id
PLUTOF_CLIENT_SECRET=sinu_kopeeritud_client_secret
PLUTOF_USERNAME=sinu_plutof_kasutajanimi_voi_email
PLUTOF_PASSWORD=sinu_plutof_parool
```

---

## Tab-klahviga automaatne täiendus (Autocompletion)

Käsk toetab nutikat Tab-täiendust kõigil platvormidel (macOS Zsh, Linux Bash, Windows PowerShell).

Kui trükid terminali parameetri eesliite ja vajutad **Tab**-klahvi:
- `sub:` + **Tab** -> kuvab toetatud puuliigid (`kuusk`, `mänd`, `kask`, `haab`, `tamm`, `saar` jne).
- `tyyp:` + **Tab** -> kuvab substraadi tüübid (`lamatüvi`, `känd`, `tüügas`, `lamaoks`, `elavpuu`, `kõdupuit`, `muld` jne).
- `ohtrus:` + **Tab** -> kuvab ohtruse astmed (`üksikud`, `vähe`, `mõõdukalt`, `sage`, `palju`, `massiliselt`).

---

## Põhifunktsioonid

1. **Vahetu sisestamine lohistades:** Lohista fotod või `.zip` arhiiv otse terminali – skript loeb EXIF-ist täpsed GPS-koordinaadid, kõrguse ja kuupäeva.
2. **Kahesuunaline taksonoomia otsing:** Tuvastab liiginimesid korraga nii eesti keeles (`pehmepoorik`, `harunev korallnarmik`) kui ladina keeles (`Sarcoporia polyspora`).
3. **Vormi 72 mõõtmiste ja substraatide tugi:** Määrab automaatselt puuliigi (*Picea abies*, *Pinus sylvestris* jne), substraadi tüübi (*lamatüvi*, *känd*, *tüügas*), asustusviisi (*Looduses*) ja ohtruse (*Üksikud*, *Vähe*, *Sage*, *Ohtralt*).
4. **3-tasandiline duplikaatide blokeering:**
   - **Tase 1 (SHA-256):** Kaitseb failisisu topeltlaadimise eest.
   - **Tase 2 (Failinimi):** Tuvastab varem kasutatud pildinimed (`PXL_...`).
   - **Tase 3 (EXIF aeg + GPS):** Hoiab ära sama hetke ja asukoha duplikaadid.
5. **Automaatne failikoristus:** Pärast edukat API-kinnitust liigutatakse allalaaditud pildid või `.zip` fail automaatselt süsteemsesse Prügikasti (*Trash*), tagades puhta `Downloads` kausta.
6. **Reaalajas kohalik andmebaas:** Salvestab vaatlused lokaalsesse SQLite andmebaasi (`plutof_vaatlused.db`) ja JSON-faili.

---

## Kasutamise näited

### 1. Lihtne vaatlus (1 foto lohistades):
```bash
seen leekmampel /Users/kasutaja/Downloads/PXL_20260817_153952692.jpg
```

### 2. Täielik vaatlus (substraat, tüüp ja ohtrus):
```bash
seen pehmepoorik /Users/kasutaja/Downloads/foto.jpg sub:kuusk tüüp:lamatüvi ohtrus:üksikud
```

### 3. ZIP arhiivi lohistamine (mitu fotot korraga):
```bash
seen "harunev korallnarmik" /Users/kasutaja/Downloads/seened.zip sub:kask tüüp:känd ohtrus:vähe
```

### 4. Minu vaatluste nimekiri terminalis:
```bash
seen --list
```

### 5. Kõik parameetrid ja abitekst:
```bash
seen --help
```

---

## Toetatud parameetrid

| Parameeter | Valikud | Selgitus |
| :--- | :--- | :--- |
| `sub:` või `substraat:` | `kuusk`, `mänd`, `kask`, `haab`, `lepp`, `tamm`, `saar`, `sarapuu`, `vaher`, `pärn` | Substraadi puuliik |
| `tyyp:` või `tüüp:` | `lamatüvi`, `känd`, `tüügas`, `lamaoks`, `elavpuu`, `kõdupuit`, `kõdu`, `okkad`, `lehed`, `muld` | Substraadi kuju/seisund |
| `ohtrus:` | `üksikud`, `vähe`, `mõõdukalt`, `sage`, `palju`, `massiliselt` | Viljakehade rohkus |
| `märkus:` | `märkus:tekst` | Vabatekstiline lisamärkus |
| `--keep` | | Jätab algse faili kausta alles (ei kustuta) |
| `--force` | | Lubab teadlikult varem saadetud foto uuesti saata |

---

## Litsents

MIT License. Vabalt kasutatav kõigile mükoloogidele ja loodushuvilistele.
