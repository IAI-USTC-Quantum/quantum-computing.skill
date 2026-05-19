# Report Template

The aggregated version-tracker report follows this markdown format.

## Header Block

```
# UnifiedQuantum Version Tracker Report

**Date:** YYYY-MM-DD HH:MM
**Baseline version:** vX.Y.Z (from repo CLAUDE.md)
**Latest version:** vA.B.C (installed / git tags / PyPI)
**Classification:** MAJOR | MINOR | PATCH
**Git range:** vX.Y.Z..vA.B.C
```

## Changelog Summary

```
## Changelog Summary: vA.B.C

### ⚠ BREAKING (N items)
- item 1
- item 2

### Added (M items)
- item 1
- ...

### Fixed (P items)
- ...

### Changed (Q items)
- ...
```

## Smoke Test Results

```
## Smoke Test Results

| Skill | Status | Time (s) | Key API | Diagnostic |
|-------|--------|----------|---------|------------|
| uniqc-basic-usage | PASS | 1.8 | Circuit + Simulator | Circuit -> simulate_pmeasure -> dummy submit all OK |
| uniqc-cloud-submit | PASS | 2.1 | find_backend + compile | find_backend -> dry_run -> compile -> submit_task all OK |
| uniqc-result-analysis | PASS | 1.5 | UnifiedResult fields | UnifiedResult fields + visualization imports OK |
| uniqc-xeb-qem | PASS | 3.2 | ReadoutEM.apply | ReadoutEM calibration + apply pipeline OK |
| uniqc-circuit-interop | PASS | 0.8 | to_qiskit_circuit | Circuit interop exports + round-trip OK |
| uniqc-noise-simulation | PASS | 4.5 | NoisySimulator | NoisySimulator + chip-backed dummy OK |
| uniqc-qaoa | PASS | 5.1 | run_qaoa_workflow | QAOA workflow + hand-rolled ansatz OK |
| uniqc-quantum-ml | SKIP | 0.2 | QuantumLayer | SKIP: torch not installed |
| uniqc-algorithm-cases | PASS | 0.6 | ghz_state, qft_circuit | GHZ, QFT, Grover, QPE fragments all OK |
| uniqc-quantum-volume | PASS | 2.8 | QV circuit + heavy set | QV n=2 circuit + heavy set (2 heavy outputs of 4) |
| uniqc-classical-shadow | PASS | 3.0 | classical_shadow | Classical shadow workflow + low-level API OK |
| uniqc-doctor-config | PASS | 1.9 | uniqc doctor CLI | uniqc doctor CLI + config module imports OK |
| uniqc-platform-verify | PASS | 2.4 | find_backend | Platform verify backend inspection + XEB imports OK |

**12/13 skills pass (92%)**  (total: 5.1s)
```

## Cross-Reference

```
## Cross-Reference: Failures vs Known Breaking Changes

### Expected Failures
| Skill | Failure | Changelog Item | Action |
|-------|---------|---------------|--------|
| uniqc-basic-usage | `ImportError: OriginIR_Simulator` | `OriginIR_Simulator removed` (BREAKING) | Update SKILL.md to use `Simulator` |

### Unexpected Failures (Regressions)
| Skill | Failure | Possible Cause | Action |
|-------|---------|---------------|--------|
| (none) | | | |

### Skills With No Gap
| Skill | Notes |
|-------|-------|
| uniqc-cloud-submit | Matches vA.B.C API |
| ... | |
```

## Recommendations

```
## Recommendations

### Skills Needing SKILL.md Updates
- uniqc-basic-usage: replace `OriginIR_Simulator` with `Simulator`
- uniqc-xeb-qem: update `xeb_workflow` signature

### Skills Needing Example Rewrites
- uniqc-noisy-simulation: `ErrorLoader_GateTypeError` API changed

### Skills With No Gap
- Remaining N skills: smoke tests pass, docs match API
```

## CLAUDE.md Update

```
## CLAUDE.md Version Banner Update

- Line 46: `Current alignment: **UnifiedQuantum vX.Y.Z**` -> `Current alignment: **UnifiedQuantum vA.B.C (YYYY-MM-DD)**`
```