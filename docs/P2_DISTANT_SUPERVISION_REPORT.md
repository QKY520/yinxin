# P2 Distant-Supervision Report

Status: completed and backed up; stopped before 14B or human annotation

Run time: 2026-07-16T10:55:09+08:00

Execution mode: GPU-free (`/dev/nvidia0` absent)

Generation commit: `269cc5384a17490284796802bb3e18c9ef50c3e1`

Independent verifier commit: `ea6c36fdf5a0504a7b11ffc6aa2fad4fdad38740`

## Method

- Input: 400 unchanged candidate passages and 5770 private QAonMilitaryKG seed
  terms, both pinned by SHA256.
- Matching: deterministic, exact, longest-first, non-overlapping string match.
- Suggested type: `EQUIPMENT` only.
- Relations: never inferred; every proposal has an empty relation list.
- The proposals are machine suggestions, not gold labels.
- LLM disagreement fields remain `NOT_COMPUTED_LLM_NOT_RUN`.
- All human annotation and adjudication fields remain `NOT_STARTED` or blank.

## Statistics

| Measure | Value |
| --- | ---: |
| Candidate passages | 400 |
| Passages with at least one seed match | 15 |
| Passages without a seed match | 385 |
| Match coverage | 3.75% |
| Proposed entities | 23 |
| Proposed relations | 0 |
| Unique matched spans | 17 |

| Source | Candidates | Matched candidates |
| --- | ---: | ---: |
| Baidu Baike | 7 | 5 |
| Patent | 84 | 0 |
| CMNEE | 309 | 10 |

The low coverage is preserved as the honest outcome of exact dictionary
matching. No fuzzy matching, glossary expansion, or favorable filtering was
introduced after seeing the result.

## Outputs

| Artifact | Records | Bytes | SHA256 |
| --- | ---: | ---: | --- |
| `domain_distant_supervision.jsonl` | 400 | 283945 | `b40e9d5c34c27d22b699d758af79c88705e4e4637184458aaae04bbaa05af96b` |
| `p2_review_sheet_distant_supervision.jsonl` | 400 | 597326 | `47ed7376af38e0909739e7d1f1f4faa8189b1c900b7fa241f0479c75a7f87993` |
| `p2_review_sheet_distant_supervision.csv` | 400 | 681271 | `c6cc5f34c0deccb4c6dbc113b63cd9fc6682ea0161272fa4c0e129daee766cbe` |
| `distant_supervision_report.json` | 1 | 2720 | `2fbf5cd839b5b1998db198364f462e8a03091f1866029c303f729c31a81c3c23` |
| `p2_distant_supervision.jsonl` | 1 | 943 | `53a3b19087bfb548fd3901a5a5d313eeb0624967f342e60970a50c595d1acf5c` |

The source-bearing artifacts are private under `/root/autodl-tmp` and
`D:\yinsir\backups\P2`; they are ignored by Git.

## Backup

- Remote archive:
  `/root/autodl-tmp/backup/p2/p2_distant_supervision_20260716.tar.gz`
- Local private archive:
  `D:\yinsir\backups\P2\p2_distant_supervision_20260716.tar.gz`
- Bytes: `413471`
- Entries: `11`
- SHA256:
  `15908dca3bb768f9175fac62c9d04e2f0dc5762423563f1d61029d21c4d24701`
- Remote `gzip -t`: passed
- Remote SHA256 check: passed
- Local SHA256 and entry-count checks: passed

## Verification

- Independent row-level verification: passed.
- Proposal, JSONL review sheet, and CSV IDs/order/text/entities/relations agree.
- All 400 proposal and review records reload successfully.
- All human CSV columns are blank; all human JSON fields are untouched.
- LLM use, paid GPU use, splitting, freezing, and human annotation are all
  recorded as false.
- Full remote test suite: 27/27 passed.
- `domain_support.jsonl`, `domain_dev.jsonl`, `domain_test.jsonl`, and `FROZEN`
  remain absent.

## Current Gate

Stop before Qwen2.5-14B-AWQ assisted refinement. Starting that stage requires:

1. a proposed sanity batch, runtime/cost estimate, output/cache plan, and stop
   conditions;
2. the human's explicit 14B and budget approval;
3. the human switching AutoDL from GPU-free to paid GPU mode;
4. a fresh `nvidia-smi` and conflicting-process check before launch.

Human annotation remains a separate human action after LLM suggestions have
been generated and reviewed operationally.
