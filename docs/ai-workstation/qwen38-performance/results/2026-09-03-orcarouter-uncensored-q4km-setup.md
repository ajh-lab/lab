# Qwen3.8 OrcaRouter Uncensored Q4_K_M Setup

Date: 2026-09-03 (America/Chicago)

## Objective

Set up a separate Hugging Face Qwen3.8 27B uncensored model on helios for
interactive testing, while preserving the known-good Q6_K configuration as the
rollback path and removing Q6_K from VRAM before testing.

## Candidate

Selected model:

- Repository: `chimingw/Qwen3.8-27B-Uncensored-OrcaRouter-GGUF`
- Revision: `58ebd123013160600229eda180b5b17f3fb7af9d`
- File: `Qwen3.8-27B-Uncensored-OrcaRouter-Q4_K_M.gguf`
- Source lineage: pinned conversion/quantization of
  `orcarouter/Qwen3.8-27B-Uncensored-FP8`
- Published file size: 16,810,714,496 bytes
- Published SHA-256:
  `3445102e9cde5d562508642c100a2f5ac3368a5a3f748442811d7a95daee3bec`

Reasoning:

1. The user requested a model from the OrcaRouter uncensored Qwen3.8 27B
   Hugging Face family.
2. The direct OrcaRouter GGUF repo is gated, while this preservation release is
   public and pins its source revision.
3. Q4_K_M is the safest first interactive test point: small enough for the
   current workstation memory split, higher quality than Q3/IQ fallbacks, and
   already aligned with the existing llama.cpp service pattern.

## Rollback Capture

Before changing runtime state, the current setup was captured under:

- `/home/helios/.hermes/backups/qwen38-orcarouter-test-20260903T164613Z`

Captured evidence included:

- root Hermes config
- LiteLLM config
- Q6_K, Q4_K_M, and BF16 systemd unit files
- LiteLLM model list
- llama user-unit list
- `rocm-smi --showpids`
- `ollama ps`

Initial state:

| Check | Result |
| --- | --- |
| Q6 service | active |
| Q4 service | inactive |
| BF16 service | inactive |
| Q6 health | `{"status":"ok"}` |
| LiteLLM/Hermes services | active |
| Ollama residents | none |
| Resident llama process | Q6_K, 26,650,734,592 bytes VRAM |

## Download

Downloaded to:

- `/mnt/ai/models/qwen38-orcarouter-uncensored-q4km/Qwen3.8-27B-Uncensored-OrcaRouter-Q4_K_M.gguf`

Verification:

```text
Qwen3.8-27B-Uncensored-OrcaRouter-Q4_K_M.gguf: OK
```

Final size:

- 16,810,714,496 bytes

## Runtime Setup

Created user service:

- `llama-qwen38-orcarouter-uncensored-q4km.service`

Endpoint:

- `http://127.0.0.1:11448/v1`

Alias:

- `qwen3.8-27b-uncensored-orcarouter-q4_k_m`

Service flags follow the existing Q6/Q4 pattern:

```text
--host 127.0.0.1 --port 11448
--alias qwen3.8-27b-uncensored-orcarouter-q4_k_m
-m /mnt/ai/models/qwen38-orcarouter-uncensored-q4km/Qwen3.8-27B-Uncensored-OrcaRouter-Q4_K_M.gguf
--no-mmap -ngl 99 -c 131072 -b 1024 -ub 256 -fa on
-ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off
--temp 0 --repeat-penalty 1.15
```

Q6_K was stopped before starting this service. Before start, `rocm-smi` showed
no KFD PIDs and `ollama ps` was empty. The OrcaRouter service reached health in
6 seconds.

## LiteLLM And Hermes

Added non-default LiteLLM route:

- `qwen3.8-27b-uncensored-orcarouter-q4_k_m`

Added the alias to the root Hermes custom model list and all profile custom
model lists. Existing profile defaults were not changed.

Created test profile:

- `qwen38-27b-uncensored-orcarouter-q4_k_m-web-terminal-128k`

This profile was cloned from the Q6_K web-terminal profile shape and only
changes the default model plus description.

Additional backups:

- `/home/helios/.hermes/backups/qwen38-orcarouter-route-20260903T170403Z`
- `/home/helios/.hermes/backups/qwen38-orcarouter-profile-20260903T170528Z`

## Smoke Test

Direct llama.cpp smoke:

```json
{"model":"qwen3.8-27b-uncensored-orcarouter-q4_k_m","content":"ORCAROUTER_OK","finish_reason":"stop","usage":{"completion_tokens":6,"prompt_tokens":20,"total_tokens":26,"prompt_tokens_details":{"cached_tokens":0}}}
```

LiteLLM smoke:

```json
{"model":"qwen3.8-27b-uncensored-orcarouter-q4_k_m","content":"ORCAROUTER_OK","finish_reason":"stop","usage":{"completion_tokens":6,"prompt_tokens":20,"total_tokens":26,"prompt_tokens_details":{"cached_tokens":16}}}
```

## Final State

The OrcaRouter test model was left running for user evaluation. Q6_K remains the
configured default and rollback model, but is intentionally stopped so the new
test model is the only resident llama.cpp model in VRAM.

| Check | Result |
| --- | --- |
| OrcaRouter service | active |
| OrcaRouter health | `{"status":"ok"}` |
| Q6 service | inactive |
| LiteLLM route count | 1 |
| Hermes test profile | present |
| Hermes config/profile lists containing alias | 16 |
| Ollama residents | none |
| Resident llama process | OrcaRouter Q4_K_M, 21,446,123,520 bytes VRAM |

Rollback command:

```bash
systemctl --user stop llama-qwen38-orcarouter-uncensored-q4km.service
systemctl --user start llama-qwen38-uncensored-q6k.service
curl -fsS http://127.0.0.1:11446/health
```
