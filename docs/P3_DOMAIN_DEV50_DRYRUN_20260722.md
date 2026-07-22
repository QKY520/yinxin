# P3 Domain Dev50 Sanitize Dry-Run

Date: 2026-07-22

## Scope

This is a GPU-free P3 preparation step after the human audit of
`docs/P3_DOMAIN_DEV20_SANITY_AUDIT_20260722.md`.

- Dataset: self-built equipment `domain_dev` full 50 rows.
- Support pool: `domain_support.jsonl` only.
- Config: A, fixed-random K=5, seed 42.
- Sanitization: proposal-stage invalid-unit dropping enabled.
- Exclusions: `domain_test`, P4, P5, full ablation grid.
- Model calls: forbidden in config and not performed.
- GPU: not visible.

## Command

Remote command:

```bash
cd /root/project
test ! -e /dev/nvidia0
/root/autodl-tmp/venvs/equipment-ie/bin/python scripts/run_p3_extraction.py \
  --config configs/p3_domain_dev50_a_k5_sanity_sanitize_dryrun.yaml \
  --dry-run
```

## Result

```json
{
  "run_id": "p3-domain-dev50-a-k5-seed42-sanity-sanitize-dryrun",
  "dataset": "domain_dev50",
  "query_records": 50,
  "model_calls": 0,
  "api_called": false,
  "model_weights_loaded": false,
  "gpu_device_present": false,
  "max_prompt_chars": 3953,
  "config_sha256": "ed53bfb602ac736e6d1042f1a66cad37ec092109559b226b2bdbcda6189b65e8",
  "dry_run_prompts_sha256": "fa80e30942902e7a2dc27288c9a71b91a00169aba14a75f9cbee6ebb43f73b52"
}
```

Fixed examples selected:

- `domain-candidate-0004`
- `domain-candidate-0027`
- `domain-candidate-0078`
- `domain-candidate-0186`
- `domain-candidate-0203`

## Local Backup

Copied to:

```text
D:\yinsir\backups\P3\p3_domain_dev50_sanitize_dryrun_20260722\
```

Local SHA256:

| File | SHA256 |
| --- | --- |
| `p3_domain_dev50_a_k5_sanity_sanitize_dryrun_manifest.json` | `8c87ce5bd75454a520ed73391cb2f56270962ec99c20c317537c7277ec9f12c9` |
| `p3_domain_dev50_a_k5_sanity_sanitize_dryrun_prompts.jsonl` | `fa80e30942902e7a2dc27288c9a71b91a00169aba14a75f9cbee6ebb43f73b52` |

## Gate Status

The dry-run gate passed:

- all 50 dev rows were planned;
- prompt construction completed;
- max prompt length stayed well below the 8192 model context budget;
- no model API was called;
- no GPU was visible;
- no test/P4/P5 artifact was touched.

Next allowed action, only after explicit human approval, is a paid-GPU
execution of this same `domain_dev50` config A sanitize sanity. Do not run
`domain_test`, P4, P5, or the ablation grid yet.
