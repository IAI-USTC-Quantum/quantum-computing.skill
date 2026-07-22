# Smoke Test Guide

Each smoke test is a minimal standalone Python script (~10-30 lines) that exercises the core API of one skill. The goal is the fastest possible check: does the API still exist and produce valid output when called with the most basic arguments?

## Philosophy

- **Core import/construct/execute only.** Test that the primary objects can be imported, constructed, and exercised once. Do NOT test edge cases, plotting, optional dependencies, or performance.
- **Dummy backends only.** All tests use `dummy:local:simulator` or `dummy:local:virtual-line-N`. No real cloud submissions.
- **Fail fast.** The first assertion failure or unexpected exception exits nonzero.
- **Self-contained.** Each script can be run with `python smoke_<name>.py` with no arguments, no environment variables, no configuration.

## Template

```python
"""Smoke test for <skill-name>.
Tests: <list the 2-3 APIs exercised>.
"""
import sys


def main() -> int:
    # 1. Import core APIs
    # 2. Construct primary objects
    # 3. Exercise one critical method
    # 4. Print confirmation and return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Dummy Backend Policy

| Skill | Backend | Reason |
|-------|---------|--------|
| Most skills | `dummy:local:simulator` | Fast, no network, no credentials |
| uniqc-basic-usage | `dummy:local:simulator` + temporary HOME-scoped `dummy:virtual:smoke-machine` | Exercises the v0.0.16 YAML init/list/show/validate/submit lifecycle without touching the user's config |
| uniqc-noise-simulation | `dummy:local:simulator` + `dummy:originq:WK_C180` | Tests both noiseless and chip-backed dummy paths |
| uniqc-platform-verify | `dummy:local:simulator` + `dummy:local:virtual-line-3` | Tests backend info cache and XEB on virtual line |
| uniqc-xeb-qem | `dummy:local:simulator` | Readout EM works on any backend |

**Never use real cloud backends** (`originq:WK_C180`, `ibm:ibm_fez`, `quark:Baihua`) in smoke tests unless the user explicitly requests "Remote" mode with cost acknowledgement.

## Optional Dependencies

If a smoke test needs an optional dependency (torch, qiskit), use `try/except ImportError` and exit 0 with "SKIP":

```python
try:
    import torch
except ImportError:
    print("SKIP: torch not installed (optional dependency)")
    return 0
```

Missing optional deps are deployment issues, not API breakage. Do NOT fail on
missing optional deps. A `SKIP:` for any other reason is invalid: the
aggregate marks it as a failure and exits nonzero.

## Expected Per-Skill Test Time

| Skill | Expected time | Notes |
|-------|-------------|-------|
| smoke_basic_usage | ~2s | Statevector sim + dummy submit |
| smoke_cloud_submit | ~2s | Dry-run + compile + submit |
| smoke_result_analysis | ~2s | Dummy submit + field access |
| smoke_xeb_qem | ~3s | ReadoutEM calibration + apply |
| smoke_circuit_interop | ~1s | String exports, no simulation |
| smoke_noise_simulation | ~5s | Density matrix sim + chip-backed dummy |
| smoke_qaoa | ~5s | QAOA workflow with COBYLA optimization |
| smoke_quantum_ml | ~2s | QuantumLayer forward pass |
| smoke_algorithm_cases | ~1s | Fragment construction, no simulation |
| smoke_quantum_volume | ~3s | Qiskit QV circuit + statevector sim |
| smoke_classical_shadow | ~3s | Shadow workflow + low-level API |
| smoke_doctor_config | ~2s | CLI subprocess calls |
| smoke_platform_verify | ~3s | Backend info + XEB skip |

Total: ~35s sequentially, ~5s with parallel dispatch.

## Adding a New Smoke Test

When a 14th skill is added to the repo:

1. Create `smoke_<short_name>.py` in `.claude/skills/uniqc-version-tracker/examples/smoke-tests/`.
2. Add the filename to `SMOKE_SCRIPTS` list in `examples/aggregate_report.py`.
3. Add the mapping to `SKILL_MAP` dict in `examples/aggregate_report.py`.
4. Add the skill name to the sub-agent dispatch list in SKILL.md Phase 3.