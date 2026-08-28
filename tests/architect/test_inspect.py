from architect.ast import Const, Sym, Sum, Prod, Pow, Mechanism
from architect.inspect import inspect_mechanism, is_loop_success


def _textbook_menu():
    # 2-type linear screening menu known to be IC/IR (mirror a z3_validated corpus entry).
    # Uses single-char symbol bases (t_i for the type) so the rendered LaTeX round-trips
    # through serialize.render()'s parser check — multi-letter names like "theta_i" are
    # split letter-by-letter by parse_latex and fail the round-trip.
    u = Sum([Sym("R_i"), Prod([Const(-1), Sym("t_i"), Sym("e_i")])])
    ic = Sum([Sym("R_i"), Prod([Const(-1), Sym("t_i"), Sym("e_i")]),
              Prod([Const(-1), Sym("R_j")]), Prod([Sym("t_i"), Sym("e_j")])])
    return Mechanism("Contract", utility=u, payment=Sym("R_i"), ic=ic, ir=u,
                     params={}, type_space=["lo", "hi"])


def test_inspect_returns_a_verification_result():
    r = inspect_mechanism(_textbook_menu(), meta={"paper_id": "t", "num_clients": 2})
    assert r.verdict in {"VERIFIED", "VERIFIED_TEMPLATE", "COUNTEREXAMPLE", "UNKNOWN", "UNSUPPORTED"}


def test_is_loop_success_requires_entry_specific():
    class R:  # minimal stand-in
        verdict = "VERIFIED"; entry_specific = False
    assert is_loop_success(R()) is False
    R.entry_specific = True
    assert is_loop_success(R()) is True
