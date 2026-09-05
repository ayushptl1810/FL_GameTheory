# R12 — Nash-Equilibrium / Action-Choice Track — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Handoff from R11 (read before starting)

**This section must be filled in by R11's Task 8 Step 3 before R12 begins.**
Until R11 lands, treat the following as placeholders to be replaced with
R11's actual findings:

- Numeric-tolerance convention actually used by R11: _(R11 fills in — expect
  `1e-6` start-point agreement / `1e-8` residual per R11's plan, confirm the
  real values landed)_.
- Verdict-metadata field name + shape actually used for a numeric flip:
  _(R11 fills in — confirm the real `corpus.json` field name, e.g.
  `z3_verdict`, rather than assuming)_.
- SciPy gotchas hit: _(R11 fills in)_.
- Post-R11 corpus counts (Stackelberg + Contract slices): _(R11 fills in)_.

R12 itself does not use SciPy (it is a finite-enumeration track, not a
numeric-optimization one), so most of the above is informational rather
than load-bearing — but Task 1's baseline snapshot should reflect the real
post-R11 corpus state, not this plan's original draft-time snapshot.

**Goal:** Build a new Track 5b — `src/tracks/track_nash.py` — that verifies
truthfulness/participation proved as a Nash-equilibrium best-response
condition over a small, finite, discrete action set (e.g. `{abstain, join,
buy}`), for mechanisms where no type-vs-type screening IC constraint exists
because the paper's truthfulness claim isn't a screening claim at all. Wire
it into the verifier and the AST path, then sweep the 10-entry
no-screening-IC family named in the R9 spec's "R10" section (renumbered R12
in this program).

**Architecture:** This is a new-track round in the mold of R5's
`track_coalition.py` — new corpus schema fields (`action_set`,
`action_payoffs`), a small standalone verifier module with no `architect.*`
import, wired into `verify_shapley`'s exact wiring *pattern* (not the same
function — a new `verify_nash_action_choice` gets its own dispatch entry).
The check is genuinely simple once the data exists: for every player and
every action, is the stated/observed action a best response — i.e. does no
other action in the finite set give that player strictly higher payoff,
holding others' actions fixed? This is finite enumeration (like
`track_coalition.py`'s Tier B core/IR check over `2^k` coalitions), not
numeric optimization, so it reuses none of R11's SciPy work directly but
should reuse R11's tolerance-and-metadata *conventions* per the handoff
above for consistency across the program's `VERIFIED` semantics.

**First, confirm the 10-entry family's real category is what R9 diagnosed.**
R9's audit found the `no-follower-IR-stated` family had a mismatched cause
in at least one sampled entry (`1811_12082`) — the same open-ended-tracing
discipline applies here: Task 2 re-traces all 10 named entries
(`2408_13223`, `2505_02462`, `2505_05842`, `2605_02935`,
`Bornstein2023realistic_incentive`, `Huang2024aigc`,
`Karimireddy2022data_sharing`, `Li2026network`, `Zhang2020fedserving`,
`Zhao2023truthful`) against the *current* code (post-R11) before assuming
all 10 are still a clean fit — some may have shifted, or may turn out to be
peer-prediction/BNE shapes the finite-action-Nash check genuinely can't
represent either (the R9 spec itself distinguishes "Nash-equilibrium over a
small discrete action set" from "Bayesian persuasion feasibility" and "peer-
prediction BNE" as three distinct shapes bundled under one family name —
only the first is this round's target; the other two stay `MANUAL` with a
corrected, more specific obstruction).

**Tech Stack:** Python 3.14, pure Python (no SymPy/Z3/SciPy needed — finite
enumeration over an explicit action set and payoff table). Tests: pytest,
`PYTHONPATH=src:.`. Verifier/gate: `PYTHONPATH=src`.

**Spec:** `docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`
(§R12), and `docs/superpowers/specs/2026-09-05-R9-manual-root-cause-audit.md`
(§"R10 — Nash-equilibrium / action-choice track", which named this round
before it was renumbered R12 in the umbrella program).

## Global Constraints

- **Monotone corpus gate.** After every task, `PYTHONPATH=src python -m
  scripts.round_gate --baseline docs/superpowers/notes/round-R12-baseline.md
  --only Contract corpus.json` must print `GATE: PASS` (the 10 entries are
  currently categorized `Contract` per R9's family listing — confirm this
  in Task 1; if any are actually a different category, gate on that
  category instead for that entry, or extend `round_gate` to accept
  multiple `--only` category filters if it doesn't already — check
  `scripts/round_gate.py`'s CLI before assuming a single `--only` covers
  mixed categories).
- **Per-round baseline.** Task 1 captures `round-R12-baseline.md`.
- **Every flip cross-checked.** Each new `VERIFIED` records in
  `docs/superpowers/notes/round-R12-new-verified.md`: entry id, the action
  set and payoff table used, the best-response check shown for every
  player/action pair, and one independent check (a hand-verified best-
  response table, or a cited game-theory equilibrium concept the paper
  itself invokes).
