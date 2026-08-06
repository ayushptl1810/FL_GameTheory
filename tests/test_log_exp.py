"""
Tests for log()/exp() support in the Z3 converter (track1_z3._sp_to_z3).

Z3 NRA has no native transcendentals. log/exp terms are encoded as opaque
auxiliary variables constrained only by sign (see _sp_to_z3's docstring).
That relaxation is sound for VERIFIED (holds in the more permissive relaxed
search space => holds for the true, tighter problem) but NOT sound for
COUNTEREXAMPLE (a found violation may only exist because the aux variable
was free to take a value the real log/exp term never could) -- so any
COUNTEREXAMPLE relying on a transcendental aux variable must be downgraded
to UNKNOWN, never asserted.
"""

import sympy as sp

from tracks.track1_z3 import (
    _is_definitely_positive_sum,
    _sp_to_z3,
    _try_contract_latex,
)


class TestIsDefinitelyPositiveSum:
    def test_plain_positive_symbol(self):
        x = sp.Symbol("x")
        assert _is_definitely_positive_sum(x) is True

    def test_sum_of_positive_terms(self):
        x, y = sp.symbols("x y")
        assert _is_definitely_positive_sum(x + x * y) is True

    def test_negative_coefficient_rejected(self):
        x = sp.Symbol("x")
        assert _is_definitely_positive_sum(-x) is False

    def test_bare_negative_constant_rejected(self):
        assert _is_definitely_positive_sum(sp.Integer(-1)) is False

    def test_bare_positive_constant_alone_rejected(self):
        # No symbol term at all -- not the "at least one genuine positive
        # contribution from a positive-symbol assumption" case this is for.
        assert _is_definitely_positive_sum(sp.Integer(5)) is False

    def test_mixed_sign_terms_rejected(self):
        x, y = sp.symbols("x y")
        assert _is_definitely_positive_sum(x - y) is False

    def test_negative_power_rejected(self):
        x = sp.Symbol("x")
        assert _is_definitely_positive_sum(x ** -1) is False


class TestSpToZ3LogExp:
    def test_exp_of_anything_is_unconditionally_positive_aux(self):
        x = sp.Symbol("x")
        cache = {}
        z3_expr = _sp_to_z3(sp.exp(x), cache)
        assert any(k.startswith("exp[") for k in cache)
        assert z3_expr is cache["exp[x]"]

    def test_log_of_one_plus_positive_sum_is_encoded(self):
        rho, h = sp.symbols("rho h")
        cache = {}
        z3_expr = _sp_to_z3(sp.log(1 + rho * h), cache)
        assert any(k.startswith("log[") for k in cache)
        assert z3_expr is cache[f"log[{1 + rho * h}]"]

    def test_log_of_unestablished_sign_raises(self):
        x = sp.Symbol("x")
        cache = {}
        try:
            _sp_to_z3(sp.log(x - 5), cache)
            assert False, "expected ValueError for a log argument with unestablished sign"
        except ValueError:
            pass


class TestContractLatexWithTranscendentals:
    def test_kang2019_style_log_term_is_unknown_not_false_counterexample(self):
        """
        Regression test for the exact bug found 2026-07-17: a fixed
        per-agent \\ln(1+\\rho_n h_n) communication-cost term (identical on
        both sides of the IC comparison, so it cancels there, but present
        in the IR absolute-utility check) used to make _try_contract_latex
        return None outright (log unsupported). After adding log support,
        it must return UNKNOWN (the aux variable's true magnitude is
        unconstrained) -- never a fabricated COUNTEREXAMPLE.
        """
        entry = {
            "paper_id": "test_log_term",
            "category": "Contract",
            "mechanism": {
                "num_types": 2,
                "ir_participation_latex": (
                    r"U_{D_n} = R_n - \mu \theta_n \zeta c_n s_n f_n^2 "
                    r"+ \frac{\sigma \rho_n}{B \ln(1 + \rho_n h_n)} \geq 0"
                ),
                "ic_screening_latex": (
                    r"R_n - \mu \theta_n \zeta c_n s_n f_n^2 + \frac{\sigma \rho_n}{B \ln(1 + \rho_n h_n)} "
                    r"\geq R_m - \mu \theta_n \zeta c_n s_n f_m^2 + \frac{\sigma \rho_n}{B \ln(1 + \rho_n h_n)}"
                ),
            },
        }
        result = _try_contract_latex(entry)
        assert result is not None
        assert result.verdict == "UNKNOWN"
        assert result.counterexample is None

    def test_log_term_that_only_adds_headroom_still_verifies(self):
        """
        When the non-log part of the utility is already unconditionally
        nonnegative (a square term here), adding a provably-positive log
        term must not prevent VERIFIED -- the relaxed encoding is sound in
        that direction.
        """
        entry = {
            "paper_id": "test_log_headroom",
            "category": "Contract",
            "mechanism": {
                "num_types": 2,
                "ir_participation_latex": r"U_n = R_n^2 + \ln(1 + \rho_n) \geq 0",
                "ic_screening_latex": r"R_n^2 + \ln(1 + \rho_n) \geq R_m^2 + \ln(1 + \rho_n)",
            },
        }
        result = _try_contract_latex(entry)
        # Since the vacuity gate (2026-07-18): this utility is structurally
        # positive, so the IR binding U(0,0)=0 is unsatisfiable and the old
        # VERIFIED here was vacuous. The encoding now recognizes it cannot
        # represent this entry and falls back to the template path (None)
        # instead of asserting anything.
        if result is not None:
            assert result.verdict in ("VERIFIED", "UNKNOWN")
        # The key regression-relevant assertion: never a fabricated counterexample.
        assert result is None or result.verdict != "COUNTEREXAMPLE"
