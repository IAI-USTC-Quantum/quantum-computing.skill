"""Smoke test for uniqc-quantum-volume.
Tests: QV circuit via qiskit, Circuit.from_qasm, heavy-set computation.
Skips if qiskit not installed (qiskit is a core dep in uniqc>=0.0.13 but the
smoke harness may run against a stale environment).
"""
import sys

import numpy as np


def main() -> int:
    try:
        from qiskit.circuit import ClassicalRegister
        from qiskit.circuit.library import quantum_volume
        from qiskit.qasm2 import dumps
    except ImportError:
        print("SKIP: qiskit not installed (expected as core dep in uniqc>=0.0.13)")
        return 0

    from uniqc import Circuit
    from uniqc.simulator import Simulator

    n = 2
    qc = quantum_volume(n, n, seed=0)
    qc.add_register(ClassicalRegister(n, "c"))
    qc.measure(range(n), range(n))
    qasm = dumps(qc.decompose().decompose().decompose())
    circuit = Circuit.from_qasm(qasm)

    sim = Simulator(backend_type="statevector")
    probs = np.asarray(sim.simulate_pmeasure(circuit.originir))
    median = float(np.median(probs))
    heavy = {int(i) for i, p in enumerate(probs) if p > median}
    assert len(heavy) > 0, "Heavy set is empty"

    print(f"PASS: QV n={n} circuit + heavy set ({len(heavy)} heavy outputs of {len(probs)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())