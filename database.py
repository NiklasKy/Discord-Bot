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
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Create AFK users table with start and end times
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS afk_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        display_name TEXT NOT NULL,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
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

    def set_afk(self, user_id: int, display_name: str, start_date: datetime, end_date: datetime, reason: str, clan_role_id: int):
        """Set a user as AFK"""
        self.deactivate_previous_afk(user_id)
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO afk_users 
                (user_id, display_name, start_date, end_date, reason, clan_role_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (
                user_id, 
                display_name, 
                start_date.strftime("%Y-%m-%d %H:%M:%S"),
                end_date.strftime("%Y-%m-%d %H:%M:%S"),
                reason,
                clan_role_id
            ))
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
        current_time = datetime.now()
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                if clan_role_id is not None:
                    cursor.execute('''
                        SELECT 
                            user_id, 
                            display_name, 
                            start_date,
                            end_date, 
                            reason, 
                            created_at 
                        FROM afk_users 
                        WHERE is_active = 1 
                        AND clan_role_id = ?
                        AND (
                            (start_date <= ? AND end_date > ?) 
                            OR start_date > ?
                        )
                        ORDER BY start_date ASC
                    ''', (
                        clan_role_id,
                        current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        current_time.strftime("%Y-%m-%d %H:%M:%S")
                    ))
                else:
                    cursor.execute('''
                        SELECT 
                            user_id, 
                            display_name, 
                            start_date,
                            end_date, 
                            reason, 
                            created_at 
                        FROM afk_users 
                        WHERE is_active = 1 
                        AND (
                            (start_date <= ? AND end_date > ?) 
                            OR start_date > ?
                        )
                        ORDER BY start_date ASC
                    ''', (
                        current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        current_time.strftime("%Y-%m-%d %H:%M:%S")
                    ))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting active AFK users: {e}")
            raise

    def get_user_afk_history(self, user_id: int, limit: int = 5):
        """Get AFK history for a specific user"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        display_name, 
                        start_date,
                        end_date, 
                        reason, 
                        created_at, 
                        ended_at,
                        clan_role_id
                    FROM afk_users 
                    WHERE user_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (user_id, limit))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting user AFK history: {e}")
            raise

    def get_afk_statistics(self, clan_role_id: int = None):
        """Get AFK statistics for a specific clan"""
        current_time = datetime.now()
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            if clan_role_id is not None:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_afk,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(CASE 
                            WHEN is_active = 1 
                            AND start_date <= ? 
                            AND end_date > ? 
                            THEN 1 
                        END) as active_now,
                        COUNT(CASE 
                            WHEN is_active = 1 
                            AND start_date > ? 
                            THEN 1 
                        END) as scheduled_future,
                        AVG(CASE 
                            WHEN ended_at IS NOT NULL 
                            THEN julianday(COALESCE(ended_at, end_date)) - julianday(start_date)
                            WHEN end_date < ?
                            THEN julianday(end_date) - julianday(start_date)
                        END) as avg_duration_days
                    FROM afk_users
                    WHERE clan_role_id = ?
                ''', (
                    current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    clan_role_id
                ))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_afk,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(CASE 
                            WHEN is_active = 1 
                            AND start_date <= ? 
                            AND end_date > ? 
                            THEN 1 
                        END) as active_now,
                        COUNT(CASE 
                            WHEN is_active = 1 
                            AND start_date > ? 
                            THEN 1 
                        END) as scheduled_future,
                        AVG(CASE 
                            WHEN ended_at IS NOT NULL 
                            THEN julianday(COALESCE(ended_at, end_date)) - julianday(start_date)
                            WHEN end_date < ?
                            THEN julianday(end_date) - julianday(start_date)
                        END) as avg_duration_days
                    FROM afk_users
                ''', (
                    current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    current_time.strftime("%Y-%m-%d %H:%M:%S")
                ))
            
            return cursor.fetchone()

    def delete_afk_entries(self, user_id: int, all_entries: bool = False) -> int:
        """
        Delete AFK entries for a specific user
        
        Args:
            user_id: The Discord user ID
            all_entries: If True, deletes all entries, if False only deletes active entries
        
        Returns:
            Number of deleted entries
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                if all_entries:
                    # Delete all entries for the user
                    cursor.execute('''
                        DELETE FROM afk_users 
                        WHERE user_id = ?
                    ''', (user_id,))
                else:
                    # Delete only active entries
                    cursor.execute('''
                        DELETE FROM afk_users 
                        WHERE user_id = ? AND is_active = 1
                    ''', (user_id,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logging.info(f"Deleted {deleted_count} AFK entries for user {user_id}")
                return deleted_count

        except sqlite3.Error as e:
            logging.error(f"Error deleting AFK entries: {e}")
            raise 

    def get_user_active_afk(self, user_id: int):
        """Get current and future AFK entries for a user"""
        current_time = datetime.now()
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        display_name, 
                        start_date,
                        end_date, 
                        reason,
                        created_at,
                        clan_role_id
                    FROM afk_users 
                    WHERE user_id = ? 
                    AND is_active = 1
                    AND end_date >= ?
                    ORDER BY start_date ASC
                ''', (user_id, current_time.strftime("%Y-%m-%d %H:%M:%S")))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Error getting user active AFK entries: {e}")
            raise