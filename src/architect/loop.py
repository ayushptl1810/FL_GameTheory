"""CEGIS loop controller: propose -> synthesize -> render -> MC pre-filter -> verify,
with a per-verdict repair/restart policy (spec S3)."""
from __future__ import annotations
import os
import time
import types as _t

from architect.types import ProblemSpec, Feedback, ArchitectResult
from architect.serialize import render, OutsideParseableFragment
from architect.mc import mc_prefilter
from architect.inspect import inspect_mechanism, is_loop_success

REPAIR_CAP, RESTART_CAP, UNKNOWN_CAP, UNSUPPORTED_CAP = 5, 1, 2, 1


def _default_deps(index):
    from architect import rag, router, architect as arch, synthesize as syn
    return _t.SimpleNamespace(
        retrieve=lambda spec, k, index=index: rag.retrieve(spec, k, index=index),
        route=lambda spec, index=index: router.route(spec, index),
        propose=arch.propose,
        synthesize=syn.synthesize,
        make_constraints=lambda m: syn.Constraints(
            ic=m.ic, ir=m.ir, budget_lhs=None, budget_rhs=None,
            type_space=m.type_space, param_bounds={}),
        render=render, mc_prefilter=mc_prefilter,
        inspect=inspect_mechanism, is_success=is_loop_success)


def _families_tried(transcript) -> str:
    fams: list[str] = []
    for e in transcript:
        f = e.get("family")
        if f and f not in fams:
            fams.append(f)
    return ", ".join(fams) or "(none recorded)"


