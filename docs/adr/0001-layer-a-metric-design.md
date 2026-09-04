# ADR-0001: Layer A as the only CI gate

**Status:** Accepted  
**Date:** 2026-09-04  
**Deciders:** Ivan Beira

## Context

RAG teams routinely change chunking, retrieval scoring, prompt text, and
`top_k`. Failures show up as "the demo got worse" without a reproducible
artifact that names the first config change that broke labeled cases.

This kit is a portable eval harness, not a domain RAG application and not a
RAGAS clone. It exists so a CI job can prove that a retrieval/config snapshot
still satisfies labeled fixtures.

The design is an extraction of the Layer A / Layer B split documented in
[frontline-clinical-rag ADR-009](https://github.com/ivanbbctba/frontline-clinical-rag/blob/main/docs/adr/ADR-009.md).
That ADR used clinical graph state and Merck fixtures. This kit keeps the
determinism rule and drops the domain graph, the PDF corpus, and any live
provider.

## Decision

Gate `run`, `compare`, and `bisect` on **Layer A** metrics only:

| ID | Metric | PASS when |
|----|--------|-----------|
| A1 | `hit_at_k` | at least one gold document id is retrieved |
| A2 | `recall_at_k` | retrieved ∩ gold meets `recall_at_k_min` |
| A3 | `mrr` | informational unless `mrr_min > 0` |
| A4 | `precision_at_k` | informational unless `precision_at_k_min > 0` |
| A5 | `must_mention` | every required substring appears in the answer |
| A6 | `forbidden` | no forbidden substring appears in the answer |
| A7 | `citation_support` | every cited id was actually retrieved |

Invariants:

1. Metric functions are pure. Identical retrieved ids, gold ids, answer text,
   and `EvalConfig` produce identical PASS/FAIL.
2. No LLM-as-judge. Generation is an adapter input, not a scoring model.
3. Latency and live-provider variance are Layer B and never flip the suite
   verdict.
4. Retriever and LLM adapters are protocols. CI uses `MockRetriever` plus
   `MockLLM` over the toy transit corpus so no API keys are required.

A suite PASSes only when every case PASSes every gating metric. `compare`
diffs two reports by case id. `bisect` binary-searches an ordered list of
config snapshots and reports the first snapshot that fails Layer A.

## Consequences

Positive: CI is hermetic, cheap, and bisectable. A retrieval regression has a
named snapshot rather than a vibe.

Negative: Layer A will not catch fluent-but-wrong answers that still retrieve
the gold document and mention the required tokens. That is deferred to an
optional Layer B behind an explicit flag, not this MVP.
