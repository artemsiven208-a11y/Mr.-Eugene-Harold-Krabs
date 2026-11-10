"""Поиск формата по тексту и исправление опечаток."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards import conversion_keyboard, search_confirmation
from bot.states import ConversionStates
from converters.registry import ConversionRegistry
from utils.format_search import find_format_candidates, normalize_format

router = Router(name="format-search")


@router.callback_query(F.data == "search:other")
async def search_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ConversionStates.waiting_format)
    await callback.answer()
    if callback.message:
        await callback.message.edit_text("Напишите расширение или название формата, например: pdf, jpeg или ворд.")


@router.message(ConversionStates.waiting_format, F.text)
async def search_format(message: Message, state: FSMContext, registry: ConversionRegistry) -> None:
    data = await state.get_data()
    source = data.get("source_format")
    if not source:
        await state.clear()
        await message.answer("Сначала отправьте файл.")
        return
    routes = registry.options_for(source)
    available = [route.target for route in routes]
    candidates = find_format_candidates(message.text, available)
    if not candidates:
        await message.answer(
            f"Не нашёл подходящий формат «{message.text}». Доступные варианты: "
            + ", ".join(target.upper() for target in available),
            reply_markup=conversion_keyboard(routes),
        )
        await state.set_state(ConversionStates.processing)
        return
    if len(candidates) == 1 and normalize_format(message.text) == candidates[0]:
        await message.answer(
            f"Нашёл доступную конвертацию в {candidates[0].upper()}. Подтвердить?",
            reply_markup=search_confirmation(candidates[0]),
        )
        return
    await message.answer(
        f"Возможно, ты имел в виду {candidates[0].upper()}?",
        reply_markup=search_confirmation(candidates[0]),
    )

