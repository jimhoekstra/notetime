init:
    uv run main.py

dev:
    uv run fastapi dev notetime/app.py

test:
    uv run python -m unittest

format:
    uv run ruff format . && uv run ruff check --fix .