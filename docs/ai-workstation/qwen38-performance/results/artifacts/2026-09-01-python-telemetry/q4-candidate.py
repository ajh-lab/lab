from __future__ import annotations

import math
from datetime import datetime, timezone


def _parse_rfc3339_utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("observed_at must be a string")
    s = value.strip()
    # RFC 3339 requires explicit offset; accept Z or +hh:mm / -hh:mm (seconds optional per common usage? spec says explicit timezone)
    # Python fromisoformat in 3.11 handles 'Z' and offsets with colon, but not without seconds if present? It does handle fractional seconds up to any digits.
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid RFC3339 timestamp: {value!r}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("observed_at must contain an explicit timezone")
    return dt.astimezone(timezone.utc)


def _format_utc(dt: datetime) -> str:
    # Exactly six fractional digits followed by Z
    micro = dt.microsecond
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{micro:06d}Z"


def _validate_event(ev, max_gap_seconds):  # noqa: ARG001 (max_gap not used per-event)
    if not isinstance(ev, dict):
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
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _best_fix_rank(fix: str) -> int:
    order = {"2d": 0, "3d": 1, "rtk_float": 2, "rtk_fixed": 3}
    if fix == "none":
        # Should not appear in positioned segments, but just in case rank lowest? Spec says best-fix from those four. none events are excluded.
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
        norm = _validate_event(ev, gap)
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
            best_rank = -1
            for e in current_segment:
                r = _best_fix_rank(e[3])
                if r > best_rank:
                    best_rank = r

            # Find the fix string corresponding to best_rank (highest rank)
            # We need actual fix label; pick from events with that rank. Since ranks map uniquely, we can reverse-map or just track during iteration.
            # Simpler: recompute by scanning for max rank and taking first such fix? But multiple fixes could share same rank? No, each fix has unique rank among the four. So best_fix is determined by highest rank present.
            # Let's compute properly: iterate to find max rank and corresponding fix label (any event with that rank; they all have same fix string for a given rank).

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
                    # else elapsed zero -> but timestamps sorted; could be equal? If same timestamp, gap logic would have split unless <= prev ts... actually "less than or equal to previous positioned event's timestamp" starts new segment. So within a segment, each next ts is strictly greater than prev? Not necessarily: condition says start new if ts <= prev_ts. So in-segment consecutive events must have ts > prev_ts. Thus dt_sec > 0 always for n>1.
                    prev = cur

            # Determine best_fix label
            max_rank_seen = -1
            best_label = None
            for e in current_segment:
                r = _best_fix_rank(e[3])
                if r > max_rank_seen:
                    max_rank_seen = r
                    best_label = e[3]

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
                    elapsed = (dt_utc - prev_dt).total_seconds()
                    # Start new segment if ts <= prev_ts OR elapsed > max_gap
                    if dt_utc <= prev_dt or elapsed > gap:
                        flush_segment()
                        current_segment = [ev]
                    else:
                        current_segment.append(ev)

        # End of asset events; flush any remaining open segment
        flush_segment()

    segments_out.sort(key=lambda s: (s["asset_id"], s["start_at"]))
    return segments_out
