FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Dependencies first, so the layer survives source changes.
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip poetry \
    && poetry install --no-root --no-ansi

COPY sneaker_bot ./sneaker_bot

# The bot reads its configuration from the environment (see .env.template):
#   SECRET_TOKEN_BOT, ID_CHANNEL, NEWS_URL, MAX_PAGES, ...
CMD ["python", "-m", "sneaker_bot.main"]
