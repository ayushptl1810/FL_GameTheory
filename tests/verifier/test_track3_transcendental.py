"""Task 14 — Track 3 multivariable transcendental Contract IC.

Covers the widened interval box search for the `R_i * ln(1/theta_i)` menu
shape over INDEPENDENT type / reward boxes:

  * a synthetic multi-type gap that is δ-IC on the box            -> VERIFIED
  * a genuine single-symbol IC violation beyond δ                 -> COUNTEREXAMPLE
  * a multi-symbol adversarial-values "counterexample"            -> UNKNOWN
    (menu/type symbols are structural, not free params), and the verdict
    still carries an honest δ-bounded IC-regret number.
"""
import sys
from pathlib import Path

import sympy as sp

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tracks.track3_dreal import (  # noqa: E402
    _DELTA,
    check_nonneg_box,
    max_ic_regret_over_box,
    track3_check_from_sympy,
)


def _bounds(*triples):
    return [(sp.Symbol(n), lo, hi) for n, lo, hi in triples]


# ── the widened box search ──────────────────────────────────────────────────

def test_multitype_log_gap_is_delta_ic_over_independent_boxes():
    # gap(a, b, t) = a * ln(1/t) + b  with a,b > 0 and t in (0,1]  =>  ln(1/t) >= 0
    # so gap >= 0 everywhere: the R_i*ln(1/theta_i) shape with an IR slack term,
    # over independent reward (a, b) and type (t) boxes.
    a, b, t = sp.symbols("a b t")
    gap = a * sp.log(1 / t) + b
    bnds = _bounds(("a", 0.001, 10.0), ("b", 0.001, 10.0), ("t", 0.001, 1.0))
    res = track3_check_from_sympy(
        gap, gap, bnds, list(bnds), _DELTA,
        entry_specific=True, paper_id="synthetic_log_ic",
        theta_min=0.001, theta_max=1.0,
    )
    assert res.verdict == "VERIFIED"
    assert res.track == 3


def test_single_symbol_genuine_violation_is_counterexample():
    # ln(1/t) - 5 < 0 for t in (0.3, 1]: one free symbol, a real violation.
    t = sp.Symbol("t")
    status, witness = check_nonneg_box(sp.log(1 / t) - 5, [(t, 0.3, 1.0)])
    assert status == "counterexample"
    assert witness is not None and "t" in witness


def test_multisymbol_adversarial_values_suppressed_to_unknown_with_regret():
    # (R_i - R_j) * ln(1/t) - (e_i^2 - e_j^2): a box "counterexample" only
    # exists because R_i, R_j, e_i, e_j are picked adversarially and
    # independently -- in the real menu they are pinned. Must be UNKNOWN,
    # never COUNTEREXAMPLE, and the notes must carry the honest δ-regret.
    R_i, R_j, t, e_i, e_j = sp.symbols("R_i R_j t e_i e_j")
    gap = (R_i - R_j) * sp.log(1 / t) - (e_i**2 - e_j**2)
    bnds = _bounds(
        ("R_i", 0.001, 5.0), ("R_j", 0.001, 5.0), ("t", 0.001, 1.0),
        ("e_i", 0.001, 3.0), ("e_j", 0.001, 3.0),
    )
    res = track3_check_from_sympy(
        gap, None, bnds, [], _DELTA,
        entry_specific=True, paper_id="synthetic_multisym",
        theta_min=0.001, theta_max=1.0,
    )
    assert res.verdict != "COUNTEREXAMPLE"
    assert res.verdict in ("UNKNOWN", "VERIFIED_TEMPLATE")
    assert any("suppressed" in c for c in res.conditions)
    assert any("IC-regret" in c and "δ-IC on the box" in c for c in res.conditions)


def test_max_ic_regret_zero_on_provably_nonneg_box():
    a, t = sp.symbols("a t")
    assert max_ic_regret_over_box(a * sp.log(1 / t), [(a, 0.001, 10.0), (t, 0.001, 1.0)]) == 0.0


def test_max_ic_regret_is_a_safe_upper_bound():
    # min of (R_i - R_j)*ln(1/t) - (e_i^2 - e_j^2) on the box is about
    # (-5)*ln(1000) - (0 - 9) ~= -43.5; the reported bound must be >= that.
    R_i, R_j, t, e_i, e_j = sp.symbols("R_i R_j t e_i e_j")
    gap = (R_i - R_j) * sp.log(1 / t) - (e_i**2 - e_j**2)
    bnds = _bounds(
        ("R_i", 0.001, 5.0), ("R_j", 0.001, 5.0), ("t", 0.001, 1.0),
        ("e_i", 0.001, 3.0), ("e_j", 0.001, 3.0),
    )
    reg = max_ic_regret_over_box(gap, bnds)
    assert reg is not None and reg >= 43.0


# ── Architect prompt: emits Func{ln} for log settings ───────────────────────

def test_architect_prompt_has_transcendental_branch():
    from architect.architect import RETRIEVAL_PROMPT

    assert '"t":"Func","name":"ln"' in RETRIEVAL_PROMPT
    assert "do NOT linearise" in RETRIEVAL_PROMPT


def test_verify_from_ast_routes_func_ln_contract_to_track3():
    # A Contract mechanism whose utility carries a real Func("ln") node reaches
    # the Track 3 seam via _classify_ast, not the linear-menu path.
    from architect.ast import Const, Sym, Prod, Pow, Sum, Func, Mechanism
    from architect.ast_verify import _classify_ast

    util = Sum([
        Prod([Sym("R_i"), Func("ln", Pow(Sym("theta_i"), -1))]),
        Prod([Const(-1), Sym("k"), Sym("R_i")]),
    ])
    m = Mechanism(
        category="Contract", utility=util, payment=Sym("R_i"),
        ic=Sum([util, Prod([Const(-1), util])]), ir=util,
        type_space=[0.1, 0.9], meta={"num_types": 2},
    )
    assert _classify_ast(m) == 3
