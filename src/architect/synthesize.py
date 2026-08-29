from __future__ import annotations
from dataclasses import dataclass, field
import z3, sympy
from architect.ast import Const, Sym, Unknown, Sum, Prod, Pow, Func, Mechanism
from architect.serialize import ast_to_sympy


@dataclass
class Constraints:
    ic: object
    ir: object
    budget_lhs: object | None
    budget_rhs: float | None
    type_space: list
    param_bounds: dict = field(default_factory=dict)


def collect_unknowns(node) -> list:
    if isinstance(node, Unknown):
        return [node.name]
    if isinstance(node, Sum):
        return [n for t in node.terms for n in collect_unknowns(t)]
    if isinstance(node, Prod):
        return [n for f in node.factors for n in collect_unknowns(f)]
    if isinstance(node, Pow):
        return collect_unknowns(node.base)
    if isinstance(node, Func):
        return collect_unknowns(node.arg)
    return []


def _sympy_to_z3(expr, zvars):
    if expr.is_Number:
        return z3.RealVal(str(sympy.Rational(expr)))
    if expr.is_Symbol:
        return zvars.setdefault(expr.name, z3.Real(expr.name))
    if expr.is_Add:
        return z3.Sum([_sympy_to_z3(a, zvars) for a in expr.args])
    if expr.is_Mul:
        out = z3.RealVal(1)
        for a in expr.args:
            out = out * _sympy_to_z3(a, zvars)
        return out
    if expr.is_Pow:
        base = _sympy_to_z3(expr.base, zvars)
        if not (getattr(expr.exp, "is_Integer", False) or float(expr.exp).is_integer()):
            raise ValueError(f"cannot translate non-integer exponent {expr.exp!r} to z3 (fragment limit)")
        e = int(expr.exp)
        out = z3.RealVal(1)
        for _ in range(abs(e)):
            out = out * base
        return out if e >= 0 else 1 / out
    raise ValueError(f"cannot translate {expr!r} to z3 (fragment limit)")


def _unknowns_to_syms(node):
    """Rewrite every Unknown to a plain Sym of the same name. Used for
    Stackelberg, where a model that over-marks Unknown (e.g. tagging the
    leader's price) really just meant 'symbol' -- keeping the structure and
    letting verify() derive the follower FOC is far better than picking values."""
    if isinstance(node, Unknown):
        return Sym(node.name)
    if isinstance(node, Sum):
        return Sum([_unknowns_to_syms(t) for t in node.terms])
    if isinstance(node, Prod):
        return Prod([_unknowns_to_syms(f) for f in node.factors])
    if isinstance(node, Pow):
        return Pow(_unknowns_to_syms(node.base), node.exp)
    if isinstance(node, Func):
        return Func(node.name, _unknowns_to_syms(node.arg))
    return node


def _substitute_unknowns(node, model: dict):
    if isinstance(node, Unknown):
        if node.name not in model:
            raise ValueError(f"Unknown '{node.name}' has no solved value")
        return Const(model[node.name])
    if isinstance(node, Sum):
        return Sum([_substitute_unknowns(t, model) for t in node.terms])
    if isinstance(node, Prod):
        return Prod([_substitute_unknowns(f, model) for f in node.factors])
    if isinstance(node, Pow):
        return Pow(_substitute_unknowns(node.base, model), node.exp)
    if isinstance(node, Func):
        return Func(node.name, _substitute_unknowns(node.arg, model))
    return node


def _all_unknowns(m: Mechanism) -> list:
    """Every distinct Unknown name across the mechanism, not just the payment
    subtree -- models routinely put free coefficients in ic/ir/utility too, and
    each one needs a solved value before _substitute_unknowns runs."""
    seen, out = set(), []
    for sub in (m.payment, m.utility, m.ic, m.ir):
        for n in collect_unknowns(sub):
            if n not in seen:
                seen.add(n)
                out.append(n)
    return out


def synthesize(m: Mechanism, c: Constraints):
    unknowns = _all_unknowns(m)
    if not unknowns:
        return m  # fully concrete already -- nothing to solve, let verify() run
    if len(unknowns) > 5:
        return "UNSAT"
    if m.category == "Stackelberg":
        # Synthesis mode's ForAll(ic>=0, ir>=0) solve does not fit Stackelberg
        # (no screening IC; m.ic holds an FOC). Models routinely over-mark
        # Unknown here -- tagging the leader's price or the cost coefficient --
        # so demote every Unknown back to a plain Sym and let verify() derive
        # the follower FOC and check IR at the optimum. That keeps the structure
        # intact instead of picking arbitrary values.
        return Mechanism(
            m.category,
            utility=_unknowns_to_syms(m.utility),
            payment=_unknowns_to_syms(m.payment),
            ic=_unknowns_to_syms(m.ic),
            ir=_unknowns_to_syms(m.ir),
            params=dict(m.params), type_space=m.type_space,
            provenance=m.provenance, meta=dict(m.meta))
    zvars: dict = {}
    for u in unknowns:
        zvars[u] = z3.Real(u)
    for t in c.type_space:
        zvars[t] = z3.Real(t)
    solver = z3.Solver()
    for u in unknowns:
        lo, hi = c.param_bounds.get(u, (-10.0, 10.0))
        solver.add(zvars[u] >= lo, zvars[u] <= hi)

    def _z3(node):
        return _sympy_to_z3(sympy.expand(ast_to_sympy(node)), zvars)

    body = z3.And(_z3(c.ic) >= 0, _z3(c.ir) >= 0)
    if c.budget_lhs is not None and c.budget_rhs is not None:
        body = z3.And(body, _z3(c.budget_lhs) <= c.budget_rhs)
    type_syms = [zvars[t] for t in c.type_space]
    if type_syms:
        dom = z3.And(*[z3.And(s >= z3.RealVal("1/10"), s <= 1) for s in type_syms])
        solver.add(z3.ForAll(type_syms, z3.Implies(dom, body)))
    else:
        solver.add(body)

    if solver.check() != z3.sat:
        return "UNSAT"
    mdl = solver.model()
    vals = {}
    for u in unknowns:
        r = mdl[zvars[u]]
        vals[u] = float(sympy.Rational(str(r))) if r is not None else 0.0
    return Mechanism(m.category,
                     utility=_substitute_unknowns(m.utility, vals),
                     payment=_substitute_unknowns(m.payment, vals),
                     ic=_substitute_unknowns(m.ic, vals),
                     ir=_substitute_unknowns(m.ir, vals),
                     params={**m.params, **vals}, type_space=m.type_space,
                     provenance=m.provenance)
