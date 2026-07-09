from datetime import datetime


def format_duration(start: datetime, end: datetime) -> str:
    seconds = int((end - start).total_seconds())

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        return f"{hours} год {minutes} хв"

    return f"{minutes} хв"


def format_location(location: str) -> str:
    if location in ("м. Суми", "Суми"):
        return f"🏙️ <b>{location}</b>"

    return f"🏛️ <b>{location}</b>"


def alert_started_message(
    location: str,
    start_time: datetime
) -> str:
    return (
        "🚨 <b>ПОВІТРЯНА ТРИВОГА</b>\n\n"
        f"{format_location(location)}\n"
        f"🕒 <b>Початок:</b> "
        f"{start_time.strftime('%H:%M')}\n\n"
        "🛡 <b>Негайно пройдіть "
        "до найближчого укриття.</b>\n"
        "🔕 Не ігноруйте сигнал "
        "повітряної тривоги.\n"
        "📢 Слідкуйте за офіційними "
        "повідомленнями.\n\n"
        "📢 <a href='https://t.me/sumy_alert1'>"
        "@sumy_alert1</a>"
    )


def alert_ended_message(
    location: str,
    start_time: datetime,
    end_time: datetime
) -> str:
    return (
        "✅ <b>ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ</b>\n\n"
        f"{format_location(location)}\n\n"
        f"🕒 <b>Початок:</b> "
        f"{start_time.strftime('%H:%M')}\n"
        f"🕒 <b>Відбій:</b> "
        f"{end_time.strftime('%H:%M')}\n"
        f"⏱ <b>Тривалість:</b> "
        f"{format_duration(start_time, end_time)}\n\n"
        "💙 Бережіть себе!\n"
        "🙏 Дякуємо, що були уважними.\n\n"
        "📢 <a href='https://t.me/sumy_alert1'>"
        "@sumy_alert1</a>"
    )