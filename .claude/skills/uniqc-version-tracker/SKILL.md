---
name: uniqc-version-tracker
description: "Use when the user asks to check for a new UnifiedQuantum release, track API changes, run smoke tests across all skills, or produce a version-alignment report. This skill teaches a 5-phase workflow: DETECT version gap (installed uniqc vs CLAUDE.md baseline + git tags + PyPI), DIFF changelog/commits between releases, SMOKE-TEST all 13 skills in parallel via sub-agents, AGGREGATE results cross-referenced with breaking changes, and REPORT with a markdown table + recommendations. All smoke tests use dummy backends only — no real cloud submission."
---

# Uniqc Version Tracker Skill

Use this skill to automatically track UnifiedQuantum releases and assess API breakage across all 13 skills in this repo. The workflow is designed for Claude Code sub-agent parallelism: detection and diffing run sequentially, then 13 smoke-test agents launch simultaneously, and results aggregate into a single markdown report.

This skill **reports, does not fix**. It identifies which skills need updates and why, but never auto-edits SKILL.md files or example scripts without explicit user approval.

## Core Mental Model

The tracker follows a 5-phase pipeline:

```
DETECT ──► DIFF ──► SMOKE-TEST (13 parallel sub-agents) ──► AGGREGATE ──► REPORT
```

1. **DETECT**: Compare installed `uniqc.__version__` against the CLAUDE.md baseline. Check upstream git tags and PyPI for newer releases. If aligned, exit early. If gap found, proceed.
2. **DIFF**: Parse the upstream CHANGELOG.md for the new version's `### ⚠ BREAKING` / `### Added` / `### Fixed` / `### Changed` sections. Run `git log vOLD..vNEW --oneline --no-merges` in the upstream repo. Cross-reference breaking changes against `grep -r` in `skills/` to identify affected files.
3. **SMOKE-TEST**: Dispatch 13 Claude Code sub-agents in parallel, each running one smoke test script from `examples/smoke-tests/`. Each sub-agent reports PASS/FAIL/SKIP + elapsed time + diagnostic message. Total wall time equals the slowest smoke test (~5 seconds).
4. **AGGREGATE**: Collect all 13 exit codes and output. Cross-reference each FAIL against known breaking changes from Phase 2. Classify each failure as "expected" (matches a changelog item) or "UNEXPECTED REGRESSION" (no matching changelog item — possible bug or undocumented change).
5. **REPORT**: Render the full markdown report following the template in [references/report-template.md](references/report-template.md). Include the header block, changelog summary, 13-row results table, cross-reference table, and prioritized recommendations.

## First Decision

| User goal | Read first |
|---|---|
| "Check if there's a new uniqc release" | Run Phase 1 (DETECT) — [examples/detect_version.py](examples/detect_version.py) |
| "What changed in the new version?" | Run Phase 2 (DIFF) — [references/changelog-parsing.md](references/changelog-parsing.md) + [references/commit-diffing.md](references/commit-diffing.md) |
| "Run smoke tests against the current install" | Run Phase 3 (SMOKE-TEST) — [references/smoke-test-guide.md](references/smoke-test-guide.md) + [examples/aggregate_report.py](examples/aggregate_report.py) |
| "Give me the full version-tracking report" | Run all 5 phases end-to-end |
| "Add a smoke test for a new skill" | [references/smoke-test-guide.md](references/smoke-test-guide.md) — "Adding a New Smoke Test" section |

## Practical Defaults

- **Dummy backends only.** All smoke tests use `dummy:local:simulator` or `dummy:local:virtual-line-N`. Never submit to real cloud backends (`originq:WK_C180`, `ibm:ibm_fez`, `quark:Baihua`) during automated smoke testing unless the user explicitly requests "Remote" mode with cost acknowledgement.
- **Missing optional deps = SKIP, not FAIL.** If `torch` or `qiskit` is not installed, the smoke test prints `SKIP: <dep> not installed` and exits 0. Missing optional dependencies are deployment issues, not API breakage.
- **Phase 1 runs first, always.** Don't diff or smoke-test without confirming a version gap exists. If `detect_version.py` reports "Aligned", stop and report that to the user — no further phases needed.
- **Parallel dispatch is the default for Phase 3.** Launch all 13 smoke-test sub-agents in a single message via the Agent tool. Do not run them sequentially unless the user asks for sequential mode.
- **Report, don't fix.** The tracker identifies what broke and which skills need updates. It does not auto-edit skill files. Present the report and ask the user which fixes they want applied.
- **Changelog is the primary source; commit diff is the ground truth.** Parse the changelog first for structured breaking-change info. Then verify with `git diff vOLD..vNEW` — flag any breaking change found in the diff that is missing from the changelog as an "undocumented breaking change."
- **setuptools_scm versioning.** Git tags are the canonical version source for UnifiedQuantum. `uniqc/_version.py` is auto-generated — never read it as authoritative. Development builds have `.devN` suffixes; strip them when looking up changelog entries.
- **The upstream repo is assumed to be at `../UnifiedQuantum`** relative to this repo's root. If it's elsewhere, the user must provide the path.

