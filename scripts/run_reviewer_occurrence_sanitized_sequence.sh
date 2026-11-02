#!/usr/bin/env bash
set -euo pipefail

cd /root/project
source /root/venv/bin/activate

ROOT=/root/autodl-tmp/reviewer_qwen_occurrence_sanitized_20260917
CONFIG_ROOT=configs/reviewer_qwen_occurrence_sanitized_20260917/runtime_authorized

for system in zero_shot bm25_only rag_only ec_fsie_full; do
  python -m scripts.run_p3_extraction \
    --config "${CONFIG_ROOT}/${system}_pilot20.yaml" \
    2>&1 | tee "${ROOT}/logs/${system}_pilot20.log"

  SYSTEM="${system}" ROOT="${ROOT}" python - <<'PY'
import json
import os
from pathlib import Path

system = os.environ["SYSTEM"]
root = Path(os.environ["ROOT"])
summary = json.loads((root / "pilot20" / system / "summary.json").read_text(encoding="utf-8"))
failures = int(summary["parse_failures"])
rows = int(summary["query_records"])
accepted = int(summary["entity_audit_counts"]["accepted_entities"])
f1 = float(summary["entity_micro"]["f1"])
if failures / rows > 0.25:
    raise SystemExit(f"STOP {system}: parser failures {failures}/{rows} exceed 25%")
if accepted <= 0 or f1 <= 0.0:
    raise SystemExit(f"STOP {system}: semantic gate failed accepted={accepted}, f1={f1}")
print(f"PASS {system}: parser={failures}/{rows}, accepted={accepted}, f1={f1:.6f}")
PY
done
