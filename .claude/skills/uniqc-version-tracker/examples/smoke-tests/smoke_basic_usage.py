"""Smoke test for uniqc-basic-usage.
Tests: Circuit construction, Simulator.simulate_pmeasure, submit_task to dummy.
"""
import sys


def main() -> int:
    from uniqc import Circuit, submit_task, wait_for_result
    from uniqc.simulator import Simulator

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    probs = Simulator(backend_type="statevector").simulate_pmeasure(c)
    assert len(probs) == 4, f"Expected 4 probabilities, got {len(probs)}"

    uid = submit_task(c, backend="dummy:local:simulator", shots=100)
    result = wait_for_result(uid, timeout=30)
    assert result is not None and result.counts, "No counts returned from dummy submit"

    print("PASS: Circuit -> simulate_pmeasure -> dummy submit all OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())