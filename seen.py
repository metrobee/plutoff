#!/usr/bin/env python3
"""
Seen CLI - Ülilihtne ja nutikas seenevaatluste sisestaja terminalist
-------------------------------------------------------------------
Autor: Boris Meldre & Antigravity (2026)
Asukoht: /Users/metrobee/GEMINI/scripts/seen_cli.py

Kasutamine:
  seen <liiginimi> [LOHISTA PILDID] [substraat:kuusk] [tüüp:lamapuu] [ohtrus:üksikud] [märkus:tekst]
"""

import os
import sys
import json
import math
import uuid
import sqlite3
import hashlib
import datetime
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

CREDENTIALS_FILE = os.path.expanduser("~/.plutof_env")
CACHE_FILE = os.path.expanduser("~/.plutof_geo_cache.json")
TAXA_CACHE_FILE = os.path.expanduser("~/.plutof_taxa_cache.json")
PROCESSED_REGISTRY_FILE = os.path.expanduser("~/.plutof_processed_photos.json")
BORIS_REGISTER_FILE = "/Users/metrobee/GEMINI/data/boris_seened_photos_register.json"
PHOTOS_TAXA_DB = "/Users/metrobee/GEMINI/data/photos_taxa.db"
LOCAL_OBS_DB = "/Users/metrobee/GEMINI/data/plutof_vaatlused.db"
LOCAL_OBS_JSON = "/Users/metrobee/GEMINI/data/plutof_vaatlused.json"

# Substraatide vastavused: Eestikeelne nimi -> (Teaduslik nimi, PlutoF Taksoni ID)
SUBSTRATE_MAP = {
    "kuusk": ("Picea abies (L.) H.Karst.", "6223"),
    "kuuse": ("Picea abies (L.) H.Karst.", "6223"),
    "picea": ("Picea abies (L.) H.Karst.", "6223"),
    "picea abies": ("Picea abies (L.) H.Karst.", "6223"),
    "mänd": ("Pinus sylvestris L.", "6318"),
    "männi": ("Pinus sylvestris L.", "6318"),
    "mand": ("Pinus sylvestris L.", "6318"),
    "pinus": ("Pinus sylvestris L.", "6318"),
    "pinus sylvestris": ("Pinus sylvestris L.", "6318"),
    "kask": ("Betula pendula Roth", "3102"),
    "kase": ("Betula pendula Roth", "3102"),
    "arukask": ("Betula pendula Roth", "3102"),
    "sookask": ("Betula pubescens Ehrh.", "3104"),
    "betula": ("Betula pendula Roth", "3102"),
    "haab": ("Populus tremula L.", "6504"),
    "haava": ("Populus tremula L.", "6504"),
    "harilik haab": ("Populus tremula L.", "6504"),
    "populus": ("Populus tremula L.", "6504"),
    "sarapuu": ("Corylus avellana L.", "3769"),
    "corylus": ("Corylus avellana L.", "3769"),
    "sanglepp": ("Alnus glutinosa (L.) Gaertn.", "2675"),
    "hall-lepp": ("Alnus incana (L.) Moench", "2676"),
    "hall lepp": ("Alnus incana (L.) Moench", "2676"),
    "lepp": ("Alnus incana (L.) Moench", "2676"),
    "lepa": ("Alnus incana (L.) Moench", "2676"),
    "alnus": ("Alnus", "2674"),
    "tamm": ("Quercus robur L.", "6779"),
    "tamme": ("Quercus robur L.", "6779"),
    "quercus": ("Quercus robur L.", "6779"),
    "pärn": ("Tilia cordata Mill.", "7880"),
    "parn": ("Tilia cordata Mill.", "7880"),
    "tilia": ("Tilia cordata Mill.", "7880"),
    "vaher": ("Acer platanoides L.", "2379"),
    "acer": ("Acer platanoides L.", "2379"),
    "saar": ("Fraxinus excelsior L.", "4525"),
    "fraxinus": ("Fraxinus excelsior L.", "4525")
}

# Substraadi tüübi vastavused: Eestikeelne nimi -> (Tüüp string, PlutoF Type ID)
TYPE_MAP = {
    "lamapuu": ("Lamatüvi", 15),
    "lamatüvi": ("Lamatüvi", 15),
    "lamatyvi": ("Lamatüvi", 15),
    "log": ("Lamatüvi", 15),
    "känd": ("Känd", 13),
    "kand": ("Känd", 13),
    "stump": ("Känd", 13),
    "tüügas": ("Tüügas", 14),
    "tyygas": ("Tüügas", 14),
    "snag": ("Tüügas", 14),
    "lamaoks": ("Lamaoks", 46),
    "oks": ("Lamaoks", 46),
    "elavpuu": ("Elav puu", 16),
    "elav puu": ("Elav puu", 16),
    "kõdupuit": ("Kõdupuit", 41),
    "kodupuit": ("Kõdupuit", 41),
    "muld": ("Muld", 9),
    "pinnas": ("Muld", 9),
    "kõdu": ("Kõdu", 35),
    "kodu": ("Kõdu", 35),
    "okkad": ("Okkad", 29),
    "lehed": ("Lehed", 20)
}

ABUNDANCE_MAP = {
    "üksik": "Üksikud",
    "üksikud": "Üksikud",
    "yksik": "Üksikud",
    "yksikud": "Üksikud",
    "vähe": "Vähe",
    "vahe": "Vähe",
    "mõõdukalt": "Mõõdukalt",
    "moodukalt": "Mõõdukalt",
    "sage": "Sage",
    "palju": "Palju",
    "massiliselt": "Massiliselt",
    "massiline": "Massiliselt"
}


