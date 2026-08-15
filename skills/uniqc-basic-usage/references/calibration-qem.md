# Calibration and QEM Reference

Calibration experiments characterize hardware error rates; QEM (Quantum Error Mitigation) applies those results to correct measurement outcomes. UnifiedQuantum (current 0.0.11.x) exposes both as CLI commands and Python APIs.

## Quick Path

1. **Run calibration** (readout + XEB) via CLI or Python.
2. **Apply QEM** to measurement counts via `ReadoutEM` or `M3Mitigator`.
3. Results are cached to `~/.uniqc/calibration_cache/` with ISO-8601 timestamps.

---

## XEB Benchmarking

Cross-entropy benchmarking measures 1q and 2q gate fidelity by running random circuits at increasing depth and fitting an exponential decay.

### CLI

```bash
# 1q XEB on qubits 0,1,2,3
uniqc calibrate xeb --qubits 0 1 2 3 --type 1q --backend dummy --shots 1000 --depths 5 10 20 40

# 2q XEB on qubit pair (0,1) -- when --type 2q, qubits are paired as
# (qubits[0], qubits[1]). For more than 2 qubits or arbitrary pair sets, use
# the Python API `xeb_workflow.run_2q_xeb_workflow(pairs=[(a, b), ...])`.
uniqc calibrate xeb --qubits 0 1 --type 2q --backend dummy --shots 1000

# Real chip (uses cached characterization data)
uniqc calibrate xeb --backend originq:WK_C180 --shots 1000
```

Note: there is **no** `--parallel` flag on `uniqc calibrate xeb` (run
`uniqc calibrate xeb --help` to verify). For parallel multi-pair XEB use the
Python API: `xeb_workflow.run_parallel_xeb_workflow(backend=..., target_qubits=[...])`.

### Python API

```python
from uniqc.algorithms.workflows import xeb_workflow

# 1q XEB -- pass the backend identifier (string), not an adapter object.
results_1q = xeb_workflow.run_1q_xeb_workflow(
    backend="dummy:local:virtual-line-3",
    qubits=[0, 1, 2, 3],
    shots=1000,
    depths=[5, 10, 20, 40],
    use_readout_em=True,
)  # -> dict[int, XEBResult]
print(results_1q[0].fidelity_per_layer)

# 2q XEB -- the keyword is `pairs=`, not `qubit_pairs=`.
results_2q = xeb_workflow.run_2q_xeb_workflow(
    backend="dummy:local:virtual-line-3",
    pairs=[(0, 1), (1, 2)],
    shots=1000,
    depths=[5, 10, 20],
    use_readout_em=True,
)  # -> dict[tuple[int, int], XEBResult]
```

### Result Type: `XEBResult`

```python
from uniqc import XEBResult

# Real fields (verify with: dataclasses.fields(XEBResult)):
result.calibrated_at        # str: ISO-8601 UTC timestamp
result.backend              # str: backend identifier
result.type                 # str: 'xeb_1q' | 'xeb_2q' | 'xeb_2q_parallel'
                            #      (NOT '1q' / '2q' — check the full literal)
result.qubit                # int | None: target qubit (1q runs)
result.pairs                # tuple[tuple[int, int], ...] | None: target pairs (2q runs)
result.fidelity_per_layer   # float: per-layer fidelity (exponential decay rate r)
result.fidelity_std_error   # float: standard error of the fit
result.fit_a                # float: A in F(m) = A * r^m + B
result.fit_b                # float: B in F(m) = A * r^m + B
result.fit_r                # float: same as fidelity_per_layer
result.depths               # tuple[int, ...]: circuit depths used
result.n_circuits           # int: random circuits per depth
result.shots                # int: shots per circuit
```

---

## Readout Calibration

Measures the confusion matrix for single-qubit or two-qubit joint measurements by preparing known states and recording measurement outcomes.

### CLI

```bash
# 1q readout calibration on qubits 0,1
uniqc calibrate readout --qubits 0 1 --backend dummy --shots 1000

# 2q joint readout calibration on pair (0,1)
uniqc calibrate readout --qubits 0 1 --type 2q --backend dummy --shots 1000
```

