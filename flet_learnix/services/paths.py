"""
paths.py — Central path resolver for liq (PRODUCTION GRADE)

This is the ONLY source of truth for all file paths in the application.

Rules enforced:
  - Writable files (DB, keys, logs) → %LOCALAPPDATA%\\liq\\data  (Windows)
                                       ~/.liq/data               (fallback)
  - Bundled assets (read-only)       → sys._MEIPASS/assets           (packaged)
                                       <project_root>/assets          (dev)
  - sys._MEIPASS is ONLY used for locating bundled read-only assets.
  - sys._MEIPASS is NEVER used for writable data paths.
  - Relative paths are NEVER used anywhere.
  - The application NEVER writes to System32 or CWD.
"""

import os
import sys
import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# Runtime-context detection
# ---------------------------------------------------------------------------

def _is_packaged() -> bool:
    """Return True when running inside a PyInstaller / flet-build bundle."""
    return getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS")


def _is_mobile() -> bool:
    """Return True when running on Android or iOS (Flet mobile build)."""
    platform = os.environ.get("FLET_PLATFORM", "").lower()
    return platform in ("android", "ios")


# ---------------------------------------------------------------------------
# Writable data directory  (DB + encryption key + logs)
# ---------------------------------------------------------------------------

def get_data_dir() -> Path:
    """Return the writable data directory for this installation.

    Priority order:
      1. SCHOOL_DB_DIR env-var override  (allows CI / testing overrides)
      2. Android / iOS sandboxed storage  (FLET_APP_STORAGE_DATA)
      3. Windows → %LOCALAPPDATA%\\liq\\data
      4. macOS/Linux → ~/.liq/data   (XDG_DATA_HOME honoured when set)
      5. Ultimate fallback → ~/.liq/data

    The directory is created automatically if it does not exist.
    sys._MEIPASS is NEVER consulted here.
    """

    # 1. Explicit environment override (CI, QA, developer override)
    env_override = os.environ.get("SCHOOL_DB_DIR", "").strip()
    if env_override:
        p = Path(env_override).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 2. Mobile (Android / iOS) sandbox
    if _is_mobile():
        android_dir = os.environ.get("FLET_APP_STORAGE_DATA", "").strip()
        if android_dir:
            p = Path(android_dir)
        else:
            p = Path.home() / ".liq" / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 3. Windows — always use %LOCALAPPDATA%\liq\data
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        p = Path(local_app_data) / "liq" / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 4. macOS / Linux — respect XDG_DATA_HOME, else ~/.local/share
    xdg_data = os.environ.get("XDG_DATA_HOME", "").strip()
    if xdg_data:
        p = Path(xdg_data) / "liq"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # 5. Ultimate cross-platform fallback
    p = Path.home() / ".liq" / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Specific writable-file paths
# ---------------------------------------------------------------------------

def get_db_path() -> str:
    """Return the absolute path to the SQLite database file (writable)."""
    return str(get_data_dir() / "school_data.db")


def get_fernet_key_path() -> Path:
    """Return the absolute Path to the Fernet encryption key file (writable)."""
    return get_data_dir() / "secret.key"


def get_log_path() -> Path:
    """Return the absolute Path to the application log file (writable)."""
    return get_data_dir() / "liq.log"


# ---------------------------------------------------------------------------
# Read-only asset directory  (images, fonts, etc.)
# ---------------------------------------------------------------------------

def get_assets_dir() -> str:
    """Return the absolute path to the assets directory (READ-ONLY).

    - Packaged (sys._MEIPASS present): assets are bundled inside the executable.
    - Development: assets/ folder at the project root.

    sys._MEIPASS is ONLY used here, never for writable paths.
    """
    if _is_packaged() and hasattr(sys, "_MEIPASS"):
        p = Path(sys._MEIPASS) / "assets"
        return str(p)

    # Development: resolve from this file's location.
    # File is at: flet_learnix/services/paths.py
    # Project root is 2 levels up.
    try:
        project_root = Path(__file__).resolve().parents[2]
    except (IndexError, NameError):
        project_root = Path.cwd()
    return str(project_root / "assets")


# ---------------------------------------------------------------------------
# Bundle seed directory  (initial DB / key shipped inside the package)
# ---------------------------------------------------------------------------

def get_bundle_seed_dir() -> Path:
    """Return path to bundled seed data inside the packaged executable.

    In development this points to the project's database/ folder so that
    existing dev data is used as the seed.

    In a packaged build, PyInstaller/flet embeds the seed files under
    sys._MEIPASS/database_seed/.
    """
    if _is_packaged() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "database_seed"

    # Development: use the project-level database/ directory
    try:
        project_root = Path(__file__).resolve().parents[2]
    except (IndexError, NameError):
        project_root = Path.cwd()
    return project_root / "database"


# ---------------------------------------------------------------------------
# Seed routine — copy initial DB/key from bundle on first launch
# ---------------------------------------------------------------------------

def seed_data_from_bundle() -> None:
    """Copy the initial database and key from the bundled seed directory to the
    writable data directory.

    Rules:
      - ONLY runs if the database does NOT already exist (idempotent).
      - NEVER overwrites existing data.
      - Safe to call multiple times without damage.
    """
    target_db = Path(get_db_path())

    # Nothing to seed if the database already exists
    if target_db.exists():
        return

    seed_dir = get_bundle_seed_dir()

    # Copy the seed database if present in the bundle
    seed_db = seed_dir / "school_data.db"
    if seed_db.exists():
        target_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(seed_db), str(target_db))
        _safe_log(f"[paths] Seeded database from bundle: {target_db}")

    # Copy the seed Fernet key if present (and target doesn't exist)
    seed_key = seed_dir / "secret.key"
    target_key = get_fernet_key_path()
    if seed_key.exists() and not target_key.exists():
        target_key.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(seed_key), str(target_key))
        _safe_log(f"[paths] Seeded Fernet key from bundle: {target_key}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_log(message: str) -> None:
    """Print safely, ignoring Unicode errors in restricted consoles."""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", errors="replace").decode("ascii"))


# ---------------------------------------------------------------------------
# Sanity check — run this module directly to verify paths
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== liq Path Resolver ===")
    print(f"  Packaged    : {_is_packaged()}")
    print(f"  Mobile      : {_is_mobile()}")
    print(f"  Data dir    : {get_data_dir()}")
    print(f"  DB path     : {get_db_path()}")
    print(f"  Key path    : {get_fernet_key_path()}")
    print(f"  Log path    : {get_log_path()}")
    print(f"  Assets dir  : {get_assets_dir()}")
    print(f"  Seed dir    : {get_bundle_seed_dir()}")
    print("=== All paths resolved without error ===")
