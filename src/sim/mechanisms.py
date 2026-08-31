"""Adapter: a verified mechanism -> a per-round FedAvg reward hook.

Reuses the exact AST->SymPy->lambdify path that src/architect/mc.py uses, so the
sim scores payments with the same expression semantics the verifier saw. The
adapter is READ-ONLY over the mechanism (spec: "The sim never proposes or repairs
a mechanism").
"""
from __future__ import annotations

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


def _symbol_env(report: ClientReport, ctx: RoundContext, n_reports: int) -> dict:
    return {"q": report.claimed_quality, "v": report.claimed_quality,
            "e": _effort_proxy(report), "B": ctx.budget, "n": float(n_reports)}


def _renormalise(raw: dict[int, float], budget: float) -> dict[int, float]:
    clamped = {cid: max(0.0, float(p)) for cid, p in raw.items()}
    total = sum(clamped.values())
    if total > budget > 0:
        f = budget / total
        return {cid: p * f for cid, p in clamped.items()}
    return clamped


def _rhs_expr(latex_or_ast):
    if isinstance(latex_or_ast, str):
        s = latex_or_ast.split("=", 1)[-1]
        s = s.replace("_i", "").replace("_j", "").replace("\\", "")
        s = s.replace("{", "(").replace("}", ")")
        env = {k: sympy.Symbol(k) for k in ("q", "e", "B", "n", "v")}
        return sympy.sympify(s, locals=env)
    if ast_to_sympy is not None:
        return ast_to_sympy(latex_or_ast)
    raise TypeError(f"cannot build expr from {type(latex_or_ast)!r}")


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
        latex = (mechanism.get("payment_rule_latex")
                 or mechanism.get("ir_participation_latex")
                 or mechanism.get("client_utility_latex"))
        if latex is None:
            raise KeyError("mechanism_dict has no payment/utility latex field")
        return _hook_from_expr(_rhs_expr(latex), budget)

    raise TypeError(f"unsupported mechanism type {type(mechanism)!r}")


# ponytail: the latex-string branch does crude cleanup (strip _i, braces) for
# hand-written fixtures. Real generated mechanisms should be passed as a
# Mechanism AST (run.py loads them that way), which uses ast_to_sympy directly.
