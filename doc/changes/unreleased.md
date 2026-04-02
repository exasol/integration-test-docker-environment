# Unreleased

## Summary

This release fixes vulnerabilities by updating transitive dependencies in the `poetry.lock` file.

| Name         | Version | ID                  | Fix Versions | Updated to |
|--------------|---------|---------------------|--------------|------------|
| black        | 25.12.0 | CVE-2026-32274      | 26.3.1       | 26.3.1     |
| cryptography | 46.0.5  | CVE-2026-34073      | 46.0.6       | 46.0.6     |
| pygments     | 2.19.2  | CVE-2026-4539       | 2.20.0       | 2.20.0     |
| requests     | 2.32.5  | CVE-2026-25645      | 2.33.0       | 2.33.1     |
| tornado      | 6.5.4   | GHSA-78cv-mqj4-43f7 | 6.5.5        | 6.5.5      |
| tornado      | 6.5.4   | CVE-2026-31958      | 6.5.5        | 6.5.5      |

To ensure usage of secure packages, it is up to the user to similarly relock their dependencies.

## Refactoring:
- #602: Removed joblib Python module dependency
- #594: Removed old integration tests

## Bug Fixes:
- #600: Fixed nox session name

## Security Issues:
- #611: Updated to PTB 6.1.1 & fixed vulnerabilities by re-locking transitive dependencies
