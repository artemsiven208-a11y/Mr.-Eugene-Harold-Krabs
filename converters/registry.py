"""Единый реестр реальных направлений конвертации."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from converters.base import ConversionContext, ConversionResult
from converters.documents import (
    docx_to_html,
    docx_to_pdf,
    docx_to_txt,
    html_to_pdf,
    html_to_txt,
    libreoffice_convert,
    md_to_html,
    md_to_pdf,
    rtf_to_pdf,
    rtf_to_txt,
    txt_to_html,
    txt_to_pdf,
)
from converters.images import image_to_image
from converters.media import ffmpeg_convert
from converters.pdf import pdf_to_images, pdf_to_txt
from converters.spreadsheets import csv_to_xlsx, xlsx_to_csv
from utils.config import Config
from utils.system_tools import ExternalTools


ConverterFunction = Callable[[ConversionContext], ConversionResult]


@dataclass(frozen=True, slots=True)
class Route:
    source: str
    target: str
    label: str
    converter: ConverterFunction


class ConversionRegistry:
    def __init__(self, routes: list[Route]):
        self._routes = {(route.source, route.target): route for route in routes}

    @property
    def route_count(self) -> int:
        return len(self._routes)

    def options_for(self, source: str) -> list[Route]:
        preferred = {"pdf": 0, "txt": 1, "jpg": 2, "jpeg": 2, "webp": 3, "xlsx": 4, "csv": 5}
        return sorted(
            (route for (origin, _), route in self._routes.items() if origin == source),
            key=lambda route: preferred.get(route.target, 99),
        )

    def get(self, source: str, target: str) -> Route | None:
        return self._routes.get((source, target))

    def available_targets(self) -> list[str]:
        return sorted({target for _, target in self._routes})

    def sources(self) -> list[str]:
        return sorted({source for source, _ in self._routes})

    def convert(self, context: ConversionContext) -> ConversionResult:
        route = self.get(context.source_format, context.target_format)
        if not route:
            raise ValueError("Недоступное направление конвертации")
        return route.converter(context)


def build_registry(tools: ExternalTools, config: Config) -> ConversionRegistry:
    routes: list[Route] = []

    def add(source: str, target: str, label: str, converter: ConverterFunction) -> None:
        routes.append(Route(source, target, label, converter))

    images = ["png", "jpg", "jpeg", "webp", "bmp", "tiff", "gif"]
    for source in images:
        for target in images + ["pdf"]:
            if target != source:
                add(source, target, target.upper(), image_to_image)
    for source in images:
        add(source, "pdf", "PDF", image_to_image)
    add("pdf", "txt", "TXT", pdf_to_txt)
    add("pdf", "png", "PNG", pdf_to_images)
    add("pdf", "jpg", "JPG", pdf_to_images)
    add("txt", "pdf", "PDF", txt_to_pdf)
    add("txt", "html", "HTML", txt_to_html)
    add("md", "html", "HTML", md_to_html)
    add("md", "pdf", "PDF", md_to_pdf)
    add("html", "txt", "TXT", html_to_txt)
    add("html", "pdf", "PDF", html_to_pdf)
    add("docx", "pdf", "PDF", docx_to_pdf)
    add("docx", "txt", "TXT", docx_to_txt)
    add("docx", "html", "HTML", docx_to_html)
    add("rtf", "txt", "TXT", rtf_to_txt)
    add("rtf", "pdf", "PDF", rtf_to_pdf)
    add("csv", "xlsx", "XLSX", csv_to_xlsx)
    add("xlsx", "csv", "CSV", xlsx_to_csv)

    if tools.libreoffice:
        office = lambda context: libreoffice_convert(context, tools.libreoffice)  # noqa: E731
        for source in {"docx", "doc", "odt", "rtf"}:
            add(source, "pdf", "PDF", office)
            if source != "docx":
                add(source, "docx", "DOCX", office)
        add("html", "pdf", "PDF", office)
        add("pdf", "docx", "DOCX", office)
        for source in {"xlsx", "xls", "ods"}:
            add(source, "pdf", "PDF", office)
            if source != "xlsx":
                add(source, "xlsx", "XLSX", office)
        for source in {"pptx", "ppt", "odp"}:
            add(source, "pdf", "PDF", office)
            if source != "pptx":
                add(source, "pptx", "PPTX", office)

    if tools.ffmpeg:
        media_audio = {"mp3", "wav", "ogg", "flac", "m4a"}
        media_video = {"mp4", "webm", "mov", "mkv"}
        media_converter = lambda context: ffmpeg_convert(context, tools.ffmpeg)  # noqa: E731
        for source in media_audio:
            for target in media_audio:
                if target != source:
                    add(source, target, target.upper(), media_converter)
        for source in media_video:
            for target in media_video:
                if target != source:
                    add(source, target, target.upper(), media_converter)
            add(source, "mp3", "MP3 (аудио)", media_converter)

    return ConversionRegistry(routes)
