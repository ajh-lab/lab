import math
from datetime import datetime, timezone
from collections import defaultdict


def reconstruct_tracks(events, max_gap_seconds):
    # Validate max_gap_seconds
    if isinstance(max_gap_seconds, bool):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if not math.isfinite(max_gap_seconds) or max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")

    # Materialize and validate all events
    normalized_events = []
    seen = {}

    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Each event must be a mapping")

        expected_keys = {"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"}
        event_keys = set(event.keys())
        if event_keys != expected_keys:
            raise ValueError("Event has incorrect keys")

        # Validate asset_id
        asset_id = event["asset_id"]
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")
        asset_id = asset_id.strip()
        if not asset_id:
            raise ValueError("asset_id must be non-empty after stripping")

        # Validate sequence
        sequence = event["sequence"]
        if isinstance(sequence, bool):
            raise ValueError("sequence must be a non-negative int")
        if not isinstance(sequence, int):
            raise ValueError("sequence must be a non-negative int")
        if sequence < 0:
            raise ValueError("sequence must be a non-negative int")

        # Validate observed_at
        observed_at_str = event["observed_at"]
        if not isinstance(observed_at_str, str):
            raise ValueError("observed_at must be an RFC3339 string")
        try:
            dt = datetime.fromisoformat(observed_at_str)
        except ValueError:
            raise ValueError("observed_at must be a valid RFC3339 string")
        if dt.tzinfo is None:
            raise ValueError("observed_at must contain an explicit timezone")
        dt_utc = dt.astimezone(timezone.utc)

        # Validate fix
        fix = event["fix"]
        valid_fixes = {"none", "2d", "3d", "rtk_float", "rtk_fixed"}
        if fix not in valid_fixes:
            raise ValueError("fix must be one of: none, 2d, 3d, rtk_float, rtk_fixed")

        # Validate latitude and longitude
        latitude = event["latitude"]
        longitude = event["longitude"]

        if fix == "none":
            if latitude is not None or longitude is not None:
                raise ValueError("For fix 'none', latitude and longitude must both be None")
            lat_val = None
            lon_val = None
        else:
            if latitude is None or longitude is None:
                raise ValueError("For positioned fixes, latitude and longitude must be finite real numbers")
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

        normalized_event = {
            "asset_id": asset_id,
            "sequence": sequence,
            "observed_at": dt_utc,
            "fix": fix,
            "latitude": lat_val,
            "longitude": lon_val,
        }

        key = (asset_id, sequence)
        if key in seen:
            existing = seen[key]
            # Check if all six normalized values are identical
            if (
                existing["asset_id"] != normalized_event["asset_id"]
                or existing["sequence"] != normalized_event["sequence"]
                or existing["observed_at"] != normalized_event["observed_at"]
                or existing["fix"] != normalized_event["fix"]
                or existing["latitude"] != normalized_event["latitude"]
                or existing["longitude"] != normalized_event["longitude"]
            ):
                raise ValueError("Duplicate (asset_id, sequence) with different values")
        else:
            seen[key] = normalized_event
            normalized_events.append(normalized_event)

    # Group by asset_id
    assets = defaultdict(list)
    for event in normalized_events:
        assets[event["asset_id"]].append(event)

    # Process each asset
    segments = []
    for asset_id, asset_events in assets.items():
        # Sort by (observed_at, sequence)
        asset_events.sort(key=lambda e: (e["observed_at"], e["sequence"]))

        # Process events to form segments
        current_segment = None
        for event in asset_events:
            if event["fix"] == "none":
                # Close active segment
                if current_segment is not None:
                    segments.append(current_segment)
                    current_segment = None
                continue

            # Positioned event
            if current_segment is None:
                # Start new segment
                current_segment = {
                    "asset_id": asset_id,
                    "events": [event],
                }
            else:
                prev_event = current_segment["events"][-1]
                prev_time = prev_event["observed_at"]
                curr_time = event["observed_at"]
                elapsed = (curr_time - prev_time).total_seconds()

                if elapsed <= 0 or elapsed > max_gap_seconds:
                    # Close current segment and start new one
                    segments.append(current_segment)
                    current_segment = {
                        "asset_id": asset_id,
                        "events": [event],
                    }
                else:
                    # Add to current segment
                    current_segment["events"].append(event)

        # Close any remaining segment
        if current_segment is not None:
            segments.append(current_segment)

    # Convert segments to output format
    results = []
    for segment in segments:
        asset_id = segment["asset_id"]
        events = segment["events"]

        if not events:
            continue

        start_at = events[0]["observed_at"]
        end_at = events[-1]["observed_at"]
        sample_count = len(events)

        start_lat = events[0]["latitude"]
        start_lon = events[0]["longitude"]
        end_lat = events[-1]["latitude"]
        end_lon = events[-1]["longitude"]

        # Compute distance and max speed
        total_distance = 0.0
        max_speed = 0.0

        for i in range(1, len(events)):
            prev_event = events[i - 1]
            curr_event = events[i]

            lat1 = prev_event["latitude"]
            lon1 = prev_event["longitude"]
            lat2 = curr_event["latitude"]
            lon2 = curr_event["longitude"]

            dist = haversine(lat1, lon1, lat2, lon2)
            total_distance += dist

            elapsed = (curr_event["observed_at"] - prev_event["observed_at"]).total_seconds()
            if elapsed > 0:
                speed = dist / elapsed
                if speed > max_speed:
                    max_speed = speed

        # Determine best fix
        fix_rank = {"2d": 0, "3d": 1, "rtk_float": 2, "rtk_fixed": 3}
        best_fix = None
        best_rank = -1
        for event in events:
            rank = fix_rank[event["fix"]]
            if rank > best_rank:
                best_rank = rank
                best_fix = event["fix"]

        # Format timestamps
        start_at_str = format_utc(start_at)
        end_at_str = format_utc(end_at)

        result = {
            "asset_id": asset_id,
            "start_at": start_at_str,
            "end_at": end_at_str,
            "sample_count": sample_count,
            "start_position": (start_lat, start_lon),
            "end_position": (end_lat, end_lon),
            "distance_m": round(total_distance, 3),
            "max_speed_mps": round(max_speed, 3),
            "best_fix": best_fix,
        }
        results.append(result)

    # Sort by (asset_id, start_at)
    results.sort(key=lambda r: (r["asset_id"], r["start_at"]))

    return results


def haversine(lat1, lon1, lat2, lon2):
    R = 6371008.8
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def format_utc(dt):
    # Format with exactly six fractional digits followed by Z
    dt_utc = dt.astimezone(timezone.utc)
    # Get the components
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day
    hour = dt_utc.hour
    minute = dt_utc.minute
    second = dt_utc.second
    microsecond = dt_utc.microsecond

    # Format with six fractional digits
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}.{microsecond:06d}Z"
