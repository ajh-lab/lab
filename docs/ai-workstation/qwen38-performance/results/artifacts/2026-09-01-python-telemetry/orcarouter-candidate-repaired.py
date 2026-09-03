from datetime import datetime, timezone
import math


def _parse_rfc3339_utc(value):
    if not isinstance(value, str):
        raise ValueError("observed_at must be a string")
    s = value.strip()
    # RFC 3339 requires at least YYYY-MM-DDTHH:MM:SS with timezone offset or Z
    if len(s) < 20:
        raise ValueError("invalid observed_at format")

    # Validate the structure more strictly to ensure only hours and minutes in offset
    # Pattern: date T time [Z | +HH:MM | -HH:MM]
    import re
    pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$'
    if not re.match(pattern, s):
        raise ValueError(f"invalid RFC3339 timestamp: {value!r}")

    try:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f"invalid RFC3339 timestamp: {value!r}")

    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("observed_at must contain an explicit timezone")

    return dt.astimezone(timezone.utc)


def _format_utc(dt):
    micro = dt.microsecond
    base = dt.strftime('%Y-%m-%dT%H:%M:%S')
    frac = f'{micro:06d}'
    return f"{base}.{frac}Z"


def _validate_event(event):
    # Accept any mapping (including MappingProxyType) by checking for keys() method and __getitem__
    if not hasattr(event, 'keys') or not callable(getattr(event, '__getitem__', None)):
        raise ValueError("event must be a mapping")

    required_keys = {'asset_id', 'sequence', 'observed_at', 'fix', 'latitude', 'longitude'}
    try:
        keys = set(event.keys())
    except Exception as e:
        raise ValueError(f"invalid event mapping: {e}") from None

    if keys != required_keys:
        missing = required_keys - keys
        extra = keys - required_keys
        raise ValueError(f"event must have exactly the six required keys; missing={missing}, extra={extra}")

    # asset_id
    aid_raw = event['asset_id']
    if not isinstance(aid_raw, str):
        raise ValueError("asset_id must be a string")
    aid = aid_raw.strip()
    if not aid:
        raise ValueError("asset_id must be non-empty after stripping")

    # sequence
    seq = event['sequence']
    if isinstance(seq, bool) or not isinstance(seq, int):
        raise ValueError("sequence must be a non-negative integer (bool invalid)")
    if seq < 0:
        raise ValueError("sequence must be non-negative")

    # observed_at
    dt_utc = _parse_rfc3339_utc(event['observed_at'])

    # fix
    valid_fixes = {'none', '2d', '3d', 'rtk_float', 'rtk_fixed'}
    fix = event['fix']
    if not isinstance(fix, str) or fix not in valid_fixes:
        raise ValueError("fix must be one of none, 2d, 3d, rtk_float, rtk_fixed")

    # latitude and longitude
    lat_raw = event['latitude']
    lon_raw = event['longitude']

    if fix == 'none':
        if lat_raw is not None or lon_raw is not None:
            raise ValueError("for fix=none, both latitude and longitude must be None")
        lat = None
        lon = None
    else:
        for name, val in (('latitude', lat_raw), ('longitude', lon_raw)):
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(f"{name} must be a finite real number")
            v = float(val)
            if math.isnan(v) or math.isinf(v):
                raise ValueError(f"{name} must be finite")

        lat = float(lat_raw)
        lon = float(lon_raw)

        if not (-90.0 <= lat <= 90.0):
            raise ValueError("latitude out of range [-90, 90]")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError("longitude out of range [-180, 180]")

    return (aid, seq, dt_utc, fix, lat, lon)


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371008.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    # Handle antimeridian: use the smaller angular difference in longitude
    dlambda_raw = lon2 - lon1
    if dlambda_raw > 180.0:
        dlambda_raw -= 360.0
    elif dlambda_raw < -180.0:
        dlambda_raw += 360.0
    dlambda = math.radians(dlambda_raw)

    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def _best_fix_rank(fix):
    ranks = {'2d': 0, '3d': 1, 'rtk_float': 2, 'rtk_fixed': 3}
    if fix not in ranks:
        raise ValueError(f"unexpected fix value: {fix}")
    return ranks[fix]


