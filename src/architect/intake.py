from __future__ import annotations
import json
from architect.llm import llm_complete
from architect.types import ProblemSpec, FAILURE_MODES

INTAKE_SYSTEM_PROMPT = (
    "You extract a structured spec from a Federated Learning incentive problem "
    "description. Return ONLY a JSON object with keys: n_clients (int|null), "
    "cost_structure (str|null), type_model (str|null), observability (str|null), "
    "budget (number|null), failure_modes (list from: non_iid, "
    "unverifiable_quality, communication_externality, collusion). "
    "Use null when the text does not state something. Do not guess."
)

_REQUIRED = ("n_clients", "cost_structure", "type_model", "observability", "budget")


def intake(text: str, *, complete=llm_complete) -> ProblemSpec:
    raw = complete(INTAKE_SYSTEM_PROMPT, text, json_mode=True)
    data = json.loads(raw)
    fms, notes = [], []
    for fm in data.get("failure_modes") or []:
        (fms if fm in FAILURE_MODES else notes).append(fm)
    spec = ProblemSpec(
        raw_text=text,
        n_clients=data.get("n_clients"), cost_structure=data.get("cost_structure"),
        type_model=data.get("type_model"), observability=data.get("observability"),
        budget=data.get("budget"), failure_modes=fms,
        notes=("unrecognized failure_modes: " + ", ".join(notes)) if notes else "")
    spec.missing_fields = [k for k in _REQUIRED if getattr(spec, k) is None]
    return spec
