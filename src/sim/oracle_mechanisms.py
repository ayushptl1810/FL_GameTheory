"""Hand-designed reward callables, one per setting, standing in for 'the closest
corpus paper' (spec comparison arm 'oracle'). Deliberately simple and open."""
from __future__ import annotations


def _cross_device_quadratic(reports, ctx):
    if not reports:
        return {}
    share = ctx.budget / len(reports)
    return {r.client_id: min(r.claimed_quality, 1.0) * share for r in reports}


def _hierarchical_edge(reports, ctx):
    if not reports:
        return {}
    by_edge: dict[int, list] = {}
    for r in reports:
        by_edge.setdefault(r.client_id // 10, []).append(r)
    edge_share = ctx.budget / len(by_edge)
    out = {}
    for members in by_edge.values():
        per = edge_share / len(members)
        for r in members:
            out[r.client_id] = per
    return out


ORACLES = {
    "cross_device_quadratic": _cross_device_quadratic,   # ref: flat quality-capped split
    "hierarchical_edge": _hierarchical_edge,             # ref: two-level per-edge uniform pricing
}
