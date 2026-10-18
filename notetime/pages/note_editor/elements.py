from typing import Iterable

from newsflash.elements import Input, Textarea, Button, Horizontal
from newsflash.models import Element


class NoteIDInput(Input):
    id: str = "note-id-input"
    input_type: str = "hidden"


class NoteTextarea(Textarea):
    id: str = "note-textarea"
    placeholder: str = "write a note..."
    rows: int = 15


class NewNoteButton(Button):
    id: str = "new-note-button"
    label: str = "New"


class SaveNoteButton(Button):
    id: str = "save-note-button"
    label: str = "Save"


class NoteEditorButtons(Horizontal):
    id: str = "note-editor-buttons"
    flex_sizes: list[int] = [1, 1]

    def compose(self) -> Iterable[Element]:
        yield NewNoteButton()
        yield SaveNoteButton()
