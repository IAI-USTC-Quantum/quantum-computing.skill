# Parsing OriginIR and OpenQASM 2.0

Pass a string directly to `normalize_to_circuit()` whenever possible. It
records the source type and yields the canonical `Circuit`:

```python
from pathlib import Path
from uniqc import normalize_to_circuit

source = Path("circuit.qasm").read_text()
normalized = normalize_to_circuit(source)
circuit = normalized.circuit
print(normalized.type)  # "qasm" or "originir"
```

For an explicitly QASM-only path, use `Circuit.from_qasm(text)`. QASM 2.0
input needs a `creg` when it contains measurements. For parser-level
diagnostics, use `OpenQASM2_BaseParser` or `OriginIR_BaseParser`, call
`.parse(text)`, then `.to_circuit()`.

`Circuit.originir` emits OriginIR-ext by default. Local parsing and
simulation accept it; use `Circuit.to_originir_official()` only at the
OriginQ cloud boundary.
