"""File storage for uploads.

Supabase Storage when configured; otherwise a local directory, so uploads work
with no credentials. Same interface either way — callers never branch on it.
"""
from __future__ import annotations

import hashlib
import os
import pathlib

BUCKET = os.getenv("SUPABASE_BUCKET", "uploads")
LOCAL_DIR = pathlib.Path(os.getenv("LOCAL_STORAGE_DIR", ".storage"))
MAX_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
ALLOWED = {"application/pdf", "text/plain", "text/markdown", "application/octet-stream"}


class UploadTooLarge(Exception):
    pass


class UploadTypeNotAllowed(Exception):
    pass


def _validate(data: bytes, mime: str) -> None:
    # Trust boundary: never store what we have not size- and type-checked.
    if len(data) > MAX_BYTES:
        raise UploadTooLarge(f"file is {len(data)} bytes, limit is {MAX_BYTES}")
    if mime not in ALLOWED:
        raise UploadTypeNotAllowed(mime)


def _key(data: bytes, filename: str) -> str:
    digest = hashlib.sha256(data).hexdigest()[:32]
    suffix = pathlib.Path(filename).suffix.lower()[:10]
    return f"{digest}{suffix}"


def _supabase():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not (url and key):
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


def store(data: bytes, *, filename: str, mime: str = "application/pdf") -> str:
    """Store bytes, return a storage key. Content-addressed, so re-uploading the
    same file is a no-op rather than a duplicate."""
    _validate(data, mime)
    key = _key(data, filename)

    client = _supabase()
    if client is not None:
        try:
            client.storage.from_(BUCKET).upload(
                key, data, {"content-type": mime, "upsert": "true"}
            )
            return key
        except Exception:
            pass  # fall through to local storage rather than losing the upload

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    (LOCAL_DIR / key).write_bytes(data)
    return key


def load(key: str) -> bytes | None:
    client = _supabase()
    if client is not None:
        try:
            return client.storage.from_(BUCKET).download(key)
        except Exception:
            pass
    path = LOCAL_DIR / key
    return path.read_bytes() if path.exists() else None


def signed_url(key: str, *, ttl: int = 3600) -> str:
    """A URL the browser can read. Supabase issues a signed URL; locally we
    serve the bytes back through the API."""
    client = _supabase()
    if client is not None:
        try:
            res = client.storage.from_(BUCKET).create_signed_url(key, ttl)
            url = res.get("signedURL") or res.get("signedUrl")
            if url:
                return url
        except Exception:
            pass
    return f"/files/{key}"
