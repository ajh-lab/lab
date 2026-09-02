"""Pure-Python telemetry reducer."""

import math
from datetime import datetime, timezone


def _parse_rfc3339_utc(value):
    """Parse an RFC 3339 string with explicit timezone into a UTC-aware datetime."""
    if not isinstance(value, str) or len(value) < 20:
        raise ValueError("observed_at must be a valid RFC 3339 string")

    # Normalize 'Z' to '+00:00' for fromisoformat compatibility.
    s = value.strip()
    if not s:
        raise ValueError("observed_at is empty")
    if s[-1] in ("z", "Z"):
        s = s[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(s)
    except (ValueError, TypeError):
        raise ValueError(f"invalid RFC 3339 timestamp: {value!r}") from None

    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("observed_at must contain an explicit timezone")

    return dt.astimezone(timezone.utc)


def _format_utc(dt):
    """Format a UTC datetime with exactly six fractional digits and 'Z'."""
    # Ensure microsecond precision.
    us = dt.microsecond
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{us:06d}Z"


def _validate_event(event):
    """Validate a single event mapping and return normalized tuple."""
    if not isinstance(event, dict):
        raise ValueError("event must be a mapping")

    required = {"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"}
    keys = set(event.keys())
    if keys != required:
        missing = required - keys
        extra = keys - required
        raise ValueError(f"event has wrong keys; missing={missing}, extra={extra}")

    # asset_id
    raw_asset = event["asset_id"]
    if not isinstance(raw_asset, str):
        raise ValueError("asset_id must be a string")
    asset_id = raw_asset.strip()
    if not asset_id:
        raise ValueError("asset_id is empty after stripping")

    # sequence
    seq = event["sequence"]
    if isinstance(seq, bool) or not isinstance(seq, int):
        raise ValueError("sequence must be a non-negative integer (bool invalid)")
    if seq < 0:
        raise ValueError("sequence must be non-negative")

    # observed_at
    dt_utc = _parse_rfc3339_utc(event["observed_at"])

    # fix
    fix = event["fix"]
    valid_fixes = {"none", "2d", "3d", "rtk_float", "rtk_fixed"}
    if not isinstance(fix, str) or fix not in valid_fixes:
        raise ValueError("invalid fix value")

    # latitude / longitude
    lat_raw = event["latitude"]
    lon_raw = event["longitude"]

    if fix == "none":
        if lat_raw is not None or lon_raw is not None:
            raise ValueError("for none fix, both coordinates must be None")
        lat = None
        lon = None
    else:
        for name, val in (("latitude", lat_raw), ("longitude", lon_raw)):
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(f"{name} must be a finite real number")
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"{name} is not finite")

        lat = float(lat_raw)
        lon = float(lon_raw)

        if not (-90.0 <= lat <= 90.0):
            raise ValueError("latitude out of range [-90, 90]")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError("longitude out of range [-180, 180]")

    return (asset_id, seq, dt_utc, fix, lat, lon)


