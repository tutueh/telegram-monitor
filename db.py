import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_tables()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def init_tables(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    msg_id INTEGER,
                    group_id INTEGER,
                    group_name TEXT,
                    sender_id INTEGER,
                    text TEXT,
                    has_media INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    msg_id INTEGER,
                    group_id INTEGER,
                    type TEXT,
                    brand TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_message(self, msg_id, group_id, group_name, sender_id, text, has_media):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (msg_id, group_id, group_name, sender_id, text, has_media) VALUES (?, ?, ?, ?, ?, ?)",
                (msg_id, group_id, group_name, sender_id, text, 1 if has_media else 0)
            )
            conn.commit()
            return cursor.lastrowid

    def save_alert(self, msg_id, group_id, alert_type, brand, content):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO alerts (msg_id, group_id, type, brand, content) VALUES (?, ?, ?, ?, ?)",
                (msg_id, group_id, alert_type, brand, content)
            )
            conn.commit()

    def get_recent_alerts(self, limit=15):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.created_at, m.group_name, a.type, a.brand, a.content 
                FROM alerts a 
                JOIN messages m ON a.msg_id = m.id 
                ORDER BY a.created_at DESC 
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def get_stats(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM messages")
            msg_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM alerts")
            alert_count = cursor.fetchone()[0]

            cursor.execute("SELECT type, COUNT(*) FROM alerts GROUP BY type")
            alert_types = cursor.fetchall()

            cursor.execute("SELECT brand, COUNT(*) FROM alerts GROUP BY brand ORDER BY COUNT(*) DESC LIMIT 5")
            top_brands = cursor.fetchall()

            return {
                'messages': msg_count,
                'alerts': alert_count,
                'types': dict(alert_types),
                'brands': dict(top_brands)
            }
