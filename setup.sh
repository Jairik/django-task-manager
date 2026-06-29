#!/usr/bin/env bash
# Bootstrap local development: PostgreSQL, env file, dependencies, migrations.
# Supports Linux (systemd, OpenRC, SysV), macOS (Homebrew), and WSL.

set -euo pipefail

# Project root is the directory containing this script.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ROOT_DIR}/.env.testing"

# Default database name; overridden after .env.testing is loaded.
POSTGRES_DB="${POSTGRES_DB:-task_manager}"

# Populated by detect_platform().
OS_NAME=""
OS_TYPE=""       # linux | darwin | windows | unknown
DISTRO_ID=""     # e.g. arch, ubuntu, fedora (Linux only)
IS_WSL=false


# Print a clear error and stop when a required command is missing.
require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Error: '$1' is required but not installed." >&2
        exit 1
    fi
}


# Detect operating system and Linux distribution when available.
detect_platform() {
    OS_NAME="$(uname -s)"

    case "$OS_NAME" in
        Linux)
            OS_TYPE="linux"
            if [[ -f /proc/version ]] && grep -qi microsoft /proc/version; then
                IS_WSL=true
            fi
            if [[ -f /etc/os-release ]]; then
                # shellcheck disable=SC1091
                source /etc/os-release
                DISTRO_ID="${ID:-linux}"
            else
                DISTRO_ID="linux"
            fi
            ;;
        Darwin)
            OS_TYPE="darwin"
            DISTRO_ID="macos"
            ;;
        MINGW* | MSYS* | CYGWIN*)
            OS_TYPE="windows"
            DISTRO_ID="windows"
            ;;
        *)
            OS_TYPE="unknown"
            DISTRO_ID="unknown"
            ;;
    esac

    echo "Detected platform: ${OS_NAME} (${DISTRO_ID})"
}


# Run a command with sudo when available; otherwise run it directly.
try_sudo() {
    if [[ "$EUID" -eq 0 ]]; then
        "$@"
        return $?
    fi

    if command -v sudo >/dev/null 2>&1; then
        if sudo -n "$@" 2>/dev/null; then
            return 0
        fi
        if [[ -t 0 ]]; then
            sudo "$@"
            return $?
        fi
    fi

    return 1
}


# Print platform-specific PostgreSQL install/start instructions.
print_postgresql_help() {
    echo ""
    echo "Start PostgreSQL manually, then re-run this script."
    echo ""

    case "$OS_TYPE" in
        darwin)
            echo "macOS (Homebrew):"
            echo "  brew install postgresql@16"
            echo "  brew services start postgresql@16"
            echo "  brew services list"
            ;;
        linux)
            case "$DISTRO_ID" in
                arch | endeavouros | manjaro)
                    echo "Arch Linux:"
                    echo "  sudo pacman -S postgresql"
                    echo "  sudo -u postgres initdb -D /var/lib/postgres/data"
                    echo "  sudo systemctl enable --now postgresql"
                    ;;
                ubuntu | debian | pop | linuxmint)
                    echo "Debian / Ubuntu:"
                    echo "  sudo apt update && sudo apt install postgresql postgresql-contrib"
                    echo "  sudo systemctl enable --now postgresql"
                    echo "  # versioned clusters may use: sudo pg_ctlcluster 16 main start"
                    ;;
                fedora | rhel | centos | rocky | almalinux)
                    echo "Fedora / RHEL:"
                    echo "  sudo dnf install postgresql-server postgresql"
                    echo "  sudo postgresql-setup --initdb"
                    echo "  sudo systemctl enable --now postgresql"
                    ;;
                opensuse* | sles)
                    echo "openSUSE:"
                    echo "  sudo zypper install postgresql postgresql-server"
                    echo "  sudo systemctl enable --now postgresql"
                    ;;
                *)
                    echo "Linux (generic systemd):"
                    echo "  sudo systemctl start postgresql"
                    echo "  systemctl status postgresql"
                    ;;
            esac
            if [[ "$IS_WSL" == true ]]; then
                echo ""
                echo "WSL note: ensure the PostgreSQL service is running inside WSL,"
                echo "not only on the Windows host."
            fi
            ;;
        windows)
            echo "Windows:"
            echo "  Use WSL2 with a Linux distro and run this script inside WSL, or"
            echo "  install PostgreSQL for Windows and start the service from Services."
            ;;
        *)
            echo "Generic:"
            echo "  Start your local PostgreSQL server, then verify with:"
            echo "  pg_isready -h localhost -p 5432"
            ;;
    esac
}


