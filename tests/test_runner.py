"""Suite runner gate tests."""

from __future__ import annotations

from rag_eval_bisect.adapters import MockLLM, MockRetriever
from rag_eval_bisect.runner import run_suite


def test_baseline_keyword_config_passes_toy_suite(toy_suite, toy_corpus, baseline_config):
    report = run_suite(
        toy_suite,
        toy_corpus,
        baseline_config,
        retriever=MockRetriever(toy_corpus),
        llm=MockLLM(),
    )
    assert report.passed is True
    assert report.passed_cases == report.total_cases == 5
    assert report.snapshot_id == "01-baseline"


def test_title_only_config_fails_toy_suite(toy_suite, toy_corpus, title_only_config):
    report = run_suite(
        toy_suite,
        toy_corpus,
        title_only_config,
        retriever=MockRetriever(toy_corpus),
        llm=MockLLM(),
    )
    assert report.passed is False
    assert report.passed_cases < report.total_cases
    failed = [case.case_id for case in report.cases if not case.passed]
    assert "night-owl-hours" in failed
