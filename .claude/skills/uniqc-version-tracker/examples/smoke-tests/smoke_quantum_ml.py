"""Smoke test for uniqc-quantum-ml.
Tests: QuantumLayer via circuit_def pattern. Skips if torch not installed.
"""
import sys
import math


def main() -> int:
    try:
        import torch  # noqa: F401
    except ImportError:
        print("SKIP: torch not installed (optional dependency)")
        return 0

    from uniqc import circuit_def, QuantumLayer
    from uniqc.algorithms.core.measurement import pauli_expectation

    @circuit_def(name="smoke_rx", qregs={"q": 1}, params=["theta"])
    def smoke_rx(circ, q, theta):
        circ.rx(q[0], theta[0])
        return circ

    qc = smoke_rx.build_standalone()
    layer = QuantumLayer(
        circuit=qc,
        expectation_fn=lambda c: pauli_expectation(c, "Z0"),
        n_outputs=1,
        init_params=torch.tensor([0.5]),
        shift=math.pi / 2,
    )
    output = layer()
    assert output is not None, "QuantumLayer forward pass returned None"

    print("PASS: QuantumLayer OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())