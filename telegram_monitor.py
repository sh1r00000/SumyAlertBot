import re
import time

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from config import API_HASH, API_ID, TELEGRAM_SESSION
from logger import logger
from threat_parser import extract_sumy_events


SOURCE_CHANNEL = "kpszsu"

# Полностью одинаковый текст не публикуем
# повторно в течение трёх минут.
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


def _remove_old_duplicates(now: float) -> None:
    expired = [
        key
        for key, created_at in recent_messages.items()
        if now - created_at > DUPLICATE_SECONDS
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
        and now - previous_time <= DUPLICATE_SECONDS
    ):
        return True

    recent_messages[key] = now

    return False


def _strip_leading_symbols(text: str) -> str:
    return re.sub(
        r"^[^\wА-Яа-яІіЇїЄєҐґ0-9]+",
        "",
        text,
    ).strip()


def _build_channel_message(
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
            cleaned := _strip_leading_symbols(line)
        )
    ]

    body = "\n".join(cleaned_lines)

    return (
        f"{icon} {body}\n\n"
        f"👉 @sumy_alert1"
    )


async def start_telegram_monitor(
    bot,
    channel: str,
) -> None:
    if not API_ID:
        raise RuntimeError("Не указан API_ID")

    if not API_HASH:
        raise RuntimeError("Не указан API_HASH")

    # На Railway используется TELEGRAM_SESSION.
    # На компьютере — файл sumy_monitor.session.
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

    async def process_message(event) -> None:
        try:
            message = event.raw_text or ""

            if not message.strip():
                return

            # Одно сообщение может содержать несколько
            # различных угроз для Сум.
            sumy_events = extract_sumy_events(
                message
            )

            if not sumy_events:
                return

            for event_data in sumy_events:
                channel_message = (
                    _build_channel_message(
                        event_data
                    )
                )

                if _is_duplicate(channel_message):
                    logger.info(
                        "Пропущен дубль сообщения "
                        "Воздушных сил: type=%s",
                        event_data["type"],
                    )

                    continue

                await bot.send_message(
                    chat_id=channel,
                    text=channel_message,
                )

                logger.info(
                    "Опубликовано официальное "
                    "сообщение: type=%s",
                    event_data["type"],
                )

        except Exception as error:
            logger.exception(
                "Ошибка обработки сообщения "
                "Воздушных сил: %s",
                error,
            )

    # Новые публикации.
    client.add_event_handler(
        process_message,
        events.NewMessage(
            chats=[SOURCE_CHANNEL]
        ),
    )

    # Редактирование уже опубликованных сообщений.
    client.add_event_handler(
        process_message,
        events.MessageEdited(
            chats=[SOURCE_CHANNEL]
        ),
    )

    logger.info(
        "Подключение к официальному "
        "каналу Воздушных сил..."
    )

    try:
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError(
                "Telegram-сессия не авторизована. "
                "Проверь TELEGRAM_SESSION в Railway."
            )

        logger.info(
            "Официальный монитор Воздушных сил "
            "запущен. Отслеживаются новые "
            "и отредактированные сообщения."
        )

        await client.run_until_disconnected()

    finally:
        await client.disconnect()

        logger.info(
            "Официальный монитор "
            "Воздушных сил остановлен."
        )