# Return 0 when PostgreSQL accepts connections on the configured host/port.
postgresql_is_ready() {
    if ! command -v pg_isready >/dev/null 2>&1; then
        return 1
    fi

    pg_isready -h "${POSTGRES_HOST:-localhost}" -p "${POSTGRES_PORT:-5432}" >/dev/null 2>&1
}


# Wait up to ~20 seconds for PostgreSQL to become reachable.
wait_for_postgresql() {
    echo "Waiting for PostgreSQL to accept connections..."
    for _ in {1..20}; do
        if postgresql_is_ready; then
            echo "PostgreSQL is ready."
            return 0
        fi
        sleep 1
    done

    echo "Error: PostgreSQL is not accepting connections." >&2
    print_postgresql_help
    exit 1
}


# Return candidate systemd unit names for PostgreSQL on this machine.
postgresql_systemd_units() {
    local units=()

    if command -v systemctl >/dev/null 2>&1; then
        while IFS= read -r unit; do
            [[ -n "$unit" ]] && units+=("$unit")
        done < <(systemctl list-unit-files --type=service --no-pager 'postgresql*.service' 2>/dev/null \
            | awk 'NF && $2 != "masked" { print $1 }')

        # Prefer generic postgresql.service when present.
        if systemctl list-unit-files postgresql.service >/dev/null 2>&1; then
            units=("postgresql.service" "${units[@]}")
        fi
    fi

    # Deduplicate while preserving order.
    printf '%s\n' "${units[@]}" | awk '!seen[$0]++'
}


# Start PostgreSQL on macOS using Homebrew services.
start_postgresql_brew() {
    require_command brew

    local brew_service=""
    brew_service="$(brew services list 2>/dev/null | awk '/^postgresql@/ { print $1; exit }')"

    if [[ -z "$brew_service" ]]; then
        brew_service="postgresql"
    fi

    echo "Starting PostgreSQL via Homebrew ($brew_service)..."
    brew services start "$brew_service"
}


# Start PostgreSQL on Linux using systemd, OpenRC, or SysV init.
start_postgresql_linux() {
    local unit

    if command -v systemctl >/dev/null 2>&1; then
        while IFS= read -r unit; do
            [[ -z "$unit" ]] && continue
            echo "Trying systemd unit: $unit"
            if try_sudo systemctl start "$unit"; then
                wait_for_postgresql
                return 0
            fi
        done < <(postgresql_systemd_units)

        # Debian/Ubuntu versioned clusters sometimes need pg_ctlcluster.
        if command -v pg_ctlcluster >/dev/null 2>&1; then
            local version
            version="$(ls /etc/postgresql 2>/dev/null | sort -nr | head -1 || true)"
            if [[ -n "$version" ]]; then
                echo "Trying pg_ctlcluster ${version} main..."
                if try_sudo pg_ctlcluster "$version" main start; then
                    wait_for_postgresql
                    return 0
                fi
            fi
        fi
    fi

    if command -v rc-service >/dev/null 2>&1; then
        echo "Trying OpenRC service: postgresql"
        if try_sudo rc-service postgresql start; then
            wait_for_postgresql
            return 0
        fi
    fi

    if command -v service >/dev/null 2>&1; then
        echo "Trying SysV service: postgresql"
        if try_sudo service postgresql start; then
            wait_for_postgresql
            return 0
        fi
    fi

    return 1
}


# Start PostgreSQL using the best strategy for the current platform.
start_postgresql() {
    if postgresql_is_ready; then
        echo "PostgreSQL is already running."
        return 0
    fi

    echo "Starting PostgreSQL..."

    case "$OS_TYPE" in
        darwin)
            if start_postgresql_brew; then
                wait_for_postgresql
                return 0
            fi
            ;;
        linux)
            if start_postgresql_linux; then
                return 0
            fi
            ;;
        windows)
            echo "Error: Native Windows shells are not supported by this script." >&2
            print_postgresql_help
            exit 1
            ;;
    esac

    echo "Error: Could not start PostgreSQL automatically." >&2
    print_postgresql_help
    exit 1
}


# Verify the shared environment file exists before setup continues.
ensure_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "Error: $ENV_FILE not found." >&2
        exit 1
    fi

    echo "Using environment file: .env.testing"
}


# Load POSTGRES_* variables so setup steps and Django use the same settings.
load_env() {
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a

    # Re-export explicitly so child processes (uv run) always receive them.
    export POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD POSTGRES_HOST POSTGRES_PORT
}


# Pick the default psql database used for admin commands on this platform.
postgres_admin_db() {
    if [[ "$OS_TYPE" == "darwin" ]]; then
        # Homebrew installs often expose a postgres maintenance database.
        echo "postgres"
        return 0
    fi

    echo "postgres"
}


