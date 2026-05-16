from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import SCHEMA_VERSION, get_connection, get_schema_version, init_db


if __name__ == "__main__":
    with get_connection() as conn:
        before = get_schema_version(conn)

    applied = init_db()

    with get_connection() as conn:
        after = get_schema_version(conn)

    if before > 0 and before == after:
        print(
            f"Database already initialized at schema version v{after}. "
            "No destructive overwrite was performed."
        )
    elif before > 0 and before != after:
        print(f"Database schema upgraded from v{before} to v{after}.")
    else:
        print(f"Database initialized at schema version v{applied}.")

    if after != SCHEMA_VERSION:
        print(
            f"WARNING: Expected schema version v{SCHEMA_VERSION}, "
            f"but DB reports v{after}. Please check migrations manually."
        )
