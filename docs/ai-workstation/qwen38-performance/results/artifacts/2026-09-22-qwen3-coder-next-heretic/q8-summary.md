# Qwen3-Coder-Next Uncensored Heretic Benchmark


Run directory: `/home/helios/benchmarks/qwen3-coder-next-heretic-20260922T102804Z`

| Quant | Context | Status | Load s | Sentinel gen tok/s | Coding gen tok/s | Long prefill tok/s | Long gen tok/s | Tool calls | Mem avail after health MiB | Swap used after health MiB | VRAM used after health MiB |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Q6_K | 131072 | failed_start |  | None | None | None | None | None |  |  |  |
| Q6_K | 262144 | failed_start |  | None | None | None | None | None |  |  |  |
| Q8_0 | 131072 | completed | 24 | 31.668813676023948 | 31.57614075359539 | 474.21440652111454 | 24.55377382803581 | 1 | 23463.5 | 10094.5 | 84479.2 |
| Q8_0 | 262144 | completed | 24 | 30.469615404651236 | 31.522396662828942 | 474.22740115215436 | 23.933398874025634 | 1 | 23001.6 | 10094.6 | 86880.2 |
