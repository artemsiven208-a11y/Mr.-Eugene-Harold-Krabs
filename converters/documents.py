"""Конвертация текстовых и офисных документов."""

from __future__ import annotations

import html
from html.parser import HTMLParser
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


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1251", errors="replace")


def txt_to_html(context: ConversionContext) -> ConversionResult:
    result = output_path(context, "html")
    paragraphs = [html.escape(line) for line in _read_text(context.source_path).splitlines()]
    body = "\n".join(f"<p>{line}</p>" for line in paragraphs if line) or "<p></p>"
    result.write_text(
        "<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\"><title>Документ</title></head>"
        f"<body>{body}</body></html>",
        encoding="utf-8",
    )
    return ConversionResult(result)


def _docx_document(context: ConversionContext) -> Document:
    try:
        return Document(context.source_path)
    except Exception as exc:
        raise ConversionError("Не удалось прочитать DOCX. Возможно, файл повреждён.") from exc


def _docx_blocks(document: Document) -> list[str]:
    blocks = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        blocks.append("\n".join("\t".join(cell.text for cell in row.cells) for row in table.rows))
    return blocks


def docx_to_pdf(context: ConversionContext) -> ConversionResult:
    document = _docx_document(context)
    text = "\n\n".join(_docx_blocks(document))
    result = _text_to_pdf(context, text)
    return ConversionResult(
        result.path,
        "LibreOffice не найден: сохранены текст и таблицы, сложное форматирование упрощено.",
    )


def docx_to_html(context: ConversionContext) -> ConversionResult:
    document = _docx_document(context)
    parts: list[str] = []
    for paragraph in document.paragraphs:
        if paragraph.text:
            parts.append(f"<p>{html.escape(paragraph.text)}</p>")
    for table in document.tables:
        rows = []
        for row in table.rows:
            cells = "".join(f"<td>{html.escape(cell.text)}</td>" for cell in row.cells)
            rows.append(f"<tr>{cells}</tr>")
        parts.append(f"<table><tbody>{''.join(rows)}</tbody></table>")
    result = output_path(context, "html")
    result.write_text(
        "<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\"><title>Документ</title></head>"
        f"<body>{''.join(parts) or '<p></p>'}</body></html>",
        encoding="utf-8",
    )
    return ConversionResult(result)


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


def md_to_pdf(context: ConversionContext) -> ConversionResult:
    return _text_to_pdf(context, _read_text(context.source_path))


def html_to_txt(context: ConversionContext) -> ConversionResult:
    class TextExtractor(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []

        def handle_data(self, data: str) -> None:
            value = " ".join(data.split())
            if value:
                self.parts.append(value)

    source = _read_text(context.source_path)
    parser = TextExtractor()
    parser.feed(source)
    result = output_path(context, "txt")
    result.write_text("\n".join(parser.parts), encoding="utf-8")
    return ConversionResult(result)


def html_to_pdf(context: ConversionContext) -> ConversionResult:
    text_context = ConversionContext(
        context.source_path,
        context.source_name,
        context.source_format,
        "pdf",
        context.output_dir,
        context.timeout_seconds,
    )
    text_path = html_to_txt(
        ConversionContext(
            context.source_path,
            context.source_name,
            context.source_format,
            "txt",
            context.output_dir,
            context.timeout_seconds,
        )
    ).path
    result = _text_to_pdf(text_context, text_path.read_text(encoding="utf-8"))
    text_path.unlink(missing_ok=True)
    return ConversionResult(
        result.path,
        "HTML преобразован в PDF как безопасный текстовый документ.",
    )


def docx_to_txt(context: ConversionContext) -> ConversionResult:
    document = _docx_document(context)
    chunks = _docx_blocks(document)
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


def rtf_to_pdf(context: ConversionContext) -> ConversionResult:
    raw = context.source_path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"\\'[0-9a-fA-F]{2}", "", raw)
    text = re.sub(r"\\[a-z]+-?\d* ?", "", text)
    text = re.sub(r"[{}]", "", text).replace("\\par", "\n")
    return _text_to_pdf(context, text.strip())


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
