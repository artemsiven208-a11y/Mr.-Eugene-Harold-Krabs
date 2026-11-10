"""Определение формата файла по имени, MIME и сигнатуре."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import mimetypes


EXTENSION_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "csv": "text/csv",
    "txt": "text/plain",
    "md": "text/markdown",
    "html": "text/html",
}


@dataclass(frozen=True, slots=True)
class FileInfo:
    extension: str
    mime_type: str | None
    category: str


def _category(extension: str) -> str:
    if extension in {"pdf", "docx", "doc", "odt", "rtf", "txt", "md", "html"}:
        return "document"
    if extension in {"xlsx", "xls", "ods", "csv"}:
        return "spreadsheet"
    if extension in {"pptx", "ppt", "odp"}:
        return "presentation"
    if extension in {"png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff", "gif"}:
        return "image"
    if extension in {"mp3", "wav", "ogg", "flac", "m4a", "mp4", "webm", "mov", "mkv"}:
        return "media"
    return "unknown"


def _signature(data: bytes) -> str | None:
    if data.startswith(b"%PDF"):
        return "pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "webp"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data.startswith(b"BM"):
        return "bmp"
    if data.startswith(b"PK\x03\x04"):
        return None  # OOXML, уточняется по расширению.
    if data.startswith(b"ID3") or data[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"}:
        return "mp3"
    return None


def detect_file_type(path: Path, original_name: str | None = None, mime_type: str | None = None) -> FileInfo:
    name = original_name or path.name
    extension = Path(name).suffix.lower().lstrip(".")
    try:
        with path.open("rb") as file:
            signature = _signature(file.read(32))
    except OSError:
        signature = None
    if signature:
        extension = signature
    if not extension and mime_type:
        extension = next((ext for ext, mime in EXTENSION_MIME.items() if mime == mime_type), "")
    if not mime_type:
        mime_type = EXTENSION_MIME.get(extension) or mimetypes.guess_type(name)[0]
    return FileInfo(extension=extension, mime_type=mime_type, category=_category(extension))

