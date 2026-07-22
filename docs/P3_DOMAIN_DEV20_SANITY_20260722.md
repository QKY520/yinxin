# P3 Domain Dev20 Sanity Report - 2026-07-22

## Scope

The human explicitly rejected CLUENER-focused sanity for the current paper
route and requested equipment-domain sanity only. This run therefore used the
self-built equipment-domain data:

- support: `/root/autodl-tmp/data/domain_support.jsonl`
- query: first 20 rows of `/root/autodl-tmp/data/domain_dev.jsonl`
- model: Qwen2.5-7B via vLLM
- config: A
- examples: fixed-random
- K: 5
- seed: 42
- no glossary
- no RAG
- no self-verification
- no domain test
- no P4/P5

## Pre-Run Checks

- GPU: RTX 4090
- memory before vLLM: `0 MiB / 24564 MiB`
- conflicting GPU processes: none
- vLLM served model:
  `/root/autodl-tmp/models/qwen2.5-7b`
- 20-row query subset:
  `/root/project/cache/p3_domain_dev20_seed42.jsonl`

Dry-run result:

- query records: `20`
- model calls: `0`
- max prompt chars: `3953`
- prompt manifest SHA256:
  `3c40e43ca38f1bd23319820ddc1c0cc0323081386e6c48129b5f1159b30a711d`

## Result

Run ID:

- `p3-domain-dev20-a-k5-seed42-sanity`

Metrics:

- query records: `20`
- parse failures: `9`
- parse-failure rate: `45.0%`
- entity micro precision: `0.5778`
- entity micro recall: `0.4031`
- entity micro F1: `0.4749`
- per-query SHA256:
  `27e446ac8ea32c8c8c2d083b3854a8e1348c6e3d1e59d1eb97f916eb9ddc00bc`

Gate status:

- F1 is nonzero.
- Parse-failure rate is far above the `<5%` P3 gate.
- P3 domain sanity failed.

## Failure Diagnosis

The failures are not random infrastructure failures. The 7B model produced
useful entities in many rows, but strict whole-record parsing failed often.

Main parse-error categories:

- overlapping or nested entities;
- duplicate entities after retry;
- model-generated spans not exactly present in the source text, such as
  removing punctuation or normalizing commas;
- unsupported schema types such as `ORG`;
- span boundary mismatch for quoted equipment names.

This shows that prompt-only correction is insufficient for the equipment
domain under the current strict whole-record parser.

## Backup

Remote archive:

- `/root/autodl-tmp/backup/p3/p3_domain_dev20_sanity_20260722.tar.gz`

Local archive:

- `D:\yinsir\backups\P3\p3_domain_dev20_sanity_20260722.tar.gz`

Archive size:

- `43069` bytes

Remote/local archive SHA256:

- `775955d7b3c099ff63f1d70e384401e349363b3a74aae405cf01ada1f7ce35b6`

## Cost Estimate

The agent-managed domain vLLM window was approximately 15:00-15:12
Asia/Shanghai on 2026-07-22, about 12 minutes.

At the previously recorded 2.7 CNY/hour, this is about:

- `0.20 hours * 2.7 = 0.54 CNY`

Platform billing is authoritative.

## Next Recommendation

Do not continue paid GPU retries in the same form.

The next step should be GPU-free:

1. Keep strict exact-span evaluation for final metrics.
2. Add a proposal-stage sanitization layer that can drop invalid entities and
   relations with explicit flags instead of failing the whole record.
3. Log invalid-unit counts separately from full-record parse failures.
4. Dry-run the revised domain config.
5. Ask the human before another small paid-GPU retry.

Do not run domain test, P4, P5, or the full ablation grid until a domain P3
sanity passes.
