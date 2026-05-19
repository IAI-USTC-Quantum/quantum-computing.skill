"""Smoke test for uniqc-noise-simulation.
Tests: NoisySimulator with Depolarizing, chip-backed dummy (dummy:originq:WK_C180).
"""
import sys


def main() -> int:
    from uniqc import Circuit, submit_task, wait_for_result
    from uniqc.simulator import NoisySimulator
    from uniqc.simulator.error_model import Depolarizing, ErrorLoader_GenericError

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    loader = ErrorLoader_GenericError(generic_error=[Depolarizing(0.001)])
    noisy = NoisySimulator(error_loader=loader)
    counts = noisy.simulate_shots(c, shots=200)
    assert counts, "Noisy simulator returned no counts"
    assert sum(counts.values()) == 200, f"Shot sum mismatch: {sum(counts.values())}"

    uid = submit_task(c, backend="dummy:local:virtual-line-3", shots=100)
    result = wait_for_result(uid, timeout=60)
    assert result is not None and result.counts, "Dummy virtual-line returned no counts"

    print("PASS: NoisySimulator + dummy backend OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())