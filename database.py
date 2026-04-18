"""
database.py - Handles all database operations for the Task Manager app.

Uses Python's built-in sqlite3 module, so no extra installation needed.
The database file (tasks.db) is created automatically on first run.
"""

import sqlite3
from datetime import datetime

# Path to the SQLite database file
DB_FILE = "tasks.db"


def get_connection():
    """Open and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    # Return rows as dict-like objects so we can access columns by name
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Create the tasks table if it doesn't already exist.
    Called once when the app starts up.
    """
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT    NOT NULL,
            done       INTEGER NOT NULL DEFAULT 0,   -- 0 = pending, 1 = complete
            created_at TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_all_tasks():
    """Return all tasks, newest first."""
    conn = get_connection()
    tasks = conn.execute(
        "SELECT * FROM tasks ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return tasks


def add_task(title):
    """Insert a new task with the given title."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO tasks (title, created_at) VALUES (?, ?)",
        (title, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()


def complete_task(task_id):
    """Mark a task as done (done = 1)."""
    conn = get_connection()
    conn.execute(
        "UPDATE tasks SET done = 1 WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()


def reopen_task(task_id):
    """Mark a task as pending again (done = 0)."""
    conn = get_connection()
    conn.execute(
        "UPDATE tasks SET done = 0 WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()


def delete_task(task_id):
    """Permanently remove a task from the database."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )
    conn.commit()
    conn.close()
