# Submit, poll, and fetch results

The minimal happy path:

```text
config validate -> dry-run -> submit -> task show -> result --wait
```

## End-to-end Python (single circuit)

```python
from uniqc import (
    Circuit, compile, find_backend,
    dry_run_task, submit_task,
    query_task, wait_for_result,
)

c = Circuit(2); c.h(0); c.cnot(0, 1); c.measure(0); c.measure(1)

# 1. dry-run
check = dry_run_task(c, backend="originq:WK_C180", shots=200)
if not check.success:
    raise RuntimeError(check.error or check.details)

# 2. compile against the chip (skip if you only target dummy/simulators)
bi = find_backend("originq:WK_C180")
c_native = compile(c, bi, level=2)            # H/CNOT -> CZ/SX/RZ

# 3. submit
uid = submit_task(c_native, backend="originq:WK_C180", shots=200)
print("uniqc task id:", uid)                  # uqt_<32-hex>

# 4. status
info = query_task(uid)
print(info.status, info.platform, info.created_at)

# 5. wait & fetch (blocks)
result = wait_for_result(uid, timeout=300, poll_interval=5)
print(result.counts)                          # dict[str, int]
print("shots:", result.shots, "platform:", result.platform)
```

## End-to-end CLI

```bash
# from a saved file
uniqc submit circuit.originir --backend originq:WK_C180 --shots 200 --dry-run
uid=$(uniqc submit circuit.originir --backend originq:WK_C180 --shots 200)
echo "$uid"

uniqc task show "$uid"
uniqc result "$uid" --wait                    # blocks until success/fail
uniqc result "$uid" --json                    # machine-readable counts
```

`uniqc result <uid>` (without `--wait`) returns immediately with whatever
the gateway has cached. `--wait` polls every 5s by default; tune with
`--poll-interval`.

## Batches in one task id (uniqc ≥ 0.0.12)

```python
from uniqc import submit_batch, wait_for_result

uid = submit_batch(circuits, backend="originq:WK_C180", shots=200)
print(uid)                                    # one uqt_* even if there are 1000 circuits
results = wait_for_result(uid, timeout=600)   # -> list[UnifiedResult]

for i, r in enumerate(results):
    print(i, r.counts if r is not None else "FAILED")
```

Why one id for many circuits:

- Backends with native batch support (OriginQ ≤ 200/group, IBM ≤ 100/group)
  use it; uniqc shards above that limit transparently.
- Backends with no native batch (Quark / TianYan / LogicalQubit / Dummy) get
  one shard per circuit but the user still sees a single `uqt_*`.

To recover the underlying platform task ids:

```python
from uniqc import get_platform_task_ids
for s in get_platform_task_ids(uid):
    print(s.shard_index, s.platform_task_id, s.circuit_count, s.status)
```

CLI: `uniqc task shards "$uid"` (table) or `-f json` (machine-readable).

## Polling without blocking

```python
import time
from uniqc import query_task

uid = submit_task(c, backend="originq:WK_C180", shots=200)
while True:
    info = query_task(uid)
    if info.status in ("SUCCESS", "FINISHED", "FAILED"):
        break
    time.sleep(10)
```

`info.status` strings come from the platform; `wait_for_result` already
implements this loop with timeout + sane terminal-state detection — prefer
it unless you need custom logic.

## Useful submit kwargs

| kwarg              | default | notes                                                                                                |
| ------------------ | ------- | ---------------------------------------------------------------------------------------------------- |
| `shots`            | `1000`  | Real-hardware first run: 100–200.                                                                    |
| `local_compile`    | `1`     | qiskit transpile pass, `optimization_level`. `0` skips, `2`/`3` deeper. qiskit is a **core dep** in 0.0.13 — no extra needed.        |
| `cloud_compile`    | `1`     | Ask cloud to optimise. `0` to disable.                                                                                                |
| `metadata`         | `None`  | `dict` saved alongside the task in `~/.uniqc/cache/tasks.sqlite`.                                                                     |
| `options`          | `None`  | Platform-specific `BackendOptions` (e.g. `QuarkOptions(chip_id="Baihua", compile=True)`).                                             |
| `backend_name`     | `None`  | Legacy two-arg form (`backend="originq", backend_name="WK_C180"`). uniqc 0.0.13 prefers (and largely enforces) the single `provider:chip` string. |

## Re-attaching to an old task id from a fresh shell

`~/.uniqc/cache/tasks.sqlite` is the source of truth. Anywhere uniqc is
installed and pointed at the same config dir, you can do:

```bash
uniqc task show uqt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
uniqc result   uqt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx --wait
```

```python
from uniqc import wait_for_result
result = wait_for_result("uqt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", timeout=600)
```

If you only have the platform-native task id (e.g. an OriginQ MD5), note
that the implicit platform-id → `uqt_*` lookup fallback was **removed in
0.1.0**: `query_task("<platform_id>")` no longer resolves it. Recover the
`uqt_*` from your submission log/output, or query the platform console
directly. (The shard index itself stays; only the implicit fallback is gone.)
