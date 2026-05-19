"""Smoke test for uniqc-xeb-qem.
Tests: run_readout_em_workflow, ReadoutEM.apply pipeline.
"""
import sys


def main() -> int:
    from uniqc import Circuit, submit_task, wait_for_result
    from uniqc.algorithms.workflows import readout_em_workflow

    em = readout_em_workflow.run_readout_em_workflow(
        backend="dummy:local:simulator", qubits=[0, 1], pairs=[(0, 1)], shots=100
    )
    assert em is not None, "ReadoutEM is None"

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    uid = submit_task(c, backend="dummy:local:simulator", shots=100)
    result = wait_for_result(uid, timeout=30)
    clean = em.apply(result)
    assert clean.counts, "Mitigated result has no counts"

    print("PASS: ReadoutEM calibration + apply pipeline OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())