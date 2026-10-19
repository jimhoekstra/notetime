from typing import Iterable

from newsflash import Page, FunctionRegistry
from newsflash.elements import NotificationContainer
from newsflash.models import Element

from notetime.elements.page_header import PageHeader

from .elements import NoteIDInput, NoteTextarea, NoteEditorButtons
from .functions import function_registry
from .constants import PATH_TO_NOTES


class NoteEditorPage(Page):
    path: str = "/"
    function_registry: FunctionRegistry = function_registry
    page_title: str = "notetime"

    def compose(self) -> Iterable[Element]:
        note_id = self.request.query_params.get("note-id")
        if note_id is not None:
            path_to_note = PATH_TO_NOTES / f"{note_id}.md"
            if not path_to_note.exists():
                yield Page(path="/")
        
            note_text = path_to_note.read_text()
        else:
            note_id = ""
            note_text = ""

        yield PageHeader()
        yield NoteIDInput(value=note_id)
        yield NoteTextarea(value=note_text, autofocus=note_id == "")
        yield NoteEditorButtons()
        yield NotificationContainer()
