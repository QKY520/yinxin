#!/usr/bin/env python3
"""Support-only BERT-CRF baseline primitives.

Training is intentionally invoked only by a later approved execution step.
The module keeps the BIO conversion and CRF implementation dependency-light so
that M1 can validate it with synthetic data in GPU-free mode.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import random
from typing import Any, Iterable, Mapping, Sequence


def entities_to_bio(text: str, entities: Sequence[dict[str, object]], *, allowed_types: Sequence[str]) -> list[str]:
    labels = ["O"] * len(text)
    allowed = set(allowed_types)
    for entity in sorted(entities, key=lambda value: (int(value["start"]), -int(value["end"]))):
        start, end, entity_type = int(entity["start"]), int(entity["end"]), str(entity["type"])
        if not (0 <= start < end <= len(text)) or entity_type not in allowed:
            raise ValueError("invalid entity span/type")
        if any(label != "O" for label in labels[start:end]):
            raise ValueError("overlapping entities are not representable in BIO")
        labels[start] = f"B-{entity_type}"
        for index in range(start + 1, end):
            labels[index] = f"I-{entity_type}"
    return labels


def bio_to_entities(labels: Sequence[str]) -> list[tuple[int, int, str]]:
    entities: list[tuple[int, int, str]] = []
    start: int | None = None
    current: str | None = None
    for index, label in enumerate([str(value) for value in labels] + ["O"]):
        if label.startswith("B-"):
            if start is not None and current is not None:
                entities.append((start, index, current))
            start, current = index, label[2:]
        elif label.startswith("I-") and start is not None and current == label[2:]:
            continue
        else:
            if start is not None and current is not None:
                entities.append((start, index, current))
            start, current = None, None
    return entities


@dataclass(frozen=True)
class CRFConfig:
    num_tags: int
    start_tag: int = 0
    end_tag: int = 1


def build_linear_chain_crf():
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise RuntimeError("torch is required for BERT-CRF training") from exc

    class LinearChainCRF(nn.Module):
        def __init__(self, num_tags: int):
            super().__init__()
            if num_tags < 3:
                raise ValueError("CRF requires at least two boundary tags and one label")
            self.num_tags = num_tags
            self.transitions = nn.Parameter(torch.zeros(num_tags, num_tags))

        def _score(self, emissions, tags, mask):
            batch, length, _ = emissions.shape
            score = emissions[:, 0].gather(1, tags[:, 0:1]).squeeze(1)
            for t in range(1, length):
                active = mask[:, t]
                score = score + emissions[:, t].gather(1, tags[:, t:t + 1]).squeeze(1) * active
                score = score + self.transitions[tags[:, t - 1], tags[:, t]] * active
            return score

        def _log_partition(self, emissions, mask):
            alpha = emissions[:, 0]
            for t in range(1, emissions.size(1)):
                next_alpha = torch.logsumexp(alpha.unsqueeze(2) + self.transitions.unsqueeze(0) + emissions[:, t].unsqueeze(1), dim=1)
                alpha = torch.where(mask[:, t].unsqueeze(1), next_alpha, alpha)
            return torch.logsumexp(alpha, dim=1)

        def neg_log_likelihood(self, emissions, tags, mask):
            return (self._log_partition(emissions, mask) - self._score(emissions, tags, mask)).mean()

        @torch.no_grad()
        def decode(self, emissions, mask):
            paths = []
            for batch_index in range(emissions.size(0)):
                length = int(mask[batch_index].sum().item())
                score = emissions[batch_index, 0]
                backpointers = []
                for t in range(1, length):
                    values = score.unsqueeze(1) + self.transitions + emissions[batch_index, t].unsqueeze(0)
                    best_score, best_prev = values.max(dim=0)
                    score, backpointers = best_score, backpointers + [best_prev]
                tag = int(score.argmax().item())
                path = [tag]
                for previous in reversed(backpointers):
                    tag = int(previous[tag].item())
                    path.append(tag)
                paths.append(list(reversed(path)))
            return paths

    return LinearChainCRF


def build_bio_label_vocab(entity_types: Sequence[str]) -> tuple[list[str], dict[str, int]]:
    """Return deterministic BIO tags and their integer IDs."""
    if not entity_types:
        raise ValueError("entity_types must not be empty")
    tags = ["O"]
    for entity_type in entity_types:
        if not isinstance(entity_type, str) or not entity_type:
            raise ValueError("entity types must be non-empty strings")
        tags.extend((f"B-{entity_type}", f"I-{entity_type}"))
    return tags, {tag: index for index, tag in enumerate(tags)}


def _record_to_char_tags(record: Mapping[str, Any], entity_types: Sequence[str]) -> list[str]:
    return entities_to_bio(str(record["text"]), record.get("entities", []), allowed_types=entity_types)


def encode_records(
    records: Sequence[Mapping[str, Any]],
    tokenizer: Any,
    label_to_id: Mapping[str, int],
    entity_types: Sequence[str],
    *,
    max_length: int,
) -> list[dict[str, Any]]:
    """Tokenize records and align character BIO labels to token offsets."""
    encoded: list[dict[str, Any]] = []
    for record in records:
        text = str(record["text"])
        char_tags = _record_to_char_tags(record, entity_types)
        item = tokenizer(text, truncation=True, max_length=max_length, return_offsets_mapping=True)
        offsets = item.pop("offset_mapping")
        labels: list[int] = []
        for start, end in offsets:
            if end <= start or start >= len(char_tags):
                labels.append(-100)
            else:
                labels.append(label_to_id[char_tags[start]])
        item["labels"] = labels
        item["record_id"] = str(record["id"])
        item["text"] = text
        item["offset_mapping"] = offsets
        encoded.append(item)
    return encoded


def _pad_batch(items: Sequence[Mapping[str, Any]], pad_token_id: int) -> tuple[Any, Any, Any]:
    import torch
    width = max(len(item["input_ids"]) for item in items)
    input_ids, attention, labels = [], [], []
    for item in items:
        padding = width - len(item["input_ids"])
        input_ids.append(list(item["input_ids"]) + [pad_token_id] * padding)
        attention.append(list(item["attention_mask"]) + [0] * padding)
        labels.append(list(item["labels"]) + [-100] * padding)
    return (
        torch.tensor(input_ids, dtype=torch.long),
        torch.tensor(attention, dtype=torch.bool),
        torch.tensor(labels, dtype=torch.long),
    )


def _decode_token_entities(
    text: str,
    tags: Sequence[str],
    offsets: Sequence[Sequence[int]],
) -> list[dict[str, Any]]:
    char_tags = ["O"] * len(text)
    for tag, pair in zip(tags, offsets):
        start, end = int(pair[0]), int(pair[1])
        if end > start and 0 <= start < len(text):
            for index in range(start, min(end, len(text))):
                char_tags[index] = tag
    entities = []
    for start, end, entity_type in bio_to_entities(char_tags):
        entities.append({"start": start, "end": end, "type": entity_type, "span": text[start:end]})
    return entities


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def train_support_only(
    support_records: Sequence[Mapping[str, Any]],
    tune_records: Sequence[Mapping[str, Any]],
    *,
    model_path: str,
    entity_types: Sequence[str],
    seed: int,
    max_epochs: int = 20,
    patience: int = 3,
    learning_rate: float = 3e-5,
    batch_size: int = 8,
    max_length: int = 256,
    device: str | None = None,
) -> tuple[Any, Any, list[str], dict[str, Any]]:
    """Train BERT + linear-chain CRF on support; tune only on ``tune_records``."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    random.seed(seed)
    torch.manual_seed(seed)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    encoder = AutoModel.from_pretrained(model_path, local_files_only=True)
    tags, label_to_id = build_bio_label_vocab(entity_types)
    crf = build_linear_chain_crf()(len(tags))
    class Head(torch.nn.Module):
        def __init__(self):
            super().__init__(); self.encoder = encoder; self.dropout = torch.nn.Dropout(0.1); self.classifier = torch.nn.Linear(encoder.config.hidden_size, len(tags)); self.crf = crf
        def forward(self, input_ids, attention, labels=None):
            hidden = self.dropout(self.encoder(input_ids=input_ids, attention_mask=attention).last_hidden_state)
            emissions = self.classifier(hidden)
            active = attention.bool() if labels is None else labels.ne(-100)
            safe_labels = torch.where(active, labels if labels is not None else torch.zeros_like(attention, dtype=torch.long), torch.zeros_like(attention, dtype=torch.long))
            loss = self.crf.neg_log_likelihood(emissions, safe_labels, active) if labels is not None else None
            return loss, emissions, active
    model = Head()
    target = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model.to(target)
    support = encode_records(support_records, tokenizer, label_to_id, entity_types, max_length=max_length)
    tune = encode_records(tune_records, tokenizer, label_to_id, entity_types, max_length=max_length)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    best_loss, stale, best_state = float("inf"), 0, None
    for _epoch in range(max_epochs):
        model.train(); random.Random(seed + _epoch).shuffle(support); total = 0.0
        for offset in range(0, len(support), batch_size):
            batch = support[offset:offset + batch_size]
            ids, attention, labels = _pad_batch(batch, tokenizer.pad_token_id or 0)
            ids, attention, labels = ids.to(target), attention.to(target), labels.to(target)
            optimizer.zero_grad(); loss, _, _ = model(ids, attention, labels); loss.backward(); optimizer.step(); total += float(loss.detach())
        model.eval(); tune_loss = 0.0
        with torch.no_grad():
            for offset in range(0, len(tune), batch_size):
                batch = tune[offset:offset + batch_size]; ids, attention, labels = _pad_batch(batch, tokenizer.pad_token_id or 0); loss, _, _ = model(ids.to(target), attention.to(target), labels.to(target)); tune_loss += float(loss)
        tune_loss /= max(1, (len(tune) + batch_size - 1) // batch_size)
        if tune_loss < best_loss:
            best_loss, stale, best_state = tune_loss, 0, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= patience: break
    if best_state is not None: model.load_state_dict(best_state)
    return model, tokenizer, tags, {"best_tune_loss": best_loss, "epochs_completed": _epoch + 1, "device": str(target)}


def predict_records(model: Any, tokenizer: Any, tags: Sequence[str], records: Sequence[Mapping[str, Any]], *, max_length: int = 256, batch_size: int = 8) -> list[dict[str, Any]]:
    import torch
    encoded = encode_records(records, tokenizer, {tag: i for i, tag in enumerate(tags)}, [tag.split("-", 1)[1] for tag in tags if tag.startswith("B-")], max_length=max_length)
    target = next(model.parameters()).device; model.eval(); output=[]
    with torch.no_grad():
        for offset in range(0, len(encoded), batch_size):
            batch=encoded[offset:offset+batch_size]; ids,attention,_=_pad_batch(batch, tokenizer.pad_token_id or 0); _,emissions,active=model(ids.to(target),attention.to(target)); paths=model.crf.decode(emissions,active)
            for item,path in zip(batch,paths):
                output.append({"id":item["record_id"],"text":item["text"],"entities":_decode_token_entities(item["text"],[tags[i] for i in path],item["offset_mapping"]),"relations":[]})
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Support-only BERT-CRF baseline")
    parser.add_argument("--support", required=True); parser.add_argument("--tune", required=True); parser.add_argument("--evaluation", required=True); parser.add_argument("--model-path", required=True); parser.add_argument("--output", required=True); parser.add_argument("--seed", type=int, required=True); parser.add_argument("--entity-types", nargs="+", default=["EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"]); parser.add_argument("--allow-evaluation", action="store_true")
    args = parser.parse_args()
    if not args.allow_evaluation: raise SystemExit("evaluation requires --allow-evaluation in the later locked execution step")
    support, tune, evaluation = load_jsonl(args.support), load_jsonl(args.tune), load_jsonl(args.evaluation)
    model, tokenizer, tags, train_meta = train_support_only(support, tune, model_path=args.model_path, entity_types=args.entity_types, seed=args.seed)
    predictions = predict_records(model, tokenizer, tags, evaluation)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps({"predictions": predictions, "train": train_meta, "test_read": True}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
