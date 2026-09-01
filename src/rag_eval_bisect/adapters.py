"""Retriever and LLM adapter protocols plus hermetic mock implementations."""

from __future__ import annotations

import re
from typing import Protocol, Sequence

from rag_eval_bisect.models import (
    CorpusDoc,
    EvalConfig,
    GeneratedAnswer,
    RetrievedChunk,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "at",
        "be",
        "can",
        "do",
        "does",
        "for",
        "from",
        "how",
        "i",
        "in",
        "is",
        "my",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "where",
        "which",
        "with",
    }
)


def tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric tokens used by the mock retriever."""

    return set(_TOKEN_RE.findall(text.lower()))


def content_tokens(text: str) -> set[str]:
    """Tokens used for ranking: stopwords removed, light plural folding."""

    raw = tokenize(text) - _STOPWORDS
    folded = set(raw)
    for token in raw:
        if token.endswith("s") and len(token) > 3:
            folded.add(token[:-1])
        elif len(token) > 2:
            folded.add(f"{token}s")
    return folded


class Retriever(Protocol):
    """Pluggable retrieval adapter. Implementations must be side-effect free."""

    def retrieve(self, question: str, config: EvalConfig) -> list[RetrievedChunk]:
        """Return ranked chunks for ``question`` under ``config``."""


class LLMAdapter(Protocol):
    """Pluggable generation adapter. Layer A never judges this output."""

    def generate(self, question: str, chunks: Sequence[RetrievedChunk]) -> GeneratedAnswer:
        """Produce an answer and citation ids from retrieved chunks."""


class MockRetriever:
    """Deterministic keyword overlap retriever over an in-memory corpus.

    ``score_mode="keyword"`` scores query overlap against title and body.
    ``score_mode="title_only"`` ignores body text and is useful as a failing
    snapshot in bisect walkthroughs.
    """

    def __init__(self, corpus: Sequence[CorpusDoc]) -> None:
        self._corpus = tuple(corpus)

    def retrieve(self, question: str, config: EvalConfig) -> list[RetrievedChunk]:
        """Rank corpus docs by token overlap and return the configured top-k."""

        query_tokens = content_tokens(question)
        scored: list[tuple[float, str, CorpusDoc]] = []
        for doc in self._corpus:
            title_tokens = content_tokens(doc.title)
            body_tokens = content_tokens(f"{doc.title} {doc.text}")
            if config.score_mode == "title_only":
                overlap = len(query_tokens & title_tokens)
                score = float(overlap)
            else:
                overlap = len(query_tokens & body_tokens)
                title_hits = len(query_tokens & title_tokens)
                score = float(overlap) + config.title_boost * float(title_hits)
            if score >= config.min_score:
                scored.append((score, doc.id, doc))

        scored.sort(key=lambda item: (-item[0], item[1]))
        chunks: list[RetrievedChunk] = []
        for rank, (score, _doc_id, doc) in enumerate(scored[: config.top_k], start=1):
            chunks.append(
                RetrievedChunk(
                    doc_id=doc.id,
                    title=doc.title,
                    text=doc.text,
                    score=score,
                    rank=rank,
                )
            )
        return chunks


class MockLLM:
    """Fixed generator that concatenates retrieved text and cites those ids.

    No API keys. Answers stay stable so Layer A string checks are reproducible.
    """

    def generate(self, question: str, chunks: Sequence[RetrievedChunk]) -> GeneratedAnswer:
        """Return retrieved text as the answer, or a deterministic empty reply."""

        del question
        if not chunks:
            return GeneratedAnswer(
                text="No supporting documents were retrieved.",
                citations=[],
            )
        joined = " ".join(chunk.text for chunk in chunks)
        return GeneratedAnswer(
            text=joined,
            citations=[chunk.doc_id for chunk in chunks],
        )
