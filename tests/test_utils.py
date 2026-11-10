from pathlib import Path

from utils.file_detection import detect_file_type
from utils.format_search import find_format_candidates, normalize_format


def test_detect_png_by_signature(tmp_path: Path) -> None:
    path = tmp_path / "unknown.bin"
    path.write_bytes(b"\x89PNG\r\n\x1a\nrest")
    info = detect_file_type(path, "unknown.bin", "application/octet-stream")
    assert info.extension == "png"
    assert info.category == "image"


def test_format_search_typo_and_alias() -> None:
    assert find_format_candidates("jepg", ["jpg", "webp"])[0] == "jpg"
    assert normalize_format(".ВОРД") == "docx"

