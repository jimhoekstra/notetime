from typing import Iterable

from newsflash import Page, FunctionRegistry
from newsflash.elements import Header, NotificationContainer, Link
from newsflash.models import Element

from .elements import NoteIDInput, NoteTextarea, SaveNoteButton, NotesList
from .functions import function_registry
from .constants import PATH_TO_NOTES


class NoteEditorPage(Page):
    path: str = "/"
    function_registry: FunctionRegistry = function_registry

    def compose(self) -> Iterable[Element]:
        note_id = self.request.query_params.get("note-id")
        if note_id is not None:
            path_to_note = PATH_TO_NOTES / f"{note_id}.md"
            if not path_to_note.exists():
                yield NoteEditorPage()
        
            note_text = path_to_note.read_text()
        else:
            note_id = ""
            note_text = ""
        
        yield Header(id="new-note-header", text="New Note")
        yield Link(id="new-note-link", href=self.path, text="New note")

        yield NoteIDInput(value=note_id)
        yield NoteTextarea(value=note_text)
        yield SaveNoteButton()
        yield NotesList()

        yield NotificationContainer()
