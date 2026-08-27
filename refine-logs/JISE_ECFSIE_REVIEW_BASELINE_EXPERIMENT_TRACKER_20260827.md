# Reviewer Baseline Experiment Tracker — 2026-08-27

| Run ID | Milestone | Variant | Dataset | K | Seeds | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1-01 | M1 | Matrix validator | domain + CLUENER | 1/5/10 | n/a | DONE | 54 unique run specs; test boundary enforced |
| M1-02 | M1 | BM25 implementation | domain + CLUENER | 5 | n/a | DONE | Deterministic top-3 retrieval primitive |
| M1-03 | M1 | BERT-CRF BIO/CRF core | domain + CLUENER | 5 | n/a | DONE | Support-only training interface; no model run |
| B1-* | M2 | zero-shot/glossary/BM25/RAG/BERT-CRF | both | 5 | 42/43/44 | TODO | Requires sanity and execution approval |
| B2-* | M3 | A/D K scan | both | 1/10 | 42/43/44 | TODO | No K-specific tuning |
| B3-* | M4 | Paired statistics | both | mixed | n/a | TODO | Lock test families before analysis |

No GPU, model call, test inference, or paper edit is authorized by this tracker.
