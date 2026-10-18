from typing import Iterable

from newsflash.elements import Header, Link, Vertical, Horizontal
from newsflash.models import Element


class PageHeader(Vertical):
    id: str = "page-header-and-nav"

    def compose(self) -> Iterable[Element]:
        yield Header(id="page-header", text="NoteTime")

        yield Horizontal(
            id="navbar",
            children=[
                Link(id="new-note-link", href="/", text="New"),
                Link(id="search-note-link", href="/search", text="Search"),
            ]
        )
