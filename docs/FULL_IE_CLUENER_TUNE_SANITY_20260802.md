# FULL-IE F4b CLUENER Tune Sanity

Date: 2026-08-02
Gate: `FULL_IE_CLUENER_TUNE_SANITY_APPROVED`
Status: `DONE_WITH_NEGATIVE_VERIFICATION_EVIDENCE`

## Outcome

The bounded F4b CLUENER tune sanity is complete. CDEV1 ran A/B/C/D NER and
CDEV2 ran entity-only E-prime over C and E over D on the deterministic
50-record `cluener_tune_subset50_seed42.jsonl`, always at K=5 and seed42.

CDEV1 passes its structural sanity gate: every config has 50 reloadable rows,
zero parse failures, zero unsupported entity types, verified prompt/config/
resource hashes, and complete prompt/cache/raw-response provenance. D is the
strongest row on this tune subset, but this is not final public generalization
evidence.

Neither CDEV2 row passes the positive verification-claim gate. E-prime lowers
F1 and has a `65.79%` correct-drop rate. E raises F1 by only `0.005556`, while
its `69.44%` correct-drop rate is just below the pre-specified `70%` threshold.
Both outcomes are retained. These six tune sanity rows are not final reported
cells, so full-matrix accounting remains `0/60`.

## Scope And Preflight

- Human-reported price: `2.8 CNY/hour` for the RTX 4090 24 GB.
- Preflight GPU: NVIDIA GeForce RTX 4090, `24,564 MiB` total, `0 MiB` used.
- No conflicting vLLM, Qwen, extraction, verification, or screen process was
  present before launch.
- Only the SSH alias `autodl-paper` was used. No project Python ran on Windows.
- The F3 files were not edited. Six dated execution configs were copied to
  `configs/full_ie_f4b_cluener_tune_20260802/` and given only the bounded F4b
  authorization and new output/cache paths.
- Frozen query/support/glossary/RAG resource SHA256 values were rechecked.

## CDEV1 Results

All metrics below were independently recomputed from the 50 per-query rows.
FP is an exact entity false-positive count.

| Config | Precision | Recall | F1 | TP | FP | FN | Parse failures | Retry rows | Mean total ms/query |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | `0.495798` | `0.556604` | `0.524444` | 59 | 60 | 47 | `0/50` | 2 | `908.904` |
| B | `0.580000` | `0.547170` | `0.563107` | 58 | 42 | 48 | `0/50` | 5 | `1829.199` |
| C | `0.576923` | `0.566038` | `0.571429` | 60 | 44 | 46 | `0/50` | 4 | `812.462` |
| D | `0.627273` | `0.650943` | `0.638889` | 69 | 41 | 37 | `0/50` | 8 | `7608.604` |

The clean tune-only deltas are B-A `+0.038662`, C-B `+0.008322`, and D-C
`+0.067460` F1. C and D replay B's exact per-query demonstration IDs. D has
exactly three RAG passages for every query and zero query self-hits. These
single-seed tune results may guide a later separately approved freeze decision,
but they cannot be reported as final CLUENER results.

D's mean RAG selection time is `6668.675 ms/query`, versus a mean total time of
`812.462 ms/query` for C. The large D latency is therefore primarily the CPU
embedding/reranking path and must remain visible in later feasibility review.

The extraction sanitizer retained all rejected-unit events in the per-query
rows: A/B/C/D have `22/17/15/11` events. These are structured-output cleanup
diagnostics, not parse failures or evidence of higher task quality.

## CDEV2 Results And Deletion Audit

Only entity atoms were verified. CLUENER relations remained empty throughout.
Invalid verifier output is conservatively kept by contract; both runs had zero
invalid outputs.

| Config | Source | Raw P/R/F1 | Verified P/R/F1 | F1 delta | FP raw -> verified | Correct drops | Drop rate | Positive gate |
| --- | --- | --- | --- | ---: | --- | --- | ---: | --- |
| E-prime | C | `0.576923/0.566038/0.571429` | `0.712121/0.443396/0.546512` | `-0.024917` | `44 -> 19` | `25/38` | `65.79%` | FAIL |
| E | D | `0.627273/0.650943/0.638889` | `0.783784/0.547170/0.644444` | `+0.005556` | `41 -> 16` | `25/36` | `69.44%` | FAIL |

E-prime deletes 25 false positives and 13 true positives. E deletes 25 false
positives and 11 true positives. Both increase precision while reducing recall.
E-prime is clearly negative on F1; E has a small positive F1 delta but misses
the `>=70%` correct-drop requirement by one deletion. Neither supports a
positive CoVe/self-verification claim.

