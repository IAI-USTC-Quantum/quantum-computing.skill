"""Smoke test for uniqc-result-analysis.
Tests: UnifiedResult field access, plot_histogram/plot_distribution imports.
"""
import sys


def main() -> int:
    from uniqc import Circuit, submit_task, wait_for_result
    from uniqc.visualization import plot_histogram, plot_distribution

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    uid = submit_task(c, backend="dummy:local:simulator", shots=100)
    result = wait_for_result(uid, timeout=30)

    assert result.counts, "Empty counts"
    assert result.shots == 100, f"Expected 100 shots, got {result.shots}"
    assert result.platform == "dummy", f"Expected dummy platform, got {result.platform}"

    total = sum(result.counts.values())
    assert total == 100, f"Count sum {total} != 100"

    assert callable(plot_histogram), "plot_histogram is not callable"
    assert callable(plot_distribution), "plot_distribution is not callable"

    print("PASS: UnifiedResult fields + visualization imports OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())