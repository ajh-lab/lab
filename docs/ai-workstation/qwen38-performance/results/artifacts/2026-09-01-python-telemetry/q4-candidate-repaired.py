from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone


def _parse_rfc3339_utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("observed_at must be a string")
    s = value.strip()

    # RFC 3339 requires an explicit offset (Z or ±hh:mm). Python's fromisoformat is too permissive.
    suffix = None
    body = s
    if s.endswith(("Z", "z")):
        body, suffix = s[:-1], "Z"
    else:
        # Find the last 'T' to separate date and time; offset must be at end of string after time part.
        t_idx = s.rfind("T")
        if t_idx == -1 or not (t_idx + 2 < len(s)):
            raise ValueError(f"invalid RFC3339 timestamp: {value!r}")
        # Offset starts right after the seconds/fractional part of time.
        # Time format is HH:MM[:SS[.fff...]]. We need to find where offset begins.
        # Simpler heuristic for valid strings ending in ±hh:mm or ±hmm (RFC3339 allows no colon? No, RFC 3339 says "±HH:MM". Python fromisoformat accepts both but we must reject seconds).
        # Let's scan backwards to find the offset start.
        i = len(s) - 1
        while i > t_idx and s[i] not in "+-":
            i -= 1
        if i <= t_idx:
            raise ValueError(f"invalid RFC3339 timestamp (missing explicit timezone): {value!r}")
        
        offset_str = s[i:]
        body = s[:i]
        
        # Validate offset format strictly: ±HH:MM or ±HMM? 
        # Spec says "explicit timezone". Standard is +hh:mm. Python 3.11 fromisoformat accepts +hmm too but RFC3339 grammar is [+-]HH:MM.
        # The failure case was '+00:00:30'. This implies the offset part contained a colon and extra digits, or it was parsed as time with seconds? 
        # Actually if string ends in +00:00:30, fromisoformat might interpret :30 as fractional seconds of the *time* before the Z/offset? No.
        # If we split at '+', offset is '00:00:30'. This has two colons. Invalid for HH:MM.
        
        if len(offset_str) < 5:
            raise ValueError(f"invalid RFC3339 timestamp (bad offset): {value!r}")
        sign = offset_str[0]
        rest = offset_str[1:]
        
        # Must be exactly HH:MM or HMM? Let's stick to strict HH:MM as per common interpretation of "hours and minutes". 
        # If it contains a colon, format must be XX:XX. Length 5 (HH:MM).
        if ":" in rest:
            parts = rest.split(":")
            if len(parts) != 2 or len(parts[0]) != 2 or len(parts[1]) != 2:
                raise ValueError(f"invalid RFC3339 timestamp (bad offset format): {value!r}")
            # Check digits
            if not parts[0].isdigit() or not parts[1].isdigit():
                raise ValueError(f"invalid RFC3339 timestamp (non-digit in offset): {value!r}")
        else:
            # No colon. Must be 4 digits HHMM? Or 2/3? 
            # To be safe and strict, if no colon, it's likely invalid for standard "hh:mm" expectation unless we accept compact. 
            # Given the failure was about *extra* precision (seconds), rejecting non-colon or wrong length is safer.
            if len(rest) != 4:
                raise ValueError(f"invalid RFC3339 timestamp (bad offset format): {value!r}")
            if not rest.isdigit():
                raise ValueError(f"invalid RFC3339 timestamp (non-digit in offset): {value!r}")

    # Now parse body with fromisoformat. Body should be YYYY-MM-DDTHH:MM[:SS[.fff]]
    try:
        dt = datetime.fromisoformat(body)
    except ValueError as exc:
        raise ValueError(f"invalid RFC3339 timestamp: {value!r}") from exc

    if suffix == "Z":
        offset_delta = timedelta(0)
    else:
        # Reconstruct offset for validation/application. We already validated format above, but let's ensure it parses to a valid time delta.
        sign_char = s[len(body)]  # The + or - char we split on
        rest_str = s[len(body)+1:]
        
        if ":" in rest_str:
            h_part, m_part = rest_str.split(":")
            hours = int(h_part)
            minutes = int(m_part)
        else:
            hours = int(rest_str[:2])
            minutes = int(rest_str[2:])
            
        offset_delta = timedelta(hours=hours, minutes=minutes)
        if sign_char == "-":
            offset_delta = -offset_delta

    # Apply offset to get UTC. 
    # fromisoformat(body) gives naive datetime (since we stripped the Z/offset).
    local_dt = dt.replace(tzinfo=None)  # Ensure naive for calculation, though it is already if body had no tz
    utc_dt = local_dt - offset_delta
    
    return utc_dt


