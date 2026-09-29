from typing import Iterable

from newsflash.elements import Input, Textarea, Button, Vertical, Link
from newsflash.models import Element

from .constants import PATH_TO_NOTES


class NoteIDInput(Input):
    id: str = "note-id-input"
    input_type: str = "hidden"


class NoteTextarea(Textarea):
    id: str = "note-textarea"
    placeholder: str = "write a note..."
    rows: int = 15


class SaveNoteButton(Button):
    id: str = "save-note-button"
    label: str = "Save"


class NotesList(Vertical):
    id: str = "notes-list"

    def compose(self) -> Iterable[Element]:
        all_note_files = sorted(PATH_TO_NOTES.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        all_note_ids = [note_file.name.removesuffix(".md") for note_file in all_note_files]
            
        for note_id in all_note_ids:
            yield Link(
                id=f"note-link-{note_id}",
                href=f"/?note-id={note_id}",
                text=(PATH_TO_NOTES / f"{note_id}.md").read_text()[:100],
            )
