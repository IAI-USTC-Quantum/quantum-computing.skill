# `QNNClassifier` — tabular binary classification

`QNNClassifier(n_qubits=4, n_features=2, depth=2)` is the simplest
PyTorch QML model in uniqc. It encodes `n_features` classical inputs
into `n_qubits` qubits via angle encoding, runs a depth-`depth`
hardware-efficient ansatz, and reads out a sigmoid-activated scalar.

## Install

```bash
pip install unified-quantum[pytorch] scikit-learn
```

## End-to-end on `make_moons`

```python
import torch
import torch.nn as nn
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from uniqc import QNNClassifier


def main():
    torch.manual_seed(0)

    X_np, y_np = make_moons(n_samples=400, noise=0.15, random_state=42)
    X_np = StandardScaler().fit_transform(X_np)
    X_train_np, X_test_np, y_train_np, y_test_np = train_test_split(
        X_np, y_np, test_size=0.2, random_state=42)

    X_train = torch.tensor(X_train_np, dtype=torch.float32)
    y_train = torch.tensor(y_train_np, dtype=torch.float32)
    X_test  = torch.tensor(X_test_np,  dtype=torch.float32)
    y_test  = torch.tensor(y_test_np,  dtype=torch.float32)

    model = QNNClassifier(n_qubits=4, n_features=2, depth=2)
    opt   = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.BCELoss()

    for epoch in range(60):
        opt.zero_grad()
        y_pred = model(X_train)
        loss = loss_fn(y_pred, y_train)
        loss.backward()
        opt.step()
        if (epoch + 1) % 10 == 0:
            with torch.no_grad():
                tr_acc = ((y_pred > 0.5).float() == y_train).float().mean()
                te_pred = model(X_test)
                te_acc = ((te_pred > 0.5).float() == y_test).float().mean()
            print(f"epoch {epoch+1:3d}  loss={loss.item():.4f}  "
                  f"tr_acc={tr_acc:.4f}  te_acc={te_acc:.4f}")


if __name__ == "__main__":
    main()
```

## Hyperparameter knobs

| arg          | default | meaning                                                              |
| ------------ | ------- | -------------------------------------------------------------------- |
| `n_qubits`   | 4       | width of the quantum register; `≥ n_features`                        |
| `n_features` | 2       | number of classical input features per sample                        |
| `depth`      | 2       | number of HEA-style entangler layers; deeper = more parameters       |

Total trainable count: roughly `2 * n_qubits * depth + n_features * n_qubits`.

## Tips

- If `n_features > n_qubits`, the encoder will reuse qubits — usually a
  bad idea. Bump `n_qubits` instead.
- `depth=2` gives 16 trainable parameters for `n_qubits=4`; enough for
  toy 2D datasets. Move to `depth=3` only if loss plateaus too early.
- For multi-class problems, replace `QNNClassifier` with a small wrapper
  around `QuantumLayer(n_outputs=K)` and `nn.CrossEntropyLoss` — see
  the QuantumLayer reference.

## Inspecting what the model learned

```python
print(model.state_dict())
print("trainable param count:", sum(p.numel() for p in model.parameters()))
```

The state dict keys reflect the underlying torchquantum `Op` parameters
plus any classical readout / encoder weights.

## Saving / loading

```python
torch.save(model.state_dict(), "qnn_moons.pt")

new_model = QNNClassifier(n_qubits=4, n_features=2, depth=2)
new_model.load_state_dict(torch.load("qnn_moons.pt"))
new_model.eval()
```

The constructor must match the saved geometry — `n_qubits`, `n_features`,
`depth` all matter. Store them alongside the weights file.

## When to pick this vs. the others

- **`QNNClassifier`** — tabular features, binary labels, ≤ ~10
  features.
- **`QCNNClassifier`** — quantum-state inputs (already prepared
  amplitude vectors), pooling layers reduce qubit count.
- **`HybridQCLModel`** — classical → quantum → classical sandwich. Pick
  this when your dataset is too high-dim for direct angle encoding.