def _format_utc(dt: datetime) -> str:
    micro = dt.microsecond
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{micro:06d}Z"


def _validate_event(ev):
    if not isinstance(ev, Mapping):
        raise ValueError("event must be a mapping")

    required = {"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"}
    keys = set(ev.keys())
    if keys != required:
        missing = required - keys
        extra = keys - required
        raise ValueError(f"event has wrong keys; missing={missing}, extra={extra}")

    asset_id_raw = ev["asset_id"]
    if not isinstance(asset_id_raw, str):
        raise ValueError("asset_id must be a string")
    asset_id = asset_id_raw.strip()
    if not asset_id:
        raise ValueError("asset_id must be non-empty after stripping")

    seq = ev["sequence"]
    if isinstance(seq, bool) or not isinstance(seq, int):
        raise ValueError("sequence must be an integer (bool invalid)")
    if seq < 0:
        raise ValueError("sequence must be non-negative")

    obs_raw = ev["observed_at"]
    dt_utc = _parse_rfc3339_utc(obs_raw)

    fix = ev["fix"]
    valid_fixes = {"none", "2d", "3d", "rtk_float", "rtk_fixed"}
    if not isinstance(fix, str) or fix not in valid_fixes:
        raise ValueError("invalid fix value")

    lat_raw = ev["latitude"]
    lon_raw = ev["longitude"]

    if fix == "none":
        if lat_raw is not None or lon_raw is not None:
            raise ValueError("for none fix, latitude and longitude must be None")
        lat = None
        lon = None
    else:
        for name, val in (("latitude", lat_raw), ("longitude", lon_raw)):
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(f"{name} must be a real number")
            v = float(val)
            if not math.isfinite(v):
                raise ValueError(f"{name} must be finite")

        lat = float(lat_raw)
        lon = float(lon_raw)
        if not (-90.0 <= lat <= 90.0):
            raise ValueError("latitude out of range [-90, 90]")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError("longitude out of range [-180, 180]")

    return (asset_id, seq, dt_utc, fix, lat, lon)


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371008.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    
    # Antimeridian-safe delta longitude
    dlon_raw = lon2 - lon1
    if dlon_raw > 180.0:
        dlon = dlon_raw - 360.0
    elif dlon_raw < -180.0:
        dlon = dlon_raw + 360.0
    else:
        dlon = dlon_raw
        
    dlamb = math.radians(dlon)

    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlamb / 2.0) ** 2)
    
    # Clamp to [0, 1] for numerical stability in sqrt(1-a)
    a = max(0.0, min(1.0, a))
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _best_fix_rank(fix: str) -> int:
    order = {"2d": 0, "3d": 1, "rtk_float": 2, "rtk_fixed": 3}
    if fix == "none":
        return -1
    return order[fix]


