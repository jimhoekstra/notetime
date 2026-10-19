from typing import Iterable

from newsflash import Page, FunctionRegistry
from newsflash.models import Element
from newsflash.elements import NotificationContainer

from notetime.elements.page_header import PageHeader
from notetime.models import Note
from notetime.constants import PATH_TO_NOTES

from .elements import SearchInput, NoteSummaryList
from .functions import function_registry


class SearchPage(Page):
    path: str = "/search"
    page_title: str = "notetime"
    function_registry: FunctionRegistry = function_registry

    def compose(self) -> Iterable[Element]:
        yield PageHeader()
        yield SearchInput()

        notes: list[Note] = []
        for file in PATH_TO_NOTES.iterdir():
            notes.append(Note.load_from(path=file))

        yield NoteSummaryList(notes=notes)
        yield NotificationContainer()
