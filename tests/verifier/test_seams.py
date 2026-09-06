import json

from verifier import verify

CORPUS = json.load(open("corpus.json"))
VCG = [e for e in CORPUS if e.get("category") == "VCG"][:8]


def test_vcg_verdicts_unchanged_after_seam_extraction():
    # Phase 2 Task 5 established VERIFIED_SHAPE/False for all 8 (grid check failed
    # closed, regex fallback = structural match, not a proof).
    # R2 (2026-09-03) VCG sweep: the allocation-classifier formalization path
    # (architect.formalize.formalize_vcg_entry) built a typed allocation node for
    # 4 of these 8, so verify_from_ast's finite-grid DSIC proof now succeeds
    # entry-specifically -> VERIFIED/True. The other 4 keep the regex fallback
    # (classifier returned null / rule not grid-encodable) -> VERIFIED_SHAPE/False.
    # R2 Task 9 (hand-check, 2026-09-03): Cui2024auction_market's flip was REVERTED
    # -- its payment b_{t,j}*DeltaG_{t,i} is a first-price product, not a Clarke
    # pivot -- then diagnosed MANUAL. 2404_13841 and Ahmed2023frimfl were also
    # diagnosed MANUAL (budget-constrained greedy, out of the grid-decidable
    # family). Batool2022fl_mab stays VERIFIED_SHAPE as an R6 formalization-miss
    # candidate. The remaining 4 VERIFIED flips were each cross-checked against
    # Groves 1973 / Clarke 1971 by hand.
    # R2 Task 10 (Critical #1 fix + clean re-sweep): a typed allocation node made
    # render() swap the paper's payment for a canonical Clarke pivot, so the grid
    # proved a textbook mechanism rather than the entry's own math. The paper's
    # real payment now wins, and parse_payment reads welfare-difference Clarke
    # pivots (S(x*)-S(z*), r(x*)-sum_{k!=i}) on single-item welfare-max
    # allocations. Corpus re-swept clean under the fix, Task 9 adjudication kept:
    # 3 real entry-specific VERIFIED (2504_05563, 3626307_3626311, Cong2020vcg);
    # 2404_13841 / Ahmed2023frimfl / Cui2024auction_market diagnosed MANUAL
    # (budget-knapsack / posted-price / first-price-product, none Groves);
    # Cheng2022uav dropped VERIFIED->VERIFIED_SHAPE (welfare diff over a 3-index
    # allocation, weights unresolvable -> fails closed, now an R6 candidate);
    # Batool2022fl_mab stays VERIFIED_SHAPE (R6, score defined but argmax never
    # stated).
    # R-shape-cleanup (2026-09-05): the last 8 VERIFIED_SHAPE entries were
    # diagnosed to a real terminal state (verdict_override). Cheng2022uav's
    # allocation is a 3-index buyer/data-seller/UAV-seller assignment with an
    # opaque coalition-value F(.) never given a closed form -- no track can
    # substitute a value for an opaque function reference -> MANUAL. See
    # corpus.json's manual_diagnosis on this entry for the full obstruction.
    expected = {
        "2404_13841": ("MANUAL", False),
        "2504_05563": ("VERIFIED", True),
        "3626307_3626311": ("VERIFIED", True),
        "Ahmed2023frimfl": ("MANUAL", False),
        # R6-R7: flipped to MANUAL, second-pass reclaim attempted and failed (fail-closed)
        "Batool2022fl_mab": ("MANUAL", False),
        "Cheng2022uav": ("MANUAL", False),
        "Cong2020vcg": ("VERIFIED", True),
        "Cui2024auction_market": ("MANUAL", False),
    }
    for e in VCG:
        r = verify(e)
        assert e["paper_id"] in expected
        assert (r.verdict, r.entry_specific) == expected[e["paper_id"]]


_CONTRACT_IDS = [
    # all 5 currently entry-specific VERIFIED
    "2307_15975",
    "Li2025bayesian_incentive",
    "Lim2020contract_healthcare",
    "Sun2022coded",
    "Tan2025renegotiable_contract",
    # 3 template (linear-cost model) entries
    "2102_03401",
    "2308_12502",
    "2403_09153",
]
CONTRACT = [e for e in CORPUS if e.get("paper_id") in _CONTRACT_IDS]


