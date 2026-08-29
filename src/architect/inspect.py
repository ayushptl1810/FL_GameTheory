from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from verifier import verify
from architect.serialize import render
from architect.ast import Mechanism
from architect.ast_verify import verify_from_ast


def inspect_mechanism(m: Mechanism, meta: dict):
    """Render a Mechanism AST and run Stage 1's verify() on it.

    With ARCHITECT_AST_VERIFY=1, dispatch to the AST-native verifier instead.
    loop.py::_finish renders mechanism_latex from render(m) independently, so
    the flagged branch needs no render call.
    """
    if os.environ.get("ARCHITECT_AST_VERIFY") == "1":
        return verify_from_ast(m, meta)
    mechanism_dict, _ = render(m)
    entry = {
        "paper_id": meta.get("paper_id", "architect-proposal"),
        "num_clients": meta.get("num_clients", len(m.type_space) or 2),
        "quality_tier": meta.get("quality_tier", "silver"),
        **{k: v for k, v in meta.items() if k not in {"category", "mechanism"}},
        "category": m.category,
        "mechanism": mechanism_dict,
    }
    return verify(entry)


def is_loop_success(r) -> bool:
    """The CEGIS loop terminates only on an entry-specific VERIFIED verdict."""
    return getattr(r, "verdict", None) == "VERIFIED" and getattr(r, "entry_specific", False) is True
