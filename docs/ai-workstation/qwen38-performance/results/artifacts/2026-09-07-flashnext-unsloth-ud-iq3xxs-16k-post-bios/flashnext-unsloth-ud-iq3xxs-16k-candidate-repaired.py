import math
import math
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from collections.abc import Mapping

def reconstruct_tracks(events, max_gap_seconds):
    # Validate max_gap_seconds
    if isinstance(max_gap_seconds, bool):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if math.isnan(max_gap_seconds) or math.isinf(max_gap_seconds):
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    if max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")

    # Parse RFC3339 timestamp with explicit timezone
    def parse_rfc3339(ts_str):
        if not isinstance(ts_str, str):
            raise ValueError("observed_at must be a string")

        # Strict RFC3339 validation for timezone offset
        # RFC3339 allows: Z or +HH:MM or -HH:MM
        # We need to ensure the offset part is strictly HH:MM if present

        ts = ts_str
        if ts.endswith('Z'):
            ts = ts[:-1] + '+00:00'

        # Check if there is a timezone offset and validate its format
        # Look for the last '+' or '-' that indicates timezone
        # But we must be careful not to confuse with negative years or other parts

        # A more robust approach: try to parse with fromisoformat, but first
        # validate the timezone offset format manually if it exists

        # Find potential timezone offset
        # RFC3339 format: YYYY-MM-DDTHH:MM:SS[.fraction][Z|+HH:MM|-HH:MM]

        # Let's check if the string ends with a timezone indicator
        # If it ends with Z, we already handled it.
        # Otherwise, check for +HH:MM or -HH:MM at the end

        # We need to find the timezone part. It's the last occurrence of + or -
        # that is followed by HH:MM pattern.

        # Simple approach: check if the string matches a strict pattern for the offset
        import re

        # Pattern for the entire RFC3339 string with strict offset validation
        # This regex ensures the offset is exactly HH:MM if present
        rfc3339_pattern = re.compile(
            r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?'
            r'(Z|[+-]\d{2}:\d{2})$'
        )

        if not rfc3339_pattern.match(ts_str):
            raise ValueError(f"Invalid RFC3339 timestamp: {ts_str}")

        # Now parse with fromisoformat
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            raise ValueError(f"Invalid RFC3339 timestamp: {ts_str}")

        if dt.tzinfo is None:
            raise ValueError("observed_at must contain an explicit timezone")

        # Convert to UTC
        dt_utc = dt.astimezone(timezone.utc)
        return dt_utc

    # Validate and normalize a single event
    def validate_event(event):
        if not isinstance(event, Mapping):
            raise ValueError("Each event must be a mapping")
        required_keys = {'asset_id', 'sequence', 'observed_at', 'fix', 'latitude', 'longitude'}
        event_keys = set(event.keys())
        if event_keys != required_keys:
            raise ValueError(f"Event must contain exactly these keys: {required_keys}")

        # asset_id
        asset_id = event['asset_id']
        if not isinstance(asset_id, str):
            raise ValueError("asset_id must be a string")
        asset_id = asset_id.strip()
        if not asset_id:
            raise ValueError("asset_id must be non-empty after stripping")

        # sequence
        sequence = event['sequence']
        if isinstance(sequence, bool):
            raise ValueError("sequence must be a non-negative int")
        if not isinstance(sequence, int):
            raise ValueError("sequence must be a non-negative int")
        if sequence < 0:
            raise ValueError("sequence must be a non-negative int")

        # observed_at
        observed_at_str = event['observed_at']
        observed_at = parse_rfc3339(observed_at_str)

        # fix
        fix = event['fix']
        valid_fixes = {'none', '2d', '3d', 'rtk_float', 'rtk_fixed'}
        if fix not in valid_fixes:
            raise ValueError(f"fix must be one of {valid_fixes}")

        # latitude, longitude
        latitude = event['latitude']
        longitude = event['longitude']

        if fix == 'none':
            if latitude is not None or longitude is not None:
                raise ValueError("For fix 'none', latitude and longitude must be None")
            lat = None
            lon = None
        else:
            if isinstance(latitude, bool) or isinstance(longitude, bool):
                raise ValueError("latitude and longitude must be finite real numbers")
            if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
                raise ValueError("latitude and longitude must be finite real numbers")
            if math.isnan(latitude) or math.isinf(latitude) or math.isnan(longitude) or math.isinf(longitude):
                raise ValueError("latitude and longitude must be finite real numbers")
            lat = float(latitude)
            lon = float(longitude)
            if not (-90 <= lat <= 90):
                raise ValueError("latitude must be in [-90, 90]")
            if not (-180 <= lon <= 180):
                raise ValueError("longitude must be in [-180, 180]")

        return {
            'asset_id': asset_id,
            'sequence': sequence,
            'observed_at': observed_at,
            'fix': fix,
            'latitude': lat,
            'longitude': lon
        }

    # Materialize and validate all events
    validated_events = []
    for event in events:
        validated_events.append(validate_event(event))

    # Deduplicate using (asset_id, sequence)
    seen = {}
    for ev in validated_events:
        key = (ev['asset_id'], ev['sequence'])
        if key in seen:
            prev = seen[key]
            # Check if all six normalized values are identical
            if (prev['asset_id'] != ev['asset_id'] or
                prev['sequence'] != ev['sequence'] or
                prev['observed_at'] != ev['observed_at'] or
                prev['fix'] != ev['fix'] or
                prev['latitude'] != ev['latitude'] or
                prev['longitude'] != ev['longitude']):
                raise ValueError(f"Duplicate key {key} with different values")
        else:
            seen[key] = ev

    # Group by asset_id
    assets = defaultdict(list)
    for ev in seen.values():
        assets[ev['asset_id']].append(ev)

    # Sort each asset's events by (observed_at, sequence)
    for asset_id in assets:
        assets[asset_id].sort(key=lambda e: (e['observed_at'], e['sequence']))

    # Haversine distance
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371008.8
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    # Best fix rank
    fix_rank = {'2d': 0, '3d': 1, 'rtk_float': 2, 'rtk_fixed': 3}

    def format_timestamp(dt):
        # Format with exactly six fractional digits followed by Z
        # dt is already in UTC
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'

    def build_segment(asset_id, seg_events):
        # seg_events is a list of positioned events
        n = len(seg_events)
        start_ev = seg_events[0]
        end_ev = seg_events[-1]

        start_at = format_timestamp(start_ev['observed_at'])
        end_at = format_timestamp(end_ev['observed_at'])

        start_position = (start_ev['latitude'], start_ev['longitude'])
        end_position = (end_ev['latitude'], end_ev['longitude'])

        # Compute distance and max speed
        total_distance = 0.0
        max_speed = 0.0

        for i in range(1, n):
            prev_ev = seg_events[i - 1]
            curr_ev = seg_events[i]
            lat1, lon1 = prev_ev['latitude'], prev_ev['longitude']
            lat2, lon2 = curr_ev['latitude'], curr_ev['longitude']
            dist = haversine(lat1, lon1, lat2, lon2)
            total_distance += dist
            elapsed = (curr_ev['observed_at'] - prev_ev['observed_at']).total_seconds()
            if elapsed > 0:
                speed = dist / elapsed
                if speed > max_speed:
                    max_speed = speed

        # Round to three decimal places
        distance_m = round(total_distance, 3)
        max_speed_mps = round(max_speed, 3)

        # Best fix
        best_fix = min(seg_events, key=lambda e: fix_rank[e['fix']])['fix']

        return {
            'asset_id': asset_id,
            'start_at': start_at,
            'end_at': end_at,
            'sample_count': n,
            'start_position': start_position,
            'end_position': end_position,
            'distance_m': distance_m,
            'max_speed_mps': max_speed_mps,
            'best_fix': best_fix
        }

    segments = []

    for asset_id, evs in assets.items():
        active_segment = None  # list of positioned events in current segment
        prev_positioned = None  # last positioned event in active segment

        for ev in evs:
            if ev['fix'] == 'none':
                # Close active segment if exists
                if active_segment:
                    segments.append(build_segment(asset_id, active_segment))
                    active_segment = None
                    prev_positioned = None
                continue

            # Positioned event
            if active_segment is None:
                # Start new segment
                active_segment = [ev]
                prev_positioned = ev
            else:
                # Check if we need to start a new segment
                prev_ts = prev_positioned['observed_at']
                curr_ts = ev['observed_at']
                elapsed = (curr_ts - prev_ts).total_seconds()

                if curr_ts <= prev_ts:
                    # Timestamp is less than or equal to previous positioned event's timestamp
                    # Close current segment and start new one
                    segments.append(build_segment(asset_id, active_segment))
                    active_segment = [ev]
                    prev_positioned = ev
                elif elapsed > max_gap_seconds:
                    # Elapsed time strictly greater than max_gap_seconds
                    segments.append(build_segment(asset_id, active_segment))
                    active_segment = [ev]
                    prev_positioned = ev
                else:
                    # Continue current segment
                    active_segment.append(ev)
                    prev_positioned = ev

        # Close any remaining active segment
        if active_segment:
            segments.append(build_segment(asset_id, active_segment))

    # Sort segments by (asset_id, start_at)
    segments.sort(key=lambda s: (s['asset_id'], s['start_at']))

    return segments