def run(spec: ProblemSpec, *, index=None, budget_s: float = 600.0, deps=None) -> ArchitectResult:
    deps = deps or _default_deps(index)
    t0 = time.monotonic()
    transcript: list[dict] = []
    iterations = solver_calls = 0
    repair_used = restart_used = unknown_used = unsupported_used = 0
    feedback: Feedback | None = None
    emitted_family: str | None = None

    rag_hits = deps.retrieve(spec, 5, index=index)
    mode = deps.route(spec, index)

    def _finish(status, mech_dict, latex, cert) -> ArchitectResult:
        return ArchitectResult(
            status=status, mechanism_latex=latex or "",
            mechanism_dict=mech_dict or {}, certificate=cert or [],
            mode=mode, iterations=iterations, solver_calls=solver_calls,
            wall_clock=time.monotonic() - t0, transcript=transcript,
            emitted_family=emitted_family,
            family_match=(None if emitted_family is None or not spec.expected_family
                          else emitted_family == spec.expected_family))

    def _repair(fb: Feedback) -> str:
        """Apply repair/restart accounting. Return 'fail' | 'continue'."""
        nonlocal repair_used, restart_used, feedback
        feedback = fb
        repair_used += 1
        if repair_used > REPAIR_CAP:
            if restart_used < RESTART_CAP:
                restart_used += 1
                repair_used = 0
                feedback = Feedback(kind="restart", hint=_families_tried(transcript))
                transcript.append({"iter": iterations, "note": "restart"})
                return "continue"
            return "fail"
        return "continue"

    while True:
        if time.monotonic() - t0 > budget_s:
            transcript.append({"iter": iterations, "note": "wall_clock_exceeded"})
            return _finish("FAILED", None, None, None)
        iterations += 1

        try:
            m = deps.propose(spec, mode, rag_hits, feedback)
        except Exception as exc:  # noqa: BLE001
            # A malformed / unparseable proposal is a repairable event, not a
            # hard stop: feed the exact decode error back and let the model
            # retry within the repair budget (per the plan's error table).
            transcript.append({"iter": iterations, "mode": mode,
                               "verdict": "PROPOSE_ERROR",
                               "note": f"propose_error: {exc}"})
            if _repair(Feedback(
                    kind="parse_hint",
                    hint=(f"your previous reply did not decode into a valid "
                          f"Mechanism: {exc}. Return ONLY the JSON object with "
                          f"top-level keys category, utility, payment, ic, ir "
                          f"(each of utility/payment/ic/ir an algebra node "
                          f'{{"t":...}}).'))) == "fail":
                return _finish("FAILED", None, None, None)
            continue

        if mode == "Synthesis":
            try:
                out = deps.synthesize(m, deps.make_constraints(m))
            except (ValueError, TypeError) as exc:
                out = "UNSAT"
                _syn_exc = str(exc)
            else:
                _syn_exc = None
            if out == "UNSAT":
                entry = {"iter": iterations, "mode": mode,
                         "verdict": "SYN_UNSAT", "family": m.category}
                if _syn_exc:
                    entry["note"] = f"synthesize_error: {_syn_exc}"
                transcript.append(entry)
                hint = ("no parameter values satisfy IC + IR + budget for that "
                        "template -- change the STRUCTURE (different payment "
                        "form), not just the coefficients.")
                if m.category == "Stackelberg":
                    hint = ("Stackelberg mechanisms are not solved by parameter "
                            "search. Give the follower utility with CONCRETE "
                            "numeric coefficients (no Unknown nodes) as one "
                            "closed-form polynomial, e.g. p_i*e_i - 0.5*e_i^2.")
                if _repair(Feedback(kind="reformulate", hint=hint)) == "fail":
                    return _finish("FAILED", None, None, None)
                continue
            m = out

        try:
            if os.environ.get("ARCHITECT_AST_VERIFY") == "1":
                # Verification runs on the AST directly; skip the serialize
                # round-trip parse so no LaTeX parser runs in the loop.
                mech_dict, latex = deps.render(m, check_roundtrip=False)
            else:
                mech_dict, latex = deps.render(m)   # byte-identical to pre-Task-13
        except OutsideParseableFragment as exc:
            transcript.append({"iter": iterations, "mode": mode, "verdict": "PARSE",
                               "family": m.category, "note": exc.hint})
            if _repair(Feedback(kind="parse_hint", hint=exc.hint)) == "fail":
                return _finish("FAILED", None, None, None)
            continue

        # Family fidelity (Option A): the loop is hard-constrained to the
        # eval-supplied expected_family (intake extraction is future work).
        # An off-family proposal is fed back as a
        # repairable event; it never silently reframes into another family.
        emitted_family = getattr(m, "category", None) or (mech_dict or {}).get("category")
        if spec.expected_family and emitted_family != spec.expected_family:
            fb = Feedback(kind="wrong_family",
                          hint=(f"You proposed a {emitted_family} mechanism, but "
                                f"this FL setting requires a {spec.expected_family} "
                                f"mechanism. Re-propose in the {spec.expected_family} "
                                f"family."))
            transcript.append({"iter": iterations, "family": emitted_family,
                               "hint": fb.hint})
            if _repair(fb) == "fail":
                return _finish("FAILED", None, None, None)
            continue

        # The MC pre-filter samples every symbol independently in [0.1, 1] with
        # no structural constraints. That is a sound quick check only for VCG
        # (dominant-strategy, independent private values). For Contract it needs
        # a type ordering it does not have -> spurious "violations" on valid
        # screening menus (same reason Stage 1's Z3 suppresses unordered Contract
        # counterexamples to UNKNOWN); for Stackelberg there is no IC to check.
        # So the pre-filter runs for VCG only; other families go straight to the
        # real verifier, which imposes the right assumptions.
        mc = deps.mc_prefilter(m) if m.category == "VCG" else None
        if mc is not None:
            transcript.append({"iter": iterations, "mode": mode,
                               "verdict": "MC_COUNTEREXAMPLE",
                               "family": m.category, "counterexample": mc})
            if _repair(Feedback(kind="counterexample", counterexample=mc)) == "fail":
                return _finish("FAILED", None, None, None)
            continue

        solver_calls += 1
        r = deps.inspect(m, {"paper_id": "architect-proposal",
                             "num_clients": spec.n_clients or 2})
        transcript.append({"iter": iterations, "mode": mode, "verdict": r.verdict,
                           "family": getattr(r, "category", m.category),
                           "counterexample": getattr(r, "counterexample", None)})

        if deps.is_success(r):
            return _finish("VERIFIED", mech_dict, latex, list(getattr(r, "conditions", [])))

        if r.verdict == "COUNTEREXAMPLE":
            if _repair(Feedback(kind="counterexample",
                                counterexample=getattr(r, "counterexample", None),
                                conditions=list(getattr(r, "conditions", [])))) == "fail":
                return _finish("FAILED", None, None, None)
            continue

        if r.verdict == "UNKNOWN":
            unknown_used += 1
            if unknown_used > UNKNOWN_CAP:
                return _finish("FAILED", None, None, None)
            feedback = Feedback(kind="reformulate",
                                hint="simplify the utility, keep the same family")
            continue

        if r.verdict == "UNSUPPORTED":
            unsupported_used += 1
            if unsupported_used > UNSUPPORTED_CAP:
                return _finish("FAILED", None, None, None)
            feedback = Feedback(kind="force_family",
                                hint="choose VCG, Contract, or Stackelberg")
            continue

        if r.verdict in ("VERIFIED_TEMPLATE", "VERIFIED_SHAPE"):
            # The math parsed but the verifier could only check a generic
            # template, not this specific mechanism -- usually a missing piece
            # of metadata or an FOC/IC the entry-specific parser can't isolate.
            # VERIFIED_SHAPE is weaker still (a payment-shape regex match, no
            # solver run). Both are repairable: hint and retry within the budget
            # instead of hard-failing the loop.
            transcript.append({"iter": iterations, "mode": mode,
                               "verdict": r.verdict, "family": r.category,
                               "note": getattr(r, "notes", "")})
            if r.verdict == "VERIFIED_SHAPE":
                hint = ("that is only a payment-SHAPE match, not a proof -- the "
                        "verifier ran no solver on your mechanism. The "
                        "allocation/payment must be in a form the DSIC grid "
                        "check can encode: a highest-bidder allocation "
                        r"(x_i = 1 if b_i = \max_j b_j) with the Clarke pivot "
                        r"payment p_i = \max_{j \neq i} b_j. Re-propose in that "
                        "form.")
                if _repair(Feedback(kind="reformulate", hint=hint)) == "fail":
                    return _finish("FAILED", None, None, None)
                continue
            hint = ("the verifier could only check a GENERIC TEMPLATE of your "
                    "mechanism, not the specific one -- that does not count as a "
                    "proof. Make the entry-specific check engage: for Stackelberg "
                    'include meta={"equilibrium_existence": true, '
                    '"follower_decision": "<the follower decision var, e.g. e_i>", '
                    '"num_types": <int>} and give the follower utility as one '
                    "closed-form expression; for Contract author ic as the "
                    "two-term Sum described above and set meta.num_types / "
                    "meta.type_variable; keep the algebra simple.")
            if _repair(Feedback(kind="reformulate", hint=hint)) == "fail":
                return _finish("FAILED", None, None, None)
            continue

        return _finish("FAILED", None, None, None)
