# `sim/` — FL empirical-validation layer

Runs a **verified** incentive mechanism inside a real (small) FedAvg loop against
a client population that **violates the mechanism's formal assumptions**, and
measures where deployment behaviour diverges from the certificate.

Spec: [`docs/superpowers/specs/2026-08-30-fl-simulation-validation-design.md`](../../docs/superpowers/specs/2026-08-30-fl-simulation-validation-design.md).
Findings: [`docs/sim-results.md`](../../docs/sim-results.md),
[`docs/sim-notes.md`](../../docs/sim-notes.md).

## Modules

| file | responsibility |
|---|---|
| `fedavg.py` | NumPy FedAvg loop, synthetic Gaussian-blob data, Dirichlet non-IID partition, `LogRegModel`, per-round `RewardHook`, `RunLog` |
| `clients.py` | `Action`, `Client` base + 6 strategy models (honest / quality-misreporter / dropout / coalition / bounded-rational / interdependent-value) |
| `mechanisms.py` | `build_reward_hook(mechanism, setting, budget)` — turns a callable / `architect.ast.Mechanism` / mechanism-dict into a per-round reward hook. Read-only over the mechanism. |
| `oracle_mechanisms.py` | hand-designed reward callables, one per setting (the `oracle` arm) |
| `run.py` | `SETTINGS`, `POPULATIONS`, `build_population`, `run_setting(setting, arm, population, seed) -> metrics dict`, `main()` CLI |
| `report.py` | `aggregate` seeds → `write_report` → `docs/sim-results.md` |
| `fixtures/generated/<setting>.json` | the mechanism the Architect loop produced **and the verifier certified** for that setting (checked-in snapshot) |

## Run it

```bash
PYTHONPATH=src python -m sim.run --setting all --seeds 0 1 2 --out docs/sim-results.md
```

`--setting` takes a single setting name or `all`. Arms default to
`none oracle generated`.

## Tests

```bash
PYTHONUTF8=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/sim/ -q
```

`PYTHONUTF8=1` is needed on a non-UTF-8 Windows locale (the report and its
test read back block-drawing characters). `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`
avoids an unrelated third-party pytest plugin that fails to import in this env.

## Regenerating the `generated` fixtures

The fixtures are snapshots of real `ArchitectResult.mechanism_dict` output. To
refresh one, run the Architect loop with `ARCHITECT_AST_VERIFY=1` (AST-native
verification — no LaTeX parser needed) and an LLM backend configured
(`ARCHITECT_LLM_PROVIDER` + key), then write
`{"kind": "dict", "note": "...", "certificate": [...], "mechanism_dict": {...}}`.
A fixture whose `note` contains `PLACEHOLDER` is flagged in the report and its
row is marked "not evidence". Fixtures must not be hand-tuned (spec
honest-framing rule). See `docs/sim-notes.md` for the exact prompts used.
