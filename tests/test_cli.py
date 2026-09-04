"""CLI harness tests for run, compare, and bisect."""

from __future__ import annotations

import json

from rag_eval_bisect.cli import main


def test_cli_run_writes_passing_report(tmp_path, repo_root):
    output = tmp_path / "report.json"
    code = main(
        [
            "run",
            "--suite",
            str(repo_root / "fixtures" / "suite.yaml"),
            "--corpus",
            str(repo_root / "fixtures" / "corpus.json"),
            "--config",
            str(repo_root / "fixtures" / "snapshots" / "01-baseline.json"),
            "--output",
            str(output),
        ]
    )
    assert code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert payload["total_cases"] == 5


def test_cli_run_fails_on_title_only(tmp_path, repo_root):
    output = tmp_path / "bad.json"
    code = main(
        [
            "run",
            "--suite",
            str(repo_root / "fixtures" / "suite.yaml"),
            "--corpus",
            str(repo_root / "fixtures" / "corpus.json"),
            "--config",
            str(repo_root / "fixtures" / "snapshots" / "04-title-only.json"),
            "--output",
            str(output),
        ]
    )
    assert code == 1
    assert json.loads(output.read_text(encoding="utf-8"))["passed"] is False


def test_cli_compare_detects_regression(tmp_path, repo_root):
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    assert (
        main(
            [
                "run",
                "--config",
                str(repo_root / "fixtures" / "snapshots" / "01-baseline.json"),
                "--output",
                str(good),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "run",
                "--config",
                str(repo_root / "fixtures" / "snapshots" / "04-title-only.json"),
                "--output",
                str(bad),
            ]
        )
        == 1
    )
    assert main(["compare", str(good), str(bad)]) == 1


def test_cli_bisect_prints_first_fail(repo_root):
    code = main(["bisect", "--snapshots", str(repo_root / "fixtures" / "snapshots")])
    assert code == 1
