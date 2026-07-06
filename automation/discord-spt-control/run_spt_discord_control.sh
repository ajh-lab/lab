#!/usr/bin/env bash
set -euo pipefail

set -a
if [[ -f "$HOME/.hermes/.env" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/.hermes/.env"
fi
if [[ -f "$HOME/.config/spt-discord-control/config.env" ]]; then
  # shellcheck disable=SC1090
  source "$HOME/.config/spt-discord-control/config.env"
fi
set +a

exec "$HOME/.local/share/lab/spt-discord-control/venv/bin/python" \
  "$HOME/.local/share/lab/spt-discord-control/spt_discord_control_bot.py"
