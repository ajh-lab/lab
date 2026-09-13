# DeepSeek Harness Local IQ4_XS Launcher

This launcher starts DeepSeek Harness on the local Windows workstation and points
its DeepSeek-compatible model adapter at the AI workstation LiteLLM LAN proxy.

## Target

- Harness home: `C:\Users\adamj\.dsh-lab-iq4xs`
- Patch template: `automation\deepseek-harness\config\iq4xs.cordis.patch.yml`
- Web UI: `http://127.0.0.1:3080/`
- API base: `http://192.168.1.123:4000/v1`
- Model: `qwen3.8-flash-next-uncensored-orcarouter-iq4_xs`
- Context: `65536`

## Start

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\adamj\SourceControl\lab\automation\deepseek-harness\scripts\Start-DeepSeekHarness-IQ4XS.ps1
```

The launcher resolves the LiteLLM LAN bearer key from OpenBao path
`secret/homelab/providers/litellm`, field `lan_api_key` or `api_key`. If that
path is not readable from the local bootstrap token, it falls back to the AI
workstation runtime file `/home/helios/.config/litellm/litellm-lan-api-key.env`
over SSH. The key is injected only into the Harness process environment as
`DEEPSEEK_API_KEY`.

If `C:\Users\adamj\.dsh-lab-iq4xs\cordis.patch.yml` is missing, the launcher
copies the tracked patch template into place before startup.

## Notes

- The local Harness patch disables DeepSeek-specific request extensions so the
  local LiteLLM/llama.cpp route receives ordinary OpenAI-compatible chat
  completions.
- Harness is currently launched through `npx --yes @deepseek-ai/dsh@0.1.2-rc.1`
  so the version is pinned without requiring a global npm install.
