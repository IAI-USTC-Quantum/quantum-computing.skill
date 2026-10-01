"""Smoke test for uniqc-basic-usage.
Tests: Circuit construction, local simulation, dummy submission, the
offline YAML virtual-backend lifecycle, and the 0.1.1 rendering engine
(Circuit.draw / render + Circuit.to_matrix + `uniqc draw` CLI).
"""
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


def main() -> int:
    import numpy as np

    from uniqc import Circuit, submit_task, wait_for_result
    from uniqc.simulator import Simulator
    from uniqc.visualization import render

    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)

    probs = Simulator(backend_type="statevector").simulate_pmeasure(c)
    assert len(probs) == 4, f"Expected 4 probabilities, got {len(probs)}"

    # 0.1.1 rendering engine: text / svg / latex modes on core deps.
    art = str(c.draw("text", fold=0))
    assert "q[0]" in art and "q[1]" in art, f"text art missing wires: {art!r}"
    svg = render(c, mode="svg")
    assert isinstance(svg, str) and "<svg" in svg, "svg render did not return SVG markup"
    tikz = c.draw("latex")
    assert "quantikz" in tikz, "latex render did not return quantikz source"

    # 0.1.1 full-unitary export: bell state column of the unitary.
    bell = Circuit(2)
    bell.h(0)
    bell.cnot(0, 1)
    u = bell.to_matrix()
    assert u.shape == (4, 4) and np.iscomplexobj(u), f"bad to_matrix shape/dtype: {u}"
    assert np.allclose(u @ u.conj().T, np.eye(4), atol=1e-9), "to_matrix is not unitary"
    assert abs(abs(u[3, 0]) - 2**-0.5) < 1e-9, "to_matrix |00> column is not the bell state"

    uid = submit_task(c, backend="dummy:local:simulator", shots=100)
    result = wait_for_result(uid, timeout=30)
    assert result is not None and result.counts, "No counts returned from dummy submit"

    scratch_home = Path.cwd() / f".uniqc-smoke-{uuid.uuid4().hex}"
    try:
        scratch_home.mkdir()
        # Path.home() on Windows resolves via USERPROFILE, not HOME, so
        # redirect both to keep the scratch isolation cross-platform.
        env = os.environ | {"HOME": str(scratch_home)}
        if os.name == "nt":
            env = env | {"USERPROFILE": str(scratch_home)}
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

        # 0.1.1 `uniqc draw` CLI: text to stdout, svg to a file.
        drawn = run("draw", str(circuit_file), "--fold", "0")
        assert "q[0]" in drawn.stdout, f"uniqc draw text stdout missing wires: {drawn.stdout!r}"
        svg_file = scratch_home / "bell.svg"
        run("draw", str(circuit_file), "-m", "svg", "-o", str(svg_file))
        assert svg_file.is_file() and svg_file.stat().st_size > 100, "uniqc draw svg wrote no file"
    finally:
        shutil.rmtree(scratch_home, ignore_errors=True)

    print("PASS: Circuit + dummy + virtual YAML lifecycle + draw/to_matrix OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())