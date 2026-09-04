"""FastAPI service exposing health and Layer A eval-run endpoints."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from rag_eval_bisect.fixtures import load_corpus, load_suite
from rag_eval_bisect.models import EvalConfig, EvalReport
from rag_eval_bisect.runner import run_suite

app = FastAPI(
    title="rag-eval-bisect-kit",
    description="Hermetic Layer A RAG evaluation with JSON reports.",
    version="0.1.0",
)


class RunRequest(BaseModel):
    """Optional config override for ``POST /eval/run``."""

    config: EvalConfig | None = Field(default=None)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by CI and local smoke checks."""

    return {"status": "ok"}


@app.post("/eval/run", response_model=EvalReport)
def eval_run(request: RunRequest | None = None) -> EvalReport:
    """Run the default toy suite and return a Layer A report."""

    config = request.config if request is not None else None
    return run_suite(load_suite(), load_corpus(), config)
