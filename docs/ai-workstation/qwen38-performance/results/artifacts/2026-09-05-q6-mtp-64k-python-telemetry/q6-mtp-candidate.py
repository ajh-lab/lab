"""Pure-Python telemetry reducer."""

import math
from datetime import datetime, timezone


def _parse_rfc3339_utc(value):
    """Parse an RFC 3339 string with explicit timezone into a UTC-aware datetime."""
    if not isinstance(value, str) or len(value) < 20:
        raise ValueError("observed_at must be a valid RFC 3339 string")

    # Normalize 'Z' to '+00:00' for fromisoformat compatibility (Python 3.11 handles Z natively, but keep explicit).
    s = value.strip()
    if not s:
        raise ValueError("observed_at must be non-empty")

    try:
        # Python 3.11+ datetime.fromisoformat supports 'Z' and fractional seconds of any length.
        dt = datetime.fromisoformat(s)
    except (ValueError, TypeError):
        raise ValueError(f"invalid RFC 3339 timestamp: {value!r}")

    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("observed_at must contain an explicit timezone")

    return dt.astimezone(timezone.utc)


def _format_utc(dt):
    """Format a UTC datetime with exactly six fractional digits followed by Z."""
    # Ensure microsecond precision; truncate if needed (fromisoformat gives up to 6).
    us = dt.microsecond
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{us:06d}Z"


def _validate_event(event):
    """Validate a single event mapping and return normalized tuple."""
    if not isinstance(event, dict):
        raise ValueError("event must be a mapping")

    required_keys = {"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"}
    keys = set(event.keys())
    if keys != required_keys:
        missing = required_keys - keys
        extra = keys - required_keys
        raise ValueError(f"event has wrong keys; missing={missing}, extra={extra}")

    # asset_id
    raw_asset = event["asset_id"]
    if not isinstance(raw_asset, str):
        raise ValueError("asset_id must be a string")
    asset_id = raw_asset.strip()
    if not asset_id:
        raise ValueError("asset_id must be non-empty after stripping")

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
            raise ValueError("for none fix, latitude and longitude must be None")
        lat = None
        lon = None
    else:
        for name, val in (("latitude", lat_raw), ("longitude", lon_raw)):
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(f"{name} must be a finite real number")
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"{name} must be finite")

        lat = float(lat_raw)
        lon = float(lon_raw)

        if not (-90.0 <= lat <= 90.0):
            raise ValueError("latitude out of range [-90, 90]")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError("longitude out of range [-180, 180]")

    return (asset_id, seq, dt_utc, fix, lat, lon)


def _haversine(lat1, lon1, lat2, lon2):
    """Haversine distance in metres. Earth radius 6371008.8 m."""
    r = 6371008.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)

    # Handle antimeridian: take the shortest angular difference in longitude.
    dlambda_raw = math.radians(lon2 - lon1)
    if abs(dlambda_raw) > math.pi:
        dlambda = 2 * math.pi - abs(dlambda_raw)
        sign = 1 if dlambda_raw < 0 else -1
        # Actually, haversine uses sin^2 so sign doesn't matter for the squared term.
        # But we need correct delta lambda in [-pi, pi].
        dlambda = math.radians(lon2 - lon1)
        while dlambda > math.pi:
            dlambda -= 2 * math.pi
        while dlambda < -math.pi:
            dlambda += 2 * math.pi

    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
    c = 2 * r * math.asin(math.sqrt(a))
    return c


def _best_fix_rank(fix):
    """Return rank for best-fix comparison (higher is better)."""
    ranks = {"2d": 1, "3d": 2, "rtk_float": 3, "rtk_fixed": 4}
    if fix == "none":
        return -1
    return ranks.get(fix, -1)


def reconstruct_tracks(events, max_gap_seconds):
    """Reconstruct tracks from telemetry events."""

    # Validate max_gap_seconds
    if isinstance(max_gap_seconds, bool) or not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite non-negative real number")
    mg = float(max_gap_seconds)
    if math.isnan(mg) or math.isinf(mg):
        raise ValueError("max_gap_seconds must be finite")
    if mg < 0:
        raise ValueError("max_gap_seconds must be non-negative")

    # Materialize and validate all events, deduplicate.
    seen = {}  # (asset_id, sequence) -> normalized tuple
    for ev in events:
        norm = _validate_event(ev)
        key = (norm[0], norm[1])
        if key in seen:
            existing = seen[key]
            if existing != norm:
                raise ValueError("duplicate event with differing values")
        else:
            seen[key] = norm

    # Group by asset_id.
    assets = {}  # asset_id -> list of normalized events
    for (asset_id, seq, dt_utc, fix, lat, lon) in seen.values():
        if asset_id not in assets:
            assets[asset_id] = []
        assets[asset_id].append((dt_utc, seq, fix, lat, lon))

    # Process each asset.
    all_segments = []
    for asset_id in sorted(assets.keys()):
        evts = assets[asset_id]
        # Sort by (observed_at, sequence)
        evts.sort(key=lambda x: (x[0], x[1]))

        segments = _build_segments(asset_id, evts, mg)
        all_segments.extend(segments)

    # Final sort by (asset_id, start_at). Since we already grouped and sorted assets,
    # and within each asset segments are in chronological order, this should be fine.
    # But to be safe:
    all_segments.sort(key=lambda s: (s["asset_id"], s["start_at"]))

    return all_segments


