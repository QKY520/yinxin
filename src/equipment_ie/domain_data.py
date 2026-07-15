"""GPU-free preparation helpers for the self-built equipment corpus."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from equipment_ie.schema import SchemaError, validate_record


_SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？；!?;])")
_WHITESPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Collapse source whitespace while preserving punctuation and characters."""

    return _WHITESPACE.sub(" ", html.unescape(text)).strip()


def chunk_text(text: str, *, min_chars: int, max_chars: int) -> list[str]:
    """Split text into deterministic sentence-aware 100-300 character passages."""

    if not 0 < min_chars <= max_chars:
        raise ValueError("invalid chunk length bounds")
    normalized = clean_text(text)
    if len(normalized) < min_chars:
        return []
    sentences = [piece.strip() for piece in _SENTENCE_BOUNDARY.split(normalized) if piece.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        while len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:max_chars])
            sentence = sentence[max_chars:]
        if not sentence:
            continue
        if not current:
            current = sentence
        elif len(current) + len(sentence) <= max_chars:
            current += sentence
        else:
            if len(current) >= min_chars:
                chunks.append(current)
                current = sentence
            else:
                room = max_chars - len(current)
                current += sentence[:room]
                chunks.append(current)
                current = sentence[room:]
    if current:
        if len(current) >= min_chars:
            chunks.append(current)
        elif chunks and len(chunks[-1]) + len(current) <= max_chars:
            chunks[-1] += current
    return [chunk for chunk in chunks if min_chars <= len(chunk) <= max_chars]


def normalized_ngrams(text: str, ngram_size: int) -> frozenset[str]:
    if ngram_size <= 0:
        raise ValueError("ngram_size must be positive")
    normalized = "".join(text.lower().split())
    if len(normalized) < ngram_size:
        return frozenset({normalized}) if normalized else frozenset()
    return frozenset(
        normalized[index : index + ngram_size]
        for index in range(len(normalized) - ngram_size + 1)
    )


def ngram_containment(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left.intersection(right)) / min(len(left), len(right))


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_objects_jsonl_atomic(path: Path | str, rows: Iterable[Mapping[str, Any]]) -> int:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    count = 0
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                count += 1
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return count


def iter_objects_jsonl(path: Path | str) -> Iterator[dict[str, Any]]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source}:{line_number}: invalid JSON") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{source}:{line_number}: expected object")
            yield value


def extract_seed_terms(path: Path | str, revision: str) -> list[dict[str, Any]]:
    """Extract exact equipment names from QAonMilitaryKG's Mongo JSON dump."""

    terms: dict[str, dict[str, Any]] = {}
    for row_index, raw in enumerate(iter_objects_jsonl(path)):
        term = raw.get("名称")
        if not isinstance(term, str) or not term.strip():
            continue
        term = clean_text(term)
        source_id = raw.get("_id", {})
        if isinstance(source_id, dict):
            source_id = source_id.get("$oid", row_index)
        terms.setdefault(
            term,
            {
                "term": term,
                "category": clean_text(str(raw.get("大类", ""))),
                "subtype": clean_text(str(raw.get("类型", ""))),
                "source": "QAonMilitaryKG-RomanGao",
                "source_id": str(source_id),
                "source_revision": revision,
                "license": "NOASSERTION",
            },
        )
    return [terms[term] for term in sorted(terms)]


def keyword_score(text: str, specific: Sequence[str], general: Sequence[str]) -> int:
    return 3 * sum(keyword in text for keyword in specific) + sum(
        keyword in text for keyword in general
    )


