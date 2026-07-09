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
        self.active_alert = None

        alerts = get_active_alerts()

        if alerts:
            location, started_at = alerts[0]

            self.active_alert = {
                "location": location,
                "started_at": datetime.fromisoformat(
                    started_at
                )
            }

            logger.info(
                f"Восстановлена тревога: "
                f"{location}"
            )

    async def check(self, bot, channel):
        try:
            alert = await get_sumy_alert()

        except Exception as e:
            logger.error(
                f"Ошибка API: {e}"
            )
            return

        # ---------------- Начало тревоги ----------------
        if (
            alert
            and self.active_alert is None
        ):
            self.active_alert = alert

            save_active_alert(
                alert["location"],
                alert["started_at"].isoformat()
            )

            await bot.send_message(
                channel,
                alert_started_message(
                    alert["location"],
                    alert["started_at"]
                ),
                parse_mode="HTML"
            )

            logger.info(
                f"🚨 Тревога: "
                f"{alert['location']}"
            )

        # ---------------- Отбой ----------------
        elif (
            not alert
            and self.active_alert
        ):
            end_time = datetime.now(
                ZoneInfo("Europe/Kyiv")
            ).replace(tzinfo=None)

            await bot.send_message(
                channel,
                alert_ended_message(
                    self.active_alert["location"],
                    self.active_alert["started_at"],
                    end_time
                ),
                parse_mode="HTML"
            )

            logger.info(
                f"✅ Отбой: "
                f"{self.active_alert['location']}"
            )

            remove_active_alert(
                self.active_alert["location"]
            )

            self.active_alert = None