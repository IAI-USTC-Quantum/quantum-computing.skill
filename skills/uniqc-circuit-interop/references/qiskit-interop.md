# qiskit ↔ uniqc

qiskit (and `qiskit-aer`, `qiskit-ibm-runtime`) is a **core dependency**
of uniqc 0.0.13 — no `[qiskit]` extra needed. Conversion in either
direction is a single call.

## uniqc → qiskit

```python
from uniqc import Circuit

c = Circuit(2)
c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)

qc = c.to_qiskit_circuit()       # qiskit.QuantumCircuit
print(qc.draw())
print(qc.qregs, qc.cregs)
```

Behaviour:

- Quantum and classical registers are emitted (named `q` and `c`).
- Numeric gate parameters round-trip cleanly.
- `uniqc.Parameter` symbolic params become qiskit `Parameter` objects.
- Measurements come through as qiskit `measure` instructions.

## qiskit → uniqc

Three equivalent paths; pick by ergonomics.

```python
from qiskit.circuit import QuantumCircuit, ClassicalRegister
from uniqc import normalize_to_circuit

qc = QuantumCircuit(2, 2)
qc.h(0); qc.cx(0, 1); qc.measure([0, 1], [0, 1])

# (a) Universal normalize: returns a NormalizedCircuit (.circuit + .type tag)
nc = normalize_to_circuit(qc)
print(nc.type, type(nc.circuit))            # 'qiskit', uniqc.Circuit
c1 = nc.circuit

# (b) Pass qc directly into any AnyQuantumCircuit-accepting API
from uniqc import submit_task
uid = submit_task(qc, backend="dummy:local:simulator", shots=200)

# (c) Hand-roll via QASM2
from qiskit.qasm2 import dumps
from uniqc import Circuit
c3 = Circuit.from_qasm(dumps(qc))
```

(a) and (b) are preferred. (c) only when you already have QASM text.

## qiskit-library helpers (e.g. `quantum_volume`)

`qiskit.circuit.library.quantum_volume(n, depth, seed=...)` returns a
circuit whose 2-qubit blocks are `UnitaryGate` instances. Those don't
round-trip through QASM2 — `qiskit.qasm2.dumps` raises
`Qasm2ExporterError`.

Workaround: decompose first.

```python
from qiskit.circuit import ClassicalRegister
from qiskit.circuit.library import quantum_volume
from qiskit.qasm2 import dumps
from uniqc import Circuit

qc = quantum_volume(4, 4, seed=42)
qc.add_register(ClassicalRegister(4, "c"))
qc.measure(range(4), range(4))

decomposed = qc.decompose().decompose().decompose()       # land on u(θ,φ,λ) + cx
qasm = dumps(decomposed)
c = Circuit.from_qasm(qasm)
```

uniqc 0.0.13 `Circuit.from_qasm` accepts `u(θ,φ,λ)` and `cx` (the
post-decomposition basis).

## Pitfalls

- **Empty `creg`**. `Circuit.from_qasm` raises
  `RegisterDefinitionError: Register is empty` if the QASM has no
  classical register. Always declare and use one
  (`add_register(ClassicalRegister(n, "c"))`, then `measure(...)`).
- **`Parameter` collisions across `qc.assign_parameters(...)`**. If
  the qiskit circuit has bound + unbound parameters, decide which
  side owns binding. `Circuit.to_qiskit_circuit()` carries unbound
  symbols across; bind on the qiskit side if you want a numeric circuit.
- **Endianness on display**. qiskit displays bitstrings big-endian by
  default (`qreg[0]` on the left). uniqc and the rest of the pipeline
  are little-endian (`c[0]` on the right). Since 0.0.13 uniqc enforces
  `c[0] = LSB` end-to-end across every adapter — drop any
  hand-reversal you may have added pre-0.0.13.
- **`qiskit-aer` is in core**. You no longer need `pip install
  unified-quantum[qiskit]`. If qiskit is missing, reinstall uniqc.

## Verifying a conversion

```python
import numpy as np
from uniqc.simulator import Simulator

# Round-trip equality at the statevector level (ignore phase).
sv_uniqc  = Simulator("statevector").simulate_statevector(c)
sv_qiskit = Simulator("statevector").simulate_statevector(c.to_qiskit_circuit())
inner = np.vdot(sv_uniqc, sv_qiskit)
assert abs(abs(inner) - 1.0) < 1e-9, f"differ: |<ψ|φ>|={abs(inner)}"
```
