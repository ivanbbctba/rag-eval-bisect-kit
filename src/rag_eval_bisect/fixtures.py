"""Toy municipal-transit corpus and fixture suite for hermetic mock retrieval."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from rag_eval_bisect.models import CorpusDoc, EvalConfig, FixtureCase, FixtureSuite

_REPO_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


TOY_CORPUS: tuple[CorpusDoc, ...] = (
    CorpusDoc(
        id="night-owl",
        title="After-Hours Fleet",
        text=(
            "The night owl bus runs from 12:30 a.m. to 4:30 a.m. on Fridays and "
            "Saturdays. Late-night service uses the same downtown loop as daytime routes."
        ),
    ),
    CorpusDoc(
        id="bike-policy",
        title="Carry-On Rules",
        text=(
            "Riders may bring a bicycle on the train during off-peak hours. "
            "Folding bikes are allowed at all times. Peak-hour bicycle boarding "
            "is restricted on crowded cars."
        ),
    ),
    CorpusDoc(
        id="fare-policy",
        title="Payment Windows",
        text=(
            "A single fare includes one transfer within 90 minutes. Transfers "
            "are encoded on the same card tap. Cash riders receive a paper transfer slip."
        ),
    ),
    CorpusDoc(
        id="lost-found",
        title="Property Desk",
        text=(
            "Lost backpacks and other items are held at the central lost and found "
            "office for 14 days. Bring a photo ID to recover property."
        ),
    ),
    CorpusDoc(
        id="route-red",
        title="Trunk Corridor",
        text=(
            "Red line stations include Harbor, Midtown, University, and Airport. "
            "The red line is the north-south trunk of the municipal rail network."
        ),
    ),
    CorpusDoc(
        id="route-blue",
        title="Waterfront Branch",
        text=(
            "Blue line stations include Market, Ferry, and Lighthouse. "
            "The waterfront branch stays on its own corridor."
        ),
    ),
    CorpusDoc(
        id="service-alerts",
        title="Night Notices",
        text=(
            "Service alerts are posted on the website and station boards. Alerts "
            "do not change the published night owl timetable."
        ),
    ),
    CorpusDoc(
        id="accessibility",
        title="Boarding Assistance",
        text=(
            "Wheelchair users board through the first door. Operators deploy a "
            "ramp on request. Priority seating is marked near the operator."
        ),
    ),
)


TOY_SUITE = FixtureSuite(
    suite_id="transit-toy-v1",
    cases=[
        FixtureCase(
            id="night-owl-hours",
            question="What time does the night owl bus run?",
            gold_doc_ids=["night-owl"],
            must_mention=["12:30"],
        ),
        FixtureCase(
            id="bike-on-train",
            question="Can I bring a bicycle on the train?",
            gold_doc_ids=["bike-policy"],
            must_mention=["off-peak"],
        ),
        FixtureCase(
            id="fare-transfer",
            question="How do transfers work with one fare?",
            gold_doc_ids=["fare-policy"],
            must_mention=["90 minutes"],
        ),
        FixtureCase(
            id="lost-backpack",
            question="Where do I recover a lost backpack?",
            gold_doc_ids=["lost-found"],
            must_mention=["14 days"],
        ),
        FixtureCase(
            id="red-line-stations",
            question="Which stations are on the red line?",
            gold_doc_ids=["route-red"],
            must_mention=["Harbor"],
        ),
    ],
)


def default_fixtures_dir() -> Path:
    """Resolve the repo ``fixtures/`` directory from cwd or checkout root."""

    cwd_dir = Path.cwd() / "fixtures"
    if cwd_dir.exists():
        return cwd_dir
    return _REPO_FIXTURES


def load_corpus(path: Path | None = None) -> list[CorpusDoc]:
    """Load corpus documents from JSON, or return the built-in toy corpus."""

    if path is None:
        candidate = default_fixtures_dir() / "corpus.json"
        if not candidate.exists():
            return list(TOY_CORPUS)
        path = candidate
    payload = json.loads(path.read_text(encoding="utf-8"))
    docs = payload["docs"] if isinstance(payload, dict) and "docs" in payload else payload
    return [CorpusDoc.model_validate(doc) for doc in docs]


def load_suite(path: Path | None = None) -> FixtureSuite:
    """Load a fixture suite from YAML or JSON, or return the built-in suite."""

    if path is None:
        candidate = default_fixtures_dir() / "suite.yaml"
        if not candidate.exists():
            return TOY_SUITE
        path = candidate
    text = path.read_text(encoding="utf-8")
    payload = yaml.safe_load(text) if path.suffix in {".yaml", ".yml"} else json.loads(text)
    return FixtureSuite.model_validate(payload)


def load_config(path: Path) -> EvalConfig:
    """Load an eval config snapshot from JSON or YAML."""

    text = path.read_text(encoding="utf-8")
    payload = yaml.safe_load(text) if path.suffix in {".yaml", ".yml"} else json.loads(text)
    if "snapshot_id" not in payload:
        payload["snapshot_id"] = path.stem
    return EvalConfig.model_validate(payload)


def load_snapshots(directory: Path) -> list[EvalConfig]:
    """Load ordered config snapshots (filename sort) from a directory."""

    files = sorted(
        [
            path
            for path in directory.iterdir()
            if path.suffix in {".json", ".yaml", ".yml"} and path.is_file()
        ]
    )
    if not files:
        raise FileNotFoundError(f"no snapshot files found in {directory}")
    return [load_config(path) for path in files]
