"""Deterministic Layer A retrieval and string-match metrics.

These functions are pure: identical retrieved ids, gold ids, answer text, and
thresholds always produce identical PASS/FAIL. No LLM judge is invoked.
"""

from __future__ import annotations

from collections.abc import Sequence

from rag_eval_bisect.models import EvalConfig, FixtureCase, GeneratedAnswer, MetricResult


def compute_layer_a_metrics(
    case: FixtureCase,
    retrieved_ids: Sequence[str],
    answer: GeneratedAnswer,
    config: EvalConfig,
) -> list[MetricResult]:
    """Compute gating Layer A metrics for one case."""

    return [
        _hit_at_k(case, retrieved_ids, config),
        _recall_at_k(case, retrieved_ids, config),
        _mrr(case, retrieved_ids, config),
        _precision_at_k(case, retrieved_ids, config),
        _must_mention(case, answer),
        _forbidden(case, answer),
        _citation_support(retrieved_ids, answer, config),
    ]


def case_passed(metrics: Sequence[MetricResult]) -> bool:
    """A case passes when every gating metric passes."""

    return all(metric.passed for metric in metrics if metric.gating)


def _hit_at_k(
    case: FixtureCase, retrieved_ids: Sequence[str], config: EvalConfig
) -> MetricResult:
    retrieved = set(retrieved_ids)
    gold = set(case.gold_doc_ids)
    value = 1.0 if retrieved & gold else 0.0
    return MetricResult(
        id="A1",
        name="hit_at_k",
        value=value,
        threshold=config.hit_at_k_min,
        passed=value >= config.hit_at_k_min,
        gating=True,
        detail="at least one gold document appears in the retrieved set",
    )


def _recall_at_k(
    case: FixtureCase, retrieved_ids: Sequence[str], config: EvalConfig
) -> MetricResult:
    gold = set(case.gold_doc_ids)
    if not gold:
        return MetricResult(
            id="A2",
            name="recall_at_k",
            value=1.0,
            threshold=config.recall_at_k_min,
            passed=True,
            gating=True,
            detail="no gold documents labeled",
        )
    value = len(set(retrieved_ids) & gold) / len(gold)
    return MetricResult(
        id="A2",
        name="recall_at_k",
        value=value,
        threshold=config.recall_at_k_min,
        passed=value >= config.recall_at_k_min,
        gating=True,
        detail="fraction of gold documents retrieved",
    )


def _mrr(
    case: FixtureCase, retrieved_ids: Sequence[str], config: EvalConfig
) -> MetricResult:
    gold = set(case.gold_doc_ids)
    value = 0.0
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in gold:
            value = 1.0 / rank
            break
    gating = config.mrr_min > 0.0
    return MetricResult(
        id="A3",
        name="mrr",
        value=value,
        threshold=config.mrr_min if gating else None,
        passed=value >= config.mrr_min if gating else True,
        gating=gating,
        detail="reciprocal rank of the first gold document",
    )


def _precision_at_k(
    case: FixtureCase, retrieved_ids: Sequence[str], config: EvalConfig
) -> MetricResult:
    if not retrieved_ids:
        value = 0.0
    else:
        value = len(set(retrieved_ids) & set(case.gold_doc_ids)) / len(retrieved_ids)
    gating = config.precision_at_k_min > 0.0
    return MetricResult(
        id="A4",
        name="precision_at_k",
        value=value,
        threshold=config.precision_at_k_min if gating else None,
        passed=value >= config.precision_at_k_min if gating else True,
        gating=gating,
        detail="fraction of retrieved documents that are gold",
    )


def _must_mention(case: FixtureCase, answer: GeneratedAnswer) -> MetricResult:
    haystack = answer.text.casefold()
    missing = [term for term in case.must_mention if term.casefold() not in haystack]
    passed = not missing
    return MetricResult(
        id="A5",
        name="must_mention",
        value=0.0 if missing else 1.0,
        threshold=1.0 if case.must_mention else None,
        passed=passed,
        gating=True,
        detail="missing terms: {0}".format(missing) if missing else "all required terms present",
    )


def _forbidden(case: FixtureCase, answer: GeneratedAnswer) -> MetricResult:
    haystack = answer.text.casefold()
    hits = [term for term in case.forbidden if term.casefold() in haystack]
    passed = not hits
    return MetricResult(
        id="A6",
        name="forbidden",
        value=0.0 if hits else 1.0,
        threshold=1.0 if case.forbidden else None,
        passed=passed,
        gating=True,
        detail="forbidden terms present: {0}".format(hits) if hits else "no forbidden terms",
    )


def _citation_support(
    retrieved_ids: Sequence[str],
    answer: GeneratedAnswer,
    config: EvalConfig,
) -> MetricResult:
    retrieved = set(retrieved_ids)
    unsupported = [doc_id for doc_id in answer.citations if doc_id not in retrieved]
    if not config.require_citations:
        return MetricResult(
            id="A7",
            name="citation_support",
            value=1.0,
            threshold=None,
            passed=True,
            gating=False,
            detail="citation check disabled",
        )
    passed = not unsupported
    return MetricResult(
        id="A7",
        name="citation_support",
        value=0.0 if unsupported else 1.0,
        threshold=1.0,
        passed=passed,
        gating=True,
        detail=(
            "unsupported citations: {0}".format(unsupported)
            if unsupported
            else "all citations were retrieved"
        ),
    )
