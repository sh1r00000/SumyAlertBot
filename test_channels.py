from telethon import TelegramClient
from dotenv import load_dotenv
import os

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

client = TelegramClient("sumy_monitor", api_id, api_hash)

channels = [
    "kpszsu",
    "sumyregion",
    "ZhenyokSay"
]

async def main():
    for channel in channels:
        try:
            entity = await client.get_entity(channel)
            print(f"✅ Доступ есть: {entity.title}")
        except Exception as e:
            print(f"❌ Ошибка доступа к {channel}: {e}")

with client:
    client.loop.run_until_complete(main())