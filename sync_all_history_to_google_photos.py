#!/usr/bin/env python3
"""
Sünkroonib PlutoF seenevaatluste fotod TÜ HPC S3-st Google Photos albumisse 'PlutoF Vaatlused'
koos täielike eestikeelsete metaandmetega (eestikeelne nimi, ladina nimi, asukoht, substraat, ohtrus, aeg, link).
"""

import os
import sys
import json
import time
import sqlite3
import urllib.request
import urllib.error

sys.path.insert(0, "/Users/metrobee/GEMINI/scripts")
import google_photos_sync

LOCAL_OBS_DB = "/Users/metrobee/GEMINI/data/plutof_vaatlused.db"
PROGRESS_FILE = os.path.expanduser("~/.google_photos_rich_synced.json")


def load_synced() -> set:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_synced(synced_set: set):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(synced_set), f, indent=2)
    except Exception:
        pass


def embed_gps_to_jpeg_bytes(img_bytes: bytes, lat: float, lon: float) -> bytes:
    if lat is None or lon is None:
        return img_bytes
    try:
        from PIL import Image, ExifTags
        import io
        im = Image.open(io.BytesIO(img_bytes))
        exif = im.getexif()
        gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)

        def to_deg(val):
            d = int(abs(val))
            m = int((abs(val) - d) * 60)
            s = round(((abs(val) - d) * 60 - m) * 60, 4)
            return (float(d), float(m), float(s))

        gps_ifd[1] = 'N' if lat >= 0 else 'S'
        gps_ifd[2] = to_deg(lat)
        gps_ifd[3] = 'E' if lon >= 0 else 'W'
        gps_ifd[4] = to_deg(lon)

        exif[ExifTags.IFD.GPSInfo] = gps_ifd
        out = io.BytesIO()
        im.save(out, format="JPEG", exif=exif, quality=95)
        return out.getvalue()
    except Exception:
        return img_bytes


LOCK_FILE = "/tmp/sync_all_history_gphotos.lock"

