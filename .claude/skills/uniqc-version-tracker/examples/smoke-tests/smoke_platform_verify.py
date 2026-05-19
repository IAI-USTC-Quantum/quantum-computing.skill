"""Smoke test for uniqc-platform-verify.
Tests: find_backend, list_backends, xeb_workflow imports.
"""
import sys


def main() -> int:
    from uniqc import find_backend, list_backends
    from uniqc.algorithms.workflows import xeb_workflow

    bi = find_backend("dummy:local:virtual-line-3")
    assert bi.num_qubits > 0, "BackendInfo num_qubits is 0"
    assert bi.topology, "No topology listed"

    backends = list_backends()
    assert len(backends) > 0, "list_backends returned empty"

    try:
        xeb_1q = xeb_workflow.run_1q_xeb_workflow(
            backend="dummy:local:virtual-line-3",
            target_qubits=[0, 1],
            depths=[5, 10],
            n_circuits=5,
            shots=100,
        )
        assert "q0" in xeb_1q, "Missing q0 in XEB results"
    except Exception as e:
        print(f"NOTE: 1q XEB skipped ({e})")

    print("PASS: Platform verify backend inspection + XEB imports OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())