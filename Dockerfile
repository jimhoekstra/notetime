FROM ghcr.io/astral-sh/uv:python3.13-trixie

ENV PYTHONUNBUFFERED=1

RUN useradd --create-home appuser

COPY --chown=appuser:appuser . /app

WORKDIR /app

USER appuser

RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["fastapi", "run", "notetime/app.py"]