# pyqpanda3 ↔ uniqc

Install the OriginQ optional dependency before using pyqpanda3 objects:

```bash
pip install "unified-quantum[originq]"
```

On supported Python versions, convert a uniqc circuit with
`Circuit.to_pyqpanda3_circuit()`. Conversely, pass a pyqpanda3 circuit to
`normalize_to_circuit()` or directly to `simulate`, `compile`, or
`submit_task`; these public entry points accept `AnyQuantumCircuit`.

pyqpanda3 conversion uses OriginIR internally. Custom pyqpanda3 macros that
have no OriginIR mapping cannot round-trip and should be decomposed before
conversion. The `[originq]` extra is unavailable on Python 3.14 until
pyqpanda3 publishes compatible wheels.
