#!/usr/bin/env python3
"""
Taim CLI - Minimalistlik ja nutikas taimevaatluste sisestaja terminalist
-------------------------------------------------------------------------
Autor: Boris Meldre & Antigravity (2026)
Asukoht: /Users/metrobee/GEMINI/scripts/taim_cli.py

Kasutamine:
  taim <taimenimi> [LOHISTA PILDID] [elupaik:park] [ohtrus:üksikud] [olek:viljub] [märkus:tekst]
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
import subprocess
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = "/Users/metrobee/GEMINI/data/plutof_vaatlused.db"
CACHE_FILE = "/Users/metrobee/.plutof_geo_cache.json"
TAXA_CACHE_FILE = "/Users/metrobee/.plutof_plant_taxa_cache.json"
CREDENTIALS_FILE = os.path.expanduser("~/.plutof_env")

def load_credentials() -> Dict[str, str]:
    creds = {}
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip().strip("'\"")
    return creds

def get_plutof_token(creds: Dict[str, str]) -> str:
    url = "https://api.plutof.ut.ee/v1/oauth2/token/"
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": creds.get("PLUTOF_CLIENT_ID", ""),
        "client_secret": creds.get("PLUTOF_CLIENT_SECRET", ""),
        "username": creds.get("PLUTOF_USERNAME", ""),
        "password": creds.get("PLUTOF_PASSWORD", "")
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["access_token"]

def get_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_decimal_from_dms(dms, ref: str) -> Optional[float]:
    try:
        if not dms or len(dms) < 3:
            return None
        def to_f(v):
            if hasattr(v, "num") and hasattr(v, "den"):
                return float(v.num) / float(v.den) if v.den != 0 else 0.0
            if isinstance(v, tuple) and len(v) == 2:
                return float(v[0]) / float(v[1]) if v[1] != 0 else 0.0
            return float(v)
        deg = to_f(dms[0])
        minute = to_f(dms[1])
        sec = to_f(dms[2])
        dec = deg + (minute / 60.0) + (sec / 3600.0)
        if ref in ["S", "W"]:
            dec = -dec
        return dec
    except Exception:
        return None

def extract_exif(image_path: str) -> Dict[str, Any]:
    exif_data = {
        "date_time": None,
        "latitude": None,
        "longitude": None,
        "altitude": None
    }
    ext = os.path.splitext(image_path)[1].lower()
    
    # Kui on HEIC, loeme mdls abil või teisendame ajutiselt
    if ext in [".heic", ".heif"]:
        try:
            res_date = subprocess.run(["mdls", "-name", "kMDItemContentCreationDate", "-raw", image_path], capture_output=True, text=True)
            if res_date.stdout and "(null)" not in res_date.stdout:
                d_str = res_date.stdout.strip()
                if " " in d_str:
                    exif_data["date_time"] = d_str.split(" +")[0].replace("-", ":")
            
            res_lat = subprocess.run(["mdls", "-name", "kMDItemLatitude", "-raw", image_path], capture_output=True, text=True)
            res_lon = subprocess.run(["mdls", "-name", "kMDItemLongitude", "-raw", image_path], capture_output=True, text=True)
            if res_lat.stdout and "(null)" not in res_lat.stdout and res_lon.stdout and "(null)" not in res_lon.stdout:
                exif_data["latitude"] = float(res_lat.stdout.strip())
                exif_data["longitude"] = float(res_lon.stdout.strip())
        except Exception:
            pass

    try:
        from PIL import Image, ExifTags
        with Image.open(image_path) as img:
            raw_exif = img._getexif()
            if raw_exif:
                for tag_id, val in raw_exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag in ["DateTimeOriginal", "DateTimeDigitized", "DateTime"] and not exif_data["date_time"]:
                        exif_data["date_time"] = str(val).strip()
                    elif tag == "GPSInfo":
                        gps_info = {}
                        for t in val:
                            sub_tag = ExifTags.GPSTAGS.get(t, t)
                            gps_info[sub_tag] = val[t]
                        if "GPSLatitude" in gps_info and "GPSLatitudeRef" in gps_info:
                            exif_data["latitude"] = get_decimal_from_dms(gps_info["GPSLatitude"], gps_info["GPSLatitudeRef"])
                        if "GPSLongitude" in gps_info and "GPSLongitudeRef" in gps_info:
                            exif_data["longitude"] = get_decimal_from_dms(gps_info["GPSLongitude"], gps_info["GPSLongitudeRef"])
    except Exception:
        pass

    return exif_data

def reverse_geocode(lat: float, lon: float) -> Dict[str, str]:
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    cache_key = f"{round(lat, 4)},{round(lon, 4)}"
    if cache_key in cache:
        return cache[cache_key]

    geo_data = {
        "country": "Eesti",
        "county": "",
        "commune": "",
        "locality": "",
        "full_area_name": ""
    }

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}&zoom=14&addressdetails=1"
        req = urllib.request.Request(url, headers={"User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            addr = data.get("address", {})
            geo_data["country"] = addr.get("country", "Eesti")
            geo_data["county"] = addr.get("county", addr.get("state", ""))
            geo_data["commune"] = addr.get("municipality", addr.get("city", addr.get("town", addr.get("village", ""))))
            geo_data["locality"] = addr.get("village", addr.get("suburb", addr.get("hamlet", addr.get("neighbourhood", ""))))
            
            parts = [geo_data["country"]]
            if geo_data["county"]:
                parts.append(geo_data["county"])
            if geo_data["commune"]:
                parts.append(geo_data["commune"])
            geo_data["full_area_name"] = ", ".join(parts)
            cache[cache_key] = geo_data
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return geo_data

def fetch_plutof_plant_taxon(query: str) -> Dict[str, Any]:
    raw_query = query.strip()
    norm_query = raw_query.lower()
    
    urls = [
        f"https://api.plutof.ut.ee/v1/public/taxa/autocomplete/?q={urllib.parse.quote(raw_query)}",
        f"https://api.plutof.ut.ee/v1/public/taxa/autocomplete/?name={urllib.parse.quote(raw_query)}"
    ]

    taxon_info = {
        "search_name": raw_query,
        "taxon_name": raw_query,
        "full_name": raw_query,
        "rank": "Liik",
        "taxon_id": None,
        "vernacular_name": "",
        "kingdom": "Plantae"
    }

    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                d = json.loads(resp.read().decode("utf-8"))
                items = d.get("data", [])
                if items:
                    def sort_key(it):
                        at = it.get("attributes", {})
                        tname = at.get("taxon_name", "").lower()
                        vern = at.get("vernacular_name", "").lower()
                        vern_match = 0 if norm_query in vern else 1
                        sci_match = 0 if norm_query in tname else 1
                        rank_score = 0 if at.get("taxon_rank") in ["Species", "Genus"] else 1
                        return (vern_match, sci_match, rank_score)
                    
                    sorted_items = sorted(items, key=sort_key)
                    match = sorted_items[0]
                    attrs = match.get("attributes", {})
                    taxon_info["taxon_id"] = match.get("id")
                    taxon_info["full_name"] = attrs.get("name", raw_query)
                    taxon_info["taxon_name"] = attrs.get("taxon_name", raw_query)
                    taxon_info["rank"] = attrs.get("taxon_rank", "Liik")
                    taxon_info["vernacular_name"] = attrs.get("vernacular_name", "")
                    break
        except Exception:
            pass

    return taxon_info

def move_to_trash(filepath: str) -> bool:
    try:
        abs_path = os.path.abspath(filepath)
        if ".photoslibrary" in abs_path or "Photos Library" in abs_path:
            return False
        cmd = f'tell application "Finder" to delete POSIX file "{abs_path}"'
        subprocess.run(["osascript", "-e", cmd], check=True, capture_output=True)
        return True
    except Exception:
        return False

def upload_file_to_plutof(filepath: str, token: str) -> Tuple[str, str]:
    boundary = uuid.uuid4().hex
    content_type = f"multipart/form-data; boundary={boundary}"
    body = []
    body.append(f"--{boundary}".encode())
    fn = os.path.basename(filepath)
    body.append(f'Content-Disposition: form-data; name="file"; filename="{fn}"'.encode())
    body.append(b"Content-Type: image/jpeg")
    body.append(b"")
    with open(filepath, "rb") as f:
        body.append(f.read())
    body.append(f"--{boundary}--".encode())
    body.append(b"")
    payload = b"\r\n".join(body)

    url = "https://api.plutof.ut.ee/v1/public/files/"
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": content_type,
        "User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"
    }, method="POST")

    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        data = res.get("data", {})
        file_id = data.get("id", "")
        attrs = data.get("attributes", {})
        s3_url = attrs.get("url", "")
        return str(file_id), s3_url

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h"]:
        print("""
