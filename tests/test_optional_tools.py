import shutil
from pathlib import Path

import pytest
from docx import Document

from converters.base import ConversionContext
from converters.documents import libreoffice_convert


@pytest.mark.skipif(
    not (shutil.which("libreoffice") or shutil.which("soffice") or Path(r"C:\Program Files\LibreOffice\program\soffice.exe").is_file()),
    reason="LibreOffice не установлен в окружении тестов",
)
def test_docx_to_pdf_with_libreoffice(tmp_path: Path) -> None:
    source = tmp_path / "document.docx"
    document = Document()
    document.add_paragraph("Проверка LibreOffice")
    document.save(source)
    executable = shutil.which("libreoffice") or shutil.which("soffice") or r"C:\Program Files\LibreOffice\program\soffice.exe"
    result = libreoffice_convert(
        ConversionContext(source, source.name, "docx", "pdf", tmp_path, timeout_seconds=60),
        executable,
    )
    assert result.path.exists()
