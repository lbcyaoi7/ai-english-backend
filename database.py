import sqlite3
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager

DATABASE_PATH = "records.db"

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                scenario TEXT NOT NULL,
                score REAL,
                issues TEXT,
                suggestions TEXT,
                improved TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def save_record(text: str, scenario: str, score: float, issues: List[str], suggestions: List[str], improved: str) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO records (text, scenario, score, issues, suggestions, improved, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (text, scenario, score, str(issues), str(suggestions), improved, datetime.now().isoformat()))
        conn.commit()
        return cursor.lastrowid

def get_records(limit: int = 50) -> List[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, text, scenario, score, issues, suggestions, improved, created_at
            FROM records
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_record_by_id(record_id: int) -> Optional[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, text, scenario, score, issues, suggestions, improved, created_at
            FROM records
            WHERE id = ?
        """, (record_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

init_db()