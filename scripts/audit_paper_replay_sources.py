"""Read-only provenance check for the manuscript's retrieval description."""
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


support = {row["id"] for row in rows("/root/autodl-tmp/data/domain_support.jsonl")}
queries = {row["id"] for row in rows("/root/autodl-tmp/data/domain_test.jsonl")}
root = Path("/root/autodl-tmp/reviewer_qwen_neutral_envelope_formal_20260917/replay_manifests")
report = {}
for system in ("bm25", "dense"):
    data = json.loads((root / f"{system}.json").read_text(encoding="utf-8"))
    selections = [p for row in data["rows"] for p in row["selected_passages"]]
    ids = [p["id"].split("#chunk-")[0] for p in selections]
    report[system] = {
        "selected_slots": len(ids),
        "unique_source_ids": len(set(ids)),
        "support_source_slots": sum(x in support for x in ids),
        "test_source_slots": sum(x in queries for x in ids),
        "support_source_ids": sorted(set(ids) & support),
    }
print(json.dumps(report, ensure_ascii=False, indent=2))
