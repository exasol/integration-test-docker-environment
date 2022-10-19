# Integration-Test-Docker-Environment 1.X.Y, released TBD

## Summary

TBD

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.14

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime

## Bug Fixes:

n/a

## Features / Enhancements:

n/a

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
