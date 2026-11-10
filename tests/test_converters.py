from pathlib import Path

import fitz
from PIL import Image

from converters.base import ConversionContext
from converters.documents import txt_to_pdf
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
