"""Upload de imagini pe ImageKit.

Backendul face upload-ul (nu frontendul), ca să nu expună cheia privată.
Folosim direct API-ul de upload ImageKit cu Basic auth (private key ca
username), ca să fim independenți de versiunea SDK-ului."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY", "")
URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT", "https://ik.imagekit.io/a7m1pnm28/")
UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"


class ImageKitNotConfigured(Exception):
    pass


class ImageKitUploadError(Exception):
    pass


def is_configured() -> bool:
    return bool(PRIVATE_KEY)


def upload_bytes(file_bytes: bytes, file_name: str, folder: str = "/kooka") -> dict:
    """Urcă bytes pe ImageKit. Întoarce {"url", "fileId", "thumbnailUrl"}."""
    if not PRIVATE_KEY:
        raise ImageKitNotConfigured(
            "IMAGEKIT_PRIVATE_KEY lipsește din .env"
        )

    try:
        resp = requests.post(
            UPLOAD_URL,
            auth=(PRIVATE_KEY, ""),          # Basic auth: private key ca username
            files={"file": (file_name, file_bytes)},
            data={
                "fileName": file_name,
                "folder": folder,
                "useUniqueFileName": "true",
            },
            timeout=30,
        )
    except requests.RequestException as e:
        raise ImageKitUploadError(f"Eroare rețea ImageKit: {e}")

    if resp.status_code >= 400:
        raise ImageKitUploadError(f"ImageKit {resp.status_code}: {resp.text}")

    data = resp.json()
    return {
        "url": data.get("url", ""),
        "fileId": data.get("fileId", ""),
        "thumbnailUrl": data.get("thumbnailUrl", ""),
    }
