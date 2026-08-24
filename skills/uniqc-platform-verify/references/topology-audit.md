# Topology audit

The platform tells you (via the backend cache):

- `bi.qubits.n_qubits` — total qubits.
- `bi.qubits.available_qubits` — currently usable.
- `bi.qubits.coupling_map` — pairs that support a native 2q gate.
- `bi.basis_gates` — supported gate names.

Every entry deserves a one-shot probe before you trust it.

## Probe each available qubit

```python
from uniqc import Circuit, find_backend, submit_task, wait_for_result

CHIP = "originq:WK_C180"
bi = find_backend(CHIP)

bad_qubits = []
for q in sorted(bi.qubits.available_qubits):
    c = Circuit(bi.qubits.n_qubits)
    c.x(q); c.measure(q)
    uid = submit_task(c, backend=CHIP, shots=200)
    r = wait_for_result(uid, timeout=120)
    if r is None:
        bad_qubits.append((q, "submit failed"))
        continue
    # |1> should dominate; readout error is what we're measuring.
    bit_q_idx = bi.qubits.n_qubits - 1 - q     # uniqc default little-endian (c[0]=LSB)
    p1 = sum(n for k, n in r.counts.items() if k[bit_q_idx] == "1") / r.shots
    if p1 < 0.5:                                 # cripplingly bad readout
        bad_qubits.append((q, f"P(|1>)={p1:.2f}"))

print("Qubits worse than 50% readout-1:", bad_qubits)
```

> uniqc 0.0.13 enforces `c[0] = LSB` end-to-end across every adapter
> (OriginQ / dummy / simulator / IBM / …). Don't hand-reverse for any platform.

## Probe each coupling pair

```python
from uniqc.algorithms.workflows import xeb_workflow

failures = []
for (i, j) in bi.qubits.coupling_map:
    try:
        result = xeb_workflow.run_2q_xeb_workflow(
            backend=CHIP, pairs=[(i, j)],
            depths=[5, 10], n_circuits=10, shots=500,
        )
        f = list(result.values())[0].fidelity_per_layer
        if f < 0.90:
            failures.append((i, j, f))
    except Exception as exc:
        # uniqc 0.0.13 strict pre-flight will raise *before* dispatching
        # if the pair has no calibrated CZ — that's a real audit finding.
        failures.append((i, j, repr(exc)))

print("Pairs worse than 90% / pre-flight failed:", failures)
```

## Probe the basis-gate list

```python
from uniqc import Circuit, dry_run_task

passed, missing = [], []
for g in bi.basis_gates:
    c = Circuit(2)
    if g.lower() in {"h", "x", "y", "z", "sx", "s", "t", "i"}:
        getattr(c, g.lower())(0)
    elif g.lower() in {"cz", "cnot", "swap", "iswap", "ecr"}:
        getattr(c, g.lower())(0, 1)
    elif g.lower() in {"rx", "ry", "rz"}:
        getattr(c, g.lower())(0, 0.0)
    c.measure(0); c.measure(1)
    check = dry_run_task(c, backend=CHIP, shots=10)
    (passed if check.success else missing).append(g)

print("compiles:", passed)
print("missing :", missing)        # nominally-supported gates that fail compile
```

## What "topology audit" output should look like

For each chip:

```
Chip: originq:WK_C180
  cached_at: 2026-05-14T08:00:00Z
  refreshed_at: 2026-05-14T15:42:00Z

  qubits:
    nominal:    169
    available:  151           (18 retired)
    bad_readout (P(|1>)<0.5): []

  topology:
    pairs:                     312
    pairs_low_fidelity (<.90): [(58,68), (114,121)]
    pairs_pre_flight_failed:   [(13,14), (21,22), (60,61)]

  basis_gates:
    advertised: ['cz', 'sx', 'rz', 'rx', 'measure', 'reset']
    compile_ok: ['cz', 'sx', 'rz', 'rx']
    compile_fail: ['measure', 'reset']    # advisory; these are not gates
```

Anything in `pairs_pre_flight_failed` was caught **before** the
hardware was touched — uniqc 0.0.13's pre-flight is doing its job.

## Notes

- **`bi.qubits.qubit_info[i]`** carries vendor-published values
  (single-qubit error, T1, T2, readout). Compare to the measured
  values from `xeb_workflow` / readout calibration; cf.
  `fidelity-audit.md`.
- **OriginQ chip names are case-sensitive** on real submit. The
  `dummy:originq:<chip>` rule path accepts lowercase aliases; do
  **not** carry that habit into real audits.
- **For IBM** the topology can be queried via
  `bi.qubits.coupling_map` after an explicit `uniqc backend update
  --platform ibm` (works as of 0.0.13; previously stayed stale).
