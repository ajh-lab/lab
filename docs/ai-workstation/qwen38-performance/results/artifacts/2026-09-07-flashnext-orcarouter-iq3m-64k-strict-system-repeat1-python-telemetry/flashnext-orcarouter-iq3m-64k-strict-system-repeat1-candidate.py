import math
from datetime import datetime, timezone
from collections import defaultdict
from typing import Any, Iterable, Mapping, List, Dict, Tuple, Optional, Union

# Constants
EARTH_RADIUS_M = 6371008.8
FIX_RANKS = {"2d": 1, "3d": 2, "rtk_float": 3, "rtk_fixed": 4}
VALID_FIXES = {"none", "2d", "3d", "rtk_float", "rtk_fixed"}
REQUIRED_KEYS = frozenset({"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"})


def _validate_max_gap_seconds(max_gap_seconds: Any) -> float:
    if isinstance(max_gap_seconds, bool):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if not math.isfinite(max_gap_seconds):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    return float(max_gap_seconds)


def _parse_rfc3339_utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("observed_at must be an RFC3339 string")
    # Try parsing with fromisoformat (Python 3.11 supports Z)
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"observed_at is not a valid RFC3339 string: {value}")
    if dt.tzinfo is None:
        raise ValueError("observed_at must contain an explicit timezone")
    # Normalize to UTC
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc


