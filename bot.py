import asyncio

from aiogram import Bot

from config import (
    ALERTS_API_KEY,
    API_HASH,
    API_ID,
    BOT_TOKEN,
    CHANNEL_USERNAME,
)
from database import init_database
from logger import logger
from scheduler import start_scheduler
from telegram_monitor import start_telegram_monitor


async def main() -> None:
    logger.info("Запуск Sumy Alert Bot...")

    # Проверяем обязательные переменные
    if not BOT_TOKEN:
        raise RuntimeError("Не указан BOT_TOKEN")

    if not CHANNEL_USERNAME:
        raise RuntimeError("Не указан CHANNEL_USERNAME")

    if not ALERTS_API_KEY:
        raise RuntimeError("Не указан ALERTS_API_KEY")

    if not API_ID:
        raise RuntimeError("Не указан API_ID")

    if not API_HASH:
        raise RuntimeError("Не указан API_HASH")

    # Создаём таблицы базы данных
    init_database()

    bot = Bot(token=BOT_TOKEN)

    logger.info("Telegram-бот успешно создан.")

    # Обычные тревоги и Telegram-мониторинг
    # будут работать одновременно.
    scheduler_task = asyncio.create_task(
        start_scheduler(
            bot,
            CHANNEL_USERNAME,
        ),
        name="alerts_scheduler",
    )

    monitor_task = asyncio.create_task(
        start_telegram_monitor(
            bot,
            CHANNEL_USERNAME,
        ),
        name="telegram_monitor",
    )

    tasks = [
        scheduler_task,
        monitor_task,
    ]

    logger.info(
        "Запущены сервисы: тревоги/отбои и мониторинг угроз."
    )

    try:
        await asyncio.gather(*tasks)

    finally:
        # Корректно останавливаем оба процесса
        for task in tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        await bot.session.close()

        logger.info("Sumy Alert Bot остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем.")

    except Exception as error:
        logger.exception(
            "Критическая ошибка при работе бота: %s",
            error,
        )
        raise