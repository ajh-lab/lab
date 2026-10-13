#!/usr/bin/env python3
import asyncio
import os
import time
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

from aiohttp import ClientSession, ClientTimeout, web

BACKEND = os.getenv("LITELLM_BACKEND_URL", "http://127.0.0.1:4004").rstrip("/")
API_KEYS = {
    "shared": os.getenv("LITELLM_LAN_API_KEY", ""),
    "family-assistant": os.getenv("FAMILY_ASSISTANT_LITELLM_API_KEY", ""),
}
REQUESTS = Counter()
LATENCY_SECONDS = Counter()

BLOCKED_IP = "192.168.86.2"
BLOCK_TIMEZONE = ZoneInfo("America/Chicago")


def is_scheduled_block(peer_ip: str | None, now: datetime | None = None) -> bool:
    if peer_ip != BLOCKED_IP:
        return False
    local = datetime.now(BLOCK_TIMEZONE) if now is None else now.astimezone(BLOCK_TIMEZONE)
    return local.weekday() < 5 and 8 <= local.hour < 17


@web.middleware
async def scheduled_ip_block(request: web.Request, handler):
    # Trust the socket peer, never client-supplied forwarding headers.
    peer = request.transport.get_extra_info("peername") if request.transport else None
    peer_ip = peer[0] if peer else None
    if is_scheduled_block(peer_ip):
        return web.json_response(
            {"error": {"message": "Access blocked Monday-Friday 08:00-17:00 America/Chicago",
                       "type": "scheduled_access_denied"}},
            status=403,
        )
    return await handler(request)

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _client_name(request: web.Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    supplied = authorization.removeprefix("Bearer ")
    for name, key in API_KEYS.items():
        if key and supplied == key:
            return name
    return None


def _metric_path(path: str) -> str:
    return "chat_completions" if path.endswith("/chat/completions") else "other"


async def metrics(_: web.Request) -> web.Response:
    lines = [
        "# HELP litellm_lan_proxy_requests_total Requests accepted by the LAN proxy.",
        "# TYPE litellm_lan_proxy_requests_total counter",
    ]
    for (client, method, path, status), count in sorted(REQUESTS.items()):
        lines.append(
            f'litellm_lan_proxy_requests_total{{client="{client}",method="{method}",path="{path}",status="{status}"}} {count}'
        )
    lines.extend([
        "# HELP litellm_lan_proxy_request_duration_seconds_total Cumulative proxy request duration.",
        "# TYPE litellm_lan_proxy_request_duration_seconds_total counter",
    ])
    for (client, method, path, status), duration in sorted(LATENCY_SECONDS.items()):
        lines.append(
            f'litellm_lan_proxy_request_duration_seconds_total{{client="{client}",method="{method}",path="{path}",status="{status}"}} {duration:.6f}'
        )
    return web.Response(text="\n".join(lines) + "\n", content_type="text/plain")


async def handle(request: web.Request) -> web.StreamResponse:
    client = _client_name(request)
    if client is None:
        return web.json_response(
            {"error": {"message": "Unauthorized", "type": "authentication_error"}},
            status=401,
        )

    started = time.monotonic()
    target = f"{BACKEND}{request.rel_url}"
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP and key.lower() not in {"host", "authorization"}
    }
    body = await request.read()
    metric_key: tuple[str, str, str, str] | None = None
    try:
        async with request.app["client"].request(
            request.method,
            target,
            headers=headers,
            data=body if body else None,
            allow_redirects=False,
        ) as upstream:
            metric_key = (client, request.method, _metric_path(request.path), str(upstream.status))
            response_headers = {
                key: value for key, value in upstream.headers.items() if key.lower() not in HOP_BY_HOP
            }
            response = web.StreamResponse(status=upstream.status, headers=response_headers)
            await response.prepare(request)
            async for chunk in upstream.content.iter_chunked(65536):
                await response.write(chunk)
            await response.write_eof()
            return response
    finally:
        if metric_key is not None:
            REQUESTS[metric_key] += 1
            LATENCY_SECONDS[metric_key] += time.monotonic() - started


async def on_startup(app: web.Application) -> None:
    app["client"] = ClientSession(timeout=ClientTimeout(total=1800, sock_connect=30))


async def on_cleanup(app: web.Application) -> None:
    await app["client"].close()


app = web.Application(client_max_size=128 * 1024**2, middlewares=[scheduled_ip_block])
app.router.add_get("/metrics", metrics)
app.router.add_route("*", "/{tail:.*}", handle)
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == "__main__":
    host = os.getenv("LITELLM_LAN_PROXY_HOST", "0.0.0.0")
    port = int(os.getenv("LITELLM_LAN_PROXY_PORT", "4000"))
    web.run_app(app, host=host, port=port, access_log=None)
