"""Binary search over ordered config snapshots to the first failing change."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from rag_eval_bisect.adapters import LLMAdapter, Retriever
from rag_eval_bisect.models import CorpusDoc, EvalConfig, EvalReport, FixtureSuite
from rag_eval_bisect.runner import run_suite


class SnapshotProbe(BaseModel):
    """One snapshot evaluated during bisect."""

    snapshot_id: str
    passed: bool
    passed_cases: int
    total_cases: int

    model_config = ConfigDict(frozen=True)


class BisectResult(BaseModel):
    """First failing snapshot plus the probes used to locate it."""

    first_failing_snapshot: str | None
    all_passed: bool
    probes: list[SnapshotProbe] = Field(default_factory=list)
    culprit_report: EvalReport | None = None

    model_config = ConfigDict(frozen=True)


def bisect_snapshots(
    snapshots: Sequence[EvalConfig],
    suite: FixtureSuite,
    corpus: Sequence[CorpusDoc],
    *,
    retriever: Retriever | None = None,
    llm: LLMAdapter | None = None,
) -> BisectResult:
    """Return the earliest snapshot that fails Layer A gates.

    Snapshots must be ordered oldest-to-newest, as in a config changelog.
    The search is binary; each probe is recorded so the path is auditable.
    """

    if not snapshots:
        raise ValueError("at least one config snapshot is required")

    probes: list[SnapshotProbe] = []
    reports: dict[int, EvalReport] = {}

    def probe(index: int) -> EvalReport:
        if index not in reports:
            reports[index] = run_suite(
                suite,
                corpus,
                snapshots[index],
                retriever=retriever,
                llm=llm,
            )
            report = reports[index]
            probes.append(
                SnapshotProbe(
                    snapshot_id=report.snapshot_id or snapshots[index].snapshot_id or str(index),
                    passed=report.passed,
                    passed_cases=report.passed_cases,
                    total_cases=report.total_cases,
                )
            )
        return reports[index]

    low = 0
    high = len(snapshots) - 1
    first_fail: int | None = None

    last = probe(high)
    if last.passed:
        return BisectResult(first_failing_snapshot=None, all_passed=True, probes=probes)

    first = probe(low)
    if not first.passed:
        return BisectResult(
            first_failing_snapshot=first.snapshot_id or snapshots[0].snapshot_id or "0",
            all_passed=False,
            probes=probes,
            culprit_report=first,
        )

    while low + 1 < high:
        mid = (low + high) // 2
        report = probe(mid)
        if report.passed:
            low = mid
        else:
            high = mid
            first_fail = mid

    culprit_index = first_fail if first_fail is not None else high
    culprit = probe(culprit_index)
    return BisectResult(
        first_failing_snapshot=culprit.snapshot_id
        or snapshots[culprit_index].snapshot_id
        or str(culprit_index),
        all_passed=False,
        probes=probes,
        culprit_report=culprit,
    )
