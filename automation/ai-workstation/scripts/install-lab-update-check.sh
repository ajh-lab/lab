#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_script="${script_dir}/lab-update-check.sh"
target_script="${HOME}/.local/bin/lab-update-check"
systemd_user_dir="${HOME}/.config/systemd/user"

if [[ ! -f "$source_script" ]]; then
  echo "Source script not found: $source_script" >&2
  exit 1
fi

mkdir -p "${HOME}/.local/bin" "$systemd_user_dir" /mnt/ai/logs/system-updates
install -m 0755 "$source_script" "$target_script"

cat > "${systemd_user_dir}/lab-update-check.service" <<'UNIT'
[Unit]
Description=Lab workstation package update check
Documentation=file:/home/helios/lab/ai-baseline-context.md

[Service]
Type=oneshot
ExecStart=/home/helios/.local/bin/lab-update-check
UNIT

cat > "${systemd_user_dir}/lab-update-check.timer" <<'UNIT'
[Unit]
Description=Weekly lab workstation package update check

[Timer]
OnCalendar=Sat 09:00
RandomizedDelaySec=2h
Persistent=true
Unit=lab-update-check.service

[Install]
WantedBy=timers.target
UNIT

systemctl --user daemon-reload
systemctl --user enable --now lab-update-check.timer

if [[ "${1:-}" == "--run-now" ]]; then
  systemctl --user start lab-update-check.service
fi

systemctl --user list-timers lab-update-check.timer --no-pager