def reconstruct_tracks(events, max_gap_seconds):
    # Validate max_gap_seconds: finite non-negative real; bool invalid
    if isinstance(max_gap_seconds, bool) or not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite non-negative real number")
    gap = float(max_gap_seconds)
    if not math.isfinite(gap):
        raise ValueError("max_gap_seconds must be finite")
    if gap < 0.0:
        raise ValueError("max_gap_seconds must be non-negative")

    # Materialize and validate all events; deduplicate by (asset_id, sequence)
    seen = {}  # key -> normalized tuple
    for ev in events:
        norm = _validate_event(ev)
        asset_id, seq, dt_utc, fix, lat, lon = norm
        key = (asset_id, seq)
        if key in seen:
            prev = seen[key]
            # Compare all six normalized values; timestamps must be identical too
            if prev != norm:
                raise ValueError("duplicate (asset_id, sequence) with differing values")
        else:
            seen[key] = norm

    # Group by asset_id
    assets = {}  # asset_id -> list of events
    for norm in seen.values():
        asset_id, seq, dt_utc, fix, lat, lon = norm
        assets.setdefault(asset_id, []).append(norm)

    segments_out = []

    for asset_id in sorted(assets.keys()):
        evs = assets[asset_id]
        # Sort by (observed_at, sequence)
        evs.sort(key=lambda e: (e[2], e[1]))  # dt_utc is comparable; seq int

        current_segment = []  # list of positioned events in this segment

        def flush_segment():
            nonlocal current_segment
            if not current_segment:
                return
            n = len(current_segment)
            start_ev = current_segment[0]
            end_ev = current_segment[-1]
            start_at_dt = start_ev[2]
            end_at_dt = end_ev[2]

            total_dist = 0.0
            max_speed = 0.0
            
            # Determine best_fix label and rank in one pass? Or separate. 
            # We need the fix string with highest rank.
            max_rank_seen = -1
            best_label = None
            for e in current_segment:
                r = _best_fix_rank(e[3])
                if r > max_rank_seen:
                    max_rank_seen = r
                    best_label = e[3]

            if n > 1:
                prev = current_segment[0]
                for i in range(1, n):
                    cur = current_segment[i]
                    d = _haversine(prev[4], prev[5], cur[4], cur[5])
                    total_dist += d
                    dt_sec = (cur[2] - prev[2]).total_seconds()
                    if dt_sec > 0.0:
                        speed = d / dt_sec
                        if speed > max_speed:
                            max_speed = speed
                    # else elapsed zero -> but timestamps sorted; could be equal? 
                    # Condition for new segment is ts <= prev_ts. So within a valid segment, consecutive events must have strictly increasing timestamps.
                    # Thus dt_sec should always be > 0 if n>1 and logic holds. But just in case of floating point weirdness or same timestamp allowed by some edge interpretation? 
                    # Spec: "starts a new segment when ... its timestamp is less than or equal to the previous positioned event's timestamp".
                    # So strictly greater required for continuity. dt_sec > 0 guaranteed.
                    prev = cur

            segments_out.append({
                "asset_id": asset_id,
                "start_at": _format_utc(start_at_dt),
                "end_at": _format_utc(end_at_dt),
                "sample_count": n,
                "start_position": (float(start_ev[4]), float(start_ev[5])),
                "end_position": (float(end_ev[4]), float(end_ev[5])),
                "distance_m": round(total_dist, 3),
                "max_speed_mps": round(max_speed, 3),
                "best_fix": best_label,
            })

        for ev in evs:
            asset_id_e, seq_e, dt_utc, fix, lat, lon = ev
            if fix == "none":
                # Closes active segment; not included
                flush_segment()
                current_segment = []
            else:
                if not current_segment:
                    current_segment.append(ev)
                else:
                    prev_ev = current_segment[-1]
                    prev_dt = prev_ev[2]
                    
                    # Start new segment if ts <= prev_ts OR elapsed > max_gap
                    if dt_utc <= prev_dt:
                        flush_segment()
                        current_segment = [ev]
                    else:
                        elapsed = (dt_utc - prev_dt).total_seconds()
                        if elapsed > gap:
                            flush_segment()
                            current_segment = [ev]
                        else:
                            current_segment.append(ev)

        # End of asset events; flush any remaining open segment
        flush_segment()

    segments_out.sort(key=lambda s: (s["asset_id"], s["start_at"]))
    return segments_out
