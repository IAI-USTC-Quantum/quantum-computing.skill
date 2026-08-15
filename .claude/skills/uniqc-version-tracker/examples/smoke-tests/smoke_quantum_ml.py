"""Smoke test for uniqc-quantum-ml's native and TorchQuantum backends."""
import sys


def main() -> int:
    try:
        import torch  # noqa: F401
    except ImportError:
        print("SKIP: torch not installed (optional dependency)")
        return 0

    try:
        import torchquantum as tq
    except ImportError:
        print("SKIP: torchquantum not installed (optional dependency)")
        return 0

    from uniqc import Circuit, expectation
    from uniqc.simulator.torchquantum_simulator import TorchQuantumSimulator

    c = Circuit(1)
    theta = torch.tensor(0.3, requires_grad=True)
    c.rx(0, theta)
    assert c.has_param, "Circuit.has_param should be True for tensor param"
    assert len(c.param_map) >= 1, "Circuit.param_map empty after add"

    native = expectation(c, [("Z", 1.0)], backend="virtual")
    assert native.shape == torch.Size([]) and native.requires_grad, "Native expectation is not differentiable"
    native.backward()

    qdev = tq.QuantumDevice(n_wires=1, bsz=1)
    tq.RX(has_params=True, trainable=True)(qdev, wires=0)
    assert qdev.get_states_1d().shape[-1] == 2, "TorchQuantum gate forward failed"

    tq_sim = TorchQuantumSimulator(n_wires=1)
    tq_value = tq_sim.expectation(c.opcode_list, [("Z", 1.0)], c.param_map, n_qubits=1)
    assert tq_value.shape == torch.Size([]), "TorchQuantum expectation returned an invalid shape"

    print("PASS: native tensor expectation + TorchQuantum import/build/forward OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())