### Python API

```python
from uniqc.calibration.readout import ReadoutCalibrator

# 默认 shots=1000, timeout=300.0s, poll_interval=2.0s（E-U7, uniqc ≥ 0.0.11.dev30）
# 真机排队较长时可调大 timeout / poll_interval
calibrator = ReadoutCalibrator(adapter=dummy_adapter, shots=1000)
# calibrator = ReadoutCalibrator(adapter=originq_adapter, shots=1000, timeout=900.0, poll_interval=10.0)
result = calibrator.calibrate_1q(qubit=0)
# 1q confusion_matrix: rows=measured, cols=prepared.
# So result.confusion_matrix[i][j] == P(measure=i | prep=j); diagonal == [P(0|0), P(1|1)].
print(result.confusion_matrix)
print(result.assignment_fidelity)   # average of diagonal = (P(0|0) + P(1|1)) / 2
```

### Result Type: `ReadoutCalibrationResult`

```python
from uniqc import ReadoutCalibrationResult

result.confusion_matrix     # tuple[tuple[float, ...], ...]: row=measured, col=prepared.
                            # 1q: 2x2, ``M[i][j] = P(measure=i | prep=j)``
                            # 2q: 4x4 over (|00>, |01>, |10>, |11>)
result.assignment_fidelity  # float: average diagonal element
result.qubit                # int (1q) or tuple[int,int] (2q)
result.type                 # "readout_1q" or "readout_2q"
result.backend              # str: backend identifier
result.calibrated_at        # str: ISO-8601 UTC timestamp

# Dict-like access for dict-era code:
result["confusion_matrix"]   # equivalent to attribute access
"qubit" in result            # True
```

> Back-compat tip: `ReadoutCalibrationResult` is a frozen dataclass that also implements `__getitem__` and `__contains__`, so old call sites that treated it as a dict still work after the result-type migration.

---

## Pattern Analysis

Analyzes 2-qubit gate structure to determine parallel execution groups using DSatur graph coloring.

```bash
# Analyze qubit connectivity patterns
uniqc calibrate pattern --qubits 0 1 2 3 4 5

# Analyze a specific circuit
uniqc calibrate pattern --type circuit --circuit my_circuit.ir
```

Output: shows which 2q gate pairs can execute in parallel (layer groups) and the chromatic number of the interaction graph.

---

## QEM: ReadoutEM and M3Mitigator

### ReadoutEM — Unified Interface

`ReadoutEM` is the primary interface for applying readout error mitigation to measurement counts. It wraps `ReadoutCalibrator` internally and dispatches to 1q, 2q, or per-qubit sequential mitigation automatically.

The recommended entry point is the workflow API, which only needs a backend
identifier:

```python
from uniqc.algorithms.workflows import readout_em_workflow

em = readout_em_workflow.run_readout_em_workflow(
    backend="dummy:local:virtual-line-3", qubits=[0, 1], shots=1000,
)
corrected = em.mitigate_counts(raw_counts, measured_qubits=[0, 1])
```

Lower-level forms also exist:

```python
from uniqc import ReadoutEM

em = ReadoutEM(adapter, max_age_hours=24.0, shots=1000)        # adapter = QuantumAdapter
corrected_counts = em.mitigate_counts(raw_counts, measured_qubits=[0, 1])
```

```python
from uniqc.algorithms.workflows.readout_em_workflow import apply_readout_em

# `result` is a task result object; `readout_em` is a `ReadoutEM` instance.
corrected = apply_readout_em(result, readout_em, measured_qubits=[0, 1])
```

Dispatch logic:
- **1 qubit**: uses 1q calibration for that qubit
- **2 qubits**: uses 2q joint calibration
- **>2 qubits**: applies per-qubit 1q calibration sequentially (tensor-product approximation)

### M3Mitigator — Confusion Matrix Inversion

`M3Mitigator` uses a pre-computed calibration confusion matrix to correct measurement outcomes via linear inversion.

