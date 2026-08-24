---
name: uniqc-platform-verify
description: "Use when the user wants to verify that a quantum platform's published / cached metadata is actually accurate: cross-check chip topology, qubit availability, basis gates, calibration freshness, and 1q/2q/parallel-CZ gate fidelities against measured XEB + readout calibration on the live backend. Detect stale chip cache, drift between vendor-published numbers and measured values, qubits that should be excluded, and silent backend regressions. Builds on the uniqc 0.0.13 backend-cache refresh fix (IBM/Quark `uniqc backend update --platform` actually refreshes now; TianYan/LogicalQubit since 0.1.0), the strict pre-flight policy in `uniqc.calibration.xeb`, and the parallel-CZ XEB module."
---

# Uniqc Platform Verification Skill

This skill answers: *"is the chip metadata I'm planning my experiment
against actually true today?"*

It is the operational counterpart to `uniqc-xeb-qem` (which calibrates
and mitigates) and `uniqc-doctor-config` (which inspects the local
install). Here we **measure**, **compare**, and **report drift**
against vendor-published or cached chip data.

> Why this matters: real chips drift on the order of hours (T1, T2,
> readout) and weeks (median 2q fidelity). The local backend cache
> (`~/.uniqc/backend/backends.json` + `~/.uniqc/backend/chips/`)
> is **lazy** — `find_backend(...)` happily returns rows that are
> days stale. Pre-0.0.13, `uniqc backend update --platform ibm` even
> reported success while writing nothing.

## Decision tree

| User goal                                                         | Read first                                                       |
| ----------------------------------------------------------------- | ---------------------------------------------------------------- |
| "Is my local chip cache fresh? Refresh it and tell me what changed." | [references/cache-freshness.md](references/cache-freshness.md) |
| "Verify the topology / coupling map / available qubits."          | [references/topology-audit.md](references/topology-audit.md)     |
| "Compare measured 1q/2q/readout fidelity to claimed."             | [references/fidelity-audit.md](references/fidelity-audit.md)     |
| "Run the full audit and produce a report."                        | **End-to-end audit recipe** below                                  |
| "Detect drift across two snapshots of the same chip."             | [references/cache-freshness.md](references/cache-freshness.md)   |

## End-to-end audit recipe (the one users actually want)

```python
from datetime import datetime, timezone
from uniqc import (
    find_backend, list_backends,
    submit_task, wait_for_result,
    Circuit,
)
from uniqc.calibration import find_cached_results
from uniqc.algorithms.workflows import xeb_workflow, readout_em_workflow

CHIP = "originq:WK_C180"

# 1. Force-refresh the local cache (uniqc 0.0.13 actually refreshes for ibm/quafu/quark too).
import subprocess
subprocess.run(["uniqc", "backend", "update", "--platform", CHIP.split(":")[0]], check=True)

# 2. Read the freshly-cached metadata.
bi = find_backend(CHIP)
print(f"Chip {CHIP}")
print(f"  cached at:  {bi.calibrated_at}")
print(f"  qubits:     {bi.qubits.n_qubits}")
print(f"  basis:      {bi.basis_gates}")
print(f"  available:  {len(bi.qubits.available_qubits)} qubits")
print(f"  couplings:  {len(bi.qubits.coupling_map)} pairs")

# 3. Measure 1q + 2q XEB + readout on a small region (cheap audit).
target = sorted(bi.qubits.available_qubits)[:4]
xeb_1q = xeb_workflow.run_1q_xeb_workflow(
    backend=CHIP, target_qubits=target, depths=[5, 10, 20], n_circuits=20, shots=1000)
xeb_2q = xeb_workflow.run_2q_xeb_workflow(
    backend=CHIP, pairs=[(target[i], target[i+1]) for i in range(len(target)-1)],
    depths=[5, 10, 20], n_circuits=20, shots=1000)
readout = readout_em_workflow.run_readout_em_workflow(
    backend=CHIP, qubits=target, shots=2000)

# 4. Compare measured to claimed (claimed lives on bi.qubits.qubit_info[i]).
for q in target:
    info = bi.qubits.qubit_info[q]              # vendor-published characterization
    meas = xeb_1q[f"q{q}"]                       # XEBResult
    claimed_1q = 1.0 - getattr(info, "single_qubit_gate_error", 0.0)
    measured_1q = meas.fidelity_per_layer
    print(f"q{q}  claimed-1q-F={claimed_1q:.4f}  measured-1q-F={measured_1q:.4f}  "
          f"Δ={measured_1q - claimed_1q:+.4f}")
```

## Practical defaults

