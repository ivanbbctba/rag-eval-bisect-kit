"""FastAPI health and eval-run endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from rag_eval_bisect.api import app
from rag_eval_bisect.models import EvalConfig


def test_health_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_eval_run_default_passes():
    client = TestClient(app)
    response = client.post("/eval/run", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["total_cases"] == 5


def test_eval_run_accepts_failing_config():
    client = TestClient(app)
    config = EvalConfig(snapshot_id="api-title-only", top_k=2, score_mode="title_only")
    response = client.post("/eval/run", json={"config": config.model_dump()})
    assert response.status_code == 200
    assert response.json()["passed"] is False
