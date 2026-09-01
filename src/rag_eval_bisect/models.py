"""Eval config, fixture, and report models for Layer A RAG evaluation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CorpusDoc(BaseModel):
    """One document in a hermetic toy or user-supplied corpus."""

    id: str
    title: str
    text: str

    model_config = ConfigDict(frozen=True)


class RetrievedChunk(BaseModel):
    """A ranked retrieval hit returned by a retriever adapter."""

    doc_id: str
    title: str
    text: str
    score: float
    rank: int

    model_config = ConfigDict(frozen=True)


class GeneratedAnswer(BaseModel):
    """Adapter output: answer text plus cited document ids."""

    text: str
    citations: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class FixtureCase(BaseModel):
    """One labeled eval case. Gold ids and string checks stay deterministic."""

    id: str
    question: str
    gold_doc_ids: list[str]
    must_mention: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class FixtureSuite(BaseModel):
    """Named collection of fixture cases used by run/compare/bisect."""

    suite_id: str
    cases: list[FixtureCase]

    model_config = ConfigDict(frozen=True)


class EvalConfig(BaseModel):
    """Retrieval and Layer A gate thresholds for one eval snapshot."""

    top_k: int = 4
    min_score: float = 0.0
    title_boost: float = 0.0
    score_mode: Literal["keyword", "title_only"] = "keyword"
    hit_at_k_min: float = 1.0
    recall_at_k_min: float = 1.0
    mrr_min: float = 0.0
    precision_at_k_min: float = 0.0
    require_citations: bool = True
    snapshot_id: str | None = None

    model_config = ConfigDict(frozen=True)


class MetricResult(BaseModel):
    """Single deterministic metric with an optional gating threshold."""

    id: str
    name: str
    value: float | None
    threshold: float | None
    passed: bool
    gating: bool = True
    detail: str = ""

    model_config = ConfigDict(frozen=True)


class CaseResult(BaseModel):
    """Per-case Layer A results, retrieved ids, and generated answer."""

    case_id: str
    question: str
    passed: bool
    retrieved_ids: list[str]
    citations: list[str]
    answer: str
    metrics: list[MetricResult]

    model_config = ConfigDict(frozen=True)


class EvalReport(BaseModel):
    """Suite-level PASS/FAIL report written by `rag-eval run`."""

    suite_id: str
    snapshot_id: str | None
    passed: bool
    passed_cases: int
    total_cases: int
    config: EvalConfig
    cases: list[CaseResult]
    extra: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)
