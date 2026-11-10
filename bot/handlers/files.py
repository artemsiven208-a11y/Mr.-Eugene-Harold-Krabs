"""Приём файлов и запуск конвертаций."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.keyboards import conversion_keyboard
from bot.states import ConversionStates, clear_job_state
from converters.base import ConversionContext, ConversionError
from converters.registry import ConversionRegistry
from utils.config import Config
from utils.file_detection import FileInfo, detect_file_type
from utils.file_manager import create_job_dir, has_disk_space, safe_filename

logger = logging.getLogger(__name__)
router = Router(name="files")


def _size_text(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} МБ"
    return f"{max(1, size // 1024)} КБ"


def _received_text(name: str, info: FileInfo, size: int) -> str:
    return (
        "<b>Файл получен</b>\n\n"
        f"Название: {name}\n"
        f"Формат: {info.extension.upper() or 'не определён'}\n"
        f"Размер: {_size_text(size)}\n\n"
        "<b>Во что конвертировать?</b>"
    )


async def receive_file(
    message: Message,
    state: FSMContext,
    bot,
    config: Config,
    registry: ConversionRegistry,
    file_id: str,
    original_name: str,
    mime_type: str | None,
    file_size: int | None,
) -> None:
    if file_size and file_size > config.max_file_size:
        await message.answer(
            f"Файл слишком большой. Максимальный размер: {config.max_file_size // 1024 // 1024} МБ."
        )
        return
    if not has_disk_space(config, file_size or config.max_file_size):
        await message.answer("На диске недостаточно места для обработки файла.")
        return
    await clear_job_state(state)
    job_dir = create_job_dir(config)
    safe_name = safe_filename(original_name)
    source_path = job_dir / safe_name
    try:
        telegram_file = await bot.get_file(file_id)
        if not telegram_file.file_path:
            raise RuntimeError("Telegram не вернул путь к файлу")
        await bot.download_file(telegram_file.file_path, destination=source_path)
        actual_size = source_path.stat().st_size
    except Exception:
        logger.exception("Не удалось скачать файл из Telegram")
        from utils.file_manager import cleanup_job

        cleanup_job(job_dir)
        await message.answer("Не удалось скачать файл. Попробуйте отправить его ещё раз.")
        return
    if actual_size > config.max_file_size:
        from utils.file_manager import cleanup_job

        cleanup_job(job_dir)
        await message.answer(
            f"Файл слишком большой. Максимальный размер: {config.max_file_size // 1024 // 1024} МБ."
        )
        return
    info = detect_file_type(source_path, safe_name, mime_type)
    routes = registry.options_for(info.extension)
    if not routes:
        from utils.file_manager import cleanup_job

        cleanup_job(job_dir)
        await message.answer(
            f"Формат {info.extension.upper() or 'файла'} пока не поддерживается. "
            "Отправьте файл в другом формате."
        )
        return
    await state.update_data(
        job_dir=str(job_dir),
        source_path=str(source_path),
        source_name=safe_name,
        source_format=info.extension,
        source_category=info.category,
        menu_message_id=None,
    )
    await state.set_state(ConversionStates.processing)
    sent = await message.answer(_received_text(safe_name, info, actual_size), reply_markup=conversion_keyboard(routes))
    await state.update_data(menu_message_id=sent.message_id)


@router.message(F.document)
async def document_handler(message: Message, state: FSMContext, bot, config: Config, registry: ConversionRegistry) -> None:
    document = message.document
    await receive_file(
        message,
        state,
        bot,
        config,
        registry,
        document.file_id,
        document.file_name or "document",
        document.mime_type,
        document.file_size,
    )


@router.message(F.photo)
async def photo_handler(message: Message, state: FSMContext, bot, config: Config, registry: ConversionRegistry) -> None:
    photo = message.photo[-1]
    await receive_file(
        message,
        state,
        bot,
        config,
        registry,
        photo.file_id,
        f"photo_{message.message_id}.jpg",
        "image/jpeg",
        photo.file_size,
    )


@router.message(F.audio)
async def audio_handler(message: Message, state: FSMContext, bot, config: Config, registry: ConversionRegistry) -> None:
    audio = message.audio
    await receive_file(
        message,
        state,
        bot,
        config,
        registry,
        audio.file_id,
        audio.file_name or "audio.mp3",
        audio.mime_type,
        audio.file_size,
    )


@router.message(F.video)
async def video_handler(message: Message, state: FSMContext, bot, config: Config, registry: ConversionRegistry) -> None:
    video = message.video
    await receive_file(
        message,
        state,
        bot,
        config,
        registry,
        video.file_id,
        video.file_name or "video.mp4",
        video.mime_type,
        video.file_size,
    )


async def start_conversion(callback: CallbackQuery, target: str, state: FSMContext, registry: ConversionRegistry, config: Config, semaphore: asyncio.Semaphore) -> None:
    data = await state.get_data()
    source_path = data.get("source_path")
    source_format = data.get("source_format")
    if not source_path or not source_format:
        await callback.answer("Сначала отправьте файл", show_alert=True)
        return
    route = registry.get(source_format, target)
    if not route:
        await callback.answer("Это направление недоступно", show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(f"Конвертирую файл в {target.upper()}…")
    await state.set_state(ConversionStates.processing)
    context = ConversionContext(
        source_path=Path(source_path),
        source_name=data["source_name"],
        source_format=source_format,
        target_format=target,
        output_dir=Path(data["job_dir"]),
        timeout_seconds=config.conversion_timeout,
    )
    try:
        async with semaphore:
            result = await asyncio.to_thread(registry.convert, context)
    except ConversionError as exc:
        logger.warning("Конвертация %s -> %s завершилась ошибкой: %s", source_format, target, exc)
        if callback.message:
            await callback.message.edit_text(str(exc), reply_markup=conversion_keyboard(registry.options_for(source_format)))
        return
    except Exception:
        logger.exception("Неожиданная ошибка конвертации %s -> %s", source_format, target)
        if callback.message:
            await callback.message.edit_text("Не удалось завершить конвертацию. Попробуйте ещё раз.")
        return
    caption = f"Готово. Файл конвертирован в {target.upper()}."
    if result.warning:
        caption += f"\n{result.warning}"
    try:
        if callback.message:
            await callback.message.answer_document(FSInputFile(result.path), caption=caption)
            await callback.message.edit_text(
                "Выберите ещё один формат для этого файла:",
                reply_markup=conversion_keyboard(registry.options_for(source_format)),
            )
    except Exception:
        logger.exception("Не удалось отправить результат пользователю")
        if callback.message:
            await callback.message.edit_text("Файл готов, но Telegram не смог его отправить. Попробуйте ещё раз.")


@router.callback_query(F.data.startswith("convert:"))
async def convert_callback(callback: CallbackQuery, state: FSMContext, registry: ConversionRegistry, config: Config, job_semaphore: asyncio.Semaphore) -> None:
    target = callback.data.split(":", 1)[1]
    await start_conversion(callback, target, state, registry, config, job_semaphore)


@router.callback_query(F.data.startswith("search_pick:"))
async def search_pick_callback(callback: CallbackQuery, state: FSMContext, registry: ConversionRegistry, config: Config, job_semaphore: asyncio.Semaphore) -> None:
    target = callback.data.split(":", 1)[1]
    await start_conversion(callback, target, state, registry, config, job_semaphore)

