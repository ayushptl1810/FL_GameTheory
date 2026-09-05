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


def _is_best_response(
    payoffs: dict, players: list, profile: tuple, actions: list, player: str
) -> bool:
    """True iff no unilateral deviation by `player` (holding all others'
    actions in `profile` fixed) strictly increases `player`'s payoff."""
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
    """Check `_is_best_response` for every player at the one stated
    equilibrium profile. Returns (all_ok, per-player condition strings)."""
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
    """Reads mechanism.action_set, mechanism.players,
    mechanism.action_payoffs and mechanism.stated_equilibrium_profile.
    Missing any -> MANUAL. Parse failure -> MANUAL with the ValueError
    message. All best-response checks hold -> VERIFIED (entry_specific).
    Any player with a profitable deviation -> COUNTEREXAMPLE.
    """
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