# Run a PostgreSQL admin command with the correct user for this platform.
run_as_postgres() {
    local admin_db
    admin_db="$(postgres_admin_db)"

    # Linux and most WSL installs use a dedicated postgres OS account.
    if [[ "$OS_TYPE" == "linux" ]] && id postgres >/dev/null 2>&1; then
        try_sudo -u postgres "$@" && return 0
    fi

    # macOS Homebrew typically runs PostgreSQL as the current user.
    if [[ "$OS_TYPE" == "darwin" ]]; then
        if id postgres >/dev/null 2>&1; then
            try_sudo -u postgres "$@" && return 0
        fi

        # Connect through the local maintenance database as the current user.
        if [[ "$1" == "psql" ]]; then
            psql -d "$admin_db" "${@:2}"
            return $?
        fi

        "$@"
        return $?
    fi

    # Last resort: run directly (may work when the current user is a superuser).
    if [[ "$1" == "psql" ]]; then
        psql -d "$admin_db" "${@:2}"
        return $?
    fi

    "$@"
}


# Ensure the configured role exists and has the password from .env.testing.
ensure_postgres_role() {
    local role_exists

    role_exists="$(run_as_postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'")"

    if [[ "$role_exists" != "1" ]]; then
        echo "Creating PostgreSQL role '${POSTGRES_USER}'..."
        if [[ "$OS_TYPE" == "darwin" ]] && ! id postgres >/dev/null 2>&1; then
            run_as_postgres psql -v ON_ERROR_STOP=1 -c \
                "CREATE USER \"${POSTGRES_USER}\" WITH SUPERUSER PASSWORD '${POSTGRES_PASSWORD}';"
        else
            run_as_postgres createuser -s "${POSTGRES_USER}"
            run_as_postgres psql -v ON_ERROR_STOP=1 -c \
                "ALTER USER \"${POSTGRES_USER}\" WITH PASSWORD '${POSTGRES_PASSWORD}';"
        fi
        return 0
    fi

    echo "Setting password for PostgreSQL role '${POSTGRES_USER}'..."
    run_as_postgres psql -v ON_ERROR_STOP=1 -c \
        "ALTER USER \"${POSTGRES_USER}\" WITH PASSWORD '${POSTGRES_PASSWORD}';"
}


# Create the application database owned by the configured role.
ensure_database() {
    local db_exists

    db_exists="$(run_as_postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'")"

    if [[ "$db_exists" == "1" ]]; then
        echo "Database '${POSTGRES_DB}' already exists."
        return 0
    fi

    echo "Creating database '${POSTGRES_DB}'..."
    if [[ "$OS_TYPE" == "darwin" ]] && ! id postgres >/dev/null 2>&1; then
        run_as_postgres psql -v ON_ERROR_STOP=1 -c \
            "CREATE DATABASE \"${POSTGRES_DB}\" OWNER \"${POSTGRES_USER}\";"
    else
        run_as_postgres createdb -O "${POSTGRES_USER}" "${POSTGRES_DB}"
    fi
}


# Install Python dependencies with uv when available, otherwise pip.
install_dependencies() {
    if command -v uv >/dev/null 2>&1; then
        echo "Installing dependencies with uv..."
        uv sync
        return 0
    fi

    echo "uv not found; falling back to pip + venv..."
    require_command python3

    if [[ ! -d "${ROOT_DIR}/.venv" ]]; then
        python3 -m venv "${ROOT_DIR}/.venv"
    fi

    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.venv/bin/activate"
    pip install -r requirements.txt
}


# Run Django migrations against the configured PostgreSQL database.
run_migrations() {
    echo "Running migrations..."

    if command -v uv >/dev/null 2>&1; then
        uv run python manage.py migrate
    else
        python3 manage.py migrate
    fi
}


main() {
    echo "=== django-task-manager setup ==="

    detect_platform
    ensure_env_file
    load_env
    start_postgresql
    ensure_postgres_role
    ensure_database
    install_dependencies
    run_migrations

    # Reload .env.testing at the end so exported vars are set for any follow-up
    # commands in the same script session (parent shell still needs to source it).
    echo ""
    echo "Loading environment from .env.testing..."
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
    export POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD POSTGRES_HOST POSTGRES_PORT

    echo ""
    echo "Setup complete. In your shell, load env and start the dev server:"
    if command -v uv >/dev/null 2>&1; then
        echo "  set -a && source .env.testing && set +a"
        echo "  uv run python manage.py runserver"
    else
        echo "  set -a && source .env.testing && set +a"
        echo "  source .venv/bin/activate && python manage.py runserver"
    fi
}


main "$@"