```python
from uniqc import M3Mitigator

# From a pre-loaded result (verified working on uniqc 0.0.11.dev10).
mitigator = M3Mitigator(calibration_result=readout_result)

# Or from a cached file.
mitigator = M3Mitigator(
    cache_path="~/.uniqc/calibration_cache/readout_1q_dummy_0_20250101T120000Z.json",
    max_age_hours=48.0,
)

corrected = mitigator.mitigate(raw_counts)
```

### StaleCalibrationError

Both `M3Mitigator` and `ReadoutEM` enforce TTL-based freshness. If the calibration data is older than `max_age_hours`, a `StaleCalibrationError` is raised.

> Note: on uniqc 0.0.11.dev10, `StaleCalibrationError` inherits **directly from `Exception`**, NOT from `UnifiedQuantumError`. Catching `UnifiedQuantumError` will miss it — catch `StaleCalibrationError` explicitly.

```python
from uniqc import StaleCalibrationError

try:
    mitigator = M3Mitigator(cache_path=path, max_age_hours=1.0)
except StaleCalibrationError:
    # Re-run calibration
    ...
```

---

## Workflows Module

High-level functions that combine calibration steps:

```python
from uniqc.algorithms.workflows import xeb_workflow, readout_em_workflow

# XEB workflows -- always pass `backend=<str>`.
result_1q = xeb_workflow.run_1q_xeb_workflow(backend="dummy", qubits=[0, 1], shots=1000)
result_2q = xeb_workflow.run_2q_xeb_workflow(backend="dummy", pairs=[(0, 1)], shots=1000)
result_par = xeb_workflow.run_parallel_xeb_workflow(
    backend="dummy", target_qubits=[0, 1, 2, 3], shots=1000,
)

# Readout EM workflow.
em = readout_em_workflow.run_readout_em_workflow(backend="dummy", qubits=[0, 1], shots=1000)
corrected = em.mitigate_counts(raw_counts, measured_qubits=[0, 1])
```

---

## Calibration Cache

- **Location**: `~/.uniqc/calibration_cache/`
- **Naming**: `{type}_{backend}_{qubit-id}_{timestamp}.json` where `qubit-id` is `q<n>` for 1q and `pair-u-v` for 2q. Example actual filename: `readout_1q_dummy_q0_20260507T010843.099800Z.json`. (uniqc < 0.0.11.dev23 produced `+0000` instead of the trailing `Z`; this was fixed in `fix/audit-review`.)
- **Persistence**: `save_calibration_result()` and `load_calibration_result()` from `uniqc`
- **Discovery**: `find_cached_results(cache_dir=None, backend=None, result_type=None)` returns a list of cached results

```python
from uniqc import find_cached_results, load_calibration_result

# Find all cached readout results for the dummy backend.
# NOTE: the keyword is `result_type=`, not `type=`.
cached = find_cached_results(backend="dummy", result_type="readout_1q")
if cached:
    result = load_calibration_result(cached[0])
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `StaleCalibrationError` | Calibration data exceeds `max_age_hours` | Re-run `uniqc calibrate readout` or increase `max_age_hours` |
| `FileNotFoundError` in `M3Mitigator` | Missing calibration cache file | Run `uniqc calibrate readout` first |
| Confusion matrix all zeros | Adapter returned empty counts | Check adapter connectivity and shot count |
| `TimelineDurationError` | Duration data missing for a gate | Pass explicit `gate_durations` dict or use backend metadata |

---

## API Reality Check (don't hallucinate these)

- ❌ `uniqc.qem.ZNE` — **does not exist**. UnifiedQuantum's QEM scope is currently **readout-only** (`M3Mitigator`, `ReadoutEM`). For ZNE/PEC/Mitiq integration, use the upstream `mitiq` package directly.
- ❌ `XEBCalibrator` — **does not exist**. The XEB benchmarking class is `XEBenchmarker` (singular `enchmarker`, no `Calibrator` suffix). Import: `from uniqc.calibration import XEBenchmarker` (uniqc ≥ 0.0.11.dev23) or `from uniqc.calibration.xeb.benchmarker import XEBenchmarker` on older versions.
- ❌ `M3Mitigator.apply(...)` — **does not exist**. The methods are `mitigate_counts(raw_counts, measured_qubits=...)` and `mitigate_probabilities(raw_probs, measured_qubits=...)`.
