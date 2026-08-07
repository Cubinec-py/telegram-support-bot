# 🤖 Telegram Support Bot

A Telegram-based support desk: players open tickets, managers claim and answer them from a manager panel inside the same bot. Built with aiogram 3, PostgreSQL, Redis and SQLAlchemy (async), running fully in Docker.

## ✨ Features

### For users
- 🌍 **Multi-language**: Russian, English, Spanish, Ukrainian
- 🎫 **Ticket system**: auto-numbered tickets (`TKT-000001`, ...) with a limit on active tickets per user
- 💬 **Conversation history**: every message on both sides is stored against the ticket
- 📊 **Status tracking**: Open → In progress → Waiting for user → Closed
- ✅ **Delivery confirmation**: every message you send gets an acknowledgment, so it's never unclear whether it went through
- 📱 **Simple UI**: everything driven by reply-keyboard buttons, no need to remember commands

### For managers
- 📋 **Shared unassigned queue**: new tickets are *not* auto-assigned — they land in a shared "new tickets" list and any manager claims one manually via "Take" (avoids one manager silently getting all the load)
- 🔔 **Broadcast notifications**: every admin in `ADMIN_IDS` is notified when a new ticket comes in, in their own configured language
- 💬 **Reply flow**: claim a ticket, reply inline, close it when resolved
- ⏱️ **Auto-close**: tickets with no new message for `AUTO_CLOSE_TIMEOUT` minutes are closed automatically (based on actual last activity, not just any status change)
- 🌐 **Localized panel**: the manager panel and notifications are shown in the manager's own language, not hardcoded

### Reliability
- 🔒 **Per-user update serialization**: a Redis lock ensures a single user's updates are processed strictly one at a time, so spamming messages can't race the FSM state and create duplicate tickets
- 🚦 **Rate limiting**: a per-user Redis-backed limiter drops excess updates before they even reach the lock/handler
- 🧹 **No lost messages**: if a ticket gets closed mid-conversation (by the user or a manager), the next message is redirected to another active ticket or the user is told to open a new one — it's never silently attached to a dead ticket

## 🛠 Tech stack

- **Python 3.11**
- **aiogram 3.3** — async Telegram Bot API framework
- **PostgreSQL 16**
- **Redis 7** — FSM storage, rate limiting, per-user locking
- **SQLAlchemy 2.0** (async) — ORM
- **Alembic** — database migrations
- **Docker & Docker Compose** — containerization

There is no task scheduler library — ticket auto-close runs as a plain `asyncio` loop inside the bot process (`bot/utils/scheduler.py`), not APScheduler or Celery.

## 📋 Requirements

- Docker (20.10+)
- Docker Compose v2 (the `docker compose` plugin, not the standalone `docker-compose` binary)
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

## 🚀 Quick start

### 1. Clone the repository

```bash
git clone <repository-url>
cd telegram-support-bot
```

