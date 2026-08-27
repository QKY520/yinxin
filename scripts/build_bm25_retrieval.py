#!/usr/bin/env python3
"""Small dependency-free BM25 index used by the reviewer baseline package.

This module is intentionally limited to retrieval.  It never reads evaluation
gold labels and never performs model calls.  The caller supplies a labels-
stripped corpus and can persist the returned IDs for a later prompt run.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Iterable, Mapping, Sequence


TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u3400-\u9fff]")


def tokenize(text: str) -> list[str]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class CorpusRow:
    row_id: str
    text: str


class BM25Index:
    def __init__(self, rows: Sequence[CorpusRow], *, k1: float = 1.2, b: float = 0.75):
        if not rows:
            raise ValueError("BM25 corpus must not be empty")
        if k1 <= 0 or not 0 <= b <= 1:
            raise ValueError("invalid BM25 parameters")
        self.rows = tuple(rows)
        self.k1 = float(k1)
        self.b = float(b)
        self.tokens = tuple(tokenize(row.text) for row in self.rows)
        self.lengths = tuple(len(tokens) for tokens in self.tokens)
        self.avgdl = sum(self.lengths) / len(self.lengths)
        postings: dict[str, list[int]] = {}
        for index, tokens in enumerate(self.tokens):
            for term in set(tokens):
                postings.setdefault(term, []).append(index)
        self.postings = {term: tuple(indices) for term, indices in postings.items()}
        self.idf = {
            term: math.log(1.0 + (len(self.rows) - len(indices) + 0.5) / (len(indices) + 0.5))
            for term, indices in self.postings.items()
        }

    def scores(self, query: str) -> list[float]:
        query_terms = tokenize(query)
        frequencies: dict[str, int] = {}
        for term in query_terms:
            frequencies[term] = frequencies.get(term, 0) + 1
        scores = [0.0] * len(self.rows)
        for term, qtf in frequencies.items():
            if term not in self.postings:
                continue
            idf = self.idf[term]
            for index in self.postings[term]:
                tf = self.tokens[index].count(term)
                norm = 1.0 - self.b + self.b * self.lengths[index] / self.avgdl
                scores[index] += idf * (tf * (self.k1 + 1.0) / (tf + self.k1 * norm)) * qtf
        return scores

    def retrieve(self, query: str, *, top_k: int = 3) -> list[dict[str, object]]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        scores = self.scores(query)
        ranked = sorted(range(len(self.rows)), key=lambda i: (-scores[i], i))[:top_k]
        return [
            {"id": self.rows[i].row_id, "text": self.rows[i].text, "score": scores[i]}
            for i in ranked
        ]


def load_jsonl(path: str | Path) -> list[CorpusRow]:
    rows: list[CorpusRow] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            row_id = record.get("id")
            text = record.get("text")
            if not isinstance(row_id, str) or not row_id:
                raise ValueError(f"{path}:{line_number}: id must be a non-empty string")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"{path}:{line_number}: text must be non-empty")
            rows.append(CorpusRow(row_id=row_id, text=text))
    return rows


def write_retrieval_manifest(index: BM25Index, queries: Iterable[Mapping[str, object]], path: str | Path, *, top_k: int = 3) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for query in queries:
            query_id = query.get("id")
            text = query.get("text")
            if not isinstance(query_id, str) or not isinstance(text, str):
                raise ValueError("query requires string id and text")
            handle.write(json.dumps({"id": query_id, "retrieved": index.retrieve(text, top_k=top_k)}, ensure_ascii=False) + "\n")