def test_contract_verdicts_unchanged_after_seam_extraction():
    # Behavior lock for Task 4: snapshot of verify() on 8 corpus Contract
    # entries, captured before extracting _contract_check_core from
    # _try_contract_latex.
    expected_contract = {
        "2307_15975": ("VERIFIED", True),
        "Li2025bayesian_incentive": ("VERIFIED", True),
        "Lim2020contract_healthcare": ("VERIFIED", True),
        "Sun2022coded": ("VERIFIED", True),
        "Tan2025renegotiable_contract": ("VERIFIED", True),
        # R3a Task 12: 2102_03401 and 2308_12502 were diagnosed MANUAL. Both
        # parse and pass the soundness gate, but the Z3 encoding rejects their
        # utilities (opaque u_3(.) / symbolic superscript on r_j^L, plus a
        # population-coupled kappa_j), so no solver ever ran on the entry's own
        # math -- the VERIFIED_TEMPLATE was a generic linear-cost skeleton.
        # 2403_09153 stays on the template as an R6 candidate (prime-notation
        # contract index is a parser gap, not a semantic obstruction).
        "2102_03401": ("MANUAL", False),
        "2308_12502": ("MANUAL", False),
        # R6-R7: flipped to MANUAL, second-pass reclaim attempted and failed (fail-closed)
        "2403_09153": ("MANUAL", False),
    }
    assert len(CONTRACT) == len(expected_contract)
    for e in CONTRACT:
        r = verify(e)
        assert e["paper_id"] in expected_contract
        assert (r.verdict, r.entry_specific) == expected_contract[e["paper_id"]]


_STACKELBERG_IDS = [
    # the 1 currently entry-specific VERIFIED
    "Sarikaya2019stackelberg_workers",
    # 5 template-only entries
    "1811_12082",
    "2101_05628",
    "2101_12428",
    "2103_05866",
    "2110_12876",
]
STACKELBERG = [e for e in CORPUS if e.get("paper_id") in _STACKELBERG_IDS]


def test_stackelberg_verdicts_unchanged_after_seam_extraction():
    # Behavior lock for Task 5: snapshot of verify() on 6 corpus Stackelberg
    # entries, captured before extracting _stackelberg_check_core from
    # _try_stackelberg_latex.
    expected_stackelberg = {
        "Sarikaya2019stackelberg_workers": ("VERIFIED", True),
        # Corpus-wide sweep (2026-09-06): verdict_override removed after
        # transcribing fixed_constants (b_i, c_i) from Sec. V; the
        # follower-IR blocker itself is unresolved (no U>=0 statement in
        # the paper), so the entry-specific path still declines and falls
        # through to the generic quadratic template -- an honest
        # VERIFIED_TEMPLATE, not a guessed VERIFIED.
        "1811_12082": ("VERIFIED_TEMPLATE", False),
        # R3b Task 15: adjudicated MANUAL (vector / multi-stage follower
        # decisions the single-variable FOC path cannot reduce). The seam
        # this test locks is unchanged; only the verdict_override is new.
        "2101_05628": ("MANUAL", False),
        "2101_12428": ("MANUAL", False),
        "2103_05866": ("MANUAL", False),
        # R6-R7: flipped to MANUAL, second-pass reclaim attempted and failed (fail-closed)
        "2110_12876": ("MANUAL", False),
    }
    assert len(STACKELBERG) == len(expected_stackelberg)
    for e in STACKELBERG:
        r = verify(e)
        assert e["paper_id"] in expected_stackelberg
        assert (r.verdict, r.entry_specific) == expected_stackelberg[e["paper_id"]]


# Behavior lock for Task 7: every corpus entry that currently routes to
# Track 2 (SOS, 4), Track 3 (interval, 2), or Track 4 (Bayesian, 1), captured
# before extracting track{2,3,4}_check_from_sympy from verify_track{2,3,4}.
# {paper_id: (verdict, entry_specific, track)}
_EXPECTED_T234 = {
    "2307_15975": ("VERIFIED", True, 2),
    "Lim2020contract_healthcare": ("VERIFIED", True, 2),
    "Sun2022coded": ("VERIFIED", True, 2),
    "Tan2025renegotiable_contract": ("VERIFIED", True, 2),
    # R4 Task 8: type_variable corrected to the single screening type \theta_i
    # (was ambiguous prose naming both theta and e), so Track 1's single-crossing
    # ordering now applies and the entry proves VERIFIED on Track 2 (SOS).
    "Tian2021contract": ("VERIFIED", True, 2),
    # R3a Task 12 diagnosed the two remaining UNKNOWNs plus the Bayesian
    # 2602_21844 as MANUAL. Kang2019contract_mobile: Track 3's box search is
    # intractable at 9/11 free variables. 2602_21844: Track 4 cannot reduce the
    # multi-agent posterior expectation E_{c_{-k}}[.] to a closed form. Both
    # keep their track; only the verdict is now recorded rather than left
    # UNKNOWN, and entry_specific drops to False with the override.
    "Kang2019contract_mobile": ("MANUAL", False, 3),
    # Corpus-wide sweep (2026-09-06): verdict_override removed after
    # transcribing fixed_constants (zeta, psi, mu, l) from Table II. B,
    # h_n, N_0, sigma, rho_n remain individually unresolved, so Track 3's
    # dReal interval search reports its own honest UNKNOWN (delta-sound,
    # not exact) rather than a guessed verdict.
    "Kang2019reliable_contract": ("UNKNOWN", True, 3),
    "Sarikaya2019stackelberg_workers": ("VERIFIED", True, 3),
    "Li2025bayesian_incentive": ("VERIFIED", True, 4),
    "2602_21844": ("MANUAL", False, 4),
}


