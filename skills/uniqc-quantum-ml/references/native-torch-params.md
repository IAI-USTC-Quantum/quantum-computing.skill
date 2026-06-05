# Native PyTorch parameter integration (uniqc ≥ 0.0.15)

Since uniqc 0.0.15, `Circuit` exposes first-class trainable parameters.
You no longer need to wrap your circuit in `circuit_def` or `QuantumLayer`
just to train it with PyTorch — pass a `torch.Tensor` directly into any
parametric gate and uniqc auto-registers it as an `nn.Parameter`.

This page is the canonical reference for the **layer 0** workflow shown
on the main SKILL.md page.

## Mental model

| API                          | Role                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------- |
| `c.add_gate(..., torch.Tensor)` (or convenience `c.rx(0, theta_tensor)`) | Param is auto-registered as `nn.Parameter`.            |
| `c.add_gate(..., has_param=True)` (kwarg) | **Opt-in** auto-creation of an `nn.Parameter` for that gate. Different from the property below. |
| `c.param_map`                | Ordered list (`list[torch.Tensor]`) of registered tensor params — positional access.  |
| `c.param_dict`               | Name-keyed view (`dict[str, torch.Tensor]`) for `state_dict` round-trips.             |
| `c.has_param` (property)     | `True` iff ≥1 param is a `torch.Tensor`. Pure-float params → `False`.                 |
| `c.has_tensor_params()`      | Method form of the property; same semantics.                                          |
| `c.set_param_last(value)`    | Setter for the most recently added parametric gate; raises `IndexError` on empty circuit (v0.0.15 fix). |
| `uniqc.expectation(c, obs)`  | Backend-agnostic differentiable expectation; works on statevector / TorchQuantum.     |

> 🔍 The `has_param` **property** (no-argument query) and the `has_param=`
> **kwarg** (passed to `add_gate` / convenience gate methods) are unrelated
> names sharing the same English word. The property tests `Circuit`-wide
> trainability; the kwarg flips on per-gate auto-creation. Conflating them
> is a real footgun — when in doubt, use `c.has_tensor_params()` for the
> circuit-level query.

## End-to-end training loop

```python
import torch
from uniqc import Circuit, expectation
from uniqc.algorithms.core.measurement import Pauli

# Drive ⟨Z⟩ to -1 (i.e. flip |0⟩ to |1⟩) via gradient descent on θ.
theta = torch.tensor(0.05, requires_grad=True)
c = Circuit(1)
c.rx(0, theta)
assert c.has_param                # True iff ≥1 tensor param

opt = torch.optim.Adam([theta], lr=0.1)
for epoch in range(200):
    opt.zero_grad()
    e = expectation(c, Pauli("Z0"))   # scalar torch.Tensor, autograd-aware
    loss = (e + 1.0) ** 2             # target: ⟨Z⟩ = -1
    loss.backward()
    opt.step()
    if (epoch + 1) % 50 == 0:
        print(f"epoch {epoch+1:3d}  ⟨Z⟩={float(e):+.4f}  θ={float(theta):+.4f}")
```

Multi-parameter circuits work the same way — every tensor param is
registered, autograd tracks all of them:

```python
thetas = [torch.tensor(0.1, requires_grad=True) for _ in range(3)]
c = Circuit(2)
c.rx(0, thetas[0])
c.ry(1, thetas[1])
c.cnot(0, 1)
c.rz(0, thetas[2])

opt = torch.optim.Adam(thetas, lr=0.05)
for _ in range(100):
    opt.zero_grad()
    e = expectation(c, Pauli("Z0Z1"))
    (e - 1.0).pow(2).backward()
    opt.step()
```

## `state_dict()` round-trip

`Circuit.param_dict` gives you name-keyed access for stateful
checkpointing. Treat it as the QML-equivalent of `nn.Module.state_dict()`:

```python
# Save
snapshot = {k: v.detach().clone() for k, v in c.param_dict.items()}

# Restore by re-binding tensors with requires_grad
for k, t in snapshot.items():
    c.param_dict[k].data.copy_(t)
```

## When to use this over `QuantumLayer` / `QNNClassifier`

| You want…                                                                      | Use                              |
| ------------------------------------------------------------------------------ | --------------------------------- |
| Minimal-boilerplate VQE / single-circuit optimisation on statevector           | **Native torch params (layer 0)** |
| Real-hardware / dummy-sampling gradient via parameter-shift                    | `QuantumLayer` (layer 2)          |
| One-line sklearn-style classifier on tabular / image data                      | `QNNClassifier` / `QCNNClassifier` (layer 1, needs torchquantum) |
| Manual gradient research / custom parameter-shift rule                         | Hand-written (layer 3)            |

For real-hardware training, layer 0 isn't a fit — `uniqc.expectation()`
uses statevector autograd and assumes a noiseless, fully-observable
backend. Switch to `QuantumLayer`'s parameter-shift gradient for
sampling-based backends.

## Cross-references

- Upstream best-practice example:
  `examples/3_best_practices/11_native_torch_training.py` in the
  UnifiedQuantum repo.
- Backend list accepted by `uniqc.expectation(..., backend=...)`:
  statevector (default), TorchQuantum (`backend="torchquantum"` if
  installed).
- For the parameter-shift mathematics behind `QuantumLayer`, see
  [parameter-shift.md](parameter-shift.md).
