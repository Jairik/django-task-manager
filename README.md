# Django Task Manager (aka Ultra Super Project Task Manager+)

A single-user task management web app built with Django and PostgreSQL. Create projects, add tasks, track status and due dates, and search or filter lists from the browser.

## Features

- **Projects** — create, edit, and delete with name, description, priority, due date, and up to three tags
- **Tasks** — create, edit, and delete within a project; advance status (to do → in progress → done) or revert done tasks back to to do
- **Home page** — project grid with progress bars, soonest open-task due date, fuzzy search (`?q=`), and toolbar filters (due date, priority) and sort options
- **Project detail** — tasks grouped by status with overdue highlighting, fuzzy search, and toolbar filters/sort
- **Light/dark theme** — persisted in the browser; respects system preference on first visit

No login or user accounts for now - the app assumes one local user.

## Prerequisites

PostgreSQL, Python 3.14+, and **uv** (or pip + venv). The setup script supports Linux (Arch, Debian/Ubuntu, Fedora/RHEL, openSUSE, WSL) and macOS (Homebrew).

For manual installs, Docker setup, per-platform PostgreSQL commands, and pip/uv workflows, see [docs/prerequisites.md](docs/prerequisites.md).

## Quick setup (recommended)

Run the setup script from the project root. It detects your platform, starts PostgreSQL, creates the database role, installs dependencies, and runs migrations.

**Linux/WSL** may require `sudo` to start PostgreSQL and run admin commands as the `postgres` OS user. **macOS (Homebrew)** typically does not.

```bash
chmod +x setup.sh   # first time only
./setup.sh
```

Then load your env and start the server:

```bash
set -a && source .env.testing && set +a
uv run python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Docker (development)

Run the app and PostgreSQL with Docker Compose:

```bash
docker compose up --build
```

Open [http://localhost:8000/](http://localhost:8000/). Stop the stack with `docker compose down`.

If Docker is not installed or you hit permission errors on the Docker socket, see [docs/prerequisites.md](docs/prerequisites.md#docker-development).

Automated tests are still intended to run on the host, as seen below.

## Running tests

146 automated tests cover views, queries, filters, and UI helpers.

```bash
set -a && source .env.testing && set +a
uv run pytest
```

## Project layout

```
config/          Django project settings and root URLs
tasks/           Main app — models, views, forms, queries, templates
tests/           Pytest suite
docs/            Schema, stack, and design notes for reviewers
static/          Shared CSS and client-side toolbar scripts
```

Each major subdirectory has a short `README.md` describing its role.

## Tech stack

Python 3.14+, Django 5.2, PostgreSQL (`psycopg` 3), server-rendered Django templates, Tailwind CSS via the Play CDN, and pytest for automated tests. See [docs/stack.md](docs/stack.md) for the full breakdown and rationale.

## Documentation


| Document                                                 | Contents                                           |
| -------------------------------------------------------- | -------------------------------------------------- |
| [docs/stack.md](docs/stack.md)                           | Technologies used and how they fit together        |
| [docs/schema.md](docs/schema.md)                         | Database tables, indexes, and Django model mapping |
| [docs/objectives.md](docs/objectives.md)                 | Original requirements                              |
| [docs/futureImprovements.md](docs/futureImprovements.md) | What would change with more time or at scale       |
| [docs/prerequisites.md](docs/prerequisites.md)           | Manual setup, Docker, and per-platform PostgreSQL  |


