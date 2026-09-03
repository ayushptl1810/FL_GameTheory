r"""Task 11-pre Part A: `_parse_contract_entry` gap fixes.

Two textual pre-steps were added ahead of the existing utility-call
expansion:

  * `_strip_contract_prose`        -- drops an "IC:" label, a `\text{...}`
    prose lead-in, a trailing `\quad \forall ...` quantifier, and any
    SECOND contract introduced after a `\qquad`.
  * `_strip_call_args_on_powers`   -- drops a menu-item indexation tag on a
    squared quantity, e.g. `R_i^2(\theta_k^1)` -> `R_i^2`.

Plus a Bayesian bail-out: an `E_{...}[...]` / `\mathbb{E}` wrapper makes
`_parse_contract_entry` return None so `verify()` falls through to the
Track 4 path rather than grid-checking an ex-ante constraint pointwise.

Every case below is either a real corpus entry or a minimal synthetic
fixture. The overriding rule is FAIL CLOSED: a form we cannot confidently
parse must yield None, never a guessed obligation.
"""
import json
import pathlib

import pytest

from tracks.track1_z3 import (
    _parse_contract_entry,
    _strip_call_args_on_powers,
    _strip_contract_prose,
)
from verifier import verify

_CORPUS = json.loads(
    (pathlib.Path(__file__).resolve().parents[2] / "corpus.json").read_text()
)


def _entry(paper_id: str) -> dict:
    for e in _CORPUS:
        if e.get("paper_id") == paper_id:
            return e
    raise AssertionError(f"corpus entry {paper_id!r} not found")


# --------------------------------------------------------------------------
# _strip_contract_prose
# --------------------------------------------------------------------------

def test_strip_prose_removes_ic_label_and_trailing_quantifier():
    s = (
        r"IC: ConV_n R_n - E_n \geq ConV_n R_i - E_i, \quad \forall n, i \in N,"
        r"\ n \neq i \quad \text{(paper's Eq. 24)}"
    )
    assert _strip_contract_prose(s) == r"ConV_n R_n - E_n \geq ConV_n R_i - E_i"


def test_strip_prose_keeps_only_the_first_of_two_contracts():
    r"""A `\qquad` after the first inequality introduces a SECOND contract
    (Wan states a model-owner and a worker contract in one string). Only the
    primary one may survive -- concatenating both would be nonsense."""
    s = (
        r"\text{Model-owner (Eq. 8): } \varphi_m R_m - C V_m \geq "
        r"\varphi_z R_z - C V_z, \quad m \neq z. "
        r"\qquad \text{Worker (Eq. 32): } r_m - c_m q_m \geq r_z - c_z q_z"
    )
    out = _strip_contract_prose(s)
    assert out.startswith(r"\varphi_m R_m")
    assert "r_m - c_m q_m" not in out
    assert out.count(r"\geq") == 1


def test_strip_prose_is_identity_on_a_clean_inequality():
    s = r"\theta_i R_i - c q_i \geq \theta_i R_j - c q_j"
    assert _strip_contract_prose(s) == s


def test_strip_prose_handles_empty_string():
    assert _strip_contract_prose("") == ""


# --------------------------------------------------------------------------
# _strip_call_args_on_powers
# --------------------------------------------------------------------------

def test_strip_call_args_removes_menu_indexation_tag():
    s = r"\theta_i^2 R_i^2(\theta_k^1) - cT_i^2(\theta_k^1) - E"
    assert _strip_call_args_on_powers(s) == r"\theta_i^2 R_i^2 - cT_i^2 - E"


def test_strip_call_args_leaves_a_non_power_call_alone():
    """Only a call directly on a `^2` is an indexation tag. A general
    function call carries real arguments and must NOT be stripped."""
    s = r"\theta_j S(\rho_j(t),\zeta_j(t)) - C(\rho_j(t),\phi_j(t))"
    assert _strip_call_args_on_powers(s) == s


# --------------------------------------------------------------------------
# Entries that now parse
# --------------------------------------------------------------------------

def test_wen2025_parses_to_the_screening_shape():
    r"""The `(\theta_k^1)` tag was the only blocker; removing it exposes a
    clean type-fixed / contract-varying IC."""
    parsed = _parse_contract_entry(_entry("Wen2025diffusion_contract"))
    assert parsed is not None
    _U_ir, U_rhs, type_sub, contract_sub, _n, _from_lhs = parsed
    assert (type_sub, contract_sub) == ("i", "j")
    # The deviating-contract utility must retain the TRUE type's subscript.
    assert any("theta_" in str(s) and "i" in str(s) for s in U_rhs.free_symbols)


def test_wen2025_verifies_end_to_end():
    assert verify(_entry("Wen2025diffusion_contract")).verdict == "VERIFIED"


# --------------------------------------------------------------------------
# Fail-closed: forms deliberately NOT widened
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "paper_id, why",
    [
        # IC RHS keeps each side at its OWN type (varphi_m R_m vs varphi_z R_z):
        # an equilibrium-utility ordering, not U_m(contract_z). The soundness
        # gate must reject it.
        ("International_Journal_of_Intelligent_Systems_-_2024_-_Wan_-_"
         "Hierarchical_Incentive_Mechanism_for_Federated_Learning__A",
         "both sides at own type; not a deviation"),
        # IR is indexed by `a`, the IC by `n`/`i`. Equating them would be a guess.
        ("Wang2022motilearn_contract", "IR and IC use different index symbols"),
        # `R_{n-1}` is a single symbol, not an iterable index.
        ("Kang2022blockchain_metaverse", "n-1 subscript arithmetic"),
        # Deviation is a predicate (`\hat\theta_i \neq \theta_i`), unsubstitutable.
        ("2502_20882", "deviation stated as a predicate"),
        # Opaque multi-arg functions G/C with no algebraic definition.
        ("Saputra2020fl_contract", "undefined opaque functions"),
        ("Saputra2021iov_contract", "undefined opaque functions"),
        # IC references W_U^i, a function the entry never defines.
        ("Ma2023joint_pricing", "IC references an undefined function"),
        # Utility formal args are bundle symbols with no stated decomposition.
        ("Lim2020contract", "bundle-argument utility call"),
        ("Wu2021contract_DP", "bundle-argument utility call"),
        # Prime notation as the contract index plus a `|\gamma` conditional.
        ("2403_09153", "prime contract index and conditional bar"),
    ],
)
def test_unsupported_forms_still_fail_closed(paper_id, why):
    assert _parse_contract_entry(_entry(paper_id)) is None, why


def test_bayesian_expectation_bails_to_track4():
    r"""An `E_{c_{-k}}[...]` wrapper states an EX-ANTE constraint. Stripping
    the expectation and grid-checking pointwise would prove something
    strictly stronger than the paper claims, so the LaTeX path must decline
    and leave the entry to the Bayesian track."""
    assert _parse_contract_entry(_entry("2602_21844")) is None


def test_bayesian_bailout_does_not_catch_a_plain_symbol_named_E():
    r"""Wen2025's utility carries a bare constant `E`. The Bayesian guard
    keys on `E_{...}[` / `\mathbb{E}` and must not fire on that."""
    assert _parse_contract_entry(_entry("Wen2025diffusion_contract")) is not None
