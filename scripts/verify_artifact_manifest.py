#!/usr/bin/env python3
"""Independently verify byte sizes and SHA256 values in an artifact manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.schema import sha256_file  # noqa: E402


def verify_manifest(path: Path) -> dict[str, int]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"{path}: manifest must be a non-empty list")
    total_bytes = 0
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: entry {index} is not an object")
        artifact = Path(entry["path"])
        expected_bytes = int(entry["bytes"])
        if not artifact.is_file():
            raise FileNotFoundError(artifact)
        actual_bytes = artifact.stat().st_size
        if actual_bytes != expected_bytes:
            raise ValueError(
                f"{artifact}: expected {expected_bytes} bytes, got {actual_bytes}"
            )
        actual_sha256 = sha256_file(artifact)
        if actual_sha256 != entry["sha256"]:
            raise ValueError(f"{artifact}: SHA256 mismatch")
        total_bytes += actual_bytes
    return {"artifacts": len(entries), "bytes": total_bytes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest",
        type=Path,
        nargs="?",
        default=Path("/root/autodl-tmp/backup/p1/artifact_manifest.json"),
    )
    args = parser.parse_args()
    result = verify_manifest(args.manifest)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
