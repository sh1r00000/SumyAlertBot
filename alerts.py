from datetime import datetime
from zoneinfo import ZoneInfo

from api import get_sumy_alert
from messages import (
    alert_started_message,
    alert_ended_message,
)
from database import (
    save_active_alert,
    remove_active_alert,
    get_active_alerts,
)
from local_threat_state import set_drone_active
from logger import logger


ALLOWED_LOCATIONS = {
    "Сумський район",
    "м. Суми",
    "Суми",
}


class AlertManager:
    def __init__(self):
        self.active_alert = None

        stored_alerts = get_active_alerts()

        for location, started_at in stored_alerts:
            # Удаляем старые записи других районов,
            # оставшиеся в Railway Volume.
            if location not in ALLOWED_LOCATIONS:
                remove_active_alert(location)

                logger.warning(
                    "Удалена устаревшая тревога "
                    "из базы: %s",
                    location,
                )

                continue

            try:
                parsed_started_at = datetime.fromisoformat(
                    started_at
                )

            except (TypeError, ValueError):
                remove_active_alert(location)

                logger.warning(
                    "Удалена повреждённая запись "
                    "тревоги: %s",
                    location,
                )

                continue

            # Нужна только одна активная тревога.
            if self.active_alert is None:
                self.active_alert = {
                    "location": location,
                    "started_at": parsed_started_at,
                }

                logger.info(
                    "Восстановлена тревога: %s",
                    location,
                )

            else:
                remove_active_alert(location)

                logger.warning(
                    "Удалена лишняя активная "
                    "тревога из базы: %s",
                    location,
                )

    async def check(self, bot, channel):
        try:
            alert = await get_sumy_alert()

        except Exception as error:
            logger.exception(
                "Ошибка API тревог: %s",
                error,
            )
            return

        # Начало воздушной тревоги
        if alert and self.active_alert is None:
            self.active_alert = alert

            save_active_alert(
                alert["location"],
                alert["started_at"].isoformat(),
            )

            await bot.send_message(
                chat_id=channel,
                text=alert_started_message(
                    alert["location"],
                    alert["started_at"],
                ),
                parse_mode="HTML",
            )

            logger.info(
                "🚨 Тревога: %s",
                alert["location"],
            )

            return

        # Пока тревога для Сум или Сумского района
        # остаётся активной — ничего не отправляем.
        if alert and self.active_alert:
            return

        # Официальный отбой воздушной тревоги
        if not alert and self.active_alert:
            end_time = datetime.now(
                ZoneInfo("Europe/Kyiv")
            ).replace(tzinfo=None)

            await bot.send_message(
                chat_id=channel,
                text=alert_ended_message(
                    self.active_alert["location"],
                    self.active_alert["started_at"],
                    end_time,
                ),
                parse_mode="HTML",
            )

            logger.info(
                "✅ Отбой: %s",
                self.active_alert["location"],
            )

            remove_active_alert(
                self.active_alert["location"]
            )

            # После официального отбоя сбрасываем
            # внутренний статус локальной угрозы БпЛА.
            set_drone_active(False)

            self.active_alert = None