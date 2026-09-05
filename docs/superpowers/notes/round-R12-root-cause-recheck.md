# R12 — Re-trace of the 10 no-screening-IC entries against current code

**Method note (deviation from plan wording).** The plan's Task 2 says "open
its PDF and read the truthfulness proof". No paper PDFs are present in this
repository. Each of the 10 entries, however, already carries a PDF-derived
shape diagnosis written in earlier rounds: an R3a LLM extraction pass *over
the PDF text* (which declined with `confident=false` for every one of these
— the correct fail-closed outcome, meaning no payoff table was ever
transcribable), plus hand-written `notes` / `manual_diagnosis` from the
2026-07-18 `ic_screening_latex` review pass and R9's audit. This re-trace
classifies each entry from that stored evidence and from the current
`mechanism` dict. Where the stored evidence already names the equilibrium
shape precisely, it is taken as the re-derived shape; no entry's shape was
in doubt on re-read.

**Shape legend (from the plan / R9 spec):**
- **(a)** Nash over a *finite, discrete* action set (`{abstain, join, buy}`-shaped), proved by "no profitable unilateral deviation" over that set — **R12's real target**.
- **(b)** Peer-prediction / Bayesian-Truth-Serum: truthfulness via a proper scoring rule over reported *signals* — out of scope.
- **(c)** Bayesian persuasion / information design — out of scope.
- **(d)** Something else — R9's family label needs re-diagnosis. Includes **continuous-action** moral-hazard Nash equilibria, which are Nash but have no finite set for `verify_nash_action_choice` to enumerate.

## Per-entry table

| paper_id | R9 family label | re-derived shape | match? | notes |
|---|---|---|---|---|
| 2408_13223 | no-screening-IC / Nash-action | **a** | yes | Paper poses a Nash equilibrium over `{abstain, join, buy}`; rewards assigned per platform-known type, no menu self-selection. Finite-action shape confirmed. No numeric payoff table in the extracted text (R3a extraction declined). |
| 2505_02462 | no-screening-IC / Nash-action | **d** | no | Graph-based reciprocal model-sharing. Single self-reported-cost truthfulness property (Lemma 1 / Thm 2) plus a real IR proof (Thm 1). No per-player action set at all — a one-shot truthful-report property, not a best-response-over-actions check. |
| 2505_05842 | no-screening-IC / Nash-action | **c** | no | DaringFed — dynamic Bayesian persuasion: server sends a signal over the posterior of tau and offers one uniform reward; feasibility governed by Bayesian Consistency / Plausibility / Benefit (Defs 2-4). Signal design, not a player action choice. |
| 2605_02935 | no-screening-IC / Nash-action | **a** | yes | DeRelayL — "IR/IC per blockchain role via strategy-proofness against a small fixed deviation set". A finite best-response check in spirit. But no type space, no cost function, no payoff table transcribed -> nothing to enumerate. |
| Bornstein2023realistic_incentive | no-screening-IC / Nash-action | **d** | no | REALFM — moral hazard over a **continuously** self-chosen contribution `m_i`; Theorem 1 is a Nash condition on a continuous action. Paper explicitly distinguishes itself from contract theory. No finite action set. |
| Huang2024aigc | no-screening-IC / Nash-action | **d** | no | IMFL-AIGC — a single uniform unit-data price; "type-1/type-2" are post-hoc behavioural regions of a continuous `(s_k, lambda_k)` space, not a finite action set. Continuous best-response, no payoff table. |
| Karimireddy2022data_sharing | no-screening-IC / Nash-action | **d** | no | Moral hazard / **continuous-action** Nash with *verifiable* costs; the paper's own "Theorem 4.6 (Incentive compatibility)" is a no-distortion property of the continuous equilibrium contribution, not self-selection and not a finite-action best-response. |
| Li2026network | no-screening-IC / Nash-action | **a** | yes | Non-monotonic network effects — per-type closed-form payment plus an explicit **3-action** `{abstain, join, buy}` equilibrium. Finite-action shape confirmed. No numeric payoff table in the extracted text. |
| Zhang2020fedserving | no-screening-IC / Nash-action | **b** | no | FedServing — Bayesian peer-prediction / Bayesian Truth Serum with a BNE truthfulness proof (Defs 1-2) over reported predictions. Proper-scoring-rule shape, not a finite action choice. |
| Zhao2023truthful | no-screening-IC / Nash-action | **d** | no | Hidden-action moral hazard: server assigns one desired action; Lemma 2 is a Nash condition over **continuous** effort `(e_i, D_i)`. No finite action set to enumerate. |

## Partition

**Shape (a) — finite-action Nash, R12's target:** `2408_13223`,
`2605_02935`, `Li2026network` (3 entries).

**Not this round:**
- **(b) peer-prediction BNE:** `Zhang2020fedserving`
- **(c) Bayesian persuasion:** `2505_05842`
- **(d) continuous-action Nash / other:** `Bornstein2023realistic_incentive`,
  `Huang2024aigc`, `Karimireddy2022data_sharing`, `Zhao2023truthful`,
  `2505_02462`

## Flip outlook

All three shape-(a) entries were subject to the R3a extraction pass, which
declined for every one (`confident=false`, empty fields) — meaning **no
concrete numeric action-payoff table is available to transcribe** for any of
them, and none is present in the current `mechanism` dict. Under the plan's
fail-closed rule ("An action set or payoff not stated ... is left absent and
the entry stays `MANUAL`"), R12 produces **zero flips**. The round's
deliverable is the `track_nash.py` verifier + its wiring + tests (so a
future entry that *does* carry a transcribed payoff table is checkable
without new plumbing), and a corrected, shape-specific `manual_diagnosis`
for all 10 entries replacing the generic "no-screening-IC" text.
