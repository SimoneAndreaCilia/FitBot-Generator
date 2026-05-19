# WOD — Workout of the Day Telegram Bot

Generatore di schede di allenamento personalizzate accessibile tramite Telegram Bot.

## Quick Start

```bash
# 1. Clone & create virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS / Linux

# 2. Install dependencies (including dev tools)
pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env
# Edit .env and set TELEGRAM_BOT_TOKEN

# 4. Run database migrations
alembic upgrade head

# 5. Start the bot
wod-bot
```

## Development

```bash
# Run tests with coverage
pytest

# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
pylint src/wod/
mypy src/wod/
```

## Architecture

| Layer | Path | Purpose |
|-------|------|---------|
| **Core** | `src/wod/core/` | Domain logic — filtering, split generation, intensity |
| **DB** | `src/wod/db/` | SQLAlchemy models & repositories |
| **Bot** | `src/wod/bot/` | Telegram interface — handlers & keyboards |

See the [implementation plan](docs/implementation_plan.md) for full details.

## License

MIT
