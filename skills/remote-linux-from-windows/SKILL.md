---
name: remote-linux-from-windows
description: Run reliable remote Linux operations from a Windows or PowerShell agent workspace without fighting quoting, line endings, SSH, or secret-handling issues.
---

# Remote Linux From Windows

Use this skill when the agent is running from Windows, PowerShell, or VS Code on
Windows and needs to operate a Linux host over SSH. This includes BS01 field
rack nodes, the ai-workstation, k3s nodes, and other lab Linux servers.

If the agent is already running on Linux and not crossing a Windows-to-Linux
shell boundary, this skill is usually not needed.

## Core Rules

1. Keep PowerShell, SSH, and Bash quoting layers simple.
2. Prefer small transferred scripts over large inline `ssh "bash -c ..."`
   commands.
3. Use LF line endings for scripts that will run on Linux.
4. Never print secrets, raw environment dumps, private keys, tokens, or database
   URLs.
5. Prefer OpenBAO-backed secret resolution. Use `.env` fallback only when the
   lab context explicitly allows it.
6. Put temporary local helper scripts under `tmp/<task-or-topic>/`, not in the
   repo root.
7. Remove or document remote temporary files when they contain operational
   details.

## Recommended Workflow

For non-trivial remote Linux work from Windows:

1. Create a local task folder under `tmp/`.
2. Write the remote script there with LF endings.
3. Transfer the script to the Linux host.
4. Normalize line endings on the host if needed.
5. Run the script with `bash`.
6. Capture only the minimum useful output.
7. Verify the resulting service, config, or deployment state.

## PowerShell To Linux Script Pattern

Use this pattern for small remote scripts when `scp` or nested quoting becomes
fragile:

```powershell
$script = @'
set -euo pipefail
hostname
whoami
uname -a
'@

$bytes = [System.Text.Encoding]::UTF8.GetBytes($script)
$script64 = [Convert]::ToBase64String($bytes)
ssh user@host "printf %s '$script64' | base64 -d > /tmp/agent-task.sh && tr -d '\r' < /tmp/agent-task.sh > /tmp/agent-task.lf && mv /tmp/agent-task.lf /tmp/agent-task.sh && chmod +x /tmp/agent-task.sh && bash /tmp/agent-task.sh"
```

For larger scripts, write them to `tmp/<task-or-topic>/script.sh`, then use
`scp` or `ssh` stdin transfer. Avoid Windows CRLF endings:

```powershell
$local = "tmp/<task-or-topic>/script.sh"
scp $local user@host:/tmp/script.sh
ssh user@host "tr -d '\r' < /tmp/script.sh > /tmp/script.lf && mv /tmp/script.lf /tmp/script.sh && chmod +x /tmp/script.sh && bash /tmp/script.sh"
```

## Avoid These Patterns

- Do not embed multi-line Bash heredocs directly inside PowerShell strings when
  the script includes `$`, quotes, pipes, JSON, Python snippets, or `&&`.
- Do not chain secret reads with commands that might echo the secret.
- Do not run `env`, `printenv`, `set`, or `systemctl show` broadly when secrets
  may be present.
- Do not use `set -x` around secret material.
- Do not assume PowerShell globbing behaves like Bash globbing.
- Do not rely on CRLF scripts running correctly on Linux.

## SSH Checks

Start with cheap reachability checks:

```powershell
ssh user@host "hostname && whoami && pwd && uname -srm"
```

For service work:

```powershell
ssh user@host "systemctl is-active <service>; systemctl --no-pager --full status <service>"
ssh user@host "journalctl -u <service> --no-pager -n 80"
```

For network work:

```powershell
ssh user@host "ip -brief addr; ip route; ping -c 2 <target>"
```

## Sudo And Secrets

When sudo is required:

- Resolve credentials with the documented lab secret helpers.
- Do not echo passwords into logs.
- Prefer existing helper scripts or non-interactive sudo validation patterns
  already used in the repo.
- If OpenBAO is unavailable but SSH works, use the documented fallback only as a
  temporary operational measure.

## Verification Standard

Do not stop after copying a file or restarting a service. Verify the actual
outcome:

- service active state
- logs after restart
- expected ports listening
- expected API health endpoint
- expected Kubernetes or ArgoCD object state
- expected database or NATS behavior, without printing secrets

