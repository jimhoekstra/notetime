from pathlib import Path
from typing import Type

from newsflash import App, Page
from newsflash.widgets import TextArea, Input, Button, Notifications, Grid
from newsflash.widgets.widgets import Widget

from notetime.db import (
    get_db_connection,
    update_note,
    create_note,
    get_note_by_id,
    get_in_progress_note,
    get_all_notes,
)


def get_default_note_text() -> str:
    con, cur = get_db_connection()
    note = get_in_progress_note(cur)
    con.close()
    return note.text


class NoteSearchInput(Input):
    id: str = "note-search-input"
    placeholder: str = "search..."
    value: str = ""
    autofocus: bool = True


class NoteIDInput(Input):
    id: str = "note-id-input"
    type: str = "hidden"
    value: str = "1"


class NoteTextArea(TextArea):
    id: str = "note-textarea"
    rows: int = 15
    autofocus: bool = True
    placeholder: str = "write a new note..."

    def on_input(
        self,
        note_id_input: NoteIDInput,
    ) -> list[Widget]:
        assert self.value is not None

        con, cur = get_db_connection()
        note = get_note_by_id(cur, note_id=int(note_id_input.value))
        assert note is not None

        note.text = self.value
        update_note(con, cur, note)

        con.close()
        return []


class SaveButton(Button):
    id: str = "save-button"
    label: str = "Save"

    def on_click(
        self,
        notifications: Notifications,
        note_id_input: NoteIDInput,
        note_textarea: NoteTextArea,
    ) -> list[Widget]:
        note_id = int(note_id_input.value)
        con, cur = get_db_connection()

        assert note_textarea.value is not None

        if note_id == 1:
            buffer_note = get_in_progress_note(cur=cur)

            # Make sure the buffer note contains the current content
            # of the textarea element before saving
            assert note_textarea.value == buffer_note.text
            new_note = create_note(
                con=con,
                cur=cur,
                text=note_textarea.value,
            )

            buffer_note.text = ""
            update_note(con=con, cur=cur, note=buffer_note)

            notifications.push(f"Created new note with ID {new_note.id}")
        else:
            current_note = get_note_by_id(cur=cur, note_id=note_id)
            assert current_note is not None

            text = note_textarea.value
            title = text.splitlines()[0] if text else ""
            if len(text.splitlines()) > 1:
                text = "\n".join(text.splitlines()[1:])
            else:
                text = ""

            current_note.id = note_id
            current_note.title = title
            current_note.text = text
            current_note.set_updated_at_now()

            updated_note = update_note(
                con=con,
                cur=cur,
                note=current_note,
            )

            notifications.push(f"Updated note {updated_note.id}")

        con.close()

        # note_textarea.value = ""
        # note_id_input.value = "1"

        return [notifications]


class ClearButton(Button):
    id: str = "clear-button"
    label: str = "New"

    def on_click(
        self,
        note_id_input: NoteIDInput,
        note_textarea: NoteTextArea,
    ) -> list[Widget]:
        note_id_input.value = "1"
        note_textarea.value = ""

        con, cur = get_db_connection()
        note = get_in_progress_note(cur=cur)
        note.text = ""
        update_note(con=con, cur=cur, note=note)

        con.close()
        return [note_id_input, note_textarea]


class EditNoteButton(Button):
    id: str = "edit-note-button"
    label: str = "Edit"
    classes: list[str] = ["edit-note-button"]

    def on_click(
        self,
        note_textarea: NoteTextArea,
        note_id_input: NoteIDInput,
    ) -> list[Widget]:
        note_id = self.id.replace("edit-note-", "").replace("-button", "")

        con, cur = get_db_connection()
        note = get_note_by_id(cur=cur, note_id=int(note_id))
        con.close()

        if note is not None:
            note_textarea.value = note.text
            note_id_input.value = str(note.id)

            return [note_textarea, note_id_input]
        else:
            return []


class NoteWidget(Widget):
    template: tuple[str, str] = ("templates", "note_widget.html")
    title: str = ""
    text: str = ""
    updated_at: str = ""
    created_at: str = ""

    include_in_context: set[str] = {
        "id",
        "title",
        "text",
        "hx_include",
        "hx_swap_oob",
        "updated_at",
        "created_at",
    }

    def _post_init(self) -> None:
        self.children = [
            EditNoteButton(
                id=f"edit-note-{self.id}-button",
            )
        ]
        return super()._post_init()


class NoteGrid(Grid[NoteWidget]):
    id: str = "note-grid"
    num_columns: int = 2
    item_type: Type[NoteWidget] = NoteWidget

    def _post_init(self) -> None:
        con, cur = get_db_connection()
        all_notes = get_all_notes(cur=cur)
        con.close()

        self.items = [
            NoteWidget(
                id=str(note.id),
                title=note.title,
                text=note.text,
                updated_at=note.updated_at.strftime("%Y-%m-%d %H:%M"),
                created_at=note.created_at.strftime("%Y-%m-%d %H:%M"),
            )
            for note in all_notes
        ]
        return super()._post_init()


class NewNotePage(Page):
    id: str = "new-note-page"
    path: str = "/"
    title: str = "NoteTime"
    template: tuple[str, str] = ("templates", "new_note.html")
    children: list[Widget] = []
    note_id: int = 1

    def _post_init(self) -> None:
        con, cur = get_db_connection()
        note = get_note_by_id(cur=cur, note_id=self.note_id)
        assert note is not None
        con.close()

        self.children = [
            NoteIDInput(value=str(self.note_id)),
            NoteTextArea(value=note.get_full_text()),
            SaveButton(),
            ClearButton(),
        ]
        return super()._post_init()


note_overview_page = Page(
    id="note-overview-page",
    path="/notes",
    title="Note Overview",
    template=("templates", "note_overview.html"),
    children=[
        NoteSearchInput(),
        NoteGrid(),
    ],
)

app = App(
    pages=[NewNotePage(), note_overview_page],
    template_folders=[("templates", Path.cwd() / "notetime" / "templates")],
)
