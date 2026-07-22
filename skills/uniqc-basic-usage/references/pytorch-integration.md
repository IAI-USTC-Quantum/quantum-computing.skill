# PyTorch 集成参考

## 目录

- 当前公开接口
- `QuantumLayer`
- Parameter-shift 辅助函数
- 批处理辅助函数
- `TorchQuantumLayer`
- 使用这些接口时记住

UnifiedQuantum 当前的 PyTorch 集成是辅助工具风格，而不是“一整套端到端训练框架”。

基础安装（已包含 TorchQuantum 专用后端所需的 `torchquantum-ng`，导入名仍为 `torchquantum`）：

```bash
pip install "unified-quantum[pytorch]"
```

## 当前公开接口

```python
from uniqc.torch_adapter import (
    QuantumLayer,
    batch_execute,
    batch_execute_with_params,
    parameter_shift_gradient,
    compute_all_gradients,
)
```

这些对象也是 `uniqc` 顶层的 lazy export，可以写 `from uniqc import batch_execute`，但显式 `from uniqc.torch_adapter import ...` 仍然可用且更明确。

可选情况下还可能有：

```python
from uniqc.torch_adapter import TorchQuantumLayer
```

## `QuantumLayer`

`QuantumLayer` 是一个基于 parameter-shift 的 `nn.Module` 包装器。

它需要两个核心输入：

1. 一个带参数映射的电路模板
2. 一个从绑定后线路计算期望值的函数

这里要特别保守一点说明：

- `QuantumLayer` 不是“给任意 `Circuit` 一包就能直接训练”
- 调用方需要准备好一个适配它的参数化线路模板
- 如果用户只是想先验证思路，通常先用 `parameter_shift_gradient` 或 `batch_execute_with_params` 更稳

因此更稳妥的理解是：把 `QuantumLayer` 当成“已有参数化线路模板后的包装器”，不要把它当成零配置的端到端训练入口。

最小可运行示例：

```python
import torch
from uniqc import Circuit, Parameter
from uniqc.torch_adapter import QuantumLayer

theta = Parameter('theta')
qc = Circuit(); qc.ry(0, theta); qc.measure(0)

def expectation(circuit) -> float:
    from uniqc.simulator import Simulator
    probs = Simulator().simulate_pmeasure(circuit)
    return probs[0] - probs[1]            # ⟨Z⟩

layer = QuantumLayer(
    circuit=qc,
    expectation_fn=expectation,
    init_params=torch.zeros(1),
)
```

- 构造签名是 `QuantumLayer(circuit, expectation_fn, n_outputs=1, init_params=None, shift=π/2)`。
- 参数名从 `circuit._parameters` 自动读取，**不要**传 `param_names=`。
- `expectation_fn(circuit)` 接收一个**已经绑定好参数**的 `Circuit`，返回 Python `float`（或者长度 `n_outputs` 的浮点序列）。

## Parameter-shift 辅助函数

### 单参数梯度

```python
from uniqc.torch_adapter import parameter_shift_gradient

grad = parameter_shift_gradient(circuit, "theta", expectation_fn)
```

### 全部参数梯度

```python
from uniqc.torch_adapter import compute_all_gradients

grads = compute_all_gradients(circuit, expectation_fn)
```

## 批处理辅助函数

### 批量执行多个线路

```python
from uniqc.torch_adapter import batch_execute

results = batch_execute(circuits, executor, n_workers=4)
```

### 对一个模板绑定多组参数

```python
from uniqc.torch_adapter import batch_execute_with_params

results = batch_execute_with_params(
    circuit_template,
    [{"theta": 0.1}, {"theta": 0.2}],
    executor,
)
```

## `TorchQuantumLayer`

如果用户安装了 `torchquantum`，还可能使用 `TorchQuantumLayer`，它走的是 TorchQuantum 的原生自动求导路径，而不是 parameter-shift。

适合场景：

- 已经在用 TorchQuantum
- 想要更“端到端”的可微分体验

## 使用这些接口时记住

- 把这些工具理解为“辅助工具”
- 用户仍要自己定义 expectation / loss / optimizer
- 不要默认 UnifiedQuantum 自带完整数据集管道
- 如果示例需要 `torchvision`、`scikit-learn` 等第三方库，要单独确认这些依赖
