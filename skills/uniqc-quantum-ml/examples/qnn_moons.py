#!/usr/bin/env python3
"""QNNClassifier on make_moons. Needs torchquantum.

Install:
    pip install unified-quantum[pytorch] scikit-learn

Usage:
    python qnn_moons.py
"""

from __future__ import annotations


def main() -> None:
    try:
        import torch
        import torch.nn as nn
        from sklearn.datasets import make_moons
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from uniqc import QNNClassifier
    except ImportError as exc:
        raise SystemExit(
            f"Required dependencies missing: {exc}\n"
            "Install with:\n"
            "  pip install unified-quantum[pytorch] scikit-learn"
        )

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

    print(f"trainable parameters: {sum(p.numel() for p in model.parameters())}")

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

    torch.save(model.state_dict(), "qnn_moons.pt")
    print("saved -> qnn_moons.pt")


if __name__ == "__main__":
    main()
