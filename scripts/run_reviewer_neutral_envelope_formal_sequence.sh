#!/usr/bin/env bash
set -euo pipefail
cd /root/project
source /root/venv/bin/activate

ROOT=/root/autodl-tmp/reviewer_qwen_neutral_envelope_formal_20260917
CONFIG_ROOT=configs/reviewer_qwen_neutral_envelope_formal_20260917/runtime_authorized

for system in zero_shot bm25_only rag_only ec_fsie_full; do
  python -m scripts.run_p3_extraction --config "${CONFIG_ROOT}/${system}.yaml" \
    2>&1 | tee "${ROOT}/${system}.log"
  SYSTEM="${system}" ROOT="${ROOT}" python - <<'PY'
import json, os
from pathlib import Path
system, root = os.environ["SYSTEM"], Path(os.environ["ROOT"])
summary = json.loads((root / "formal" / system / "summary.json").read_text(encoding="utf-8"))
failed, rows = int(summary["parse_failures"]), int(summary["query_records"])
f1 = float(summary["entity_micro"]["f1"])
if failed / rows > 0.20:
    raise SystemExit(f"STOP {system}: parser failures {failed}/{rows} exceed 20%")
if f1 <= 0.0:
    raise SystemExit(f"STOP {system}: F1 is not positive")
print(f"PASS {system}: parser={failed}/{rows}, f1={f1:.6f}")
PY
done
