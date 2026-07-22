---
name: uniqc-noise-simulation
description: "Use when the user wants to model and simulate quantum noise locally with UnifiedQuantum (uniqc ≥ 0.0.13): build error channels (Depolarizing / TwoQubitDepolarizing / BitFlip / PhaseFlip / AmplitudeDamping / PauliError1Q/2Q / Kraus1Q), wire them into ErrorLoader_GenericError / GateTypeError / GateSpecificError, attach readout error, run NoisySimulator on density-matrix or vector backends, drive chip-backed dummy backends (`dummy:originq:<chip>`, `dummy:quark:<chip>`), and validate the noise model against a calibration cache. Notes the 0.0.13 NoisySimulator MRO fix (noise injection no longer silently skipped on certain paths)."
---

# Uniqc Noise Simulation Skill

This skill is the **modeling-side** counterpart to `uniqc-xeb-qem`
(which *measures* errors) and `uniqc-platform-verify` (which *audits*
them). Use it when the user wants to:

- Add a noise channel to a local simulation to predict hardware behavior.
- Build a chip-faithful noisy execution that doesn't burn cloud quota.
- Reproduce a known hardware effect (T1/T2 decay, biased readout,
  crosstalk) in a controlled environment.
- Validate that a noise model matches a measured calibration before
  publishing simulated results.

> 0.0.13 fix: `NoisySimulator` previously had a multiple-inheritance
> order that silently dropped noise injection on some
> `simulate_pmeasure` / `simulate_shots` paths. The MRO is corrected
> in 0.0.13. **If a previous "noisy" sim looked suspiciously
> ideal, re-run it on 0.0.13.**

## Decision tree

| User goal                                                   | Read first                                                             |
| ----------------------------------------------------------- | ---------------------------------------------------------------------- |
| "Add a single uniform depolarizing channel"                 | [references/error-channels.md](references/error-channels.md)           |
| "Different noise per gate type / per qubit"                 | **Mental model** below                                                 |
| "Add readout error on top of a circuit"                     | **Practical defaults** below                                           |
| "Use the chip's own published characterization as the noise model" | [references/chip-backed-dummy.md](references/chip-backed-dummy.md) |
| "Compare my noise model to a measured XEB / readout cal"    | [references/chip-backed-dummy.md](references/chip-backed-dummy.md) |

## Mental model

```
                      ┌──────────────────────┐
        Circuit ─────►│  NoisySimulator      │
                      │  backend_type=       │
                      │   "density_matrix"   │
                      │  error_loader=       │
                      │   ErrorLoader_*      │
                      │  readout_error=      │
                      │   {q: [p01, p10]}    │
                      └────────┬─────────────┘
                               │
                  shots/probs/density-matrix
                               │
                               ▼
       ┌──────────────────────────────────────────────────┐
       │  Error model layers (applied in order):          │
       │   1. coherent gate                               │
       │   2. ErrorLoader inserts Kraus / Pauli channels  │
       │      after each gate (per the loader policy)     │
       │   3. readout flip on each measured qubit         │
       └──────────────────────────────────────────────────┘
```

Three loader layers (most general at the bottom):

1. `ErrorLoader_GenericError(generic_error=[ch1, ch2, ...])` —
   applies the same list of channels after every gate.
2. `ErrorLoader_GateTypeError(generic_error=..., gatetype_error={'H': [...], 'CNOT': [...]})` —
   per-gate-type override on top of `generic_error`.
3. `ErrorLoader_GateSpecificError({(gate, qubit_or_pair): [ch, ...], ...})` —
   per-gate-and-qubit override; the most chip-faithful.

## Cheat sheet

