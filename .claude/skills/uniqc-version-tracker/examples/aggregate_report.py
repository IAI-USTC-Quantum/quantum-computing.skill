"""Run all smoke tests and emit human- and machine-readable summaries.

Usage:
    python aggregate_report.py --smoke-dir ./smoke-tests --json-summary smoke-summary.json
"""
from __future__ import annotations

import argparse
import json
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
    ap.add_argument(
        "--json-summary",
        type=Path,
        help="Write the machine-readable result summary to this path.",
    )
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
        output = (r.stdout or "").strip()
        skip_lines = [line for line in output.splitlines() if line.startswith("SKIP:")]
        if r.returncode != 0:
            status = "FAIL"
            diag = (r.stderr or output).strip()[-200:]
        elif skip_lines:
            diag = skip_lines[-1]
            status = "SKIP" if "optional dependency" in diag.lower() else "FAIL"
            if status == "FAIL":
                diag = f"Invalid SKIP (only missing optional dependencies may skip): {diag}"
        else:
            status = "PASS"
            diag = output.split("\n")[-1] if output else "-"

        results.append((skill, status, elapsed, diag or "-"))

    passed = 0
    for skill, status, elapsed, diag in results:
        d = diag.replace("\n", " ")[:100]
        print(f"| {skill} | {status} | {elapsed:.1f} | {d} |")
        if status == "PASS":
            passed += 1

    total = time.monotonic() - t0
    failed = sum(status in {"FAIL", "ERROR", "TIMEOUT"} for _, status, _, _ in results)
    skipped = sum(status == "SKIP" for _, status, _, _ in results)
    summary = {
        "ok": failed == 0,
        "uniqc_version": uniqc_ver,
        "total": len(results),
        "passed": passed,
        "skipped": skipped,
        "failed": failed,
        "duration_seconds": round(total, 3),
        "results": [
            {
                "skill": skill,
                "status": status,
                "duration_seconds": round(elapsed, 3),
                "diagnostic": diag,
            }
            for skill, status, elapsed, diag in results
        ],
    }
    print()
    print(
        f"**{passed}/{len(results)} skills pass ({100*passed/len(results):.0f}%), "
        f"{skipped} skipped, {failed} failed**  (total: {total:.1f}s)"
    )
    print(f"JSON summary: {json.dumps(summary, ensure_ascii=False, sort_keys=True)}")
    if args.json_summary:
        args.json_summary.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()