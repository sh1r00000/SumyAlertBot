import asyncio

from alerts import AlertManager
from logger import logger


async def start_scheduler(bot, channel):
    logger.info("Планировщик запущен.")

    manager = AlertManager()

    while True:
        try:
            await manager.check(bot, channel)

        except Exception as e:
            logger.exception(f"Ошибка в планировщике: {e}")

        await asyncio.sleep(10)