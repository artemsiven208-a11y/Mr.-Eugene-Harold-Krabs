"""Поиск выходного формата с нормализацией и исправлением опечаток."""

from __future__ import annotations

import difflib
import re


ALIASES = {
    "ворд": "docx",
    "word": "docx",
    "документ": "docx",
    "эксель": "xlsx",
    "excel": "xlsx",
    "таблица": "xlsx",
    "изображение": "png",
    "картинка": "png",
    "фото": "jpg",
    "текст": "txt",
    "текстовый файл": "txt",
    "веб-страница": "html",
    "видео": "mp4",
    "аудио": "mp3",
}


def normalize_format(value: str) -> str:
    value = value.strip().lower().replace("ё", "е")
    value = re.sub(r"\s+", " ", value)
    value = value.lstrip(".")
    return ALIASES.get(value, value)


def find_format_candidates(value: str, available: list[str], limit: int = 4) -> list[str]:
    normalized = normalize_format(value)
    if normalized in available:
        return [normalized]
    aliases = {normalize_format(key): val for key, val in ALIASES.items()}
    if normalized in aliases and aliases[normalized] in available:
        return [aliases[normalized]]
    return difflib.get_close_matches(normalized, available, n=limit, cutoff=0.45)
