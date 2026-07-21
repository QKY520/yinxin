# P2 250-Record Failed-Gate Error Record

Date: 2026-07-21

This file records why the first 250-record LLM proposal pass was rejected. It
does not store row-level failed predictions or raw model outputs.

## Failed Run

- Run ID: `p2-llm-label-250-v1`
- Commit: `61688ce058267e279cfd1d1b0aed1599761b21c7`
- Config: `configs/p2_llm_label_250_v1.yaml`
- Records: 250
- Status: completed execution, failed success gate
- Gate: parse failure rate must be below 5%
- Observed parse failures: 35/250
- Observed parse failure rate: 14.0%
- GPU service duration recorded by run report: 3027.736 seconds

## Main Failure Pattern

The run failed mainly because the proposal parser rejected entire records when
the model emitted invalid relations. Most errors were relation schema issues,
not malformed JSON. The dominant categories were:

- `USES` type-matrix violations
- `HAS_METRIC` type-matrix violations
- `PART_OF` type-matrix violations
- relations referencing entities removed by overlap resolution or otherwise
  missing

There were also a smaller number of entity-level parsing failures caused by
unlocatable spans, duplicate entities, or wrong occurrence indices. These remain
true parse failures in the corrected pass.

## Corrective Action

Commit `30b783ea003d9a55e6dff28fffb7e1a2d7a99bce` added a P2 proposal-only
parser mode:

- keep strict entity parsing;
- keep final evaluation parsing strict by default;
- drop invalid LLM relations during P2 review-sheet proposal generation;
- log every dropped invalid relation as
  `LLM_RELATION_DROPPED_INVALID_SCHEMA`;
- support `--execute-from-cache` so cached model outputs can be re-parsed in
  GPU-free mode without additional LLM calls.

## Corrected Run

- Run ID: `p2-llm-label-250-v2-cache-reparse`
- Commit: `30b783ea003d9a55e6dff28fffb7e1a2d7a99bce`
- Mode: cache-only reparse in GPU-free mode
- Records: 250
- Cache hits: 263
- New model calls: 0
- Parse failures: 7/250
- Parse failure rate: 2.8%
- Success gate: passed
- Invalid relations dropped and logged: 125

## Data-Retention Action

The failed v1 row-level data artifacts are not retained as active experiment
data. Only this error summary and the structured decision log are retained.
