"""Config-snapshot bisect tests."""

from __future__ import annotations

from rag_eval_bisect.bisect import bisect_snapshots
from rag_eval_bisect.fixtures import load_snapshots


def test_bisect_finds_title_only_as_first_failure(toy_suite, toy_corpus, repo_root):
    snapshots = load_snapshots(repo_root / "fixtures" / "snapshots")
    result = bisect_snapshots(snapshots, toy_suite, toy_corpus)
    assert result.all_passed is False
    assert result.first_failing_snapshot == "04-title-only"
    assert result.culprit_report is not None
    assert result.culprit_report.passed is False


def test_bisect_all_pass_when_only_good_snapshots(toy_suite, toy_corpus, repo_root):
    snapshots = load_snapshots(repo_root / "fixtures" / "snapshots")[:3]
    result = bisect_snapshots(snapshots, toy_suite, toy_corpus)
    assert result.all_passed is True
    assert result.first_failing_snapshot is None
