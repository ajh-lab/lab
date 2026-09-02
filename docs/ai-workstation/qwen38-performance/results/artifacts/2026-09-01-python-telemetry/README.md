# Python Telemetry Evaluation Artifacts

These artifacts reproduce the 2026-09-01 Q4_K_M and BF16 implementation
comparison.

## Inputs And Harness

- `prompt.txt`: exact blind implementation specification
- `hidden_tests.py`: 13 core behavioral tests
- `adversarial_tests.py`: 5 mapping and RFC3339 probes
- `run_model.py`: deterministic LiteLLM request and response extraction
- `build_repair_prompt.py`: constructs the identical two-item feedback cycle

The tests were never included in either model prompt. Future model comparisons
must run in an isolated directory and must not permit the model to read this
artifact folder.

## Generated Outputs

- `q4-candidate.py` and `q4-candidate-repaired.py`
- `bf16-candidate.py` and `bf16-candidate-repaired.py`
- matching `*-raw-response.json` API records

Raw response files contain generated content, model identifiers, usage counts,
and response metadata. They contain no credentials or environment values.
