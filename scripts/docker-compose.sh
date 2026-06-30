#!/usr/bin/env bash
# Run docker compose with correct permissions on Linux after `usermod -aG docker`.
# Current shells do not pick up new groups until you log out/in or run `newgrp docker`.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Docker API is reachable in this shell — run compose directly.
if docker info >/dev/null 2>&1; then
    exec docker compose "$@"
fi

# User is in the docker group but this session was started before usermod took effect.
if getent group docker | grep -qw "$USER"; then
    echo "Note: docker group not active in this shell. Using sg docker (or run: newgrp docker)." >&2
    exec sg docker -c "cd $(printf '%q' "$ROOT_DIR") && docker compose $(printf '%q ' "$@")"
fi

echo "Cannot access Docker (permission denied on /var/run/docker.sock)." >&2
echo "" >&2
echo "Install and start Docker, then add your user to the docker group:" >&2
echo "  sudo pacman -S docker docker-compose" >&2
echo "  sudo systemctl enable --now docker" >&2
echo "  sudo usermod -aG docker \$USER" >&2
echo "" >&2
echo "Log out and back in, or run: newgrp docker" >&2
exit 1