## Phase 1 — DETECT

Check for a version gap:

```bash
# Installed version
python -c "import uniqc; print(uniqc.__version__)"

# CLAUDE.md baseline
grep -oP 'UnifiedQuantum v\K[0-9.]+' CLAUDE.md

# Latest git tag in upstream repo
git -C ../UnifiedQuantum tag --sort=-version:refname | head -1

# Latest on PyPI (fallback if no local upstream clone)
pip index versions unified-quantum 2>/dev/null | head -1
```

Or run the helper script:

```bash
python .claude/skills/uniqc-version-tracker/examples/detect_version.py --repo-path .
```

If the installed version is newer than the CLAUDE.md baseline, a gap exists — proceed to Phase 2.

## Phase 2 — DIFF

Extract structured changelog info and commit-level changes:

```bash
# Parse changelog for a specific version
python .claude/skills/uniqc-version-tracker/examples/parse_changelog.py X.Y.Z \
  --changelog-path ../UnifiedQuantum/CHANGELOG.md

# Commit log between two tags
git -C ../UnifiedQuantum log vOLD..vNEW --oneline --no-merges

# Files-changed overview
git -C ../UnifiedQuantum diff vOLD..vNEW --stat -- uniqc/

# API surface diff (new exports, removed exports)
git -C ../UnifiedQuantum diff vOLD..vNEW -- uniqc/__init__.py

# Targeted diffs for known breakage hotspots
git -C ../UnifiedQuantum diff vOLD..vNEW -- uniqc/simulator/
git -C ../UnifiedQuantum diff vOLD..vNEW -- uniqc/cli/
git -C ../UnifiedQuantum diff vOLD..vNEW -- uniqc/task/
git -C ../UnifiedQuantum diff vOLD..vNEW -- uniqc/backend_adapter/
```

Cross-reference breaking changes against skills:

```bash
# For each CRITICAL item from the changelog, search for affected skills
grep -rl "RemovedAPIName\|RenamedAPIName" skills/ --include="*.md" --include="*.py"
```

See [references/changelog-parsing.md](references/changelog-parsing.md) for severity classification (CRITICAL / SIGNIFICANT / INFORMATIONAL) and [references/commit-diffing.md](references/commit-diffing.md) for commit message filtering and semver classification.

## Phase 3 — SMOKE-TEST

Dispatch 13 sub-agents in parallel. Each sub-agent runs one smoke test:

```
Agent: "Smoke test uniqc-basic-usage"
  Run: python .claude/skills/uniqc-version-tracker/examples/smoke-tests/smoke_basic_usage.py
  Report: PASS/FAIL/SKIP + time + diagnostic

Agent: "Smoke test uniqc-cloud-submit"
  Run: python .claude/skills/uniqc-version-tracker/examples/smoke-tests/smoke_cloud_submit.py
  Report: PASS/FAIL/SKIP + time + diagnostic

... (all 13 skills, one agent each)
```

Or run all sequentially with the aggregator for a quick check:

```bash
python .claude/skills/uniqc-version-tracker/examples/aggregate_report.py \
  --smoke-dir .claude/skills/uniqc-version-tracker/examples/smoke-tests \
  --json-summary smoke-summary.json
```

The aggregator exits nonzero for every `FAIL`, `ERROR`, `TIMEOUT`, or invalid
`SKIP`. Only a missing optional dependency may emit `SKIP:` and keep the
aggregate green.

## Fast structural and parity gates

Run this offline gate before every PR; it blocks broken local links, missing
Skill front matter, and missing reference targets:

```bash
python .claude/skills/uniqc-version-tracker/examples/validate_skill_repository.py \
  --repo-path . --json
```

For release parity, point the Skill-side checker at a UnifiedQuantum checkout:

```bash
python .claude/skills/uniqc-version-tracker/examples/verify_upstream_contract.py \
  --repo-path ../UnifiedQuantum
```

It checks the v0.1.1 commit, Python range, PyTorch extra, the
`uniqc-cppsimulator` split (no CMakeLists), Quafu removal, the new
tianyan/logicalqubit extras, config schema versioning, cache/config
paths, backend grammar, CLI lifecycle/flag, cloud-test opt-in default,
and the deprecation policy — plus the 0.1.1 rendering contract: the
seven-mode `circuit_render` engine behind `render()` / `Circuit.draw()`,
the `uniqc draw` CLI, `Circuit.to_matrix()`, and the 0.2.0 deprecation of
the legacy `draw()` / `draw_html()` wrappers (19 checks). The
UnifiedQuantum PR workflow should invoke this
script with `--repo-path "$GITHUB_WORKSPACE"` after checking out this Skill
repository (or its release artifact); no main-repository file change is needed
for the checker itself.

The 13 smoke tests and their expected times:

