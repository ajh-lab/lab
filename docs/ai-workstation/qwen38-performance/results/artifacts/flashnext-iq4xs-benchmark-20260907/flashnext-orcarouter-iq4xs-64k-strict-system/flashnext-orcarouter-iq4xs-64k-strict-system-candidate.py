import math
from datetime import datetime, timezone
from collections import defaultdict
from typing import Any, Iterable, Mapping

# Constants
EARTH_RADIUS_M = 6371008.8
FIX_RANKS = {"2d": 1, "3d": 2, "rtk_float": 3, "rtk_fixed": 4}
VALID_FIXES = {"none", "2d", "3d", "rtk_float", "rtk_fixed"}
REQUIRED_KEYS = frozenset({"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"})


def _validate_max_gap_seconds(max_gap_seconds: Any) -> float:
    """Validate max_gap_seconds is a finite, non-negative real number (bool invalid)."""
    if isinstance(max_gap_seconds, bool):
        raise ValueError("max_gap_seconds must not be a bool")
    if not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a real number")
    if math.isnan(max_gap_seconds) or math.isinf(max_gap_seconds):
        raise ValueError("max_gap_seconds must be finite")
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be non-negative")
    return float(max_gap_seconds)


def _parse_rfc3339_utc(s: str) -> datetime:
    """Parse an RFC3339 string with explicit timezone and normalize to UTC."""
    if not isinstance(s, str):
        raise ValueError("observed_at must be a string")
    # Try parsing with fromisoformat (Python 3.11 supports Z)
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        raise ValueError(f"Invalid RFC3339 timestamp: {s}")
    if dt.tzinfo is None:
        raise ValueError(f"Timestamp must have explicit timezone: {s}")
    # Normalize to UTC
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc


def _validate_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize a single event. Returns a normalized dict."""
    if not isinstance(event, Mapping):
        raise ValueError("Event must be a mapping")

    # Check exact keys
    event_keys = set(event.keys())
    if event_keys != REQUIRED_KEYS:
        raise ValueError(f"Event has incorrect keys: {event_keys}")

    # asset_id: non-empty string after stripping
    asset_id = event["asset_id"]
    if not isinstance(asset_id, str):
        raise ValueError("asset_id must be a string")
    asset_id = asset_id.strip()
    if not asset_id:
        raise ValueError("asset_id must be non-empty after stripping")

    # sequence: non-negative int; bool invalid
    sequence = event["sequence"]
    if isinstance(sequence, bool):
        raise ValueError("sequence must not be a bool")
    if not isinstance(sequence, int):
        raise ValueError("sequence must be an int")
    if sequence < 0:
        raise ValueError("sequence must be non-negative")

    # observed_at: RFC3339 with explicit timezone, normalize to UTC
    observed_at = event["observed_at"]
    dt_utc = _parse_rfc3339_utc(observed_at)

    # fix: one of the valid fixes
    fix = event["fix"]
    if not isinstance(fix, str):
        raise ValueError("fix must be a string")
    if fix not in VALID_FIXES:
        raise ValueError(f"Invalid fix value: {fix}")

    # latitude, longitude
    latitude = event["latitude"]
    longitude = event["longitude"]

    if fix == "none":
        if latitude is not None or longitude is not None:
            raise ValueError("For fix 'none', latitude and longitude must be None")
        lat_val = None
        lon_val = None
    else:
        # Both must be finite real numbers (bool invalid)
        if isinstance(latitude, bool) or isinstance(longitude, bool):
            raise ValueError("latitude and longitude must not be bool")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError("latitude and longitude must be real numbers")
        if math.isnan(latitude) or math.isinf(latitude):
            raise ValueError("latitude must be finite")
        if math.isnan(longitude) or math.isinf(longitude):
            raise ValueError("longitude must be finite")
        if not (-90 <= latitude <= 90):
            raise ValueError("latitude out of range")
        if not (-180 <= longitude <= 180):
            raise ValueError("longitude out of range")
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


def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute haversine distance in meters between two lat/lon points."""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_M * c


def _format_utc(dt: datetime) -> str:
    """Format a UTC datetime with exactly six fractional digits followed by Z."""
    # dt is already in UTC
    # Format: YYYY-MM-DDTHH:MM:SS.ffffffZ
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _best_fix(fixes: list[str]) -> str:
    """Return the best fix from a list of fix strings."""
    best = None
    best_rank = -1
    for fix in fixes:
        rank = FIX_RANKS[fix]
        if rank > best_rank:
            best_rank = rank
            best = fix
    return best


