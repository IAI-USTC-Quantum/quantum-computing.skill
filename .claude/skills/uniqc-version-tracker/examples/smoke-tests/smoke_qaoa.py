"""Smoke test for uniqc-qaoa.
Tests: qaoa_ansatz, pauli_expectation, run_qaoa_workflow.
"""
import sys


def main() -> int:
    from uniqc import qaoa_ansatz
    from uniqc.algorithms.core.measurement import pauli_expectation
    from uniqc.algorithms.workflows.qaoa_workflow import run_qaoa_workflow

    cost_compact = [("ZZI", 1.0), ("IZZ", 1.0), ("ZIZ", 1.0)]
    result = run_qaoa_workflow(
        cost_compact, n_qubits=3, p=1, method="COBYLA", options={"maxiter": 10}
    )
    assert result.energy is not None, "QAOA workflow returned no energy"

    cost_indexed = [("Z0Z1", 1.0), ("Z1Z2", 1.0), ("Z0Z2", 1.0)]
    circuit = qaoa_ansatz(cost_indexed, p=1, betas=[0.5], gammas=[0.5])
    energy = sum(c * pauli_expectation(circuit, ps) for ps, c in cost_indexed)
    assert isinstance(energy, (int, float, complex)), f"Bad energy type: {type(energy)}"

    print("PASS: QAOA workflow + hand-rolled ansatz OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())