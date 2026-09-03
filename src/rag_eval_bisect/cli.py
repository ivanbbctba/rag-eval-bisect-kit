"""CLI for running and comparing Layer A RAG eval reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rag_eval_bisect.compare import compare_reports
from rag_eval_bisect.fixtures import load_config, load_corpus, load_suite
from rag_eval_bisect.models import EvalReport
from rag_eval_bisect.runner import run_suite


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``rag-eval`` console script."""

    parser = argparse.ArgumentParser(
        prog="rag-eval",
        description="Run or compare deterministic Layer A RAG evals.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_run_parser(subparsers)
    _add_compare_parser(subparsers)
    args = parser.parse_args(argv)
    return args.handler(args)


def _add_run_parser(subparsers: argparse._SubParsersAction[Any]) -> None:
    parser = subparsers.add_parser("run", help="execute a fixture suite and emit a JSON report")
    parser.add_argument("--suite", type=Path, help="fixture suite YAML or JSON")
    parser.add_argument("--corpus", type=Path, help="corpus JSON")
    parser.add_argument("--config", type=Path, help="eval config snapshot")
    parser.add_argument("--output", type=Path, help="write report JSON to this path")
    parser.set_defaults(handler=_cmd_run)


def _add_compare_parser(subparsers: argparse._SubParsersAction[Any]) -> None:
    parser = subparsers.add_parser("compare", help="diff two Layer A reports")
    parser.add_argument("before", type=Path, help="baseline report JSON")
    parser.add_argument("after", type=Path, help="candidate report JSON")
    parser.add_argument("--output", type=Path, help="write diff JSON to this path")
    parser.set_defaults(handler=_cmd_compare)


def _cmd_run(args: argparse.Namespace) -> int:
    suite = load_suite(args.suite)
    corpus = load_corpus(args.corpus)
    config = load_config(args.config) if args.config else None
    report = run_suite(suite, corpus, config)
    _emit(report.model_dump(), args.output)
    _print_run_summary(report)
    return 0 if report.passed else 1


def _cmd_compare(args: argparse.Namespace) -> int:
    before = EvalReport.model_validate_json(args.before.read_text(encoding="utf-8"))
    after = EvalReport.model_validate_json(args.after.read_text(encoding="utf-8"))
    diff = compare_reports(before, after)
    _emit(diff.model_dump(), args.output)
    print(
        f"regressions={len(diff.regressions)} improvements={len(diff.improvements)} "
        f"before={'PASS' if diff.before_passed else 'FAIL'} "
        f"after={'PASS' if diff.after_passed else 'FAIL'}"
    )
    for case_id in diff.regressions:
        print(f"REGRESSION {case_id}")
    return 1 if diff.regressions else 0


def _print_run_summary(report: Any) -> None:
    verdict = "PASS" if report.passed else "FAIL"
    snapshot = report.snapshot_id or "default"
    print(f"{verdict} {report.passed_cases}/{report.total_cases} suite={report.suite_id} snapshot={snapshot}")
    for case in report.cases:
        status = "PASS" if case.passed else "FAIL"
        print(f"  {status} {case.case_id} retrieved={case.retrieved_ids}")


def _emit(payload: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(payload, indent=2)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    raise SystemExit(main())
