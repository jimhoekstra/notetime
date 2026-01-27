from unittest import TestCase
from pathlib import Path
import sqlite3

from notetime.db import (
    initialize_database,
    create_note,
    update_note,
    get_note_by_id,
)


class TestDB(TestCase):
    def setUp(self) -> None:
        self.db_path = Path(":memory:")
        self.con = sqlite3.connect(self.db_path)
        self.cur = self.con.cursor()
        initialize_database(self.con, self.cur)

    def tearDown(self) -> None:
        self.con.close()

    def test_initialize_database(self):
        self.cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table';
        """)

        tables: set[str] = {row[0] for row in self.cur.fetchall()}
        tables = {table for table in tables if not table.startswith("sqlite_")}
        expected_tables = {"notes", "tags", "note_tags"}
        self.assertEqual(tables, expected_tables)

    def test_create_note(self):
        note = create_note(
            con=self.con,
            cur=self.cur,
            text="Test note\nThis is a test note.",
            tags=["test", "note"],
        )
        self.assertIsNotNone(note.id)
        assert note.id is not None

        # TODO: Uncomment when tags are implemented in create_note
        # all_tags = set(get_all_tags(self.cur))
        # self.assertEqual(all_tags, {"test", "note"})

        retrieved_note = get_note_by_id(self.cur, note.id)
        self.assertIsNotNone(retrieved_note)
        assert retrieved_note is not None

        self.assertEqual(retrieved_note.title, "Test note")
        self.assertEqual(retrieved_note.text, "This is a test note.")
        # TODO: Uncomment when tags are implemented in create_note
        # self.assertEqual(set(retrieved_note.tags), {"test", "note"})

    def test_update_note(self):
        note = create_note(
            con=self.con,
            cur=self.cur,
            text="Test note\nThis is the initial note.",
        )

        self.assertIsNotNone(note.id)
        assert note.id is not None

        note.title = "Test note"
        note.text = "This is the updated note."
        note.tags = ["updated", "note"]

        update_note(
            con=self.con,
            cur=self.cur,
            note=note,
        )

        retrieved_note = get_note_by_id(self.cur, note.id)
        self.assertIsNotNone(retrieved_note)
        assert retrieved_note is not None

        self.assertEqual(retrieved_note.title, "Test note")
        self.assertEqual(retrieved_note.text, "This is the updated note.")
        # TODO: Uncomment when tags are implemented in update_note
        # self.assertEqual(set(retrieved_note.tags), {"updated", "note"})

    def test_delete_unused_tags(self):
        note = create_note(
            con=self.con,
            cur=self.cur,
            text="Test note\nThis is the initial note.",
        )

        self.assertIsNotNone(note.id)
        assert note.id is not None

        note.title = "Test note"
        note.text = "This is the updated note."
        note.tags = ["updated", "note"]

        update_note(
            con=self.con,
            cur=self.cur,
            note=note,
        )

        retrieved_note = get_note_by_id(self.cur, note.id)
        self.assertIsNotNone(retrieved_note)
        assert retrieved_note is not None

        self.assertEqual(retrieved_note.title, "Test note")
        self.assertEqual(retrieved_note.text, "This is the updated note.")
        # TODO: Uncomment when tags are implemented in update_note
        # self.assertEqual(set(retrieved_note.tags), {"updated", "note"})

        # TODO: Uncomment when tags are implemented in update_note
        # all_tags = set(get_all_tags(self.cur))
        # self.assertEqual(all_tags, {"initial", "updated", "note"})

        # delete_unused_tags(self.con, self.cur)

        # TODO: Uncomment when tags are implemented in update_note
        # all_tags_after_deletion = set(get_all_tags(self.cur))
        # self.assertEqual(all_tags_after_deletion, {"updated", "note"})
