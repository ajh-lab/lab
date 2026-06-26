# Temporary Workspace

Use this folder for disposable agent-generated files, experiments, command
outputs, and scratch scripts.

Rules:

- Put temporary files under `tmp/<task-or-topic>/`.
- Do not create scratch files in the repository root.
- Do not put secrets, tokens, kubeconfigs, private keys, or webhook URLs here.
- Keep durable automation in `automation/`, durable docs in `docs/`, and active
  cloned repositories in `repositories/`.
- Anything under `tmp/` is ignored by git unless explicitly allow-listed.
