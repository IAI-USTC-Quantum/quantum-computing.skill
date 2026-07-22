---
name: uniqc-quantum-ml
description: "Use when the user wants to do quantum machine learning with UnifiedQuantum + PyTorch: native `Circuit.param_map` / `param_dict` / `set_param_last` + `uniqc.expectation()` for backend-agnostic differentiable training (v0.0.15), high-level `QNNClassifier` / `QCNNClassifier` / `HybridQCLModel`, low-level `QuantumLayer` (parameter-shift autograd over a `Circuit`), and end-to-end PyTorch training loops on classical datasets (moons / MNIST / quantum-state classification). Covers torchquantum optional dependency and parameter-shift gradients."
---

# Uniqc Quantum ML Skill

This skill is the entry point for **PyTorch-based** quantum machine
learning. UnifiedQuantum exposes four layers:

| Layer | Class / API                                          | Use for                                              |
| ----- | ---------------------------------------------------- | ---------------------------------------------------- |
| 0 (v0.0.15) | `Circuit.param_map` + `uniqc.expectation()` (native) | Minimal-boilerplate trainable circuits with `torch.Tensor` params, no `QuantumLayer` wrapper required |
| 1     | `QNNClassifier`, `QCNNClassifier`, `HybridQCLModel`  | Drop-in classifiers for tabular / image / state inputs |
| 2     | `QuantumLayer(circuit, expectation_fn, ...)`         | Custom architectures around your own `Circuit`       |
| 3     | Hand-written parameter-shift gradient                | Algorithmic research                                 |

> ⚠️ Optional dependency: classes in layer 1 import **torchquantum**.
> The pip extra `unified-quantum[pytorch]` now pulls **both** `torch` and
> `torchquantum-ng` (the community TorchQuantum fork; the import name stays
> `torchquantum`):
>
> ```bash
> pip install "unified-quantum[pytorch]"
> ```
>
> If the user hits `ImportError: torchquantum`, install it before
> retrying. `QuantumLayer` (layer 2) does **not** need torchquantum — it
> uses uniqc's own simulator + parameter-shift. **Layer 0 (v0.0.15) also
> does not need torchquantum** — `uniqc.expectation()` works on the
> built-in statevector simulator with autograd through tensor params.

## First decision

| User goal                                                      | Read first                                              |
| -------------------------------------------------------------- | ------------------------------------------------------- |
| "Use torch tensors as circuit params and train end-to-end (v0.0.15)" | [references/native-torch-params.md](references/native-torch-params.md) |
| "Train a binary classifier on a tabular dataset"               | [references/qnn-classifier.md](references/qnn-classifier.md) |
| "Train an image / state classifier (deep)"                     | [references/qcnn-and-hybrid.md](references/qcnn-and-hybrid.md) |
| "Wrap my own circuit so PyTorch sees its parameters"           | [references/quantumlayer.md](references/quantumlayer.md) |
| "Understand the parameter-shift rule / why π/2"                | [references/parameter-shift.md](references/parameter-shift.md) |
| "Run training on a real / dummy backend, not local sim"        | [references/quantumlayer.md](references/quantumlayer.md) (`expectation_fn` swap) |

## Mental model

```
classical input ─► classical encoder (optional)
                  └──► QuantumLayer / QNNClassifier
                       │  forward: prepare circuit, sample / statevector
                       │  backward: parameter-shift (Δθ = ±π/2)
                  └──► classical decoder (optional)
                       └──► loss
```

For QNNClassifier / QCNNClassifier / HybridQCLModel, all three slabs are
already wired; you only supply data + optimiser.

## Practical defaults

- **Dataset prep**: standard-scale features (mean 0 / std 1) before
  amplitude or angle encoding. Skipping this is the #1 reason a QML
  model "trains" but never improves.
- **Optimizer**: Adam(lr=0.01) for `QNNClassifier`; reduce to 0.005 if
  you see oscillation. Use AdamW if you have many trainable params.
- **Loss**: BCELoss (binary), CrossEntropyLoss (multi-class). For
  expectation-as-output regression, use MSELoss.
- **Batch size**: 8–32 for QML on a laptop; the per-iter cost is
  dominated by the circuit forward pass.
- **Epochs**: start with 50 and watch `loss.item()` plateau before
  scaling up.
- **Device**: torchquantum simulators run on CPU by default; pass
  `device='cuda'` if your build supports it.
- **Seeds**: set `torch.manual_seed`, `numpy.random.seed`, and pass
  `random_state` to scikit-learn — QML training is sensitive.

## Cheat sheet — native torch params (v0.0.15, recommended for new code)

Since uniqc 0.0.15, a `Circuit` has first-class trainable parameters:
pass a `torch.Tensor` into a gate and it is auto-registered as an
`nn.Parameter`, reachable via `Circuit.param_map` (positional) or
`Circuit.param_dict` (name-keyed). `uniqc.expectation()` then computes
a differentiable expectation value across statevector / TorchQuantum
backends — autograd flows through both.

```python
import torch
from uniqc import Circuit, expectation
from uniqc.algorithms.core.measurement import Pauli

# Build a 1-qubit RX circuit with a trainable angle.
theta = torch.tensor(0.1, requires_grad=True)
c = Circuit(1)
c.rx(0, theta)
assert c.has_param          # property: True iff ≥1 param is a torch.Tensor

# expectation() is backend-agnostic and differentiable.
target_z = -1.0
opt = torch.optim.Adam([theta], lr=0.1)
for epoch in range(100):
    opt.zero_grad()
    e = expectation(c, Pauli("Z0"))   # scalar torch.Tensor
    loss = (e - target_z) ** 2
    loss.backward()
    opt.step()
    if (epoch + 1) % 20 == 0:
        print(f"epoch {epoch+1:3d}  ⟨Z⟩={float(e):+.4f}  loss={loss.item():.4f}")
```