def _build_segments(asset_id, evts, max_gap):
    """Build list of segment dicts for one asset's sorted events."""
    segments = []
    active = None  # dict with current segment state

    def close_segment():
        nonlocal active
        if active is not None:
            segs.append(_finalize_segment(asset_id, active))
            active = None

    for dt_utc, seq, fix, lat, lon in evts:
        if fix == "none":
            # Closes the active segment; none event itself is not included.
            close_segment()
            continue

        # Positioned event (lat/lon are floats)
        if active is None:
            # Start new segment
            active = {
                "start_dt": dt_utc,
                "end_dt": dt_utc,
                "samples": 1,
                "start_lat": lat,
                "start_lon": lon,
                "end_lat": lat,
                "end_lon": lon,
                "distance_m": 0.0,
                "max_speed": 0.0,
                "best_fix_rank": _best_fix_rank(fix),
            }
        else:
            prev_dt = active["end_dt"]
            elapsed = (dt_utc - prev_dt).total_seconds()

            # Check if we should start a new segment:
            # 1. timestamp <= previous positioned event's timestamp -> new segment
            #    Wait, the spec says "when its timestamp is less than or equal to the previous
            #    positioned event's timestamp". Since events are sorted by (observed_at, sequence),
            #    if timestamps are equal but sequences differ, we still have dt_utc >= prev_dt.
            #    Actually re-reading: "starts a new segment when ... its timestamp is less than or
            #    equal to the previous positioned event's timestamp". This means if dt_utc <= prev_dt,
            #    start new. But since sorted by (observed_at, sequence), dt_utc >= prev_dt always holds
            #    for consecutive events in the same asset after sorting... unless there are duplicate
            #    timestamps with different sequences. In that case dt_utc == prev_dt is possible.
            if elapsed <= 0:
                close_segment()
                active = {
                    "start_dt": dt_utc,
                    "end_dt": dt_utc,
                    "samples": 1,
                    "start_lat": lat,
                    "start_lon": lon,
                    "end_lat": lat,
                    "end_lon": lon,
                    "distance_m": 0.0,
                    "max_speed": 0.0,
                    "best_fix_rank": _best_fix_rank(fix),
                }
            elif elapsed > max_gap:
                close_segment()
                active = {
                    "start_dt": dt_utc,
                    "end_dt": dt_utc,
                    "samples": 1,
                    "start_lat": lat,
                    "start_lon": lon,
                    "end_lat": lat,
                    "end_lon": lon,
                    "distance_m": 0.0,
                    "max_speed": 0.0,
                    "best_fix_rank": _best_fix_rank(fix),
                }
            else:
                # Continue current segment
                dist = _haversine(active["end_lat"], active["end_lon"], lat, lon)
                speed = dist / elapsed if elapsed > 0 else 0.0

                active["distance_m"] += dist
                if speed > active["max_speed"]:
                    active["max_speed"] = speed
                active["samples"] += 1
                active["end_dt"] = dt_utc
                active["end_lat"] = lat
                active["end_lon"] = lon

                rank = _best_fix_rank(fix)
                if rank > active["best_fix_rank"]:
                    active["best_fix_rank"] = rank

    close_segment()
    return segments


def _finalize_segment(asset_id, state):
    """Convert internal segment state to output dict."""
    start_at_str = _format_utc(state["start_dt"])
    end_at_str = _format_utc(state["end_dt"])

    dist_rounded = round(state["distance_m"], 3)
    speed_rounded = round(state["max_speed"], 3)

    # Determine best fix string from rank.
    rank_to_fix = {1: "2d", 2: "3d", 3: "rtk_float", 4: "rtk_fixed"}
    best_fix_str = rank_to_fix.get(state["best_fix_rank"], "none")

    return {
        "asset_id": asset_id,
        "start_at": start_at_str,
        "end_at": end_at_str,
        "sample_count": state["samples"],
        "start_position": (state["start_lat"], state["start_lon"]),
        "end_position": (state["end_lat"], state["end_lon"]),
        "distance_m": dist_rounded,
        "max_speed_mps": speed_rounded,
        "best_fix": best_fix_str,
    }
