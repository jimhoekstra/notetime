import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from notetime.tags import extract_tags

from pydantic import BaseModel, Field


def adapt_datetime_iso(dt: datetime) -> str:
    return dt.isoformat()


sqlite3.register_adapter(datetime, adapt_datetime_iso)

PATH_TO_DB = Path.cwd() / "data" / "db.sqlite3"


def get_db_connection() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    con = sqlite3.connect(PATH_TO_DB, check_same_thread=False)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()
    return con, cur


class Note(BaseModel):
    id: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title: str = ""
    text: str = ""
    tags: list[str] | None = None

    def set_updated_at_now(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def get_full_text(self) -> str:
        if self.title and self.text:
            return f"{self.title}\n{self.text}"
        elif self.title:
            return self.title
        else:
            return self.text

    def set_tags_from_text(self) -> None:
        self.tags = extract_tags(self.get_full_text())

    def fetch_tags_from_db(self, cur: sqlite3.Cursor) -> None:
        assert self.id is not None
        cur.execute(
            """
            SELECT t.name FROM tags t
            JOIN note_tags nt ON t.id = nt.tag_id
            WHERE nt.note_id = ?
            """,
            (self.id,),
        )
        tags = [tag_row[0] for tag_row in cur.fetchall()]
        self.tags = tags


class Tag(BaseModel):
    id: int | None = None
    name: str
    num_notes: int = 0


CREATE_NOTES = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    title TEXT,
    text TEXT
);
"""

CREATE_TAGS = """
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
"""

CREATE_NOTE_TAGS = """
CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (note_id, tag_id),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
"""


def initialize_database(con: sqlite3.Connection, cur: sqlite3.Cursor):
    cur.execute(CREATE_NOTES)
    cur.execute(CREATE_TAGS)
    cur.execute(CREATE_NOTE_TAGS)
    con.commit()

    note = create_note(
        con=con,
        cur=cur,
        text="",
    )
    assert note.id == 1


def upsert_tags(
    con: sqlite3.Connection,
    cur: sqlite3.Cursor,
    tags: list[str],
) -> list[int]:
    cur.executemany(
        """
            INSERT INTO tags (name) 
            VALUES (?) 
            ON CONFLICT(name) DO UPDATE SET name=name 
        """,
        [(tag,) for tag in tags],
    )
    con.commit()

    tag_ids_placeholders = ",".join("?" for _ in tags)
    cur.execute(
        f"""
            SELECT id FROM tags WHERE name IN ({tag_ids_placeholders})
        """,
        tags,
    )
    tag_ids = [row[0] for row in cur.fetchall()]

    return tag_ids


def update_note_tags(
    con: sqlite3.Connection,
    cur: sqlite3.Cursor,
    note_id: int,
    tag_ids: list[int],
) -> None:
    cur.execute("BEGIN;")

    tag_ids_placeholders = ",".join("?" for _ in tag_ids)
    cur.execute(
        "DELETE FROM note_tags WHERE note_id = ? AND "
        f"tag_id NOT IN ({tag_ids_placeholders})",
        (note_id, *tag_ids),
    )

    cur.executemany(
        "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
        [(note_id, tag_id) for tag_id in tag_ids],
    )

    cur.execute("COMMIT;")
    con.commit()
    delete_unused_tags(con, cur)


def create_note(
    con: sqlite3.Connection,
    cur: sqlite3.Cursor,
    text: str,
) -> Note:
    title = text.splitlines()[0] if text else ""
    if len(text.splitlines()) > 1:
        text = "\n".join(text.splitlines()[1:])
    else:
        text = ""

    note = Note(
        id=None,
        title=title,
        text=text,
    )

    note.set_tags_from_text()
    assert note.tags is not None

    cur.execute(
        "INSERT INTO notes (title, text, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (title, text, note.created_at, note.updated_at),
    )
    con.commit()

    note_id = cur.lastrowid
    assert note_id is not None
    note.id = note_id

    tag_ids = upsert_tags(con=con, cur=cur, tags=note.tags)
    update_note_tags(con=con, cur=cur, note_id=note.id, tag_ids=tag_ids)

    return note


def update_note(
    con: sqlite3.Connection,
    cur: sqlite3.Cursor,
    note: Note,
) -> Note:
    assert note.id is not None
    note.set_tags_from_text()
    assert note.tags is not None

    note.set_updated_at_now()
    cur.execute(
        "UPDATE notes SET title = ?, text = ?, updated_at = ? WHERE id = ?",
        (note.title, note.text, note.updated_at, note.id),
    )
    con.commit()

    tag_ids = upsert_tags(con=con, cur=cur, tags=note.tags)
    update_note_tags(con=con, cur=cur, note_id=note.id, tag_ids=tag_ids)

    updated_note = get_note_by_id(cur, note.id)
    assert updated_note is not None
    return updated_note


def get_note_by_id(
    cur: sqlite3.Cursor,
    note_id: int,
) -> Note | None:
    cur.execute(
        "SELECT id, created_at, updated_at, title, text FROM notes WHERE id = ?",
        (note_id,),
    )
    row = cur.fetchone()
    if row is None:
        return None

    note = Note(
        id=row[0],
        created_at=row[1],
        updated_at=row[2],
        title=row[3] or "",
        text=row[4] or "",
    )
    note.fetch_tags_from_db(cur)
    return note


def get_notes_by_tags(
    cur: sqlite3.Cursor,
    tag_names: list[str],
) -> list[Note]:
    q = f"""
        SELECT n.id, n.created_at, n.updated_at, n.title, n.text FROM notes n
        JOIN note_tags nt ON n.id = nt.note_id
        JOIN tags t ON nt.tag_id = t.id
        WHERE t.name IN ({",".join("?" for _ in tag_names)})
        GROUP BY n.id
        HAVING COUNT(DISTINCT t.id) = ?
        """

    cur.execute(
        q,
        tag_names + [len(tag_names)],
    )

    notes = []
    for row in cur.fetchall():
        note = Note(
            id=row[0],
            created_at=row[1],
            updated_at=row[2],
            title=row[3] or "",
            text=row[4] or "",
        )
        notes.append(note)

    return notes


def get_all_tags(
    cur: sqlite3.Cursor,
) -> list[Tag]:
    cur.execute("SELECT id, name FROM tags")

    tags = [
        Tag(
            id=row[0],
            name=row[1],
            num_notes=len(get_notes_by_tags(cur, [row[1]])),
        )
        for row in cur.fetchall()
    ]

    return sorted(tags, key=lambda tag: tag.num_notes, reverse=True)


def delete_unused_tags(
    con: sqlite3.Connection,
    cur: sqlite3.Cursor,
) -> None:
    cur.execute("""
        DELETE FROM tags
        WHERE id NOT IN (SELECT DISTINCT tag_id FROM note_tags)
    """)
    con.commit()


def get_in_progress_note(
    cur: sqlite3.Cursor,
) -> Note:
    note = get_note_by_id(cur, note_id=1)
    assert note is not None
    return note


def get_all_notes(cur: sqlite3.Cursor) -> list[Note]:
    cur.execute(
        "SELECT id, title, text, created_at, updated_at FROM notes ORDER BY updated_at DESC"
    )
    notes = [
        Note(
            id=row[0],
            title=row[1] or "",
            text=row[2] or "",
            created_at=row[3],
            updated_at=row[4],
        )
        for row in cur.fetchall()
        if row[0] != 1  # Exclude in-progress note
    ]

    return notes
