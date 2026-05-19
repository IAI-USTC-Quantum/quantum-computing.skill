"""Smoke test for uniqc-classical-shadow.
Tests: run_classical_shadow_workflow, classical_shadow, shadow_expectation.
"""
import sys


def main() -> int:
    from uniqc import Circuit
    from uniqc.algorithms.core.measurement import classical_shadow, shadow_expectation
    from uniqc.algorithms.workflows import classical_shadow_workflow as csw

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    result = csw.run_classical_shadow_workflow(c, ["ZZ", "XX", "ZI", "IZ"], n_shadow=200)
    assert "ZZ" in result.expectations, "Missing ZZ in expectations"
    assert result.n_snapshots == 200, f"Expected 200 snapshots, got {result.n_snapshots}"

    snapshots = classical_shadow(c, shots=100)
    zz = shadow_expectation(snapshots, "ZZ")
    assert isinstance(zz, (int, float)), f"Bad shadow_expectation type: {type(zz)}"

    print(f"PASS: Classical shadow workflow + low-level API OK (⟨ZZ⟩≈{zz:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())