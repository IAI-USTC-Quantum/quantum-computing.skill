# Commit Diffing Guide

Teaches how to diff git commits between two UnifiedQuantum release tags to detect API changes.

## Core Commands

### List commits between two tags

```bash
git -C ../UnifiedQuantum log vOLD..vNEW --oneline --no-merges
```

### Files-changed overview

```bash
git -C ../UnifiedQuantum diff vOLD..vNEW --stat
```

### API surface diff (Python package only)

```bash
git -C ../UnifiedQuantum diff vOLD..vNEW -- uniqc/
```

## Commit Message Filtering

Not all commits are relevant to API tracking. Filter by prefix:

| Prefix | Relevant? | Reason |
|--------|-----------|--------|
| `feat:` / `feature:` | YES | New APIs, new modules, new function signatures |
| `fix:` | YES | Bug fixes that may change behaviour |
| `refactor:` | MAYBE | Internal reorganisation, check if public API changed |
| `BREAKING CHANGE:` | YES | Explicit breaking change marker |
| `docs:` | NO | Documentation only, no code changes |
| `chore:` | NO | Build/tooling/config |
| `ci:` | NO | CI pipeline changes |
| `test:` | NO | Test-only changes |
| `style:` | NO | Formatting/linting |

## Semver Classification

Parse both version strings as `(major, minor, patch)`:

- **MAJOR bump** (X in `X.y.z`): every public API reference in skills is potentially stale. Full smoke test required. `### ⚠ BREAKING` section is mandatory reading.
- **MINOR bump** (Y in `x.Y.z`): check `### Added` for new APIs that skills should adopt. Old APIs should still work. Full smoke test.
- **PATCH bump** (Z in `x.y.Z`): check `### Fixed` and `### Changed`. Smoke tests should be near-100% green.

## setuptools_scm Versioning

UnifiedQuantum uses `setuptools_scm` for version management. Key facts:

- Git tags are the source of truth (`v0.0.14`).
- `uniqc/_version.py` is auto-generated — never read it as canonical.
- Development builds have `.devN` suffixes (e.g., `0.0.14.dev43` = 43 commits past v0.0.14 tag).
- Use `git tag --sort=-version:refname` to list all release tags.

## Targeted File Diffs for Known Breakage Patterns

Based on historical breakage between v0.0.12 and v0.0.13:

```bash
# Simulator class renames
git diff vOLD..vNEW -- uniqc/simulator/

# CLI flag changes
git diff vOLD..vNEW -- uniqc/cli/

# Task submission signature changes
git diff vOLD..vNEW -- uniqc/task/

# Backend adapter changes
git diff vOLD..vNEW -- uniqc/backend_adapter/
```

## Undocumented Changes

Not all API changes appear in the changelog. The commit diff is the ground truth:

1. Scan `git diff vOLD..vNEW -- uniqc/__init__.py` for new exports and removed exports.
2. Scan `git diff vOLD..vNEW --stat -- uniqc/` for deleted files (removed modules).
3. Check for `DeprecationWarning` additions that signal future removals.

If you find a breaking change in the commit diff that is NOT in the changelog `### ⚠ BREAKING` section, flag it as an **undocumented breaking change** in the report.