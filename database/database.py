"""
database.py — Database schema creation helper.

db_name defaults to the safe LOCALAPPDATA path via paths.py.
Never uses a bare relative filename like "school_data.db".
"""

import sqlite3
import os
import sys
from pathlib import Path


def _get_safe_default_db() -> str:
    """Return the safe, absolute default DB path.

    Priority:
      1. SCHOOL_DB_PATH env var (set by db_services before any import)
      2. LOCALAPPDATA\\Learnix\\data\\school_data.db  (Windows)
      3. ~/.learnix/data/school_data.db             (fallback)
    """
    env = os.environ.get("SCHOOL_DB_PATH", "").strip()
    if env:
        return env

    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        p = Path(local_app_data) / "Learnix" / "data"
    else:
        p = Path.home() / ".learnix" / "data"

    p.mkdir(parents=True, exist_ok=True)
    return str(p / "school_data.db")


def create_school_database(db_name: str = "") -> None:
    """Create the school database and its core empty tables.

    Args:
        db_name: Absolute path to the SQLite file.
                 Defaults to the safe LOCALAPPDATA directory.
    """
    if not db_name:
        db_name = _get_safe_default_db()

    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT    NOT NULL
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT    NOT NULL UNIQUE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS terms (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT    NOT NULL UNIQUE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                term_id    INTEGER NOT NULL,
                score      REAL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (term_id)    REFERENCES terms(id)    ON DELETE CASCADE,
                CONSTRAINT unique_grade_per_subject_term UNIQUE (student_id, subject_id, term_id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id            INTEGER NOT NULL,
                subject_id            INTEGER NOT NULL,
                attendance_percentage REAL    DEFAULT 0,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                CONSTRAINT unique_attendance_per_subject UNIQUE (student_id, subject_id)
            );
        """)

        conn.commit()
        print(f"Database '{db_name}' created with empty tables.")
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()


def insert_subjects_manually(subjects_list, db_name: str = "") -> None:
    """Insert subjects into the database, skipping duplicates.

    Args:
        subjects_list: List of subject name strings.
        db_name: Absolute path to the SQLite file.
                 Defaults to the safe LOCALAPPDATA directory.
    """
    if not subjects_list:
        print("No subjects provided.")
        return

    if not db_name:
        db_name = _get_safe_default_db()

    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        inserted = 0
        for name in subjects_list:
            try:
                cursor.execute("INSERT INTO subjects (name) VALUES (?)", (name,))
                inserted += 1
            except sqlite3.IntegrityError:
                print(f"Subject '{name}' already exists, skipping.")
        conn.commit()
        print(f"Inserted {inserted} new subject(s).")
    except sqlite3.Error as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_school_database()
