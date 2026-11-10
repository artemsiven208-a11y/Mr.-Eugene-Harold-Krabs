"""Точка входа Telegram-бота-конвертера."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.handlers.commands import router as commands_router
from bot.handlers.files import router as files_router
from bot.handlers.search import router as search_router
from bot.states import router as state_router
from converters.registry import build_registry
from utils.config import load_config
from utils.file_manager import cleanup_stale_jobs
from utils.system_tools import detect_external_tools

logger = logging.getLogger(__name__)


async def configure_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Запустить бота"),
            BotCommand(command="help", description="Как пользоваться ботом"),
            BotCommand(command="formats", description="Доступные форматы"),
            BotCommand(command="cancel", description="Отменить текущую операцию"),
        ]
    )


async def run() -> None:
    config = load_config()
    tools = detect_external_tools(config)
    registry = build_registry(tools, config)
    cleanup_stale_jobs(config)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp["config"] = config
    dp["registry"] = registry
    dp["tools"] = tools
    dp["job_semaphore"] = asyncio.Semaphore(config.max_concurrent_jobs)
    dp.include_router(commands_router)
    dp.include_router(files_router)
    dp.include_router(search_router)
    dp.include_router(state_router)

    await configure_commands(bot)
    logger.info(
        "Бот запущен. LibreOffice: %s, FFmpeg: %s, маршрутов: %d",
        "доступен" if tools.libreoffice else "не найден",
        "доступен" if tools.ffmpeg else "не найден",
        registry.route_count,
    )
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception:
        logger.exception("Бот завершился из-за ошибки запуска")
        sys.exit(1)


if __name__ == "__main__":
    main()

