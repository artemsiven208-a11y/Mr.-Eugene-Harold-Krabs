"""Клавиатуры Telegram-интерфейса."""

from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from converters.registry import Route


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поддерживаемые форматы"), KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def conversion_keyboard(routes: list[Route]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for route in routes:
        builder.button(text=route.label, callback_data=f"convert:{route.target}")
    builder.adjust(3)
    builder.button(text="Другой формат 🔎", callback_data="search:other")
    builder.button(text="Отмена", callback_data="cancel")
    builder.adjust(3, 1, 1)
    return builder.as_markup()


def search_confirmation(target: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Да, {target.upper()}", callback_data=f"search_pick:{target}")
    builder.button(text="Другие варианты", callback_data="search:other")
    builder.button(text="Отмена", callback_data="cancel")
    builder.adjust(1, 1, 1)
    return builder.as_markup()
