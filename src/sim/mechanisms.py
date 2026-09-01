"""Adapter: a verified mechanism -> a per-round FedAvg reward hook.

Reuses the exact AST->SymPy->lambdify path that src/architect/mc.py uses, so the
sim scores payments with the same expression semantics the verifier saw. The
adapter is READ-ONLY over the mechanism (spec: "The sim never proposes or repairs
a mechanism").
"""
from __future__ import annotations

import re
import warnings

import numpy as np
import sympy

from sim.fedavg import ClientReport, RoundContext

try:
    from architect.serialize import ast_to_sympy
    from architect.ast import Mechanism
except Exception:  # pragma: no cover
    ast_to_sympy = None
    Mechanism = ()  # isinstance-safe


def zero_reward_hook(reports, ctx):
    return {}


def _effort_proxy(report: ClientReport) -> float:
    return float(np.linalg.norm(report.delta_params))


# Symbols the sim can bind from a per-round client report. A Contract mechanism
# also mentions ``theta`` (the client's private cost type): the server never sees
# it, so the sim binds the type the CLAIM implies -- a higher claimed quality
# reads as a lower-cost (cheaper to reward) type.
_KNOWN_SYMBOLS = ("q", "v", "e", "B", "n", "theta")


def _symbol_env(report: ClientReport, ctx: RoundContext, n_reports: int) -> dict:
    q = float(report.claimed_quality)
    return {"q": q, "v": q, "e": _effort_proxy(report), "B": ctx.budget,
            "n": float(n_reports), "theta": 1.0 / max(q, 0.1)}


def _renormalise(raw: dict[int, float], budget: float) -> dict[int, float]:
    clamped = {cid: max(0.0, float(p)) for cid, p in raw.items()}
    total = sum(clamped.values())
    if total > budget > 0:
        f = budget / total
        return {cid: p * f for cid, p in clamped.items()}
    return clamped


_GEQ_SPLIT = re.compile(r"\\geq|\\leq|\\ge|\\le|<|>")
_SUB_BRACE = re.compile(r"_\{[^}]*\}")
_SUB_BARE = re.compile(r"_[A-Za-z0-9]+")
_SUP_BRACE = re.compile(r"\^\{([^}]*)\}")
_SUP_BARE = re.compile(r"\^([0-9A-Za-z]+)")
_FRAC = re.compile(r"\\frac\{([^}]*)\}\{([^}]*)\}")
_MACRO = re.compile(r"\\([A-Za-z]+)")
_IMPLICIT_1 = re.compile(r"([0-9A-Za-z\)])\s+([A-Za-z\(])")
_IMPLICIT_2 = re.compile(r"(\))\s*(\()")


def _latex_to_sympy_str(latex: str) -> str:
    """Best-effort LaTeX -> sympy-parseable string for generated / hand-written
    mechanism fields. Handles the small vocabulary these fields use: an ``=`` or
    ``\\geq 0`` split, ``_{i}`` / ``_i`` subscripts, ``^{2}`` superscripts, a
    ``\\frac``, Greek macros, and implicit multiplication."""
    s = _GEQ_SPLIT.split(latex)[0]              # keep the LHS of an inequality
    if "=" in s:
        s = s.split("=", 1)[1]                  # RHS of an assignment
    s = s.replace("\\left", "").replace("\\right", "")
    s = _FRAC.sub(r"((\1)/(\2))", s)
    s = _SUB_BRACE.sub("", s)                   # drop {..} subscripts
    s = _SUB_BARE.sub("", s)                    # drop bare subscripts
    s = _SUP_BRACE.sub(r"**(\1)", s)            # ^{..} -> **(..)
    s = _SUP_BARE.sub(r"**\1", s)               # ^2    -> **2
    s = _MACRO.sub(r"\1", s)                    # \theta -> theta
    s = s.replace("{", "(").replace("}", ")")
    for _ in range(3):                          # implicit multiplication
        s = _IMPLICIT_1.sub(r"\1*\2", s)
        s = _IMPLICIT_2.sub(r"\1*\2", s)
    return s.strip()


def _rhs_expr(latex_or_ast):
    if isinstance(latex_or_ast, str):
        env = {k: sympy.Symbol(k) for k in _KNOWN_SYMBOLS}
        return sympy.sympify(_latex_to_sympy_str(latex_or_ast), locals=env)
    if ast_to_sympy is not None:
        return ast_to_sympy(latex_or_ast)
    raise TypeError(f"cannot build expr from {type(latex_or_ast)!r}")


def _payment_from_utility(util_expr):
    """U_i(reward, signals) -> reward(signals) at the IR-binding point (U_i = 0).

    The reward variable is whichever free symbol is not in ``_KNOWN_SYMBOLS``
    (e.g. ``R`` / ``w`` / ``p``). If there is not exactly one, or it cannot be
    solved for, fall back to the utility expression unchanged. Reading the
    payment off the verified IR constraint is not mechanism design -- it is the
    deployment point the certificate already pins down.
    """
    unknown = [x for x in util_expr.free_symbols if str(x) not in _KNOWN_SYMBOLS]
    if len(unknown) != 1:
        return util_expr
    sol = sympy.solve(sympy.Eq(util_expr, 0), unknown[0])
    return sol[0] if sol else util_expr


def _hook_from_expr(expr, budget: float):
    syms = sorted(expr.free_symbols, key=str)
    f = sympy.lambdify([sympy.Symbol(str(s)) for s in syms], expr, "numpy")
    warned = {"done": False}

    def hook(reports, ctx):
        raw = {}
        for rep in reports:
            env = _symbol_env(rep, ctx, len(reports))
            missing = [str(s) for s in syms if str(s) not in env]
            if missing and not warned["done"]:
                warnings.warn(f"mechanism expr has unbound symbols {missing}; treating as 0")
                warned["done"] = True
            raw[rep.client_id] = float(f(*[env.get(str(s), 0.0) for s in syms]))
        return _renormalise(raw, budget)

    return hook


def build_reward_hook(mechanism, setting: str, *, budget: float):
    if callable(mechanism) and not (Mechanism and isinstance(mechanism, Mechanism)):
        def hook(reports, ctx, _inner=mechanism):
            return _renormalise(dict(_inner(reports, ctx)), budget)
        return hook

    if Mechanism and isinstance(mechanism, Mechanism):
        node = getattr(mechanism, "payment", None) or getattr(mechanism, "utility")
        return _hook_from_expr(_rhs_expr(node), budget)

    if isinstance(mechanism, dict):
        if mechanism.get("payment_rule_latex"):
            return _hook_from_expr(_rhs_expr(mechanism["payment_rule_latex"]), budget)
        if mechanism.get("client_utility_latex"):
            util = _rhs_expr(mechanism["client_utility_latex"])
            return _hook_from_expr(_payment_from_utility(util), budget)
        if mechanism.get("ir_participation_latex"):
            return _hook_from_expr(_rhs_expr(mechanism["ir_participation_latex"]), budget)
        raise KeyError("mechanism_dict has no payment/utility latex field")

    raise TypeError(f"unsupported mechanism type {type(mechanism)!r}")


# ponytail: the latex-string branch does crude cleanup (subscripts, \frac, Greek,
# implicit multiplication) for hand-written and LLM-generated fixtures. Passing a
# Mechanism AST instead uses architect.serialize.ast_to_sympy directly and skips
# all of this.
