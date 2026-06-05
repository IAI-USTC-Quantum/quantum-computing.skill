# Authoring quantum-program files

A "quantum-program file" is anything `uniqc submit` can read directly.
Currently that means **`.originir` / `.qasm`** plus any Python script that
constructs a `Circuit` and exports one of those. This page shows the
shortest path from a Python `Circuit` to a file the CLI can submit.

## Build the circuit in Python

```python
# build_circuit.py
from uniqc import Circuit

c = Circuit(2)
c.h(0)
c.cnot(0, 1)
c.measure(0)        # measure to default cbit 0
c.measure(1)
print(c.originir)   # human-readable OriginIR
print(c.qasm)       # OpenQASM 2.0
```

> Both `.originir` and `.qasm` are **properties** (no parentheses).
> `c.originir()` raises `TypeError: 'str' object is not callable`.

## Persist as `.originir` (recommended for OriginQ + dummy)

```python
from pathlib import Path
Path("circuit.originir").write_text(c.originir)
```

`uniqc submit circuit.originir --backend ...` will read it directly.

### OriginIR vs OriginIR-ext (uniqc ≥ 0.0.15)

As of uniqc 0.0.15, `c.originir` returns **OriginIR-ext** by default
(a strict superset that adds `ECR`/`ISWAP`/`XX`/`YY`/`ZZ`/`XY`/`PHASE2Q`/
`UU15`/`RPhi*`, `QRAM`, `DEF`/`ENDDEF`, inline `dagger`/`controlled_by(...)`,
error channels). For plain circuits (H/CNOT/RX/RY/RZ/CZ/MEASURE …) the two
forms are byte-identical, so the snippet above keeps working. If your
circuit uses any ext-only construct **and** you submit to OriginQ real
hardware, persist the official form instead:

```python
Path("circuit.originir").write_text(c.to_originir_official())
```

For raw text you already have on disk, convert with:

```python
from uniqc.compile import convert_originir_ext_to_originir
official = convert_originir_ext_to_originir(Path("circuit.originir").read_text())
```

Local `Simulator` / `NoisySimulator` and `dummy:*` backends accept both
languages — no conversion needed for sanity-check runs.

## Persist as `.qasm` (recommended for IBM / Quafu)

```python
Path("circuit.qasm").write_text(c.qasm)
```

For IBM/Quafu uniqc auto-converts at submit time, so writing OriginIR is
also fine — but storing the QASM you actually intend to submit avoids a
round-trip.

## Persist as a `.py` script (cleanest for reuse)

```python
# emit_circuit.py
"""Build the Bell-state demo circuit and write program files."""
from pathlib import Path
from uniqc import Circuit

def build() -> Circuit:
    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)
    return c

if __name__ == "__main__":
    c = build()
    Path("circuit.originir").write_text(c.originir)
    Path("circuit.qasm").write_text(c.qasm)
    print("wrote circuit.originir, circuit.qasm")
```

Submit from the CLI:

```bash
python emit_circuit.py
uniqc submit circuit.originir --backend dummy:local:simulator --shots 1000 --dry-run
```

## Bigger circuits — fragment composition

`uniqc` exports algorithm fragments that **return a new `Circuit`** — these
compose with `add_circuit`:

```python
from uniqc import Circuit, qft_circuit, ghz_state, hea, qaoa_ansatz

# QFT on first 4 qubits
prog = Circuit(5)
prog.add_circuit(ghz_state(3))            # 3-qubit GHZ on qubits 0..2
prog.add_circuit(qft_circuit(4), qubits=[1, 2, 3, 4])
for q in range(5):
    prog.measure(q)
print(prog.originir)
```

(For the legacy in-place `fn(circuit, ...)` form: it still works on the
current release but emits `DeprecationWarning`. New code should use the
fragment form above.)

## Round-trip from `.originir` back to a `Circuit`

```python
from uniqc import Circuit
c2 = Circuit.from_originir(Path("circuit.originir").read_text())
```

Use this when the user gives you a file and you need to inspect or modify
it before submission.

## Format conversion via the CLI

```bash
uniqc circuit convert circuit.originir --to qasm > circuit.qasm
uniqc circuit convert circuit.qasm --to originir > circuit.originir
```

This is the one-liner for "I only have a QASM file but my backend wants
OriginIR" (or vice versa).

## Validation before submit

```bash
uniqc simulate circuit.originir --shots 1000               # local sanity
uniqc submit  circuit.originir --backend dummy:local:simulator --dry-run   # backend sanity
```

If both pass, you are clear to run the real submit (see
[submit-and-poll.md](submit-and-poll.md)).
