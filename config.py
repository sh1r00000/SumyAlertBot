import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
ALERTS_API_KEY = os.getenv("ALERTS_API_KEY")

_api_id = os.getenv("API_ID")

API_ID = int(_api_id) if _api_id else None
API_HASH = os.getenv("API_HASH")
TELEGRAM_SESSION = os.getenv("TELEGRAM_SESSION")