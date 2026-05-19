"""Smoke test for uniqc-algorithm-cases.
Tests: ghz_state, qft_circuit, grover_oracle, qpe_circuit.
"""
import sys


def main() -> int:
    from uniqc import Circuit, ghz_state, qft_circuit, grover_oracle
    from uniqc.algorithms.core.circuits import qpe_circuit

    ghz = ghz_state(qubits=[0, 1, 2])
    assert ghz.qubit_num == 3, f"Expected 3 GHZ qubits, got {ghz.qubit_num}"

    qft = qft_circuit(qubits=[0, 1, 2])
    assert qft.qubit_num == 3, f"Expected 3 QFT qubits, got {qft.qubit_num}"

    oracle = grover_oracle(marked_state=5, n_qubits=3)
    assert oracle.qubit_num == 4, f"Expected 4 Grover qubits (3 + 1 ancilla), got {oracle.qubit_num}"

    phi = 0.375
    U = Circuit(1)
    U.rz(0, 2 * 3.141592653589793 * phi)
    prep = Circuit(1)
    prep.x(0)
    qpe = qpe_circuit(n_precision=3, unitary_circuit=U, state_prep=prep, measure=True)
    assert qpe.qubit_num == 4, f"Expected 4 QPE qubits, got {qpe.qubit_num}"

    print("PASS: GHZ, QFT, Grover, QPE fragments all OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())