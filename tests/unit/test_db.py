from unittest import TestCase
from pathlib import Path
import sqlite3

from notetime.db import (
    initialize_database,
    create_note,
    update_note,
    get_note_by_id,
    get_all_tags,
    get_notes_by_tags,
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
            text="Test note\nThis is a @test @note.",
        )
        self.assertIsNotNone(note.id)
        assert note.id is not None

        all_tags = set([tag.name for tag in get_all_tags(self.cur)])
        self.assertEqual(all_tags, {"test", "note"})

        retrieved_note = get_note_by_id(self.cur, note.id)

        self.assertIsNotNone(retrieved_note)
        assert retrieved_note is not None
        assert retrieved_note.tags is not None

        self.assertEqual(retrieved_note.title, "Test note")
        self.assertEqual(retrieved_note.text, "This is a @test @note.")
        self.assertEqual(set(retrieved_note.tags), {"test", "note"})

    def test_update_note(self):
        note = create_note(
            con=self.con,
            cur=self.cur,
            text="Test note\nThis is the @initial note.",
        )

        self.assertIsNotNone(note.id)
        assert note.id is not None

        note.title = "Test note"
        note.text = "This is the @updated @note."

        update_note(
            con=self.con,
            cur=self.cur,
            note=note,
        )

        retrieved_note = get_note_by_id(self.cur, note.id)
        self.assertIsNotNone(retrieved_note)
        assert retrieved_note is not None
        assert retrieved_note.tags is not None

        self.assertEqual(retrieved_note.title, "Test note")
        self.assertEqual(retrieved_note.text, "This is the @updated @note.")
        self.assertEqual(set(retrieved_note.tags), {"updated", "note"})

    def test_delete_unused_tags(self):
        note = create_note(
            con=self.con,
            cur=self.cur,
            text="Test note\nThis is the @initial note.",
        )

        self.assertIsNotNone(note.id)
        assert note.id is not None

        note.title = "Test note"
        note.text = "This is the @updated @note."

        update_note(
            con=self.con,
            cur=self.cur,
            note=note,
        )

        retrieved_note = get_note_by_id(self.cur, note.id)
        self.assertIsNotNone(retrieved_note)
        assert retrieved_note is not None
        assert retrieved_note.tags is not None

        self.assertEqual(retrieved_note.title, "Test note")
        self.assertEqual(retrieved_note.text, "This is the @updated @note.")
        self.assertEqual(set(retrieved_note.tags), {"updated", "note"})

        # After updating the note, the "initial" tag should be unused and deleted
        all_tags = set([tag.name for tag in get_all_tags(self.cur)])
        self.assertEqual(all_tags, {"updated", "note"})

    def test_get_note_by_tag(self):
        note1 = create_note(
            con=self.con,
            cur=self.cur,
            text="Test note 1\nThis is the @first note.",
        )

        note2 = create_note(
            con=self.con,
            cur=self.cur,
            text="Test note 2\nThis is the @second note.",
        )

        note3 = create_note(
            con=self.con,
            cur=self.cur,
            text="Test note 3\nThis is the @third note with a @second tag.",
        )

        notes_with_first_tag = get_notes_by_tags(self.cur, ["first"])
        self.assertEqual(len(notes_with_first_tag), 1)
        self.assertEqual(notes_with_first_tag[0].id, note1.id)

        notes_with_second_tag = get_notes_by_tags(self.cur, ["second"])
        self.assertEqual(len(notes_with_second_tag), 2)
        note_ids_with_second_tag = {note.id for note in notes_with_second_tag}
        self.assertEqual(note_ids_with_second_tag, {note2.id, note3.id})

        notes_with_third_tag = get_notes_by_tags(self.cur, ["third"])
        self.assertEqual(len(notes_with_third_tag), 1)
        self.assertEqual(notes_with_third_tag[0].id, note3.id)

        notes_with_third_and_second_tags = get_notes_by_tags(
            self.cur, ["third", "second"]
        )
        self.assertEqual(len(notes_with_third_and_second_tags), 1)
        self.assertEqual(notes_with_third_and_second_tags[0].id, note3.id)
