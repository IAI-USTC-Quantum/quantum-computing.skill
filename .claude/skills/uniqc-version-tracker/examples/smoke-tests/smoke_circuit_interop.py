"""Smoke test for uniqc-circuit-interop.
Tests: Circuit.to_qiskit_circuit, .originir/.qasm exports, from_qasm round-trip,
normalize_to_circuit.
"""
import sys


def main() -> int:
    from uniqc import Circuit, normalize_to_circuit

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    originir = c.originir
    assert "H q[0]" in originir, f"OriginIR missing H gate: {originir[:80]}"

    qasm = c.qasm
    assert "OPENQASM" in qasm, f"QASM missing header: {qasm[:80]}"

    try:
        qc = c.to_qiskit_circuit()
        assert qc.num_qubits == 2, f"Expected 2 qubits, got {qc.num_qubits}"
    except ImportError:
        print("WARNING: qiskit not available (should be core in v0.0.13+)")

    c2 = Circuit.from_qasm(qasm)
    assert c2.qubit_num == 2, f"Round-trip lost qubits: got {c2.qubit_num}"

    nc = normalize_to_circuit(qasm)
    assert nc.qubit_num == 2, f"normalize_to_circuit: got {nc.qubit_num} qubits"

    print("PASS: Circuit interop exports + round-trip OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())