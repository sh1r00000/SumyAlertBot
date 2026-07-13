import sqlite3
from pathlib import Path

from logger import logger


DB_PATH = Path("/data/stats.db")


def init_database():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_alerts (
            location TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            sent INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()

    logger.info(
        "База данных успешно инициализирована."
    )


def save_active_alert(location, started_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Монитор хранит только одну общую активную тревогу
    # для Сум и Сумского района.
    cursor.execute("""
        DELETE FROM active_alerts
    """)

    cursor.execute("""
        INSERT INTO active_alerts (
            location,
            started_at,
            sent
        )
        VALUES (?, ?, 1)
    """, (
        location,
        started_at
    ))

    conn.commit()
    conn.close()


def get_active_alerts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT location, started_at
        FROM active_alerts
        ORDER BY started_at ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def remove_active_alert(location):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM active_alerts
        WHERE location = ?
    """, (
        location,
    ))

    conn.commit()
    conn.close()


def clear_active_alerts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM active_alerts
    """)

    conn.commit()
    conn.close()