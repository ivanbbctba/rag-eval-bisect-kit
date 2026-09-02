"""Suite runner that executes fixtures and gates on Layer A metrics."""

from __future__ import annotations

from collections.abc import Sequence

from rag_eval_bisect.adapters import LLMAdapter, MockLLM, MockRetriever, Retriever
from rag_eval_bisect.metrics import case_passed, compute_layer_a_metrics
from rag_eval_bisect.models import (
    CaseResult,
    CorpusDoc,
    EvalConfig,
    EvalReport,
    FixtureCase,
    FixtureSuite,
)


def run_suite(
    suite: FixtureSuite,
    corpus: Sequence[CorpusDoc],
    config: EvalConfig | None = None,
    *,
    retriever: Retriever | None = None,
    llm: LLMAdapter | None = None,
) -> EvalReport:
    """Run every case through retrieval + generation, then apply Layer A gates.

    The suite verdict is PASS only when every case passes every gating metric.
    """

    eval_config = config or EvalConfig()
    active_retriever = retriever or MockRetriever(corpus)
    active_llm = llm or MockLLM()

    case_results: list[CaseResult] = []
    for case in suite.cases:
        case_results.append(
            _run_case(case, eval_config, active_retriever, active_llm)
        )

    passed_cases = sum(1 for result in case_results if result.passed)
    return EvalReport(
        suite_id=suite.suite_id,
        snapshot_id=eval_config.snapshot_id,
        passed=passed_cases == len(case_results) and bool(case_results),
        passed_cases=passed_cases,
        total_cases=len(case_results),
        config=eval_config,
        cases=case_results,
    )


def _run_case(
    case: FixtureCase,
    config: EvalConfig,
    retriever: Retriever,
    llm: LLMAdapter,
) -> CaseResult:
    chunks = retriever.retrieve(case.question, config)
    answer = llm.generate(case.question, chunks)
    retrieved_ids = [chunk.doc_id for chunk in chunks]
    metrics = compute_layer_a_metrics(case, retrieved_ids, answer, config)
    return CaseResult(
        case_id=case.id,
        question=case.question,
        passed=case_passed(metrics),
        retrieved_ids=retrieved_ids,
        citations=list(answer.citations),
        answer=answer.text,
        metrics=metrics,
    )