### 2. Create a Telegram bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` and follow the prompts to get a **Bot Token**
3. Get your own Telegram ID from [@userinfobot](https://t.me/userinfobot)

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in at least:

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz   # from BotFather
ADMIN_IDS=123456789,987654321                     # manager Telegram IDs, comma-separated
POSTGRES_PASSWORD=<a real password>                # don't leave the placeholder
```

Everything else has a sane default — see the [Configuration](#️-configuration) section below.

### 4. Start the stack

```bash
docker compose up -d --build
```

This builds and starts `postgres`, `redis` and `bot`. On startup, the `bot` container automatically runs `alembic upgrade head` before starting the bot — there's no separate manual migration step.

### 5. Done 🎉

Find your bot in Telegram and send `/start`.

## 📱 Using the bot

### As a user

1. Send `/start`, pick a language
2. **📝 Create ticket** → describe your problem in the next message
3. You'll get a confirmation with the ticket number; keep typing in the same chat to add more messages to it — each one is acknowledged
4. A manager will reply once they've claimed the ticket; you'll be notified
5. The ticket auto-closes after `AUTO_CLOSE_TIMEOUT` minutes of inactivity once a manager has replied and is waiting on you

Main menu buttons:
- **📝 Create ticket**
- **📋 My tickets** — your active tickets and their status
- **🌐 Change language**

### As a manager

1. Add your Telegram ID to `ADMIN_IDS` in `.env` and restart the bot (`docker compose restart bot`)
2. Use `/manager` or the **👨‍💼 Manager Panel** button
3. New tickets show up for *every* admin as a notification — open **🆕 New tickets** and tap one to claim it ("Take")
4. Once claimed, reply from the ticket view; the user gets notified
5. Close the ticket when resolved

Manager panel:
- **📋 My tickets** — tickets currently assigned to you
- **🆕 New tickets** — unclaimed tickets waiting in the shared queue
- **📊 Statistics** — basic count of your active tickets

## 📁 Project structure

```
telegram-support-bot/
├── main.py                        # Entry point: wires up bot, DB, Redis, middleware, scheduler
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── .env.example
│
├── bot/
│   ├── config.py                  # Pydantic settings, read from .env
│   │
│   ├── database/
│   │   ├── database.py            # Engine/session factory, init_db()
│   │   ├── models.py              # SQLAlchemy models: User, Manager, Ticket, Message
│   │   └── repositories.py        # Data access layer (row-locking for concurrency safety)
│   │
│   ├── handlers/
│   │   ├── user_handlers.py       # User-facing flow + manager reply-keyboard buttons
│   │   └── manager_handlers.py    # Manager panel callbacks (claim/reply/close)
│   │
│   ├── keyboards/keyboards.py     # Keyboard builders
│   │
│   ├── locales/                   # ru.json / en.json / es.json / uk.json
│   │
│   ├── middlewares/
│   │   ├── db_middleware.py           # Injects a DB session per update
│   │   ├── rate_limit_middleware.py   # Drops updates over the per-user rate limit
│   │   └── user_lock_middleware.py    # Serializes per-user update processing
│   │
│   ├── states/states.py           # FSM states
│   │
│   └── utils/
│       ├── i18n.py                # Translation lookup
│       ├── language.py            # Resolve a Telegram user's saved language
│       ├── notifications.py       # Outbound notifications (handles blocked-bot errors)
│       └── scheduler.py           # Auto-close loop
│
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 001_initial_migration.py
│       └── 002_ticket_activity_tracking.py
│
└── logs/                          # Mounted into the container, created automatically
```

## 🗄️ Database

**users**
| column | type | notes |
|---|---|---|
| id | BigInteger PK | internal id |
| telegram_id | BigInteger, unique | |
| username, first_name, last_name | String, nullable | |
| language | enum (ru/en/es/uk) | |
| created_at, updated_at | DateTime | |

**managers**
| column | type | notes |
|---|---|---|
| id | BigInteger PK | internal id |
| telegram_id | BigInteger, unique | |
| username | String, nullable | |
| first_name | String | |
| status | enum (online/offline/busy) | not currently surfaced in the UI |
| is_active | Boolean | |
| created_at, updated_at | DateTime | |

**tickets**
| column | type | notes |
|---|---|---|
| id | BigInteger PK | |
| ticket_number | String, unique | `TKT-000001` style |
| user_id | FK → users | |
| manager_id | FK → managers, nullable | null until claimed |
| status | enum (open/in_progress/waiting_user/closed) | |
| subject | String, nullable | first message, truncated |
| created_at, updated_at | DateTime | |
| last_activity_at | DateTime | bumped only on new messages — what auto-close actually checks |
| closed_at | DateTime, nullable | |

**messages**
| column | type | notes |
|---|---|---|
| id | BigInteger PK | |
| ticket_id | FK → tickets | |
| user_id | FK → users, nullable | set if the message is from the user |
| manager_id | FK → managers, nullable | set if the message is from a manager |
| message_text | Text | |
| created_at | DateTime | |

`is_from_user` is not a stored column — it's a Python property (`user_id is not None`) derived from which FK is set.

## ⚙️ Configuration

All variables are documented in `.env.example`. Summary:

**Required:**
| variable | description |
|---|---|
| `BOT_TOKEN` | Telegram bot token |
| `ADMIN_IDS` | comma-separated Telegram IDs with manager access |
| `POSTGRES_PASSWORD` | Postgres password |

**Optional (defaults shown):**
| variable | default | description |
|---|---|---|
| `DEFAULT_LANGUAGE` | `ru` | default language for new users |
| `SUPPORTED_LANGUAGES` | `ru,en,es,uk` | comma-separated language codes enabled in the UI |
| `MAX_ACTIVE_TICKETS_PER_USER` | `3` | ticket-creation limit per user |
| `AUTO_CLOSE_TIMEOUT` | `60` | minutes of inactivity before auto-close |
| `LOG_LEVEL` | `INFO` | Python logging level |

### Adding a new language

1. Create `bot/locales/<code>.json`, copying the key structure from an existing file (e.g. `en.json`)
2. Translate every value
3. Add `<code>` to `SUPPORTED_LANGUAGES` in `.env`
4. Restart the bot

## 🔧 Operating the stack

```bash
docker compose up -d              # start everything
docker compose down               # stop everything (keeps volumes/data)
docker compose down -v            # stop and WIPE all data (postgres/redis volumes)
docker compose restart bot        # restart just the bot
docker compose up -d --build bot  # rebuild the bot image and restart it (after a code change)
docker compose logs -f bot        # follow bot logs
docker compose ps                 # container status
```

### Database / migrations

Migrations run automatically on container start (`alembic upgrade head` in the Dockerfile `CMD`). To run Alembic manually:

```bash
docker compose exec bot alembic current                              # current DB revision
docker compose exec bot alembic upgrade head                         # apply pending migrations
docker compose exec bot alembic revision --autogenerate -m "message" # generate a new migration from model changes
```

Always review autogenerated migrations before committing them — Alembic doesn't reliably detect every kind of change.

### Backups

```bash
docker compose exec postgres pg_dump -U postgres support_bot > backup_$(date +%Y%m%d_%H%M%S).sql
docker compose exec -T postgres psql -U postgres support_bot < backup_20260101_120000.sql
```

## 🔍 Troubleshooting

**Bot doesn't start**
```bash
docker compose logs bot
docker compose ps
docker compose up -d --build bot
```

**DB connection / migration errors**
```bash
docker compose exec postgres pg_isready -U postgres
docker compose exec bot alembic current
```
If the schema is genuinely broken beyond repair in a throwaway environment: `docker compose down -v && docker compose up -d --build` (this deletes all data — never run this against a real database).

**Bot doesn't respond to anything**
```bash
docker compose logs -f bot   # look for a traceback — an unhandled exception in a handler
                              # is logged here but the user just sees silence
```

**FSM / Redis weirdness (user stuck in a broken flow)**
```bash
docker compose exec redis redis-cli ping
docker compose exec redis redis-cli FLUSHALL   # wipes ALL FSM state for ALL users, last resort
```

## 🔐 Security notes

- `postgres` and `redis` do **not** publish their ports to the host by default — they're only reachable from `bot` over the internal Compose network. Don't add `ports:` for them unless you have a specific reason to reach them from outside Docker (and then restrict the source with a firewall).
- Never commit `.env` — it holds the bot token and DB password. It's already gitignored.
- Migrations under `alembic/versions/` **are** tracked in git — that's intentional, don't add them back to `.gitignore`.
- `pgAdmin` is present but commented out in `docker-compose.yml`. If you re-enable it, put it behind a reverse proxy with auth/TLS rather than exposing port 5050 directly, and don't reuse the Postgres password for its own login.

## 🚀 Deploying

There's no separate prod compose file — the same `docker-compose.yml` is used everywhere, with a `.env` that lives only on the target machine (never committed).

```bash
# on the server, first time:
git clone <repository-url> /opt/telegram-support-bot
cd /opt/telegram-support-bot
cp .env.example .env   # then fill in real values
docker compose up -d --build

# subsequent deploys:
git pull
docker compose up -d --build bot
```
