import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo

from config import ALERTS_API_KEY

STATUS_API_URL = "https://api.alerts.in.ua/v1/iot/active_air_raid_alerts/20.json"
DETAILS_API_URL = "https://api.alerts.in.ua/v1/alerts/active.json"


async def get_alert_status():
    headers = {
        "Authorization": f"Bearer {ALERTS_API_KEY}"
    }

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            STATUS_API_URL,
            headers=headers
        ) as response:

            if response.status != 200:
                text = await response.text()
                raise Exception(
                    f"API Error {response.status}: {text}"
                )

            text = await response.text()
            status = text.strip().replace('"', "")

            if status not in ("A", "N", "P"):
                raise Exception(
                    f"Unknown API status: {status}"
                )

            return status


async def get_sumy_alert():
    headers = {
        "Authorization": f"Bearer {ALERTS_API_KEY}"
    }

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            DETAILS_API_URL,
            headers=headers
        ) as response:

            if response.status != 200:
                text = await response.text()
                raise Exception(
                    f"API Error {response.status}: {text}"
                )

            data = await response.json()

    sumy_alerts = []

    for alert in data["alerts"]:

        if alert["alert_type"] != "air_raid":
            continue

        if alert["location_oblast"] != "Сумська область":
            continue

        started_at = (
            datetime.fromisoformat(
                alert["started_at"].replace(
                    "Z",
                    "+00:00"
                )
            )
            .astimezone(
                ZoneInfo("Europe/Kyiv")
            )
            .replace(tzinfo=None)
        )

        sumy_alerts.append({
            "location": alert["location_title"],
            "location_type": alert["location_type"],
            "started_at": started_at,
        })

    if not sumy_alerts:
        return None

    # 1. Приоритет тревоги по всей области
    for alert in sumy_alerts:
        if alert["location"] == "Сумська область":
            return alert

    # 2. Приоритет тревоги по городу Сумы
    for alert in sumy_alerts:
        if alert["location"] in (
            "м. Суми",
            "Суми"
        ):
            return alert

    # 3. Если тревога только в районе или громаде
    return sumy_alerts[0]