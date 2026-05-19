#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "${script_dir}/../../.." && pwd)"
source_dir="${repo_root}/skills/lab-ops"
codex_home="${CODEX_HOME:-${HOME}/.codex}"
target_dir="${codex_home}/skills/lab-ops"

if [[ ! -f "${source_dir}/SKILL.md" ]]; then
  echo "lab-ops skill not found at ${source_dir}" >&2
  exit 1
fi

mkdir -p "$(dirname -- "${target_dir}")"

if [[ -L "${target_dir}" ]]; then
  ln -sfn "${source_dir}" "${target_dir}"
elif [[ -e "${target_dir}" ]]; then
  mkdir -p "${target_dir}"
  cp -a "${source_dir}/." "${target_dir}/"
else
  ln -s "${source_dir}" "${target_dir}"
fi

echo "Installed lab-ops skill at ${target_dir}"
