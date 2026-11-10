"""Команды бота и главное меню."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.keyboards import main_keyboard
from bot.states import clear_job_state
from converters.registry import ConversionRegistry

router = Router(name="commands")


START_TEXT = (
    "<b>Конвертер файлов</b>\n\n"
    "Отправьте документ, изображение или другой файл, а я предложу доступные форматы и конвертирую его.\n\n"
    "Можно также пересылать файлы из других чатов."
)


@router.message(Command("start"))
async def start(message: Message, state: FSMContext) -> None:
    await clear_job_state(state)
    await message.answer(START_TEXT, reply_markup=main_keyboard())


@router.message(Command("help"))
@router.message(F.text == "Помощь")
async def help_command(message: Message) -> None:
    await message.answer(
        "Отправьте файл сообщением. Бот определит формат, покажет доступные направления и вернёт результат.\n\n"
        "Команды: /start, /formats, /cancel.\n"
        "Если нужного формата нет в кнопках, выберите «Другой формат»."
    )


@router.message(Command("formats"))
@router.message(F.text == "Поддерживаемые форматы")
async def formats_command(message: Message, registry: ConversionRegistry) -> None:
    grouped: dict[str, list[str]] = {}
    for source in registry.sources():
        targets = [route.target.upper() for route in registry.options_for(source)]
        if targets:
            grouped[source.upper()] = targets
    if not grouped:
        await message.answer("Сейчас доступных конвертаций нет.")
        return
    lines = ["<b>Доступные направления</b>"]
    lines.extend(f"{source} → {', '.join(targets)}" for source, targets in sorted(grouped.items()))
    await message.answer("\n".join(lines))


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext) -> None:
    await clear_job_state(state)
    await message.answer("Текущая операция отменена.", reply_markup=main_keyboard())


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await clear_job_state(state)
    await callback.answer("Операция отменена")
    if callback.message:
        await callback.message.edit_text("Операция отменена.")
