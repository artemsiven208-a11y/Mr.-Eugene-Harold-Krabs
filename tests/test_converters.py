from pathlib import Path

import fitz
from PIL import Image
from docx import Document

from converters.base import ConversionContext
from converters.documents import docx_to_pdf, txt_to_pdf
from converters.images import image_to_image
from converters.pdf import pdf_to_txt


def context(source: Path, target: str, output: Path) -> ConversionContext:
    return ConversionContext(source, source.name, source.suffix.lstrip("."), target, output)


def test_png_transparency_to_jpg(tmp_path: Path) -> None:
    source = tmp_path / "прозрачный.png"
    Image.new("RGBA", (10, 10), (255, 0, 0, 0)).save(source)
    result = image_to_image(context(source, "jpg", tmp_path))
    converted = Image.open(result.path)
    assert converted.mode == "RGB"
    assert converted.getpixel((0, 0)) == (255, 255, 255)


def test_jpg_to_webp(tmp_path: Path) -> None:
    source = tmp_path / "photo.jpg"
    Image.new("RGB", (10, 10), "blue").save(source)
    result = image_to_image(context(source, "webp", tmp_path))
    assert result.path.suffix == ".webp"
    assert Image.open(result.path).format == "WEBP"


def test_txt_pdf_and_pdf_txt_with_russian_text(tmp_path: Path) -> None:
    source = tmp_path / "текст.txt"
    source.write_text("Привет, мир!\nВторая строка.", encoding="utf-8")
    pdf = txt_to_pdf(context(source, "pdf", tmp_path))
    document = fitz.open(pdf.path)
    assert document.page_count == 1
    document.close()
    extracted = pdf_to_txt(context(pdf.path, "txt", tmp_path))
    assert "Привет" in extracted.path.read_text(encoding="utf-8")


def test_docx_to_pdf_without_libreoffice(tmp_path: Path) -> None:
    source = tmp_path / "документ.docx"
    document = Document()
    document.add_paragraph("Документ для PDF")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Левая ячейка"
    table.rows[0].cells[1].text = "Правая ячейка"
    document.save(source)
    result = docx_to_pdf(context(source, "pdf", tmp_path))
    extracted = "\n".join(page.get_text() for page in fitz.open(result.path)).replace("\xa0", " ")
    assert "Документ для PDF" in extracted
    assert "Левая ячейка" in extracted
