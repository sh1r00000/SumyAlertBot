from telethon import TelegramClient, events
from dotenv import load_dotenv
from threat_parser import parse_message
import os

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

client = TelegramClient(
    "sumy_monitor",
    api_id,
    api_hash
)

CHANNELS = [
    "kpszsu",
    "sumyregion",
    "ZhenyokSay"
]

# Активные угрозы
active_threats = {}


@client.on(events.NewMessage(chats=CHANNELS))
async def handler(event):
    channel = await event.get_chat()

    source = getattr(channel, "username", None)
    message = event.raw_text

    # Парсим сообщение
    result = parse_message(source, message)

    # Не относится к Сумам или району
    if not result.get("sumy_related", False):
        return

    threat_type = result["type"]
    status = result["status"]

    # Если тип определить не удалось — пропускаем
    if threat_type is None:
        return

    # Иконка угрозы
    icons = {
        "drone": "🛸",
        "missile": "🚀",
        "kab": "💣"
    }

    icon = icons.get(threat_type, "❓")

    # -------------------------------
    # Завершение угрозы
    # -------------------------------
    if status == "ended":
        if threat_type in active_threats:
            del active_threats[threat_type]

            print("\n" + "=" * 50)
            print(f"✅ Угроза завершена: {icon} {threat_type}")
            print(message)
            print("=" * 50)

        return

    # -------------------------------
    # Обновление существующей угрозы
    # -------------------------------
    if threat_type in active_threats:
        active_threats[threat_type]["sources"].add(source)
        active_threats[threat_type]["last_message"] = message

        print("\n" + "=" * 50)
        print(f"🔄 Обновление угрозы: {icon} {threat_type}")
        print(f"Источники: {', '.join(active_threats[threat_type]['sources'])}")
        print()
        print(message)
        print("=" * 50)

        return

    # -------------------------------
    # Новая угроза
    # -------------------------------
    active_threats[threat_type] = {
        "sources": {source},
        "last_message": message
    }

    status_icons = {
        "active": "🚨",
        "engaged": "💥",
        "ended": "✅"
    }

    status_icon = status_icons.get(status, "❓")

    print("\n" + "=" * 50)
    print(f"🆕 Новая угроза")
    print(f"Источник: {channel.title}")
    print(f"Тип угрозы: {icon} {threat_type}")
    print(f"Статус: {status_icon} {status}")
    print(f"Доверие: {result['confidence']}")
    print()
    print(message)
    print("=" * 50)


async def main():
    print("🚨 Мониторинг Сум запущен...")
    print(f"📡 Отслеживаем каналы: {', '.join(CHANNELS)}")

    await client.start()
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())