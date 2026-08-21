#!/usr/bin/env python3
"""
Google Photos Sync Module for PlutoF Mushroom Observations.
Handles OAuth authentication, album management (' PlutoF Vaatlused'), and photo tagging.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List

TOKEN_FILE = os.path.expanduser("~/.google_photos_token.json")
CLIENT_SECRET_FILE = "/Users/metrobee/Projects/realtime-veebis/client_secret_903136773415-32vkc2o5482in9r5nabq4gd1c6podceg.apps.googleusercontent.com.json"
ALBUM_NAME = "PlutoF Vaatlused"
SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.sharing",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata"
]

MULTILINGUAL_CACHE_FILE = os.path.expanduser("~/.taxa_multilingual_names_cache.json")
LANG_MAP = {
    "est": "eesti", "et": "eesti",
    "swe": "rootsi", "sv": "rootsi",
    "nob": "norra", "nno": "norra", "nor": "norra", "no": "norra",
    "dan": "taani", "da": "taani",
    "fin": "soome", "fi": "soome",
    "eng": "inglise", "en": "inglise",
    "deu": "saksa", "de": "saksa"
}
LANG_DISPLAY_ORDER = ["eesti", "rootsi", "norra", "taani", "soome", "inglise", "saksa"]


def get_multilingual_taxa_names(taxon_id: Any, taxon_name: str, est_fallback: str = "") -> Dict[str, str]:
    """Tagastab taksoni rahvapärased nimed eri keeltes (PlutoF + GBIF)."""
    cache = {}
    if os.path.exists(MULTILINGUAL_CACHE_FILE):
        try:
            with open(MULTILINGUAL_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    clean_sci = taxon_name.split("(")[0].strip()
    if " " in clean_sci:
        parts = clean_sci.split()
        if len(parts) >= 2:
            clean_sci = f"{parts[0]} {parts[1]}"

    cache_key = f"{taxon_id or ''}_{clean_sci}".strip("_")
    if cache_key in cache:
        res = cache[cache_key]
        if est_fallback and "eesti" not in res:
            res["eesti"] = est_fallback.capitalize()
        return res

    names = {}
    # 0. Kui taxon_id puudub või eesti nimi puudub, lahendame PlutoF autocomplete kaudu
    if not taxon_id:
        try:
            url_ac = "https://api.plutof.ut.ee/v1/public/taxa/autocomplete/?name=" + urllib.parse.quote(clean_sci)
            req_ac = urllib.request.Request(url_ac, headers={"User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"})
            with urllib.request.urlopen(req_ac, timeout=4) as resp:
                data_ac = json.loads(resp.read().decode("utf-8"))
                for it in data_ac.get("data", []):
                    at = it.get("attributes", {})
                    if not at.get("is_synonym"):
                        taxon_id = str(it.get("id"))
                        v_est = at.get("vernacular_name")
                        if v_est and "eesti" not in names:
                            names["eesti"] = v_est.strip().capitalize()
                        break
        except Exception:
            pass

    # 1. PlutoF taksoni detailpäring
    if taxon_id:
        try:
            url = f"https://api.plutof.ut.ee/v1/public/taxa/{taxon_id}/"
            req = urllib.request.Request(url, headers={"User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                v_list = data.get("data", {}).get("attributes", {}).get("vernacular_names", [])
                for it in v_list:
                    l = LANG_MAP.get(it.get("language"))
                    n = it.get("name", "").strip()
                    if l and n and l not in names:
                        names[l] = n.capitalize()
        except Exception:
            pass

    # 2. GBIF rahvapärased nimed
    try:
        url_match = "https://api.gbif.org/v1/species/match?name=" + urllib.parse.quote(clean_sci)
        req_match = urllib.request.Request(url_match, headers={"User-Agent": "PlutoFObservationAssistant/1.0"})
        with urllib.request.urlopen(req_match, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        usage_key = data.get("usageKey")
        if usage_key:
            v_url = f"https://api.gbif.org/v1/species/{usage_key}/vernacularNames"
            req_v = urllib.request.Request(v_url, headers={"User-Agent": "PlutoFObservationAssistant/1.0"})
            with urllib.request.urlopen(req_v, timeout=4) as resp:
                v_data = json.loads(resp.read().decode("utf-8"))
            for it in v_data.get("results", []):
                l = LANG_MAP.get(it.get("language"))
                n = it.get("vernacularName", "").strip()
                if l and n and l not in names:
                    names[l] = n.capitalize()
    except Exception:
        pass

    cache[cache_key] = names
    try:
        with open(MULTILINGUAL_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return names


PROPOSED_NAMES_FILE = "/Users/metrobee/GEMINI/data/pakutud_seeninimed.json"

def get_proposed_name(sci_name: str) -> Optional[Dict[str, str]]:
    if not os.path.exists(PROPOSED_NAMES_FILE):
        return None
    try:
        with open(PROPOSED_NAMES_FILE, "r", encoding="utf-8") as f:
            proposals = json.load(f)
        clean_sci = sci_name.split("(")[0].strip().lower()
        clean_first_two = " ".join(clean_sci.split()[:2]) if " " in clean_sci else clean_sci
        for p in proposals:
            p_sci = p.get("teaduslik_nimi", "").split("(")[0].strip().lower()
            p_first_two = " ".join(p_sci.split()[:2]) if " " in p_sci else p_sci
            if clean_sci == p_sci or clean_first_two == p_first_two:
                return p
    except Exception:
        pass
    return None


def format_google_photos_description(obs_data: Any, fallback_obs_id: str = "", fallback_taxon_name: str = "") -> str:
    """Kujundab detailse, mitmekeelse ja emotikonivaba kirjelduse Google Photos jaoks."""
    if isinstance(obs_data, dict):
        lines = []
        vern = (obs_data.get("vernacular_name") or "").strip()
        sci = (obs_data.get("taxon_name") or fallback_taxon_name).strip()
        taxon_id = obs_data.get("taxon_id")

        # Mitmekeelsed rahvapärased nimed
        multi_names = get_multilingual_taxa_names(taxon_id, sci, vern)
        if not vern and "eesti" in multi_names:
            vern = multi_names["eesti"]

        # Kontrolli pakutud nime tabelist
        prop = get_proposed_name(sci)
        prop_name = prop.get("pakutud_nimi", "").strip().capitalize() if prop else ""

        if not vern and prop_name:
            vern = f"{prop_name} [pakutud nimi]"

        if vern:
            vern = vern[0].upper() + vern[1:] if len(vern) > 1 else vern.upper()

        if vern and sci:
            lines.append(f"{vern} ({sci})")
        elif vern:
            lines.append(vern)
        elif sci:
            lines.append(sci)

        obs_id = obs_data.get("id") or obs_data.get("obs_id") or fallback_obs_id
        if obs_id:
            lines.append(f"PlutoF ID: {obs_id}")
            lines.append(f"https://app.plutof.ut.ee/observation/view/{obs_id}")

        # Rahvapärased nimed (eesti, rootsi, norra, taani, soome jne)
        names_formatted = []
        for l_key in LANG_DISPLAY_ORDER:
            if l_key in multi_names:
                names_formatted.append(f"{l_key}: {multi_names[l_key]}")

        if prop_name:
            names_formatted.append(f"eesti (pakutud): {prop_name}")

        if names_formatted:
            lines.append("")
            lines.append("Rahvapärased nimed:")
            lines.extend(names_formatted)

        loc_parts = [
            obs_data.get("locality"),
            obs_data.get("commune") or obs_data.get("municipality"),
            obs_data.get("county")
        ]
        loc_str = ", ".join([str(p).strip() for p in loc_parts if p and str(p).strip()])
        if loc_str:
            lines.append("")
            lines.append(f"Asukoht: {loc_str}")

        lat = obs_data.get("latitude") or obs_data.get("lat")
        lon = obs_data.get("longitude") or obs_data.get("lon")
        if lat is not None and lon is not None:
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                if not loc_str:
                    lines.append("")
                lines.append(f"Koordinaadid: {lat_f:.5f}, {lon_f:.5f}")
            except Exception:
                pass

        dt = obs_data.get("date_time")
        if dt:
            lines.append(f"Aeg: {dt}")

        elupaik = obs_data.get("habitat") or obs_data.get("elupaik")
        if elupaik:
            lines.append(f"Elupaik: {elupaik}")

        olek = obs_data.get("phenology") or obs_data.get("olek")
        if olek:
            lines.append(f"Olek: {olek}")

        sub = obs_data.get("substrate")
        stype = obs_data.get("substrate_type")
        if sub and stype:
            lines.append(f"Substraat: {sub} ({stype})")
        elif sub:
            lines.append(f"Substraat: {sub}")
        elif stype:
            lines.append(f"Substraadi tüüp: {stype}")

        abund = obs_data.get("abundance")
        if abund:
            lines.append(f"Ohtrus: {abund}")

        collectors = obs_data.get("collectors")
        if collectors and collectors != "Boris Meldre":
            lines.append(f"Kogujad: {collectors}")

        remarks = obs_data.get("remarks")
        if remarks:
            lines.append(f"Märkus: {remarks}")

        return "\n".join(lines)
    else:
        # Fallback lihtsa stringi korral
        obs_id = fallback_obs_id or str(obs_data)
        if fallback_taxon_name:
            return f"PlutoF ID: {obs_id} | {fallback_taxon_name}\nhttps://app.plutof.ut.ee/observation/view/{obs_id}"
        return f"PlutoF ID: {obs_id}\nhttps://app.plutof.ut.ee/observation/view/{obs_id}"


def get_authenticated_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            if not os.path.exists(CLIENT_SECRET_FILE):
                print(f"Viga: Google OAuth faili ei leitud ({CLIENT_SECRET_FILE})", file=sys.stderr)
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, "w") as token_out:
            token_out.write(creds.to_json())

    return creds


ALBUM_ID_FILE = os.path.expanduser("~/.google_photos_album_id.txt")
ALBUMS_CACHE_FILE = os.path.expanduser("~/.google_photos_albums_cache.json")

def get_or_create_album(creds, album_name: str = ALBUM_NAME) -> Optional[str]:
    """Tagastab albumi ID või loob selle."""
    cache = {}
    if os.path.exists(ALBUMS_CACHE_FILE):
        try:
            with open(ALBUMS_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                if album_name in cache:
                    return cache[album_name]
        except Exception:
            pass

    # Legacy album_id fallback seente jaoks
    if album_name == ALBUM_NAME and os.path.exists(ALBUM_ID_FILE):
        try:
            with open(ALBUM_ID_FILE, "r") as f:
                aid = f.read().strip()
                if aid:
                    cache[album_name] = aid
                    with open(ALBUMS_CACHE_FILE, "w", encoding="utf-8") as f_out:
                        json.dump(cache, f_out, indent=2)
                    return aid
        except Exception:
            pass

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    # Loo uus album
    url_create = "https://photoslibrary.googleapis.com/v1/albums"
    payload = json.dumps({"album": {"title": album_name}}).encode("utf-8")
    try:
        req = urllib.request.Request(url_create, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            album_id = data.get("id")
            if album_id:
                cache[album_name] = album_id
                with open(ALBUMS_CACHE_FILE, "w", encoding="utf-8") as f_out:
                    json.dump(cache, f_out, indent=2)
                return album_id
    except Exception as e:
        print(f"Uue albumi '{album_name}' loomine ebaõnnestus: {e}", file=sys.stderr)
        return None


def sync_observation_to_google_photos(photo_paths: List[str], obs_info: Any, taxon_name: str = "", album_name: str = ALBUM_NAME) -> bool:
    """Lisab vaatluse fotod määratud Google Photos albumisse täielike metaandmetega."""
    try:
        creds = get_authenticated_service()
        if not creds:
            return False

        album_id = get_or_create_album(creds, album_name=album_name)
        if not album_id:
            return False

        headers_upload = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/octet-stream",
            "X-Goog-Upload-Protocol": "raw"
        }

        headers_json = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }

        # Kujunda täielik kirjeldus
        if isinstance(obs_info, dict):
            description_text = format_google_photos_description(obs_info)
        else:
            description_text = format_google_photos_description(str(obs_info), fallback_obs_id=str(obs_info), fallback_taxon_name=taxon_name)

        import time

        for fp in photo_paths:
            if not os.path.exists(fp):
                continue

            fname = os.path.basename(fp)
            upload_headers = dict(headers_upload)
            upload_headers["X-Goog-Upload-File-Name"] = fname

            with open(fp, "rb") as f:
                img_bytes = f.read()

            upload_token = None
            for attempt in range(3):
                try:
                    req_up = urllib.request.Request(
                        "https://photoslibrary.googleapis.com/v1/uploads",
                        data=img_bytes,
                        headers=upload_headers
                    )
                    with urllib.request.urlopen(req_up, timeout=30) as resp:
                        upload_token = resp.read().decode("utf-8")
                        break
                except urllib.error.HTTPError as e:
                    if e.code == 429 or e.code >= 500:
                        time.sleep(2 * (attempt + 1))
                    else:
                        raise e

            if not upload_token:
                continue

            # Lisa albumisse täieliku kirjeldusega
            create_payload = json.dumps({
                "albumId": album_id,
                "newMediaItems": [
                    {
                        "description": description_text,
                        "simpleMediaItem": {
                            "fileName": fname,
                            "uploadToken": upload_token
                        }
                    }
                ]
            }).encode("utf-8")

            for attempt in range(3):
                try:
                    req_batch = urllib.request.Request(
                        "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                        data=create_payload,
                        headers=headers_json
                    )
                    with urllib.request.urlopen(req_batch, timeout=20) as resp:
                        break
                except urllib.error.HTTPError as e:
                    if e.code == 429 or e.code >= 500:
                        time.sleep(2 * (attempt + 1))
                    else:
                        raise e

        print(f"Sünkroonitud Google Photos albumisse: '{ALBUM_NAME}'")
        return True
    except Exception as e:
        print(f"Google Photos sünkroonimise märkus: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    print(" Käivitan Google Photos autentimise...")
    creds = get_authenticated_service()
    if creds:
        album_id = get_or_create_album(creds)
        print(f" Google Photos ühendus edukas! Album: '{ALBUM_NAME}' (ID: {album_id})")
    else:
        print(" Autentimine ebaõnnestus.")
