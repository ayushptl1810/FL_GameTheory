# R4 — Newly VERIFIED entries (hand cross-checked)

Every flip below was cross-checked by hand against the source PDF before it was
allowed to stand. Fail-closed: an unconfirmed certificate is a rejected flip.

Date: 2026-09-04

---

## Tian2021contract

**Category:** Contract · **Track:** 2 (parametric SOS / positivity certificate)
**Flip:** MANUAL → VERIFIED

### The widening

R4 Task 8 corrected the entry's `type_variable`. It previously carried the
ambiguous prose *"data coverage quality \theta_i and training willingness e_i"*,
which made `_type_family()` match **both** the `theta` and the `e` families, so no
single type ordering could be imposed and the entry fell through to MANUAL. It is
now just `\( \theta_i \)` — the single screening type.

This is sound because the paper's effort variable is a **moral-hazard action, not a
second screening dimension**. Paper Eq. (10)–(11): the client's own FOC
`∂U_i/∂e_i = θ_i R_i − c e_i` gives `ê_i = (1/c) θ_i R_i`, and effort is substituted
out **before** the screening IC. The operational IC/IR (Eqs. 12, 19) are
one-dimensional in `θ_i`, with single-crossing `(θ_i − θ_j)(R_i − R_j) ≥ 0` (Eq. 16).

### The cross-check

Certificate form, as reported by the solver:

> parametric positivity certificate over ordered-increment coordinates | type family
> `theta` (value-type), n=2 | bindings solved for reward family `R` | **degree-0
> Positivstellensatz (posynomial)** + sympy assumptions | exact symbolic proof, no SDP

The four discharged conditions, with the IC gap dumped symbolically:

| Condition | Expression | Sign |
|---|---|---|
| IC(0,1) | `(c·de_1²·dθ_1 + 2c·de_1·dθ_1·e_lo + 2·df_1·dθ_1) / (2·dθ_1 + 2·θ_lo)` | ≥ 0 |
| IC(1,0) | `0` (binding — adjacent upward IC is solved to equality) | = 0 |
| IR(0)   | `0` (binding — IR binds at the worst type) | = 0 |
| IR(1)   | `(c·dθ_1·e_lo² + 2·dθ_1·f_lo) / (2·θ_lo)` | ≥ 0 |

Every monomial in both numerators carries a **positive** coefficient and every
denominator is a positive sum — that is exactly the degree-0 Positivstellensatz
(posynomial) certificate, and it is non-negative on the whole positive orthant of
the increment coordinates. `sp.ask(Q.nonnegative(·))` returns `True` for both under
the solver's declared assumptions.

IC gap evaluated at concrete type pairs (`c = e_lo = θ_lo = dθ_1 = 1`):

| `de_1` | `df_1` | IC(0,1) |
|---|---|---|
| 0.0 | 0.0 | **+0.0000** |
| 0.5 | 0.5 | **+0.5625** |
| 1.0 | 2.0 | **+1.7500** |
| 2.0 | 1.0 | **+2.5000** |

IR(1) at `f_lo ∈ {0, 0.5, 2}` → `+0.5000`, `+1.0000`, `+2.5000`. All non-negative.

### ⚠ The certificate rests on an IMPLICIT assumption: `de_1 ≥ 0`

**This must be recorded explicitly.** The posynomial certificate is non-negative
*only on the positive orthant of the increment coordinates*. Concretely, at
`de_1 = −1.5, df_1 = 0` the IC(0,1) gap evaluates to **−0.1875** — negative.

The solver does not merely hope for this: `track2_sos.py:460` parametrizes every
non-type menu family with `_sp.Symbol(f"d{base}_{j}", nonnegative=True)`, so
`de_1 ≥ 0` and `df_1 ≥ 0` are **declared assumptions of the coordinate system**.
The certificate is therefore internally sound; the question is whether the paper
licenses those assumptions. It does:

- **Lemma 1** (Monotonicity between θ and R): *"the contract rewards should follow
  the order R_1 < ⋯ < R_I with θ_1 < ⋯ < θ_I"* — R co-monotone with θ.