def test_track234_verdicts_unchanged_after_seam_extraction():
    seen = {}
    for e in CORPUS:
        r = verify(e)
        if getattr(r, "track", None) in (2, 3, 4):
            seen[e["paper_id"]] = (r.verdict, r.entry_specific, r.track)
    assert seen == _EXPECTED_T234


# Behavior lock for Task 5: the 4 corpus entries that route to Track 2 (SOS),
# captured BEFORE track2_check_from_sympy was made SymPy-native (signature
# changed from (entry, gap_expr, theta_sym) to
# (gap_expr, theta_sym, theta_min, theta_max, *, ir_expr, ...) with all
# entry/LaTeX parsing lifted into verify_track2's front-end).
_EXPECTED_TRACK2 = {
    "2307_15975": ("VERIFIED", True),
    "Lim2020contract_healthcare": ("VERIFIED", True),
    "Sun2022coded": ("VERIFIED", True),
    "Tan2025renegotiable_contract": ("VERIFIED", True),
    "Tian2021contract": ("VERIFIED", True),   # R4 Task 8 type_variable fix
}


def test_track2_verdicts_unchanged_after_sympy_native_refactor():
    seen = {}
    for e in CORPUS:
        r = verify(e)
        if getattr(r, "track", None) == 2:
            seen[e["paper_id"]] = (r.verdict, r.entry_specific)
    assert seen == _EXPECTED_TRACK2


# Behavior lock for Task 6: the corpus entries that route to Track 3 (interval
# arithmetic), captured BEFORE track3_check_from_sympy was made SymPy-native
# (signature changed from (entry, paper_id, category, mech, theta_min,
# theta_max) to (ic_expr, ir_expr, ic_bounds, ir_bounds, delta, *,
# entry_specific, paper_id, category, ...) with all entry/LaTeX parsing and
# bound extraction lifted into verify_track3's front-end).
_EXPECTED_TRACK3 = {
    "Sarikaya2019stackelberg_workers": ("VERIFIED", True),
    # R3a Task 12: diagnosed MANUAL (9 free vars in IC / 11 in IR make the
    # interval box search intractable at delta=0.001). Still routes to Track 3.
    "Kang2019contract_mobile": ("MANUAL", False),
    # Corpus-wide sweep (2026-09-06): verdict_override removed after
    # transcribing fixed_constants (zeta, psi, mu, l); remaining free
    # symbols (B, h_n, N_0, sigma, rho_n) leave the interval search
    # genuinely undecided -- an honest UNKNOWN, not a guessed verdict.
    "Kang2019reliable_contract": ("UNKNOWN", True),
}


def test_track3_verdicts_unchanged_after_sympy_native_refactor():
    seen = {}
    for e in CORPUS:
        r = verify(e)
        if getattr(r, "track", None) == 3:
            seen[e["paper_id"]] = (r.verdict, r.entry_specific)
    assert seen == _EXPECTED_TRACK3


# Behavior lock for Task 7: the corpus entries that route to Track 4 (Bayesian
# symbolic integration), captured BEFORE track4_check_from_sympy was made
# SymPy-native (signature changed from (paper_id, category, theta_min,
# theta_max, distribution, ir_raw, ic_raw, ir_expr, theta_sym) to
# (ir_expr, ic_gap, theta_sym, theta_min, theta_max, distribution, *,
# ic_gap_err, entry_specific, paper_id, category) with the IC-gap LaTeX parse
# lifted into verify_track4's front-end via _parse_ic_gap).
_EXPECTED_TRACK4 = {
    "Li2025bayesian_incentive": ("VERIFIED", True),
    # R3a Task 12: diagnosed MANUAL -- Track 4's symbolic integrator cannot
    # reduce the multi-agent posterior expectation E_{c_{-k}}[.] to a
    # posynomial-checkable closed form.
    "2602_21844": ("MANUAL", False),
}


def test_track4_verdicts_unchanged_after_sympy_native_refactor():
    seen = {}
    for e in CORPUS:
        r = verify(e)
        if getattr(r, "track", None) == 4:
            seen[e["paper_id"]] = (r.verdict, r.entry_specific)
    assert seen == _EXPECTED_TRACK4
