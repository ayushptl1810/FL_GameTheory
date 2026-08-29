"""Adversarial soundness suite: verify() must never certify a known-unsound
mechanism. Each BROKEN fixture is provably not IC/IR (see the `# why unsound:`
note beside it in broken_mechanisms.py) and reaches an entry-specific verifier
path; a VERIFIED / VERIFIED_TEMPLATE for any of them is a soundness bug.

TEMPLATE_FALLBACK_HOLES are the cases the verifier still passes because a
category's generic template path ignores the entry's own math; they are pinned
here as xfail so a future change either closes them (xpass -> tighten) or is
caught if it makes them worse.
"""
import pytest

from verifier import verify
from tests.verifier.broken_mechanisms import BROKEN, TEMPLATE_FALLBACK_HOLES

UNSOUND = {"VERIFIED", "VERIFIED_TEMPLATE"}


def _entry(case):
    entry = {"category": case["category"], "paper_id": case["name"],
             "mechanism": dict(case["mechanism"])}
    if "params" in case:
        entry["mechanism"].setdefault("eval_params", case["params"])
    return entry


@pytest.mark.parametrize("case", BROKEN, ids=[c["name"] for c in BROKEN])
def test_broken_mechanism_is_never_verified(case):
    res = verify(_entry(case))
    assert res.verdict not in UNSOUND, (
        f"{case['name']}: verifier returned {res.verdict} for an unsound mechanism")


@pytest.mark.parametrize("case", TEMPLATE_FALLBACK_HOLES,
                         ids=[c["name"] for c in TEMPLATE_FALLBACK_HOLES])
# strict=True: every case here is a KNOWN template-fallback / VCG-entry-specific
# hole a future phase will close. When one closes it must fail loudly (forcing an
# un-xfail), not silently xpass. None of these is run-to-run indeterminate.
@pytest.mark.xfail(reason="generic template path ignores entry-specific math; "
                          "closing this is a verifier redesign (see task-D-report.md)",
                   strict=True)
def test_template_fallback_hole_documented(case):
    res = verify(_entry(case))
    assert res.verdict not in UNSOUND, (
        f"{case['name']}: verifier returned {res.verdict} for an unsound mechanism")
