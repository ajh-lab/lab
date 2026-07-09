#!/usr/bin/env python3
"""Benchmark local Hermes/Ollama model aliases through LiteLLM or Ollama.

This script is intentionally dependency-free so it can run directly on the
ai-workstation with the system Python.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MODELS = [
    "hermes-qwen3-coder:30b-64k",
    "hermes-qwen3-coder:30b-128k",
    "hermes-qwen3-coder:30b-256k",
]


SCENARIOS = {
    "smoke": {
        "max_tokens": 32,
        "prompt": "Reply exactly: BENCH_OK",
    },
    "rust-light": {
        "max_tokens": 384,
        "prompt": (
            "Create a minimal Rust CLI application that prints a greeting. "
            "Show the file layout and the contents of Cargo.toml and src/main.rs. "
            "Keep the answer concise."
        ),
    },
    "code-review": {
        "max_tokens": 512,
        "prompt": (
            "Review this Python function for bugs and provide a corrected version:\n\n"
            "def average(values):\n"
            "    total = 0\n"
            "    for value in values:\n"
            "        total += value\n"
            "    return total / len(values)\n\n"
            "Mention only concrete failure cases and the fixed code."
        ),
    },
}


@dataclass
class Result:
    provider: str
    model: str
    scenario: str
    ok: bool
    elapsed_seconds: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    prompt_tokens_per_second: float | None = None
    completion_tokens_per_second: float | None = None
    first_200_chars: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": self.provider,
            "model": self.model,
            "scenario": self.scenario,
            "ok": self.ok,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_tokens_per_second": _round(self.prompt_tokens_per_second),
            "completion_tokens_per_second": _round(self.completion_tokens_per_second),
            "first_200_chars": self.first_200_chars,
            "error": self.error,
        }


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def post_json(url: str, payload: dict[str, Any], timeout: int, headers: dict[str, str] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=request_headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run_litellm(model: str, scenario: str, prompt: str, max_tokens: int, args: argparse.Namespace) -> Result:
    url = args.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise coding assistant. Answer directly and stop when complete.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": args.temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {args.api_key}"}
    started = time.monotonic()
    try:
        body = post_json(url, payload, args.timeout, headers)
        elapsed = time.monotonic() - started
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return Result(args.provider, model, scenario, False, time.monotonic() - started, error=str(exc))

    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = body.get("usage") or {}
    completion_tokens = usage.get("completion_tokens")
    prompt_tokens = usage.get("prompt_tokens")
    total_tokens = usage.get("total_tokens")
    tps = completion_tokens / elapsed if completion_tokens and elapsed > 0 else None
    return Result(
        args.provider,
        model,
        scenario,
        True,
        elapsed,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        completion_tokens_per_second=tps,
        first_200_chars=content.replace("\n", "\\n")[:200],
    )


def run_ollama(model: str, scenario: str, prompt: str, max_tokens: int, args: argparse.Namespace) -> Result:
    url = args.ollama_url.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise coding assistant. Answer directly and stop when complete.",
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": args.temperature,
            "num_predict": max_tokens,
        },
    }
    started = time.monotonic()
    try:
        body = post_json(url, payload, args.timeout)
        elapsed = time.monotonic() - started
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return Result(args.provider, model, scenario, False, time.monotonic() - started, error=str(exc))

    content = body.get("message", {}).get("content", "")
    prompt_tokens = body.get("prompt_eval_count")
    completion_tokens = body.get("eval_count")
    prompt_duration = body.get("prompt_eval_duration")
    completion_duration = body.get("eval_duration")
    prompt_tps = prompt_tokens / (prompt_duration / 1_000_000_000) if prompt_tokens and prompt_duration else None
    completion_tps = completion_tokens / (completion_duration / 1_000_000_000) if completion_tokens and completion_duration else None
    return Result(
        args.provider,
        model,
        scenario,
        True,
        elapsed,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=(prompt_tokens or 0) + (completion_tokens or 0),
        prompt_tokens_per_second=prompt_tps,
        completion_tokens_per_second=completion_tps,
        first_200_chars=content.replace("\n", "\\n")[:200],
    )


def print_ollama_ps() -> None:
    try:
        completed = subprocess.run(["ollama", "ps"], check=False, capture_output=True, text=True, timeout=10)
    except (FileNotFoundError, subprocess.SubprocessError):
        return
    if completed.stdout.strip():
        print("\nollama ps:")
        print(completed.stdout.rstrip())


def append_jsonl(path: Path | None, result: Result) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result.to_dict(), sort_keys=True) + "\n")


def print_result(result: Result) -> None:
    status = "ok" if result.ok else "FAIL"
    tps = "" if result.completion_tokens_per_second is None else f", out_tps={result.completion_tokens_per_second:.2f}"
    ptps = "" if result.prompt_tokens_per_second is None else f", prompt_tps={result.prompt_tokens_per_second:.2f}"
    tokens = ""
    if result.prompt_tokens is not None or result.completion_tokens is not None:
        tokens = f", prompt={result.prompt_tokens}, out={result.completion_tokens}, total={result.total_tokens}"
    print(f"{status:4} {result.provider:7} {result.model:34} {result.scenario:12} {result.elapsed_seconds:8.2f}s{tokens}{ptps}{tps}")
    if result.error:
        print(f"     error: {result.error}")


def build_long_prompt(target_tokens: int) -> str:
    # Roughly four characters per token for English text. This is a synthetic
    # prefill test, not a semantic quality benchmark.
    target_chars = target_tokens * 4
    sentence = (
        "This benchmark paragraph describes a lab service, its deployment state, "
        "and the operational checks an assistant should perform before making changes. "
    )
    repeated = (sentence * ((target_chars // len(sentence)) + 1))[:target_chars]
    return (
        "Read the context below, then answer with exactly the final service name mentioned.\n\n"
        f"{repeated}\n\nFinal service name: ai-workstation-benchmark\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Hermes/Ollama model aliases.")
    parser.add_argument("--provider", choices=["litellm", "ollama"], default="litellm")
    parser.add_argument("--base-url", default="http://127.0.0.1:4004/v1", help="LiteLLM OpenAI-compatible base URL")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434", help="Ollama base URL")
    parser.add_argument("--api-key", default="no-key-required")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS), help="Comma-separated model aliases")
    parser.add_argument("--scenarios", default="smoke,rust-light,code-review", help="Comma-separated scenario names")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--jsonl", type=Path)
    parser.add_argument("--long-context-tokens", type=int, default=0, help="Add a synthetic long-context scenario")
    parser.add_argument("--show-ollama-ps", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    models = [item.strip() for item in args.models.split(",") if item.strip()]
    selected = [item.strip() for item in args.scenarios.split(",") if item.strip()]
    scenarios = dict(SCENARIOS)
    if args.long_context_tokens > 0:
        long_name = f"long-{args.long_context_tokens}"
        scenarios[long_name] = {
            "max_tokens": 32,
            "prompt": build_long_prompt(args.long_context_tokens),
        }
        if long_name not in selected:
            selected.append(long_name)

    unknown = [name for name in selected if name not in scenarios]
    if unknown:
        print(f"Unknown scenario(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    print(f"provider={args.provider} repeat={args.repeat} temperature={args.temperature}")
    print(f"models={', '.join(models)}")
    if args.show_ollama_ps:
        print_ollama_ps()

    runner = run_litellm if args.provider == "litellm" else run_ollama
    failed = False
    for _ in range(args.repeat):
        for model in models:
            for scenario_name in selected:
                scenario = scenarios[scenario_name]
                result = runner(model, scenario_name, scenario["prompt"], scenario["max_tokens"], args)
                print_result(result)
                append_jsonl(args.jsonl, result)
                failed = failed or not result.ok
    if args.show_ollama_ps:
        print_ollama_ps()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