def acquire_lock():
    try:
        import fcntl
        lock_fd = open(LOCK_FILE, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except (IOError, BlockingIOError):
        print("Märkus: Teine sünkroonimisprotsess juba töötab. Lõpetan.", file=sys.stderr)
        sys.exit(0)


def main():
    lock_fd = acquire_lock()
    print("=" * 80)
    print("PLUTOF SEENEVAATLUSTE FOTODE SÜNKROONIMINE GOOGLE PHOTOS ALBUMISSE")
    print("=" * 80)

    creds = google_photos_sync.get_authenticated_service()
    if not creds:
        print("Viga: Google Photos autentimine ebaõnnestus!", file=sys.stderr)
        return

    album_id = google_photos_sync.get_or_create_album(creds, album_name="PlutoF Vaatlused")
    if not album_id:
        print("Viga: Albumit ei leitud ega saanud luua!", file=sys.stderr)
        return

    print(f"Sihtalbum: 'PlutoF Vaatlused' (ID: {album_id})")

    synced = load_synced()
    print(f"Varasemalt sünkroonitud fotode räsisi/kirjeid: {len(synced)}")

    if not os.path.exists(LOCAL_OBS_DB):
        print(f"Viga: Andmebaasi ei leitud: {LOCAL_OBS_DB}", file=sys.stderr)
        return

    conn = sqlite3.connect(LOCAL_OBS_DB)
    c = conn.cursor()
    c.execute("""
    SELECT 
        o.id,
        o.taxon_name,
        o.taxon_id,
        o.vernacular_name,
        o.date_time,
        o.latitude,
        o.longitude,
        o.locality,
        o.county,
        o.commune,
        o.substrate,
        o.substrate_type,
        o.abundance,
        o.remarks,
        o.collectors,
        p.sha256,
        p.filename,
        COALESCE(p.filepath, p.image_url) AS photo_url
    FROM observations o
    JOIN observation_photos p ON o.id = p.observation_id
    WHERE (p.filepath LIKE 'http%' OR p.image_url LIKE 'http%')
    ORDER BY o.date_time DESC;
    """)

    rows = c.fetchall()
    conn.close()

    total = len(rows)
    print(f"Kokku fotodega kirjeid andmebaasis: {total}")
    print("-" * 80)

    headers_upload = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/octet-stream",
        "X-Goog-Upload-Protocol": "raw"
    }

    headers_json = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    success_count = 0
    skipped_count = 0

    for idx, r in enumerate(rows, 1):
        (obs_id, taxon_name, taxon_id, vernacular_name, date_time,
         latitude, longitude, locality, county, commune, substrate,
         substrate_type, abundance, remarks, collectors,
         sha256_hash, filename, photo_url) = r

        sync_key = f"{obs_id}_{sha256_hash or filename}"
        if sync_key in synced:
            skipped_count += 1
            continue

        if not photo_url:
            synced.add(sync_key)
            continue

        obs_data = {
            "id": obs_id,
            "taxon_name": taxon_name,
            "taxon_id": taxon_id,
            "vernacular_name": vernacular_name,
            "date_time": date_time,
            "latitude": latitude,
            "longitude": longitude,
            "locality": locality,
            "county": county,
            "commune": commune,
            "substrate": substrate,
            "substrate_type": substrate_type,
            "abundance": abundance,
            "remarks": remarks,
            "collectors": collectors
        }

        description_text = google_photos_sync.format_google_photos_description(obs_data)
        display_label = vernacular_name or taxon_name or f"Vaatlus {obs_id}"

        print(f"[{idx}/{total}] Vaatlus {obs_id}: {display_label} ...", end="", flush=True)

        try:
            # 1. Tõmba foto TÜ HPC S3-st
            req_img = urllib.request.Request(photo_url, headers={"User-Agent": "PlutoFObservationAssistant/1.0"})
            with urllib.request.urlopen(req_img, timeout=25) as resp:
                img_bytes = resp.read()

            # Lisa pildile GPS EXIF metaandmed kui need andmebaasis olemas
            if latitude is not None and longitude is not None:
                img_bytes = embed_gps_to_jpeg_bytes(img_bytes, float(latitude), float(longitude))

            fname = filename or f"PlutoF_{obs_id}_{os.path.basename(photo_url)}"
            upload_h = dict(headers_upload)
            upload_h["X-Goog-Upload-File-Name"] = fname

            # 2. Lae Google Photos üleslaadimispuhvrisse
            upload_token = None
            for attempt in range(3):
                try:
                    req_up = urllib.request.Request(
                        "https://photoslibrary.googleapis.com/v1/uploads",
                        data=img_bytes,
                        headers=upload_h
                    )
                    with urllib.request.urlopen(req_up, timeout=35) as resp:
                        upload_token = resp.read().decode("utf-8")
                        break
                except urllib.error.HTTPError as e:
                    if e.code == 401:
                        # Värskenda token kui aegus
                        creds = google_photos_sync.get_authenticated_service()
                        upload_h["Authorization"] = f"Bearer {creds.token}"
                        headers_json["Authorization"] = f"Bearer {creds.token}"
                    elif e.code == 429 or e.code >= 500:
                        time.sleep(3 * (attempt + 1))
                    else:
                        raise e

            if not upload_token:
                print(" Üleslaadimise tokenit ei saadud.")
                continue

            # 3. Loo meediaüksus albumisse täieliku kirjeldusega
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
                    with urllib.request.urlopen(req_batch, timeout=25) as resp:
                        break
                except urllib.error.HTTPError as e:
                    if e.code == 401:
                        creds = google_photos_sync.get_authenticated_service()
                        headers_json["Authorization"] = f"Bearer {creds.token}"
                    elif e.code == 429 or e.code >= 500:
                        time.sleep(3 * (attempt + 1))
                    else:
                        raise e

            synced.add(sync_key)
            save_synced(synced)
            success_count += 1
            print(" Lisatud täieliku kirjeldusega!")
            time.sleep(1.2)

        except Exception as e:
            print(f" Viga: {e}")

    print("=" * 80)
    print(f"KÕIK VALMIS! Lisatud {success_count} fotot Google Photos albumisse 'PlutoF Vaatlused'. Vahele jäetud (juba olemas): {skipped_count}.")
    print("=" * 80)


if __name__ == "__main__":
    main()
