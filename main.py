import sqlite3
from pathlib import Path

from notetime.db import (
    initialize_database,
)

if __name__ == "__main__":
    path_to_db = Path.cwd() / "db.sqlite3"
    path_to_db.unlink(missing_ok=True)

    con = sqlite3.connect(path_to_db)
    cur = con.cursor()
    initialize_database(con, cur)
