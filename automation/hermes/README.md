# Hermes Kanban Helpers

These scripts let local AI agents query and recover Hermes Kanban cards from the
Windows lab repo without opening the Hermes dashboard or editing Kanban SQLite
databases directly.

Default target:

- SSH host: `helios@192.168.1.123`
- Board: `kalshi-research-bot`

## Query Cards

```powershell
python .\automation\hermes\scripts\query_kanban.py list
python .\automation\hermes\scripts\query_kanban.py list --status blocked
python .\automation\hermes\scripts\query_kanban.py show t_b4c17c0e
python .\automation\hermes\scripts\query_kanban.py runs t_b4c17c0e
python .\automation\hermes\scripts\query_kanban.py log t_b4c17c0e --tail 30000
```

Use `--board <slug>` for non-default boards:

```powershell
python .\automation\hermes\scripts\query_kanban.py --board kalshi-research-bot list
```

## Recover Cards

`reset_card.py` uses official Hermes commands only. It shows the card first and
will not mutate state unless `--yes` is provided. Do not include secrets in
reasons or comments.

```powershell
python .\automation\hermes\scripts\reset_card.py t_123 --action comment --reason "diagnostic note"
python .\automation\hermes\scripts\reset_card.py t_123 --action unblock --reason "verified blocker is resolved" --yes
python .\automation\hermes\scripts\reset_card.py t_123 --action reclaim --reason "stale running claim" --yes
python .\automation\hermes\scripts\reset_card.py t_123 --action promote --reason "dependencies verified" --dry-run
python .\automation\hermes\scripts\reset_card.py t_123 --action promote --reason "dependencies verified" --yes
```

Use `unblock` for blocked cards, `reclaim` for stale running cards, and
`promote` for ready/todo cards whose dependencies are complete.
