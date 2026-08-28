from __future__ import annotations
from architect.llm import llm_complete
from architect.rag import nearest_distance
from architect.types import ProblemSpec

ROUTER_SYSTEM_PROMPT = (
    "Answer strictly 'yes' or 'no'. You are told an FL incentive setup and a "
    "candidate corpus paper title. Answer 'yes' only if that paper's mechanism "
    "family is a close structural match for the setup."
)
_HYBRID_PROMPT = (
    "Answer strictly 'yes' or 'no'. Does this FL incentive setup require "
    "combining two different mechanism families (e.g. auction allocation with "
    "contract-style payments) to be solved well?"
)


def _yes(text: str) -> bool:
    return text.strip().lower().startswith("y")


def route(spec: ProblemSpec, index, *, tau_retrieval: float = 0.15,
          complete=llm_complete):
    if nearest_distance(spec, index) < tau_retrieval:
        title = index.entries[0].get("title", "")
        if _yes(complete(ROUTER_SYSTEM_PROMPT, f"Setup: {spec.raw_text}\nPaper: {title}")):
            return "Retrieval"
    if len(spec.failure_modes) >= 2:
        return "Hybrid"
    if _yes(complete(_HYBRID_PROMPT, spec.raw_text)):
        return "Hybrid"
    return "Synthesis"
