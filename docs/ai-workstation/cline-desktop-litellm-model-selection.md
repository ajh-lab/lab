# Cline Desktop LiteLLM Model Selection

Last updated: 2026-09-21

## Current Setup

Cline Desktop is configured to use the ai-workstation Cline-filtered LiteLLM LAN endpoint:

```text
http://192.168.1.123:4002/v1
```

The LiteLLM LAN API key is stored in OpenBao at `secret/homelab/providers/litellm`, field `lan_api_key`. Do not store the key in this repository.

The Cline Desktop local config lives under:

```text
C:\Users\adamj\.cline\data
```

The selected provider is `litellm` for both plan and act mode. The selected model is the friendly alias:

```text
qwen3.8-flash-next
```

That alias is mapped in LiteLLM to the currently loaded ai-workstation backend:

```text
qwen3.8-flash-next-uncensored-orcarouter-iq4_xs
```

The active llama.cpp backend is the manual Flash-Next IQ4_XS service on port `11454`.

The local Cline provider registry has been collapsed to the LiteLLM provider only. The local Cline model registry has been collapsed to one model only:

```text
qwen3.8-flash-next
```

The only remaining Cline secret key slot is `liteLlmApiKey`. The older local `deepSeekApiKey` entry was removed from Cline's local secrets after backing up the full config, so Cline does not re-migrate DeepSeek as a configured provider.

## LiteLLM Model Discovery

The ai-workstation LiteLLM `model_list` has been reduced to one advertised
model so Cline, DSH, and other OpenAI-compatible harnesses cannot discover or
select stale routes:

```text
qwen3.8-flash-next
```

The standard LAN auth proxy remains available on port `4000`, but it now
advertises only the same single friendly alias. The internal LiteLLM endpoint
on `127.0.0.1:4004` also advertises only this alias.

The old multi-model LiteLLM configuration is preserved in the backup listed
below.

## Cline Model Discovery Filter

Cline Desktop uses a dedicated filtered proxy:

```text
litellm-cline-auth-proxy.service
```

The service listens on `0.0.0.0:4002`, reuses the same LiteLLM LAN bearer key, forwards requests to the internal LiteLLM backend on `127.0.0.1:4004`, and filters `GET /v1/models` down to:

```text
qwen3.8-flash-next
```

Remote service files:

```text
/home/helios/.config/systemd/user/litellm-cline-auth-proxy.service
/home/helios/.local/share/litellm-cline-auth-proxy/litellm_cline_auth_proxy.py
```

## Backups From This Change

Local Cline Desktop config backup:

```text
C:\Users\adamj\SourceControl\lab\tmp\cline-config-backup-20260921-151916
```

Additional local Cline config backup before collapsing old provider entries:

```text
C:\Users\adamj\SourceControl\lab\tmp\cline-config-backup-collapse-20260921-153630
```

Cline Desktop WebView local-storage cache backup:

```text
C:\Users\adamj\SourceControl\lab\tmp\cline-webview-localstorage-backup-20260921-153733
```

VS Code Cline extension model-cache backup:

```text
C:\Users\adamj\SourceControl\lab\tmp\cline-vscode-model-cache-backup-20260921-153841
```

DSH active config and launcher-template backup before removing secondary
provider/model entries:

```text
C:\Users\adamj\SourceControl\lab\tmp\dsh-single-model-config-backup-20260921-222059
```

These backups are under `tmp/`, which is ignored by git. Treat them as local-sensitive because they may contain API keys or prior provider configuration.

Remote LiteLLM config backup on ai-workstation:

```text
/home/helios/.config/litellm/backups/cline-friendly-alias-20260921-202109/config.yaml
```

Remote LiteLLM config backup before reducing global model discovery to one
model:

```text
/home/helios/.config/litellm/backups/limit-model-list-qwen-flashnext-20260921-221900/config.yaml
```

## Verification

After adding the alias, internal LiteLLM `/v1/models` included `qwen3.8-flash-next`, and a direct internal LiteLLM chat completion using that model returned `CLINE_ALIAS_OK`.

After adding the Cline-filtered proxy, `http://192.168.1.123:4002/v1/models` returned exactly one model, `qwen3.8-flash-next`, and a LAN-auth chat completion through the filtered endpoint returned `OK` in about 12 seconds.

After collapsing local Cline config and restarting Cline Desktop, the persisted provider list contained only `litellm`, the model registry contained only `qwen3.8-flash-next`, and the remaining local secret key list contained only `liteLlmApiKey`.

After reducing the LiteLLM server-side `model_list`, internal
`http://127.0.0.1:4004/v1/models`, LAN `http://192.168.1.123:4000/v1/models`,
and Cline-filtered `http://192.168.1.123:4002/v1/models` each returned exactly
one model: `qwen3.8-flash-next`. LAN-auth chat completions through both `4000`
and `4002` returned `OK`.