def init_local_db():
    os.makedirs(os.path.dirname(LOCAL_OBS_DB), exist_ok=True)
    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS observations (
        id TEXT PRIMARY KEY,
        taxon_name TEXT,
        taxon_id TEXT,
        vernacular_name TEXT,
        date_time TEXT,
        latitude REAL,
        longitude REAL,
        altitude REAL,
        locality TEXT,
        county TEXT,
        commune TEXT,
        substrate TEXT,
        substrate_type TEXT,
        abundance TEXT,
        remarks TEXT,
        url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS observation_photos (
        sha256 TEXT PRIMARY KEY,
        filename TEXT,
        filepath TEXT,
        observation_id TEXT,
        plutof_file_id TEXT,
        uploaded_at TEXT,
        FOREIGN KEY(observation_id) REFERENCES observations(id)
    );
    """)
    conn.commit()
    conn.close()


def record_observation_locally(obs_data: Dict[str, Any], photos_data: List[Dict[str, Any]]):
    init_local_db()
    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    
    c.execute("""
    INSERT OR REPLACE INTO observations 
    (id, taxon_name, taxon_id, vernacular_name, date_time, latitude, longitude, altitude, locality, county, commune, substrate, substrate_type, abundance, remarks, url, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        obs_data["id"],
        obs_data.get("taxon_name"),
        obs_data.get("taxon_id"),
        obs_data.get("vernacular_name"),
        obs_data.get("date_time"),
        obs_data.get("latitude"),
        obs_data.get("longitude"),
        obs_data.get("altitude"),
        obs_data.get("locality"),
        obs_data.get("county"),
        obs_data.get("commune"),
        obs_data.get("substrate"),
        obs_data.get("substrate_type"),
        obs_data.get("abundance"),
        obs_data.get("remarks"),
        obs_data.get("url"),
        datetime.datetime.now(datetime.timezone.utc).isoformat()
    ))

    for p in photos_data:
        c.execute("""
        INSERT OR REPLACE INTO observation_photos
        (sha256, filename, filepath, observation_id, plutof_file_id, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (
            p["sha256"],
            p["file_name"],
            p["file_path"],
            obs_data["id"],
            p.get("plutof_file_id"),
            datetime.datetime.now(datetime.timezone.utc).isoformat()
        ))

    conn.commit()
    
    # Ekspordi ka JSON
    c.execute("SELECT * FROM observations ORDER BY created_at DESC;")
    cols = [d[0] for d in c.description]
    all_rows = []
    for r in c.fetchall():
        row_dict = dict(zip(cols, r))
        # Pildid
        c.execute("SELECT sha256, filename, plutof_file_id, filepath FROM observation_photos WHERE observation_id = ?;", (row_dict["id"],))
        p_cols = [d[0] for d in c.description]
        row_dict["photos"] = [dict(zip(p_cols, pr)) for pr in c.fetchall()]
        all_rows.append(row_dict)
    
    with open(LOCAL_OBS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, indent=2, ensure_ascii=False)
        
    conn.close()


def check_existing_photo(sha256: str, filename: str = "", date_iso: str = "", lat: float = None, lon: float = None) -> Optional[Dict[str, Any]]:
    """Kontrollib, kas foto SHA-256 räsi, failinimi või täpne EXIF aeg/GPS on juba varem sisestatud."""
    init_local_db()
    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    
    # 1. Kontrolli SHA-256 räsi järgi
    c.execute("""
    SELECT p.sha256, p.filename, p.observation_id, p.uploaded_at, o.taxon_name, o.url
    FROM observation_photos p
    LEFT JOIN observations o ON p.observation_id = o.id
    WHERE p.sha256 = ?;
    """, (sha256,))
    row = c.fetchone()
    if row and row[2]:
        conn.close()
        return {
            "match_reason": "SHA-256 räsi",
            "sha256": row[0],
            "filename": row[1],
            "observation_id": row[2],
            "uploaded_at": row[3],
            "taxon_name": row[4],
            "url": row[5] or f"https://app.plutof.ut.ee/observation/view/{row[2]}"
        }
    
    # 2. Kontrolli failinime järgi (kui failinimi on spetsiifiline nagu PXL_...)
    if filename and not filename.startswith("foto") and not filename.startswith("image"):
        c.execute("""
        SELECT p.sha256, p.filename, p.observation_id, p.uploaded_at, o.taxon_name, o.url
        FROM observation_photos p
        LEFT JOIN observations o ON p.observation_id = o.id
        WHERE p.filename = ? OR p.filepath LIKE ?;
        """, (filename, f"%{filename}"))
        row_fn = c.fetchone()
        if row_fn and row_fn[2]:
            conn.close()
            return {
                "match_reason": "Failinimi",
                "sha256": row_fn[0],
                "filename": row_fn[1],
                "observation_id": row_fn[2],
                "uploaded_at": row_fn[3],
                "taxon_name": row_fn[4],
                "url": row_fn[5] or f"https://app.plutof.ut.ee/observation/view/{row_fn[2]}"
            }

    # 3. Kontrolli täpse EXIF kuupäeva ja koordinaatide järgi
    if date_iso and lat is not None and lon is not None:
        c.execute("""
        SELECT id, taxon_name, date_time, url
        FROM observations
        WHERE (date_time = ? OR date_time LIKE ?) 
          AND ABS(latitude - ?) < 0.00005 
          AND ABS(longitude - ?) < 0.00005;
        """, (date_iso, f"{date_iso[:10]}%", lat, lon))
        row_geo = c.fetchone()
        if row_geo:
            conn.close()
            return {
                "match_reason": "EXIF aeg ja GPS",
                "sha256": sha256,
                "filename": filename,
                "observation_id": row_geo[0],
                "uploaded_at": row_geo[2],
                "taxon_name": row_geo[1],
                "url": row_geo[3] or f"https://app.plutof.ut.ee/observation/view/{row_geo[0]}"
            }

    conn.close()
    
    # 4. Kontrolli ka varasemat räsiregistrit
    reg = load_processed_registry()
    if sha256 in reg:
        return {
            "match_reason": "Räsiregister",
            "sha256": sha256,
            "filename": reg[sha256].get("file_name", "tundmatu"),
            "observation_id": reg[sha256].get("observation_id", "N/A"),
            "uploaded_at": reg[sha256].get("uploaded_at", "N/A"),
            "taxon_name": reg[sha256].get("taxon", "N/A"),
            "url": f"https://app.plutof.ut.ee/observation/view/{reg[sha256].get('observation_id')}"
        }

    return None


def show_my_observations():
    """Kuvab terminalis kõik kasutaja kohalikud seenevaatlused."""
    init_local_db()
    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    c.execute("SELECT id, taxon_name, date_time, locality, county, url FROM observations ORDER BY id DESC;")
    rows = c.fetchall()
    conn.close()

    print("=" * 80)
    print(f" MINU SEENEVAATLUSED PLUTOF-IS (Kokku: {len(rows)} vaatlust)")
    print("=" * 80)
    if not rows:
        print("Vaatlusi pole veel sisestatud.")
    for r in rows:
        print(f"🆔 ID: {r[0]} |  {r[1]}")
        print(f"    {r[3]}, {r[4]} | 🕒 {r[2]}")
        print(f"   🔗 {r[5]}")
        print("-" * 80)


def load_local_taxa_mappings() -> Dict[str, str]:
    mapping = {}
    if os.path.exists(BORIS_REGISTER_FILE):
        try:
            with open(BORIS_REGISTER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for it in data:
                    est = it.get("eestikeelne_nimi", "").strip().lower()
                    lat = it.get("teaduslik_nimi", "").strip()
                    if est and lat:
                        mapping[est] = lat
                        mapping[est.replace("-", " ")] = lat
                        mapping[est.replace(" ", "-")] = lat
                        mapping[est.replace(" ", "")] = lat
                        mapping[est.replace("-", "")] = lat
        except Exception:
            pass

    if os.path.exists(PHOTOS_TAXA_DB):
        try:
            conn = sqlite3.connect(f"file:{PHOTOS_TAXA_DB}?mode=ro", uri=True)
            c = conn.cursor()
            c.execute("SELECT estonian_name, latin_name FROM taxa WHERE kingdom = 'Fungi' AND estonian_name IS NOT NULL AND latin_name IS NOT NULL;")
            for est_n, lat_n in c.fetchall():
                est = est_n.strip().lower()
                lat = lat_n.strip()
                if est and lat:
                    mapping[est] = lat
                    mapping[est.replace("-", " ")] = lat
                    mapping[est.replace(" ", "-")] = lat
                    mapping[est.replace(" ", "")] = lat
                    mapping[est.replace("-", "")] = lat
            conn.close()
        except Exception:
            pass

    return mapping


def load_credentials() -> Dict[str, str]:
    creds = {}
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip().strip("\"'")
    return creds


def get_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_processed_registry() -> Dict[str, Any]:
    if os.path.exists(PROCESSED_REGISTRY_FILE):
        try:
            with open(PROCESSED_REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_processed_registry(registry: Dict[str, Any]):
    with open(PROCESSED_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def get_decimal_from_dms(dms, ref: str) -> Optional[float]:
    try:
        deg = float(dms[0])
        minutes = float(dms[1])
        sec = float(dms[2])
        if math.isnan(deg) or math.isnan(minutes) or math.isnan(sec):
            return None
        dec = deg + minutes / 60.0 + sec / 3600.0
        if ref in ["S", "W"]:
            dec = -dec
        return dec
    except Exception:
        return None


def extract_exif(image_path: str) -> Dict[str, Any]:
    result = {
        "file_name": os.path.basename(image_path),
        "file_path": os.path.abspath(image_path),
        "sha256": get_sha256(image_path),
        "date_time": None,
        "date_iso": None,
        "lat": None,
        "lon": None,
        "altitude": None,
        "camera": None
    }
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        if not exif:
            return result

        labeled = {}
        gps_info = {}
        for tag_id, val in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            labeled[tag] = val
            if tag == "GPSInfo":
                for k, v in val.items():
                    sub_tag = GPSTAGS.get(k, k)
                    gps_info[sub_tag] = v

        result["camera"] = f"{labeled.get('Make', '')} {labeled.get('Model', '')}".strip()

        dt_str = labeled.get("DateTimeOriginal") or labeled.get("DateTime")
        if dt_str:
            result["date_time"] = dt_str
            try:
                dt = datetime.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                result["date_iso"] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                result["date_iso"] = dt_str

        if gps_info:
            lat_dms = gps_info.get("GPSLatitude")
            lat_ref = gps_info.get("GPSLatitudeRef", "N")
            lon_dms = gps_info.get("GPSLongitude")
            lon_ref = gps_info.get("GPSLongitudeRef", "E")
            alt = gps_info.get("GPSAltitude")

            if lat_dms and lon_dms:
                lat = get_decimal_from_dms(lat_dms, lat_ref)
                lon = get_decimal_from_dms(lon_dms, lon_ref)
                if lat is not None and lon is not None:
                    result["lat"] = round(lat, 8)
                    result["lon"] = round(lon, 8)

            if alt is not None:
                try:
                    alt_val = float(alt)
                    if not math.isnan(alt_val):
                        result["altitude"] = round(alt_val, 1)
                except Exception:
                    pass

    except Exception as e:
        print(f"  Viga faili {image_path} lugemisel: {e}", file=sys.stderr)

    return result


def reverse_geocode(lat: float, lon: float) -> Dict[str, str]:
    cache_key = f"{round(lat, 4)}_{round(lon, 4)}"
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    if cache_key in cache:
        return cache[cache_key]

    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"}
    )

    geo_data = {
        "country": "Eesti",
        "country_code": "ee",
        "county": "",
        "municipality": "",
        "locality": "",
        "full_area_name": ""
    }

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            addr = data.get("address", {})

            country = addr.get("country", "Eesti")
            county = addr.get("county", addr.get("state", ""))
            municipality = addr.get("municipality", addr.get("city", addr.get("town", "")))
            
            locality = (
                addr.get("village") or
                addr.get("hamlet") or
                addr.get("city_district") or
                addr.get("suburb") or
                addr.get("road") or
                ""
            )
            if locality and not (locality.endswith("küla") or locality.endswith("linn") or locality.endswith("alevik")):
                if addr.get("hamlet") or addr.get("village"):
                    locality += " küla"

            geo_data["country"] = country
            geo_data["country_code"] = addr.get("country_code", "ee")
            geo_data["county"] = county
            geo_data["municipality"] = municipality
            geo_data["locality"] = locality

            parts = [p for p in [country, county, municipality] if p]
            geo_data["full_area_name"] = ", ".join(parts)

            cache[cache_key] = geo_data
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    except Exception as e:
        print(f"Hoiatus: Pöörd-geokodeerimine ebaõnnestus ({e}).", file=sys.stderr)

    return geo_data


def fetch_plutof_taxon_info(taxon_query: str) -> Dict[str, Any]:
    raw_query = taxon_query.strip()
    norm_query = raw_query.lower()
    
    local_taxa = load_local_taxa_mappings()
    scientific_search = local_taxa.get(norm_query) or local_taxa.get(norm_query.replace("-", " ")) or raw_query

    taxa_cache = {}
    if os.path.exists(TAXA_CACHE_FILE):
        try:
            with open(TAXA_CACHE_FILE, "r", encoding="utf-8") as f:
                taxa_cache = json.load(f)
        except Exception:
            taxa_cache = {}

    if scientific_search in taxa_cache:
        return taxa_cache[scientific_search]
    if raw_query in taxa_cache:
        return taxa_cache[raw_query]

    taxon_info = {
        "search_name": raw_query,
        "taxon_name": scientific_search,
        "full_name": scientific_search,
        "rank": "Liik",
        "taxon_id": None,
        "vernacular_name": "",
        "kingdom": "Fungi"
    }

    urls_to_try = [
        f"https://api.plutof.ut.ee/v1/public/taxa/autocomplete/?q={urllib.parse.quote(raw_query)}",
        f"https://api.plutof.ut.ee/v1/public/taxa/autocomplete/?name={urllib.parse.quote(scientific_search)}",
        f"https://api.plutof.ut.ee/v1/public/taxa/autocomplete/?name={urllib.parse.quote(raw_query)}"
    ]

    for url in urls_to_try:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("data", [])
                if items:
                    def sort_key(it):
                        at = it.get("attributes", {})
                        rank_score = 0 if at.get("taxon_rank") == "Species" else 1
                        syn_score = 1 if at.get("is_synonym") else 0
                        vern_score = 0 if at.get("vernacular_name", "").lower() == norm_query else 1
                        return (rank_score, syn_score, vern_score)
                    
                    sorted_items = sorted(items, key=sort_key)
                    match = sorted_items[0]
                    attrs = match.get("attributes", {})
                    taxon_info["taxon_id"] = match.get("id")
                    taxon_info["full_name"] = attrs.get("name", raw_query)
                    taxon_info["taxon_name"] = attrs.get("taxon_name", raw_query)
                    taxon_info["rank"] = "Liik" if attrs.get("taxon_rank") == "Species" else attrs.get("taxon_rank", "Liik")
                    taxon_info["vernacular_name"] = attrs.get("vernacular_name", "")
                    
                    taxa_cache[raw_query] = taxon_info
                    taxa_cache[scientific_search] = taxon_info
                    with open(TAXA_CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(taxa_cache, f, ensure_ascii=False, indent=2)
                    break
        except Exception as e:
            print(f"Hoiatus: Taksoni päring ebaõnnestus ({e}).", file=sys.stderr)

    return taxon_info


def get_plutof_token(creds: Dict[str, str]) -> str:
    ep = "https://api.plutof.ut.ee/v1/public/auth/token/"
    payload = {
        "grant_type": "password",
        "client_id": creds["PLUTOF_CLIENT_ID"],
        "client_secret": creds["PLUTOF_CLIENT_SECRET"],
        "username": creds["PLUTOF_USERNAME"],
        "password": creds["PLUTOF_PASSWORD"]
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(ep, data=data, headers={"User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["access_token"]


def get_user_person_id(token: str) -> str:
    url = "https://api.plutof.ut.ee/v1/public/user-profile/"
    req = urllib.request.Request(url, headers={
        "User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)",
        "Authorization": f"Bearer {token}"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return str(data["data"]["relationships"]["person"]["data"]["id"])


def get_country_id(country_name: str, token: str) -> str:
    if country_name.lower() in ["eesti", "estonia"]:
        return "47"
    url = f"https://api.plutof.ut.ee/v1/public/countries/autocomplete/?name={urllib.parse.quote(country_name)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)",
        "Authorization": f"Bearer {token}"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("data"):
                return str(data["data"][0]["id"])
    except Exception:
        pass
    return "47"


def move_to_trash(filepath: str) -> bool:
    """Liigutab faili turvaliselt macOS Prügikasti (Trash)."""
    try:
        abs_path = os.path.abspath(filepath)
        cmd = f'tell application "Finder" to delete POSIX file "{abs_path}"'
        import subprocess
        subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)
        return True
    except Exception:
        try:
            trash_dir = os.path.expanduser("~/.Trash")
            dest = os.path.join(trash_dir, os.path.basename(filepath))
            if os.path.exists(dest):
                base, ext = os.path.splitext(os.path.basename(filepath))
                dest = os.path.join(trash_dir, f"{base}_{int(datetime.datetime.now().timestamp())}{ext}")
            os.rename(filepath, dest)
            return True
        except Exception as e:
            print(f"  Hoiatus: Ei saanud faili prügikasti liigutada: {e}", file=sys.stderr)
            return False


def upload_file_to_plutof(filepath: str, token: str) -> str:
    boundary = uuid.uuid4().hex
    content_type = f"multipart/form-data; boundary={boundary}"

    body = []
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="upload"; filename="{os.path.basename(filepath)}"'.encode())
    body.append(b"Content-Type: image/jpeg\r\n")
    with open(filepath, "rb") as f:
        body.append(f.read())

    body.append(f"--{boundary}".encode())
    body.append(b'Content-Disposition: form-data; name="is_public"\r\n')
    body.append(b"true")

    body.append(f"--{boundary}--".encode())
    body.append(b"")

    payload_bytes = b"\r\n".join(body)

    url = "https://api.plutof.ut.ee/v1/public/files/"
    req = urllib.request.Request(url, data=payload_bytes, headers={
        "User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)",
        "Authorization": f"Bearer {token}",
        "Content-Type": content_type
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return str(res["data"]["id"])
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_body)
            for err in err_json.get("errors", []):
                if "already have a file" in err.get("message", "").lower() and err.get("id"):
                    return str(err["id"])
        except Exception:
            pass
        raise RuntimeError(f"Faili üleslaadimine ebaõnnestus ({e.code}): {err_body}")


def parse_cli_args(args_list: List[str]) -> Tuple[str, List[str], Dict[str, Any]]:
    files = []
    flags = {
        "substraat_nimi": "",
        "substraat_taxon_id": None,
        "tüüp_nimi": "",
        "tüüp_id": None,
        "ohtrus": "",
        "märkus": "",
        "force": False
    }
    taxon_words = []

    valid_exts = (".jpg", ".jpeg", ".heic", ".png", ".webp", ".zip")

    for arg in args_list:
        arg_clean = arg.strip("\"'")
        if arg_clean == "--force":
            flags["force"] = True
            continue
        if arg_clean in ["--keep", "-k", "keep"]:
            flags["keep"] = True
            continue

        if os.path.isfile(arg_clean) or arg_clean.lower().endswith(valid_exts) or ("/" in arg_clean and os.path.exists(arg_clean)):
            if os.path.exists(arg_clean):
                files.append(arg_clean)
            continue

        lower_arg = arg_clean.lower()
        if any(lower_arg.startswith(prefix) for prefix in ["substraat:", "sub:", "subst:"]):
            val = arg_clean.split(":", 1)[1].strip()
            mapped = SUBSTRATE_MAP.get(val.lower())
            if mapped:
                flags["substraat_nimi"] = mapped[0]
                flags["substraat_taxon_id"] = mapped[1]
            else:
                flags["substraat_nimi"] = val
        elif any(lower_arg.startswith(prefix) for prefix in ["tüüp:", "tyyp:", "type:"]):
            val = arg_clean.split(":", 1)[1].strip()
            mapped = TYPE_MAP.get(val.lower())
            if mapped:
                flags["tüüp_nimi"] = mapped[0]
                flags["tüüp_id"] = mapped[1]
            else:
                flags["tüüp_nimi"] = val
        elif any(lower_arg.startswith(prefix) for prefix in ["ohtrus:", "oht:", "abund:"]):
            val = arg_clean.split(":", 1)[1].strip()
            flags["ohtrus"] = ABUNDANCE_MAP.get(val.lower(), val)
        elif any(lower_arg.startswith(prefix) for prefix in ["märkus:", "markus:", "märkused:", "note:", "notes:"]):
            val = arg_clean.split(":", 1)[1].strip()
            flags["märkus"] = val
        else:
            taxon_words.append(arg_clean)

    taxon_name = " ".join(taxon_words).strip()
    return taxon_name, files, flags


def show_options_table():
    print("""
================================================================================
 PLUTOF SEENEVAATLUSE VALIKUD JA PARAMEETRID
================================================================================

 1. SUBSTRAAT (sub: või substraat:)
--------------------------------------------------------------------------------
  kuusk       -> Picea abies (L.) H.Karst. (Harilik kuusk)
  mänd        -> Pinus sylvestris L. (Harilik mänd)
  kask        -> Betula pendula Roth (Arukask)
  sookask     -> Betula pubescens Ehrh. (Sookask)
  haab        -> Populus tremula L. (Harilik haab)
  lepp        -> Alnus incana (L.) Moench (Hall lepp)
  sanglepp    -> Alnus glutinosa (L.) Gaertn. (Sanglepp / must lepp)
  tamm        -> Quercus robur L. (Harilik tamm)
  saar        -> Fraxinus excelsior L. (Harilik saar)
  vaher       -> Acer platanoides L. (Harilik vaher)
  sarapuu     -> Corylus avellana L. (Harilik sarapuu)
  pärn        -> Tilia cordata Mill. (Harilik pärn)

 2. SUBSTRAADI TÜÜP (tyyp: või tüüp:)
--------------------------------------------------------------------------------
  lamatüvi    -> Log (Mahakukkunud tüvi / lamapuu) [PlutoF ID: 15]
  känd        -> Stump (Puukänd) [PlutoF ID: 13]
  tüügas      -> Snag (Püstine kuivanud tüvi) [PlutoF ID: 14]
  lamaoks     -> Dead lying branch (Mahakukkunud lamaoks) [PlutoF ID: 46]
  elavpuu     -> Living tree (Elav kasvav puu) [PlutoF ID: 16]
  kõdupuit    -> Decayed wood (Tugevasti kõdunenud puit) [PlutoF ID: 41]
  kõdu        -> Litter (Metsakõdu / varis) [PlutoF ID: 35]
  okkad       -> Coniferous needles (Okkavaris) [PlutoF ID: 29]
  lehed       -> Deciduous leaves (Lehevaris) [PlutoF ID: 20]
  muld        -> Mineral soil (Metsamuld / mineraalpinnas) [PlutoF ID: 9]

 3. OHTRUS (ohtrus: või oht:)
--------------------------------------------------------------------------------
  üksikud     -> Üksikud viljakehad (1–3 tk)
  vähe        -> Vähe (mõned eksemplarid)
  mõõdukalt   -> Mõõdukalt (tavaline leiukoht)
  sage        -> Sage (arvukalt viljakehi)
  palju       -> Palju (suurem kogumik)
  massiliselt -> Massiliselt (ulatuslik esinemine)

 4. MÄRKUS (märkus:)
--------------------------------------------------------------------------------
  märkus:tekst -> Vabatekstiline märkus või vaatluse detailid

 5. SÜNKROON JA VAATLUSED
--------------------------------------------------------------------------------
  seen --sync  -> Tõmbab kõik PlutoF vaatlused kohalikku andmebaasi

 NÄITED:
  seen tumepruun-taelik /tee/foto.jpg sub:kuusk tyyp:lamatüvi ohtrus:üksikud
  seen "roosa pess" /tee/foto1.jpg /tee/foto2.jpg sub:kuusk tyyp:lamatüvi
================================================================================
""")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "--options", "options", "abi", "--abi"]:
        show_options_table()
        return

    if "--sync" in sys.argv or "sync" in sys.argv:
        print(" Sünkroonin PlutoF vaatlusi...")
        sync_all_my_observations()
        return

    if any(arg in sys.argv for arg in ["--list", "list", "--vaatlused", "vaatlused"]):
        show_my_observations()
        return

    if "--auth-google" in sys.argv or "--google-auth" in sys.argv:
        sys.path.insert(0, "/Users/metrobee/GEMINI/scripts")
        import google_photos_sync
        google_photos_sync.get_authenticated_service()
        return

    taxon_name, file_paths, flags = parse_cli_args(sys.argv[1:])

    if not file_paths:
        print(" Viga: Palun lohista terminali vähemalt üks foto!", file=sys.stderr)
        return

    if not taxon_name:
        print(" Viga: Palun määra seeneliik (eesti või ladina keeles)!", file=sys.stderr)
        return

    # 0. Paki lahti ZIP failid, kui kasutaja lohistas .zip arhiivi
    original_files_to_trash = list(file_paths)
    resolved_photo_paths = []
    import zipfile, tempfile

    img_extensions = (".jpg", ".jpeg", ".heic", ".png", ".webp")

    for fp in file_paths:
        if fp.lower().endswith(".zip") and zipfile.is_zipfile(fp):
            temp_dir = tempfile.mkdtemp(prefix="seen_zip_")
            try:
                with zipfile.ZipFile(fp, 'r') as z:
                    z.extractall(temp_dir)
                # Otsi pildifailid rekursiivselt
                extracted_imgs = []
                for root, _, fnames in os.walk(temp_dir):
                    for fn in sorted(fnames):
                        if fn.lower().endswith(img_extensions) and not fn.startswith("._") and not fn.startswith("."):
                            extracted_imgs.append(os.path.join(root, fn))
                if extracted_imgs:
                    print(f" Arhiivist '{os.path.basename(fp)}' leitud {len(extracted_imgs)} fotot.")
                    resolved_photo_paths.extend(extracted_imgs)
                else:
                    print(f"  Arhiivist '{os.path.basename(fp)}' ei leitud ühtegi toetatud pildifaili!", file=sys.stderr)
            except Exception as e:
                print(f"  Viga ZIP arhiivi lahtipakkimisel ({fp}): {e}", file=sys.stderr)
        else:
            resolved_photo_paths.append(fp)

    if not resolved_photo_paths:
        print(" Viga: Töötlemiseks ei leitud ühtegi pildifaili!", file=sys.stderr)
        return

    # 1. RANGE DUPLIKAATIDE KONTROLL (SHA-256 + Failinimi + EXIF)
    for fp in resolved_photo_paths:
        file_sha = get_sha256(fp)
        fn = os.path.basename(fp)
        existing = check_existing_photo(file_sha, filename=fn)
        if existing and not flags.get("force"):
            print("=" * 80, file=sys.stderr)
            print(f" DUPLIKAADI HOIATUS JA BLOKEERING! (Alus: {existing.get('match_reason', 'Räsi')})", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            print(f"Foto '{fn}' on juba varem sisestatud PlutoF vaatlusena!", file=sys.stderr)
            print(f"🆔 Varasem vaatlus ID: {existing['observation_id']}", file=sys.stderr)
            print(f" Varasem takson: {existing.get('taxon_name')}", file=sys.stderr)
            print(f"🔗 Vaatluse link: {existing['url']}", file=sys.stderr)
            print(f"🕒 Sisestatud: {existing.get('uploaded_at')}", file=sys.stderr)
            print("-" * 80, file=sys.stderr)
            print("Ükski foto ei tohi olla mitmes vaatluses. Toiming peatati!", file=sys.stderr)
            print("(Kui soovid seda siiski teadlikult uuesti saata, lisa parameeter --force)", file=sys.stderr)
            print("=" * 80, file=sys.stderr)
            sys.exit(1)

    creds = load_credentials()
    if not creds.get("PLUTOF_USERNAME") or not creds.get("PLUTOF_PASSWORD"):
        print(" Viga: PlutoF volitused puuduvad failis ~/.plutof_env", file=sys.stderr)
        return

    print("=" * 80)
    print(f" SEENEVAATLUSE SISESTAMINE")
    print("=" * 80)
    print(f" Otsitav takson: {taxon_name}")
    if flags["substraat_nimi"]:
        print(f" Substraat: {flags['substraat_nimi']}")
    if flags["tüüp_nimi"]:
        print(f" Tüüp: {flags['tüüp_nimi']}")
    if flags["ohtrus"]:
        print(f" Ohtrus: {flags['ohtrus']}")
    if flags["märkus"]:
        print(f" Märkus: {flags['märkus']}")
    print(f" Fotosid kokku: {len(resolved_photo_paths)}")
    print("-" * 80)

    # 2. Taksoni info
    taxon_info = fetch_plutof_taxon_info(taxon_name)
    if not taxon_info.get("taxon_id"):
        print(f" Viga: PlutoF registrist ei leitud taksonit '{taxon_name}'!", file=sys.stderr)
        print(" Kontrolli liiginime õigekirja või kasuta ladinakeelset nime.", file=sys.stderr)
        return

    print(f" PlutoF takson: {taxon_info['full_name']} (ID: {taxon_info['taxon_id']})")

    # 3. Piltide EXIF
    items = []
    last_valid_gps = None
    for fp in resolved_photo_paths:
        info = extract_exif(fp)
        if (info["lat"] is None or info["lon"] is None) and last_valid_gps:
            info["lat"] = last_valid_gps["lat"]
            info["lon"] = last_valid_gps["lon"]
            info["altitude"] = last_valid_gps.get("altitude")
            info["gps_inherited"] = True
        elif info["lat"] is not None and info["lon"] is not None:
            last_valid_gps = {"lat": info["lat"], "lon": info["lon"], "altitude": info.get("altitude")}
            info["gps_inherited"] = False

        if info["lat"] is not None and info["lon"] is not None:
            geo = reverse_geocode(info["lat"], info["lon"])
            info.update(geo)
            info["wkt_point"] = f"SRID=4326;POINT ({info['lon']} {info['lat']})"

        items.append(info)

    primary = items[0]
    if primary.get("lat") and primary.get("lon"):
        print(f" Asukoht: {primary.get('full_area_name')} ({primary.get('locality')})")
        print(f" Koordinaadid: {primary.get('lat')}, {primary.get('lon')} (Aeg: {primary.get('date_time')})")
    else:
        print("  Hoiatus: Fotost ei leitud GPS koordinaate!")

    # 4. Autentimine ja üleslaadimine
    print(" Sünkroonin fotosid ja saadan vaatluse PlutoF API-sse...")
    token = get_plutof_token(creds)
    person_id = get_user_person_id(token)
    country_id = get_country_id(primary.get("country", "Eesti"), token)

    uploaded_file_ids = []
    for idx, it in enumerate(items, 1):
        print(f"   [{idx}/{len(items)}] Pilt: {it['file_name']} ...", end="", flush=True)
        fid = upload_file_to_plutof(it["file_path"], token)
        uploaded_file_ids.append(fid)
        it["plutof_file_id"] = fid
        print(f" Valmis (ID: {fid})")

    # 5. Vaatluse moodustamine
    raw_dt = primary.get("date_time", "")
    if raw_dt and " " in raw_dt:
        d_part, t_part = raw_dt.split(" ", 1)
        timespan_begin = f"{d_part.replace(':', '-')}"
    elif primary.get("date_iso"):
        timespan_begin = primary["date_iso"].split("T")[0]
    else:
        timespan_begin = datetime.datetime.now().strftime("%Y-%m-%d")

    # Koosta märkused
    remarks_parts = []
    if flags["ohtrus"]:
        remarks_parts.append(f"Ohtrus: {flags['ohtrus']}")
    if flags["substraat_nimi"] or flags["tüüp_nimi"]:
        sub_desc = []
        if flags["substraat_nimi"]:
            sub_desc.append(flags["substraat_nimi"])
        if flags["tüüp_nimi"]:
            sub_desc.append(flags["tüüp_nimi"])
        remarks_parts.append(f"Substraat: {', '.join(sub_desc)}")
    if flags["märkus"]:
        remarks_parts.append(flags["märkus"])

    full_remarks = " | ".join(remarks_parts)

    substrate_obj = {}
    if flags["tüüp_id"]:
        substrate_obj["substrate_type"] = flags["tüüp_id"]

    # Tunnused ja mõõtmised (Measurements)
    # Form 72: Measurement 93 = Ohtrus, Measurement 135 = Asustusviis (382 = Looduses)
    ABUNDANCE_CHOICE_MAP = {
        "üksikud": 233, "üksik": 233, "yksikud": 233, "yksik": 233, "solitary": 233,
        "harva": 234, "vähe": 234, "vahe": 234, "rare": 234,
        "sage": 235, "mõõdukalt": 235, "moodukalt": 235, "frequent": 235,
        "ohtralt": 236, "palju": 236, "common": 236,
        "väga ohtralt": 237, "vaga ohtralt": 237, "massiliselt": 237, "massiline": 237, "abundant": 237
    }
    
    measurements_list = [
        {"measurement": 135, "value": "382"}  # Looduses / In wild
    ]
    if flags["ohtrus"]:
        choice_id = ABUNDANCE_CHOICE_MAP.get(flags["ohtrus"].lower())
        if choice_id:
            measurements_list.append({"measurement": 93, "value": str(choice_id)})

    obs_attrs = {
        "is_public": True,
        "timespan_begin": timespan_begin,
        "timespan_begin_format": "YYYY-MM-DD",
        "locality_text": primary.get("locality", ""),
        "district": primary.get("county", ""),
        "commune": primary.get("municipality", ""),
        "geom": primary.get("wkt_point", ""),
        "remarks": full_remarks,
        "measurements": measurements_list
    }
    if substrate_obj:
        obs_attrs["substrate"] = substrate_obj

    obs_rels = {
        "mainform": {
            "data": {"type": "Form", "id": "72"}
        },
        "taxon_node": {
            "data": {"type": "Taxon", "id": str(taxon_info["taxon_id"])}
        },
        "country": {
            "data": {"type": "Country", "id": country_id}
        },
        "collected_by": {
            "data": [{"type": "Person", "id": person_id}]
        },
        "files": {
            "data": [{"type": "File", "id": fid} for fid in uploaded_file_ids]
        }
    }
    if flags.get("substraat_taxon_id"):
        obs_rels["substrate_taxon"] = {
            "data": {"type": "Taxon", "id": str(flags["substraat_taxon_id"])}
        }

    obs_payload = {
        "data": {
            "type": "Observation",
            "attributes": obs_attrs,
            "relationships": obs_rels
        }
    }

    if flags["substraat_taxon_id"]:
        obs_payload["data"]["relationships"]["substrate_taxon"] = {
            "data": {"type": "Taxon", "id": str(flags["substraat_taxon_id"])}
        }

    req_obs = urllib.request.Request(
        "https://api.plutof.ut.ee/v1/public/observations/",
        data=json.dumps(obs_payload).encode("utf-8"),
        headers={
            "User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }
    )

    try:
        with urllib.request.urlopen(req_obs, timeout=20) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            obs_id = str(res.get("data", {}).get("id"))
    except urllib.error.HTTPError as e:
        err_b = e.read().decode("utf-8", errors="ignore")
        print(f" PlutoF API viga ({e.code}): {err_b}", file=sys.stderr)
        return

    # 6. Salvesta vaatlus ja piltide räsid reaalajas kohalikku andmebaasi
    obs_record = {
        "id": obs_id,
        "taxon_name": taxon_info["full_name"],
        "taxon_id": str(taxon_info["taxon_id"]),
        "vernacular_name": taxon_info.get("vernacular_name", ""),
        "date_time": timespan_begin,
        "latitude": primary.get("lat"),
        "longitude": primary.get("lon"),
        "altitude": primary.get("altitude"),
        "locality": primary.get("locality"),
        "county": primary.get("county"),
        "commune": primary.get("municipality"),
        "substrate": flags["substraat_nimi"],
        "substrate_type": flags["tüüp_nimi"],
        "abundance": flags["ohtrus"],
        "remarks": full_remarks,
        "url": f"https://app.plutof.ut.ee/observation/view/{obs_id}"
    }
    
    record_observation_locally(obs_record, items)

    # 7. Google Photos albumisse lisamine (' PlutoF Vaatlused')
    if os.path.exists(os.path.expanduser("~/.google_photos_token.json")):
        try:
            sys.path.insert(0, "/Users/metrobee/GEMINI/scripts")
            from google_photos_sync import sync_observation_to_google_photos
            sync_observation_to_google_photos(resolved_photo_paths, obs_id, taxon_info["full_name"])
        except Exception as e:
            pass

    # 8. Liiguta töödeldud pildifailid või ZIP arhiiv turvaliselt prügikasti (Trash)
    if not flags.get("keep"):
        for fp in original_files_to_trash:
            if fp and os.path.exists(fp):
                if move_to_trash(fp):
                    print(f"  '{os.path.basename(fp)}' liigutati prügikasti (Downloads kaust on puhas).")

    print("=" * 80)
    print(f" VAATLUS EDUKALT SALVESTATUD PLUTOF / E-ELURIKKUSE ANDMEBAASI!")
    print(f"🆔 PlutoF ID: {obs_id}")
    print(f"🔗 Vaatluse link: https://app.plutof.ut.ee/observation/view/{obs_id}")
    print(f"💾 Salvestatud kohalikku andmebaasi: {LOCAL_OBS_DB}")
    print("=" * 80)


if __name__ == "__main__":
    main()
