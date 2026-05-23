#!/usr/bin/env bash
set -u

log_dir="/mnt/ai/logs/system-updates"
mkdir -p "$log_dir"

stamp="$(date +%Y%m%d-%H%M%S)"
log="$log_dir/update-check-$stamp.log"
latest="$log_dir/latest.log"

{
  echo "Lab update check started: $(date --iso-8601=seconds)"
  echo "Host: $(hostname)"
  echo "Running kernel: $(uname -r)"
  echo

  dnf5 check-upgrade --refresh
  rc=$?

  echo
  echo "dnf5 check-upgrade exit code: $rc"
  if [ "$rc" -eq 100 ]; then
    echo "Status: updates available"
  elif [ "$rc" -eq 0 ]; then
    echo "Status: no updates available"
  else
    echo "Status: check failed"
  fi
  echo "Lab update check finished: $(date --iso-8601=seconds)"
} > "$log" 2>&1

rc="$(grep 'dnf5 check-upgrade exit code:' "$log" | tail -1 | grep -oE '[0-9]+$')"
cp "$log" "$latest"

if [ "$rc" = "100" ] || [ "$rc" = "0" ]; then
  exit 0
fi

exit "${rc:-1}"
