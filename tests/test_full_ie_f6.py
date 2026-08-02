from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_f6 import (  # noqa: E402
    F6_GATE,
    F6_VERSION,
    build_cluener_replay_manifest,
    build_domain_consensus_manifest,
    inspect_cpu_model_memory,
    sha256_file,
    text_sha256,
    validate_f6_inputs,
    validate_replay_manifest,
)


INPUT_PATH = (
    PROJECT_ROOT
    / "configs"
    / "full_ie_f6_replay_prep_20260802"
    / "replay_inputs.json"
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def query_rows(count: int) -> list[dict]:
    return [{"id": f"q{index}", "text": f"query text {index} unique"} for index in range(count)]


def passage_row(record_id: str, suffix: str = "") -> dict:
    ids = [f"p{index}#chunk-0" for index in range(1, 4)]
    displays = [
        f"title {index} | unit | {passage_id}: unrelated evidence {index} {suffix}"
        for index, passage_id in enumerate(ids, start=1)
    ]
    return {
        "id": record_id,
        "rag_passage_ids": ids,
        "rag_passages": displays,
    }


class FullIEF6Test(unittest.TestCase):
    def load_inputs(self) -> dict:
        return json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    def test_real_inputs_freeze_bounded_scope(self) -> None:
        report = validate_f6_inputs(self.load_inputs(), repo_root=PROJECT_ROOT)
        self.assertEqual(report["version"], F6_VERSION)
        self.assertEqual(report["gate"], F6_GATE)
        self.assertEqual(report["resources"], 6)
        self.assertEqual(report["domain_sources"], 3)
        self.assertFalse(report["gpu_required"])
        self.assertFalse(report["llm_calls_allowed"])

    def test_inputs_reject_execution_and_retrieval_changes(self) -> None:
        authorized = self.load_inputs()
        authorized["authorization"]["stage_execution_allowed"] = True
        with self.assertRaisesRegex(ValueError, "bounded F6"):
            validate_f6_inputs(authorized, repo_root=PROJECT_ROOT)

        retrieval = self.load_inputs()
        retrieval["retrieval"]["retrieve_top_k"] = 10
        with self.assertRaisesRegex(ValueError, "F5 freeze"):
            validate_f6_inputs(retrieval, repo_root=PROJECT_ROOT)

    def test_cpu_memory_preflight_uses_model_weight_lower_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            embedding = root / "embedding"
            reranker = root / "reranker"
            embedding.mkdir()
            reranker.mkdir()
            (embedding / "pytorch_model.bin").write_bytes(b"e" * 100)
            (embedding / "projection.pt").write_bytes(b"p" * 10)
            (reranker / "model.safetensors").write_bytes(b"r" * 200)
            inputs = self.load_inputs()
            inputs["models"]["embedding_path"] = str(embedding)
            inputs["models"]["reranker_path"] = str(reranker)

            blocked = inspect_cpu_model_memory(inputs, memory_limit_bytes=300)
            self.assertEqual(blocked["minimum_model_weight_bytes"], 310)
            self.assertFalse(blocked["sufficient"])
            self.assertEqual(blocked["headroom_bytes_before_runtime"], -10)

            sufficient = inspect_cpu_model_memory(inputs, memory_limit_bytes=400)
            self.assertTrue(sufficient["sufficient"])

    def synthetic_inputs(self, root: Path, *, query_count: int) -> dict:
        queries = root / "query.jsonl"
        corpus = root / "corpus.jsonl"
        write_jsonl(queries, query_rows(query_count))
        write_jsonl(corpus, [{"id": "p1", "text": "unrelated evidence"}])
        inputs = self.load_inputs()
        inputs["resources"]["domain_query"] = {
            "path": str(queries),
            "sha256": sha256_file(queries),
            "rows": query_count,
        }
        inputs["resources"]["cluener_query"] = copy.deepcopy(
            inputs["resources"]["domain_query"]
        )
        inputs["resources"]["domain_corpus"] = {
            "path": str(corpus),
            "sha256": sha256_file(corpus),
            "rows": 1,
        }
        inputs["resources"]["cluener_corpus"] = copy.deepcopy(
            inputs["resources"]["domain_corpus"]
        )
        return inputs

    def test_domain_consensus_requires_three_identical_seed_replays(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = self.synthetic_inputs(root, query_count=2)
            source_locks = []
            for seed in (42, 43, 44):
                path = root / f"seed{seed}.jsonl"
                write_jsonl(path, [passage_row("q0"), passage_row("q1")])
                source_locks.append(
                    {"path": str(path), "sha256": sha256_file(path), "rows": 2, "seed": seed}
                )
            inputs["domain_consensus_sources"] = source_locks
            output = root / "domain.json"
            manifest = build_domain_consensus_manifest(
                inputs,
                output_path=output,
                config_sha256="a" * 64,
            )
            self.assertEqual(manifest["query_records"], 2)
            self.assertNotIn("text", manifest["rows"][0])
            self.assertTrue(output.is_file())

            changed = root / "seed44.jsonl"
            write_jsonl(changed, [passage_row("q0", "changed"), passage_row("q1")])
            with self.assertRaisesRegex(ValueError, "differs"):
                build_domain_consensus_manifest(
                    inputs,
                    output_path=output,
                    config_sha256="a" * 64,
                )

    def test_cluener_builder_resumes_checkpoint_without_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = self.synthetic_inputs(root, query_count=2)
            calls: list[str] = []

            def selector_builder(_config: dict):
                def select(record: dict) -> list[dict]:
                    calls.append(record["id"])
                    row = passage_row(record["id"])
                    return [
                        {
                            "id": passage_id,
                            "source_id": passage_id.split("#", 1)[0],
                            "source_type": "unit",
                            "title": "title",
                            "chunk_index": 0,
                            "text": "must not be serialized",
                            "rerank_score": float(3 - index),
                            "display": display,
                        }
                        for index, (passage_id, display) in enumerate(
                            zip(row["rag_passage_ids"], row["rag_passages"])
                        )
                    ]

                return select, {"mode": "bge_faiss_rerank"}

            output = root / "cluener.json"
            checkpoint = root / "rows.jsonl"
            checkpoint_meta = root / "checkpoint.json"
            manifest = build_cluener_replay_manifest(
                inputs,
                output_path=output,
                checkpoint_path=checkpoint,
                checkpoint_metadata_path=checkpoint_meta,
                config_sha256="b" * 64,
                selector_builder=selector_builder,
                progress_every=0,
            )
            self.assertEqual(calls, ["q0", "q1"])
            self.assertNotIn("text", manifest["rows"][0]["selected_passages"][0])
            calls.clear()
            build_cluener_replay_manifest(
                inputs,
                output_path=output,
                checkpoint_path=checkpoint,
                checkpoint_metadata_path=checkpoint_meta,
                config_sha256="b" * 64,
                selector_builder=selector_builder,
                progress_every=0,
            )
            self.assertEqual(calls, [])

    def valid_manifest(self, root: Path) -> tuple[dict, dict]:
        inputs = self.synthetic_inputs(root, query_count=2)
        rows = []
        for query in query_rows(2):
            replay = passage_row(query["id"])
            rows.append(
                {
                    "id": query["id"],
                    "query_text_sha256": text_sha256(query["text"]),
                    **replay,
                    "selected_passages": [
                        {
                            "id": passage_id,
                            "source_id": passage_id.split("#", 1)[0],
                            "display": display,
                            "rerank_score": 1.0,
                        }
                        for passage_id, display in zip(
                            replay["rag_passage_ids"], replay["rag_passages"]
                        )
                    ],
                }
            )
        manifest = {
            "version": F6_VERSION,
            "human_gate": F6_GATE,
            "dataset": "cluener",
            "config_sha256": "c" * 64,
            "f5_manifest_sha256": "592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e",
            "query_path_sha256": inputs["resources"]["cluener_query"]["sha256"],
            "query_records": 2,
            "api_called": False,
            "llm_calls": 0,
            "gpu_device_present": False,
            "rows": rows,
        }
        return inputs, manifest

    def test_replay_validation_rejects_prohibited_fields_and_self_hits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inputs, manifest = self.valid_manifest(Path(directory))
            report = validate_replay_manifest(
                manifest,
                inputs,
                dataset="cluener",
                config_sha256="c" * 64,
            )
            self.assertEqual(report["selected_passages"], 6)

            leaked = copy.deepcopy(manifest)
            leaked["rows"][0]["gold"] = {}
            with self.assertRaisesRegex(ValueError, "prohibited field"):
                validate_replay_manifest(
                    leaked,
                    inputs,
                    dataset="cluener",
                    config_sha256="c" * 64,
                )

            self_hit = copy.deepcopy(manifest)
            self_hit["rows"][0]["selected_passages"][0]["source_id"] = "q0"
            with self.assertRaisesRegex(ValueError, "self-hit"):
                validate_replay_manifest(
                    self_hit,
                    inputs,
                    dataset="cluener",
                    config_sha256="c" * 64,
                )

            nonfinite = copy.deepcopy(manifest)
            nonfinite["rows"][0]["selected_passages"][0]["rerank_score"] = float("inf")
            with self.assertRaisesRegex(ValueError, "finite reranker score"):
                validate_replay_manifest(
                    nonfinite,
                    inputs,
                    dataset="cluener",
                    config_sha256="c" * 64,
                )

    def test_replay_validation_rejects_fixed_8gram_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inputs, manifest = self.valid_manifest(Path(directory))
            passage_id = manifest["rows"][0]["rag_passage_ids"][0]
            display = f"title | unit | {passage_id}: query text 0 unique"
            manifest["rows"][0]["rag_passages"][0] = display
            manifest["rows"][0]["selected_passages"][0]["display"] = display
            with self.assertRaisesRegex(ValueError, "containment"):
                validate_replay_manifest(
                    manifest,
                    inputs,
                    dataset="cluener",
                    config_sha256="c" * 64,
                )


if __name__ == "__main__":
    unittest.main()
