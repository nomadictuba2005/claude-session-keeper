#!/usr/bin/env python3
"""
Session Statistics and History Tracking
Tracks session success rates, response times, and historical data
"""
import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading

class SessionStats:
    """Track and analyze session statistics"""

    def __init__(self, db_path: str = "session_history.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Session history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    response_time REAL,
                    error_message TEXT,
                    session_type TEXT DEFAULT 'regular',
                    response_preview TEXT
                )
            ''')

            # Daily statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_checks INTEGER DEFAULT 0,
                    successful INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    avg_response_time REAL,
                    uptime_percentage REAL
                )
            ''')

            # System events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    data TEXT
                )
            ''')

            conn.commit()

    def record_session(self, success: bool, response_time: float = None,
                      error_message: str = None, session_type: str = "regular",
                      response_preview: str = None):
        """Record a health check session"""
        with self.lock:
            timestamp = datetime.now().isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Insert session record
                cursor.execute('''
                    INSERT INTO sessions (timestamp, success, response_time, error_message, session_type, response_preview)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (timestamp, 1 if success else 0, response_time, error_message, session_type, response_preview))

                # Update daily stats
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (today,))
                row = cursor.fetchone()

                if row:
                    total = row[1] + 1
                    successful = row[2] + (1 if success else 0)
                    failed = row[3] + (0 if success else 1)

                    # Calculate average response time
                    if response_time and row[4]:
                        avg_time = (row[4] * row[1] + response_time) / total
                    elif response_time:
                        avg_time = response_time
                    else:
                        avg_time = row[4]

                    uptime = (successful / total) * 100 if total > 0 else 0

                    cursor.execute('''
                        UPDATE daily_stats
                        SET total_checks = ?, successful = ?, failed = ?, avg_response_time = ?, uptime_percentage = ?
                        WHERE date = ?
                    ''', (total, successful, failed, avg_time, uptime, today))
                else:
                    cursor.execute('''
                        INSERT INTO daily_stats (date, total_checks, successful, failed, avg_response_time, uptime_percentage)
                        VALUES (?, 1, ?, ?, ?, ?)
                    ''', (today, 1 if success else 0, 0 if success else 1, response_time, 100.0 if success else 0.0))

                conn.commit()

    def record_event(self, event_type: str, description: str, data: dict = None):
        """Record a system event"""
        with self.lock:
            timestamp = datetime.now().isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO events (timestamp, event_type, description, data)
                    VALUES (?, ?, ?, ?)
                ''', (timestamp, event_type, description, json.dumps(data) if data else None))
                conn.commit()

    def get_recent_sessions(self, limit: int = 20) -> List[Dict]:
        """Get recent session records"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sessions ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_today_stats(self) -> Dict:
        """Get today's statistics"""
        today = datetime.now().strftime('%Y-%m-%d')

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (today,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return {
                'date': today,
                'total_checks': 0,
                'successful': 0,
                'failed': 0,
                'avg_response_time': None,
                'uptime_percentage': 100.0
            }

    def get_weekly_stats(self) -> List[Dict]:
        """Get last 7 days of statistics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM daily_stats
                ORDER BY date DESC LIMIT 7
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_overall_stats(self) -> Dict:
        """Get overall lifetime statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total counts
            cursor.execute('SELECT COUNT(*), SUM(success), AVG(response_time) FROM sessions')
            row = cursor.fetchone()
            total = row[0] or 0
            successful = row[1] or 0
            avg_response = row[2]

            # First and last session
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM sessions')
            times = cursor.fetchone()

            # Current streak
            cursor.execute('''
                SELECT success FROM sessions ORDER BY timestamp DESC LIMIT 10
            ''')
            recent = cursor.fetchall()
            streak = 0
            for r in recent:
                if r[0] == 1:
                    streak += 1
                else:
                    break

            return {
                'total_sessions': total,
                'successful_sessions': successful,
                'failed_sessions': total - successful,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'avg_response_time': avg_response,
                'first_session': times[0],
                'last_session': times[1],
                'current_success_streak': streak
            }

    def get_events(self, limit: int = 50, event_type: str = None) -> List[Dict]:
        """Get system events"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if event_type:
                cursor.execute('''
                    SELECT * FROM events WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?
                ''', (event_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM events ORDER BY timestamp DESC LIMIT ?
                ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def export_stats(self, filepath: str = "stats_export.json"):
        """Export all statistics to JSON"""
        data = {
            'exported_at': datetime.now().isoformat(),
            'overall': self.get_overall_stats(),
            'today': self.get_today_stats(),
            'weekly': self.get_weekly_stats(),
            'recent_sessions': self.get_recent_sessions(100),
            'recent_events': self.get_events(100)
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return filepath

    def get_status_summary(self) -> Dict:
        """Get a quick status summary for display"""
        today = self.get_today_stats()
        overall = self.get_overall_stats()
        recent = self.get_recent_sessions(1)

        return {
            'last_check': recent[0]['timestamp'] if recent else None,
            'last_status': 'success' if recent and recent[0]['success'] else 'failed' if recent else 'never',
            'today_checks': today['total_checks'],
            'today_success_rate': today['uptime_percentage'],
            'overall_success_rate': overall['success_rate'],
            'current_streak': overall['current_success_streak'],
            'total_sessions': overall['total_sessions']
        }
