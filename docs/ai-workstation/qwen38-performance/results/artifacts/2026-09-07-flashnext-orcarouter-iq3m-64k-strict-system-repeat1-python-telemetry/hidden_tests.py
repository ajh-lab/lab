import importlib.util
import math
import pathlib
import sys


MODULE_PATH = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("candidate", MODULE_PATH)
candidate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(candidate)
reconstruct_tracks = candidate.reconstruct_tracks


def event(asset, seq, at, fix="3d", lat=0.0, lon=0.0):
    return {
        "asset_id": asset,
        "sequence": seq,
        "observed_at": at,
        "fix": fix,
        "latitude": lat,
        "longitude": lon,
    }


def expect_value_error(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def close(actual, expected, tolerance=0.001):
    assert math.isclose(actual, expected, abs_tol=tolerance), (actual, expected)


cases = []


def case(name):
    def decorate(fn):
        cases.append((name, fn))
        return fn
    return decorate


@case("empty iterable")
def _():
    assert reconstruct_tracks(iter(()), 5) == []


@case("validates gap")
def _():
    for bad in (-1, True, float("inf"), float("nan"), "5", None):
        expect_value_error(lambda bad=bad: reconstruct_tracks([], bad))


@case("validates exact schema and scalar types")
def _():
    malformed = [
        {**event("a", 1, "2026-01-01T00:00:00Z"), "extra": 1},
        event(" ", 1, "2026-01-01T00:00:00Z"),
        event("a", True, "2026-01-01T00:00:00Z"),
        event("a", -1, "2026-01-01T00:00:00Z"),
        event("a", 1, "2026-01-01T00:00:00"),
        event("a", 1, "bad-time"),
        event("a", 1, "2026-01-01T00:00:00Z", lat=True),
        event("a", 1, "2026-01-01T00:00:00Z", lat=91),
        event("a", 1, "2026-01-01T00:00:00Z", lon=181),
        event("a", 1, "2026-01-01T00:00:00Z", fix="bad"),
        event("a", 1, "2026-01-01T00:00:00Z", fix="none", lat=0, lon=0),
        event("a", 1, "2026-01-01T00:00:00Z", fix="3d", lat=None, lon=None),
    ]
    for item in malformed:
        expect_value_error(lambda item=item: reconstruct_tracks([item], 5))


@case("normalizes values and does not mutate input")
def _():
    source = event(" asset ", 4, "2026-01-01T01:02:03+01:00", lat=1, lon=2)
    before = dict(source)
    result = reconstruct_tracks([source], 5)
    assert source == before
    assert result == [{
        "asset_id": "asset",
        "start_at": "2026-01-01T00:02:03.000000Z",
        "end_at": "2026-01-01T00:02:03.000000Z",
        "sample_count": 1,
        "start_position": (1.0, 2.0),
        "end_position": (1.0, 2.0),
        "distance_m": 0.0,
        "max_speed_mps": 0.0,
        "best_fix": "3d",
    }]


@case("deduplicates normalized identity")
def _():
    a = event("asset", 1, "2026-01-01T00:00:00Z", lat=1, lon=2)
    b = event(" asset ", 1, "2025-12-31T19:00:00-05:00", lat=1.0, lon=2.0)
    result = reconstruct_tracks([a, b, dict(a)], 5)
    assert len(result) == 1
    assert result[0]["sample_count"] == 1


@case("rejects conflicting duplicate sequence")
def _():
    a = event("asset", 1, "2026-01-01T00:00:00Z", lat=1, lon=2)
    b = event("asset", 1, "2026-01-01T00:00:01Z", lat=1, lon=2)
    expect_value_error(lambda: reconstruct_tracks([a, b], 5))


@case("sorts assets and events deterministically")
def _():
    data = [
        event("b", 2, "2026-01-01T00:00:02Z", lat=0, lon=0.002),
        event("a", 2, "2026-01-01T00:00:01Z", lat=0, lon=0.001),
        event("b", 1, "2026-01-01T00:00:01Z", lat=0, lon=0.001),
        event("a", 1, "2026-01-01T00:00:00Z", lat=0, lon=0),
    ]
    result = reconstruct_tracks(iter(data), 2)
    assert [x["asset_id"] for x in result] == ["a", "b"]
    assert all(x["sample_count"] == 2 for x in result)


@case("gap equality joins and greater gap splits")
def _():
    data = [
        event("a", 1, "2026-01-01T00:00:00Z"),
        event("a", 2, "2026-01-01T00:00:05Z", lon=0.001),
        event("a", 3, "2026-01-01T00:00:10.000001Z", lon=0.002),
    ]
    result = reconstruct_tracks(data, 5)
    assert [x["sample_count"] for x in result] == [2, 1]


@case("none closes segment and is omitted")
def _():
    data = [
        event("a", 1, "2026-01-01T00:00:00Z"),
        event("a", 2, "2026-01-01T00:00:01Z", fix="none", lat=None, lon=None),
        event("a", 3, "2026-01-01T00:00:02Z", fix="rtk_fixed", lon=0.001),
    ]
    result = reconstruct_tracks(data, 10)
    assert [x["sample_count"] for x in result] == [1, 1]
    assert result[1]["best_fix"] == "rtk_fixed"


@case("same timestamp starts a new segment")
def _():
    data = [
        event("a", 1, "2026-01-01T00:00:00Z"),
        event("a", 2, "2026-01-01T00:00:00+00:00", lon=0.001),
    ]
    result = reconstruct_tracks(data, 10)
    assert [x["sample_count"] for x in result] == [1, 1]


@case("computes distance speed and best fix")
def _():
    data = [
        event("a", 1, "2026-01-01T00:00:00Z", fix="2d", lat=0, lon=0),
        event("a", 2, "2026-01-01T00:00:10Z", fix="rtk_float", lat=0, lon=0.001),
        event("a", 3, "2026-01-01T00:00:30Z", fix="3d", lat=0, lon=0.002),
    ]
    result = reconstruct_tracks(data, 20)[0]
    close(result["distance_m"], 222.39, 0.01)
    close(result["max_speed_mps"], 11.12, 0.01)
    assert result["best_fix"] == "rtk_float"
    assert set(result) == {
        "asset_id", "start_at", "end_at", "sample_count",
        "start_position", "end_position", "distance_m",
        "max_speed_mps", "best_fix",
    }


@case("handles antimeridian")
def _():
    data = [
        event("a", 1, "2026-01-01T00:00:00Z", lat=0, lon=179.999),
        event("a", 2, "2026-01-01T00:00:10Z", lat=0, lon=-179.999),
    ]
    result = reconstruct_tracks(data, 10)[0]
    close(result["distance_m"], 222.39, 0.05)
    assert result["distance_m"] < 300


@case("materializes before raising")
def _():
    consumed = []

    def source():
        consumed.append(1)
        yield event("a", 1, "2026-01-01T00:00:00Z")
        consumed.append(2)
        yield event("a", 2, "bad")

    expect_value_error(lambda: reconstruct_tracks(source(), 5))
    assert consumed == [1, 2]


failures = []
for name, fn in cases:
    try:
        fn()
    except Exception as exc:
        failures.append((name, type(exc).__name__, str(exc)))
        print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    else:
        print(f"PASS {name}")

print(f"SUMMARY {len(cases) - len(failures)}/{len(cases)} passed")
raise SystemExit(1 if failures else 0)
