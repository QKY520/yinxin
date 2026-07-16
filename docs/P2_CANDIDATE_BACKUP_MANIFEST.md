# P2 Candidate-Stage Backup Manifest

Status: candidate collection backed up; formal annotation not started

Verified at: 2026-07-16T09:12:34+08:00

Boot mode: GPU-free (`/dev/nvidia0` absent)

Code commit at backup: `9e99cbac5d43960c87796aaf6fc5f52bb4e4369f`

Machine-readable counterpart: `docs/p2_candidate_backup_manifest.json`.

## Archive

- Remote: `/root/autodl-tmp/backup/p2/p2_candidate_stage_20260716.tar.gz`
- Local private copy: `D:\yinsir\backups\P2\p2_candidate_stage_20260716.tar.gz`
- Bytes: `119550484`
- SHA256: `6879810924e417f58b6c2ef32932a526c39c7da74f4dedbf849c0d202afa26ce`
- Archive entries: `373`
- Remote `gzip -t`: passed
- Remote SHA256 check: passed
- Local SHA256 check: passed
- Remote and local entry counts: `373`
- Content listing: `p2_candidate_stage_20260716.contents.txt` beside both copies

The archive contains the full `/root/autodl-tmp/data/p2` source/cache tree plus
the selected candidates, seed terms, collection config, structured log, stdout,
deduplication record, and collection report. It is private and ignored by Git.

## Core Artifacts

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `/root/autodl-tmp/data/domain_candidates.jsonl` | 429919 | `32622228a7e0d45b31ce7ee2c0f78bcad0a5aa4a07ad8d01212bd03d3c19ee4f` |
| `/root/autodl-tmp/data/domain_seed_terms.jsonl` | 1505648 | `4e65516b2aa7ebbb06377f5724a4f31ab13e11bbeaee9f4bc9f13999f6c37171` |
| `/root/autodl-tmp/backup/p2/candidate_dedup.json` | 594 | `0c288474512641ac988bf21d33c4fd43105c3e4407e66dc4208423441dbd524e` |
| `/root/autodl-tmp/backup/p2/collection_report.json` | 4988 | `6dc9a92ef370904c2fa912876c2365e5993d6e7425da46a305cfc2fd65e93a28` |
| `/root/project/logs/p2_collection.jsonl` | 1705 | `cd35b70066791f310ee4ea55ae7a0dbfab2cdce325e0de63d025e010e75c2906` |
| `/root/project/logs/p2_collect_stdout.log` | 685 | `4a1bc3f7bbcb29106d6c604a640a2e13935c7a9e7c9b6a66b13da6328bcbeb02` |
| `/root/project/configs/p2_domain_data.yaml` | 3168 | `7f1b7ce8ec6ac20a52d8c453cc8f255eccacef80b8131da716a1cee0f1f0522f` |

Each lightweight core artifact was also copied separately under the local
private `D:\yinsir\backups\P2` directory and hash-checked.

## Collection Result

- Candidate records: `400`
- Source counts: Baidu Baike `7`, patent abstracts `84`, CMNEE `309`
- Candidate-stage 8-gram removals: `3`
- Seed terms: `5770`
- Candidate round trip: passed
- Formal annotation: not started
- Paid GPU use: none

This is not Gate 2 completion. It does not contain approved annotations,
`domain_support.jsonl`, `domain_dev.jsonl`, `domain_test.jsonl`, `FROZEN`, or
the final test-to-RAG deduplication log.

## License Boundary

- The KPPatent-ZH source is pinned with its MIT license.
- CMNEE is pinned with Apache-2.0 source metadata.
- QAonMilitaryKG source licensing is `NOASSERTION`; seed terms remain private.
- Baidu Baike cache and all corpus-derived candidate text remain private.
- No source text, seed dictionary, or private archive is committed to Git.
