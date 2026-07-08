from datetime import datetime


def format_duration(start: datetime, end: datetime) -> str:
    seconds = int((end - start).total_seconds())

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        return f"{hours} год {minutes} хв"

    return f"{minutes} хв"


def format_location(location: str) -> str:
    if "область" in location:
        return f"🌍 <b>{location}</b>"

    if "район" in location:
        return f"🏛️ <b>{location}</b>"

    if "громада" in location:
        return f"🏘️ <b>{location}</b>"

    if location.startswith("м."):
        return f"🏙️ <b>{location}</b>"

    return f"📍 <b>{location}</b>"


def alert_started_message(location: str, start_time: datetime) -> str:
    return (
        "🚨 <b>ПОВІТРЯНА ТРИВОГА</b>\n\n"
        f"{format_location(location)}\n"
        f"🕒 <b>Початок:</b> {start_time.strftime('%H:%M')}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🛡 <b>Негайно пройдіть до найближчого укриття.</b>\n\n"
        "🔕 Не ігноруйте сигнал повітряної тривоги.\n"
        "📢 Слідкуйте за офіційними повідомленнями.\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 <b>Sumy Alert</b>"
    )


def alert_updated_message(old_location: str, new_location: str) -> str:
    return (
        "🔄 <b>ОНОВЛЕННЯ ТРИВОГИ</b>\n\n"
        f"📍 <b>Було:</b> {format_location(old_location)}\n"
        f"📍 <b>Стало:</b> {format_location(new_location)}\n\n"
        "⚠️ Зона повітряної тривоги змінилася.\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 <b>Sumy Alert</b>"
    )


def alert_ended_message(location: str, start_time: datetime, end_time: datetime) -> str:
    return (
        "✅ <b>ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ</b>\n\n"
        f"{format_location(location)}\n\n"
        f"🕒 <b>Початок:</b> {start_time.strftime('%H:%M')}\n"
        f"🕒 <b>Відбій:</b> {end_time.strftime('%H:%M')}\n"
        f"⏱ <b>Тривалість:</b> {format_duration(start_time, end_time)}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "💙 Бережіть себе!\n"
        "🙏 Дякуємо, що були уважними.\n\n"
        "🤖 <b>Sumy Alert</b>"
    )