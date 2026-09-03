r"""Task 11-pre Part B: LLM IC/IR extraction for empty-IC Contract entries.

Ten corpus Contract entries carry an empty `ic_screening_latex`; the paper
states the screening constraints only in prose/PDF. `formalize_contract_entry`
asks a model for them, re-checks the result through the ORDINARY deterministic
Z3 path, and -- only if that path returns a real verdict -- stashes the latex
under `*_llm` fallback keys.

Two invariants the tests below pin down:

  * the paper's own latex always wins; `_llm` keys are consulted by
    `_parse_contract_entry` only when the original field is empty, so
    `verify()` stays deterministic and API-key-free.
  * fail closed: no confidence, no IC, or a non-verdict from Z3 leaves the
    entry untouched with no `_llm` keys persisted.

Every test uses a fake `complete`; nothing here calls a live model.
"""
import json

import pytest

from architect.formalize import (
    extract_contract_constraints,
    formalize_contract_entry,
)
from architect.llm import LLMError
from tracks.track1_z3 import _parse_contract_entry

# A textbook linear screening contract: type `theta_i` scales the reward, the
# per-unit cost `c` is shared across types (single-crossing holds), and the
# deviating-contract RHS keeps the TRUE type. Mirrors the shape of the corpus
# entries that already verify (e.g. Lim2020contract_healthcare).
_GOOD = {
    "ic_screening_latex": r"\theta_i R_i - c q_i \geq \theta_i R_j - c q_j",
    "ir_participation_latex": r"\theta_i R_i - c q_i \geq 0",
    "client_utility_latex": r"u_i = \theta_i R_i - c q_i",
    "num_types": 3,
    "confident": True,
}


def _fake(payload):
    """A `complete` that returns `payload` (dict -> JSON, str verbatim)."""
    def complete(system, user, json_mode=False):
        return payload if isinstance(payload, str) else json.dumps(payload)
    return complete


def _raiser(exc):
    def complete(system, user, json_mode=False):
        raise exc
    return complete


def _empty_ic_entry(**mech_over):
    mech = {
        "ic_screening_latex": "",
        "ir_participation_latex": "",
        "client_utility_latex": "",
        # Names the type symbol so the verifier can establish the type
        # ordering; without it the IC gap's sign is unidentified and every
        # entry -- corpus or synthetic -- comes back UNKNOWN.
        "type_variable": "willingness-to-pay theta_i",
    }
    mech.update(mech_over)
    return {"paper_id": "Synthetic_empty_ic", "category": "Contract",
            "mechanism": mech}


# --------------------------------------------------------------------------
# 1. extract_contract_constraints
# --------------------------------------------------------------------------

def test_extract_returns_parsed_dict_on_good_json():
    out = extract_contract_constraints(
        _empty_ic_entry(), "paper text", complete=_fake(_GOOD))
    assert out["confident"] is True
    assert out["ic_screening_latex"] == _GOOD["ic_screening_latex"]
    assert out["num_types"] == 3


@pytest.mark.parametrize(
    "payload, label",
    [
        ("not json at all", "malformed JSON"),
        ("[1, 2, 3]", "JSON that is not an object"),
        ({"ic_screening_latex": r"a \geq b"}, "missing confident key"),
        ({"confident": True}, "missing latex keys"),
        ({"confident": "yes", "ic_screening_latex": r"a \geq b"},
         "confident is a string, not a bool"),
    ],
)
def test_extract_fails_closed_on_bad_payloads(payload, label):
    out = extract_contract_constraints(
        _empty_ic_entry(), "paper text", complete=_fake(payload))
    assert out["confident"] is False, label


def test_extract_fails_closed_on_llm_error():
    out = extract_contract_constraints(
        _empty_ic_entry(), "paper text", complete=_raiser(LLMError("boom")))
    assert out == {
        "confident": False, "ic_screening_latex": "",
        "ir_participation_latex": "", "client_utility_latex": "",
        "num_types": None,
    }


def test_extract_rejects_bool_num_types():
    """`True` is an int in Python; it must not slip through as a type count."""
    out = extract_contract_constraints(
        _empty_ic_entry(), "t", complete=_fake({**_GOOD, "num_types": True}))
    assert out["num_types"] is None


# --------------------------------------------------------------------------
# 2. Already-parseable entry -> nothing to extract, model never called
# --------------------------------------------------------------------------

def test_parseable_entry_short_circuits_without_calling_the_model():
    calls = []

    def complete(system, user, json_mode=False):
        calls.append(1)
        return json.dumps(_GOOD)

    entry = {
        "paper_id": "Synthetic_parseable", "category": "Contract",
        "mechanism": {
            "ic_screening_latex": _GOOD["ic_screening_latex"],
            "ir_participation_latex": _GOOD["ir_participation_latex"],
            "client_utility_latex": _GOOD["client_utility_latex"],
            "num_types": 3,
            "type_variable": "willingness-to-pay theta_i",
        },
    }
    assert _parse_contract_entry(entry) is not None, "fixture must be parseable"
    res = formalize_contract_entry(entry, "paper text", complete=complete)
    assert res.verdict == "UNKNOWN"
    assert "nothing to extract" in res.notes
    assert calls == [], "model must not be called for a parseable entry"


