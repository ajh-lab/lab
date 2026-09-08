import math
from collections.abc import Mapping
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
    """Parse an RFC3339 string with explicit timezone and return a datetime in UTC."""
    if not isinstance(s, str):
        raise ValueError("observed_at must be a string")
    # Try parsing with fromisoformat (Python 3.11 supports Z)
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
    if not isinstance(event, Mapping):
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
    if fix not in VALID_FIXES:
        raise ValueError(f"fix must be one of {VALID_FIXES}")

    # latitude, longitude
    latitude = event["latitude"]
    longitude = event["longitude"]

    if fix == "none":
        if latitude is not None or longitude is not None:
            raise ValueError("For fix 'none', latitude and longitude must both be None")
        lat = None
        lon = None
    else:
        if isinstance(latitude, bool) or isinstance(longitude, bool):
            raise ValueError("latitude and longitude must be finite real numbers for positioned fixes")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError("latitude and longitude must be finite real numbers for positioned fixes")
        if math.isnan(latitude) or math.isinf(latitude):
            raise ValueError("latitude must be finite")
        if math.isnan(longitude) or math.isinf(longitude):
            raise ValueError("longitude must be finite")
        lat = float(latitude)
        lon = float(longitude)
        if lat < -90 or lat > 90:
            raise ValueError("latitude must be in [-90, 90]")
        if lon < -180 or lon > 180:
            raise ValueError("longitude must be in [-180, 180]")

    return {
        "asset_id": asset_id,
        "sequence": sequence,
        "observed_at": dt_utc,
        "fix": fix,
        "latitude": lat,
        "longitude": lon,
    }


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Compute haversine distance in meters between two points given in degrees."""
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
    max_gap_seconds = _validate_max_gap_seconds(max_gap_seconds)

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
    segments = []

    for asset_id in sorted(assets.keys()):
        asset_events = assets[asset_id]
        # Sort by (observed_at, sequence)
        asset_events.sort(key=lambda e: (e["observed_at"], e["sequence"]))

        # Process events to form segments
        current_segment = []  # list of positioned events in the current segment

        for ev in asset_events:
            if ev["fix"] == "none":
                # Close the active segment
                if current_segment:
                    segments.append(_build_segment(asset_id, current_segment))
                    current_segment = []
                continue

            # Positioned event
            if not current_segment:
                # Start a new segment
                current_segment.append(ev)
            else:
                prev_ev = current_segment[-1]
                elapsed = (ev["observed_at"] - prev_ev["observed_at"]).total_seconds()
                if elapsed <= max_gap_seconds:
                    # Continue the segment
                    current_segment.append(ev)
                else:
                    # Close the current segment and start a new one
                    segments.append(_build_segment(asset_id, current_segment))
                    current_segment = [ev]

        # Close any remaining segment
        if current_segment:
            segments.append(_build_segment(asset_id, current_segment))

    # Sort segments by (asset_id, start_at)
    segments.sort(key=lambda s: (s["asset_id"], s["start_at"]))

    return segments


def _build_segment(asset_id, segment_events):
    """Build a segment dictionary from a list of positioned events."""
    # All events in the segment are positioned (fix != "none")
    first = segment_events[0]
    last = segment_events[-1]

    start_at = _format_utc(first["observed_at"])
    end_at = _format_utc(last["observed_at"])
    sample_count = len(segment_events)

    start_position = (first["latitude"], first["longitude"])
    end_position = (last["latitude"], last["longitude"])

    # Compute total distance
    total_distance = 0.0
    for i in range(1, len(segment_events)):
        prev = segment_events[i - 1]
        curr = segment_events[i]
        d = _haversine_distance(prev["latitude"], prev["longitude"], curr["latitude"], curr["longitude"])
        total_distance += d

    # Compute max speed
    max_speed = 0.0
    for i in range(1, len(segment_events)):
        prev = segment_events[i - 1]
        curr = segment_events[i]
        d = _haversine_distance(prev["latitude"], prev["longitude"], curr["latitude"], curr["longitude"])
        elapsed = (curr["observed_at"] - prev["observed_at"]).total_seconds()
        if elapsed > 0:
            speed = d / elapsed
            if speed > max_speed:
                max_speed = speed

    # Best fix
    best_fix = "2d"
    best_rank = -1
    for ev in segment_events:
        rank = FIX_RANK[ev["fix"]]
        if rank > best_rank:
            best_rank = rank
            best_fix = ev["fix"]

    return {
        "asset_id": asset_id,
        "start_at": start_at,
        "end_at": end_at,
        "sample_count": sample_count,
        "start_position": start_position,
        "end_position": end_position,
        "distance_m": round(total_distance, 3),
        "max_speed_mps": round(max_speed, 3),
        "best_fix": best_fix,
    }
