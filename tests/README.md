# Tests

Run tests only on the AutoDL instance:

```bash
cd /root/project
source /root/venv/bin/activate
python -m unittest discover -s tests -v
```

P1 tests cover schema validation, atomic JSONL writes, exact span round trips,
source-specific offset conversion, relation indexing, and deterministic support
sampling. Later phases add prompt parsing, metric recomputation, cache behavior,
and result-completeness checks.

P2 tests also enforce the approved schema, occurrence-based LLM parsing,
relation type matrices, deterministic sanity selection, request-cache identity,
DS/LLM disagreement preservation, formula-safe review CSVs, and untouched human
annotation fields.
