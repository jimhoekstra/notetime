from typing import Iterable

from newsflash.models import Element
from newsflash.functions import FunctionRegistry
from local_llm.model_endpoints import retrieve

from notetime.constants import PATH_TO_NOTES
from notetime.models import Note

from .elements import SearchInput, NoteSummaryList


function_registry = FunctionRegistry()


@function_registry.add(on=SearchInput().input())
def search_notes(search_input: SearchInput) -> Iterable[Element]:
    query = search_input.value

    notes: list[Note] = []
    for file in PATH_TO_NOTES.iterdir():
        notes.append(Note.load_from(path=file))
    
    documents: list[str] = [note.full_text for note in notes]

    matches = retrieve(
        query=query,
        documents=documents,
        top_n=3,
    )

    matched_notes = [notes[match.index] for match in matches]
    yield NoteSummaryList(notes=matched_notes)
