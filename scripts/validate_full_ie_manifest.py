#!/usr/bin/env python3
"""Build or validate the fixed 60-cell full-IE manifest inventory."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_manifest import (  # noqa: E402
    aggregate_manifest_metrics,
    build_planned_manifest,
    validate_full_ie_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest")
    source.add_argument("--write-planned")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--aggregate-output")
    parser.add_argument("--report-output")
    return parser.parse_args()


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: manifest must be a JSON object")
    return value


def main() -> int:
    args = parse_args()
    if args.write_planned:
        if args.require_complete or args.aggregate_output:
            raise ValueError(
                "--write-planned cannot be combined with --require-complete or "
                "--aggregate-output"
            )
        manifest = build_planned_manifest()
        report = validate_full_ie_manifest(manifest)
        write_json_atomic(Path(args.write_planned), manifest)
    else:
        manifest = load_manifest(Path(args.manifest))
        report = validate_full_ie_manifest(
            manifest,
            require_complete=args.require_complete,
        )
        if args.aggregate_output:
            aggregates = aggregate_manifest_metrics(manifest)
            write_json_atomic(Path(args.aggregate_output), aggregates)
    if args.report_output:
        write_json_atomic(Path(args.report_output), report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
