"""Pure-Python telemetry reducer."""

import math
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone


_EARTH_RADIUS_M = 6371008.8
_FIX_RANKS = {"2d": 0, "3d": 1, "rtk_float": 2, "rtk_fixed": 3}
_VALID_FIXES = frozenset(_FIX_RANKS)
_REQUIRED_KEYS = frozenset(
    ("asset_id", "sequence", "observed_at", "fix", "latitude", "longitude")
)


def _is_finite_real(value):
    """Return True if value is a finite real number (int or float), not bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def _parse_rfc3339_utc(ts_str):
    """Parse an RFC 3339 timestamp string with explicit timezone to a UTC datetime.

    Accepts 'Z' suffix. Raises ValueError on malformed input or missing offset.
    Returns an aware datetime in UTC.
    """
    if not isinstance(ts_str, str):
        raise ValueError("observed_at must be a string")

    s = ts_str.strip()
    # Replace trailing Z with +00:00 for fromisoformat compatibility (Python 3.11 handles 'Z' natively)
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as exc:
        raise ValueError(f"malformed observed_at: {ts_str!r}") from exc

    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("observed_at must contain an explicit timezone")

    # RFC 3339 requires offset to be hours and minutes only (no seconds)
    off = dt.utcoffset()
    total_seconds = int(off.total_seconds())
    if total_seconds % 60 != 0:
        raise ValueError("observed_at timezone offset must have whole-minute precision")

    return dt.astimezone(timezone.utc)


def _format_utc(dt):
    """Format a UTC datetime with exactly six fractional digits followed by Z."""
    # Ensure microsecond precision; if microseconds are 0, still show .000000
    us = dt.microsecond
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{us:06d}Z"


def _validate_event(event):
    """Validate a single event mapping and return normalized tuple.

    Returns (asset_id, sequence, observed_at_utc_dt, fix, lat_float_or_None, lon_float_or_None).
    Raises ValueError on any malformation.
    """
    if not isinstance(event, Mapping) or set(event.keys()) != _REQUIRED_KEYS:
        raise ValueError("event must contain exactly the six required keys")

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
    obs_dt = _parse_rfc3339_utc(event["observed_at"])

    # fix
    fix = event["fix"]
    if not isinstance(fix, str) or fix not in _VALID_FIXES:
        raise ValueError("fix must be one of none, 2d, 3d, rtk_float, rtk_fixed")

    lat_raw = event["latitude"]
    lon_raw = event["longitude"]

    if fix == "none":
        if lat_raw is not None or lon_raw is not None:
            raise ValueError("for none fix, latitude and longitude must be None")
        lat_val = None
        lon_val = None
    else:
        if not _is_finite_real(lat_raw) or not _is_finite_real(lon_raw):
            raise ValueError(
                "latitude/longitude must be finite real numbers for positioned fixes"
            )
        lat_val = float(lat_raw)
        lon_val = float(lon_raw)
        if not (-90.0 <= lat_val <= 90.0):
            raise ValueError("latitude out of range [-90, 90]")
        if not (-180.0 <= lon_val <= 180.0):
            raise ValueError("longitude out of range [-180, 180]")

    return (asset_id, seq, obs_dt, fix, lat_val, lon_val)


def _haversine_m(lat1, lon1, lat2, lon2):
    """Compute great-circle distance in metres using haversine formula.

    Handles antimeridian correctly via standard spherical trigonometry.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return _EARTH_RADIUS_M * c


