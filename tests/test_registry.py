from types import SimpleNamespace

from converters.registry import build_registry


def test_registry_hides_optional_tools() -> None:
    tools = SimpleNamespace(libreoffice=None, ffmpeg=None)
    config = SimpleNamespace()
    registry = build_registry(tools, config)
    assert registry.get("png", "jpg") is not None
    assert registry.get("png", "mp3") is None
    assert registry.get("docx", "pdf") is None

