# P5 GPU-Free Code Audit - Relations And RAG Runtime - 2026-07-24

## Scope

This audit follows the P5 domain-test pilot diagnostic. It is code-only and
artifact-only:

- no local Python;
- no paid GPU;
- no vLLM startup;
- no dry-run;
- no new prompt generation;
- no model calls;
- no `domain_test` tuning.

The audit inspected existing configs, source code, logs, summaries, per-query
rows, and cached raw outputs.

## Question 1: Why Are Relations All Zero?

Conclusion: the P5 A/B/C/D pilot was run through the NER-only extraction path.
Zero relation predictions are expected from the current configuration and
runner, not evidence that the model tried and failed at relation extraction.

Evidence:

1. All approved P5 A/B/C/D configs set `schema.task: ner` and
   `relation_types: {}`. With an empty relation type matrix, relation extraction
   is not enabled.

2. `scripts/run_p3_extraction.py` calls `build_ner_prompt(...,
   include_relations=False, ...)` in both dry-run prompt construction and real
   execution paths. The real execution call is in the non-dry `run_execute`
   path.

3. `src/equipment_ie/extraction.py` builds examples with
   `record_as_model_json(example, include_relations=include_relations)`. When
   `include_relations=False`, support examples always show an empty
   `"relations":[]` field.

4. The prompt output format in `build_ner_prompt` explicitly shows:

   ```json
   {"entities":[{"span":"...","type":"...","occurrence":1}],"relations":[]}
   ```

5. The parser supports relations only when a non-empty `relation_types` matrix
   is passed. If raw relations appear while relations are disabled, the parser
   can drop or reject them depending on sanitization mode. In the P5 pilot,
   relation sanitization did not fire.

6. Existing cached raw outputs confirm the model generally followed the NER-only
   instruction:

   | Config | Raw outputs with `relations: []` | Raw outputs missing/non-list relations | Raw outputs with non-empty relations |
   | --- | ---: | ---: | ---: |
   | A | 168 | 1 | 0 |
   | B | 169 | 1 | 0 |
   | C | 169 | 1 | 0 |
   | D | 169 | 1 | 0 |

   The remaining A row was invalid for this raw-cache probe, but the official
   per-query parse did not fail. No row had cached non-empty raw relations.

Implication:

- The P5 pilot currently supports NER only.
- The RE metric of 0 is a configuration/coverage limitation, not a meaningful
  negative comparison between A/B/C/D.
- Do not describe A/B/C/D relation F1 as a model failure in the paper. Describe
  RE as not enabled in this pilot, or run a separately approved relation-enabled
  dev sanity before any relation claim.

Safe future fix:

- Add a separate relation-enabled config family on `domain_dev` first, not
  `domain_test`.
- Required changes would include non-empty `schema.relation_types`, prompt
  relation instructions/examples, `include_relations=True`, parser
  `relation_types=...`, relation metrics in summary, and tests.
- This changes task semantics and must not be slipped into the frozen P5 A-D
  configs.

## Question 2: Why Is D So Slow?

Conclusion: D's extra wall time is dominated by CPU RAG/reranker work outside
the logged vLLM `latency_ms`. It is not primarily vLLM generation time.

Evidence:

1. D summary:

   - elapsed time: 6237.211s
   - summed per-query vLLM latency: 436.549s
   - query records: 170
   - RAG mode: `bge_faiss_rerank`
   - embedding device: CPU
   - reranker device: CPU
   - retrieved candidates per query: 20
   - injected passages per query: 3

2. The D run log shows corpus embedding progress of 42 batches and completes
   that phase in about 2 minutes. That is not enough to explain the roughly
   1.73-hour elapsed time.

3. In `scripts/run_p3_extraction.py`, D's selector does this for each query:

   - encode the single query with BGE-M3;
   - search FAISS top-20;
   - call `FlagReranker.compute_score` on 20 query-passage pairs;
   - return top-3 passages.

   For 170 queries, this is 170 single-query embedding calls and up to 3400
   reranker pair scores on CPU.

4. The per-query `latency_ms` field only sums `chat_with_cache` latency. It
   excludes `select_rag(record)` time. Therefore D's per-query latency looks
   similar to C even though the full run is much slower.

5. Both B and D logs contain:

   ```text
   libgomp: Invalid value for environment variable OMP_NUM_THREADS
   ```

   This warning is not proven to be the main cause, but it is a CPU-threading
   hygiene issue worth fixing before more CPU-heavy embedding/rerank work.

Approximate residual:

```text
D elapsed - D vLLM latency - corpus embedding log time
~= 6237.211s - 436.549s - 121s
~= 5680s
~= 33.4s per query for non-vLLM RAG selection overhead
```

Implication:

- D is usable as a precision / false-positive-reduction row, but it is
  expensive in wall time under the current CPU reranker path.
- Repeating D for seeds 43/44 would likely cost substantial paid-GPU wall time
  even though the GPU is mostly waiting for CPU RAG selection before each vLLM
  request.

Implemented follow-up:

1. Non-semantic timing instrumentation was added to
   `scripts/run_p3_extraction.py` after this audit:
   per-query rows now include `example_selection_ms`,
   `glossary_selection_ms`, `rag_selection_ms`, `prompt_build_ms`,
   `llm_latency_ms`, and `total_record_ms`; summaries include
   `timing_totals_ms` and `timing_means_ms`.

2. A mocked unit test was added in `tests/test_extraction.py` to verify that
   execution rows and summaries contain these timing fields without touching
   real GPU, vLLM, cache, RAG models, or project data.

3. Verification was run on AutoDL GPU-free mode:

   ```text
   ~/venv/bin/python -m unittest tests.test_extraction
   Ran 16 tests in 0.096s
   OK
   ```

Remaining safe future fixes:

1. Precompute RAG selections before paid vLLM execution:
   build a frozen `{query_id: rag_passage_ids}` replay file in GPU-free mode
   using the fixed RAG config, hash it, and make D replay those IDs during paid
   extraction. This changes execution metadata/path only if the selected
   passages are byte-identical to the original selector output.

2. If precomputation is too intrusive, use CPU-thread hygiene first:
   set a valid `OMP_NUM_THREADS` value in the run shell and record it in
   execution metadata. This does not change prompt semantics, but it can affect
   wall time.

3. Do not tune `retrieve_top_k`, `top_k`, chunk size, reranker model, or RAG
   corpus based on `domain_test` results. Those are method changes and would
   violate the frozen-test rule.

## Recommended Next Step

Before any more paid P5 execution, the next GPU-free implementation option is
to add a RAG replay-manifest builder for future D runs, but only if it preserves
the exact selected passage IDs and displays under a fixed config hash. Otherwise
the next decision can be a paid replication gate with the current runner and the
new timing fields.

Then ask for a new bounded paid gate. The safest paid continuation remains:

```text
Approve paid GPU P5 domain replication: run only A/B/C/D on domain_test,
K=5, seeds 43 and 44, with no prompt/glossary/RAG/verifier tuning and no
E/E-prime.
```

Do not include relation-enabled extraction or RAG parameter changes in that
replication gate. Those require separate dev-first preparation and approval.
