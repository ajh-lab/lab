# LiteLLM LAN scheduled source-IP block

Activated 2026-10-13 on ai-workstation (192.168.1.123), at the owner's request.

- Block socket source IP `192.168.86.2` Monday-Friday, 08:00 inclusive to
  17:00 exclusive, in `America/Chicago`. IANA timezone data handles CST/CDT.
- Outside that schedule, ordinary bearer authentication applies. Other IPs
  retain their existing access. Forwarded headers cannot bypass the block.
- The middleware returns HTTP 403 (`scheduled_access_denied`) for all LAN
  proxy routes, including metrics. It evaluates each incoming request; an
  already accepted stream is not terminated when the clock reaches 08:00.
- This applies to port 4000, not the internal loopback LiteLLM route on 4004.
- No recurring job is required. The policy persists in the proxy script and
  takes effect dynamically without daily restarts.

## Source and deployment

Source: `litellm_lan_auth_proxy.py` in this directory (captured from the live
proxy, preserving existing authentication, streaming, and metrics behavior).
Runtime: `/home/helios/.local/share/litellm-lan-auth-proxy/litellm_lan_auth_proxy.py`.
Service: user unit `litellm-lan-auth-proxy.service`.
Interpreter: `/home/helios/.local/share/litellm/venv/bin/python`.

Before deployment, run `python -m unittest -v test_schedule` using the service
interpreter and confirm no port-4000 connections or inference requests are
active. Back up the runtime script, install the candidate atomically, restart
only the LAN proxy, and verify service health and authentication.

## Verification

- Linux service interpreter: weekday start/end, weekend, winter/summer UTC
  conversion, and spring DST transition cases passed.
- Middleware: blocked/allowed socket peers and spoofed X-Forwarded-For checks
  passed across models, chat completions, and metrics routes.
- Activation: no established LAN connections; inference processing count zero.
- After restart: service active, unauthenticated `/v1/models` returns 401,
  local `/metrics` returns successfully.
- No end-to-end request originating from 192.168.86.2 was made; blocked-IP
  behavior was verified through middleware tests.

## Rollback

Copy the preserved file below over the runtime script and restart the LAN
proxy after checking for active requests:

`/home/helios/.local/share/litellm-lan-auth-proxy/litellm_lan_auth_proxy.py.bak-scheduled-block-20261013T140207Z`

The backup removes the scheduled restriction and preserves bearer authentication.