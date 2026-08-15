# Backend cache & refresh

uniqc keeps two on-disk caches for backend data:

| Path                                  | Contents                                    |
| ------------------------------------- | ------------------------------------------- |
| `~/.uniqc/backend/backends.json`       | aggregated cross-platform backend list      |
| `~/.uniqc/backend/chips/`              | per-chip characterization (qubit fidelities, T1/T2, coupling map, basis gates, etc.) |

These are **lazy** — uniqc only refreshes on explicit
`uniqc backend update --platform <p>` (or `--update` on
`backend chip-display`).

> Migration note: uniqc migrates legacy `~/.uniqc/cache/backends.json` and
> `~/.uniqc/backend-cache/` on first access. Use only the paths in the table
> above in new commands and automation.

## What changed in 0.0.13

- **`uniqc backend update --platform ibm|quafu|quark`** now actually
  refreshes the on-disk chip cache via each adapter's
  `get_chip_characterization`. Previously it raised "Cache refresh not
  implemented for provider …" silently, so `backend list` returned
  stale rows for days.
- **IBM specifically** — `_build_adapter(Platform.IBM)` returned a
  bare `QiskitAdapter` whose inherited `list_backends` raised
  `NotImplementedError`; `fetch_platform_backends`'s broad `except
  Exception` swallowed it and reported success while persisting an
  empty list **on top of an existing cache**. Both issues are now
  fixed: the canonical IBM adapter implements the methods, and a
  fetched-zero result no longer overwrites the existing cache (it
  reports `fetched_newly=False` instead).

## Refresh recipe

```bash
uniqc backend update --platform originq
uniqc backend update --platform ibm
uniqc backend update --platform quark
uniqc backend list
```

Per-chip detailed data:

```bash
uniqc backend chip-display originq/WK_C180 --update
```

After `--update`, inspect:

```bash
ls -lt ~/.uniqc/backend/chips/ | head
```

## Programmatic check

```python
from uniqc import find_backend
bi = find_backend("originq:WK_C180")
print(bi.calibrated_at, bi.qubits.n_qubits, bi.basis_gates)
```

If `find_backend` raises `BackendNotFoundError`:

1. `uniqc doctor` — confirm the originq SDK is installed and the token
   is configured.
2. `uniqc backend update --platform originq` — refresh.
3. `uniqc backend list --platform originq` — confirm the chip name
   appears (case sensitive on real submit; `WK_C180` ≠ `wk_c180`).

## Cache invalidation

There is no TTL — the cache grows until you delete it. To force a
clean slate:

```bash
rm ~/.uniqc/backend/backends.json
rm -r ~/.uniqc/backend/chips/
uniqc backend update --platform originq
uniqc backend update --platform ibm
uniqc backend update --platform quark
```

For the calibration cache (XEB / readout — separate location), see the
`uniqc-xeb-qem` skill: `~/.uniqc/calibration_cache/`.