KASUTAMINE:
  taim <taimenimi> [LOHISTA_PILDID] [elupaik:mets|park|niit] [ohtrus:üksikud|arvukalt] [olek:õitseb|viljub] [märkus:tekst]

NÄITED:
  taim harilik jugapuu [kopeeri_või_lohista_foto]
  taim "harilik pärn" /tee/pildini.HEIC elupaik:park ohtrus:üksikud olek:viljub märkus:"Kärdla keskväljak"
        """)
        sys.exit(0)

    creds = load_credentials()
    if not creds.get("PLUTOF_USERNAME"):
        print("VIGA: ~/.plutof_env volitused puuduvad.", file=sys.stderr)
        sys.exit(1)

    # Parsime argumendid
    plant_query_parts = []
    file_paths = []
    flags = {}

    for arg in sys.argv[1:]:
        arg_clean = arg.strip().strip("'\"")
        if os.path.exists(arg_clean) or "/" in arg_clean or arg_clean.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
            if os.path.exists(arg_clean):
                file_paths.append(arg_clean)
        elif ":" in arg:
            k, v = arg.split(":", 1)
            flags[k.lower().strip()] = v.strip()
        else:
            plant_query_parts.append(arg)

    plant_query = " ".join(plant_query_parts).strip()
    if not plant_query:
        print("VIGA: Taimenimi puudub. Kasutamine: taim <nimi> [pildid]", file=sys.stderr)
        sys.exit(1)

    print("=" * 80)
    print(" TAIMEVAATLUSE SISESTAMINE (PLUTOF)")
    print("=" * 80)
    print(f" Otsitav taim: {plant_query}")
    print(f" Fotosid kokku: {len(file_paths)}")

    # 1. Taksoni tuvastus
    taxon_info = fetch_plutof_plant_taxon(plant_query)
    print("-" * 80)
    print(f" PlutoF takson: {taxon_info['full_name']} (ID: {taxon_info['taxon_id'] or 'Tundmatu'})")

    # 2. Metaandmed fotodelt
    exif = {"date_time": None, "latitude": None, "longitude": None}
    processed_photos = []
    
    for fp in file_paths:
        ext = os.path.splitext(fp)[1].lower()
        work_fp = fp
        # Kui on HEIC, konverteerime turvaliselt ajutisse JPEG-i
        if ext in [".heic", ".heif"]:
            tmp_jpg = f"/tmp/{uuid.uuid4().hex}.jpg"
            subprocess.run(["sips", "-s", "format", "jpeg", fp, "--out", tmp_jpg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            work_fp = tmp_jpg

        if not exif["date_time"] or not exif["latitude"]:
            img_exif = extract_exif(fp)
            if img_exif["date_time"] and not exif["date_time"]:
                exif["date_time"] = img_exif["date_time"]
            if img_exif["latitude"] and not exif["latitude"]:
                exif["latitude"] = img_exif["latitude"]
                exif["longitude"] = img_exif["longitude"]
        
        processed_photos.append(work_fp)

    # Vaikimisi aeg kui puudub
    if not exif["date_time"]:
        exif["date_time"] = datetime.datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    
    # Kuupäeva formaat YYYY-MM-DD
    dt_parts = exif["date_time"].split()
    date_str = dt_parts[0].replace(":", "-")
    time_str = dt_parts[1] if len(dt_parts) > 1 else "12:00:00"
    iso_date_time = f"{date_str}T{time_str}"

    geo = {"country": "Eesti", "county": "", "commune": "", "locality": "", "full_area_name": ""}
    if exif["latitude"] and exif["longitude"]:
        geo = reverse_geocode(exif["latitude"], exif["longitude"])
        print(f" Asukoht: {geo['full_area_name'] or 'Eesti'}")
        print(f" Koordinaadid: {round(exif['latitude'], 6)}, {round(exif['longitude'], 6)} (Aeg: {exif['date_time']})")

    token = get_plutof_token(creds)

    # 3. Laeme fotod PlutoF-i
    uploaded_files = []
    print(" Sünkroonin fotosid ja saadan vaatluse PlutoF API-sse...")
    for idx, p_path in enumerate(processed_photos, 1):
        try:
            fid, s3_url = upload_file_to_plutof(p_path, token)
            uploaded_files.append({"file_id": fid, "s3_url": s3_url, "file_name": os.path.basename(p_path), "sha256": get_sha256(p_path)})
            print(f"  [{idx}/{len(processed_photos)}] Pilt üles laaditud (ID: {fid})")
        except Exception as e:
            print(f"  Hoiatus: Pildi üleslaadimine ebaõnnestus: {e}")

    # 4. Saadame vaatluse PlutoF API-sse
    obs_payload = {
        "data": {
            "type": "Observation",
            "attributes": {
                "date_time": iso_date_time,
                "date_time_accuracy": "Day",
                "notes": flags.get("märkus", flags.get("notes", "")),
                "is_public": True
            },
            "relationships": {}
        }
    }

    if taxon_info["taxon_id"]:
        obs_payload["data"]["relationships"]["taxon_node"] = {
            "data": {"type": "Taxon", "id": str(taxon_info["taxon_id"])}
        }

    # Asukoht ja koordinaadid
    if exif["latitude"] and exif["longitude"]:
        obs_payload["data"]["relationships"]["area"] = {
            "data": {
                "type": "Area",
                "attributes": {
                    "geometry": f"SRID=4326;POINT ({exif['longitude']} {exif['latitude']})",
                    "name": geo["full_area_name"] or "Eesti",
                    "country": geo["country"] or "Eesti",
                    "state": geo["county"],
                    "municipality": geo["commune"],
                    "locality": geo["locality"]
                }
            }
        }

    # Meediafailid
    if uploaded_files:
        obs_payload["data"]["relationships"]["files"] = {
            "data": [{"type": "File", "id": str(u["file_id"])} for u in uploaded_files]
        }

    # POST vaatlus
    url = "https://api.plutof.ut.ee/v1/public/observations/"
    req = urllib.request.Request(
        url,
        data=json.dumps(obs_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json",
            "User-Agent": "PlutoFObservationAssistant/1.0 (borismeldre@gmail.com)"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        obs_res = json.loads(resp.read().decode("utf-8"))
        obs_id = obs_res["data"]["id"]

    # 5. Salvestame kohalikku andmebaasi
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT OR REPLACE INTO observations 
    (id, taxon_name, date_time, latitude, longitude, altitude, locality, county, commune, remarks, url, created_at, primary_observer)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        obs_id,
        taxon_info["full_name"],
        iso_date_time,
        exif["latitude"],
        exif["longitude"],
        None,
        geo["locality"] or geo["full_area_name"],
        geo["county"],
        geo["commune"],
        flags.get("märkus", ""),
        f"https://app.plutof.ut.ee/observation/view/{obs_id}",
        datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "Boris Meldre"
    ))

    for u in uploaded_files:
        sha = u["sha256"]
        c.execute("""
        INSERT OR REPLACE INTO observation_photos
        (sha256, filename, filepath, observation_id, plutof_file_id, image_url, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            sha,
            u["file_name"],
            u["s3_url"],
            obs_id,
            u["file_id"],
            u["s3_url"],
            datetime.datetime.now(datetime.timezone.utc).isoformat()
        ))

    conn.commit()
    conn.close()

    # 6. Puhastus (ainult Downloads kaust, mitte Apple Photos)
    for orig_fp in file_paths:
        abs_fp = os.path.abspath(orig_fp)
        if ".photoslibrary" in abs_fp or "Photos Library" in abs_fp:
            print("  Pilt säilitati Apple Photos teegis puutumatuna.")
        else:
            if move_to_trash(orig_fp):
                print(f"  '{os.path.basename(orig_fp)}' liigutati prügikasti.")

    # 7. Sünkrooni veebiarhiiv taustal
    try:
        subprocess.run(["python3", "/Users/metrobee/Projects/fungib/scripts/export_dashboard_data.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["firebase", "deploy", "--only", "hosting"], cwd="/Users/metrobee/Projects/fungib", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    print("=" * 80)
    print(f" TAIMEVAATLUS EDUKALT SALVESTATUD PLUTOF ANDMEBAASI!")
    print(f" PlutoF ID: {obs_id}")
    print(f" Vaatluse link: https://app.plutof.ut.ee/observation/view/{obs_id}")
    print("=" * 80)

if __name__ == "__main__":
    main()
