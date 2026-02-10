from pathlib import Path
from typing import Type

from newsflash import App, Page
from newsflash.widgets import (
    TextArea,
    Input,
    Button,
    Notifications,
    List,
    Grid,
    BarChart,
    Paragraph,
)
from newsflash.widgets.widgets import Widget

from notetime.db import (
    get_db_connection,
    update_note,
    create_note,
    get_note_by_id,
    get_in_progress_note,
    get_all_notes,
    get_all_tags,
    get_notes_by_tags,
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
    rows: int = 18
    autofocus: bool = True
    placeholder: str = "write a new note..."

    def on_input(
        self,
        note_id_input: NoteIDInput,
        note_description: "NoteDescription",
    ) -> list[Widget]:
        assert self.value is not None
        note_id = int(note_id_input.value)

        con, cur = get_db_connection()
        current_note = get_note_by_id(cur, note_id=note_id)
        assert current_note is not None

        text = self.value
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

        con.close()
        note_description.text = f"Editing note: {current_note.title} (id: {current_note.id}). Last updated at {updated_note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}."

        if note_id == 1:
            return []
        else:
            return [note_description]


class SaveButton(Button):
    id: str = "save-button"
    label: str = "Create Note"

    def on_click(
        self,
        notifications: Notifications,
        note_id_input: NoteIDInput,
        note_textarea: NoteTextArea,
    ) -> list[Widget]:
        note_id = int(note_id_input.value)
        con, cur = get_db_connection()

        assert note_textarea.value is not None

        assert note_id == 1
        buffer_note = get_in_progress_note(cur=cur)

        # Make sure the buffer note contains the current content
        # of the textarea element before saving
        assert note_textarea.value == buffer_note.get_full_text()
        new_note = create_note(
            con=con,
            cur=cur,
            text=note_textarea.value,
        )

        buffer_note.title = ""
        buffer_note.text = ""
        update_note(con=con, cur=cur, note=buffer_note)

        notifications.push(f"Created new note with ID {new_note.id}")

        con.close()

        return [notifications]


class ClearButton(Button):
    id: str = "clear-button"
    label: str = "New"

    def on_click(
        self,
        note_id_input: NoteIDInput,
        note_textarea: NoteTextArea,
        note_description: "NoteDescription",
        create_note: SaveButton,
    ) -> list[Widget]:
        note_id_input.value = "1"
        note_textarea.value = ""
        note_description.text = "Creating a new note. Press save to create."
        create_note.disabled = False

        con, cur = get_db_connection()
        note = get_in_progress_note(cur=cur)
        note.title = ""
        note.text = ""
        update_note(con=con, cur=cur, note=note)

        con.close()
        return [note_id_input, note_textarea, note_description, create_note]


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
        current_tags: list[str] = self.root_widget.query_params.get("tag", [])

        con, cur = get_db_connection()
        if len(current_tags) > 0:
            all_notes = get_notes_by_tags(cur=cur, tag_names=current_tags)
        else:
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


class NoteDescription(Paragraph):
    id: str = "note-description"
    text: str = ""


class TagButton(Widget):
    template: tuple[str, str] = ("templates", "tag_widget.html")
    id: str = "tag-button"
    label: str = "Tag"
    num_notes: int = 0
    url: str = "/notes"
    active: bool

    include_in_context: set[str] = {"id", "label", "num_notes", "url", "active"}


class TagList(List[TagButton]):
    id: str = "tag-list"
    item_type: Type[TagButton] = TagButton

    def _post_init(self) -> None:
        super()._post_init()

        current_tags: list[str] = self.root_widget.query_params.get("tag", [])

        def get_new_tag_list(tag_name: str) -> list[str]:
            if tag_name in current_tags:
                return [t for t in current_tags if t != tag_name]
            else:
                return current_tags + [tag_name]

        def get_new_url(tag_name: str) -> str:
            new_tags = get_new_tag_list(tag_name)
            if len(new_tags) > 0:
                return f"/notes?{'&'.join([f'tag={t}' for t in new_tags])}"
            else:
                return "/notes"

        con, cur = get_db_connection()
        all_tags = get_all_tags(cur=cur)
        con.close()

        self.items = [
            TagButton(
                id=f"tag-{tag.name}-button",
                label=tag.name,
                num_notes=tag.num_notes,
                url=get_new_url(tag.name),
                active=tag.name in current_tags,
            )
            for tag in all_tags
        ]


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

        if self.note_id == 1:
            note_description: str = "Creating a new note. Press save to create."
        else:
            note_description: str = f"Editing note: {note.title} (id: {note.id}). Updates are saved automatically."

        self.children = [
            NoteIDInput(value=str(self.note_id)),
            NoteDescription(text=note_description),
            NoteTextArea(value=note.get_full_text()),
            SaveButton(disabled=note.id != 1),
            ClearButton(),
        ]
        return super()._post_init()


class NoteOverviewPage(Page):
    id: str = "note-overview-page"
    path: str = "/notes"
    title: str = "Note Overview"
    template: tuple[str, str] = ("templates", "note_overview.html")

    def _post_init(self) -> None:
        self.children = [
            NoteSearchInput(parent=self),
            NoteGrid(parent=self),
            TagList(parent=self),
        ]
        return super()._post_init()


class TestBar(BarChart):
    id: str = "test-bar-chart"
    title: str = "Test Bar Chart"

    def on_load(self) -> list[Widget]:
        # TODO: Replace with real data
        self.set_values(
            labels=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
            values=[10, 20, 15, 25, 5, 30, 12, 18, 22, 8],
        )
        return [self]


stats_page = Page(
    id="stats-page",
    path="/stats",
    title="Stats",
    template=("templates", "stats.html"),
    children=[
        TestBar(),
    ],
)

app = App(
    pages=[NewNotePage(), NoteOverviewPage(), stats_page],
    template_folders=[("templates", Path.cwd() / "notetime" / "templates")],
)
