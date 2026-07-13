import re
import time

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from config import (
    API_HASH,
    API_ID,
    TELEGRAM_SESSION,
)
from local_threat_state import (
    is_drone_active,
    set_drone_active,
)
from logger import logger
from sumygo_parser import parse_sumygo_message
from threat_parser import extract_sumy_events


OFFICIAL_CHANNEL = "kpszsu"
MONITORING_CHANNEL = "sumygo"

PUBLIC_CHANNEL_TAG = "@sumy_alert1"

DUPLICATE_SECONDS = 3 * 60

recent_messages: dict[str, float] = {}


EVENT_ICONS = {
    "drone": "🛸",
    "missile": "🚀",
    "kab": "💣",
    "aviation": "✈️",
    "clear": "✅",
    "general": "⚠️",
}


def _normalize_text(text: str) -> str:
    text = text.casefold()
    text = re.sub(r"\s+", " ", text)

    text = re.sub(
        r"[^\wа-яіїєґ0-9 ]",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()


def _remove_old_duplicates(
    now: float,
) -> None:
    expired = [
        key
        for key, created_at
        in recent_messages.items()
        if now - created_at
        > DUPLICATE_SECONDS
    ]

    for key in expired:
        recent_messages.pop(key, None)


def _is_duplicate(text: str) -> bool:
    now = time.monotonic()

    _remove_old_duplicates(now)

    key = _normalize_text(text)

    if not key:
        return True

    previous_time = recent_messages.get(key)

    if (
        previous_time is not None
        and now - previous_time
        <= DUPLICATE_SECONDS
    ):
        return True

    recent_messages[key] = now

    return False


def _strip_leading_symbols(
    text: str,
) -> str:
    return re.sub(
        r"^[^\wА-Яа-яІіЇїЄєҐґ0-9]+",
        "",
        text,
    ).strip()


def _build_official_message(
    event_data: dict,
) -> str:
    event_type = event_data["type"]
    lines = event_data["lines"]

    icon = EVENT_ICONS.get(
        event_type,
        "⚠️",
    )

    cleaned_lines = [
        cleaned
        for line in lines
        if (
            cleaned
            := _strip_leading_symbols(line)
        )
    ]

    body = "\n".join(cleaned_lines)

    return (
        f"{icon} {body}\n\n"
        f"👉 {PUBLIC_CHANNEL_TAG}"
    )


def _build_monitoring_message(
    action: str,
) -> str:
    if action == "multiple":
        return (
            "ℹ️ За даними моніторингового "
            "каналу SUMY GO, у районі Сум "
            "фіксується декілька БпЛА.\n\n"
            "⚠️ Інформація не є офіційним "
            "повідомленням Повітряних сил.\n\n"
            f"👉 {PUBLIC_CHANNEL_TAG}"
        )

    return (
        "✅ За даними моніторингового "
        "каналу SUMY GO, БпЛА у районі "
        "Сум наразі не фіксуються.\n\n"
        "⚠️ Це не офіційний відбій "
        "повітряної тривоги. Перебувайте "
        "в укритті до офіційного відбою.\n\n"
        f"👉 {PUBLIC_CHANNEL_TAG}"
    )


async def start_telegram_monitor(
    bot,
    channel: str,
) -> None:
    if not API_ID:
        raise RuntimeError(
            "Не указан API_ID"
        )

    if not API_HASH:
        raise RuntimeError(
            "Не указан API_HASH"
        )

    if TELEGRAM_SESSION:
        session = StringSession(
            TELEGRAM_SESSION.strip()
        )
    else:
        session = "sumy_monitor"

    client = TelegramClient(
        session,
        API_ID,
        API_HASH,
    )

    async def process_official(
        event,
    ) -> None:
        try:
            message = event.raw_text or ""

            if not message.strip():
                return

            sumy_events = extract_sumy_events(
                message
            )

            if not sumy_events:
                return

            for event_data in sumy_events:
                event_type = event_data["type"]

                if event_type == "drone":
                    set_drone_active(True)

                # Редкий случай, когда официальный
                # источник прямо сообщает,
                # что БпЛА больше нет.
                if (
                    event_type == "clear"
                    and re.search(
                        r"\b(?:бпла|шахед\w*|"
                        r"дрон\w*)\b",
                        message,
                        flags=re.IGNORECASE,
                    )
                ):
                    set_drone_active(False)

                channel_message = (
                    _build_official_message(
                        event_data
                    )
                )

                if _is_duplicate(
                    channel_message
                ):
                    logger.info(
                        "Пропущен дубль "
                        "официального сообщения: "
                        "type=%s",
                        event_type,
                    )
                    continue

                await bot.send_message(
                    chat_id=channel,
                    text=channel_message,
                )

                logger.info(
                    "Опубликовано официальное "
                    "сообщение: type=%s",
                    event_type,
                )

        except Exception as error:
            logger.exception(
                "Ошибка обработки канала "
                "Воздушных сил: %s",
                error,
            )

    async def process_monitoring(
        event,
    ) -> None:
        try:
            # SUMY GO не открывает угрозу.
            # Он используется только после
            # сообщения официального источника.
            if not is_drone_active():
                return

            message = event.raw_text or ""

            monitoring_event = (
                parse_sumygo_message(message)
            )

            if monitoring_event is None:
                return

            action = monitoring_event["action"]

            channel_message = (
                _build_monitoring_message(
                    action
                )
            )

            if _is_duplicate(channel_message):
                logger.info(
                    "Пропущен дубль сообщения "
                    "SUMY GO: action=%s",
                    action,
                )
                return

            await bot.send_message(
                chat_id=channel,
                text=channel_message,
            )

            if action == "clear":
                set_drone_active(False)

            logger.info(
                "Опубликовано сообщение "
                "SUMY GO: action=%s",
                action,
            )

        except Exception as error:
            logger.exception(
                "Ошибка обработки SUMY GO: %s",
                error,
            )

    for event_builder in (
        events.NewMessage(
            chats=[OFFICIAL_CHANNEL]
        ),
        events.MessageEdited(
            chats=[OFFICIAL_CHANNEL]
        ),
    ):
        client.add_event_handler(
            process_official,
            event_builder,
        )

    for event_builder in (
        events.NewMessage(
            chats=[MONITORING_CHANNEL]
        ),
        events.MessageEdited(
            chats=[MONITORING_CHANNEL]
        ),
    ):
        client.add_event_handler(
            process_monitoring,
            event_builder,
        )

    logger.info(
        "Подключение к каналам "
        "kpszsu и sumygo..."
    )

    try:
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError(
                "Telegram-сессия не "
                "авторизована. Проверь "
                "TELEGRAM_SESSION в Railway."
            )

        # Проверяем доступ к обоим каналам.
        await client.get_entity(
            OFFICIAL_CHANNEL
        )
        await client.get_entity(
            MONITORING_CHANNEL
        )

        logger.info(
            "Мониторинг запущен: "
            "kpszsu + sumygo. "
            "Отслеживаются новые "
            "и отредактированные сообщения."
        )

        await client.run_until_disconnected()

    finally:
        await client.disconnect()

        logger.info(
            "Telegram-монитор остановлен."
        )