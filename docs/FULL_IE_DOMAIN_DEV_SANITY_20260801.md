# FULL-IE F4a Domain Dev Sanity

Date: 2026-08-01
Gate: `FULL_IE_DOMAIN_DEV_SANITY_APPROVED`
Status: `DONE_WITH_LIMITATIONS`

## Outcome

The bounded F4a domain-dev sanity is complete. DDEV1 ran A/B/C/D Stage N plus
Stage R on `domain_dev50` at K=5 seed42, and DDEV2 ran relation-aware E and
E-prime over the corresponding D and C outputs. These are dev-only diagnostics,
not final reported cells. The literal full-IE matrix therefore remains `0/60`.

The run establishes that the two-stage implementation executes end to end and
that E-prime has a local positive dev signal. It also exposes severe relation
quality limits: exact RE F1 is below `0.057` for every A-D configuration, no
configuration recovers a `HAS_METRIC` true positive, D misses the strict
per-configuration parse-failure gate, and E is negative after verification.

## Bounded Protocol Revision

The preserved v0 A Stage R attempt used strict whole-response rejection and
failed to parse relations on `38/50` rows. The single dev-only protocol revision
allowed by the gate was then consumed:

- changed only `parsing.drop_invalid_relations` from `false` to `true`;
- retained the prompt, schema, model, generation settings, exact direction,
  duplicate policy, Stage N outputs, and all raw model outputs;
- logged each rejected relation atom as `RELATION_DROPPED_INVALID_UNIT`;
- preserved the failed v0 config, log, per-query rows, and summary in the final
  backup.

No second protocol revision is permitted under the consumed F4a gate.

## DDEV1 Results

All values below are independently recomputed from the 50 per-query rows.

| Config | NER F1 | Exact RE P | Exact RE R | Exact RE F1 | RE parse failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | `0.527273` | `0.061404` | `0.052632` | `0.056680` | `1/50` (`2%`) |
| B | `0.506135` | `0.061538` | `0.030075` | `0.040404` | `2/50` (`4%`) |
| C | `0.523169` | `0.055556` | `0.030075` | `0.039024` | `1/50` (`2%`) |
| D | `0.501548` | `0.020408` | `0.007519` | `0.010989` | `3/50` (`6%`) |

The aggregate relation parse-failure rate is `7/200 = 3.5%`, but the
pre-specified stricter requirement that every configuration remain below `5%`
fails because D is at `6%`. All four exact RE F1 values are nonzero and all rows
reload, so F4a is closed as completed with limitations rather than rerun.

The sanitizer removed `577` invalid relation atoms: A `256`, B `111`, C `99`,
and D `111`. This is evidence of weak structured relation compliance, not a
model-quality gain. Across the 133 gold relation triples, all configurations
have zero `HAS_METRIC` true positives; only A has any `PART_OF` true positives.
Gold endpoint coverage is only `30.83%` to `39.85%`.

D also provides no positive RAG signal on this sanity: its NER and RE F1 are
both below C. D's Stage N RAG selection adds a mean `8190.355 ms/query`, so the
observed D latency is materially worse and must remain visible in later
result-to-claim analysis.

## DDEV2 Results

| Config | Metric | Raw F1 | Verified F1 | Delta |
| --- | --- | ---: | ---: | ---: |
| E-prime | NER | `0.523169` | `0.540816` | `+0.017647` |
| E-prime | exact RE | `0.039024` | `0.051613` | `+0.012589` |
| E | NER | `0.501548` | `0.495479` | `-0.006069` |
| E | exact RE | `0.010989` | `0.000000` | `-0.010989` |

E-prime passes the local dev positive gate. Its entity deletions are correct for
`65/81 = 80.25%` of dropped entities, and its `50/50` unique dropped relations
are correct under exact-gold membership. Entity deletion cascaded to 15
incident relations. Precision rises while recall falls, so the positive result
is specifically a deletion-quality trade-off rather than recovery of missed
units.

E passes both drop-audit thresholds but fails the positive-F1 requirement. Its
entity deletions are correct for `68/93 = 73.12%`, and `26/27 = 96.30%` of its
unique dropped relations are correct; nine incident relations are cascade
drops. Nevertheless, verification removes the only raw relation true positive
and lowers both NER and RE F1. E is therefore a mixed/negative dev result.

No invalid verifier output occurred in these two runs. The implementation's
conservative keep-on-invalid behavior remains covered by synthetic tests.

## Verification And Backup

The F4a summarizer reloads raw per-query rows and independently verifies file
SHA256 values, 50-row alignment, Stage N entity preservation, NER and exact
directed RE metrics, E/E-prime raw and verified metrics, verifier decisions,
entity-to-relation cascades, and sanitizer events.

- Targeted summarizer tests: `5/5` passed on AutoDL.
- Full repository suite: `178/178` passed on AutoDL.
- Final package manifest: `1,403` files, all verified locally and remotely.
- Summary SHA256:
  `c5e9df2c6a0c8d083670c64e604b2b881b23c33f3ac183a7d365433628d1309d`.
- Manifest SHA256:
  `26e7350fd7def8e3d4d3fb7cee3db6547d687b2ad5995bb43ad7bdfecd4ee216`.
- Archive SHA256:
  `96f586f3425d3bda77e456d6f19612d10b1aeeba729f0c0e1df9e6f0d9eae4e3`.
- Remote backup:
  `/root/autodl-tmp/backup/full_ie/f4a_domain_dev_sanity_20260731/final_r1_20260801/`.
- Local backup:
  `backups/FULL_IE/f4a_domain_dev_sanity_20260731/final_r1_20260801/`.

Final status at 2026-08-01 20:15 CST was GPU-free/no-card: `nvidia-smi -L`
returned `No devices found`, `/dev/nvidia0` was absent, no screen session
remained, and no vLLM/Qwen/Stage R/verifier process was running.

## Safety And Cost

- `domain_test`: not read.
- CLUENER tune/final data: not run.
- Manuscript edits: none.
- GitHub synchronization: none.
- Observable vLLM activity: approximately 46 minutes 23 seconds, or about
  `2.1 CNY` at `2.7 CNY/hour`.

The `2.1 CNY` value is a process-window estimate, not a platform bill. Paid GPU
mode remained active after one model window; the 2026-08-01 start-to-human
no-card switch envelope alone was about 2.5 hours. The AutoDL billing page is
authoritative, and actual cost can therefore be higher.

## Claim Boundary And Next Gate

F4a supports only implementation feasibility and a local E-prime dev signal.
It does not support a final RE, CoVe, RAG, public-generalization, K-robustness,
or full-matrix claim. The next planned step is the separate bounded
`FULL_IE_CLUENER_TUNE_SANITY_APPROVED` gate for CDEV1/CDEV2. That gate is closed
until explicitly granted and does not authorize `domain_test`, final CLUENER
evaluation, F5/F6, paper edits, or GitHub synchronization.