def test_no_pdf_text_short_circuits():
    calls = []

    def complete(system, user, json_mode=False):
        calls.append(1)
        return json.dumps(_GOOD)

    res = formalize_contract_entry(_empty_ic_entry(), None, complete=complete)
    assert res.verdict == "UNKNOWN"
    assert res.pdf_used is False
    assert calls == []


# --------------------------------------------------------------------------
# 3. Clean extraction -> VERIFIED, `_llm` keys stashed
# --------------------------------------------------------------------------

def test_clean_linear_ic_verifies_and_stashes_llm_keys():
    entry = _empty_ic_entry()
    res = formalize_contract_entry(entry, "paper text", complete=_fake(_GOOD))
    assert res.verdict == "VERIFIED", res.notes
    m = entry["mechanism"]
    assert m["ic_screening_latex_llm"] == _GOOD["ic_screening_latex"]
    assert m["ir_participation_latex_llm"] == _GOOD["ir_participation_latex"]
    # The paper's own (empty) fields are left exactly as they were.
    assert m["ic_screening_latex"] == ""
    assert m["ir_participation_latex"] == ""


def test_stashed_llm_keys_make_the_entry_parse_deterministically():
    """After the stash, `_parse_contract_entry` alone -- no model, no API key
    -- reaches the same obligation."""
    entry = _empty_ic_entry()
    formalize_contract_entry(entry, "paper text", complete=_fake(_GOOD))
    parsed = _parse_contract_entry(entry)
    assert parsed is not None
    _U_ir, _U_rhs, type_sub, contract_sub, _n, _from_lhs = parsed
    assert (type_sub, contract_sub) == ("i", "j")


# --------------------------------------------------------------------------
# 4. Not confident -> UNKNOWN, nothing persisted
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "payload, label",
    [
        ({**_GOOD, "confident": False}, "model not confident"),
        ({**_GOOD, "ic_screening_latex": "", "confident": True}, "empty IC"),
    ],
)
def test_low_confidence_extraction_persists_nothing(payload, label):
    entry = _empty_ic_entry()
    res = formalize_contract_entry(entry, "paper text", complete=_fake(payload))
    assert res.verdict == "UNKNOWN", label
    assert not any(k.endswith("_llm") for k in entry["mechanism"]), label


def test_confident_but_unverifiable_ic_persists_nothing():
    r"""A confidently-returned IC whose RHS does NOT depend on the true type
    is an equilibrium-utility ordering, not an incentive constraint. The
    soundness gate in `_parse_contract_entry` rejects it, so no verdict comes
    back and nothing is stashed."""
    bad = {
        "ic_screening_latex": r"\theta_i R_i - c_i f_i \geq \theta_j R_j - c_j f_j",
        "ir_participation_latex": r"\theta_i R_i - c_i f_i \geq 0",
        "client_utility_latex": r"U_i = \theta_i R_i - c_i f_i",
        "num_types": 3, "confident": True,
    }
    entry = _empty_ic_entry()
    res = formalize_contract_entry(entry, "paper text", complete=_fake(bad))
    assert res.verdict != "VERIFIED"
    assert not any(k.endswith("_llm") for k in entry["mechanism"])


# --------------------------------------------------------------------------
# 5. Fallback precedence: the paper's own latex always wins
# --------------------------------------------------------------------------

def test_original_latex_wins_over_llm_keys_when_both_present():
    """`_llm` keys are a FALLBACK. With both set, the parse must reflect the
    paper's own fields -- here `p`/`q` indices, not the `_llm` `i`/`j`."""
    entry = {
        "paper_id": "Synthetic_both", "category": "Contract",
        "mechanism": {
            "ic_screening_latex": r"\theta_p R_p - c_p f_p \geq \theta_p R_q - c_p f_q",
            "ir_participation_latex": r"\theta_p R_p - c_p f_p \geq 0",
            "client_utility_latex": r"U_p = \theta_p R_p - c_p f_p",
            "ic_screening_latex_llm": _GOOD["ic_screening_latex"],
            "ir_participation_latex_llm": _GOOD["ir_participation_latex"],
            "num_types": 3,
        },
    }
    parsed = _parse_contract_entry(entry)
    assert parsed is not None
    _U_ir, _U_rhs, type_sub, contract_sub, _n, _from_lhs = parsed
    assert (type_sub, contract_sub) == ("p", "q"), "paper's latex must win"


def test_llm_keys_used_only_when_original_is_empty():
    entry = _empty_ic_entry(
        ic_screening_latex_llm=_GOOD["ic_screening_latex"],
        ir_participation_latex_llm=_GOOD["ir_participation_latex"],
        client_utility_latex_llm=_GOOD["client_utility_latex"],
        num_types=3,
    )
    parsed = _parse_contract_entry(entry)
    assert parsed is not None
    _U_ir, _U_rhs, type_sub, contract_sub, _n, _from_lhs = parsed
    assert (type_sub, contract_sub) == ("i", "j")
