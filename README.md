# Django Task Manager (aka Ultra Super Project Task Manager+)

A single-user task management web app built with Django and PostgreSQL. Create projects, add tasks, track status and due dates, and search or filter lists from the browser.

## Features

- **Projects** — create, edit, and delete with name, description, priority, due date, and up to three tags
- **Tasks** — create, edit, and delete within a project; advance status (to do → in progress → done) or revert done tasks back to to do
- **Home page** — project grid with progress bars, soonest open-task due date, fuzzy search (`?q=`), and toolbar filters (due date, priority) and sort options
- **Project detail** — tasks grouped by status with overdue highlighting, fuzzy search, and toolbar filters/sort
- **Light/dark theme** — persisted in the browser; respects system preference on first visit

No login or user accounts — the app assumes one local user, per the take-home requirements.

## Tech stack

Python 3.14+, Django 5.2, PostgreSQL (`psycopg` 3), server-rendered Django templates, Tailwind CSS via the Play CDN, and pytest for automated tests. See [docs/stack.md](docs/stack.md) for the full breakdown and rationale.

## Documentation


| Document                                                 | Contents                                           |
| -------------------------------------------------------- | -------------------------------------------------- |
| [docs/stack.md](docs/stack.md)                           | Technologies used and how they fit together        |
| [docs/schema.md](docs/schema.md)                         | Database tables, indexes, and Django model mapping |
| [docs/objectives.md](docs/objectives.md)                 | Original requirements                              |
| [docs/futureImprovements.md](docs/futureImprovements.md) | What would change with more time or at scale       |


## Prerequisites

- **PostgreSQL** installed locally
- **Python 3.14+** (see `.python-version`)
- **uv** ([recommended](https://docs.astral.sh/uv/)) or **pip** + **venv**

Supported platforms: **Linux** (Arch, Debian/Ubuntu, Fedora/RHEL, openSUSE, WSL), **macOS** (Homebrew). Native Windows shells are not supported - use WSL.

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

Run the app and PostgreSQL with Docker Compose. Migrations run on startup; the web service binds `runserver` to `0.0.0.0:8000`.

### Prerequisites (Arch Linux)

```bash
sudo pacman -S docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

After `usermod`, **log out and back in** (or run `newgrp docker`) so your shell picks up the `docker` group. Without that step you will see:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

### Start the stack

```bash
docker compose up --build
```

If your session has not refreshed group membership yet, use the project wrapper (it runs compose via `sg docker` when needed):

```bash
chmod +x scripts/docker-compose.sh   # first time only
./scripts/docker-compose.sh up --build
```

Open [http://localhost:8000/](http://localhost:8000/)

Stop the stack with `docker compose down` (or `./scripts/docker-compose.sh down`).

Compose sets `POSTGRES_HOST=db` for the web container (do not use `.env.testing` as-is inside Compose — that file points at `localhost`). Automated tests are still intended to run on the host:

```bash
set -a && source .env.testing && set +a
uv run pytest
```

## Running tests

145 automated tests cover views, queries, filters, and UI helpers.

```bash
set -a && source .env.testing && set +a
uv run pytest
```

## PostgreSQL service (by platform)

The setup script tries to start PostgreSQL automatically. If it cannot, use the commands for your platform below.

### Arch Linux

```bash
sudo pacman -S postgresql
sudo -u postgres initdb -D /var/lib/postgres/data
sudo systemctl enable --now postgresql
```

### Debian / Ubuntu

```bash
sudo apt update && sudo apt install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
# versioned installs may also use: sudo pg_ctlcluster 16 main start
```

### Fedora / RHEL

```bash
sudo dnf install postgresql-server postgresql
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

### macOS (Homebrew)

```bash
brew install postgresql@16
brew services start postgresql@16
```

### WSL

Run PostgreSQL inside your WSL distro (same commands as your Linux distro above). Verify with:

```bash
pg_isready -h localhost -p 5432
```

## Manual database setup

If you prefer not to use the setup script, create the database yourself:

```bash
createdb task_manager
```

Export the variables from `.env.testing` before running Django commands:

```bash
set -a && source .env.testing && set +a
```

## Option A: uv (recommended)

[uv](https://docs.astral.sh/uv/) reads `pyproject.toml` and `uv.lock` for reproducible installs.

```bash
uv sync                                              # create .venv and install locked dependencies
set -a && source .env.testing && set +a              # load PostgreSQL credentials
uv run python manage.py migrate                      # apply migrations to PostgreSQL
uv run python manage.py runserver                    # start the dev server
```

To add or update a dependency later:

```bash
uv add <package>    # updates pyproject.toml and uv.lock
uv sync             # reinstall from the lock file
```

## Option B: pip + venv

Use this if you prefer a standard virtual environment without uv.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt                        # Django + psycopg PostgreSQL adapter
set -a && source .env.testing && set +a                # load PostgreSQL credentials
python manage.py migrate                             # apply migrations to PostgreSQL
python manage.py runserver                             # start the dev server
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