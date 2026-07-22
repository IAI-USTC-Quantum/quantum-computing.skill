"""MPS simulator usage example for the uniqc-basic-usage skill.

Demonstrates two surfaces:

1. Direct ``MPSSimulator`` API for very large 1-D nearest-neighbour circuits.
2. ``dummy:local:mps-linear-N`` backend through ``submit_task`` / ``wait_for_result``.

Requires ``unified-quantum >= 0.0.11`` (the release that ships
``uniqc.simulator.MPSSimulator``).
"""

from __future__ import annotations

from uniqc import Circuit
from uniqc.backend_adapter.task_manager import submit_task, wait_for_result
from uniqc.simulator import MPSConfig, MPSSimulator


def linear_ghz(n: int) -> Circuit:
    c = Circuit(n)
    c.h(0)
    for i in range(n - 1):
        c.cnot(i, i + 1)
    for q in range(n):
        c.measure(q)
    return c


def main() -> None:
    # 1) Direct API: 64-qubit GHZ via per-site MPS sampling.
    c = linear_ghz(64)
    sim = MPSSimulator(MPSConfig(chi_max=64, svd_cutoff=1e-12, seed=0))
    counts = sim.simulate_shots(c.originir, shots=400)
    print(f"direct MPS: max bond = {sim.max_bond}")
    print(f"  observed keys (only all-0 / all-1 expected): {sorted(counts.keys())}")
    print(f"  total shots = {sum(counts.values())}")

    # 2) dummy backend with χ truncation forced via the identifier suffix.
    task = submit_task(
        c,
        backend="dummy:local:mps-linear-64:chi=8:cutoff=1e-10",
        shots=400,
    )
    result = wait_for_result(task, timeout=60)
    print(f"dummy:local:mps-linear-64 result = {result}")


if __name__ == "__main__":
    main()
