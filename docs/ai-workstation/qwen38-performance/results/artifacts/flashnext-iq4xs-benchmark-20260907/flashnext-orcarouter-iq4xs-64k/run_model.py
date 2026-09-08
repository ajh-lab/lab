import json
import pathlib
import re
import sys
import time
import urllib.request


prompt_path = pathlib.Path(sys.argv[1])
output_path = pathlib.Path(sys.argv[2])
raw_path = pathlib.Path(sys.argv[3])
model = sys.argv[4] if len(sys.argv) > 4 else "qwen3.8-27b-uncensored-q4_k_m"

payload = {
    "model": model,
    "messages": [{"role": "user", "content": prompt_path.read_text()}],
    "temperature": 0,
    "max_tokens": 4096,
}
request = urllib.request.Request(
    "http://127.0.0.1:4004/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
started = time.monotonic()
with urllib.request.urlopen(request, timeout=900) as response:
    result = json.load(response)
elapsed = time.monotonic() - started

raw_path.write_text(json.dumps(result, indent=2))
content = result["choices"][0]["message"]["content"].strip()
match = re.fullmatch(r"```(?:python)?\s*(.*?)\s*```", content, re.DOTALL)
if match:
    content = match.group(1)
output_path.write_text(content + "\n")

usage = result.get("usage", {})
print(json.dumps({
    "elapsed_seconds": round(elapsed, 3),
    "prompt_tokens": usage.get("prompt_tokens"),
    "completion_tokens": usage.get("completion_tokens"),
    "total_tokens": usage.get("total_tokens"),
    "finish_reason": result["choices"][0].get("finish_reason"),
}))
