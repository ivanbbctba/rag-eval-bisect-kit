"""Structured diffs between two Layer A eval reports."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from rag_eval_bisect.models import CaseResult, EvalReport


class MetricDelta(BaseModel):
    """Numeric change for one named metric on one case."""

    name: str
    before: float | None
    after: float | None
    delta: float | None

    model_config = ConfigDict(frozen=True)


class CaseDiff(BaseModel):
    """PASS/FAIL flip and metric deltas for one shared case id."""

    case_id: str
    before: str
    after: str
    flipped: bool
    metric_deltas: list[MetricDelta] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class ReportDiff(BaseModel):
    """Suite-level comparison used by `rag-eval compare`."""

    before_suite_id: str
    after_suite_id: str
    before_snapshot_id: str | None
    after_snapshot_id: str | None
    before_passed: bool
    after_passed: bool
    regressions: list[str]
    improvements: list[str]
    cases: list[CaseDiff]

    model_config = ConfigDict(frozen=True)


def compare_reports(before: EvalReport, after: EvalReport) -> ReportDiff:
    """Diff two reports by case id and surface regressions first."""

    before_cases = {result.case_id: result for result in before.cases}
    after_cases = {result.case_id: result for result in after.cases}
    case_ids = sorted(set(before_cases) | set(after_cases))

    diffs: list[CaseDiff] = []
    regressions: list[str] = []
    improvements: list[str] = []
    for case_id in case_ids:
        left = before_cases.get(case_id)
        right = after_cases.get(case_id)
        before_status = _status(left)
        after_status = _status(right)
        flipped = before_status != after_status
        if before_status == "PASS" and after_status == "FAIL":
            regressions.append(case_id)
        elif before_status == "FAIL" and after_status == "PASS":
            improvements.append(case_id)
        diffs.append(
            CaseDiff(
                case_id=case_id,
                before=before_status,
                after=after_status,
                flipped=flipped,
                metric_deltas=_metric_deltas(left, right),
            )
        )

    return ReportDiff(
        before_suite_id=before.suite_id,
        after_suite_id=after.suite_id,
        before_snapshot_id=before.snapshot_id,
        after_snapshot_id=after.snapshot_id,
        before_passed=before.passed,
        after_passed=after.passed,
        regressions=regressions,
        improvements=improvements,
        cases=diffs,
    )


def _status(result: CaseResult | None) -> str:
    if result is None:
        return "MISSING"
    return "PASS" if result.passed else "FAIL"


def _metric_deltas(left: CaseResult | None, right: CaseResult | None) -> list[MetricDelta]:
    left_metrics = {metric.name: metric.value for metric in left.metrics} if left else {}
    right_metrics = {metric.name: metric.value for metric in right.metrics} if right else {}
    names = sorted(set(left_metrics) | set(right_metrics))
    deltas: list[MetricDelta] = []
    for name in names:
        before = left_metrics.get(name)
        after = right_metrics.get(name)
        delta = None
        if before is not None and after is not None:
            delta = after - before
        deltas.append(MetricDelta(name=name, before=before, after=after, delta=delta))
    return deltas
