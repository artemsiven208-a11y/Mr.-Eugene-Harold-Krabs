"""Поиск внешних программ, используемых отдельными конвертерами."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil

from utils.config import Config


@dataclass(frozen=True, slots=True)
class ExternalTools:
    libreoffice: str | None
    ffmpeg: str | None


def _find_libreoffice(config: Config) -> str | None:
    candidates = [config.libreoffice_path, shutil.which("libreoffice"), shutil.which("soffice")]
    if os.name == "nt":
        candidates.extend(
            [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        )
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    return None


def detect_external_tools(config: Config) -> ExternalTools:
    ffmpeg = config.ffmpeg_path or shutil.which("ffmpeg")
    return ExternalTools(libreoffice=_find_libreoffice(config), ffmpeg=ffmpeg)
