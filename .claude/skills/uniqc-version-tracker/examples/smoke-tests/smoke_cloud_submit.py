"""Smoke test for uniqc-cloud-submit.
Tests: find_backend, dry_run_task, compile, submit_task with provider:chip.
"""
import sys


def main() -> int:
    from uniqc import Circuit, find_backend, dry_run_task, compile, submit_task, wait_for_result

    backend_id = "dummy:local:virtual-line-3"
    bi = find_backend(backend_id)
    assert isinstance(bi.num_qubits, int), "BackendInfo num_qubits missing"

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    check = dry_run_task(c, backend=backend_id, shots=10)
    assert check.success, f"Dry-run failed: {check.error}"

    compiled = compile(c, bi)
    uid = submit_task(compiled, backend=backend_id, shots=10)
    result = wait_for_result(uid, timeout=30)
    assert result is not None, "No result from submit_task"

    print("PASS: find_backend -> dry_run -> compile -> submit_task all OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())