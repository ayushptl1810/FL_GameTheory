r"""Task 11-pre Part A: `_parse_contract_entry` gap fixes.

One textual pre-step was added ahead of the existing utility-call expansion:

  * `_strip_contract_prose`        -- drops an "IC:" label, a `\text{...}`
    prose lead-in, a trailing `\quad \forall ...` quantifier, and any
    SECOND contract introduced after a `\qquad`.

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

from tracks.track1_z3 import _parse_contract_entry, _strip_contract_prose
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
        # Superscripts are PERIOD indices, not exponents (see below).
        ("Wen2025diffusion_contract", "period superscripts, not exponents"),
    ],
)
def test_unsupported_forms_still_fail_closed(paper_id, why):
    assert _parse_contract_entry(_entry(paper_id)) is None, why


def test_wen2025_period_superscripts_stay_template():
    r"""Wen2025's IC/IR carry `^2`/`^1` PERIOD indices, not exponents: the
    paper's utility (Eq. 6) is the linear `u_n = theta_n R_n - c T_n - E`,
    and Eqs. 13-14 restate it under "IR/IC Constraints in Period 2". This
    entry's own `notes` field records the transcription as "the PERIOD-2
    static myopic IC/IR only".

    An earlier Task 11-pre attempt stripped the `(\theta_k^1)` call args as
    a menu-indexation tag, which made the entry parse and report VERIFIED --
    but on `theta_i^2 R_i^2 - c T_i^2 >= theta_i^2 R_j^2 - c T_j^2`, a
    different obligation from the paper's linear one. That widening was
    reverted; the entry must never parse to an entry-specific verdict.

    R3a Task 12 then diagnosed the entry MANUAL: the recorded IC/IR is the
    period-2 static myopic slice only, so even a correct parse would not
    certify the paper's two-period intertemporal contract. MANUAL is the
    fail-closed outcome the earlier VERIFIED_TEMPLATE was standing in for --
    what this test guards is that the entry never becomes entry-specific.
    """
    r = verify(_entry("Wen2025diffusion_contract"))
    assert r.verdict == "MANUAL"
    assert r.entry_specific is False


def test_bayesian_expectation_bails_to_track4():
    r"""An `E_{c_{-k}}[...]` wrapper states an EX-ANTE constraint. Stripping
    the expectation and grid-checking pointwise would prove something
    strictly stronger than the paper claims, so the LaTeX path must decline
    and leave the entry to the Bayesian track."""
    assert _parse_contract_entry(_entry("2602_21844")) is None


def test_bayesian_bailout_does_not_catch_a_plain_symbol_named_E():
    r"""The Bayesian guard keys on `E_{...}[` / `\mathbb{E}`, so a bare
    symbol named `E` -- or an `E[...]` that is part of the paper's own
    algebra rather than a screening-wide expectation wrapper -- must still
    parse. Han2025paid_models writes `E[v(r_i)] - c_i*m_i \geq ...` and is a
    pre-existing entry-specific parse; the guard must not swallow it."""
    assert _parse_contract_entry(_entry("Han2025paid_models")) is not None
