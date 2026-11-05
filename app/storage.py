import os
import hashlib
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def format_file_size(bytes_size: int) -> str:
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    rem_sec = seconds % 60
    if minutes < 60:
        return f"{minutes}m {rem_sec}s"
    hours = minutes // 60
    rem_min = minutes % 60
    return f"{hours}h {rem_min}m"

async def save_upload_file(file, custom_prefix: str = "file") -> tuple[str, str, int, str]:
    """
    Saves an uploaded file to the uploads directory.
    Returns: (relative_path, safe_filename, file_size, sha256_hash)
    """
    safe_name = Path(file.filename).name
    ext = Path(safe_name).suffix
    unique_name = f"{custom_prefix}_{uuid.uuid4().hex[:10]}{ext}"
    dest_path = UPLOAD_DIR / unique_name

    hasher = hashlib.sha256()
    size = 0

    with open(dest_path, "wb") as buffer:
        while chunk := await file.read(1024 * 64):  # 64KB chunks
            buffer.write(chunk)
            hasher.update(chunk)
            size += len(chunk)

    rel_path = f"uploads/{unique_name}"
    return rel_path, safe_name, size, hasher.hexdigest()
