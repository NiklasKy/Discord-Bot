import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file="bot_database.db"):
        self.db_file = db_file
        self.init_database()

    def init_database(self):
        """Initialize the database and create tables if they don't exist"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Create AFK users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS afk_users (
                    user_id INTEGER PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    until_date TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()

    def set_afk(self, user_id: int, display_name: str, until_date: datetime, reason: str):
        """Set a user as AFK"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO afk_users (user_id, display_name, until_date, reason)
                VALUES (?, ?, ?, ?)
            ''', (user_id, display_name, until_date.strftime("%Y-%m-%d %H:%M:%S"), reason))
            conn.commit()

    def remove_afk(self, user_id: int) -> bool:
        """Remove AFK status for a user"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM afk_users WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_afk(self):
        """Get all AFK users"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM afk_users ORDER BY until_date ASC')
            return cursor.fetchall()

    def clear_afk(self) -> int:
        """Clear all AFK entries"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM afk_users')
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count 