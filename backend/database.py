"""Database operations for Research Chat System.

Handles all SQLite/PostgreSQL interactions for storing and retrieving
chat messages, transcripts, and export data.
"""

import sqlite3
import csv
import io
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import DATABASE_URL


def _get_db_path() -> str:
    """Extract file path from SQLite connection string."""
    if DATABASE_URL.startswith("sqlite:///"):
        return DATABASE_URL.replace("sqlite:///", "")
    return DATABASE_URL


def _ensure_db_dir():
    """Create the database directory if it doesn't exist."""
    db_path = _get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    _ensure_db_dir()
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialise the database schema."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            task_id TEXT DEFAULT '',
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            message TEXT NOT NULL,
            model TEXT DEFAULT '',
            provider TEXT DEFAULT '',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
        CREATE INDEX IF NOT EXISTS idx_messages_student_id ON messages(student_id);
        CREATE INDEX IF NOT EXISTS idx_messages_task_id ON messages(task_id);
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
    """)
    conn.commit()
    conn.close()


def save_message(
    chat_id: str,
    student_id: str,
    task_id: str,
    role: str,
    message: str,
    model: str = "",
    provider: str = "",
) -> int:
    """Save a single message to the database. Returns the message ID."""
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO messages (chat_id, student_id, task_id, role, message, model, provider)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (chat_id, student_id, task_id, role, message, model, provider),
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id


def get_history(chat_id: str) -> list[dict]:
    """Get the conversation history for a given chat_id."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE chat_id = ? ORDER BY timestamp ASC",
        (chat_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_transcripts(
    student_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> list[dict]:
    """Get a summary of all conversations, optionally filtered."""
    conn = get_connection()
    query = """
        SELECT
            chat_id,
            student_id,
            task_id,
            MIN(timestamp) AS started_at,
            MAX(timestamp) AS last_message_at,
            COUNT(*) AS message_count
        FROM messages
        WHERE 1=1
    """
    params = []
    if student_id:
        query += " AND student_id = ?"
        params.append(student_id)
    if task_id:
        query += " AND task_id = ?"
        params.append(task_id)

    query += " GROUP BY chat_id ORDER BY MAX(timestamp) DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transcript(chat_id: str) -> list[dict]:
    """Get the full transcript for a specific conversation."""
    return get_history(chat_id)


def get_stats() -> dict:
    """Get summary statistics for the admin dashboard."""
    conn = get_connection()
    total_messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    total_conversations = conn.execute(
        "SELECT COUNT(DISTINCT chat_id) FROM messages"
    ).fetchone()[0]
    total_students = conn.execute(
        "SELECT COUNT(DISTINCT student_id) FROM messages"
    ).fetchone()[0]
    total_tasks = conn.execute(
        "SELECT COUNT(DISTINCT task_id) FROM messages WHERE task_id != ''"
    ).fetchone()[0]

    recent = conn.execute(
        "SELECT MAX(timestamp) FROM messages"
    ).fetchone()[0]

    conn.close()
    return {
        "total_messages": total_messages,
        "total_conversations": total_conversations,
        "total_students": total_students,
        "total_tasks": total_tasks,
        "last_activity": recent,
    }


def export_csv(
    student_id: Optional[str] = None,
    task_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """Export messages as CSV string, with optional filters."""
    conn = get_connection()
    query = "SELECT * FROM messages WHERE 1=1"
    params = []

    if student_id:
        query += " AND student_id = ?"
        params.append(student_id)
    if task_id:
        query += " AND task_id = ?"
        params.append(task_id)
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date + " 23:59:59")

    query += " ORDER BY timestamp ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "chat_id", "student_id", "task_id", "role", "message", "model", "provider", "timestamp"])
    for row in rows:
        writer.writerow([
            row["id"], row["chat_id"], row["student_id"], row["task_id"],
            row["role"], row["message"], row["model"], row["provider"],
            row["timestamp"],
        ])
    return output.getvalue()


def export_json(
    student_id: Optional[str] = None,
    task_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    """Export messages as JSON, grouped by conversation."""
    conn = get_connection()
    query = "SELECT * FROM messages WHERE 1=1"
    params = []

    if student_id:
        query += " AND student_id = ?"
        params.append(student_id)
    if task_id:
        query += " AND task_id = ?"
        params.append(task_id)
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date + " 23:59:59")

    query += " ORDER BY timestamp ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    # Group by chat_id
    conversations = {}
    for row in rows:
        cid = row["chat_id"]
        if cid not in conversations:
            conversations[cid] = {
                "chat_id": cid,
                "student_id": row["student_id"],
                "task_id": row["task_id"],
                "messages": [],
            }
        conversations[cid]["messages"].append({
            "id": row["id"],
            "role": row["role"],
            "message": row["message"],
            "model": row["model"],
            "provider": row["provider"],
            "timestamp": row["timestamp"],
        })

    return list(conversations.values())
