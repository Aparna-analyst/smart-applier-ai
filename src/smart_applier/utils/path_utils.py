# smart_applier/utils/path_utils.py
import os
from pathlib import Path
from typing import Dict


def get_project_root() -> Path:
    """
    Returns the absolute path to the main Smart Applier AI project root.
    Works for Streamlit, CLI, and module runs.
    """
    current = Path(__file__).resolve()

    # Traverse upward until we find the main project folder
    for parent in current.parents:
        if (parent / "data").exists() and (parent / "src" / "smart_applier").exists():
            return parent

    # Fallback: assume we're running from src/smart_applier
    return Path(__file__).resolve().parents[2]


def get_data_dirs() -> Dict[str, Path]:
    """
    Returns key data subdirectories used across the project.

    New keys:
      - "db_path": Path to the sqlite file (unless using in-memory DB).
      - "use_in_memory_db": bool indicating whether to use an in-memory DB.
    """
    root = get_project_root()
    data_root = root / "data"
    profiles = data_root / "profiles"
    jobs = data_root / "jobs"
    resumes = data_root / "resumes"

    # Make sure all file-system dirs exist
    for p in [data_root, profiles, jobs, resumes]:
        p.mkdir(parents=True, exist_ok=True)

    # Decide DB mode:
    # If environment variable USE_IN_MEMORY_DB is set to "1" or "true", we use an in-memory DB.
    use_in_memory = os.getenv("USE_IN_MEMORY_DB", "").lower() in ("1", "true", "yes")

    if use_in_memory:
        # Not a real filesystem path, but keep a marker so callers know we're using memory
        db_path = None
    else:
        db_path = data_root / "smart_applier.db"

    return {
        "root": data_root,
        "profiles": profiles,
        "jobs": jobs,
        "resumes": resumes,
        "db_path": db_path,
        "use_in_memory_db": use_in_memory,
    }


def ensure_database_exists():
    """
    Create/initialize the SQLite DB tables if using file-backed DB.
    This calls your db_setup.create_tables() lazily (import inside function to avoid circular imports).

    If using in-memory DB (USE_IN_MEMORY_DB=1), this function is a no-op because the in-memory DB
    must be created/initialized at runtime by whatever module opens the connection.
    """
    dirs = get_data_dirs()
    if dirs["use_in_memory_db"]:
        # In-memory DB is session-specific; initialization should happen where the connection is created.
        # We intentionally do not create a file here.
        print(" Using in-memory DB for this run (USE_IN_MEMORY_DB enabled).")
        return

    db_path = dirs["db_path"]
    # Import inside function to avoid circular imports during module import time.
    try:
        from smart_applier.database.db_setup import initialize_database
    except Exception as e:
        # If the import fails, surface a friendly message so you can debug
        raise RuntimeError(
            "Could not import smart_applier.database.db_setup.create_tables. "
            "Make sure the module exists and is importable. Original error: " + str(e)
        )

    # Create DB file and tables if missing
    if not db_path.exists():
        # ensure parent exists (should, but be safe)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        print(f" Creating SQLite DB at: {db_path}")
    initialize_database()  # create_tables should handle connection to the correct path (see db_setup)
