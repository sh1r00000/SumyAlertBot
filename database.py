import sqlite3
from pathlib import Path

from logger import logger

DB_PATH = Path("data/stats.db")


def init_database():
    DB_PATH.parent.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            duration INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_state (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    logger.info("База данных успешно инициализирована.")
    conn.close()


def save_alert_start(start_time):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts(started_at)
        VALUES(?)
    """, (start_time,))

    conn.commit()
    conn.close()


def save_alert_end(end_time, duration):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE alerts
        SET ended_at = ?, duration = ?
        WHERE id = (
            SELECT id
            FROM alerts
            WHERE ended_at IS NULL
            ORDER BY id DESC
            LIMIT 1
        )
    """, (end_time, duration))

    conn.commit()
    conn.close()


def get_active_alert():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT started_at
        FROM alerts
        WHERE ended_at IS NULL
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def save_last_sent_status(status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO bot_state(key, value)
        VALUES('last_sent_status', ?)
    """, (status,))

    conn.commit()
    conn.close()


def get_last_sent_status():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT value
        FROM bot_state
        WHERE key='last_sent_status'
    """)

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


if __name__ == "__main__":
    init_database()