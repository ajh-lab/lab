# Qwen3.8 27B Performance Tuning

Last verified: 2026-09-01 (America/Chicago)

## Purpose

This folder is the durable source of truth for Qwen3.8 27B inference tuning on
the AI workstation. Read this file before changing a Qwen3.8 model, toolbox,
systemd unit, LiteLLM route, Hermes profile, kernel parameter, BIOS memory
allocation, or benchmark method.

Keep experiments controlled:

1. Change one independent variable at a time.
2. Run only one benchmarked model server at a time.
3. Preserve the last working service and profile configuration before changes.
4. Use the same prompts, temperature, context, and repeat count for comparisons.
5. Record rejected changes as well as improvements.
6. Do not expose secrets, profile environment files, or model-provider keys.

Raw benchmark records are under `results/raw/`. The interpreted comparison and
experiment log are in `results/2026-09-01-baseline-and-no-mmap.md`.

## Host Baseline

| Item | Verified state |
| --- | --- |
| Host | `ai-workstation-evox2` / `helios@192.168.1.123` |
| OS | Fedora 43 |
| Kernel | `7.1.8-100.fc43.x86_64` |
| Firmware package | `linux-firmware-20260810-1.fc43.noarch` |
| Physical memory layout | 96 GiB fixed GPU allocation; about 31 GiB visible to Linux |
| GPU | Radeon 8060S / `gfx1151` |
| Kernel command line | No explicit IOMMU, GTT, TTM, or CWSR tuning parameters |
| IOMMU | Enabled |
| `amdgpu.cwsr_enable` | `1` |
| `ttm.pages_limit` | `4058925` pages, about 15.5 GiB |
| `ttm.page_pool_size` | `0` |
| TuneD profile | `throughput-performance` |
| GPU DPM level | `auto` |
| Internal LiteLLM | `http://127.0.0.1:4004/v1` |
| Benchmark harness | `automation/ai-workstation/scripts/benchmark-hermes-models.py` |

## Runtime Baseline

Both tested services use toolbox `llama-rocm-7.14-q4`, image
`docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.14`, and llama.cpp build
`10540` at commit `07822bddf`.

Common flags after experiment E002:

```text
--no-mmap -ngl 99 -c 131072 -b 1024 -ub 256 -fa on
-ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off
--temp 0 --repeat-penalty 1.15
```

### Q4 Worker Candidate

| Item | Value |
| --- | --- |
| Model | `Qwen3.8-27B-Uncensored-Q4_K_M.gguf` |
| Model path | `/mnt/ai/models/qwen38-uncensored-q4km/` |
| Approximate file size | 16 GiB |
| Service | `llama-qwen38-uncensored-q4km.service` |
| Endpoint | `http://127.0.0.1:11440/v1` |
| LiteLLM alias | `qwen3.8-27b-uncensored-q4_k_m` |
| Loaded GPU memory | About 22.2 GB decimal with 131k context |
| Current state after E002 | Active and healthy |

### BF16 Comparison Candidate

| Item | Value |
| --- | --- |
| Model | `Qwen3.8-27B-Uncensored-BF16.gguf` |
| Model path | `/mnt/ai/models/qwen38-uncensored-bf16/` |
| Approximate file size | 51 GiB |
| Service | `llama-qwen38-uncensored-bf16.service` |
| Endpoint | `http://127.0.0.1:11439/v1` |
| LiteLLM alias | `qwen3.8-27b-uncensored-bf16` |
| Hermes profile | `qwen38bf16tools` |
| Loaded GPU memory | About 57.7 GB decimal with 131k context |
| Current state after E002 | Configured and stopped |

The BF16 service was repaired on 2026-09-01 to use the healthy
`llama-rocm-7.14-q4` toolbox because the older `llama-rocm-7.14` toolbox had a
broken user mapping. The model and profile were not replaced.

## Rollback Locations

- Pre-BF16 repair and profile snapshot:
  `/home/helios/.hermes/backups/qwen38-bf16-benchmark-20260901T223023Z`
- Pre-`--no-mmap` service units:
  `/home/helios/.hermes/backups/qwen38-no-mmap-20260901T224645Z`

## Standard Benchmark Protocol

Use LiteLLM so the benchmark follows the same routing layer as Hermes:

```bash
cd ~/lab
python3 automation/ai-workstation/scripts/benchmark-hermes-models.py \
  --provider litellm \
  --models <model-alias> \
  --scenarios smoke,rust-light,code-review \
  --repeat 2 \
  --timeout 300 \
  --temperature 0 \
  --jsonl /tmp/<descriptive-result-name>.jsonl
```

Run the context case separately:

```bash
python3 automation/ai-workstation/scripts/benchmark-hermes-models.py \
  --provider litellm \
  --models <model-alias> \
  --scenarios smoke \
  --repeat 1 \
  --timeout 300 \
  --temperature 0 \
  --long-context-tokens 16000 \
  --jsonl /tmp/<descriptive-context-result-name>.jsonl
```

Record at minimum:

- model file and checksum
- toolbox image ID and llama.cpp build
- complete non-secret server flags
- service/model load state
- output tokens per second
- prompt/context elapsed time
- answer correctness
- GPU memory, temperature, and power during the run
- accepted or rejected decision

## Ordered Experiment Matrix

| ID | Variable | Status | Advancement rule |
| --- | --- | --- | --- |
| E001 | Q4 versus BF16 on ROCm 7.14 | Complete | Select practical worker baseline |
| E002 | Add `--no-mmap` | Complete, retained for stability | Keep unless regression is repeatable |
| E003 | Current stable ROCm toolbox | Pending | Advance only with equal correctness and useful speed/stability gain |
| E004 | Vulkan RADV toolbox | Pending | Compare exact same GGUF and flags |
| E005 | Batch/microbatch matrix | Pending | Improve prompt processing without OOM or decode regression |
| E006 | One-boot `amd_iommu=off` test | Pending approval | Require reversible boot test and measurable benefit |
| E007 | Dynamic GTT/TTM memory layout | Deferred | Capacity experiment requiring BIOS/kernel change and reboot |

Do not combine E003, E004, or E005. Establish a result for each independent
variable before creating a combined candidate.

## Current Decision

Q4_K_M is the preferred worker candidate. In E001 it produced correct simple
coding answers at roughly 11.5-11.9 output tokens per second, compared with
roughly 4.1 for BF16. BF16 did not show a quality advantage in the small test
set. A real issue execution still requires a restricted worker profile,
isolated worktree, mandatory CI, no automatic merge, and stronger-model review.

