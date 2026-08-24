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

CO_OBSERVERS_MAP = {
    "aa": ("Allar Antson", "81490"),
    "allar": ("Allar Antson", "81490"),
    "antson": ("Allar Antson", "81490"),
    "allar antson": ("Allar Antson", "81490"),
    "iz": ("Irma Zettur", "43966"),
    "irma": ("Irma Zettur", "43966"),
    "zettur": ("Irma Zettur", "43966"),
    "irma zettur": ("Irma Zettur", "43966"),
    "pl": ("Piret Lõhmus", "307"),
    "piret": ("Piret Lõhmus", "307"),
    "lõhmus": ("Piret Lõhmus", "307"),
    "lohmus": ("Piret Lõhmus", "307"),
    "piret lõhmus": ("Piret Lõhmus", "307"),
    "piret lohmus": ("Piret Lõhmus", "307"),
    "alm": ("Anne-Liia Maido", "74936"),
    "am": ("Anne-Liia Maido", "74936"),
    "anneliia": ("Anne-Liia Maido", "74936"),
    "maido": ("Anne-Liia Maido", "74936"),
    "anne-liia maido": ("Anne-Liia Maido", "74936"),
    "tt": ("Taavi Tatsi", "73640"),
    "taavi": ("Taavi Tatsi", "73640"),
    "tatsi": ("Taavi Tatsi", "73640"),
    "taavi tatsi": ("Taavi Tatsi", "73640"),
    "tv": ("Triin Varvas", "44416"),
    "triin": ("Triin Varvas", "44416"),
    "varvas": ("Triin Varvas", "44416"),
    "triin varvas": ("Triin Varvas", "44416"),
    "mp": ("Margit Päkk", "54665"),
    "margit": ("Margit Päkk", "54665"),
    "päkk": ("Margit Päkk", "54665"),
    "pakk": ("Margit Päkk", "54665"),
    "margit päkk": ("Margit Päkk", "54665"),
    "margit pakk": ("Margit Päkk", "54665"),
    "kp": ("Kadri Pärtel", "255"),
    "kadri": ("Kadri Pärtel", "255"),
    "pärtel": ("Kadri Pärtel", "255"),
    "partel": ("Kadri Pärtel", "255"),
    "kadri pärtel": ("Kadri Pärtel", "255"),
    "kadri partel": ("Kadri Pärtel", "255"),
    "is": ("Irja Saar", "253"),
    "irja": ("Irja Saar", "253"),
    "saar": ("Irja Saar", "253"),
    "irja saar": ("Irja Saar", "253"),
    "vl": ("Vello Liiv", "19681"),
    "vello": ("Vello Liiv", "19681"),
    "liiv": ("Vello Liiv", "19681"),
    "vello liiv": ("Vello Liiv", "19681")
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
        google_photos_media_id TEXT,
        FOREIGN KEY(observation_id) REFERENCES observations(id)
    );
    """)
    try:
        conn.execute("ALTER TABLE observation_photos ADD COLUMN google_photos_media_id TEXT;")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE observations ADD COLUMN determiner TEXT;")
    except Exception:
        pass
    conn.commit()
    conn.close()


def record_observation_locally(obs_data: Dict[str, Any], photos_data: List[Dict[str, Any]]):
    init_local_db()
    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    
    c.execute("""
    INSERT OR REPLACE INTO observations 
    (id, taxon_name, taxon_id, vernacular_name, date_time, latitude, longitude, altitude, locality, county, commune, substrate, substrate_type, abundance, remarks, url, created_at, collectors, primary_observer, is_co_observer, determiner)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
        datetime.datetime.now(datetime.timezone.utc).isoformat(),
        obs_data.get("collectors", "Boris Meldre"),
        "Boris Meldre",
        0,
        obs_data.get("determiner", "Boris Meldre")
    ))

    for p in photos_data:
        c.execute("""
        INSERT OR REPLACE INTO observation_photos
        (sha256, filename, filepath, observation_id, plutof_file_id, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """, (
            p["sha256"],
            p["file_name"],
            p.get("s3_url") or p["file_path"],
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

    # Reaalajas varukoopia Google Drive'i
    try:
        import shutil
        gdrive_candidates = [
            os.path.expanduser("~/Library/CloudStorage/GoogleDrive-borismeldre@gmail.com/Minu ketas"),
            os.path.expanduser("~/Library/CloudStorage/GoogleDrive-borismeldre@gmail.com/My Drive")
        ]
        gdrive_base = next((p for p in gdrive_candidates if os.path.exists(p)), None)
        if gdrive_base:
            backup_dir = os.path.join(gdrive_base, "PlutoF_Backup")
            os.makedirs(backup_dir, exist_ok=True)
            if os.path.exists(LOCAL_OBS_DB):
                shutil.copy2(LOCAL_OBS_DB, os.path.join(backup_dir, "plutof_vaatlused.db"))
            if os.path.exists(LOCAL_OBS_JSON):
                shutil.copy2(LOCAL_OBS_JSON, os.path.join(backup_dir, "plutof_vaatlused.json"))
    except Exception:
        pass

    # Värskenda veebidashboardi andmestikku ja juuruta pilve
    try:
        import subprocess
        exp_script = "/Users/metrobee/Projects/fungib/scripts/export_dashboard_data.py"
        if os.path.exists(exp_script):
            subprocess.run([sys.executable, exp_script], capture_output=True)
            # Taustal Firebase Hosting juurutus (ei blokeeri terminali)
            subprocess.Popen(["firebase", "deploy", "--only", "hosting"], cwd="/Users/metrobee/Projects/fungib", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


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
    import re, unicodedata
    mapping = {
        "kimp metskõrges": "Connopus acervatus",
        "kimp-metskõrges": "Connopus acervatus",
        "kimpkõrges": "Connopus acervatus",
        "kimp-kõrges": "Connopus acervatus",
        "kimp kõrges": "Connopus acervatus",
        "puidu-sametkõrges": "Flammulina velutipes",
        "puidu sametkõrges": "Flammulina velutipes",
        "sametkõrges": "Flammulina velutipes",
        "kivipuravik": "Boletus edulis",
        "männitaelik": "Porodaedalea pini",
        "männi-taelik": "Porodaedalea pini",
        "mannitaelik": "Porodaedalea pini",
        "cordiceps militaris": "Cordyceps militaris",
        "cordiceps": "Cordyceps",
        "cordyceps militaris": "Cordyceps militaris",
        "harilik kedristõlvik": "Cordyceps militaris",
        "kedristõlvik": "Cordyceps",
        "hiirheinik": "Tricholoma virgatum",
        "hiir-heinik": "Tricholoma virgatum",
    }

    # 1. ClipSnippet laiendused
    clipsnip_file = os.path.expanduser("~/.clipsnippet_snippets.json")
    if os.path.exists(clipsnip_file):
        try:
            with open(clipsnip_file, "r", encoding="utf-8") as f:
                snips = json.load(f)
                for k, val in snips.get("Seened", {}).items():
                    val_norm = unicodedata.normalize("NFC", val)
                    m_lat = re.search(r'\((.*?)\)', val_norm)
                    if m_lat:
                        lat_n = m_lat.group(1).strip()
                        est_n = re.sub(r'\(.*?\)', '', val_norm).strip().lower()
                        if est_n and lat_n:
                            for variant in [est_n, est_n.replace("-", " "), est_n.replace(" ", "-"), k.lstrip(":").replace("-", " "), k.lstrip(":")]:
                                variant_norm = unicodedata.normalize("NFC", variant).lower()
                                mapping[variant_norm] = lat_n
        except Exception:
            pass

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

    PROPOSED_TAXA_FILE = "/Users/metrobee/GEMINI/data/pakutud_seeninimed.json"
    if os.path.exists(PROPOSED_TAXA_FILE):
        try:
            with open(PROPOSED_TAXA_FILE, "r", encoding="utf-8") as f:
                p_data = json.load(f)
                for it in p_data:
                    est = it.get("pakutud_nimi", "").strip().lower()
                    lat = it.get("teaduslik_nimi", "").strip()
                    if est and lat:
                        mapping[est] = lat
                        mapping[est.replace("-", " ")] = lat
                        mapping[est.replace(" ", "-")] = lat
                        mapping[est.replace(" ", "")] = lat
                        mapping[est.replace("-", "")] = lat
        except Exception:
            pass

    # Autoriiteetsed ülekaalukad vastavused (uuendatud taksonoomia)
    overrides = {
        "kimp metskõrges": "Connopus acervatus",
        "kimp-metskõrges": "Connopus acervatus",
        "kimpkõrges": "Connopus acervatus",
        "kimp-kõrges": "Connopus acervatus",
        "kimp kõrges": "Connopus acervatus",
        "puidu-sametkõrges": "Flammulina velutipes",
        "puidu sametkõrges": "Flammulina velutipes",
        "sametkõrges": "Flammulina velutipes",
        "kivipuravik": "Boletus edulis",
        "männitaelik": "Porodaedalea pini",
        "männi-taelik": "Porodaedalea pini",
        "mannitaelik": "Porodaedalea pini",
        "hiirkäbik": "Baeospora myosura",
        "hiir-käbik": "Baeospora myosura",
        "hiirkabik": "Baeospora myosura",
        "käbik": "Baeospora",
        "kabik": "Baeospora",
        "bertilloni riisikas": "Lactifluus bertillonii",
        "bertilloni-riisikas": "Lactifluus bertillonii",
        "bertilloniriisikas": "Lactifluus bertillonii",
        "bertilloni piimik": "Lactifluus bertillonii",
        "bertilloni": "Lactifluus bertillonii",
        "lactarius bertillonii": "Lactifluus bertillonii",
        "lactifuus bertillonii": "Lactifluus bertillonii",
        "kreemriisikas": "Lactarius pubescens",
        "kreem-riisikas": "Lactarius pubescens",
        "kreem riisikas": "Lactarius pubescens",
        "kreemriisikad": "Lactarius pubescens",
        "triibuline heinik": "Tricholoma portentosum",
        "triibuline-heinik": "Tricholoma portentosum",
        "triibulineheinik": "Tricholoma portentosum",
        "tricholoma portentosum": "Tricholoma portentosum",
        "küüslauknööbik": "Mycetinis scorodonius",
        "küüslauk-nööbik": "Mycetinis scorodonius",
        "küüslauknööpik": "Mycetinis scorodonius",
        "kuuslauknoobik": "Mycetinis scorodonius",
        "okkaroisknööbik": "Gymnopus perforans",
        "okka roisknööbik": "Gymnopus perforans",
        "okka-roisknööbik": "Gymnopus perforans",
        "jõhvnööbik": "Gymnopus androsaceus",
        "jõhv-nööbik": "Gymnopus androsaceus",
        "väävelrisisikas": "Lactarius tabidus",
        "kamperrsiisikas": "Lactarius camphoratus",
        "haisev harisirmik": "Lepiota cristata",
        "haisev-harisirmik": "Lepiota cristata",
        "haisev heinik": "Tricholoma inamoenum",
        "haisev-heinik": "Tricholoma inamoenum"
    }
    for k, v in overrides.items():
        mapping[k] = v

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
    import re, unicodedata
    raw_query = unicodedata.normalize("NFC", taxon_query.strip())
    norm_query = raw_query.lower()
    
    local_taxa = load_local_taxa_mappings()
    scientific_search = local_taxa.get(norm_query) or local_taxa.get(norm_query.replace("-", " ")) or raw_query

    # Kui sisestus sisaldas sulgudes ladinakeelset nime (nt 'Harilik kivipuravik (Boletus edulis)')
    clean_query = scientific_search if (scientific_search and scientific_search != raw_query) else raw_query
    m_paren = re.search(r'\((.*?)\)', raw_query)
    if m_paren:
        paren_content = m_paren.group(1).strip()
        clean_vern = re.sub(r'\(.*?\)', '', raw_query).strip()
        if paren_content:
            scientific_search = paren_content
            clean_query = scientific_search
            norm_query = clean_vern.lower()
    elif norm_query == "kivipuravik":
        scientific_search = "Boletus edulis"
        clean_query = "Boletus edulis"

    # Perekonna taseme tuvastamine (AINULT kui kasutaja kirjutab selgelt sp. / sp / spp. / perekond)
    genus_mode = False
    if re.search(r'(\b(sp\.|spp\.|perek\.)|\b(sp|spp|perekond)\b)', norm_query, re.IGNORECASE):
        genus_mode = True
        clean_query = re.sub(r'(\b(sp\.|spp\.|perek\.)|\b(sp|spp|perekond)\b)', '', clean_query, flags=re.IGNORECASE).strip()
        clean_query = re.sub(r'(\b(sp\.|spp\.|perek\.)|\b(sp|spp|perekond)\b)', '', scientific_search, flags=re.IGNORECASE).strip()

    clean_norm = clean_query.lower()

    taxa_cache = {}
    if os.path.exists(TAXA_CACHE_FILE):
        try:
            with open(TAXA_CACHE_FILE, "r", encoding="utf-8") as f:
                taxa_cache = json.load(f)
        except Exception:
            taxa_cache = {}

    if scientific_search in taxa_cache and not genus_mode:
        return taxa_cache[scientific_search]
    if raw_query in taxa_cache and not genus_mode:
        return taxa_cache[raw_query]

    taxon_info = {
        "search_name": raw_query,
        "taxon_name": clean_query,
        "full_name": clean_query,
        "rank": "Perekond" if genus_mode else "Liik",
        "taxon_id": None,
        "vernacular_name": "",
        "kingdom": "Fungi"
    }

    candidates = []
    if scientific_search:
        candidates.append(scientific_search)
    if raw_query not in candidates:
        candidates.append(raw_query)
    if clean_query not in candidates:
        candidates.append(clean_query)
    if norm_query not in candidates:
        candidates.append(norm_query)

    # Typo corrections (nt cordiceps -> cordyceps)
    for c in list(candidates):
        if "cordiceps" in c.lower():
            candidates.append(re.sub(r'cordiceps', 'cordyceps', c, flags=re.IGNORECASE))
        if "iceps" in c.lower():
            candidates.append(re.sub(r'iceps', 'yceps', c, flags=re.IGNORECASE))

    # Genus / epithet fallback kui liiginimi sisaldab mitut sõna
    for c in list(candidates):
        words = c.split()
        if len(words) >= 2:
            if words[0] not in candidates:
                candidates.append(words[0])

    urls_to_try = []
    seen_urls = set()
    for cand in candidates:
        if cand:
            u1 = f"https://api.plutof.ut.ee/v1/public/taxa/autocomplete/?name={urllib.parse.quote(cand)}"
            u2 = f"https://api.plutof.ut.ee/v1/public/taxa/autocomplete/?q={urllib.parse.quote(cand)}"
            for u in [u1, u2]:
                if u not in seen_urls:
                    seen_urls.add(u)
                    urls_to_try.append(u)

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
                        tname = at.get("taxon_name", "").strip().lower()
                        fname = at.get("name", "").strip().lower()
                        rank = at.get("taxon_rank", "")
                        vern = at.get("vernacular_name", "").strip().lower()
                        is_syn = at.get("is_synonym", False)
                        
                        sci_targets = [clean_norm, scientific_search.lower() if scientific_search else ""]
                        sci_exact = 0 if any(tname == st or fname.startswith(st + " ") or fname == st for st in sci_targets if st) else (1 if any(st in fname for st in sci_targets if st) else 2)
                        
                        vern_targets = [norm_query, raw_query.lower(), clean_norm]
                        vern_exact = 0 if any(vern == vt for vt in vern_targets if vt) else (1 if any(vt in vern for vt in vern_targets if vt and len(vt) > 2) else 2)
                        name_match = min(sci_exact, vern_exact)

                        syn_score = 1 if is_syn else 0

                        if genus_mode:
                            rank_score = 0 if rank == "Genus" else (1 if rank == "Species" else 2)
                            return (syn_score, rank_score, name_match)
                        else:
                            rank_score = 0 if rank == "Species" else (1 if rank == "Genus" else 2)
                            return (syn_score, name_match, rank_score)
                    
                    sorted_items = sorted(items, key=sort_key)
                    match = sorted_items[0]
                    attrs = match.get("attributes", {})
                    taxon_info["taxon_id"] = match.get("id")
                    taxon_info["full_name"] = attrs.get("name", raw_query)
                    taxon_info["taxon_name"] = attrs.get("taxon_name", raw_query)
                    taxon_info["rank"] = "Perekond" if attrs.get("taxon_rank") == "Genus" else ("Liik" if attrs.get("taxon_rank") == "Species" else attrs.get("taxon_rank", "Liik"))
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


def fetch_person_id(name: str, token: str) -> Optional[str]:
    """Otsib PlutoF API-st isiku nime järgi Person ID."""
    if not name or not token:
        return None
    url = f"https://api.plutof.ut.ee/v1/public/persons/autocomplete/?name={urllib.parse.quote(name)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)",
        "Authorization": f"Bearer {token}"
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("data", [])
            if items:
                return str(items[0].get("id"))
    except Exception:
        pass
    return None


def move_to_trash(filepath: str) -> bool:
    """Liigutab faili turvaliselt macOS Prügikasti (Trash). Kui tegemist on Apple Photos teegiga (.photoslibrary), ei puutu faili kunagi."""
    try:
        abs_path = os.path.abspath(filepath)
        if ".photoslibrary" in abs_path or "Photos Library" in abs_path:
            # Apple Photos sisefail - säilitame 100% puutumatuna, et vältida Photos.app veateateid
            return False
        cmd = f'tell application "Finder" to delete POSIX file "{abs_path}"'
        import subprocess
        subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)
        return True
    except Exception:
        try:
            abs_path = os.path.abspath(filepath)
            if ".photoslibrary" in abs_path or "Photos Library" in abs_path:
                return False
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


def upload_file_to_plutof(filepath: str, token: str) -> Tuple[str, str]:
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
            fid = str(res["data"]["id"])
            dlinks = res["data"].get("attributes", {}).get("download_links", {})
            s3_url = dlinks.get("large_link") or dlinks.get("orig_link") or ""
            return fid, s3_url
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_body)
            for err in err_json.get("errors", []):
                if "already have a file" in err.get("message", "").lower() and err.get("id"):
                    fid = str(err["id"])
                    s3_url = ""
                    try:
                        f_req = urllib.request.Request(f"https://api.plutof.ut.ee/v1/public/files/{fid}/", headers={"User-Agent": "PlutoFObservationAssistant/1.0"})
                        with urllib.request.urlopen(f_req, timeout=10) as f_resp:
                            f_d = json.loads(f_resp.read().decode("utf-8"))
                            f_links = f_d.get("data", {}).get("attributes", {}).get("download_links", {})
                            s3_url = f_links.get("large_link") or f_links.get("orig_link") or ""
                    except Exception:
                        pass
                    return fid, s3_url
        except Exception:
            pass
        raise RuntimeError(f"Faili üleslaadimine ebaõnnestus ({e.code}): {err_body}")


def clean_cli_arg(arg: str) -> str:
    """Eemaldab terminali ja teksti laiendaja (ClipSnippet) bracketed-paste ANSI escape koodid (^[[200~ jne)."""
    import re
    cleaned = re.sub(r'(\x1b\[\d+~|\^\[\[\d+~|\[\d+~|\^\[|\x1b)', '', arg)
    return cleaned.strip("\"' \t\r\n")


def normalize_cli_args(args_list: List[str]) -> List[str]:
    """Ühendab tühikutega eraldatud lipud (nt ['o', ':üksikud'], ['o', ':', 'üksikud'], ['o:', 'üksikud'])."""
    known_prefixes = {
        "substraat", "subst", "sub", "s",
        "tüüp", "tyyp", "type", "t",
        "ohtrus", "oht", "abund", "o",
        "kaasvaatleja", "kaasvaatlejad", "kaaslane", "kaaslased", "kaasv", "kaas", "co", "kv",
        "määraja", "maaraja", "määras", "maaras", "mä", "ma", "det",
        "märkus", "markus", "märkused", "note", "notes", "m"
    }
    
    normalized = []
    i = 0
    while i < len(args_list):
        arg = clean_cli_arg(args_list[i])
        if not arg:
            i += 1
            continue
            
        arg_lower = arg.lower()
        
        # Juhtum 1: 'o' järgmise argumendiga ':üksikud' või ':' ja 'üksikud'
        if arg_lower in known_prefixes and i + 1 < len(args_list):
            next_arg = clean_cli_arg(args_list[i + 1])
            if next_arg.startswith(":") and len(next_arg) > 1:
                # nt 'o' ja ':üksikud' -> 'o:üksikud'
                normalized.append(f"{arg}:{next_arg[1:].strip()}")
                i += 2
                continue
            elif next_arg == ":" and i + 2 < len(args_list):
                # nt 'o' ja ':' ja 'üksikud' -> 'o:üksikud'
                val_arg = clean_cli_arg(args_list[i + 2])
                normalized.append(f"{arg}:{val_arg.strip()}")
                i += 3
                continue
            elif not next_arg.startswith(":") and not os.path.exists(next_arg) and "/" not in next_arg:
                # Kui lipp on 's' / 't' / 'o' ja järgmine argument on teadaolev väärtus (nt 'o üksikud', 's kuusk')
                if (arg_lower in ["s", "sub", "subst", "substraat"] and next_arg.lower() in SUBSTRATE_MAP) or \
                   (arg_lower in ["t", "tüüp", "tyyp", "type"] and next_arg.lower() in TYPE_MAP) or \
                   (arg_lower in ["o", "oht", "ohtrus"] and next_arg.lower() in ABUNDANCE_MAP):
                    normalized.append(f"{arg}:{next_arg}")
                    i += 2
                    continue
        
        # Juhtum 2: 'o:' ja järgmine argument 'üksikud'
        if arg_lower.endswith(":") and arg_lower[:-1] in known_prefixes and i + 1 < len(args_list):
            next_arg = clean_cli_arg(args_list[i + 1])
            if not next_arg.startswith("-"):
                normalized.append(f"{arg}{next_arg}")
                i += 2
                continue
                
        normalized.append(arg)
        i += 1
        
    return normalized


def parse_cli_args(args_list: List[str]) -> Tuple[str, List[str], Dict[str, Any]]:
    files = []
    flags = {
        "substraat_nimi": "",
        "substraat_taxon_id": None,
        "tüüp_nimi": "",
        "tüüp_id": None,
        "ohtrus": "",
        "märkus": "",
        "kaasvaatlejad": [],
        "määraja": None,
        "force": False
    }
    taxon_words = []
    expecting_co = False

    valid_exts = (".jpg", ".jpeg", ".heic", ".png", ".webp", ".zip")
    clean_args = normalize_cli_args(args_list)

    for arg in clean_args:
        arg_clean = clean_cli_arg(arg)
        if not arg_clean:
            continue
        if arg_clean == "--force":
            flags["force"] = True
            expecting_co = False
            continue
        if arg_clean in ["--keep", "-k", "keep"]:
            flags["keep"] = True
            expecting_co = False
            continue

        if os.path.isfile(arg_clean) or arg_clean.lower().endswith(valid_exts) or ("/" in arg_clean and os.path.exists(arg_clean)):
            if os.path.exists(arg_clean):
                files.append(arg_clean)
            expecting_co = False
            continue

        lower_arg = arg_clean.lower()
        clean_lower = lower_arg.lstrip(":")
        if any(clean_lower.startswith(prefix) for prefix in ["substraat:", "sub:", "subst:", "s:"]):
            val = arg_clean.lstrip(":").split(":", 1)[1].strip()
            mapped = SUBSTRATE_MAP.get(val.lower())
            if mapped:
                flags["substraat_nimi"] = mapped[0]
                flags["substraat_taxon_id"] = mapped[1]
            else:
                flags["substraat_nimi"] = val
            expecting_co = False
        elif any(clean_lower.startswith(prefix) for prefix in ["tüüp:", "tyyp:", "type:", "t:"]):
            val = arg_clean.lstrip(":").split(":", 1)[1].strip()
            mapped = TYPE_MAP.get(val.lower())
            if mapped:
                flags["tüüp_nimi"] = mapped[0]
                flags["tüüp_id"] = mapped[1]
            else:
                flags["tüüp_nimi"] = val
            expecting_co = False
        elif any(clean_lower.startswith(prefix) for prefix in ["ohtrus:", "oht:", "abund:", "o:"]):
            val = arg_clean.lstrip(":").split(":", 1)[1].strip()
            flags["ohtrus"] = ABUNDANCE_MAP.get(val.lower(), val)
            expecting_co = False
        elif any(clean_lower.startswith(prefix) for prefix in ["kv:", "kaasv:", "kaasvaatleja:", "kaaslane:", "kaaslased:", "kaas:", "co:"]):
            val = arg_clean.lstrip(":").split(":", 1)[1].strip()
            parts = [p.strip() for p in val.split(",") if p.strip()]
            for p in parts:
                p_lower = p.lower()
                if p_lower in CO_OBSERVERS_MAP:
                    c_name, c_id = CO_OBSERVERS_MAP[p_lower]
                    flags["kaasvaatlejad"].append({"name": c_name, "id": c_id})
                else:
                    flags["kaasvaatlejad"].append({"name": p, "id": None})
            expecting_co = val.endswith(",") or arg_clean.endswith(",")
        elif expecting_co or (lower_arg.rstrip(",") in CO_OBSERVERS_MAP and flags["kaasvaatlejad"]):
            # Jätk eelmisest kaasvaatlejate lipust tühiku tõttu (nt 'kv:aa, vl')
            clean_token = lower_arg.rstrip(",")
            if clean_token in CO_OBSERVERS_MAP:
                c_name, c_id = CO_OBSERVERS_MAP[clean_token]
                flags["kaasvaatlejad"].append({"name": c_name, "id": c_id})
            else:
                flags["kaasvaatlejad"].append({"name": arg_clean.rstrip(","), "id": None})
            expecting_co = arg_clean.endswith(",")
        elif any(clean_lower.startswith(prefix) for prefix in ["määraja:", "maaraja:", "määras:", "maaras:", "mä:", "ma:", "det:"]):
            val = arg_clean.lstrip(":").split(":", 1)[1].strip()
            v_lower = val.lower()
            if v_lower in CO_OBSERVERS_MAP:
                det_name, det_id = CO_OBSERVERS_MAP[v_lower]
                flags["määraja"] = {"name": det_name, "id": det_id}
            else:
                flags["määraja"] = {"name": val, "id": None}
            expecting_co = False
        elif any(clean_lower.startswith(prefix) for prefix in ["märkus:", "markus:", "märkused:", "note:", "notes:", "m:"]):
            val = arg_clean.lstrip(":").split(":", 1)[1].strip()
            flags["märkus"] = val
            expecting_co = False
        else:
            taxon_words.append(arg_clean)
            expecting_co = False

    taxon_name = " ".join(taxon_words).strip()
    return taxon_name, files, flags


def show_options_table():
    print("""
===============================================================================
 PLUTOF SEENEVAATLUSE VALIKUD JA PARAMEETRID
===============================================================================

 1. SUBSTRAAT (s:, sub: või substraat:)
-------------------------------------------------------------------------------
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

 2. SUBSTRAADI TÜÜP (t:, tyyp: või tüüp:)
-------------------------------------------------------------------------------
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

 3. OHTRUS (o:, oht: või ohtrus:)
-------------------------------------------------------------------------------
  üksikud     -> Üksikud viljakehad (1–3 tk)
  vähe        -> Vähe (mõned eksemplarid)
  mõõdukalt   -> Mõõdukalt (tavaline leiukoht)
  sage        -> Sage (arvukalt viljakehi)
  palju       -> Palju (suurem kogumik)
  massiliselt -> Massiliselt (ulatuslik esinemine)

 4. KAASVAATLEJAD (kv: või kaasv:)
-------------------------------------------------------------------------------
  aa          -> Allar Antson (ID: 81490)
  vl          -> Vello Liiv (ID: 19681)
  iz          -> Irma Zettur (ID: 43966)
  pl          -> Piret Lõhmus (ID: 307)
  alm / am    -> Anne-Liia Maido (ID: 74936)
  tt          -> Taavi Tatsi (ID: 73640)
  tv          -> Triin Varvas (ID: 44416)
  mp          -> Margit Päkk (ID: 54665)
  kp          -> Kadri Pärtel (ID: 255)
  is          -> Irja Saar (ID: 253)

 5. MÄÄRAJA (mä:, määraja:, ma: või det:)
-------------------------------------------------------------------------------
  vl          -> Vello Liiv (ID: 19681)
  is          -> Irja Saar (ID: 253)
  kp          -> Kadri Pärtel (ID: 255)
  aa          -> Allar Antson (ID: 81490)
  iz          -> Irma Zettur (ID: 43966)
  pl          -> Piret Lõhmus (ID: 307)
  alm / am    -> Anne-Liia Maido (ID: 74936)
  tt          -> Taavi Tatsi (ID: 73640)
  tv          -> Triin Varvas (ID: 44416)
  mp          -> Margit Päkk (ID: 54665)
  "Eesnimi Perekonnanimi" -> Otsitakse automaatselt PlutoF registrist

 6. MÄRKUS (m: või märkus:)
-------------------------------------------------------------------------------
  m:tekst      -> Vabatekstiline märkus või vaatluse detailid

 7. SÜNKROON JA PARANDUSED
-------------------------------------------------------------------------------
  seen sync <ID> -> Sünkroonib vaatluse PlutoF-ist andmebaasi ja Google Photosesse
  seen --sync    -> Tõmbab kõik PlutoF vaatlused kohalikku andmebaasi

 NÄITED:
  seen "Hygrophorus persicolor" /tee/foto.jpg mä:vl s:mänd o:üksikud
  seen "Ramaria sp." /tee/foto.jpg kv:aa,vl mä:is s:kuusk t:lamatüvi
  seen verev nahkis /tee/foto.jpg mä:vl s:mänd t:lamatüvi m:"ilus leid"
===============================================================================
""")


def sync_single_observation(obs_id: str):
    """Sünkroonib konkreetse vaatluse PlutoF API-st SQLite andmebaasi ja Google Photosesse."""
    print("=" * 80)
    print(f"PLUTOF VAATLUSE {obs_id} SÜNKROONIMINE")
    print("=" * 80)

    creds_file = os.path.expanduser("~/.plutof_credentials.json")
    token = None
    if os.path.exists(creds_file):
        try:
            with open(creds_file, "r") as f:
                token = json.load(f).get("access_token")
        except Exception:
            pass

    url = f"https://api.plutof.ut.ee/v1/public/observations/{obs_id}/"
    headers = {"User-Agent": "PlutoFObservationAssistant/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Viga PlutoF API päringul: {e}", file=sys.stderr)
        return

    attr = data.get("data", {}).get("attributes", {})
    rels = data.get("data", {}).get("relationships", {})

    taxon_node = rels.get("taxon_node", {}).get("data") or {}
    taxon_id = taxon_node.get("id")
    taxon_name = attr.get("representation") or ""
    remarks = attr.get("remarks") or ""

    vernacular_name = ""
    if taxon_id:
        try:
            t_url = f"https://api.plutof.ut.ee/v1/public/taxa/{taxon_id}/"
            t_req = urllib.request.Request(t_url, headers={"User-Agent": "PlutoFObservationAssistant/1.0"})
            with urllib.request.urlopen(t_req, timeout=5) as t_resp:
                t_data = json.loads(t_resp.read().decode("utf-8"))
                v_list = t_data.get("data", {}).get("attributes", {}).get("vernacular_names", [])
                for v in v_list:
                    if v.get("language") in ["est", "et"]:
                        vernacular_name = v.get("name")
                        break
        except Exception:
            pass

    init_local_db()
    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    c.execute("""
    UPDATE observations
    SET taxon_name = ?, taxon_id = ?, vernacular_name = ?, remarks = COALESCE(NULLIF(?, ''), remarks)
    WHERE id = ?;
    """, (taxon_name, taxon_id, vernacular_name, remarks, obs_id))
    conn.commit()

    c.execute("SELECT * FROM observations WHERE id = ?;", (obs_id,))
    row_data = c.fetchone()
    if not row_data:
        print(f"Hoiatus: Vaatlus {obs_id} ei leitud kohalikust andmebaasist!", file=sys.stderr)
        conn.close()
        return

    cols = [d[0] for d in c.description]
    obs_record = dict(zip(cols, row_data))

    c.execute("SELECT COALESCE(filepath, image_url), google_photos_media_id FROM observation_photos WHERE observation_id = ?;", (obs_id,))
    p_rows = c.fetchall()
    photos = [r[0] for r in p_rows if r[0]]
    old_gphotos_ids = [r[1] for r in p_rows if len(r) > 1 and r[1]]
    conn.close()

    print(f"Kohalik andmebaas uuendatud: {obs_record.get('vernacular_name', '')} ({obs_record.get('taxon_name', '')})")

    # Uuenda Google Photos
    if photos:
        print(f"Uuendan Google Photos albumi 'PlutoF Seenevaatlused' kirjeldust ({len(photos)} fotot)...")
        try:
            sys.path.insert(0, "/Users/metrobee/GEMINI/scripts")
            import google_photos_sync
            new_ids = google_photos_sync.sync_observation_to_google_photos(
                photos, obs_record, album_name="PlutoF Seenevaatlused", old_media_ids=old_gphotos_ids
            )
            if new_ids:
                conn_up = sqlite3.connect(LOCAL_OBS_DB)
                c_up = conn_up.cursor()
                for idx, gid in enumerate(new_ids):
                    if idx < len(photos):
                        c_up.execute("UPDATE observation_photos SET google_photos_media_id = ? WHERE observation_id = ? AND (filepath = ? OR image_url = ?);", (gid, obs_id, photos[idx], photos[idx]))
                conn_up.commit()
                conn_up.close()
            print("Google Photos kirjeldus ja metaandmed edukalt värskendatud (vana foto albumist eemaldatud)!")
        except Exception as e:
            print(f"Hoiatus: Google Photos uuendamine ebaõnnestus: {e}", file=sys.stderr)

    # Uuenda veebirakendus (fungib.web.app)
    try:
        exp_script = "/Users/metrobee/Projects/fungib/scripts/export_dashboard_data.py"
        if os.path.exists(exp_script):
            subprocess.run(["python3", exp_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(["firebase", "deploy", "--only", "hosting"], cwd="/Users/metrobee/Projects/fungib", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Veebirakenduse fungib.web.app andmed sünkroonitud ja taustal juurutatud!")
    except Exception:
        pass

    print("=" * 80)
    print(f"VAATLUS {obs_id} ON SÜSTEEMIDES EDUKALT VÄRSKENDATUD!")
    print(f"PlutoF link: https://app.plutof.ut.ee/observation/view/{obs_id}")
    print("=" * 80)


def update_plutof_observation(obs_id: str, args: List[str]):
    """Muudab vaatluse taksonit, määrajat või parameetreid ja sünkroonib süsteemid."""
    taxon_query, _, flags = parse_cli_args(args)
    
    init_local_db()
    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    c.execute("SELECT * FROM observations WHERE id = ?;", (obs_id,))
    row_data = c.fetchone()
    existing_record = {}
    if row_data:
        cols = [d[0] for d in c.description]
        existing_record = dict(zip(cols, row_data))
    conn.close()

    print("=" * 80)
    print(f"PLUTOF VAATLUSE {obs_id} MUUTMINE JA SÜNKROONIMINE")
    print("=" * 80)

    # 1. Taksoni muutmine (kui määratud)
    taxon_info = None
    if taxon_query:
        taxon_info = fetch_plutof_taxon_info(taxon_query)
        if taxon_info.get("taxon_id"):
            print(f"Uus takson: {taxon_info['full_name']} (ID: {taxon_info['taxon_id']})")
        else:
            print(f"Viga: PlutoF registrist ei leitud taksonit '{taxon_query}'!", file=sys.stderr)
            return

    # 2. Määraja (kui määratud)
    determiner_name = None
    if flags.get("määraja"):
        determiner_name = flags["määraja"].get("name")
        print(f"Uus määraja: {determiner_name} (ID: {flags['määraja'].get('id', '-')})")

    # 3. Kaasvaatlejad (kui määratud)
    collectors_str = None
    if flags.get("kaasvaatlejad"):
        co_names = [co["name"] for co in flags["kaasvaatlejad"]]
        collectors_str = f"Boris Meldre, {', '.join(co_names)}"
        print(f"Uued kogujad: {collectors_str}")

    # 4. Uuenda lokaalne SQLite andmebaas
    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    
    update_fields = []
    update_vals = []
    if taxon_info:
        update_fields.extend(["taxon_name = ?", "taxon_id = ?", "vernacular_name = ?"])
        update_vals.extend([taxon_info["full_name"], str(taxon_info["taxon_id"]), taxon_info.get("vernacular_name", "")])
    if determiner_name:
        update_fields.append("determiner = ?")
        update_vals.append(determiner_name)
    if collectors_str:
        update_fields.append("collectors = ?")
        update_vals.append(collectors_str)
    if flags.get("substraat_nimi"):
        update_fields.append("substrate = ?")
        update_vals.append(flags["substraat_nimi"])
    if flags.get("tüüp_nimi"):
        update_fields.append("substrate_type = ?")
        update_vals.append(flags["tüüp_nimi"])
    if flags.get("ohtrus"):
        update_fields.append("abundance = ?")
        update_vals.append(flags["ohtrus"])
    if flags.get("märkus"):
        update_fields.append("remarks = ?")
        update_vals.append(flags["märkus"])

    if update_fields:
        update_vals.append(obs_id)
        sql = f"UPDATE observations SET {', '.join(update_fields)} WHERE id = ?;"
        c.execute(sql, update_vals)
        conn.commit()

    # Loeme värsked andmed
    c.execute("SELECT * FROM observations WHERE id = ?;", (obs_id,))
    row_data = c.fetchone()
    if row_data:
        cols = [d[0] for d in c.description]
        obs_record = dict(zip(cols, row_data))
    else:
        obs_record = existing_record
        obs_record["id"] = obs_id
        if determiner_name:
            obs_record["determiner"] = determiner_name

    c.execute("SELECT COALESCE(filepath, image_url), google_photos_media_id FROM observation_photos WHERE observation_id = ?;", (obs_id,))
    p_rows = c.fetchall()
    photos = [r[0] for r in p_rows if r[0]]
    old_gphotos_ids = [r[1] for r in p_rows if len(r) > 1 and r[1]]
    conn.close()

    print(f"Kohalik andmebaas uuendatud: Määraja: {obs_record.get('determiner', '')} | Takson: {obs_record.get('taxon_name', '')}")

    # 5. Uuenda Google Photos
    if photos:
        print(f"Uuendan Google Photos albumi 'PlutoF Seenevaatlused' fotot ja kirjeldust ({len(photos)} fotot)...")
        try:
            sys.path.insert(0, "/Users/metrobee/GEMINI/scripts")
            import google_photos_sync
            new_ids = google_photos_sync.sync_observation_to_google_photos(
                photos, obs_record, album_name="PlutoF Seenevaatlused", old_media_ids=old_gphotos_ids
            )
            if new_ids:
                conn_up = sqlite3.connect(LOCAL_OBS_DB)
                c_up = conn_up.cursor()
                for idx, gid in enumerate(new_ids):
                    if idx < len(photos):
                        c_up.execute("UPDATE observation_photos SET google_photos_media_id = ? WHERE observation_id = ? AND (filepath = ? OR image_url = ?);", (gid, obs_id, photos[idx], photos[idx]))
                conn_up.commit()
                conn_up.close()
            print("Google Photos kirjeldus edukalt uuendatud (vana foto asendatud uuega)!")
        except Exception as e:
            print(f"Hoiatus: Google Photos uuendamine ebaõnnestus: {e}", file=sys.stderr)

    # 6. Uuenda veebirakendus (fungib.web.app)
    try:
        exp_script = "/Users/metrobee/Projects/fungib/scripts/export_dashboard_data.py"
        if os.path.exists(exp_script):
            subprocess.run(["python3", exp_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(["firebase", "deploy", "--only", "hosting"], cwd="/Users/metrobee/Projects/fungib", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Veebirakenduse fungib.web.app andmed sünkroonitud ja taustal juurutatud!")
    except Exception:
        pass

    print("=" * 80)
    print(f"VAATLUS {obs_id} ON SÜSTEEMIDES EDUKALT VÄRSKENDATUD!")
    print(f"PlutoF link: https://app.plutof.ut.ee/observation/view/{obs_id}")
    print("=" * 80)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help", "--options", "options", "abi", "--abi"]:
        show_options_table()
        return

    if len(sys.argv) >= 2 and sys.argv[1] in ["sync", "--sync", "sünkrooni", "--sünkrooni"]:
        if len(sys.argv) >= 3 and sys.argv[2].isdigit():
            sync_single_observation(sys.argv[2])
            return
        else:
            print("Sünkroonin kõiki PlutoF vaatlusi...")
            sync_all_my_observations()
            return

    if len(sys.argv) >= 3 and sys.argv[1] in ["update", "--update", "muuda", "--muuda", "paranda"]:
        obs_id = sys.argv[2]
        rest_args = sys.argv[3:]
        update_plutof_observation(obs_id, rest_args)
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

    # 0. Paki lahti ZIP failid või konverteeri HEIC pildid
    original_files_to_trash = list(file_paths)
    resolved_photo_paths = []
    import zipfile, tempfile, subprocess

    img_extensions = (".jpg", ".jpeg", ".heic", ".png", ".webp")

    for fp in file_paths:
        # Puhasta terminali kleebitud erimärgid
        fp = fp.strip().strip("'\"").replace("[200~", "").replace("~", "")
        if not fp or not os.path.exists(fp):
            continue

        if fp.lower().endswith(".zip") and zipfile.is_zipfile(fp):
            temp_dir = tempfile.mkdtemp(prefix="seen_zip_")
            try:
                with zipfile.ZipFile(fp, 'r') as z:
                    z.extractall(temp_dir)
                for root, _, fnames in os.walk(temp_dir):
                    for fn in sorted(fnames):
                        if fn.lower().endswith(img_extensions) and not fn.startswith("._") and not fn.startswith("."):
                            full_p = os.path.join(root, fn)
                            if full_p.lower().endswith(".heic"):
                                temp_jpg = os.path.join(temp_dir, f"{os.path.splitext(fn)[0]}.jpg")
                                subprocess.run(["sips", "-s", "format", "jpeg", full_p, "--out", temp_jpg], capture_output=True)
                                if os.path.exists(temp_jpg):
                                    resolved_photo_paths.append(temp_jpg)
                            else:
                                resolved_photo_paths.append(full_p)
                print(f" Arhiivist '{os.path.basename(fp)}' leitud {len(resolved_photo_paths)} fotot.")
            except Exception as e:
                print(f" Viga ZIP arhiivi lahtipakkimisel ({fp}): {e}", file=sys.stderr)
        elif fp.lower().endswith(".heic"):
            # Konverteeri HEIC JPEG-iks
            temp_jpg = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(os.path.basename(fp))[0]}_{int(datetime.datetime.now().timestamp())}.jpg")
            try:
                subprocess.run(["sips", "-s", "format", "jpeg", fp, "--out", temp_jpg], capture_output=True, check=True)
                if os.path.exists(temp_jpg):
                    resolved_photo_paths.append(temp_jpg)
                else:
                    resolved_photo_paths.append(fp)
            except Exception:
                resolved_photo_paths.append(fp)
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
    if flags["kaasvaatlejad"]:
        co_display = ", ".join([f"{c['name']} (ID: {c['id']})" if c.get('id') else c['name'] for c in flags["kaasvaatlejad"]])
        print(f" Kaasvaatlejad: {co_display}")
    if flags.get("määraja") and flags["määraja"].get("name"):
        det_display = f"{flags['määraja']['name']} (ID: {flags['määraja']['id']})" if flags['määraja'].get('id') else flags['määraja']['name']
        print(f" Määraja: {det_display}")
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
        fid, s3_url = upload_file_to_plutof(it["file_path"], token)
        uploaded_file_ids.append(fid)
        it["plutof_file_id"] = fid
        it["s3_url"] = s3_url
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
            "data": [{"type": "Person", "id": person_id}] + [
                {"type": "Person", "id": str(c["id"])} for c in flags.get("kaasvaatlejad", []) if c.get("id") and str(c["id"]) != str(person_id)
            ]
        },
        "files": {
            "data": [{"type": "File", "id": fid} for fid in uploaded_file_ids]
        }
    }

    # Määraja (identified_by)
    determiner_obj = flags.get("määraja")
    determiner_name = "Boris Meldre"
    if determiner_obj and determiner_obj.get("id"):
        determiner_name = determiner_obj["name"]
        obs_rels["identified_by"] = {
            "data": [{"type": "Person", "id": str(determiner_obj["id"])}]
        }
    elif determiner_obj and determiner_obj.get("name"):
        determiner_name = determiner_obj["name"]
        det_id = fetch_person_id(determiner_obj["name"], token)
        if det_id:
            determiner_obj["id"] = det_id
            obs_rels["identified_by"] = {
                "data": [{"type": "Person", "id": str(det_id)}]
            }
        else:
            obs_attrs["identification_remarks"] = f"Määraja: {determiner_obj['name']}"
            obs_rels["identified_by"] = {
                "data": [{"type": "Person", "id": str(person_id)}]
            }
    else:
        obs_rels["identified_by"] = {
            "data": [{"type": "Person", "id": str(person_id)}]
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
    co_names = [c["name"] for c in flags.get("kaasvaatlejad", [])]
    collectors_str = f"Boris Meldre, {', '.join(co_names)}" if co_names else "Boris Meldre"

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
        "collectors": collectors_str,
        "determiner": determiner_name,
        "url": f"https://app.plutof.ut.ee/observation/view/{obs_id}"
    }
    
    record_observation_locally(obs_record, items)

    # 7. Google Photos albumisse lisamine ('PlutoF Vaatlused')
    if os.path.exists(os.path.expanduser("~/.google_photos_token.json")):
        try:
            sys.path.insert(0, "/Users/metrobee/GEMINI/scripts")
            from google_photos_sync import sync_observation_to_google_photos
            sync_observation_to_google_photos(resolved_photo_paths, obs_record)
        except Exception as e:
            pass

    # 8. Liiguta töödeldud pildifailid või ZIP arhiiv turvaliselt prügikasti (Trash)
    if not flags.get("keep"):
        for fp in original_files_to_trash:
            if fp and os.path.exists(fp):
                abs_fp = os.path.abspath(fp)
                if ".photoslibrary" in abs_fp or "Photos Library" in abs_fp:
                    print(f"  Pilt säilitati Apple Photos teegis puutumatuna.")
                else:
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
