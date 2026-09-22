# Lab Agent Instructions

These instructions apply to work rooted in this lab repository. More specific
`AGENTS.md` files in nested repositories add to or override these instructions
for their own scope.

## Context Loading

- Detect the current operating system and shell before running commands.
- For non-trivial lab work, read `ai-baseline-context.md` first and run
  `automation/agent/scripts/bootstrap-lab-context.ps1` when documented for the
  task.
- For work under `repositories/<repo-name>`, read that repository's
  `AGENTS.md`, `ai-baseline-context.md`, and `docs/context/project-status.md`
  before planning or implementation. Follow only the referenced context files
  relevant to the current phase.
- For cross-repository work, read the baseline and status files for every
  affected repository and use the DroneOps repository context map before
  copying or relocating shared context.
- Refresh authoritative context at the start of each PR-sized phase, after each
  PR merge, before switching repositories, before schema or deployment work,
  and after a blocker or owner decision.

## Workspace Safety

- Treat `repositories/` as an ignored local checkout workspace, not as content
  owned by the lab repository.
- Use a fresh isolated worktree or clone for issue work. Never reset, clean,
  stash, overwrite, or reuse a shared checkout that contains unrelated work.
- Put disposable scripts, logs, command output, and experiments under
  `tmp/<task-or-topic>/`. Do not add scratch artifacts to the repository root.
- Do not revert changes you did not create. Work around unrelated changes or
  stop when they make the requested task unsafe or impossible.

## Issue And PR Delivery

- Treat the selected issue as the sole active durable goal. Read its body,
  comments, dependencies, linked PRs, and Project fields before changing code.
- Use short-lived branches and small coherent PR phases. Link each PR to its
  owning issue and keep issue and Project status truthful.
- Follow test-driven development where practical: write and run the narrowest
  failing test or check first, implement the minimum passing change, then
  refactor. Record red, green, and regression evidence in the PR; explain when
  TDD is not applicable.
- Do not declare completion from code, CI, merge, deployment, or chat history
  alone. Reconcile tests, required checks, immutable deployment, live evidence,
  acceptance criteria, issue checkboxes, Project fields, and status documents.
- Continue through PR and deployment boundaries until acceptance is complete.
  Stop only for a genuine owner action, credential need, unsafe mutation,
  architecture conflict, or persistent external failure, and state the exact
  action required.
- Before GitHub CLI calls, verify the working directory, remote, and concise
  branch status. Derive repository identity from the remote and bound each
  GitHub operation to 30 seconds.

## Windows And Remote Linux

- On Windows, use PowerShell syntax. Do not assume WSL or Docker Desktop works.
- Avoid complex PowerShell-to-SSH-to-shell quoting. For multi-line Linux work,
  transfer a small LF-normalized script or send it over SSH stdin.
- Use the relevant lab skills and runbooks for remote Linux, k3s/GitOps,
  OpenBAO, Hermes, AI-workstation, and documentation work.
- When testing local ai-workstation models, capture timestamp, model source,
  quantization, service, port, context, MTP status, memory split,
  VRAM/RAM/swap, Hermes, LiteLLM, llama.cpp, ROCm, OS/kernel versions, smoke
  results, controlled benchmark scores, and rollback state.

## Secrets And Infrastructure

- Never print, commit, or persist credentials, tokens, private keys, connection
  strings, environment dumps, or secret values. Use documented OpenBAO and
  External Secrets patterns and record only secret paths and field names.
- Prefer repository and GitOps changes over imperative live-cluster mutation.
  Verify the actual immutable deployed revision before reporting readiness.
- Use the BS01 field kubeconfig for BS01 work and the main lab kubeconfig only
  for the general Raspberry Pi cluster, as defined by the baseline.

## DroneOps Boundaries

- Preserve the browser, platform, gateway, and flight-controller boundaries in
  the DroneOps repository instructions. Browsers never communicate directly
  with hardware, MAVLink, NATS, or PostgreSQL.
- Do not change receiver assignments, aircraft-home state, credentials,
  physical hardware, or flight behavior without explicit authorization.
- Keep simulated or replay evidence separate from physical HIL evidence and do
  not infer authentication, hardware identity, or live acceptance from static
  UI text or healthy infrastructure alone.
