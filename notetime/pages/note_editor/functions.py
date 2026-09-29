from typing import Iterable
import uuid

from fastapi import HTTPException

from newsflash import FunctionRegistry, Page
from newsflash.models import Element
from newsflash.elements import Notification

from .elements import (
    SaveNoteButton,
    NoteIDInput,
    NoteTextarea,
    NotesList,
)
from .constants import PATH_TO_NOTES


function_registry = FunctionRegistry()


@function_registry.add(on=SaveNoteButton().click())
def save_new_note(
    note_id_input: NoteIDInput,
    note_textarea: NoteTextarea,
) -> Iterable[Element]:
    note_text = note_textarea.value

    if note_id_input.value == "":
        note_id = uuid.uuid4()
    else:
        note_id = note_id_input.value
    
    path = PATH_TO_NOTES / f"{note_id}.md"

    if note_id_input.value == "" and note_text == "":
        raise HTTPException(status_code=400, detail="new note cannot be empty")
    elif note_id_input.value != "" and note_text == "":
        path.unlink()
        
        # Refresh the page
        yield Page(path="/")
    else:
        path.write_text(note_text)

        # Empty the new note textarea
        yield NoteTextarea()

        # Update the notes list
        yield NotesList()

        yield Notification(message="New note saved successfully.")
