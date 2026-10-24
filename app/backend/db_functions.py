# file connections / imports
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import bcrypt

# fernet symmetric encryption for sensitive fields
# Used to encrypt PII such as user_id_code and activity log details.
try:
    from cryptography.fernet import Fernet as _Fernet
    _CRYPTO_AVAILABLE = True
except ImportError:
    _Fernet = None  # type: ignore
    _CRYPTO_AVAILABLE = False

# Cross-platform path resolution
# Import from centralized resolver; fall back to LOCALAPPDATA\Learnix\data
# (or ~/.learnix/data on non-Windows) — NEVER relative to CWD or System32.
try:
    from services.paths import get_db_path as _get_default_db_path, get_fernet_key_path as _get_fernet_key_path_fn
    DEFAULT_DB_PATH = Path(_get_default_db_path())
    _FERNET_KEY_PATH = Path(_get_fernet_key_path_fn())
except ImportError:
    # Standalone fallback: use the same LOCALAPPDATA logic as paths.py
    import os as _os
    _local_app_data = _os.environ.get("LOCALAPPDATA", "").strip()
    if _local_app_data:
        _safe_data_dir = Path(_local_app_data) / "Learnix" / "data"
    else:
        _safe_data_dir = Path.home() / ".learnix" / "data"
    _safe_data_dir.mkdir(parents=True, exist_ok=True)
    DEFAULT_DB_PATH = _safe_data_dir / "school_data.db"
    _FERNET_KEY_PATH = _safe_data_dir / "secret.key"

DB_PATH: Optional[str] = None
_fernet_cache: Optional[object] = None


# resolve db path
def _resolve_db_path(db_path: Optional[str] = None) -> str:
    if db_path:
        return os.path.abspath(db_path)
    if DB_PATH:
        return DB_PATH
    env = os.environ.get("SCHOOL_DB_PATH")
    if env:
        return os.path.abspath(env)
    return str(DEFAULT_DB_PATH)


# configure db path
def _configure_db_path(db_path: str) -> str:
    global DB_PATH
    DB_PATH = os.path.abspath(db_path)
    return DB_PATH


# safe print
def _safe_print(message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", errors="replace").decode("ascii"))


# get db connection
def get_db_connection(db_path: Optional[str] = None) -> Optional[sqlite3.Connection]:
    try:
        path = _resolve_db_path(db_path)
        db_dir = os.path.dirname(path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None


# row to dict
def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    return dict(row) if row else None


# rows to list
def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(row) for row in rows]


# execute in transaction
def _execute_in_transaction(func, *args, **kwargs):
    conn = kwargs.pop("conn", None)
    own_conn = conn is None
    if own_conn:
        conn = get_db_connection()
    if conn is None:
        return None
    try:
        result = func(conn, *args, **kwargs)
        if own_conn:
            conn.commit()
        return result
    except Exception as e:
        if own_conn:
            conn.rollback()
        print(f"Transaction error: {e}")
        raise
    finally:
        if own_conn and conn:
            conn.close()


# init db
def init_db(db_path: Optional[str] = None) -> bool:
    if db_path:
        _configure_db_path(db_path)

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON;")
        c.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS terms (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
        """)
        c.execute("""
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
        c.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id            INTEGER NOT NULL,
                subject_id            INTEGER NOT NULL,
                attendance_percentage REAL DEFAULT 0,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                CONSTRAINT unique_attendance_per_subject UNIQUE (student_id, subject_id)
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                user_id_code TEXT
            );
        """)
        try:
            c.execute("ALTER TABLE users ADD COLUMN is_disabled INTEGER DEFAULT 0;")
        except sqlite3.OperationalError:
            pass # column exists
            
# activity log for audit trail
        # Tracks every login, logout, account creation/deletion, and password change.
        c.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT    NOT NULL,
                action    TEXT    NOT NULL,
                role      TEXT    DEFAULT '',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                details   TEXT    DEFAULT ''
            );
        """)
# separate admin accounts table
        # Admin credentials are isolated from teacher/parent accounts for security.
        # Scalability: Add 'permissions' column to support granular admin roles.
        c.execute("""
            CREATE TABLE IF NOT EXISTS admin_accounts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active     INTEGER  DEFAULT 1
            );
        """)
        conn.commit()
        _safe_print("[OK] Database tables created/verified.")
        return True
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        return False
    finally:
        conn.close()


