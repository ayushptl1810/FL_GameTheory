"""Regenerate MANUAL-backlog.md from corpus.json's manual_diagnosis dicts.
Single source of truth: the corpus. Run: python scripts/build_manual_backlog.py
"""
import json, collections

c = json.load(open("corpus.json"))
rows = c if isinstance(c, list) else c.get("entries", c)
manual = [e for e in rows if e.get("verdict_override") == "MANUAL"]

FAMILIES = [
  ("no-screening-IC", lambda d: "no adverse-selection screening IC" in d["limit"]
       or "screening IC in the paper" in d["obstruction"]),
  ("vector-follower-decision", lambda d: "vector follower decision" in d["limit"]),
  ("transcendental-FOC-no-closed-form", lambda d: "transcendental" in d["limit"]
       and "closed-form" in d["limit"]),
  ("opaque-function-in-utility", lambda d: "unsupported SymPy node" in d["limit"]
       or "opaque" in d["limit"] or "undefined" in d["limit"]),
  ("RL-or-opaque-allocation", lambda d: "RL-policy" in d["limit"]
       or "opaque-algorithm allocation" in d["limit"]),
  ("no-follower-IR-stated", lambda d: "no follower IR" in d["limit"]
       or "participation constraint" in d["limit"]),
  ("coalition-value-not-instantiable", lambda d: d["track"] == 5),
  ("budget-constrained-greedy-allocation", lambda d: "budget-constrained greedy allocation" in d["limit"]),
  ("non-polynomial-gap", lambda d: "non-polynomial gap" in d["limit"]),
  ("continuous-bid-space-no-discretization", lambda d: "continuous bid space" in d["limit"]),
]
def fam(d):
    for name, pred in FAMILIES:
        try:
            if pred(d):
                return name
        except KeyError:
            pass
    return "other"

buckets = collections.defaultdict(list)
for e in manual:
    buckets[fam(e["manual_diagnosis"])].append(e)

out = ["# MANUAL Backlog", "",
       "One paragraph per corpus entry that no automated track in the pipeline can decide.",
       "Each names the mechanism, the obstruction (with the track and the specific limit hit),",
       "and the concrete human task to close it. Regenerated from corpus.json — do not hand-edit;",
       "edit the entry's manual_diagnosis and re-run scripts/build_manual_backlog.py.", "",
       f"**Total: {len(manual)} MANUAL entries.** Recurring obstruction families:", ""]
order = [n for n, _ in FAMILIES] + ["other"]
for name in order:
    ids = sorted(e["paper_id"] for e in buckets.get(name, []))
    if ids:
        out.append(f"- **{name}** ({len(ids)}): {', '.join(ids)}")
out.append("")
for name in order:
    grp = buckets.get(name, [])
    if not grp:
        continue
    out.append(f"## Family: {name}\n")
    for e in sorted(grp, key=lambda x: x["paper_id"]):
        d = e["manual_diagnosis"]
        out += [f"### {e['paper_id']} ({e.get('category','')}) — {d['round']}", "",
                f"**Mechanism:** {d['mechanism']}",
                f"**Obstruction:** {d['obstruction']} (Track {d['track']}: {d['limit']})",
                f"**Human task:** {d['human_task']}",
                f"**Diagnosed:** {d['date']}", ""]
open("docs/superpowers/notes/MANUAL-backlog.md", "w").write("\n".join(out).rstrip() + "\n")
print(f"{len(manual)} entries, "
      f"{sum(1 for k in buckets if buckets[k])} families "
      f"(other: {len(buckets.get('other', []))})")
