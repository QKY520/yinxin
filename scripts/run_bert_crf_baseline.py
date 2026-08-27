#!/usr/bin/env python3
"""Support-only BERT-CRF baseline primitives.

Training is intentionally invoked only by a later approved execution step.
The module keeps the BIO conversion and CRF implementation dependency-light so
that M1 can validate it with synthetic data in GPU-free mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


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
