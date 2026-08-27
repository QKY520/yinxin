#!/usr/bin/env python3
"""Route one reviewer-baseline run to the canonical Qwen or BERT runner.

This is an execution shim, not an authorization mechanism: the Qwen config
still passes through P3's gate validator, and BERT evaluation remains opt-in.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dispatch one reviewer baseline run")
    parser.add_argument("--runner", choices=("qwen", "bert"), required=True)
    parser.add_argument("--config", required=True, help="Qwen YAML or BERT JSON/YAML config")
    parser.add_argument("--dry-run", action="store_true", help="Qwen prompt dry-run")
    parser.add_argument("--allow-evaluation", action="store_true", help="explicitly allow BERT evaluation")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required") from exc
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a mapping")
    return value


def dispatch_qwen(config_path: Path, *, dry_run: bool) -> int:
    command = [sys.executable, str(Path(__file__).with_name("run_p3_extraction.py")), "--config", str(config_path)]
    if dry_run:
        command.append("--dry-run")
    return subprocess.run(command, check=False).returncode


def dispatch_bert(config_path: Path, *, allow_evaluation: bool) -> int:
    config = load_config(config_path)
    required = ("support", "tune", "evaluation", "model_path", "output", "seed")
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"BERT config missing keys: {missing}")
    command = [
        sys.executable,
        str(Path(__file__).with_name("run_bert_crf_baseline.py")),
        "--support", str(config["support"]),
        "--tune", str(config["tune"]),
        "--evaluation", str(config["evaluation"]),
        "--model-path", str(config["model_path"]),
        "--output", str(config["output"]),
        "--seed", str(config["seed"]),
    ]
    entity_types = config.get("entity_types")
    if entity_types:
        command.extend(["--entity-types", *[str(value) for value in entity_types]])
    if allow_evaluation:
        command.append("--allow-evaluation")
    return subprocess.run(command, check=False).returncode


def main() -> int:
    args = parse_args()
    path = Path(args.config)
    if args.runner == "qwen":
        return dispatch_qwen(path, dry_run=args.dry_run)
    return dispatch_bert(path, allow_evaluation=args.allow_evaluation)


if __name__ == "__main__":
    raise SystemExit(main())
