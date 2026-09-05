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
