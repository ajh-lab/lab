import math
from datetime import datetime, timezone
from collections import defaultdict


def reconstruct_tracks(events, max_gap_seconds):
    if isinstance(max_gap_seconds, bool):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if not math.isfinite(max_gap_seconds) or max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")

    required_keys = {"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"}
    valid_fixes = {"none", "2d", "3d", "rtk_float", "rtk_fixed"}
    fix_rank = {"2d": 0, "3d": 1, "rtk_float": 2, "rtk_fixed": 3}

    # Materialize and validate all events
    normalized_events = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Each event must be a mapping")
        if set(event.keys()) != required_keys:
            raise ValueError("Event has incorrect keys")

        asset_id = event["asset_id"]
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a non-empty string")
        asset_id = asset_id.strip()
        if not asset_id:
            raise ValueError("asset_id must be a non-empty string")

        sequence = event["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int):
            raise ValueError("sequence must be a non-negative int")
        if sequence < 0:
            raise ValueError("sequence must be a non-negative int")

        observed_at = event["observed_at"]
        if not isinstance(observed_at, str):
            raise ValueError("observed_at must be an RFC3339 string")
        # Parse RFC3339 with explicit timezone
        try:
            dt = datetime.fromisoformat(observed_at)
        except ValueError:
            raise ValueError("observed_at must be a valid RFC3339 string")
        if dt.tzinfo is None:
            raise ValueError("observed_at must contain an explicit timezone")
        # Normalize to UTC
        dt_utc = dt.astimezone(timezone.utc)

        fix = event["fix"]
        if fix not in valid_fixes:
            raise ValueError("fix must be one of the valid fix types")

        latitude = event["latitude"]
        longitude = event["longitude"]

        if fix == "none":
            if latitude is not None or longitude is not None:
                raise ValueError("For fix 'none', latitude and longitude must be None")
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

        normalized_events.append({
            "asset_id": asset_id,
            "sequence": sequence,
            "observed_at": dt_utc,
            "fix": fix,
            "latitude": lat_val,
            "longitude": lon_val,
        })

    # Deduplicate using (asset_id, sequence)
    seen = {}
    for event in normalized_events:
        key = (event["asset_id"], event["sequence"])
        if key in seen:
            existing = seen[key]
            # Check if all six normalized values are identical
            if (existing["asset_id"] != event["asset_id"] or
                existing["sequence"] != event["sequence"] or
                existing["observed_at"] != event["observed_at"] or
                existing["fix"] != event["fix"] or
                existing["latitude"] != event["latitude"] or
                existing["longitude"] != event["longitude"]):
                raise ValueError("Duplicate (asset_id, sequence) with different values")
        else:
            seen[key] = event

    # Group by asset_id
    assets = defaultdict(list)
    for event in seen.values():
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
    for seg in segments:
        events = seg["events"]
        asset_id = seg["asset_id"]

        start_event = events[0]
        end_event = events[-1]

        start_at = start_event["observed_at"]
        end_at = end_event["observed_at"]

        sample_count = len(events)

        start_position = (start_event["latitude"], start_event["longitude"])
        end_position = (end_event["latitude"], end_event["longitude"])

        # Compute distance and max speed
        total_distance = 0.0
        max_speed = 0.0

        for i in range(1, len(events)):
            prev = events[i - 1]
            curr = events[i]

            lat1 = math.radians(prev["latitude"])
            lon1 = math.radians(prev["longitude"])
            lat2 = math.radians(curr["latitude"])
            lon2 = math.radians(curr["longitude"])

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = 6371008.8 * c

            total_distance += distance

            elapsed = (curr["observed_at"] - prev["observed_at"]).total_seconds()
            if elapsed > 0:
                speed = distance / elapsed
                if speed > max_speed:
                    max_speed = speed

        # Determine best fix
        best_fix = None
        best_rank = -1
        for event in events:
            rank = fix_rank[event["fix"]]
            if rank > best_rank:
                best_rank = rank
                best_fix = event["fix"]

        results.append({
            "asset_id": asset_id,
            "start_at": start_at,
            "end_at": end_at,
            "sample_count": sample_count,
            "start_position": start_position,
            "end_position": end_position,
            "distance_m": round(total_distance, 3),
            "max_speed_mps": round(max_speed, 3),
            "best_fix": best_fix,
        })

    # Sort by (asset_id, start_at)
    results.sort(key=lambda r: (r["asset_id"], r["start_at"]))

    # Format timestamps
    for r in results:
        r["start_at"] = r["start_at"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        r["end_at"] = r["end_at"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    return results
