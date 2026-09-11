# INCIDENTS.md — PlutoFF Dashboard Süsteemsete Vigade Register

## Intsidentide Täielik Kroonika

### [INCIDENT-2026-08-20-HEIC-NATIVE-PILLOW-FAIL] iPhone HEIC Fotode Tugi ja Automaatne macOS SIPS Konverteerimine
- **Kuupäev**: 20. august 2026
- **Sümptom**: iPhone'i `.HEIC` foto edastamisel käsklusele `seen` tagastati viga: `cannot identify image file ... .HEIC` ning GPS metaandmeid ei tuvastatud.
- **Algpõhjus (RCA)**: Pythoni standardne `Pillow` teek ei toeta Apple'i HEIC-formaati ilma eraldi kompileeritud `pillow-heif` moodulita.
- **Püsiv lahendus**: Integreeritud macOS-i natiivne `sips` mootor (`sips -s format jpeg ...`), mis teisendab HEIC pildi taustal ajutiseks JPEG failiks ilma süsteemi lisapakette vajamata. Tulemusena säilivad 100% täpsed GPS koordinaadid, kõrgus ja kuupäev ning pilt laetakse PlutoF serverisse.

---

### [INCIDENT-2026-08-20-ZSH-BRACKETED-PASTE-ERROR] Terminali Bracketed Paste Märgendi [200~ Tekitatud Zsh Bad Pattern Tõrge
- **Kuupäev**: 20. august 2026
- **Sümptom**: Faili lohistamisel terminali tekkis viga: `zsh: bad pattern: [200~/Users/...`.
- **Algpõhjus (RCA)**: Terminali Bracketed Paste funktsioon lisas lohistatud tekstile ümber kontrollmärgid `[200~` ja `~`, mida Zsh tõlgendas regulaaravaldisena (*glob*).
- **Püsiv lahendus**: Koodi lisatud automaatne sisendi normaliseerimine (`.replace("[200~", "").replace("~", "")`), tagades lohistatud failiteede tõrgeteta töötlemise.

---

### [INCIDENT-2026-08-20-PLUTOFF-THUMBNAIL-404] Pisipiltide HTTP 404 Viga Tartu Ülikooli HPC S3 Serveris
- **Kuupäev**: 20. august 2026
- **Sümptom**: PlutoFF veebidashboardi (`fungib.web.app`) avavaates kuvati kaartide fotode asemel tühi ala või alt-tekst, kuigi modaalis pilt avanes.
- **Algpõhjus (RCA)**: Andmeeksport proovis tuletada pisipildi URL-i asendusega `/large/` -> `/thumbnail/`. TÜ HPC S3 serveris aga `/thumbnail/` alamkausta ei eksisteeri, mistõttu brauser sai staatilise HTTP 404 (Not Found) vastuse.
- **Püsiv lahendus**: Andmeekspordis ja esiosas seadistati piltide universaalseks allikaks otse ametlik ja toimiv `/large/` fotolink (`https://s3.hpc.ut.ee/plutof-public/large/...`).

---

### [INCIDENT-2026-08-20-LOCAL-FILEPATH-EXPOSURE] Kohalike Failiteede Asendamine Ametlike S3 Linkidega
- **Kuupäev**: 20. august 2026
- **Sümptom**: Viimati lisatud vaatluste fotod ei avanenud veebis.
- **Algpõhjus (RCA)**: `seen` CLI salvestas esialgu kohaliku arvuti failitee (`/Users/.../Downloads/...`), mida veebibrauser ei saa laadida.
- **Püsiv lahendus**: PlutoF API faili ID-de (`plutof_file_id`) kaudu tehti päringud, mis tuvastasid ja salvestasid avalikud S3 lingid `https://s3.hpc.ut.ee/plutof-public/large/...`.


## [INCIDENT-2026-08-20-CO-OBSERVATION-IMAGE-IMPORT]
- **Sümptom:** Kaasvaatluste (Allar Antson, Piret Lõhmus jt) kaartidel kuvati "Foto puudub", kuigi fotod olid PlutoF-is olemas.
- **Algpõhjus (RCA):** PlutoF standardne otsingueksport jättis vaikimisi veeru `Image URL` failist välja.
- **Lahendus:** Teostati täielik eksport 54 veeruga (sh `Image URL`), millest imporditi andmebaasi 432 uut S3 fotolinki. Nüüd omavad fotot 646 vaatlust 774-st.

