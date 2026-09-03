"""
Tests for the entry-specific Stackelberg verifier (track1_z3.py).

Real corpus.json Stackelberg entries turned out to have inconsistent/
ambiguous LaTeX (multi-clause "U = R - C, R = ..., C = ..." definitions,
chained equalities, \\min/\\max-prefixed objectives, space-juxtaposition
read as function application) that the entry-specific path correctly
declines rather than guesses at -- see Task.md for the corpus-side
follow-up. These tests use hand-built, well-formed entries to prove the
FOC/IR pipeline itself is correct, and that it fails closed (falls through
to the generic VERIFIED_TEMPLATE) on the ambiguous shapes actually found
in the corpus.
"""

from tracks.track1_z3 import (
    _demote_stray_function_calls,
    _resolve_stackelberg_utility,
    verify_stackelberg,
)


def _entry(mechanism: dict, paper_id: str = "test_entry") -> dict:
    return {"paper_id": paper_id, "category": "Stackelberg", "mechanism": mechanism}


class TestVerifyStackelbergEntrySpecific:
    def test_clean_quadratic_utility_is_verified_entry_specific(self):
        entry = _entry({
            "equilibrium_existence": True,
            "follower_utility_latex": r"U_i(e, p) = p e - \frac{e^2}{2}",
            "follower_decision": r"effort level \( e \)",
        })
        result = verify_stackelberg(entry)
        assert result.entry_specific is True
        assert result.verdict == "VERIFIED"
        assert result.track == 1

    def test_ir_violation_is_counterexample_not_verified(self):
        # Same optimum (e* = p), but a fixed cost large enough that IR
        # fails for small p -- U* = p^2/2 - 10 < 0 near p -> 0.
        entry = _entry({
            "equilibrium_existence": True,
            "follower_utility_latex": r"U_i(e, p) = p e - \frac{e^2}{2} - 10",
            "follower_decision": r"effort level \( e \)",
        })
        result = verify_stackelberg(entry)
        assert result.entry_specific is True
        assert result.verdict == "COUNTEREXAMPLE"

    def test_equilibrium_existence_false_is_unsupported(self):
        entry = _entry({
            "equilibrium_existence": False,
            "follower_utility_latex": r"U_i(e, p) = p e - \frac{e^2}{2}",
        })
        result = verify_stackelberg(entry)
        assert result.verdict == "UNSUPPORTED"
        assert result.entry_specific is False

    def test_ambiguous_decision_variable_falls_back_to_template(self):
        # Two free symbols, no follower_decision/leader_objective signal
        # to disambiguate which one the follower controls.
        entry = _entry({
            "equilibrium_existence": True,
            "follower_utility_latex": r"U = a x - b y",
            "follower_decision": "",
        })
        result = verify_stackelberg(entry)
        assert result.entry_specific is False
        assert result.verdict == "VERIFIED_TEMPLATE"

    def test_opaque_auxiliary_function_falls_back_to_template(self):
        entry = _entry({
            "equilibrium_existence": True,
            "follower_utility_latex": r"U = \Phi_i(p) - c, \quad \Phi_i(p) = p^2",
            "follower_decision": r"purchase amount \( p \)",
        })
        result = verify_stackelberg(entry)
        assert result.entry_specific is False
        assert result.verdict == "VERIFIED_TEMPLATE"

    def test_best_response_mismatch_is_rejected_not_verified(self):
        # FOC correctly gives e* = p; a best_response_latex claiming
        # something else must block VERIFIED rather than being ignored.
        entry = _entry({
            "equilibrium_existence": True,
            "follower_utility_latex": r"U_i(e, p) = p e - \frac{e^2}{2}",
            "follower_decision": r"effort level \( e \)",
            "best_response_latex": r"e^* = 2p",
        })
        result = verify_stackelberg(entry)
        assert result.entry_specific is False
        assert result.verdict == "VERIFIED_TEMPLATE"

    def test_best_response_match_is_verified(self):
        entry = _entry({
            "equilibrium_existence": True,
            "follower_utility_latex": r"U_i(e, p) = p e - \frac{e^2}{2}",
            "follower_decision": r"effort level \( e \)",
            "best_response_latex": r"e^* = p",
        })
        result = verify_stackelberg(entry)
        assert result.entry_specific is True
        assert result.verdict == "VERIFIED"

    def test_missing_follower_utility_falls_back_to_template(self):
        entry = _entry({"equilibrium_existence": True})
        result = verify_stackelberg(entry)
        assert result.entry_specific is False
        assert result.verdict == "VERIFIED_TEMPLATE"


