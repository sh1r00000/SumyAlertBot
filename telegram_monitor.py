import re
import time

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from config import API_HASH, API_ID, TELEGRAM_SESSION
from logger import logger
from threat_parser import extract_sumy_event


# Используем только официальный канал Воздушных сил
SOURCE_CHANNEL = "kpszsu"

# Полностью одинаковое сообщение повторно не публикуем 3 минуты
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
    text = re.sub(r"[^\wа-яіїєґ0-9 ]", "", text)

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
    """
    Убирает начальные эмодзи и стрелки,
    потому что мы добавляем свою иконку.
    """
    return re.sub(
        r"^[^\wА-Яа-яІіЇїЄєҐґ0-9]+",
        "",
        text,
    ).strip()


def _build_channel_message(event: dict) -> str:
    event_type = event["type"]
    lines = event["lines"]

    icon = EVENT_ICONS.get(event_type, "⚠️")

    cleaned_lines = [
        _strip_leading_symbols(line)
        for line in lines
        if _strip_leading_symbols(line)
    ]

    body = "\n".join(cleaned_lines)

    return (
        f"{icon} {body}\n\n"
        f"👉 @sumy_alert1"
    )


async def start_telegram_monitor(bot, channel: str) -> None:
    if not API_ID:
        raise RuntimeError("Не указан API_ID")

    if not API_HASH:
        raise RuntimeError("Не указан API_HASH")

    # Railway использует строку TELEGRAM_SESSION.
    # Локально используется файл sumy_monitor.session.
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

    @client.on(
        events.NewMessage(chats=[SOURCE_CHANNEL])
    )
    async def handler(event) -> None:
        try:
            message = event.raw_text or ""

            if not message.strip():
                return

            sumy_event = extract_sumy_event(message)

            if sumy_event is None:
                return

            channel_message = _build_channel_message(
                sumy_event
            )

            if _is_duplicate(channel_message):
                logger.info(
                    "Пропущен полный дубль сообщения Воздушных сил."
                )
                return

            await bot.send_message(
                chat_id=channel,
                text=channel_message,
            )

            logger.info(
                "Опубликовано официальное сообщение: type=%s",
                sumy_event["type"],
            )

        except Exception as error:
            logger.exception(
                "Ошибка обработки сообщения Воздушных сил: %s",
                error,
            )

    logger.info(
        "Подключение к официальному каналу Воздушных сил..."
    )

    try:
        await client.connect()

        if not await client.is_user_authorized():
            raise RuntimeError(
                "Telegram-сессия не авторизована. "
                "Проверь TELEGRAM_SESSION в Railway."
            )

        logger.info(
            "Официальный монитор Воздушных сил запущен."
        )

        await client.run_until_disconnected()

    finally:
        await client.disconnect()

        logger.info(
            "Официальный монитор Воздушных сил остановлен."
        )