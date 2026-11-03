"""
SQLite Memory and Conversation Persistence Manager.
Operates 100% locally with zero cloud transmission.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from config import DB_PATH

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connection(self):
        """Context manager that guarantees connection closing."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database tables for conversations and persistent facts."""
        with self._connection() as conn:
            cursor = conn.cursor()
            
            # Chat history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    tool_results TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")

            # Long-term persistent key-value memory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.commit()

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_results: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """Persist a message into the session history."""
        timestamp = datetime.now().isoformat()
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        tool_results_json = json.dumps(tool_results) if tool_results else None

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (session_id, timestamp, role, content, tool_calls, tool_results)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, timestamp, role, content, tool_calls_json, tool_results_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent chat history for a session."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, session_id, timestamp, role, content, tool_calls, tool_results
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (session_id, limit)
            )
            rows = cursor.fetchall()
            
            history = []
            for r in rows:
                item = {
                    "id": r["id"],
                    "session_id": r["session_id"],
                    "timestamp": r["timestamp"],
                    "role": r["role"],
                    "content": r["content"],
                    "tool_calls": json.loads(r["tool_calls"]) if r["tool_calls"] else None,
                    "tool_results": json.loads(r["tool_results"]) if r["tool_results"] else None,
                }
                history.append(item)
            return history

    def clear_session(self, session_id: str):
        """Clear all conversation messages in a given session."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.commit()

    def clear_all_history(self):
        """Clear all conversation history across all sessions."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            conn.commit()

    # Long-term persistent key-value memory methods
    def set_fact(self, key: str, value: str):
        """Save or update a long term memory fact."""
        timestamp = datetime.now().isoformat()
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO long_term_memory (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, timestamp)
            )
            conn.commit()

    def get_fact(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a specific long term memory fact."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM long_term_memory WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def get_all_facts(self) -> Dict[str, str]:
        """Retrieve all stored long-term memory facts."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM long_term_memory")
            rows = cursor.fetchall()
            return {r["key"]: r["value"] for r in rows}
