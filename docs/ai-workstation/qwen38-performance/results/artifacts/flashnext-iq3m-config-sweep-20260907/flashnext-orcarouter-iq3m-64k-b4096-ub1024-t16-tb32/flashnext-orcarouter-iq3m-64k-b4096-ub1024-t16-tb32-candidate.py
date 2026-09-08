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
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Each event must be a mapping")
        expected_keys = {"asset_id", "sequence", "observed_at", "fix", "latitude", "longitude"}
        if set(event.keys()) != expected_keys:
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
            raise ValueError("observed_at must be a string")
        try:
            dt = datetime.fromisoformat(observed_at_str)
        except ValueError:
            raise ValueError("observed_at must be a valid RFC3339 string with explicit timezone")
        if dt.tzinfo is None:
            raise ValueError("observed_at must contain an explicit timezone")
        # Normalize to UTC
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
                raise ValueError("latitude and longitude must be finite real numbers, not bool")
            if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
                raise ValueError("latitude and longitude must be finite real numbers")
            if not math.isfinite(latitude) or not math.isfinite(longitude):
                raise ValueError("latitude and longitude must be finite")
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
    dedup_map = {}
    for ev in normalized_events:
        key = (ev["asset_id"], ev["sequence"])
        if key in dedup_map:
            existing = dedup_map[key]
            # Check if all six normalized values are identical
            if (existing["asset_id"] != ev["asset_id"] or
                existing["sequence"] != ev["sequence"] or
                existing["observed_at"] != ev["observed_at"] or
                existing["fix"] != ev["fix"] or
                existing["latitude"] != ev["latitude"] or
                existing["longitude"] != ev["longitude"]):
                raise ValueError("Duplicate (asset_id, sequence) with different values")
        else:
            dedup_map[key] = ev

    # Group by asset_id
    assets = defaultdict(list)
    for ev in dedup_map.values():
        assets[ev["asset_id"]].append(ev)

    # Process each asset
    segments = []
    for asset_id, evs in assets.items():
        # Sort by (observed_at, sequence)
        evs.sort(key=lambda e: (e["observed_at"], e["sequence"]))

        # Process events for this asset
        active_segment = None
        for ev in evs:
            if ev["fix"] == "none":
                # Close active segment
                if active_segment is not None:
                    segments.append(active_segment)
                    active_segment = None
                continue

            # Positioned event
            if active_segment is None:
                # Start new segment
                active_segment = {
                    "asset_id": asset_id,
                    "events": [ev],
                }
            else:
                prev_ev = active_segment["events"][-1]
                elapsed = (ev["observed_at"] - prev_ev["observed_at"]).total_seconds()
                if elapsed <= 0 or elapsed > max_gap_seconds:
                    # Close current segment and start new one
                    segments.append(active_segment)
                    active_segment = {
                        "asset_id": asset_id,
                        "events": [ev],
                    }
                else:
                    # Add to active segment
                    active_segment["events"].append(ev)

        # Close any remaining active segment
        if active_segment is not None:
            segments.append(active_segment)

    # Convert segments to output format
    results = []
    for seg in segments:
        evs = seg["events"]
        asset_id = seg["asset_id"]

        start_at = evs[0]["observed_at"]
        end_at = evs[-1]["observed_at"]
        sample_count = len(evs)

        start_lat = evs[0]["latitude"]
        start_lon = evs[0]["longitude"]
        end_lat = evs[-1]["latitude"]
        end_lon = evs[-1]["longitude"]

        # Compute distance and max speed
        total_distance = 0.0
        max_speed = 0.0

        for i in range(1, len(evs)):
            prev_ev = evs[i - 1]
            curr_ev = evs[i]

            lat1 = prev_ev["latitude"]
            lon1 = prev_ev["longitude"]
            lat2 = curr_ev["latitude"]
            lon2 = curr_ev["longitude"]

            dist = haversine(lat1, lon1, lat2, lon2)
            total_distance += dist

            elapsed = (curr_ev["observed_at"] - prev_ev["observed_at"]).total_seconds()
            if elapsed > 0:
                speed = dist / elapsed
                if speed > max_speed:
                    max_speed = speed

        # Determine best fix
        fix_rank = {"2d": 0, "3d": 1, "rtk_float": 2, "rtk_fixed": 3}
        best_fix = None
        best_rank = -1
        for ev in evs:
            r = fix_rank[ev["fix"]]
            if r > best_rank:
                best_rank = r
                best_fix = ev["fix"]

        # Format timestamps
        start_at_str = format_utc(start_at)
        end_at_str = format_utc(end_at)

        results.append({
            "asset_id": asset_id,
            "start_at": start_at_str,
            "end_at": end_at_str,
            "sample_count": sample_count,
            "start_position": (start_lat, start_lon),
            "end_position": (end_lat, end_lon),
            "distance_m": round(total_distance, 3),
            "max_speed_mps": round(max_speed, 3),
            "best_fix": best_fix,
        })

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
    # dt is already in UTC
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    microsecond = dt.microsecond

    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}.{microsecond:06d}Z"
