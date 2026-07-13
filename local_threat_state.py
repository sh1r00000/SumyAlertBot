import json
from datetime import datetime, timezone
from pathlib import Path

from logger import logger


def _get_state_path() -> Path:
    railway_data = Path("/data")

    if railway_data.exists():
        return railway_data / "local_threat_state.json"

    return Path("data") / "local_threat_state.json"


STATE_PATH = _get_state_path()


def _read_state() -> dict:
    STATE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not STATE_PATH.exists():
        return {
            "drone_active": False,
            "updated_at": None,
        }

    try:
        return json.loads(
            STATE_PATH.read_text(
                encoding="utf-8"
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
    ) as error:
        logger.warning(
            "Не удалось прочитать состояние БпЛА: %s",
            error,
        )

        return {
            "drone_active": False,
            "updated_at": None,
        }


def is_drone_active() -> bool:
    state = _read_state()

    return bool(
        state.get("drone_active", False)
    )


def set_drone_active(active: bool) -> None:
    STATE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    state = {
        "drone_active": bool(active),
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    temporary_path = STATE_PATH.with_suffix(
        ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporary_path.replace(STATE_PATH)

    logger.info(
        "Локальный статус БпЛА изменён: %s",
        "активен" if active else "неактивен",
    )