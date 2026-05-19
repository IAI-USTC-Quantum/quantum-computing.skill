# Changelog Parsing Guide

Teaches how to parse the upstream UnifiedQuantum CHANGELOG.md (Keep a Changelog format).

## Format

Each release follows this structure:

```
## [X.Y.Z] - YYYY-MM-DD

Release summary paragraph.

### ⚠ BREAKING
- **removed API** — description
- **renamed API** — description

### Added
- **new feature** — description

### Fixed
- **bug fix** — description

### Changed
- **behavior change** — description

### Migration notes
- migration guidance for breaking changes
```

## Extraction Strategy

### Version block boundaries

Use the version headers as delimiters. The block for `[0.0.14]` runs from `## [0.0.14]` to the next `## [0.0.13]` header:

```bash
awk '/^## \[0\.0\.14\]/,/^## \[0\.0\.13\]/' CHANGELOG.md
```

In Python, use:

```python
import re
pattern = rf"^## \[{re.escape(version)}\].*$.*?(?=^## \[|\Z)"
m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
```

### Subsection extraction

Each subsection is delimited by `### <Label>\n` and ends at the next `### ` or the end of the version block:

```python
sec_m = re.search(rf"{re.escape('### Added')}\n(.*?)(?=### |\Z)", block, re.DOTALL)
bullets = re.findall(r"^- \*?\*?(.+?)(?:\n|$)", sec_m.group(1), re.MULTILINE)
```

### Bullet format

Each change starts with `- `, optionally with bold terms: `- **FeatureName** — explanation`.

Multi-paragraph bullets use indented continuation lines (no `-` prefix on follow-up paragraphs).

## Severity Classification

Parse bullets and classify each as:

| Severity | Keywords | Action |
|----------|----------|--------|
| CRITICAL | "removed", "renamed", "no longer accepts", "must now", "archived" | Skills referencing this API need immediate updates |
| SIGNIFICANT | "changed", "now defaults to", "enforced", "behaviour" | Skills may need example or reference updates |
| INFORMATIONAL | all others ("added", "fixed", "improved") | No action needed, but document for awareness |

## Cross-Referencing with Skills

After extracting CRITICAL items, search for affected skills:

```bash
grep -rl "OriginIR_Simulator\|QASM_Simulator" skills/ --include="*.md" --include="*.py"
```

## Edge Cases

- **Version not found in changelog**: The release may be so new the changelog hasn't been updated yet. Fall back to commit-log diff.
- **Missing section**: Not all versions have all sections. Empty sections are normal.
- **Pre-release/dev versions**: setuptools_scm generates `.devN` suffixes (e.g., `0.0.14.dev43`). Strip the dev suffix when looking up changelog entries — match against the base release tag.