- **`MANUAL` always carries a reason.** Every non-flip gets a
  `manual_diagnosis` distinguishing (per the family split found in Task 2)
  Nash-over-discrete-actions-but-no-payoff-table-transcribed vs.
  peer-prediction-BNE-not-representable vs. Bayesian-persuasion-not-
  representable vs. genuinely-still-a-different-cause.
- **Formalizer is never a verify-time dependency.** `track_nash.py` has no
  `architect.*` import; `action_payoffs` is plain declared data.
- **Corpus data is declared, not inferred.** `action_set` and
  `action_payoffs` are transcribed from the source PDF with a
  `*_source` sibling note, exactly like `track_coalition.py`'s
  `coalition_values_source` precedent. An action set or payoff not stated
  in the PDF is left absent and the entry stays `MANUAL`.
- **Fail closed.** Any action whose payoff isn't stated for every other
  player's fixed action, any equilibrium concept that isn't literally
  "no profitable unilateral deviation" (e.g. a mixed-strategy equilibrium
  the module doesn't handle, or a correlated equilibrium), or any ambiguity
  — `MANUAL`, never a guessed `VERIFIED`.
- **No branch for this round** (program-level deviation, per the umbrella
  spec) — work lands directly on the current tree.
- **Plan handoff (this round's mandate):** Task 8 of this plan updates
  `docs/superpowers/plans/2026-09-05-R13-transcendental-rootfinding.md`
  with whatever R12 discovered — corrected family membership from Task 2,
  the real post-R12 corpus counts, and any wiring-pattern lesson from
  building a second track-registration (after R5's coalition track) that
  R13 should know about (R13 modifies existing tracks rather than adding a
  new one, so this is lower-stakes than R11→R12's handoff, but still do it
  and note explicitly if there is nothing R13 needs).

---

## File Structure

**Solver code (new file):**
- `src/tracks/track_nash.py` — `verify_nash_action_choice(entry: dict) ->
  VerificationResult`; helpers `_parse_action_payoffs`,
  `_is_best_response`, `_check_all_best_responses`. Modeled directly on
  `src/tracks/track_coalition.py`'s shape (fail-closed default, no
  `architect.*` import, `VerificationResult` fields: `verdict`, `category`,
  `paper_id`, `track`, `conditions: list[str]`, `notes: str`,
  `entry_specific: bool`).

**Wiring:**
- `src/verifier.py` — add a dispatch entry for the category this track
  handles. Confirm at Task 1 whether the 10 entries are tagged `category:
  "Contract"` (per R9's listing, most likely, since they were found inside
  the Contract MANUAL cluster) or need a new category tag
  (`"NashActionChoice"`) — **do not invent a new top-level category unless
  the existing `Contract` dispatch cannot be extended to check for
  `action_set` before falling through to the screening-IC path**; prefer
  extending the existing Contract dispatch function to try
  `verify_nash_action_choice` first when `mechanism.action_set` is present,
  falling through to the normal Contract IC/IR path otherwise, to avoid a
  corpus-wide category-rename that R9 didn't ask for.
- `src/architect/ast_verify.py` — analogous branch to the Shapley one
  (`_classify_ast` line 60-61, `verify_from_ast` line 328-330): if the
  mechanism's `meta` carries `action_set`, route to
  `verify_nash_action_choice` before the existing category-based
  classification, mirroring the Shapley pattern exactly (confirmed pattern:
  a local `from tracks.track_nash import verify_nash_action_choice` import
  inside the branch, avoiding an import cycle, exactly like the
  `track_coalition` import in `ast_verify.py:329`).

**Corpus data (transcribed from PDFs):**
- `corpus.json` — Task 3 (re-trace, correct family membership) may relabel
  some of the 10; Task 5: `action_set` + `action_payoffs` +
  `action_payoffs_source` for whichever entries the PDF supports.

**Notes:**
- `docs/superpowers/notes/round-R12-baseline.md` (Task 1)
- `docs/superpowers/notes/round-R12-root-cause-recheck.md` (Task 2 — the
  re-trace of all 10 entries against current code, R9-audit-style)
- `docs/superpowers/notes/round-R12-new-verified.md` (Task 6)
- `docs/superpowers/notes/round-R12-delta.md` (Task 8)
- `docs/superpowers/notes/MANUAL-backlog.md` (appended)

**Tests:**
- `tests/tracks/test_nash_equilibrium.py` (Tasks 3-4, following the
  `test_coalition.py` naming/shape convention confirmed at plan time)

---

## Task 1: Baseline snapshot (post-R11 state)

**Files:**
- Create: `docs/superpowers/notes/round-R12-baseline.md`

**Interfaces:**
- Consumes: `scripts.snapshot_verdicts.main`, `scripts.round_gate.main`.
- Produces: the per-entry verdict table every later task's gate runs
  against, captured AFTER R11 has landed (fill in the "Handoff from R11"
  section above first).

- [ ] **Step 1: Capture the baseline**

```bash
PYTHONPATH=src python -m scripts.snapshot_verdicts corpus.json --out docs/superpowers/notes/round-R12-baseline.md
```

- [ ] **Step 2: Confirm the 10 target entries' current category and verdict**

```bash
PYTHONPATH=src python3 -c "
import json
d = json.load(open('corpus.json'))
entries = d if isinstance(d, list) else d.get('entries', d)
by_id = {e.get('paper_id'): e for e in entries}
targets = ['2408_13223','2505_02462','2505_05842','2605_02935',
           'Bornstein2023realistic_incentive','Huang2024aigc',
           'Karimireddy2022data_sharing','Li2026network',
           'Zhang2020fedserving','Zhao2023truthful']
for t in targets:
    e = by_id.get(t)
    if not e:
        print(t, 'NOT FOUND'); continue
    print(t, '| category:', e.get('category'), '| verdict_override:', e.get('verdict_override'))
"
```

Record the actual categories printed — this determines which
`scripts.round_gate --only <category>` invocation gates this round (do not
assume `Contract` without checking).

- [ ] **Step 3: Gate no-op check against whatever category(ies) Step 2 found**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R12-baseline.md --only <category-from-step-2> corpus.json
```

Expected: `GATE: PASS`.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/notes/round-R12-baseline.md
git commit -m "chore(R12): baseline snapshot"
```

---

## Task 2: Re-trace all 10 entries against current code — correct family membership

**Files:**
- Create: `docs/superpowers/notes/round-R12-root-cause-recheck.md`

**Interfaces:**
- Consumes: the entry's stored `mechanism` dict, `client_utility_latex`,
  `ir_participation_latex`, `ic_screening_latex` (expected null per R9),
  and the entry's source PDF.
- Produces: one row per entry — `paper_id`, R9's original classification
  (Nash-over-discrete-actions / peer-prediction BNE / Bayesian persuasion —
  the three shapes R9's own spec text distinguishes), a re-derived
  classification from actually reading the PDF's truthfulness proof, and a
  match/mismatch verdict — same discipline as R9's own root-cause audit.

- [ ] **Step 1: For each of the 10 entries, read the PDF's actual truthfulness/equilibrium proof**

For each entry, find the specific theorem/section that proves the
mechanism's incentive property, and classify it as exactly one of:
(a) **Nash-over-discrete-actions** — a finite action set per player
(`{abstain, join, buy}`-shaped), proved via "no profitable unilateral
deviation" over that set — **this round's real target**;
(b) **Peer-prediction / Bayesian-truthful-scoring (BTS)** — truthfulness
proved via a proper scoring rule over reported *signals*, not a finite
action choice — a genuinely different check (out of R12's scope, needs its
own track some future round);
(c) **Bayesian persuasion / information design** — the mechanism's
"truthfulness" is actually about signal/recommendation design, not a
player's action choice at all — also out of scope;
(d) **something else** — R9's family label was simply wrong for this entry;
re-diagnose fresh.

- [ ] **Step 2: Write `round-R12-root-cause-recheck.md`**

One row per entry:

```markdown
| paper_id | R9 family label | re-derived shape (a/b/c/d) | match? | notes |
|---|---|---|---|---|
| 2408_13223 | no-screening-IC / Nash-action | <a/b/c/d> | <yes/no> | <one line> |
| ... | | | | |
```

- [ ] **Step 3: Partition the 10 into "R12 targets" (shape a) and "not this round" (shapes b/c/d)**

Only shape-(a) entries proceed to Task 5's transcription attempt. Every
shape-(b)/(c)/(d) entry gets a corrected `manual_diagnosis` in Task 7
naming its real shape and why `verify_nash_action_choice` (a finite
best-response check) cannot represent it — this is exactly the R9-style
"correct the catalogue" work the umbrella program's motivation calls for.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/notes/round-R12-root-cause-recheck.md
git commit -m "docs(R12): re-trace 10 no-screening-IC entries, partition by real equilibrium shape"
```

---

## Task 3: `track_nash.py` skeleton + `_parse_action_payoffs`

**Files:**
- Create: `src/tracks/track_nash.py`
- Test: `tests/tracks/test_nash_equilibrium.py`

**Interfaces:**
- Consumes: `tracks.VerificationResult` (same dataclass `track_coalition.py`
  uses — confirm the exact import path, `from tracks import
  VerificationResult`, matches what was found by grepping `track_coalition.py`
  at plan time).
- Produces: `_parse_action_payoffs(raw: dict, players: list[str], actions:
  list[str]) -> dict[tuple[str, tuple[str, ...]], float]` — `raw` maps a
  canonical joint-action-profile key (e.g. `"player1=join,player2=abstain"`)
  to each player's payoff at that profile; returns a map keyed by
  `(player, full_action_profile_tuple) -> payoff`. Raises `ValueError` if
  any of the `len(actions) ** len(players)` joint profiles is missing a
  payoff for any player.

- [ ] **Step 1: Write the failing tests**

```python
# tests/tracks/test_nash_equilibrium.py
import pytest
from tracks.track_nash import _parse_action_payoffs


def test_parse_action_payoffs_builds_full_map():
    raw = {
        "p1=join,p2=join": {"p1": 3.0, "p2": 3.0},
        "p1=join,p2=abstain": {"p1": 1.0, "p2": 0.0},
        "p1=abstain,p2=join": {"p1": 0.0, "p2": 1.0},
        "p1=abstain,p2=abstain": {"p1": 0.0, "p2": 0.0},
    }
    got = _parse_action_payoffs(raw, players=["p1", "p2"], actions=["join", "abstain"])
    assert got[("p1", ("join", "join"))] == 3.0
    assert got[("p2", ("join", "abstain"))] == 0.0


def test_parse_action_payoffs_missing_profile_raises():
    raw = {"p1=join,p2=join": {"p1": 3.0, "p2": 3.0}}  # 3 of 4 profiles missing
    with pytest.raises(ValueError, match="missing"):
        _parse_action_payoffs(raw, players=["p1", "p2"], actions=["join", "abstain"])


def test_parse_action_payoffs_missing_player_payoff_raises():
    raw = {
        "p1=join,p2=join": {"p1": 3.0},  # p2's payoff missing at this profile
        "p1=join,p2=abstain": {"p1": 1.0, "p2": 0.0},
        "p1=abstain,p2=join": {"p1": 0.0, "p2": 1.0},
        "p1=abstain,p2=abstain": {"p1": 0.0, "p2": 0.0},
    }
    with pytest.raises(ValueError, match="missing"):
        _parse_action_payoffs(raw, players=["p1", "p2"], actions=["join", "abstain"])
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_nash_equilibrium.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write the minimal implementation**

```python
# src/tracks/track_nash.py
"""Track 5b -- Nash-equilibrium / action-choice verification.

Verifies truthfulness/participation proved as a best-response condition
over a small, finite, discrete action set (e.g. {abstain, join, buy}),
for mechanisms where no type-vs-type screening IC exists because the
truthfulness claim is a Nash-equilibrium claim, not a menu-substitution
screening claim.

Fail-closed default: not decidable. No architect/LLM imports.
"""
from __future__ import annotations

from itertools import product

from tracks import VerificationResult


def _parse_action_payoffs(
    raw: dict, players: list, actions: list
) -> dict[tuple[str, tuple], float]:
    """raw maps a joint-action-profile key ("p1=a,p2=b,...") to a
    {player: payoff} dict at that profile. Returns a map keyed by
    (player, full_profile_tuple_in_players_order) -> payoff for every
    player at every one of len(actions)**len(players) profiles.
    Raises ValueError if any profile or any player's payoff at a profile
    is missing -- fail closed, no guessed payoff.
    """
    parsed: dict[tuple[str, tuple], float] = {}
    all_profiles = list(product(actions, repeat=len(players)))
    for profile in all_profiles:
        key = ",".join(f"{p}={a}" for p, a in zip(players, profile))
        entry = raw.get(key)
        if not isinstance(entry, dict):
            raise ValueError(f"action_payoffs missing profile {key!r}")
        for p in players:
            if p not in entry:
                raise ValueError(
                    f"action_payoffs profile {key!r} missing payoff for player {p!r}"
                )
            parsed[(p, profile)] = float(entry[p])
    return parsed
```

- [ ] **Step 4: Run to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_nash_equilibrium.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/tracks/track_nash.py tests/tracks/test_nash_equilibrium.py
git commit -m "feat(R12): track_nash -- action-payoff parsing"
```

---

## Task 4: `_is_best_response` + `_check_all_best_responses` + `verify_nash_action_choice`

**Files:**
- Modify: `src/tracks/track_nash.py`
- Test: `tests/tracks/test_nash_equilibrium.py`

**Interfaces:**
- Consumes: `_parse_action_payoffs` (Task 3).
- Produces:
  - `_is_best_response(payoffs: dict, players: list, profile: tuple,
    actions: list, player: str) -> bool` — true iff no unilateral deviation
    by `player` (holding all others' actions in `profile` fixed) strictly
    increases `player`'s payoff.
  - `_check_all_best_responses(payoffs: dict, players: list, actions: list,
    stated_profile: tuple) -> tuple[bool, list[str]]` — checks
    `_is_best_response` for every player at the one `stated_profile` (the
    profile the paper claims is the equilibrium), returns `(all_ok,
    conditions)`.
  - `verify_nash_action_choice(entry: dict) -> VerificationResult` — reads
    `mechanism.action_set` (list of action names, shared across players),
    `mechanism.players` (list of player names), `mechanism.action_payoffs`
    (raw dict per `_parse_action_payoffs`),
    `mechanism.stated_equilibrium_profile` (the joint action profile the
    paper claims is the equilibrium, e.g. `{"p1": "join", "p2": "join"}`).
    Missing any of these -> `MANUAL`. Parse failure
    (`_parse_action_payoffs` raises) -> `MANUAL` with the `ValueError`
    message. All best-response checks hold -> `VERIFIED`
    (`entry_specific=True`). Any player with a profitable deviation ->
    `COUNTEREXAMPLE` naming the deviation.

- [ ] **Step 1: Confirm the track number is not already used**

```bash
grep -n "track=5\|track: 5\|\"track\": 5" src/tracks/track_coalition.py
```

`track_coalition.py` uses `track=5` (confirmed by R5's plan/design docs).
This new module therefore uses `track=6` throughout Task 4 below.

- [ ] **Step 2: Write the failing tests**

```python
# tests/tracks/test_nash_equilibrium.py -- append
from tracks.track_nash import (
    _is_best_response, _check_all_best_responses, verify_nash_action_choice,
)

_SIMPLE_PAYOFFS_RAW = {
    "p1=join,p2=join": {"p1": 3.0, "p2": 3.0},
    "p1=join,p2=abstain": {"p1": 1.0, "p2": 0.0},
    "p1=abstain,p2=join": {"p1": 0.0, "p2": 1.0},
    "p1=abstain,p2=abstain": {"p1": 0.0, "p2": 0.0},
}


def test_is_best_response_true_at_mutual_join():
    from tracks.track_nash import _parse_action_payoffs
    payoffs = _parse_action_payoffs(_SIMPLE_PAYOFFS_RAW, ["p1", "p2"], ["join", "abstain"])
    assert _is_best_response(payoffs, ["p1", "p2"], ("join", "join"), ["join", "abstain"], "p1")
    assert _is_best_response(payoffs, ["p1", "p2"], ("join", "join"), ["join", "abstain"], "p2")


def test_is_best_response_false_when_deviation_profitable():
    from tracks.track_nash import _parse_action_payoffs
    payoffs = _parse_action_payoffs(_SIMPLE_PAYOFFS_RAW, ["p1", "p2"], ["join", "abstain"])
    # at (join, abstain), p2 deviating to join raises p2's payoff 0 -> 3: profitable.
    assert not _is_best_response(
        payoffs, ["p1", "p2"], ("join", "abstain"), ["join", "abstain"], "p2"
    )


def test_verify_nash_action_choice_full_pass():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "action_set": ["join", "abstain"],
            "players": ["p1", "p2"],
            "action_payoffs": _SIMPLE_PAYOFFS_RAW,
            "stated_equilibrium_profile": {"p1": "join", "p2": "join"},
        },
    }
    r = verify_nash_action_choice(entry)
    assert r.verdict == "VERIFIED"
    assert r.entry_specific is True
    assert r.track == 6


def test_verify_nash_action_choice_counterexample_on_profitable_deviation():
    entry = {
        "paper_id": "x",
        "mechanism": {
            "action_set": ["join", "abstain"],
            "players": ["p1", "p2"],
            "action_payoffs": _SIMPLE_PAYOFFS_RAW,
            "stated_equilibrium_profile": {"p1": "join", "p2": "abstain"},  # not an eq.
        },
    }
    r = verify_nash_action_choice(entry)
    assert r.verdict == "COUNTEREXAMPLE"


def test_verify_nash_action_choice_missing_fields_is_manual():
    entry = {"paper_id": "x", "mechanism": {}}
    r = verify_nash_action_choice(entry)
    assert r.verdict == "MANUAL"
```

- [ ] **Step 3: Run to verify it fails**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_nash_equilibrium.py -k "best_response or verify_nash" -v`
Expected: FAIL — functions undefined.

- [ ] **Step 4: Implement**

```python
# append to src/tracks/track_nash.py

def _is_best_response(
    payoffs: dict, players: list, profile: tuple, actions: list, player: str
) -> bool:
    idx = players.index(player)
    current = payoffs[(player, profile)]
    for alt_action in actions:
        alt_profile = tuple(
            alt_action if i == idx else a for i, a in enumerate(profile)
        )
        if payoffs[(player, alt_profile)] > current:
            return False
    return True


def _check_all_best_responses(
    payoffs: dict, players: list, actions: list, stated_profile: tuple
) -> tuple[bool, list]:
    conditions = []
    all_ok = True
    for player in players:
        ok = _is_best_response(payoffs, players, stated_profile, actions, player)
        all_ok &= ok
        conditions.append(
            f"best-response check for {player} at profile {stated_profile}: "
            f"{'ok (no profitable deviation)' if ok else 'VIOLATED (a deviation strictly improves payoff)'}"
        )
    return all_ok, conditions


def _manual(pid: str, note: str) -> VerificationResult:
    return VerificationResult(
        verdict="MANUAL", category="Contract", paper_id=pid, track=6,
        notes=note, entry_specific=False,
    )


def verify_nash_action_choice(entry: dict) -> VerificationResult:
    pid = entry.get("paper_id", "<unknown>")
    m = entry.get("mechanism") or {}

    actions = m.get("action_set")
    players = m.get("players")
    raw_payoffs = m.get("action_payoffs")
    stated = m.get("stated_equilibrium_profile")

    if not isinstance(actions, list) or not actions:
        return _manual(pid, "no action_set stated -- cannot check a finite-action Nash equilibrium")
    if not isinstance(players, list) or not players:
        return _manual(pid, "no players list stated")
    if not isinstance(raw_payoffs, dict) or not raw_payoffs:
        return _manual(pid, "no action_payoffs transcribed -- Nash-shape confirmed but nothing to check")
    if not isinstance(stated, dict) or set(stated) != set(players):
        return _manual(pid, "no stated_equilibrium_profile naming every player's claimed action")

    try:
        payoffs = _parse_action_payoffs(raw_payoffs, players, actions)
    except ValueError as e:
        return _manual(pid, f"action_payoffs unusable: {e}")

    profile = tuple(stated[p] for p in players)
    all_ok, conditions = _check_all_best_responses(payoffs, players, actions, profile)

    if all_ok:
        return VerificationResult(
            verdict="VERIFIED", category="Contract", paper_id=pid, track=6,
            conditions=conditions, entry_specific=True,
            notes="every player's stated action is a best response over the finite action set (no profitable unilateral deviation)",
        )
    violated = [c for c in conditions if "VIOLATED" in c]
    return VerificationResult(
        verdict="COUNTEREXAMPLE", category="Contract", paper_id=pid, track=6,
        conditions=conditions, entry_specific=True,
        notes="stated equilibrium profile is not a Nash equilibrium: " + "; ".join(violated),
    )
```

- [ ] **Step 5: Run to verify it passes**

Run: `PYTHONPATH=src:. pytest tests/tracks/test_nash_equilibrium.py -v`
Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/tracks/track_nash.py tests/tracks/test_nash_equilibrium.py
git commit -m "feat(R12): best-response check + verify_nash_action_choice entry point"
```

---

## Task 5: Wire into the Contract dispatch path + AST path; transcribe corpus data

**Files:**
- Modify: `src/verifier.py` — the Contract dispatch function, to try
  `verify_nash_action_choice` first when `mechanism.action_set` is present
  (grep the existing `"Contract":` dispatch entry — same investigation
  style as R5 Task 5's `verify_shapley` edit — before writing this step,
  confirm the exact function name and line).
- Modify: `src/architect/ast_verify.py` — add a branch before the existing
  category-based `_classify_ast` fallthrough: `if m.meta.get("action_set"):
  from tracks.track_nash import verify_nash_action_choice; return
  verify_nash_action_choice({"mechanism": meta, "paper_id": pid})`.
- Modify: `corpus.json` — `action_set`, `players`, `action_payoffs`,
  `stated_equilibrium_profile`, `action_payoffs_source` for whichever of
  the shape-(a) entries (from Task 2's partition) have a concrete payoff
  table in their PDF.
- Test: `tests/tracks/test_nash_equilibrium.py` (wiring test)

**Interfaces:**
- Consumes: `verify_nash_action_choice` (Task 4).
- Produces: the Contract dispatch path tries the Nash-action check before
  its normal screening-IC path when `action_set` is present; the AST path
  routes analogously.

- [ ] **Step 1: Investigate the exact Contract dispatch site**

```bash
grep -n "\"Contract\"" src/verifier.py
```

Read the surrounding function to confirm its exact name and how it's
called, before writing the edit in Step 3.

- [ ] **Step 2: Write the failing wiring test**

```python
# tests/tracks/test_nash_equilibrium.py -- append
_ACTION_PAYOFFS_FOR_WIRING_TEST = {
    "p1=join,p2=join": {"p1": 3.0, "p2": 3.0},
    "p1=join,p2=abstain": {"p1": 1.0, "p2": 0.0},
    "p1=abstain,p2=join": {"p1": 0.0, "p2": 1.0},
    "p1=abstain,p2=abstain": {"p1": 0.0, "p2": 0.0},
}


def test_contract_dispatch_tries_nash_first_when_action_set_present():
    # Import path depends on Step 1's finding -- placeholder function name
    # `dispatch_contract` below must be replaced with the real one found
    # at Step 1 before this test can run.
    from verifier import dispatch_contract  # <- confirm real name at Step 1
    entry = {
        "paper_id": "x", "category": "Contract",
        "mechanism": {
            "action_set": ["join", "abstain"], "players": ["p1", "p2"],
            "action_payoffs": _ACTION_PAYOFFS_FOR_WIRING_TEST,
            "stated_equilibrium_profile": {"p1": "join", "p2": "join"},
        },
    }
    r = dispatch_contract(entry)
    assert r.verdict == "VERIFIED"
    assert r.track == 6
```

- [ ] **Step 3: Run, verify it fails, then wire the real dispatch**

Run the test, confirm failure (either the import name is wrong — fix it
against Step 1's real finding — or the dispatch doesn't yet try
`verify_nash_action_choice`). Add, at the top of the real Contract dispatch
function found in Step 1:

```python
    if (entry.get("mechanism") or {}).get("action_set"):
        from tracks.track_nash import verify_nash_action_choice
        r = verify_nash_action_choice(entry)
        if r.verdict in ("VERIFIED", "COUNTEREXAMPLE"):
            return r
        # else fall through to the existing screening-IC Contract path
```

- [ ] **Step 4: Wire the AST path**

In `src/architect/ast_verify.py`, before the existing `_classify_ast`-driven
dispatch in `verify_from_ast` (near the Shapley branch at line ~328), add:

```python
    if (meta or {}).get("action_set"):
        from tracks.track_nash import verify_nash_action_choice
        return verify_nash_action_choice({"mechanism": meta, "paper_id": pid})
```

- [ ] **Step 5: Run the wiring test + full existing suites**

```bash
PYTHONPATH=src:. pytest tests/tracks/test_nash_equilibrium.py tests/verifier/ tests/architect/ -q
```

Expected: PASS. No existing entry has `action_set` yet, so no other verdict
moves.

- [ ] **Step 6: Transcribe `action_set`/`action_payoffs` for the shape-(a) entries from Task 2**

For each entry Task 2 classified as shape-(a) (Nash-over-discrete-actions),
open its PDF and look for a **concrete, finite payoff table or explicit
payoff functions over a stated small action set**. If found:

```json
"action_set": ["abstain", "join", "buy"],
"players": ["client_1", "client_2"],
"action_payoffs": {"client_1=join,client_2=join": {"client_1": 2.1, "client_2": 2.1}, "...": "..."},
"stated_equilibrium_profile": {"client_1": "join", "client_2": "join"},
"action_payoffs_source": "<paper>, Table N / Sec. X worked example"
```

If the paper proves the Nash-equilibrium claim analytically (an inequality
over parametrized payoffs) rather than with a concrete numeric instance,
this module's finite-enumeration check cannot verify it either — leave the
fields absent; the entry stays `MANUAL` via the "Nash-shape confirmed but
nothing to check" path (mirrors `track_coalition.py`'s Tier-A-only MANUAL).

- [ ] **Step 7: Gate + suite + commit**

```bash
PYTHONPATH=src python -m verifier corpus.json | tail -5
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R12-baseline.md --only Contract corpus.json
PYTHONPATH=src:. pytest -q
```

```bash
git add src/verifier.py src/architect/ast_verify.py corpus.json tests/
git commit -m "feat(R12): wire verify_nash_action_choice into Contract dispatch + AST path; transcribe action_payoffs"
```

---

## Task 6: Sweep, hand-check every flip

**Files:**
- Create: `docs/superpowers/notes/round-R12-new-verified.md`

**Interfaces:**
- Consumes: the deterministic verifier output.
- Produces: hand-checked cross-validation for every flip.

- [ ] **Step 1: Run the verifier, read the shape-(a) entries' verdicts**

```bash
PYTHONPATH=src python -m verifier corpus.json 2>/dev/null | grep -A3 -iE "<shape-a paper_ids from Task 2>"
```

- [ ] **Step 2: Hand-check every `VERIFIED` and `COUNTEREXAMPLE`**

For each flip, by hand build the full payoff table from the transcribed
`action_payoffs`, and for the stated equilibrium profile, check every
player's alternative actions against their current payoff — this is
exactly what `_check_all_best_responses` does, but done independently (by
reading the JSON and computing by hand or with a fresh throwaway script,
not by re-calling the same function). Append to
`round-R12-new-verified.md`:

```markdown
## <paper_id> — R12

**What R12 now handles:** finite-action Nash-equilibrium best-response
check over action_set=<...>, players=<...>.

**Independent check (hand-derived):**
- payoff table: <full table>
- stated profile: <profile>
- for each player, every alternative action's payoff <= current payoff: <shown>
```

If a hand-check disagrees, revert to `MANUAL` and record why.

- [ ] **Step 3: Gate + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R12-baseline.md --only Contract corpus.json
```

```bash
git add docs/superpowers/notes/round-R12-new-verified.md
git commit -m "feat(R12): sweep + hand-check Nash-action-choice flips"
```

---

## Task 7: Corrected diagnoses for every non-flip (including shape b/c/d entries)

**Files:**
- Modify: `corpus.json` (`manual_diagnosis` for every entry among the 10
  that is not `VERIFIED`), `docs/superpowers/notes/MANUAL-backlog.md`

**Interfaces:**
- Consumes: Task 2's shape partition.
- Produces: a corrected, shape-specific `manual_diagnosis` for every
  non-flip — this is the direct R9-motivated fix (stale/generic
  "no-screening-IC" text replaced with the real, specific reason).

- [ ] **Step 1: For shape-(a) entries with no transcribable payoff table**

```json
"manual_diagnosis": {
  "round": "R12",
  "track": 6,
  "limit": "Nash-equilibrium shape confirmed but no concrete numeric action-payoff table in the paper",
  "mechanism": "<one line>",
  "obstruction": "The paper proves the stated profile is a best response via a parametrized inequality, not a concrete payoff table over a finite small action set -- verify_nash_action_choice's finite-enumeration check has nothing to enumerate over.",
  "human_task": "instantiate concrete numeric parameters and compute each player's payoff at every joint action profile, or verify the parametrized inequality analytically.",
  "date": "2026-09-05"
}
```

- [ ] **Step 2: For shape-(b)/(c)/(d) entries**

Write a `manual_diagnosis` naming the real shape from Task 2 (peer-
prediction/BTS, Bayesian persuasion, or the specific "something else" found)
— this replaces the generic "no-screening-IC" label R9 inherited, with the
program's own corrected, specific obstruction.

- [ ] **Step 3: Append MANUAL-backlog.md paragraphs**

Follow the existing format for every entry touched in Steps 1-2.

- [ ] **Step 4: Gate + suite + commit**

```bash
PYTHONPATH=src python -m scripts.round_gate --baseline docs/superpowers/notes/round-R12-baseline.md --only Contract corpus.json
PYTHONPATH=src:. pytest -q
```

```bash
git add corpus.json docs/superpowers/notes/MANUAL-backlog.md
git commit -m "feat(R12): corrected shape-specific diagnoses for all 10 no-screening-IC entries"
```

---

## Task 8: Delta doc, spec update, and mandatory handoff to R13's plan

**Files:**
- Create: `docs/superpowers/notes/round-R12-delta.md`
- Modify: `docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md`
- Modify: `docs/superpowers/plans/2026-09-05-R13-transcendental-rootfinding.md`
  (**required** — see Step 3)

- [ ] **Step 1: Write `round-R12-delta.md`**

Mirror R5's delta doc shape: before/after table for the 10 targeted
entries, what shipped (`track_nash.py`, the shape-(a)/(b)/(c)/(d)
partition), flip count with cross-checks, corrected-diagnosis list.

- [ ] **Step 2: Add the "Landed" paragraph to the umbrella spec**

Under R12's description in the umbrella spec, append a "Landed" paragraph
following the same style as R11's (and R2-R9's) — actual counts, the
shape-partition finding, confirmation that `track=6` was used (since
`track_coalition.py` already claims `track=5`), merge status (none — no
branch this program).

