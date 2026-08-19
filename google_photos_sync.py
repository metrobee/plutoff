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
ALBUM_NAME = " PlutoF Vaatlused"
SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.sharing",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata"
]


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
                print(f" Viga: Google OAuth faili ei leitud ({CLIENT_SECRET_FILE})", file=sys.stderr)
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, "w") as token_out:
            token_out.write(creds.to_json())

    return creds


ALBUM_ID_FILE = os.path.expanduser("~/.google_photos_album_id.txt")

def get_or_create_album(creds) -> Optional[str]:
    """Tagastab albumi ' PlutoF Vaatlused' ID või loob selle."""
    if os.path.exists(ALBUM_ID_FILE):
        try:
            with open(ALBUM_ID_FILE, "r") as f:
                aid = f.read().strip()
                if aid:
                    return aid
        except Exception:
            pass

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

    # 1. Loo uus album
    url_create = "https://photoslibrary.googleapis.com/v1/albums"
    payload = json.dumps({"album": {"title": ALBUM_NAME}}).encode("utf-8")
    try:
        req = urllib.request.Request(url_create, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            album_id = data.get("id")
            if album_id:
                with open(ALBUM_ID_FILE, "w") as f:
                    f.write(album_id)
                return album_id
    except Exception as e:
        print(f"  Uue albumi loomine ebaõnnestus: {e}", file=sys.stderr)
        return None


def sync_observation_to_google_photos(photo_paths: List[str], obs_id: str, taxon_name: str) -> bool:
    """Lisab vaatluse fotod Google Photos albumisse ' PlutoF Vaatlused'."""
    try:
        creds = get_authenticated_service()
        if not creds:
            return False

        album_id = get_or_create_album(creds)
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

            # Lisa albumisse kirjeldusega
            create_payload = json.dumps({
                "albumId": album_id,
                "newMediaItems": [
                    {
                        "description": f" PlutoF ID: {obs_id} | {taxon_name}",
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

        print(f" Sünkroonitud Google Photos albumisse: '{ALBUM_NAME}'")
        return True
    except Exception as e:
        print(f"  Google Photos sünkroonimise märkus: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    print(" Käivitan Google Photos autentimise...")
    creds = get_authenticated_service()
    if creds:
        album_id = get_or_create_album(creds)
        print(f" Google Photos ühendus edukas! Album: '{ALBUM_NAME}' (ID: {album_id})")
    else:
        print(" Autentimine ebaõnnestus.")
