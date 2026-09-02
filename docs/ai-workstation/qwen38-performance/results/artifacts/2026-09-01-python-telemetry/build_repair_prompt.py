import pathlib
import sys


original = pathlib.Path(sys.argv[1]).read_text()
candidate = pathlib.Path(sys.argv[2]).read_text()
output = pathlib.Path(sys.argv[3])

output.write_text(
    original
    + "\n\nYour previous implementation follows. Revise the complete module to fix the "
      "reported failures without weakening any passing behavior. Return only "
      "the complete Python module.\n\n"
    + candidate
    + "\n\nReported failures:\n"
      "1. A read-only collections.abc.Mapping such as MappingProxyType was "
      "rejected with ValueError, but arbitrary mappings must be accepted.\n"
      "2. observed_at='2026-01-01T00:00:00+00:00:30' was accepted, but RFC3339 "
      "timezone offsets permit only hours and minutes and this must raise "
      "ValueError.\n"
)