def reconstruct_tracks(events, max_gap_seconds):
    # Validate max_gap_seconds
    if isinstance(max_gap_seconds, bool) or not isinstance(max_gap_seconds, (int, float)):
        raise ValueError("max_gap_seconds must be a finite non-negative real number")
    gap = float(max_gap_seconds)
    if math.isnan(gap) or math.isinf(gap):
        raise ValueError("max_gap_seconds must be finite")
    if gap < 0:
        raise ValueError("max_gap_seconds must be non-negative")

    # Materialize and validate all events, deduplicate by (asset_id, sequence)
    seen = {}
    for event in events:
        norm = _validate_event(event)
        aid, seq, dt_utc, fix, lat, lon = norm
        key = (aid, seq)
        if key in seen:
            existing = seen[key]
            if existing != norm:
                raise ValueError(f"duplicate event for {key} with differing values")
        else:
            seen[key] = norm

    # Group by asset_id
    assets = {}
    for (aid, seq), norm in seen.items():
        if aid not in assets:
            assets[aid] = []
        assets[aid].append(norm)

    segments = []

    for aid in sorted(assets.keys()):
        evts = assets[aid]
        # Sort by (observed_at, sequence)
        evts.sort(key=lambda e: (e[2], e[1]))

        current_segment = []

        def _flush():
            nonlocal current_segment
            if not current_segment:
                return
            seg_events = current_segment[:]
            n = len(seg_events)
            start_dt = seg_events[0][2]
            end_dt = seg_events[-1][2]
            start_lat, start_lon = seg_events[0][4], seg_events[0][5]
            end_lat, end_lon = seg_events[-1][4], seg_events[-1][5]

            if n == 1:
                dist_m = 0.0
                max_speed = 0.0
            else:
                total_dist = 0.0
                max_spd = 0.0
                for i in range(1, n):
                    prev_dt = seg_events[i - 1][2]
                    cur_dt = seg_events[i][2]
                    elapsed = (cur_dt - prev_dt).total_seconds()
                    d = _haversine(seg_events[i - 1][4], seg_events[i - 1][5],
                                   seg_events[i][4], seg_events[i][5])
                    total_dist += d
                    if elapsed > 0:
                        spd = d / elapsed
                        if spd > max_spd:
                            max_spd = spd
                dist_m = total_dist
                max_speed = max_spd

            # Best fix in segment
            best_fix_val = None
            for e in seg_events:
                f = e[3]
                r = _best_fix_rank(f)
                if best_fix_val is None or r > _best_fix_rank(best_fix_val):
                    best_fix_val = f

            segments.append({
                'asset_id': aid,
                'start_at': _format_utc(start_dt),
                'end_at': _format_utc(end_dt),
                'sample_count': n,
                'start_position': (float(start_lat), float(start_lon)),
                'end_position': (float(end_lat), float(end_lon)),
                'distance_m': round(dist_m, 3),
                'max_speed_mps': round(max_speed, 3),
                'best_fix': best_fix_val,
            })

        for norm in evts:
            aid_n, seq_n, dt_utc, fix, lat, lon = norm
            if fix == 'none':
                _flush()
                current_segment = []
            else:
                if not current_segment:
                    current_segment.append(norm)
                else:
                    prev_dt = current_segment[-1][2]
                    elapsed = (dt_utc - prev_dt).total_seconds()
                    if dt_utc <= prev_dt or elapsed > gap:
                        _flush()
                        current_segment = [norm]
                    else:
                        current_segment.append(norm)

        # Flush any remaining active segment for this asset
        _flush()
        current_segment = []

    segments.sort(key=lambda s: (s['asset_id'], s['start_at']))

    return segments
