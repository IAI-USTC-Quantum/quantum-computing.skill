# State preparation algorithms

All return a fresh `Circuit`; compose with `Circuit.add_circuit(frag)`.

## GHZ — `(|0…0⟩ + |1…1⟩)/√2`

```python
from uniqc import Circuit, ghz_state

frag = ghz_state(qubits=[0, 1, 2])    # 3-qubit GHZ on qubits 0..2
# frag.draw() to inspect

prog = Circuit(3)
prog.add_circuit(frag)
for q in range(3):
    prog.measure(q)
```

Statevector check:

```python
from uniqc.simulator import Simulator
sim = Simulator(backend_type="statevector")
sv = sim.simulate_statevector(prog.originir)
# Expect amplitudes 1/√2 at index 0 (|000>) and 7 (|111>).
```

## W state — `(|001⟩ + |010⟩ + |100⟩)/√3`

```python
from uniqc import w_state
frag = w_state(qubits=[0, 1, 2])
```

Used as a benchmarking state for entanglement; differs from GHZ in
robustness to single-qubit loss.

## Dicke state — `|n choose k|^{-1/2} Σ_{|x|=k} |x⟩`

```python
from uniqc import dicke_state_circuit
frag = dicke_state_circuit(k=2, qubits=[0, 1, 2, 3])     # all 4-bit strings of weight 2
```

`k` controls Hamming weight; `qubits` controls width. For `k=1`, equals
the W state.

## Cluster state — measurement-based universal resource

```python
from uniqc import cluster_state
edges = [(0, 1), (1, 2), (2, 3)]                        # path graph
frag = cluster_state(qubits=[0, 1, 2, 3], edges=edges)
```

Without explicit `edges`, defaults to a chain on `qubits`.

## Thermal state (toy)

```python
from uniqc import thermal_state_circuit
frag = thermal_state_circuit(beta=1.0, qubits=[0, 1, 2])
```

This is a *demonstration* construction (not a full Gibbs state preparer).
For research-quality thermal-state preparation, fall back to QITE / VQT.

## Validating prepared states

```python
from uniqc import StateTomography
tomo = StateTomography(frag, qubits=[0, 1, 2])
rho = tomo.execute(backend="dummy:local:simulator", shots=4096)

from uniqc.algorithms.core.measurement import tomography_summary
summary = tomography_summary(rho, print_summary=True)
# eigenvalues / purity / trace / fidelity
```

## Common mistakes

- Calling the legacy in-place form `ghz_state(circuit, qubits=...)` —
  **removed in 0.1.0** (it now raises instead of mutating). Use the
  fragment form: `circuit.add_circuit(ghz_state(n, qubits=...))`.
- Forgetting to add `prog.measure(q)` before sampling. Statevector
  inspection works without it; counts-based sampling does not.
- Picking `qubits=[0, 1, 2]` when your `Circuit` only has `n_qubits=2`
  — `add_circuit` raises `IndexError`. Build the parent circuit large
  enough first.
