"""
Service database SQLite untuk menyimpan history pengguna
"""

import sqlite3
import json
from datetime import datetime
from config import config


class Database:
    def __init__(self, db_path: str = "bot_history.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Inisialisasi tabel database"""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    input_text TEXT,
                    output_url TEXT,
                    prompt_used TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """)

    def upsert_user(self, user_id: int, username: str, first_name: str):
        """Simpan atau update data user"""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO users (user_id, username, first_name)
                   VALUES (?, ?, ?)""",
                (user_id, username, first_name)
            )

    def save_history(self, user_id: int, type_: str, input_text: str,
                     output_url: str = None, prompt_used: str = None):
        """Simpan history generate"""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO history (user_id, type, input_text, output_url, prompt_used)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, type_, input_text, output_url, prompt_used)
            )

    def get_history(self, user_id: int, limit: int = None) -> list:
        """Ambil history generate user"""
        limit = limit or config.MAX_HISTORY
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT type, input_text, output_url, created_at
                   FROM history WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit)
            ).fetchall()
        return [
            {"type": r[0], "input": r[1], "output_url": r[2], "created_at": r[3]}
            for r in rows
        ]

    def get_stats(self, user_id: int) -> dict:
        """Statistik penggunaan user"""
        with self._get_conn() as conn:
            counts = conn.execute(
                """SELECT type, COUNT(*) as count
                   FROM history WHERE user_id = ?
                   GROUP BY type""",
                (user_id,)
            ).fetchall()
        return {row[0]: row[1] for row in counts}


db = Database()
