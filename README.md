# rag-eval-bisect-kit

Portable, CI-friendly RAG evaluation with a bisect UX.

RAG teams change chunking, retrieval scoring, and prompts, then cannot prove
which snapshot broke labeled cases. This kit is the eval harness for that
gap. It is not a domain RAG app and not a RAGAS clone.

Layer A (deterministic retrieval + string checks) is the only gate. Optional
LLM-as-judge scoring is out of scope for the MVP.

The Layer A / Layer B split is taken from
[frontline-clinical-rag ADR-009](https://github.com/ivanbbctba/frontline-clinical-rag/blob/main/docs/adr/ADR-009.md).
This repository generalizes that decision: same determinism rule, no clinical
graph, no Merck PDF, no API keys.

## Install

```bash
python -m pip install -e ".[dev]"
```

Requires Python 3.11+.

## What it does

| Command | Result |
|---------|--------|
| `rag-eval run` | Execute a fixture suite. Print PASS/FAIL and write a JSON report. |
| `rag-eval compare` | Diff two reports by case id. Exit 1 on regressions. |
| `rag-eval bisect` | Binary-search ordered config snapshots to the first failing change. |

Pluggable `Retriever` and `LLMAdapter` protocols ship with `MockRetriever`
and `MockLLM` over a toy municipal-transit corpus.

HTTP surface:

- `GET /health`
- `POST /eval/run` → Layer A report JSON

## Bisect walkthrough

The committed snapshots under `fixtures/snapshots/` tell a short regression
story:

1. `01-baseline` — keyword overlap, `top_k=4` → PASS
2. `02-title-boost` — same, plus title boost → PASS
3. `03-tighter-topk` — `top_k=2` → still PASS
4. `04-title-only` — score titles only, drop body text → FAIL

```bash
rag-eval run --config fixtures/snapshots/01-baseline.json --output samples/report.json
rag-eval run --config fixtures/snapshots/04-title-only.json --output /tmp/broken.json
rag-eval compare samples/report.json /tmp/broken.json
rag-eval bisect --snapshots fixtures/snapshots
```

Expected bisect line:

```text
first failing snapshot: 04-title-only
```

That is the first config that stops retrieving gold documents whose titles
do not contain the query terms (for example `After-Hours Fleet` vs
"What time does the night owl bus run?").

## Sample report

`samples/report.json` is a Layer A artifact from the baseline snapshot.
A passing suite looks like:

```json
{
  "suite_id": "transit-toy-v1",
  "snapshot_id": "01-baseline",
  "passed": true,
  "passed_cases": 5,
  "total_cases": 5
}
```

Each case records retrieved ids, citations, and the A1–A7 metric vector.
CI asserts this shape with mocks; it does not call a live model.

## HTTP

```bash
uvicorn rag_eval_bisect.api:app --port 8000
curl -s localhost:8000/health
curl -s -X POST localhost:8000/eval/run -H 'content-type: application/json' -d '{}'
```

## Tests

```bash
pytest
```

GitHub Actions runs the same command on every push to `main`.

## Metric design

See [docs/adr/0001-layer-a-metric-design.md](docs/adr/0001-layer-a-metric-design.md).
