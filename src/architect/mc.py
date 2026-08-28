from __future__ import annotations
import numpy as np, sympy
from architect.serialize import ast_to_sympy
from architect.ast import Mechanism


def mc_prefilter(m: Mechanism, *, n_samples: int = 1000, eps: float = 1e-6, seed: int = 0):
    expr = ast_to_sympy(m.ic)
    syms = sorted(expr.free_symbols, key=str)
    if not syms:
        val = float(expr)
        return None if val >= -eps else {"type": "(constant)", "ic_gap": f"{val:.6g}"}
    rng = np.random.default_rng(seed)
    lo, hi = 0.1, 1.0
    samples = {s: rng.uniform(lo, hi, n_samples) for s in syms}
    f = sympy.lambdify(syms, expr, "numpy")
    gaps = np.asarray(f(*[samples[s] for s in syms]), dtype=float)
    worst = int(np.argmin(gaps))
    if gaps[worst] < -eps:
        assign = ", ".join(f"{s}={samples[s][worst]:.4f}" for s in syms)
        return {"type": assign, "ic_gap": f"{gaps[worst]:.6g}"}
    return None
