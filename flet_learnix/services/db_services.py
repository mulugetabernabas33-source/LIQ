import os
import sys

from services.paths import get_db_path, get_data_dir

# ---------------------------------------------------------------------------
# Set SCHOOL_DB_PATH env var BEFORE importing db_functions.
# This ensures db_functions._resolve_db_path() always returns the correct
# LOCALAPPDATA path, never a relative or System32 path.
# ---------------------------------------------------------------------------
os.environ["SCHOOL_DB_PATH"] = get_db_path()

# ---------------------------------------------------------------------------
# Make app/backend importable in dev AND packaged builds.
#
# Strategy (tried in order):
#   1. Already importable (packaged build with flat bundle, or already in path)
#   2. sys._MEIPASS/app/backend   (PyInstaller / flet build packaged)
#   3. __file__-relative walk     (development source tree)
# ---------------------------------------------------------------------------
def _ensure_backend_importable() -> None:
    try:
        import db_functions  # noqa: F401
        return  # already on path — nothing to do
    except ImportError:
        pass

    # Strategy 2: packaged bundle (sys._MEIPASS)
    if hasattr(sys, "_MEIPASS"):
        candidate = os.path.join(sys._MEIPASS, "app", "backend")
        if os.path.isdir(candidate) and candidate not in sys.path:
            sys.path.insert(0, candidate)
            try:
                import db_functions  # noqa: F401
                return
            except ImportError:
                pass

    # Strategy 3: source-tree walk from __file__
    try:
        _this_file = os.path.abspath(__file__)
        # flet_learnix/services/db_services.py → root is 3 parent dirs up
        _project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(_this_file))
        )
    except NameError:
        _project_root = os.getcwd()

    candidate = os.path.join(_project_root, "app", "backend")
    if os.path.isdir(candidate) and candidate not in sys.path:
        sys.path.insert(0, candidate)


_ensure_backend_importable()

from db_functions import (  # noqa: E402
    init_db as _backend_init_db,
    get_db_connection,
    get_or_create_student,
    get_or_create_subject,
    get_or_create_term,
    get_students,
    get_subjects,
    upload_grades_from_excel,
    register_user,
    verify_user,
    log_activity,
    seed_default_admin,
    migrate_plaintext_passwords,
    decrypt_field,
    encrypt_field,
    toggle_user_status,
    delete_user,
    edit_subject,
    delete_subject_ext,
    reset_user_pwd,
)

from constants import QUARTERS, COMPONENTS

def init_app_tables():
    conn = get_db_connection()
    if conn is None:
        return
    try:
        c = conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS component_grades (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                term_id    INTEGER NOT NULL,
                component  TEXT    NOT NULL,
                score      REAL,
                UNIQUE (student_id, subject_id, term_id, component),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (term_id)    REFERENCES terms(id)    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS teacher_notes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id    INTEGER NOT NULL,
                note          TEXT    NOT NULL,
                date_recorded DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
        """)

        for q in QUARTERS:
            c.execute("INSERT OR IGNORE INTO terms (name) VALUES (?)", (q,))
        conn.commit()
    finally:
        conn.close()

def app_init_db():
    _backend_init_db()
    init_app_tables()
    seed_default_admin()
    migrate_plaintext_passwords()

def get_subject_row(name: str):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        c = conn.cursor()
        c.execute("SELECT id, name FROM subjects WHERE name = ?", (name,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_student_row(name: str):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        c = conn.cursor()
        c.execute("SELECT id, name FROM students WHERE name = ?", (name,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_term_row(name: str):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        c = conn.cursor()
        c.execute("SELECT id, name FROM terms WHERE name = ?", (name,))
        row = c.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def resolve_student_id(student_name: str):
    for nm in (
        student_name,
        student_name.replace(" ", "."),
        student_name.replace(".", " "),
    ):
        r = get_student_row(nm)
        if r:
            return r["id"]
    return None

def get_total_subjects_count() -> int:
    conn = get_db_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM subjects WHERE name != '__TERM_ATT__'")
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        conn.close()

def save_student_attendance(student_id: int, term_id: int, code: str):
    mapping = {"P": 100.0, "L": 50.0, "A": 0.0}
    pct = mapping.get(str(code).upper().strip(), 0.0)
    conn = get_db_connection()
    if conn is None:
        return
    try:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO subjects (name) VALUES ('__TERM_ATT__')")
        c.execute("SELECT id FROM subjects WHERE name = '__TERM_ATT__'")
        sentinel_id = c.fetchone()["id"]
        c.execute(
            """
            INSERT OR REPLACE INTO attendance
                (student_id, subject_id, attendance_percentage)
            VALUES (?, ?, ?)
        """,
            (student_id, sentinel_id, pct),
        )
        conn.commit()
    finally:
        conn.close()

def load_student_attendance_code(student_id: int) -> str:
    conn = get_db_connection()
    if conn is None:
        return "P"
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM subjects WHERE name = '__TERM_ATT__'")
        row = c.fetchone()
        if row is None:
            return "P"
        c.execute(
            """
            SELECT attendance_percentage FROM attendance
            WHERE student_id = ? AND subject_id = ?
        """,
            (student_id, row["id"]),
        )
        res = c.fetchone()
        if res is None:
            return "P"
        pct = res["attendance_percentage"]
        if pct >= 80:
            return "P"
        if pct >= 40:
            return "L"
        return "A"
    finally:
        conn.close()