```python
from uniqc import Circuit
from uniqc.simulator import NoisySimulator
from uniqc.simulator.error_model import (
    Depolarizing, TwoQubitDepolarizing, AmplitudeDamping, ThermalRelaxation,
    PauliError1Q, PauliError2Q, Kraus1Q,
    ErrorLoader_GenericError,
    ErrorLoader_GateTypeError,
    ErrorLoader_GateSpecificError,
)

# 1. Channels
gen = ErrorLoader_GenericError(generic_error=[
    Depolarizing(0.001),
    AmplitudeDamping(0.0005),
])

# 2. Gate-type-aware
gtype = ErrorLoader_GateTypeError(
    generic_error=[Depolarizing(0.001)],
    gatetype_error={
        'H':    [AmplitudeDamping(0.001)],
        'CNOT': [TwoQubitDepolarizing(0.005)],
    },
)

# 3. Gate-and-qubit specific (drive from a calibration cache)
gspec = ErrorLoader_GateSpecificError({
    ('H',    0):    [Depolarizing(0.0008)],
    ('CNOT', (0,1)):[TwoQubitDepolarizing(0.0061)],
    ('CZ',   (1,2)):[TwoQubitDepolarizing(0.0095)],
})

# 3b. Gate-time-aware T1/T2 relaxation (all values in ns).
thermal = ThermalRelaxation(t1_ns=50_000, t2_ns=40_000, gate_time_ns=80)

# 4. NoisySimulator
sim = NoisySimulator(
    backend_type="density_matrix",
    error_loader=gtype,
    readout_error={
        0: [0.012, 0.018],   # [p(0|1), p(1|0)]
        1: [0.014, 0.020],
    },
)

c = Circuit(2); c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)
counts = sim.simulate_shots(c, shots=2000)
rho    = sim.simulate_density_matrix(c)
```

## Practical defaults

- **Always use `backend_type="density_matrix"`** for noisy sims. The
  statevector backend cannot represent mixed states; channels collapse
  to noise-free unitaries.
- **Channels apply *after* the gate.** So `Depolarizing(p)` on an `H`
  layer is the residual error of the H gate. Don't double-count — if
  you also turn on `gatetype_error['H']`, the generic channel **and**
  the H-specific channel both fire.
- **Readout error is *separate* from gate error** and is applied at
  measurement time. Use real measured numbers from
  `ReadoutCalibrationResult.confusion_matrix` for chip-faithful
  results; the convention is `readout_error[q] = [p(0|1), p(1|0)]`.
- **For chip-faithful noise without writing the model yourself**, use
  `dummy:<provider>:<chip>` (e.g. `dummy:originq:WK_C180`). uniqc
  builds the noise model from the local backend cache. Run
  `uniqc backend update --platform <p>` before sampling.
- **For a reproducible custom noisy machine**, create
  `~/.uniqc/backend/virtual/<name>.yaml` with `uniqc backend virtual init
  <name>`, then run `list`, `show`, and `validate` before submitting to
  `dummy:virtual:<name>`. Its `noise.thermal_relaxation` converts YAML
  T1/T2 (µs) plus `gate_times_ns` into `ThermalRelaxation`; require
  `t2_us <= 2 * t1_us`.
- **Validate the model**. Compare measured XEB on the noisy sim to the
  measured XEB on the real backend (uniqc-xeb-qem) — they should
  agree within shot noise if the model is faithful.
- **MPS noise** is not supported. `dummy:local:mps-linear-N` is **always
  ideal**; for noisy MPS you'd need to drop to a small density-matrix
  sim.
- **Reproducibility**: `NoisySimulator` accepts `seed=` on the
  underlying RNG; pass it.

## Names to remember

- `uniqc.simulator.NoisySimulator`
- `uniqc.simulator.error_model.{BitFlip, PhaseFlip, Depolarizing,
  TwoQubitDepolarizing, AmplitudeDamping, PauliError1Q, PauliError2Q,
  Kraus1Q, ThermalRelaxation}`
- `uniqc.simulator.error_model.{ErrorLoader_GenericError,
  ErrorLoader_GateTypeError, ErrorLoader_GateSpecificError}`
- `dummy:<provider>:<chip>` — chip-backed dummy that builds its noise
  model from the cached chip characterization (uniqc 0.0.13 also fixed
  the bug where a Bell circuit submitted to `dummy:originq:WK_C180`
  reached the simulator as raw H+CNOT and crashed with `TopologyError`).
- `dummy:virtual:<name>` — user YAML noisy virtual machine; validate it with
  `uniqc backend virtual validate <name>` before local submission.

## Response style

- Lead with the **simplest noise model** that captures the user's
  symptom, then layer up only as needed. Do not over-fit a 6-channel
  noise model when 1 channel demonstrates the effect.
- For "match my hardware" requests, prefer `dummy:<provider>:<chip>`
  over a hand-built `ErrorLoader_GateSpecificError` — the chip-backed
  path stays consistent with vendor metadata and benefits from any
  cache refresh.
- Always note that `Simulator` (no noise) and `NoisySimulator` are
  **not interchangeable** — `Simulator(backend_type="density_matrix")`
  is *not* noisy.
