"""Операции с PDF: текст и растеризация страниц."""

from __future__ import annotations

from pathlib import Path
import zipfile

import fitz

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.documents import output_path


def pdf_to_txt(context: ConversionContext) -> ConversionResult:
    try:
        document = fitz.open(context.source_path)
        text = "\n\n".join(page.get_text() for page in document)
        document.close()
    except Exception as exc:
        raise ConversionError("Не удалось прочитать PDF. Возможно, файл повреждён.") from exc
    result = output_path(context, "txt")
    result.write_text(text, encoding="utf-8")
    warning = None if text.strip() else "В PDF не найден обычный текст. Возможно, это скан без OCR."
    return ConversionResult(result, warning)


def pdf_to_images(context: ConversionContext) -> ConversionResult:
    try:
        document = fitz.open(context.source_path)
        pages = list(document)
        if not pages:
            raise ConversionError("PDF не содержит страниц.")
        outputs: list[Path] = []
        for index, page in enumerate(pages, 1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            path = context.output_dir / f"{Path(context.source_name).stem}_{index}.{context.target_format}"
            pixmap.save(str(path))
            outputs.append(path)
        document.close()
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError("Не удалось преобразовать PDF в изображения.") from exc
    if len(outputs) == 1:
        return ConversionResult(outputs[0])
    archive = context.output_dir / f"{Path(context.source_name).stem}_pages.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in outputs:
            zip_file.write(item, item.name)
    return ConversionResult(archive, "Страницы собраны в ZIP-архив.")
