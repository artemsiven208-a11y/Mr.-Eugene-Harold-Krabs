"""Базовые типы для конвертеров."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ConversionError(Exception):
    """Ошибка, которую можно безопасно показать пользователю."""


class ToolUnavailable(ConversionError):
    """Для операции не найден обязательный внешний инструмент."""


@dataclass(frozen=True, slots=True)
class ConversionContext:
    source_path: Path
    source_name: str
    source_format: str
    target_format: str
    output_dir: Path
    timeout_seconds: int = 120


@dataclass(frozen=True, slots=True)
class ConversionResult:
    path: Path
    warning: str | None = None
