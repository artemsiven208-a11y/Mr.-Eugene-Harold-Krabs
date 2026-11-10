"""Конвертация CSV и XLSX."""

from __future__ import annotations

import csv
from pathlib import Path
import zipfile

from openpyxl import Workbook, load_workbook

from converters.base import ConversionContext, ConversionError, ConversionResult
from converters.documents import output_path


def csv_to_xlsx(context: ConversionContext) -> ConversionResult:
    result = output_path(context, "xlsx")
    workbook = Workbook()
    sheet = workbook.active
    try:
        with context.source_path.open("r", encoding="utf-8-sig", newline="") as source:
            for row in csv.reader(source):
                sheet.append(row)
    except UnicodeDecodeError:
        with context.source_path.open("r", encoding="cp1251", newline="") as source:
            for row in csv.reader(source):
                sheet.append(row)
    workbook.save(result)
    return ConversionResult(result)


def xlsx_to_csv(context: ConversionContext) -> ConversionResult:
    try:
        workbook = load_workbook(context.source_path, read_only=True, data_only=True)
    except Exception as exc:
        raise ConversionError("Не удалось прочитать таблицу XLSX.") from exc
    sheets = workbook.worksheets
    if len(sheets) == 1:
        result = output_path(context, "csv")
        with result.open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.writer(target)
            for row in sheets[0].iter_rows(values_only=True):
                writer.writerow(["" if value is None else value for value in row])
        workbook.close()
        return ConversionResult(result)
    archive = context.output_dir / f"{Path(context.source_name).stem}_sheets.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for sheet in sheets:
            csv_path = context.output_dir / f"{sheet.title}.csv"
            with csv_path.open("w", encoding="utf-8-sig", newline="") as target:
                writer = csv.writer(target)
                for row in sheet.iter_rows(values_only=True):
                    writer.writerow(["" if value is None else value for value in row])
            zip_file.write(csv_path, csv_path.name)
    workbook.close()
    return ConversionResult(archive, "Листы собраны в ZIP-архив.")

