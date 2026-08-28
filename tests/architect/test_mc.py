from architect.ast import Const, Sym, Sum, Prod, Mechanism
from architect.mc import mc_prefilter


def _ic_ok():
    ic = Sum([Prod([Sym("theta_i"), Sym("theta_i")])])   # theta_i^2 >= 0 always
    return Mechanism("Contract", utility=Sym("R_i"), payment=Sym("R_i"),
                     ic=ic, ir=Sym("R_i"), type_space=["lo"])


def _ic_bad():
    ic = Sum([Prod([Const(-1), Sym("theta_i"), Sym("theta_i")])])  # -theta_i^2 < 0
    return Mechanism("Contract", utility=Sym("R_i"), payment=Sym("R_i"),
                     ic=ic, ir=Sym("R_i"), type_space=["lo"])


def test_mc_passes_a_nonnegative_ic():
    assert mc_prefilter(_ic_ok(), n_samples=200) is None


def test_mc_catches_a_violating_ic():
    cex = mc_prefilter(_ic_bad(), n_samples=200)
    assert cex is not None and "ic_gap" in cex