def _haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in metres with antimeridian handling."""
    r = 6371008.8

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    # Handle longitude difference across the antimeridian.
    dlon_deg = lon2 - lon1
    if dlon_deg > 180.0:
        dlon_deg -= 360.0
    elif dlon_deg < -180.0:
        dlon_deg += 360.0

    dphi = phi2 - phi1
    dlambda = math.radians(dlon_deg)

    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return r * c


def _best_fix_rank(fix):
    """Return rank for best-fix comparison; higher is better."""
    ranks = {"2d": 0, "3d": 1, "rtk_float": 2, "rtk_fixed": 3}
    if fix in ranks:
        return ranks[fix]
    # 'none' should not appear in positioned segments, but guard anyway.
    return -1


def reconstruct_tracks(events, max_gap_seconds):
    """Reconstruct track segments from telemetry events."""

    # Validate max_gap_seconds
    if isinstance(max_gap_seconds, bool) or not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite non-negative real number")
    gap = float(max_gap_seconds)
    if math.isnan(gap) or math.isinf(gap):
        raise ValueError("max_gap_seconds is not finite")
    if gap < 0.0:
        raise ValueError("max_gap_seconds is negative")

    # Materialize and validate all events; deduplicate by (asset_id, sequence).
    seen = {}  # key -> normalized tuple
    for ev in events:
        norm = _validate_event(ev)
        asset_id, seq, dt_utc, fix, lat, lon = norm
        key = (asset_id, seq)

        if key not in seen:
            seen[key] = norm
        else:
            existing = seen[key]
            # Compare all six normalized values.
            if (existing[0], existing[1], existing[2].timestamp(),
                    existing[3], existing[4], existing[5]) != \
               (norm[0], norm[1], dt_utc.timestamp(), fix, lat, lon):
                raise ValueError(f"duplicate key {key} with differing values")

    # Group by asset_id.
    assets = {}  # asset_id -> list of normalized events
    for norm in seen.values():
        asset_id = norm[0]
        if asset_id not in assets:
            assets[asset_id] = []
        assets[asset_id].append(norm)

    segments = []

    for asset_id, evts in assets.items():
        # Sort by (observed_at, sequence).
        evts.sort(key=lambda e: (e[2], e[1]))

        active_segment = None  # list of positioned events in current segment

        def _flush(segment_events):
            if not segment_events:
                return
            n = len(segment_events)
            start_dt = segment_events[0][2]
            end_dt = segment_events[-1][2]
            start_lat, start_lon = segment_events[0][4], segment_events[0][5]
            end_lat, end_lon = segment_events[-1][4], segment_events[-1][5]

            total_dist = 0.0
            max_speed = 0.0
            best_rank = -1
            for ev in segment_events:
                r = _best_fix_rank(ev[3])
                if r > best_rank:
                    best_rank = r

            # Find the fix with highest rank; tie-break by first occurrence? 
            # Spec says "Best-fix" — we pick the one with highest rank. If multiple, any is fine as long as deterministic. We'll track which fix string corresponds to max rank.
            best_fix_str = None
            for ev in segment_events:
                r = _best_fix_rank(ev[3])
                if r > best_rank or (r == best_rank and best_fix_str is None):
                    # Actually we already computed best_rank above; let's just re-scan properly.
                    pass

            # Re-do cleanly: find max rank, then pick the fix string for that rank from first occurrence in segment order? 
            # The spec doesn't specify tie-breaking beyond "best". We'll use the highest-ranked fix present. If multiple have same rank (impossible since ranks are unique per fix type), no issue.
            best_fix_str = None
            max_r = -1
            for ev in segment_events:
                r = _best_fix_rank(ev[3])
                if r > max_r:
                    max_r = r
                    best_fix_str = ev[3]

            # Compute distances and speeds.
            total_dist = 0.0
            max_speed = 0.0
            for i in range(1, n):
                prev_dt = segment_events[i - 1][2]
                curr_dt = segment_events[i][2]
                elapsed_s = (curr_dt - prev_dt).total_seconds()

                dlat_prev = segment_events[i - 1][4]
                dlon_prev = segment_events[i - 1][5]
                dlat_curr = segment_events[i][4]
                dlon_curr = segment_events[i][5]

                dist = _haversine(dlat_prev, dlon_prev, dlat_curr, dlon_curr)
                total_dist += dist

                if elapsed_s > 0.0:
                    speed = dist / elapsed_s
                    if speed > max_speed:
                        max_speed = speed

            segments.append({
                "asset_id": asset_id,
                "start_at": _format_utc(start_dt),
                "end_at": _format_utc(end_dt),
                "sample_count": n,
                "start_position": (float(start_lat), float(start_lon)),
                "end_position": (float(end_lat), float(end_lon)),
                "distance_m": round(total_dist, 3),
                "max_speed_mps": round(max_speed, 3),
                "best_fix": best_fix_str,
            })

        for ev in evts:
            asset_id_ev, seq, dt_utc, fix, lat, lon = ev

            if fix == "none":
                # Closes active segment.
                _flush(active_segment)
                active_segment = None
            else:
                # Positioned event.
                if active_segment is None or len(active_segment) == 0:
                    active_segment = [ev]
                else:
                    prev_ev = active_segment[-1]
                    prev_dt = prev_ev[2]

                    # Start new segment if timestamp <= previous positioned event's timestamp,
                    # OR elapsed > max_gap_seconds.
                    if dt_utc <= prev_dt or (dt_utc - prev_dt).total_seconds() > gap:
                        _flush(active_segment)
                        active_segment = [ev]
                    else:
                        active_segment.append(ev)

        # Flush any remaining active segment at end of asset's events.
        _flush(active_segment)
        active_segment = None  # not strictly needed but for clarity

    # Sort segments by (asset_id, start_at).
    segments.sort(key=lambda s: (s["asset_id"], s["start_at"]))

    return segments
