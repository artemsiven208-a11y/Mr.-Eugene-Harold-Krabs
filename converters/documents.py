"""Конвертация текстовых и офисных документов."""

from __future__ import annotations

import html
from pathlib import Path
import re
import subprocess

import fitz
from docx import Document

from converters.base import ConversionContext, ConversionError, ConversionResult


def output_path(context: ConversionContext, extension: str | None = None) -> Path:
    suffix = extension or context.target_format
    stem = Path(context.source_name).stem or "file"
    return context.output_dir / f"{stem}.{suffix}"


def _font_path() -> str | None:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
    ]
    return next((str(path) for path in candidates if path.is_file()), None)


def _text_to_pdf(context: ConversionContext, text: str) -> ConversionResult:
    result = output_path(context, "pdf")
    document = fitz.open()
    fontfile = _font_path()
    lines = text.splitlines() or [""]
    page = document.new_page()
    rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
    kwargs = {"fontname": "helv", "fontsize": 11, "lineheight": 1.25}
    if fontfile:
        kwargs["fontfile"] = fontfile
        kwargs["fontname"] = "appfont"
    current = ""
    for line in lines:
        trial = f"{current}{line}\n"
        if len(trial.splitlines()) > 48:
            page.insert_textbox(rect, current, color=(0, 0, 0), **kwargs)
            page = document.new_page()
            current = f"{line}\n"
        else:
            current = trial
    page.insert_textbox(rect, current, color=(0, 0, 0), **kwargs)
    document.save(result)
    document.close()
    return ConversionResult(result)


def txt_to_pdf(context: ConversionContext) -> ConversionResult:
    try:
        text = context.source_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = context.source_path.read_text(encoding="cp1251", errors="replace")
    return _text_to_pdf(context, text)


def md_to_html(context: ConversionContext) -> ConversionResult:
    try:
        source = context.source_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        source = context.source_path.read_text(encoding="cp1251", errors="replace")
    rendered: list[str] = []
    for line in source.splitlines():
        escaped = html.escape(line)
        if line.startswith("### "):
            rendered.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            rendered.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            rendered.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("- "):
            rendered.append(f"<li>{html.escape(line[2:])}</li>")
        elif line:
            rendered.append(f"<p>{escaped}</p>")
    result = output_path(context, "html")
    result.write_text(
        "<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\"><title>Документ</title></head><body>"
        + "\n".join(rendered)
        + "</body></html>",
        encoding="utf-8",
    )
    return ConversionResult(result)


def docx_to_txt(context: ConversionContext) -> ConversionResult:
    try:
        document = Document(context.source_path)
    except Exception as exc:
        raise ConversionError("Не удалось прочитать DOCX. Возможно, файл повреждён.") from exc
    chunks = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        chunks.extend("\t".join(cell.text for cell in row.cells) for row in table.rows)
    result = output_path(context, "txt")
    result.write_text("\n".join(chunks), encoding="utf-8")
    return ConversionResult(result)


def rtf_to_txt(context: ConversionContext) -> ConversionResult:
    raw = context.source_path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"\\'[0-9a-fA-F]{2}", "", raw)
    text = re.sub(r"\\[a-z]+-?\d* ?", "", text)
    text = re.sub(r"[{}]", "", text).replace("\\par", "\n")
    result = output_path(context, "txt")
    result.write_text(text.strip(), encoding="utf-8")
    return ConversionResult(result)


def libreoffice_convert(context: ConversionContext, executable: str) -> ConversionResult:
    target = context.target_format
    command = [
        executable,
        "--headless",
        "--convert-to",
        target,
        "--outdir",
        str(context.output_dir),
        str(context.source_path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=context.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ConversionError("Конвертация превысила допустимое время.") from exc
    if completed.returncode != 0:
        raise ConversionError("LibreOffice не смог обработать этот документ.")
    expected = context.output_dir / f"{context.source_path.stem}.{target}"
    if not expected.exists():
        candidates = list(context.output_dir.glob(f"{context.source_path.stem}.*"))
        if not candidates:
            raise ConversionError("LibreOffice не создал выходной файл.")
        expected = candidates[0]
    return ConversionResult(expected)

