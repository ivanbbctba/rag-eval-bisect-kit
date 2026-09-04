"""Report compare tests."""

from __future__ import annotations

from rag_eval_bisect.compare import compare_reports


def test_compare_flags_title_only_regressions(passing_report, failing_report):
    diff = compare_reports(passing_report, failing_report)
    assert diff.before_passed is True
    assert diff.after_passed is False
    assert diff.regressions
    assert "night-owl-hours" in diff.regressions
    assert diff.improvements == []


def test_compare_identical_reports_has_no_flips(passing_report):
    diff = compare_reports(passing_report, passing_report)
    assert diff.regressions == []
    assert all(not case.flipped for case in diff.cases)
