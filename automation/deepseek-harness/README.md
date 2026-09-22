# DeepSeek Harness Local IQ4_XS Launcher

This launcher starts DeepSeek Harness on the local Windows workstation and points
a custom OpenAI-compatible model provider at the AI workstation LiteLLM LAN
proxy.

## Target

- Harness home: `C:\Users\adamj\.dsh-lab-iq4xs`
- Patch template: `automation\deepseek-harness\config\iq4xs.cordis.patch.yml`
- Web UI: `http://127.0.0.1:3080/`
- API base: `http://192.168.1.123:4000/v1`
- DSH provider: `AI Workstation LiteLLM` (`ai-workstation-litellm`)
- Model: `qwen3.8-flash-next`
- Context: `131072`
- Max output tokens: `16384`
- Installed web plugins:
  - `dsh-web` from `github:zhu1090093659/dsh-web`
  - `dsh-better-sidebar` from `github:omdsh-dev/DSH-better-sidebar`

## Start

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\adamj\SourceControl\lab\automation\deepseek-harness\scripts\Start-DeepSeekHarness-IQ4XS.ps1
```

The launcher resolves the LiteLLM LAN bearer key from OpenBao path
`secret/homelab/providers/litellm`, field `lan_api_key` or `api_key`. If that
path is not readable from the local bootstrap token, it falls back to the AI
workstation runtime file `/home/helios/.config/litellm/litellm-lan-api-key.env`
over SSH. The key is injected only into the Harness process environment as
`LITELLM_API_KEY`.

The launcher keeps the root and web-profile Harness patch files aligned with
the tracked IQ4_XS patch template before startup.

The launcher sets provider/model `maxTokens` to `16384`. DSH still needs a
finite cap, and upstream providers may enforce their own lower output limits.

## Notes

- The local Harness patch disables the default DeepSeek adapter and uses the
  `llm-pi-ai` adapter to declare the AI workstation LiteLLM proxy as its own
  OpenAI-compatible provider. The provider list is intentionally limited to
  the current ai-workstation model alias so DSH does not surface stale model
  routes while Cline and other harnesses are being kept to one selectable
  model.
- Harness is currently launched through `npx --yes @deepseek-ai/dsh@0.1.6-alpha.2`
  so the version is pinned without requiring a global npm install.
- DSH `0.1.6-alpha.2` requires a newer Node runtime than the Windows system
  Node `22.17.0`; the launcher prepends the bundled Codex Node runtime when
  present.
- `dsh-web` is added to the web profile bundle list. Its aggregate package
  mounts `web-ui-better-sidebar`, so the standalone Better Sidebar row may
  disable itself when duplicate detection sees the aggregate row already
  active.
- The web profile's `pnpm-workspace.yaml` explicitly allows build scripts for
  the plugin dependencies that DSH/pnpm requested during install:
  `cloudflared`, `cpu-features`, `node-pty`, `ssh2`, and the exact GitHub
  tarball key for `dsh-better-sidebar`.
