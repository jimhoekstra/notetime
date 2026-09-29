from newsflash import NewsflashApp

from starlette.middleware.trustedhost import TrustedHostMiddleware

from notetime.pages import NoteEditorPage


app = NewsflashApp(pages=[NoteEditorPage])

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1"],
)
