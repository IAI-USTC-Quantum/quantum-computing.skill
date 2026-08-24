# Cache freshness check

`find_backend(chip)` reads from the **on-disk** cache. Cache writes
only happen on `uniqc backend update --platform <p>` or
`backend chip-display ... --update`. Both routinely lag the live
chip.

## Step 1 — read the timestamps

```python
from uniqc import find_backend
from datetime import datetime, timezone

bi = find_backend("originq:WK_C180")
cached = datetime.fromisoformat(bi.calibrated_at.replace("Z", "+00:00"))
age = datetime.now(timezone.utc) - cached
print(f"chip={bi.backend_name}  cached_at={bi.calibrated_at}  age={age}")
```

## Step 2 — refresh

```bash
uniqc backend update --platform originq        # cross-platform: also use ibm/quark
uniqc backend chip-display originq/WK_C180 --update
```

uniqc 0.0.13 fix: this **actually** refreshes IBM / Quark caches now
(and TianYan / LogicalQubit since 0.1.0);
prior versions silently no-op'd for IBM and reported success. Also: when
the platform SDK returns 0 backends (typically a credential / instance
problem), the new logic keeps the existing cache instead of overwriting
it with an empty list.

## Step 3 — diff before/after

```python
import json
from pathlib import Path
import shutil

snapshot_dir = Path("~/uniqc-snapshots").expanduser()
snapshot_dir.mkdir(exist_ok=True)

src = Path("~/.uniqc/backend/chips/originq-WK_C180.json").expanduser()
prev = snapshot_dir / "WK_C180.prev.json"
curr = snapshot_dir / "WK_C180.curr.json"

if curr.exists():
    shutil.move(curr, prev)
shutil.copy(src, curr)

if prev.exists():
    a = json.loads(prev.read_text())
    b = json.loads(curr.read_text())
    print(f"calibrated_at: {a.get('calibrated_at')!r} -> {b.get('calibrated_at')!r}")
    # compare any fidelity field of interest
```

## When to refresh

| Workflow                             | Recommended refresh cadence     |
| ------------------------------------ | ------------------------------- |
| Daily VQE / QAOA on a fixed region   | At session start                |
| Quantum Volume / GHS publication run | Immediately before the run + after |
| Long-lived dashboard / monitor       | Every 1–6 hours                 |
| Casual exploration                   | Once a day                      |

## Sanity checks on the refreshed data

After refresh, sanity-check the **size** and **shape** of the cache,
not just the timestamp:

- `bi.qubits.n_qubits` shouldn't change between refreshes (chip is
  fixed). A change means you queried the wrong chip name.
- `bi.qubits.available_qubits` will shrink/grow as qubits are
  retired or returned to service.
- `bi.qubits.coupling_map` shouldn't change between refreshes either,
  modulo the same retirement story.
- `bi.basis_gates` is a vendor decision — usually stable for months.
  Sudden change means you should check the platform release notes
  before assuming your old circuits still compile.
