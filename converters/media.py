"""Конвертация аудио и видео через FFmpeg."""

from __future__ import annotations

from pathlib import Path
import subprocess

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.documents import output_path


def ffmpeg_convert(context: ConversionContext, executable: str) -> ConversionResult:
    result = output_path(context, context.target_format)
    command = [executable, "-y", "-i", str(context.source_path)]
    if context.target_format == "mp3" and context.source_format in {"mp4", "webm", "mov", "mkv"}:
        command += ["-vn", "-codec:a", "libmp3lame", "-q:a", "2"]
    elif context.target_format in {"mp3", "wav", "ogg", "flac", "m4a"}:
        command += ["-vn"]
    command.append(str(result))
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            timeout=context.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ConversionError("Конвертация превысила допустимое время.") from exc
    if completed.returncode != 0 or not result.exists():
        raise ConversionError("FFmpeg не смог обработать этот медиафайл.")
    return ConversionResult(result)

