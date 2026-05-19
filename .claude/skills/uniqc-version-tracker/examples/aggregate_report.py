"""Run all smoke tests and print an aggregated markdown report.

Usage:
    python aggregate_report.py --smoke-dir ./smoke-tests
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

SMOKE_SCRIPTS = [
    "smoke_basic_usage.py",
    "smoke_cloud_submit.py",
    "smoke_result_analysis.py",
    "smoke_xeb_qem.py",
    "smoke_circuit_interop.py",
    "smoke_noise_simulation.py",
    "smoke_qaoa.py",
    "smoke_quantum_ml.py",
    "smoke_algorithm_cases.py",
    "smoke_quantum_volume.py",
    "smoke_classical_shadow.py",
    "smoke_doctor_config.py",
    "smoke_platform_verify.py",
]

SKILL_NAMES = [s.removeprefix("smoke_").removesuffix(".py").replace("_", "-") for s in SMOKE_SCRIPTS]

SKILL_MAP = {
    "basic-usage": "uniqc-basic-usage",
    "cloud-submit": "uniqc-cloud-submit",
    "result-analysis": "uniqc-result-analysis",
    "xeb-qem": "uniqc-xeb-qem",
    "circuit-interop": "uniqc-circuit-interop",
    "noise-simulation": "uniqc-noise-simulation",
    "qaoa": "uniqc-qaoa",
    "quantum-ml": "uniqc-quantum-ml",
    "algorithm-cases": "uniqc-algorithm-cases",
    "quantum-volume": "uniqc-quantum-volume",
    "classical-shadow": "uniqc-classical-shadow",
    "doctor-config": "uniqc-doctor-config",
    "platform-verify": "uniqc-platform-verify",
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Aggregate smoke test results.")
    ap.add_argument("--smoke-dir", required=True, help="Path to smoke-tests directory")
    args = ap.parse_args()

    smoke_dir = Path(args.smoke_dir).resolve()
    if not smoke_dir.exists():
        sys.exit(f"Smoke test directory not found: {smoke_dir}")

    # Check uniqc version first
    ver_r = subprocess.run(
        [sys.executable, "-c", "import uniqc; print(uniqc.__version__)"],
        capture_output=True, text=True,
    )
    uniqc_ver = ver_r.stdout.strip() if ver_r.returncode == 0 else "unknown"

    print(f"# Smoke Test Report\n")
    print(f"**uniqc version:** {uniqc_ver}")
    print(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("| Skill | Status | Time (s) | Diagnostic |")
    print("|-------|--------|----------|------------|")

    results = []
    t0 = time.monotonic()

    for script, short_name in zip(SMOKE_SCRIPTS, SKILL_NAMES):
        skill = SKILL_MAP.get(short_name, f"uniqc-{short_name}")
        path = smoke_dir / script
        if not path.exists():
            results.append((skill, "ERROR", 0, f"Script not found: {script}"))
            continue

        t1 = time.monotonic()
        try:
            r = subprocess.run(
                [sys.executable, str(path)],
                capture_output=True, text=True, timeout=30,
            )
        except subprocess.TimeoutExpired:
            results.append((skill, "TIMEOUT", 30, "Script timed out after 30s"))
            continue

        elapsed = time.monotonic() - t1
        status = "PASS" if r.returncode == 0 else "FAIL"

        if r.returncode != 0:
            diag = r.stderr.strip()[-200:]
        else:
            diag = r.stdout.strip().split("\n")[-1]

        if r.returncode == 0 and "SKIP:" in (r.stdout or ""):
            status = "SKIP"
            diag = r.stdout.strip().split("\n")[-1]

        results.append((skill, status, elapsed, diag or "-"))

    passed = 0
    for skill, status, elapsed, diag in results:
        d = diag.replace("\n", " ")[:100]
        print(f"| {skill} | {status} | {elapsed:.1f} | {d} |")
        if status == "PASS":
            passed += 1

    total = time.monotonic() - t0
    print()
    print(f"**{passed}/{len(results)} skills pass ({100*passed/len(results):.0f}%)**  (total: {total:.1f}s)")


if __name__ == "__main__":
    main()