def patent_candidates(
    files: Sequence[Mapping[str, Any]],
    *,
    min_chars: int,
    max_chars: int,
    specific_keywords: Sequence[str],
    general_keywords: Sequence[str],
    revision: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for file_spec in files:
        split = str(file_spec["split"])
        for row_index, raw in enumerate(iter_objects_jsonl(file_spec["path"])):
            body = raw.get("body")
            if not isinstance(body, dict):
                continue
            title = clean_text(str(body.get("title", "")))
            abstract = body.get("abstract")
            if not isinstance(abstract, str):
                continue
            score = keyword_score(
                f"{title} {abstract}", specific_keywords, general_keywords
            )
            specific_match = any(keyword in f"{title} {abstract}" for keyword in specific_keywords)
            general_matches = sum(
                keyword in f"{title} {abstract}" for keyword in general_keywords
            )
            if not specific_match and general_matches < 2:
                continue
            chunks = chunk_text(abstract, min_chars=min_chars, max_chars=max_chars)
            if not chunks:
                continue
            metadata = raw.get("metadata", {})
            publication = (
                metadata.get("publication-reference", {})
                if isinstance(metadata, dict)
                else {}
            )
            document_number = str(publication.get("doc-number", ""))
            source_id = document_number or f"{split}-{row_index}"
            text = chunks[0]
            candidates.append(
                {
                    "source_candidate_id": f"patent-{split}-{source_id}",
                    "text": text,
                    "source_type": "patent",
                    "source_id": source_id,
                    "source_split": split,
                    "source_url": "https://github.com/tanggongbo/KPPatent-ZH",
                    "source_revision": revision,
                    "source_license": "MIT",
                    "title": title,
                    "selection_score": score,
                    "content_sha256": text_sha256(text),
                }
            )
    return candidates


def cmnee_candidates(
    path: Path | str,
    *,
    min_chars: int,
    max_chars: int,
    specific_keywords: Sequence[str],
    general_keywords: Sequence[str],
    revision: str,
) -> list[dict[str, Any]]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("CMNEE source must be a JSON array")
    candidates: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, dict) or not isinstance(raw.get("text"), str):
            continue
        score = keyword_score(raw["text"], specific_keywords, general_keywords)
        if score <= 0:
            continue
        chunks = chunk_text(raw["text"], min_chars=min_chars, max_chars=max_chars)
        for chunk_index, text in enumerate(chunks[:2]):
            candidates.append(
                {
                    "source_candidate_id": f"cmnee-{raw.get('id')}-{chunk_index}",
                    "text": text,
                    "source_type": "cmnee",
                    "source_id": str(raw.get("id")),
                    "source_split": "train",
                    "source_url": "https://www.modelscope.cn/datasets/mzzzhu/CMNEE",
                    "source_revision": revision,
                    "source_license": "Apache-2.0",
                    "selection_score": score,
                    "content_sha256": text_sha256(text),
                }
            )
    return candidates


class _BaikeMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.description = ""
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "meta" and (
            attributes.get("name") == "description"
            or attributes.get("property") == "og:description"
        ):
            self.description = attributes.get("content") or self.description
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


@dataclass
class BaikeCollection:
    candidates: list[dict[str, Any]]
    attempts: int
    cache_hits: int
    failures: list[dict[str, str]]


def collect_baike_candidates(
    seed_terms: Sequence[Mapping[str, Any]],
    *,
    cache_path: Path | str,
    pool_target: int,
    max_attempts: int,
    min_chars: int,
    max_chars: int,
    seed: int,
    timeout_seconds: int,
    delay_seconds: float,
    user_agent: str,
) -> BaikeCollection:
    import numpy as np

    cache_file = Path(cache_path)
    cached = {
        row["query"]: row for row in iter_objects_jsonl(cache_file)
    } if cache_file.is_file() else {}
    order = np.random.default_rng(seed).permutation(len(seed_terms))
    candidates: list[dict[str, Any]] = []
    new_cache: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    cache_hits = 0
    attempts = 0
    for raw_index in order:
        if len(candidates) >= pool_target or attempts >= max_attempts:
            break
        term = str(seed_terms[int(raw_index)]["term"])
        attempts += 1
        cached_page = cached.get(term)
        if cached_page is not None:
            cache_hits += 1
            page = cached_page
        else:
            url = f"https://baike.baidu.com/item/{quote(term, safe='')}"
            request = Request(url, headers={"User-Agent": user_agent})
            try:
                with urlopen(request, timeout=timeout_seconds) as response:
                    payload = response.read().decode("utf-8", errors="strict")
                    final_url = response.geturl()
                parser = _BaikeMetaParser()
                parser.feed(payload)
                page = {
                    "query": term,
                    "url": final_url,
                    "title": clean_text(parser.title),
                    "description": clean_text(parser.description),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                }
                new_cache.append(page)
            except Exception as exc:  # Network failures are audited, not fatal per page.
                failures.append({"query": term, "error": f"{type(exc).__name__}: {exc}"})
                time.sleep(delay_seconds)
                continue
            time.sleep(delay_seconds)
        description = str(page.get("description", ""))
        title = str(page.get("title", ""))
        probe = term[: min(4, len(term))]
        if probe not in f"{title} {description}":
            continue
        chunks = chunk_text(description, min_chars=min_chars, max_chars=max_chars)
        if not chunks:
            continue
        text = chunks[0]
        candidates.append(
            {
                "source_candidate_id": f"baike-{text_sha256(term)[:16]}",
                "text": text,
                "source_type": "baidu_baike",
                "source_id": term,
                "source_split": "public_page",
                "source_url": str(page["url"]),
                "source_revision": str(page["retrieved_at"]),
                "source_license": "Baidu Baike terms; private research cache only",
                "title": title.removesuffix("_百度百科"),
                "selection_score": 1,
                "content_sha256": text_sha256(text),
            }
        )
    if new_cache:
        merged_cache = list(cached.values()) + new_cache
        write_objects_jsonl_atomic(cache_file, sorted(merged_cache, key=lambda row: row["query"]))
    return BaikeCollection(candidates, attempts, cache_hits, failures)


