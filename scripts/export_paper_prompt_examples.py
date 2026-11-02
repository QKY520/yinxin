"""Export existing cached requests for the manuscript; never call a model."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    dev = Path("/root/autodl-tmp/reviewer_qwen_glossary_only_dev_pilot_20260918/cache/58/58b2ac3c6a3906459fc921eabe08ff6966a8166d7a41d3751e71ffb4c996af0b.json")
    full_root = Path("/root/autodl-tmp/reviewer_qwen_neutral_envelope_formal_20260917/formal/ec_fsie_full/cache")
    full = next(path for path in sorted(full_root.rglob("*.json"))
                if "上次输出未通过解析" not in path.read_text(encoding="utf-8"))
    manifest = {}
    for name, path in [("glossary_dev", dev), ("ec_full_formal", full)]:
        cached = json.loads(path.read_text(encoding="utf-8"))
        payload = cached["request"]["payload"]
        prompt = payload["messages"][0]["content"]
        (out / f"{name}_prompt.txt").write_text(prompt + "\n", encoding="utf-8")
        (out / f"{name}_response.txt").write_text(cached["content"] + "\n", encoding="utf-8")
        manifest[name] = {
            "cache_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "request_hash": cached["request_hash"],
            "prompt_sha256_without_terminal_newline": hashlib.sha256(prompt.encode()).hexdigest(),
            "generation": {key: payload[key] for key in ("temperature", "top_p", "max_tokens", "seed")},
            "status": "verbatim cached request and raw response, no new inference",
        }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
