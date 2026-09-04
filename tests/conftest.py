"""Shared fixtures for hermetic Layer A tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from rag_eval_bisect.adapters import MockLLM, MockRetriever
from rag_eval_bisect.fixtures import TOY_CORPUS, TOY_SUITE
from rag_eval_bisect.models import EvalConfig, EvalReport
from rag_eval_bisect.runner import run_suite


@pytest.fixture
def toy_corpus():
    return list(TOY_CORPUS)


@pytest.fixture
def toy_suite():
    return TOY_SUITE


@pytest.fixture
def baseline_config():
    return EvalConfig(snapshot_id="01-baseline", top_k=4, score_mode="keyword")


@pytest.fixture
def title_only_config():
    return EvalConfig(snapshot_id="04-title-only", top_k=2, score_mode="title_only")


@pytest.fixture
def passing_report(toy_suite, toy_corpus, baseline_config) -> EvalReport:
    return run_suite(
        toy_suite,
        toy_corpus,
        baseline_config,
        retriever=MockRetriever(toy_corpus),
        llm=MockLLM(),
    )


@pytest.fixture
def failing_report(toy_suite, toy_corpus, title_only_config) -> EvalReport:
    return run_suite(
        toy_suite,
        toy_corpus,
        title_only_config,
        retriever=MockRetriever(toy_corpus),
        llm=MockLLM(),
    )


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
