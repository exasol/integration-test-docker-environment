# Integration-Test-Docker-Environment 1.2.0, released 2022-11-03

Code name: DB Parameter injection

## Summary

This release supports a new option which allows the injection of custom parameters to the database and also supports `docker-db` version 7.1.17.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.15

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime

## Bug Fixes:

n/a

## Features / Enhancements:

 - #270: Added support for additional db parameters
 - #272: Added Docker-DB 7.1.15 and prepare release
 - #281: Added Docker-DB 7.1.16, 7.1.17

## Refactoring:

n/a

## Documentation:

n/a

## Security:

- Evaluated CVE-2022-42969
    - CVE will be silenced
    - The affected code is not used by our project itself, nor by the dependencies pulling in the vulnerable
      library.
      Checked dependencies:
        * Nox (Code search)
        * Pytest (Code search + [Tracking-Issue](https://github.com/pytest-dev/pytest/issues/10392)
