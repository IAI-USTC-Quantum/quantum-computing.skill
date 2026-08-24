---
name: uniqc-result-analysis
description: "Use when the user wants to analyze or visualize quantum execution results from UnifiedQuantum (uniqc ≥ 0.0.13): parse `UnifiedResult` returned by `wait_for_result` / `get_result` / `poll_result`, build counts / probability tables, compute marginals and expectation values, plot histograms with `uniqc.visualization.plot_histogram` / `plot_distribution`, render circuit diagrams with `circuit_to_html`, JSON-serialize via `uniqc submit ... --json` (fixed in 0.0.13 to handle UnifiedResult), and compare across runs / batches."
---

# Uniqc Result Analysis Skill

Use this skill after a successful `wait_for_result` / `get_result`
(or when the user already has a `~/.uniqc/cache/tasks.sqlite` row to
inspect). It covers everything **from result object to plot/table**,
including hardware-specific quirks like endianness and partial measurements.

## Mental model

`wait_for_result` (and its 0.0.13 alias `get_result`) returns either:

- `UnifiedResult` — a dataclass that **also** behaves like
  `dict[str, int]` over its `.counts`. So `result["00"]` and
  `for k in result` both work.
- `list[UnifiedResult]` — when the parent task came from `submit_batch`
  (native batch). 0.0.13 fix: `query_batch` on IBM Sampler now flattens
  to `list[dict]` instead of nested `list[list[dict]]`, so this list shape
  is consistent across providers.
- `None` — task failed; check `query_task(uid).error` (or the per-element
  `None` inside the list).

`poll_result(uid)` (top-level export, 0.0.13) returns `TaskInfo` immediately
(non-blocking) — use `TaskInfo.result` once `TaskInfo.status` reaches
`SUCCESS`.

`UnifiedResult` exposes:

| field            | purpose                                        |
| ---------------- | ---------------------------------------------- |
| `counts`         | `dict[str, int]` — bitstring -> shot count     |
| `probabilities`  | `dict[str, float]` — counts / shots            |
| `shots`          | `int` — total shots actually run               |
| `platform`       | `str` — `'originq' / 'quark' / 'ibm' / 'tianyan' / 'logicalqubit' / 'dummy'` |
| `task_id`        | `str` — uniqc id (`uqt_*`)                     |
| `backend_name`   | `str | None` — chip / simulator name           |
| `execution_time` | `float | None` — seconds, when the platform reports it |
| `raw_result`     | platform-native payload — use for debug        |
| `error_message`  | `str | None`                                   |

## First decision

| User goal                                                       | Read first                                                    |
| --------------------------------------------------------------- | ------------------------------------------------------------- |
| "Show me the counts / a clean table"                            | [references/inspect-result.md](references/inspect-result.md)  |
| "Plot a histogram / probability bar chart"                      | [references/plotting.md](references/plotting.md)              |
| "Compute an observable / Pauli expectation"                     | [references/expectations.md](references/expectations.md)      |
| "Render the circuit alongside the result"                       | [references/circuit-and-timeline.md](references/circuit-and-timeline.md) |
| "Compare two runs / two backends"                               | [references/comparison.md](references/comparison.md)          |

## Practical defaults

- Always print `result.shots` and `result.platform` along with the counts
  table — different platforms truncate / re-order bitstrings differently.
- For multi-qubit results, print **probabilities** (not raw counts) when
  comparing across runs with different shot counts.
- For real hardware, include `result.backend_name` in any plot title — chip
  characterization caches change over time and you want this in the figure.
- Save figures as PNG **and** the underlying counts as JSON next to them.
  Plots without raw data are not reproducible.
- Endianness: counts keys are **little-endian by default** on uniqc
  (qubit 0 / `c[0]` is the rightmost character), enforced end-to-end on
  every platform since 0.0.13. If you have pre-0.0.13 code that
  hand-reversed IBM keys, drop the reversal.

## CLI / JSON note (0.0.13 fix)

`uniqc submit ... --wait --format json` (and `--json`) now correctly
serialises `UnifiedResult` and `list[UnifiedResult]` payloads — pre-0.0.13
the helper only handled raw `dict` / `list`, so you would see an empty
table or a default-repr blob. Upgrade if you hit that.

## Cheat sheet

```python
from uniqc import wait_for_result, get_result, poll_result
from uniqc.visualization import plot_histogram, plot_distribution

# Either spelling is fine; get_result is the 0.0.13 alias.
result = wait_for_result("uqt_xxx", timeout=300)
# or: result = get_result("uqt_xxx", timeout=300)

# Non-blocking single-shot status check:
# info = poll_result("uqt_xxx")
# if info.status == "SUCCESS": result = info.result

# --- table
print(f"shots={result.shots}  platform={result.platform}  backend={result.backend_name}")
for bits, n in sorted(result.counts.items(), key=lambda kv: kv[1], reverse=True):
    print(f"  {bits}: {n}  ({100 * n / result.shots:.2f}%)")

# --- plot
plot_histogram(result.counts, title=f"raw counts ({result.platform})")
plot_distribution(result.probabilities, title="probabilities")
```

Both plotting helpers take either a `dict` (bitstring -> value) or a `list`
(index -> value) — the dict form is normally what you want.

## Saving + loading

```python
import json
from pathlib import Path

p = Path(f"results/{result.task_id}.json")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({
    "task_id": result.task_id,
    "platform": result.platform,
    "backend_name": result.backend_name,
    "shots": result.shots,
    "counts": result.counts,
    "probabilities": result.probabilities,
}, indent=2))
```

Reading back: just `json.loads(p.read_text())` — you do not need
`UnifiedResult` if you only want the counts.

## Failure path

```python
from uniqc import query_task
info = query_task("uqt_xxx")
if info.status == "FAILED":
    print(info.error)              # platform-side reason
    print(info.raw)                # platform payload
```

Common causes:

- "Job failed in queue" — usually transient on cloud platforms; resubmit.
- `UnsupportedGateError` — the IR you submitted contains gates the platform
  cannot execute. Re-compile against the chip basis (see the
  `uniqc-cloud-submit` skill).
- Empty counts — too few shots, or the backend ran but rejected reads on
  some qubits; check `result.raw_result` for the platform's diagnostic.

## Names to remember

- Parsing: `UnifiedResult.counts / probabilities / shots / raw_result`.
- Plotting: `uniqc.visualization.plot_histogram`,
  `uniqc.visualization.plot_distribution`,
  `uniqc.visualization.format_result` (textual summary used by the CLI).
- Circuit drawing: `uniqc.visualization.draw`, `draw_html`,
  `circuit_to_html(circuit, output_path=...)`.
- Timeline: `uniqc.visualization.schedule_circuit`,
  `plot_time_line_html` (covered in `uniqc-basic-usage`).
- Pauli observables: `uniqc.algorithms.core.measurement.pauli_expectation`,
  `PauliExpectation`, `classical_shadow`, `state_tomography`.

## Response style

- Always start with the textual table — it is reproducible without a GUI.
- Add the histogram only after asking whether the user is in a notebook /
  GUI context, or is fine writing PNG to disk.
- For any expectation / fidelity claim, show the formula and the numerical
  inputs, not just the final number.
