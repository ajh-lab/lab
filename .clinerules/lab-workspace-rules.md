# Lab Workspace Rules

- Start by reading `ai-baseline-context.md` for lab topology, services, conventions, and current state.
- Use `C:\Users\adamj\SourceControl\lab` as the local Windows workspace root.
- The ai-workstation is `helios@192.168.1.123`.
- The ai-workstation lab repo is `/home/helios/lab`.
- Active project repos should live under `/home/helios/lab/repositories`.
- Use OpenBAO for secrets. Do not print secret values.
- Use documented Hermes Kanban helper scripts where available instead of manually interacting with the dashboard.
- For lab-monitoring/Grafana work, check git state, ArgoCD/deployment state, live Grafana state, and Prometheus data separately.
- LiteLLM LAN endpoint for Cline is `http://192.168.1.123:4000/v1`.
- LiteLLM internal Hermes endpoint is `http://127.0.0.1:4004/v1`.
- Cline should use model `deepseek-v4-flash` for normal Act work and `deepseek-v4-pro` for harder Plan/recovery work.
- Commit and push only intentional changes.
- Do not revert unrelated user or agent changes.