Mean verifier time is `101.711 ms/query` for E-prime and `131.076 ms/query` for
E. The complete 74-row deletion audit is retained; no favorable subset was
selected.

## Hashes And Provenance

Execution config SHA256:

| Config | SHA256 |
| --- | --- |
| A | `bfdff2840afdb783f16410dd082a2bdc988cb925a254c3de9623d67f4c3fa2f3` |
| B | `0f122a1a1068ff916f3ad51e271e93e1659e893f96da7de351330dee769f9319` |
| C | `0e1e3f0047973404e28506d8537ce6330adc11dde8998a7a93084eecc1c59514` |
| D | `a4b947e95d001deae7edd53694722d0712d0852a2a05964805ed0ca01d1d41de` |
| E | `07da828df12535ec4ac8f45410cf39bd0ae3d99902ed4ae4f446b693ec62146e` |
| E-prime | `179823a6f0a0b628c0a76ec92697fb19ad64ff215a9441fd8cf1b1e2739e9b04` |

Frozen resource SHA256:

- query subset: `7264b03d...d8ade5`;
- support bank: `abd6a338...9a5219`;
- support-only glossary: `0ac4dc41...3ba3a9b`;
- labels-stripped RAG corpus: `f0b0cef6...ac2eb7ee`.

Per-query SHA256 A/B/C/D/E-prime/E:

- `eba8b783...46dd5`;
- `e70d00b1...a326`;
- `74aab9fc...68c3f`;
- `59fd2238...73d5`;
- `83241e1a...d4e2`;
- `e5f5b966...da22`.

The independent audit links all 219 extraction attempts and 214 verifier
requests to exactly 433 cache files. Every cache file contains the complete
prompt, parsed content, raw vLLM response, request/config hash, and raw-output
hash. There are no missing or orphaned cache files.

- Summary SHA256:
  `80997aef4e53d5494f5902932ef477d7cbdfb36b59ba13d7959568074bd5c8f1`.
- Full deletion-audit SHA256:
  `6c320f5196ad025f7848a553e834ce1fdc263e202f583c25505daa8ac81fa998`.
- Cache-index SHA256:
  `9d7cef2053823db805f34b7ded08f1ed10ca2b296c371a5c8b4976a9d1b22f1f`.

## Validation And Backup

- Focused F4b summarizer tests: `5/5` passed on AutoDL.
- Git-tracked regression suite plus the new F4b tests: `177/177` passed on
  AutoDL. Untracked M1/P6 tests were deliberately not executed.
- Remote and local package manifests: `489/489` files verified.
- Manifest SHA256:
  `6d9f03466a7a46b41d2925e834d627d52481690ddf06548ddc129a659849f7de`.
- Archive SHA256:
  `75622decfd91bd460e782da4d4694fa6bcba8187e22ec7e0a16cf62cf4d5dd4a`.
- Remote backup:
  `/root/autodl-tmp/backup/full_ie/f4b_cluener_tune_20260802/`.
- Local backup:
  `backups/FULL_IE/f4b_cluener_tune_20260802/`.

## Machine State And Cost

The vLLM service ran from `2026-08-02 10:14:16` through `11:13:03 CST`, an
observable `3,527 s = 0.979722 h`. At `2.8 CNY/hour`, the attributable service
window estimate is `2.7432 CNY`, rounded to `2.74 CNY`. This is not the AutoDL
platform bill; boot-to-no-card billing may be longer and the platform remains
authoritative.

vLLM was stopped after E completed. GPU memory returned to `0 MiB`, and no
vLLM/Qwen/extraction/verifier process or screen session remained. The final
closeout check at `13:45:59 CST` found the instance already back in no-card mode
(`No devices were found`).

## Safety, Claims, And Next Gate

- Official CLUENER dev and unlabeled test were not evaluated or prompted.
- `domain_test` was not read.
- No K=1/K=10, seed43/44, F5/F6, final matrix, manuscript, or GitHub action
  occurred.
- Failed attempts, parser retries, sanitizer events, and negative verifier
  outcomes are preserved in logs/cache/per-query rows.
- F4b's gate is consumed. No experiment or protocol-freeze gate is currently
  open.
- Current supported paper evidence remains the frozen three-seed narrow
  equipment-domain NER result. F4b adds tune-only feasibility and negative/
  mixed verifier diagnostics, not public generalization or CoVe evidence.
- The next planned phase is F5 protocol freeze, but it requires a new bounded
  human approval. Until then, stop.
