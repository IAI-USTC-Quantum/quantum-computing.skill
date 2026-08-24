---
name: uniqc-quantum-volume
description: "Use when the user wants to run a Quantum Volume (QV) test on a UnifiedQuantum-supported backend: build the standard square QV circuits (n random SU(4) layers, depth n) via qiskit, load them into uniqc, run on the target backend, compute the heavy-output probability, and apply the conventional 2/3 + lower-confidence-bound pass/fail rule across n = 2, 3, 4, … to find the largest passing n. Report `QV = 2^n_max`."
---

# Uniqc Quantum Volume Skill

Quantum Volume (QV) is a single-number benchmark that captures effective
hardware quality across width, depth, error rate, and connectivity. The
protocol (Cross et al. 2019, arXiv:1811.12926) is:

1. Pick a width `n`. Build a depth-`n` "square" QV circuit: `n` layers,
   each layer is `floor(n/2)` random SU(4) gates over a random qubit
   permutation.
2. Sample many such random circuits at width `n`.
3. For each circuit, compute the **heavy-output probability** —
   `Σ_{x : p_ideal(x) > median} p_observed(x)` — using the ideal
   statevector for the median and the hardware counts for the
   observation.
4. The mean heavy-output probability over many circuits, with a one-sided
   two-sigma lower confidence bound > 2/3, certifies that width.
5. `QV = 2 ^ n_max` where `n_max` is the largest passing width.

> ⚠️ uniqc 0.0.13 has **no built-in QV implementation**. This skill
> uses `qiskit.circuit.library.quantum_volume(n, depth, seed=...)` to
> generate the circuits and loads them into uniqc via `Circuit.from_qasm`
> (or, equivalently, by passing the qiskit `QuantumCircuit` straight into
> any `AnyQuantumCircuit`-accepting API — uniqc 0.0.13 normalizes it
> internally). qiskit is a **core dependency** in 0.0.13, so plain
> `pip install unified-quantum` is sufficient — no `[qiskit]` extra.

## First decision

| User goal                                                 | Read first                                             |
| --------------------------------------------------------- | ------------------------------------------------------ |
| "What is QV / what's the pass/fail rule?"                 | [references/protocol.md](references/protocol.md)       |
| "How do I build the QV circuit and run it on my backend?" | [references/circuit-construction.md](references/circuit-construction.md) |
| "How do I score the heavy-output probability + CI?"       | [references/analysis.md](references/analysis.md)       |
| "Just run the whole thing for me"                         | `examples/qv_demo.py`                                  |

## Mental model

```
                ┌────────────────┐    ┌────────────────────┐    ┌──────────────────┐
n, n_circuits ─►│ build QV(n,n)  │ ─► │ ideal statevector  │ ─► │ median, heavy set│
                │  via qiskit    │    │ (uniqc Simulator)  │    └──────────────────┘
                └────────┬───────┘                                       │
                         │                                               ▼
                         ├─► transpile (uniqc.compile + chip basis) ─►   │
                         │                                               ▼
                         └─► submit to backend (`submit_batch`) ──► counts
                                                                         │
                                                                         ▼
                                                       per-circuit heavy_freq
                                                                         │
                                                                         ▼
                                                  mean ± 2σ (bootstrap or normal)
                                                                         │
                                                                         ▼
                                                          pass if LCB > 2/3
```

Sweep `n = 2, 3, 4, …` until a width fails. `QV = 2 ^ (n - 1)`.

## Practical defaults

- **`n_circuits ≥ 100`** per width is the Cross-et-al recommendation;
  fewer circuits widens the confidence interval and increases the
  chance of a false fail.
- **`shots ≥ 1000`** per circuit. `dummy:local:simulator` ignores this;
  real hardware needs it.
- **`seed=...`** for reproducibility — always pass an explicit seed
  list `[0, 1, 2, …, n_circuits - 1]` so two runs against different
  backends compare apples to apples.
- For first-time real-hardware QV, start at `n=2` then climb. A QV-2
  failure usually means readout / single-qubit error is dominating —
  fix that before increasing width.
- `dry_run` against `dummy:originq:<chip>` first to ensure the
  compile-against-chip pass works (qiskit is core in 0.0.13 — no
  extra needed).
- Apply readout EM (`uniqc-xeb-qem` skill) to the counts before the
  heavy-output computation when running on noisy hardware — readout
  alone can drag the mean below 2/3 even when the gate fidelities
  would otherwise pass.

