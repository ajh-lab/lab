# E004 Results: Vulkan RADV

Date: 2026-09-01 (America/Chicago)

## Variable Under Test

The exact Q4_K_M model and E002 flags were moved to the current stable Vulkan
RADV toolbox. The candidate and ROCm 10 used the same llama.cpp build.

| Item | ROCm 10 | Vulkan RADV |
| --- | --- | --- |
| Toolbox | `llama-rocm-10.0-qwen38-test` | `llama-vulkan-radv-qwen38-test` |
| llama.cpp | build `10751`, `3466812d1` | build `10751`, `3466812d1` |
| Device view | ROCm, 98304 MiB | Vulkan RADV, 114159 MiB |
| Model and flags | Q4_K_M E002 baseline | Same |

## Results

| Scenario | ROCm 10 | Vulkan RADV |
| --- | ---: | ---: |
| Rust repeat 1 | 11.87 tok/s | 10.31 tok/s |
| Rust repeat 2 | 11.85 tok/s | 10.33 tok/s |
| Code review repeat 1 | 11.42 tok/s | 8.96 tok/s |
| Code review repeat 2 | 11.98 tok/s | 11.15 tok/s |
| 10,298-token context elapsed | 32.73 s | 35.31 s |
| Basic response correctness | Pass | Pass |
| Approximate loaded GPU memory | 22.2 GB | 21.4 GB |

Post-test idle evidence for Vulkan was 0% GPU use, 48 C, about 12.2 W socket
graphics package power, and 21.4 GB decimal GPU memory used.

## Decision

Reject Vulkan RADV for this Qwen3.8 dense Q4 worker. It exposes more addressable
memory and uses slightly less reported GPU memory, but decode and context
processing were slower and code-review throughput was less consistent. Keep
ROCm as the preferred backend.