- **Always run `uniqc backend update --platform <p>` before the audit**
  (uniqc 0.0.13 actually does this for IBM/Quafu/Quark; pre-0.0.13
  silently no-op'd for IBM).
- **Audit a small region first** (≤ 4 qubits, 1q + 2q + readout) before
  spending shots on a full-chip parallel XEB.
- For the **strict pre-flight policy** added in 0.0.13: if
  `xeb_workflow` raises a pre-flight error, *trust it* — the chip is
  reporting that the requested pairs / qubits are not in a state
  worth measuring (no calibrated CZ, qubit out of region, basis-gate
  not exposed). Fix the input rather than retrying.
- **Cache age**: anything older than `~24h` is suspicious for daily
  experiments; older than `~7d` is unsafe for fidelity-sensitive
  workflows. Reuse the QEM `max_age_hours` policy as a yardstick.
- **Comparison**: report **Δ = measured − claimed** with a sign;
  positive means "chip is better than published" (or the published
  number is conservative), negative is the case to investigate.
- **Audit cadence**: weekly for production; before-and-after any
  vendor-announced calibration window; before any QV / VQE
  benchmark you intend to publish.
- For **chip-backed dummy backends** (`dummy:originq:<chip>`) the
  audit becomes a *self-consistency* check: measured XEB on the
  noisy simulator should track the cached fidelities (they were used
  to build the noise model). Discrepancy → noise model out of date
  → refresh the chip cache then re-build.
- **Two snapshots compared** — diff today's audit against last
  week's; flag pairs whose `Δ` between the two runs exceeds 2σ of the
  individual fits. Use the snapshot procedure in `cache-freshness.md`.

## What to compare

| Metadata field                                  | Where stored (cached)                              | How to verify                                    |
| ----------------------------------------------- | -------------------------------------------------- | ------------------------------------------------ |
| `bi.qubits.n_qubits`                            | `backends.json`                                    | Count distinct qubits in `bi.qubits.coupling_map`. |
| `bi.qubits.available_qubits`                    | `backend/chips/`                                   | `submit_task` a parity-1 circuit on each; refusal → broken qubit. |
| `bi.qubits.coupling_map`                        | `backend/chips/`                                   | Try a 2q gate on each pair; topology error → wrong map. |
| `bi.basis_gates`                                | `backend/chips/`                                   | Compile a circuit using each gate; `UnsupportedGateError` → wrong basis list. |
| `qubit_info[i].T1`, `T2`                        | `backend/chips/`                                   | Run an idle-then-readout protocol; compare decay constants (separate skill). |
| `qubit_info[i].single_qubit_gate_error`         | same                                               | `xeb_workflow.run_1q_xeb_workflow` measured fidelity. |
| `qubit_info[(i,j)].two_qubit_gate_error`        | same                                               | `xeb_workflow.run_2q_xeb_workflow` per-pair.    |
| Parallel-CZ crosstalk (new in 0.0.13)           | not exposed in cache                               | `uniqc.calibration.xeb.parallel_cz` measures it. |
| `qubit_info[i].readout_error_*`                 | same                                               | `ReadoutCalibrator` confusion-matrix diagonal.   |

## Names to remember

- `uniqc backend update --platform <p>` (CLI; refreshes cache).
- `find_backend(<chip>)`, `list_backends()` (Python; read cache).
- `bi.calibrated_at`, `bi.qubits`, `bi.basis_gates`,
  `bi.qubits.qubit_info[i]` / `qubit_info[(i,j)]`.
- `uniqc.calibration.find_cached_results(backend, result_type=...)`
  — find prior XEB / readout cached locally, with `result_type=`
  keyword (NOT `type=`).
- `uniqc.calibration.xeb.parallel_cz` — new module, parallel-CZ
  crosstalk benchmarking.
- `xeb_workflow.run_1q_xeb_workflow`,
  `xeb_workflow.run_2q_xeb_workflow`,
  `xeb_workflow.run_parallel_xeb_workflow`,
  `xeb_workflow.run_parallel_cz_xeb_workflow`.
- `readout_em_workflow.run_readout_em_workflow`.
- `ReadoutCalibrationResult`, `XEBResult`.
- Pre-flight: `xeb_workflow` raises before dispatching jobs whose
  prerequisites are not satisfied (uniqc 0.0.13 strict policy).

## Response style

- Always print **chip + cached-at + measured-at** at the top of any
  audit output.
- Report Δ with a sign and an explicit "claimed vs measured" header;
  do not hide which is which.
- For drift between two snapshots, report the **delta of deltas**
  ("measured-1q-F changed by +0.0023 from snapshot A to B"), not just
  the latest absolute number.
- For failures, separate two cases:
  1. **Local cache wrong / stale** — fixable by `uniqc backend
     update`.
  2. **Chip reality has drifted** — surface to the user; do not
     "correct" the cache silently.
