# P3 Domain Dev50 Sanitize Sanity

Date: 2026-07-22

## Scope

Human-approved paid-GPU run after the successful GPU-free dry-run.

- Dataset: self-built equipment `domain_dev` full 50 rows.
- Support pool: `domain_support.jsonl` only.
- Config: A, fixed-random K=5, seed 42.
- Sanitization: documented proposal-stage invalid-unit dropping.
- Model: Qwen2.5-7B-Instruct served by vLLM.
- Explicit exclusions: `domain_test`, P4, P5, full ablation grid.

## GPU Check

Pre-run check:

```text
NVIDIA GeForce RTX 4090, 0 MiB / 24564 MiB
```

vLLM was stopped after the run. Post-run check:

```text
0 MiB / 24564 MiB
```

The vLLM process PID was `1914`.

## Command

```bash
cd /root/project
. /root/autodl-tmp/venvs/equipment-ie/bin/activate
python scripts/run_p3_extraction.py \
  --config configs/p3_domain_dev50_a_k5_sanity_sanitize.yaml
```

## Result

```json
{
  "run_id": "p3-domain-dev50-a-k5-seed42-sanity-sanitize",
  "query_records": 50,
  "parse_failures": 0,
  "parse_failure_rate": 0.0,
  "sanitized_unit_events": 49,
  "precision": 0.49137931034482757,
  "recall": 0.5570032573289903,
  "f1": 0.5221374045801527,
  "tp": 171,
  "fp": 177,
  "fn": 136,
  "elapsed_seconds": 130.383
}
```

Sanitization flag counts:

| Flag | Count |
| --- | ---: |
| `ENTITY_DROPPED_INVALID_UNIT` | 37 |
| `ENTITY_DROPPED_OVERLAP` | 12 |

Type-distribution verification:

```json
{
  "status": "ok",
  "rows": 50,
  "parse_failures": 0,
  "pred_entities": 348,
  "max_type_share": 0.5229885057471264,
  "type_counts": {
    "EQUIPMENT": 182,
    "MODULE": 138,
    "METRIC": 17,
    "TECH_SCHEME": 11
  }
}
```

The P3 bounded sanity gate passes for this proposal-stage sanitization mode:
per-query rows reload, parse-failure rate is 0%, F1 is nonzero, and no entity
type exceeds 90% of predictions.

## Hashes

| Artifact | SHA256 |
| --- | --- |
| `configs/p3_domain_dev50_a_k5_sanity_sanitize.yaml` | `670159b046adba0f26bb27c88b45b2b1398b35aa1c7992e567e9fa23995a827a` |
| `results/p3/p3_domain_dev50_a_k5_sanity_sanitize_summary.json` | `8413e37c23816379517b73f46d1ad96d76f363a7f445e46ff3b53535926c3e2b` |
| `results/p3/p3_domain_dev50_a_k5_sanity_sanitize_per_query.jsonl` | `b1b352ce080e593cc06499bd5704c4425060452aeefcb5e88095873c3a4e23f0` |
| `logs/p3_domain_dev50_vllm_20260722.log` | `2499a8d5182715a8f068c37ba06660c9fcbecfbc308be8cb44c92ae2497a2b2a` |

Backup archive:

```text
Remote: /root/autodl-tmp/backup/p3/p3_domain_dev50_sanity_sanitize_20260722.tar.gz
Local:  D:\yinsir\backups\P3\p3_domain_dev50_sanity_sanitize_20260722.tar.gz
SHA256: 3b26fbd36e0614e1dbc440cbab47c9eb05c750b6e135dc9595c0860a3f91bfac
```

The local archive hash matches the remote archive hash.

## Cost

Agent-managed paid-GPU window was approximately 20:12-20:21 Asia/Shanghai on
2026-07-22. At the user-reported 4090 price of 2.7 CNY/hour, this is roughly
0.4 CNY. AutoDL platform billing is authoritative.

## Next Gate

Stop here. Do not run `domain_test`, P4, P5, or a broader grid without another
explicit human approval.

The next sensible step is a human quality audit of:

- the summary numbers in this report;
- the per-query rows for representative false positives/false negatives;
- the 49 sanitization flags, especially the 37 invalid-unit drops.
