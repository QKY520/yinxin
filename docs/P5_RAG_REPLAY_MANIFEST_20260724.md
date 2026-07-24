# P5 D RAG Replay Manifest - 2026-07-24

## Scope

Human approved the GPU-free stage after the P5 pilot diagnostics. The goal was
to prepare a fixed RAG replay manifest for future P5 D execution without
starting paid GPU, vLLM, dry-run, or any model call.

The step reads existing P5 D artifacts and frozen `domain_test` metadata for
hash validation. It does not tune prompts, glossary, RAG parameters, verifier,
thresholds, or model settings.

## Attempt History

1. Directly rebuilding RAG selections from the fixed D config in GPU-free mode
   was attempted with valid CPU thread environment:

   ```text
   OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
   ```

   This was killed by the no-card environment with exit code 137 before writing
   a manifest. No artifact was produced. The empty build log is preserved at:

   - remote: `/root/project/logs/p5_domain_test_d_rag_k5_seed42_replay_manifest_build.log`
   - local: `D:\yinsir\logs\p5_domain_test_d_rag_k5_seed42_replay_manifest_build.log`

2. The successful path converted the already completed P5 D per-query result
   into a replay manifest. This avoids reloading CPU BGE/reranker and preserves
   the exact RAG passage IDs and display strings used in the paid seed-42 D run.

   Source per-query file:

   ```text
   /root/project/results/p5/p5_domain_test_d_rag_k5_seed42_per_query.jsonl
   ```

   Source per-query SHA256:

   ```text
   ebaa68c940223ff8688377f63a3f9dbafefaf561382b6a3445c5cdda354a1ed0
   ```

## Artifacts

Remote:

- `/root/project/logs/p5_domain_test_d_rag_k5_seed42_replay_manifest.json`
- `/root/project/logs/p5_domain_test_d_rag_k5_seed42_replay_manifest_validation.json`
- `/root/project/logs/p5_domain_test_d_rag_k5_seed42_replay_manifest_build.log`

Local synced copies:

- `D:\yinsir\logs\p5_domain_test_d_rag_k5_seed42_replay_manifest.json`
- `D:\yinsir\logs\p5_domain_test_d_rag_k5_seed42_replay_manifest_validation.json`
- `D:\yinsir\logs\p5_domain_test_d_rag_k5_seed42_replay_manifest_build.log`

Hashes:

| Artifact | SHA256 |
| --- | --- |
| replay manifest | `00f292c2d4c1f2e0e732af88518b2e2624e7266e9a64c7cc5f0049e563002685` |
| validation report | `c868be6363eb67b91b528e4ddf06e8f022b74f24a3735a7a0b759aa9a5a63563` |
| empty failed-build log | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## Validation

Validation report:

```text
/root/project/logs/p5_domain_test_d_rag_k5_seed42_replay_manifest_validation.json
```

Key checks:

- `passed: true`
- rows: 170
- unique query IDs: 170
- query records: 170
- passages per row: min 3, max 3
- replay selector selected passages: min 3, max 3
- `domain_test` query SHA256 matched:
  `42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0`
- source D per-query SHA256 matched:
  `ebaa68c940223ff8688377f63a3f9dbafefaf561382b6a3445c5cdda354a1ed0`

AutoDL was in GPU-free/no-device mode for this stage:

```text
No devices were found
GPU_FREE_OR_NVIDIA_SMI_UNAVAILABLE
```

Unit tests after adding per-query replay support:

```text
~/venv/bin/python -m unittest tests.test_extraction
Ran 18 tests in 0.094s
OK
```

## Use Constraint

This replay manifest is for future explicitly approved P5 D-style execution
only. Do not silently switch a config to `rag.mode: replay_manifest` without a
new bounded gate, because doing so changes the execution path even though the
RAG text is fixed from the previous D run.
