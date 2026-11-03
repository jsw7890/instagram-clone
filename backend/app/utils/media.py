import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings

ALLOWED = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def upload_root() -> Path:
    root = Path(settings.upload_dir)
    (root / "avatars").mkdir(parents=True, exist_ok=True)
    (root / "posts").mkdir(parents=True, exist_ok=True)
    (root / "stories").mkdir(parents=True, exist_ok=True)
    return root


def save_upload(file: UploadFile, subdir: str) -> str:
    content_type = (file.content_type or "").lower()
    ext = ALLOWED.get(content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="jpeg, png, webp 이미지만 올릴 수 있습니다")
    data = file.file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="파일이 너무 큽니다")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="빈 파일입니다")
    name = f"{uuid.uuid4().hex}{ext}"
    dest = upload_root() / subdir / name
    dest.write_bytes(data)
    return f"/media/{subdir}/{name}"


def delete_media(url: str | None) -> None:
    if not url or not url.startswith("/media/"):
        return
    path = upload_root() / url.replace("/media/", "", 1)
    if path.is_file():
        path.unlink()
