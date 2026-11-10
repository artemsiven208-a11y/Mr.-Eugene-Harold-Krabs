"""Конвертация изображений с корректной обработкой прозрачности и EXIF."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.documents import output_path


def image_to_image(context: ConversionContext) -> ConversionResult:
    try:
        image = ImageOps.exif_transpose(Image.open(context.source_path))
    except Exception as exc:
        raise ConversionError("Не удалось прочитать изображение. Файл может быть повреждён.") from exc
    warning = None
    target = context.target_format
    if getattr(image, "is_animated", False) and target != "gif":
        warning = "У GIF сохранён только первый кадр."
        image.seek(0)
    if target in {"jpg", "jpeg"}:
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            background = Image.new("RGB", image.size, "white")
            alpha = image.convert("RGBA")
            background.paste(alpha, mask=alpha.getchannel("A"))
            image = background
        else:
            image = image.convert("RGB")
    elif target == "pdf":
        image = image.convert("RGB")
    result = output_path(context, target)
    save_format = "JPEG" if target in {"jpg", "jpeg"} else target.upper()
    save_kwargs = {"quality": 92} if save_format == "JPEG" else {}
    image.save(result, format=save_format, **save_kwargs)
    image.close()
    return ConversionResult(result, warning)
