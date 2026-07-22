"""Smoke test for uniqc-basic-usage.
Tests: Circuit construction, local simulation, dummy submission, and the
offline YAML virtual-backend lifecycle.
"""
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


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

    scratch_home = Path.cwd() / f".uniqc-smoke-{uuid.uuid4().hex}"
    try:
        scratch_home.mkdir()
        env = os.environ | {"HOME": str(scratch_home)}
        uniqc_bin = str(Path(sys.executable).parent / "uniqc")

        def run(*command: str) -> subprocess.CompletedProcess[str]:
            result = subprocess.run(
                [uniqc_bin, *command], env=env, capture_output=True, text=True, timeout=30
            )
            assert result.returncode == 0, (
                f"{' '.join(command)} exited {result.returncode}: {result.stderr[-300:]}"
            )
            return result

        run("backend", "virtual", "init", "smoke-machine")
        config = scratch_home / ".uniqc" / "backend" / "virtual" / "smoke-machine.yaml"
        config.write_text(
            """num_qubits: 2
topology:
  - [0, 1]
gate_times_ns:
  default_1q: 30
  default_2q: 80
noise:
  depolarizing: {1q: 0.001, 2q: 0.01}
  thermal_relaxation:
    default: {t1_us: 50, t2_us: 40}
""",
            encoding="utf-8",
        )
        assert "smoke-machine" in run("backend", "virtual", "list").stdout
        assert "dummy:virtual:smoke-machine" in run("backend", "virtual", "show", "smoke-machine").stdout
        assert "valid" in run("backend", "virtual", "validate", "smoke-machine").stdout.lower()

        circuit_file = scratch_home / "bell.qasm"
        circuit_file.write_text(
            """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;
""",
            encoding="utf-8",
        )
        run(
            "submit",
            str(circuit_file),
            "--backend",
            "dummy:virtual:smoke-machine",
            "--shots",
            "32",
            "--wait",
        )
    finally:
        shutil.rmtree(scratch_home, ignore_errors=True)

    print("PASS: Circuit + dummy + virtual YAML init/list/show/validate/submit OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())