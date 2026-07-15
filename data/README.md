# Data Storage

Datasets are not committed to Git. Public and self-built datasets are stored on
the AutoDL data disk and backed up separately. This directory may hold the
tracked `FROZEN` marker after the domain test split is finalized.

P1 writes normalized files to `/root/autodl-tmp/data/<dataset>_<split>.jsonl`
using the unified schema documented in `AGENTS.md`. Files ending in
`_test_unlabeled.jsonl` contain official test text without gold annotations and
must never be treated as all-negative evaluation data. Few-shot support files
are deterministic unions of K sampled training records per entity type and are
named with both K and seed.