class TestResolveStackelbergUtility:
    def test_single_clause_parses_directly(self):
        expr = _resolve_stackelberg_utility(r"U_i(e, p) = p e - \frac{e^2}{2}")
        assert expr is not None
        assert str(expr.free_symbols) != "set()"

    def test_multi_clause_definition_is_substituted(self):
        # "U = R - C, R = ..., C = ..." -- the shape most follower_utility
        # fields in the real corpus actually use.
        expr = _resolve_stackelberg_utility(
            r"U_i = R_i - C_i, \quad R_i = r_i \ln(1/\theta_i), \quad C_i = \sigma_i/\theta_i"
        )
        assert expr is not None
        names = {str(s) for s in expr.free_symbols}
        # R_i and C_i must have been substituted away, not left opaque.
        assert not names & {"R_{i}", "C_{i}"}
        assert "theta_{i}" in names

    def test_opaque_capital_greek_function_bails(self):
        assert _resolve_stackelberg_utility(r"U = \Phi_i(p) - c") is None


class TestDemoteStrayFunctionCalls:
    def test_rewrites_juxtaposition_misread_as_function_call(self):
        import sympy as sp

        p, c = sp.symbols("p c")
        # sympy would already build this as Mul; simulate what parse_latex
        # produces for "c (p)" by constructing an explicit AppliedUndef.
        f = sp.Function("c")(p)
        demoted = _demote_stray_function_calls(f + c)
        assert not demoted.atoms(sp.core.function.AppliedUndef)


class TestNonStringFollowerDecisionFailsClosed:
    """R3b: the LLM formalizer put a dict (not LaTeX) under
    m.meta['follower_decision'] for at least one Stackelberg corpus entry.
    The two string-consuming readers must treat a non-str as absent ('')
    so the entry degrades to UNKNOWN instead of crashing the whole sweep
    with TypeError: expected string or bytes-like object, got 'dict'.
    """

    def test_extract_follower_symbol_with_dict_does_not_raise(self):
        from tracks.track1_z3 import _extract_follower_symbol

        out = _extract_follower_symbol(
            {"mechanism": {"follower_decision": {"x": 1}}}, set()
        )
        assert out is None

    def test_follower_decision_latex_with_dict_does_not_raise(self):
        from tracks.track1_z3 import _follower_decision_latex

        assert _follower_decision_latex({"mechanism": {"follower_decision": {"x": 1}}}) is None

    def test_extract_follower_symbol_with_dict_foc_and_br(self):
        from tracks.track1_z3 import _extract_follower_symbol

        out = _extract_follower_symbol(
            {"mechanism": {
                "follower_decision": {"x": 1},
                "follower_foc_latex": {"y": 2},
                "best_response_latex": {"z": 3},
            }},
            set(),
        )
        assert out is None

    def test_verify_from_ast_stackelberg_dict_follower_decision_returns_verdict(self):
        from architect.ast_verify import verify_from_ast
        from architect.ast import Mechanism, Sum, Prod, Const, Pow, Sym

        # Canonical VERIFIED shape, but meta.follower_decision is a dict and
        # best_response_latex is a dict -> both must fail closed, not raise.
        m = Mechanism(
            category="Stackelberg",
            utility=Sum([Prod([Sym("p_i"), Sym("e_i")]),
                         Prod([Const(-0.5), Sym("c"), Pow(Sym("e_i"), 2)])]),
            payment=Sym("p_i"), ic=Sym("e_i"), ir=Sym("e_i"),
            type_space=[],
            meta={
                "equilibrium_existence": True,
                "follower_decision": {"symbol": "e_i"},
                "best_response_latex": {"lhs": "e_i", "rhs": "p_i"},
            },
        )
        res = verify_from_ast(m)
        assert res.verdict in {"UNKNOWN", "VERIFIED_TEMPLATE", "UNSUPPORTED"}