def reconstruct_tracks(events, max_gap_seconds):
    """Reconstruct track segments from telemetry events.

    Args:
        events: iterable of event mappings (not mutated).
        max_gap_seconds: finite non-negative real; bool invalid.

    Returns:
        List of segment dicts sorted by (asset_id, start_at).
    """
    # Validate max_gap_seconds
    if isinstance(max_gap_seconds, bool) or not _is_finite_real(max_gap_seconds):
        raise ValueError("max_gap_seconds must be a finite non-negative real number")
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be non-negative")

    # Materialize and validate all events; deduplicate by (asset_id, sequence)
    seen = {}  # key -> normalized tuple
    for ev in events:
        norm = _validate_event(ev)
        asset_id, seq = norm[0], norm[1]
        key = (asset_id, seq)

        if key not in seen:
            seen[key] = norm
        else:
            existing = seen[key]
            # Compare all six normalized values for identity
            if existing != norm:
                raise ValueError(
                    f"duplicate event with differing values for {key}"
                )

    # Group by asset_id
    assets = {}  # asset_id -> list of normalized events
    for (asset_id, _seq), norm in seen.items():
        assets.setdefault(asset_id, []).append(norm)

    segments_out = []

    def _flush_segment(current_segment_events):
        if not current_segment_events:
            return None
        seg_evts = current_segment_events
        n = len(seg_evts)

        start_dt = seg_evts[0][2]
        end_dt = seg_evts[-1][2]
        sample_count = n

        # Positions
        first_lat, first_lon = seg_evts[0][4], seg_evts[0][5]
        last_lat, last_lon = seg_evts[-1][4], seg_evts[-1][5]

        if n == 1:
            dist_m = 0.0
            max_speed = 0.0
        else:
            total_dist = 0.0
            max_spd = 0.0
            for i in range(1, n):
                prev_dt = seg_evts[i - 1][2]
                cur_dt = seg_evts[i][2]
                elapsed_s = (cur_dt - prev_dt).total_seconds()
                d = _haversine_m(
                    seg_evts[i - 1][4], seg_evts[i - 1][5],
                    seg_evts[i][4], seg_evts[i][5]
                )
                total_dist += d
                if elapsed_s > 0:
                    spd = d / elapsed_s
                    if spd > max_spd:
                        max_spd = spd
            dist_m = total_dist
            max_speed = max_spd

        # Best fix in segment
        best_fix_rank = -1
        best_fix_str = "2d"  # lowest rank default; but all are positioned so at least one exists
        for e in seg_evts:
            r = _FIX_RANKS[e[3]]
            if r > best_fix_rank:
                best_fix_rank = r
                best_fix_str = e[3]

        return {
            "asset_id": asset_id,
            "start_at": _format_utc(start_dt),
            "end_at": _format_utc(end_dt),
            "sample_count": sample_count,
            "start_position": (first_lat, first_lon),
            "end_position": (last_lat, last_lon),
            "distance_m": round(dist_m, 3),
            "max_speed_mps": round(max_speed, 3),
            "best_fix": best_fix_str,
        }

    for asset_id in sorted(assets):
        evts = assets[asset_id]
        # Sort by (observed_at, sequence)
        evts.sort(key=lambda e: (e[2], e[1]))

        current_segment_events = []  # list of positioned events in active segment

        for norm in evts:
            fix = norm[3]
            if fix == "none":
                # Closes active segment; not included
                seg_dict = _flush_segment(current_segment_events)
                if seg_dict is not None:
                    segments_out.append(seg_dict)
                current_segment_events = []
            else:
                dt = norm[2]

                if not current_segment_events:
                    # Start new segment
                    current_segment_events.append(norm)
                else:
                    prev_dt = current_segment_events[-1][2]
                    elapsed_s = (dt - prev_dt).total_seconds()
                    # New segment if dt <= prev_dt OR elapsed > max_gap
                    if dt <= prev_dt or elapsed_s > max_gap_seconds:
                        seg_dict = _flush_segment(current_segment_events)
                        if seg_dict is not None:
                            segments_out.append(seg_dict)
                        current_segment_events = []
                    current_segment_events.append(norm)

        # Flush any remaining active segment at end of asset's events
        seg_dict = _flush_segment(current_segment_events)
        if seg_dict is not None:
            segments_out.append(seg_dict)

    # Sort final segments by (asset_id, start_at). Since we processed assets in sorted order
    # and within each asset segments are produced chronologically, the list is already
    # sorted. But to be safe:
    segments_out.sort(key=lambda s: (s["asset_id"], s["start_at"]))

    return segments_out
