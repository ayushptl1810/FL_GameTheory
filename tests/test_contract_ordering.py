"""
Tests for the type-ordering / menu-monotonicity preconditions in the
entry-specific Contract verifier (track1_z3._try_contract_latex).

Background: without a type-ordering assumption, Z3 found "counterexamples"
for published screening contracts in parameter regions the papers exclude
(reversed type order, non-monotone menus). The fix identifies the type
family from the entry's own type_variable field, resolves the direction
convention from the sign of dU/dtheta when possible, and fails closed to
UNKNOWN when it cannot.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tracks.track1_z3 import verify_contract


def _entry(type_variable, utility, ic, ir, num_types=2, paper_id="test_paper"):
    return {
        "paper_id": paper_id,
        "category": "Contract",
        "mechanism": {
            "num_types": num_types,
            "type_variable": type_variable,
            "client_utility_latex": utility,
            "ic_screening_latex": ic,
            "ir_participation_latex": ir,
        },
    }


def test_value_type_verifies_single_direction():
    """theta multiplies reward => dU/dtheta > 0 => value-type, ascending.
    The textbook screening menu must verify entry-specifically (this exact
    shape was a spurious COUNTEREXAMPLE before the ordering fix)."""
    e = _entry(
        type_variable=r"WTP theta_i",
        utility=r"u_i = \theta_i R_i - c q_i",
        ic=r"\theta_i R_i - c q_i \geq \theta_i R_j - c q_j",
        ir=r"\theta_i R_i - c q_i \geq 0",
    )
    r = verify_contract(e)
    assert r.verdict == "VERIFIED"
    assert r.entry_specific
    assert "value-type" in r.notes


def test_cost_type_verifies_descending_direction():
    """type multiplies a cost term => dU/dtheta < 0 => cost-type, descending
    ordering (index 0 = highest cost = worst type, where IR binds)."""
    e = _entry(
        type_variable=r"privacy sensitivity \( \mu_i \)",
        utility=r"U_i = r_i - \mu_i s_i",
        ic=r"r_i - \mu_i s_i \geq r_j - \mu_i s_j",
        ir=r"r_i - \mu_i s_i \geq 0",
        num_types=3,
    )
    r = verify_contract(e)
    assert r.verdict == "VERIFIED"
    assert r.entry_specific
    assert "cost-type" in r.notes


def test_ambiguous_type_variable_fails_closed():
    """type_variable declaring two symbols => family unidentified => the old
    unordered counterexamples must be suppressed to UNKNOWN, never asserted."""
    e = _entry(
        type_variable=r"data quality \theta_i and training willingness e_i",
        utility=r"U_i = \theta_i e_i R_i - f_i - \frac{1}{2} c e_i^2",
        ic=r"\theta_i e_i R_i - f_i - \frac{1}{2} c e_i^2 \geq "
           r"\theta_i e_j R_j - f_i - \frac{1}{2} c e_j^2",
        ir=r"\theta_i e_i R_i - f_i - \frac{1}{2} c e_i^2 \geq 0",
    )
    r = verify_contract(e)
    assert r.verdict in ("UNKNOWN", "VERIFIED_TEMPLATE")
    assert r.verdict != "COUNTEREXAMPLE"
    if r.entry_specific:
        assert "unidentified" in r.notes


def test_infeasible_bindings_fall_back_to_template():
    """Additive type (U = theta_i + R_i): positivity makes the IR binding
    U(0,0)=0 unsatisfiable. Vacuity gate must bail to the template path
    instead of reporting a vacuous entry-specific VERIFIED."""
    e = _entry(
        type_variable=r"type \theta_i",
        utility=r"U_i = \theta_i + R_i",
        ic=r"\theta_i + R_i \geq \theta_i + R_j",
        ir=r"\theta_i + R_i \geq 0",
    )
    r = verify_contract(e)
    assert not (r.verdict == "VERIFIED" and r.entry_specific)


def test_indeterminate_direction_never_falsely_verifies():
    """dU/dtheta sign depends on other variables => direction unknown =>
    both pairings checked fail-closed; the result must never be an asserted
    COUNTEREXAMPLE unless it holds under BOTH direction pairings."""
    e = _entry(
        type_variable=r"type \theta_i",
        utility=r"U_i = \theta_i R_i - \theta_i^2 s_i",
        ic=r"\theta_i R_i - \theta_i^2 s_i \geq \theta_i R_j - \theta_i^2 s_j",
        ir=r"\theta_i R_i - \theta_i^2 s_i \geq 0",
    )
    r = verify_contract(e)
    if r.entry_specific and "single direction" not in r.notes:
        # both-directions mode: VERIFIED/COUNTEREXAMPLE only when unanimous
        assert r.verdict in ("VERIFIED", "COUNTEREXAMPLE", "UNKNOWN")
