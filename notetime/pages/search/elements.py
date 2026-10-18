from typing import Iterable

from newsflash.elements import Input, Vertical, Header, Paragraph, Link
from newsflash.models import Element

from notetime.models import Note


class SearchInput(Input):
    id: str = "search-input"
    placeholder: str = "search..."
    autofocus: bool = True


class NoteSummaryList(Vertical):
    id: str = "note-summary-list"
    notes: list[Note]

    def compose(self) -> Iterable[Element]:
        for note in self.notes:
            yield NoteSummary(
                id=note.note_id,
                note=note,
            )


class NoteSummary(Vertical):
    note: Note

    def compose(self) -> Iterable[Element]:
        yield Header(
            id=f"{self.id}-header",
            text=self.note.title,
            level=2,
            margin_bottom=False,
        )

        yield Paragraph(
            id=f"{self.id}-note",
            text=self.note.text,
        )

        yield Link(
            id=f"{self.id}-link",
            href=f"/?note-id={self.note.note_id}",
            text="Open Note",
        )
