# Error channels reference

All channels live in `uniqc.simulator.error_model` and are designed to
be passed inside an `ErrorLoader_*` (see the Skill's **Mental model**). Each
channel parameter is the **probability** or **strength** of the noise.

| Channel                | Args                          | Notes                                        |
| ---------------------- | ----------------------------- | -------------------------------------------- |
| `BitFlip(p)`           | `p` ∈ [0, 1]                  | Pauli-X with probability `p`.                |
| `PhaseFlip(p)`         | `p`                           | Pauli-Z with probability `p`.                |
| `Depolarizing(p)`      | `p`                           | (1−p)·ρ + p·I/2.  Single-qubit.              |
| `TwoQubitDepolarizing(p)` | `p`                       | Acts on the **pair** of qubits the gate touched. Use after `CNOT` / `CZ`. |
| `AmplitudeDamping(γ)`  | `γ` ∈ [0, 1]                  | T1-like. `γ ≈ Δt / T1` for small `γ`.        |
| `ThermalRelaxation(t1_ns, t2_ns, gate_time_ns)` | T1/T2 and gate duration in ns | Gate-time-aware amplitude damping plus dephasing; require `t2_ns <= 2 * t1_ns`. |
| `PauliError1Q(px, py, pz)` | each `pi` ∈ [0, 1]; sum ≤ 1 | Apply X/Y/Z with given probabilities; identity otherwise. |
| `PauliError2Q(ps)`     | `ps` length 15                | Apply each non-identity 2q Pauli with given probability; ordering documented in source. |
| `Kraus1Q(kraus_ops)`   | iterable of 2×2 complex arrays | General single-qubit Kraus channel.         |

## Channel choice cheat-sheet

| What you're modeling                          | Channel                                                |
| --------------------------------------------- | ------------------------------------------------------ |
| Symmetric, "rest of error budget"             | `Depolarizing(error_per_gate)`                         |
| T1 / amplitude relaxation                     | `AmplitudeDamping(γ = Δt / T1)` after every gate, where Δt is the gate duration. |
| T2 / pure dephasing                           | `PhaseFlip(p = 0.5 * (1 - exp(-Δt / Tφ)))`             |
| T1 + T2 with known gate duration              | `ThermalRelaxation(t1_ns, t2_ns, gate_time_ns)` |
| Chip-measured 1q error (XEB or RB number)     | `PauliError1Q(px=ε/3, py=ε/3, pz=ε/3)` (depolarizing form), or `Depolarizing(ε)` |
| Chip-measured 2q error (XEB / RB)             | `TwoQubitDepolarizing(ε_2q)`                           |
| Custom non-Markovian / bespoke channel        | `Kraus1Q([K0, K1, ...])` — supply your own Kraus ops   |

## Worked example: noise budget for a CNOT layer

Say the chip reports:

- single-qubit error per gate: `1.5e-3` (depolarising-ish).
- two-qubit (CNOT) error per gate: `8.5e-3`.
- T1 = 50 µs, T2 = 30 µs; CNOT duration ≈ 200 ns.

Then the per-CNOT layer noise model is:

```python
import math
from uniqc.simulator.error_model import (
    Depolarizing, TwoQubitDepolarizing, AmplitudeDamping, PhaseFlip,
)

T1, T2, dt_cnot = 50e-6, 30e-6, 200e-9
gamma  = 1 - math.exp(-dt_cnot / T1)
T_phi  = 1 / (1 / T2 - 1 / (2 * T1))
p_phase = 0.5 * (1 - math.exp(-dt_cnot / T_phi))

cnot_layer = [
    AmplitudeDamping(gamma),         # per qubit T1
    PhaseFlip(p_phase),              # per qubit T2
    TwoQubitDepolarizing(8.5e-3),    # raw CNOT error
]
single_layer = [
    Depolarizing(1.5e-3),
]
```

`cnot_layer` goes into `ErrorLoader_GateTypeError(gatetype_error={'CNOT': cnot_layer})`,
`single_layer` into the same loader's `generic_error=`.

## Validation

1. Run the noisy circuit with `simulate_shots`.
2. Run the same circuit on `dummy:<provider>:<chip>` (chip-backed
   dummy uses the calibrated noise model — your hand-built model
   should agree to within shot noise if the channels are right).
3. If they disagree, the most likely culprit is a missing
   `AmplitudeDamping` / `PhaseFlip` layer (decoherence over gate time)
   that the chip-backed path was including for free.

## What to **not** do

- Don't apply `Depolarizing(p)` after a measurement. Channels
  belong in the **gate** layer; measurement noise is a separate
  `readout_error=` parameter on `NoisySimulator`.
- Don't sum `BitFlip + PhaseFlip` to mean depolarizing. Use
  `Depolarizing(p)` directly — the channel is not just X+Z.
- Don't model crosstalk by inflating the `TwoQubitDepolarizing(p)`
  globally — measure it via `uniqc.calibration.xeb.parallel_cz`
  (uniqc 0.0.13) and use a `GateSpecificError` with per-pair values.
