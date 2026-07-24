#!/usr/bin/env python3
"""Build a fixed RAG replay manifest from an existing extraction config."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.run_p3_extraction import (  # noqa: E402
    build_rag_selector,
    gpu_visible,
    load_records,
    load_yaml,
    sha256_file,
    write_json_atomic,
)


def canonical_sha256(value: Any) -> str:
    from equipment_ie.llm_labeling import sha256_text

    return sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def build_manifest(config: dict[str, Any], *, config_path: Path, output_path: Path) -> dict[str, Any]:
    rag_config = config.get("rag", {})
    if not isinstance(rag_config, dict) or rag_config.get("enabled") is not True:
        raise ValueError("config.rag.enabled must be true")
    if rag_config.get("mode") == "replay_manifest":
        raise ValueError("cannot build a replay manifest from replay_manifest mode")

    query_records = load_records(config["data"]["query_path"])
    select_rag, rag_metadata = build_rag_selector(config)
    rows: list[dict[str, Any]] = []
    for record in query_records:
        selected = select_rag(record)
        rows.append(
            {
                "id": record["id"],
                "rag_passage_ids": [passage["id"] for passage in selected],
                "rag_passages": [passage["display"] for passage in selected],
                "selected_passages": [
                    {
                        key: passage[key]
                        for key in (
                            "id",
                            "source_id",
                            "source_type",
                            "title",
                            "chunk_index",
                            "display",
                            "rerank_score",
                        )
                        if key in passage
                    }
                    for passage in selected
                ],
            }
        )

    manifest = {
        "stage": "rag_replay_manifest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_config_path": str(config_path),
        "source_config_sha256": sha256_file(str(config_path)),
        "source_rag_mode": rag_config.get("mode", "lexical_preview"),
        "rag_config_sha256": canonical_sha256(rag_config),
        "query_path": config["data"]["query_path"],
        "query_path_sha256": sha256_file(config["data"]["query_path"]),
        "query_records": len(query_records),
        "rag_selection": rag_metadata,
        "api_called": False,
        "model_calls": 0,
        "gpu_device_present": gpu_visible(),
        "rows": rows,
    }
    write_json_atomic(output_path, manifest)
    manifest["manifest_path"] = str(output_path)
    manifest["manifest_sha256"] = sha256_file(str(output_path))
    return manifest


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    output_path = Path(args.output)
    config = load_yaml(config_path)
    manifest = build_manifest(config, config_path=config_path, output_path=output_path)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
