"""Task 13 -- function-call notation ``f_{sub}(arg_{sub})`` (e.g. ``c_i(P_i)``).

Investigated; no new code. SymPy's ``parse_latex`` misreads ``c_i(P_i)``
as a Function application, but the existing pipeline already recovers the
intended reading:

* ``_demote_stray_function_calls`` rewrites any residual ``AppliedUndef``
  to ``head * Mul(*args)`` -- correct coefficient, argument dependence
  kept, no spurious free symbol;
* ``_insert_implicit_multiplication`` handles the *space* form
  ``c_i (P_i)^2`` one step earlier (so ``^2`` scopes to ``P_i`` only);
* ``_strip_call_syntax`` handles clause-backed ``C_k(...)`` references.

A pre-parse string fold to an "opaque symbol" was tried and reverted: no
name round-trips through ``parse_latex`` as a single ``Symbol`` across the
subscript shapes in play (``c_i_of_P_i`` tokenizes as ``c_{i_o}*f_{P_i}``).

These are characterization pins: if the existing machinery regresses on
the no-space form, they fail.
"""

import json
from pathlib import Path

import sympy as sp
from sympy.parsing.latex import parse_latex as P

from tracks.track1_z3 import _demote_stray_function_calls as D
from verifier import verify

_CORPUS = json.loads((Path(__file__).parents[2] / "corpus.json").read_text())
_ENTRIES = _CORPUS if isinstance(_CORPUS, list) else _CORPUS.get("entries", _CORPUS)


def _entry(pid):
    return next(e for e in _ENTRIES if e.get("paper_id") == pid)


# ── no-space f_{sub}(arg): _demote_stray_function_calls gives the right expr ──

def test_nospace_funcall_demotes_to_coefficient_product():
    # q_i P_i - c_i(P_i)^2  ->  c_i is a coefficient, P_i dependence kept,
    # no spurious free symbol (the reverted fold introduced `f_{P_i}`).
    got = sp.expand(D(P(r"q_i P_i - c_i(P_i)^2")))
    Pi, ci, qi = sp.symbols("P_{i} c_{i} q_{i}")
    assert got == -(Pi**2) * ci**2 + Pi * qi
    assert got.free_symbols == {Pi, ci, qi}


def test_nospace_funcall_single_arg_demotes():
    got = sp.expand(D(P(r"a - c_i(P_i)")))
    a, Pi, ci = sp.symbols("a P_{i} c_{i}")
    assert got == a - Pi * ci
    assert got.free_symbols == {a, Pi, ci}


def test_demote_retains_argument_dependence():
    # the argument variable must survive -- differentiating w.r.t. it is
    # non-zero (this is the property the Stackelberg FOC path relies on).
    expr = D(P(r"c_i(P_i)^2"))
    Pi = sp.Symbol("P_{i}")
    assert sp.diff(sp.expand(expr), Pi) != 0


# ── space form: _insert_implicit_multiplication keeps exponent scope ──────

def test_space_form_handled_via_existing_pipeline():
    # Sarikaya's follower utility: `\kappa c_i (P_i)^2` with a space.
    # Whole clause resolves and the entry is entry-specific VERIFIED.
    from tracks.track1_z3 import _resolve_stackelberg_utility

    e = _entry("Sarikaya2019stackelberg_workers")
    ux = _resolve_stackelberg_utility(e["mechanism"]["follower_utility_latex"])
    assert ux is not None
    Pi, ci, qi, kappa = sp.symbols("P_{i} c_{i} q_{i} kappa")
    # -kappa*c_i*P_i**2 + P_i*q_i  -- c_i first power (not squared),
    # i.e. the exponent bound to P_i only.
    assert sp.expand(ux) == -kappa * ci * Pi**2 + Pi * qi


# ── corpus: the f(arg)-bearing Contract + Stackelberg entries, unchanged ──

def test_corpus_entries_with_funcall_notation_at_baseline():
    expected = {
        "Sarikaya2019stackelberg_workers": "VERIFIED",        # already entry-specific
        # R6-R7: flipped to MANUAL, second-pass reclaim attempted and failed (fail-closed)
        "1811_12082": "MANUAL",                                # blocked by \exp + set-\sum
        # R3a Task 12: diagnosed MANUAL. The IC/IR parse and pass the soundness
        # gate, but u_3(.) is never defined algebraically, so _sp_to_z3 raises
        # "unsupported SymPy node u_{3}" and no obligation is built -- the old
        # VERIFIED_TEMPLATE was the generic linear-cost skeleton, not a
        # statement about this paper's own math.
        "2102_03401": "MANUAL",                               # u_3(...) undefined
    }
    for pid, want in expected.items():
        r = verify(_entry(pid))
        v = r["verdict"] if isinstance(r, dict) else r.verdict
        assert v == want, f"{pid}: {v} != {want}"
