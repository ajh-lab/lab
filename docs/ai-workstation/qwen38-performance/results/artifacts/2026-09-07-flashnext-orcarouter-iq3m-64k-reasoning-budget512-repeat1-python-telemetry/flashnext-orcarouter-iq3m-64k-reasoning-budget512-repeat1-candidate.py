import math
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
from itertools import groupby
from typing import Any, Iterable

_EARTH_RADIUS_M = 6371008.8
_FIX_RANK = {
    "2d": 1,
    "3d": 2,
    "rtk_float": 3,
    "rtk_fixed": 4,
}
_REQUIRED_EVENT_KEYS = frozenset(
    {
        "asset_id",
        "sequence",
        "observed_at",
        "fix",
        "latitude",
        "longitude",
    }
)


def _is_finite_real(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _validate_max_gap_seconds(max_gap_seconds: Any) -> float:
    if not _is_finite_real(max_gap_seconds) or max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be a finite, non-negative real number")
    return float(max_gap_seconds)


def _parse_rfc3339_utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("observed_at must be an RFC3339 string")

    text = value.strip()
    if not text:
        raise ValueError("observed_at must be an RFC3339 string")

    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("observed_at must be an RFC3339 string") from exc

    if parsed.tzinfo is None:
        raise ValueError("observed_at must contain an explicit timezone")

    return parsed.astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _normalize_event(event: Any) -> tuple[str, int, datetime, str, float | None, float | None]:
    if not isinstance(event, Mapping):
        raise ValueError("each event must be a mapping")

    if set(event) != _REQUIRED_EVENT_KEYS:
        raise ValueError("each event must contain exactly the required keys")

    asset_id = event["asset_id"]
    if not isinstance(asset_id, str):
        raise ValueError("asset_id must be a non-empty string after stripping")
    asset_id = asset_id.strip()
    if not asset_id:
        raise ValueError("asset_id must be a non-empty string after stripping")

    sequence = event["sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ValueError("sequence must be a non-negative int")

    observed_at = _parse_rfc3339_utc(event["observed_at"])

    fix = event["fix"]
    if fix not in _FIX_RANK:
        raise ValueError("fix must be one of: none, 2d, 3d, rtk_float, rtk_fixed")

    latitude = event["latitude"]
    longitude = event["longitude"]

    if fix == "none":
        if latitude is not None or longitude is not None:
            raise ValueError("latitude and longitude must be None for fix=none")
        return asset_id, sequence, observed_at, fix, None, None

    if not _is_finite_real(latitude) or not _is_finite_real(longitude):
        raise ValueError("latitude and longitude must be finite real numbers")

    latitude = float(latitude)
    longitude = float(longitude)

    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be in [-90, 90]")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be in [-180, 180]")

    return asset_id, sequence, observed_at, fix, latitude, longitude


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    return 2.0 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _build_segment(
    asset_id: str,
    events: list[tuple[str, int, datetime, str, float, float]],
) -> dict[str, Any]:
    first = events[0]
    last = events[-1]

    distance_m = 0.0
    max_speed_mps = 0.0

    for previous, current in zip(events, events[1:]):
        segment_distance = _haversine_m(
            previous[4],
            previous[5],
            current[4],
            current[5],
        )
        distance_m += segment_distance

        elapsed = (current[2] - previous[2]).total_seconds()
        if elapsed > 0:
            speed = segment_distance / elapsed
            if speed > max_speed_mps:
                max_speed_mps = speed

    best_fix = max(
        (event[3] for event in events),
        key=lambda fix: _FIX_RANK[fix],
    )

    return {
        "asset_id": asset_id,
        "start_at": _format_utc(first[2]),
        "end_at": _format_utc(last[2]),
        "sample_count": len(events),
        "start_position": (first[4], first[5]),
        "end_position": (last[4], last[5]),
        "distance_m": round(distance_m, 3),
        "max_speed_mps": round(max_speed_mps, 3),
        "best_fix": best_fix,
    }


def reconstruct_tracks(
    events: Iterable[Mapping[str, Any]],
    max_gap_seconds: float,
) -> list[dict[str, Any]]:
    max_gap_seconds = _validate_max_gap_seconds(max_gap_seconds)

    normalized_events: list[
        tuple[str, int, datetime, str, float | None, float | None]
    ] = []

    for event in events:
        normalized_events.append(_normalize_event(event))

    deduplicated: dict[tuple[str, int], tuple[str, int, datetime, str, float | None, float | None]] = {}

    for event in normalized_events:
        key = (event[0], event[1])
        previous = deduplicated.get(key)

        if previous is None:
            deduplicated[key] = event
        elif previous != event:
            raise ValueError(
                "duplicate (asset_id, sequence) events must have identical normalized values"
            )

    positioned_by_asset: dict[str, list[tuple[str, int, datetime, str, float, float]]] = (
        defaultdict(list)
    )

    for event in deduplicated.values():
        if event[3] != "none":
            positioned_by_asset[event[0]].append(
                (
                    event[0],
                    event[1],
                    event[2],
                    event[3],
                    float(event[4]),
                    float(event[5]),
                )
            )

    segments: list[dict[str, Any]] = []

    for asset_id, asset_events in positioned_by_asset.items():
        asset_events.sort(key=lambda event: (event[2], event[1]))

        current_segment: list[tuple[str, int, datetime, str, float, float]] = []
        previous_event: tuple[str, int, datetime, str, float, float] | None = None

        for event in asset_events:
            if previous_event is None:
                current_segment.append(event)
            else:
                elapsed = (event[2] - previous_event[2]).total_seconds()

                if elapsed <= 0 or elapsed > max_gap_seconds:
                    if current_segment:
                        segments.append(_build_segment(asset_id, current_segment))
                    current_segment = [event]
                else:
                    current_segment.append(event)

            previous_event = event

        if current_segment:
            segments.append(_build_segment(asset_id, current_segment))

    segments.sort(key=lambda segment: (segment["asset_id"], segment["start_at"]))
    return segments
