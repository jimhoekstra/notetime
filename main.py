from newsflash import NewsflashApp
from starlette.middleware.trustedhost import TrustedHostMiddleware

from notetime.pages import NoteEditorPage, SearchPage


app = NewsflashApp(pages=[NoteEditorPage, SearchPage])

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"],
)