- **Lemma 2** (Monotonicity between R and f): *"R and f have the same trend, namely
  R_1 < ⋯ < R_I with f_1 < ⋯ < f_I"* — licenses **`df_1 ≥ 0`**.
- **Corollary 1** (Monotonicity between f and θ): `f_i ≥ f_j ⟺ θ_i ≥ θ_j`.
- **Eq. (11)** `ê_i = (1/c)·θ_i·R_i`, and the paper states *"a client's willingness
  is positively determined by the data quality and the chosen contract"* — with
  Lemma 1 giving θ and R co-monotone, `ê_i` is increasing in the type index, which
  licenses **`de_1 ≥ 0`** (effort co-monotone with θ).

So `de_1 ≥ 0` is the paper's own optimal-contract monotonicity property. It is
**not spelled out in the entry's raw 2-D `ic_screening_latex`** (which still carries
`e_i, e_j` explicitly, with `num_types: 2` and `multidimensional_type: true`), and
an R6 consumer that re-derives the obligation without importing Lemmas 1–2 /
Corollary 1 would not reproduce this certificate. Flagged for R6.

**Verdict: HELD.**

---

## Zheng2023fl_market

**Category:** VCG · **Track:** 1 (monotone winner rule + critical-value payment,
grid k=3, 9 profiles) · **Flip:** MANUAL (R2 pin) → VERIFIED

### The widening

R4 Task 6 landed the `MonotoneThreshold` DSIC path; Task 7 transcribed
`winner_rule_monotone` + `critical_price_latex` from **Appendix B** (Algorithm 4
lines 2–5, Proposition 2). Task 7 flagged the cite as **soft**: the paper argues
sort-position monotonicity only *"intuitively"*, and Prop 2 case 2 closes the
self-referential moving-threshold interaction with a single one-line inequality
rather than a set-monotonicity argument. Task 7's review additionally noted the
Task-6 eligibility gate passed on the literal prose phrase *"critical bid for i"* in
`critical_price_latex`, not on a structural infimum form. So the pin was left in
place for this task to decide.

### The cross-check — closing the moving threshold rigorously

**The mechanism (Algorithm 4).** Write `w_j = d_j·ε̄_j'` for each owner's bid weight
and `v_j = V_j'/w_j` for the unit valuation. Sort ascending by `v`. Scanning in that
order, owner `i` joins `W` iff

```
v_i  ≤  B / (T_i + w_i)          where  T_i = Σ_{j ∈ W, j ≺ i} w_j
```

**Step 1 — remove the apparent self-reference.** Both sides are positive, so
cross-multiply by `w_i·(T_i + w_i) > 0`. Using `V_i = v_i·w_i`:

```
V_i·T_i + V_i·w_i  ≤  B·w_i        ⟺        V_i · T_i  ≤  (B − V_i) · w_i     (★)
```

`T_i` is the accumulated weight of winners **strictly before `i`** in the sort. This
is the crux the paper never states: `T_i` is a **prefix quantity**, so it does not
depend on `i`'s own bid at all. The self-reference in the paper's written threshold
`B / Σ_{j ∈ W ∪ {i}} d_j·ε̄_j'` is only *apparent* — at the moment `i` is tested, `W`
is already fixed by the scan, and the `∪ {i}` term is just `w_i`, which (★) moves to
the right-hand side. There is no fixed point to solve.

Note (★) also gives **`B − V_i ≥ 0` for every winner** for free: the LHS is ≥ 0 and
`w_i > 0`.

**Step 2 — the improving deviation moves `i` weakly earlier.** The manipulation
directions that could help `i` are `V_i' ≤ V_i`, `d_i' ≥ d_i`, `ε̄_i' ≥ ε̄_i` (case 2
of Prop 2; cases 1, 3, 4 are already closed by the paper). All three weakly decrease
`v_i = V_i/(d_i ε̄_i)`. Every *other* owner's key is untouched. Hence, **as a pure
fact about sorting**, the set `S` of owners ordered before `i` can only shrink:
`S' ⊆ S`. No greedy reasoning is needed for this step.

