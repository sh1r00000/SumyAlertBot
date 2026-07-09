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
from logger import logger


class AlertManager:
    def __init__(self):
        self.active_alerts = {}

        db_alerts = get_active_alerts()

        for location, started_at in db_alerts:
            self.active_alerts[location] = (
                datetime.fromisoformat(started_at)
            )

        if self.active_alerts:
            logger.info(
                f"Восстановлено активных тревог: "
                f"{len(self.active_alerts)}"
            )

    async def check(self, bot, channel):
        try:
            api_alerts = await get_sumy_alert()

            current_alerts = {}

            for alert in api_alerts:
                current_alerts[
                    alert["location"]
                ] = alert["started_at"]

        except Exception as e:
            logger.error(
                f"Ошибка получения данных API: {e}"
            )
            return

        # ---------------- Новые тревоги ----------------
        for location, started_at in current_alerts.items():

            if location not in self.active_alerts:

                self.active_alerts[
                    location
                ] = started_at

                save_active_alert(
                    location,
                    started_at.isoformat()
                )

                await bot.send_message(
                    channel,
                    alert_started_message(
                        location,
                        started_at
                    ),
                    parse_mode="HTML"
                )

                logger.info(
                    f"🚨 Новая тревога: "
                    f"{location}"
                )

        # ---------------- Отбой ----------------
        finished_alerts = []

        for location, started_at in self.active_alerts.items():

            if location not in current_alerts:

                end_time = datetime.now(
                    ZoneInfo("Europe/Kyiv")
                ).replace(tzinfo=None)

                await bot.send_message(
                    channel,
                    alert_ended_message(
                        location,
                        started_at,
                        end_time
                    ),
                    parse_mode="HTML"
                )

                logger.info(
                    f"✅ Отбой: {location}"
                )

                remove_active_alert(
                    location
                )

                finished_alerts.append(
                    location
                )

        for location in finished_alerts:
            del self.active_alerts[
                location
            ]