#!/usr/bin/env python3
"""Prepare the approved F3 full-IE dev/tune configs and non-test resources."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_f3 import F3_GATE, prepare_f3_package  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-gate", required=True)
    parser.add_argument("--domain-support", required=True)
    parser.add_argument("--domain-dev", required=True)
    parser.add_argument("--domain-glossary", required=True)
    parser.add_argument("--domain-rag-corpus", required=True)
    parser.add_argument("--domain-schema", required=True)
    parser.add_argument("--cluener-train-pool", required=True)
    parser.add_argument("--cluener-tune", required=True)
    parser.add_argument("--cluener-dev-blocklist", required=True)
    parser.add_argument("--resource-root", required=True)
    parser.add_argument("--config-root", required=True)
    parser.add_argument("--artifact-root", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.human_gate != F3_GATE:
        raise RuntimeError(f"expected --human-gate {F3_GATE}")
    report = prepare_f3_package(
        human_gate=args.human_gate,
        domain_support_path=Path(args.domain_support),
        domain_dev_path=Path(args.domain_dev),
        domain_glossary_path=Path(args.domain_glossary),
        domain_rag_corpus_path=Path(args.domain_rag_corpus),
        domain_schema_path=Path(args.domain_schema),
        cluener_train_pool_path=Path(args.cluener_train_pool),
        cluener_tune_path=Path(args.cluener_tune),
        cluener_dev_blocklist_path=Path(args.cluener_dev_blocklist),
        resource_root=Path(args.resource_root),
        config_root=Path(args.config_root),
        artifact_root=Path(args.artifact_root),
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
