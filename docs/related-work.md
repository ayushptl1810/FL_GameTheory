# Related Work and Positioning

## LegoNE (Li, Li, Deng — arXiv 2508.11874, Aug 2025)
LLM "architect" proposes approximate-Nash-equilibrium algorithms from a symbolic
building-block language; the LegoNE analyzer compiles each candidate into a
finite optimization problem that formally certifies its worst-case guarantee;
a reasoning LLM iterates on quantitative feedback. It discovered a new 3-player
ANE algorithm beating the only known human paradigm. Our loop shares this shape
(LLM proposer + formal certifier + feedback). **Distinction:** our contribution
must be a novel *FL-mechanism* result (future-scope Part 2) or the honest
per-family verifiability finding from spec Task 1 — not the architecture itself.

## Strategy-Logic mechanism synthesis (Mittelmann, Maubert, Murano, Perrussel — Artif. Intell. 2024)
A quantitative Strategy Logic + model checking to both verify mechanism
properties (strategy-proofness, budget balance) and synthesize mechanisms from a
logical spec, domain-general. **Distinction:** we operate on the real-valued
utility fragment via SMT / SOS / interval arithmetic rather than finite model
checking; we use an LLM proposer; we carry an FL-specific corpus prior.

## SMT in social choice (Brandl & Brandt et al., JACM; Barthe, Gaboardi et al., arXiv 1502.04052)
Computer-aided impossibility proofs and formal Bayesian-IC verification via SMT
and proof assistants, ~10 years old. **Distinction:** we claim only the
LLM-in-the-loop synthesis and the FL application, not "SMT can check IC".

## LLM + SMT counterexample loops (LEMUR; LaM4Inv; LORIS, TOPLAS 2026; arXiv 2508.00419)
The propose -> solver -> counterexample -> repair loop, with iteration caps and
restarts, is the standard template in LLM-assisted program verification.
**Distinction:** we claim only the mechanism-design instantiation (typed
mechanism AST, five-value IC verdict, FL corpus RAG), not the loop mechanics.

## Open categorization question — 2405_13879
`2405_13879` ("FACT or Fiction", NeurIPS 2024) is filed under Shapley but has no
characteristic function and no Shapley formula; its mechanism is a penalty rule +
"sandwich" truthfulness competition. Needs a human decision: new
"penalty + sandwich" family, or a documented reason it stays under Shapley. It is
currently silver-tier so `tools/validate.py` passes 185/185.
