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
            
            # Create AFK users table with status tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS afk_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    display_name TEXT NOT NULL,
                    until_date TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    ended_at TEXT DEFAULT NULL,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_status 
                ON afk_users(user_id, is_active)
            ''')
            
            conn.commit()

    def set_afk(self, user_id: int, display_name: str, until_date: datetime, reason: str):
        """Set a user as AFK"""
        # First, deactivate any active AFK status for this user
        self.deactivate_previous_afk(user_id)
        
        # Then create new AFK entry
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO afk_users 
                (user_id, display_name, until_date, reason, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (user_id, display_name, until_date.strftime("%Y-%m-%d %H:%M:%S"), reason))
            conn.commit()

    def deactivate_previous_afk(self, user_id: int):
        """Deactivate any active AFK status for a user"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE afk_users 
                SET is_active = 0, 
                    ended_at = CURRENT_TIMESTAMP 
                WHERE user_id = ? 
                AND is_active = 1
            ''', (user_id,))
            conn.commit()

    def remove_afk(self, user_id: int) -> bool:
        """Mark AFK status as inactive for a user"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE afk_users 
                SET is_active = 0, 
                    ended_at = CURRENT_TIMESTAMP 
                WHERE user_id = ? 
                AND is_active = 1
            ''', (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_active_afk(self):
        """Get all currently active AFK users"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, display_name, until_date, reason, created_at 
                FROM afk_users 
                WHERE is_active = 1 
                ORDER BY until_date ASC
            ''')
            return cursor.fetchall()

    def get_user_afk_history(self, user_id: int, limit: int = 5):
        """Get AFK history for a specific user"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT display_name, until_date, reason, created_at, ended_at 
                FROM afk_users 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return cursor.fetchall()

    def get_afk_statistics(self):
        """Get general AFK statistics"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_afk,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(CASE WHEN is_active = 1 THEN 1 END) as currently_active,
                    AVG(CASE 
                        WHEN ended_at IS NOT NULL 
                        THEN julianday(ended_at) - julianday(created_at) 
                        END) as avg_duration_days
                FROM afk_users
            ''')
            return cursor.fetchone() 