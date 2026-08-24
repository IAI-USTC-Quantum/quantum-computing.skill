# `uqt_*` task ids and shards

Since uniqc ≥ 0.0.12, every `submit_task` and `submit_batch` call returns a
single **uniqc-managed** task id of the form `uqt_<32-hex>` (36 chars,
including the `uqt_` prefix). This id is what you store, log, and reuse —
not the platform-native ids underneath it.

## Why this exists

- Different platforms returned wildly different id formats (OriginQ MD5,
  IBM `cp...`, Dummy `0x...`); downstream scripts kept
  hard-coding format assumptions.
- Auto-sharding: a batch of 500 circuits on OriginQ becomes 3 native task
  ids (default `task_group_size=200`), but the user only ever sees one id.
- Retry / re-issue logic gets a stable handle even when the backing
  platform rejects part of a batch.

## Inspect the mapping

Python:

```python
from uniqc import get_platform_task_ids
shards = get_platform_task_ids(uid)            # list[TaskShard]
for s in shards:
    print(s.shard_index, s.platform, s.platform_task_id, s.circuit_count, s.status)
```

CLI:

```bash
uniqc task shards uqt_xxxx...                  # rich table
uniqc task shards uqt_xxxx... -f json          # machine-readable
```

REST (when the local gateway is running):

```bash
curl http://127.0.0.1:8000/api/tasks/uqt_xxxx/shards
```

(Start the gateway with `uniqc gateway start --port 8000`.)

## Recover the platform id when you need it

Most pipelines should not care, but two real cases:

1. **Manually inspecting a task in the cloud console.**
   ```python
   shards = get_platform_task_ids(uid)
   print(shards[0].platform_task_id)            # paste into the cloud UI
   ```
2. **Bypassing the uniqc id entirely.**
   ```python
   ids = submit_batch(circuits, backend="originq:WK_C180",
                      shots=200, return_platform_ids=True)
   # ids: list[str] of platform-native ids; query_task / wait_for_result
   # still expect a uqt_* though — keep the uniqc id around if you intend
   # to use either of those.
   ```

## What `wait_for_result` actually returns

| Submission                          | `wait_for_result(uid)` returns |
| ----------------------------------- | ------------------------------ |
| `submit_task(c)`                    | `UnifiedResult` (single)       |
| `submit_batch([c1, c2, ...])`       | `list[UnifiedResult]` (per circuit, in order) |
| Failure                             | `None` (or per-element `None` inside the list) |

`UnifiedResult` is dict-like over its `counts`, so existing code that did
`result["00"]` / `for k in result` keeps working.

## Cache invariants

- `~/.uniqc/cache/tasks.sqlite` stores both the parent `uqt_*` row and
  every shard. Old (pre-0.0.12) rows that only had a platform id get
  auto-migrated on first read; the original platform id is preserved at
  `metadata.legacy_platform_id`.
- Passing a raw platform id to `query_task` **no longer resolves** — the
  implicit fallback through the shard index was removed in 0.1.0 (the
  shard index itself, `TaskStore.find_uniqc_id_by_platform_id`, stays for
  internal use). Always keep the `uqt_*` id from submission.
- `submit_task`/`submit_batch` never return the legacy format unless you
  pass `return_platform_ids=True`.

## Common pitfalls

- "I got `len(uid) == 36`, why?" — that's `uqt_` (4) + 32 hex chars.
  Don't slice it down to 32 expecting the old MD5/UUID shape.
- Storing `uid[:8]` as a unique key — collisions are unlikely but possible
  for large operations. Store the full string.
- Mixing legacy and uniqc ids in one workflow — pick one and stick to it
  until you have migrated all surrounding tooling.
