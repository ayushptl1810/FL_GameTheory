"""Task 8-pre: VCG allocation-classifier formalization path."""
from architect.formalize import (
    classify_vcg_allocation,
    formalize_vcg_entry,
    formalize_with_retry,
    FormalizeResult,
)


def _fake(resp_json):
    return lambda sys, user, **kw: resp_json


_VCG_MECH = {
    "allocation_rule_latex": r"x_i = 1 \text{ if } b_i = \max_j b_j",
    "payment_rule_latex": r"p_i = \max_{j \neq i} b_j",
    "client_utility_latex": r"u_i = v_i - p_i",
}


def _entry(**over):
    e = {"category": "VCG", "paper_id": "x", "num_clients": 2,
         "mechanism": dict(_VCG_MECH)}
    e.update(over)
    return e


def test_classify_highest():
    r = classify_vcg_allocation(r"x^* = \arg\max S(x)",
                                complete=_fake('{"t":"AllocHighest"}'))
    assert r == {"t": "AllocHighest"}


def test_classify_null_on_bad_json():
    assert classify_vcg_allocation("x", complete=_fake("not json")) == {"t": None}


def test_classify_null_on_unknown_type():
    assert classify_vcg_allocation("x", complete=_fake('{"t":"AllocFoo"}')) == {"t": None}


def test_classify_topk_needs_int_k():
    assert classify_vcg_allocation("x", complete=_fake('{"t":"AllocTopK"}')) == {"t": None}
    r = classify_vcg_allocation("x", complete=_fake('{"t":"AllocTopK","k":3}'))
    assert r["k"] == 3


def test_classify_weighted_needs_nonempty_list():
    r = classify_vcg_allocation(
        "x", complete=_fake('{"t":"AllocWeightedWelfare","weights":[]}'))
    assert r == {"t": None}


def test_classify_none_latex():
    called = []
    comp = lambda s, u, **kw: called.append(1) or '{"t":"AllocHighest"}'
    assert classify_vcg_allocation(None, complete=comp) == {"t": None}
    assert not called


def test_formalize_vcg_entry_highest_is_entry_specific():
    res = formalize_vcg_entry(_entry(), complete=_fake('{"t":"AllocHighest"}'))
    assert isinstance(res, FormalizeResult)
    assert res.verdict == "VERIFIED"


def test_formalize_vcg_entry_bad_payment_is_never_verified():
    # Critical #1 regression: a typed AllocHighest node makes render() substitute
    # the canonical Clarke pivot for payment_rule_latex. If the grid proved THAT,
    # this non-Groves payment would come back VERIFIED even though nobody ever
    # checked it. The paper's real payment must win -> never VERIFIED.
    m = dict(_VCG_MECH)
    m["payment_rule_latex"] = r"p_i = 42 b_i + 7"
    res = formalize_vcg_entry(_entry(mechanism=m),
                              complete=_fake('{"t":"AllocHighest"}'))
    assert res.verdict != "VERIFIED"
    assert res.verdict in ("COUNTEREXAMPLE", "UNKNOWN", "VERIFIED_SHAPE")


def test_formalize_vcg_entry_welfare_diff_payment_verifies_for_real():
    # The paper's own welfare-difference Groves pivot on a unit-weight
    # welfare-max allocation is the second price -> real entry-specific VERIFIED.
    m = dict(_VCG_MECH)
    m["allocation_rule_latex"] = r"x^* = \arg\max \sum v_i x_i"
    m["payment_rule_latex"] = r"p_i = S(x^*) - S(z^*)"
    res = formalize_vcg_entry(_entry(mechanism=m),
                              complete=_fake('{"t":"AllocHighest"}'))
    assert res.verdict == "VERIFIED"


def test_formalize_vcg_entry_null_alloc_falls_back():
    # Opaque allocation LaTeX + null classification => no typed node and the meta
    # fallback in verify_from_ast cannot parse the rule => not a full VERIFIED.
    m = dict(_VCG_MECH)
    m["allocation_rule_latex"] = r"x = \text{the output of Algorithm 3}"
    res = formalize_vcg_entry(_entry(mechanism=m), complete=_fake('{"t":null}'))
    assert res.verdict in ("VERIFIED_SHAPE", "UNKNOWN")


def test_formalize_vcg_entry_null_alloc_but_clean_latex_still_verifies():
    # Classifier is a bonus, not a gate: when the corpus allocation/payment LaTeX
    # is already parse_allocation-clean, a {"t":null} classification still yields
    # a real entry-specific VERIFIED via verify_from_ast's meta fallback.
    # (FormalizeResult has no entry_specific field; entry_specific=True rides on
    # the VerificationResult inside verify_from_ast — see test_ast_verify.py
    # test_verify_from_ast_vcg_clarke_is_real_verified.)
    res = formalize_vcg_entry(_entry(), complete=_fake('{"t":null}'))
    assert res.verdict == "VERIFIED"


def test_formalize_with_retry_dispatches_vcg():
    res = formalize_with_retry(_entry(), None,
                               complete=_fake('{"t":"AllocHighest"}'))
    assert res.verdict == "VERIFIED"
    assert res.retries == 0