# get or create student
def get_or_create_student(
    name: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[Dict[str, Any]]:
    # fn
    def _fn(conn, student_name):
        student_name = student_name.strip()
        if not student_name:
            print("Error: Student name cannot be empty.")
            return None
        c = conn.cursor()
        c.execute("SELECT id, name FROM students WHERE name = ?", (student_name,))
        existing = c.fetchone()
        if existing:
            return row_to_dict(existing)
        c.execute("INSERT INTO students (name) VALUES (?)", (student_name,))
        c.execute("SELECT id, name FROM students WHERE id = ?", (c.lastrowid,))
        return row_to_dict(c.fetchone())

    return _execute_in_transaction(_fn, name, conn=conn)


# get or create subject
def get_or_create_subject(
    name: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[Dict[str, Any]]:
    # fn
    def _fn(conn, subject_name):
        subject_name = subject_name.strip()
        if not subject_name:
            print("Error: Subject name cannot be empty.")
            return None
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO subjects (name) VALUES (?)", (subject_name,))
        c.execute("SELECT id, name FROM subjects WHERE name = ?", (subject_name,))
        return row_to_dict(c.fetchone())

    return _execute_in_transaction(_fn, name, conn=conn)


# add student
def add_student(
    name: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[Dict[str, Any]]:
    return get_or_create_student(name, conn=conn)


# get students
def get_students(conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    def _fn(conn):
        c = conn.cursor()
        c.execute("SELECT id, name FROM students ORDER BY name")
        return rows_to_list(c.fetchall())

    return _execute_in_transaction(_fn, conn=conn) or []


# get student
def get_student(
    student_id: int, conn: Optional[sqlite3.Connection] = None
) -> Optional[Dict[str, Any]]:
    # fn
    def _fn(conn, sid):
        c = conn.cursor()
        c.execute("SELECT id, name FROM students WHERE id = ?", (sid,))
        return row_to_dict(c.fetchone())

    return _execute_in_transaction(_fn, student_id, conn=conn)


# delete student
def delete_student(student_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    def _fn(conn, sid):
        c = conn.cursor()
        c.execute("DELETE FROM students WHERE id = ?", (sid,))
        return c.rowcount > 0

    return _execute_in_transaction(_fn, student_id, conn=conn) or False


# add subject
def add_subject(
    name: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[Dict[str, Any]]:
    return get_or_create_subject(name, conn=conn)


# get subjects
def get_subjects(conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    def _fn(conn):
        c = conn.cursor()
        c.execute("SELECT id, name FROM subjects ORDER BY name")
        return rows_to_list(c.fetchall())

    return _execute_in_transaction(_fn, conn=conn) or []


# delete subject
def delete_subject(subject_id: int, conn: Optional[sqlite3.Connection] = None) -> bool:
    def _fn(conn, sid):
        c = conn.cursor()
        c.execute("DELETE FROM subjects WHERE id = ?", (sid,))
        return c.rowcount > 0

    return _execute_in_transaction(_fn, subject_id, conn=conn) or False


# get or create term
def get_or_create_term(
    term_name: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[Dict[str, Any]]:
    # fn
    def _fn(conn, tname):
        tname = tname.strip()
        if not tname:
            print("Error: Term name cannot be empty.")
            return None
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO terms (name) VALUES (?)", (tname,))
        c.execute("SELECT id, name FROM terms WHERE name = ?", (tname,))
        return row_to_dict(c.fetchone())

    return _execute_in_transaction(_fn, term_name, conn=conn)


# insert grade
def insert_grade(
    student_id: int,
    subject_id: int,
    term_id: int,
    score: float,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[Dict[str, Any]]:
    if not (0 <= score <= 100):
        print(f"Error: Score {score} out of range (0-100).")
        return None

    # fn
    def _fn(conn, sid, subid, tid, sc):
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO grades (student_id, subject_id, term_id, score)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_id, subject_id, term_id)
            DO UPDATE SET score = excluded.score
        """,
            (sid, subid, tid, sc),
        )
        c.execute(
            """
            SELECT * FROM grades
            WHERE student_id = ? AND subject_id = ? AND term_id = ?
        """,
            (sid, subid, tid),
        )
        return row_to_dict(c.fetchone())

    return _execute_in_transaction(
        _fn, student_id, subject_id, term_id, score, conn=conn
    )


# fetch grades by student
def fetch_grades_by_student(
    student_id: int, conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    # fn
    def _fn(conn, sid):
        c = conn.cursor()
        c.execute(
            """
            SELECT g.id, g.score, s.name AS student_name,
                   sub.name AS subject_name, t.name AS term_name
            FROM grades g
            JOIN students s   ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
            JOIN terms t      ON g.term_id    = t.id
            WHERE g.student_id = ?
            ORDER BY t.name, sub.name
        """,
            (sid,),
        )
        return rows_to_list(c.fetchall())

    return _execute_in_transaction(_fn, student_id, conn=conn) or []


# fetch grades by subject
def fetch_grades_by_subject(
    subject_id: int, conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    # fn
    def _fn(conn, subid):
        c = conn.cursor()
        c.execute(
            """
            SELECT g.id, g.score, s.name AS student_name,
                   sub.name AS subject_name, t.name AS term_name
            FROM grades g
            JOIN students s   ON g.student_id = s.id
            JOIN subjects sub ON g.subject_id = sub.id
            JOIN terms t      ON g.term_id    = t.id
            WHERE g.subject_id = ?
            ORDER BY t.name, s.name
        """,
            (subid,),
        )
        return rows_to_list(c.fetchall())

    return _execute_in_transaction(_fn, subject_id, conn=conn) or []


# insert attendance
def insert_attendance(
    student_id: int,
    subject_id: int,
    attendance_percentage: float,
    conn: Optional[sqlite3.Connection] = None,
) -> Optional[Dict[str, Any]]:
    if not (0 <= attendance_percentage <= 100):
        print(f"Error: Attendance {attendance_percentage} out of range (0-100).")
        return None

    # fn
    def _fn(conn, sid, subid, att):
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO attendance (student_id, subject_id, attendance_percentage)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id, subject_id)
            DO UPDATE SET attendance_percentage = excluded.attendance_percentage
        """,
            (sid, subid, att),
        )
        c.execute(
            """
            SELECT * FROM attendance WHERE student_id = ? AND subject_id = ?
        """,
            (sid, subid),
        )
        return row_to_dict(c.fetchone())

    return _execute_in_transaction(
        _fn, student_id, subject_id, attendance_percentage, conn=conn
    )


# fetch attendance by student
def fetch_attendance_by_student(
    student_id: int, conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    # fn
    def _fn(conn, sid):
        c = conn.cursor()
        c.execute(
            """
            SELECT a.id, a.attendance_percentage, s.name AS student_name,
                   sub.name AS subject_name
            FROM attendance a
            JOIN students s   ON a.student_id = s.id
            JOIN subjects sub ON a.subject_id = sub.id
            WHERE a.student_id = ?
            ORDER BY sub.name
        """,
            (sid,),
        )
        return rows_to_list(c.fetchall())

    return _execute_in_transaction(_fn, student_id, conn=conn) or []


# calculate student average
def calculate_student_average(
    student_id: int, conn: Optional[sqlite3.Connection] = None
) -> float:
    # fn
    def _fn(conn, sid):
        c = conn.cursor()
        c.execute("SELECT AVG(score) FROM grades WHERE student_id = ?", (sid,))
        avg = c.fetchone()[0]
        return avg if avg is not None else 0.0

    return _execute_in_transaction(_fn, student_id, conn=conn) or 0.0


# calculate subject average
def calculate_subject_average(
    subject_id: int, conn: Optional[sqlite3.Connection] = None
) -> float:
    # fn
    def _fn(conn, subid):
        c = conn.cursor()
        c.execute("SELECT AVG(score) FROM grades WHERE subject_id = ?", (subid,))
        avg = c.fetchone()[0]
        return avg if avg is not None else 0.0

    return _execute_in_transaction(_fn, subject_id, conn=conn) or 0.0


# get top students
def get_top_students(
    limit: int = 5, conn: Optional[sqlite3.Connection] = None
) -> List[Dict[str, Any]]:
    # fn
    def _fn(conn, lim):
        c = conn.cursor()
        c.execute(
            """
            SELECT s.name AS student_name, AVG(g.score) AS average_score
            FROM students s
            JOIN grades g ON s.id = g.student_id
            GROUP BY s.id
            ORDER BY average_score DESC
            LIMIT ?
        """,
            (lim,),
        )
        return rows_to_list(c.fetchall())

    return _execute_in_transaction(_fn, limit, conn=conn) or []


# get db analytics summary
def get_db_analytics_summary(
    conn: Optional[sqlite3.Connection] = None,
) -> Dict[str, Any]:
    # fn
    def _fn(conn):
        c = conn.cursor()

        c.execute("SELECT COUNT(id) FROM students")
        total_students = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(id) FROM subjects")
        total_subjects = c.fetchone()[0] or 0

        c.execute("SELECT AVG(score) FROM grades")
        class_avg = c.fetchone()[0] or 0.0

        c.execute("""
            SELECT sub.name, AVG(g.score) AS avg_score
            FROM grades g
            JOIN subjects sub ON g.subject_id = sub.id
            GROUP BY sub.id
            ORDER BY avg_score DESC
            LIMIT 1
        """)
        strongest = c.fetchone()
        strongest_subject = strongest["name"] if strongest else "N/A"
        strongest_score = strongest["avg_score"] if strongest else 0.0

        c.execute("""
            SELECT sub.name, AVG(g.score) AS avg_score
            FROM grades g
            JOIN subjects sub ON g.subject_id = sub.id
            GROUP BY sub.id
            HAVING avg_score < 60
            ORDER BY avg_score
        """)
        weak_subjects = [row["name"] for row in c.fetchall()]

        c.execute("""
            SELECT s.name, AVG(g.score) AS avg_score
            FROM grades g
            JOIN students s ON g.student_id = s.id
            GROUP BY s.id
            ORDER BY avg_score DESC
            LIMIT 1
        """)
        top = c.fetchone()
        top_student = top["name"] if top else "N/A"
        top_score = top["avg_score"] if top else 0.0

        c.execute("SELECT AVG(attendance_percentage) FROM attendance")
        attendance_avg = c.fetchone()[0] or 0.0

        summary = {
            "total_students": total_students,
            "total_subjects": total_subjects,
            "class_average": class_avg,
            "strongest_subject": strongest_subject,
            "strongest_subject_score": strongest_score,
            "weak_subjects": weak_subjects,
            "top_student": top_student,
            "top_student_score": top_score,
            "attendance_average": attendance_avg,
        }

        try:
            import pandas as pd

            df_grades = pd.read_sql_query(
                """
                SELECT s.name AS Student, sub.name AS Subject, t.name AS Quarter, g.score
                FROM grades g
                JOIN students s   ON g.student_id = s.id
                JOIN subjects sub ON g.subject_id = sub.id
                JOIN terms t      ON g.term_id    = t.id
            """,
                conn,
            )
            df_att = pd.read_sql_query(
                """
                SELECT s.name AS Student, sub.name AS Subject, a.attendance_percentage
                FROM attendance a
                JOIN students s   ON a.student_id = s.id
                JOIN subjects sub ON a.subject_id = sub.id
            """,
                conn,
            )
            summary["overall_grades_df"] = df_grades
            summary["overall_attendance_df"] = df_att
        except ImportError:
            pass

        return summary

    return _execute_in_transaction(_fn, conn=conn) or {}


# upload grades from excel
def upload_grades_from_excel(
    file_path: str, clear_existing: bool = False
) -> Tuple[bool, str]:
    try:
        import pandas as pd
    except ImportError:
        return False, "pandas is required for Excel upload. Please install it."

    conn = get_db_connection()
    if conn is None:
        return False, "Could not connect to database."

    try:
        try:
            df = pd.read_excel(file_path)
        except ImportError as e:
            return False, f"Excel support dependency missing: {e}"

        required = {"student_name", "subject", "score", "attendance_percentage", "term"}
        if not required.issubset(df.columns):
            return False, f"Missing columns. Required: {required}"

        if clear_existing:
            c = conn.cursor()
            for tbl in ["grades", "attendance", "students", "subjects", "terms"]:
                c.execute(f"DELETE FROM {tbl}")
            conn.commit()

        for _, row in df.iterrows():
            student_name = str(row["student_name"]).strip()
            subject_name = str(row["subject"]).strip()
            term_name = str(row["term"]).strip()
            score = float(row["score"]) if pd.notna(row["score"]) else 0.0
            attendance_pct = (
                float(row["attendance_percentage"])
                if pd.notna(row["attendance_percentage"])
                else 0.0
            )

            if not (0 <= score <= 100):
                raise ValueError(
                    f"Score {score} out of range for student {student_name}"
                )
            if not (0 <= attendance_pct <= 100):
                raise ValueError(
                    f"Attendance {attendance_pct} out of range for student {student_name}"
                )

            student = get_or_create_student(student_name, conn=conn)
            if student is None:
                raise ValueError(f"Failed to get/create student '{student_name}'")

            subject = get_or_create_subject(subject_name, conn=conn)
            if subject is None:
                raise ValueError(f"Failed to get/create subject '{subject_name}'")

            term = get_or_create_term(term_name, conn=conn)
            if term is None:
                raise ValueError(f"Failed to get/create term '{term_name}'")

            grade = insert_grade(
                student["id"], subject["id"], term["id"], score, conn=conn
            )
            if grade is None:
                raise ValueError(
                    f"Failed to insert grade for {student_name}, {subject_name}, {term_name}"
                )

            att = insert_attendance(
                student["id"], subject["id"], attendance_pct, conn=conn
            )
            if att is None:
                raise ValueError(
                    f"Failed to insert attendance for {student_name}, {subject_name}"
                )

        conn.commit()
        return True, "Excel data successfully uploaded."
    except Exception as e:
        conn.rollback()
        return False, f"Error processing Excel upload: {e}"
    finally:
        conn.close()


# insert subjects manually
def insert_subjects_manually(
    subjects_list: List[str], conn: Optional[sqlite3.Connection] = None
) -> int:
    count = 0

    # fn
    def _fn(conn, subjects):
        nonlocal count
        c = conn.cursor()
        for name in subjects:
            cleaned = name.strip()
            if not cleaned:
                continue
            try:
                c.execute("INSERT INTO subjects (name) VALUES (?)", (cleaned,))
                count += 1
            except sqlite3.IntegrityError:
                pass
        return count

    return _execute_in_transaction(_fn, subjects_list, conn=conn) or 0


# register user
def register_user(
    username: str, password: str, role: str, user_id_code: str = "", conn: Optional[sqlite3.Connection] = None
) -> Tuple[bool, str]:
# password hashing
    # Password is hashed using bcrypt before inserting into the database
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _fn(conn, uname, pwd_hash, r, id_code):
        c = conn.cursor()
        try:
            c.execute(
                """
                INSERT INTO users (username, password_hash, role, user_id_code)
                VALUES (?, ?, ?, ?)
            """,
                (uname, pwd_hash, r, id_code)
            )
            return True, "User registered successfully."
        except sqlite3.IntegrityError:
            return False, "Username already exists."
        except Exception as e:
            return False, f"An error occurred: {e}"

    return _execute_in_transaction(_fn, username.lower(), hashed, role, user_id_code, conn=conn) or (False, "Transaction failed")


# verify user
def verify_user(
    username: str, password: str, role: str, conn: Optional[sqlite3.Connection] = None
) -> bool:
    def _fn(conn, uname, r):
        c = conn.cursor()
        c.execute(
            """
            SELECT password_hash, is_disabled FROM users WHERE username = ? AND role = ?
        """,
            (uname, r)
        )
        row = c.fetchone()
        return row_to_dict(row)

    user_data = _execute_in_transaction(_fn, username.lower(), role, conn=conn)
    if not user_data:
        return False
        
    if user_data.get("is_disabled", 0) == 1:
        return False

# login verification
    # Hashed password retrieved from DB is checked against the incoming password
    stored_hash = user_data["password_hash"]
    try:
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return True
    except Exception as e:
        print(f"Error checking password: {e}")
    return False


# get fernet
def _get_fernet():
    """Load or auto-generate Fernet key for symmetric encryption.
    Key is stored in %LOCALAPPDATA%\\Learnix\\data\\secret.key — keep this file safe.
    Losing the key means encrypted data is permanently unreadable.
    """
    global _fernet_cache
    if not _CRYPTO_AVAILABLE:
        return None
    if _fernet_cache is not None:
        return _fernet_cache
    try:
        if not _FERNET_KEY_PATH.exists():
            _FERNET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
            key = _Fernet.generate_key()
            _FERNET_KEY_PATH.write_bytes(key)
        _fernet_cache = _Fernet(_FERNET_KEY_PATH.read_bytes())
        return _fernet_cache
    except Exception as e:
        print(f"[WARN] Fernet key error: {e}")
        return None


# encrypt field
def encrypt_field(value: str) -> str:
    """Encrypt a string field using Fernet symmetric encryption.
    Returns original value if encryption unavailable.
    """
    if not value:
        return value
    f = _get_fernet()
    if f is None:
        return value
    try:
        return f.encrypt(value.encode('utf-8')).decode('utf-8')
    except Exception:
        return value


# decrypt field
def decrypt_field(value: str) -> str:
    """Decrypt a Fernet-encrypted string field.
    Returns original value if decryption fails (e.g. plaintext legacy data).
    """
    if not value:
        return value
    f = _get_fernet()
    if f is None:
        return value
    try:
        return f.decrypt(value.encode('utf-8')).decode('utf-8')
    except Exception:
        return value  # Return as-is if not encrypted (legacy plaintext)


# seed default admin
def seed_default_admin() -> None:
    """Create the default admin account if none exists.
    Default credentials: admin / admin123
    IMPORTANT: Change this password on first login in production.
    Scalability: Add multiple admin accounts by role (super-admin, read-only-admin, etc.)
    """
    conn = get_db_connection()
    if conn is None:
        return
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM admin_accounts")
        count = c.fetchone()[0]
        if count == 0:
            # Hash the default password with bcrypt
            default_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
            c.execute(
                "INSERT INTO admin_accounts (username, password_hash) VALUES (?, ?)",
                ('admin', default_hash)
            )
            conn.commit()
            _safe_print("[OK] Default admin account created (admin / admin123). Change on first login.")
    except Exception as e:
        print(f"[WARN] seed_default_admin: {e}")
    finally:
        conn.close()


# verify admin
def verify_admin(username: str, password: str) -> bool:
    """Verify admin credentials against admin_accounts table using bcrypt."""
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        c = conn.cursor()
        c.execute(
            "SELECT password_hash FROM admin_accounts WHERE username = ? AND is_active = 1",
            (username.strip().lower(),)
        )
        row = c.fetchone()
        if row is None:
            return False
        stored_hash = row['password_hash']
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception as e:
        print(f"[WARN] verify_admin: {e}")
        return False
    finally:
        conn.close()


# log activity
def log_activity(username: str, action: str, role: str = '', details: str = '') -> None:
    """Append an entry to the activity_log table.
    Details field is encrypted using Fernet for PII protection.
    """
    conn = get_db_connection()
    if conn is None:
        return
    try:
        # Encrypt details before storing to protect sensitive info
        encrypted_details = encrypt_field(details) if details else ''
        c = conn.cursor()
        c.execute(
            "INSERT INTO activity_log (username, action, role, details) VALUES (?, ?, ?, ?)",
            (username, action, role, encrypted_details)
        )
        conn.commit()
    except Exception as e:
        print(f"[WARN] log_activity: {e}")
    finally:
        conn.close()


# get activity log
def get_activity_log(limit: int = 200) -> List[Dict[str, Any]]:
    """Retrieve recent activity log entries (newest first)."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        c = conn.cursor()
        c.execute(
            "SELECT id, username, action, role, timestamp, details "
            "FROM activity_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return rows_to_list(c.fetchall())
    except Exception:
        return []
    finally:
        conn.close()


# get all users
def get_all_users() -> List[Dict[str, Any]]:
    """Return all user accounts from the users table."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        c = conn.cursor()
        c.execute("SELECT id, username, role, user_id_code FROM users ORDER BY role, username")
        return rows_to_list(c.fetchall())
    except Exception:
        return []
    finally:
        conn.close()


# get users by role
def get_users_by_role(role: str) -> List[Dict[str, Any]]:
    """Return user accounts filtered by role."""
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        c = conn.cursor()
        c.execute(
            "SELECT id, username, role, user_id_code FROM users WHERE role = ? ORDER BY username",
            (role,)
        )
        return rows_to_list(c.fetchall())
    except Exception:
        return []
    finally:
        conn.close()


# create user account
def create_user_account(
    username: str, password: str, role: str, user_id_code: str = ''
) -> Tuple[bool, str]:
    """Admin-facing wrapper to create teacher or parent accounts.
    user_id_code is encrypted using Fernet before storage.
    """
    # Encrypt the ID code before storing (PII protection)
    encrypted_id = encrypt_field(user_id_code) if user_id_code else ''
    return register_user(username, password, role, encrypted_id)


# update user password
def update_user_password(
    username: str, new_password: str, role: str
) -> Tuple[bool, str]:
    """Reset a user's password. New password is hashed with bcrypt."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c = conn.cursor()
        c.execute(
            "UPDATE users SET password_hash = ? WHERE username = ? AND role = ?",
            (new_hash, username, role)
        )
        if c.rowcount == 0:
            return False, "User not found."
        conn.commit()
        return True, "Password updated successfully."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


# delete user account
def delete_user_account(username: str, role: str) -> Tuple[bool, str]:
    """Permanently delete a user account."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username = ? AND role = ?", (username, role))
        if c.rowcount == 0:
            return False, "User not found."
        conn.commit()
        return True, "Account deleted."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


# migrate plaintext passwords
def migrate_plaintext_passwords() -> None:
    """One-time migration: re-hash any plaintext passwords in the users table.
    bcrypt hashes always start with '$2b$' — others are treated as plaintext.
    This ensures backward compatibility when upgrading existing deployments.
    """
    conn = get_db_connection()
    if conn is None:
        return
    try:
        c = conn.cursor()
        c.execute("SELECT id, password_hash FROM users")
        rows = c.fetchall()
        migrated = 0
        for row in rows:
            ph = row['password_hash']
            # bcrypt hashes start with $2a$ or $2b$ — skip if already hashed
            if ph and not ph.startswith('$2'):
                new_hash = bcrypt.hashpw(ph.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, row['id']))
                migrated += 1
        if migrated > 0:
            conn.commit()
            _safe_print(f"[OK] Migrated {migrated} plaintext password(s) to bcrypt.")
    except Exception as e:
        print(f"[WARN] migrate_plaintext_passwords: {e}")
    finally:
        conn.close()


# update admin password
def update_admin_password(username: str, new_password: str) -> Tuple[bool, str]:
    """Update an admin account password with bcrypt hash."""
    conn = get_db_connection()
    if conn is None:
        return False, "Database connection failed."
    try:
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c = conn.cursor()
        c.execute(
            "UPDATE admin_accounts SET password_hash = ? WHERE username = ?",
            (new_hash, username.strip().lower())
        )
        if c.rowcount == 0:
            return False, "Admin account not found."
        conn.commit()
        return True, "Password updated."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

# ======== ADMIN EXTENSIONS ========

def toggle_user_status(user_id: int, is_disabled: int, conn=None) -> bool:
    def _fn(conn, uid, disabled):
        c = conn.cursor()
        c.execute("UPDATE users SET is_disabled = ? WHERE id = ?", (disabled, uid))
        return c.rowcount > 0
    return _execute_in_transaction(_fn, user_id, is_disabled, conn=conn) or False

def delete_user(user_id: int, conn=None) -> bool:
    def _fn(conn, uid):
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id = ?", (uid,))
        return c.rowcount > 0
    return _execute_in_transaction(_fn, user_id, conn=conn) or False

def edit_subject(subject_id: int, new_name: str, conn=None) -> bool:
    def _fn(conn, sid, name):
        c = conn.cursor()
        try:
            c.execute("UPDATE subjects SET name = ? WHERE id = ?", (name, sid))
            return c.rowcount > 0
        except sqlite3.IntegrityError:
            return False
    return _execute_in_transaction(_fn, subject_id, new_name, conn=conn) or False

def delete_subject_ext(subject_id: int, conn=None) -> bool:
    def _fn(conn, sid):
        c = conn.cursor()
        c.execute("DELETE FROM subjects WHERE id = ?", (sid,))
        return c.rowcount > 0
    return _execute_in_transaction(_fn, subject_id, conn=conn) or False

def reset_user_pwd(user_id: int, new_pwd: str, conn=None) -> bool:
    import bcrypt
    hashed = bcrypt.hashpw(new_pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    def _fn(conn, uid, pwd_hash):
        c = conn.cursor()
        c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, uid))
        return c.rowcount > 0
    return _execute_in_transaction(_fn, user_id, hashed, conn=conn) or False

if __name__ == "__main__":
    init_db()
    seed_default_admin()
