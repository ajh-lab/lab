import math
from datetime import datetime, timezone


def reconstruct_tracks(events, max_gap_seconds):
    # Validate max_gap_seconds: must be finite, non-negative real number; bool is invalid
    if isinstance(max_gap_seconds, bool) or not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if math.isnan(max_gap_seconds) or math.isinf(max_gap_seconds):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")

    # Materialize and validate all events
    normalized_events = []
    for event in events:
        expected_keys = {'asset_id', 'sequence', 'observed_at', 'fix', 'latitude', 'longitude'}

        try:
            actual_keys = set(event.keys())
        except AttributeError:
            raise ValueError("Each event must be a mapping with exactly six keys")

        if actual_keys != expected_keys:
            raise ValueError(f"Event has incorrect keys. Expected {expected_keys}, got {actual_keys}")

        # Validate asset_id
        asset_id_raw = event['asset_id']
        if not isinstance(asset_id_raw, str):
            raise ValueError("asset_id must be a non-empty string after stripping")
        asset_id = asset_id_raw.strip()
        if not asset_id:
            raise ValueError("asset_id must be a non-empty string after stripping")

        # Validate sequence
        seq = event['sequence']
        if isinstance(seq, bool) or not isinstance(seq, int):
            raise ValueError("sequence must be a non-negative integer; bool is invalid")
        if seq < 0:
            raise ValueError("sequence must be a non-negative integer")

        # Validate observed_at
        obs_raw = event['observed_at']
        if not isinstance(obs_raw, str):
            raise ValueError("observed_at must be an RFC3339 string with explicit timezone")

        try:
            dt = datetime.fromisoformat(obs_raw)
        except (ValueError, TypeError):
            raise ValueError(f"observed_at is not a valid RFC3339 timestamp: {obs_raw}")

        if dt.tzinfo is None:
            raise ValueError("observed_at must contain an explicit timezone")

        # Check for seconds in offset by inspecting the string representation of tzinfo or raw string logic
        # datetime.fromisoformat accepts offsets with seconds. We need to reject them unless they are 0?
        # The spec says "RFC3339 timezone offsets permit only hours and minutes".
        # Standard RFC3339 allows [+-]HH:MM[:SS[,.ffffff]]. However, the prompt explicitly states:
        # "observed_at='2026-01-01T00:00:00+00:00:30' was accepted... this must raise ValueError."
        # This implies we should reject offsets that have a seconds component, even if valid in some extended ISO formats.

        offset = dt.utcoffset()
        if offset is not None:
            total_seconds = int(offset.total_seconds())
            if total_seconds % 60 != 0:
                raise ValueError("observed_at timezone offset must be a multiple of one minute")

        # Normalize to UTC
        obs_dt = dt.astimezone(timezone.utc)

        # Validate fix
        fix_val = event['fix']
        valid_fixes = {'none', '2d', '3d', 'rtk_float', 'rtk_fixed'}
        if not isinstance(fix_val, str) or fix_val not in valid_fixes:
            raise ValueError(f"fix must be one of {valid_fixes}, got {fix_val}")

        # Validate latitude and longitude based on fix type
        lat = event['latitude']
        lon = event['longitude']

        if fix_val == 'none':
            if lat is not None or lon is not None:
                raise ValueError("For fix='none', both latitude and longitude must be None")
            norm_lat = None
            norm_lon = None
        else:
            # For other fixes, both must be finite real numbers (bool invalid)
            for coord_name, coord_val in [('latitude', lat), ('longitude', lon)]:
                if isinstance(coord_val, bool):
                    raise ValueError(f"{coord_name} cannot be a boolean")
                if not isinstance(coord_val, (int, float)):
                    raise ValueError(f"{coord_name} must be a finite real number for fix={fix_val}")
                if math.isnan(coord_val) or math.isinf(coord_val):
                    raise ValueError(f"{coord_name} must be a finite real number")

            norm_lat = float(lat)
            norm_lon = float(lon)

            # Validate ranges
            if not (-90 <= norm_lat <= 90):
                raise ValueError("latitude must be in [-90, 90]")
            if not (-180 <= norm_lon <= 180):
                raise ValueError("longitude must be in [-180, 180]")

        normalized_events.append({
            'asset_id': asset_id,
            'sequence': seq,
            'observed_at': obs_dt,
            'fix': fix_val,
            'latitude': norm_lat,
            'longitude': norm_lon,
        })

    # Deduplicate using (asset_id, sequence)
    dedup_map = {}  # key: (asset_id, sequence) -> normalized event data for comparison

    for ev in normalized_events:
        key = (ev['asset_id'], ev['sequence'])
        if key not in dedup_map:
            dedup_map[key] = {
                'observed_at': ev['observed_at'],
                'fix': ev['fix'],
                'latitude': ev['latitude'],
                'longitude': ev['longitude'],
            }
        else:
            existing = dedup_map[key]
            # Check if all six normalized values are identical
            if (existing['observed_at'] != ev['observed_at'] or
                existing['fix'] != ev['fix'] or
                existing['latitude'] != ev['latitude'] or
                existing['longitude'] != ev['longitude']):
                raise ValueError(f"Duplicate key {key} with different values")

    # Group by asset_id and sort each group by (observed_at, sequence)
    assets = {}  # asset_id -> list of events sorted by (observed_at, sequence)

    for key, data in dedup_map.items():
        asset_id, seq = key
        if asset_id not in assets:
            assets[asset_id] = []
        assets[asset_id].append({
            'sequence': seq,
            **data
        })

    # Sort each asset's events by (observed_at, sequence)
    for asset_id in assets:
        assets[asset_id].sort(key=lambda e: (e['observed_at'], e['sequence']))

    segments = []

    for asset_id, evs in assets.items():
        active_segment = None  # list of positioned events forming the current segment

        for ev in evs:
            if ev['fix'] == 'none':
                # A none event closes the active segment and is not included
                if active_segment is not None:
                    segments.append(_build_segment(asset_id, active_segment))
                    active_segment = None
            else:
                # Positioned event
                if active_segment is None:
                    active_segment = [ev]
                else:
                    prev_ev = active_segment[-1]

                    if ev['observed_at'] <= prev_ev['observed_at']:
                        # Timestamp is less than or equal to previous positioned event's timestamp -> new segment
                        segments.append(_build_segment(asset_id, active_segment))
                        active_segment = [ev]
                    else:
                        elapsed = (ev['observed_at'] - prev_ev['observed_at']).total_seconds()

                        if elapsed > max_gap_seconds:
                            # Elapsed time strictly greater than max_gap_seconds -> new segment
                            segments.append(_build_segment(asset_id, active_segment))
                            active_segment = [ev]
                        else:
                            # Equality with gap limit remains in one segment
                            active_segment.append(ev)

        if active_segment is not None and len(active_segment) > 0:
            segments.append(_build_segment(asset_id, active_segment))

    # Sort segments by (asset_id, start_at)
    segments.sort(key=lambda s: (s['asset_id'], s['start_at']))

    return segments


