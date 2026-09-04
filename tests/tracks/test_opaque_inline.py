from tracks.track1_z3 import _opaque_inline


def test_opaque_inline_substitutes():
    mech = {"opaque_function_forms": {"u_3": r"\alpha \theta_i + \beta"}}
    out = _opaque_inline(mech, r"R_i - u_3(\theta_i) - E")
    assert r"u_3(" not in out
    assert r"\alpha \theta_i + \beta" in out


def test_opaque_inline_absent_noop():
    assert _opaque_inline({}, r"R_i - x") == r"R_i - x"
