# P3 Domain Dev50 B-kNN Sanitize Sanity

Date: 2026-07-22

## Scope

Human-approved next small step after the A baseline audit in
`docs/P3_DOMAIN_DEV50_SANITIZE_AUDIT_20260722.md`.

- Dataset: self-built equipment `domain_dev` full 50 rows.
- Support pool: `domain_support.jsonl` only.
- Config: B, BGE-M3 + FAISS kNN examples, K=5.
- Sanitization: documented proposal-stage invalid-unit dropping.
- Model: Qwen2.5-7B-Instruct served by vLLM.
- Explicit exclusions: `domain_test`, P4, P5, full ablation grid.

## Implementation Notes

Added B support to `scripts/run_p3_extraction.py`:

- `examples.mode: knn_retrieval`;
- BGE-M3 dense embeddings;
- normalized vectors;
- FAISS `IndexFlatIP`;
- per-query `example_ids` recorded in dry-run rows and execution rows.

Added sanitizer detail:

- occurrence drops now record `occurrence_requested`,
  `occurrence_available`, and `occurrence_starts`;
- duplicate drops now record `duplicate_key`.

Important runtime fix:

- `embedding.device: cpu` now forces `CUDA_VISIBLE_DEVICES=""` before importing
  FlagEmbedding, so BGE-M3 does not compete with vLLM for GPU memory.

## Dry-Run

```json
{
  "run_id": "p3-domain-dev50-b-knn-k5-seed42-sanity-sanitize-dryrun",
  "query_records": 50,
  "model_calls": 0,
  "api_called": false,
  "embedding_model_path": "/root/autodl-tmp/models/bge-m3",
  "embedding_device": "cpu",
  "faiss_index": "IndexFlatIP",
  "support_candidates": 30,
  "max_prompt_chars": 4459,
  "config_sha256": "c9c0e728b0c1097bf0e08793d0c1d7ce3b4588794117d991ee59c014d40e819b",
  "dry_run_prompts_sha256": "e661c0fd2801e42e494033a036ef19099a4a16b0c5503415f25c9496975ff5c1"
}
```

## Execution Result

```json
{
  "run_id": "p3-domain-dev50-b-knn-k5-seed42-sanity-sanitize",
  "query_records": 50,
  "parse_failures": 0,
  "parse_failure_rate": 0.0,
  "sanitized_unit_events": 32,
  "precision": 0.47674418604651164,
  "recall": 0.5342019543973942,
  "f1": 0.5038402457757296,
  "tp": 164,
  "fp": 180,
  "fn": 143,
  "elapsed_seconds": 194.088
}
```

Sanitization flag counts:

| Flag | Count |
| --- | ---: |
| `ENTITY_DROPPED_INVALID_UNIT` | 27 |
| `ENTITY_DROPPED_OVERLAP` | 5 |

Type-distribution verification:

```json
{
  "status": "ok",
  "rows": 50,
  "parse_failures": 0,
  "pred_entities": 344,
  "max_type_share": 0.5,
  "type_counts": {
    "EQUIPMENT": 172,
    "MODULE": 116,
    "METRIC": 34,
    "TECH_SCHEME": 22
  }
}
```

The B sanity gate passes structurally: per-query rows reload, parse-failure
rate is 0%, F1 is nonzero, and no entity type exceeds 90% of predictions.

## Comparison With A

| Config | P | R | F1 | Parse failures | Sanitized events |
| --- | ---: | ---: | ---: | ---: | ---: |
| A fixed-random | 0.4914 | 0.5570 | 0.5221 | 0/50 | 49 |
| B kNN | 0.4767 | 0.5342 | 0.5038 | 0/50 | 32 |

B is lower than A by about `0.0183` F1 on this dev sanity. This is a preserved
negative result, not a failure to hide. It suggests that the current BGE-M3
kNN demonstrations are not yet improving the A baseline on this 50-row domain
dev slice.

Likely causes to inspect before C/P4:

- retrieved support examples may be semantically close but annotation-pattern
  mismatched;
- B increased METRIC/TECH_SCHEME predictions while reducing EQUIPMENT/MODULE;
- support pool has only 30 rows, so nearest examples may not cover several dev
  text formats;
- patent-format rows remain brittle.

## Runtime Issues Preserved

Two operational issues occurred and were fixed:

1. Reusing an old vLLM process caused an HTTP timeout. The stale process showed
   port readiness but 0 MiB GPU memory. It was killed and vLLM was restarted.
2. FlagEmbedding initially tried to use CUDA and collided with vLLM memory. The
   successful run used `env CUDA_VISIBLE_DEVICES=` for the runner, and the code
   was patched so `embedding.device: cpu` enforces this behavior.

These issues did not affect the final B result file, which was generated after
the clean restart and CPU-embedding fix.

## Hashes

| Artifact | SHA256 |
| --- | --- |
| `configs/p3_domain_dev50_b_knn_k5_sanity_sanitize.yaml` | `8d543db693749144eec99e8b60d8fca211e8e977ff16e2d14c2a3f89e67b9d8f` |
| `results/p3/p3_domain_dev50_b_knn_k5_sanity_sanitize_summary.json` | `91055b38375f5691a732cb5a13078ac038c9812ff31abb25224239d6a799133e` |
| `results/p3/p3_domain_dev50_b_knn_k5_sanity_sanitize_per_query.jsonl` | `4c3b3741e67dc64f47ff0eba0e761b7817fe15af55541b169c208de8fb1d09e4` |
| `logs/p3_domain_dev50_b_knn_vllm_20260722.log` | `b934f80534cf461ca1e9369e96ab971c71c2d58d6d7ea28d5eb0c226b7f9358d` |

Backup archive:

```text
Remote: /root/autodl-tmp/backup/p3/p3_domain_dev50_b_knn_sanity_sanitize_20260722.tar.gz
Local:  D:\yinsir\backups\P3\p3_domain_dev50_b_knn_sanity_sanitize_20260722.tar.gz
SHA256: 53ac62255488fb9ca9269d9c789141dffec1d5729b2e6a75c99c519f0d3348db
```

## Cost

The B phase used paid GPU time for vLLM startup plus the B run and debugging.
At the user-reported 4090 price of 2.7 CNY/hour, the agent-managed window is
roughly about 1 CNY. AutoDL platform billing is authoritative.

## Next Gate

Stop here. Do not proceed to C/P4/P5 or `domain_test` until the human audits
the B result. The immediate audit target is the kNN example choices and the
reason B underperformed A.