def _haversine(lat1, lon1, lat2, lon2):
    """Compute haversine distance between two points in metres."""
    R = 6371008.8

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def _build_segment(asset_id, segment_events):
    """Build a segment dictionary from a list of positioned events."""
    if not segment_events:
        return None

    first_ev = segment_events[0]
    last_ev = segment_events[-1]

    start_at_dt = first_ev['observed_at']
    end_at_dt = last_ev['observed_at']

    sample_count = len(segment_events)

    # Compute total distance and max speed
    if sample_count == 1:
        distance_m = 0.0
        max_speed_mps = 0.0
    else:
        total_distance = 0.0
        max_speed = 0.0

        for i in range(1, len(segment_events)):
            prev_ev = segment_events[i - 1]
            curr_ev = segment_events[i]

            lat1 = prev_ev['latitude']
            lon1 = prev_ev['longitude']
            lat2 = curr_ev['latitude']
            lon2 = curr_ev['longitude']

            dist = _haversine(lat1, lon1, lat2, lon2)
            total_distance += dist

            elapsed = (curr_ev['observed_at'] - prev_ev['observed_at']).total_seconds()
            if elapsed > 0:
                speed = dist / elapsed
                if speed > max_speed:
                    max_speed = speed

        distance_m = round(total_distance, 3)
        max_speed_mps = round(max_speed, 3)

    # Determine best fix rank
    fix_rank_map = {'2d': 0, '3d': 1, 'rtk_float': 2, 'rtk_fixed': 3}
    best_fix = None
    best_rank = -1

    for ev in segment_events:
        r = fix_rank_map[ev['fix']]
        if r > best_rank:
            best_rank = r
            best_fix = ev['fix']

    # Format timestamps with exactly six fractional digits followed by Z
    start_at_str = _format_utc(start_at_dt)
    end_at_str = _format_utc(end_at_dt)

    return {
        'asset_id': asset_id,
        'start_at': start_at_str,
        'end_at': end_at_str,
        'sample_count': sample_count,
        'start_position': (first_ev['latitude'], first_ev['longitude']),
        'end_position': (last_ev['latitude'], last_ev['longitude']),
        'distance_m': distance_m if isinstance(distance_m, float) else round(float(distance_m), 3),
        'max_speed_mps': max_speed_mps if isinstance(max_speed_mps, float) else round(float(max_speed_mps), 3),
        'best_fix': best_fix,
    }


def _format_utc(dt):
    """Format a UTC datetime with exactly six fractional digits followed by Z."""
    # dt is already in UTC timezone
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    microsecond = dt.microsecond

    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}.{microsecond:06d}Z"
