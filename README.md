# SneakerCheckPriceBot

A Telegram bot that finds and compares sneaker prices across stores and delivers
the latest sneaker news — asynchronous, container-ready, and small enough to read
in one sitting.

[Русская версия](./README_RU.md)

![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED)
![License](https://img.shields.io/badge/license-MIT-green)
[![tests](https://github.com/Nikita-Pugach/SneakerCheckPriceBot/actions/workflows/tests.yml/badge.svg)](https://github.com/Nikita-Pugach/SneakerCheckPriceBot/actions/workflows/tests.yml)

## What it does

- **Price check** — searches several stores and shows matching offers with prices
  and links.
- **Guided search** — instead of one free-text prompt the bot walks the user
  through brand → model → size as a conversation (aiogram FSM), with a "show
  everything" shortcut at every step.
- **News** — the latest sneaker headlines for the last N hours, pulled from an
  RSS feed.
- **Subscription gate** — the bot checks that the user is subscribed to a channel
  before unlocking the menu.
- **Menu-driven UI** — inline keyboards, no commands to memorise beyond `/start`.

An "order sneakers" flow (a link to the partner store) is planned but not
implemented yet.

## Sources

| Store | How it is read |
|---|---|
| bunt.by | catalogue pages, then the product page for the price |
| sneakers.by | catalogue pages, then the product page for the price |
| kufar.by | its public JSON search API, prices come with the results |

Kufar is a classifieds board, so conditions and prices vary — it is there for
coverage, not as a shop. A new store is a module in `sneaker_bot/parsers/` with a
search function and a price extractor.

## How the search flow works

```
/start → subscription check → main menu
                                 │
                    ┌────────────┴────────────┐
                 Prices                     News
                    │                         │
        brand → model → size          last N hours
                    │                         │
             parse stores → offers      headlines
```

State machine: `aiogram.fsm`. Parsing: `aiohttp` + BeautifulSoup, one module per
store, so adding a store means adding one function and registering it.

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Bot framework | aiogram 3.x |
| HTTP / parsing | aiohttp, BeautifulSoup, lxml |
| News | feedparser |
| Config | python-dotenv |
| Packaging | Poetry |
| Runtime | Docker (python:3.12-slim) |

## Quick start

```bash
git clone https://github.com/Nikita-Pugach/SneakerCheckPriceBot.git
cd SneakerCheckPriceBot
poetry install
cp .env.template .env      # then fill in the values
poetry run python -m sneaker_bot.main
```

You need a bot token from [@BotFather](https://t.me/BotFather) and a channel the
bot can check subscriptions against.

## Configuration

Everything comes from `.env` (see [`.env.template`](./.env.template)):

| Variable | Purpose |
|---|---|
| `SECRET_TOKEN_BOT` | Telegram bot token |
| `ID_CHANNEL` | Channel used for the subscription check |
| `NEWS_URL` | RSS feed for the news section |
| `LAST_HOURS` | How far back to look for news |
| `MAX_PAGES`, `MAX_PAGES_BUNT`, `MAX_PAGES_SNEAK`, `PER_CAT` | How deep the parsers go |
| `USER_AGENT` | User-Agent header for HTTP requests |
| `SNEAKERS_WOMEN_URL`, `SNEAKERS_MEN_URL` | Store catalogue URLs |
| `BASE_URL`, `CATALOG_MEN_PATH`, `CATALOG_WOMEN_PATH` | Second store's catalogue |

Nothing secret is committed: `.env` is ignored, `.env.template` holds placeholders.

## Docker

```bash
docker build -t sneaker-bot .
docker run --rm --env-file .env sneaker-bot
```

The image installs dependencies from the lock file and starts
`python -m sneaker_bot.main`.

## Project layout

```
sneaker_bot/
├── handlers/     routers for commands and button callbacks
├── menu/         keyboards and menu texts
├── parsers/      price and news parsers
├── services/     message sending, text building, shared logic
├── setting.py    bot and dispatcher setup
├── startup.py    command registration
├── sub_checker.py subscription check
├── tasks.py      async task helpers
└── main.py       entry point
```

## FAQ

**The bot does not start.** Check `.env` — a missing `SECRET_TOKEN_BOT` is the
usual cause. Then confirm Python 3.12 and Poetry are installed.

**How do I add a store?** Add a parser function in `parsers/price_parser.py` and
call it from the search flow.

**How do I change menus or texts?** `menu/` for keyboards,
`services/send_messages.py` for messages.

## Authors

- [Kirill](https://github.com/Kirill-cmd-ops) — parsers, handlers, news, the
  original bot.
- [Nikita Pugach](https://github.com/Nikita-Pugach) — guided search flow (FSM),
  price parser fixes, configuration handling, packaging and docs.

## License

MIT. See [LICENSE](./LICENSE).