def rank_candidates(candidates: Sequence[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    import numpy as np

    order = np.random.default_rng(seed).permutation(len(candidates))
    random_rank = {int(index): rank for rank, index in enumerate(order)}
    return [
        candidates[index]
        for index in sorted(
            range(len(candidates)),
            key=lambda index: (-int(candidates[index]["selection_score"]), random_rank[index]),
        )
    ]


def select_quotas_with_dedup(
    pools: Mapping[str, Sequence[dict[str, Any]]],
    quotas: Mapping[str, int],
    *,
    seed: int,
    ngram_size: int,
    containment_threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    accepted_grams: list[frozenset[str]] = []
    removed: list[dict[str, Any]] = []
    for source_type in ("baidu_baike", "patent", "cmnee"):
        quota = int(quotas[source_type])
        source_count = 0
        for candidate in rank_candidates(pools[source_type], seed):
            grams = normalized_ngrams(candidate["text"], ngram_size)
            duplicate_index: int | None = None
            duplicate_score = 0.0
            for index, existing in enumerate(accepted_grams):
                score = ngram_containment(grams, existing)
                if score >= containment_threshold:
                    duplicate_index = index
                    duplicate_score = score
                    break
            if duplicate_index is not None:
                removed.append(
                    {
                        "removed_id": candidate["source_candidate_id"],
                        "kept_id": accepted[duplicate_index]["source_candidate_id"],
                        "source_type": source_type,
                        "ngram_size": ngram_size,
                        "containment": round(duplicate_score, 6),
                        "reason": "8gram_containment",
                    }
                )
                continue
            accepted.append(candidate)
            accepted_grams.append(grams)
            source_count += 1
            if source_count == quota:
                break
        if source_count != quota:
            raise ValueError(
                f"{source_type}: needed {quota} unique candidates, found {source_count}"
            )
    final: list[dict[str, Any]] = []
    for index, candidate in enumerate(accepted, start=1):
        row = dict(candidate)
        row["id"] = f"domain-candidate-{index:04d}"
        row.pop("selection_score", None)
        validate_candidate(row)
        final.append(row)
    return final, removed


def validate_candidate(row: Mapping[str, Any]) -> None:
    required = {
        "id",
        "source_candidate_id",
        "text",
        "source_type",
        "source_id",
        "source_split",
        "source_url",
        "source_revision",
        "source_license",
        "title",
        "content_sha256",
    }
    missing = required.difference(row)
    if missing:
        raise ValueError(f"candidate missing keys: {sorted(missing)}")
    text = row["text"]
    if not isinstance(text, str) or not 100 <= len(text) <= 300:
        raise ValueError(f"{row['id']}: candidate text length is outside 100-300")
    if row["content_sha256"] != text_sha256(text):
        raise ValueError(f"{row['id']}: candidate content hash mismatch")


def match_seed_entities(text: str, terms: Sequence[str]) -> list[dict[str, Any]]:
    """Longest-first exact seed matching for post-approval distant supervision."""

    occupied = [False] * len(text)
    matches: list[dict[str, Any]] = []
    for term in sorted(set(terms), key=lambda value: (-len(value), value)):
        if len(term) < 2:
            continue
        cursor = 0
        while True:
            start = text.find(term, cursor)
            if start < 0:
                break
            end = start + len(term)
            if not any(occupied[start:end]):
                matches.append(
                    {"start": start, "end": end, "type": "EQUIPMENT", "span": term}
                )
                occupied[start:end] = [True] * (end - start)
            cursor = start + 1
    return sorted(matches, key=lambda entity: (entity["start"], entity["end"]))


def prelabel_candidate(row: Mapping[str, Any], terms: Sequence[str]) -> dict[str, Any]:
    """Create a unified proposal record. Do not run before schema approval."""

    record = {
        "id": row["id"],
        "text": row["text"],
        "entities": match_seed_entities(row["text"], terms),
        "relations": [],
    }
    validate_record(record)
    return record