**Step 3 — the inductive step: the surviving prefix replays identically.** This is
what Prop 2 asserts but does not prove. The greedy is a strict left-to-right scan
whose state (`W`, running total) after processing any prefix is a function **of that
prefix alone**. Since `S' ⊆ S` and the relative order of the owners within `S'` is
unchanged (their keys never moved), the scan over `S'` makes exactly the same
accept/reject decision on each of them in both runs. Therefore

```
W' ∩ S'  =  W ∩ S'  ⊆  W ∩ S        ⟹        T_i' = Σ_{W' ∩ S'} w_j  ≤  T_i
```

In particular **no owner can newly appear in `i`'s prefix** — `i` moving earlier can
only *evict* owners from its prefix, never add them. (This is the step that makes a
cascade analysis unnecessary: there is nothing to cascade into `i`'s prefix.)

**Step 4 — conclude.** `i` won under `b_i`, so (★) held: `V_i·T_i ≤ (B − V_i)·w_i`.
Under `b_i'` we have `T_i' ≤ T_i` (Step 3), `V_i' ≤ V_i`, and `w_i' ≥ w_i`, and with
`B − V_i ≥ 0` from Step 1:

```
V_i'·T_i'  ≤  V_i·T_i  ≤  (B − V_i)·w_i  ≤  (B − V_i')·w_i'
```

which is exactly (★) for `b_i'`. So `i` still wins. ∎

Both the threshold `i` must beat and `i`'s sort position therefore move
**monotonically in `i`'s favour at every step of the greedy**, which is what the
rigorous close required. Together with the critical unit payment
`p^unit = B / Σ_{j ∈ W ∪ {i}} d_j·ε̄_j'` (Algorithm 4 line 5) — independent of `i`'s
report given the winner set — Myerson's characterization yields truthfulness.

**Machine corroboration.** The argument was additionally stress-tested on the
executable mechanism (~1.4M randomized profiles, `n ∈ [3,7]`, `B ∈ {0.5,1,3,10}`),
checking each step separately:

| Property tested | Violations |
|---|---|
| Winner stays a winner under `V↓ / d↑ / ε↑` (incl. joint 3-way) | **0** |
| Predecessor total `T_i` never increases | **0** |
| Predecessor *set* inclusion `S' ⊆ S` (Step 2) | **0** |
| Prefix decisions identical on `S'` (Step 3) | **0** |
| No new predecessor appears | **0** |
| `B − V_i ≥ 0` for every winner (Step 1) | **0** |
| Monotonicity under **exact ties** in `v` | **0** |

The search corroborates; the proof above is the guarantee.

**Verdict: HELD** — pin lifted, `manual_diagnosis_resolved` recorded.

*Note on test pinning:* `tests/verifier/test_seams.py` pins only the **first 8** VCG
entries (`VCG = [... category == "VCG"][:8]`); `Zheng2023fl_market` is not among them
and is not referenced by any other expected dict, so no test change was required for
this flip. (Tian2021contract's pins were added in Task 8 and are unchanged.)

---

## Rejected flips

None this round. Both candidate flips were cross-checked and held.

`GPS2023afl_recruit` was assessed for a COUNTEREXAMPLE verdict and **fails closed to
MANUAL**: its `payment_rule_latex` `p_i(b) = b_i − C_i(t)` is first-price (increasing
in own bid) and byte-identical to `client_utility_latex`, so the recorded model is
degenerate — but no source PDF exists (`arxiv_id`, `source` both null), the winner
count `k` is unspecified ("among the lowest bids"), and no true cost `c_i` appears
anywhere in the entry. A profitable-deviation witness `(b_i, b_i', b_{-i}, k)` would
require inventing `k` and the cost semantics, which would be fabrication rather than
a rigorous counterexample. Left MANUAL with an R4-refreshed diagnosis.
