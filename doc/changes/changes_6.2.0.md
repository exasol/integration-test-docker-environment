# 6.2.0 - 2026-05-29

## Summary

ImageInfo uses now build_name in the target tag if available. Furthermore, some refactoring, internal fixes and updates.

## Security Issues

This release fixes vulnerabilities by updating dependencies:

| Dependency | Vulnerability | Affected | Fixed in |
|------------|---------------|----------|----------|
| black | CVE-2026-32274 | 25.12.0 | 26.3.1 |
| cryptography | PYSEC-2026-36 | 46.0.5 | 46.0.7 |
| cryptography | PYSEC-2026-35 | 46.0.5 | 46.0.6 |
| gitpython | CVE-2026-42215 | 3.1.46 | 3.1.47 |
| gitpython | CVE-2026-42284 | 3.1.46 | 3.1.47 |
| gitpython | CVE-2026-44244 | 3.1.46 | 3.1.49 |
| gitpython | GHSA-mv93-w799-cj2w | 3.1.46 | 3.1.50 |
| idna | CVE-2026-45409 | 3.11 | 3.15 |
| pip | CVE-2026-3219 | 26.0.1 | 26.1 |
| pip | CVE-2026-6357 | 26.0.1 | 26.1 |
| pygments | CVE-2026-4539 | 2.19.2 | 2.20.0 |
| pytest | CVE-2025-71176 | 7.4.4 | 9.0.3 |
| requests | CVE-2026-25645 | 2.32.5 | 2.33.0 |
| starlette | PYSEC-2026-161 | 0.52.1 | 1.0.1 |
| tornado | PYSEC-2026-140 | 6.5.4 | 6.5.5 |
| tornado | GHSA-78cv-mqj4-43f7 | 6.5.4 | 6.5.5 |
| tornado | CVE-2026-35536 | 6.5.4 | 6.5.5 |
| urllib3 | PYSEC-2026-142 | 2.6.3 | 2.7.0 |
| urllib3 | PYSEC-2026-141 | 2.6.3 | 2.7.0 |

## Refactoring:

- #602: Removed joblib Python module dependency
- #594: Removed old integration tests
- #627: Updated to PTB 8.1.1

## Features:

- #626: ImageInfo uses now build_name in the target tag if available

## Bug Fixes:

- #600: Fixed nox session name

## Security Issues:

- #611: Updated to PTB 6.1.1 & fixed vulnerabilities by re-locking transitive dependencies
- #627: Updated to PTB 7.0.0, updated `pytest` to 9.0.3, fixed vulnerabilities by re-locking transitive dependencies, and modified tests to pull docker images first

## Dependency Updates

### `main`

* Updated dependency `click:8.3.1` to `8.4.1`
* Updated dependency `fabric:3.2.2` to `3.2.3`
* Updated dependency `gitpython:3.1.46` to `3.1.50`
* Updated dependency `jsonpickle:4.1.1` to `4.1.2`
* Updated dependency `requests:2.32.5` to `2.34.2`
* Updated dependency `simplejson:3.20.2` to `4.1.1`

### `dev`

* Updated dependency `exasol-toolbox:5.1.1` to `8.1.1`
* Removed dependency `joblib:1.5.3`
* Updated dependency `mypy:1.19.1` to `1.20.2`
* Updated dependency `pyexasol:2.0.0` to `2.2.1`
* Updated dependency `pyinstaller:6.19.0` to `6.20.0`
* Updated dependency `pytest:7.4.4` to `9.0.3`
* Updated dependency `types-pyinstaller:6.19.0.20260215` to `6.20.0.20260518`