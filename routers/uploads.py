"""Upload de imagini pe ImageKit (proxy securizat prin backend)."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

import models
from deps import get_current_user
from services import imagekit

router = APIRouter(tags=["uploads"])

ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    folder: str = Form("/kooka"),
    user: models.User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED:
        raise HTTPException(400, "Format acceptat: JPEG, PNG, WEBP, GIF")

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(400, "Imaginea depășește 8 MB")

    if not imagekit.is_configured():
        raise HTTPException(
            503,
            "Upload indisponibil: lipsesc cheile ImageKit (IMAGEKIT_PRIVATE_KEY în .env)",
        )

    safe_folder = folder if folder.startswith("/") else f"/{folder}"
    try:
        result = imagekit.upload_bytes(content, file.filename or "upload", safe_folder)
    except imagekit.ImageKitUploadError as e:
        raise HTTPException(502, f"Upload eșuat: {e}")

    return result
