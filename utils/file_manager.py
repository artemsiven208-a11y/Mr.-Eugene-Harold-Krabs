"""Безопасные временные каталоги для заданий конвертации."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import re
import shutil
import time
from typing import Iterator
from uuid import uuid4

from utils.config import Config


def safe_filename(name: str, fallback: str = "file") -> str:
    name = Path(name or fallback).name
    name = re.sub(r"[^\w.()\- ]", "_", name, flags=re.UNICODE).strip(" .")
    return name or fallback


def create_job_dir(config: Config) -> Path:
    path = config.temp_root / uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path


def has_disk_space(config: Config, expected_bytes: int) -> bool:
    """Оставляет запас под исходный и выходной файлы."""
    try:
        free_bytes = shutil.disk_usage(config.temp_root).free
    except OSError:
        return False
    return free_bytes >= max(10 * 1024 * 1024, expected_bytes * 2)


def cleanup_job(path: Path | str) -> None:
    try:
        shutil.rmtree(Path(path), ignore_errors=True)
    except OSError:
        pass


def cleanup_stale_jobs(config: Config) -> None:
    cutoff = time.time() - config.temp_ttl_minutes * 60
    if not config.temp_root.exists():
        return
    for child in config.temp_root.iterdir():
        try:
            if child.is_dir() and child.stat().st_mtime < cutoff:
                cleanup_job(child)
        except OSError:
            continue


@contextmanager
def job_directory(config: Config) -> Iterator[Path]:
    path = create_job_dir(config)
    try:
        yield path
    finally:
        cleanup_job(path)
