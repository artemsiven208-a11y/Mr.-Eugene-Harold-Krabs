"""Загрузка и проверка настроек из окружения."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    bot_token: str
    max_file_size: int
    max_concurrent_jobs: int
    temp_ttl_minutes: int
    conversion_timeout: int
    libreoffice_path: str | None
    ffmpeg_path: str | None
    temp_root: Path


def _positive_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Параметр {name} должен быть целым числом") from exc
    if value < minimum:
        raise RuntimeError(f"Параметр {name} должен быть не меньше {minimum}")
    return value


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Не указан BOT_TOKEN. Создайте файл .env по примеру .env.example")
    root = Path(os.getenv("TEMP_ROOT", "temp")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return Config(
        bot_token=token,
        max_file_size=_positive_int("MAX_FILE_SIZE_MB", 20) * 1024 * 1024,
        max_concurrent_jobs=_positive_int("MAX_CONCURRENT_JOBS", 3),
        temp_ttl_minutes=_positive_int("TEMP_FILE_TTL_MINUTES", 30),
        conversion_timeout=_positive_int("CONVERSION_TIMEOUT_SECONDS", 120),
        libreoffice_path=os.getenv("LIBREOFFICE_PATH") or None,
        ffmpeg_path=os.getenv("FFMPEG_PATH") or None,
        temp_root=root,
    )
