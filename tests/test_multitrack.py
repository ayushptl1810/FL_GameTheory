"""
Tests for the three track paths added 2026-07-19 to make the multi-track
architecture genuinely load-bearing:

- Track 3: multi-dimensional interval branch-and-bound (check_nonneg_box)
  and its use as the rigorous replacement for the old sampling-based
  Stackelberg IR fallback.
- Track 2: parametric positivity certificates for symbolic discrete-type
  screening contracts (ordered-increment coordinates + binding solve +
  posynomial decomposition).
- Track 4: discrete-prior Bayesian IC under paper-declared assumptions.
"""
import sys
from pathlib import Path

import sympy as sp

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tracks.track2_sos import _parametric_contract_certificate, verify_track2
from tracks.track3_dreal import check_nonneg_box
from tracks.track4_sympy import _check_discrete_bayesian
from verifier import verify


# ── Track 3: multi-dim interval engine ───────────────────────────────────────

def test_box_verifies_positive_expression():
    x, y = sp.symbols("x y")
    status, witness = check_nonneg_box(x**2 + y + 1, [(x, 0.001, 10), (y, 0.001, 10)])
    assert status == "verified"
    assert witness is None


def test_box_finds_violation_with_witness():
    x = sp.Symbol("x")
    status, witness = check_nonneg_box(x - 2, [(x, 0.001, 1.0)])
    assert status == "counterexample"
    assert witness is not None and "x" in witness


def test_box_transcendental_verified():
    # log(1+x) >= 0 for x > 0 — the transcendental case Z3 cannot touch.
    x = sp.Symbol("x")
    status, _ = check_nonneg_box(sp.log(1 + x), [(x, 0.001, 100.0)])
    assert status == "verified"


def test_box_unknown_on_unsupported():
    x = sp.Symbol("x")
    status, _ = check_nonneg_box(sp.zeta(x), [(x, 0.001, 1.0)])
    assert status == "unknown"


# ── Track 2: parametric certificate ──────────────────────────────────────────

def _contract_entry(**over):
    e = {
        "paper_id": "test_parametric",
        "category": "Contract",
        "mechanism": {
            "num_types": 2,
            "type_variable": r"WTP theta_i",
            "client_utility_latex": r"u_i = \theta_i R_i - c q_i",
            "ic_screening_latex": r"\theta_i R_i - c q_i \geq \theta_i R_j - c q_j",
            "ir_participation_latex": r"\theta_i R_i - c q_i \geq 0",
        },
    }
    e["mechanism"].update(over)
    return e


def test_parametric_certificate_verifies_textbook_menu():
    r = _parametric_contract_certificate(_contract_entry())
    assert r is not None
    assert r.verdict == "VERIFIED"
    assert r.track == 2
    assert r.entry_specific
    assert any("posynomial" in c for c in r.conditions)


def test_parametric_certificate_ambiguous_type_bails():
    r = _parametric_contract_certificate(
        _contract_entry(type_variable=r"quality \theta_i and effort q_i"))
    assert r is None


def test_parametric_certificate_transcendental_bails():
    r = _parametric_contract_certificate(_contract_entry(
        client_utility_latex=r"u_i = \theta_i R_i - \ln(q_i)",
        ic_screening_latex=r"\theta_i R_i - \ln(q_i) \geq \theta_i R_j - \ln(q_j)",
        ir_participation_latex=r"\theta_i R_i - \ln(q_i) \geq 0",
    ))
    assert r is None


def test_dispatcher_routes_contract_to_track2():
    r = verify(_contract_entry())
    assert r.track == 2
    assert r.verdict == "VERIFIED"


# ── Track 4: discrete-prior Bayesian IC ──────────────────────────────────────

def _bayesian_entry(**over):
    e = {
        "paper_id": "test_bayes",
        "category": "Contract",
        "mechanism": {
            "ic_type": "bayesian",
            "ic_screening_latex": r"P_h \cdot R - C \geq P_m \cdot R - C",
            "ir_participation_latex": r"P_h \cdot R - C \geq 0",
            "bayesian_assumptions_latex": [r"P_h \geq P_m", r"R > \frac{C}{P_h}"],
        },
    }
    e["mechanism"].update(over)
    return e


def test_discrete_bayesian_verifies_under_assumptions():
    r = _check_discrete_bayesian(_bayesian_entry())
    assert r is not None
    assert r.verdict == "VERIFIED"
    assert r.track == 4
    assert r.entry_specific


def test_discrete_bayesian_requires_assumptions():
    r = _check_discrete_bayesian(_bayesian_entry(bayesian_assumptions_latex=[]))
    assert r is None


def test_discrete_bayesian_insufficient_assumptions_unknown_not_cex():
    # Without P_h >= P_m the IC gap (P_h - P_m)R is not certifiable —
    # must yield UNKNOWN, never a fabricated counterexample.
    r = _check_discrete_bayesian(
        _bayesian_entry(bayesian_assumptions_latex=[r"R > \frac{C}{P_h}"]))
    assert r is not None
    assert r.verdict in ("UNKNOWN", "VERIFIED_TEMPLATE")
    assert r.verdict != "COUNTEREXAMPLE"


def test_dispatcher_routes_bayesian_to_track4():
    r = verify(_bayesian_entry())
    assert r.track == 4
    assert r.verdict == "VERIFIED"


# ── Cross-track consistency ──────────────────────────────────────────────────

def test_track2_and_z3_agree_on_textbook_menu():
    """Track 2's certificate and Track 1's Z3 proof are independent methods;
    both must verify the same textbook screening menu."""
    from tracks.track1_z3 import verify_contract
    e = _contract_entry()
    r1 = verify_contract(e)
    r2 = _parametric_contract_certificate(e)
    assert r1.verdict == "VERIFIED"
    assert r2 is not None and r2.verdict == "VERIFIED"
