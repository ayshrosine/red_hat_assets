"""File uploads via Emergent object storage + short-lived HMAC-signed URLs."""
import asyncio
import base64
import hashlib
import hmac
import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import Response as FastAPIResponse

from deps import db, iso, now_utc, new_id, get_current_user, JWT_SECRET
from storage import put_object, get_object, build_path

log = logging.getLogger("assetflow.uploads")
router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"}
FILE_TOKEN_TTL_SECONDS = 300  # 5 min


def _sign_file_token(file_id: str, ttl: int = FILE_TOKEN_TTL_SECONDS) -> tuple[str, int]:
    exp = int(time.time()) + ttl
    sig = hmac.new(JWT_SECRET.encode(), f"{file_id}:{exp}".encode(), hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(f"{exp}.".encode() + sig).rstrip(b"=").decode()
    return token, exp


def _verify_file_token(file_id: str, token: str) -> bool:
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode())
        sep = raw.index(b".")
        exp = int(raw[:sep])
        sig = raw[sep + 1 :]
        if exp < int(time.time()):
            return False
        expected = hmac.new(JWT_SECRET.encode(), f"{file_id}:{exp}".encode(), hashlib.sha256).digest()
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False


@router.post("")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    ctype = file.content_type or "application/octet-stream"
    if ctype not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ctype}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    path = build_path(user["user_id"], file.filename or "upload", ctype)
    try:
        result = await asyncio.to_thread(put_object, path, data, ctype)
    except Exception as e:
        log.exception("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Storage upload failed")
    file_id = new_id("fil")
    await db.files.insert_one({
        "file_id": file_id, "storage_path": result["path"],
        "original_filename": file.filename, "content_type": ctype,
        "size": result.get("size", len(data)),
        "uploaded_by": user["user_id"], "is_deleted": False,
        "created_at": iso(now_utc()),
    })
    return {
        "file_id": file_id,
        "url": f"/api/uploads/{file_id}",
        "content_type": ctype,
        "size": result.get("size", len(data)),
        "filename": file.filename,
    }


@router.post("/{file_id}/sign")
async def sign_file_url(file_id: str, user: dict = Depends(get_current_user)):
    rec = await db.files.find_one({"file_id": file_id, "is_deleted": False}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    token, exp = _sign_file_token(file_id)
    return {"url": f"/api/uploads/{file_id}?token={token}", "expires_at": exp, "ttl_seconds": FILE_TOKEN_TTL_SECONDS}


@router.get("/{file_id}")
async def download_file(file_id: str, request: Request, token: Optional[str] = None):
    authorized = False
    if token and _verify_file_token(file_id, token):
        authorized = True
    if not authorized:
        try:
            await get_current_user(request)
            authorized = True
        except HTTPException:
            pass
    if not authorized:
        raise HTTPException(status_code=401, detail="Not authenticated")
    rec = await db.files.find_one({"file_id": file_id, "is_deleted": False}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content, ctype = await asyncio.to_thread(get_object, rec["storage_path"])
    except Exception as e:
        log.exception("Download failed: %s", e)
        raise HTTPException(status_code=500, detail="Storage download failed")
    return FastAPIResponse(content=content, media_type=rec.get("content_type", ctype))