- [ ] **Step 3: Update R13's plan with R12's actual findings (mandatory handoff)**

Open `docs/superpowers/plans/2026-09-05-R13-transcendental-rootfinding.md`
and add a `## Handoff from R12 (read before starting)` subsection near the
top containing:

- Confirmation that `track_nash.py` used `track=6` (R13 doesn't add a new
  track, but should know the numbering convention for any verdict metadata
  it writes).
- The corrected post-R12 corpus counts for the Contract slice (and any
  other category R12 touched).
- Any lesson from wiring a second track into the Contract dispatch
  function (Task 5) that's relevant to R13's own dispatch-site edits (R13
  extends `_sp_to_z3`'s transcendental rejection point directly rather than
  adding a new track, so the wiring shape differs — note this difference
  explicitly rather than assuming R13 can copy R12's wiring pattern).
- Confirmation of whether any of R12's shape-(b)/(c)/(d) reclassified
  entries turned out to actually be transcendental-equation cases R13
  should also target (cross-check R12's Task 2 recheck against R13's
  target list before R13 starts, in case of overlap).

Do this step even if R12 reclaimed 0 entries.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/notes/round-R12-delta.md \
        docs/superpowers/specs/2026-09-05-R11-R13-solver-capability-expansion-design.md \
        docs/superpowers/plans/2026-09-05-R13-transcendental-rootfinding.md
git commit -m "docs(R12): delta note, spec landed paragraph, handoff to R13's plan"
```

---

## Self-Review

**1. Spec coverage:** §R12 "new track, Nash-equilibrium over a discrete
action set, 10 target entries" — Tasks 3-4 (track), Task 5 (wiring +
transcription), Task 6 (sweep). The R9 spec's own three-way shape
distinction (Nash-action / peer-prediction-BNE / Bayesian-persuasion) is
made an explicit, executable step (Task 2) rather than assumed — this
directly continues R9's "don't trust the stored label, re-trace" discipline
the umbrella program is built on. Cross-round invariants (baseline,
monotone gate, cross-check, MANUAL-carries-a-reason, fail-closed,
plan-handoff) are all present as explicit tasks/steps.

**2. Placeholder scan:** the "Handoff from R11" section at the top is
explicitly marked as placeholders R11 must fill — this is a stated,
mechanical dependency, not an unaddressed gap (R11's Task 8 Step 3 exists
specifically to fill it). Task 5 Step 1-2's "confirm the real function
name" step is investigation-before-code, not a vague "figure it out" — it's
a concrete grep command with a concrete next action, and the wiring test in
Step 2 is explicit that its import name is a placeholder pending Step 1.

**3. Type consistency:** `_parse_action_payoffs(raw, players, actions) ->
dict[tuple[str, tuple], float]` (Task 3) is consumed with that exact shape
by `_is_best_response`/`_check_all_best_responses` (Task 4).
`verify_nash_action_choice(entry: dict) -> VerificationResult` matches how
Task 5 calls it from both dispatch sites. `track=6` is used consistently in
`_manual`, both `VERIFIED`/`COUNTEREXAMPLE` returns, and every test
assertion — resolved once in Task 4 Step 1 (confirmed against
`track_coalition.py`'s `track=5`) rather than left ambiguous.

**4. Ambiguity check:** "best response" is made precise (no alternative
action strictly increases payoff, holding others fixed) with a runnable
definition, not a prose gesture. The track-number choice is settled
explicitly rather than deferred to execution time.

**5. Deviation from the original umbrella-spec R12 description:** the
original spec named this round's target as "the 10-entry no-screening-IC
family" without the shape-partition step. This plan adds Task 2 as a
correctness gate before committing to building the track against
potentially-wrong assumptions about all 10 entries — consistent with the
umbrella spec's own motivation (verification IS the product; a track built
against a mis-diagnosed family would itself be an unverified claim). This
addition is noted here rather than silently expanding scope.
