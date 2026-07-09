---
name: hermes-kanban
description: Operate Hermes Kanban boards and cards from the lab repo. Use when Codex, Helios, Cline, or DeepSeek needs to inspect boards, blocked cards, running tasks, logs, worker profiles, assignment, safe recovery, or Kanban-driven project execution without using the dashboard or editing SQLite directly.
---

# Hermes Kanban

## Operating Rule

Use the repo helper scripts under `automation/hermes/` before probing the dashboard. Do not edit Hermes Kanban SQLite databases directly unless the user explicitly asks for low-level repair.

Default target:

- ai-workstation SSH: `helios@192.168.1.123`
- Default board: `kalshi-research-bot`
- Helper docs: `automation/hermes/README.md`

## Read Board State

```powershell
python .\automation\hermes\scripts\query_kanban.py boards
python .\automation\hermes\scripts\query_kanban.py list
python .\automation\hermes\scripts\query_kanban.py list --status blocked
python .\automation\hermes\scripts\query_kanban.py show <task_id>
python .\automation\hermes\scripts\query_kanban.py runs <task_id>
python .\automation\hermes\scripts\query_kanban.py log <task_id> --tail 30000
```

Use `--board <slug>` for non-default boards.

## Safe Recovery

Use `reset_card.py`; it shows the card first and mutates only with `--yes` or `--dry-run` where applicable.

```powershell
python .\automation\hermes\scripts\reset_card.py <task_id> --action comment --reason "diagnostic note"
python .\automation\hermes\scripts\reset_card.py <task_id> --action unblock --reason "blocker resolved" --yes
python .\automation\hermes\scripts\reset_card.py <task_id> --action reclaim --reason "stale running claim" --yes
python .\automation\hermes\scripts\reset_card.py <task_id> --action promote --reason "dependencies verified" --dry-run
```

Do not include secrets in comments or reasons.

## Profiles And Assignment

Hermes profiles are valid Kanban assignees. Check them on ai-workstation:

```bash
hermes profile list
hermes kanban assignees
```

Current model split:

- `default`: local `hermes-qwen3-coder:30b-256k` via LiteLLM/Ollama on ai-workstation.
- `deepseek-v4-flash`: DeepSeek V4 Flash profile for normal paid DeepSeek work.
- `deepseek-v4-pro`: DeepSeek V4 Pro profile for harder coding/review/research tasks.

Assign cards by profile name only after confirming the profile exists and its gateway is running or spawnable.

## Worker Health

For blocked/running cards, inspect in this order:

1. `query_kanban.py show <task_id>`
2. `query_kanban.py runs <task_id>`
3. `query_kanban.py log <task_id> --tail 30000`
4. `hermes kanban diagnostics` on ai-workstation if the helper output is insufficient.

Prefer fixing the underlying repo/config issue, then unblock/reclaim through official Hermes commands.
