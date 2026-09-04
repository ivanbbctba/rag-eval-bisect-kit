"""Unit tests for deterministic Layer A metrics."""

from __future__ import annotations

from rag_eval_bisect.metrics import case_passed, compute_layer_a_metrics
from rag_eval_bisect.models import EvalConfig, FixtureCase, GeneratedAnswer


def _metrics(retrieved, answer_text="Harbor 12:30 off-peak", citations=None, **case_kw):
    case = FixtureCase(
        id="case",
        question="q",
        gold_doc_ids=["route-red"],
        must_mention=["Harbor"],
        **case_kw,
    )
    answer = GeneratedAnswer(text=answer_text, citations=citations or retrieved)
    return compute_layer_a_metrics(case, retrieved, answer, EvalConfig())


def test_hit_and_recall_pass_when_gold_retrieved():
    metrics = {metric.name: metric for metric in _metrics(["route-red", "route-blue"])}
    assert metrics["hit_at_k"].value == 1.0
    assert metrics["recall_at_k"].value == 1.0
    assert metrics["mrr"].value == 1.0


def test_hit_fails_when_gold_missing():
    metrics = {metric.name: metric for metric in _metrics(["route-blue"])}
    assert metrics["hit_at_k"].passed is False
    assert metrics["recall_at_k"].value == 0.0
    assert case_passed(metrics.values()) is False


def test_must_mention_is_case_insensitive():
    metrics = _metrics(["route-red"], answer_text="harbor station list")
    assert {metric.name: metric for metric in metrics}["must_mention"].passed is True


def test_forbidden_term_fails_gate():
    metrics = _metrics(
        ["route-red"],
        answer_text="Harbor is closed permanently",
        forbidden=["permanently"],
    )
    assert {metric.name: metric for metric in metrics}["forbidden"].passed is False


def test_citation_support_rejects_unretrieved_ids():
    metrics = _metrics(["route-red"], citations=["route-red", "ghost"])
    assert {metric.name: metric for metric in metrics}["citation_support"].passed is False


def test_identical_inputs_are_deterministic():
    first = _metrics(["route-red"])
    second = _metrics(["route-red"])
    assert [metric.model_dump() for metric in first] == [metric.model_dump() for metric in second]
