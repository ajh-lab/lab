import importlib.util
import pathlib
import sys
from types import MappingProxyType


module_path = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("candidate", module_path)
candidate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(candidate)


base = {
    "asset_id": "asset",
    "sequence": 1,
    "observed_at": "2026-01-01T00:00:00Z",
    "fix": "3d",
    "latitude": 0.0,
    "longitude": 0.0,
}


tests = []


def test(name):
    def decorate(fn):
        tests.append((name, fn))
        return fn
    return decorate


@test("accepts read-only Mapping implementation")
def _():
    result = candidate.reconstruct_tracks([MappingProxyType(base)], 5)
    assert result[0]["sample_count"] == 1


@test("rejects RFC3339 offset containing seconds")
def _():
    invalid = dict(base, observed_at="2026-01-01T00:00:00+00:00:30")
    try:
        candidate.reconstruct_tracks([invalid], 5)
    except ValueError:
        return
    raise AssertionError("accepted a timezone offset that is not RFC3339")


@test("rejects timestamp without seconds")
def _():
    invalid = dict(base, observed_at="2026-01-01T00:00+00:00")
    try:
        candidate.reconstruct_tracks([invalid], 5)
    except ValueError:
        return
    raise AssertionError("accepted RFC3339 timestamp without required seconds")


@test("rejects compact timezone offset")
def _():
    invalid = dict(base, observed_at="2026-01-01T00:00:00+0000")
    try:
        candidate.reconstruct_tracks([invalid], 5)
    except ValueError:
        return
    raise AssertionError("accepted timezone offset without required colon")


@test("accepts lowercase RFC3339 t and z")
def _():
    valid = dict(base, observed_at="2026-01-01t00:00:00z")
    result = candidate.reconstruct_tracks([valid], 5)
    assert result[0]["start_at"] == "2026-01-01T00:00:00.000000Z"


failures = 0
for name, fn in tests:
    try:
        fn()
    except Exception as exc:
        failures += 1
        print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    else:
        print(f"PASS {name}")

print(f"SUMMARY {len(tests) - failures}/{len(tests)} passed")
raise SystemExit(1 if failures else 0)
