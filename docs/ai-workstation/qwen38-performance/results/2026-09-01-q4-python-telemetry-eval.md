# Q4 Implementation Evaluation: Python Telemetry Reducer

Date: 2026-09-01 (America/Chicago)

## Objective

Evaluate whether Qwen3.8 27B Uncensored Q4_K_M can implement a relatively
complex, DroneOps-relevant Python specification rather than merely answer
short coding prompts. The model had no access to the tests and could not deploy
or modify a repository.

The task required a standard-library-only telemetry reducer with:

- strict event and scalar validation
- RFC3339 parsing and UTC normalization
- normalized duplicate detection
- deterministic per-asset sorting
- gap and no-fix segment boundaries
- haversine distance with antimeridian handling
- speed and best-fix aggregation
- exact output schema and timestamp formatting
- no input mutation

## First Attempt

| Metric | Result |
| --- | ---: |
| Prompt tokens | 702 |
| Completion tokens | 2,514 |
| Elapsed time | 212.608 s |
| Generated module size | 237 lines |
| Core hidden tests | 13/13 |
| Additional standards tests | 0/5 |
| Combined score | 13/18 |

The implementation compiled and passed every original hidden test. This
included malformed input, normalization, deduplication, deterministic sorting,
gap equality, no-fix segmentation, equal timestamps, distance, speed, best-fix
selection, antimeridian behavior, and full input materialization.

Manual contract review found that the implementation required a concrete
`dict` instead of accepting arbitrary `collections.abc.Mapping` objects. Its
use of `datetime.fromisoformat` was also more permissive than RFC3339 for some
invalid forms and rejected a valid lowercase form.

## Feedback Cycle

The model received only two concrete failures: accept arbitrary mappings and
reject timezone offsets containing seconds. It was asked to return a complete
corrected module without weakening passing behavior.

| Metric | Result |
| --- | ---: |
| Prompt tokens | 3,329 |
| Completion tokens | 3,410 |
| Elapsed time | 296.842 s |
| Generated module size | 317 lines |
| Original hidden tests | 13/13 |
| Standards tests | 3/5 |
| Combined score | 16/18 |

The repair fixed both reported failures and retained all original behavior.
Three unreported RFC3339 probes then showed that it correctly accepted lowercase
`t`/`z`, but still accepted a timestamp without required seconds and a compact
timezone offset without the required colon.

The repair also became 80 lines longer and included uncertain explanatory
comments around timestamp parsing. This indicates successful test-driven
recovery but incomplete generalization of the governing standard.

## Decision

The result supports Q4_K_M as a practical local implementation worker for
scoped DroneOps issues with explicit acceptance criteria and executable tests.
It does not support unsupervised merging or using Q4 as the final authority for
protocol, authentication, persistence, migration, or safety-sensitive work.

Keep the existing routing decision:

1. Q4 performs bounded implementation in an isolated worktree.
2. Focused tests and CI are mandatory.
3. A stronger reviewer checks contract and architecture boundaries.
4. BF16 or a hosted model is an escalation path after reasoning-related
   failures, not the default solely because it has higher precision.

To determine whether BF16 earns that escalation role, run this exact blind
task and test suite against BF16 and compare combined correctness, repair
quality, elapsed time, and reviewer correction effort.
