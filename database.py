import sqlite3
from datetime import datetime
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_database.log'),
        logging.StreamHandler()
    ]
)

class Database:
    def __init__(self, db_file="bot_database.db"):
        self.db_file = db_file
        logging.info(f"Initializing database at: {os.path.abspath(db_file)}")
        self.init_database()

    def init_database(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            # Ensure the directory exists
            db_dir = os.path.dirname(os.path.abspath(self.db_file))
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logging.info(f"Created directory: {db_dir}")

            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Create AFK users table with clan information
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS afk_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        display_name TEXT NOT NULL,
                        until_date TEXT NOT NULL,
                        reason TEXT,
                        clan_role_id INTEGER NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        ended_at TEXT DEFAULT NULL,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Create indices for faster queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_status 
                    ON afk_users(user_id, is_active)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_clan_status 
                    ON afk_users(clan_role_id, is_active)
                ''')
                
                conn.commit()
                logging.info("Database initialized successfully")

        except sqlite3.Error as e:
            logging.error(f"SQLite error during initialization: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during database initialization: {e}")
            raise

    def set_afk(self, user_id: int, display_name: str, until_date: datetime, reason: str, clan_role_id: int):
        """Set a user as AFK"""
        self.deactivate_previous_afk(user_id)
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO afk_users 
                (user_id, display_name, until_date, reason, clan_role_id, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (user_id, display_name, until_date.strftime("%Y-%m-%d %H:%M:%S"), reason, clan_role_id))
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

    def get_all_active_afk(self, clan_role_id: int = None):
        """Get all active AFK users, optionally filtered by clan"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            if clan_role_id is not None:
                cursor.execute('''
                    SELECT user_id, display_name, until_date, reason, created_at 
                    FROM afk_users 
                    WHERE is_active = 1 AND clan_role_id = ?
                    ORDER BY until_date ASC
                ''', (clan_role_id,))
            else:
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
                SELECT display_name, until_date, reason, created_at, ended_at, clan_role_id
                FROM afk_users 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return cursor.fetchall()

    def get_afk_statistics(self, clan_role_id: int = None):
        """Get AFK statistics for a specific clan"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            if clan_role_id is not None:
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
                    WHERE clan_role_id = ?
                ''', (clan_role_id,))
            else:
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