def _validate_event(event: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(event, Mapping):
        raise ValueError("Each event must be a mapping")
    keys = set(event.keys())
    if keys != REQUIRED_KEYS:
        raise ValueError(f"Event has incorrect keys: {keys}")

    asset_id = event["asset_id"]
    if not isinstance(asset_id, str):
        raise ValueError("asset_id must be a string")
    asset_id = asset_id.strip()
    if not asset_id:
        raise ValueError("asset_id must be non-empty after stripping")

    sequence = event["sequence"]
    if isinstance(sequence, bool):
        raise ValueError("sequence must be a non-negative int")
    if not isinstance(sequence, int):
        raise ValueError("sequence must be a non-negative int")
    if sequence < 0:
        raise ValueError("sequence must be a non-negative int")

    observed_at = _parse_rfc3339_utc(event["observed_at"])

    fix = event["fix"]
    if not isinstance(fix, str):
        raise ValueError("fix must be a string")
    if fix not in VALID_FIXES:
        raise ValueError(f"fix must be one of {VALID_FIXES}")

    latitude = event["latitude"]
    longitude = event["longitude"]

    if fix == "none":
        if latitude is not None or longitude is not None:
            raise ValueError("For fix 'none', latitude and longitude must be None")
        lat_val = None
        lon_val = None
    else:
        if latitude is None or longitude is None:
            raise ValueError(f"For fix '{fix}', latitude and longitude must be finite real numbers")
        if isinstance(latitude, bool) or isinstance(longitude, bool):
            raise ValueError("latitude and longitude must be finite real numbers")
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            raise ValueError("latitude and longitude must be finite real numbers")
        if not math.isfinite(latitude) or not math.isfinite(longitude):
            raise ValueError("latitude and longitude must be finite real numbers")
        if not (-90 <= latitude <= 90):
            raise ValueError("latitude must be in [-90, 90]")
        if not (-180 <= longitude <= 180):
            raise ValueError("longitude must be in [-180, 180]")
        lat_val = float(latitude)
        lon_val = float(longitude)

    return {
        "asset_id": asset_id,
        "sequence": sequence,
        "observed_at": observed_at,
        "fix": fix,
        "latitude": lat_val,
        "longitude": lon_val,
    }


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


def _format_utc(dt: datetime) -> str:
    # Format with exactly six fractional digits followed by Z
    # dt is already in UTC
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def reconstruct_tracks(events: Iterable[Mapping[str, Any]], max_gap_seconds: Any) -> List[Dict[str, Any]]:
    max_gap = _validate_max_gap_seconds(max_gap_seconds)

    # Materialize and validate all events
    validated_events: List[Dict[str, Any]] = []
    for event in events:
        validated_events.append(_validate_event(event))

    # Deduplicate using (asset_id, sequence)
    seen: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for ev in validated_events:
        key = (ev["asset_id"], ev["sequence"])
        if key in seen:
            existing = seen[key]
            # Check if all six normalized values are identical
            if (
                existing["asset_id"] != ev["asset_id"]
                or existing["sequence"] != ev["sequence"]
                or existing["observed_at"] != ev["observed_at"]
                or existing["fix"] != ev["fix"]
                or existing["latitude"] != ev["latitude"]
                or existing["longitude"] != ev["longitude"]
            ):
                raise ValueError(f"Duplicate key {key} with different values")
        else:
            seen[key] = ev

    # Group by asset_id
    assets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in seen.values():
        assets[ev["asset_id"]].append(ev)

    # Process each asset
    segments: List[Dict[str, Any]] = []

    for asset_id, asset_events in assets.items():
        # Sort by (observed_at, sequence)
        asset_events.sort(key=lambda e: (e["observed_at"], e["sequence"]))

        # Process events to form segments
        current_segment: Optional[List[Dict[str, Any]]] = None
        current_segment_events: List[Dict[str, Any]] = []

        for ev in asset_events:
            if ev["fix"] == "none":
                # Close active segment
                if current_segment is not None:
                    segments.append(_build_segment(current_segment_events))
                    current_segment = None
                    current_segment_events = []
                continue

            # Positioned event
            if current_segment is None:
                # Start new segment
                current_segment = [ev]
                current_segment_events = [ev]
            else:
                prev_ev = current_segment_events[-1]
                elapsed = (ev["observed_at"] - prev_ev["observed_at"]).total_seconds()
                if elapsed <= 0 or elapsed > max_gap:
                    # Close current segment and start new one
                    segments.append(_build_segment(current_segment_events))
                    current_segment = [ev]
                    current_segment_events = [ev]
                else:
                    current_segment_events.append(ev)

        # Close any remaining segment
        if current_segment is not None:
            segments.append(_build_segment(current_segment_events))

    # Sort segments by (asset_id, start_at)
    segments.sort(key=lambda s: (s["asset_id"], s["start_at"]))

    return segments


def _build_segment(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not events:
        raise ValueError("Segment cannot be empty")

    asset_id = events[0]["asset_id"]
    start_at = events[0]["observed_at"]
    end_at = events[-1]["observed_at"]
    sample_count = len(events)

    start_position = (events[0]["latitude"], events[0]["longitude"])
    end_position = (events[-1]["latitude"], events[-1]["longitude"])

    # Compute distance and max speed
    distance_m = 0.0
    max_speed_mps = 0.0

    if sample_count > 1:
        for i in range(1, len(events)):
            prev_ev = events[i - 1]
            curr_ev = events[i]
            lat1, lon1 = prev_ev["latitude"], prev_ev["longitude"]
            lat2, lon2 = curr_ev["latitude"], curr_ev["longitude"]
            dist = _haversine(lat1, lon1, lat2, lon2)
            distance_m += dist
            elapsed = (curr_ev["observed_at"] - prev_ev["observed_at"]).total_seconds()
            if elapsed > 0:
                speed = dist / elapsed
                if speed > max_speed_mps:
                    max_speed_mps = speed

    # Best fix
    best_fix = "none"
    best_rank = 0
    for ev in events:
        rank = FIX_RANKS[ev["fix"]]
        if rank > best_rank:
            best_rank = rank
            best_fix = ev["fix"]

    return {
        "asset_id": asset_id,
        "start_at": _format_utc(start_at),
        "end_at": _format_utc(end_at),
        "sample_count": sample_count,
        "start_position": start_position,
        "end_position": end_position,
        "distance_m": round(distance_m, 3),
        "max_speed_mps": round(max_speed_mps, 3),
        "best_fix": best_fix,
    }