| # | Script | Skill | Time | Exercises |
|---|--------|-------|------|-----------|
| 1 | `smoke_basic_usage.py` | uniqc-basic-usage | ~8s | Circuit + Simulator.simulate_pmeasure + submit_task + draw/to_matrix |
| 2 | `smoke_cloud_submit.py` | uniqc-cloud-submit | ~2s | find_backend + dry_run + compile + submit_task |
| 3 | `smoke_result_analysis.py` | uniqc-result-analysis | ~2s | UnifiedResult fields + plot_histogram import |
| 4 | `smoke_xeb_qem.py` | uniqc-xeb-qem | ~3s | ReadoutEM calibration + apply |
| 5 | `smoke_circuit_interop.py` | uniqc-circuit-interop | ~1s | to_qiskit_circuit + exports + round-trip |
| 6 | `smoke_noise_simulation.py` | uniqc-noise-simulation | ~5s | NoisySimulator + Depolarizing + chip-backed dummy |
| 7 | `smoke_qaoa.py` | uniqc-qaoa | ~5s | qaoa_ansatz + run_qaoa_workflow |
| 8 | `smoke_quantum_ml.py` | uniqc-quantum-ml | ~2s | QuantumLayer forward pass (SKIP if no torch) |
| 9 | `smoke_algorithm_cases.py` | uniqc-algorithm-cases | ~1s | ghz_state, qft_circuit, grover, qpe fragments |
| 10 | `smoke_quantum_volume.py` | uniqc-quantum-volume | ~3s | Qiskit QV circuit + heavy-set |
| 11 | `smoke_classical_shadow.py` | uniqc-classical-shadow | ~3s | classical_shadow workflow + shadow_expectation |
| 12 | `smoke_doctor_config.py` | uniqc-doctor-config | ~2s | uniqc doctor CLI + config module imports |
| 13 | `smoke_platform_verify.py` | uniqc-platform-verify | ~3s | find_backend + list_backends + xeb_workflow import |

See [references/smoke-test-guide.md](references/smoke-test-guide.md) for the full smoke test philosophy, dummy backend policy, and instructions for adding a 14th test.

## Phase 4 — AGGREGATE

For each smoke test result, cross-reference against the changelog:

- **PASS** → skill is compatible with the new version. No action needed.
- **FAIL + matches a BREAKING changelog item** → "Expected Failure." The skill's SKILL.md or examples need updates to match the new API. List in the report's "Expected Failures" table with the specific changelog item and recommended fix.
- **FAIL + no matching changelog item** → "Unexpected Regression." Possible undocumented breaking change, bug, or environment issue. Flag prominently in the report.
- **SKIP** → optional dependency missing. Not a version-tracking concern.

Build the cross-reference tables following the template in [references/report-template.md](references/report-template.md).

## Phase 5 — REPORT

Render the full markdown report with these sections:

1. **Header Block** — date, baseline version, latest version, classification (MAJOR/MINOR/PATCH), git range
2. **Changelog Summary** — BREAKING, Added, Fixed, Changed sections extracted from upstream
3. **Smoke Test Results** — 13-row table (Skill | Status | Time | Key API | Diagnostic)
4. **Cross-Reference** — Expected Failures table, Unexpected Regressions table, Skills With No Gap table
5. **Recommendations** — prioritized list: skills needing SKILL.md updates, skills needing example rewrites, skills with no gap
6. **CLAUDE.md Update** — the exact line change needed for the version banner

The exact markdown format is specified in [references/report-template.md](references/report-template.md). Follow it precisely so reports are comparable across runs.

## Names to Remember

- PyPI package: `unified-quantum`
- Python import: `uniqc`
- Upstream repo (assumed): `../UnifiedQuantum`
- This skill's smoke tests: `.claude/skills/uniqc-version-tracker/examples/smoke-tests/`
- Helper scripts: `examples/detect_version.py`, `examples/parse_changelog.py`, `examples/aggregate_report.py`
- Reference docs: `references/changelog-parsing.md`, `references/commit-diffing.md`, `references/smoke-test-guide.md`, `references/report-template.md`
- CLAUDE.md baseline line: `Current alignment: **UnifiedQuantum vX.Y.Z**`
- Git tag format: `vX.Y.Z` (setuptools_scm)
- 13 skill directories: `skills/uniqc-{basic-usage,cloud-submit,result-analysis,xeb-qem,circuit-interop,noise-simulation,qaoa,quantum-ml,algorithm-cases,quantum-volume,classical-shadow,doctor-config,platform-verify}`

## Response Style

- Lead with the version gap: "uniqc v0.0.14 is available (you're on v0.0.13). Running full tracking workflow..."
- Present the 5-phase pipeline as it executes — tell the user which phase is running and what it found.
- After the report, summarize in one sentence: "X/Y skills pass, Z need updates for [specific API change]."
- Never auto-edit skill files. Present the recommendations table and ask: "Should I apply these fixes?"
- If all 13 smoke tests pass, celebrate briefly but still show the changelog summary so the user knows what new features are available.
- For unexpected regressions, recommend filing an upstream issue with the minimal reproducer from the smoke test.