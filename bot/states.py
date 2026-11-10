"""Состояния FSM и очистка временных данных задания."""

from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.keyboards import main_keyboard
from utils.file_manager import cleanup_job

router = Router(name="fallback")


class ConversionStates(StatesGroup):
    waiting_format = State()
    processing = State()


async def clear_job_state(state: FSMContext) -> None:
    data = await state.get_data()
    job_dir = data.get("job_dir")
    if job_dir:
        cleanup_job(job_dir)
    await state.clear()


@router.message()
async def fallback(message: Message) -> None:
    if message.text and message.text.startswith("/"):
        return
    await message.answer("Отправьте файл, который нужно конвертировать.", reply_markup=main_keyboard())

