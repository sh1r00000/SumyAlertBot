from datetime import datetime
from zoneinfo import ZoneInfo

from api import get_alert_status, get_sumy_alert
from messages import (
    alert_started_message,
    alert_ended_message,
    alert_updated_message,
)
from database import (
    save_alert_start,
    save_alert_end,
    get_active_alert,
)
from logger import logger


class AlertManager:
    def __init__(self):
        self.previous_status = None
        self.alert_started = None
        self.current_location = None
        self.location = "Сумська область"

        active_alert = get_active_alert()

        if active_alert:
            self.alert_started = datetime.fromisoformat(active_alert)
            self.previous_status = "A"

            logger.info(
                f"Восстановлена активная тревога с {self.alert_started}"
            )

    async def check(self, bot, channel):
        try:
            status = await get_alert_status()
            alert = await get_sumy_alert()

            if alert:
                self.location = alert["location"]

            if status not in ("A", "P", "N"):
                logger.warning(f"Получен неизвестный статус: {status}")
                return

            logger.info(
                f"Предыдущий: {self.previous_status} | Новый: {status}"
            )

        except Exception as e:
            logger.error(f"Ошибка получения данных API: {e}")
            return

        # ---------------- Начало тревоги ----------------
        if self.previous_status == "N" and status in ("A", "P"):

            if alert:
                self.alert_started = alert["started_at"]
            else:
                self.alert_started = datetime.now(
                    ZoneInfo("Europe/Kyiv")
                ).replace(tzinfo=None)

            self.current_location = self.location

            save_alert_start(
                self.alert_started.isoformat()
            )

            await bot.send_message(
                channel,
                alert_started_message(
                    self.location,
                    self.alert_started
                ),
                parse_mode="HTML"
            )

            logger.info(
                "🚨 Отправлено сообщение о начале тревоги."
            )

        # ---------------- Изменение локации ----------------
        elif (
            self.previous_status in ("A", "P")
            and status in ("A", "P")
        ):

            if (
                self.current_location
                and self.current_location != self.location
            ):
                await bot.send_message(
                    channel,
                    alert_updated_message(
                        self.current_location,
                        self.location
                    ),
                    parse_mode="HTML"
                )

                logger.info(
                    f"Локация изменилась: "
                    f"{self.current_location} -> {self.location}"
                )

                self.current_location = self.location

        # ---------------- Отбой ----------------
        elif (
            self.previous_status in ("A", "P")
            and status == "N"
        ):

            end_time = datetime.now(
                ZoneInfo("Europe/Kyiv")
            ).replace(tzinfo=None)

            if self.alert_started:

                duration = int(
                    (
                        end_time
                        - self.alert_started
                    ).total_seconds()
                )

                save_alert_end(
                    end_time.isoformat(),
                    duration
                )

                await bot.send_message(
                    channel,
                    alert_ended_message(
                        self.location,
                        self.alert_started,
                        end_time
                    ),
                    parse_mode="HTML"
                )

                logger.info(
                    "✅ Отправлено сообщение об отбое тревоги."
                )

            else:
                logger.warning(
                    "Получен отбой, но время начала неизвестно."
                )

            self.alert_started = None
            self.current_location = None

        self.previous_status = status