from typing import Self
from pathlib import Path

from pydantic import BaseModel


class Note(BaseModel):
    note_id: str
    title: str
    text: str
    full_text: str

    @classmethod
    def load_from(cls, path: Path) -> Self:
        full_text = path.read_text()
        lines = full_text.splitlines()

        if len(lines) >= 2 and lines[0] != "" and lines[1] == "":
            title = lines[0]
            text = "\n".join(lines[2:])
        else:
            title = "<no title>"
            text = full_text

        return cls(
            note_id=path.name.removesuffix(".md"),
            title=title,
            text=text,
            full_text=full_text,
        )
