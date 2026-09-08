import math
from datetime import datetime, timezone
from collections import defaultdict

EARTH_RADIUS_M = 6371008.8

FIX_RANK = {
    "2d": 0,
    "3d": 1,
    "rtk_float": 2,
    "rtk_fixed": 3,
}

VALID_FIXES = {"none", "2d", "3d", "rtk_float", "rtk_fixed"}

REQUIRED_KEYS = {"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"}


def _validate_max_gap_seconds(max_gap_seconds):
    if isinstance(max_gap_seconds, bool):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if math.isnan(max_gap_seconds) or math.isinf(max_gap_seconds):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    return float(max_gap_seconds)


def _parse_rfc3339_utc(s):
    """Parse an RFC3339 string with explicit timezone, return datetime in UTC."""
    if not isinstance(s, str):
        raise ValueError("observed_at must be a string")
    # Try parsing with timezone info
    # RFC3339 requires timezone offset or Z
    # Python's fromisoformat in 3.11 can handle Z and offsets
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        raise ValueError(f"observed_at is not a valid RFC3339 string: {s}")
    if dt.tzinfo is None:
        raise ValueError(f"observed_at must contain an explicit timezone: {s}")
    # Convert to UTC
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc


def _validate_event(event):
    """Validate and normalize a single event. Returns a normalized dict."""
    if not isinstance(event, dict):
        raise ValueError("Each event must be a mapping")
    keys = set(event.keys())
    if keys != REQUIRED_KEYS:
        raise ValueError(f"Event has incorrect keys: {keys}")

    # asset_id
    asset_id = event["asset_id"]
    if not isinstance(asset_id, str):
        raise ValueError("asset_id must be a string")
    asset_id = asset_id.strip()
    if not asset_id:
        raise ValueError("asset_id must be non-empty after stripping")

    # sequence
    sequence = event["sequence"]
    if isinstance(sequence, bool):
        raise ValueError("sequence must be a non-negative int")
    if not isinstance(sequence, int):
        raise ValueError("sequence must be a non-negative int")
    if sequence < 0:
        raise ValueError("sequence must be a non-negative int")

    # observed_at
    observed_at = event["observed_at"]
    dt_utc = _parse_rfc3339_utc(observed_at)

    # fix
    fix = event["fix"]
    if not isinstance(fix, str):
        raise ValueError("fix must be a string")
    if fix not in VALID_FIXES:
        raise ValueError(f"fix must be one of {VALID_FIXES}")

    # latitude, longitude
    latitude = event["latitude"]
    longitude = event["longitude"]

    if fix == "none":
        if latitude is not None or longitude is not None:
            raise ValueError("For fix 'none', latitude and longitude must both be None")
        lat_val = None
        lon_val = None
    else:
        if latitude is None or longitude is None:
            raise ValueError(f"For fix '{fix}', latitude and longitude must both be finite real numbers")
        if isinstance(latitude, bool) or isinstance(longitude, bool):
            raise ValueError("latitude and longitude must be finite real numbers, not bool")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError("latitude and longitude must be finite real numbers")
        if math.isnan(latitude) or math.isinf(latitude):
            raise ValueError("latitude must be a finite real number")
        if math.isnan(longitude) or math.isinf(longitude):
            raise ValueError("longitude must be a finite real number")
        if not (-90 <= latitude <= 90):
            raise ValueError("latitude must be in [-90, 90]")
        if not (-180 <= longitude <= 180):
            raise ValueError("longitude must be in [-180, 180]")
        lat_val = float(latitude)
        lon_val = float(longitude)

    return {
        "asset_id": asset_id,
        "sequence": sequence,
        "observed_at": dt_utc,
        "fix": fix,
        "latitude": lat_val,
        "longitude": lon_val,
    }


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Compute haversine distance in meters between two points."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


def _format_utc(dt):
    """Format a UTC datetime with exactly six fractional digits followed by Z."""
    # dt is already in UTC
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{dt.microsecond:06d}Z"


