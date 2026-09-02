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

Implementation-quality evaluations are recorded in
`results/2026-09-01-q4-python-telemetry-eval.md` and
`results/2026-09-01-bf16-python-telemetry-eval.md`, with the coding-specialized
comparison in `results/2026-09-01-qwen3-coder-python-telemetry-eval.md`. They
test whether throughput, precision, and specialization translate into useful
coding behavior rather than treating model labels as sufficient worker metrics.
The intermediate-precision promotion decision is recorded in
`results/2026-09-01-q6-python-telemetry-eval.md`.

Qwen3.8-Flash-Next preflight is recorded in
`results/2026-09-02-flash-next-preflight.md`. It stopped before any large
download because official FP8/BF16 checkpoints and quality-preserving GGUFs do
not fit the current 96 GiB GPU allocation, while plausible-fit third-party
GGUFs are low precision and require a newer llama.cpp runtime than the active
ROCm toolbox provides.

## Host Baseline

| Item | Verified state |
| --- | --- |
| Host | `ai-workstation-evox2` / `helios@192.168.1.123` |
| OS | Fedora 43 |
| Kernel | `7.1.9-100.fc43.x86_64` |
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

The Q4, Q6, and BF16 comparison services use toolbox `llama-rocm-7.14-q4`, image
`docker.io/kyuz0/amd-strix-halo-toolboxes:rocm-7.14`, and llama.cpp build
`10540` at commit `07822bddf`.

Common flags after experiment E002:

```text
--no-mmap -ngl 99 -c 131072 -b 1024 -ub 256 -fa on
-ctk q8_0 -ctv q8_0 --parallel 1 --reasoning off
--temp 0 --repeat-penalty 1.15
```

### Q6 Default Worker

| Item | Value |
| --- | --- |
| Model | `Qwen3.8-27B-Uncensored-Q6_K.gguf` |
| Model path | `/mnt/ai/models/qwen38-uncensored-q6k/` |
| Exact file size | 22,430,999,968 bytes |
| Service | `llama-qwen38-uncensored-q6k.service` |
| Endpoint | `http://127.0.0.1:11446/v1` |
| LiteLLM alias | `qwen3.8-27b-uncensored-q6_k` |
| Hermes web profile | `qwen38-27b-uncensored-q6_k-web-terminal-128k` |
| Loaded GPU memory | 27,386,691,584 bytes with 131k context |
| Current state | Enabled, active, healthy, and selected by the Hermes default profile |

### Q4 Rollback Candidate

| Item | Value |
| --- | --- |
| Model | `Qwen3.8-27B-Uncensored-Q4_K_M.gguf` |
| Model path | `/mnt/ai/models/qwen38-uncensored-q4km/` |
| Approximate file size | 16 GiB |
| Service | `llama-qwen38-uncensored-q4km.service` |
| Endpoint | `http://127.0.0.1:11440/v1` |
| LiteLLM alias | `qwen3.8-27b-uncensored-q4_k_m` |
| Loaded GPU memory | About 22.2 GB decimal with 131k context |
| Current state | Installed, disabled, and inactive after the Q6 promotion |

### BF16 Comparison Candidate

| Item | Value |
| --- | --- |
| Model | `Qwen3.8-27B-Uncensored-BF16.gguf` |
| Model path | `/mnt/ai/models/qwen38-uncensored-bf16/` |
| Approximate file size | 51 GiB |
| Service | `llama-qwen38-uncensored-bf16.service` |
| Endpoint | `http://127.0.0.1:11439/v1` |
| LiteLLM alias | `qwen3.8-27b-uncensored-bf16` |
| Hermes full profile | `qwen38-27b-uncensored-bf16-full-128k` |
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
- Pre-E006 `7.1.8` boot-entry snapshot:
  `/home/helios/.hermes/backups/qwen38-iommu-20260901T231833Z`
- Pre-E006 `7.1.9` boot-entry snapshot:
  `/home/helios/.hermes/backups/qwen38-iommu-20260901T232227Z`

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
| E003 | Current stable ROCm 10 toolbox | Complete, neutral | No promotion; speed difference was within run variance |
| E004 | Vulkan RADV toolbox | Complete, rejected | Slower decode and context processing than ROCm |
| E005 | Batch/microbatch matrix | Complete, neutral | Cold-start repeats showed no material improvement |
| E006 | One-boot `amd_iommu=off` test | Complete, rejected | No measurable decode or cold-context benefit |
| E007 | Dynamic GTT/TTM memory layout | Deferred | Capacity experiment requiring BIOS/kernel change and reboot |
| E008 | Q6_K implementation quality | Complete, promoted | Better blind score with acceptable latency and VRAM cost |
| E009 | Qwen3.8-Flash-Next preflight | Blocked before download | Needs side-by-side llama.cpp >= b10665 and owner acceptance of low-precision text-only test |

