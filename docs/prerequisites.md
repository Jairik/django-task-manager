# Prerequisites and manual setup

The [setup script](../setup.sh) handles PostgreSQL, the database role, dependencies, and migrations on most supported platforms. Use this guide when you need to install or troubleshoot prerequisites yourself, or when you prefer not to use the setup script.

## Runtime requirements

- **PostgreSQL** installed locally (or via Docker Compose for containerized development)
- **Python 3.14+** (see `.python-version`)
- **uv** ([recommended](https://docs.astral.sh/uv/)) or **pip** + **venv**

Supported platforms: **Linux** (Arch, Debian/Ubuntu, Fedora/RHEL, openSUSE, WSL), **macOS** (Homebrew). Native Windows shells are not supported — use WSL.

## Docker (development)

Docker Compose runs the app and PostgreSQL together. Migrations run on startup; the web service binds `runserver` to `0.0.0.0:8000`.

### Install Docker (Arch Linux)

```bash
sudo pacman -S docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

After `usermod`, **log out and back in** (or run `newgrp docker`) so your shell picks up the `docker` group. Without that step you will see:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

If your session has not refreshed group membership yet, use the project wrapper (it runs compose via `sg docker` when needed):

```bash
chmod +x scripts/docker-compose.sh   # first time only
./scripts/docker-compose.sh up --build
```

Compose sets `POSTGRES_HOST=db` for the web container (do not use `.env.testing` as-is inside Compose — that file points at `localhost`).

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