> ⚠️ **Sanity check first**: run the demo against
> `dummy:local:simulator`. The measured mean heavy-output should match
> the *ideal* mean heavy-output (printed by the demo) to within shot
> noise — both will sit around 0.79 (n=2) / 0.85 (n≥3). If you see
> **higher** values, something is wrong (the heavy-set computation has
> a bug, or the measurements skipped). If you see lower values on
> `dummy:local:simulator`, that is impossible — file an issue. The
> 0.85 ceiling is a feature of the protocol, not a bug; see
> `references/protocol.md` for the Porter-Thomas explanation.

## CLI cheat sheet

There is no `uniqc qv` CLI command. The skill is pure-Python; if you
want a CLI experience, run `examples/qv_demo.py`:

```bash
python qv_demo.py --backend dummy:local:simulator --n 3 --n_circuits 50 --shots 1000
python qv_demo.py --backend originq:WK_C180     --n 2 --n_circuits 200 --shots 1000
```

## Python cheat sheet

```python
import numpy as np
from qiskit.circuit import ClassicalRegister
from qiskit.circuit.library import quantum_volume
from qiskit.qasm2 import dumps

from uniqc import Circuit, submit_batch, wait_for_result
from uniqc.simulator import Simulator


def build_qv(n: int, *, seed: int) -> Circuit:
    """Square QV: width n, depth n. Returns a uniqc Circuit with measurements."""
    qc = quantum_volume(n, n, seed=seed)
    qc.add_register(ClassicalRegister(n, "c"))
    qc.measure(range(n), range(n))
    qasm = dumps(qc.decompose().decompose().decompose())   # to basis gates
    return Circuit.from_qasm(qasm)


def heavy_set(circuit: Circuit, *, n: int) -> tuple[set[int], float]:
    """Indices x with p_ideal(x) > median, and the median."""
    sim   = Simulator(backend_type="statevector")
    probs = np.asarray(sim.simulate_pmeasure(circuit.originir))
    median = float(np.median(probs))
    return {int(i) for i, p in enumerate(probs) if p > median}, median


def heavy_freq(counts: dict, heavy: set[int], *, n: int) -> float:
    """Frequency of heavy outputs in the sampled counts."""
    total = sum(counts.values()) or 1
    hits = 0
    for bits, c in counts.items():
        # uniqc counts keys are bitstrings (little-endian: q0 rightmost)
        idx = int(bits, 2)
        if idx in heavy:
            hits += c
    return hits / total


def run_qv(backend: str, n: int, n_circuits: int = 100, shots: int = 1000):
    circuits, heavies = [], []
    for s in range(n_circuits):
        c = build_qv(n, seed=s)
        h, _ = heavy_set(c, n=n)
        circuits.append(c); heavies.append(h)

    uid = submit_batch(circuits, backend=backend, shots=shots)
    results = wait_for_result(uid, timeout=900)
    freqs = np.array([heavy_freq(r.counts, h, n=n) for r, h in zip(results, heavies)])

    mean   = float(freqs.mean())
    sigma  = float(freqs.std(ddof=1))
    lcb_2sigma = mean - 2 * sigma / np.sqrt(n_circuits)
    return {"mean": mean, "lcb_2sigma": lcb_2sigma, "pass": lcb_2sigma > 2 / 3}
```

## Names to remember

- `qiskit.circuit.library.quantum_volume(n, depth, seed=...)` — circuit
  factory (note: `QuantumVolume` *class* form is deprecated since
  qiskit 2.2; use the function form).
- `Circuit.from_qasm(qasm_str)` — load qiskit's QASM2 dump.
- `submit_batch(circuits, backend=...)` — one `uqt_*` for the whole
  sweep, returns `list[UnifiedResult]` after `wait_for_result`.
- `Simulator(backend_type="statevector").simulate_pmeasure(originir)`
  — ideal probabilities for the heavy-set computation.
- Pass rule: mean heavy-output probability minus `2σ / sqrt(N)` > 2/3.

## Response style

- Always run the protocol on `dummy:local:simulator` first as a
  sanity check — ideal QV of every width should land near 0.85 mean
  heavy-output (the asymptotic Porter-Thomas value).
- Report `mean ± 2σ/√N`, the 2/3 threshold, and the pass/fail
  decision — never just the mean.
- For a width that fails, say what the dominant suspect is
  (readout vs gates vs queue / decoherence) — XEB and readout
  calibration on the same chip narrow it down quickly.
- `QV = 2^n_max` is the canonical figure of merit; report it
  alongside the per-width breakdown.