## [INCIDENT-2026-08-20-DEFAULT-SORT-ORDER]
- **Sümptom:** Äsja terminalist sisestatud vaatlus (Aprikoosvöödik) ei ilmunud nimekirja algusesse.
- **Algpõhjus (RCA):** Nimekiri oli varem sorteeritud leiu kuupäeva järgi (`date_time DESC`), mistõttu 2021. aasta leiu foto paigutus 2021. aasta kirjete juurde.
- **Lahendus:** Muudeti vaikimisi sorteerimine sisestamise aja järgi (`created_at DESC`) ning lisati kasutajale sorteerimise rippmenüü.

## [INCIDENT-2026-08-20-PHOTOS-APP-CRASH-PREVENTION]
- **Süsteem:** `seen` CLI (`seen_cli.py`)
- **Sümptom:** Apple Photos rakendusest otse kopeeritud failide puhul tekkis Photos.app sulgumisviga.
- **Algpõhjus (RCA):** Skript liigutas Photos Library sisefaili prügikasti.
- **Püsiv Lahendus:** Lisatud `.photoslibrary` failikaitse `move_to_trash` funktsiooni.

## [INCIDENT-2026-08-20-HOMEBREW-RELEASE-V120]
- **Süsteem:** `plutoff` ja `homebrew-tap`
- **Tegevus:** Versioon uuendatud `v1.2.0` peale Homebrewis.

## [INCIDENT-2026-08-20-TAXON-MAPPING-AMBIGUITY]
- **Süsteem:** `seen` CLI
- **Sümptom:** `kahkjas mampel` valis vale sünonüümi/liigi.
- **Lahendus:** Eelistatakse alati kohalikku ClipSnippet teaduslikku nime. Välja antud `v1.2.1`.

## [INCIDENT-2026-08-20-TAIM-CLI-FORM-AND-AUTH-FIX]
- **Süsteem:** `taim` CLI
- **Sümptom:** Taimevormi viga lahendatud `Form 73` integratsiooniga. Välja antud `v1.3.1`.

## [INCIDENT-2026-08-20-TAIM-CLI-ISOLATION-AND-PRIVATE-REPO]
- **Arhitektuur:** `taim` CLI eraldatud privaatsesse repositooriumisse (`metrobee/taim`).

## [INCIDENT-2026-08-20-CLIPSNIPPET-BRACKETED-PASTE-CLEANUP]
- **Süsteem:** CLI ja Zsh
- **Lahendus:** Eemaldatud `^[[200~` koodid `clean_cli_arg` funktsiooniga ja `unset zle_bracketed_paste`.

## [INCIDENT-2026-08-20-KIVIPURAVIK-TAXON-MATCHING]
- **Süsteem:** `seen` CLI
- **Sümptom:** `kivipuravik` valis vale liigi (*Neoboletus*).
- **Lahendus:** Täiendatud sorteerimisloogikat ja lisatud sulgude tugi. Välja antud `v1.2.2`.

## [INCIDENT-2026-08-20-TAXA-CACHE-STALE-KIVIPURAVIK]
- **Süsteem:** `seen` CLI
- **Sümptom:** Vahemälust võeti vana vigane kirje.
- **Lahendus:** Vahemälu puhastatud ja parandatud vaatlus `#8318721`.

## [INCIDENT-2026-08-20-CO-OBSERVER-FLAG-SUPPORT]
- **Süsteem:** `seen` CLI
- **Funktsioon:** Lisatud `kaasv:aa` jms kaasvaatlejate lipud. Välja antud `v1.2.3`.

## [INCIDENT-2026-08-20-VELLO-LIIV-ALIAS-ADDED]
- **Süsteem:** `seen` CLI
- **Täiendus:** Lisatud `kaasv:vl` (*Vello Liiv* ID: 19681). Välja antud `v1.2.4`.

## [INCIDENT-2026-08-20-KV-PREFIX-AND-LEADING-COLONS]
- **Süsteem:** `seen` CLI
- **Täiendus:** Lisatud `kv:` ja `:kaasvaatleja:` formaatide tugi. Välja antud `v1.2.5`.

## [INCIDENT-2026-08-20-CO-OBSERVER-LIST-WHITESPACE-SPLIT]
- **Süsteem:** `seen` CLI
- **Lahendus:** Lubatud tühikud koma järel kaasvaatlejate loetelus (`kv:aa, vl`). Välja antud `v1.2.6`.

