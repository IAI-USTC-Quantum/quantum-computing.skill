# API reference

## Function-level API

### `classical_shadow(circuit, qubits=None, shots=4096, n_shadow=None, seed=None) -> list[ShadowSnapshot]`

Collects classical-shadow snapshots. Each snapshot draws an independent
uniform random single-qubit Clifford (`X`, `Y`, `Z`-basis rotation) per
qubit, then executes the circuit, then measures.

Args:

- `circuit`: any `AnyQuantumCircuit` input. Must include measurements
  on every qubit you intend to observe.
- `shots`: integer; number of snapshots collected (default `4096`).
- `n_shadow`: optional; if `None` defaults to `shots`. Lets you
  decouple "experimental shots" from "snapshot count" when the
  underlying simulator returns multiple samples per circuit.
- `qubits`: optional list of qubit indices to restrict observation to.
- `seed`: optional int (added in 0.1.0) for reproducible snapshots;
  `None` keeps OS-entropy randomness.

Returns: `list[ShadowSnapshot]`. Each snapshot is a dataclass holding
the random Pauli basis indices and the measured bitstring.

### `shadow_expectation(snapshots, pauli_string) -> float`

Estimates ⟨P⟩ from a previously-collected snapshot list.

`pauli_string` is **compact form** of length `n_qubit`: e.g. `"ZIZ"`
(`Z` on q0, `I` on q1, `Z` on q2). Indexed forms (`"Z0Z2"`) are
**not** accepted by the shadow estimator — convert first by padding
with `I`.

Re-call `shadow_expectation(snapshots, ...)` with as many distinct
Pauli strings as you like — no extra hardware shots needed.

## Class-level API

```python
from uniqc.algorithms.core.measurement import ClassicalShadow

cs = ClassicalShadow(circuit, n_shadow=1000)
random_circuits = cs.get_readout_circuits()      # list[Circuit] (random bases)
cs.execute(backend="dummy:local:simulator", shots=1)   # populates internal snapshots
val = cs.expectation("ZZ")
```

The class API is convenient when you want to drive the random-basis
circuits through your own batching / hardware path; it separates
"build the random-basis circuits" from "execute".

## Workflow driver

```python
from uniqc.algorithms.workflows import classical_shadow_workflow as csw

result = csw.run_classical_shadow_workflow(
    circuit=c,
    pauli_observables=["ZZ", "XX", "YY"],
    shots=2000,
    n_shadow=None,             # default: same as shots
    qubits=None,               # default: all qubits
)

print(result.n_snapshots)
print(result.expectations)
print(result.snapshots[:3])
```

Returns `ShadowWorkflowResult(snapshots, expectations, n_snapshots)`.

## Hardware-friendly batching

`classical_shadow(...)` runs `n_shadow` distinct random-basis
circuits internally. Against a local simulator that's free; against
real hardware that's a job per circuit unless you pre-batch:

```python
from uniqc.algorithms.core.measurement import ClassicalShadow
from uniqc import submit_batch, wait_for_result

cs = ClassicalShadow(c, n_shadow=200)
random_basis_circuits = cs.get_readout_circuits()

# Native-batch submit (uniqc 0.0.12+: returns a single uqt_*; uniqc shards
# server-side once it exceeds adapter.max_native_batch_size).
uid = submit_batch(random_basis_circuits, backend="originq:WK_C180", shots=200)
results = wait_for_result(uid, timeout=600)        # list[UnifiedResult]

# Feed the per-circuit results back into the shadow estimator. The
# exact reconstruction step depends on the chosen ClassicalShadow API
# layer; consult the source if you need to wire raw counts in by hand.
```

For most users the simple in-process path
`run_classical_shadow_workflow(c, ..., shots=N)` is enough; reach for
the batching variant only when hardware queue time matters.
