"""Mock retriever and LLM adapter tests."""

from __future__ import annotations

from rag_eval_bisect.adapters import MockLLM, MockRetriever, tokenize
from rag_eval_bisect.models import CorpusDoc, EvalConfig


def test_tokenize_is_lowercase_alnum():
    assert tokenize("Night-Owl 12:30!") == {"night", "owl", "12", "30"}


def test_keyword_retriever_ranks_gold_first():
    corpus = [
        CorpusDoc(id="noise", title="Misc", text="unrelated municipal memo"),
        CorpusDoc(id="night-owl", title="After-Hours Fleet", text="The night owl bus runs late."),
    ]
    chunks = MockRetriever(corpus).retrieve(
        "What time does the night owl bus run?",
        EvalConfig(top_k=2, score_mode="keyword"),
    )
    assert chunks[0].doc_id == "night-owl"
    assert chunks[0].score >= chunks[-1].score


def test_title_only_mode_ignores_body_terms():
    corpus = [
        CorpusDoc(id="night-owl", title="After-Hours Fleet", text="The night owl bus runs late."),
        CorpusDoc(id="alerts", title="Night Notices", text="website boards"),
    ]
    chunks = MockRetriever(corpus).retrieve(
        "What time does the night owl bus run?",
        EvalConfig(top_k=1, score_mode="title_only"),
    )
    assert [chunk.doc_id for chunk in chunks] == ["alerts"]


def test_mock_llm_cites_retrieved_ids_only():
    chunks = MockRetriever(
        [CorpusDoc(id="fare-policy", title="Payment Windows", text="A single fare includes one transfer.")]
    ).retrieve("How do transfers work with one fare?", EvalConfig(top_k=1))
    answer = MockLLM().generate("How do transfers work with one fare?", chunks)
    assert answer.citations == ["fare-policy"]
    assert "transfer" in answer.text
