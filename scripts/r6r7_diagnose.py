"""R6-R7 Phase 7: flip every non-reclaimed residual VERIFIED_TEMPLATE to diagnosed MANUAL.

Each DIAG value is transcribed from the entry's `notes` (Batch-C/D/E fail-closed
review) -- Task 4's Phase-6 LLM sweep already re-checked all 25 against source
PDFs and reclaimed 0. Not invented. Run once: python scripts/r6r7_diagnose.py

track=1 for every entry: this is the corpus's existing convention -- the 57
pre-existing MANUAL entries across Contract/VCG/Stackelberg overwhelmingly use
track=1 regardless of category (grep manual_diagnosis.track in corpus.json),
so track=1 here keeps Task 6's family-grouping regex consistent with the rest
of the corpus rather than introducing a category-keyed scheme that isn't
actually used anywhere else.
"""
import json
from architect.formalize import write_manual_diagnosis, append_backlog_paragraph

DIAG = {
    "1811_12082": dict(
        track=1,
        mechanism="Leader (data requester) sets rewards/prices; follower (model owner) "
                  "chooses computing/data resource contribution s_i^d over a box domain.",
        limit="Stackelberg: no follower IR / participation constraint stated in the paper",
        obstruction="Batch-C review left ir_follower_latex null (fail-closed) -- the only "
                    "constraint on s_i^d is the box domain s_i^d in [0, s_i^{d,u}] (Sec. "
                    "III.1), a feasibility bound, not a U_follower >= 0 / outside-option IR.",
        human_task="Re-read Sec. III.1-III.2 of 1811_12082 for any implicit participation "
                   "floor tied to the outside option; if none exists in the paper, this stays "
                   "MANUAL -- Track 1's IR check has no statement to encode."),
    "2110_12876": dict(
        track=1,
        mechanism="Leader (parking-lot operator) sets reward r_j; follower (vehicle) "
                  "chooses participation rho_i^j subject to parking-capacity and budget caps.",
        limit="Stackelberg: no follower IR / participation constraint stated in the paper",
        obstruction="Batch-C review left ir_follower_latex null (fail-closed) -- the only "
                    "stated constraints are the parking-capacity cap (sum_i rho_i^j <= n^j) "
                    "and the leader-side budget cap r_j^max <= g_j; no U_i >= 0 or outside "
                    "option appears for the vehicle follower.",
        human_task="Re-read the vehicle (follower) problem statement for any implicit "
                   "U_i >= 0 condition; if none exists, transcribing one would fabricate a "
                   "constraint the paper never states, so this stays MANUAL."),
    "2203_00270": dict(
        track=1,
        mechanism="Follower's FOC/best-response derived case-by-case (tp_i^k<0 / >0 "
                  "branches) from the P3/P5 problem in Appendix A/B; leader sets prices "
                  "p_b^k, p_s^k.",
        limit="Stackelberg: no follower IR / participation constraint; case-selection logic "
              "is qualitative, not closed-form",
        obstruction="Batch-C review transcribed follower_foc_latex/best_response_latex from "
                    "Appendix A/B (verified against pp.12-13 image) but the fully optimal "
                    "e_i^{k,*} requires selecting among {e_{i,1}^{k,*}, e_{i,2}^{k,*}, "
                    "RP_i^k-D_i^k} via a 3-scenario comparison (Fig. 12/App. B) that is not "
                    "itself a closed-form expression; ir_follower_latex left null "
                    "fail-closed (no IR statement in the paper).",
        human_task="Formalize the Fig. 12/Appendix B case-selection (relative ordering of "
                   "p_s^k, p_b^k, delta_i^k) as a piecewise closed form usable by Track 1, "
                   "or confirm no IR constraint exists so this stays MANUAL."),
    "2403_09153": dict(
        track=1,
        mechanism="Contract-theoretic FL incentive design; principal offers a menu of "
                  "contracts to agents of private cost/type.",
        limit="Contract: key_assumptions list was sanitized (prompt-anchoring contamination) "
              "and single-crossing (Spence-Mirrlees) removed as unverified",
        obstruction="The 2026-07-18 sanitization pass removed 'single-crossing (Spence-"
                    "Mirrlees)' from key_assumptions because it matched the extraction-"
                    "prompt's verbatim example rather than being independently corroborated "
                    "by this entry's own formal fields, and removed 'quadratic cost' as "
                    "contradicted by the entry's own math -- Track 1's IC/IR check needs a "
                    "confirmed single-crossing assumption to run.",
        human_task="Re-read the paper's own statement of the contract-design problem to "
                   "confirm (or refute) single-crossing directly from its constraints/cost "
                   "function, then re-add it to key_assumptions only if independently "
                   "verified against the PDF text (not the extraction-prompt template)."),
    "2404_08261": dict(
        track=1,
        mechanism="Leader (server) sets a privacy-budget-linked incentive; follower "
                  "(client) chooses privacy budget epsilon_i maximizing its own utility.",
        limit="Stackelberg: no follower IR / participation constraint stated in the paper",
        obstruction="Batch-C review left ir_follower_latex null (fail-closed) -- no 's.t.' "
                    "or constraint block appears for the follower's privacy-budget "
                    "optimization problem beyond the bare utility definition itself; no "
                    "U_i >= 0 or outside-option condition is stated anywhere.",
        human_task="Re-read the client's privacy-budget optimization problem statement in "
                   "full (including any domain restrictions on epsilon_i) for an implicit "
                   "participation floor; if none exists, this stays MANUAL."),
    "2502_20882": dict(
        track=1,
        mechanism="Contract-theoretic FL incentive design between a server/platform and "
                  "clients of private type.",
        limit="Contract: notes field is empty -- no manual-review record of what is missing",
        obstruction="This entry has no `notes` explaining why it sits at VERIFIED_TEMPLATE; "
                    "the field is blank, meaning no prior Batch-C/D/E reviewer diagnosed the "
                    "specific missing formal field, so Track 1 has nothing confirmed to run "
                    "an IC/IR check against.",
        human_task="Open pdfs/2502_20882.pdf and the corpus.json formal fields for this "
                   "entry side by side; identify which of ic_screening_latex / "
                   "ir_participation_latex / server_objective_latex is null or unverified, "
                   "transcribe it from the paper's own constraint labels, and only then "
                   "attempt Track 1."),
    "2508_07676": dict(
        track=1,
        mechanism="Leader (server) sets an incentive schedule; follower (client) chooses "
                  "contribution rate rho_i(t) maximizing utility U_i-hat (Eq. 5).",
        limit="Stackelberg: no follower IR; follower FOC only described narratively, never "
              "printed as a numbered equation",
        obstruction="Batch D review left follower_foc_latex null fail-closed -- the paper's "
                    "Proof Sketch of Theorem 3 only narrates 'setting the first-order "
                    "derivative to zero' and never prints the FOC itself, even though a "
                    "reconstructed derivative does reproduce the paper's own Eq. (6) "
                    "(best_response_latex). ir_follower_latex also left null: the paper "
                    "critiques prior work's 'unconditional participation' assumption but "
                    "imposes no formal IR constraint of its own.",
        human_task="Confirm in the Proof Sketch of Theorem 3 whether the FOC is ever printed "
                   "as a standalone numbered equation anywhere else in the paper (e.g. an "
                   "appendix); if truly absent, this entry stays MANUAL since Track 1 needs "
                   "a printed FOC, not a reconstructed one."),
    "Batool2022fl_mab": dict(
        track=1,
        mechanism="VCG-style auction: platform scores/ranks bidders via a per-client scoring "
                  "function S(r_i,p_i)=alpha1 r1+alpha2 r2+alpha3 r3-p_i (Eq. 3).",
        limit="VCG: no separate platform-level objective distinct from the per-client "
              "scoring/allocation rule",
        obstruction="objective_latex left null fail-closed -- the paper only ever states the "
                    "per-client scoring function used to rank/select bidders (already "
                    "recorded as allocation_rule_latex); it never separately writes a "
                    "platform-level welfare-maximization or cost-minimization objective, "
                    "which Track 1's VCG DSIC/efficiency check requires as a distinct field.",
        human_task="Check whether the paper anywhere states an aggregate objective (e.g. "
                   "sum of S(r_i,p_i) over selected bidders, or a welfare/cost expression) "
                   "outside Eq. 3; if the scoring rule genuinely doubles as the only stated "
                   "objective, this stays MANUAL since Track 1 needs objective and "
                   "allocation rule as separate fields."),
    "Cao2025service": dict(
        track=1,
        mechanism="Leader = Task Publisher (TP); follower = Local Model Owners (LMOs) "
                  "competing via Eq. 9's unconstrained optimization problem.",
        limit="Stackelberg: no follower IR / participation constraint stated for the LMO",
        obstruction="Batch D review left ir_follower_latex null fail-closed -- the LMO's "
                    "problem (Eq. 9) has no constraints at all; Definition 1 is a "
                    "Nash-equilibrium condition among LMOs, not an IR statement. The paper's "
                    "'base participation reward' Rbase (Eq. 6) incentivizes the Worker "
                    "(a different, lower-tier actor who collects data for an LMO), not the "
                    "LMO follower itself.",
        human_task="Confirm no IR statement exists anywhere else in the paper for the LMO "
                   "(the follower already modeled in this entry, leader=TP); if Rbase truly "
                   "only applies to the Worker sub-actor, this entry stays MANUAL as there is "
                   "no follower-level IR to transcribe."),
    "Chen2023multifactor_iot": dict(
        track=1,
        mechanism="Leader sets reward Ii^t; follower (data owner) chooses effort/accuracy "
                  "contribution Acci^t under a reputation-linked reward.",
        limit="Stackelberg: no follower IR / participation constraint stated for the data "
              "owner",
        obstruction="Batch D review left ir_follower_latex null fail-closed -- no constraint "
                    "block or utility>=0 condition appears anywhere for the data owner's "
                    "optimization problem. Theorem 2 (Ii^t monotonic in reputation Ri^t and "
                    "accuracy Acci^t) is a fairness result, and Definition 7 (Optimal "
                    "Equilibrium) is the standard best-response equilibrium definition -- "
                    "neither is an IR statement.",
        human_task="Re-scan the data owner's optimization problem statement and any "
                   "footnotes/remarks for an implicit non-negativity condition; absent one, "
                   "this stays MANUAL."),
    "FLamma2025stackelberg": dict(
        track=1,
        mechanism="Adaptive gamma-based Stackelberg game between server (leader) and "
                  "clients (followers) intended to promote fairness in FL incentives.",
        limit="Stackelberg: notes give only the paper's abstract-level description, no "
              "diagnosed missing formal field",
        obstruction="This entry's notes never went through a Batch-C/D/E field-level review "
                    "-- they only restate the paper's stated purpose ('address limitations of "
                    "existing methods and promote fairness'), so no specific null field "
                    "(follower_foc_latex / ir_follower_latex / best_response_latex) has been "
                    "identified yet for Track 1 to consume.",
        human_task="Open pdfs/FLamma2025stackelberg.pdf, locate the leader/follower "
                   "optimization problems and any stated IR/FOC, and transcribe whichever "
                   "formal fields are printed; if the gamma-based mechanism lacks a follower "
                   "IR statement (as with the sibling Stackelberg entries in this batch), "
                   "record that explicitly and leave this MANUAL."),
    "Hu2020trading": dict(
        track=1,
        mechanism="Leader sets price beta_i; follower (user i) chooses contribution rho_i "
                  "maximizing utility, with a corner solution rho_i = -infty when "
                  "unprofitable (Eq. 15).",
        limit="Stackelberg: no follower IR / participation constraint stated as a formal "
              "inequality",
        obstruction="Batch E review left ir_follower_latex null fail-closed -- the paper "
                    "never states U_i >= 0 formally. It only notes informally, right after "
                    "Eq. (15), that a user sets rho_i = -infty to avoid a deficit when the "
                    "best strategy beta_i(rho_{-i}) is non-positive -- a behavioral "
                    "description of the corner solution already embedded in best_response_"
                    "latex, not a separately stated IR constraint.",
        human_task="Confirm whether the corner-solution description near Eq. (15) can be "
                   "formalized as an equivalent IR inequality without adding content beyond "
                   "what the paper states; if it cannot be done without fabricating a "
                   "constraint the paper doesn't write, this stays MANUAL."),
    "Hu2022truthful_FEL": dict(
        track=1,
        mechanism="Leader/device-side Stackelberg incentive; follower's utility U_d "
                  "(integrand H_d, Eq. 3) yields an optimal s* via an Euler-Lagrange "
                  "argument analogous to r*(s).",
        limit="Stackelberg: follower FOC never printed as a numbered equation; no follower "
              "IR/participation constraint stated",
        obstruction="Batch E review left follower_foc_latex null fail-closed -- the paper "
                    "states only that s* is derived 'using the similar method' as r*(s) and "
                    "reports the resulting second-order condition d^2Hd/ds^2 = -A_eTheta/rho "
                    "< 0 (verbatim) plus the resulting s* (already recorded as "
                    "best_response_latex), but never prints the FOC itself. ir_follower_latex "
                    "also left null: Section IV.D 'Truthfulness Analysis' proves incentive-"
                    "compatibility only, not U_d >= 0.",
        human_task="Check Section IV or any appendix for a printed first-order condition for "
                   "s* (not just the stated second-order condition); if absent, this stays "
                   "MANUAL since Track 1 needs a transcribed FOC, not a reconstruction."),
    "Javaherian2025stackelberg_ic": dict(
        track=1,
        mechanism="Leader sets gamma; follower (client i) chooses reporting/participation "
                  "level tau_i, with Definition 1 stating a formal IR constraint and Lemma 5 "
                  "proving the Nash equilibrium tau* satisfies it.",
        limit="Stackelberg: IR is stated and proven satisfied at equilibrium, but the entry "
              "still sits at VERIFIED_TEMPLATE -- likely missing a different formal field "
              "for Track 1",
        obstruction="Batch E review added ir_follower_latex, transcribed exactly from "
                    "Definition 1 (Individual Rationality), and noted Lemma 5 proves "
                    "U_i(gamma,tau_i*,tau_{-i}*) >= 0 at the client-level Nash equilibrium -- "
                    "IR is the one field this notes entry confirms is present, so the "
                    "remaining VERIFIED_TEMPLATE gap must be in another field (e.g. "
                    "follower_foc_latex or best_response_latex) not covered by this note.",
        human_task="Diff this entry's formal fields against Track 1's required-field list "
                   "to find which field besides ir_follower_latex is still null/unverified, "
                   "then transcribe it from the paper (Definition 1's surrounding section is "
                   "already confirmed correct and needs no further work)."),
    "Lee2024sfl_stackelberg": dict(
        track=1,
        mechanism="Leader (server) sets baseline S; follower (client n) chooses decision "
                  "d_n subject only to the box constraint 0 <= d_n <= D_n (Problem 13).",
        limit="Stackelberg: no follower IR / participation constraint stated in the game "
              "formulation",
        obstruction="Batch E review left ir_follower_latex null fail-closed -- no formal "
                    "U_n >= 0 constraint appears in the game formulation; the only follower "
                    "constraint is the box bound on d_n. The paper's baseline constant "
                    "S = 10^6 (Section V, footnote 5) is set purely as a plotting convenience "
                    "'to ensure U_n is greater than zero' when computing the Price-of-Anarchy "
                    "ratio (Eq. 28) -- an experimental/numerical artifact, not a declared "
                    "mechanism-design IR constraint.",
        human_task="Confirm the footnote-5 baseline S is never promoted to a formal "
                   "constraint anywhere in the main game formulation (Problem 13 or "
                   "surrounding text); if it stays purely numerical, this entry remains "
                   "MANUAL."),
    "Li2025iiot_drl": dict(
        track=1,
        mechanism="Leader sets reward; follower (IIoT node i) chooses update cycle theta_i "
                  "subject only to the feasibility bound theta_i >= theta_i^min (Problem P1, "
                  "Eq. 11).",
        limit="Stackelberg: no follower IR / participation constraint stated in the paper",
        obstruction="Batch E review left ir_follower_latex null fail-closed -- Problem P1 "
                    "imposes only the lower-bound feasibility constraint theta_i >= "
                    "theta_i^min on the update-cycle decision variable, not a utility-based "
                    "U_i >= 0 condition; no IR/participation constraint appears anywhere else "
                    "in the paper.",
        human_task="Re-check any DRL-training-loop description (Section on the DRL agent) "
                   "for an implicit participation/dropout rule that could be formalized as "
                   "IR; absent that, this entry stays MANUAL."),
    "Lim2020contract": dict(
        track=1,
        mechanism="Contract-theoretic FL incentive design where the private type is a "
                  "4-dimensional cost vector, reduced by the paper to an auxiliary "
                  "2-dimensional (y, z) type.",
        limit="Contract: genuinely multi-dimensional type (4-D cost vector -> 2-D auxiliary "
              "type) outside the verifier's single-dimension substitution machinery",
        obstruction="The corpus note flags that Track 1's single-dimension substitution "
                    "machinery may not fully capture a 4-D-reduced-to-2-D type space, so any "
                    "resulting verdict must be treated with caution -- this is a structural "
                    "mismatch between the paper's multidimensional screening model and the "
                    "verifier's current type-substitution capability, not a missing field.",
        human_task="Confirm whether the (y, z) auxiliary reduction genuinely collapses to an "
                   "equivalent single-crossing scalar type (in which case it could be "
                   "reformalized for Track 1) or is irreducibly 2-D screening (in which case "
                   "this needs a genuinely multidimensional mechanism-design proof, i.e. "
                   "stays MANUAL); read Section on the contract-type reduction to decide."),
    "Ma2023joint_pricing": dict(
        track=1,
        mechanism="Server (Stage II) offers a menu of contracts phi_j=(d_j,r_j) to clients "
                  "of private type theta_j; client payoff W_U^i (Eq. 6).",
        limit="Contract: ic_screening_latex was added from the paper's own (IC) label, but "
              "client_utility_latex is a simplified rendering of the same W_U^i that drops "
              "the congestion-term sum over k in I",
        obstruction="The 2026-07-18 review transcribed ic_screening_latex directly from "
                    "Problem 1's own (IC) constraint label (verified against PDF p.5), but "
                    "flagged that the existing client_utility_latex field simplifies W_U^i by "
                    "dropping the explicit sum over k in I inside the congestion term -- left "
                    "untouched per instructions, so the two fields are not on the same "
                    "footing for Track 1's consistency check.",
        human_task="Rewrite client_utility_latex to include the full sum-over-k congestion "
                   "term matching W_U^i (Eq. 6) exactly, so it is consistent with the "
                   "already-verified ic_screening_latex before re-attempting Track 1."),
    "Mai2022double_auction": dict(
        track=1,
        mechanism="Iterative double auction (IDA) and an RL-based double-auction variant "
                  "matching buyers and sellers to maximize market efficiency and social "
                  "welfare.",
        limit="VCG: notes give only the paper's abstract-level description, no diagnosed "
              "missing formal field",
        obstruction="This entry's notes never went through a Batch-C/D/E field-level review "
                    "-- they only restate the paper's stated contribution (an IDA algorithm "
                    "and an RL-based double-auction algorithm), so no specific null field "
                    "(objective_latex / allocation_rule_latex / payment_rule_latex) has been "
                    "identified yet for Track 1's DSIC/efficiency check to consume.",
        human_task="Open pdfs/Mai2022double_auction.pdf, locate the formal auction-clearing "
                   "objective and price-setting rule for the IDA algorithm specifically (not "
                   "the RL variant, which likely has no closed form), and transcribe them "
                   "into the missing formal fields."),
    "Saputra2020fl_contract": dict(
        track=1,
        mechanism="Server offers a menu of contracts to clients of private type; merged "
                  "from a duplicate corpus entry (2004_01828, same PDF).",
        limit="Contract: possible phi-factor discrepancy between the merged duplicate's "
              "ir_participation_latex / server_objective_latex, not independently "
              "re-verified against the PDF",
        obstruction="The dedup note flags a minor phi-weighting discrepancy between the two "
                    "merged copies' ir_participation_latex and server_objective_latex fields "
                    "that was never independently re-checked against the source PDF, so "
                    "Track 1 would be running against a field of uncertain fidelity.",
        human_task="Open pdfs/Saputra2020fl_contract.pdf, locate the phi weighting term in "
                    "both ir_participation_latex and server_objective_latex, and confirm "
                    "(or correct) it directly against the printed equations before trusting "
                    "a Track 1 verdict on this entry."),
    "Saputra2021iov_contract": dict(
        track=1,
        mechanism="SVs (principals) offer contracts to VSPs (agents) whose private type is "
                  "theta_j (budget level); zeta_n(t) is a contract term offered by SVs, not "
                  "the hidden type -- roles reversed vs. the usual server-designs-contract "
                  "convention.",
        limit="Contract: medium-confidence satisfaction function S() due to OCR artifacts in "
              "the source PDF",
        obstruction="The correction note fixes the private-type identification (theta_j, not "
                    "zeta_n(t)) and the role-reversal (VSP is the agent, SVs are principals), "
                    "but flags that the exact form of the satisfaction function S() is only "
                    "medium-confidence because of OCR artifacts in the source PDF -- Track 1 "
                    "needs a verified S() to run the IC/IR check.",
        human_task="Open pdfs/Saputra2021iov_contract.pdf directly (image view, not OCR "
                    "text-extraction) at the page defining S(), and transcribe the exact "
                    "functional form to replace the OCR-uncertain version before re-running "
                    "Track 1."),
    "Saputra2021straggling": dict(
        track=1,
        mechanism="MUs (clients, principals) design a contract for the MAP (server, agent) "
                  "whose private type is pi_i -- roles reversed vs. the usual server-designs-"
                  "contract convention; involves square-root gain functions G_o, G_l.",
        limit="Contract: square-root gain functions likely fall outside the verifier's "
              "polynomial-friendly assumptions",
        obstruction="The note flags that the role-reversed contract (MUs as principals, MAP "
                    "as agent) is structurally fine but its square-root gain functions (G_o, "
                    "G_l) are likely outside Track 1's polynomial-friendly assumption set, so "
                    "even a correctly transcribed IC/IR pair may not resolve under the "
                    "current solver encoding.",
        human_task="Check whether Track 1's Z3 encoding can handle sqrt-form gain functions "
                   "(e.g. via a polynomial relaxation or bound); if not, this stays MANUAL as "
                   "a solver-capability gap rather than a missing-field gap."),
    "Wu2021contract_DP": dict(
        track=1,
        mechanism="Contract-theoretic FL incentive design with differential privacy, private "
                  "type genuinely 3-dimensional (theta_x, tau_y, rho_z).",
        limit="Contract: genuinely 3-dimensional type outside the verifier's single-"
              "dimension substitution machinery",
        obstruction="The corpus note states the verifier's single-dimension substitution "
                    "machinery cannot capture a genuinely 3-D type space, so any verdict "
                    "produced here should not be trusted as covering the paper's actual "
                    "multidimensional screening claim -- this is a structural solver-"
                    "capability gap, not a missing-field gap.",
        human_task="Confirm whether (theta_x, tau_y, rho_z) can be reduced to a single "
                   "monotone scalar index preserving the paper's IC ordering (as some sibling "
                   "multi-dim entries attempt); if genuinely irreducible, this needs a "
                   "hand-proved multidimensional screening argument and stays MANUAL."),
    "Xiao2020stackelberg_twostage": dict(
        track=1,
        mechanism="Two-stage Stackelberg: server (leader, Stage I) and worker (follower, "
                  "Stage II) choose local accuracy theta_i^(t); follower FOC is Eq. (13), "
                  "solved by best_response_latex (Theorem 1's NE local accuracy).",
        limit="Stackelberg: follower IR is enforced algorithmically (Algorithm 1 quit-check) "
              "rather than as a constraint inside the Stage II arg max",
        obstruction="follower_foc_latex was transcribed from Eq. (13) (verified against "
                    "rendered PDF p.4). ir_follower_latex: the paper DOES state an explicit "
                    "participation condition, but enforces it algorithmically -- Algorithm 1 "
                    "Steps 7-8 say 'if any worker's utility < 0 then the worker quits from "
                    "this round and Goto Step 3' -- transcribed as U_i^(t) >= 0, but this is "
                    "a post-hoc per-round check outside the Stage II arg max in Eq. (11), not "
                    "a constraint appearing inside the optimization problem itself (Steps 4-5 "
                    "apply the symmetric check to the server's own utility).",
        human_task="Decide whether Track 1's IR check can accept an algorithmically-enforced "
                   "(outside-the-arg-max) participation condition as equivalent to an inline "
                   "constraint; if the check requires the constraint to appear inside the "
                   "Stage II optimization problem itself, this entry stays MANUAL as a "
                   "genuine structural mismatch, not a missing transcription."),
    # Zheng2023fl_market intentionally excluded: its stored z3_verdict field is
    # a stale VERIFIED_TEMPLATE, but live verify(entry) on this corpus already
    # returns VERIFIED (entry_specific=True) via the transcribed 'All-in'
    # baseline fields -- flipping it to MANUAL would be a real regression
    # (round_gate: REGRESSION Zheng2023fl_market: VERIFIED -> MANUAL). The
    # brief's Step-1 listing script only reads the stored field and so wrongly
    # pulled it into the 25; it is out of Phase-7's actual scope (any entry
    # currently VERIFIED does not need a MANUAL diagnosis).
}


def main():
    c = json.load(open("corpus.json"))
    rows = c if isinstance(c, list) else c.get("entries", c)
    by = {e["paper_id"]: e for e in rows}
    for pid, d in DIAG.items():
        e = by[pid]
        assert not e.get("verdict_override"), f"{pid} already overridden"
        write_manual_diagnosis(e, round_="R7", today="2026-09-06", **d)
        append_backlog_paragraph(e)
    json.dump(c, open("corpus.json", "w"), indent=2, ensure_ascii=False)
    open("corpus.json", "a").write("\n")
    print(f"{len(DIAG)} entries flipped to diagnosed MANUAL")


if __name__ == "__main__":
    main()
