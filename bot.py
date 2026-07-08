import asyncio

from aiogram import Bot

from config import ALERTS_API_KEY, BOT_TOKEN, CHANNEL_USERNAME
from scheduler import start_scheduler
from database import init_database
from logger import logger


async def main():
    logger.info("Запуск Sumy Alert Bot...")

    if not BOT_TOKEN:
        raise RuntimeError("Не указан BOT_TOKEN в .env")

    if not CHANNEL_USERNAME:
        raise RuntimeError("Не указан CHANNEL_USERNAME в .env")

    if not ALERTS_API_KEY:
        raise RuntimeError("Не указан ALERTS_API_KEY в .env")

    init_database()

    bot = Bot(BOT_TOKEN)

    logger.info("Бот успешно запущен.")

    try:
        await start_scheduler(bot, CHANNEL_USERNAME)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем.")
