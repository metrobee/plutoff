# PlutoFF (Seen & Taim CLI)

Professionaalne, minimalistlik ja ülikiire macOS CLI seene- ja taimevaatluste sisestamiseks otse terminalist PlutoF / eElurikkuse andmebaasi.

---

## 1. Paigaldamine Homebrew kaudu

```bash
# Lisa Homebrew repositoorium
brew tap metrobee/homebrew-tap

# Paigalda tööriist
brew install seen
# või
brew install plutoff
```

---

## 2. Seadistamine

Loo fail `~/.plutof_env` oma PlutoF API volitustega:
```bash
PLUTOF_CLIENT_ID="sinu_client_id"
PLUTOF_CLIENT_SECRET="sinu_client_secret"
PLUTOF_USERNAME="sinu_kasutajanimi"
PLUTOF_PASSWORD="sinu_parool"
```

---

## 3. Tööriistad ja Parameetrid

### 1. `seen` (Mükoloogia)
Toetab nii täispikki kui ka ülilühikesi parameetreid:

| Lühike lipp | Täispikk vaste | Kirjeldus / Näited |
| :--- | :--- | :--- |
| **`s:`** | `substraat:` | Puuliik (*kuusk, mänd, kask, haab, lepp, sanglepp, tamm jne*) |
| **`t:`** | `tüüp:` / `tyyp:` | Substraadi tüüp (*lamatüvi, känd, tüügas, lamaoks, kõdu, muld*) |
| **`o:`** | `ohtrus:` | Ohtrus (*üksikud, vähe, mõõdukalt, sage, palju, massiliselt*) |
| **`kv:`** | `kaasv:` / `kaasvaatleja:` | Kaasvaatlejad (*aa, vl, iz, pl, alm, tt, tv, mp, kp, is*) |
| **`m:`** | `märkus:` | Vabatekstiline märkus või leiu lisainfo |

### 2. ZSH Tab-automaatlõpetus (Tab Completion)
- Kirjuta `s:` ja vajuta **`<TAB>`** -> avaneb puuliikide loend.
- Kirjuta `t:` ja vajuta **`<TAB>`** -> avaneb substraadi tüüpide loend.
- Kirjuta `o:` või `oht:` ja vajuta **`<TAB>`** -> avaneb ohtruse loend.
- Kirjuta `kv:` ja vajuta **`<TAB>`** -> avaneb kaasvaatlejate loend.

---

## 4. Omadused ja Töökindlus

- **Apple Photos otsetugi:** Fotosid saab kopeerida otse macOS Photos rakendusest ja kleepida terminali. Teegi sisefailid (`*.photoslibrary`) säilitatakse alati 100% puutumatuna.
- **Natiivne HEIC teisendus:** Teisendab macOS natiivse `sips` utiliidi abil Apple `.HEIC` fotod automaatselt JPEG-formaati, säilitades täieliku EXIF ajatempli ja GPS koordinaadid.
- **Tühikutaluv argumentide normaliseerija:** Toetab ka tühikutega eraldatud lippe (nt `o :üksikud`, `s : kuusk`, `t : lamatüvi`).
- **Automaatne taksonituvastus ja sünonüümide disambiguatsioon:** Toetab eesti tavanimesid, liike ja perekondi (*nt Männitaelik -> Porodaedalea pini, Hiirkäbik -> Baeospora myosura, Käbik -> Baeospora*).
- **Automaatne pilvesünkroon:** Iga lisatud vaatlus uuendab SQLite andmebaasi ja juurutab reaalajas veebiarhiivi aadressile [https://fungib.web.app](https://fungib.web.app).

---

## 5. Kasutamise näited

```bash
# Kiire seenevaatlus lühilippudega
seen "harilik kuuseriisikas" [FOTO] s:kuusk t:kõdu o:massiliselt

# Seenevaatlus koos kaasvaatlejate ja märkusega
seen hiirkäbik [FOTO] kv:aa,vl s:kuusk t:kõdu o:üksikud m:"kuusekäbil"

# Taimevaatlus
taim "harilik jugapuu" [FOTO] elupaik:park ohtrus:üksikud olek:viljub
```

