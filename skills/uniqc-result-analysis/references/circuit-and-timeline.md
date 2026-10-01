# Rendering circuits and timelines

uniqc ships a few helpers for visualizing the program itself, which is
useful when you want to put the result next to the circuit that produced it.

## Circuit drawing (uniqc ≥ 0.1.1 rendering engine)

One layout core feeds seven output modes — `text` (self-developed ASCII /
Unicode art, no pyqpanda3 dependency), `svg`, `png`, `mpl` (matplotlib
Figure), `latex` (quantikz source), `html`, and `interactive`
(click-to-inspect gates):

```python
from uniqc.visualization import render

print(circuit)                       # text art in the terminal
art = render(circuit, mode="text")   # same drawing as a TextDrawing object
svg = circuit.draw("svg")            # str; also render(circuit, mode="svg")
tikz = circuit.draw("latex")         # quantikz source, paste into a paper
render(circuit, mode="html", filename="circuit.html")
```

Shared options on `render()` / `Circuit.draw()`: `style`
(`quantikz` default | `qiskit` | `modern` | `print`), `theme`
(`light`/`dark`), `fold` (gates per row: `"auto"` | int | `0` to disable),
`orientation` (`h` time→ / `v` time↓), `qubit_order` (`asc`/`desc`),
`param_mode` (`pi`/`decimal`/`symbol`/`hidden`), `show_clbits`,
`charset` (`ascii`/`unicode`), `scale`, `filename`. In Jupyter a `Circuit`
cell output renders itself as inline SVG (`_repr_svg_`); `mode=None`
auto-picks `svg` in Jupyter and `text` in a terminal.

The same engine backs the CLI (`uniqc draw <file>` for OriginIR / QASM
files — see the `uniqc-basic-usage` cli guide).

> ⚠️ `uniqc.visualization.draw()` / `draw_html()` (and the
> `uniqc.compile.draw` re-export) are deprecated wrappers that emit a
> `DeprecationWarning` and will be **removed in uniqc 0.2.0** — the old
> text output delegated to pyqpanda3. Use
> `render(circuit, mode="text"/"html")` or `Circuit.draw(...)` instead.

## Self-contained HTML

```python
from uniqc.visualization import circuit_to_html
circuit_to_html(circuit, output_path="circuit.html",
                title="QAOA p=2 ansatz on 4 qubits")
```

Open `circuit.html` in any browser. Nothing on the page links back to a
local Python kernel.

## Timelines (scheduled circuit)

A "timeline" is the compiled circuit with explicit per-gate durations,
useful for understanding what actually runs on hardware.

```python
from uniqc import compile, find_backend
from uniqc.visualization import schedule_circuit, plot_time_line_html

bi      = find_backend("originq:WK_C180")
compiled = compile(my_circuit, bi, level=2)
schedule = schedule_circuit(compiled, backend_info=bi)   # TimelineSchedule
print(schedule.total_duration, schedule.unit)
print(schedule.gate_durations)

plot_time_line_html(compiled, output_path="timeline.html",
                    backend_info=bi, title="QAOA-p2 timeline")
```

`TimelineSchedule` exposes `gates`, `qubits`, `total_duration`, `unit`,
`gate_durations`, plus a `time_points` property. (No `n_layers` /
`resources` — read `max(g.layer for g in gates) + 1` if you need layer
count.)

> ℹ️ `schedule_circuit` and `plot_time_line_html` use qiskit internally to
> handle logical (un-scheduled) `Circuit` input. As of uniqc 0.0.13 qiskit
> is a **core dependency** — no `[qiskit]` extra required.

## Result + circuit on one HTML page

A common workflow is to ship "circuit.html + counts.png + counts.json" as
a per-task evidence bundle:

```python
from pathlib import Path
import json
import matplotlib.pyplot as plt

from uniqc.visualization import circuit_to_html, plot_histogram

base = Path(f"reports/{result.task_id}")
base.mkdir(parents=True, exist_ok=True)

circuit_to_html(circuit, output_path=base / "circuit.html",
                title=f"task {result.task_id[:10]}…")
plot_histogram(result.counts, title="counts")
plt.savefig(base / "counts.png", dpi=160, bbox_inches="tight")
plt.close()

(base / "counts.json").write_text(json.dumps({
    "shots": result.shots,
    "platform": result.platform,
    "backend_name": result.backend_name,
    "counts": result.counts,
}, indent=2))
```

## When the user just wants to see the diagram

If they are in Jupyter, make the circuit the cell's last expression — it
renders as inline SVG automatically (`_repr_svg_`).

If they are in a terminal:

```python
print(circuit)                # or: print(circuit.draw("text"))
```

If you are running headless / inside CI:

```python
from uniqc.visualization import render
render(circuit, mode="html", filename="circuit.html")
print("Open circuit.html in a browser.")
```