## [INCIDENT-2026-08-20-GENUS-LEVEL-OBSERVATIONS-SUPPORT]
- **Süsteem:** `seen` CLI
- **Täiendus:** Lisatud perekonna tasemel vaatluste tugi (`Ramaria sp.`, `ramaria`, `harik sp.`). Välja antud `v1.2.7`.

## [INCIDENT-2026-08-20-KIMP-SAMETKORGES-MAPPING]
- **Süsteem:** `seen` CLI
- **Lahendus:** Lisatud `kimp-sametkõrges` sidumine liigiga *Flammulina velutipes* (ID: 147778). Välja antud `v1.2.9`.

## [INCIDENT-2026-08-20-KIMP-METSKORGES-CONNOPUS]
- **Süsteem:** `seen` CLI
- **Lahendus:** `Kimp-metskõrges` seotud taksoniga *Connopus acervatus* (ID: 141001). Välja antud `v1.3.2`.

## [INCIDENT-2026-08-20-CSS-BRACE-SYNTAX-ERROR-AND-MOBILE-LAYOUT]
- **Süsteem:** `fungib.web.app` frontend
- **Sümptom:** Brauser kuvas unstyled HTML-i, kuna stiilifaili parsimine katkes.
- **Algpõhjus (RCA):** `[data-theme="dark"]` selektoril puudus sulgev loogeline sulg `}`, mistõttu CSS-parser luges terve faili vigaseks ja loobus stiilide rakendamisest.
- **Püsiv Lahendus:**
  1. Süntaks parandatud ja kontrollitud automaatse AST/braces parseriga.
  2. Versioon tõstetud `styles.css?v=4`.
  3. Juurutatud Firebase Hostingusse ja commititud GitHubi.

## [INCIDENT-2026-08-20-FIREBASE-AUTH-GATE-AND-DOCS-UPDATE]
- **Süsteem:** `fungib.web.app` frontend ja turvalisus
- **Funktsioon:** Lisatud Google Sign-In autentimisvärav (`ALLOWED_EMAILS = ['borismeldre@gmail.com']`), mis teeb arhiivi privaatseks.
- **Dokumentatsioon:** Uuendatud `README.md` koos täieliku paigaldus- ja seadistusjuhendiga uutele kasutajatele.

# INCIDENT LOGS & RCA (ROOT CAUSE ANALYSIS) - FUNGIB

## INCIDENT 004: Observations.json Payload Bloat & Lack of Herbarium Filtering
- **Kuupäev:** 2026-08-30
- **Sümptom:** `observations.json` faili suurus kasvas 9.4 MB-ni, kuna iga 2108 vaatluse juures dubleeriti 14 keele etümoloogilist sõnastikku (`vernacular_names`). Puudus spetsiaalne otsing ja filter teaduskollektsioonide (TU, TAA, DNA proovid, mikroskoopia) eristamiseks.
- **RCA:**
  1. Denormaliseeritud JSON struktuur tekitas ~4.5 MB tarbetut dubleerimist 680 liigi vahel.
  2. Herbaariumi ja DNA proovide metaandmed olid maetud vabatekstilistesse märkustesse ilma struktuurse tuvastuseta.
- **Püsiv Lahendus:**
  1. Normaliseeritud taksonite register `taxa`, vähendades failimahtu 48% (4.93 MB-ni).
  2. Implementeeritud `extract_specimen_info` mootor (tuvastab TU/TAA/KM koodid, DNA proovid, eosemõõdud).
  3. Lisatud kliendipoolne Web Worker välkotsing ja DOM virtualiseerimine (`content-visibility: auto`).

### [INCIDENT-2026-08-30-SEARCH-CONJUNCTIVE-AND-PRECISION] Otsingumootori Mitmesõnaliste Päringute Konjunktiivsuse ja Täpsuse Refaktoorimine
- **Kuupäev**: 30. august 2026
- **Sümptom**: Otsides liitpäringut `hall napsik` kuvati 62 ebarelevantsest tulemust (sh *Amanita phalloides*, *Clitocybe nebularis* jms), mitte ainult 3 reaalset liigi *Pluteus salicinus* (*hall napsik*) vaatlust.
- **Algpõhjus (RCA)**:
  1. `js/search-worker.js` teostas lahtist disjunktiivset (OR) liitmist, kus iga otsingusõna lisas vasteid eraldi.
  2. `token.includes(qToken)` lubas suvalisi sisesõnalisi vasteid (nt ladinakeelne tüvi `phalloides` vastas otsingusõnale `hall`).
  3. Otsingutulemused kirjutati `app.js` poolt üle vaikimisi kuupäevalise sorteerimisega, eirates relevantsust.