Do not combine E003, E004, or E005. Establish a result for each independent
variable before creating a combined candidate.

Long-context repetitions must restart the model service before every measured
run. llama.cpp prompt-cache reuse otherwise turns later repetitions into cache
tests and invalidates cold prompt-processing comparisons.

## Current Decision

Q6_K is the preferred quality-first local Qwen3.8 worker. On the blind Python
telemetry task it scored 14/18 initially and 16/18 after feedback, compared
with Q4's 13/18 and 16/18. It took 11.9% longer across both generations and
used about 5.2 GB more VRAM, but improved first-pass correctness and produced a
shorter repaired implementation. Q4 remains installed as the faster rollback.
A real issue execution still requires a restricted worker profile, isolated
worktree, mandatory CI, no automatic merge, and stronger-model review.

ROCm 10 build `10751` was also tested against the same Q4 file and flags. Its
decode and context results were effectively equal to ROCm 7.14 build `10540`,
so the current service was not promoted solely for version freshness.

Vulkan RADV build `10751` was slower for the same dense Q4 model. Keep ROCm as
the Qwen3.8 backend; retain Vulkan only as a compatibility option or for a
future model-specific experiment.

Batch candidates `2048/512` and `4096/1024` did not materially outperform the
`1024/256` control. Retain `1024/256` until a different model or workload
demonstrates a repeatable prompt-processing benefit.

After E005, a stopped toolbox-backed test unit left its child `llama-server`
process alive. The orphan held about 22 GB of VRAM and kept the GPU busy even
though port `11444` was no longer listening. Terminating that exact test PID
restored the expected final state: only primary port `11440`, about 22.2 GB of
VRAM in use, an idle GPU, and a healthy primary endpoint. Future toolbox tests
must verify process and GPU state in addition to systemd unit state.

E006 disabled AMD IOMMU for one controlled boot. Decode remained within normal
variance and three cold 10,298-token context runs averaged 32.84 seconds versus
the 32.87-second control. The 0.03-second difference is not meaningful. The
flag was removed from the saved boot entry before the restoration reboot, so
normal IOMMU behavior remains the accepted configuration.

The standalone Python telemetry evaluation increased confidence that Q4_K_M is
useful for scoped implementation work: it passed all 13 initial hidden tests on
its first attempt. Additional standards-focused review found five RFC3339 and
mapping-contract cases; after one feedback cycle it passed three of those five
while retaining all original behavior. Keep Q4 as the primary local candidate,
but require tests and review for exact protocol, security, persistence, and
safety contracts.

BF16 performed worse on the identical blind task. It scored 10/18 initially
and 14/18 after the same two-item feedback cycle, compared with Q4's 13/18 and
16/18. BF16 also took 578.806 and 605.428 seconds for the two generations,
compared with Q4's 212.608 and 296.842 seconds. Retain BF16 for controlled
experiments only; this test supplies no evidence for promoting it as the
default worker.

The source model family also publishes `Q5_K_M` and `Q8_0` GGUFs. Q6_K passed
the same blind evaluation and was promoted on 2026-09-01. Because its observed
advantage is small and comes from one deterministic task, revisit the decision
after several real GitHub issues rather than assuming quantization alone
guarantees better results.

The resident Qwen3-Coder 30B-A3B Q8_0 model was much faster but less correct on
the same task. It scored 10/18 in 58.123 seconds initially and 12/18 in 53.121
seconds after feedback. Keep it as a candidate for low-risk, heavily tested
work such as documentation, scaffolding, focused UI edits, and mechanical test
creation. Qwen3.8 Q6 is now the preferred local implementation worker for
general DroneOps issues; Q4 remains the rollback and faster-throughput option.

Qwen3.8-Flash-Next was preflighted on 2026-09-02 and not downloaded. The
official BF16 and FP8 checkpoints are too large for the current memory split,
Q4-class GGUFs exceed the GPU budget after runtime overhead, and the active
ROCm llama.cpp build `10540` predates the GGUF publisher's required `b10665`
support for the new architecture. Revisit only after preparing a side-by-side
newer ROCm llama.cpp runtime and accepting that the first local test would need
to be low-precision, text-only, and non-default.
