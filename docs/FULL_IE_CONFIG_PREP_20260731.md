# FULL-IE F3 Configuration And Resource Preparation

Date: 2026-07-31
Gate: `FULL_IE_F3_CONFIG_PREP_APPROVED`
Status: `DONE` (`PREPARED_NOT_AUTHORIZED` for all future-run configs)

## Outcome

F3 completed in AutoDL GPU-free/no-card mode. It prepared the exact resources,
hashes, and future F4 runner configs required for a bounded domain-dev and
CLUENER-tune sanity. It did not run an empirical experiment and does not change
the full-IE evidence count (`0/60`).

## Prepared Resources

| Resource | Result | SHA256 |
| --- | ---: | --- |
| CLUENER support bank | 30 records; all 10 types covered | `abd6a338bf393426f35e12a08d073c6661e59131bc52ae77ca9f96d8859a5219` |
| CLUENER tune subset | 50 records; all 10 types covered | `7264b03d3e34a3213281cc1858d073fe86104d5f8d055050ba658ee950d8ade5` |
| Support-only glossary | 61 exact surface/type entries | `0ac4dc41ceb9c458250354fef3826c8b21a9d128c9491a6477b2171f03ba3a9b` |
| Labels-stripped RAG corpus | 9,584 train-pool text rows | `f0b0cef66415bff65537076d1ab16552038dcb4388ed22c133255057ac2eb7ee` |
| Dedup report | 89 removed rows | `c9f610d3a51ff7978c14f1bab16e284d4281ca3774f470acc56c70dab8de471c` |

The fixed deduplication protocol used character 8-gram containment at threshold
`0.80`. It removed 30 exact support IDs, 34 tune overlaps, 24 CLUENER-dev text
overlaps, and one additional support overlap. The official CLUENER dev file was
used only as a text-only final-evaluation blocklist; its labels were not used for
prompting, metrics, model selection, or tuning.

## Prepared Configs

- Six domain dev cells: A/B/C/D Stage N+R and E/E-prime entity+relation atomic
  verification, K=5 seed42.
- Six CLUENER tune cells: A/B/C/D NER and E/E-prime entity-only verification,
  K=5 seed42.
- `16` executable stage YAMLs plus one `12`-cell run matrix.
- All YAMLs have `authorized: false` and `model_calls_allowed: false`.
- No YAML contains a `domain_test`, CLUENER official dev, or unlabeled test run
  path. No prompt or per-query artifact was generated.

## Implementation And Validation

Added the F3 preparation/validation module and CLI, extended the future model
gates without authorizing them, and added CLUENER entity-only E/E-prime support.
The current F3 gate token is rejected by every model runner.

- New F3 synthetic tests: `5/5` passed.
- Affected full-IE runner tests: `9/9` passed.
- Full repository test suite on AutoDL: `173/173` passed.
- Independent manifest validation: `74` files checked; all hashes and copied
  artifacts matched.
- Final mode: `No devices found`, `/dev/nvidia0` absent, and no vLLM/Qwen/model
  process.

Manifest SHA256:
`6302052aca1602d73bb96b53b1d702bebabc548f0e9fa694a7d317b0f2e7aa44`.

Report SHA256:
`eaab6f7a11ede8d9240e81acea9ca88e4a9e90ee56d852357fa9eb02617f5964`.

Remote package:
`/root/autodl-tmp/backup/full_ie/f3_config_prep_20260731/`.

Local package:
`backups/FULL_IE/f3_config_prep_20260731/`.

## Safety And Cost

- `domain_test`: not read.
- Real prompt generation: none.
- Model/API/vLLM calls: none.
- GPU: none.
- Manuscript edits: none.
- GitHub sync: none.
- Paid cost: `0 CNY`.

## Next Gate

F4 remains closed. The immediate next subgate is
`FULL_IE_DOMAIN_DEV_SANITY_APPROVED`, limited to DDEV1/DDEV2. It must stop after
domain-dev metrics and the required verifier drop audit. CLUENER tune sanity
requires the later separate `FULL_IE_CLUENER_TUNE_SANITY_APPROVED` gate. Neither
gate authorizes `domain_test`, final CLUENER evaluation, F5/F6, paper edits, or
GitHub sync.
