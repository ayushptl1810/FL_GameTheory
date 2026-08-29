from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Mode = Literal["Retrieval", "Synthesis", "Hybrid"]
FAILURE_MODES = {"non_iid", "unverifiable_quality", "communication_externality", "collusion"}

@dataclass
class ProblemSpec:
    raw_text: str
    n_clients: int | None = None
    cost_structure: str | None = None
    type_model: str | None = None
    observability: str | None = None
    budget: float | None = None
    failure_modes: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    notes: str = ""
    expected_family: str | None = None

@dataclass
class Feedback:
    kind: Literal["counterexample", "parse_hint", "reformulate", "force_family", "restart", "wrong_family"]
    counterexample: dict | None = None
    conditions: list[str] = field(default_factory=list)
    hint: str = ""

@dataclass
class ArchitectResult:
    status: Literal["VERIFIED", "FAILED"]
    mechanism_latex: str
    mechanism_dict: dict
    certificate: list[str]
    mode: str
    iterations: int
    solver_calls: int
    wall_clock: float
    transcript: list[dict]
    emitted_family: str | None = None
    family_match: bool | None = None