def reconstruct_tracks(events, max_gap_seconds):
    # Validate max_gap_seconds
    max_gap = _validate_max_gap_seconds(max_gap_seconds)

    # Materialize and validate all events
    normalized_events = []
    for event in events:
        normalized = _validate_event(event)
        normalized_events.append(normalized)

    # Deduplicate using (asset_id, sequence)
    seen = {}
    for ev in normalized_events:
        key = (ev["asset_id"], ev["sequence"])
        if key in seen:
            existing = seen[key]
            # Check all six normalized values are identical
            if (existing["asset_id"] != ev["asset_id"] or
                existing["sequence"] != ev["sequence"] or
                existing["observed_at"] != ev["observed_at"] or
                existing["fix"] != ev["fix"] or
                existing["latitude"] != ev["latitude"] or
                existing["longitude"] != ev["longitude"]):
                raise ValueError(f"Duplicate key {key} with different values")
        else:
            seen[key] = ev

    # Group by asset_id
    assets = defaultdict(list)
    for ev in seen.values():
        assets[ev["asset_id"]].append(ev)

    # Process each asset independently
    all_segments = []

    for asset_id in sorted(assets.keys()):
        events_list = assets[asset_id]
        # Sort by (observed_at, sequence)
        events_list.sort(key=lambda e: (e["observed_at"], e["sequence"]))

        # Process events to form segments
        current_segment = []  # list of positioned events in current segment

        for ev in events_list:
            if ev["fix"] == "none":
                # Close active segment
                if current_segment:
                    segment = _build_segment(current_segment)
                    all_segments.append(segment)
                    current_segment = []
                # none event is not included in any segment
                continue

            # Positioned event
            if not current_segment:
                # Start new segment
                current_segment.append(ev)
            else:
                prev_ev = current_segment[-1]
                # Check if timestamp is less than or equal to previous positioned event's timestamp
                if ev["observed_at"] <= prev_ev["observed_at"]:
                    # Start new segment
                    if current_segment:
                        segment = _build_segment(current_segment)
                        all_segments.append(segment)
                    current_segment = [ev]
                else:
                    # Check elapsed time
                    elapsed = (ev["observed_at"] - prev_ev["observed_at"]).total_seconds()
                    if elapsed > max_gap:
                        # Start new segment
                        segment = _build_segment(current_segment)
                        all_segments.append(segment)
                        current_segment = [ev]
                    else:
                        # Continue current segment
                        current_segment.append(ev)

        # Close any remaining segment
        if current_segment:
            segment = _build_segment(current_segment)
            all_segments.append(segment)

    # Sort segments by (asset_id, start_at)
    all_segments.sort(key=lambda s: (s["asset_id"], s["start_at"]))

    return all_segments


def _build_segment(segment_events):
    """Build a segment dictionary from a list of positioned events."""
    if not segment_events:
        return None

    first = segment_events[0]
    last = segment_events[-1]

    # Compute total distance
    total_distance = 0.0
    max_speed = 0.0

    for i in range(1, len(segment_events)):
        prev_ev = segment_events[i - 1]
        curr_ev = segment_events[i]

        lat1 = prev_ev["latitude"]
        lon1 = prev_ev["longitude"]
        lat2 = curr_ev["latitude"]
        lon2 = curr_ev["longitude"]

        dist = _haversine_distance(lat1, lon1, lat2, lon2)
        total_distance += dist

        elapsed = (curr_ev["observed_at"] - prev_ev["observed_at"]).total_seconds()
        if elapsed > 0:
            speed = dist / elapsed
            if speed > max_speed:
                max_speed = speed

    # Best fix
    best_fix_rank = -1
    best_fix = None
    for ev in segment_events:
        rank = FIX_RANK[ev["fix"]]
        if rank > best_fix_rank:
            best_fix_rank = rank
            best_fix = ev["fix"]

    return {
        "asset_id": first["asset_id"],
        "start_at": _format_utc(first["observed_at"]),
        "end_at": _format_utc(last["observed_at"]),
        "sample_count": len(segment_events),
        "start_position": (first["latitude"], first["longitude"]),
        "end_position": (last["latitude"], last["longitude"]),
        "distance_m": round(total_distance, 3),
        "max_speed_mps": round(max_speed, 3),
        "best_fix": best_fix,
    }