def reconstruct_tracks(events: Iterable[Mapping[str, Any]], max_gap_seconds: float) -> list[dict[str, Any]]:
    """Reconstruct tracks from telemetry events."""
    # Validate max_gap_seconds
    max_gap = _validate_max_gap_seconds(max_gap_seconds)

    # Materialize and validate all events
    validated_events = []
    for event in events:
        validated = _validate_event(event)
        validated_events.append(validated)

    # Deduplicate using (asset_id, sequence)
    # Two occurrences collapse only when all six normalized values are identical
    seen: dict[tuple[str, int], dict[str, Any]] = {}
    for ev in validated_events:
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
                raise ValueError(f"Duplicate key with different values: {key}")
        else:
            seen[key] = ev

    # Group by asset_id
    assets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in seen.values():
        assets[ev["asset_id"]].append(ev)

    # Process each asset independently
    all_segments = []

    for asset_id in sorted(assets.keys()):
        asset_events = assets[asset_id]
        # Sort by (observed_at, sequence)
        asset_events.sort(key=lambda e: (e["observed_at"], e["sequence"]))

        # Process events to form segments
        current_segment: list[dict[str, Any]] = []

        for ev in asset_events:
            if ev["fix"] == "none":
                # A none event closes the active segment and is not included
                if current_segment:
                    segment = _build_segment(current_segment)
                    all_segments.append(segment)
                    current_segment = []
                continue

            # Positioned event
            if not current_segment:
                # Start a new segment
                current_segment.append(ev)
            else:
                prev_ev = current_segment[-1]
                prev_dt = prev_ev["observed_at"]
                curr_dt = ev["observed_at"]

                # Calculate elapsed time in seconds
                elapsed = (curr_dt - prev_dt).total_seconds()

                # Start new segment if:
                # - timestamp is less than or equal to previous positioned event's timestamp
                # - elapsed time is strictly greater than max_gap_seconds
                if elapsed <= 0 or elapsed > max_gap:
                    # Close current segment
                    segment = _build_segment(current_segment)
                    all_segments.append(segment)
                    # Start new segment
                    current_segment = [ev]
                else:
                    # Add to current segment
                    current_segment.append(ev)

        # Close any remaining segment
        if current_segment:
            segment = _build_segment(current_segment)
            all_segments.append(segment)

    # Sort segments by (asset_id, start_at)
    all_segments.sort(key=lambda s: (s["asset_id"], s["start_at"]))

    return all_segments


def _build_segment(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a segment dictionary from a list of positioned events."""
    if not events:
        raise ValueError("Cannot build segment from empty list")

    asset_id = events[0]["asset_id"]
    start_at = events[0]["observed_at"]
    end_at = events[-1]["observed_at"]
    sample_count = len(events)

    start_position = (events[0]["latitude"], events[0]["longitude"])
    end_position = (events[-1]["latitude"], events[-1]["longitude"])

    # Compute distance and speed
    total_distance = 0.0
    max_speed = 0.0

    for i in range(1, len(events)):
        prev_ev = events[i - 1]
        curr_ev = events[i]

        lat1, lon1 = prev_ev["latitude"], prev_ev["longitude"]
        lat2, lon2 = curr_ev["latitude"], curr_ev["longitude"]

        dist = _haversine_distance_m(lat1, lon1, lat2, lon2)
        total_distance += dist

        elapsed = (curr_ev["observed_at"] - prev_ev["observed_at"]).total_seconds()
        if elapsed > 0:
            speed = dist / elapsed
            if speed > max_speed:
                max_speed = speed

    # Round to three decimal places
    distance_m = round(total_distance, 3)
    max_speed_mps = round(max_speed, 3)

    # Best fix
    fixes = [ev["fix"] for ev in events]
    best_fix = _best_fix(fixes)

    return {
        "asset_id": asset_id,
        "start_at": _format_utc(start_at),
        "end_at": _format_utc(end_at),
        "sample_count": sample_count,
        "start_position": start_position,
        "end_position": end_position,
        "distance_m": distance_m,
        "max_speed_mps": max_speed_mps,
        "best_fix": best_fix,
    }