Key v0.0.15 entry points:

- `Circuit.param_map` — positional list of trainable parameters (mirrors
  the order tensor params were added).
- `Circuit.param_dict` — name-keyed view for friendly `state_dict()`
  round-trips (`{gate-name: torch.Tensor}`).
- `Circuit.has_param` (property) — `True` only when ≥1 param is a
  `torch.Tensor`. Pure float params → `False`. *(Distinct from the
  `has_param=` keyword argument on `add_gate(...)` / convenience gate
  methods, which opts-in to auto-creating an `nn.Parameter` for a
  specific gate.)*
- `Circuit.has_tensor_params()` — equivalent method form; same semantics.
- `Circuit.set_param_last(value)` — setter for the most recently added
  parametric gate; raises `IndexError` on an empty circuit (v0.0.15 fix).
- `uniqc.expectation(circuit, observable, backend=...)` — backend-agnostic
  differentiable expectation. Exposed at the top level.

Use this layer when:

- you don't need parameter-shift on hardware (statevector is enough);
- you want minimal boilerplate (no `circuit_def` / `QuantumLayer`);
- the model gradient should match plain autograd on the
  statevector — no finite-difference / parameter-shift gap.

Fall back to `QuantumLayer` (layer 2) when you need parameter-shift
gradients (e.g., on real hardware / dummy backends with sampling
noise), and to layer 1 classifiers when you want a one-line
classifier with sklearn-like fit semantics.

## Cheat sheet — `QNNClassifier`

```python
import torch
import torch.nn as nn
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler
from uniqc import QNNClassifier

X_np, y_np = make_moons(n_samples=200, noise=0.15, random_state=42)
X_np = StandardScaler().fit_transform(X_np)
X = torch.tensor(X_np, dtype=torch.float32)
y = torch.tensor(y_np, dtype=torch.float32)

model = QNNClassifier(n_qubits=4, n_features=2, depth=2)
opt = torch.optim.Adam(model.parameters(), lr=0.01)
loss_fn = nn.BCELoss()

for epoch in range(50):
    opt.zero_grad()
    y_pred = model(X)
    loss = loss_fn(y_pred, y)
    loss.backward()
    opt.step()
    if (epoch + 1) % 10 == 0:
        acc = ((y_pred > 0.5).float() == y).float().mean()
        print(f"epoch {epoch+1:3d}  loss={loss.item():.4f}  acc={acc:.4f}")
```

## Cheat sheet — `QuantumLayer` (custom circuit)

> ⚠️ `QuantumLayer` in uniqc 0.0.13.dev0 needs a circuit built via
> `circuit_def(...).build_standalone()` — building with bare
> `Circuit()` + `Parameter("theta")` will **not** populate the
> `_parameters` dict and the backward pass crashes. If `QuantumLayer`
> misbehaves, fall back to the manual parameter-shift loop in
> `examples/quantumlayer_demo.py`. See `references/quantumlayer.md`
> for the full story.

```python
import math
import torch
from uniqc import circuit_def, QuantumLayer
from uniqc.algorithms.core.measurement import pauli_expectation

@circuit_def(name="single_rx", qregs={"q": 1}, params=["theta"])
def single_rx(circ, q, theta):
    circ.rx(q[0], theta[0])
    return circ

qc = single_rx.build_standalone()
layer = QuantumLayer(
    circuit=qc,
    expectation_fn=lambda c: pauli_expectation(c, "Z0"),
    n_outputs=1,
    init_params=torch.tensor([1.0]),
    shift=math.pi / 2,
)
print(layer())          # forward pass returns a torch tensor
```

`QuantumLayer.parameters()` returns a torch `Parameter` you can hand to
any optimiser. Parameter names live at `layer._param_names` (private —
no public accessor in this version).

## Names to remember

- **Native torch params (v0.0.15, layer 0)**: `Circuit.param_map`,
  `Circuit.param_dict`, `Circuit.has_param` (property) /
  `Circuit.has_tensor_params()`, `Circuit.set_param_last(value)`,
  `uniqc.expectation(circuit, observable, backend=...)`. Pass
  `torch.Tensor` into any gate to auto-register as `nn.Parameter`. The
  upstream best-practice example is
  `examples/3_best_practices/11_native_torch_training.py`.
- High-level classifiers (need torchquantum): `QNNClassifier`,
  `QCNNClassifier`, `HybridQCLModel`.
- Low-level wrapping: `QuantumLayer(circuit, expectation_fn, n_outputs,
  init_params, shift)` from `uniqc.torch_adapter.quantum_layer`
  (re-exported as `uniqc.QuantumLayer`).
- Symbolic params on `Circuit`: `uniqc.Parameter("name")` — substitute
  via `circuit.bind({theta: value})`. (Distinct from layer-0 native
  torch params; symbolic params remain useful for hand-rolled
  parameter-shift loops.)
- Optional extra: `pip install unified-quantum[pytorch]` — pulls both
  torch and torchquantum-ng (import name stays `torchquantum`).

## Response style

- Always do `StandardScaler` on classical features unless the user has
  a reason not to. Mention it explicitly; it is the most common silent
  bug in QML demos.
- For new architectures, prototype with `QuantumLayer` over a small
  circuit; only graduate to torchquantum when you need the high-level
  classes.
- Print loss every 10 epochs, not every step — reduces noise in the log.
- Save `model.state_dict()` after training; QML hyperparameter sweeps
  are expensive to redo.
