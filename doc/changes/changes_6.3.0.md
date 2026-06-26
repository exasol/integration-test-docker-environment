# 6.3.0 - 2026-06-26

## Summary

This release adds support for docker-db version 2026.1.0 and 2025.1.11.

## Security Issues

This release fixes vulnerabilities by updating dependencies:

| Dependency | Vulnerability | Affected | Fixed in |
|------------|---------------|----------|----------|
| cryptography | GHSA-537c-gmf6-5ccf | 48.0.0 | 48.0.1 |
| msgpack | GHSA-6v7p-g79w-8964 | 1.1.2 | 1.2.1 |
| pip | PYSEC-2026-196 | 26.1.1 | 26.1.2 |
| tornado | GHSA-pw6j-qg29-8w7f | 6.5.6 | 6.5.7 |

## Features 

 - #640: Added support for 2026.1.0
 - #640: Added support for 2025.1.11

## Refactorings

 - #635: Removed broken release nox session in noxfile
 - #644: Updated `exasol-toolbox` to 10.0.0

## Bugs

 - #642: Fixed `DockerBuildImageTask` if base image is not in local docker registry
 

## Dependency Updates

### `dev`

* Updated dependency `exasol-toolbox:8.1.1` to `10.0.0`
* Updated dependency `pyexasol:2.2.1` to `2.2.2`
* Updated dependency `pyinstaller:6.20.0` to `6.21.0`
* Updated dependency `pytest:9.0.3` to `9.1.1`
* Updated dependency `types-pyinstaller:6.20.0.20260518` to `6.21.0.20260616`