"""Smoke test for uniqc-quantum-ml.
Tests: QuantumLayer via circuit_def pattern. Skips if torch not installed.
Also verifies the v0.0.15 top-level `uniqc.expectation()` export and the
native PyTorch parameter integration entry points (`Circuit.param_map`,
`Circuit.param_dict`, `Circuit.has_param`).
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

    # v0.0.15: top-level `expectation` export must exist.
    import uniqc
    assert hasattr(uniqc, "expectation"), "v0.0.15 top-level uniqc.expectation is missing"

    # v0.0.15: native torch-param integration on Circuit.
    from uniqc import Circuit
    c = Circuit(1)
    theta = torch.tensor(0.3, requires_grad=True)
    c.rx(0, theta)
    assert c.has_param, "Circuit.has_param should be True for tensor param"
    assert "rx_0" in c.param_dict or len(c.param_dict) >= 1, "Circuit.param_dict empty after add"
    assert len(c.param_map) >= 1, "Circuit.param_map empty after add"

    print("PASS: QuantumLayer + native torch params (param_map/param_dict/has_param) + uniqc.expectation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())