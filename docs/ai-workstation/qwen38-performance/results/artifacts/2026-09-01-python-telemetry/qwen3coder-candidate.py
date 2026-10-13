import datetime
import math
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Iterator

EARTH_RADIUS = 6371008.8
FIX_RANK = {"none": 0, "2d": 1, "3d": 2, "rtk_float": 3, "rtk_fixed": 4}


def reconstruct_tracks(events: Iterator[Dict[str, Any]], max_gap_seconds: float) -> List[Dict[str, Any]]:
    if not isinstance(max_gap_seconds, (int, float)) or max_gap_seconds < 0 or not math.isfinite(max_gap_seconds):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")

    # Materialize and validate all events
    event_list = []
    seen_keys = set()
    for i, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"Event {i} is not a mapping")
        if len(event) != 6:
            raise ValueError(f"Event {i} must have exactly 6 keys")
        keys = set(event.keys())
        if keys != {"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"}:
            raise ValueError(f"Event {i} has incorrect keys: {sorted(keys)}")
        seen_keys.update(keys)

        # Validate asset_id
        asset_id = event["asset_id"]
        if not isinstance(asset_id, str):
            raise ValueError(f"Event {i} asset_id must be a string")
        asset_id = asset_id.strip()
        if not asset_id:
            raise ValueError(f"Event {i} asset_id must be non-empty after stripping")

        # Validate sequence
        sequence = event["sequence"]
        if not isinstance(sequence, int) or sequence < 0:
            raise ValueError(f"Event {i} sequence must be a non-negative integer")
        if isinstance(sequence, bool):
            raise ValueError(f"Event {i} sequence must not be bool")

        # Validate observed_at
        observed_at_str = event["observed_at"]
        if not isinstance(observed_at_str, str):
            raise ValueError(f"Event {i} observed_at must be a string")
        try:
            observed_at = datetime.datetime.fromisoformat(observed_at_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Event {i} observed_at is not valid RFC3339")
        if observed_at.tzinfo is None:
            raise ValueError(f"Event {i} observed_at must have timezone")
        observed_at = observed_at.astimezone(datetime.timezone.utc)

        # Validate fix
        fix = event["fix"]
        if fix not in FIX_RANK:
            raise ValueError(f"Event {i} fix must be one of none, 2d, 3d, rtk_float, rtk_fixed")

        # Validate coordinates
        lat = event["latitude"]
        lon = event["longitude"]
        if fix == "none":
            if lat is not None or lon is not None:
                raise ValueError(f"Event {i} latitude and longitude must be None for fix 'none'")
        else:
            if not isinstance(lat, (int, float)) or not math.isfinite(lat) or lat < -90 or lat > 90:
                raise ValueError(f"Event {i} latitude must be a finite number in [-90, 90]")
            if not isinstance(lon, (int, float)) or not math.isfinite(lon) or lon < -180 or lon > 180:
                raise ValueError(f"Event {i} longitude must be a finite number in [-180, 180]")
            lat = float(lat)
            lon = float(lon)

        event_list.append({
            "asset_id": asset_id,
            "sequence": sequence,
            "observed_at": observed_at,
            "fix": fix,
            "latitude": lat,
            "longitude": lon
        })

    # Deduplicate using (asset_id, sequence)
    deduped = {}
    for event in event_list:
        key = (event["asset_id"], event["sequence"])
        if key in deduped:
            old = deduped[key]
            if not all(old[k] == event[k] for k in ["asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"]):
                raise ValueError(f"Duplicate key {key} with different values")
        else:
            deduped[key] = event

    # Group by asset_id
    asset_events = defaultdict(list)
    for event in deduped.values():
        asset_events[event["asset_id"]].append(event)

    # Process each asset
    segments = []
    for asset_id, events in asset_events.items():
        # Sort by (observed_at, sequence)
        events.sort(key=lambda e: (e["observed_at"], e["sequence"]))

        # Process events to form segments
        active_segment = None
        for event in events:
            if event["fix"] == "none":
                # Close active segment if exists
                if active_segment is not None:
                    segments.append(_finalize_segment(active_segment))
                    active_segment = None
                continue

            # Positioned event
            lat = event["latitude"]
            lon = event["longitude"]
            timestamp = event["observed_at"]

            # Start new segment if none active or gap too large or timestamp <= last
            start_new = active_segment is None
            if not start_new and timestamp <= active_segment["last_timestamp"]:
                start_new = True
            if not start_new and active_segment["last_timestamp"] is not None:
                gap = (timestamp - active_segment["last_timestamp"]).total_seconds()
                if gap > max_gap_seconds:
                    start_new = True

            if start_new:
                if active_segment is not None:
                    segments.append(_finalize_segment(active_segment))
                active_segment = {
                    "asset_id": asset_id,
                    "start_at": timestamp,
                    "end_at": timestamp,
                    "sample_count": 1,
                    "start_position": (lat, lon),
                    "end_position": (lat, lon),
                    "distance_m": 0.0,
                    "max_speed_mps": 0.0,
                    "best_fix": event["fix"],
                    "last_timestamp": timestamp,
                    "positions": [(lat, lon)]
                }
            else:
                # Extend current segment
                assert active_segment is not None
                active_segment["end_at"] = timestamp
                active_segment["sample_count"] += 1
                active_segment["end_position"] = (lat, lon)
                active_segment["last_timestamp"] = timestamp
                active_segment["positions"].append((lat, lon))
                # Update best fix
                if FIX_RANK[event["fix"]] > FIX_RANK[active_segment["best_fix"]]:
                    active_segment["best_fix"] = event["fix"]

        # Finalize last segment if exists
        if active_segment is not None:
            segments.append(_finalize_segment(active_segment))

    # Sort segments
    segments.sort(key=lambda s: (s["asset_id"], s["start_at"]))

    return segments


def _finalize_segment(segment: Dict[str, Any]) -> Dict[str, Any]:
    # Compute distance and speed
    positions = segment["positions"]
    distance_m = 0.0
    max_speed_mps = 0.0

    if len(positions) > 1:
        prev_pos = positions[0]
        prev_time = segment["start_at"]
        for i in range(1, len(positions)):
            curr_pos = positions[i]
            curr_time = segment["start_at"] + datetime.timedelta(seconds=(i * 1.0))  # Placeholder
            # Recompute actual timestamps
            curr_time = segment["start_at"] + datetime.timedelta(
                seconds=(i * (segment["end_at"] - segment["start_at"]).total_seconds() / (len(positions) - 1))
            )
            # Actually, we need to compute the correct time for each position
            # Let's recompute properly
            total_seconds = (segment["end_at"] - segment["start_at"]).total_seconds()
            if total_seconds > 0:
                time_step = total_seconds / (len(positions) - 1)
                curr_time = segment["start_at"] + datetime.timedelta(seconds=i * time_step)
            else:
                curr_time = segment["start_at"]

            dist = _haversine_distance(prev_pos[0], prev_pos[1], curr_pos[0], curr_pos[1])
            distance_m += dist

            # Compute speed
            dt = (curr_time - prev_time).total_seconds()
            if dt > 0:
                speed = dist / dt
                max_speed_mps = max(max_speed_mps, speed)

            prev_pos = curr_pos
            prev_time = curr_time

    # Format timestamps
    def fmt_timestamp(dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return {
        "asset_id": segment["asset_id"],
        "start_at": fmt_timestamp(segment["start_at"]),
        "end_at": fmt_timestamp(segment["end_at"]),
        "sample_count": segment["sample_count"],
        "start_position": segment["start_position"],
        "end_position": segment["end_position"],
        "distance_m": round(distance_m, 3),
        "max_speed_mps": round(max_speed_mps, 3),
        "best_fix": segment["best_fix"]
    }


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Distance in meters
    return EARTH_RADIUS * c
