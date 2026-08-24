# Error → action mapping

uniqc 0.0.13 enriched every public-facing error with a doc link and
a one-line fix hint. Read the error message verbatim and follow that
hint first. The table below is the curated short list for issues
that actually surface during installation, configuration, and the
first cloud submit.

| Error class                          | Most common trigger                                                                                                  | First fix                                                                                                                  |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `MissingDependencyError`             | A platform SDK / extra is not installed (the message names which one).                                              | Run the `pip install ...` line embedded in the error; re-run `uniqc doctor`.                                              |
| `ConfigError` / `ConfigValidationError` | Token / proxy / instance field missing or malformed.                                                              | `uniqc config set <key> <value>`; re-run `uniqc config validate`.                                                          |
| `AuthenticationError`                | Token rejected by the platform.                                                                                      | Re-issue the token from the platform console; re-set; `uniqc config validate`.                                            |
| `BackendNotFoundError`               | Chip name typo, or `backend list` is stale.                                                                          | `uniqc backend update --platform <p>`; `uniqc backend list --platform <p>` to find the canonical chip id (case-sensitive). |
| `BackendNotAvailableError`           | Chip is in maintenance / offline.                                                                                    | Pick another chip; `uniqc backend list --platform <p>` shows status.                                                        |
| `NetworkError`                       | Outbound HTTPS blocked.                                                                                              | See `proxy.md`. For IBM: `uniqc config set ibm.proxy.https <URL>`.                                                          |
| `PlatformNotFoundError`              | `backend="ibm:..."` but `ibm` SDK / config absent.                                                                   | `uniqc doctor`; install the SDK / set the token.                                                                           |
| `ProfileNotFoundError`               | `UNIQC_PROFILE=<x>` set, but `<x>` not in `config.yaml`.                                                             | `unset UNIQC_PROFILE`, or `uniqc config init-profile <x>`.                                                                  |
| `InsufficientCreditsError` / `QuotaExceededError` | Real-hardware account out of quota.                                                                  | Lower shots; switch to `dummy:<platform>:<chip>` for development; contact platform support.                                 |
| `TaskNotFoundError`                  | `query_task("<id>")` for an id not in `~/.uniqc/cache/tasks.sqlite`.                                                 | If the id is a `uqt_*`, you may be on a different config profile / different machine. Re-attach via REST / re-submit.       |
| `TaskFailedError`                    | Job ran but platform reported failure.                                                                                | Inspect `query_task(uid).error`; `uniqc task shards <uid>` for batch failures.                                              |
| `TaskTimeoutError`                   | `wait_for_result(uid, timeout=...)` hit the limit before the platform finished.                                      | Retry with longer timeout, or use `poll_result(uid)` in your own loop. The task is **still running** — id stays valid.      |
| `StaleCalibrationError`              | A `qem` mitigator refused to apply because the calibration cache row is older than `max_age_hours`.                  | Re-run the calibration (`uniqc calibrate readout/xeb …`). Inherits from `Exception`, not `UnifiedQuantumError` — catch separately. |
| `CompilationFailedError`             | Topology / basis-gate mismatch (qiskit transpile failure). Pre-0.0.13 also triggered by missing `[qiskit]` extra; in 0.0.13 qiskit is core. | Check that the chip exposes the gates you need; reduce circuit; pass `local_compile=0` to skip qiskit pass.                |
| `CircuitTranslationError`            | Source IR cannot be parsed into the platform's submit language (OriginIR ↔ QASM2 conversion failed).                  | Inspect the failing gate / parameter; reduce the offending block.                                                            |
| `UnsupportedGateError`               | Submitted IR uses a gate the chip's basis set doesn't support.                                                        | Compile first (`compile(c, find_backend(...), level=2)`) or choose a different chip.                                        |
| `TopologyError`                      | Two-qubit gate on a non-coupled pair.                                                                                  | `compile(...)` to insert SWAPs; or pick connected qubits via `RegionSelector`.                                              |
| `RegisterDefinitionError` / `RegisterNotFoundError` / `RegisterOutOfRangeError` | OriginIR / QASM2 has malformed register definitions.                                            | Auto-emit registers (`Circuit` does this) or check the input file.                                                          |
| `BackendOptionsError`                | Wrong `BackendOptions` subclass for the platform (e.g. `OriginQOptions` passed to `quark`).                          | Use `BackendOptionsFactory().create_default('quark')` or `from_kwargs('quark', **kw)`.                                       |
| `ModuleNotFoundError: uniqc.backend_adapter.task.adapters.quafu_adapter` | Quafu was removed in 0.1.0 (deprecated through 0.0.x).                                                             | Migrate to Quark: `pip install unified-quantum[quark]`, backend `quark:<chip>`.                                               |

## Debugging cadence

1. **Read the error verbatim.** The hint and doc link are part of the
   message in 0.0.13.
2. **`uniqc doctor`.** Cross-check the env, deps, and tokens. Most
   user-reported "submit fails" issues are caught here.
3. **One change at a time.** Reset config, refresh cache, retry
   doctor. Don't fix three things at once — you won't know which
   helped.
4. **Smoke test against `dummy:local:simulator` / `dummy:<platform>:<chip>`**
   before retrying real hardware. The dummy paths require no quota and
   exercise the same submit / query / wait code paths.