- **Püsiv lahendus**:
  1. Juurutatud range konjunktiivne (AND) sobitus: kõik otsingusõnad peavad leiduma vaatluse indekseeritud kirjeldustes.
  2. Eemaldatud suvalised sisesõnalised osavasted ja asendatud täpsete sõna-/eesliite- ja liitsõnavaste reeglitega.
  3. Lisatud täieliku fraasi boonus (+1000 punkti) ja tulemuste automaatne reastamine relevantsusskoori järgi.
  4. Päring `hall napsik` tagastab nüüd 100% täpsusega täpselt 3 liigi *Pluteus salicinus* vaatlust.

---

### [INCIDENT-2026-09-05-FUNGIB-HOSTING-OVERWRITE] Firebase Hosting Sihtprojekti Ülekirjutuse Tõrge ja PlutoFF Arhiivi Taastamine
- **Kuupäev**: 5. september 2026
- **Sümptom**: Rakendus `https://fungib.web.app/` ei töötanud; PlutoFF mükoloogiaarhiivi asemel avanes mittetoimiv teise projekti ("Sittkeeb") dashboard, mille alamlehed ja andmepäringud ebaõnnestusid.
- **Algpõhjus (RCA)**: 4. septembril 2026 teostati välisest repositooriumist (`realtime-veebis`) ekslik Hosting deploy olukorras, kus Firebase CLI aktiivseks vaike-projektiks oli märgitud `fungib` ja puudus lokaalne lukustusfail `.firebaserc`. Selle tagajärjel kirjutati `fungib.web.app` üle võõra veebirakenduse staatiliste failidega.
- **Püsiv lahendus**:
  1. Loodud range projekti lukustus `.firebaserc` (`{"projects": {"default": "fungib"}}`), mis välistab vale projekti sihtimise.
  2. Eraldatud konfiguratsioonid ja lisatud `.gitignore` reeglid ajutiste vahemälude jaoks.
  3. Täiendatud autentimise valge nimekirja tuge (`boris.meldre@ut.ee` lisatud ametliku meiliaadressina `app.js` koodis).
  4. Teostatud PlutoFF täielik taaskomplekteerimine ja ametlik taas-deploy Firebase Hostingusse (`fungib.web.app`).
  5. Verifitseeritud HTTP 200 vastused lehe indeksi, 2135 vaatlusega normaliseeritud andmefaili (`observations.json`), Leaflet kaardikihtide ja Web Worker taustaotsingu jaoks.

---

### [INCIDENT-2026-09-11-SEEN-CLI-DEPLOY-AND-STDOUT-LEAK] seen CLI Automaatse Juurutuse Tõrge ja Terminali Väljundileke
- **Kuupäev**: 11. september 2026
- **Sümptom**: Pärast `seen` käsuga vaatluse lisamist (sh vaatlus `8334701` *Amyloporia xantha*) ei jõudnud andmed veebirakendusse `https://fungib.web.app` ning kasutaja terminali prinditi eksportija silumisinfo (`Eksport edukas: 2293 vaatlust ja 697 taksonit...`).
- **Algpõhjus (RCA)**:
  1. Varasemas commits asendati sünkroonne funktsioon `deploy_to_fungib()` funktsiooniga `run_post_sync_hook()`, kus käivitati `subprocess.Popen([sys.executable, exp_script], start_new_session=True)`.
  2. See jättis teostamata käsu `firebase deploy --only hosting --project fungib`, jättes veebirakenduse uuendamata.
  3. Protsessi standardväljundit ei vaigistatud, mistõttu eksportija statistika lekkis vaatluse sisestamise järel terminali.
- **Püsiv lahendus**:
  1. Taastatud sünkroonne `deploy_to_fungib()` funktsionaalsus `seen` CLI koodis (`capture_output=True`), tagades terminali puhtuse ja silumisväljundi peitmise.
  2. Firebase Hosting juurutus käivitatakse automaatselt ja korrektselt pärast andmete eksporti (`firebase deploy --only hosting --project fungib`).
  3. Uuendatud kood sünkroniseeritud failides `/Users/metrobee/GEMINI/scripts/seen_cli.py` ja `/Users/metrobee/GEMINI/projekti_hoidlad/plutoff/seen.py`.
  4. Veebirakendus `https://fungib.web.app` juurutatud, vaatlus `8334701` on reaalajas kättesaadav.

